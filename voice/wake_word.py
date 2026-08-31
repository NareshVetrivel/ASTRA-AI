"""
ASTRA-AI
========

Local Wake Word Detection
-------------------------

Wake word:
    DHEEPTHI

Engine:
    Faster-Whisper

Responsibilities:
    - Continuously listen to microphone locally.
    - Run Faster-Whisper locally for wake-word detection.
    - Detect DHEEPTHI.
    - Provide live microphone audio level for the UI waveform.
    - Trigger the detection callback once per wake event.
    - Automatically stop the current wake session after detection.
    - Allow main_window.py to start a fresh command capture.

Does NOT:
    - call Groq for wake detection
    - process commands
    - control UI
    - execute commands
    - require an API key
    - require internet connection for wake detection

Runtime pipeline:

    Microphone
        ↓
    PCM16 / 16 kHz
        ↓
    Faster-Whisper
        ↓
    Wake text
        ↓
    DHEEPTHI detected
        ↓
    detection callback
        ↓
    main_window.py
        ↓
    TTS "Listening"
        ↓
    Fresh command microphone capture
        ↓
    Groq Whisper STT
        ↓
    Existing command-processing pipeline
"""

from __future__ import annotations

import os
import threading
import time
from pathlib import Path
from typing import Callable, Optional

import numpy as np
import sounddevice as sd

try:
    from faster_whisper import WhisperModel
except ImportError:
    WhisperModel = None


