"""
voice/text_to_speech.py

ASTRA-AI
Premium Text To Speech Manager
"""

from __future__ import annotations

import threading
import time

from voice.edge_tts_engine import EdgeTTSEngine


class TextToSpeech:
    """
    Central Text-To-Speech Manager.
    """

    def __init__(self):

        self.engine = EdgeTTSEngine()

        self.enabled = True

        self._closing = False

        self.lock = threading.Lock()

    # --------------------------------------------------
    # Speak
    # --------------------------------------------------

    def speak(
        self,
        text: str
    ):

        if self._closing:

            return

        if not self.enabled:

            return

        if text is None:

            return

        text = str(text).strip()

        if not text:

            return

        try:

            with self.lock:

                if self.engine is not None:

                    self.engine.speak(text)

        except Exception as error:

            print(f"TTS Error : {error}")

    # --------------------------------------------------
    # Stop
    # --------------------------------------------------

    def stop(self):

        try:

            with self.lock:

                if self.engine is not None:

                    self.engine.stop()

        except Exception:

            pass

    # --------------------------------------------------
    # Enable / Disable
    # --------------------------------------------------

    def set_enabled(
        self,
        enabled=True
    ):

        self.enabled = bool(enabled)

    # --------------------------------------------------
    # Speaking Status
    # --------------------------------------------------

    def speaking(self):

        try:

            if self.engine is None:

                return False

            return self.engine.speaking()

        except Exception:

            return False

    # --------------------------------------------------
    # Wait Until Speech Finishes
    # --------------------------------------------------

    def wait_until_done(self):

        while self.speaking():

            time.sleep(0.02)

    # --------------------------------------------------
    # Voice
    # --------------------------------------------------

    def set_voice(
        self,
        voice
    ):

        try:

            if self.engine is not None:

                self.engine.set_voice(voice)

        except Exception:

            pass

    # --------------------------------------------------
    # Rate
    # --------------------------------------------------

    def set_rate(
        self,
        rate
    ):

        try:

            if (

                self.engine is not None

                and

                hasattr(self.engine, "set_rate")

            ):

                self.engine.set_rate(rate)

        except Exception:

            pass

    # --------------------------------------------------
    # Volume
    # --------------------------------------------------

    def set_volume(
        self,
        volume
    ):

        try:

            if (

                self.engine is not None

                and

                hasattr(self.engine, "set_volume")

            ):

                self.engine.set_volume(volume)

        except Exception:

            pass

    # --------------------------------------------------
    # Cleanup
    # --------------------------------------------------

    def close(self):

        self._closing = True

        try:

            self.stop()

        except Exception:

            pass

        self.engine = None

        print(

            "TextToSpeech shutdown completed."

        )