"""
Billing Automation Engine - Enterprise-grade billing with Stripe integration.

Handles invoice generation, tax compliance, payment processing, and
billing automation for enterprise customers.
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from .types import BillingPeriod, PricingPlan, PricingTier, UsageType

logger = logging.getLogger(__name__)


@dataclass
class InvoiceItem:
    """Individual item on an invoice."""

    description: str
    quantity: int
    unit_price: float
    amount: float
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def total_amount(self) -> float:
        """Calculate total amount for this item."""
        return self.quantity * self.unit_price


@dataclass
class TaxInfo:
    """Tax information for billing."""

    country_code: str
    state_code: Optional[str] = None
    tax_rate: float = 0.0  # Percentage (e.g., 8.25 for 8.25%)
    tax_type: str = "VAT"  # VAT, GST, Sales Tax, etc.

    def calculate_tax(self, amount: float) -> float:
        """Calculate tax amount for a given amount."""
        return amount * (self.tax_rate / 100)


@dataclass
class Invoice:
    """Complete invoice with all billing details."""

    invoice_id: str
    tenant_id: str
    billing_period: BillingPeriod
    issue_date: datetime
    due_date: datetime

    # Customer info
    customer_name: str
    customer_email: str
    billing_address: Dict[str, str]

    # Invoice items
    items: List[InvoiceItem] = field(default_factory=list)

    # Taxes
    tax_info: Optional[TaxInfo] = None

    # Totals
    subtotal: float = 0.0
    tax_amount: float = 0.0
    total_amount: float = 0.0

    # Status
    status: str = "draft"  # draft, sent, paid, overdue, cancelled
    stripe_invoice_id: Optional[str] = None
    payment_date: Optional[datetime] = None

    def calculate_totals(self) -> None:
        """Calculate invoice totals including taxes."""
        self.subtotal = sum(item.total_amount for item in self.items)

        if self.tax_info:
            self.tax_amount = self.tax_info.calculate_tax(self.subtotal)

        self.total_amount = self.subtotal + self.tax_amount

    def add_item(
        self,
        description: str,
        quantity: int,
        unit_price: float,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Add an item to the invoice."""
        amount = quantity * unit_price
        item = InvoiceItem(
            description=description,
            quantity=quantity,
            unit_price=unit_price,
            amount=amount,
            metadata=metadata or {},
        )
        self.items.append(item)
        self.calculate_totals()

    def to_stripe_format(self) -> Dict[str, Any]:
        """Convert invoice to Stripe-compatible format."""
        return {
            "customer_email": self.customer_email,
            "description": f"Vertice Enterprise Billing - {self.billing_period.period_start.strftime('%B %Y')}",
            "metadata": {
                "tenant_id": self.tenant_id,
                "billing_period_start": self.billing_period.period_start.isoformat(),
                "billing_period_end": self.billing_period.period_end.isoformat(),
            },
            "line_items": [
                {
                    "description": item.description,
                    "quantity": item.quantity,
                    "unit_amount": int(item.unit_price * 100),  # Convert to cents
                    "metadata": item.metadata,
                }
                for item in self.items
            ],
            "tax_rates": [
                {
                    "display_name": f"{self.tax_info.tax_type} ({self.tax_info.tax_rate}%)",
                    "percentage": self.tax_info.tax_rate,
                    "inclusive": False,
                }
            ]
            if self.tax_info
            else [],
        }


