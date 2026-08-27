"""
voice/edge_tts_engine.py

ASTRA-AI
Premium Microsoft Edge Neural TTS Engine

Features
--------
✓ Microsoft Edge Neural Voice
✓ Faster Response
✓ Blocking + Non-blocking API
✓ Thread Safe
✓ Stop Current Speech
✓ Request Generation Protection
✓ Queue Safe
✓ Auto Cleanup
✓ Explicit Success / Failure Reporting
✓ Rate Support
✓ Volume Support

IMPORTANT
---------
Each speech request receives a generation ID.

When stop() or a new speak() request occurs:

    Old generation
        ↓
    Invalidated
        ↓
    Playback stopped
        ↓
    Old worker cannot continue successfully

This prevents an older worker from incorrectly
continuing after a newer request has started.
"""

from __future__ import annotations

import asyncio
import os
import tempfile
import threading

import edge_tts
import pygame


# ============================================================
# EDGE TTS ENGINE
# ============================================================

class EdgeTTSEngine:

    # ========================================================
    # INITIALIZATION
    # ========================================================

    def __init__(self):

        # ----------------------------------------------------
        # VOICE SETTINGS
        # ----------------------------------------------------

        self.voice = "en-IN-NeerjaNeural"

        self.rate = 0

        self.volume = 100

        # ----------------------------------------------------
        # THREAD SAFETY
        # ----------------------------------------------------

        self.lock = threading.RLock()

        # ----------------------------------------------------
        # CURRENT NON-BLOCKING THREAD
        # ----------------------------------------------------

        self.current_thread = None

        # ----------------------------------------------------
        # STATE
        # ----------------------------------------------------

        self.is_speaking = False

        self._closed = False

        # ----------------------------------------------------
        # REQUEST GENERATION
        #
        # Every request receives a unique generation number.
        #
        # stop() invalidates the active generation.
        #
        # This prevents old workers from becoming active again
        # after a new request clears a shared event.
        # ----------------------------------------------------

        self._generation = 0

        # ----------------------------------------------------
        # CURRENT PLAYBACK FILE
        # ----------------------------------------------------

        self._current_filename = None

        # ----------------------------------------------------
        # INITIALIZE PYGAME MIXER
        # ----------------------------------------------------

        try:

            if not pygame.mixer.get_init():

                pygame.mixer.init()

        except Exception as error:

            print(
                f"Edge TTS Mixer Init Error : {error}"
            )

    # ========================================================
    # REQUEST GENERATION
    # ========================================================

    def _next_generation(self):
        """
        Create and return a new active generation ID.
        """

        with self.lock:

            self._generation += 1

            return self._generation

    def _is_generation_active(
        self,
        generation: int,
    ):
        """
        Return True only if this worker still owns
        the currently active Edge TTS request.
        """

        if self._closed:

            return False

        with self.lock:

            return (
                generation
                == self._generation
            )

    # ========================================================
    # FORMAT RATE
    # ========================================================

    def _get_edge_rate(self):
        """
        Convert integer rate into Edge TTS rate format.

        Examples:

            0    -> +0%
            20   -> +20%
            -20  -> -20%
        """

        try:

            rate = int(
                self.rate
            )

        except (
            TypeError,
            ValueError,
        ):

            rate = 0

        # Keep the value within a reasonable range.

        rate = max(
            -100,
            min(
                100,
                rate,
            ),
        )

        if rate >= 0:

            return f"+{rate}%"

        return f"{rate}%"

    # ========================================================
    # FORMAT VOLUME
    # ========================================================

    def _get_edge_volume(self):
        """
        Convert integer volume into Edge TTS volume format.

        Examples:

            100 -> +0%
            80  -> -20%
            120 -> +20%
        """

        try:

            volume = int(
                self.volume
            )

        except (
            TypeError,
            ValueError,
        ):

            volume = 100

        volume = max(
            0,
            min(
                200,
                volume,
            ),
        )

        edge_volume = (
            volume
            - 100
        )

        if edge_volume >= 0:

            return (
                f"+{edge_volume}%"
            )

        return (
            f"{edge_volume}%"
        )

    # ========================================================
    # GENERATE SPEECH
    # ========================================================

    async def _generate(
        self,
        text,
        filename,
    ):
        """
        Generate Edge TTS audio.
        """

        communicate = edge_tts.Communicate(

            text=text,

            voice=self.voice,

            rate=self._get_edge_rate(),

            volume=self._get_edge_volume(),

        )

        await communicate.save(
            filename
        )

    # ========================================================
    # INTERNAL BLOCKING SPEECH
    # ========================================================

    def speak_blocking(
        self,
        text,
    ):
        """
        Generate and play Edge TTS synchronously.

        Returns
        -------
        bool

            True
                Edge TTS completed successfully.

            False
                Edge TTS failed or was cancelled.

        IMPORTANT
        ---------
        This method does NOT perform fallback.

        TextToSpeech decides whether Piper or pyttsx3
        should be used after Edge failure.
        """

        if self._closed:

            return False

        if text is None:

            return False

        text = str(
            text
        ).strip()

        if not text:

            return False

        # ----------------------------------------------------
        # CREATE REQUEST GENERATION
        # ----------------------------------------------------

        generation = (
            self._next_generation()
        )

        filename = None

        loop = None

        playback_started = False

        try:

            # ------------------------------------------------
            # REQUEST STILL ACTIVE?
            # ------------------------------------------------

            if not self._is_generation_active(
                generation
            ):

                return False

            # ------------------------------------------------
            # MARK SPEAKING
            # ------------------------------------------------

            with self.lock:

                if not self._is_generation_active(
                    generation
                ):

                    return False

                self.is_speaking = True

            # ------------------------------------------------
            # CREATE TEMPORARY MP3 FILE
            # ------------------------------------------------

            temp = tempfile.NamedTemporaryFile(

                delete=False,

                suffix=".mp3",

            )

            filename = temp.name

            temp.close()

            with self.lock:

                if self._is_generation_active(
                    generation
                ):

                    self._current_filename = (
                        filename
                    )

            # ------------------------------------------------
            # CREATE EVENT LOOP
            # ------------------------------------------------

            loop = asyncio.new_event_loop()

            # ------------------------------------------------
            # GENERATE EDGE SPEECH
            # ------------------------------------------------

            try:

                loop.run_until_complete(

                    self._generate(

                        text,

                        filename,

                    )

                )

            except Exception as error:

                print(

                    f"Edge TTS Generate Error : "
                    f"{error}"

                )

                return False

            finally:

                try:

                    loop.close()

                except Exception:

                    pass

                loop = None

            # ------------------------------------------------
            # REQUEST CANCELLED WHILE GENERATING?
            # ------------------------------------------------

            if not self._is_generation_active(
                generation
            ):

                return False

            # ------------------------------------------------
            # VALIDATE GENERATED FILE
            # ------------------------------------------------

            if not os.path.exists(
                filename
            ):

                print(

                    "Edge TTS Error : "
                    "Generated audio file not found."

                )

                return False

            if os.path.getsize(
                filename
            ) == 0:

                print(

                    "Edge TTS Error : "
                    "Generated audio file is empty."

                )

                return False

            # ------------------------------------------------
            # REQUEST STILL ACTIVE BEFORE PLAYBACK?
            # ------------------------------------------------

            if not self._is_generation_active(
                generation
            ):

                return False

            # ------------------------------------------------
            # PLAYBACK
            # ------------------------------------------------

            try:

                pygame.mixer.music.load(
                    filename
                )

                # --------------------------------------------
                # Re-check ownership immediately before play.
                # --------------------------------------------

                if not self._is_generation_active(
                    generation
                ):

                    try:

                        pygame.mixer.music.stop()

                    except Exception:

                        pass

                    return False

                pygame.mixer.music.play()

                playback_started = True

            except Exception as error:

                print(

                    f"Edge TTS Playback Error : "
                    f"{error}"

                )

                return False

            # ------------------------------------------------
            # WAIT FOR PLAYBACK
            # ------------------------------------------------

            while True:

                # --------------------------------------------
                # OLD REQUEST?
                # --------------------------------------------

                if not self._is_generation_active(
                    generation
                ):

                    return False

                # --------------------------------------------
                # PLAYBACK FINISHED?
                # --------------------------------------------

                try:

                    if not pygame.mixer.music.get_busy():

                        break

                except Exception:

                    return False

                pygame.time.wait(
                    10
                )

            # ------------------------------------------------
            # FINAL OWNERSHIP CHECK
            # ------------------------------------------------

            if not self._is_generation_active(
                generation
            ):

                return False

            return True

        except Exception as error:

            print(

                f"Edge TTS Error : "
                f"{error}"

            )

            return False

        finally:

            # ------------------------------------------------
            # CLEANUP EVENT LOOP
            # ------------------------------------------------

            if loop is not None:

                try:

                    loop.close()

                except Exception:

                    pass

            # ------------------------------------------------
            # ONLY ACTIVE GENERATION MAY STOP/UNLOAD AUDIO
            #
            # This is important because an old worker must
            # never stop audio belonging to a newer request.
            # ------------------------------------------------

            is_active = (
                self._is_generation_active(
                    generation
                )
            )

            if is_active:

                try:

                    if playback_started:

                        pygame.mixer.music.stop()

                except Exception:

                    pass

                try:

                    pygame.mixer.music.unload()

                except Exception:

                    pass

            # ------------------------------------------------
            # DELETE TEMP FILE
            # ------------------------------------------------

            if filename:

                try:

                    if os.path.exists(
                        filename
                    ):

                        os.remove(
                            filename
                        )

                except Exception:

                    pass

            # ------------------------------------------------
            # CLEAR STATE ONLY IF THIS IS STILL THE ACTIVE
            # REQUEST.
            # ------------------------------------------------

            with self.lock:

                if (
                    generation
                    == self._generation
                ):

                    if (
                        self._current_filename
                        == filename
                    ):

                        self._current_filename = None

                    self.is_speaking = False

    # ========================================================
    # NON-BLOCKING SPEAK
    # ========================================================

    def speak(
        self,
        text,
    ):
        """
        Non-blocking speech API.

        Returns
        -------
        threading.Thread | None
        """

        if self._closed:

            return None

        if text is None:

            return None

        text = str(
            text
        ).strip()

        if not text:

            return None

        # ----------------------------------------------------
        # STOP PREVIOUS REQUEST
        # ----------------------------------------------------

        self.stop()

        # ----------------------------------------------------
        # START NEW THREAD
        #
        # speak_blocking() creates its own generation.
        # ----------------------------------------------------

        worker = threading.Thread(

            target=self.speak_blocking,

            args=(
                text,
            ),

            daemon=True,

            name="ASTRA-Edge-TTS",

        )

        with self.lock:

            self.current_thread = worker

        worker.start()

        return worker

    # ========================================================
    # STOP
    # ========================================================

    def stop(
        self,
    ):
        """
        Stop the current Edge TTS request.

        The active generation is invalidated before
        playback is stopped.

        Therefore an old worker cannot continue and
        report a successful completion later.
        """

        with self.lock:

            # ------------------------------------------------
            # INVALIDATE ACTIVE REQUEST
            # ------------------------------------------------

            self._generation += 1

            self.is_speaking = False

            self._current_filename = None

        # ----------------------------------------------------
        # STOP PYGAME PLAYBACK
        # ----------------------------------------------------

        try:

            if pygame.mixer.get_init():

                pygame.mixer.music.stop()

        except Exception:

            pass

        # ----------------------------------------------------
        # UNLOAD CURRENT MUSIC
        # ----------------------------------------------------

        try:

            if pygame.mixer.get_init():

                pygame.mixer.music.unload()

        except Exception:

            pass

    # ========================================================
    # VOICE
    # ========================================================

    def set_voice(
        self,
        voice,
    ):
        """
        Set Microsoft Edge Neural voice.

        Example:

            en-IN-NeerjaNeural
            en-IN-PrabhatNeural
        """

        if voice:

            self.voice = str(
                voice
            ).strip()

    # ========================================================
    # RATE
    # ========================================================

    def set_rate(
        self,
        rate,
    ):
        """
        Set Edge speech rate.

        Recommended range:

            -100 to 100
        """

        try:

            self.rate = int(
                rate
            )

        except (
            TypeError,
            ValueError,
        ):

            self.rate = 0

    # ========================================================
    # VOLUME
    # ========================================================

    def set_volume(
        self,
        volume,
    ):
        """
        Set Edge speech volume.

        100 = normal volume.

        Range:

            0 to 200
        """

        try:

            self.volume = int(
                volume
            )

        except (
            TypeError,
            ValueError,
        ):

            self.volume = 100

    # ========================================================
    # STATUS
    # ========================================================

    def speaking(
        self,
    ):
        """
        Return True when Edge TTS is currently active.
        """

        with self.lock:

            if self.is_speaking:

                return True

        try:

            if (

                pygame.mixer.get_init()

                and

                pygame.mixer.music.get_busy()

            ):

                return True

        except Exception:

            pass

        return False

    # ========================================================
    # CLEANUP
    # ========================================================

    def close(
        self,
    ):
        """
        Shutdown Edge TTS engine.

        pygame mixer is intentionally NOT quit here
        because other ASTRA TTS providers may share it.
        """

        if self._closed:

            return

        self._closed = True

        self.stop()

        worker = self.current_thread

        if (

            worker is not None

            and worker.is_alive()

            and worker
            is not threading.current_thread()

        ):

            try:

                worker.join(
                    timeout=1.0
                )

            except Exception:

                pass

        with self.lock:

            self.current_thread = None

            self._current_filename = None

            self.is_speaking = False

        print(
            "Edge TTS Engine shutdown completed."
        )