"""
voice/text_to_speech.py

ASTRA-AI
Premium Multi-Provider Text To Speech Manager

Fallback order
--------------
1. Microsoft Edge Neural TTS
2. Piper Offline TTS
3. Windows SAPI / pyttsx3

The manager is responsible for deciding which
provider should speak. Individual engines should
only report success or failure.
"""

from __future__ import annotations

import threading
import time

from voice.edge_tts_engine import EdgeTTSEngine


class TextToSpeech:
    """
    Central Text-To-Speech Manager.

    Provider order:

        Edge TTS
            ↓ failure
        Piper TTS
            ↓ failure
        pyttsx3
            ↓ failure
        No speech
    """

    def __init__(self):

        # --------------------------------------------------
        # Provider Engines
        # --------------------------------------------------

        self.edge_engine = EdgeTTSEngine()

        # These imports are intentionally handled safely.
        #
        # The files will be created next:
        #
        # voice/piper_tts_engine.py
        # voice/pyttsx3_tts_engine.py
        #

        self.piper_engine = None

        self.pyttsx3_engine = None

        self._load_fallback_engines()

        # --------------------------------------------------
        # Compatibility
        # --------------------------------------------------

        # Existing ASTRA code may access self.engine.
        #
        # Keep Edge as the primary engine reference.

        self.engine = self.edge_engine

        # --------------------------------------------------
        # State
        # --------------------------------------------------

        self.enabled = True

        self._closing = False

        self.lock = threading.RLock()

        self.current_thread = None

        self._speaking = False

        self._stop_event = threading.Event()

    # ======================================================
    # Load Fallback Engines
    # ======================================================

    def _load_fallback_engines(self):
        """
        Load Piper and pyttsx3 safely.

        If either module is temporarily unavailable,
        ASTRA continues running with the providers that
        are available.
        """

        # --------------------------------------------------
        # Piper
        # --------------------------------------------------

        try:

            from voice.piper_tts_engine import PiperTTSEngine

            self.piper_engine = PiperTTSEngine()

            print(
                "Piper TTS Engine Ready."
            )

        except Exception as error:

            self.piper_engine = None

            print(
                f"Piper TTS Engine Unavailable : {error}"
            )

        # --------------------------------------------------
        # pyttsx3
        # --------------------------------------------------

        try:

            from voice.pyttsx3_tts_engine import (
                Pyttsx3TTSEngine
            )

            self.pyttsx3_engine = Pyttsx3TTSEngine()

            print(
                "pyttsx3 TTS Engine Ready."
            )

        except Exception as error:

            self.pyttsx3_engine = None

            print(
                f"pyttsx3 TTS Engine Unavailable : {error}"
            )

    # ======================================================
    # Speak
    # ======================================================

    def speak(
        self,
        text: str
    ):
        """
        Speak text using the fallback chain.

        This method is non-blocking.

        Provider order:

            Edge
            Piper
            pyttsx3
        """

        if self._closing:

            return

        if not self.enabled:

            return

        if text is None:

            return

        text = str(text).strip()

        if not text:

            return

        with self.lock:

            # ----------------------------------------------
            # Stop previous speech
            # ----------------------------------------------

            self.stop()

            self._stop_event.clear()

            # ----------------------------------------------
            # Start new speech worker
            # ----------------------------------------------

            self.current_thread = threading.Thread(

                target=self._speak_worker,

                args=(text,),

                daemon=True

            )

            self.current_thread.start()

    # ======================================================
    # Speech Worker
    # ======================================================

    def _speak_worker(
        self,
        text: str
    ):
        """
        Execute providers sequentially.

        IMPORTANT:
        A provider must return True only when it
        successfully completed speech.

        Returning False causes the next provider
        to be attempted.
        """

        self._speaking = True

        try:

            # ==================================================
            # PROVIDER 1
            # Edge TTS
            # ==================================================

            if (

                self.edge_engine is not None

                and

                not self._stop_event.is_set()

            ):

                print(
                    "\nTTS Provider : Edge TTS"
                )

                try:

                    success = self.edge_engine.speak_blocking(
                        text
                    )

                    if success:

                        print(
                            "TTS Success : Edge TTS"
                        )

                        return

                    print(
                        "Edge TTS failed. "
                        "Trying Piper TTS..."
                    )

                except Exception as error:

                    print(
                        f"Edge TTS Error : {error}"
                    )

            # ==================================================
            # PROVIDER 2
            # Piper TTS
            # ==================================================

            if (

                self.piper_engine is not None

                and

                not self._stop_event.is_set()

            ):

                print(
                    "TTS Provider : Piper TTS"
                )

                try:

                    success = self.piper_engine.speak_blocking(
                        text
                    )

                    if success:

                        print(
                            "TTS Success : Piper TTS"
                        )

                        return

                    print(
                        "Piper TTS failed. "
                        "Trying Windows pyttsx3..."
                    )

                except Exception as error:

                    print(
                        f"Piper TTS Error : {error}"
                    )

            # ==================================================
            # PROVIDER 3
            # pyttsx3
            # ==================================================

            if (

                self.pyttsx3_engine is not None

                and

                not self._stop_event.is_set()

            ):

                print(
                    "TTS Provider : Windows pyttsx3"
                )

                try:

                    success = self.pyttsx3_engine.speak_blocking(
                        text
                    )

                    if success:

                        print(
                            "TTS Success : Windows pyttsx3"
                        )

                        return

                    print(
                        "Windows pyttsx3 TTS failed."
                    )

                except Exception as error:

                    print(
                        f"pyttsx3 TTS Error : {error}"
                    )

            # ==================================================
            # All Providers Failed
            # ==================================================

            if not self._stop_event.is_set():

                print(
                    "\nTTS Error : "
                    "All TTS providers failed."
                )

        finally:

            self._speaking = False

    # ======================================================
    # Stop
    # ======================================================

    def stop(self):
        """
        Stop speech from all providers.
        """

        self._stop_event.set()

        # --------------------------------------------------
        # Edge
        # --------------------------------------------------

        try:

            if self.edge_engine is not None:

                self.edge_engine.stop()

        except Exception:

            pass

        # --------------------------------------------------
        # Piper
        # --------------------------------------------------

        try:

            if self.piper_engine is not None:

                self.piper_engine.stop()

        except Exception:

            pass

        # --------------------------------------------------
        # pyttsx3
        # --------------------------------------------------

        try:

            if self.pyttsx3_engine is not None:

                self.pyttsx3_engine.stop()

        except Exception:

            pass

        self._speaking = False

    # ======================================================
    # Enable / Disable
    # ======================================================

    def set_enabled(
        self,
        enabled=True
    ):

        self.enabled = bool(enabled)

        if not self.enabled:

            self.stop()

    # ======================================================
    # Speaking Status
    # ======================================================

    def speaking(self):

        if self._speaking:

            return True

        # --------------------------------------------------
        # Provider-level status check
        # --------------------------------------------------

        providers = (

            self.edge_engine,

            self.piper_engine,

            self.pyttsx3_engine,

        )

        for engine in providers:

            try:

                if (

                    engine is not None

                    and

                    hasattr(
                        engine,
                        "speaking"
                    )

                    and

                    engine.speaking()

                ):

                    return True

            except Exception:

                continue

        return False

    # ======================================================
    # Wait Until Speech Finishes
    # ======================================================

    def wait_until_done(self):

        while self.speaking():

            time.sleep(0.02)

    # ======================================================
    # Voice
    # ======================================================

    def set_voice(
        self,
        voice
    ):
        """
        Set voice for supported providers.

        Edge supports explicit Edge voice names.

        Piper / pyttsx3 may ignore the value when
        the provider uses a fixed configured voice.
        """

        providers = (

            self.edge_engine,

            self.piper_engine,

            self.pyttsx3_engine,

        )

        for engine in providers:

            try:

                if (

                    engine is not None

                    and

                    hasattr(
                        engine,
                        "set_voice"
                    )

                ):

                    engine.set_voice(
                        voice
                    )

            except Exception:

                continue

    # ======================================================
    # Rate
    # ======================================================

    def set_rate(
        self,
        rate
    ):

        providers = (

            self.edge_engine,

            self.piper_engine,

            self.pyttsx3_engine,

        )

        for engine in providers:

            try:

                if (

                    engine is not None

                    and

                    hasattr(
                        engine,
                        "set_rate"
                    )

                ):

                    engine.set_rate(
                        rate
                    )

            except Exception:

                continue

    # ======================================================
    # Volume
    # ======================================================

    def set_volume(
        self,
        volume
    ):

        providers = (

            self.edge_engine,

            self.piper_engine,

            self.pyttsx3_engine,

        )

        for engine in providers:

            try:

                if (

                    engine is not None

                    and

                    hasattr(
                        engine,
                        "set_volume"
                    )

                ):

                    engine.set_volume(
                        volume
                    )

            except Exception:

                continue

    # ======================================================
    # Cleanup
    # ======================================================

    def close(self):

        if self._closing:

            return

        self._closing = True

        # --------------------------------------------------
        # Stop current speech
        # --------------------------------------------------

        try:

            self.stop()

        except Exception:

            pass

        # --------------------------------------------------
        # Close Edge
        # --------------------------------------------------

        try:

            if self.edge_engine is not None:

                self.edge_engine.close()

        except Exception:

            pass

        # --------------------------------------------------
        # Close Piper
        # --------------------------------------------------

        try:

            if self.piper_engine is not None:

                self.piper_engine.close()

        except Exception:

            pass

        # --------------------------------------------------
        # Close pyttsx3
        # --------------------------------------------------

        try:

            if self.pyttsx3_engine is not None:

                self.pyttsx3_engine.close()

        except Exception:

            pass

        # --------------------------------------------------
        # Clear references
        # --------------------------------------------------

        self.edge_engine = None

        self.piper_engine = None

        self.pyttsx3_engine = None

        self.engine = None

        self.current_thread = None

        self._speaking = False

        print(
            "TextToSpeech shutdown completed."
        )