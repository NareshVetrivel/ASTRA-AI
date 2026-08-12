"""
ASTRA-AI Multi-Command Planner

Converts a long natural-language command into a structured
ActionPlan that can be executed sequentially.

The planner is responsible for:
    - Detecting whether a command requires multiple actions.
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

    Example:

        User:
            "Open Chrome then search Sona College and
             click the first result."

        Output:

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
                            "query": "Sona College"
                        }
                    ),
                    ActionStep(
                        action="click_search_result",
                        parameters={
                            "index": 0
                        }
                    )
                ]
            )
    """

    # ---------------------------------------------------------
    # Supported action names
    # ---------------------------------------------------------

    SUPPORTED_ACTIONS = {
        # Application
        "launch_application",
        "close_application",

        # Browser
        "open_website",
        "google_search",
        "youtube_search",
        "play_youtube",
        "click_search_result",

        # Files
        "open_file",
        "create_file",
        "rename_file",
        "copy_file",
        "move_file",
        "delete_file",

        # Folders
        "open_folder",
        "create_folder",
        "rename_folder",
        "copy_folder",
        "move_folder",
        "delete_folder",

        # Archive
        "compress_zip",
        "extract_zip",

        # Keyboard / text
        "type_text",
        "press_key",

        # Mouse
        "click",
        "double_click",
        "right_click",
    }

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
10. Use zero-based indexes for search results.
11. "first result" = index 0.
12. "second result" = index 1.
13. "third result" = index 2.
14. If the command is ambiguous, do not invent missing values.

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
        multiple actions.

        This is a lightweight first-pass detector.

        It is NOT the final planner.

        Examples
        --------
        "open chrome"
            -> False

        "open chrome then search google"
            -> True
        """

        if not command:
            return False

        text = command.strip().lower()

        if not text:
            return False

        # -----------------------------------------------------
        # Strong multi-command separators
        # -----------------------------------------------------

        separators = [
            " then ",
            " and then ",
            " after that ",
            " next ",
            " finally ",
        ]

        for separator in separators:

            if separator in text:
                return True

        # -----------------------------------------------------
        # Common command chaining patterns
        # -----------------------------------------------------

        patterns = [
            r"\bopen\b.*\bsearch\b",
            r"\bopen\b.*\bclick\b",
            r"\bsearch\b.*\bclick\b",
            r"\bcreate\b.*\bmove\b",
            r"\bfind\b.*\bmove\b",
            r"\bfind\b.*\bcopy\b",
            r"\brename\b.*\bmove\b",
            r"\bdownload\b.*\bopen\b",
            r"\bsearch\b.*\bplay\b",
        ]

        for pattern in patterns:

            if re.search(pattern, text):

                return True

        return False

    # ---------------------------------------------------------

    def create_plan(
        self,
        command: str,
    ) -> ActionPlan:
        """
        Create an ActionPlan from a natural-language command.

        The actual interpretation is delegated to Gemini.

        Raises
        ------
        ValueError
            If the command is empty or Gemini returns an
            invalid action plan.

        RuntimeError
            If Gemini cannot produce a usable plan.
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

        prompt = self._build_prompt(command)

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

            plan.original_command = command

            self._validate_plan(plan)

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
    # Gemini Integration
    # =========================================================

    def _generate_plan_response(
        self,
        prompt: str,
    ) -> str:
        """
        Generate a structured action plan using the
        dedicated Gemini planning method.

        GeminiClient handles:
            - API key rotation
            - quota fallback
            - invalid-key fallback
            - JSON response generation
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
    ) -> str:
        """
        Build the final Gemini planning prompt.
        """

        return (
            self.SYSTEM_PROMPT
            + "\n\n"
            + "USER COMMAND:\n"
            + command
            + "\n\n"
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
        """

        if not response:

            raise ValueError(
                "Gemini returned an empty planning response."
            )

        cleaned = response.strip()

        # -----------------------------------------------------
        # Remove Markdown code fences if Gemini accidentally
        # returns them.
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
        # First attempt: direct JSON parsing
        # -----------------------------------------------------

        try:

            data = json.loads(
                cleaned
            )

        except json.JSONDecodeError:

            # -------------------------------------------------
            # Second attempt:
            # Extract the outermost JSON object.
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

        if not isinstance(data, dict):

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

            if not step.action:

                raise ValueError(
                    f"Step {index + 1} has no action."
                )

            action = step.action.strip()

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

            # -------------------------------------------------
            # Give missing step IDs a deterministic value.
            # -------------------------------------------------

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

        Useful for logging and debugging.
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