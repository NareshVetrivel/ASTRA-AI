from __future__ import annotations

from pathlib import Path
from typing import Any

from ff_agent.models import AgentContext, VerificationResult


class ExecutionVerifier:
    """
    Verifies the result of file and folder operations.

    The verifier is independent from the execution engine so the agent
    can confirm the actual filesystem state.
    """

    def verify(
        self,
        context: AgentContext,
        execution_result: Any,
    ) -> VerificationResult:
        """
        Verify the operation using both the executor result and the
        current filesystem state.
        """

        if not self._execution_succeeded(execution_result):
            return VerificationResult(
                success=False,
                message="The filesystem operation reported a failure.",
                failed_items=self._extract_failed_items(
                    execution_result
                ),
                data={
                    "execution_result": execution_result,
                },
            )

        verifier = self._get_verifier(context.intent)

        return verifier(context, execution_result)

    def _get_verifier(self, intent: str):
        """Return the correct verification method."""

        if intent in {
            "create_file",
            "create_folder",
        }:
            return self._verify_creation

        if intent in {
            "move_file",
            "move_folder",
        }:
            return self._verify_move

        if intent in {
            "copy_file",
            "copy_folder",
        }:
            return self._verify_copy

        if intent in {
            "rename_file",
            "rename_folder",
        }:
            return self._verify_rename

        if intent in {
            "delete_file",
            "delete_folder",
        }:
            return self._verify_deletion

        return self._verify_generic

    def _execution_succeeded(
        self,
        result: Any,
    ) -> bool:
        """Read success from the existing executor result."""

        if isinstance(result, dict):
            return bool(
                result.get(
                    "success",
                    result.get("ok", False),
                )
            )

        success = getattr(result, "success", None)

        if success is not None:
            return bool(success)

        return bool(result)

    def _verify_creation(
        self,
        context: AgentContext,
        execution_result: Any,
    ) -> VerificationResult:
        """Verify that a created item now exists."""

        path = self._extract_result_path(
            execution_result,
            fallback=context.target,
        )

        if path and Path(path).exists():
            return VerificationResult(
                success=True,
                message="Creation verified successfully.",
                verified_items=[str(path)],
            )

        return VerificationResult(
            success=False,
            message=(
                "The operation reported success, but the created "
                "item could not be verified."
            ),
        )

    def _verify_move(
        self,
        context: AgentContext,
        execution_result: Any,
    ) -> VerificationResult:
        """Verify source removal and destination existence."""

        source = context.source or context.target
        destination = self._extract_result_path(execution_result)

        if not destination and source and context.destination:
            destination = str(
                Path(context.destination) / Path(source).name
            )

        if (
            destination
            and Path(destination).exists()
            and (
                not source
                or not Path(source).exists()
            )
        ):
            return VerificationResult(
                success=True,
                message="Move verified successfully.",
                verified_items=[str(destination)],
            )

        return VerificationResult(
            success=False,
            message=(
                "The operation reported success, but the move "
                "could not be fully verified."
            ),
            failed_items=[str(source)] if source else [],
        )

    def _verify_copy(
        self,
        context: AgentContext,
        execution_result: Any,
    ) -> VerificationResult:
        """Verify destination existence while preserving source."""

        source = context.source or context.target
        destination = self._extract_result_path(execution_result)

        if not destination and source and context.destination:
            destination = str(
                Path(context.destination) / Path(source).name
            )

        if (
            destination
            and Path(destination).exists()
            and (
                not source
                or Path(source).exists()
            )
        ):
            return VerificationResult(
                success=True,
                message="Copy verified successfully.",
                verified_items=[str(destination)],
            )

        return VerificationResult(
            success=False,
            message=(
                "The operation reported success, but the copy "
                "could not be fully verified."
            ),
        )

    def _verify_rename(
        self,
        context: AgentContext,
        execution_result: Any,
    ) -> VerificationResult:
        """Verify that the renamed path exists."""

        path = self._extract_result_path(execution_result)

        if path and Path(path).exists():
            return VerificationResult(
                success=True,
                message="Rename verified successfully.",
                verified_items=[str(path)],
            )

        return VerificationResult(
            success=False,
            message=(
                "The operation reported success, but the rename "
                "could not be verified."
            ),
        )

    def _verify_deletion(
        self,
        context: AgentContext,
        execution_result: Any,
    ) -> VerificationResult:
        """Verify that the deleted item no longer exists."""

        target = context.target or context.source

        if target and not Path(target).exists():
            return VerificationResult(
                success=True,
                message="Deletion verified successfully.",
                verified_items=[str(target)],
            )

        return VerificationResult(
            success=False,
            message=(
                "The operation reported success, but the target "
                "still exists."
            ),
            failed_items=[str(target)] if target else [],
        )

    def _verify_generic(
        self,
        context: AgentContext,
        execution_result: Any,
    ) -> VerificationResult:
        """Fallback verification for other operations."""

        return VerificationResult(
            success=True,
            message="Operation completed successfully.",
            data={
                "execution_result": execution_result,
            },
        )

    def _extract_result_path(
        self,
        result: Any,
        fallback: str | None = None,
    ) -> str | None:
        """Extract a resulting filesystem path from executor data."""

        if isinstance(result, dict):
            for key in (
                "path",
                "result_path",
                "destination",
                "destination_path",
                "new_path",
            ):
                value = result.get(key)

                if isinstance(value, str) and value.strip():
                    return value

            data = result.get("data")

            if isinstance(data, dict):
                return self._extract_result_path(
                    data,
                    fallback,
                )

        for attribute in (
            "path",
            "result_path",
            "destination",
            "destination_path",
            "new_path",
        ):
            value = getattr(result, attribute, None)

            if isinstance(value, str) and value.strip():
                return value

        return fallback

    def _extract_failed_items(
        self,
        result: Any,
    ) -> list[str]:
        """Extract failed items from executor result."""

        if isinstance(result, dict):
            items = result.get("failed_items")

            if isinstance(items, list):
                return [str(item) for item in items]

        return []