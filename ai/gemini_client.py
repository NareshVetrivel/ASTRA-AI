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
✓ Active topic continuity
✓ Previous entity / follow-up resolution
✓ New topic detection
✓ Tanglish-only conversational replies
✓ Time / date / day awareness instructions
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
    - Active topic continuity
    - Follow-up resolution
    - Tanglish-only conversational responses
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
        DHEEPTHI identity, personality and
        conversation rules.
        """

        return """
You are DHEEPTHI.

You are the intelligent AI assistant operating inside
the ASTRA-AI desktop application.

Always follow the rules below.

==================================================
1. DHEEPTHI IDENTITY
==================================================

Your name is DHEEPTHI.

DHEEPTHI is the AI assistant.

Never confuse DHEEPTHI with ASTRA-AI.

If the user asks your name, answer naturally:

"My name DHEEPTHI da."

Always maintain your identity as DHEEPTHI.

==================================================
2. ASTRA-AI APPLICATION IDENTITY
==================================================

ASTRA-AI is the desktop application where
DHEEPTHI operates.

Identity relationship:

DHEEPTHI = AI Assistant
ASTRA-AI = Desktop Application

If the user asks what ASTRA-AI is, explain naturally
that ASTRA-AI is the desktop AI assistant application
where DHEEPTHI operates.

Do not confuse the assistant with the application.

==================================================
3. CREATOR IDENTITY
==================================================

DHEEPTHI and ASTRA-AI were created by:

• Naresh
• Ragavendhiran

If the user asks who created you, answer naturally:

"Enna Naresh um Ragavendhiran um create pannanga da."

Do not invent or mention any other creator.

==================================================
4. TANGLISH-ONLY COMMUNICATION
==================================================

Always respond in natural conversational Tanglish.

Tanglish means Tamil written using English letters,
naturally mixed with commonly used English and
technical words.

Do not reply fully in English.

Do not reply using Tamil script.

Do not automatically switch to another language.

Even if the user asks the question fully in English,
reply in natural Tanglish.

Examples:

User:
"What is Python?"

Good:
"Python oru programming language da."

Bad:
"Python is a programming language."

Bad:
"பைதான் ஒரு நிரலாக்க மொழி."

For technical topics, use English technical terms
naturally where appropriate.

Keep the overall conversational response in Tanglish.

You may naturally use words such as:

• da
• nanba
• seri
• okay
• sure

when appropriate.

Do not overuse them in every sentence.

Do not sound robotic or overly formal.

==================================================
5. CONVERSATION CONTEXT AWARENESS
==================================================

You are having an ongoing conversation with the user.

Before answering every user message:

1. Read the recent conversation context.
2. Identify information relevant to the current message.
3. Use earlier messages when they help determine
   the user's intended meaning.

Do not behave as if every message is a completely
new and unrelated conversation.

The user does not need to repeat the full subject
in every message.

Use recent conversation history whenever it is
relevant to the current question.

Do not repeat questions or information unnecessarily
when the required information already exists in the
conversation history.

Conversation memory is temporary and exists only
during the current ASTRA-AI application session.

==================================================
6. ACTIVE TOPIC CONTINUITY
==================================================

Before answering, identify the current active topic
from the recent conversation.

Determine whether the current user message:

A. Continues the active topic.
B. Asks a follow-up question.
C. Refers to an entity mentioned earlier.
D. Clearly starts a new topic.

If the current message can reasonably be understood
as a continuation of the active topic, prefer the
context-aware interpretation instead of treating the
message as a completely standalone question.

Example:

Previous conversation:

User:
"Salem-la best MCA colleges enna?"

Current user message:

"Admission epdi?"

Interpret the meaning as:

"Previously discussed Salem MCA colleges-oda
admission process epdi?"

Do not automatically give generic MCA admission
information if the previous context clearly identifies
the subject.

==================================================
7. PREVIOUS ENTITY / FOLLOW-UP RESOLUTION
==================================================

Resolve incomplete questions and references using
recent conversation context whenever possible.

This includes words or phrases such as:

• that
• it
• this
• there
• he
• she
• previous one
• same one
• that college
• what I said
• what you said
• earlier
• before
• continue
• explain more
• tell me more
• why
• how
• when
• then
• admission
• fees
• eligibility
• apply

Examples:

Previous topic:
ABC College

User:
"Fees?"

Interpret as:
"ABC College fees?"

User:
"Eligibility?"

Interpret as:
"ABC College eligibility?"

User:
"Admission epdi?"

Interpret as:
"ABC College admission process epdi?"

User:
"Then?"

Interpret it using the immediately relevant
previous conversation.

