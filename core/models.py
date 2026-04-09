from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class CasePriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class CaseStatus(str, Enum):
    CREATED = "created"
    ACCEPTED = "accepted"
    PLANNING = "planning"
    INTERNAL_REVIEW = "internal_review"
    SUBMITTED_FOR_APPROVAL = "submitted_for_approval"
    APPROVED = "approved"
    REJECTED = "rejected"
    ESCALATED = "escalated"
    DISPATCHED = "dispatched"
    EXECUTING = "executing"
    REPORTING = "reporting"
    ARCHIVED = "archived"
    PAUSED = "paused"
    FROZEN = "frozen"
    CANCELLED = "cancelled"
    REPAIR_PENDING = "repair_pending"
    REPAIR_AUTHORIZED = "repair_authorized"
    RERUNNING = "rerunning"


class GovernanceLayer(str, Enum):
    PERSONAL = "personal"
    DEPARTMENT = "department"
    COMPANY = "company"


class TimelineEvent(BaseModel):
    event_id: str
    event_type: str
    actor: str = "system"
    from_status: CaseStatus | None = None
    to_status: CaseStatus | None = None
    message: str | None = None
    payload: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utc_now)


class CaseRecord(BaseModel):
    case_id: str
    title: str
    content: str
    priority: CasePriority = CasePriority.MEDIUM
    submitted_by: str
    layer: GovernanceLayer = GovernanceLayer.PERSONAL
    status: CaseStatus = CaseStatus.CREATED
    metadata: dict[str, Any] = Field(default_factory=dict)
    timeline: list[TimelineEvent] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class CreateCaseRequest(BaseModel):
    title: str
    content: str
    priority: CasePriority = CasePriority.MEDIUM
    submitted_by: str
    layer: GovernanceLayer = GovernanceLayer.PERSONAL
    metadata: dict[str, Any] = Field(default_factory=dict)


class ActionRequest(BaseModel):
    reason: str | None = None
    actor: str = "system"


class RepairOrderRequest(BaseModel):
    strategy: str
    reason: str
    scope: str
    actor: str = "company_silijian"


class AgentProfile(BaseModel):
    agent_id: str
    name: str
    layer: GovernanceLayer
    office: str
    duty: str
    deployment_hint: str


class RuntimeCapability(BaseModel):
    agent_id: str
    preferred_backend: str
    supported_backends: list[str]
    notes: str

