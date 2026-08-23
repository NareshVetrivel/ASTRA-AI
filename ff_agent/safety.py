from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from ff_agent.models import (
    AgentContext,
    ExecutionPlan,
    RiskLevel,
    SafetyResult,
)


class SafetyManager:
    """
    Performs lightweight safety checks before filesystem execution.

    This layer does not replace the protection already present in
    FileManager and FolderManager. It provides an additional
    agent-level guard before execution.
    """

    DESTRUCTIVE_INTENTS = {
        "delete_file",
        "delete_folder",
    }

    MOVE_COPY_INTENTS = {
        "move_file",
        "move_folder",
        "copy_file",
        "copy_folder",
    }

    def evaluate(
        self,
        context: AgentContext,
        plan: ExecutionPlan,
    ) -> SafetyResult:
        """
        Evaluate whether the operation is safe to execute.
        """

        warnings: list[str] = []
        conflicts: list[dict[str, Any]] = []

        protected_reason = self._check_protected_paths(context)

        if protected_reason:
            return SafetyResult(
                allowed=False,
                risk_level=RiskLevel.HIGH,
                requires_confirmation=False,
                message=protected_reason,
                warnings=[protected_reason],
            )

        if context.intent in self.DESTRUCTIVE_INTENTS:
            return SafetyResult(
                allowed=True,
                risk_level=RiskLevel.HIGH,
                requires_confirmation=True,
                message=(
                    "This operation will permanently delete "
                    "a file or folder. Confirmation is required."
                ),
            )

        if context.intent in self.MOVE_COPY_INTENTS:
            conflict = self._check_destination_conflict(context)

            if conflict:
                conflicts.append(conflict)
                warnings.append(
                    "A file or folder with the same name already "
                    "exists at the destination."
                )

        requires_confirmation = (
            plan.requires_confirmation
            or bool(conflicts)
        )

        message = (
            "Safety checks completed successfully."
        )

        if conflicts:
            message = (
                "Safety checks found destination conflicts. "
                "Confirmation is required before continuing."
            )

        return SafetyResult(
            allowed=True,
            risk_level=plan.risk_level,
            requires_confirmation=requires_confirmation,
            message=message,
            conflicts=conflicts,
            warnings=warnings,
        )

    def _check_protected_paths(
        self,
        context: AgentContext,
    ) -> str | None:
        """
        Prevent obviously dangerous operations on filesystem roots
        and critical Windows directories.
        """

        paths = [
            context.source,
            context.destination,
            context.target,
        ]

        for raw_path in paths:
            if not raw_path:
                continue

            try:
                path = Path(
                    os.path.abspath(raw_path)
                )
            except (OSError, ValueError):
                continue

            path_string = str(path).lower()

            if self._is_filesystem_root(path):
                return (
                    "For safety, operations on a filesystem root "
                    "are not allowed."
                )

            protected_locations = (
                "\\windows",
                "\\program files",
                "\\program files (x86)",
            )

            for location in protected_locations:
                if (
                    path_string == location
                    or path_string.startswith(location + "\\")
                ):
                    return (
                        "For safety, operations on protected system "
                        "directories are not allowed."
                    )

        return None

    def _is_filesystem_root(
        self,
        path: Path,
    ) -> bool:
        """Return True when the path is a filesystem root."""

        return path == path.anchor

    def _check_destination_conflict(
        self,
        context: AgentContext,
    ) -> dict[str, Any] | None:
        """
        Detect an existing item with the same source name
        in the destination directory.
        """

        if not context.destination:
            return None

        source = (
            context.source
            or context.target
        )

        if not source:
            return None

        try:
            source_path = Path(source)
            destination_path = Path(context.destination)

            if not destination_path.exists():
                return None

            conflict_path = (
                destination_path / source_path.name
            )

            if conflict_path.exists():
                return {
                    "source": str(source_path),
                    "destination": str(destination_path),
                    "conflict_path": str(conflict_path),
                }

        except (OSError, ValueError):
            return None

        return None