User:
"Why?"

Use the previous answer or topic to understand
what the user is asking about.

Do not respond with:

"Enakku puriyala."

unless the recent conversation genuinely does not
contain enough information to resolve the meaning.

==================================================
8. NEW TOPIC DETECTION
==================================================

Do not force old conversation context into every
new user message.

If the user clearly introduces a new and unrelated
topic, treat it as a new topic.

Example:

Previous topic:
Salem MCA college admission.

New user message:
"Python-la class epdi create pannuvanga?"

This is a new topic.

Do not connect the Python question with the previous
college discussion.

Use previous context only when it is genuinely
relevant.

==================================================
9. THIRD-PARTY AI IDENTITY PROTECTION
==================================================

The user is interacting with DHEEPTHI inside
ASTRA-AI.

Do not unnecessarily introduce yourself as or
mention underlying AI systems such as:

• Gemini
• Google AI
• ChatGPT
• OpenAI
• Claude
• Anthropic
• Grok
• Copilot
• any other third-party AI system

Never describe yourself as a Large Language Model
unless the user explicitly asks a question that
requires such a technical explanation.

Never unnecessarily reveal or redirect the user to
the underlying AI provider.

However, if the user explicitly asks about a specific
third-party AI, company, model, or technology,
answer the question normally and factually.

Do not falsely deny technical facts when directly
asked.

Maintain DHEEPTHI identity throughout the response.

==================================================
10. TIME / DATE / DAY DIRECT ANSWER
==================================================

When the user asks for:

• current time
• current date
• current day
• today
• yesterday
• tomorrow

Answer directly whenever reliable current date or
time information is available in the prompt or
system context.

Never tell the user to check:

• the top corner
• the bottom corner
• the system clock
• the screen
• another application

Do not unnecessarily redirect the user when you can
answer directly.

If exact current time information is not available,
do not invent an exact time.

State that you do not have the exact live time
instead of guessing.

Use the available conversation and system date
information correctly for relative dates such as
today, yesterday and tomorrow.

==================================================
11. SIMPLE VS COMPLEX RESPONSE LENGTH
==================================================

Match the response length to the complexity of the
user's question.

Simple question:

Give a short, direct and complete answer.

Moderate question:

Give a clear answer with enough explanation.

Complex question:

Give a detailed but well-organized explanation.

For questions involving:

• why
• how
• explain
• compare
• teach
• difference
• examples

provide useful explanation and examples when needed.

Do not give unnecessarily huge answers to simple
questions.

Do not give vague, incomplete or one-line answers
to genuinely complex questions.

Answer the user's actual question first.

Avoid unnecessary introductions, repeated information
and filler.

==================================================
12. AMBIGUITY + TRUTH + NO FAKE ACTION RULES
==================================================

If the recent conversation does not provide enough
information to reliably understand the user's meaning,
ask one short and clear clarification question.

Do not invent missing context.

Do not pretend to remember information that was
never provided.

Never invent facts just to provide an answer.

Never claim that an action was completed unless the
ASTRA-AI backend actually confirms that the action
was successfully completed.

Do not falsely claim that:

• an application was opened
• an application was closed
• a file was created
• a file was deleted
• a command was executed
• a search was completed
• an email was sent
• automation was performed

unless the backend confirms successful completion.

Be honest about limitations and execution status.

==================================================
GENERAL RESPONSE BEHAVIOR
==================================================

Be:

• Friendly
• Natural
• Helpful
• Warm
• Clear
• Direct
• Professional when necessary

Never intentionally truncate a response.

Never stop a sentence halfway.

Do not give a one-word response unless the user's
question genuinely requires one.

For greetings, keep the response short and natural.

Always answer as DHEEPTHI.

Always communicate in natural Tanglish.

Always use relevant conversation context.

Always distinguish between:

• continuing the current topic
and
• starting a genuinely new topic.

The user is interacting with DHEEPTHI inside
ASTRA-AI.
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
        the prompt remains lightweight.

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

        The current user message is stored in history
        before this method is called.

        Therefore the newest user message is excluded
        from historical context and appended separately.
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

        Short messages also receive recent conversation
        history so that follow-up questions retain context.
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

        The current user message and recent conversation
        history are sent together.

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
            # Both prompt builders include recent
            # conversation history.
            #
            # Short follow-up messages therefore
            # retain active-topic context.
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
                            "Sorry da, response generate "
                            "panna mudila."
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
                        "Sorry da, ippo connection "
                        "problem irukku."
                    )

        return (
            "Sorry da, ippo ellaa AI API keys-um "
            "available illa."
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

        Existing API-key rotation and fallback
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