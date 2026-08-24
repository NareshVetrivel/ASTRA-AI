"""
Command Dispatcher Module

Routes the detected intent
to the appropriate controller.
"""

from pathlib import Path

from ai.gemini_client import GeminiClient
from automation.screen_recorder import ScreenRecorder
from automation.file_system_agent import FileSystemAgent
from ff_agent import FileFolderAgent

class CommandDispatcher:

    """
    Central command dispatcher.
    """

    def __init__(
        self,
        tts,
        app_launcher,
        app_closer,
        keyboard_controller,
        mouse_controller,
        window_controller,
        system_controller,
        file_finder,
        folder_manager,
        file_manager,
        browser_controller,
        whisper,
        gemini_client: GeminiClient
    ):

        self.tts = tts

        self.app_launcher = app_launcher
        self.app_closer = app_closer

        self.keyboard = keyboard_controller
        self.mouse = mouse_controller
        self.window = window_controller
        self.system = system_controller
        self.file_finder = file_finder

        self.folder_manager = folder_manager
        self.file_manager = file_manager
        self.browser = browser_controller

        self.whisper = whisper

        self.gemini = gemini_client

        self.screen_recorder = ScreenRecorder()

        # --------------------------------------------------
        # File System Agent
        # --------------------------------------------------
        # Central filesystem orchestration layer.
        # FileFinder, FileManager and FolderManager are
        # still used internally by FileSystemAgent.
        self.file_system_agent = FileSystemAgent(
            file_finder=self.file_finder,
            file_manager=self.file_manager,
            folder_manager=self.folder_manager,
        )

        # --------------------------------------------------
        # Intelligent File & Folder Agent
        # --------------------------------------------------
        # The smart agent wraps the existing FileSystemAgent.
        # It does not replace the existing filesystem engine.
        self.file_folder_agent = FileFolderAgent(
            file_system_agent=self.file_system_agent
        )


    # --------------------------------------------------
    # Helper : Intelligent File & Folder Agent
    # --------------------------------------------------

    def process_file_folder_agent(
        self,
        intent,
        entity=None,
        user_text=None,
        typed_text=None,
        browser=None,
        website=None,
        search_query=None,
        profile=None,
        multi_command=False,
        selection=None,
        skip_confirmation=False,
    ):
        """
        Route supported file and folder commands through the FF Agent.

        Selection is resolved here before the smart agent is called.
        This guarantees that after the user chooses option 1/2/3..., the
        selected filesystem path is preserved and the same candidate list is
        not shown again.
        """

        supported_intents = {
            "open_file", "create_file", "rename_file", "copy_file",
            "move_file", "delete_file", "open_folder", "create_folder",
            "rename_folder", "copy_folder", "move_folder", "delete_folder",
            "compress_file", "compress_zip", "extract_zip", "unzip",
        }

        if intent not in supported_intents:
            return None

        command = user_text or typed_text or ""

        if entity is None:
            entities = {}
        elif isinstance(entity, dict):
            entities = dict(entity)
        else:
            entities = {"entity": entity}

        # --------------------------------------------------
        # Normalize aliases produced by EntityExtractor.
        # --------------------------------------------------
        if intent.endswith("_folder"):
            source_value = (
                entities.get("source")
                or entities.get("source_path")
                or entities.get("folder_path")
                or entities.get("folder")
                or entities.get("foldername")
                or entities.get("old_name")
                or entities.get("target")
                or entities.get("entity")
            )
            if source_value and intent not in {"create_folder"}:
                entities.setdefault("source", source_value)
                entities.setdefault("target", source_value)
        else:
            source_value = (
                entities.get("source")
                or entities.get("source_path")
                or entities.get("file_path")
                or entities.get("file")
                or entities.get("filename")
                or entities.get("old_name")
                or entities.get("target")
                or entities.get("entity")
            )
            if source_value and intent not in {"create_file"}:
                entities.setdefault("source", source_value)
                entities.setdefault("target", source_value)

        if not entities.get("destination"):
            destination = (
                entities.get("destination_path")
                or entities.get("to")
            )
            if destination:
                entities["destination"] = destination

        # --------------------------------------------------
        # Normalize archive aliases.
        # --------------------------------------------------
        if intent in {"compress_file", "compress_zip", "extract_zip", "unzip"}:
            archive_source = (
                entities.get("source")
                or entities.get("source_path")
                or entities.get("file_path")
                or entities.get("filename")
                or entities.get("file")
                or entities.get("zip_file")
                or entities.get("archive")
                or entities.get("target")
                or entities.get("entity")
            )
            if archive_source:
                entities.setdefault("source", archive_source)
                entities.setdefault("target", archive_source)
                entities.setdefault("entity", archive_source)

        # --------------------------------------------------
        # Normalize open targets.
        # --------------------------------------------------
        if intent in {"open_file", "open_folder"}:
            open_target = (
                entities.get("target")
                or entities.get("entity")
                or entities.get("name")
            )
            if isinstance(open_target, str):
                cleaned_target = open_target.strip()
                for prefix in (
                    "open the folder ", "open the file ",
                    "open folder ", "open file ", "open ",
                ):
                    if cleaned_target.lower().startswith(prefix):
                        cleaned_target = cleaned_target[len(prefix):].strip()
                        break
                if cleaned_target:
                    entities["target"] = cleaned_target
                    entities["entity"] = cleaned_target
                    entities["source"] = cleaned_target

        # --------------------------------------------------
        # Resolve ambiguous existing source BEFORE FF Agent.
        # --------------------------------------------------
        selection_intents = {
            "rename_file", "copy_file", "move_file", "delete_file",
            "rename_folder", "copy_folder", "move_folder", "delete_folder",
            "compress_file", "compress_zip", "extract_zip", "unzip",
        }

        if intent in selection_intents:
            source_query = entities.get("source") or entities.get("target")

            if source_query:
                is_folder = intent.endswith("_folder")

                # A selection from MainWindow is always 1-based.
                if selection is not None:
                    resolver = (
                        self.resolve_folder_selection
                        if is_folder
                        else self.resolve_file_candidate
                    )
                    resolution = resolver(source_query, selection)
                else:
                    resolver = (
                        self.resolve_folder_selection
                        if is_folder
                        else self.resolve_file_candidate
                    )
                    resolution = resolver(source_query, None)

                if resolution.get("requires_selection"):
                    pending_payload = self.build_selection_payload(
                        intent=intent,
                        entity=entities,
                        typed_text=typed_text,
                        browser=browser,
                        website=website,
                        search_query=search_query,
                        profile=profile,
                        user_text=user_text,
                        multi_command=multi_command,
                    )

                    target_type = "folder" if is_folder else "file"

                    return self.response(
                        False,
                        "",
                        f"Status : {target_type.title()} Selection Required",
                        resolution.get("message")
                        or f"Please select the correct {target_type}.",
                        requires_selection=True,
                        selection_required=True,
                        requires_clarification=True,
                        candidates=resolution.get("candidates", []),
                        pending_action=intent,
                        pending_payload=pending_payload,
                        selection_type=target_type,
                    )

                if not resolution.get("success"):
                    return self.response(
                        False,
                        "",
                        "Status : File/Folder Not Found",
                        resolution.get("message")
                        or "The selected file or folder could not be found.",
                    )

                resolved_path = resolution.get("path")
                if resolved_path:
                    # Preserve exact path for every later stage:
                    # selection -> confirmation -> confirmed execution.
                    entities["source"] = resolved_path
                    entities["target"] = resolved_path
                    entities["entity"] = resolved_path
                    if is_folder:
                        entities["folder_path"] = resolved_path
                    else:
                        entities["file_path"] = resolved_path

        # Do not pass a stale numeric selection to the smart agent once
        # the exact path has already been resolved.
        entities.pop("selection", None)
        entities.pop("selected_index", None)

        result = self.file_folder_agent.execute(
            command=command,
            intent=intent,
            entities=entities,
            confirmed=skip_confirmation,
        )

        if result.requires_clarification:
            candidates = list(result.candidates or [])
            selection_required = bool(
                result.data.get("selection_required", False)
            )

            if candidates or selection_required:
                pending_payload = self.build_selection_payload(
                    intent=intent,
                    entity=entities,
                    typed_text=typed_text,
                    browser=browser,
                    website=website,
                    search_query=search_query,
                    profile=profile,
                    user_text=user_text,
                    multi_command=multi_command,
                )
                target_type = "folder" if "folder" in str(intent).lower() else "file"
                return self.response(
                    False,
                    "",
                    f"Status : {target_type.title()} Selection Required",
                    result.message or f"Please select the correct {target_type}.",
                    requires_selection=True,
                    selection_required=True,
                    requires_clarification=True,
                    candidates=candidates,
                    pending_action=intent,
                    pending_payload=pending_payload,
                    selection_type=target_type,
                    agent_status=result.status.value,
                    agent_data=result.data,
                )

            return self.response(
                False,
                "",
                "Status : Information Required",
                result.message,
                requires_information=True,
                requires_clarification=True,
                agent_status=result.status.value,
                agent_data=result.data,
                candidates=[],
            )

        if result.requires_confirmation:
            confirmation_payload = self.build_selection_payload(
                intent=intent,
                entity=entities,
                typed_text=typed_text,
                browser=browser,
                website=website,
                search_query=search_query,
                profile=profile,
                user_text=user_text,
                multi_command=multi_command,
            )
            return self.confirmation_response(
                message=result.message,
                intent=intent,
                entity=entities,
                typed_text=typed_text,
                browser=browser,
                website=website,
                search_query=search_query,
                profile=profile,
                user_text=user_text,
                multi_command=multi_command,
                selection=None,
                confirmation_action=intent,
                confirmation_payload=confirmation_payload,
            )

        if not result.success:
            return self.response(
                False,
                "",
                "Status : File/Folder Operation Failed",
                result.message,
                agent_status=result.status.value,
                agent_data=result.data,
                error=result.error,
            )

        success_message = self._format_file_operation_success(
            intent=intent,
            entities=entities,
            agent_result=result,
        )

        # Speak the final successful operation acknowledgement.
        # The same message is returned to MainWindow for the UI.
        success_message = self.speak(
            success_message
        )

        return self.response(
            True,
            self._file_operation_success_status(intent),
            "Status : File/Folder Operation Failed",
            success_message,
            agent_status=result.status.value,
            agent_data=result.data,
            verified_items=result.data.get(
                "verified_items",
                []
            ),
        )


    # --------------------------------------------------
    # Helper : Human-Friendly Filesystem Success Message
    # --------------------------------------------------

    def _format_file_operation_success(
        self,
        intent,
        entities,
        agent_result,
    ):
        """Build one exact success message for UI and TTS."""

        entities = entities or {}
        data = getattr(agent_result, "data", {}) or {}
        execution = data.get("execution_result", {})
        if not isinstance(execution, dict):
            execution = {}

        source = (
            execution.get("source")
            or entities.get("source")
            or entities.get("target")
            or entities.get("entity")
            or entities.get("file_path")
            or entities.get("folder_path")
        )
        destination = (
            execution.get("destination")
            or execution.get("destination_path")
            or execution.get("copied_path")
            or entities.get("destination")
        )
        result_path = (
            execution.get("path")
            or execution.get("result_path")
            or execution.get("new_path")
            or execution.get("copied_path")
        )
        new_name = (
            execution.get("new_name")
            or entities.get("new_name")
            or entities.get("destination_name")
            or entities.get("rename_to")
        )

        def name_of(value):
            if not value:
                return "item"
            try:
                return Path(str(value)).name or str(value)
            except Exception:
                return str(value)

        item_type = "folder" if "folder" in str(intent) else "file"
        source_name = name_of(source)
        destination_name = name_of(destination)

        if intent in {"rename_file", "rename_folder"}:
            target_name = name_of(new_name or result_path)
            return (
                f'{item_type.title()} "{source_name}" renamed successfully '
                f'to "{target_name}".'
            )

        if intent in {"copy_file", "copy_folder"}:
            return (
                f'{item_type.title()} "{source_name}" copied successfully '
                f'to "{destination_name}".'
            )

        if intent in {"move_file", "move_folder"}:
            return (
                f'{item_type.title()} "{source_name}" moved successfully '
                f'to "{destination_name}".'
            )

        if intent in {"compress_file", "compress_zip"}:
            archive_name = name_of(result_path)
            if archive_name == "item":
                archive_name = f"{Path(source_name).stem}.zip"
            return (
                f'"{source_name}" compressed successfully as '
                f'"{archive_name}".'
            )

        if intent in {"extract_zip", "unzip"}:
            extracted_to = name_of(result_path or destination)
            if extracted_to == "item":
                extracted_to = Path(source_name).stem
            return (
                f'Archive "{source_name}" extracted successfully '
                f'to "{extracted_to}".'
            )

        return getattr(agent_result, "message", "Operation completed successfully.")

    def _file_operation_success_status(self, intent):
        """Return a clear UI status for supported filesystem operations."""

        statuses = {
            "rename_file": "Status : File Renamed",
            "rename_folder": "Status : Folder Renamed",
            "copy_file": "Status : File Copied",
            "copy_folder": "Status : Folder Copied",
            "move_file": "Status : File Moved",
            "move_folder": "Status : Folder Moved",
            "compress_file": "Status : ZIP Created",
            "compress_zip": "Status : ZIP Created",
            "extract_zip": "Status : ZIP Extracted",
            "unzip": "Status : ZIP Extracted",
        }
        return statuses.get(intent, "Status : File/Folder Operation Completed")


    # --------------------------------------------------
    # Helper : Standard Response
    # --------------------------------------------------

    def response(
        self,
        success: bool,
        success_status: str,
        failed_status: str,
        assistant_reply: str = "",
        **extra
    ):

        result = {

            "success": success,

            "status": (

                success_status
                if success
                else failed_status

            ),

            # Used by MainWindow
            "message": assistant_reply,

            # Optional backward compatibility
            "assistant_reply": assistant_reply

        }

        # Preserve optional orchestration data such as
        # multiple-file candidates for the UI.
        result.update(extra)

        return result

    # --------------------------------------------------
    # Helper : Resolve File Candidate
    # --------------------------------------------------

    def resolve_file_candidate(
        self,
        filename,
        selection=None
    ):
        """
        Resolve a file without silently selecting the first
        match.

        Returns the FileSystemAgent resolution result.
        When multiple files match and no selection is supplied,
        the caller must return the candidates to the UI.
        """

        return self.file_system_agent.resolve_file_selection(
            filename,
            selection
        )

    # --------------------------------------------------
    # Helper : Resolve Folder Candidates
    # --------------------------------------------------

    def resolve_folder_selection(
        self,
        folder_name,
        selection=None
    ):
        """
        Resolve a folder with explicit multiple-match handling.

        A single folder is resolved directly.

        Multiple folders with the same name are returned to
        MainWindow so the user can choose a numbered candidate.

        The selected folder path is preserved in the dispatcher
        payload and reused after confirmation.
        """

        if folder_name is None:
            return {
                "success": False,
                "message": "Folder name is required.",
                "candidates": [],
                "requires_selection": False,
            }

        folder_name = str(folder_name).strip().strip('"').strip("'")

        if not folder_name:
            return {
                "success": False,
                "message": "Folder name is required.",
                "candidates": [],
                "requires_selection": False,
            }

        # --------------------------------------------------
        # Direct / special folder resolution
        # --------------------------------------------------

        direct = Path(folder_name).expanduser()

        try:
            if direct.exists() and direct.is_dir():
                path = str(direct.resolve())
                return {
                    "success": True,
                    "path": path,
                    "candidates": [
                        {
                            "index": 1,
                            "name": direct.name or path,
                            "path": path,
                        }
                    ],
                    "requires_selection": False,
                }
        except (OSError, RuntimeError):
            pass

        special = self.file_system_agent.resolve_special_folder(
            folder_name
        )

        if special and not str(special).lower().startswith("shell:"):
            path = str(special)
            return {
                "success": True,
                "path": path,
                "candidates": [
                    {
                        "index": 1,
                        "name": Path(path).name or folder_name,
                        "path": path,
                    }
                ],
                "requires_selection": False,
            }

        # --------------------------------------------------
        # Search known user roots.
        # --------------------------------------------------

        home = Path.home()

        roots = [
            home,
            home / "Desktop",
            home / "Documents",
            home / "Downloads",
            home / "Pictures",
            home / "Videos",
            home / "Music",
            home / "OneDrive",
            home / "OneDrive" / "Desktop",
            home / "OneDrive" / "Documents",
            home / "OneDrive" / "Downloads",
            home / "OneDrive" / "Pictures",
            Path.cwd(),
        ]

        normalized = folder_name.lower().rstrip("\\/")

        candidates_by_path = {}

        for root in roots:

            try:
                if not root.exists() or not root.is_dir():
                    continue
            except OSError:
                continue

            # Search direct children first.
            try:
                for child in root.iterdir():

                    try:
                        if (
                            child.is_dir()
                            and child.name.lower() == normalized
                        ):
                            candidates_by_path[
                                str(child.resolve())
                            ] = child
                    except (OSError, RuntimeError):
                        continue
            except (OSError, PermissionError):
                pass

        # --------------------------------------------------
        # Bounded recursive search.
        # This catches nested folders without scanning an
        # unbounded number of directories.
        # --------------------------------------------------

        if not candidates_by_path:

            max_depth = 4

            for root in roots:

                try:
                    root = root.resolve()
                except (OSError, RuntimeError):
                    continue

                try:
                    root_parts = len(root.parts)

                    for current, dirs, _files in __import__(
                        "os"
                    ).walk(root):

                        current_path = Path(current)

                        try:
                            depth = len(current_path.parts) - root_parts
                        except Exception:
                            depth = max_depth + 1

                        if depth > max_depth:
                            dirs[:] = []
                            continue

                        for dirname in list(dirs):

                            if dirname.lower() != normalized:
                                continue

                            candidate = current_path / dirname

                            try:
                                candidates_by_path[
                                    str(candidate.resolve())
                                ] = candidate
                            except (OSError, RuntimeError):
                                pass

                except (OSError, PermissionError):
                    continue

        candidates = [
            {
                "index": index,
                "name": path.name,
                "path": str(path),
            }
            for index, path in enumerate(
                sorted(
                    candidates_by_path.values(),
                    key=lambda p: str(p).lower()
                ),
                start=1
            )
        ]

        # --------------------------------------------------
        # No match
        # --------------------------------------------------

        if not candidates:

            return {
                "success": False,
                "message": f"Folder not found: {folder_name}",
                "candidates": [],
                "requires_selection": False,
            }

        # --------------------------------------------------
        # Single match
        # --------------------------------------------------

        if len(candidates) == 1:

            return {
                "success": True,
                "path": candidates[0]["path"],
                "candidates": candidates,
                "requires_selection": False,
            }

        # --------------------------------------------------
        # Multiple matches -> ask UI for numbered selection.
        # --------------------------------------------------

        if selection is None:

            return {
                "success": False,
                "message": (
                    f"Multiple folders found for "
                    f"'{folder_name}'. Please select one."
                ),
                "candidates": candidates,
                "requires_selection": True,
            }

        try:
            selected_index = int(
                str(selection).strip()
            )
        except (TypeError, ValueError):

            return {
                "success": False,
                "message": "Invalid folder selection.",
                "candidates": candidates,
                "requires_selection": True,
            }

        if not (
            1
            <= selected_index
            <= len(candidates)
        ):

            return {
                "success": False,
                "message": (
                    f"Invalid selection. Choose a number "
                    f"between 1 and {len(candidates)}."
                ),
                "candidates": candidates,
                "requires_selection": True,
            }

        selected = candidates[
            selected_index - 1
        ]

        return {
            "success": True,
            "path": selected["path"],
            "candidates": candidates,
            "selected_index": selected_index,
            "requires_selection": False,
        }

    # --------------------------------------------------
    # Helper : Multiple Target Selection Response
    # --------------------------------------------------

    def multiple_target_response(
        self,
        result,
        action_name,
        target_type="file",
        pending_payload=None,
    ):
        """
        Return a numbered target-selection response to MainWindow.

        The same response contract is used for files and folders so
        the existing UI selection flow remains unchanged.
        """

        candidates = result.get(
            "candidates",
            []
        )

        if not candidates:

            return self.response(
                False,
                "",
                f"Status : {target_type.title()} Selection Failed",
                result.get(
                    "message",
                    f"No matching {target_type} was found."
                ),
            )

        payload = (
            dict(pending_payload)
            if isinstance(
                pending_payload,
                dict
            )
            else dict(
                getattr(
                    self,
                    "_current_selection_payload",
                    {}
                )
            )
        )

        return self.response(
            False,
            "",
            f"Status : {target_type.title()} Selection Required",
            (
                f"Please choose a {target_type} from the list."
            ),
            requires_selection=True,
            selection_required=True,
            candidates=candidates,
            pending_action=action_name,
            pending_payload=payload,
            selection_type=target_type,
        )

    # --------------------------------------------------
    # Helper : Selection Payload
    # --------------------------------------------------

    @staticmethod
    def build_selection_payload(
        intent,
        entity=None,
        typed_text=None,
        browser=None,
        website=None,
        search_query=None,
        profile=None,
        user_text=None,
        multi_command=False,
    ):
        """
        Preserve the original command context while the UI waits
        for a numbered filesystem selection.

        This prevents a spoken response such as "2" from being
        interpreted as a brand-new command.
        """

        return {
            "intent": intent,
            "entity": entity,
            "typed_text": typed_text,
            "browser": browser,
            "website": website,
            "search_query": search_query,
            "profile": profile,
            "user_text": user_text,
            "multi_command": multi_command,
        }

    # --------------------------------------------------
    # Helper : Multiple File Selection Response
    # --------------------------------------------------

    def multiple_file_response(
        self,
        result,
        action_name,
        pending_payload=None
    ):
        """
        Return multiple matching filesystem candidates to MainWindow.

        MainWindow displays the candidates in the UI and waits for
        the user's numeric selection. The dispatcher does not speak
        or listen here.
        """

        candidates = result.get(
            "candidates",
            []
        )

        if not candidates:

            return self.response(
                False,
                "",
                "Status : File Selection Failed",
                "No matching files were found.",
            )

        # Always preserve the exact command payload.
        payload = (
            dict(pending_payload)
            if isinstance(
                pending_payload,
                dict
            )
            else dict(
                getattr(
                    self,
                    "_current_selection_payload",
                    {}
                )
            )
        )

        return self.response(
            False,
            "",
            "Status : File Selection Required",
            "Please choose a file from the list.",
            requires_selection=True,
            selection_required=True,
            candidates=candidates,
            pending_action=action_name,
            pending_payload=payload,
        )

    # --------------------------------------------------
    # Helper : Speak + Return Message
    # --------------------------------------------------

    def speak(
        self,
        message: str
    ):

        self.tts.speak(message)

        return message

    # --------------------------------------------------
    # Helper : Confirmation Request
    # --------------------------------------------------

    def confirmation_response(
        self,
        message,
        intent,
        entity=None,
        typed_text=None,
        browser=None,
        website=None,
        search_query=None,
        profile=None,
        user_text=None,
        multi_command=False,
        selection=None,
        confirmation_action=None,
        confirmation_payload=None,
    ):
        """
        Return a non-blocking confirmation request to MainWindow.

        The dispatcher must never directly listen to the microphone
        for confirmation because MainWindow owns the microphone
        lifecycle.
        """

        return self.response(
            False,
            "",
            "Status : Confirmation Required",
            message,
            requires_confirmation=True,
            confirmation_required=True,
            confirmation_message=message,
            confirmation_action=(
                confirmation_action
                or intent
            ),
            confirmation_payload=(
                confirmation_payload
                or {
                    "intent": intent,
                    "entity": entity,
                    "typed_text": typed_text,
                    "browser": browser,
                    "website": website,
                    "search_query": search_query,
                    "profile": profile,
                    "user_text": user_text,
                    "multi_command": multi_command,
                    "selection": selection,
                }
            ),
        )

    # --------------------------------------------------
    # Helper : Legacy Confirmation Compatibility
    # --------------------------------------------------

    def confirm_action(self, message):
        """
        Legacy compatibility helper.

        Confirmation must be handled by MainWindow.
        This method is intentionally kept only so older code paths
        do not crash.

        New filesystem operations MUST use confirmation_response()
        when skip_confirmation is False.
        """

        return True

    # --------------------------------------------------
    # Helper : Execute Confirmed Action
    # --------------------------------------------------

    def execute_confirmed_action(
        self,
        confirmation_action,
        payload=None
    ):
        """
        Execute an operation after MainWindow receives an explicit
        YES confirmation.

        The original command context is restored from payload and
        dispatch() is re-entered with skip_confirmation=True.
        """

        payload = payload or {}

        return self.dispatch(
            intent=payload.get(
                "intent",
                confirmation_action
            ),
            entity=payload.get("entity"),
            typed_text=payload.get("typed_text"),
            browser=payload.get("browser"),
            website=payload.get("website"),
            search_query=payload.get("search_query"),
            profile=payload.get("profile"),
            user_text=payload.get("user_text"),
            multi_command=payload.get(
                "multi_command",
                False
            ),
            selection=payload.get("selection"),
            skip_confirmation=True
        )

    # --------------------------------------------------
    # Dispatcher
    # --------------------------------------------------

    def dispatch(
        self,
        intent,
        entity=None,
        typed_text=None,
        browser=None,
        website=None,
        search_query=None,
        profile=None,
        user_text=None,
        multi_command=False,
        selection=None,
        skip_confirmation=False
    ):
        """
        Execute the detected intent.

        Returns
        -------
        dict
        """

        try:

            # Preserve the complete command context. If filesystem
            # resolution becomes ambiguous, this payload is returned
            # to MainWindow so a numbered voice selection can resume
            # the original operation instead of starting a new command.
            self._current_selection_payload = (
                self.build_selection_payload(
                    intent=intent,
                    entity=entity,
                    typed_text=typed_text,
                    browser=browser,
                    website=website,
                    search_query=search_query,
                    profile=profile,
                    user_text=user_text,
                    multi_command=multi_command,
                )
            )

            # ==================================================
            # INTELLIGENT FILE & FOLDER AGENT
            # ==================================================
            # Always route supported file/folder intents through the
            # FF Agent. On confirmed re-entry, skip_confirmation is
            # passed as confirmed=True so safety confirmation is not
            # requested again, while execution and verification still
            # happen inside the FF Agent pipeline.

            agent_result = self.process_file_folder_agent(
                intent=intent,
                entity=entity,
                user_text=user_text,
                typed_text=typed_text,
                browser=browser,
                website=website,
                search_query=search_query,
                profile=profile,
                multi_command=multi_command,
                selection=selection,
                skip_confirmation=skip_confirmation,
            )

            if agent_result is not None:
                return agent_result

            # -------------------------
            # AI Conversation
            # -------------------------

            if intent == "ai_chat":

                reply = self.gemini.generate_response(
                    user_text or typed_text or entity or ""
                )

                self.tts.speak(reply)

                return self.response(

                    True,

                    "Status : AI Response",

                    "Status : AI Failed",

                    reply

                )

            # -------------------------
            # Launch Application
            # -------------------------

            if (
                intent == "launch_application"
                and entity
            ):

                # Website takes priority
                if website:

                    reply = self.speak(
                        f"Opening {website}"
                    )

                    success = self.browser.open_website(

                        website,

                        browser or entity

                    )

                    return self.response(

                        success,

                        "Status : Website Opened",

                        "Status : Website Failed",

                        reply

                    )

                app_name = entity.replace(
                    ".exe",
                    ""
                )

                reply = self.speak(
                    f"Opening {app_name}"
                )

                # --------------------------------------------------
                # Chrome must use the existing ASTRA Playwright
                # browser session on CDP port 9222.
                #
                # This avoids launching another Chrome process
                # through AppLauncher and prevents the Chrome
                # profile chooser / session conflict.
                # --------------------------------------------------

                if app_name.lower() in {
                    "chrome",
                    "google chrome",
                    "googlechrome"
                }:

                    # --------------------------------------------------
                    # Chrome is handled by the ASTRA Playwright session.
                    #
                    # Playwright uses the existing Chrome Default profile
                    # through CDP port 9222.
                    #
                    # Do NOT use AppLauncher for Chrome here.
                    # --------------------------------------------------

                    success = self.browser.open_browser(
                        "chrome"
                    )

                    if success:

                        reply = self.speak(
                            "Chrome is ready."
                        )

                    else:

                        reply = self.speak(
                            "Unable to open Chrome."
                        )

                else:

                    # --------------------------------------------------
                    # All other applications keep the existing
                    # AppLauncher behavior.
                    # --------------------------------------------------

                    success = (
                        self.app_launcher
                        .launch_application(
                            entity
                        )
                    )

                return self.response(

                    success,

                    "Status : Application Opened",

                    "Status : Launch Failed",

                    reply

                )

            # -------------------------
            # Close Application
            # -------------------------

            elif (
                intent == "close_application"
                and entity
            ):

                app_name = entity.replace(
                    ".exe",
                    ""
                ).strip()

                # ---------------------------------
                # Check Application First
                # ---------------------------------

                is_running = (
                    self.app_closer
                    .is_running(entity)
                )

                if not is_running:

                    reply = self.speak(
                        f"{app_name} is not running."
                    )

                    return self.response(

                        False,

                        "",

                        "Status : Application Not Running",

                        reply

                    )

                # ---------------------------------
                # Application Is Running
                # ---------------------------------

                reply = self.speak(
                    f"Closing {app_name}."
                )

                # ---------------------------------
                # Close Application
                # ---------------------------------

                success = (
                    self.app_closer
                    .close_application(entity)
                )

                # ---------------------------------
                # Final Response
                # ---------------------------------

                if success:

                    reply = self.speak(
                        f"{app_name} closed successfully."
                    )

                else:

                    reply = self.speak(
                        f"Unable to close {app_name}."
                    )

                return self.response(

                    success,

                    "Status : Application Closed",

                    "Status : Application Close Failed",

                    reply

                )

            # -------------------------
            # Type Text
            # -------------------------

            elif (
                intent == "type_text"
                and typed_text
            ):

                reply = self.speak(
                    "Typing your text."
                )

                success = self.keyboard.type_text(
                    typed_text
                )

                return self.response(

                    success,

                    "Status : Typing Completed",

                    "Status : Typing Failed",

                    reply

                )

            # -------------------------
            # Copy
            # -------------------------

            elif intent == "copy":

                reply = self.speak("Copying.")

                success = self.keyboard.copy()

                return self.response(

                    success,

                    "Status : Copy Completed",

                    "Status : Copy Failed",

                    reply

                )

            # -------------------------
            # Paste
            # -------------------------

            elif intent == "paste":

                reply = self.speak("Pasting.")

                success = self.keyboard.paste()

                return self.response(

                    success,

                    "Status : Paste Completed",

                    "Status : Paste Failed",

                    reply

                )

            # -------------------------
            # Cut
            # -------------------------

            elif intent == "cut":

                reply = self.speak("Cutting.")

                success = self.keyboard.cut()

                return self.response(

                    success,

                    "Status : Cut Completed",

                    "Status : Cut Failed",

                    reply

                )

            # -------------------------
            # Undo
            # -------------------------

            elif intent == "undo":

                reply = self.speak("Undoing.")

                success = self.keyboard.undo()

                return self.response(

                    success,

                    "Status : Undo Completed",

                    "Status : Undo Failed",

                    reply

                )

            # -------------------------
            # Redo
            # -------------------------

            elif intent == "redo":

                reply = self.speak("Redoing.")

                success = self.keyboard.redo()

                return self.response(

                    success,

                    "Status : Redo Completed",

                    "Status : Redo Failed",

                    reply

                )

            # -------------------------
            # Enter
            # -------------------------

            elif intent == "press_enter":

                reply = self.speak(
                    "Pressing Enter."
                )

                success = self.keyboard.press_key(
                    "enter"
                )

                return self.response(

                    success,

                    "Status : Enter Pressed",

                    "Status : Enter Failed",

                    reply

                )

            # -------------------------
            # Tab
            # -------------------------

            elif intent == "press_tab":

                reply = self.speak(
                    "Pressing Tab."
                )

                success = self.keyboard.press_key(
                    "tab"
                )

                return self.response(

                    success,

                    "Status : Tab Pressed",

                    "Status : Tab Failed",

                    reply

                )

            # -------------------------
            # Arrow Up
            # -------------------------

            elif intent == "arrow_up":

                reply = self.speak(
                    "Moving up."
                )

                success = self.keyboard.arrow_up()

                return self.response(

                    success,

                    "Status : Arrow Up Pressed",

                    "Status : Arrow Up Failed",

                    reply

                )

            # -------------------------
            # Arrow Down
            # -------------------------

            elif intent == "arrow_down":

                reply = self.speak(
                    "Moving down."
                )

                success = self.keyboard.arrow_down()

                return self.response(

                    success,

                    "Status : Arrow Down Pressed",

                    "Status : Arrow Down Failed",

                    reply

                )

            # -------------------------
            # Arrow Left
            # -------------------------

            elif intent == "arrow_left":

                reply = self.speak(
                    "Moving left."
                )

                success = self.keyboard.arrow_left()

                return self.response(

                    success,

                    "Status : Arrow Left Pressed",

                    "Status : Arrow Left Failed",

                    reply

                )

            # -------------------------
            # Arrow Right
            # -------------------------

            elif intent == "arrow_right":

                reply = self.speak(
                    "Moving right."
                )

                success = self.keyboard.arrow_right()

                return self.response(

                    success,

                    "Status : Arrow Right Pressed",

                    "Status : Arrow Right Failed",

                    reply

                )

            # -------------------------
            # Backspace
            # -------------------------

            elif intent == "backspace":

                reply = self.speak(
                    "Pressing Backspace."
                )

                success = self.keyboard.backspace()

                return self.response(

                    success,

                    "Status : Backspace Pressed",

                    "Status : Backspace Failed",

                    reply

                )


            # -------------------------
            # Delete
            # -------------------------

            elif intent == "delete":

                reply = self.speak(
                    "Pressing Delete."
                )

                success = self.keyboard.delete()

                return self.response(

                    success,

                    "Status : Delete Pressed",

                    "Status : Delete Failed",

                    reply

                )

            # -------------------------
            # Home
            # -------------------------

            elif intent == "home":

                reply = self.speak(
                    "Pressing Home."
                )

                success = self.keyboard.home()

                return self.response(

                    success,

                    "Status : Home Pressed",

                    "Status : Home Failed",

                    reply

                )

            # -------------------------
            # End
            # -------------------------

            elif intent == "end":

                reply = self.speak(
                    "Pressing End."
                )

                success = self.keyboard.end()

                return self.response(

                    success,

                    "Status : End Pressed",

                    "Status : End Failed",

                    reply

                )

            # -------------------------
            # Page Up
            # -------------------------

            elif intent == "page_up":

                reply = self.speak(
                    "Pressing Page Up."
                )

                success = self.keyboard.page_up()

                return self.response(

                    success,

                    "Status : Page Up Pressed",

                    "Status : Page Up Failed",

                    reply

                )

            # -------------------------
            # Page Down
            # -------------------------

            elif intent == "page_down":

                reply = self.speak(
                    "Pressing Page Down."
                )

                success = self.keyboard.page_down()

                return self.response(

                    success,

                    "Status : Page Down Pressed",

                    "Status : Page Down Failed",

                    reply

                )

            # -------------------------
            # Escape
            # -------------------------

            elif intent == "escape":

                reply = self.speak(
                    "Pressing Escape."
                )

                success = self.keyboard.escape()

                return self.response(

                    success,

                    "Status : Escape Pressed",

                    "Status : Escape Failed",

                    reply

                )

            # -------------------------
            # Space
            # -------------------------

            elif intent == "space":

                reply = self.speak(
                    "Pressing Space."
                )

                success = self.keyboard.space()

                return self.response(

                    success,

                    "Status : Space Pressed",

                    "Status : Space Failed",

                    reply

                )

            # -------------------------
            # Select All
            # -------------------------

            elif intent == "select_all":

                reply = self.speak(
                    "Selecting all."
                )

                success = self.keyboard.hotkey(
                    "ctrl",
                    "a"
                )

                return self.response(

                    success,

                    "Status : Select All Completed",

                    "Status : Select All Failed",

                    reply

                )

            # -------------------------
            # Save
            # -------------------------

            elif intent == "save_file":

                reply = self.speak(
                    "Saving file."
                )

                success = self.keyboard.hotkey(
                    "ctrl",
                    "s"
                )

                return self.response(

                    success,

                    "Status : File Saved",

                    "Status : Save Failed",

                    reply

                )

            # -------------------------
            # Print
            # -------------------------

            elif intent == "print_file":

                reply = self.speak(
                    "Opening print dialog."
                )

                success = self.keyboard.hotkey(
                    "ctrl",
                    "p"
                )

                return self.response(

                    success,

                    "Status : Print Dialog Opened",

                    "Status : Print Failed",

                    reply

                )
            # -------------------------
            # Left Click
            # -------------------------

            elif intent == "left_click":

                reply = self.speak(
                    "Left clicking."
                )

                success = self.mouse.left_click()

                return self.response(

                    success,

                    "Status : Left Click Completed",

                    "Status : Left Click Failed",

                    reply

                )

            # -------------------------
            # Right Click
            # -------------------------

            elif intent == "right_click":

                reply = self.speak(
                    "Right clicking."
                )

                success = self.mouse.right_click()

                return self.response(

                    success,

                    "Status : Right Click Completed",

                    "Status : Right Click Failed",

                    reply

                )

            # -------------------------
            # Double Click
            # -------------------------

            elif intent == "double_click":

                reply = self.speak(
                    "Double clicking."
                )

                success = self.mouse.double_click()

                return self.response(

                    success,

                    "Status : Double Click Completed",

                    "Status : Double Click Failed",

                    reply

                )

            # -------------------------
            # Scroll Up
            # -------------------------

            elif intent == "scroll_up":

                reply = self.speak(
                    "Scrolling up."
                )

                success = self.mouse.scroll_up()

                return self.response(

                    success,

                    "Status : Scroll Up Completed",

                    "Status : Scroll Up Failed",

                    reply

                )

            # -------------------------
            # Scroll Down
            # -------------------------

            elif intent == "scroll_down":

                reply = self.speak(
                    "Scrolling down."
                )

                success = self.mouse.scroll_down()

                return self.response(

                    success,

                    "Status : Scroll Down Completed",

                    "Status : Scroll Down Failed",

                    reply

                )

            # -------------------------
            # Minimize Window
            # -------------------------

            elif intent == "minimize_window":

                reply = self.speak(
                    "Minimizing window."
                )

                success = self.window.minimize_window()

                return self.response(

                    success,

                    "Status : Window Minimized",

                    "Status : Minimize Failed",

                    reply

                )

            # -------------------------
            # Maximize Window
            # -------------------------

            elif intent == "maximize_window":

                reply = self.speak(
                    "Maximizing window."
                )

                success = self.window.maximize_window()

                return self.response(

                    success,

                    "Status : Window Maximized",

                    "Status : Maximize Failed",

                    reply

                )

            # -------------------------
            # Restore Window
            # -------------------------

            elif intent == "restore_window":

                reply = self.speak(
                    "Restoring window."
                )

                success = self.window.restore_window()

                return self.response(

                    success,

                    "Status : Window Restored",

                    "Status : Restore Failed",

                    reply

                )


            # -------------------------
            # Close Window
            # -------------------------

            elif intent == "close_window":

                reply = self.speak(
                    "Closing window."
                )

                success = self.window.close_window()

                return self.response(

                    success,

                    "Status : Window Closed",

                    "Status : Close Failed",

                    reply

                )

            # -------------------------
            # Volume Up
            # -------------------------

            elif intent == "volume_up":

                reply = self.speak(
                    "Increasing volume."
                )

                success = self.system.volume_up()

                return self.response(

                    success,

                    "Status : Volume Increased",

                    "Status : Volume Up Failed",

                    reply

                )

            # -------------------------
            # Volume Down
            # -------------------------

            elif intent == "volume_down":

                reply = self.speak(
                    "Decreasing volume."
                )

                success = self.system.volume_down()

                return self.response(

                    success,

                    "Status : Volume Decreased",

                    "Status : Volume Down Failed",

                    reply

                )

            # -------------------------
            # Set Exact Volume
            # -------------------------

            elif intent == "set_volume":

                if entity is None:

                    message = (
                        "Please specify the volume percentage."
                    )

                    self.tts.speak(message)

                    return self.response(
                        False,
                        "",
                        "Status : Volume Value Missing",
                        message
                    )

                try:

                    volume = int(entity)

                except (TypeError, ValueError):

                    message = (
                        "I could not understand the volume value."
                    )

                    self.tts.speak(message)

                    return self.response(
                        False,
                        "",
                        "Status : Invalid Volume",
                        message
                    )

                if not 0 <= volume <= 100:

                    message = (
                        "Volume must be between 0 and 100 percent."
                    )

                    self.tts.speak(message)

                    return self.response(
                        False,
                        "",
                        "Status : Invalid Volume",
                        message
                    )

                # ---------------------------------
                # Read Current Volume
                # ---------------------------------

                current_volume = self.system.get_volume()

                if current_volume is None:

                    message = (
                        "I could not read the current volume."
                    )

                    self.tts.speak(message)

                    return self.response(
                        False,
                        "",
                        "Status : Volume Read Failed",
                        message
                    )

                # ---------------------------------
                # Determine Message
                # ---------------------------------

                if volume > current_volume:

                    message = (
                        f"Increasing volume to {volume} percent."
                    )

                elif volume < current_volume:

                    message = (
                        f"Decreasing volume to {volume} percent."
                    )

                else:

                    message = (
                        f"Volume is already at {volume} percent."
                    )

                # ---------------------------------
                # Apply Volume
                # ---------------------------------

                success = self.system.set_volume(volume)

                # ---------------------------------
                # Final Response
                # ---------------------------------

                if success:

                    self.tts.speak(message)

                else:

                    message = (
                        "Unable to set the volume."
                    )

                    self.tts.speak(message)

                return self.response(

                    success,

                    "Status : Volume Set",

                    "Status : Volume Set Failed",

                    message

                )

            # -------------------------
            # Mute
            # -------------------------

            elif intent == "mute":

                reply = self.speak(
                    "Muting audio."
                )

                success = self.system.mute()

                return self.response(

                    success,

                    "Status : Audio Toggled",

                    "Status : Mute Failed",

                    reply

                )

            # -------------------------
            # Brightness Up
            # -------------------------

            elif intent == "brightness_up":

                reply = self.speak(
                    "Increasing brightness."
                )

                success = self.system.brightness_up()

                return self.response(

                    success,

                    "Status : Brightness Increased",

                    "Status : Brightness Up Failed",

                    reply

                )

            # -------------------------
            # Brightness Down
            # -------------------------

            elif intent == "brightness_down":

                reply = self.speak(
                    "Decreasing brightness."
                )

                success = self.system.brightness_down()

                return self.response(

                    success,

                    "Status : Brightness Decreased",

                    "Status : Brightness Down Failed",

                    reply

                )

            # -------------------------
            # Set Exact Brightness
            # -------------------------

            elif intent == "set_brightness":

                if entity is None:

                    message = (
                        "Please specify the brightness percentage."
                    )

                    self.tts.speak(message)

                    return self.response(
                        False,
                        "",
                        "Status : Brightness Value Missing",
                        message
                    )

                try:

                    brightness = int(entity)

                except (TypeError, ValueError):

                    message = (
                        "I could not understand the brightness value."
                    )

                    self.tts.speak(message)

                    return self.response(
                        False,
                        "",
                        "Status : Invalid Brightness",
                        message
                    )

                if not 0 <= brightness <= 100:

                    message = (
                        "Brightness must be between 0 and 100 percent."
                    )

                    self.tts.speak(message)

                    return self.response(
                        False,
                        "",
                        "Status : Invalid Brightness",
                        message
                    )

                # ---------------------------------
                # Read Current Brightness
                # ---------------------------------

                current_brightness = (
                    self.system.get_brightness()
                )

                if current_brightness is None:

                    message = (
                        "I could not read the current brightness."
                    )

                    self.tts.speak(message)

                    return self.response(
                        False,
                        "",
                        "Status : Brightness Read Failed",
                        message
                    )

                # ---------------------------------
                # Determine Message
                # ---------------------------------

                if brightness > current_brightness:

                    message = (
                        f"Increasing brightness to "
                        f"{brightness} percent."
                    )

                elif brightness < current_brightness:

                    message = (
                        f"Decreasing brightness to "
                        f"{brightness} percent."
                    )

                else:

                    message = (
                        f"Brightness is already at "
                        f"{brightness} percent."
                    )

                # ---------------------------------
                # Apply Brightness
                # ---------------------------------

                success = self.system.set_brightness(
                    brightness
                )

                # ---------------------------------
                # Final Response
                # ---------------------------------

                if success:

                    self.tts.speak(message)

                else:

                    message = (
                        "Unable to set the brightness."
                    )

                    self.tts.speak(message)

                return self.response(

                    success,

                    "Status : Brightness Set",

                    "Status : Brightness Set Failed",

                    message

                )

            # -------------------------
            # Lock Screen
            # -------------------------

            elif intent == "lock_screen":

                reply = self.speak(
                    "Locking computer."
                )

                success = self.system.lock_screen()

                return self.response(

                    success,

                    "Status : System Locked",

                    "Status : Lock Failed",

                    reply

                )

            # -------------------------
            # Shutdown
            # -------------------------

            elif intent == "shutdown":

                if not self.confirm_action(
                    "Are you sure you want to shut down the computer?"
                ):

                    reply = self.speak(
                        "Shutdown cancelled."
                    )

                    return self.response(

                        False,

                        "",

                        "Status : Shutdown Cancelled",

                        reply

                    )

                reply = self.speak(
                    "Shutting down the computer."
                )

                success = self.system.shutdown()

                return self.response(

                    success,

                    "Status : System Shutdown",

                    "Status : Shutdown Failed",

                    reply

                )

            # -------------------------
            # Restart
            # -------------------------

            elif intent == "restart":

                if not self.confirm_action(
                    "Are you sure you want to restart the computer?"
                ):

                    reply = self.speak(
                        "Restart cancelled."
                    )

                    return self.response(

                        False,

                        "",

                        "Status : Restart Cancelled",

                        reply

                    )

                reply = self.speak(
                    "Restarting the computer."
                )

                success = self.system.restart()

                return self.response(

                    success,

                    "Status : System Restarting",

                    "Status : Restart Failed",

                    reply

                )

            # -------------------------
            # Sleep
            # -------------------------

            elif intent == "sleep":

                if not self.confirm_action(
                    "Do you want to put the computer to sleep?"
                ):

                    reply = self.speak(
                        "Sleep cancelled."
                    )

                    return self.response(

                        False,

                        "",

                        "Status : Sleep Cancelled",

                        reply

                    )

                reply = self.speak(
                    "Putting the computer to sleep."
                )

                success = self.system.sleep()

                return self.response(

                    success,

                    "Status : System Sleeping",

                    "Status : Sleep Failed",

                    reply

                )

            # -------------------------
            # Sign Out
            # -------------------------

            elif intent == "sign_out":

                if not self.confirm_action(
                    "Are you sure you want to sign out?"
                ):

                    reply = self.speak(
                        "Sign out cancelled."
                    )

                    return self.response(

                        False,

                        "",

                        "Status : Sign Out Cancelled",

                        reply

                    )

                reply = self.speak(
                    "Signing out."
                )

                success = self.system.sign_out()

                return self.response(

                    success,

                    "Status : Signing Out",

                    "Status : Sign Out Failed",

                    reply

                )

            # -------------------------
            # Open Windows Settings
            # -------------------------

            elif intent == "open_settings":

                reply = self.speak(
                    "Opening Windows Settings."
                )

                success = self.system.open_settings()

                return self.response(

                    success,

                    "Status : Settings Opened",

                    "Status : Settings Failed",

                    reply

                )

            # -------------------------
            # Open Command Prompt
            # -------------------------

            elif intent == "open_cmd":

                reply = self.speak(
                    "Opening Command Prompt."
                )

                success = self.system.open_cmd()

                return self.response(

                    success,

                    "Status : Command Prompt Opened",

                    "Status : Command Prompt Failed",

                    reply

                )

            # -------------------------
            # Open PowerShell
            # -------------------------

            elif intent == "open_powershell":

                reply = self.speak(
                    "Opening PowerShell."
                )

                success = self.system.open_powershell()

                return self.response(

                    success,

                    "Status : PowerShell Opened",

                    "Status : PowerShell Failed",

                    reply

                )

            # -------------------------
            # Open Control Panel
            # -------------------------

            elif intent == "open_control_panel":

                reply = self.speak(
                    "Opening Control Panel."
                )

                success = self.system.open_control_panel()

                return self.response(

                    success,

                    "Status : Control Panel Opened",

                    "Status : Control Panel Failed",

                    reply

                )

            # -------------------------
            # Start Screen Recording
            # -------------------------

            elif intent == "start_screen_recording":

                if self.screen_recorder.is_recording():

                    reply = self.speak(
                        "Screen recording is already running."
                    )

                    return self.response(

                        False,

                        "",

                        "Status : Recording Already Active",

                        reply

                    )

                success = (
                    self.screen_recorder
                    .start_recording()
                )

                if success:

                    reply = self.speak(
                        "Screen recording started."
                    )

                else:

                    reply = self.speak(
                        "Unable to start screen recording."
                    )

                return self.response(

                    success,

                    "Status : Screen Recording Started",

                    "Status : Screen Recording Failed",

                    reply

                )

            # -------------------------
            # Stop Screen Recording
            # -------------------------

            elif intent == "stop_screen_recording":

                if not self.screen_recorder.is_recording():

                    reply = self.speak(
                        "There is no active screen recording."
                    )

                    return self.response(

                        False,

                        "",

                        "Status : No Active Recording",

                        reply

                    )

                output_path = (
                    self.screen_recorder
                    .stop_recording()
                )

                if output_path:

                    filename = (
                        output_path
                        .replace("\\", "/")
                        .split("/")[-1]
                    )

                    reply = self.speak(
                        f"Screen recording saved as {filename}."
                    )

                    return self.response(

                        True,

                        "Status : Screen Recording Saved",

                        "Status : Screen Recording Save Failed",

                        reply

                    )

                reply = self.speak(
                    "Unable to save the screen recording."
                )

                return self.response(

                    False,

                    "",

                    "Status : Screen Recording Save Failed",

                    reply

                )

            # -------------------------
            # Open Camera
            # -------------------------

            elif intent == "open_camera":

                reply = self.speak(
                    "Opening camera."
                )

                success = self.system.open_camera()

                return self.response(

                    success,

                    "Status : Camera Opened",

                    "Status : Camera Failed",

                    reply

                )

            # -------------------------
            # Capture Photo
            # -------------------------

            elif intent == "capture_photo":

                reply = self.speak(
                    "Capturing photo."
                )

                photo_path = self.system.capture_photo()

                success = bool(photo_path)

                if success:

                    reply = self.speak(
                        "Photo captured successfully."
                    )

                else:

                    reply = self.speak(
                        "Unable to capture photo."
                    )

                return self.response(

                    success,

                    "Status : Photo Captured",

                    "Status : Photo Capture Failed",

                    reply

                )

            # -------------------------
            # Screenshot
            # -------------------------

            elif intent == "take_screenshot":

                reply = self.speak(
                    "Taking screenshot."
                )

                success = self.system.take_screenshot()

                return self.response(

                    bool(success),

                    "Status : Screenshot Saved",

                    "Status : Screenshot Failed",

                    reply

                )

            # -------------------------
            # Task Manager
            # -------------------------

            elif intent == "open_task_manager":

                reply = self.speak(
                    "Opening Task Manager."
                )

                success = self.system.open_task_manager()

                return self.response(

                    success,

                    "Status : Task Manager Opened",

                    "Status : Task Manager Failed",

                    reply

                )

            # -------------------------
            # File Explorer
            # -------------------------

            elif intent == "open_file_explorer":

                reply = self.speak(
                    "Opening File Explorer."
                )

                success = self.system.open_file_explorer()

                return self.response(

                    success,

                    "Status : File Explorer Opened",

                    "Status : File Explorer Failed",

                    reply

                )
            
            # ==================================================
            # FILE SYSTEM AGENT
            # ==================================================

            # -------------------------
            # Open File
            # -------------------------

            elif (
                intent == "open_file"
                and entity
            ):

                filename = (
                    entity.get("filename")
                    or entity.get("source")
                    or entity.get("file_path")
                    if isinstance(entity, dict)
                    else str(entity)
                )

                resolution = self.resolve_file_candidate(
                    filename,
                    selection
                )

                if resolution.get("requires_selection"):

                    return self.multiple_target_response(
                        resolution,
                        "open_file",
                        target_type="file",
                        pending_payload=self._current_selection_payload
                    )

                if not resolution.get("success"):

                    reply = self.speak(
                        resolution.get(
                            "message",
                            f"File not found: {filename}"
                        )
                    )

                    return self.response(
                        False,
                        "",
                        "Status : File Not Found",
                        reply
                    )

                reply = self.speak(
                    f"Opening {filename}"
                )

                result = self.file_system_agent.execute(
                    "open_file",
                    {
                        "entity": filename,
                        "selection": selection
                    }
                )

                success = bool(
                    result.get("success")
                )

                if success:
                    self.keyboard.activate_window()

                if not success:
                    reply = self.speak(
                        result.get(
                            "message",
                            "Unable to open the file."
                        )
                    )

                return self.response(
                    success,
                    "Status : File Opened",
                    "Status : File Open Failed",
                    reply
                )

            # -------------------------
            # Open Folder
            # -------------------------

            elif (
                intent == "open_folder"
                and entity
            ):

                folder_name = (
                    entity.get("folder")
                    or entity.get("folder_name")
                    or entity.get("folder_path")
                    or entity.get("source")
                    if isinstance(entity, dict)
                    else str(entity)
                )

                resolution = self.resolve_folder_selection(
                    folder_name,
                    selection
                )

                if resolution.get("requires_selection"):

                    return self.multiple_target_response(
                        resolution,
                        "open_folder",
                        target_type="folder",
                        pending_payload=self._current_selection_payload
                    )

                if not resolution.get("success"):

                    reply = self.speak(
                        resolution.get(
                            "message",
                            f"Folder not found: {folder_name}"
                        )
                    )

                    return self.response(
                        False,
                        "",
                        "Status : Folder Not Found",
                        reply
                    )

                selected_path = resolution.get(
                    "path",
                    folder_name
                )

                reply = self.speak(
                    f"Opening {folder_name}"
                )

                result = self.file_system_agent.execute(
                    "open_folder",
                    {
                        "entity": selected_path,
                        "selection": selection
                    }
                )

                success = bool(
                    result.get("success")
                )

                if success:
                    self.keyboard.activate_window()

                else:
                    reply = self.speak(
                        result.get(
                            "message",
                            "Unable to open the folder."
                        )
                    )

                return self.response(
                    success,
                    "Status : Folder Opened",
                    "Status : Folder Not Found",
                    reply
                )

            # -------------------------
            # Create File
            # -------------------------

            elif (
                intent == "create_file"
                and entity
            ):

                reply = self.speak(
                    f"Creating {entity}"
                )

                result = self.file_system_agent.execute(
                    "create_file",
                    {
                        "entity": entity
                    }
                )

                success = bool(
                    result.get("success")
                )

                if success:

                    reply = self.speak(
                        "File created successfully."
                    )

                else:

                    reply = self.speak(
                        result.get(
                            "message",
                            "Unable to create the file."
                        )
                    )

                return self.response(

                    success,

                    "Status : File Created",

                    "Status : Create Failed",

                    reply

                )

            # -------------------------
            # Delete File
            # -------------------------

            elif (
                intent == "delete_file"
                and entity
            ):

                filename = (
                    entity.get("filename")
                    or entity.get("source")
                    or entity.get("file_path")
                    if isinstance(entity, dict)
                    else str(entity)
                )

                resolution = self.resolve_file_candidate(
                    filename,
                    selection
                )

                if resolution.get(
                    "requires_selection"
                ):

                    return self.multiple_file_response(
                        resolution,
                        "delete_file",
                        pending_payload=self._current_selection_payload
                    )

                if not resolution.get("success"):

                    reply = self.speak(
                        resolution.get(
                            "message",
                            f"File not found: {filename}"
                        )
                    )

                    return self.response(
                        False,
                        "",
                        "Status : File Not Found",
                        reply
                    )

                # ---------------------------------
                # Confirmation
                # ---------------------------------

                if not skip_confirmation:

                    return self.confirmation_response(
                        "Do you want to delete this file?",
                        intent="delete_file",
                        entity=entity,
                        typed_text=typed_text,
                        browser=browser,
                        website=website,
                        search_query=search_query,
                        profile=profile,
                        user_text=user_text,
                        multi_command=multi_command,
                        selection=selection,
                        confirmation_action="delete_file",
                    )

                # ---------------------------------
                # Execute after YES
                # ---------------------------------

                result = self.file_system_agent.execute(
                    "delete_file",
                    {
                        "entity": filename,
                        "selection": selection
                    }
                )

                success = bool(
                    result.get("success")
                )

                if success:

                    reply = self.speak(
                        "File deleted successfully."
                    )

                else:

                    reply = self.speak(
                        result.get(
                            "message",
                            "Unable to delete the file."
                        )
                    )

                return self.response(
                    success,
                    "Status : File Deleted",
                    "Status : Delete Failed",
                    reply
                )

            # -------------------------
            # Rename File
            # -------------------------

            elif (
                intent == "rename_file"
                and entity
            ):

                if isinstance(entity, dict):

                    old_name = (
                        entity.get("old_name")
                        or entity.get("filename")
                        or entity.get("source")
                        or entity.get("file_path")
                    )

                    new_name = (
                        entity.get("new_name")
                        or entity.get("newName")
                        or entity.get("destination_name")
                    )

                else:

                    old_name = str(entity)
                    new_name = None

                if not old_name or not new_name:

                    reply = self.speak(
                        "I need both the current file name and the new file name."
                    )

                    return self.response(
                        False,
                        "",
                        "Status : Rename Information Missing",
                        reply
                    )

                resolution = self.resolve_file_candidate(
                    old_name,
                    selection
                )

                if resolution.get("requires_selection"):

                    return self.multiple_file_response(
                        resolution,
                        "rename_file",
                        pending_payload=self._current_selection_payload
                    )

                if not resolution.get("success"):

                    reply = self.speak(
                        resolution.get(
                            "message",
                            f"File not found: {old_name}"
                        )
                    )

                    return self.response(
                        False,
                        "",
                        "Status : File Not Found",
                        reply
                    )

                # ---------------------------------
                # Confirmation
                # ---------------------------------

                if not skip_confirmation:

                    return self.confirmation_response(
                        (
                            f"Do you want to rename "
                            f"{old_name} to {new_name}?"
                        ),
                        intent="rename_file",
                        entity=entity,
                        typed_text=typed_text,
                        browser=browser,
                        website=website,
                        search_query=search_query,
                        profile=profile,
                        user_text=user_text,
                        multi_command=multi_command,
                        selection=selection,
                        confirmation_action="rename_file",
                    )

                result = self.file_system_agent.execute(
                    "rename_file",
                    {
                        "source": old_name,
                        "new_name": new_name,
                        "selection": selection
                    }
                )

                success = bool(
                    result.get("success")
                )

                if success:

                    reply = self.speak(
                        "File renamed successfully."
                    )

                else:

                    reply = self.speak(
                        result.get(
                            "message",
                            "Unable to rename the file."
                        )
                    )

                return self.response(
                    success,
                    "Status : File Renamed",
                    "Status : Rename Failed",
                    reply
                )

            # -------------------------
            # Copy File
            # -------------------------

            elif (
                intent == "copy_file"
                and entity
            ):

                if isinstance(entity, dict):

                    filename = (
                        entity.get("filename")
                        or entity.get("source")
                        or entity.get("file_path")
                    )

                    destination = (
                        entity.get("destination")
                        or entity.get("destination_folder")
                        or entity.get("target")
                    )

                else:

                    filename = str(entity)
                    destination = None

                if not filename or not destination:

                    reply = self.speak(
                        "I need the file and destination folder."
                    )

                    return self.response(
                        False,
                        "",
                        "Status : Copy Information Missing",
                        reply
                    )

                resolution = self.resolve_file_candidate(
                    filename,
                    selection
                )

                if resolution.get("requires_selection"):

                    return self.multiple_file_response(
                        resolution,
                        "copy_file",
                        pending_payload=self._current_selection_payload
                    )

                if not resolution.get("success"):

                    reply = self.speak(
                        resolution.get(
                            "message",
                            f"File not found: {filename}"
                        )
                    )

                    return self.response(
                        False,
                        "",
                        "Status : File Not Found",
                        reply
                    )

                # ---------------------------------
                # Confirmation
                # ---------------------------------

                if not skip_confirmation:

                    return self.confirmation_response(
                        "Do you want to copy this file?",
                        intent="copy_file",
                        entity=entity,
                        typed_text=typed_text,
                        browser=browser,
                        website=website,
                        search_query=search_query,
                        profile=profile,
                        user_text=user_text,
                        multi_command=multi_command,
                        selection=selection,
                        confirmation_action="copy_file",
                    )

                result = self.file_system_agent.execute(
                    "copy_file",
                    {
                        "source": filename,
                        "destination": destination,
                        "selection": selection
                    }
                )

                success = bool(
                    result.get("success")
                )

                if success:

                    reply = self.speak(
                        "File copied successfully."
                    )

                else:

                    reply = self.speak(
                        result.get(
                            "message",
                            "Unable to copy the file."
                        )
                    )

                return self.response(
                    success,
                    "Status : File Copied",
                    "Status : Copy Failed",
                    reply
                )

            # -------------------------
            # Move File
            # -------------------------

            elif (
                intent == "move_file"
                and entity
            ):

                if isinstance(entity, dict):

                    filename = (
                        entity.get("filename")
                        or entity.get("source")
                        or entity.get("file_path")
                    )

                    destination = (
                        entity.get("destination")
                        or entity.get("destination_folder")
                        or entity.get("target")
                    )

                else:

                    filename = str(entity)
                    destination = None

                if not filename or not destination:

                    reply = self.speak(
                        "I need the file and destination folder."
                    )

                    return self.response(
                        False,
                        "",
                        "Status : Move Information Missing",
                        reply
                    )

                resolution = self.resolve_file_candidate(
                    filename,
                    selection
                )

                if resolution.get("requires_selection"):

                    return self.multiple_file_response(
                        resolution,
                        "move_file",
                        pending_payload=self._current_selection_payload
                    )

                if not resolution.get("success"):

                    reply = self.speak(
                        resolution.get(
                            "message",
                            f"File not found: {filename}"
                        )
                    )

                    return self.response(
                        False,
                        "",
                        "Status : File Not Found",
                        reply
                    )

                # ---------------------------------
                # Confirmation
                # ---------------------------------

                if not skip_confirmation:

                    return self.confirmation_response(
                        "Do you want to move this file?",
                        intent="move_file",
                        entity=entity,
                        typed_text=typed_text,
                        browser=browser,
                        website=website,
                        search_query=search_query,
                        profile=profile,
                        user_text=user_text,
                        multi_command=multi_command,
                        selection=selection,
                        confirmation_action="move_file",
                    )

                result = self.file_system_agent.execute(
                    "move_file",
                    {
                        "source": filename,
                        "destination": destination,
                        "selection": selection
                    }
                )

                success = bool(
                    result.get("success")
                )

                if success:

                    reply = self.speak(
                        "File moved successfully."
                    )

                else:

                    reply = self.speak(
                        result.get(
                            "message",
                            "Unable to move the file."
                        )
                    )

                return self.response(
                    success,
                    "Status : File Moved",
                    "Status : Move Failed",
                    reply
                )

            # -------------------------
            # Compress File
            # -------------------------

            elif (
                intent == "compress_file"
                and entity
            ):

                filename = (
                    entity.get("filename")
                    or entity.get("source")
                    or entity.get("file_path")
                    if isinstance(entity, dict)
                    else str(entity)
                )

                resolution = self.resolve_file_candidate(
                    filename,
                    selection
                )

                if resolution.get("requires_selection"):

                    return self.multiple_file_response(
                        resolution,
                        "compress_file",
                        pending_payload=self._current_selection_payload
                    )

                if not resolution.get("success"):

                    reply = self.speak(
                        resolution.get(
                            "message",
                            f"File not found: {filename}"
                        )
                    )

                    return self.response(
                        False,
                        "",
                        "Status : File Not Found",
                        reply
                    )

                # ---------------------------------
                # Confirmation
                # ---------------------------------

                if not skip_confirmation:

                    return self.confirmation_response(
                        "Do you want to compress this file?",
                        intent="compress_file",
                        entity=entity,
                        typed_text=typed_text,
                        browser=browser,
                        website=website,
                        search_query=search_query,
                        profile=profile,
                        user_text=user_text,
                        multi_command=multi_command,
                        selection=selection,
                        confirmation_action="compress_file",
                    )

                result = self.file_system_agent.execute(
                    "compress_file",
                    {
                        "entity": filename,
                        "selection": selection
                    }
                )

                success = bool(
                    result.get("success")
                )

                if success:

                    reply = self.speak(
                        "ZIP archive created successfully."
                    )

                else:

                    reply = self.speak(
                        result.get(
                            "message",
                            "Unable to compress the file."
                        )
                    )

                return self.response(
                    success,
                    "Status : ZIP Created",
                    "Status : Compression Failed",
                    reply
                )

            # -------------------------
            # Extract ZIP
            # -------------------------

            elif (
                intent == "extract_zip"
                and entity
            ):

                filename = (
                    entity.get("filename")
                    or entity.get("source")
                    or entity.get("file_path")
                    or entity.get("zip_file")
                    if isinstance(entity, dict)
                    else str(entity)
                )

                resolution = self.resolve_file_candidate(
                    filename,
                    selection
                )

                if resolution.get("requires_selection"):

                    return self.multiple_file_response(
                        resolution,
                        "extract_zip",
                        pending_payload=self._current_selection_payload
                    )

                if not resolution.get("success"):

                    reply = self.speak(
                        resolution.get(
                            "message",
                            f"ZIP file not found: {filename}"
                        )
                    )

                    return self.response(
                        False,
                        "",
                        "Status : ZIP File Not Found",
                        reply
                    )

                # ---------------------------------
                # Confirmation
                # ---------------------------------

                if not skip_confirmation:

                    return self.confirmation_response(
                        "Do you want to extract this archive?",
                        intent="extract_zip",
                        entity=entity,
                        typed_text=typed_text,
                        browser=browser,
                        website=website,
                        search_query=search_query,
                        profile=profile,
                        user_text=user_text,
                        multi_command=multi_command,
                        selection=selection,
                        confirmation_action="extract_zip",
                    )

                result = self.file_system_agent.execute(
                    "extract_zip",
                    {
                        "entity": filename,
                        "selection": selection
                    }
                )

                success = bool(
                    result.get("success")
                )

                if success:

                    reply = self.speak(
                        "ZIP archive extracted successfully."
                    )

                else:

                    reply = self.speak(
                        result.get(
                            "message",
                            "Unable to extract the ZIP archive."
                        )
                    )

                return self.response(
                    success,
                    "Status : ZIP Extracted",
                    "Status : Extraction Failed",
                    reply
                )

            # ==================================================
            # FOLDER SYSTEM OPERATIONS
            # ==================================================

            # -------------------------
            # Create Folder
            # -------------------------

            elif (
                intent == "create_folder"
                and entity
            ):

                # ---------------------------------
                # Create directly
                # No confirmation required
                # ---------------------------------

                reply = self.speak(
                    f"Creating {entity} folder."
                )

                result = self.file_system_agent.execute(
                    "create_folder",
                    {
                        "entity": entity
                    }
                )

                success = bool(
                    result.get("success")
                )

                if success:

                    reply = self.speak(
                        "Folder created successfully."
                    )

                else:

                    reply = self.speak(
                        result.get(
                            "message",
                            "Unable to create the folder."
                        )
                    )

                return self.response(
                    success,
                    "Status : Folder Created",
                    "Status : Create Failed",
                    reply
                )


            # -------------------------
            # Rename Folder
            # -------------------------

            elif (
                intent == "rename_folder"
                and entity
            ):

                if isinstance(entity, dict):

                    source = (
                        entity.get("source")
                        or entity.get("folder")
                        or entity.get("folder_path")
                        or entity.get("old_name")
                    )

                    new_name = (
                        entity.get("new_name")
                        or entity.get("newName")
                        or entity.get("destination_name")
                    )

                else:

                    source = str(entity)
                    new_name = None

                if not source or not new_name:

                    reply = self.speak(
                        "I need both the current folder and the new folder name."
                    )

                    return self.response(
                        False,
                        "",
                        "Status : Rename Information Missing",
                        reply
                    )

                resolution = self.resolve_folder_selection(
                    source,
                    selection
                )

                if resolution.get("requires_selection"):

                    return self.multiple_target_response(
                        resolution,
                        "rename_folder",
                        target_type="folder",
                        pending_payload=self._current_selection_payload
                    )

                if not resolution.get("success"):

                    reply = self.speak(
                        resolution.get(
                            "message",
                            f"Folder not found: {source}"
                        )
                    )

                    return self.response(
                        False,
                        "",
                        "Status : Folder Not Found",
                        reply
                    )

                resolved_source = resolution.get(
                    "path",
                    source
                )

                if not skip_confirmation:

                    return self.confirmation_response(
                        (
                            f"Do you want to rename "
                            f"{Path(resolved_source).name} "
                            f"to {new_name}?"
                        ),
                        intent="rename_folder",
                        entity=entity,
                        typed_text=typed_text,
                        browser=browser,
                        website=website,
                        search_query=search_query,
                        profile=profile,
                        user_text=user_text,
                        multi_command=multi_command,
                        selection=selection,
                        confirmation_action="rename_folder",
                    )

                result = self.file_system_agent.execute(
                    "rename_folder",
                    {
                        "source": resolved_source,
                        "new_name": new_name
                    }
                )

                success = bool(
                    result.get("success")
                )

                if success:

                    reply = self.speak(
                        "Folder renamed successfully."
                    )

                else:

                    reply = self.speak(
                        result.get(
                            "message",
                            "Unable to rename the folder."
                        )
                    )

                return self.response(
                    success,
                    "Status : Folder Renamed",
                    "Status : Rename Failed",
                    reply
                )

            # -------------------------
            # Delete Folder
            # -------------------------

            elif (
                intent == "delete_folder"
                and entity
            ):

                folder_name = (
                    entity.get("folder")
                    or entity.get("folder_name")
                    or entity.get("folder_path")
                    or entity.get("source")
                    if isinstance(entity, dict)
                    else str(entity)
                )

                resolution = self.resolve_folder_selection(
                    folder_name,
                    selection
                )

                if resolution.get("requires_selection"):

                    return self.multiple_target_response(
                        resolution,
                        "delete_folder",
                        target_type="folder",
                        pending_payload=self._current_selection_payload
                    )

                if not resolution.get("success"):

                    reply = self.speak(
                        resolution.get(
                            "message",
                            f"Folder not found: {folder_name}"
                        )
                    )

                    return self.response(
                        False,
                        "",
                        "Status : Folder Not Found",
                        reply
                    )

                resolved_source = resolution.get(
                    "path",
                    folder_name
                )

                if not skip_confirmation:

                    return self.confirmation_response(
                        (
                            f"Do you want to delete the folder "
                            f"{Path(resolved_source).name}?"
                        ),
                        intent="delete_folder",
                        entity=entity,
                        typed_text=typed_text,
                        browser=browser,
                        website=website,
                        search_query=search_query,
                        profile=profile,
                        user_text=user_text,
                        multi_command=multi_command,
                        selection=selection,
                        confirmation_action="delete_folder",
                    )

                result = self.file_system_agent.execute(
                    "delete_folder",
                    {
                        "entity": resolved_source
                    }
                )

                success = bool(
                    result.get("success")
                )

                if success:

                    reply = self.speak(
                        "Folder deleted successfully."
                    )

                else:

                    reply = self.speak(
                        result.get(
                            "message",
                            "Unable to delete the folder."
                        )
                    )

                return self.response(
                    success,
                    "Status : Folder Deleted",
                    "Status : Delete Failed",
                    reply
                )

            # -------------------------
            # Move Folder
            # -------------------------

            elif (
                intent == "move_folder"
                and entity
            ):

                if isinstance(entity, dict):

                    source = (
                        entity.get("source")
                        or entity.get("foldername")
                        or entity.get("folder")
                        or entity.get("folder_path")
                    )

                    destination = (
                        entity.get("destination")
                        or entity.get("destination_folder")
                        or entity.get("target")
                    )

                else:

                    source = str(entity)
                    destination = None

                if not source or not destination:

                    reply = self.speak(
                        "I need the folder and destination folder."
                    )

                    return self.response(
                        False,
                        "",
                        "Status : Move Information Missing",
                        reply
                    )

                source_resolution = self.resolve_folder_selection(
                    source,
                    selection
                )

                if source_resolution.get("requires_selection"):

                    return self.multiple_target_response(
                        source_resolution,
                        "move_folder",
                        target_type="folder",
                        pending_payload=self._current_selection_payload
                    )

                if not source_resolution.get("success"):

                    reply = self.speak(
                        source_resolution.get(
                            "message",
                            f"Folder not found: {source}"
                        )
                    )

                    return self.response(
                        False,
                        "",
                        "Status : Folder Not Found",
                        reply
                    )

                destination_path = (
                    self.file_system_agent.resolve_folder(
                        destination
                    )
                )

                if not destination_path:

                    reply = self.speak(
                        f"Destination folder not found: {destination}"
                    )

                    return self.response(
                        False,
                        "",
                        "Status : Destination Folder Not Found",
                        reply
                    )

                resolved_source = source_resolution.get(
                    "path",
                    source
                )

                if not skip_confirmation:

                    return self.confirmation_response(
                        (
                            f"Do you want to move "
                            f"{Path(resolved_source).name} "
                            f"to {destination}?"
                        ),
                        intent="move_folder",
                        entity=entity,
                        typed_text=typed_text,
                        browser=browser,
                        website=website,
                        search_query=search_query,
                        profile=profile,
                        user_text=user_text,
                        multi_command=multi_command,
                        selection=selection,
                        confirmation_action="move_folder",
                    )

                result = self.file_system_agent.execute(
                    "move_folder",
                    {
                        "source": resolved_source,
                        "destination": destination_path
                    }
                )

                success = bool(
                    result.get("success")
                )

                if success:

                    reply = self.speak(
                        "Folder moved successfully."
                    )

                else:

                    reply = self.speak(
                        result.get(
                            "message",
                            "Unable to move the folder."
                        )
                    )

                return self.response(
                    success,
                    "Status : Folder Moved",
                    "Status : Move Failed",
                    reply
                )

            # -------------------------
            # Copy Folder
            # -------------------------

            elif (
                intent == "copy_folder"
                and entity
            ):

                if isinstance(entity, dict):

                    source = (
                        entity.get("source")
                        or entity.get("foldername")
                        or entity.get("folder")
                        or entity.get("folder_path")
                    )

                    destination = (
                        entity.get("destination")
                        or entity.get("destination_folder")
                        or entity.get("target")
                    )

                else:

                    source = str(entity)
                    destination = None

                if not source or not destination:

                    reply = self.speak(
                        "I need the folder and destination folder."
                    )

                    return self.response(
                        False,
                        "",
                        "Status : Copy Information Missing",
                        reply
                    )

                source_resolution = self.resolve_folder_selection(
                    source,
                    selection
                )

                if source_resolution.get("requires_selection"):

                    return self.multiple_target_response(
                        source_resolution,
                        "copy_folder",
                        target_type="folder",
                        pending_payload=self._current_selection_payload
                    )

                if not source_resolution.get("success"):

                    reply = self.speak(
                        source_resolution.get(
                            "message",
                            f"Folder not found: {source}"
                        )
                    )

                    return self.response(
                        False,
                        "",
                        "Status : Folder Not Found",
                        reply
                    )

                destination_path = (
                    self.file_system_agent.resolve_folder(
                        destination
                    )
                )

                if not destination_path:

                    reply = self.speak(
                        f"Destination folder not found: {destination}"
                    )

                    return self.response(
                        False,
                        "",
                        "Status : Destination Folder Not Found",
                        reply
                    )

                resolved_source = source_resolution.get(
                    "path",
                    source
                )

                if not skip_confirmation:

                    return self.confirmation_response(
                        (
                            f"Do you want to copy "
                            f"{Path(resolved_source).name} "
                            f"to {destination}?"
                        ),
                        intent="copy_folder",
                        entity=entity,
                        typed_text=typed_text,
                        browser=browser,
                        website=website,
                        search_query=search_query,
                        profile=profile,
                        user_text=user_text,
                        multi_command=multi_command,
                        selection=selection,
                        confirmation_action="copy_folder",
                    )

                result = self.file_system_agent.execute(
                    "copy_folder",
                    {
                        "source": resolved_source,
                        "destination": destination_path
                    }
                )

                success = bool(
                    result.get("success")
                )

                if success:

                    reply = self.speak(
                        "Folder copied successfully."
                    )

                else:

                    reply = self.speak(
                        result.get(
                            "message",
                            "Unable to copy the folder."
                        )
                    )

                return self.response(
                    success,
                    "Status : Folder Copied",
                    "Status : Copy Failed",
                    reply
                )

            # -------------------------
            # Empty Recycle Bin
            # -------------------------

            elif intent == "empty_recycle_bin":

                # ---------------------------------
                # Confirmation
                # ---------------------------------

                if not skip_confirmation:

                    return self.confirmation_response(
                        "Do you want to empty the recycle bin?",
                        intent="empty_recycle_bin",
                        entity=entity,
                        typed_text=typed_text,
                        browser=browser,
                        website=website,
                        search_query=search_query,
                        profile=profile,
                        user_text=user_text,
                        multi_command=multi_command,
                        selection=selection,
                        confirmation_action="empty_recycle_bin",
                    )

                # ---------------------------------
                # Execute after YES
                # ---------------------------------

                success = (
                    self.folder_manager
                    .empty_recycle_bin()
                )

                if success:

                    reply = self.speak(
                        "Recycle Bin emptied successfully."
                    )

                else:

                    reply = self.speak(
                        "Unable to empty the Recycle Bin."
                    )

                return self.response(
                    success,
                    "Status : Recycle Bin Emptied",
                    "Status : Recycle Bin Empty Failed",
                    reply
                )

            # -------------------------
            # Search by Extension
            # -------------------------

            elif (
                intent == "search_extension"
                and entity
            ):

                reply = self.speak(
                    f"Searching for {entity} files."
                )

                results = self.file_manager.search_by_extension(
                    entity
                )

                if results:

                    reply = self.speak(
                        f"Showing {entity.upper()} files in File Explorer."
                    )

                    print("\n========== DISPATCH DEBUG ==========")
                    print("Calling show_search_results()")
                    print("Entity :", entity)
                    print("Results :", len(results))
                    print("====================================")

                    self.file_manager.show_search_results(

                        results,

                        f"*.{entity.lower().lstrip('.')}"
                    )

                    # Give Explorer time to finish rendering
                    self.window.wait_for_window(
                        "File Explorer",
                        timeout=10
                    )

                    self.keyboard.activate_window(
                        0.5
                    )

                else:

                    reply = self.speak(
                        "No matching files found."
                    )

                return self.response(

                    bool(results),

                    "Status : Explorer Search Opened",

                    "Status : No Files Found",

                    reply

                )


            # -------------------------
            # Search by Date
            # -------------------------

            elif (
                intent == "search_date"
                and entity
            ):

                reply = self.speak(
                    "Searching files."
                )

                results = self.file_manager.search_by_date(
                    int(entity)
                )

                if results:

                    reply = self.speak(
                        "Showing search results in File Explorer."
                    )

                    if int(entity) == 0:

                        query = "datemodified:today"

                    elif int(entity) == 1:

                        query = "datemodified:yesterday"

                    elif int(entity) <= 7:

                        query = "datemodified:this week"

                    elif int(entity) <= 31:

                        query = "datemodified:this month"

                    else:

                        query = "datemodified:this year"

                    self.file_manager.show_search_results(

                        results,

                        query

                    )

                    self.window.wait_for_window(
                        "File Explorer",
                        timeout=10
                    )

                    self.keyboard.activate_window(
                        0.5
                    )

                else:

                    reply = self.speak(
                        "No matching files found."
                    )

                return self.response(

                    bool(results),

                    "Status : Explorer Search Opened",

                    "Status : No Files Found",

                    reply

                )

            # -------------------------
            # Open Website
            # -------------------------

            elif intent == "open_website":

                if not website:

                    return {

                        "success": False,

                        "status": "Status : Invalid Website"

                    }

                reply = self.speak(
                    f"Opening {website}"
                )

                success = self.browser.open_website(

                    website,

                    browser or "chrome"

                )

                return self.response(

                    success,

                    "Status : Website Opened",

                    "Status : Website Failed",

                    reply

                )

            # -------------------------
            # Google Home
            # -------------------------

            elif intent == "open_google":

                reply = self.speak(
                    "Opening Google."
                )

                success = self.browser.open_google(
                    browser or "chrome"
                )

                return self.response(

                    success,

                    "Status : Google Opened",

                    "Status : Google Failed",

                    reply

                )

            # -------------------------
            # Youtube Home
            # -------------------------

            elif intent == "open_youtube":

                reply = self.speak(
                    "Opening YouTube."
                )

                success = self.browser.open_youtube(
                    browser or "chrome"
                )

                return self.response(

                    success,

                    "Status : YouTube Opened",

                    "Status : YouTube Failed",

                    reply

                )

            # -------------------------
            # Google Search
            # -------------------------

            elif intent == "google_search":

                if not search_query:

                    return self.response(

                        False,

                        "",

                        "Status : Invalid Search"

                    )

                reply = self.speak(
                    f"Searching Google for {search_query}."
                )

                success = self.browser.google_search(

                    search_query,

                    browser or "chrome",

                    new_tab=not multi_command

                )

                return self.response(

                    success,

                    "Status : Search Completed",

                    "Status : Search Failed",

                    reply

                )

            # -------------------------
            # YouTube Search
            # -------------------------

            elif intent == "youtube_search":

                if not search_query:

                    return self.response(

                        False,

                        "",

                        "Status : Invalid Search"

                    )

                reply = self.speak(
                    f"Searching YouTube for {search_query}."
                )

                success = self.browser.youtube_search(

                    search_query,

                    browser or "chrome",

                    new_tab=not multi_command

                )

                return self.response(

                    success,

                    "Status : YouTube Search",

                    "Status : Search Failed",

                    reply

                )

            # -------------------------
            # Play YouTube
            # -------------------------

            elif intent == "play_youtube":

                query = search_query or entity

                if not query:

                    return self.response(

                        False,

                        "",

                        "Status : Invalid Video"

                    )

                reply = self.speak(
                    f"Playing {query} on YouTube."
                )

                success = self.browser.play_youtube(

                    query,

                    browser or "chrome",

                    new_tab=not multi_command

                )

                return self.response(

                    success,

                    "Status : Playing Video",

                    "Status : Play Failed",

                    reply

                )

            # -------------------------
            # Click Google Search Result
            # -------------------------

            elif intent == "click_search_result":

                # ---------------------------------
                # Default to first result
                # ---------------------------------

                result_index = 0

                # ---------------------------------
                # Multi-command planner sends the
                # result index through entity.
                # ---------------------------------

                if entity is not None:

                    try:

                        result_index = int(
                            entity
                        )

                    except (
                        TypeError,
                        ValueError
                    ):

                        result_index = 0

                # ---------------------------------
                # Convert zero-based index into
                # human-readable result number.
                # ---------------------------------

                result_number = (
                    result_index + 1
                )

                reply = self.speak(
                    f"Opening search result {result_number}."
                )

                # ---------------------------------
                # Playwright performs the actual
                # browser interaction.
                # ---------------------------------

                success = (
                    self.browser
                    .click_search_result(
                        result_index
                    )
                )

                # ---------------------------------
                # Final Response
                # ---------------------------------

                if success:

                    reply = self.speak(
                        f"Search result {result_number} opened successfully."
                    )

                else:

                    reply = self.speak(
                        f"Unable to open search result {result_number}."
                    )

                return self.response(

                    success,

                    "Status : Search Result Opened",

                    "Status : Search Result Failed",

                    reply

                )

            # -------------------------
            # New Tab
            # -------------------------

            elif intent == "new_tab":

                reply = self.speak(
                    "Opening a new tab."
                )

                success = self.browser.new_tab()

                return self.response(

                    success,

                    "Status : New Tab",

                    "Status : New Tab Failed",

                    reply

                )

            # -------------------------
            # Close Tab
            # -------------------------

            elif intent == "close_tab":

                reply = self.speak(
                    "Closing the current tab."
                )

                success = self.browser.close_tab()

                return self.response(

                    success,

                    "Status : Tab Closed",

                    "Status : Close Tab Failed",

                    reply

                )

            # -------------------------
            # Next Tab
            # -------------------------

            elif intent == "next_tab":

                reply = self.speak(
                    "Switching to the next tab."
                )

                success = self.browser.next_tab()

                return self.response(

                    success,

                    "Status : Next Tab",

                    "Status : Next Tab Failed",

                    reply

                )

            # -------------------------
            # Previous Tab
            # -------------------------

            elif intent == "previous_tab":

                reply = self.speak(
                    "Switching to the previous tab."
                )

                success = self.browser.previous_tab()

                return self.response(

                    success,

                    "Status : Previous Tab",

                    "Status : Previous Tab Failed",

                    reply

                )

            # -------------------------
            # Refresh 
            # -------------------------

            elif intent == "refresh":

                reply = self.speak(
                    "Refreshing the page."
                )

                success = self.browser.refresh()

                return self.response(

                    success,

                    "Status : Page Refreshed",

                    "Status : Refresh Failed",

                    reply

                )

            # -------------------------
            # Downloads
            # -------------------------

            elif intent == "browser_downloads":

                reply = self.speak(
                    "Opening Downloads."
                )

                success = self.browser.open_downloads()

                return self.response(

                    success,

                    "Status : Downloads Opened",

                    "Status : Downloads Failed",

                    reply

                )

            # -------------------------
            # History
            # -------------------------

            elif intent == "browser_history":

                reply = self.speak(
                    "Opening browsing history."
                )

                success = self.browser.open_history()

                return self.response(

                    success,

                    "Status : History Opened",

                    "Status : History Failed",

                    reply

                )

            # -------------------------
            # Bookmark Bar
            # -------------------------

            elif intent == "browser_bookmarks":

                reply = self.speak(
                    "Opening the bookmarks bar."
                )

                success = self.browser.show_bookmarks()

                return self.response(

                    success,

                    "Status : Bookmark Bar",

                    "Status : Bookmark Bar Failed",

                    reply

                )

            # -------------------------
            # Bookmark Page
            # -------------------------

            elif intent == "bookmark_page":

                reply = self.speak(
                    "Bookmarking this page."
                )

                success = self.browser.bookmark_page()

                return self.response(

                    success,

                    "Status : Page Bookmarked",

                    "Status : Bookmark Failed",

                    reply

                )

            # -------------------------
            # Address Bar
            # -------------------------

            elif intent == "address_bar":

                reply = self.speak(
                    "Focusing the address bar."
                )

                success = self.browser.focus_address_bar()

                return self.response(

                    success,

                    "Status : Address Bar",

                    "Status : Address Bar Failed",

                    reply

                )

            # -------------------------
            # Browser Back
            # -------------------------

            elif intent == "browser_back":

                reply = self.speak(
                    "Going back."
                )

                success = self.browser.back()

                return self.response(

                    success,

                    "Status : Back",

                    "Status : Back Failed",

                    reply

                )

            # -------------------------
            # Browser Forward
            # -------------------------

            elif intent == "browser_forward":

                reply = self.speak(
                    "Going forward."
                )

                success = self.browser.forward()

                return self.response(

                    success,

                    "Status : Forward",

                    "Status : Forward Failed",

                    reply

                )

            # -------------------------
            # Private Window
            # -------------------------

            elif intent == "private_window":

                reply = self.speak(
                    "Opening a private window."
                )

                success = self.browser.private_window()

                return self.response(

                    success,

                    "Status : Private Window",

                    "Status : Private Window Failed",

                    reply

                )

            # -------------------------
            # Open Chrome Profile
            # -------------------------

            elif intent == "open_chrome_profile":

                reply = self.speak(
                    f"Opening {profile} profile."
                )

                success = self.browser.open_profile(
                    profile,
                    website
                )

                return self.response(

                    success,

                    "Status : Chrome Profile Opened",

                    "Status : Profile Failed",

                    reply

                )

            # -------------------------
            # Search by Size
            # -------------------------

            elif (
                intent == "search_size"
                and entity
            ):

                reply = self.speak(
                    f"Searching files larger than {entity} megabytes."
                )

                results = self.file_manager.search_by_size(
                    float(entity)
                )

                if results:

                    reply = self.speak(
                        f"I found {len(results)} files."
                    )

                    reply = self.speak(
                        "Opening File Explorer."
                    )

                    query = f"size:>{int(float(entity))}MB"

                    self.file_manager.show_search_results(

                        results,

                        query

                    )

                    self.window.wait_for_window(
                        "File Explorer",
                        timeout=10
                    )

                    self.keyboard.activate_window(
                        0.5
                    )

                else:

                    reply = self.speak(
                        "No matching files found."
                    )

                return self.response(

                    bool(results),

                    f"Status : {len(results) if results else 0} Files Found",

                    "Status : No Files Found",

                    reply

                )

            return self.response(

                False,

                "",

                "Status : No Action",

                ""

            )

        except Exception as error:

            import traceback

            traceback.print_exc()

            print(
                f"Dispatcher Error : {error}"
            )

            reply = self.speak(
                "Sorry. Something went wrong."
            )

            return self.response(

                False,

                "",

                "Status : Dispatcher Error",

                reply

            )