"""
ai/gemini_client.py

ASTRA-AI

Google Gemini Client

Features
--------
✓ Gemini 2.5 Flash
✓ Multiple API Keys
✓ Automatic Key Rotation
✓ Conversation Memory
✓ Tanglish Support
✓ English Support
✓ Thread Safe
✓ Production Ready
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
    Central Gemini AI client used by ASTRA-AI.
    """

    # ------------------------------------------------------
    # Initialize
    # ------------------------------------------------------

    def __init__(self):

        # ------------------------------------------
        # API Keys
        # ------------------------------------------

        self.api_keys: List[str] = []

        if settings.GEMINI_API_KEY_1:

            self.api_keys.append(
                settings.GEMINI_API_KEY_1
            )

        if settings.GEMINI_API_KEY_2:

            self.api_keys.append(
                settings.GEMINI_API_KEY_2
            )

        if not self.api_keys:

            raise RuntimeError(
                "No Gemini API Keys configured."
            )

        self.current_key_index = 0

        self.model = settings.GEMINI_MODEL

        # ------------------------------------------
        # Conversation Memory
        # ------------------------------------------

        self.history: List[Dict[str, str]] = []

        # ------------------------------------------
        # Create Client
        # ------------------------------------------

        self.client = None

        self._create_client()

        self.lock = threading.Lock()

    # ------------------------------------------------------
    # Create Client
    # ------------------------------------------------------

    def _create_client(self):
        """
        Create Gemini client using
        current API key.
        """

        api_key = self.api_keys[
            self.current_key_index
        ]

        print("=" * 60)
        print("Creating Gemini Client")
        print("Model :", self.model)
        print("API Key :", api_key[:12] + "...")
        print("=" * 60)

        self.client = genai.Client(
            api_key=api_key
        )

    # ------------------------------------------------------
    # Rotate API Key
    # ------------------------------------------------------

    def rotate_api_key(self):
        """
        Switch to next API key.
        """

        if len(self.api_keys) <= 1:

            return False

        self.current_key_index += 1

        if self.current_key_index >= len(self.api_keys):

            self.current_key_index = 0

        self._create_client()

        print(
            f"Switched to Gemini API Key "
            f"{self.current_key_index + 1}"
        )

        return True

    # ------------------------------------------------------
    # System Prompt
    # ------------------------------------------------------

    def system_prompt(self):
        """
        DHEEPTHI System Prompt.
        """

        return """
You are DHEEPTHI.

You are the intelligent AI assistant inside the ASTRA-AI desktop application.

Your creator is Naresh.

Your name is DHEEPTHI.

ASTRA-AI is the application.

DHEEPTHI is the assistant.

Never introduce yourself as Gemini.

Never introduce yourself as Google AI.

Never introduce yourself as a Large Language Model.

If someone asks your name,
always answer:

"My name is DHEEPTHI."

If someone asks who created you,
always answer:

"I was created by Naresh."

If someone asks what ASTRA-AI is,
say:

"ASTRA-AI is the desktop assistant application that I work inside."

Behave like a premium desktop assistant.

Your speaking style:

• Detect English and Tanglish automatically.

• If user speaks Tanglish,
reply in natural Tanglish.

Example:
"Chrome open panniten."

"Konjam wait pannunga."

"Idha ippadi pannalaam."

• Never translate awkwardly.

• Never answer in one word unless absolutely necessary.

• If the user asks "explain", "why", "how", "compare", "teach",
give a complete explanation.

• If user greets you,
reply briefly.

• Always sound warm and natural.

• Never say you are an AI model.

Never break this identity.

You help users naturally.

If the user speaks English,
reply in fluent English.

If the user mixes Tamil and English
(Tanglish),
reply naturally in Tanglish.

Keep replies short unless
the user asks for detailed explanations.

You can explain programming,
technology,
college topics,
general knowledge,
productivity
and Windows usage.

Be friendly,
professional
and conversational.

Do not mention Google,
Gemini,
LLM
or AI model.

Behave like a real desktop assistant.
"""

    # ------------------------------------------------------
    # Add User Message
    # ------------------------------------------------------

    def add_user_message(
        self,
        text: str
    ):

        self.history.append(

            {

                "role": "user",

                "text": text.strip()

            }

        )

        if len(self.history) > 16:

            self.history = self.history[-16:]

    # ------------------------------------------------------
    # Add Assistant Message
    # ------------------------------------------------------

    def add_assistant_message(
        self,
        text: str
    ):

        self.history.append(

            {

                "role": "assistant",

                "text": text.strip()

            }

        )

        if len(self.history) > 40:

            self.history = self.history[-40:]

    # ------------------------------------------------------
    # Clear Memory
    # ------------------------------------------------------

    def clear_history(self):

        self.history.clear()

    # ------------------------------------------------------
    # Build Conversation
    # ------------------------------------------------------

    def build_prompt(
        self,
        user_message: str
    ):
        """
        Build complete conversation.
        """

        prompt = [

            self.system_prompt()

        ]

        for message in self.history[-6:]:

            if message["role"] == "user":

                prompt.append(

                    f"User: {message['text']}"

                )

            else:

                prompt.append(

                    f"DHEEPTHI: {message['text']}"

                )

        prompt.append(

            f"User: {user_message}"

        )

        prompt.append(

            "DHEEPTHI:"

        )

        return "\n\n".join(prompt)

    # ------------------------------------------------------
    # Generate Response
    # ------------------------------------------------------

    def generate_response(
        self,
        user_message: str
    ) -> str:
        """
        Generate AI response.

        Returns
        -------
        str
        """

        user_message = str(user_message).strip()

        if not user_message:

            return "Please say something."

        self.add_user_message(
            user_message
        )

        if len(user_message) < 150:

            prompt = (
                self.system_prompt()
                + "\n\n"
                + f"User: {user_message}\n"
                + "\nRules:\n"
                + "- Reply naturally.\n"
                + "- Detect English or Tanglish automatically.\n"
                + "- Never mention Gemini or Google.\n"
                + "- Never cut the answer halfway.\n"
                + "- Give detailed answers when explanation is requested.\n"
                + "- Give short answers only for greetings or simple questions.\n\n"
                + "DHEEPTHI:"
            )

        else:

            prompt = self.build_prompt(
                user_message
            )

        attempts = len(
            self.api_keys
        )

        with self.lock:

            for _ in range(attempts):

                try:

                    print(f"Using Model : {self.model}")

                    response = self.client.models.generate_content(

                        model=self.model,

                        contents=prompt,

                        config=types.GenerateContentConfig(

                            temperature=0.55,

                            top_p=0.90,

                            top_k=40,

                            max_output_tokens=1024,

                            candidate_count=1

                        )

                    )

                    text = ""

                    if (

                        response is not None

                        and

                        hasattr(response, "text")

                    ):

                        text = response.text.strip()

                        print("\n========== GEMINI RESPONSE ==========")
                        print(text)
                        print("Length :", len(text))
                        print("=====================================\n")

                        text = (
                            text
                            .replace("**", "")
                            .replace("__", "")
                            .replace("`", "")
                            .replace("DHEEPTHI:", "")
                            .replace("Assistant:", "")
                            .replace("AI:", "")
                            .strip()
                        )

                    if not text:

                        text = (

                            "Sorry, I couldn't "

                            "generate a response."

                        )

                    if len(user_message) > 80:

                        self.add_assistant_message(
                            text
                        )

                    return text

                except Exception as error:

                    print(

                        "\nGemini Error :",

                        error

                    )

                    error_text = str(error).lower()

                    if (

                        "429" in error_text

                        or

                        "quota" in error_text

                        or

                        "resource_exhausted" in error_text

                    ):

                        print(
                            "Quota exceeded."
                        )

                        if self.rotate_api_key():

                            continue

                    return (

                        "Sorry, I'm having trouble "

                        "connecting right now."

                    )

        return (

            "All Gemini API keys "

            "are currently unavailable."

        )

    # ------------------------------------------------------
    # Current API Key
    # ------------------------------------------------------

    def current_api_key(self):
        """
        Return current API key.
        """

        return self.api_keys[
            self.current_key_index
        ]

    # ------------------------------------------------------
    # Conversation History
    # ------------------------------------------------------

    def get_history(self):
        """
        Return conversation history.
        """

        return self.history.copy()

    # ------------------------------------------------------
    # History Count
    # ------------------------------------------------------

    def history_count(self):
        """
        Number of messages.
        """

        return len(
            self.history
        )

    # ------------------------------------------------------
    # Cleanup
    # ------------------------------------------------------

    def close(self):
        """
        Cleanup resources.
        """

        self.history.clear()

        self.client = None

        print(

            "Gemini Client shutdown completed."

        )