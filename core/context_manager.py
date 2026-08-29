"""
Context Manager Module

Maintains ASTRA-AI conversational and
execution context.

Responsibilities:

- Track the last user command
- Track the last detected intent
- Track the last executed action
- Track the current / last application
- Track the current / last file
- Track the current / last folder
- Maintain lightweight session history
- Provide context to follow-up commands

ASTRA-AI V1
"""

from collections import deque
from copy import deepcopy
from datetime import datetime
from threading import RLock


class ContextManager:
    """
    Lightweight context manager for ASTRA-AI.

    Context is primarily maintained in memory
    for fast access.

    This allows ASTRA to understand follow-up
    commands such as:

        "Open Chrome"
        "Search YouTube"

        "Open my project folder"
        "Open the latest file"

        "Close it"

    The manager stores recent conversational and
    execution state without performing expensive
    database operations for every command.
    """

    def __init__(
        self,
        max_history=20
    ):

        # ------------------------------------------
        # Thread Safety
        # ------------------------------------------

        self.lock = RLock()

        # ------------------------------------------
        # Maximum History
        # ------------------------------------------

        self.max_history = max(
            1,
            int(max_history)
        )

        # ------------------------------------------
        # Session History
        # ------------------------------------------

        self.history = deque(
            maxlen=self.max_history
        )

        # ------------------------------------------
        # Current Context
        # ------------------------------------------

        self.context = {

            "last_command": None,

            "last_intent": None,

            "last_action": None,

            "last_application": None,

            "last_file": None,

            "last_folder": None,

            "last_target": None,

            "last_result": None,

            "last_updated": None,

        }

    # ==================================================
    # INTERNAL HELPERS
    # ==================================================

    def _timestamp(self):
        """
        Return the current timestamp.
        """

        return datetime.now().isoformat()

    # --------------------------------------------------

    def _normalize_value(
        self,
        value
    ):
        """
        Normalize simple string values.

        Non-string values are returned unchanged.
        """

        if isinstance(
            value,
            str
        ):

            value = value.strip()

            return value or None

        return value

    # --------------------------------------------------

    def _update_timestamp(self):
        """
        Update context timestamp.
        """

        self.context[
            "last_updated"
        ] = self._timestamp()

    # ==================================================
    # COMMAND CONTEXT
    # ==================================================

    def set_last_command(
        self,
        command
    ):
        """
        Store the latest user command.
        """

        command = (
            self._normalize_value(
                command
            )
        )

        with self.lock:

            self.context[
                "last_command"
            ] = command

            self._update_timestamp()

    # --------------------------------------------------

    def get_last_command(self):
        """
        Return the latest user command.
        """

        with self.lock:

            return self.context.get(
                "last_command"
            )

    # ==================================================
    # INTENT CONTEXT
    # ==================================================

    def set_last_intent(
        self,
        intent
    ):
        """
        Store the latest detected intent.
        """

        intent = (
            self._normalize_value(
                intent
            )
        )

        with self.lock:

            self.context[
                "last_intent"
            ] = intent

            self._update_timestamp()

    # --------------------------------------------------

    def get_last_intent(self):
        """
        Return the latest detected intent.
        """

        with self.lock:

            return self.context.get(
                "last_intent"
            )

    # ==================================================
    # ACTION CONTEXT
    # ==================================================

    def set_last_action(
        self,
        action
    ):
        """
        Store the latest executed action.
        """

        action = (
            self._normalize_value(
                action
            )
        )

        with self.lock:

            self.context[
                "last_action"
            ] = action

            self._update_timestamp()

    # --------------------------------------------------

    def get_last_action(self):
        """
        Return the latest executed action.
        """

        with self.lock:

            return self.context.get(
                "last_action"
            )

    # ==================================================
    # APPLICATION CONTEXT
    # ==================================================

    def set_last_application(
        self,
        application
    ):
        """
        Store the latest application target.

        Example:

            chrome
            notepad
            vscode
        """

        application = (
            self._normalize_value(
                application
            )
        )

        with self.lock:

            self.context[
                "last_application"
            ] = application

            self.context[
                "last_target"
            ] = application

            self._update_timestamp()

    # --------------------------------------------------

    def get_last_application(self):
        """
        Return the latest application.
        """

        with self.lock:

            return self.context.get(
                "last_application"
            )

    # ==================================================
    # FILE CONTEXT
    # ==================================================

    def set_last_file(
        self,
        file_path
    ):
        """
        Store the latest file target.
        """

        file_path = (
            self._normalize_value(
                file_path
            )
        )

        with self.lock:

            self.context[
                "last_file"
            ] = file_path

            self.context[
                "last_target"
            ] = file_path

            self._update_timestamp()

    # --------------------------------------------------

    def get_last_file(self):
        """
        Return the latest file.
        """

        with self.lock:

            return self.context.get(
                "last_file"
            )

    # ==================================================
    # FOLDER CONTEXT
    # ==================================================

    def set_last_folder(
        self,
        folder_path
    ):
        """
        Store the latest folder target.
        """

        folder_path = (
            self._normalize_value(
                folder_path
            )
        )

        with self.lock:

            self.context[
                "last_folder"
            ] = folder_path

            self.context[
                "last_target"
            ] = folder_path

            self._update_timestamp()

    # --------------------------------------------------

    def get_last_folder(self):
        """
        Return the latest folder.
        """

        with self.lock:

            return self.context.get(
                "last_folder"
            )

    # ==================================================
    # TARGET CONTEXT
    # ==================================================

    def set_last_target(
        self,
        target
    ):
        """
        Store the latest generic target.
        """

        target = (
            self._normalize_value(
                target
            )
        )

        with self.lock:

            self.context[
                "last_target"
            ] = target

            self._update_timestamp()

    # --------------------------------------------------

    def get_last_target(self):
        """
        Return the latest generic target.
        """

        with self.lock:

            return self.context.get(
                "last_target"
            )

    # ==================================================
    # RESULT CONTEXT
    # ==================================================

    def set_last_result(
        self,
        result
    ):
        """
        Store the latest execution result.

        Result can be a string, dictionary,
        boolean or any lightweight Python value.
        """

        with self.lock:

            self.context[
                "last_result"
            ] = result

            self._update_timestamp()

    # --------------------------------------------------

    def get_last_result(self):
        """
        Return the latest execution result.
        """

        with self.lock:

            return self.context.get(
                "last_result"
            )

    # ==================================================
    # HISTORY
    # ==================================================

    def add_history(
        self,
        command=None,
        intent=None,
        action=None,
        target=None,
        result=None
    ):
        """
        Add one command execution entry
        to the session history.
        """

        entry = {

            "timestamp":
                self._timestamp(),

            "command":
                self._normalize_value(
                    command
                ),

            "intent":
                self._normalize_value(
                    intent
                ),

            "action":
                self._normalize_value(
                    action
                ),

            "target":
                self._normalize_value(
                    target
                ),

            "result":
                result,

        }

        with self.lock:

            self.history.append(
                entry
            )

    # --------------------------------------------------

    def get_history(
        self,
        limit=None
    ):
        """
        Return recent context history.

        The newest entry is returned last.
        """

        with self.lock:

            history = list(
                self.history
            )

            if limit is not None:

                try:

                    limit = int(
                        limit
                    )

                    if limit > 0:

                        history = (
                            history[-limit:]
                        )

                    else:

                        history = []

                except (
                    TypeError,
                    ValueError
                ):

                    pass

            return deepcopy(
                history
            )

    # --------------------------------------------------

    def get_last_history_item(self):
        """
        Return the latest history entry.
        """

        with self.lock:

            if not self.history:

                return None

            return deepcopy(
                self.history[-1]
            )

    # ==================================================
    # COMPLETE CONTEXT UPDATE
    # ==================================================

    def update_context(
        self,
        command=None,
        intent=None,
        action=None,
        application=None,
        file_path=None,
        folder_path=None,
        target=None,
        result=None,
        add_to_history=True
    ):
        """
        Update multiple context values
        in one thread-safe operation.

        This should normally be called after
        ASTRA processes a command.
        """

        with self.lock:

            if command is not None:

                self.context[
                    "last_command"
                ] = self._normalize_value(
                    command
                )

            if intent is not None:

                self.context[
                    "last_intent"
                ] = self._normalize_value(
                    intent
                )

            if action is not None:

                self.context[
                    "last_action"
                ] = self._normalize_value(
                    action
                )

            if application is not None:

                application = (
                    self._normalize_value(
                        application
                    )
                )

                self.context[
                    "last_application"
                ] = application

                self.context[
                    "last_target"
                ] = application

            if file_path is not None:

                file_path = (
                    self._normalize_value(
                        file_path
                    )
                )

                self.context[
                    "last_file"
                ] = file_path

                self.context[
                    "last_target"
                ] = file_path

            if folder_path is not None:

                folder_path = (
                    self._normalize_value(
                        folder_path
                    )
                )

                self.context[
                    "last_folder"
                ] = folder_path

                self.context[
                    "last_target"
                ] = folder_path

            if target is not None:

                self.context[
                    "last_target"
                ] = self._normalize_value(
                    target
                )

            if result is not None:

                self.context[
                    "last_result"
                ] = result

            self._update_timestamp()

            if add_to_history:

                history_target = target

                if history_target is None:

                    history_target = (
                        self.context.get(
                            "last_target"
                        )
                    )

                self.history.append(

                    {

                        "timestamp":
                            self._timestamp(),

                        "command":
                            command,

                        "intent":
                            intent,

                        "action":
                            action,

                        "target":
                            history_target,

                        "result":
                            result,

                    }

                )

    # ==================================================
    # CONTEXT RESOLUTION
    # ==================================================

    def resolve_reference(
        self,
        reference
    ):
        """
        Resolve simple contextual references.

        Supported examples:

            it
            this
            that

        Resolution priority:

            1. Last target
            2. Last file
            3. Last folder
            4. Last application
        """

        if not reference:

            return None

        normalized = (
            str(reference)
            .strip()
            .lower()
        )

        references = {

            "it",

            "this",

            "that",

            "this one",

            "that one",

            "the same",

            "same",

        }

        if normalized not in references:

            return reference

        with self.lock:

            return (

                self.context.get(
                    "last_target"
                )

                or

                self.context.get(
                    "last_file"
                )

                or

                self.context.get(
                    "last_folder"
                )

                or

                self.context.get(
                    "last_application"
                )

            )

    # --------------------------------------------------

    def has_context(self):
        """
        Return True when ASTRA currently
        has meaningful context.
        """

        with self.lock:

            return any(

                self.context.get(
                    key
                )

                for key in (

                    "last_command",

                    "last_intent",

                    "last_action",

                    "last_application",

                    "last_file",

                    "last_folder",

                    "last_target",

                )

            )

    # ==================================================
    # CONTEXT ACCESS
    # ==================================================

    def get_context(self):
        """
        Return a safe copy of the
        complete current context.
        """

        with self.lock:

            return deepcopy(
                self.context
            )

    # --------------------------------------------------

    def get_context_summary(self):
        """
        Return a compact context summary.

        Useful for debugging and logging.
        """

        with self.lock:

            return {

                "command":
                    self.context.get(
                        "last_command"
                    ),

                "intent":
                    self.context.get(
                        "last_intent"
                    ),

                "action":
                    self.context.get(
                        "last_action"
                    ),

                "application":
                    self.context.get(
                        "last_application"
                    ),

                "file":
                    self.context.get(
                        "last_file"
                    ),

                "folder":
                    self.context.get(
                        "last_folder"
                    ),

                "target":
                    self.context.get(
                        "last_target"
                    ),

            }

    # ==================================================
    # CLEAR CONTEXT
    # ==================================================

    def clear_context(
        self,
        clear_history=False
    ):
        """
        Clear the active session context.

        Session history is preserved by default.
        """

        with self.lock:

            self.context = {

                "last_command": None,

                "last_intent": None,

                "last_action": None,

                "last_application": None,

                "last_file": None,

                "last_folder": None,

                "last_target": None,

                "last_result": None,

                "last_updated":
                    self._timestamp(),

            }

            if clear_history:

                self.history.clear()

    # --------------------------------------------------

    def clear_history(self):
        """
        Remove all session history.
        """

        with self.lock:

            self.history.clear()

    # ==================================================
    # DEBUG
    # ==================================================

    def __repr__(self):
        """
        Return a useful debug representation.
        """

        summary = (
            self.get_context_summary()
        )

        return (

            "ContextManager("
            f"command={summary['command']!r}, "
            f"intent={summary['intent']!r}, "
            f"action={summary['action']!r}, "
            f"target={summary['target']!r}"
            ")"

        )