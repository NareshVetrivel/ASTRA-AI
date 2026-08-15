"""
voice/pyttsx3_tts_engine.py

ASTRA-AI
Windows Offline Text-To-Speech Engine

Provider
--------
Windows SAPI through pyttsx3

Fallback position
-----------------
1. Edge TTS
2. Piper TTS
3. pyttsx3 / Windows SAPI

Features
--------
✓ Fully offline
✓ Windows native speech engine
✓ Female voice selection
✓ Thread safe
✓ Stop current speech
✓ Explicit success/failure reporting
✓ Compatible with TextToSpeech manager
"""

from __future__ import annotations

import threading

import pyttsx3


class Pyttsx3TTSEngine:
    """
    Windows SAPI based TTS engine.

    This engine is the final offline fallback
    when Edge and Piper are unavailable.
    """

    def __init__(self):

        # --------------------------------------------------
        # State
        # --------------------------------------------------

        self.lock = threading.RLock()

        self.current_thread = None

        self.stop_event = threading.Event()

        self.is_speaking = False

        self._closed = False

        # --------------------------------------------------
        # Voice settings
        # --------------------------------------------------

        self.voice = None

        self.rate = 170

        self.volume = 1.0

        # --------------------------------------------------
        # Available voices
        # --------------------------------------------------

        self.voices = []

        # --------------------------------------------------
        # Engine
        # --------------------------------------------------

        self.engine = None

        try:

            self.engine = pyttsx3.init()

            self.voices = self.engine.getProperty(
                "voices"
            )

            print(
                f"pyttsx3 voices detected : "
                f"{len(self.voices)}"
            )

            # ----------------------------------------------
            # Select female voice
            # ----------------------------------------------

            selected_voice = self._find_female_voice()

            if selected_voice is not None:

                self.voice = selected_voice

                self.engine.setProperty(
                    "voice",
                    selected_voice
                )

                print(
                    "pyttsx3 female voice selected."
                )

            elif self.voices:

                self.voice = self.voices[0].id

                self.engine.setProperty(
                    "voice",
                    self.voice
                )

                print(
                    "pyttsx3 female voice not detected. "
                    "Using first available voice."
                )

            # ----------------------------------------------
            # Default rate
            # ----------------------------------------------

            self.engine.setProperty(
                "rate",
                self.rate
            )

            # ----------------------------------------------
            # Default volume
            # ----------------------------------------------

            self.engine.setProperty(
                "volume",
                self.volume
            )

        except Exception as error:

            self.engine = None

            print(
                f"pyttsx3 initialization error : {error}"
            )

    # ======================================================
    # Find Female Voice
    # ======================================================

    def _find_female_voice(self):
        """
        Find the best available female Windows SAPI voice.

        Returns
        -------
        str | None
            Voice ID when found.
        """

        if not self.voices:

            return None

        female_keywords = [

            "female",
            "zira",
            "samantha",
            "hazel",
            "heera",
            "kalpana",
            "susan",
            "aria",
            "jenny",
            "neerja",

        ]

        # --------------------------------------------------
        # First pass: explicit female metadata/name
        # --------------------------------------------------

        for voice in self.voices:

            try:

                voice_id = str(
                    getattr(
                        voice,
                        "id",
                        ""
                    )
                ).lower()

                voice_name = str(
                    getattr(
                        voice,
                        "name",
                        ""
                    )
                ).lower()

                voice_description = str(
                    getattr(
                        voice,
                        "languages",
                        ""
                    )
                ).lower()

                combined = (

                    voice_id
                    + " "
                    + voice_name
                    + " "
                    + voice_description

                )

                for keyword in female_keywords:

                    if keyword in combined:

                        return voice.id

            except Exception:

                continue

        # --------------------------------------------------
        # Second pass: inspect voice metadata
        # --------------------------------------------------

        for voice in self.voices:

            try:

                gender = str(
                    getattr(
                        voice,
                        "gender",
                        ""
                    )
                ).lower()

                if "female" in gender:

                    return voice.id

            except Exception:

                continue

        return None

    # ======================================================
    # Blocking Speak
    # ======================================================

    def speak_blocking(
        self,
        text
    ):
        """
        Speak text synchronously through Windows SAPI.

        Returns
        -------
        bool
            True  -> speech completed successfully.
            False -> speech failed.
        """

        if self._closed:

            return False

        if self.engine is None:

            return False

        if not text:

            return False

        text = str(text).strip()

        if not text:

            return False

        with self.lock:

            self.stop_event.clear()

            self.is_speaking = True

            try:

                # ------------------------------------------
                # Apply current settings
                # ------------------------------------------

                if self.voice:

                    self.engine.setProperty(
                        "voice",
                        self.voice
                    )

                self.engine.setProperty(
                    "rate",
                    self.rate
                )

                self.engine.setProperty(
                    "volume",
                    self.volume
                )

                # ------------------------------------------
                # Queue speech
                # ------------------------------------------

                self.engine.say(
                    text
                )

                # ------------------------------------------
                # Run speech
                # ------------------------------------------

                if self.stop_event.is_set():

                    self.engine.stop()

                    return False

                self.engine.runAndWait()

                # ------------------------------------------
                # Stop requested
                # ------------------------------------------

                if self.stop_event.is_set():

                    try:

                        self.engine.stop()

                    except Exception:

                        pass

                    return False

                return True

            except Exception as error:

                print(
                    f"pyttsx3 TTS Error : {error}"
                )

                return False

            finally:

                self.is_speaking = False

    # ======================================================
    # Non-Blocking Speak
    # ======================================================

    def speak(
        self,
        text
    ):
        """
        Non-blocking public speak method.
        """

        if self._closed:

            return None

        if not text:

            return None

        text = str(text).strip()

        if not text:

            return None

        with self.lock:

            self.stop()

            self.current_thread = threading.Thread(

                target=self.speak_blocking,

                args=(text,),

                daemon=True

            )

            self.current_thread.start()

            return self.current_thread

    # ======================================================
    # Stop
    # ======================================================

    def stop(self):
        """
        Stop current Windows speech.
        """

        self.stop_event.set()

        try:

            if self.engine is not None:

                self.engine.stop()

        except Exception:

            pass

        self.is_speaking = False

    # ======================================================
    # Voice
    # ======================================================

    def set_voice(
        self,
        voice
    ):
        """
        Set a specific Windows SAPI voice.

        If the supplied voice does not exist,
        the current voice is preserved.
        """

        if not voice:

            return

        if not self.voices:

            return

        voice = str(
            voice
        )

        for available_voice in self.voices:

            try:

                if (

                    str(
                        getattr(
                            available_voice,
                            "id",
                            ""
                        )
                    )

                    == voice

                ):

                    self.voice = (
                        available_voice.id
                    )

                    if self.engine is not None:

                        self.engine.setProperty(
                            "voice",
                            self.voice
                        )

                    return

            except Exception:

                continue

    # ======================================================
    # Rate
    # ======================================================

    def set_rate(
        self,
        rate
    ):

        try:

            self.rate = int(
                rate
            )

        except (
            TypeError,
            ValueError
        ):

            self.rate = 170

        if self.engine is not None:

            try:

                self.engine.setProperty(
                    "rate",
                    self.rate
                )

            except Exception:

                pass

    # ======================================================
    # Volume
    # ======================================================

    def set_volume(
        self,
        volume
    ):

        try:

            value = float(
                volume
            )

            # Support both:
            #
            # 0.0 - 1.0
            # 0   - 100

            if value > 1.0:

                value = value / 100.0

            self.volume = max(
                0.0,
                min(
                    value,
                    1.0
                )
            )

        except (
            TypeError,
            ValueError
        ):

            self.volume = 1.0

        if self.engine is not None:

            try:

                self.engine.setProperty(
                    "volume",
                    self.volume
                )

            except Exception:

                pass

    # ======================================================
    # Get Voices
    # ======================================================

    def get_voices(self):
        """
        Return available Windows SAPI voices.

        Useful for debugging or future voice
        selection UI.
        """

        result = []

        for voice in self.voices:

            try:

                result.append(
                    {
                        "id": getattr(
                            voice,
                            "id",
                            ""
                        ),

                        "name": getattr(
                            voice,
                            "name",
                            ""
                        ),

                        "languages": getattr(
                            voice,
                            "languages",
                            []
                        ),
                    }
                )

            except Exception:

                continue

        return result

    # ======================================================
    # Status
    # ======================================================

    def speaking(self):

        return self.is_speaking

    # ======================================================
    # Cleanup
    # ======================================================

    def close(self):

        if self._closed:

            return

        self._closed = True

        try:

            self.stop()

        except Exception:

            pass

        self.current_thread = None

        self.engine = None

        self.voices = []

        print(
            "pyttsx3 TTS Engine shutdown completed."
        )