class BillingEngine:
    """
    Enterprise billing automation engine.

    Handles:
    - Invoice generation
    - Tax calculation and compliance
    - Stripe integration
    - Payment processing
    - Billing cycle management
    """

    def __init__(self, stripe_secret_key: str, tax_rates: Optional[Dict[str, TaxInfo]] = None):
        """
        Initialize billing engine.

        Args:
            stripe_secret_key: Stripe secret key for API calls
            tax_rates: Tax rates by country/state
        """
        self.stripe_secret_key = stripe_secret_key
        self.tax_rates = tax_rates or self._get_default_tax_rates()

        # In-memory storage (production would use database)
        self.invoices: Dict[str, Invoice] = {}
        self.billing_periods: Dict[str, List[BillingPeriod]] = {}

    async def create_invoice(
        self,
        tenant_id: str,
        customer_info: Dict[str, Any],
        billing_period: BillingPeriod,
        auto_send: bool = True,
    ) -> Invoice:
        """
        Create a new invoice for a billing period.

        Args:
            tenant_id: Tenant identifier
            customer_info: Customer billing information
            billing_period: Billing period with usage data
            auto_send: Whether to automatically send the invoice

        Returns:
            Created invoice
        """
        # Generate invoice ID
        invoice_id = f"INV-{tenant_id}-{billing_period.period_start.strftime('%Y%m')}"

        # Determine tax info based on billing address
        tax_info = self._get_tax_info(customer_info.get("billing_address", {}))

        # Create invoice
        invoice = Invoice(
            invoice_id=invoice_id,
            tenant_id=tenant_id,
            billing_period=billing_period,
            issue_date=datetime.now(),
            due_date=datetime.now() + timedelta(days=30),  # Net 30
            customer_name=customer_info["name"],
            customer_email=customer_info["email"],
            billing_address=customer_info["billing_address"],
            tax_info=tax_info,
        )

        # Add base plan item
        invoice.add_item(
            description=f"{billing_period.pricing_plan.name} Plan - {billing_period.period_start.strftime('%B %Y')}",
            quantity=1,
            unit_price=billing_period.pricing_plan.base_price_monthly,
            metadata={"plan_tier": billing_period.pricing_plan.tier.value},
        )

        # Add overage items if any
        if billing_period.overage_cost > 0:
            # Break down overages by type (simplified)
            overage_descriptions = []

            if (
                billing_period.usage_summary.get(UsageType.AI_TOKENS, 0)
                > billing_period.pricing_plan.max_ai_tokens
            ):
                excess_tokens = (
                    billing_period.usage_summary[UsageType.AI_TOKENS]
                    - billing_period.pricing_plan.max_ai_tokens
                )
                token_cost = (
                    excess_tokens / 1000
                ) * billing_period.pricing_plan.overage_ai_tokens_per_1k
                invoice.add_item(
                    description=f"AI Tokens Overage ({excess_tokens:,} tokens)",
                    quantity=1,
                    unit_price=token_cost,
                    metadata={"overage_type": "ai_tokens", "excess_quantity": excess_tokens},
                )

            if (
                billing_period.usage_summary.get(UsageType.STORAGE_GB, 0)
                > billing_period.pricing_plan.max_storage_gb
            ):
                excess_storage = (
                    billing_period.usage_summary[UsageType.STORAGE_GB]
                    - billing_period.pricing_plan.max_storage_gb
                )
                storage_cost = excess_storage * billing_period.pricing_plan.overage_storage_per_gb
                invoice.add_item(
                    description=f"Storage Overage ({excess_storage} GB)",
                    quantity=1,
                    unit_price=storage_cost,
                    metadata={"overage_type": "storage", "excess_quantity": excess_storage},
                )

        # Store invoice
        self.invoices[invoice_id] = invoice

        # Auto-send if requested
        if auto_send:
            await self.send_invoice(invoice_id)

        logger.info(
            f"Created invoice {invoice_id} for tenant {tenant_id}: ${invoice.total_amount:.2f}"
        )
        return invoice

    async def send_invoice(self, invoice_id: str) -> bool:
        """
        Send invoice via Stripe.

        Args:
            invoice_id: Invoice identifier

        Returns:
            True if sent successfully
        """
        if invoice_id not in self.invoices:
            logger.error(f"Invoice {invoice_id} not found")
            return False

        invoice = self.invoices[invoice_id]

        try:
            # In a real implementation, this would call Stripe API
            # For now, we'll simulate the Stripe integration

            stripe_data = invoice.to_stripe_format()

            # Simulate Stripe API call
            logger.info(f"Simulating Stripe invoice creation for {invoice_id}")

            # Mark as sent
            invoice.status = "sent"
            invoice.stripe_invoice_id = f"simulated_stripe_{invoice_id}"

            logger.info(f"Invoice {invoice_id} sent successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to send invoice {invoice_id}: {e}")
            return False

    async def process_payment(
        self, invoice_id: str, payment_method_id: str, amount: Optional[float] = None
    ) -> bool:
        """
        Process payment for an invoice.

        Args:
            invoice_id: Invoice identifier
            payment_method_id: Stripe payment method ID
            amount: Amount to charge (defaults to invoice total)

        Returns:
            True if payment processed successfully
        """
        if invoice_id not in self.invoices:
            logger.error(f"Invoice {invoice_id} not found")
            return False

        invoice = self.invoices[invoice_id]
        amount = amount or invoice.total_amount

        try:
            # Simulate Stripe payment processing
            logger.info(f"Simulating payment processing for invoice {invoice_id}: ${amount:.2f}")

            # Mark as paid
            invoice.status = "paid"
            invoice.payment_date = datetime.now()

            logger.info(f"Payment processed successfully for invoice {invoice_id}")
            return True

        except Exception as e:
            logger.error(f"Payment processing failed for invoice {invoice_id}: {e}")
            return False

    def get_invoice(self, invoice_id: str) -> Optional[Invoice]:
        """Get invoice by ID."""
        return self.invoices.get(invoice_id)

    def get_tenant_invoices(self, tenant_id: str) -> List[Invoice]:
        """Get all invoices for a tenant."""
        return [inv for inv in self.invoices.values() if inv.tenant_id == tenant_id]

    def _get_tax_info(self, billing_address: Dict[str, str]) -> Optional[TaxInfo]:
        """Get tax information based on billing address."""
        country = billing_address.get("country", "").upper()

        if country in self.tax_rates:
            return self.tax_rates[country]

        # Default to no tax if country not found
        return None

    def _get_default_tax_rates(self) -> Dict[str, TaxInfo]:
        """Get default tax rates for major countries."""
        return {
            "US": TaxInfo(
                country_code="US",
                tax_rate=0.0,  # Sales tax varies by state, handled separately
                tax_type="Sales Tax",
            ),
            "GB": TaxInfo(
                country_code="GB",
                tax_rate=20.0,  # UK VAT
                tax_type="VAT",
            ),
            "DE": TaxInfo(
                country_code="DE",
                tax_rate=19.0,  # German VAT
                tax_type="VAT",
            ),
            "FR": TaxInfo(
                country_code="FR",
                tax_rate=20.0,  # French VAT
                tax_type="VAT",
            ),
            "BR": TaxInfo(
                country_code="BR",
                tax_rate=0.0,  # Tax included in pricing for Brazil
                tax_type="Tax Included",
            ),
        }


__all__ = ["Invoice", "InvoiceItem", "TaxInfo", "BillingEngine"]
