"""
voice/text_to_speech.py

ASTRA-AI
Premium Multi-Provider Text To Speech Manager

Fallback order
--------------
1. Microsoft Edge Neural TTS
2. Piper Offline TTS
3. Windows SAPI / pyttsx3

IMPORTANT
---------
Only one speech request is allowed to control the
TTS pipeline at a time.

When a new speech request starts:

    Old speech request
        ↓
    Invalidated
        ↓
    All providers stopped
        ↓
    New speech request starts

This prevents multiple TTS worker threads from
continuing into fallback providers simultaneously.
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

    Only the latest speech request is allowed to
    continue through the provider fallback chain.
    """

    # ======================================================
    # INITIALIZATION
    # ======================================================

    def __init__(self):

        # --------------------------------------------------
        # PROVIDER ENGINES
        # --------------------------------------------------

        self.edge_engine = EdgeTTSEngine()

        self.piper_engine = None

        self.pyttsx3_engine = None

        self._load_fallback_engines()

        # --------------------------------------------------
        # COMPATIBILITY
        #
        # Existing ASTRA code may access self.engine.
        #
        # Keep Edge as the primary engine reference.
        # --------------------------------------------------

        self.engine = self.edge_engine

        # --------------------------------------------------
        # STATE
        # --------------------------------------------------

        self.enabled = True

        self._closing = False

        self.lock = threading.RLock()

        self.current_thread = None

        self._speaking = False

        self._stop_event = threading.Event()

        # --------------------------------------------------
        # REQUEST ID
        #
        # Every speech request gets a unique ID.
        #
        # When a new request starts:
        #
        # request_id increases
        #
        # Older workers become invalid and are not
        # allowed to continue into fallback providers.
        # --------------------------------------------------

        self._request_id = 0

    # ======================================================
    # LOAD FALLBACK ENGINES
    # ======================================================

    def _load_fallback_engines(
        self,
    ):
        """
        Load Piper and pyttsx3 safely.

        If either module is temporarily unavailable,
        ASTRA continues running with the providers that
        are available.
        """

        # --------------------------------------------------
        # PIPER
        # --------------------------------------------------

        try:

            from voice.piper_tts_engine import (
                PiperTTSEngine
            )

            self.piper_engine = (
                PiperTTSEngine()
            )

            print(
                "Piper TTS Engine Ready."
            )

        except Exception as error:

            self.piper_engine = None

            print(
                f"Piper TTS Engine Unavailable : "
                f"{error}"
            )

        # --------------------------------------------------
        # PYTTSX3
        # --------------------------------------------------

        try:

            from voice.pyttsx3_tts_engine import (
                Pyttsx3TTSEngine
            )

            self.pyttsx3_engine = (
                Pyttsx3TTSEngine()
            )

            print(
                "pyttsx3 TTS Engine Ready."
            )

        except Exception as error:

            self.pyttsx3_engine = None

            print(
                f"pyttsx3 TTS Engine Unavailable : "
                f"{error}"
            )

    # ======================================================
    # REQUEST STATUS
    # ======================================================

    def _is_request_active(
        self,
        request_id: int,
    ) -> bool:
        """
        Return True only when this worker still owns
        the active speech request.
        """

        if self._closing:

            return False

        if self._stop_event.is_set():

            return False

        with self.lock:

            return (
                request_id
                == self._request_id
            )

    # ======================================================
    # STOP ALL PROVIDERS
    # ======================================================

    def _stop_all_providers(
        self,
    ):
        """
        Stop audio from every available provider.

        This method does not modify request IDs.
        """

        # --------------------------------------------------
        # EDGE
        # --------------------------------------------------

        try:

            if self.edge_engine is not None:

                self.edge_engine.stop()

        except Exception:

            pass

        # --------------------------------------------------
        # PIPER
        # --------------------------------------------------

        try:

            if self.piper_engine is not None:

                self.piper_engine.stop()

        except Exception:

            pass

        # --------------------------------------------------
        # PYTTSX3
        # --------------------------------------------------

        try:

            if self.pyttsx3_engine is not None:

                self.pyttsx3_engine.stop()

        except Exception:

            pass

    # ======================================================
    # SPEAK
    # ======================================================

    def speak(
        self,
        text: str,
    ):
        """
        Speak text using the fallback chain.

        This method is non-blocking.

        Only the latest speech request is allowed
        to continue.

        Provider order:

            Edge
            Piper
            pyttsx3
        """

        if self._closing:

            return None

        if not self.enabled:

            return None

        if text is None:

            return None

        text = str(
            text
        ).strip()

        if not text:

            return None

        with self.lock:

            # ----------------------------------------------
            # INVALIDATE PREVIOUS WORKER
            #
            # Increasing request ID ensures any previous
            # worker becomes invalid.
            # ----------------------------------------------

            self._request_id += 1

            request_id = self._request_id

            # ----------------------------------------------
            # STOP PREVIOUS AUDIO
            # ----------------------------------------------

            self._stop_event.set()

            self._stop_all_providers()

            # ----------------------------------------------
            # PREPARE NEW REQUEST
            # ----------------------------------------------

            self._stop_event.clear()

            self._speaking = True

            # ----------------------------------------------
            # START NEW WORKER
            # ----------------------------------------------

            self.current_thread = threading.Thread(

                target=self._speak_worker,

                args=(
                    request_id,
                    text,
                ),

                daemon=True,

                name=(
                    f"ASTRA-TTS-"
                    f"{request_id}"
                ),
            )

            self.current_thread.start()

            return self.current_thread

    # ======================================================
    # SPEECH WORKER
    # ======================================================

    def _speak_worker(
        self,
        request_id: int,
        text: str,
    ):
        """
        Execute providers sequentially.

        A provider must return True only when it
        successfully completes speech.

        Before moving to another provider, the worker
        verifies that it still owns the active request.

        An older cancelled worker can never continue
        into Piper or pyttsx3.
        """

        try:

            # ==================================================
            # PROVIDER 1
            # EDGE TTS
            # ==================================================

            if not self._is_request_active(
                request_id
            ):

                return

            if self.edge_engine is not None:

                print(
                    "\nTTS Provider : Edge TTS"
                )

                try:

                    success = (
                        self.edge_engine.speak_blocking(
                            text
                        )
                    )

                    # ------------------------------------------
                    # IMPORTANT
                    #
                    # Before checking success or moving into
                    # fallback, verify that this worker is still
                    # the current request.
                    # ------------------------------------------

                    if not self._is_request_active(
                        request_id
                    ):

                        return

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

                    if self._is_request_active(
                        request_id
                    ):

                        print(
                            f"Edge TTS Error : "
                            f"{error}"
                        )

            # ==================================================
            # PROVIDER 2
            # PIPER TTS
            # ==================================================

            if not self._is_request_active(
                request_id
            ):

                return

            if self.piper_engine is not None:

                print(
                    "TTS Provider : Piper TTS"
                )

                try:

                    success = (
                        self.piper_engine.speak_blocking(
                            text
                        )
                    )

                    # ------------------------------------------
                    # Verify worker ownership before fallback.
                    # ------------------------------------------

                    if not self._is_request_active(
                        request_id
                    ):

                        return

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

                    if self._is_request_active(
                        request_id
                    ):

                        print(
                            f"Piper TTS Error : "
                            f"{error}"
                        )

            # ==================================================
            # PROVIDER 3
            # PYTTSX3
            # ==================================================

            if not self._is_request_active(
                request_id
            ):

                return

            if self.pyttsx3_engine is not None:

                print(
                    "TTS Provider : Windows pyttsx3"
                )

                try:

                    success = (
                        self.pyttsx3_engine.speak_blocking(
                            text
                        )
                    )

                    # ------------------------------------------
                    # Verify worker ownership.
                    # ------------------------------------------

                    if not self._is_request_active(
                        request_id
                    ):

                        return

                    if success:

                        print(
                            "TTS Success : "
                            "Windows pyttsx3"
                        )

                        return

                    print(
                        "Windows pyttsx3 TTS failed."
                    )

                except Exception as error:

                    if self._is_request_active(
                        request_id
                    ):

                        print(
                            f"pyttsx3 TTS Error : "
                            f"{error}"
                        )

            # ==================================================
            # ALL PROVIDERS FAILED
            # ==================================================

            if self._is_request_active(
                request_id
            ):

                print(
                    "\nTTS Error : "
                    "All TTS providers failed."
                )

        finally:

            # --------------------------------------------------
            # ONLY CURRENT WORKER MAY CHANGE GLOBAL STATE
            #
            # Example:
            #
            # Request 1 starts
            # Request 2 starts
            # Request 1 finishes later
            #
            # Request 1 must NOT set _speaking=False because
            # Request 2 may still be speaking.
            # --------------------------------------------------

            with self.lock:

                if (
                    request_id
                    == self._request_id
                ):

                    self._speaking = False

    # ======================================================
    # STOP
    # ======================================================

    def stop(
        self,
    ):
        """
        Stop speech from all providers.

        The current worker is invalidated so it cannot
        continue into fallback providers after stop().
        """

        with self.lock:

            # --------------------------------------------------
            # INVALIDATE CURRENT WORKER
            # --------------------------------------------------

            self._request_id += 1

            # --------------------------------------------------
            # SIGNAL STOP
            # --------------------------------------------------

            self._stop_event.set()

            # --------------------------------------------------
            # STOP ALL PROVIDERS
            # --------------------------------------------------

            self._stop_all_providers()

            self._speaking = False

    # ======================================================
    # ENABLE / DISABLE
    # ======================================================

    def set_enabled(
        self,
        enabled=True,
    ):

        self.enabled = bool(
            enabled
        )

        if not self.enabled:

            self.stop()

    # ======================================================
    # SPEAKING STATUS
    # ======================================================

    def speaking(
        self,
    ):

        with self.lock:

            if self._speaking:

                return True

        # --------------------------------------------------
        # PROVIDER-LEVEL STATUS CHECK
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

                    and hasattr(
                        engine,
                        "speaking",
                    )

                    and engine.speaking()

                ):

                    return True

            except Exception:

                continue

        return False

    # ======================================================
    # WAIT UNTIL SPEECH FINISHES
    # ======================================================

    def wait_until_done(
        self,
    ):

        while self.speaking():

            if self._closing:

                break

            time.sleep(
                0.02
            )

    # ======================================================
    # VOICE
    # ======================================================

    def set_voice(
        self,
        voice,
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

                    and hasattr(
                        engine,
                        "set_voice",
                    )

                ):

                    engine.set_voice(
                        voice
                    )

            except Exception:

                continue

    # ======================================================
    # RATE
    # ======================================================

    def set_rate(
        self,
        rate,
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

                    and hasattr(
                        engine,
                        "set_rate",
                    )

                ):

                    engine.set_rate(
                        rate
                    )

            except Exception:

                continue

    # ======================================================
    # VOLUME
    # ======================================================

    def set_volume(
        self,
        volume,
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

                    and hasattr(
                        engine,
                        "set_volume",
                    )

                ):

                    engine.set_volume(
                        volume
                    )

            except Exception:

                continue

    # ======================================================
    # CLEANUP
    # ======================================================

    def close(
        self,
    ):

        if self._closing:

            return

        self._closing = True

        # --------------------------------------------------
        # INVALIDATE ALL ACTIVE WORKERS
        # --------------------------------------------------

        with self.lock:

            self._request_id += 1

            self._stop_event.set()

            self._speaking = False

        # --------------------------------------------------
        # STOP CURRENT SPEECH
        # --------------------------------------------------

        self._stop_all_providers()

        # --------------------------------------------------
        # WAIT BRIEFLY FOR CURRENT WORKER
        #
        # Do not block application shutdown indefinitely.
        # --------------------------------------------------

        worker = self.current_thread

        if (

            worker is not None

            and worker.is_alive()

            and worker is not threading.current_thread()

        ):

            try:

                worker.join(
                    timeout=1.0
                )

            except Exception:

                pass

        # --------------------------------------------------
        # CLOSE EDGE
        # --------------------------------------------------

        try:

            if self.edge_engine is not None:

                self.edge_engine.close()

        except Exception:

            pass

        # --------------------------------------------------
        # CLOSE PIPER
        # --------------------------------------------------

        try:

            if self.piper_engine is not None:

                self.piper_engine.close()

        except Exception:

            pass

        # --------------------------------------------------
        # CLOSE PYTTSX3
        # --------------------------------------------------

        try:

            if self.pyttsx3_engine is not None:

                self.pyttsx3_engine.close()

        except Exception:

            pass

        # --------------------------------------------------
        # CLEAR REFERENCES
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