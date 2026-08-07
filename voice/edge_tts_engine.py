"""
voice/edge_tts_engine.py

ASTRA-AI
Premium Microsoft Edge Neural TTS Engine

Features
--------
✓ Microsoft Edge Neural Voice
✓ Non-blocking
✓ Thread Safe
✓ Stop Current Speech
✓ Queue Safe
✓ Auto Cleanup
"""

import asyncio
import os
import tempfile
import threading

import edge_tts
import pygame


class EdgeTTSEngine:

    def __init__(self):

        self.voice = "en-IN-NeerjaNeural"

        self.lock = threading.Lock()

        self.current_thread = None

        self.stop_event = threading.Event()

        self.is_speaking = False

        if not pygame.mixer.get_init():

            pygame.mixer.init()

    # --------------------------------------------------
    # Generate Speech
    # --------------------------------------------------

    async def _generate(self, text, filename):

        communicate = edge_tts.Communicate(

            text=text,

            voice=self.voice

        )

        await communicate.save(filename)

    # --------------------------------------------------
    # Internal Speaker
    # --------------------------------------------------

    def _worker(self, text):

        self.stop_event.clear()

        self.is_speaking = True

        temp = tempfile.NamedTemporaryFile(

            delete=False,

            suffix=".mp3"

        )

        filename = temp.name

        temp.close()

        loop = asyncio.new_event_loop()

        asyncio.set_event_loop(loop)

        try:

            loop.run_until_complete(

                self._generate(

                    text,

                    filename

                )

            )

        finally:

            loop.close()

        try:

            pygame.mixer.music.load(

                filename

            )

            pygame.mixer.music.play()

            while pygame.mixer.music.get_busy():

                if self.stop_event.is_set():

                    pygame.mixer.music.stop()

                    break

                pygame.time.wait(50)

        finally:

            try:

                pygame.mixer.music.stop()

            except Exception:

                pass

            try:

                pygame.mixer.music.unload()

            except Exception:

                pass

            if os.path.exists(filename):

                os.remove(filename)

            self.is_speaking = False

    # --------------------------------------------------
    # Speak
    # --------------------------------------------------

    def speak(self, text):

        if not text:

            return

        text = str(text).strip()

        if not text:

            return

        with self.lock:

            self.stop()

            if (

                self.current_thread

                and

                self.current_thread.is_alive()

            ):

                self.current_thread.join(timeout=2)

            self.current_thread = threading.Thread(

                target=self._worker,

                args=(text,),

                daemon=True

            )

            self.current_thread.start()

    # --------------------------------------------------
    # Stop
    # --------------------------------------------------

    def stop(self):

        self.stop_event.set()

        try:

            pygame.mixer.music.stop()

        except Exception:

            pass

        if (

            self.current_thread

            and

            self.current_thread.is_alive()

        ):

            self.current_thread.join(timeout=2)

        self.current_thread = None

        self.is_speaking = False

    # --------------------------------------------------
    # Voice
    # --------------------------------------------------

    def set_voice(self, voice):

        self.voice = voice

    # --------------------------------------------------
    # Status
    # --------------------------------------------------

    def speaking(self):

        return self.is_speaking

    # --------------------------------------------------
    # Cleanup
    # --------------------------------------------------

    def close(self):

        self.stop()

        try:

            pygame.mixer.quit()

        except Exception:

            pass