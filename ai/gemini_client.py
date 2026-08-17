"""
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
✓ Temporary in-memory conversation
✓ Context-aware replies
✓ Automatic language/style matching
✓ English support
✓ Tamil support
✓ Tanglish support
✓ Mixed Tamil + English support
✓ Thread safe
✓ Clean API-key logging
✓ Production-ready error handling

IMPORTANT
---------
Conversation history exists only in RAM.

It is NOT saved to SQLite or any permanent storage.

When the application closes:
    GeminiClient.close()
        ↓
    history.clear()
        ↓
    temporary conversation is erased.
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

    Responsibilities
    ----------------
    - Gemini API communication
    - API key rotation
    - Temporary conversation memory
    - Context-aware conversation
    - Language/style preservation
    - Structured action-plan generation

    This class does NOT execute desktop commands.
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
        # Temporary Conversation Memory
        # ------------------------------------------

        self.history: List[Dict[str, str]] = []

        # Maximum messages retained in RAM.
        #
        # Example:
        #
        # 20 user + assistant messages
        #
        # This prevents unnecessary RAM growth on
        # lower-end systems.
        self.max_history_messages = 40

        # Number of previous messages actually sent
        # to Gemini as conversational context.
        #
        # Keeping this smaller improves performance.
        self.context_messages = 12

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
        DHEEPTHI system personality and conversation rules.
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

If someone asks your name, answer naturally:

"My name is DHEEPTHI."

If someone asks who created you, answer naturally:

"I was created by Naresh."

If someone asks what ASTRA-AI is, answer naturally:

"ASTRA-AI is the desktop assistant application
that I work inside."

Never break this identity.

==================================================
CONVERSATION
==================================================

You are having an ongoing conversation with the user.

Use the recent conversation history provided
in the prompt.

Remember relevant information from earlier messages
during the current application session.

If the user refers to:

• "that"
• "it"
• "this"
• "he"
• "she"
• "the previous one"
• "what I said"
• "what you said"
• "earlier"
• "before"
• "continue"
• "explain more"

use the recent conversation context to understand
what the user means.

Do not behave as if every message is a completely
new conversation.

Do not repeat questions that have already been
answered when the required information exists
in the conversation history.

IMPORTANT:

Conversation memory is temporary.

The conversation exists only during the current
ASTRA-AI application session.

==================================================
LANGUAGE
==================================================

Automatically detect the language and communication
style used by the user.

The user's language/style should determine your
response language/style.

Supported styles include:

• English
• Tamil
• Tanglish
• Tamil + English mixed conversation

--------------------------------------------------
ENGLISH
--------------------------------------------------

If the user communicates in English:

Reply naturally in English.

Do not unnecessarily translate the response
into Tamil.

Example:

User:
"Can you explain Python?"

Good:

"Sure. Python is a high-level programming language
known for its simple syntax and wide range of uses."

--------------------------------------------------
TAMIL
--------------------------------------------------

If the user communicates in Tamil:

Reply naturally in Tamil.

Do not unnecessarily translate the response into
English.

Use natural conversational Tamil.

--------------------------------------------------
TANGLISH
--------------------------------------------------

If the user communicates in Tanglish:

Reply naturally in Tanglish.

Do NOT convert natural Tanglish into overly formal
Tamil.

Preserve the user's conversational style.

Example:

User:
"Chrome open pannu."

Good:

"Chrome open panniten."

User:
"Konjam wait pannu."

Good:

"Sure da, konjam wait pannunga."

User:
"Enakku Python explain pannu."

Good:

"Sure da. Python oru programming language..."

User:
"Idha simple ah sollu."

Good:

"Sure da, simple-ah explain pannuren."

--------------------------------------------------
MIXED LANGUAGE
--------------------------------------------------

If the user naturally mixes Tamil and English,
preserve the same mixed communication style.

Example:

User:
"Python oda main use enna da?"

Good:

"Python oda main use programming, automation,
data science, AI, web development madhiri
different areas-la irukku da."

Do NOT force the response into completely
formal Tamil.

Do NOT force the response into completely
English when the user is naturally using Tanglish.

==================================================
NATURAL FRIENDLY STYLE
==================================================

The user prefers a friendly conversational assistant.

Be:

• Friendly
• Natural
• Helpful
• Warm
• Clear
• Professional when necessary

You may naturally use conversational words such as:

• da
• nanba
• sure
• okay
• seri

when the user's communication style supports it.

Do not overuse them in every sentence.

Do not sound robotic.

==================================================
RESPONSE QUALITY
==================================================

Never intentionally truncate a response.

Never stop a sentence halfway.

Never give a one-word response unless the
question genuinely requires one word.

For greetings:

Keep the response short and natural.

For simple questions:

Give a concise but complete answer.

For explanations:

Provide enough useful detail.

For:

• why
• how
• explain
• compare
• teach
• difference
• examples

give a useful and complete explanation.

Do not unnecessarily produce huge responses
for simple conversational messages.

==================================================
CONVERSATIONAL CONTINUITY
==================================================

If the user says:

"okay"

"seri"

"continue"

"then?"

"what about that?"

"explain that"

"tell me more"

"why?"

interpret it using the recent conversation context.

Do not respond with:

"I don't know what you mean"

unless the context genuinely does not contain
enough information.

==================================================
DESKTOP ASSISTANT BEHAVIOR
==================================================

Behave like a premium personal desktop assistant.

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

Do not claim that an action was performed unless
the application backend actually reports that
the action was performed.

==================================================
IMPORTANT
==================================================

The user is interacting with DHEEPTHI,
not directly with the underlying AI service.

Always maintain DHEEPTHI identity.

Always follow the user's language and
conversation style naturally.

Always use available conversation context.
"""

    # ------------------------------------------------------
    # Add User Message
    # ------------------------------------------------------

    def add_user_message(
        self,
        text: str
    ):

        text = str(
            text
        ).strip()

        if not text:

            return

        with self.lock:

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

        text = str(
            text
        ).strip()

        if not text:

            return

        with self.lock:

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

        if len(
            self.history
        ) > self.max_history_messages:

            self.history = self.history[
                -self.max_history_messages:
            ]

    # ------------------------------------------------------
    # Build Conversation Context
    # ------------------------------------------------------

    def _build_conversation_context(
        self
    ) -> str:
        """
        Build recent conversation context.

        Only recent messages are sent to Gemini so that
        the prompt remains lightweight on lower-end
        systems.

        The complete temporary history remains in RAM.
        """

        if not self.history:

            return ""

        recent_history = self.history[
            -self.context_messages:
        ]

        context_parts = []

        for message in recent_history:

            role = message.get(
                "role",
                ""
            )

            text = message.get(
                "text",
                ""
            ).strip()

            if not text:

                continue

            if role == "user":

                context_parts.append(
                    f"User: {text}"
                )

            elif role == "assistant":

                context_parts.append(
                    f"DHEEPTHI: {text}"
                )

        if not context_parts:

            return ""

        return "\n".join(
            context_parts
        )

    # ------------------------------------------------------
    # Build Conversation Prompt
    # ------------------------------------------------------

    def build_prompt(
        self,
        user_message: str
    ):
        """
        Build a context-aware conversational prompt.

        IMPORTANT:
        The user message is already stored in history
        before this method is called.

        Therefore we exclude the newest user message
        from the historical context and append it
        separately as the current message.
        """

        user_message = str(
            user_message
        ).strip()

        prompt_parts = [

            self.system_prompt()

        ]

        # ------------------------------------------
        # Historical Context
        # ------------------------------------------

        historical_messages = self.history[:-1]

        recent_history = historical_messages[
            -self.context_messages:
        ]

        if recent_history:

            prompt_parts.append(
                "==================================================\n"
                "RECENT CONVERSATION\n"
                "=================================================="
            )

            for message in recent_history:

                role = message.get(
                    "role",
                    ""
                )

                text = message.get(
                    "text",
                    ""
                ).strip()

                if not text:

                    continue

                if role == "user":

                    prompt_parts.append(
                        f"User: {text}"
                    )

                elif role == "assistant":

                    prompt_parts.append(
                        f"DHEEPTHI: {text}"
                    )

        # ------------------------------------------
        # Current User Message
        # ------------------------------------------

        prompt_parts.append(
            "==================================================\n"
            "CURRENT USER MESSAGE\n"
            "=================================================="
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
        Lightweight prompt builder.

        Even short messages receive recent conversation
        context.

        This fixes the previous issue where short messages
        such as:

            "what did I say?"
            "why?"
            "continue"
            "what about that?"

        were sent to Gemini without conversation history.
        """

        user_message = str(
            user_message
        ).strip()

        prompt_parts = [

            self.system_prompt()

        ]

        # ------------------------------------------
        # Recent Context
        # ------------------------------------------

        historical_messages = self.history[:-1]

        recent_history = historical_messages[
            -self.context_messages:
        ]

        if recent_history:

            prompt_parts.append(
                "==================================================\n"
                "RECENT CONVERSATION\n"
                "=================================================="
            )

            for message in recent_history:

                role = message.get(
                    "role",
                    ""
                )

                text = message.get(
                    "text",
                    ""
                ).strip()

                if not text:

                    continue

                if role == "user":

                    prompt_parts.append(
                        f"User: {text}"
                    )

                elif role == "assistant":

                    prompt_parts.append(
                        f"DHEEPTHI: {text}"
                    )

        # ------------------------------------------
        # Current Message
        # ------------------------------------------

        prompt_parts.append(
            "==================================================\n"
            "CURRENT USER MESSAGE\n"
            "=================================================="
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

        text = str(
            text
        ).strip()

        replacements = (

            ("DHEEPTHI:", ""),

            ("Assistant:", ""),

            ("AI:", ""),

        )

        for old, new in replacements:

            text = text.replace(
                old,
                ""
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

        Conversation memory is maintained temporarily
        in RAM.

        The user's current message and recent conversation
        history are sent together to Gemini.

        API keys automatically rotate when the current
        key becomes unavailable.
        """

        if self._closing:

            return (
                "DHEEPTHI is shutting down."
            )

        user_message = str(
            user_message
        ).strip()

        if not user_message:

            return (
                "Please say something."
            )

        # ------------------------------------------
        # Save User Message
        # ------------------------------------------

        with self.lock:

            self.add_user_message(
                user_message
            )

            # --------------------------------------
            # Prompt Selection
            # --------------------------------------
            #
            # Both prompt types now include recent
            # conversation history.
            #
            # Short messages therefore retain context.
            # --------------------------------------

            if len(
                user_message
            ) < 150:

                prompt = (
                    self.build_simple_prompt(
                        user_message
                    )
                )

            else:

                prompt = (
                    self.build_prompt(
                        user_message
                    )
                )

        # ------------------------------------------
        # API Attempts
        # ------------------------------------------

        with self.lock:

            total_keys = len(
                self.api_keys
            )

            attempted_keys = set()

            for _ in range(
                total_keys
            ):

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

                            config=(
                                types.GenerateContentConfig(

                                    temperature=0.55,

                                    top_p=0.90,

                                    top_k=40,

                                    max_output_tokens=2048,

                                    candidate_count=1

                                )
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
        Generate a structured JSON action plan for
        ASTRA-AI multi-command execution.

        This method is intentionally separate from
        generate_response() because multi-command planning
        requires machine-readable JSON instead of a normal
        conversational response.

        Existing Gemini API-key rotation and fallback
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

            for _ in range(
                total_keys
            ):

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

                            config=(
                                types.GenerateContentConfig(

                                    temperature=0.10,

                                    top_p=0.90,

                                    top_k=20,

                                    max_output_tokens=4096,

                                    candidate_count=1,

                                    response_mime_type=(
                                        "application/json"
                                    )

                                )
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

            return [
                message.copy()
                for message in self.history
            ]

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

        IMPORTANT:

        Conversation history is intentionally cleared here.

        Therefore conversation memory is temporary and
        disappears when ASTRA-AI shuts down.
        """

        with self.lock:

            self._closing = True

            # ------------------------------------------
            # Erase temporary conversation memory
            # ------------------------------------------

            self.history.clear()

            # ------------------------------------------
            # Release Gemini client
            # ------------------------------------------

            self.client = None

            print(
                "Gemini Client shutdown completed."
            )