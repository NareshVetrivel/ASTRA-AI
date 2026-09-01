"""
ASTRA-AI Multi-Command Planner

Converts a long natural-language command into a structured
ActionPlan that can be executed sequentially.

The planner is responsible for:
    - Detecting whether a command requires multiple actions.
    - Handling natural-language command chaining.
    - Handling common speech-to-text connector mistakes.
    - Asking Gemini to convert long commands into structured steps.
    - Validating the generated action plan.
    - Keeping planning separate from actual execution.

ASTRA-AI V1
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any, Dict, Optional

from ai.gemini_client import GeminiClient

from planner.action_models import (
    ActionPlan,
    ActionStep,
)


logger = logging.getLogger(__name__)


class MultiCommandPlanner:
    """
    Creates structured action plans from long user commands.

    The planner does NOT execute actions.

    Examples
    --------
    User:
        "Open Chrome then search Sona College"

    Output:
        launch_application -> chrome
        google_search -> Sona College

    Word example:
        "open Word then create a blank document"

    Output:
        launch_application -> word
        create_blank_document

    The planner also handles common speech-recognition
    variations such as:

        "open notepad 10 type hello"

    where "10" may be a speech-to-text recognition
    error for "then".
    """

    # ---------------------------------------------------------
    # Supported action names
    # ---------------------------------------------------------

    SUPPORTED_ACTIONS = {
        # -----------------------------------------------------
        # Application
        # -----------------------------------------------------

        "launch_application",
        "close_application",

        # -----------------------------------------------------
        # Browser
        # -----------------------------------------------------

        "open_website",
        "google_search",
        "youtube_search",
        "play_youtube",
        "click_search_result",

        # -----------------------------------------------------
        # Files
        # -----------------------------------------------------

        "open_file",
        "create_file",
        "rename_file",
        "copy_file",
        "move_file",
        "delete_file",

        # -----------------------------------------------------
        # Folders
        # -----------------------------------------------------

        "open_folder",
        "create_folder",
        "rename_folder",
        "copy_folder",
        "move_folder",
        "delete_folder",

        # -----------------------------------------------------
        # Archive
        # -----------------------------------------------------

        "compress_zip",
        "extract_zip",

        # -----------------------------------------------------
        # Keyboard / text
        # -----------------------------------------------------

        "type_text",
        "press_key",

        # -----------------------------------------------------
        # Mouse
        # -----------------------------------------------------

        "click",
        "double_click",
        "right_click",

        # -----------------------------------------------------
        # Microsoft Word V1
        # -----------------------------------------------------

        "create_blank_document",
    }

    # ---------------------------------------------------------
    # Action verbs
    # ---------------------------------------------------------
    #
    # These are used only for detecting command boundaries.
    #
    # IMPORTANT:
    # "and" is NOT considered a separator by itself.
    #
    # We only treat "and" as a command connector when an
    # actual action follows it.
    # ---------------------------------------------------------

    ACTION_START_WORDS = (
        "open",
        "launch",
        "start",
        "close",
        "exit",
        "quit",
        "search",
        "find",
        "click",
        "double click",
        "right click",
        "type",
        "write",
        "enter",
        "press",
        "create",
        "make",
        "rename",
        "copy",
        "move",
        "delete",
        "remove",
        "download",
        "play",
        "go",
        "visit",
        "browse",
        "extract",
        "compress",
    )

    # ---------------------------------------------------------
    # Natural language connectors
    # ---------------------------------------------------------

    COMMAND_CONNECTORS = (
        "and then",
        "after that",
        "then",
        "next",
        "finally",
        "after",
        "and",
    )

    # ---------------------------------------------------------
    # Planner prompt
    # ---------------------------------------------------------

    SYSTEM_PROMPT = """
You are the command planning engine for ASTRA-AI.

Your job is to convert a user's natural-language command into
a structured sequence of executable actions.

IMPORTANT RULES:

1. Return ONLY valid JSON.
2. Do not return Markdown.
3. Do not explain your answer.
4. Do not execute anything.
5. Do not invent actions outside the supported action list.
6. Preserve the user's intended order.
7. Each independent operation must become a separate step.
8. Later steps may depend on earlier steps.
9. Keep important user entities such as:
   - application names
   - file names
   - folder names
   - website names
   - search queries
   - result indexes
   - text to type
   - Word document paths
   - Word formatting values
