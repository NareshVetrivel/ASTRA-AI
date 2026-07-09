"""
Text To Speech Wrapper

Uses Microsoft Edge TTS Engine.
"""

from voice.edge_tts_engine import EdgeTTSEngine


class TextToSpeech:
    """
    Public interface for ASTRA TTS.
    """

    def __init__(self):

        self.engine = EdgeTTSEngine()

    def speak(self, text):

        self.engine.speak(text)