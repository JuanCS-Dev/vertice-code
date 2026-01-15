"""
Vertice-Code Database Models
SQLAlchemy models with Pydantic schemas for multi-tenant SaaS platform
"""

from __future__ import annotations

import uuid
from datetime import datetime, date
from typing import Optional, List, Dict, Any
from decimal import Decimal

from sqlalchemy import (
    Column,
    String,
    Integer,
    Boolean,
    DateTime,
    Text,
    ForeignKey,
    JSON,
    Numeric,
    ARRAY,
    Date,
    text,
    Index,
)
from sqlalchemy.types import UUID as SQLUUID
from sqlalchemy.dialects.postgresql import BYTEA, INET
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, Mapped
from pydantic import BaseModel, Field

Base = declarative_base()


# =============================================================================
# SQLAlchemy Models
# =============================================================================


class Workspace(Base):
    """Workspace (Tenant) model"""

    __tablename__ = "workspaces"

    id: Mapped[uuid.UUID] = Column(SQLUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = Column(String(255), nullable=False)
    slug: Mapped[str] = Column(String(100), nullable=False, unique=True)
    description: Mapped[Optional[str]] = Column(Text)

    # Billing & Limits
    subscription_plan: Mapped[str] = Column(String(50), default="free")
    monthly_token_limit: Mapped[int] = Column(Integer, default=100000)
    storage_limit_gb: Mapped[int] = Column(Integer, default=5)

    # Encryption (GDPR)
    data_encryption_key: Mapped[Optional[bytes]] = Column(BYTEA)
    key_encryption_version: Mapped[int] = Column(Integer, default=1)

    # Metadata
    created_at: Mapped[datetime] = Column(DateTime(timezone=True), server_default=text("NOW()"))
    updated_at: Mapped[datetime] = Column(DateTime(timezone=True), server_default=text("NOW()"))
    is_active: Mapped[bool] = Column(Boolean, default=True)

    # Soft delete
    deleted_at: Mapped[Optional[datetime]] = Column(DateTime(timezone=True))
    deletion_reason: Mapped[Optional[str]] = Column(Text)

    # Relationships
    users: Mapped[List["User"]] = relationship("User", back_populates="workspace")
    agents: Mapped[List["Agent"]] = relationship("Agent", back_populates="workspace")
    # knowledge_entries: Mapped[List["KnowledgeEntry"]] = relationship(
    #     "KnowledgeEntry", back_populates="workspace"
    # )


class User(Base):
    """User model with Google Identity integration"""

    __tablename__ = "users"

    id: Mapped[uuid.UUID] = Column(SQLUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    auth_id: Mapped[str] = Column(String(255), nullable=False, unique=True)

    # Profile
    email: Mapped[str] = Column(String(255), nullable=False)
    first_name: Mapped[Optional[str]] = Column(String(255))
    last_name: Mapped[Optional[str]] = Column(String(255))
    username: Mapped[Optional[str]] = Column(String(100), unique=True)
    avatar_url: Mapped[Optional[str]] = Column(Text)

    # Workspace membership
    workspace_id: Mapped[Optional[uuid.UUID]] = Column(
        SQLUUID(as_uuid=True), ForeignKey("workspaces.id")
    )
    role: Mapped[str] = Column(String(50), default="member")

    # Preferences
    preferences: Mapped[Dict[str, Any]] = Column(JSON, default=dict)
    timezone: Mapped[str] = Column(String(50), default="UTC")
    language: Mapped[str] = Column(String(10), default="en")

    # Security
    last_login_at: Mapped[Optional[datetime]] = Column(DateTime(timezone=True))
    login_count: Mapped[int] = Column(Integer, default=0)
    mfa_enabled: Mapped[bool] = Column(Boolean, default=False)

    # Metadata
    created_at: Mapped[datetime] = Column(DateTime(timezone=True), server_default=text("NOW()"))
    updated_at: Mapped[datetime] = Column(DateTime(timezone=True), server_default=text("NOW()"))
    is_active: Mapped[bool] = Column(Boolean, default=True)

    # GDPR
    data_retention_until: Mapped[Optional[datetime]] = Column(DateTime(timezone=True))
    consent_given_at: Mapped[Optional[datetime]] = Column(DateTime(timezone=True))
    marketing_consent: Mapped[bool] = Column(Boolean, default=False)

    # Relationships
    workspace: Mapped[Optional["Workspace"]] = relationship("Workspace", back_populates="users")


class Agent(Base):
    """Agent model for autonomous AI agents"""

    __tablename__ = "agents"

    id: Mapped[uuid.UUID] = Column(SQLUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workspace_id: Mapped[uuid.UUID] = Column(
        SQLUUID(as_uuid=True), ForeignKey("workspaces.id"), nullable=False
    )

    # Identity
    agent_name: Mapped[str] = Column(String(255), nullable=False)
    agent_type: Mapped[str] = Column(String(100), default="generic")
    description: Mapped[Optional[str]] = Column(Text)

    # API Key (hashed)
    api_key_hash: Mapped[str] = Column(String(128), nullable=False, unique=True)
    key_rotation_required: Mapped[bool] = Column(Boolean, default=False)

    # Capabilities & Limits
    scopes: Mapped[List[str]] = Column(ARRAY(String), default=["read:memory", "write:logs"])
    daily_token_budget: Mapped[int] = Column(Integer, default=1000)
    max_concurrent_sessions: Mapped[int] = Column(Integer, default=5)

    # Status
    is_active: Mapped[bool] = Column(Boolean, default=True)
    last_seen_at: Mapped[Optional[datetime]] = Column(DateTime(timezone=True))
    total_tokens_used: Mapped[int] = Column(Integer, default=0)

    # Configuration
    system_prompt: Mapped[Optional[str]] = Column(Text)
    model_preferences: Mapped[Dict[str, Any]] = Column(JSON, default=dict)
    custom_instructions: Mapped[Optional[str]] = Column(Text)

    # Metadata
    created_at: Mapped[datetime] = Column(DateTime(timezone=True), server_default=text("NOW()"))
    updated_at: Mapped[datetime] = Column(DateTime(timezone=True), server_default=text("NOW()"))
    created_by: Mapped[Optional[uuid.UUID]] = Column(SQLUUID(as_uuid=True), ForeignKey("users.id"))

    # GDPR
    data_encryption_key: Mapped[Optional[bytes]] = Column(BYTEA)
    retention_policy: Mapped[str] = Column(String(50), default="standard")

    # Relationships
    workspace: Mapped["Workspace"] = relationship("Workspace", back_populates="agents")


class KnowledgeEntry(Base):
    """Knowledge base entries for RAG"""

    __tablename__ = "knowledge_entries"

    id: Mapped[uuid.UUID] = Column(SQLUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workspace_id: Mapped[uuid.UUID] = Column(
        SQLUUID(as_uuid=True), ForeignKey("workspaces.id"), nullable=False
    )

    # Content
    content_type: Mapped[str] = Column(String(50), nullable=False)
    title: Mapped[Optional[str]] = Column(String(500))
    content: Mapped[str] = Column(Text, nullable=False)
    content_metadata: Mapped[Dict[str, Any]] = Column(JSON, default=dict)

    # Vector embeddings
    vector_id: Mapped[Optional[str]] = Column(String(255))
    embedding_model: Mapped[str] = Column(String(100), default="text-embedding-ada-002")
    content_hash: Mapped[Optional[str]] = Column(String(64))

    # Access control
    access_level: Mapped[str] = Column(String(50), default="workspace")
    owner_id: Mapped[Optional[uuid.UUID]] = Column(SQLUUID(as_uuid=True), ForeignKey("users.id"))

    # Encryption
    is_encrypted: Mapped[bool] = Column(Boolean, default=False)
    encryption_key_version: Mapped[int] = Column(Integer, default=1)

    # Metadata
    created_at: Mapped[datetime] = Column(DateTime(timezone=True), server_default=text("NOW()"))
    updated_at: Mapped[datetime] = Column(DateTime(timezone=True), server_default=text("NOW()"))
    created_by: Mapped[Optional[uuid.UUID]] = Column(SQLUUID(as_uuid=True), ForeignKey("users.id"))
    last_accessed_at: Mapped[Optional[datetime]] = Column(DateTime(timezone=True))

    # Relationships
    workspace: Mapped["Workspace"] = relationship("Workspace")


class UsageRecord(Base):
    """Usage tracking for billing"""

    __tablename__ = "usage_records"

    id: Mapped[uuid.UUID] = Column(SQLUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workspace_id: Mapped[uuid.UUID] = Column(
        SQLUUID(as_uuid=True), ForeignKey("workspaces.id"), nullable=False
    )

    # What was used
    resource_type: Mapped[str] = Column(String(100), nullable=False)
    resource_id: Mapped[Optional[str]] = Column(String(255))

    # Quantities
    quantity_used: Mapped[Decimal] = Column(Numeric(15, 6), nullable=False)
    unit: Mapped[str] = Column(String(50), nullable=False)

    # Cost
    unit_cost: Mapped[Optional[Decimal]] = Column(Numeric(10, 6))
    total_cost: Mapped[Optional[Decimal]] = Column(Numeric(12, 6))

    # Attribution
    user_id: Mapped[Optional[uuid.UUID]] = Column(SQLUUID(as_uuid=True), ForeignKey("users.id"))
    agent_id: Mapped[Optional[uuid.UUID]] = Column(SQLUUID(as_uuid=True), ForeignKey("agents.id"))
    session_id: Mapped[Optional[str]] = Column(String(255))

    # Metadata
    recorded_at: Mapped[datetime] = Column(DateTime(timezone=True), server_default=text("NOW()"))
    billing_period: Mapped[date] = Column(Date, nullable=False, default=date.today)


class Subscription(Base):
    """Stripe subscription management"""

    __tablename__ = "subscriptions"

    id: Mapped[uuid.UUID] = Column(SQLUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workspace_id: Mapped[uuid.UUID] = Column(
        SQLUUID(as_uuid=True), ForeignKey("workspaces.id"), unique=True, nullable=False
    )

    # Stripe integration
    stripe_subscription_id: Mapped[Optional[str]] = Column(String(255), unique=True)
    stripe_customer_id: Mapped[str] = Column(String(255), nullable=False)

    # Plan details
    plan_name: Mapped[str] = Column(String(100), nullable=False)
    plan_interval: Mapped[str] = Column(String(20), default="month")  # month, year
    unit_amount: Mapped[int] = Column(Integer, nullable=False)  # Cents
    currency: Mapped[str] = Column(String(3), default="usd")

    # Status
    status: Mapped[str] = Column(String(50), default="incomplete")
    current_period_start: Mapped[Optional[datetime]] = Column(DateTime(timezone=True))
    current_period_end: Mapped[Optional[datetime]] = Column(DateTime(timezone=True))
    cancel_at_period_end: Mapped[bool] = Column(Boolean, default=False)
    canceled_at: Mapped[Optional[datetime]] = Column(DateTime(timezone=True))

    # Trial
    trial_start: Mapped[Optional[datetime]] = Column(DateTime(timezone=True))
    trial_end: Mapped[Optional[datetime]] = Column(DateTime(timezone=True))

    # Metadata
    created_at: Mapped[datetime] = Column(DateTime(timezone=True), server_default=text("NOW()"))
    updated_at: Mapped[datetime] = Column(DateTime(timezone=True), server_default=text("NOW()"))

    # Relationships
    workspace: Mapped["Workspace"] = relationship("Workspace")


class AuditLog(Base):
    """Audit log for compliance"""

    __tablename__ = "audit_log"

    id: Mapped[uuid.UUID] = Column(SQLUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workspace_id: Mapped[Optional[uuid.UUID]] = Column(
        SQLUUID(as_uuid=True), ForeignKey("workspaces.id")
    )

    # Event details
    event_type: Mapped[str] = Column(String(100), nullable=False)
    event_description: Mapped[Optional[str]] = Column(Text)
    severity: Mapped[str] = Column(String(20), default="info")

    # Actor
    actor_type: Mapped[str] = Column(String(50), nullable=False)
    actor_id: Mapped[Optional[str]] = Column(String(255))
    actor_ip: Mapped[Optional[str]] = Column(INET)

    # Resource
    resource_type: Mapped[Optional[str]] = Column(String(100))
    resource_id: Mapped[Optional[str]] = Column(String(255))

    # Event data
    old_values: Mapped[Optional[Dict[str, Any]]] = Column(JSON)
    new_values: Mapped[Optional[Dict[str, Any]]] = Column(JSON)
    event_metadata: Mapped[Dict[str, Any]] = Column(JSON, default=dict)

    # Compliance
    gdpr_processing: Mapped[bool] = Column(Boolean, default=False)
    data_subject_id: Mapped[Optional[str]] = Column(String(255))

    # Timestamp
    # Timestamp
    created_at: Mapped[datetime] = Column(DateTime(timezone=True), server_default=text("NOW()"))


class ChatSession(Base):
    """Chat session history"""

    __tablename__ = "chat_sessions"

    id: Mapped[uuid.UUID] = Column(SQLUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workspace_id: Mapped[Optional[uuid.UUID]] = Column(
        SQLUUID(as_uuid=True), ForeignKey("workspaces.id")
    )
    user_id: Mapped[Optional[uuid.UUID]] = Column(SQLUUID(as_uuid=True), ForeignKey("users.id"))

    title: Mapped[Optional[str]] = Column(String(255))
    model_used: Mapped[str] = Column(String(100), default="gemini-3-pro-preview")

    # Metadata
    created_at: Mapped[datetime] = Column(DateTime(timezone=True), server_default=text("NOW()"))
    updated_at: Mapped[datetime] = Column(DateTime(timezone=True), server_default=text("NOW()"))

    # Relationships
    messages: Mapped[List["ChatMessage"]] = relationship(
        "ChatMessage",
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="ChatMessage.created_at",
    )


class ChatMessage(Base):
    """Individual chat message"""

    __tablename__ = "chat_messages"

    id: Mapped[uuid.UUID] = Column(SQLUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = Column(
        SQLUUID(as_uuid=True), ForeignKey("chat_sessions.id"), nullable=False
    )

    role: Mapped[str] = Column(String(20), nullable=False)  # user, assistant, system
    content: Mapped[str] = Column(Text, nullable=False)

    # Token usage (optional)
    tokens_count: Mapped[Optional[int]] = Column(Integer)

    created_at: Mapped[datetime] = Column(DateTime(timezone=True), server_default=text("NOW()"))

    # Relationships
    session: Mapped["ChatSession"] = relationship("ChatSession", back_populates="messages")


# Indexes for performance
Index("idx_workspaces_slug", Workspace.slug)
Index("idx_users_auth_id", User.auth_id)
Index("idx_users_workspace_id", User.workspace_id)
Index("idx_agents_workspace_id", Agent.workspace_id)
Index("idx_agents_api_key_hash", Agent.api_key_hash)
Index("idx_knowledge_workspace_id", KnowledgeEntry.workspace_id)
Index("idx_usage_workspace_period", UsageRecord.workspace_id, UsageRecord.billing_period)
Index("idx_audit_workspace_created", AuditLog.workspace_id, AuditLog.created_at.desc())
Index("idx_chat_sessions_user", ChatSession.user_id, ChatSession.updated_at.desc())
Index("idx_chat_messages_session", ChatMessage.session_id, ChatMessage.created_at)


# =============================================================================
# Pydantic Schemas
# =============================================================================


class WorkspaceBase(BaseModel):
    name: str = Field(..., max_length=255)
    slug: str = Field(..., max_length=100)
    description: Optional[str] = None


class WorkspaceCreate(WorkspaceBase):
    pass


class WorkspaceUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    subscription_plan: Optional[str] = None
    monthly_token_limit: Optional[int] = None
    storage_limit_gb: Optional[int] = None


class Workspace(WorkspaceBase):
    id: uuid.UUID
    subscription_plan: str
    monthly_token_limit: int
    storage_limit_gb: int
    created_at: datetime
    updated_at: datetime
    is_active: bool

    class Config:
        from_attributes = True
        arbitrary_types_allowed = True


class UserBase(BaseModel):
    email: str = Field(..., max_length=255)
    first_name: Optional[str] = Field(None, max_length=255)
    last_name: Optional[str] = Field(None, max_length=255)
    username: Optional[str] = Field(None, max_length=100)
    avatar_url: Optional[str] = None


class UserCreate(UserBase):
    auth_id: str = Field(..., max_length=255)
    workspace_id: Optional[uuid.UUID] = None


class UserUpdate(BaseModel):
    first_name: Optional[str] = Field(None, max_length=255)
    last_name: Optional[str] = Field(None, max_length=255)
    username: Optional[str] = Field(None, max_length=100)
    avatar_url: Optional[str] = None
    preferences: Optional[Dict[str, Any]] = None
    timezone: Optional[str] = None
    language: Optional[str] = None


class User(UserBase):
    id: uuid.UUID
    auth_id: str
    workspace_id: Optional[uuid.UUID]
    role: str
    preferences: Dict[str, Any]
    timezone: str
    language: str
    last_login_at: Optional[datetime]
    login_count: int
    mfa_enabled: bool
    created_at: datetime
    updated_at: datetime
    is_active: bool

    class Config:
        from_attributes = True
        arbitrary_types_allowed = True


class AgentBase(BaseModel):
    agent_name: str = Field(..., max_length=255)
    agent_type: str = "generic"
    description: Optional[str] = None
    scopes: List[str] = ["read:memory", "write:logs"]
    daily_token_budget: int = 1000


class AgentCreate(AgentBase):
    workspace_id: uuid.UUID


class AgentUpdate(BaseModel):
    agent_name: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    scopes: Optional[List[str]] = None
    daily_token_budget: Optional[int] = None
    system_prompt: Optional[str] = None
    model_preferences: Optional[Dict[str, Any]] = None
    custom_instructions: Optional[str] = None


class Agent(AgentBase):
    id: uuid.UUID
    workspace_id: uuid.UUID
    is_active: bool
    last_seen_at: Optional[datetime]
    total_tokens_used: int
    system_prompt: Optional[str]
    model_preferences: Dict[str, Any]
    custom_instructions: Optional[str]
    created_at: datetime
    updated_at: datetime
    created_by: Optional[uuid.UUID]

    class Config:
        from_attributes = True
        arbitrary_types_allowed = True


class KnowledgeEntryBase(BaseModel):
    content_type: str = Field(..., max_length=50)
    title: Optional[str] = Field(None, max_length=500)
    content: str
    metadata: Dict[str, Any] = {}
    access_level: str = "workspace"


class KnowledgeEntryCreate(KnowledgeEntryBase):
    workspace_id: uuid.UUID
    owner_id: Optional[uuid.UUID] = None


class KnowledgeEntryUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=500)
    content: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    access_level: Optional[str] = None


class KnowledgeEntry(KnowledgeEntryBase):
    id: uuid.UUID
    workspace_id: uuid.UUID
    vector_id: Optional[str]
    embedding_model: str
    content_hash: Optional[str]
    owner_id: Optional[uuid.UUID]
    is_encrypted: bool
    encryption_key_version: int
    created_at: datetime
    updated_at: datetime
    created_by: Optional[uuid.UUID]
    last_accessed_at: Optional[datetime]

    class Config:
        from_attributes = True
        arbitrary_types_allowed = True