10. Use zero-based indexes for search results.
11. "first result" = index 0.
12. "second result" = index 1.
13. "third result" = index 2.
14. If the command is ambiguous, do not invent missing values.

COMMAND CHAINING RULES:

Users may naturally connect multiple actions using:

- then
- and then
- after
- after that
- next
- finally
- and

Examples:

"open notepad then type hello"

"open notepad and type hello"

"open notepad and then type hello"

"open notepad after type hello"

"open notepad after that type hello"

"open notepad next type hello"

"open chrome then search Sona College"

"open chrome and search Sona College"

"open Word then create a blank document"

"open Microsoft Word and create a blank document"

"create a blank Word document then type hello"

IMPORTANT:

Do NOT split normal text containing the word "and".

Example:

"type my name and department"

This is ONE type_text action.

The word "and" should only be treated as a command connector
when a new recognizable action starts after it.

SPEECH-TO-TEXT NORMALIZATION:

Voice recognition may incorrectly convert command connectors.

For ASTRA-AI command planning:

- "10" between two recognizable actions may mean "then".
- "ten" between two recognizable actions may mean "then".
- "and then" means "then".
- "after that" means the next action follows the previous action.
- "next" means the next action follows the previous action.

Examples:

"open notepad 10 type hello"

means:

"open notepad then type hello"

"open notepad ten type hello"

means:

"open notepad then type hello"

Do NOT convert every occurrence of "10" or "ten".
Only interpret it as a command connector when it occurs
between two recognizable actions.

VERY IMPORTANT FOR TYPE_TEXT:

When creating a type_text action, preserve the user's intended
text exactly as much as possible.

For example:

User:
"open notepad then type my name is naresh from MCA Department"

Output:

{
    "action": "type_text",
    "parameters": {
        "text": "my name is naresh from MCA Department"
    }
}

Do not include command connector words such as:
- then
- and then
- after
- after that
- next

inside the text to be typed.

MICROSOFT WORD V1:

ASTRA-AI supports Microsoft Word actions through the existing
WordAgent and WordAutomation pipeline.

For creating a new blank Word document use:

"create_blank_document"

Examples:

"open Word then create a blank document"

Output:

{
    "action": "launch_application",
    "parameters": {
        "application": "word"
    }
}

followed by:

{
    "action": "create_blank_document",
    "parameters": {}
}

"create a blank Word document and type hello"

should create the appropriate sequential actions:

1. create_blank_document
2. type_text

When creating a blank Word document, do NOT invent a file path
unless the user explicitly provides one.

SUPPORTED ACTIONS:

launch_application
close_application

open_website
google_search
youtube_search
play_youtube
click_search_result

open_file
create_file
rename_file
copy_file
move_file
delete_file

open_folder
create_folder
rename_folder
copy_folder
move_folder
delete_folder

compress_zip
extract_zip

type_text
press_key

click
double_click
right_click

create_blank_document

OUTPUT FORMAT:

