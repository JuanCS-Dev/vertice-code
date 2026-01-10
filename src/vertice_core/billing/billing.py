"""
Billing Automation Engine - Enterprise-grade billing with Stripe integration.

Handles invoice generation, tax compliance, payment processing, and
billing automation for enterprise customers.
"""

import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from .types import BillingPeriod, UsageType

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
            "tax_rates": (
                [
                    {
                        "display_name": f"{self.tax_info.tax_type} ({self.tax_info.tax_rate}%)",
                        "percentage": self.tax_info.tax_rate,
                        "inclusive": False,
                    }
                ]
                if self.tax_info
                else []
            ),
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

    def __init__(
        self,
        stripe_secret_key: str,
        tax_rates: Optional[Dict[str, TaxInfo]] = None,
        ai_optimization_enabled: bool = True,  # 2026 AI-powered billing
    ):
        """
        Initialize billing engine with AI-powered optimization (2026).

        Args:
            stripe_secret_key: Stripe secret key for API calls
            tax_rates: Tax rates by country/state
            ai_optimization_enabled: Enable AI-powered billing optimization
        """
        self.stripe_secret_key = stripe_secret_key
        self.tax_rates = tax_rates or self._get_default_tax_rates()
        self.ai_optimization_enabled = ai_optimization_enabled

        # In-memory storage (production would use database)
        self.invoices: Dict[str, Invoice] = {}
        self.billing_periods: Dict[str, List[BillingPeriod]] = {}

        # AI-powered features (2026)
        self.payment_retry_patterns: Dict[str, Dict] = {}
        self.customer_risk_profiles: Dict[str, Dict] = {}

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
            overage_descriptions: List[str] = []

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

    async def optimize_payment_retry_strategy(
        self, tenant_id: str, failed_payment_history: List[Dict]
    ) -> Dict[str, Any]:
        """
        AI-powered payment retry optimization (2026 trend).

        Analyzes payment failure patterns and optimizes retry strategy.

        Args:
            tenant_id: Tenant identifier
            failed_payment_history: History of failed payment attempts

        Returns:
            Optimized retry strategy
        """
        if not self.ai_optimization_enabled:
            return self._default_retry_strategy()

        # Analyze failure patterns
        failure_reasons = [f.get("reason", "unknown") for f in failed_payment_history]

        # Simple AI analysis (in production, use ML models)
        card_declines = failure_reasons.count("card_declined")
        insufficient_funds = failure_reasons.count("insufficient_funds")
        expired_cards = failure_reasons.count("card_expired")

        # Calculate optimal retry strategy
        if card_declines > len(failure_reasons) * 0.5:
            # High card decline rate - focus on card updates
            strategy = {
                "recommendation": "card_update_campaign",
                "retry_delays": [24, 72, 168],  # 1d, 3d, 1w
                "max_attempts": 3,
                "ai_insight": "High card decline rate suggests expired/invalid cards",
            }
        elif insufficient_funds > len(failure_reasons) * 0.3:
            # Insufficient funds - longer delays
            strategy = {
                "recommendation": "extended_retry",
                "retry_delays": [72, 168, 336],  # 3d, 1w, 2w
                "max_attempts": 3,
                "ai_insight": "Insufficient funds pattern - allow more time between retries",
            }
        else:
            # General failures - standard approach
            strategy = {
                "recommendation": "standard_retry",
                "retry_delays": [24, 72, 168],
                "max_attempts": 3,
                "ai_insight": "Mixed failure reasons - use standard retry pattern",
            }

        # Store learned patterns for future optimization
        self.payment_retry_patterns[tenant_id] = {
            "last_updated": time.time(),
            "failure_analysis": {
                "card_declines": card_declines,
                "insufficient_funds": insufficient_funds,
                "expired_cards": expired_cards,
                "total_failures": len(failed_payment_history),
            },
            "optimal_strategy": strategy,
        }

        return strategy

    async def predictive_dunning_management(
        self, tenant_id: str, overdue_invoices: List[Invoice]
    ) -> Dict[str, Any]:
        """
        AI-powered predictive dunning management (2026 enterprise trend).

        Predicts payment likelihood and optimizes dunning strategy.

        Args:
            tenant_id: Tenant identifier
            overdue_invoices: List of overdue invoices

        Returns:
            Optimized dunning strategy
        """
        if not overdue_invoices:
            return {"action": "no_action", "reason": "no_overdue_invoices"}

        # Calculate risk score based on overdue history
        total_overdue = sum(inv.total_amount for inv in overdue_invoices)
        days_overdue = max(
            (time.time() - inv.due_date.timestamp()) / 86400 for inv in overdue_invoices
        )

        # Simple risk scoring (production would use ML)
        risk_score = min(100, (total_overdue / 1000) * 10 + (days_overdue / 30) * 20)

        if risk_score > 70:
            # High risk - immediate action
            strategy = {
                "action": "immediate_collection",
                "priority": "urgent",
                "communication": "executive_outreach",
                "ai_insight": f"High risk score ({risk_score:.1f}) - immediate attention required",
            }
        elif risk_score > 40:
            # Medium risk - escalated dunning
            strategy = {
                "action": "escalated_dunning",
                "priority": "high",
                "communication": "multi_channel_campaign",
                "ai_insight": f"Medium risk score ({risk_score:.1f}) - escalated engagement needed",
            }
        else:
            # Low risk - standard dunning
            strategy = {
                "action": "standard_dunning",
                "priority": "normal",
                "communication": "email_sequence",
                "ai_insight": f"Low risk score ({risk_score:.1f}) - standard collection process",
            }

        # Update risk profile
        self.customer_risk_profiles[tenant_id] = {
            "last_updated": time.time(),
            "risk_score": risk_score,
            "total_overdue": total_overdue,
            "avg_days_overdue": days_overdue,
            "recommended_strategy": strategy,
        }

        return strategy

    def _default_retry_strategy(self) -> Dict[str, Any]:
        """Default payment retry strategy when AI is disabled."""
        return {
            "recommendation": "standard_retry",
            "retry_delays": [24, 72, 168],  # 1d, 3d, 1w
            "max_attempts": 3,
            "ai_insight": "AI optimization disabled - using standard retry pattern",
        }

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
        """Get comprehensive tax rates for 50+ countries (2026 Global Compliance)."""
        return {
            # North America
            "US": TaxInfo(country_code="US", tax_rate=0.0, tax_type="Sales Tax"),
            "CA": TaxInfo(country_code="CA", tax_rate=5.0, tax_type="GST"),
            "MX": TaxInfo(country_code="MX", tax_rate=16.0, tax_type="IVA"),
            # European Union (VAT rates as of 2026)
            "GB": TaxInfo(country_code="GB", tax_rate=20.0, tax_type="VAT"),
            "DE": TaxInfo(country_code="DE", tax_rate=19.0, tax_type="VAT"),
            "FR": TaxInfo(country_code="FR", tax_rate=20.0, tax_type="VAT"),
            "IT": TaxInfo(country_code="IT", tax_rate=22.0, tax_type="VAT"),
            "ES": TaxInfo(country_code="ES", tax_rate=21.0, tax_type="VAT"),
            "NL": TaxInfo(country_code="NL", tax_rate=21.0, tax_type="VAT"),
            "BE": TaxInfo(country_code="BE", tax_rate=21.0, tax_type="VAT"),
            "AT": TaxInfo(country_code="AT", tax_rate=20.0, tax_type="VAT"),
            "SE": TaxInfo(country_code="SE", tax_rate=25.0, tax_type="VAT"),
            "DK": TaxInfo(country_code="DK", tax_rate=25.0, tax_type="VAT"),
            "FI": TaxInfo(country_code="FI", tax_rate=24.0, tax_type="VAT"),
            "PT": TaxInfo(country_code="PT", tax_rate=23.0, tax_type="VAT"),
            "IE": TaxInfo(country_code="IE", tax_rate=23.0, tax_type="VAT"),
            "LU": TaxInfo(country_code="LU", tax_rate=17.0, tax_type="VAT"),
            "MT": TaxInfo(country_code="MT", tax_rate=18.0, tax_type="VAT"),
            "CY": TaxInfo(country_code="CY", tax_rate=19.0, tax_type="VAT"),
            "EE": TaxInfo(country_code="EE", tax_rate=20.0, tax_type="VAT"),
            "LV": TaxInfo(country_code="LV", tax_rate=21.0, tax_type="VAT"),
            "LT": TaxInfo(country_code="LT", tax_rate=21.0, tax_type="VAT"),
            "SK": TaxInfo(country_code="SK", tax_rate=20.0, tax_type="VAT"),
            "SI": TaxInfo(country_code="SI", tax_rate=22.0, tax_type="VAT"),
            "HR": TaxInfo(country_code="HR", tax_rate=25.0, tax_type="VAT"),
            "PL": TaxInfo(country_code="PL", tax_rate=23.0, tax_type="VAT"),
            "HU": TaxInfo(country_code="HU", tax_rate=27.0, tax_type="VAT"),
            "CZ": TaxInfo(country_code="CZ", tax_rate=21.0, tax_type="VAT"),
            "RO": TaxInfo(country_code="RO", tax_rate=19.0, tax_type="VAT"),
            "BG": TaxInfo(country_code="BG", tax_rate=20.0, tax_type="VAT"),
            "GR": TaxInfo(country_code="GR", tax_rate=24.0, tax_type="VAT"),
            # Asia Pacific
            "AU": TaxInfo(country_code="AU", tax_rate=10.0, tax_type="GST"),
            "NZ": TaxInfo(country_code="NZ", tax_rate=15.0, tax_type="GST"),
            "JP": TaxInfo(country_code="JP", tax_rate=10.0, tax_type="VAT"),
            "KR": TaxInfo(country_code="KR", tax_rate=10.0, tax_type="VAT"),
            "SG": TaxInfo(country_code="SG", tax_rate=9.0, tax_type="GST"),
            "HK": TaxInfo(country_code="HK", tax_rate=0.0, tax_type="No Tax"),
            "IN": TaxInfo(country_code="IN", tax_rate=18.0, tax_type="GST"),
            "CN": TaxInfo(country_code="CN", tax_rate=13.0, tax_type="VAT"),
            "TW": TaxInfo(country_code="TW", tax_rate=5.0, tax_type="VAT"),
            "TH": TaxInfo(country_code="TH", tax_rate=7.0, tax_type="VAT"),
            "MY": TaxInfo(country_code="MY", tax_rate=10.0, tax_type="GST"),
            "PH": TaxInfo(country_code="PH", tax_rate=12.0, tax_type="VAT"),
            "ID": TaxInfo(country_code="ID", tax_rate=11.0, tax_type="VAT"),
            # Latin America
            "BR": TaxInfo(country_code="BR", tax_rate=0.0, tax_type="Tax Included"),
            "AR": TaxInfo(country_code="AR", tax_rate=21.0, tax_type="IVA"),
            "CL": TaxInfo(country_code="CL", tax_rate=19.0, tax_type="IVA"),
            "CO": TaxInfo(country_code="CO", tax_rate=19.0, tax_type="IVA"),
            "PE": TaxInfo(country_code="PE", tax_rate=18.0, tax_type="IGV"),
            "UY": TaxInfo(country_code="UY", tax_rate=22.0, tax_type="IVA"),
            "PY": TaxInfo(country_code="PY", tax_rate=10.0, tax_type="IVA"),
            # Middle East & Africa
            "AE": TaxInfo(country_code="AE", tax_rate=5.0, tax_type="VAT"),
            "SA": TaxInfo(country_code="SA", tax_rate=15.0, tax_type="VAT"),
            "ZA": TaxInfo(country_code="ZA", tax_rate=15.0, tax_type="VAT"),
            "EG": TaxInfo(country_code="EG", tax_rate=14.0, tax_type="VAT"),
            "NG": TaxInfo(country_code="NG", tax_rate=7.5, tax_type="VAT"),
            "KE": TaxInfo(country_code="KE", tax_rate=16.0, tax_type="VAT"),
            "GH": TaxInfo(country_code="GH", tax_rate=15.0, tax_type="VAT"),
            # Special territories
            "CH": TaxInfo(country_code="CH", tax_rate=8.1, tax_type="VAT"),
            "NO": TaxInfo(country_code="NO", tax_rate=25.0, tax_type="VAT"),
            "IS": TaxInfo(country_code="IS", tax_rate=24.0, tax_type="VAT"),
            "TR": TaxInfo(country_code="TR", tax_rate=20.0, tax_type="VAT"),
        }


__all__ = ["Invoice", "InvoiceItem", "TaxInfo", "BillingEngine"]
