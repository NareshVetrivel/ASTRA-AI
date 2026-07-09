"""
Microsoft Edge Text To Speech Engine
"""

import asyncio
import os
import tempfile

import edge_tts
import pygame


class EdgeTTSEngine:
    """
    Microsoft Edge Neural Text To Speech Engine
    """

    def __init__(self):

        self.voice = "en-US-JennyNeural"

        pygame.mixer.init()

    async def _generate_speech(self, text, file_path):

        communicate = edge_tts.Communicate(
            text=text,
            voice=self.voice
        )

        await communicate.save(file_path)

    def speak(self, text):

        if not text:
            return

        temp_file = tempfile.NamedTemporaryFile(
            delete=False,
            suffix=".mp3"
        )

        temp_path = temp_file.name

        temp_file.close()

        try:

            asyncio.run(
                self._generate_speech(
                    text,
                    temp_path
                )
            )

            pygame.mixer.music.load(temp_path)

            pygame.mixer.music.play()

            while pygame.mixer.music.get_busy():
                pygame.time.Clock().tick(10)

        finally:

            pygame.mixer.music.unload()

            if os.path.exists(temp_path):
                os.remove(temp_path)