{
    "original_command": "user command",
    "description": "short description",
    "steps": [
        {
            "step_id": "step_1",
            "action": "launch_application",
            "parameters": {
                "application": "chrome"
            },
            "description": "Open Chrome"
        }
    ]
}
"""

    def __init__(
        self,
        gemini_client: Optional[GeminiClient] = None,
    ) -> None:
        """
        Initialize the multi-command planner.

        Parameters
        ----------
        gemini_client:
            Existing ASTRA GeminiClient instance.

            If not supplied, a new client is created.
        """

        self.gemini = (
            gemini_client
            if gemini_client is not None
            else GeminiClient()
        )

    # =========================================================
    # Public API
    # =========================================================

    def is_multi_command(
        self,
        command: str,
    ) -> bool:
        """
        Determine whether a command appears to contain
        multiple independent actions.

        Supports:

            then
            and then
            after
            after that
            next
            finally
            and

        Also handles common STT mistakes:

            10
            ten

        Examples:

            "open chrome"
                -> False

            "open chrome then search google"
                -> True

            "open notepad and type hello"
                -> True

            "open notepad 10 type hello"
                -> True

            "open notepad ten type hello"
                -> True

            "type my name and department"
                -> False
        """

        if not command:
            return False

        text = self._normalize_for_detection(
            command
        )

        if not text:
            return False

        # -----------------------------------------------------
        # Strong connectors
        # -----------------------------------------------------

        strong_connectors = (
            " and then ",
            " after that ",
            " then ",
            " next ",
            " finally ",
            " after ",
        )

        for connector in strong_connectors:

            if connector in text:

                left, right = text.split(
                    connector,
                    1,
                )

                if (
                    self._looks_like_action(left)
                    and self._looks_like_action(right)
                ):

                    return True

        # -----------------------------------------------------
        # "and" connector
        # -----------------------------------------------------

        if self._contains_action_aware_and(text):

            return True

        # -----------------------------------------------------
        # STT connector:
        #
        #     10
        #     ten
        # -----------------------------------------------------

        if self._contains_stt_then_connector(text):

            return True

        # -----------------------------------------------------
        # Common action chaining patterns
        # -----------------------------------------------------

        patterns = [
            r"\bopen\b.+\bsearch\b",
            r"\bopen\b.+\bclick\b",
            r"\bsearch\b.+\bclick\b",
            r"\bcreate\b.+\bmove\b",
            r"\bfind\b.+\bmove\b",
            r"\bfind\b.+\bcopy\b",
            r"\brename\b.+\bmove\b",
            r"\bdownload\b.+\bopen\b",
            r"\bsearch\b.+\bplay\b",
            r"\bopen\b.+\btype\b",
            r"\blaunch\b.+\btype\b",
            r"\bcreate\b.+\btype\b",
            r"\bopen\b.+\bcreate\b",
            r"\bcreate\b.+\btype\b",
        ]

        for pattern in patterns:

            if re.search(
                pattern,
                text,
            ):

                return True

        return False

    # =========================================================
    # Plan Creation
    # =========================================================

    def create_plan(
        self,
        command: str,
    ) -> ActionPlan:
        """
        Create an ActionPlan from a natural-language command.

        Gemini interprets the normalized command and generates
        the executable action sequence.
        """

        if not command:

            raise ValueError(
                "Cannot create a plan from an empty command."
            )

        command = command.strip()

        if not command:

            raise ValueError(
                "Cannot create a plan from an empty command."
            )

        logger.info(
            "Creating multi-command plan for: %s",
            command,
        )

        # -----------------------------------------------------
        # Normalize only high-confidence STT connector errors.
        # -----------------------------------------------------

        planning_command = (
            self._normalize_command_for_planning(
                command
            )
        )

        if planning_command != command:

            logger.info(
                "Normalized planning command: %s",
                planning_command,
            )

        prompt = self._build_prompt(
            planning_command,
            original_command=command,
        )

        try:

            response = self._generate_plan_response(
                prompt
            )

            data = self._parse_json_response(
                response
            )

            plan = ActionPlan.from_dict(
                data
            )

            # Always preserve actual user command.
            plan.original_command = command

            self._validate_plan(
                plan
            )

            logger.info(
                "Created action plan with %d step(s).",
                plan.total_steps,
            )

            return plan

        except Exception as exc:

            logger.exception(
                "Failed to create action plan."
            )

            raise RuntimeError(
                f"Unable to create action plan: {exc}"
            ) from exc

    # =========================================================
    # Command Normalization
    # =========================================================

    def _normalize_for_detection(
        self,
        command: str,
    ) -> str:
        """
        Normalize a command for detection.

        This does NOT globally replace "10" or "ten".
        """

        text = command.strip().lower()

        if not text:
            return ""

        # Normalize repeated whitespace.
        text = re.sub(
            r"\s+",
            " ",
            text,
        )

        # Normalize common punctuation.
        text = re.sub(
            r"\s*[,;]\s*",
            " ",
            text,
        )

        return text.strip()

    # ---------------------------------------------------------

    def _normalize_command_for_planning(
        self,
        command: str,
    ) -> str:
        """
        Normalize only high-confidence speech-to-text
        connector errors before sending the command to Gemini.

        Supported:

            10  -> then
            ten -> then

        ONLY when the connector occurs between recognizable
        actions.

        Examples:

            open notepad 10 type hello
                -> open notepad then type hello

            open notepad ten type hello
                -> open notepad then type hello

            type 10 students
                -> unchanged

            type ten students
                -> unchanged
        """

        text = self._normalize_for_detection(
            command
        )

        if not text:
            return command

        pattern = re.compile(
            r"\s+(10|ten)\s+",
            re.IGNORECASE,
        )

        while True:

            match = pattern.search(
                text
            )

            if match is None:
                break

            left = text[:match.start()].strip()
            right = text[match.end():].strip()

            # -------------------------------------------------
            # Only convert when:
            #
            # LEFT  = recognizable action
            # RIGHT = starts with recognizable action
            # -------------------------------------------------

            if (
                self._looks_like_action(left)
                and self._starts_with_action(right)
            ):

                text = (
                    left
                    + " then "
                    + right
                )

                continue

            # -------------------------------------------------
            # This occurrence is normal user content.
            #
            # Look for another occurrence later in the command.
            # -------------------------------------------------

            next_start = match.end()

            next_match = pattern.search(
                text,
                next_start,
            )

            if next_match is None:
                break

            # Do not globally replace the current occurrence.
            # The current token is ordinary user content.
            #
            # The next occurrence will be checked only if the
            # loop reaches it.
            break

        return text

    # =========================================================
    # Action Detection Helpers
    # =========================================================

    def _looks_like_action(
        self,
        text: str,
    ) -> bool:
        """
        Determine whether a text segment appears to contain
        a recognizable command action.

        This helper is used only for command-boundary detection.
        """

        if not text:
            return False

        value = text.strip().lower()

        if not value:
            return False

        # -----------------------------------------------------
        # Direct action-start detection
        # -----------------------------------------------------

        for action_word in self.ACTION_START_WORDS:

            if value.startswith(
                action_word + " "
            ):

                return True

            if value == action_word:

                return True

        # -----------------------------------------------------
        # Common action verb detection
        # -----------------------------------------------------

        action_pattern = (
            r"\b("
            r"open|launch|start|close|exit|quit|"
            r"search|find|click|type|write|press|"
            r"create|make|rename|copy|move|delete|"
            r"remove|download|play|visit|browse|"
            r"extract|compress"
            r")\b"
        )

        return bool(
            re.search(
                action_pattern,
                value,
            )
        )

    # ---------------------------------------------------------

    def _contains_action_aware_and(
        self,
        text: str,
    ) -> bool:
        """
        Detect "and" as a command connector only when the
        right side starts with a recognizable action.

        Examples:

            open notepad and type hello
                -> True

            open chrome and search google
                -> True

            type my name and department
                -> False
        """

        pattern = re.compile(
            r"\s+and\s+",
            re.IGNORECASE,
        )

        matches = list(
            pattern.finditer(text)
        )

        if not matches:
            return False

        for match in matches:

            left = text[:match.start()].strip()
            right = text[match.end():].strip()

            if not left or not right:
                continue

            if not self._starts_with_action(
                right
            ):

                continue

            if not self._looks_like_action(
                left
            ):

                continue

            return True

        return False

    # ---------------------------------------------------------

    def _starts_with_action(
        self,
        text: str,
    ) -> bool:
        """
        Check whether a text segment starts with a known
        action verb.
        """

        if not text:
            return False

        value = text.strip().lower()

        if not value:
            return False

        for action_word in self.ACTION_START_WORDS:

            if value.startswith(
                action_word + " "
            ):

                return True

            if value == action_word:

                return True

        return False

    # ---------------------------------------------------------

    def _contains_stt_then_connector(
        self,
        text: str,
    ) -> bool:
        """
        Detect speech-to-text substitutions:

            10
            ten

        only when they occur between two recognizable actions.

        Examples:

            open notepad 10 type hello
                -> True

            open notepad ten type hello
                -> True

            type 10 students
                -> False

            type ten students
                -> False
        """

        pattern = re.compile(
            r"\s+(10|ten)\s+",
            re.IGNORECASE,
        )

        for match in pattern.finditer(
            text
        ):

            left = text[:match.start()].strip()
            right = text[match.end():].strip()

            if not left or not right:
                continue

            if not self._looks_like_action(
                left
            ):
                continue

            if not self._starts_with_action(
                right
            ):
                continue

            return True

        return False

    # =========================================================
    # Gemini Integration
    # =========================================================

    def _generate_plan_response(
        self,
        prompt: str,
    ) -> str:
        """
        Generate a structured action plan using Gemini.
        """

        if not hasattr(
            self.gemini,
            "generate_structured_plan",
        ):

            raise AttributeError(
                "GeminiClient does not provide "
                "generate_structured_plan()."
            )

        response = (
            self.gemini.generate_structured_plan(
                prompt
            )
        )

        if response is None:

            raise RuntimeError(
                "Gemini returned an empty planning response."
            )

        response = str(
            response
        ).strip()

        if not response:

            raise RuntimeError(
                "Gemini returned an empty planning response."
            )

        return response

    # =========================================================
    # Prompt Construction
    # =========================================================

    def _build_prompt(
        self,
        command: str,
        original_command: Optional[str] = None,
    ) -> str:
        """
        Build the final Gemini planning prompt.
        """

        original = (
            original_command
            if original_command is not None
            else command
        )

        return (
            self.SYSTEM_PROMPT
            + "\n\n"
            + "ORIGINAL USER COMMAND:\n"
            + original
            + "\n\n"
            + "NORMALIZED COMMAND FOR PLANNING:\n"
            + command
            + "\n\n"
            + "IMPORTANT:\n"
            + "The normalized command may contain a corrected "
            + "speech-to-text connector. Preserve the intended "
            + "meaning and execute each independent action "
            + "sequentially.\n\n"
            + "Return ONLY the JSON action plan."
        )

    # =========================================================
    # JSON Parsing
    # =========================================================

    def _parse_json_response(
        self,
        response: str,
    ) -> Dict[str, Any]:
        """
        Parse Gemini's JSON response.

        Handles:
            - normal JSON
            - accidental Markdown code fences
            - surrounding whitespace
            - surrounding non-JSON text
        """

        if not response:

            raise ValueError(
                "Gemini returned an empty planning response."
            )

        cleaned = response.strip()

        # -----------------------------------------------------
        # Remove Markdown code fences.
        # -----------------------------------------------------

        if cleaned.startswith("```"):

            cleaned = re.sub(
                r"^```(?:json)?\s*",
                "",
                cleaned,
                flags=re.IGNORECASE,
            )

            cleaned = re.sub(
                r"\s*```$",
                "",
                cleaned,
            )

            cleaned = cleaned.strip()

        # -----------------------------------------------------
        # Direct JSON parsing.
        # -----------------------------------------------------

        try:

            data = json.loads(
                cleaned
            )

        except json.JSONDecodeError:

            # -------------------------------------------------
            # Extract outer JSON object.
            # -------------------------------------------------

            start = cleaned.find("{")
            end = cleaned.rfind("}")

            if start == -1 or end == -1:

                raise ValueError(
                    "Gemini response does not contain valid JSON."
                )

            json_text = cleaned[
                start : end + 1
            ]

            try:

                data = json.loads(
                    json_text
                )

            except json.JSONDecodeError as exc:

                raise ValueError(
                    f"Invalid JSON returned by Gemini: {exc}"
                ) from exc

        if not isinstance(
            data,
            dict,
        ):

            raise ValueError(
                "Gemini planning response must be a JSON object."
            )

        return data

    # =========================================================
    # Validation
    # =========================================================

    def _validate_plan(
        self,
        plan: ActionPlan,
    ) -> None:
        """
        Validate an ActionPlan before execution.
        """

        if not isinstance(
            plan,
            ActionPlan,
        ):

            raise TypeError(
                "Expected an ActionPlan instance."
            )

        if not plan.steps:

            raise ValueError(
                "Generated action plan contains no steps."
            )

        for index, step in enumerate(
            plan.steps
        ):

            if not isinstance(
                step,
                ActionStep,
            ):

                raise ValueError(
                    f"Step {index + 1} is not a valid ActionStep."
                )

            if not step.action:

                raise ValueError(
                    f"Step {index + 1} has no action."
                )

            action = step.action.strip().lower()

            step.action = action

            if action not in self.SUPPORTED_ACTIONS:

                raise ValueError(
                    "Unsupported action generated by Gemini: "
                    f"{action}"
                )

            if not isinstance(
                step.parameters,
                dict,
            ):

                raise ValueError(
                    f"Step {index + 1} parameters must be "
                    "a dictionary."
                )

            if not step.step_id:

                step.step_id = (
                    f"step_{index + 1}"
                )

        # -----------------------------------------------------
        # Ensure original command is available.
        # -----------------------------------------------------

        if not plan.original_command:

            plan.original_command = ""

    # =========================================================
    # Utility
    # =========================================================

    def plan_to_json(
        self,
        plan: ActionPlan,
    ) -> str:
        """
        Convert an ActionPlan into formatted JSON.
        """

        if not isinstance(
            plan,
            ActionPlan,
        ):

            raise TypeError(
                "Expected an ActionPlan instance."
            )

        return json.dumps(
            plan.to_dict(),
            indent=4,
            ensure_ascii=False,
            default=str,
        )


__all__ = [
    "MultiCommandPlanner",
]