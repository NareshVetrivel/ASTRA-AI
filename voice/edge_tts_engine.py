"""
Microsoft Edge Text To Speech Engine
"""

import asyncio
import os
import tempfile
import threading

import edge_tts
import pygame


class EdgeTTSEngine:
    """
    Microsoft Edge Neural Text To Speech Engine
    """

    def __init__(self):

        self.voice = "en-IN-NeerjaNeural"

        if not pygame.mixer.get_init():
            pygame.mixer.init()

    async def _generate_speech(self, text, file_path):
        """
        Generate speech using Microsoft Edge TTS.
        """

        communicate = edge_tts.Communicate(
            text=text,
            voice=self.voice
        )

        await communicate.save(file_path)

    def _speak_sync(self, text):
        """
        Generate and play speech inside
        a dedicated thread.
        """

        temp_file = tempfile.NamedTemporaryFile(
            delete=False,
            suffix=".mp3"
        )

        temp_path = temp_file.name
        temp_file.close()

        loop = asyncio.new_event_loop()

        try:

            asyncio.set_event_loop(loop)

            loop.run_until_complete(
                self._generate_speech(
                    text,
                    temp_path
                )
            )

        finally:

            loop.close()

        try:

            pygame.mixer.music.load(temp_path)

            pygame.mixer.music.play()

            while pygame.mixer.music.get_busy():
                pygame.time.Clock().tick(10)

        finally:

            try:
                pygame.mixer.music.unload()
            except Exception:
                pass

            if os.path.exists(temp_path):
                os.remove(temp_path)

    def speak(self, text):
        """
        Speak text asynchronously.
        """

        if not text:
            return

        threading.Thread(
            target=self._speak_sync,
            args=(text,),
            daemon=True
        ).start()