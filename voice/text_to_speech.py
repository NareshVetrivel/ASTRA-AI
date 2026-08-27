"""
voice/text_to_speech.py

ASTRA-AI
Premium Multi-Provider Text To Speech Manager

Fallback order
--------------
1. Microsoft Edge Neural TTS
2. Piper Offline TTS
3. Windows SAPI / pyttsx3

Avatar integration
------------------
speech_started(text)
    -> Avatar should switch to "speaking"

speech_finished(success)
    -> Avatar controller can continue with
       success / error / idle flow.

Only one speech request is allowed to control the
TTS pipeline at a time.
"""

from __future__ import annotations

import threading
import time

from PySide6.QtCore import QObject, Signal

from voice.edge_tts_engine import EdgeTTSEngine


class TextToSpeech(QObject):
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

    Signals are emitted from the TTS manager so the UI can
    safely switch the avatar state through Qt's queued signal
    delivery.

    Only the latest speech request is allowed to continue.
    """

    # ======================================================
    # QT SIGNALS
    # ======================================================

    speech_started = Signal(str)
    speech_finished = Signal(bool)

    # ======================================================
    # INITIALIZATION
    # ======================================================

    def __init__(self, parent=None):

        super().__init__(parent)

        # --------------------------------------------------
        # PROVIDER ENGINES
        # --------------------------------------------------

        self.edge_engine = EdgeTTSEngine()

        self.piper_engine = None
        self.pyttsx3_engine = None

        self._load_fallback_engines()

        # --------------------------------------------------
        # COMPATIBILITY
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
        # --------------------------------------------------

        self._request_id = 0

    # ======================================================
    # LOAD FALLBACK ENGINES
    # ======================================================

    def _load_fallback_engines(self):
        """
        Load Piper and pyttsx3 safely.
        """

        try:

            from voice.piper_tts_engine import PiperTTSEngine

            self.piper_engine = PiperTTSEngine()

            print("Piper TTS Engine Ready.")

        except Exception as error:

            self.piper_engine = None

            print(
                f"Piper TTS Engine Unavailable : {error}"
            )

        try:

            from voice.pyttsx3_tts_engine import Pyttsx3TTSEngine

            self.pyttsx3_engine = Pyttsx3TTSEngine()

            print("pyttsx3 TTS Engine Ready.")

        except Exception as error:

            self.pyttsx3_engine = None

            print(
                f"pyttsx3 TTS Engine Unavailable : {error}"
            )

    # ======================================================
    # REQUEST STATUS
    # ======================================================

    def _is_request_active(
        self,
        request_id: int,
    ) -> bool:

        if self._closing:
            return False

        if self._stop_event.is_set():
            return False

        with self.lock:

            return request_id == self._request_id

    # ======================================================
    # STOP ALL PROVIDERS
    # ======================================================

    def _stop_all_providers(self):
        """
        Stop audio from every available provider.
        """

        for engine in (
            self.edge_engine,
            self.piper_engine,
            self.pyttsx3_engine,
        ):

            try:

                if engine is not None:
                    engine.stop()

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
        Start speech asynchronously.

        The speech_started signal is emitted by the worker
        before the provider begins speaking.

        The speech_finished signal is emitted only by the
        currently active request.
        """

        if self._closing:
            return None

        if not self.enabled:
            return None

        if text is None:
            return None

        text = str(text).strip()

        if not text:
            return None

        with self.lock:

            # Invalidate previous worker.

            self._request_id += 1

            request_id = self._request_id

            # Stop previous audio.

            self._stop_event.set()

            self._stop_all_providers()

            # Prepare new request.

            self._stop_event.clear()

            self._speaking = True

            self.current_thread = threading.Thread(

                target=self._speak_worker,

                args=(
                    request_id,
                    text,
                ),

                daemon=True,

                name=f"ASTRA-TTS-{request_id}",
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

        IMPORTANT:
        Avatar SPEAKING starts when this request actually
        enters the active speech pipeline.

        Avatar completion is emitted only after the current
        request finishes successfully or all providers fail.
        """

        completed_successfully = False

        started_emitted = False

        try:

            if not self._is_request_active(request_id):
                return

            # --------------------------------------------------
            # SPEAKING START
            # --------------------------------------------------

            self.speech_started.emit(text)

            started_emitted = True

            print("[TTS] Speech started.")

            # ==================================================
            # PROVIDER 1 — EDGE
            # ==================================================

            if self.edge_engine is not None:

                print("\nTTS Provider : Edge TTS")

                try:

                    success = self.edge_engine.speak_blocking(text)

                    if not self._is_request_active(request_id):
                        return

                    if success:

                        completed_successfully = True

                        print("TTS Success : Edge TTS")

                        return

                    print(
                        "Edge TTS failed. "
                        "Trying Piper TTS..."
                    )

                except Exception as error:

                    if self._is_request_active(request_id):

                        print(
                            f"Edge TTS Error : {error}"
                        )

            # ==================================================
            # PROVIDER 2 — PIPER
            # ==================================================

            if not self._is_request_active(request_id):
                return

            if self.piper_engine is not None:

                print("TTS Provider : Piper TTS")

                try:

                    success = self.piper_engine.speak_blocking(text)

                    if not self._is_request_active(request_id):
                        return

                    if success:

                        completed_successfully = True

                        print("TTS Success : Piper TTS")

                        return

                    print(
                        "Piper TTS failed. "
                        "Trying Windows pyttsx3..."
                    )

                except Exception as error:

                    if self._is_request_active(request_id):

                        print(
                            f"Piper TTS Error : {error}"
                        )

            # ==================================================
            # PROVIDER 3 — PYTTSX3
            # ==================================================

            if not self._is_request_active(request_id):
                return

            if self.pyttsx3_engine is not None:

                print("TTS Provider : Windows pyttsx3")

                try:

                    success = (
                        self.pyttsx3_engine.speak_blocking(
                            text
                        )
                    )

                    if not self._is_request_active(request_id):
                        return

                    if success:

                        completed_successfully = True

                        print(
                            "TTS Success : Windows pyttsx3"
                        )

                        return

                    print(
                        "Windows pyttsx3 TTS failed."
                    )

                except Exception as error:

                    if self._is_request_active(request_id):

                        print(
                            f"pyttsx3 TTS Error : {error}"
                        )

            # ==================================================
            # ALL PROVIDERS FAILED
            # ==================================================

            if self._is_request_active(request_id):

                print(
                    "\nTTS Error : "
                    "All TTS providers failed."
                )

        finally:

            should_emit_finished = False

            with self.lock:

                # Only the current request may change global
                # speech state or notify the UI.

                if request_id == self._request_id:

                    self._speaking = False

                    should_emit_finished = (
                        started_emitted
                        and
                        not self._closing
                    )

            if should_emit_finished:

                self.speech_finished.emit(
                    completed_successfully
                )

                print(
                    "[TTS] Speech finished. "
                    f"Success : {completed_successfully}"
                )

    # ======================================================
    # STOP
    # ======================================================

    def stop(self):
        """
        Stop speech and invalidate the active worker.

        A cancelled request must not emit speech_finished,
        otherwise a stale worker could force the avatar into
        success/error/idle during a newer operation.
        """

        with self.lock:

            self._request_id += 1

            self._stop_event.set()

            self._stop_all_providers()

            self._speaking = False

    # ======================================================
    # ENABLE / DISABLE
    # ======================================================

    def set_enabled(
        self,
        enabled=True,
    ):

        self.enabled = bool(enabled)

        if not self.enabled:
            self.stop()

    # ======================================================
    # SPEAKING STATUS
    # ======================================================

    def speaking(self):

        with self.lock:

            if self._speaking:
                return True

        providers = (
            self.edge_engine,
            self.piper_engine,
            self.pyttsx3_engine,
        )

        for engine in providers:

            try:

                if (
                    engine is not None
                    and hasattr(engine, "speaking")
                    and engine.speaking()
                ):

                    return True

            except Exception:

                continue

        return False

    # ======================================================
    # WAIT UNTIL SPEECH FINISHES
    # ======================================================

    def wait_until_done(self):

        while self.speaking():

            if self._closing:
                break

            time.sleep(0.02)

    # ======================================================
    # VOICE
    # ======================================================

    def set_voice(
        self,
        voice,
    ):

        for engine in (
            self.edge_engine,
            self.piper_engine,
            self.pyttsx3_engine,
        ):

            try:

                if (
                    engine is not None
                    and hasattr(engine, "set_voice")
                ):

                    engine.set_voice(voice)

            except Exception:

                continue

    # ======================================================
    # RATE
    # ======================================================

    def set_rate(
        self,
        rate,
    ):

        for engine in (
            self.edge_engine,
            self.piper_engine,
            self.pyttsx3_engine,
        ):

            try:

                if (
                    engine is not None
                    and hasattr(engine, "set_rate")
                ):

                    engine.set_rate(rate)

            except Exception:

                continue

    # ======================================================
    # VOLUME
    # ======================================================

    def set_volume(
        self,
        volume,
    ):

        for engine in (
            self.edge_engine,
            self.piper_engine,
            self.pyttsx3_engine,
        ):

            try:

                if (
                    engine is not None
                    and hasattr(engine, "set_volume")
                ):

                    engine.set_volume(volume)

            except Exception:

                continue

    # ======================================================
    # CLEANUP
    # ======================================================

    def close(self):

        if self._closing:
            return

        self._closing = True

        with self.lock:

            self._request_id += 1

            self._stop_event.set()

            self._speaking = False

        self._stop_all_providers()

        worker = self.current_thread

        if (
            worker is not None
            and worker.is_alive()
            and worker is not threading.current_thread()
        ):

            try:

                worker.join(timeout=1.0)

            except Exception:

                pass

        for engine in (
            self.edge_engine,
            self.piper_engine,
            self.pyttsx3_engine,
        ):

            try:

                if engine is not None:
                    engine.close()

            except Exception:

                pass

        self.edge_engine = None
        self.piper_engine = None
        self.pyttsx3_engine = None
        self.engine = None
        self.current_thread = None
        self._speaking = False

        print(
            "TextToSpeech shutdown completed."
        )
