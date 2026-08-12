"""
ai/gemini_client.py

ASTRA-AI
DHEEPTHI Gemini Client

Features
--------
✓ Gemini Flash model
✓ Four API key support
✓ Automatic API key rotation
✓ Quota-aware fallback
✓ Invalid-key fallback
✓ Conversation memory
✓ Tanglish support
✓ English support
✓ Thread safe
✓ Clean API-key logging
✓ Production-ready error handling
"""

from __future__ import annotations

import threading
from typing import Dict, List

from google import genai
from google.genai import types

from config import settings


# ==========================================================
# Gemini Client
# ==========================================================

class GeminiClient:
    """
    Central Gemini AI client used by DHEEPTHI.

    Supports multiple Gemini API keys and automatically
    rotates to another key when the current key becomes
    unavailable.
    """

    # ------------------------------------------------------
    # Initialize
    # ------------------------------------------------------

    def __init__(self):

        # ------------------------------------------
        # API Keys
        # ------------------------------------------

        self.api_keys: List[str] = []

        for index in range(1, 5):

            key = getattr(
                settings,
                f"GEMINI_API_KEY_{index}",
                None
            )

            if key:

                key = str(key).strip()

                if key and key not in self.api_keys:

                    self.api_keys.append(key)

        if not self.api_keys:

            raise RuntimeError(
                "No Gemini API Keys configured."
            )

        # ------------------------------------------
        # Runtime
        # ------------------------------------------

        self.current_key_index = 0

        self.model = getattr(
            settings,
            "GEMINI_MODEL",
            "models/gemini-3.5-flash"
        )

        # ------------------------------------------
        # Conversation Memory
        # ------------------------------------------

        self.history: List[Dict[str, str]] = []

        self.max_history_messages = 40

        # ------------------------------------------
        # Thread Lock
        # ------------------------------------------

        self.lock = threading.RLock()

        # ------------------------------------------
        # Gemini Client
        # ------------------------------------------

        self.client = None

        self._closing = False

        self._create_client()

        print(
            f"Gemini Client Ready | "
            f"Model : {self.model} | "
            f"Keys : {len(self.api_keys)}"
        )

    # ------------------------------------------------------
    # Create Gemini Client
    # ------------------------------------------------------

    def _create_client(self):
        """
        Create Gemini client using the currently
        selected API key.
        """

        if self._closing:

            return

        api_key = self.api_keys[
            self.current_key_index
        ]

        print(
            "\nCreating Gemini Client..."
        )

        print(
            f"Model : {self.model}"
        )

        print(
            f"API Key : "
            f"{self._masked_key(api_key)}"
        )

        self.client = genai.Client(
            api_key=api_key
        )

    # ------------------------------------------------------
    # Mask API Key
    # ------------------------------------------------------

    @staticmethod
    def _masked_key(
        api_key: str
    ) -> str:
        """
        Safely display API key without exposing
        the actual secret.
        """

        if not api_key:

            return "Unavailable"

        if len(api_key) <= 8:

            return "********"

        return (
            api_key[:4]
            + "..."
            + api_key[-4:]
        )

    # ------------------------------------------------------
    # Rotate API Key
    # ------------------------------------------------------

    def rotate_api_key(self):
        """
        Switch to the next available Gemini API key.

        Returns
        -------
        bool
            True if another key is available.
        """

        with self.lock:

            if len(self.api_keys) <= 1:

                print(
                    "No alternate Gemini API key available."
                )

                return False

            old_index = self.current_key_index

            self.current_key_index = (
                self.current_key_index + 1
            ) % len(self.api_keys)

            # If we have already cycled through every key,
            # caller can decide whether to stop.
            if (
                self.current_key_index
                == old_index
            ):

                return False

            self._create_client()

            print(
                f"Switched to Gemini API Key "
                f"{self.current_key_index + 1}/"
                f"{len(self.api_keys)}"
            )

            return True

    # ------------------------------------------------------
    # System Prompt
    # ------------------------------------------------------

    def system_prompt(self):
        """
        DHEEPTHI system personality and language rules.
        """

        return """
You are DHEEPTHI.

You are the intelligent AI assistant inside the
ASTRA-AI desktop application.

Your creator is Naresh.

Your name is DHEEPTHI.

ASTRA-AI is the application.

DHEEPTHI is the assistant.

==================================================
IDENTITY
==================================================

Never introduce yourself as Gemini.

Never introduce yourself as Google AI.

Never introduce yourself as a Large Language Model.

If someone asks your name, answer:

"My name is DHEEPTHI."

If someone asks who created you, answer:

"I was created by Naresh."

If someone asks what ASTRA-AI is, answer naturally:

"ASTRA-AI is the desktop assistant application that I
work inside."

Never break this identity.

==================================================
LANGUAGE
==================================================

Detect the user's language automatically.

Supported conversational styles include:

• English
• Tamil
• Tanglish
• Mixed English + Tamil

If the user speaks English:

Reply naturally in fluent English.

If the user speaks Tanglish:

Reply naturally in Tanglish.

Do NOT translate Tanglish into awkward formal Tamil.

Examples:

User:
"Chrome open pannu."

Good:
"Chrome open panniten."

User:
"Konjam wait pannu."

Good:
"Sure, konjam wait pannunga."

User:
"YouTube la oru song podu."

Good:
"Sure, YouTube-la song play pannuren."

User:
"Enakku Python explain pannu."

Good:
"Sure. Python oru programming language..."

If the user mixes Tamil and English,
preserve that natural mixed style.

==================================================
RESPONSE QUALITY
==================================================

Never intentionally truncate a response.

Never stop a sentence halfway.

Never give a one-word response unless the
question genuinely requires one word.

For greetings:

Keep the response short and natural.

For simple commands:

Give a concise confirmation.

For explanations:

Provide a complete and useful explanation.

For:

• why
• how
• explain
• compare
• teach
• difference
• examples

give enough detail to properly answer the user.

Do not unnecessarily produce huge responses
for simple desktop commands.

==================================================
DESKTOP ASSISTANT BEHAVIOR
==================================================

Behave like a premium personal desktop assistant.

Be:

• Friendly
• Natural
• Helpful
• Professional
• Conversational

You can help with:

• Programming
• Technology
• College topics
• General knowledge
• Productivity
• Windows usage
• Files
• Applications
• Automation
• AI concepts

Do not mention:

• Gemini
• Google
• LLM
• internal model details

unless the user explicitly asks about the underlying
technology.

==================================================
IMPORTANT
==================================================

The user is interacting with DHEEPTHI,
not directly with the underlying AI service.

Always maintain DHEEPTHI identity.
"""

    # ------------------------------------------------------
    # Add User Message
    # ------------------------------------------------------

    def add_user_message(
        self,
        text: str
    ):

        text = str(text).strip()

        if not text:

            return

        self.history.append(

            {
                "role": "user",
                "text": text
            }

        )

        self._trim_history()

    # ------------------------------------------------------
    # Add Assistant Message
    # ------------------------------------------------------

    def add_assistant_message(
        self,
        text: str
    ):

        text = str(text).strip()

        if not text:

            return

        self.history.append(

            {
                "role": "assistant",
                "text": text
            }

        )

        self._trim_history()

    # ------------------------------------------------------
    # Trim History
    # ------------------------------------------------------

    def _trim_history(self):

        if len(self.history) > self.max_history_messages:

            self.history = self.history[
                -self.max_history_messages:
            ]

    # ------------------------------------------------------
    # Clear Memory
    # ------------------------------------------------------

    def clear_history(self):

        with self.lock:

            self.history.clear()

    # ------------------------------------------------------
    # Build Conversation
    # ------------------------------------------------------

    def build_prompt(
        self,
        user_message: str
    ):
        """
        Build conversation prompt using recent memory.
        """

        prompt_parts = [

            self.system_prompt()

        ]

        for message in self.history[-8:]:

            if message["role"] == "user":

                prompt_parts.append(

                    f"User: {message['text']}"

                )

            elif message["role"] == "assistant":

                prompt_parts.append(

                    f"DHEEPTHI: {message['text']}"

                )

        prompt_parts.append(

            f"User: {user_message}"

        )

        prompt_parts.append(

            "DHEEPTHI:"

        )

        return "\n\n".join(
            prompt_parts
        )

    # ------------------------------------------------------
    # Build Simple Prompt
    # ------------------------------------------------------

    def build_simple_prompt(
        self,
        user_message: str
    ):
        """
        Build a lightweight prompt for short commands.
        """

        return (

            self.system_prompt()

            + "\n\n"

            + f"User: {user_message}"

            + "\n\n"

            + "Rules:\n"

            + "- Detect English, Tamil or Tanglish automatically.\n"

            + "- Reply naturally in the user's language style.\n"

            + "- Never mention Gemini or Google.\n"

            + "- Never truncate the answer.\n"

            + "- Keep simple commands concise.\n"

            + "- Give complete explanations when requested.\n"

            + "\nDHEEPTHI:"

        )

    # ------------------------------------------------------
    # Is Retryable Error
    # ------------------------------------------------------

    @staticmethod
    def _is_retryable_error(
        error
    ):
        """
        Detect errors where another API key should
        be attempted.
        """

        error_text = str(
            error
        ).lower()

        retry_keywords = (

            "429",

            "quota",

            "resource_exhausted",

            "rate limit",

            "too many requests",

            "401",

            "403",

            "unauthorized",

            "permission denied",

            "api key",

            "invalid argument",

        )

        return any(
            keyword in error_text
            for keyword in retry_keywords
        )

    # ------------------------------------------------------
    # Clean Response
    # ------------------------------------------------------

    @staticmethod
    def _clean_response(
        text: str
    ) -> str:
        """
        Clean unnecessary formatting while preserving
        the actual answer.
        """

        if not text:

            return ""

        text = str(text).strip()

        replacements = (

            ("DHEEPTHI:", ""),

            ("Assistant:", ""),

            ("AI:", ""),

        )

        for old, new in replacements:

            text = text.replace(
                old,
                new
            )

        text = (
            text
            .replace("**", "")
            .replace("__", "")
            .replace("`", "")
            .strip()
        )

        return text

    # ------------------------------------------------------
    # Generate Response
    # ------------------------------------------------------

    def generate_response(
        self,
        user_message: str
    ) -> str:
        """
        Generate DHEEPTHI response.

        Automatically rotates through all configured
        Gemini API keys when the current key fails.
        """

        if self._closing:

            return (
                "DHEEPTHI is shutting down."
            )

        user_message = str(
            user_message
        ).strip()

        if not user_message:

            return "Please say something."

        # ------------------------------------------
        # Save User Message
        # ------------------------------------------

        with self.lock:

            self.add_user_message(
                user_message
            )

        # ------------------------------------------
        # Prompt Selection
        # ------------------------------------------

        if len(user_message) < 150:

            prompt = self.build_simple_prompt(
                user_message
            )

        else:

            prompt = self.build_prompt(
                user_message
            )

        # ------------------------------------------
        # API Attempts
        # ------------------------------------------

        with self.lock:

            total_keys = len(
                self.api_keys
            )

            attempted_keys = set()

            for _ in range(total_keys):

                if self._closing:

                    return (
                        "DHEEPTHI is shutting down."
                    )

                current_index = (
                    self.current_key_index
                )

                if current_index in attempted_keys:

                    break

                attempted_keys.add(
                    current_index
                )

                try:

                    print(
                        f"Using Gemini Key "
                        f"{current_index + 1}/"
                        f"{total_keys}"
                    )

                    print(
                        f"Using Model : "
                        f"{self.model}"
                    )

                    response = (
                        self.client.models.generate_content(

                            model=self.model,

                            contents=prompt,

                            config=types.GenerateContentConfig(

                                temperature=0.55,

                                top_p=0.90,

                                top_k=40,

                                max_output_tokens=2048,

                                candidate_count=1

                            )

                        )
                    )

                    # ----------------------------------
                    # Extract Response
                    # ----------------------------------

                    text = ""

                    if response is not None:

                        if hasattr(
                            response,
                            "text"
                        ):

                            text = (
                                response.text
                                or ""
                            ).strip()

                    text = self._clean_response(
                        text
                    )

                    print(
                        "\n========== DHEEPTHI RESPONSE =========="
                    )

                    print(
                        text
                    )

                    print(
                        "Length :",
                        len(text)
                    )

                    print(
                        "Key Used :",
                        current_index + 1
                    )

                    print(
                        "=======================================\n"
                    )

                    if not text:

                        text = (
                            "Sorry, I couldn't "
                            "generate a response."
                        )

                    # ----------------------------------
                    # Save Assistant Response
                    # ----------------------------------

                    self.add_assistant_message(
                        text
                    )

                    return text

                except Exception as error:

                    print(
                        "\nGemini Error :",
                        error
                    )

                    # ----------------------------------
                    # Retry With Next Key
                    # ----------------------------------

                    if self._is_retryable_error(
                        error
                    ):

                        print(
                            "Current Gemini API key "
                            "is unavailable."
                        )

                        if self.rotate_api_key():

                            continue

                    # ----------------------------------
                    # Non-retryable Error
                    # ----------------------------------

                    print(
                        "Gemini request failed."
                    )

                    return (
                        "Sorry, I'm having trouble "
                        "connecting right now."
                    )

        return (
            "All Gemini API keys are "
            "currently unavailable."
        )

    # ------------------------------------------------------
    # Generate Structured Action Plan
    # ------------------------------------------------------

    def generate_structured_plan(
        self,
        prompt: str
    ) -> str:
        """
        Generate a structured JSON action plan for ASTRA-AI
        multi-command execution.

        This method is intentionally separate from
        generate_response() because multi-command planning
        requires machine-readable JSON instead of a normal
        conversational response.

        The existing Gemini API-key rotation and fallback
        mechanism is preserved.
        """

        if self._closing:

            return ""

        prompt = str(
            prompt
        ).strip()

        if not prompt:

            return ""

        # ------------------------------------------
        # API Attempts
        # ------------------------------------------

        with self.lock:

            total_keys = len(
                self.api_keys
            )

            attempted_keys = set()

            for _ in range(total_keys):

                if self._closing:

                    return ""

                current_index = (
                    self.current_key_index
                )

                if current_index in attempted_keys:

                    break

                attempted_keys.add(
                    current_index
                )

                try:

                    print(
                        f"Using Gemini Planner Key "
                        f"{current_index + 1}/"
                        f"{total_keys}"
                    )

                    print(
                        f"Using Model : "
                        f"{self.model}"
                    )

                    response = (
                        self.client.models.generate_content(

                            model=self.model,

                            contents=prompt,

                            config=types.GenerateContentConfig(

                                temperature=0.10,

                                top_p=0.90,

                                top_k=20,

                                max_output_tokens=4096,

                                candidate_count=1,

                                response_mime_type="application/json"

                            )

                        )
                    )

                    # ----------------------------------
                    # Extract Response
                    # ----------------------------------

                    text = ""

                    if response is not None:

                        if hasattr(
                            response,
                            "text"
                        ):

                            text = (
                                response.text
                                or ""
                            ).strip()

                    if not text:

                        raise RuntimeError(
                            "Gemini returned an empty "
                            "structured-plan response."
                        )

                    print(
                        "\n========== GEMINI ACTION PLAN =========="
                    )

                    print(
                        text
                    )

                    print(
                        "Length :",
                        len(text)
                    )

                    print(
                        "Key Used :",
                        current_index + 1
                    )

                    print(
                        "========================================\n"
                    )

                    return text

                except Exception as error:

                    print(
                        "\nGemini Planner Error :",
                        error
                    )

                    # ----------------------------------
                    # Retry With Next API Key
                    # ----------------------------------

                    if self._is_retryable_error(
                        error
                    ):

                        print(
                            "Current Gemini API key "
                            "is unavailable for planning."
                        )

                        if self.rotate_api_key():

                            continue

                    # ----------------------------------
                    # Non-retryable Error
                    # ----------------------------------

                    print(
                        "Gemini structured planning "
                        "request failed."
                    )

                    return ""

        return ""

    # ------------------------------------------------------
    # Current API Key
    # ------------------------------------------------------

    def current_api_key(self):
        """
        Return the currently selected API key.

        Internal use only.
        """

        return self.api_keys[
            self.current_key_index
        ]

    # ------------------------------------------------------
    # Current API Key Number
    # ------------------------------------------------------

    def current_api_key_number(self):

        return (
            self.current_key_index + 1
        )

    # ------------------------------------------------------
    # Total API Keys
    # ------------------------------------------------------

    def total_api_keys(self):

        return len(
            self.api_keys
        )

    # ------------------------------------------------------
    # Conversation History
    # ------------------------------------------------------

    def get_history(self):

        with self.lock:

            return self.history.copy()

    # ------------------------------------------------------
    # History Count
    # ------------------------------------------------------

    def history_count(self):

        with self.lock:

            return len(
                self.history
            )

    # ------------------------------------------------------
    # Cleanup
    # ------------------------------------------------------

    def close(self):
        """
        Cleanup Gemini resources.
        """

        with self.lock:

            self._closing = True

            self.history.clear()

            self.client = None

            print(
                "Gemini Client shutdown completed."
            )