"""
voice/edge_tts_engine.py

ASTRA-AI
Premium Microsoft Edge Neural TTS Engine

Features
--------
✓ Microsoft Edge Neural Voice
✓ Faster Response
✓ Non-blocking
✓ Thread Safe
✓ Stop Current Speech
✓ Queue Safe
✓ Auto Cleanup
✓ Explicit success/failure reporting
"""

from __future__ import annotations

import asyncio
import os
import tempfile
import threading

import edge_tts
import pygame


class EdgeTTSEngine:

    def __init__(self):

        self.voice = "en-IN-NeerjaNeural"

        self.rate = 0
        self.volume = 100

        self.lock = threading.Lock()

        self.current_thread = None

        self.stop_event = threading.Event()

        self.is_speaking = False

        self._closed = False

        if not pygame.mixer.get_init():

            pygame.mixer.init()

    # --------------------------------------------------
    # Generate Speech
    # --------------------------------------------------

    async def _generate(
        self,
        text,
        filename
    ):
        """
        Generate Edge TTS audio.
        """

        communicate = edge_tts.Communicate(
            text=text,
            voice=self.voice,
        )

        await communicate.save(filename)

    # --------------------------------------------------
    # Internal Blocking Speech
    # --------------------------------------------------

    def speak_blocking(
        self,
        text
    ):
        """
        Generate and play Edge TTS synchronously.

        Returns
        -------
        bool
            True  -> Edge TTS succeeded.
            False -> Edge TTS failed.

        IMPORTANT
        ---------
        This method does NOT use a fallback.
        The caller decides whether to try Piper
        or another TTS provider.
        """

        if self._closed:

            return False

        if not text:

            return False

        text = str(text).strip()

        if not text:

            return False

        filename = None

        loop = None

        self.stop_event.clear()

        self.is_speaking = True

        try:

            # ------------------------------------------
            # Temporary MP3 file
            # ------------------------------------------

            temp = tempfile.NamedTemporaryFile(
                delete=False,
                suffix=".mp3",
            )

            filename = temp.name

            temp.close()

            # ------------------------------------------
            # Create event loop
            # ------------------------------------------

            loop = asyncio.new_event_loop()

            asyncio.set_event_loop(loop)

            # ------------------------------------------
            # Generate Edge speech
            # ------------------------------------------

            try:

                loop.run_until_complete(
                    self._generate(
                        text,
                        filename,
                    )
                )

            except Exception as error:

                print(
                    f"Edge TTS Generate Error : {error}"
                )

                return False

            finally:

                try:

                    loop.close()

                except Exception:

                    pass

                loop = None

            # ------------------------------------------
            # Stop requested?
            # ------------------------------------------

            if self.stop_event.is_set():

                return False

            # ------------------------------------------
            # Validate generated file
            # ------------------------------------------

            if not os.path.exists(filename):

                print(
                    "Edge TTS Error : "
                    "Generated audio file not found."
                )

                return False

            if os.path.getsize(filename) == 0:

                print(
                    "Edge TTS Error : "
                    "Generated audio file is empty."
                )

                return False

            # ------------------------------------------
            # Playback
            # ------------------------------------------

            try:

                pygame.mixer.music.load(
                    filename
                )

                pygame.mixer.music.play()

            except Exception as error:

                print(
                    f"Edge TTS Playback Error : {error}"
                )

                return False

            while (

                pygame.mixer.music.get_busy()

                and

                not self.stop_event.is_set()

            ):

                pygame.time.wait(10)

            if self.stop_event.is_set():

                return False

            return True

        except Exception as error:

            print(
                f"Edge TTS Error : {error}"
            )

            return False

        finally:

            # ------------------------------------------
            # Cleanup loop
            # ------------------------------------------

            if loop is not None:

                try:

                    loop.close()

                except Exception:

                    pass

            # ------------------------------------------
            # Stop playback
            # ------------------------------------------

            try:

                pygame.mixer.music.stop()

            except Exception:

                pass

            try:

                pygame.mixer.music.unload()

            except Exception:

                pass

            # ------------------------------------------
            # Delete temporary file
            # ------------------------------------------

            if filename:

                try:

                    if os.path.exists(filename):

                        os.remove(filename)

                except Exception:

                    pass

            self.is_speaking = False

    # --------------------------------------------------
    # Non-Blocking Speak
    # --------------------------------------------------

    def speak(
        self,
        text
    ):
        """
        Preserve the existing non-blocking API.

        Returns
        -------
        threading.Thread | None
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
                daemon=True,
            )

            self.current_thread.start()

            return self.current_thread

    # --------------------------------------------------
    # Stop
    # --------------------------------------------------

    def stop(self):

        self.stop_event.set()

        try:

            pygame.mixer.music.stop()

        except Exception:

            pass

        self.is_speaking = False

    # --------------------------------------------------
    # Voice
    # --------------------------------------------------

    def set_voice(
        self,
        voice
    ):

        if voice:

            self.voice = str(voice)

    # --------------------------------------------------
    # Rate
    # --------------------------------------------------

    def set_rate(
        self,
        rate
    ):

        try:

            self.rate = int(rate)

        except (TypeError, ValueError):

            self.rate = 0

    # --------------------------------------------------
    # Volume
    # --------------------------------------------------

    def set_volume(
        self,
        volume
    ):

        try:

            self.volume = int(volume)

        except (TypeError, ValueError):

            self.volume = 100

    # --------------------------------------------------
    # Status
    # --------------------------------------------------

    def speaking(self):

        return self.is_speaking

    # --------------------------------------------------
    # Cleanup
    # --------------------------------------------------

    def close(self):

        self._closed = True

        self.stop()

        try:

            pygame.mixer.music.stop()

        except Exception:

            pass

        # Do NOT quit pygame mixer here.
        #
        # Piper / other TTS providers may use
        # the same mixer instance.
        #
        # The central TextToSpeech manager will
        # perform final mixer cleanup.

        print(
            "Edge TTS Engine shutdown completed."
        )