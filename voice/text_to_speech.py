"""
voice/text_to_speech.py

ASTRA-AI
Premium Text To Speech Manager
"""

import time

from voice.edge_tts_engine import EdgeTTSEngine


class TextToSpeech:
    """
    Central Text-To-Speech manager.
    """

    def __init__(self):

        self.engine = EdgeTTSEngine()

        self.enabled = True

        self._closing = False

    # --------------------------------------------------
    # Speak
    # --------------------------------------------------

    def speak(self, text):

        if self._closing:
            return

        if not self.enabled:
            return

        if not text:
            return

        text = str(text).strip()

        if not text:
            return

        try:

            self.engine.speak(text)

        except Exception as error:

            print(f"TTS Error : {error}")

    # --------------------------------------------------
    # Stop
    # --------------------------------------------------

    def stop(self):

        try:

            self.engine.stop()

        except Exception:

            pass

    # --------------------------------------------------
    # Enable / Disable
    # --------------------------------------------------

    def set_enabled(self, enabled=True):

        self.enabled = enabled

    # --------------------------------------------------
    # Speaking Status
    # --------------------------------------------------

    def speaking(self):
        """
        Return actual engine speaking status.
        """

        try:
            return self.engine.speaking()
        except Exception:
            return False

    # --------------------------------------------------
    # Wait Until Speech Finishes
    # --------------------------------------------------

    def wait_until_done(self):

        while self.speaking():

            time.sleep(0.05)

    # --------------------------------------------------
    # Voice
    # --------------------------------------------------

    def set_voice(self, voice):

        self.engine.set_voice(voice)

    # --------------------------------------------------
    # Rate
    # --------------------------------------------------

    def set_rate(self, rate):

        if hasattr(self.engine, "set_rate"):

            self.engine.set_rate(rate)

    # --------------------------------------------------
    # Volume
    # --------------------------------------------------

    def set_volume(self, volume):

        if hasattr(self.engine, "set_volume"):

            self.engine.set_volume(volume)

    # --------------------------------------------------
    # Cleanup
    # --------------------------------------------------

    def close(self):

        self._closing = True

        self.stop()

        self.engine = None

        print("TextToSpeech shutdown completed.")