class WakeWordDetector:
    """
    Local DHEEPTHI wake-word detector using Faster-Whisper.

    Public lifecycle remains compatible with the existing
    main_window.py usage:

        start()
        stop()
        rearm()
        listen_for_wake_word()
        is_running()
        is_model_loaded()
        get_audio_level()
        set_detection_callback()
        set_level_callback()
        close()

    Important:

        Faster-Whisper = WAKE DETECTION ONLY

        Groq = COMMAND STT

    The wake audio is never passed to the command pipeline.
    After DHEEPTHI detection, main_window.py should speak
    "Listening" and then begin a fresh command recording.
    """

    # ==================================================
    # AUDIO CONFIGURATION
    # ==================================================

    SAMPLE_RATE = 16000
    CHANNELS = 1

    # Faster-Whisper works better when given a small
    # rolling microphone window.
    BLOCK_SIZE = 3200

    WAKE_WINDOW_SECONDS = 3.0

    # ==================================================
    # AUDIO LEVEL
    # ==================================================

    AUDIO_LEVEL_GAIN = 28.0

    AUDIO_LEVEL_ATTACK = 0.35

    AUDIO_LEVEL_RELEASE = 0.12

    AUDIO_PEAK_MIX = 0.25

    AUDIO_NOISE_FLOOR = 0.008

    # ==================================================
    # WAKE WORD
    # ==================================================

    WAKE_WORD = "dheepthi"

    # ==================================================
    # FASTER-WHISPER CONFIGURATION
    # ==================================================

    DEFAULT_MODEL = os.getenv(
        "ASTRA_WAKE_MODEL",
        "small",
    ).strip()

    WHISPER_DEVICE = os.getenv(
        "ASTRA_WAKE_DEVICE",
        "cpu",
    ).strip()

    WHISPER_COMPUTE_TYPE = os.getenv(
        "ASTRA_WAKE_COMPUTE_TYPE",
        "int8",
    ).strip()

    WHISPER_LANGUAGE = os.getenv(
        "ASTRA_WAKE_LANGUAGE",
        "en",
    ).strip()

    # ==================================================
    # DETECTION
    # ==================================================

    DETECTION_COOLDOWN_SECONDS = 1.25

    # ==================================================
    # INITIALIZATION
    # ==================================================

    def __init__(
        self,
        model_directory: str | os.PathLike | None = None,
        on_detected: Optional[
            Callable[[str], None]
        ] = None,
        level_callback: Optional[
            Callable[[float], None]
        ] = None,
    ):
        """
        Initialize Faster-Whisper wake detection.

        model_directory is kept for compatibility with the
        previous WakeWordDetector constructor.

        It may point to:
            - a model directory
            - a Faster-Whisper model path
        """

        self.model_path = (
            Path(model_directory).expanduser()
            if model_directory
            else None
        )

        self.on_detected = on_detected

        self.level_callback = level_callback

        # ==================================================
        # LIFECYCLE
        # ==================================================

        self._running = False

        self._stop_requested = False

        self._closing = False

        self._detected = False

        self._thread: threading.Thread | None = None

        # ==================================================
        # DETECTION GUARD
        # ==================================================

        self._detection_latched = False

        self._detection_lock = threading.Lock()

        self._last_detection_time = 0.0

        # ==================================================
        # FASTER-WHISPER
        # ==================================================

        self.model = None

        self._model_loaded = False

        self._model_lock = threading.RLock()

        # ==================================================
        # MICROPHONE
        # ==================================================

        self._stream = None

        self._lock = threading.RLock()

        # ==================================================
        # AUDIO LEVEL
        # ==================================================

        self.audio_level = 0.0

        self.audio_peak = 0.0

        self._last_audio_level = 0.0

        # ==================================================
        # WAKE AUDIO BUFFER
        # ==================================================

        self._audio_buffer = np.zeros(
            int(
                self.SAMPLE_RATE
                * self.WAKE_WINDOW_SECONDS
            ),
            dtype=np.float32,
        )

        self._buffer_lock = threading.RLock()

        self._samples_received = 0

        # ==================================================
        # DEBUG
        # ==================================================

        self._last_wake_text = ""

        self._last_wake_log_time = 0.0

        # ==================================================
        # WAKE VARIATIONS
        # ==================================================

        self.wake_words = (
            "dheepthi",
            "deepthi",
            "deepti",
            "deepthee",
            "deepthy",
            "deeptee",
            "dhepti",
            "dhepthi",
            "dheethi",
            "dhethi",
        )

        self.wake_phrases = (
            "deep the",
            "deep thee",
            "deep tea",
            "deep thi",
            "deep tee",
            "deep ti",
            "deep th",
            "deep t",

            "dheep the",
            "dheep thee",
            "dheep tea",
            "dheep thi",
            "dheep tee",
            "dheep ti",
            "dheep th",
            "dheep t",

            "deep deep",
            "deepdeep",

            "dheep deep",
            "deep dheep",

            "beep the",
            "beep thi",
            "beep tea",

            "weep the",
            "weep thi",
            "weep tea",

            "hey dheepthi",
            "hey deepthi",
            "hey deepti",

            "hello dheepthi",
            "hello deepthi",
            "hello deepti",

            "hi dheepthi",
            "hi deepthi",
            "hi deepti",

            "okay dheepthi",
            "okay deepthi",
            "okay deepti",

            "ok dheepthi",
            "ok deepthi",
            "ok deepti",
        )

        self.reject_phrases = (
            "deep sleep",
            "sleep deeply",
            "deep thought",
            "deep thoughts",
            "deep water",
            "deep voice",
            "deep breath",
            "deep breathing",
        )

        # ==================================================
        # STARTUP LOG
        # ==================================================

        print(
            "\n========== ASTRA WAKE WORD =========="
        )

        print(
            f"Wake Word : {self.WAKE_WORD}"
        )

        print(
            "Engine : Faster-Whisper"
        )

        print(
            "Mode : LOCAL / OFFLINE"
        )

        print(
            f"Model : {self.DEFAULT_MODEL}"
        )

        print(
            f"Device : {self.WHISPER_DEVICE}"
        )

        print(
            f"Compute Type : "
            f"{self.WHISPER_COMPUTE_TYPE}"
        )

        print(
            "Groq : DISABLED FOR WAKE"
        )

        print(
            "Vosk : DISABLED"
        )

        print(
            "Live Wake Waveform : ENABLED"
        )

        print(
            "=====================================\n"
        )

    # ==================================================
    # TEXT NORMALIZATION
    # ==================================================

    @staticmethod
    def _normalize_text(
        text: str,
    ) -> str:

        if not text:
            return ""

        text = str(
            text
        ).lower().strip()

        cleaned = []

        for character in text:

            if (
                character.isalnum()
                or character.isspace()
            ):
                cleaned.append(
                    character
                )
            else:
                cleaned.append(" ")

        return " ".join(
            "".join(cleaned).split()
        )

    # ==================================================
    # LOAD FASTER-WHISPER
    # ==================================================

    def load_model(self) -> bool:
        """
        Load Faster-Whisper locally.

        This model is used ONLY for DHEEPTHI wake detection.
        """

        if self._closing:
            return False

        if WhisperModel is None:

            print(
                "\nFaster-Whisper is not installed."
            )

            print(
                "Install with:"
            )

            print(
                "python -m pip install faster-whisper"
            )

            return False

        with self._model_lock:

            if (
                self._model_loaded
                and self.model is not None
            ):
                return True

            try:

                print(
                    "\nLoading local "
                    "Faster-Whisper model..."
                )

                print(
                    f"Model : "
                    f"{self.DEFAULT_MODEL}"
                )

                print(
                    f"Device : "
                    f"{self.WHISPER_DEVICE}"
                )

                print(
                    f"Compute Type : "
                    f"{self.WHISPER_COMPUTE_TYPE}"
                )

                self.model = WhisperModel(
                    self.DEFAULT_MODEL,
                    device=self.WHISPER_DEVICE,
                    compute_type=(
                        self.WHISPER_COMPUTE_TYPE
                    ),
                )

                self._model_loaded = True

                print(
                    "Faster-Whisper model "
                    "loaded successfully."
                )

                print(
                    "DHEEPTHI wake detection ready."
                )

                return True

            except Exception as error:

                self.model = None

                self._model_loaded = False

                print(
                    "Faster-Whisper Model Error : "
                    f"{error}"
                )

                return False

    # ==================================================
    # AUDIO LEVEL
    # ==================================================

    def _update_audio_level(
        self,
        audio: np.ndarray,
    ):
        try:

            if (
                audio is None
                or audio.size == 0
            ):
                return

            samples = np.asarray(
                audio,
                dtype=np.float32,
            )

            samples /= 32768.0

            rms = float(
                np.sqrt(
                    np.mean(
                        np.square(
                            samples
                        )
                    )
                )
            )

            peak = float(
                np.max(
                    np.abs(samples)
                )
            )

            self.audio_peak = (
                self.audio_peak * 0.75
                + peak * 0.25
            )

            if (
                rms
                <= self.AUDIO_NOISE_FLOOR
            ):

                target = 0.0

            else:

                adjusted = (
                    rms
                    - self.AUDIO_NOISE_FLOOR
                )

                target = (
                    adjusted
                    * self.AUDIO_LEVEL_GAIN
                )

                peak_level = (
                    self.audio_peak
                    * self.AUDIO_LEVEL_GAIN
                    * 0.45
                )

                target = (
                    target
                    * (
                        1.0
                        - self.AUDIO_PEAK_MIX
                    )
                    + peak_level
                    * self.AUDIO_PEAK_MIX
                )

                target = min(
                    max(
                        target,
                        0.0,
                    ),
                    1.0,
                )

            current = (
                self._last_audio_level
            )

            if target > current:

                alpha = (
                    self.AUDIO_LEVEL_ATTACK
                )

            else:

                alpha = (
                    self.AUDIO_LEVEL_RELEASE
                )

            level = (
                current
                + (
                    target
                    - current
                )
                * alpha
            )

            level = min(
                max(
                    float(level),
                    0.0,
                ),
                1.0,
            )

            self._last_audio_level = level

            self.audio_level = level

            callback = (
                self.level_callback
            )

            if callback is not None:

                try:
                    callback(level)
                except Exception:
                    pass

        except Exception:
            pass

    # ==================================================
    # RESET AUDIO LEVEL
    # ==================================================

    def _reset_audio_level(self):

        self.audio_level = 0.0

        self.audio_peak = 0.0

        self._last_audio_level = 0.0

        callback = (
            self.level_callback
        )

        if callback is not None:

            try:
                callback(0.0)
            except Exception:
                pass

    # ==================================================
    # APPEND AUDIO
    # ==================================================

    def _append_audio(
        self,
        audio: np.ndarray,
    ):
        """
        Maintain a rolling wake-word audio window.
        """

        if (
            audio is None
            or audio.size == 0
        ):
            return

        with self._buffer_lock:

            required = len(
                self._audio_buffer
            )

            if len(audio) >= required:

                self._audio_buffer[:] = (
                    audio[-required:]
                )

                self._samples_received = (
                    required
                )

                return

            shift = len(audio)

            self._audio_buffer[:-shift] = (
                self._audio_buffer[shift:]
            )

            self._audio_buffer[-shift:] = (
                audio
            )

            self._samples_received = min(
                self._samples_received
                + shift,
                required,
            )

    # ==================================================
    # GET WAKE AUDIO
    # ==================================================

    def _get_wake_audio(self):

        with self._buffer_lock:

            if (
                self._samples_received
                < self.SAMPLE_RATE * 0.5
            ):
                return None

            return (
                self._audio_buffer.copy()
            )

    # ==================================================
    # TRANSCRIBE WAKE AUDIO
    # ==================================================

    def _transcribe_wake_audio(
        self,
        audio: np.ndarray,
    ) -> str:

        if (
            audio is None
            or audio.size == 0
        ):
            return ""

        if self.model is None:
            return ""

        try:

            segments, _ = (
                self.model.transcribe(
                    audio,
                    language=(
                        self.WHISPER_LANGUAGE
                    ),
                    beam_size=1,
                    best_of=1,
                    temperature=0.0,
                    vad_filter=True,
                    condition_on_previous_text=False,
                    without_timestamps=True,
                )
            )

            text = " ".join(
                segment.text.strip()
                for segment in segments
                if segment.text
            )

            return self._normalize_text(
                text
            )

        except Exception as error:

            print(
                "Faster-Whisper wake "
                "transcription error : "
                f"{error}"
            )

            return ""

    # ==================================================
    # WAKE WORD MATCHING
    # ==================================================

    def _contains_wake_word(
        self,
        text: str,
    ) -> bool:

        normalized = (
            self._normalize_text(text)
        )

        if not normalized:
            return False

        # ------------------------------------------
        # Reject obvious unrelated phrases
        # ------------------------------------------

        for rejected in (
            self.reject_phrases
        ):

            if rejected in normalized:

                return False

        # ------------------------------------------
        # Exact wake word
        # ------------------------------------------

        words = normalized.split()

        for word in words:

            if word in self.wake_words:

                return True

        # ------------------------------------------
        # Wake phrases
        # ------------------------------------------

        for phrase in self.wake_phrases:

            if phrase in normalized:

                return True

        # ------------------------------------------
        # "deep deep" / similar Whisper output
        # ------------------------------------------

        if (
            "deep deep"
            in normalized
        ):

            return True

        if (
            "deepdeep"
            in normalized
        ):

            return True

        # ------------------------------------------
        # Common Whisper segmentation
        # ------------------------------------------

        if (
            "deep"
            in words
            and len(words) <= 4
        ):

            return True

        return False

    # ==================================================
    # PRINT WAKE TEXT
    # ==================================================

    def _print_wake_text(
        self,
        text: str,
    ):

        text = self._normalize_text(
            text
        )

        if not text:
            return

        now = time.monotonic()

        # Avoid flooding terminal with identical
        # Faster-Whisper results.

        if (
            text == self._last_wake_text
            and (
                now
                - self._last_wake_log_time
            ) < 0.7
        ):

            return

        self._last_wake_text = text

        self._last_wake_log_time = now

        print(
            f"Wake STT : {text}"
        )

    # ==================================================
    # DETECTION
    # ==================================================

    def _handle_detection(
        self,
        text: str,
    ):
        """
        Handle one DHEEPTHI detection.

        This stops wake detection immediately.

        main_window.py receives the callback and is
        responsible for:

            TTS "Listening"
            ↓
            Fresh command capture
            ↓
            Groq Whisper
            ↓
            Existing command processing
        """

        now = time.monotonic()

        with self._detection_lock:

            if self._detection_latched:

                return

            if (
                now
                - self._last_detection_time
                < self.DETECTION_COOLDOWN_SECONDS
            ):

                return

            if (
                not self._running
                or self._closing
            ):

                return

            self._detection_latched = True

            self._detected = True

            self._last_detection_time = now

            self._running = False

        print(
            "\n⚡ DHEEPTHI "
            "WAKE WORD DETECTED"
        )

        print(
            f"Wake Text : {text}"
        )

        print(
            "Wake audio discarded."
        )

        print(
            "Handing control to "
            "main_window.py."
        )

        self._close_stream()

        callback = (
            self.on_detected
        )

        if callback is not None:

            try:

                callback(
                    self.WAKE_WORD
                )

            except TypeError:

                try:
                    callback()
                except Exception as error:

                    print(
                        "Wake callback error : "
                        f"{error}"
                    )

            except Exception as error:

                print(
                    "Wake callback error : "
                    f"{error}"
                )

    # ==================================================
    # MICROPHONE CALLBACK
    # ==================================================

    def _audio_callback(
        self,
        indata,
        frames,
        time_info,
        status,
    ):

        if (
            self._closing
            or not self._running
        ):

            return

        try:

            if (
                indata is None
                or len(indata) == 0
            ):

                return

            audio = np.frombuffer(
                bytes(indata),
                dtype=np.int16,
            )

            if audio.size == 0:
                return

            # ------------------------------------------
            # UI waveform
            # ------------------------------------------

            self._update_audio_level(
                audio
            )

            # ------------------------------------------
            # Rolling wake buffer
            # ------------------------------------------

            self._append_audio(
                audio.astype(
                    np.float32
                )
                / 32768.0
            )

            # ------------------------------------------
            # Only transcribe after enough audio
            # ------------------------------------------

            wake_audio = (
                self._get_wake_audio()
            )

            if wake_audio is None:
                return

            # ------------------------------------------
            # Faster-Whisper
            # ------------------------------------------

            text = (
                self._transcribe_wake_audio(
                    wake_audio
                )
            )

            if not text:
                return

            self._print_wake_text(
                text
            )

            # ------------------------------------------
            # DHEEPTHI
            # ------------------------------------------

            if self._contains_wake_word(
                text
            ):

                self._handle_detection(
                    text
                )

        except Exception as error:

            print(
                "Wake audio callback error : "
                f"{error}"
            )

    # ==================================================
    # OPEN MICROPHONE
    # ==================================================

    def _open_stream(self) -> bool:

        try:

            self._stream = (
                sd.RawInputStream(
                    samplerate=(
                        self.SAMPLE_RATE
                    ),
                    blocksize=(
                        self.BLOCK_SIZE
                    ),
                    dtype="int16",
                    channels=(
                        self.CHANNELS
                    ),
                    callback=(
                        self._audio_callback
                    ),
                )
            )

            self._stream.start()

            print(
                "🎤 DHEEPTHI wake "
                "microphone started."
            )

            print(
                "📈 Live wake waveform enabled."
            )

            return True

        except Exception as error:

            print(
                "Microphone Stream Error : "
                f"{error}"
            )

            self._close_stream()

            return False

    # ==================================================
    # CLOSE MICROPHONE
    # ==================================================

    def _close_stream(self):

        stream = self._stream

        self._stream = None

        if stream is not None:

            try:
                stream.stop()
            except Exception:
                pass

            try:
                stream.close()
            except Exception:
                pass

        self._reset_audio_level()

    # ==================================================
    # LISTEN FOR WAKE WORD
    # ==================================================

    def listen_for_wake_word(
        self,
    ) -> bool:
        """
        Blocking Faster-Whisper wake listener.

        Returns:

            True
                DHEEPTHI detected.

            False
                listener stopped or failed.
        """

        if self._closing:
            return False

        if not self.load_model():
            return False

        with self._lock:

            self._stop_requested = False

            self._detected = False

            self._last_wake_text = ""

            self._last_wake_log_time = 0.0

            with self._detection_lock:

                self._detection_latched = False

            with self._buffer_lock:

                self._audio_buffer.fill(
                    0.0
                )

                self._samples_received = 0

            self._running = True

            self._reset_audio_level()

            print(
                "\n========== "
                "DHEEPTHI / FASTER-WHISPER "
                "=========="
            )

            print(
                "DHEEPTHI standby: "
                "LOCAL Faster-Whisper wake detection."
            )

            print(
                "Groq wake detection: DISABLED"
            )

            print(
                "\n========== "
                "DHEEPTHI STANDBY "
                "=========="
            )

            print(
                "Listening locally with "
                "Faster-Whisper..."
            )

            print(
                "Say: DHEEPTHI"
            )

            print(
                "Wake Engine : Faster-Whisper"
            )

            print(
                "Wake Mode : LOCAL / OFFLINE"
            )

            print(
                f"Model : "
                f"{self.DEFAULT_MODEL}"
            )

            print(
                "Groq : COMMAND STT ONLY"
            )

            print(
                "Vosk : DISABLED"
            )

            print(
                "=======================================\n"
            )

            if not self._open_stream():

                self._running = False

                return False

        try:

            while (
                self._running
                and not self._closing
                and not self._stop_requested
            ):

                threading.Event().wait(
                    0.05
                )

            return bool(
                self._detected
            )

        finally:

            self._running = False

            self._close_stream()

            print(
                "DHEEPTHI wake listener stopped."
            )

    # ==================================================
    # ASYNC START
    # ==================================================

    def start(self) -> bool:
        """
        Start Faster-Whisper wake detection
        in a background thread.
        """

        if self._closing:
            return False

        with self._lock:

            if self._running:
                return True

            if (
                self._thread is not None
                and self._thread.is_alive()
            ):

                return True

            self._stop_requested = False

            self._detected = False

            with self._detection_lock:

                self._detection_latched = False

            self._thread = threading.Thread(
                target=self._listen_worker,
                name="ASTRA-FasterWhisper-Wake",
                daemon=True,
            )

            self._thread.start()

            return True

    # ==================================================
    # BACKGROUND WORKER
    # ==================================================

    def _listen_worker(self):

        try:

            self.listen_for_wake_word()

        except Exception as error:

            print(
                "Wake listener worker error : "
                f"{error}"
            )

    # ==================================================
    # STOP
    # ==================================================

    def stop(self):
        """
        Stop current wake detection.
        """

        with self._lock:

            self._stop_requested = True

            self._running = False

            self._close_stream()

        print(
            "DHEEPTHI wake listener stopped."
        )

    # ==================================================
    # RE-ARM
    # ==================================================

    def rearm(self) -> bool:
        """
        Start a new Faster-Whisper wake session.

        This is called by the existing application
        after the command pipeline is complete.
        """

        if self._closing:
            return False

        self.stop()

        with self._detection_lock:

            self._detection_latched = False

        self._detected = False

        with self._buffer_lock:

            self._audio_buffer.fill(
                0.0
            )

            self._samples_received = 0

        return self.start()

    # ==================================================
    # STATUS
    # ==================================================

    def is_running(self) -> bool:

        return bool(
            self._running
        )

    def is_model_loaded(self) -> bool:

        return bool(
            self._model_loaded
            and self.model is not None
        )

    def get_audio_level(self) -> float:

        return float(
            self.audio_level
        )

    # ==================================================
    # CALLBACKS
    # ==================================================

    def set_detection_callback(
        self,
        callback: Optional[
            Callable[[str], None]
        ],
    ):

        self.on_detected = callback

    def set_level_callback(
        self,
        callback: Optional[
            Callable[[float], None]
        ],
    ):

        self.level_callback = callback

    # ==================================================
    # CLOSE
    # ==================================================

    def close(self):

        self._closing = True

        self._stop_requested = True

        self._running = False

        self._close_stream()

        self.on_detected = None

        self.level_callback = None

        self.model = None

        self._model_loaded = False

        print(
            "DHEEPTHI Faster-Whisper "
            "wake detector shutdown completed."
        )


# ======================================================
# DIRECT TEST
# ======================================================

if __name__ == "__main__":

    print(
        "\n=========================================="
    )

    print(
        " ASTRA-AI FASTER-WHISPER WAKE TEST"
    )

    print(
        "=========================================="
    )

    detector = WakeWordDetector()

    try:

        print(
            "\nSay DHEEPTHI."
        )

        detected = (
            detector.listen_for_wake_word()
        )

        print(
            f"\nWake detected : {detected}"
        )

        if detected:

            print(
                "\nWake pipeline result:"
            )

            print(
                "1. DHEEPTHI detected"
            )

            print(
                '2. main_window.py -> TTS "Listening"'
            )

            print(
                "3. Fresh command microphone capture"
            )

            print(
                "4. Groq Whisper STT"
            )

            print(
                "5. Existing command-processing pipeline"
            )

    except KeyboardInterrupt:

        print(
            "\nTest interrupted."
        )

    finally:

        detector.close()