from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

from ff_agent.context_resolver import ContextResolver
from ff_agent.models import (
    AgentContext,
    AgentResult,
    AgentStatus,
)
from ff_agent.planner import FileFolderPlanner
from ff_agent.safety import SafetyManager
from ff_agent.verifier import ExecutionVerifier


class FileFolderAgent:
    """
    Smart orchestration layer for ASTRA-AI file and folder automation.

    Flow for operations that can affect existing files/folders:

        command
            -> context resolution
            -> candidate selection
            -> exact path resolution
            -> confirmation
            -> execution
            -> verification

    Existing FileSystemAgent remains responsible for the actual
    filesystem operation.
    """

    SELECTION_INTENTS = {
        "rename_file",
        "rename_folder",
        "copy_file",
        "copy_folder",
        "move_file",
        "move_folder",
        "delete_file",
        "delete_folder",
        "compress_file",
        "compress_zip",
        "extract_zip",
        "unzip",
    }

    CONFIRMATION_INTENTS = {
        "rename_file",
        "rename_folder",
        "copy_file",
        "copy_folder",
        "move_file",
        "move_folder",
        "delete_file",
        "delete_folder",
        "compress_file",
        "compress_zip",
        "extract_zip",
        "unzip",
    }

    FILE_INTENTS = {
        "rename_file",
        "copy_file",
        "move_file",
        "delete_file",
        "compress_file",
        "compress_zip",
        "extract_zip",
        "unzip",
    }

    FOLDER_INTENTS = {
        "rename_folder",
        "copy_folder",
        "move_folder",
        "delete_folder",
    }

    def __init__(
        self,
        file_system_agent: Any,
        context_resolver: ContextResolver | None = None,
        planner: FileFolderPlanner | None = None,
        safety_manager: SafetyManager | None = None,
        verifier: ExecutionVerifier | None = None,
    ) -> None:
        self.file_system_agent = file_system_agent

        self.context_resolver = (
            context_resolver
            or ContextResolver()
        )

        self.planner = (
            planner
            or FileFolderPlanner()
        )

        self.safety_manager = (
            safety_manager
            or SafetyManager()
        )

        self.verifier = (
            verifier
            or ExecutionVerifier()
        )

    def execute(
        self,
        command: str,
        intent: str,
        entities: dict[str, Any] | None = None,
        *,
        confirmed: bool = False,
    ) -> AgentResult:
        """
        Execute a file or folder operation.

        Important selection flow:

            1. First request -> FileSystemAgent returns candidates.
            2. User selects an option.
            3. Agent resolves the selected item to an exact path.
            4. Agent asks for confirmation.
            5. Only confirmed=True performs the operation.
        """

        entities = dict(entities or {})

        intent = (
            str(intent or "")
            .strip()
            .lower()
        )

        try:
            # ==================================================
            # 1. CONTEXT RESOLUTION
            # ==================================================

            resolution = (
                self.context_resolver.resolve(
                    command=command,
                    intent=intent,
                    entities=entities,
                )
            )

            if not resolution.success:
                return self._clarification_result(
                    intent=intent,
                    message=resolution.message,
                    candidates=resolution.candidates,
                    missing_fields=(
                        resolution.missing_fields
                    ),
                    clarification_type=(
                        resolution.clarification_type
                    ),
                )

            context = resolution.context

            # ==================================================
            # 2. CANDIDATE SELECTION
            #
            # Selection must happen BEFORE confirmation.
            # ==================================================

            selection = self._get_selection(
                context.entities
            )

            if (
                intent in self.SELECTION_INTENTS
                and selection is None
                and not self._has_exact_target_path(
                    context,
                    intent,
                )
            ):
                selection_result = (
                    self._delegate_execution(
                        command=command,
                        intent=intent,
                        entities=context.entities,
                        context=context,
                        preflight=True,
                    )
                )

                # ----------------------------------------------
                # FileSystemAgent found multiple candidates
                # ----------------------------------------------

                if self._requires_selection(
                    selection_result
                ):
                    return self._clarification_result(
                        intent=intent,
                        message=(
                            selection_result.get(
                                "message"
                            )
                            or
                            "Please select the correct "
                            "file or folder."
                        ),
                        candidates=(
                            self._extract_candidates(
                                selection_result
                            )
                        ),
                        clarification_type=(
                            "ambiguous_target"
                        ),
                        data={
                            "selection_required": True,
                            "original_entities": dict(
                                context.entities
                            ),
                        },
                    )

                # ----------------------------------------------
                # Real failure during selection stage
                # ----------------------------------------------

                if not self._execution_succeeded(
                    selection_result
                ):
                    return (
                        self._execution_failure_result(
                            intent=intent,
                            result=selection_result,
                        )
                    )

                # ----------------------------------------------
                # Keep exact path if safely returned
                # ----------------------------------------------

                selected_path = (
                    self._extract_result_path(
                        selection_result
                    )
                )

                if selected_path:
                    self._apply_resolved_path(
                        context,
                        intent,
                        selected_path,
                    )

            # ==================================================
            # 3. UI ALREADY SENT FULL PATH
            #
            # Remove old option number because FileSystemAgent
            # would otherwise try to apply selection again.
            # ==================================================

            if (
                intent in self.SELECTION_INTENTS
                and selection is not None
                and self._has_exact_target_path(
                    context,
                    intent,
                )
            ):
                self._remove_selection_keys(
                    context.entities
                )

            # ==================================================
            # 4. USER SELECTED OPTION NUMBER
            #
            # Convert option number to exact filesystem path.
            # ==================================================

            if (
                intent in self.SELECTION_INTENTS
                and selection is not None
                and not self._has_exact_target_path(
                    context,
                    intent,
                )
            ):
                selected_path = (
                    self._resolve_selected_path(
                        context=context,
                        intent=intent,
                        selection=selection,
                    )
                )

                if selected_path is None:
                    return self._clarification_result(
                        intent=intent,
                        message=(
                            "The selected option is no longer "
                            "valid. Please select again."
                        ),
                        candidates=(
                            self._find_candidates(
                                context=context,
                                intent=intent,
                            )
                        ),
                        clarification_type=(
                            "invalid_selection"
                        ),
                        data={
                            "selection_required": True,
                            "original_entities": dict(
                                context.entities
                            ),
                        },
                    )

                self._apply_resolved_path(
                    context,
                    intent,
                    selected_path,
                )

                # Exact path is now resolved.
                # Do not send stale numeric selection again.
                self._remove_selection_keys(
                    context.entities
                )

            # ==================================================
            # 5. BUILD EXECUTION PLAN
            # ==================================================

            plan = self.planner.create_plan(
                context
            )

            # ==================================================
            # 6. SAFETY VALIDATION
            # ==================================================

            safety_result = (
                self.safety_manager.evaluate(
                    context=context,
                    plan=plan,
                )
            )

            if not safety_result.allowed:
                return AgentResult(
                    success=False,
                    status=AgentStatus.FAILED,
                    message=safety_result.message,
                    intent=intent,
                    data={
                        "warnings": (
                            safety_result.warnings
                        ),
                        "conflicts": (
                            safety_result.conflicts
                        ),
                        "risk_level": (
                            safety_result
                            .risk_level
                            .value
                        ),
                    },
                    error=safety_result.message,
                    plan=plan,
                )

            # ==================================================
            # 7. CONFIRMATION
            #
            # IMPORTANT:
            # Candidate selection is already completed before
            # reaching this block.
            # ==================================================

            requires_confirmation = (
                safety_result.requires_confirmation
                or
                intent in self.CONFIRMATION_INTENTS
            )

            if (
                requires_confirmation
                and not confirmed
            ):
                return AgentResult(
                    success=False,
                    status=(
                        AgentStatus
                        .CONFIRMATION_REQUIRED
                    ),
                    message=(
                        self._build_confirmation_message(
                            context=context,
                            safety_message=(
                                safety_result.message
                            ),
                        )
                    ),
                    intent=intent,
                    data={
                        "warnings": (
                            safety_result.warnings
                        ),
                        "conflicts": (
                            safety_result.conflicts
                        ),
                        "risk_level": (
                            safety_result
                            .risk_level
                            .value
                        ),
                        "confirmation_required": True,
                        "entities": dict(
                            context.entities
                        ),
                        "source": context.source,
                        "destination": (
                            context.destination
                        ),
                        "target": context.target,
                    },
                    requires_confirmation=True,
                    plan=plan,
                )

            # ==================================================
            # 8. REAL EXECUTION
            # ==================================================

            execution_result = (
                self._delegate_execution(
                    command=command,
                    intent=intent,
                    entities=context.entities,
                    context=context,
                )
            )

            # ----------------------------------------------
            # Defensive selection handling
            # ----------------------------------------------

            if self._requires_selection(
                execution_result
            ):
                return self._clarification_result(
                    intent=intent,
                    message=(
                        execution_result.get(
                            "message"
                        )
                        or
                        "Please select the correct "
                        "file or folder."
                    ),
                    candidates=(
                        self._extract_candidates(
                            execution_result
                        )
                    ),
                    clarification_type=(
                        "ambiguous_target"
                    ),
                    data={
                        "selection_required": True,
                        "original_entities": dict(
                            context.entities
                        ),
                    },
                )

            # ==================================================
            # 9. VERIFY RESULT
            # ==================================================

            verification = self.verifier.verify(
                context=context,
                execution_result=execution_result,
            )

            if not verification.success:
                return AgentResult(
                    success=False,
                    status=AgentStatus.FAILED,
                    message=verification.message,
                    intent=intent,
                    data={
                        "execution_result": (
                            execution_result
                        ),
                        "verified_items": (
                            verification
                            .verified_items
                        ),
                        "failed_items": (
                            verification
                            .failed_items
                        ),
                        "verification": (
                            verification.data
                        ),
                    },
                    error=verification.message,
                    plan=plan,
                )

            # ==================================================
            # 10. SUCCESS
            # ==================================================

            return AgentResult(
                success=True,
                status=AgentStatus.COMPLETED,
                message=verification.message,
                intent=intent,
                data={
                    "execution_result": (
                        execution_result
                    ),
                    "verified_items": (
                        verification.verified_items
                    ),
                    "verification": (
                        verification.data
                    ),
                    "risk_level": (
                        safety_result
                        .risk_level
                        .value
                    ),
                },
                plan=plan,
            )

        except Exception as exc:

            print(
                "\n========== FF AGENT ERROR =========="
            )

            print(
                f"Command : {command}"
            )

            print(
                f"Intent  : {intent}"
            )

            print(
                f"Error Type : "
                f"{type(exc).__name__}"
            )

            print(
                f"Error      : {exc}"
            )

            print(
                "====================================\n"
            )

            return AgentResult(
                success=False,
                status=AgentStatus.FAILED,
                message=(
                    "The file and folder operation could not "
                    "be completed."
                ),
                intent=intent,
                error=str(exc),
            )

    # ======================================================
    # SELECTION / PATH RESOLUTION
    # ======================================================

    def _get_selection(
        self,
        entities: dict[str, Any],
    ) -> Any:

        for key in (
            "selection",
            "selected_index",
            "file_selection",
            "folder_selection",
        ):
            value = entities.get(key)

            if (
                value is not None
                and str(value).strip()
            ):
                return value

        return None

    def _remove_selection_keys(
        self,
        entities: dict[str, Any],
    ) -> None:

        for key in (
            "selection",
            "selected_index",
            "file_selection",
            "folder_selection",
        ):
            entities.pop(
                key,
                None,
            )

    def _has_exact_target_path(
        self,
        context: AgentContext,
        intent: str,
    ) -> bool:

        value = self._get_source_value(
            context,
            intent,
        )

        if (
            not value
            or not isinstance(
                value,
                str,
            )
        ):
            return False

        try:
            return (
                Path(value)
                .expanduser()
                .exists()
            )

        except (
            OSError,
            ValueError,
        ):
            return False

    def _get_source_value(
        self,
        context: AgentContext,
        intent: str,
    ) -> str | None:

        if intent in self.FILE_INTENTS:
            keys = (
                "file_path",
                "source_path",
                "source",
                "file",
                "filename",
                "target",
                "entity",
            )

        else:
            keys = (
                "folder_path",
                "source_path",
                "source",
                "folder",
                "target",
                "entity",
            )

        for key in keys:

            value = context.entities.get(
                key
            )

            if (
                isinstance(
                    value,
                    str,
                )
                and value.strip()
            ):
                return value.strip()

        if context.source:
            return context.source

        if context.target:
            return context.target

        return None

    def _resolve_selected_path(
        self,
        context: AgentContext,
        intent: str,
        selection: Any,
    ) -> str | None:

        candidates = self._find_candidates(
            context=context,
            intent=intent,
        )

        try:
            selected_index = int(
                str(selection).strip()
            )

        except (
            TypeError,
            ValueError,
        ):
            return None

        if not (
            1
            <= selected_index
            <= len(candidates)
        ):
            return None

        selected = candidates[
            selected_index - 1
        ]

        path = selected.get(
            "path"
        )

        if (
            isinstance(
                path,
                str,
            )
            and path.strip()
        ):
            return path.strip()

        return None

    def _find_candidates(
        self,
        context: AgentContext,
        intent: str,
    ) -> list[dict[str, Any]]:

        source_value = (
            self._get_source_value(
                context,
                intent,
            )
        )

        if not source_value:
            return []

        if intent in self.FILE_INTENTS:
            finder = getattr(
                self.file_system_agent,
                "find_file_candidates",
                None,
            )

        else:
            finder = getattr(
                self.file_system_agent,
                "find_folder_candidates",
                None,
            )

        if not callable(
            finder
        ):
            return []

        try:
            candidates = finder(
                source_value
            )

        except Exception:
            return []

        if not isinstance(
            candidates,
            list,
        ):
            return []

        return [
            item
            for item in candidates
            if isinstance(
                item,
                dict,
            )
        ]

    def _apply_resolved_path(
        self,
        context: AgentContext,
        intent: str,
        path: str,
    ) -> None:

        path = str(path)

        if intent in self.FILE_INTENTS:

            context.entities[
                "file_path"
            ] = path

            context.entities[
                "file"
            ] = path

        else:

            context.entities[
                "folder_path"
            ] = path

            context.entities[
                "folder"
            ] = path

        context.entities[
            "source"
        ] = path

        context.entities[
            "source_path"
        ] = path

        context.entities[
            "target"
        ] = path

        context.entities[
            "entity"
        ] = path

        context.source = path
        context.target = path

    # ======================================================
    # RESULT HELPERS
    # ======================================================

    def _requires_selection(
        self,
        result: Any,
    ) -> bool:

        return (
            isinstance(
                result,
                dict,
            )
            and bool(
                result.get(
                    "requires_selection"
                )
            )
        )

    def _extract_candidates(
        self,
        result: Any,
    ) -> list[dict[str, Any]]:

        if not isinstance(
            result,
            dict,
        ):
            return []

        candidates = result.get(
            "candidates"
        )

        if not isinstance(
            candidates,
            list,
        ):
            return []

        return [
            item
            for item in candidates
            if isinstance(
                item,
                dict,
            )
        ]

    def _execution_succeeded(
        self,
        result: Any,
    ) -> bool:

        if isinstance(
            result,
            dict,
        ):
            return bool(
                result.get(
                    "success",
                    result.get(
                        "ok",
                        False,
                    ),
                )
            )

        success = getattr(
            result,
            "success",
            None,
        )

        if success is not None:
            return bool(success)

        return bool(result)

    def _extract_result_path(
        self,
        result: Any,
    ) -> str | None:

        if not isinstance(
            result,
            dict,
        ):
            return None

        for key in (
            "path",
            "result_path",
            "source",
            "source_path",
            "target",
        ):

            value = result.get(
                key
            )

            if (
                isinstance(
                    value,
                    str,
                )
                and value.strip()
            ):
                return value.strip()

        return None

    def _clarification_result(
        self,
        *,
        intent: str,
        message: str,
        candidates: (
            list[dict[str, Any]]
            | None
        ) = None,
        missing_fields: (
            list[str]
            | None
        ) = None,
        clarification_type: str | None = None,
        data: dict[str, Any] | None = None,
    ) -> AgentResult:

        result_data = dict(
            data or {}
        )

        result_data[
            "missing_fields"
        ] = list(
            missing_fields or []
        )

        result_data[
            "clarification_type"
        ] = clarification_type

        return AgentResult(
            success=False,
            status=(
                AgentStatus
                .CLARIFICATION_REQUIRED
            ),
            message=message,
            intent=intent,
            data=result_data,
            candidates=list(
                candidates or []
            ),
            requires_clarification=True,
        )

    def _execution_failure_result(
        self,
        *,
        intent: str,
        result: Any,
    ) -> AgentResult:

        message = (
            result.get(
                "message"
            )
            if isinstance(
                result,
                dict,
            )
            else None
        ) or (
            "The filesystem operation failed."
        )

        return AgentResult(
            success=False,
            status=AgentStatus.FAILED,
            message=message,
            intent=intent,
            data={
                "execution_result": result,
            },
            error=message,
        )

    def _build_confirmation_message(
        self,
        context: AgentContext,
        safety_message: str,
    ) -> str:

        intent_text = (
            context.intent
            .replace(
                "_",
                " ",
            )
        )

        source = (
            context.source
            or context.target
        )

        destination = (
            context.destination
            or context.entities.get(
                "new_name"
            )
            or context.entities.get(
                "destination_name"
            )
        )

        if source and destination:

            return (
                f"Ready to {intent_text} "
                f"'{source}' "
                f"to '{destination}'. "
                "Do you want to continue?"
            )

        if source:

            return (
                f"Ready to {intent_text} "
                f"'{source}'. "
                "Do you want to continue?"
            )

        return (
            safety_message
            or
            (
                f"Ready to {intent_text}. "
                "Do you want to continue?"
            )
        )

    # ======================================================
    # EXECUTION DELEGATION
    # ======================================================

    def _delegate_execution(
        self,
        command: str,
        intent: str,
        entities: dict[str, Any],
        context: AgentContext,
        *,
        preflight: bool = False,
    ) -> Any:
        """
        Delegate to the existing FileSystemAgent.

        When preflight=True, this is used only for intents that the
        FileSystemAgent itself protects with requires_selection=True.
        No confirmed filesystem mutation is allowed in this stage.
        """

        executor = self._get_executor()

        payload = dict(
            entities
        )

        # --------------------------------------------------
        # Add resolved source
        # --------------------------------------------------

        if context.source:

            payload[
                "source"
            ] = context.source

        # --------------------------------------------------
        # Add resolved destination
        # --------------------------------------------------

        if context.destination:

            payload[
                "destination"
            ] = context.destination

        # --------------------------------------------------
        # Add resolved target
        # --------------------------------------------------

        if context.target:

            payload[
                "target"
            ] = context.target

            payload[
                "entity"
            ] = context.target

        # --------------------------------------------------
        # Normalize rename operations
        # --------------------------------------------------

        if intent in {
            "rename_file",
            "rename_folder",
        }:

            new_name = (
                payload.get(
                    "new_name"
                )
                or payload.get(
                    "destination_name"
                )
                or payload.get(
                    "rename_to"
                )
                or payload.get(
                    "new_path"
                )
            )

            if new_name:

                payload[
                    "new_name"
                ] = new_name

        # --------------------------------------------------
        # Normalize copy and move source
        # --------------------------------------------------

        if (
            intent in {
                "copy_file",
                "copy_folder",
                "move_file",
                "move_folder",
            }
            and not payload.get(
                "source"
            )
        ):

            source = (
                payload.get(
                    "file"
                )
                or payload.get(
                    "folder"
                )
                or payload.get(
                    "target"
                )
                or payload.get(
                    "entity"
                )
            )

            if source:

                payload[
                    "source"
                ] = source

        # --------------------------------------------------
        # Debug
        # --------------------------------------------------

        print(
            "\n========== FF AGENT EXECUTION =========="
        )

        print(
            f"Command : {command}"
        )

        print(
            f"Intent  : {intent}"
        )

        print(
            f"Preflight : {preflight}"
        )

        print(
            f"Payload : {payload}"
        )

        print(
            "========================================\n"
        )

        # --------------------------------------------------
        # Execute
        # --------------------------------------------------

        try:

            result = executor(
                intent,
                payload,
            )

            print(
                "\n========== FILE SYSTEM RESULT =========="
            )

            print(
                f"Intent : {intent}"
            )

            print(
                f"Result : {result}"
            )

            print(
                "========================================\n"
            )

            return result

        except Exception as exc:

            print(
                "\n========== FILE SYSTEM EXECUTION ERROR =========="
            )

            print(
                f"Intent     : {intent}"
            )

            print(
                f"Payload    : {payload}"
            )

            print(
                f"Error Type : "
                f"{type(exc).__name__}"
            )

            print(
                f"Error      : {exc}"
            )

            print(
                "=================================================\n"
            )

            raise

    def _get_executor(
        self,
    ) -> Callable[..., Any]:

        method_names = (
            "execute",
            "handle",
            "run",
            "process",
            "dispatch",
        )

        for method_name in method_names:

            method = getattr(
                self.file_system_agent,
                method_name,
                None,
            )

            if callable(
                method
            ):
                return method

        raise AttributeError(
            "The configured FileSystemAgent "
            "does not expose a supported "
            "execution method."
        )

    @staticmethod
    def result_to_dict(
        result: AgentResult,
    ) -> dict[str, Any]:

        data = dict(result.data or {})

        selection_required = bool(
            data.get("selection_required")
            or data.get("requires_selection")
            or (
                result.requires_clarification
                and bool(result.candidates)
            )
        )

        return {
            "success": result.success,

            "status": result.status.value,

            "message": result.message,

            "intent": result.intent,

            "data": data,

            "candidates": result.candidates,

            # UI FileSelectionPanel compatibility
            "requires_selection": selection_required,

            "selection_required": selection_required,

            "requires_confirmation": (
                result.requires_confirmation
            ),

            "requires_clarification": (
                result.requires_clarification
            ),

            "error": result.error,
        }