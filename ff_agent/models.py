from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class AgentStatus(str, Enum):
    """Current state of the File & Folder Agent."""

    READY = "ready"
    CLARIFICATION_REQUIRED = "clarification_required"
    CONFIRMATION_REQUIRED = "confirmation_required"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"


class RiskLevel(str, Enum):
    """Risk classification for filesystem operations."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass
class AgentContext:
    """
    Normalized context used by the File & Folder Agent.

    The entities dictionary is intentionally preserved because the
    existing ASTRA planner/entity extraction pipeline already produces
    structured entity data.
    """

    command: str
    intent: str
    entities: dict[str, Any] = field(default_factory=dict)

    source: str | None = None
    destination: str | None = None
    target: str | None = None

    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ResolutionResult:
    """Result returned after resolving filesystem context."""

    success: bool
    context: AgentContext

    message: str = ""

    needs_clarification: bool = False
    clarification_type: str | None = None

    candidates: list[dict[str, Any]] = field(default_factory=list)
    missing_fields: list[str] = field(default_factory=list)

    data: dict[str, Any] = field(default_factory=dict)


@dataclass
class ExecutionStep:
    """One logical step prepared before execution."""

    name: str
    action: str
    parameters: dict[str, Any] = field(default_factory=dict)


@dataclass
class ExecutionPlan:
    """Filesystem execution plan."""

    intent: str
    steps: list[ExecutionStep] = field(default_factory=list)

    risk_level: RiskLevel = RiskLevel.LOW
    requires_confirmation: bool = False

    message: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class SafetyResult:
    """Safety evaluation before execution."""

    allowed: bool
    risk_level: RiskLevel

    requires_confirmation: bool = False
    message: str = ""

    conflicts: list[dict[str, Any]] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


@dataclass
class VerificationResult:
    """Verification result after filesystem execution."""

    success: bool
    message: str = ""

    verified_items: list[str] = field(default_factory=list)
    failed_items: list[str] = field(default_factory=list)

    data: dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentResult:
    """
    Final response returned by the File & Folder Agent.

    This structure is intentionally flexible so CommandDispatcher and
    UI layers can convert it into their existing response format.
    """

    success: bool
    status: AgentStatus

    message: str = ""

    intent: str | None = None
    data: dict[str, Any] = field(default_factory=dict)

    candidates: list[dict[str, Any]] = field(default_factory=list)

    requires_confirmation: bool = False
    requires_clarification: bool = False

    plan: ExecutionPlan | None = None

    error: str | None = None