"""
ASTRA-AI Action Models

Defines the standard data structures used by the
multi-command planning and execution system.

ASTRA-AI V1
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class ActionStatus(str, Enum):
    """
    Execution status of an individual action step.
    """

    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class ActionStep:
    """
    Represents one executable action inside a
    multi-command plan.

    Example:

        ActionStep(
            action="google_search",
            parameters={
                "query": "Sona College website"
            }
        )
    """

    action: str

    parameters: Dict[str, Any] = field(
        default_factory=dict
    )

    step_id: Optional[str] = None

    description: str = ""

    status: ActionStatus = ActionStatus.PENDING

    result: Any = None

    error: Optional[str] = None

    metadata: Dict[str, Any] = field(
        default_factory=dict
    )

    def mark_running(self) -> None:
        """
        Mark this action as currently executing.
        """

        self.status = ActionStatus.RUNNING

        self.error = None

    def mark_success(
        self,
        result: Any = None
    ) -> None:
        """
        Mark this action as successfully completed.
        """

        self.status = ActionStatus.SUCCESS

        self.result = result

        self.error = None

    def mark_failed(
        self,
        error: str
    ) -> None:
        """
        Mark this action as failed.
        """

        self.status = ActionStatus.FAILED

        self.error = str(error)

    def mark_skipped(
        self,
        reason: Optional[str] = None
    ) -> None:
        """
        Mark this action as skipped.
        """

        self.status = ActionStatus.SKIPPED

        if reason:
            self.error = reason

    @property
    def is_complete(self) -> bool:
        """
        Return True when the action reached a terminal state.
        """

        return self.status in {
            ActionStatus.SUCCESS,
            ActionStatus.FAILED,
            ActionStatus.SKIPPED,
        }

    @property
    def is_successful(self) -> bool:
        """
        Return True when the action completed successfully.
        """

        return self.status == ActionStatus.SUCCESS

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the action step into a serializable dictionary.
        """

        return {
            "step_id": self.step_id,
            "action": self.action,
            "parameters": self.parameters,
            "description": self.description,
            "status": self.status.value,
            "result": self.result,
            "error": self.error,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(
        cls,
        data: Dict[str, Any]
    ) -> "ActionStep":
        """
        Create an ActionStep from a dictionary.

        This is useful when Gemini returns a structured
        action plan.
        """

        if not isinstance(data, dict):
            raise TypeError(
                "Action step data must be a dictionary."
            )

        action = data.get("action")

        if not action:
            raise ValueError(
                "Action step is missing 'action'."
            )

        raw_status = data.get(
            "status",
            ActionStatus.PENDING.value
        )

        try:

            status = ActionStatus(raw_status)

        except ValueError:

            status = ActionStatus.PENDING

        parameters = data.get(
            "parameters",
            {}
        )

        if not isinstance(parameters, dict):

            parameters = {}

        metadata = data.get(
            "metadata",
            {}
        )

        if not isinstance(metadata, dict):

            metadata = {}

        return cls(
            action=str(action).strip(),
            parameters=parameters,
            step_id=data.get("step_id"),
            description=str(
                data.get("description", "")
            ),
            status=status,
            result=data.get("result"),
            error=data.get("error"),
            metadata=metadata,
        )


@dataclass
class ActionPlan:
    """
    Represents the complete execution plan for a
    user command.

    Example:

        ActionPlan(
            steps=[
                ActionStep(
                    action="launch_application",
                    parameters={
                        "application": "chrome"
                    }
                ),
                ActionStep(
                    action="google_search",
                    parameters={
                        "query": "Sona College website"
                    }
                ),
                ActionStep(
                    action="click_search_result",
                    parameters={
                        "index": 0
                    }
                ),
            ]
        )
    """

    steps: List[ActionStep] = field(
        default_factory=list
    )

    original_command: str = ""

    plan_id: Optional[str] = None

    description: str = ""

    metadata: Dict[str, Any] = field(
        default_factory=dict
    )

    def add_step(
        self,
        step: ActionStep
    ) -> None:
        """
        Add an action step to the plan.
        """

        if not isinstance(step, ActionStep):

            raise TypeError(
                "Only ActionStep objects can be added."
            )

        self.steps.append(step)

    def get_step(
        self,
        index: int
    ) -> ActionStep:
        """
        Return a step using its zero-based index.
        """

        if index < 0 or index >= len(self.steps):

            raise IndexError(
                f"Action step index out of range: {index}"
            )

        return self.steps[index]

    @property
    def total_steps(self) -> int:
        """
        Return the number of steps in the plan.
        """

        return len(self.steps)

    @property
    def is_multi_step(self) -> bool:
        """
        Return True when the plan contains more than one action.
        """

        return self.total_steps > 1

    @property
    def is_complete(self) -> bool:
        """
        Return True when every step reached a terminal state.
        """

        if not self.steps:
            return True

        return all(
            step.is_complete
            for step in self.steps
        )

    @property
    def is_successful(self) -> bool:
        """
        Return True when every step completed successfully.
        """

        if not self.steps:
            return False

        return all(
            step.is_successful
            for step in self.steps
        )

    @property
    def has_failed(self) -> bool:
        """
        Return True when at least one step failed.
        """

        return any(
            step.status == ActionStatus.FAILED
            for step in self.steps
        )

    def failed_step(self) -> Optional[ActionStep]:
        """
        Return the first failed step, if any.
        """

        for step in self.steps:

            if step.status == ActionStatus.FAILED:

                return step

        return None

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the complete action plan into a
        serializable dictionary.
        """

        return {
            "plan_id": self.plan_id,
            "original_command": self.original_command,
            "description": self.description,
            "steps": [
                step.to_dict()
                for step in self.steps
            ],
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(
        cls,
        data: Dict[str, Any]
    ) -> "ActionPlan":
        """
        Create an ActionPlan from a dictionary.

        Expected structure:

            {
                "original_command": "...",
                "steps": [
                    {
                        "action": "...",
                        "parameters": {}
                    }
                ]
            }
        """

        if not isinstance(data, dict):

            raise TypeError(
                "Action plan data must be a dictionary."
            )

        raw_steps = data.get(
            "steps",
            []
        )

        if not isinstance(raw_steps, list):

            raise ValueError(
                "Action plan 'steps' must be a list."
            )

        steps = []

        for raw_step in raw_steps:

            steps.append(
                ActionStep.from_dict(
                    raw_step
                )
            )

        metadata = data.get(
            "metadata",
            {}
        )

        if not isinstance(metadata, dict):

            metadata = {}

        return cls(
            steps=steps,
            original_command=str(
                data.get(
                    "original_command",
                    ""
                )
            ),
            plan_id=data.get("plan_id"),
            description=str(
                data.get(
                    "description",
                    ""
                )
            ),
            metadata=metadata,
        )

    def reset(self) -> None:
        """
        Reset all steps to pending state.

        Useful when a plan needs to be executed again.
        """

        for step in self.steps:

            step.status = ActionStatus.PENDING
            step.result = None
            step.error = None


__all__ = [
    "ActionStatus",
    "ActionStep",
    "ActionPlan",
]