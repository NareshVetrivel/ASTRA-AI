from __future__ import annotations

from typing import Any

from ff_agent.models import (
    AgentContext,
    ExecutionPlan,
    ExecutionStep,
    RiskLevel,
)


class FileFolderPlanner:
    """
    Builds a lightweight execution plan for file and folder operations.

    The planner does not execute filesystem operations. Existing
    ASTRA automation components remain responsible for execution.
    """

    HIGH_RISK_INTENTS = {
        "delete_file",
        "delete_folder",
    }

    MEDIUM_RISK_INTENTS = {
        "move_file",
        "move_folder",
        "copy_file",
        "copy_folder",
        "rename_file",
        "rename_folder",
    }

    def create_plan(self, context: AgentContext) -> ExecutionPlan:
        """
        Create an execution plan from resolved agent context.
        """

        risk_level = self._get_risk_level(context.intent)
        requires_confirmation = (
            risk_level == RiskLevel.HIGH
        )

        steps = self._build_steps(context)

        return ExecutionPlan(
            intent=context.intent,
            steps=steps,
            risk_level=risk_level,
            requires_confirmation=requires_confirmation,
            message=self._build_plan_message(
                context,
                steps,
            ),
            metadata={
                "command": context.command,
                "source": context.source,
                "destination": context.destination,
                "target": context.target,
                "entities": context.entities,
            },
        )

    def _get_risk_level(self, intent: str) -> RiskLevel:
        """Determine the filesystem risk level."""

        if intent in self.HIGH_RISK_INTENTS:
            return RiskLevel.HIGH

        if intent in self.MEDIUM_RISK_INTENTS:
            return RiskLevel.MEDIUM

        return RiskLevel.LOW

    def _build_steps(
        self,
        context: AgentContext,
    ) -> list[ExecutionStep]:
        """
        Build logical execution steps.

        These steps describe what should happen. Actual execution is
        delegated to the existing FileSystemAgent.
        """

        intent = context.intent

        parameters = self._build_parameters(context)

        if intent == "create_file":
            return [
                ExecutionStep(
                    name="validate_target",
                    action="validate",
                    parameters=parameters,
                ),
                ExecutionStep(
                    name="create_file",
                    action="execute",
                    parameters=parameters,
                ),
                ExecutionStep(
                    name="verify_file",
                    action="verify",
                    parameters=parameters,
                ),
            ]

        if intent == "create_folder":
            return [
                ExecutionStep(
                    name="validate_target",
                    action="validate",
                    parameters=parameters,
                ),
                ExecutionStep(
                    name="create_folder",
                    action="execute",
                    parameters=parameters,
                ),
                ExecutionStep(
                    name="verify_folder",
                    action="verify",
                    parameters=parameters,
                ),
            ]

        if intent in {
            "move_file",
            "move_folder",
            "copy_file",
            "copy_folder",
        }:
            return [
                ExecutionStep(
                    name="validate_source",
                    action="validate",
                    parameters=parameters,
                ),
                ExecutionStep(
                    name="validate_destination",
                    action="validate",
                    parameters=parameters,
                ),
                ExecutionStep(
                    name=intent,
                    action="execute",
                    parameters=parameters,
                ),
                ExecutionStep(
                    name="verify_result",
                    action="verify",
                    parameters=parameters,
                ),
            ]

        if intent in {
            "rename_file",
            "rename_folder",
        }:
            return [
                ExecutionStep(
                    name="validate_target",
                    action="validate",
                    parameters=parameters,
                ),
                ExecutionStep(
                    name="validate_new_name",
                    action="validate",
                    parameters=parameters,
                ),
                ExecutionStep(
                    name=intent,
                    action="execute",
                    parameters=parameters,
                ),
                ExecutionStep(
                    name="verify_rename",
                    action="verify",
                    parameters=parameters,
                ),
            ]

        if intent in {
            "delete_file",
            "delete_folder",
        }:
            return [
                ExecutionStep(
                    name="validate_target",
                    action="validate",
                    parameters=parameters,
                ),
                ExecutionStep(
                    name="confirm_deletion",
                    action="confirm",
                    parameters=parameters,
                ),
                ExecutionStep(
                    name=intent,
                    action="execute",
                    parameters=parameters,
                ),
                ExecutionStep(
                    name="verify_deletion",
                    action="verify",
                    parameters=parameters,
                ),
            ]

        if intent in {
            "search_file",
            "search_folder",
        }:
            return [
                ExecutionStep(
                    name="prepare_search",
                    action="validate",
                    parameters=parameters,
                ),
                ExecutionStep(
                    name=intent,
                    action="execute",
                    parameters=parameters,
                ),
            ]

        return [
            ExecutionStep(
                name="execute_operation",
                action="execute",
                parameters=parameters,
            )
        ]

    def _build_parameters(
        self,
        context: AgentContext,
    ) -> dict[str, Any]:
        """
        Preserve all resolved context and upstream entities.
        """

        parameters = {
            "source": context.source,
            "destination": context.destination,
            "target": context.target,
        }

        parameters.update(context.entities)

        return parameters

    def _build_plan_message(
        self,
        context: AgentContext,
        steps: list[ExecutionStep],
    ) -> str:
        """Build a human-readable execution plan summary."""

        step_names = ", ".join(
            step.name.replace("_", " ")
            for step in steps
        )

        return (
            f"Prepared a plan for "
            f"{context.intent.replace('_', ' ')}: "
            f"{step_names}."
        )