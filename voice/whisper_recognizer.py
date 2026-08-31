"""
ASTRA-AI
========

Speech Recognition / Wake Word Module

FINAL VOICE PIPELINE
--------------------

WAKE STAGE:
    Microphone
        ↓
    Continuous audio stream
        ↓
    Rolling audio buffer
        ↓
    Faster-Whisper LOCAL
        ↓
    DHEEPTHI dataset + controlled fuzzy matching
        ↓
    DHEEPTHI detected?
       ├── NO  → keep listening
       └── YES
              ↓
       stop wake stream
              ↓
       discard wake audio
              ↓
       fresh command recording
              ↓
       Groq Whisper
              ↓
       Command Dispatcher

IMPORTANT
---------
- Vosk is not used.
- openWakeWord is not used.
- Faster-Whisper is used only for local wake detection.
- Groq Whisper is used for normal/manual commands.
- Wake audio is never reused as command audio.
- Wake microphone remains physically OPEN continuously.
- The 4-second value is only an internal analysis window.
- DHEEPTHI detection immediately breaks wake listening.

WAKE MATCHING
-------------
The detector is recall-oriented, but it does NOT accept the
generic word "deep" by itself.

Explicitly supported examples include:
    dheepthi
    deepthi
    deepti
    deepthy
    deeptee
    dhepthi
    edipty
    deeply
    deep deep
    the the
    deep thi
    deep thee
    deep tea
    deep tee
    deep ti
    deep t
    hey dheepthi
    hello dheepthi
    hi dheepthi
    okay dheepthi
    wake up dheepthi
    wakeup dheepthi

Fuzzy matching is performed against the wake dataset and its
short n-grams. Arbitrary long sentences are not fuzzy-matched
against the canonical wake word.
"""

from __future__ import annotations

import os
import re
import tempfile
import threading
import wave
from difflib import SequenceMatcher
from pathlib import Path
from queue import Empty, Queue
from typing import Callable, Optional

import numpy as np
import sounddevice as sd
import speech_recognition as sr
from faster_whisper import WhisperModel

from voice.groq_recognizer import (
    GroqRecognizer,
    GroqSTTError,
)


class WhisperRecognizer:
    """ASTRA-AI speech recognizer."""

    # ==================================================
    # FASTER-WHISPER WAKE CONFIGURATION
    # ==================================================

    WAKE_MODEL_NAME = (
        os.getenv("ASTRA_WAKE_MODEL", "small").strip()
        or "small"
    )

    WAKE_COMPUTE_TYPE = (
        os.getenv(
            "ASTRA_WHISPER_COMPUTE_TYPE",
            "int8",
        ).strip()
        or "int8"
    )

    WAKE_DEVICE = (
        os.getenv(
            "ASTRA_WHISPER_DEVICE",
            "cpu",
        ).strip()
        or "cpu"
    )

    WAKE_LANGUAGE = "en"

    # ==================================================
    # CONTINUOUS WAKE AUDIO
    # ==================================================

    # Internal Whisper analysis window only.
    # The physical microphone never stops here.
    WAKE_ANALYSIS_SECONDS = 4.0

    # New analysis roughly every 1.5 seconds.
    WAKE_ANALYSIS_INTERVAL = 1.5

    WAKE_SAMPLE_RATE = 16000
    WAKE_CHANNELS = 1
    WAKE_BUFFER_SECONDS = 8.0

    # ==================================================
    # FASTER-WHISPER
    # ==================================================

    WAKE_VAD_FILTER = True
    WAKE_BEAM_SIZE = 1

    # ==================================================
    # NORMAL COMMAND RECORDING
    # ==================================================

    MAX_PHRASE_SECONDS = 20
    COMMAND_TIMEOUT = 5
    COMMAND_PHRASE_TIME_LIMIT = 20

    # ==================================================
    # SPEECH RECOGNITION
    # ==================================================

    PAUSE_THRESHOLD = 0.75
    PHRASE_THRESHOLD = 0.30
    NON_SPEAKING_DURATION = 0.40
    AMBIENT_CALIBRATION_SECONDS = 0.40

    MIN_ENERGY_THRESHOLD = 120
    MAX_ENERGY_THRESHOLD = 900

    # ==================================================
    # WAKE MATCHING
    # ==================================================

    # Do not lower this to make generic English words wake ASTRA.
    WAKE_SINGLE_WORD_THRESHOLD = 0.78

    # Fuzzy matching against explicit dataset entries.
    WAKE_FUZZY_THRESHOLD = 0.76

    # Fuzzy matching for short transcript n-grams.
    WAKE_NGRAM_THRESHOLD = 0.76

    # A fuzzy token must be at least this long unless it is
    # an explicit dataset entry.
    WAKE_MIN_FUZZY_TOKEN_LENGTH = 5

    # ==================================================
    # INITIALIZATION
    # ==================================================

    def __init__(
        self,
        groq_recognizer: GroqRecognizer | None = None,
        level_callback: Optional[Callable[[float], None]] = None,
    ):
        # --------------------------------------------------
        # SpeechRecognition is used only for command/manual
        # recording and confirmation.
        # --------------------------------------------------

        self.recognizer = sr.Recognizer()
        self.recognizer.dynamic_energy_threshold = True
        self.recognizer.energy_threshold = 180
        self.recognizer.dynamic_energy_adjustment_damping = 0.12
        self.recognizer.dynamic_energy_ratio = 1.5
        self.recognizer.pause_threshold = self.PAUSE_THRESHOLD
        self.recognizer.phrase_threshold = self.PHRASE_THRESHOLD
        self.recognizer.non_speaking_duration = (
            self.NON_SPEAKING_DURATION
        )
        self.recognizer.operation_timeout = None

        try:
            self.microphone = sr.Microphone()
        except Exception as error:
            print(
                "Microphone Initialization Error : "
                f"{error}"
            )
            self.microphone = None

        # --------------------------------------------------
        # Faster-Whisper model
        # --------------------------------------------------

        self.model: WhisperModel | None = None
        self._model_loaded = False
        self._model_lock = threading.RLock()

        # --------------------------------------------------
        # Groq command STT
        # --------------------------------------------------

        self.groq = (
            groq_recognizer
            if groq_recognizer is not None
            else GroqRecognizer(
                model="whisper-large-v3-turbo"
            )
        )

        # --------------------------------------------------
        # Audio meter
        # --------------------------------------------------

        self.audio_level = 0.0
        self.audio_stream = None
        self.level_callback = level_callback

        # --------------------------------------------------
        # Lifecycle
        # --------------------------------------------------

        self._closing = False
        self._stop_requested = False
        self._noise_calibrated = False
        self.last_audio = None

        # --------------------------------------------------
        # Wake state
        # --------------------------------------------------

        self.wake_word_active = False
        self._wake_standby_mode = False
        self._wake_detected = False

        # --------------------------------------------------
        # One microphone operation at a time
        # --------------------------------------------------

        self._microphone_lock = threading.RLock()

        # --------------------------------------------------
        # Continuous sounddevice wake stream
        # --------------------------------------------------

        self._wake_stream: sd.InputStream | None = None

        self._wake_audio_queue: Queue[np.ndarray] = Queue(
            maxsize=100
        )

        self._wake_buffer = np.empty(
            0,
            dtype=np.float32,
        )

        self._wake_total_samples = 0
        self._wake_stream_lock = threading.RLock()
        self._wake_detection_lock = threading.Lock()

        # ==================================================
        # DHEEPTHI WAKE DATASET
        # ==================================================
        #
        # IMPORTANT:
        # These are explicit accepted ASR forms.
        #
        # "deep" alone is deliberately NOT included.
        # ==================================================

        self.wake_words = frozenset(
            {
                # ------------------------------------------
                # Canonical / direct spellings
                # ------------------------------------------
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

                # ------------------------------------------
                # Observed ASR distortions
                # ------------------------------------------
                "edipty",
                "edipthi",
                "edhepti",
                "edhepthi",
                "deethi",
                "deethy",
                "depty",
                "depti",
                "dipthi",
                "dipti",
                "dhipthi",
                "deepie",
                "deeptie",
                "dheepie",
                "dheepi",

                # ------------------------------------------
                # Split-word forms
                # ------------------------------------------
                "deep thi",
                "deep thee",
                "deep tea",
                "deep tee",
                "deep ti",
                "deep th",
                "deep t",
                "deep d",

                "dheep thi",
                "dheep thee",
                "dheep tea",
                "dheep tee",
                "dheep ti",
                "dheep th",
                "dheep t",
                "dheep d",

                # ------------------------------------------
                # Greeting + wake forms
                # ------------------------------------------
                "hey dheepthi",
                "hey deepthi",
                "hey deepti",
                "hey deepthee",
                "hey deepthy",
                "hey deeptee",

                "hello dheepthi",
                "hello deepthi",
                "hello deepti",
                "hello deepthee",
                "hello deepthy",
                "hello deeptee",

                "hi dheepthi",
                "hi deepthi",
                "hi deepti",
                "hi deepthee",
                "hi deepthy",

                "okay dheepthi",
                "okay deepthi",
                "okay deepti",

                "ok dheepthi",
                "ok deepthi",
                "ok deepti",

                # ------------------------------------------
                # Common Whisper phonetic forms
                # ------------------------------------------
                "beep the",
                "weep the",
                "deep the",
                "deep thee",
                "deep tea",
                "deep tee",
                "deep thi",
                "deep ti",

                "dheep the",
                "dheep thee",
                "dheep tea",
                "dheep tee",
                "dheep thi",
                "dheep ti",

                # ------------------------------------------
                # Repeated forms observed from ASR
                # ------------------------------------------
                "deep deep",
                "deepdeep",
                "the the",
                "thethe",
                "dheep dheep",
                "dheepdheep",
                "deepthi deepthi",
                "dheepthi dheepthi",

                # ------------------------------------------
                # Wake-up phrases
                # ------------------------------------------
                "wake up dheepthi",
                "wake up deepthi",
                "wake up deepti",

                "wakeup dheepthi",
                "wakeup deepthi",
                "wakeup deepti",

                "wake dheepthi",
                "wake deepthi",
                "wake deepti",
            }
        )

        self.wake_phrase_variations = frozenset(
            {
                # ------------------------------------------
                # Short ASR forms that represent DHEEPTHI
                # ------------------------------------------
                "deeply",
                "deep please",
                "deep plz",

                "deep t",
                "deep ti",
                "deep thi",
                "deep thee",
                "deep tee",
                "deep tea",
                "deep th",
                "deep d",

                "dheep t",
                "dheep ti",
                "dheep thi",
                "dheep thee",
                "dheep tee",
                "dheep tea",
                "dheep th",
                "dheep d",

                # ------------------------------------------
                # Repetition
                # ------------------------------------------
                "deep deep",
                "deepdeep",
                "deep deep deep",
                "the the",
                "thethe",
                "the the the",

                # ------------------------------------------
                # Wake-up ASR distortions
                # ------------------------------------------
                "deep wake up",
                "deep wakeup",
                "dheep wake up",
                "dheep wakeup",

                "deep deep wake up",
                "deepdeep wake up",
                "deep deep wakeup",
                "deepdeep wakeup",

                "deep deep make up",
                "deepdeep make up",

                # ------------------------------------------
                # Greeting + shortened wake
                # ------------------------------------------
                "hey deep",
                "hey deeply",
                "hey dheep",

                "hello deep",
                "hello deeply",
                "hello dheep",

                "hi deep",
                "hi deeply",
                "hi dheep",

                "okay deep",
                "okay dheep",

                "ok deep",
                "ok dheep",

                # ------------------------------------------
                # Whisper phonetic forms
                # ------------------------------------------
                "beep",
                "beep the",
                "beep thee",
                "weep",
                "weep the",
                "weep thee",

                "deeply deep",
                "deep deeply",
            }
        )

        # --------------------------------------------------
        # Obvious English phrases which should not activate
        # unless an actual wake dataset item also appears.
        #
        # These are exact/strong false-activation guards.
        # --------------------------------------------------

        self.wake_reject_phrases = frozenset(
            {
                "deep sleep",
                "sleep deeply",
                "deep thought",
                "deep thoughts",
                "deep water",
                "deep voice",
                "deep breath",
                "deep breathing",
                "deep learning",
                "deep neural network",
                "deep meaning",
                "deep hole",
                "deep sea",
                "deep ocean",
            }
        )

        # --------------------------------------------------
        # Canonical spellings only for fuzzy token matching.
        #
        # Generic "deep" is intentionally excluded.
        # --------------------------------------------------

        self._wake_candidates = (
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
            "edipty",
            "edipthi",
            "edhepti",
            "edhepthi",
            "deethi",
            "deethy",
            "depty",
            "depti",
            "dipthi",
            "dipti",
            "dhipthi",
            "deepie",
            "deeptie",
            "dheepie",
            "dheepi",
        )

        # --------------------------------------------------
        # Normalized dataset used by all fuzzy matching.
        # --------------------------------------------------

        self._wake_fuzzy_dataset = frozenset(
            self._normalize_dataset_item(item)
            for item in (
                set(self.wake_words)
                | set(self.wake_phrase_variations)
            )
            if item
        )

        # Dataset entries are separated into single-token and
        # phrase entries so fuzzy matching does not accidentally
        # make a generic word activate.
        self._wake_single_word_dataset = frozenset(
            item
            for item in self._wake_fuzzy_dataset
            if " " not in item
        )

        self._wake_phrase_dataset = frozenset(
            item
            for item in self._wake_fuzzy_dataset
            if " " in item
        )

        # ==================================================
        # STARTUP LOG
        # ==================================================

        print("\n========== ASTRA WHISPER ==========")
        print("Wake Engine : Faster-Whisper")
        print("Wake Mode : LOCAL / OFFLINE")
        print(f"Wake Model : {self.WAKE_MODEL_NAME}")
        print(f"Compute Type : {self.WAKE_COMPUTE_TYPE}")
        print(f"Device : {self.WAKE_DEVICE}")
        print("Wake Capture : CONTINUOUS")
        print(
            f"Analysis Window : "
            f"{self.WAKE_ANALYSIS_SECONDS} seconds"
        )
        print(
            f"Analysis Interval : "
            f"{self.WAKE_ANALYSIS_INTERVAL} seconds"
        )
        print("Wake Word : DHEEPTHI")
        print(
            f"Wake Dataset Entries : "
            f"{len(self._wake_fuzzy_dataset)}"
        )
        print(
            f"Wake Fuzzy Threshold : "
            f"{self.WAKE_FUZZY_THRESHOLD}"
        )
        print(
            f"Wake Token Fuzzy Threshold : "
            f"{self.WAKE_SINGLE_WORD_THRESHOLD}"
        )
        print("Command STT : Groq Whisper")
        print("Vosk : DISABLED")
        print("openWakeWord : DISABLED")
        print("Live Wake Waveform : ENABLED")
        print("Continuous Mic : ENABLED")
        print("Generic 'deep' alone : DISABLED")
        print("Recall-Oriented Wake Matching : ENABLED")
        print("===================================\n")

    # ==================================================
    # DATASET NORMALIZATION
    # ==================================================

    @staticmethod
    def _normalize_dataset_item(text: str) -> str:
        if not text:
            return ""

        text = str(text).lower().strip()
        text = re.sub(r"[^a-z0-9\s]+", " ", text)
        return re.sub(r"\s+", " ", text).strip()

    # ==================================================
    # LOAD FASTER-WHISPER
    # ==================================================

    def load_model(self) -> bool:
        if self._closing:
            return False

        with self._model_lock:
            if self._model_loaded and self.model is not None:
                return True

            try:
                print("\nLoading local Faster-Whisper model...")
                print(f"Model : {self.WAKE_MODEL_NAME}")
                print(f"Device : {self.WAKE_DEVICE}")
                print(
                    f"Compute Type : "
                    f"{self.WAKE_COMPUTE_TYPE}"
                )

                self.model = WhisperModel(
                    self.WAKE_MODEL_NAME,
                    device=self.WAKE_DEVICE,
                    compute_type=self.WAKE_COMPUTE_TYPE,
                )

                self._model_loaded = True

                print(
                    "Faster-Whisper model "
                    "loaded successfully."
                )
                print(
                    "DHEEPTHI local wake "
                    "detection ready."
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

    def is_model_loaded(self) -> bool:
        return bool(
            self._model_loaded
            and self.model is not None
        )

    # ==================================================
    # AUDIO LEVEL
    # ==================================================

    @staticmethod
    def _calculate_audio_level(
        samples: np.ndarray,
    ) -> float:
        if samples is None or samples.size == 0:
            return 0.0

        try:
            rms = float(
                np.sqrt(
                    np.mean(
                        np.square(samples)
                    )
                )
            )
            level = min(rms * 22.0, 1.0)
            return max(0.0, level)
        except Exception:
            return 0.0

    def _publish_audio_level(
        self,
        samples: np.ndarray,
    ):
        level = self._calculate_audio_level(samples)

        self.audio_level = (
            self.audio_level * 0.80
            + level * 0.20
        )

        callback = self.level_callback
        if callback is not None:
            try:
                callback(self.audio_level)
            except Exception:
                pass

    # ==================================================
    # MANUAL AUDIO CALLBACK
    # ==================================================

    def _manual_audio_callback(
        self,
        indata,
        frames,
        time_info,
        status,
    ):
        try:
            if indata is None or len(indata) == 0:
                return

            samples = np.asarray(
                indata,
                dtype=np.float32,
            )

            self._publish_audio_level(samples)

        except Exception:
            pass

    # ==================================================
    # START AUDIO METER
    # ==================================================

    def start_audio_meter(self):
        if (
            self._closing
            or self.audio_stream is not None
        ):
            return

        try:
            self.audio_stream = sd.InputStream(
                channels=1,
                samplerate=16000,
                blocksize=1024,
                dtype="float32",
                latency="high",
                callback=self._manual_audio_callback,
            )

            self.audio_stream.start()

            print(
                "🎚️ Live microphone "
                "audio meter started."
            )

        except Exception as error:
            print(
                f"Audio Meter Error : {error}"
            )
            self.audio_stream = None

    # ==================================================
    # STOP AUDIO METER
    # ==================================================

    def stop_audio_meter(self):
        stream = self.audio_stream
        self.audio_stream = None

        if stream is not None:
            try:
                stream.stop()
            except Exception:
                pass

            try:
                stream.close()
            except Exception:
                pass

        self.audio_level = 0.0

        callback = self.level_callback
        if callback is not None:
            try:
                callback(0.0)
            except Exception:
                pass

    # ==================================================
    # CONTINUOUS WAKE CALLBACK
    # ==================================================

    def _wake_stream_callback(
        self,
        indata,
        frames,
        time_info,
        status,
    ):
        """
        Audio callback only captures audio.

        Faster-Whisper never runs inside this callback.
        """

        if (
            self._closing
            or not self.wake_word_active
        ):
            return

        try:
            if indata is None or len(indata) == 0:
                return

            samples = np.asarray(
                indata,
                dtype=np.float32,
            ).reshape(-1)

            if samples.size == 0:
                return

            self._publish_audio_level(samples)

            audio_copy = np.array(
                samples,
                dtype=np.float32,
                copy=True,
            )

            with self._wake_stream_lock:
                self._wake_total_samples += int(
                    audio_copy.size
                )

            try:
                self._wake_audio_queue.put_nowait(
                    audio_copy
                )
            except Exception:
                try:
                    self._wake_audio_queue.get_nowait()
                except Empty:
                    pass

                try:
                    self._wake_audio_queue.put_nowait(
                        audio_copy
                    )
                except Exception:
                    pass

        except Exception as error:
            print(
                "Wake audio callback error : "
                f"{error}"
            )

    # ==================================================
    # START CONTINUOUS WAKE STREAM
    # ==================================================

    def _start_wake_stream(self) -> bool:
        with self._wake_stream_lock:
            if self._wake_stream is not None:
                return True

            try:
                self._wake_audio_queue = Queue(maxsize=100)
                self._wake_buffer = np.empty(
                    0,
                    dtype=np.float32,
                )
                self._wake_total_samples = 0

                self._wake_stream = sd.InputStream(
                    samplerate=self.WAKE_SAMPLE_RATE,
                    channels=self.WAKE_CHANNELS,
                    dtype="float32",
                    blocksize=1024,
                    latency="high",
                    callback=self._wake_stream_callback,
                )

                self._wake_stream.start()

                print(
                    "\n🎤 Continuous wake "
                    "microphone started."
                )
                print(
                    "🎙️ Microphone will remain "
                    "OPEN until DHEEPTHI is detected."
                )
                print(
                    "📈 Continuous wake waveform enabled."
                )

                return True

            except Exception as error:
                print(
                    f"Wake Stream Error : {error}"
                )
                self._stop_wake_stream()
                return False

    # ==================================================
    # STOP CONTINUOUS WAKE STREAM
    # ==================================================

    def _stop_wake_stream(self):
        with self._wake_stream_lock:
            stream = self._wake_stream
            self._wake_stream = None

            if stream is not None:
                try:
                    stream.stop()
                except Exception:
                    pass

                try:
                    stream.close()
                except Exception:
                    pass

            self._wake_buffer = np.empty(
                0,
                dtype=np.float32,
            )
            self._wake_total_samples = 0

            try:
                while True:
                    self._wake_audio_queue.get_nowait()
            except Empty:
                pass

            self.audio_level = 0.0

            callback = self.level_callback
            if callback is not None:
                try:
                    callback(0.0)
                except Exception:
                    pass

            print(
                "🎤 Continuous wake "
                "microphone stopped."
            )

    # ==================================================
    # CONSUME WAKE AUDIO
    # ==================================================

    def _consume_wake_audio(
        self,
    ) -> np.ndarray | None:
        blocks: list[np.ndarray] = []

        try:
            while True:
                block = (
                    self._wake_audio_queue.get_nowait()
                )

                if (
                    block is not None
                    and block.size > 0
                ):
                    blocks.append(block)

        except Empty:
            pass

        if blocks:
            incoming = np.concatenate(blocks)

            if self._wake_buffer.size == 0:
                self._wake_buffer = incoming
            else:
                self._wake_buffer = np.concatenate(
                    (
                        self._wake_buffer,
                        incoming,
                    )
                )

        max_samples = int(
            self.WAKE_BUFFER_SECONDS
            * self.WAKE_SAMPLE_RATE
        )

        if self._wake_buffer.size > max_samples:
            self._wake_buffer = self._wake_buffer[
                -max_samples:
            ]

        analysis_samples = int(
            self.WAKE_ANALYSIS_SECONDS
            * self.WAKE_SAMPLE_RATE
        )

        if self._wake_buffer.size < analysis_samples:
            return None

        return np.array(
            self._wake_buffer[
                -analysis_samples:
            ],
            dtype=np.float32,
            copy=True,
        )

    # ==================================================
    # WRITE WAKE SNAPSHOT
    # ==================================================

    def _write_wake_snapshot(
        self,
        samples: np.ndarray,
    ) -> str | None:
        if samples is None or samples.size == 0:
            return None

        path = None

        try:
            path = self._temporary_audio_path("wake")

            clipped = np.clip(
                samples,
                -1.0,
                1.0,
            )

            pcm16 = (
                clipped * 32767.0
            ).astype(np.int16)

            with wave.open(path, "wb") as wav_file:
                wav_file.setnchannels(
                    self.WAKE_CHANNELS
                )
                wav_file.setsampwidth(2)
                wav_file.setframerate(
                    self.WAKE_SAMPLE_RATE
                )
                wav_file.writeframes(
                    pcm16.tobytes()
                )

            return path

        except Exception as error:
            print(
                f"Wake Snapshot Error : {error}"
            )

            if path:
                try:
                    os.remove(path)
                except Exception:
                    pass

            return None

    # ==================================================
    # LOCAL FASTER-WHISPER TRANSCRIPTION
    # ==================================================

    def _transcribe_wake_local(
        self,
        audio_file: str | Path,
    ) -> str | None:
        if self._closing:
            return None

        if not audio_file:
            return None

        if not self.load_model():
            return None

        try:
            segments, info = self.model.transcribe(
                str(audio_file),
                language=self.WAKE_LANGUAGE,
                beam_size=self.WAKE_BEAM_SIZE,
                vad_filter=self.WAKE_VAD_FILTER,
                condition_on_previous_text=False,
                temperature=0.0,
                without_timestamps=True,
            )

            parts: list[str] = []

            for segment in segments:
                text = (
                    segment.text
                    if segment is not None
                    else ""
                )

                if text:
                    parts.append(text.strip())

            transcript = self.normalize_wake_text(
                " ".join(parts).strip()
            )

            if transcript:
                print(
                    "Wake Faster-Whisper : "
                    f"{transcript}"
                )
            else:
                print(
                    "Wake Faster-Whisper : "
                    "<empty>"
                )

            return transcript or None

        except Exception as error:
            print(
                "Faster-Whisper Wake Error : "
                f"{error}"
            )
            return None

    # ==================================================
    # CONTINUOUS WAKE ANALYSIS
    # ==================================================

    def _analyze_continuous_wake_audio(
        self,
        samples: np.ndarray,
    ) -> str | None:
        if (
            self._closing
            or not self.wake_word_active
        ):
            return None

        path = self._write_wake_snapshot(samples)
        if path is None:
            return None

        try:
            return self._transcribe_wake_local(path)
        finally:
            try:
                os.remove(path)
            except Exception:
                pass

    # ==================================================
    # NORMALIZE WAKE TEXT
    # ==================================================

    @staticmethod
    def normalize_wake_text(text) -> str:
        if not text:
            return ""

        text = str(text).lower().strip()
        text = re.sub(
            r"[^a-z0-9\s_-]+",
            " ",
            text,
        )
        text = text.replace("_", " ")

        return re.sub(
            r"\s+",
            " ",
            text,
        ).strip()

    # ==================================================
    # FUZZY SIMILARITY
    # ==================================================

    @staticmethod
    def _similarity(
        left: str,
        right: str,
    ) -> float:
        left = re.sub(
            r"[^a-z0-9]+",
            "",
            left.lower(),
        )
        right = re.sub(
            r"[^a-z0-9]+",
            "",
            right.lower(),
        )

        if not left or not right:
            return 0.0

        return SequenceMatcher(
            None,
            left,
            right,
        ).ratio()

    # ==================================================
    # CANONICAL WAKE SIMILARITY
    # ==================================================

    def wake_word_similarity(self, word) -> float:
        cleaned = re.sub(
            r"[^a-z]+",
            "",
            (word or "").lower(),
        )

        if not cleaned:
            return 0.0

        return max(
            (
                self._similarity(
                    cleaned,
                    candidate,
                )
                for candidate in self._wake_candidates
            ),
            default=0.0,
        )

    # ==================================================
    # WAKE-LIKE TOKEN
    # ==================================================

    def _is_wake_like_token(
        self,
        token,
    ) -> bool:
        normalized = self.normalize_wake_text(token)

        if not normalized or " " in normalized:
            return False

        # Exact single-token dataset item.
        if normalized in self._wake_single_word_dataset:
            print(
                "Wake Token Exact Match : "
                f"{normalized}"
            )
            return True

        # Never allow generic "deep" as a fuzzy wake token.
        if normalized in {
            "deep",
            "the",
            "tea",
            "tee",
            "thi",
            "ti",
            "th",
            "t",
            "d",
        }:
            return False

        if len(normalized) < self.WAKE_MIN_FUZZY_TOKEN_LENGTH:
            return False

        score = self.wake_word_similarity(normalized)

        if score >= self.WAKE_SINGLE_WORD_THRESHOLD:
            print(
                "Wake Token Fuzzy Match : "
                f"'{normalized}' "
                f"(score={score:.2f})"
            )
            return True

        return False

    # ==================================================
    # N-GRAM GENERATOR
    # ==================================================

    @staticmethod
    def _generate_ngrams(
        words: list[str],
        maximum: int = 5,
    ):
        total = len(words)

        for size in range(
            1,
            min(maximum, total) + 1,
        ):
            for index in range(
                0,
                total - size + 1,
            ):
                yield " ".join(
                    words[
                        index:index + size
                    ]
                )

    # ==================================================
    # DATASET FUZZY MATCH
    # ==================================================

    def _fuzzy_dataset_match(
        self,
        normalized: str,
    ) -> tuple[bool, str | None, float]:
        if not normalized:
            return False, None, 0.0

        words = normalized.split()
        best_match = None
        best_score = 0.0

        # ----------------------------------------------
        # Phrase n-grams first.
        # ----------------------------------------------

        for ngram in self._generate_ngrams(
            words,
            maximum=5,
        ):
            if len(ngram) < 3:
                continue

            # Do not fuzzy-match one generic word such as
            # "deep" against phrase entries.
            if " " not in ngram:
                continue

            for candidate in self._wake_phrase_dataset:
                score = self._similarity(
                    ngram,
                    candidate,
                )

                if score > best_score:
                    best_score = score
                    best_match = candidate

        if (
            best_match is not None
            and best_score >= self.WAKE_NGRAM_THRESHOLD
        ):
            return True, best_match, best_score

        # ----------------------------------------------
        # Single-token fuzzy matching against explicit
        # dataset items only.
        # ----------------------------------------------

        for word in words:
            if len(word) < self.WAKE_MIN_FUZZY_TOKEN_LENGTH:
                continue

            if word in {
                "deep",
                "the",
                "tea",
                "tee",
                "thi",
                "ti",
                "th",
                "t",
                "d",
            }:
                continue

            for candidate in self._wake_single_word_dataset:
                if len(candidate) < 5:
                    continue

                score = self._similarity(
                    word,
                    candidate,
                )

                if score > best_score:
                    best_score = score
                    best_match = candidate

        if (
            best_match is not None
            and best_score >= self.WAKE_SINGLE_WORD_THRESHOLD
        ):
            return True, best_match, best_score

        return False, best_match, best_score

    # ==================================================
    # REPEATED DATASET FORM
    # ==================================================

    @staticmethod
    def _contains_repeated_wake_form(
        words: list[str],
    ) -> bool:
        if len(words) < 2:
            return False

        for index in range(len(words) - 1):
            first = words[index]
            second = words[index + 1]

            if first != second:
                continue

            if first in {
                "deep",
                "dheep",
                "deeply",
                "the",
                "dheepthi",
                "deepthi",
                "deepti",
            }:
                return True

        return False

    # ==================================================
    # SPLIT DHEEPTHI FAMILY
    # ==================================================

    def _contains_split_wake_form(
        self,
        words: list[str],
    ) -> bool:
        """
        Accept explicit DHEEPTHI split pronunciations.

        IMPORTANT:
        "deep" alone is NOT accepted.
        """

        endings = {
            "thi",
            "thee",
            "tea",
            "tee",
            "ti",
            "th",
            "t",
            "d",
            "please",
            "plz",
        }

        for index, word in enumerate(words):
            if word not in {
                "deep",
                "dheep",
            }:
                continue

            if index + 1 >= len(words):
                continue

            following = words[index + 1]

            if following in endings:
                print(
                    "Wake Split-Word Match : "
                    f"{word} {following}"
                )
                return True

        return False

    # ==================================================
    # JOINED ASR FORM
    # ==================================================

    def _joined_wake_match(
        self,
        words: list[str],
    ) -> bool:
        if not words:
            return False

        joined = "".join(words)

        candidates = (
            "deepdeep",
            "deepdee",
            "deepthi",
            "deepthee",
            "deepthy",
            "deeptee",
            "dheepthi",
            "dhepthi",
            "dheethi",
            "dhethi",
            "edipty",
            "edipthi",
            "edhepti",
            "edhepthi",
            "thethe",
        )

        for candidate in candidates:
            if candidate in joined:
                print(
                    "Wake Joined Match : "
                    f"'{joined}' -> '{candidate}'"
                )
                return True

            score = self._similarity(
                joined,
                candidate,
            )

            if score >= self.WAKE_FUZZY_THRESHOLD:
                print(
                    "Wake Joined Fuzzy Match : "
                    f"'{joined}' -> '{candidate}' "
                    f"(score={score:.2f})"
                )
                return True

        return False

    # ==================================================
    # CONTAINS WAKE WORD
    # ==================================================

    def contains_wake_word(
        self,
        text,
    ) -> bool:
        """
        Recall-oriented DHEEPTHI matching with explicit
        false-activation guards.

        Detection order:
            1. exact reject guard
            2. exact dataset phrase/token
            3. repeated dataset form
            4. split-word dataset form
            5. explicit token fuzzy match
            6. joined ASR form
            7. short dataset n-gram fuzzy match
        """

        normalized = self.normalize_wake_text(text)

        if not normalized:
            return False

        print(
            f"Wake Match Analyzer : {normalized}"
        )

        # ----------------------------------------------
        # 1. Exact false-activation guard.
        # ----------------------------------------------

        if normalized in self.wake_reject_phrases:
            print(
                "Wake Reject Match : "
                f"{normalized}"
            )
            return False

        words = normalized.split()

        if not words:
            return False

        # ----------------------------------------------
        # 2. Exact dataset match.
        # ----------------------------------------------

        if normalized in self._wake_fuzzy_dataset:
            print(
                "Wake Dataset Exact Match : "
                f"{normalized}"
            )
            return True

        # Dataset phrase/token anywhere in the transcript.
        for candidate in self._wake_fuzzy_dataset:
            if len(candidate) < 4:
                continue

            pattern = (
                rf"(?<!\w)"
                rf"{re.escape(candidate)}"
                rf"(?!\w)"
            )

            if re.search(pattern, normalized):
                print(
                    "Wake Dataset Phrase Match : "
                    f"'{candidate}'"
                )
                return True

        # ----------------------------------------------
        # 3. Repeated forms.
        # ----------------------------------------------

        if self._contains_repeated_wake_form(words):
            print(
                "Wake Repeated-Form Match : "
                f"{normalized}"
            )
            return True

        # ----------------------------------------------
        # 4. Split DHEEPTHI forms.
        # ----------------------------------------------

        if self._contains_split_wake_form(words):
            return True

        # ----------------------------------------------
        # 5. Explicit single-token fuzzy matching.
        # ----------------------------------------------

        for word in words:
            if self._is_wake_like_token(word):
                print(
                    "Wake Token Match : "
                    f"{word}"
                )
                return True

        # ----------------------------------------------
        # 6. Joined ASR forms.
        # ----------------------------------------------

        if self._joined_wake_match(words):
            return True

        # ----------------------------------------------
        # 7. Dataset n-gram fuzzy matching.
        # ----------------------------------------------

        matched, candidate, score = (
            self._fuzzy_dataset_match(normalized)
        )

        if matched:
            print(
                "Wake Dataset Fuzzy Match : "
                f"'{normalized}' -> "
                f"'{candidate}' "
                f"(score={score:.2f})"
            )
            return True

        print("Wake Match : NO")
        return False

    # ==================================================
    # REMOVE WAKE WORD
    # ==================================================

    def remove_wake_word(
        self,
        text,
    ) -> str:
        if not text:
            return ""

        original = " ".join(
            str(text).strip().split()
        )

        normalized = self.normalize_wake_text(
            original
        )

        # Longest forms first.
        prefixes = (
            "wake up dheepthi",
            "wake up deepthi",
            "wake up deepti",

            "wakeup dheepthi",
            "wakeup deepthi",
            "wakeup deepti",

            "hey dheepthi",
            "hey deepthi",
            "hey deepti",
            "hey deepthee",
            "hey deepthy",
            "hey deeptee",

            "hello dheepthi",
            "hello deepthi",
            "hello deepti",
            "hello deepthee",
            "hello deepthy",
            "hello deeptee",

            "hi dheepthi",
            "hi deepthi",
            "hi deepti",
            "hi deepthee",
            "hi deepthy",

            "okay dheepthi",
            "okay deepthi",
            "okay deepti",

            "ok dheepthi",
            "ok deepthi",
            "ok deepti",

            "deep deep wake up",
            "deepdeep wake up",
            "deep deep wakeup",
            "deepdeep wakeup",
            "deep deep make up",
            "deepdeep make up",

            "deep please",
            "deep plz",

            "deep thee",
            "deep tea",
            "deep thi",
            "deep tee",
            "deep ti",
            "deep th",
            "deep t",
            "deep d",

            "dheep thee",
            "dheep tea",
            "dheep thi",
            "dheep tee",
            "dheep ti",
            "dheep th",
            "dheep t",
            "dheep d",
        )

        for prefix in sorted(
            prefixes,
            key=len,
            reverse=True,
        ):
            if normalized.startswith(prefix):
                words = original.split()
                return " ".join(
                    words[len(prefix.split()):]
                ).strip()

        words = original.split()

        if not words:
            return ""

        first = re.sub(
            r"^[^\w-]+|[^\w-]+$",
            "",
            words[0].lower(),
        )

        single_wake_forms = {
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
            "edipty",
            "edipthi",
            "edhepti",
            "edhepthi",
            "deethi",
            "deethy",
            "depty",
            "depti",
            "dipthi",
            "dipti",
            "dhipthi",
            "deepie",
            "deeptie",
            "dheepie",
            "dheepi",
            "deeply",
        }

        if first in single_wake_forms:
            return " ".join(words[1:]).strip()

        if len(words) >= 2:
            second = re.sub(
                r"^[^\w-]+|[^\w-]+$",
                "",
                words[1].lower(),
            )

            if (
                first in {"deep", "dheep"}
                and second in {
                    "thi",
                    "thee",
                    "tea",
                    "tee",
                    "ti",
                    "th",
                    "t",
                    "d",
                    "please",
                    "plz",
                }
            ):
                return " ".join(words[2:]).strip()

        return original

    # ==================================================
    # GARBAGE DETECTION
    # ==================================================

    @staticmethod
    def _is_repetitive_garbage(
        text,
    ) -> bool:
        if not text:
            return True

        words = re.findall(
            r"[a-z]+",
            text.lower(),
        )

        if len(words) < 5:
            return False

        if len(set(words)) == 1:
            return True

        counts: dict[str, int] = {}

        for word in words:
            counts[word] = counts.get(word, 0) + 1

        highest = max(counts.values())

        return (
            highest >= 8
            and highest / len(words) >= 0.80
        )

    # ==================================================
    # TEMP AUDIO PATH
    # ==================================================

    def _temporary_audio_path(
        self,
        prefix: str,
    ) -> str:
        directory = os.path.abspath(
            os.path.join(
                "temp",
                "voice",
            )
        )

        os.makedirs(
            directory,
            exist_ok=True,
        )

        fd, path = tempfile.mkstemp(
            prefix=f"{prefix}_",
            suffix=".wav",
            dir=directory,
        )

        os.close(fd)
        return path

    # ==================================================
    # MANUAL MICROPHONE CALIBRATION
    # ==================================================

    def _calibrate_microphone(
        self,
        source,
    ):
        if (
            self._noise_calibrated
            or self._closing
        ):
            return

        if self.recognizer is None:
            return

        try:
            print(
                "🎧 Calibrating microphone..."
            )

            self.recognizer.adjust_for_ambient_noise(
                source,
                duration=self.AMBIENT_CALIBRATION_SECONDS,
            )

            threshold = max(
                self.MIN_ENERGY_THRESHOLD,
                min(
                    int(
                        self.recognizer.energy_threshold
                    ),
                    self.MAX_ENERGY_THRESHOLD,
                ),
            )

            self.recognizer.energy_threshold = threshold
            self._noise_calibrated = True

            print(
                "🎧 Microphone calibrated."
            )
            print(
                f"Energy Threshold : {threshold}"
            )

        except Exception as error:
            print(
                "Microphone Calibration Error : "
                f"{error}"
            )

    # ==================================================
    # NORMAL COMMAND RECORDING
    # ==================================================

    def record_audio(
        self,
        timeout=None,
        phrase_time_limit=None,
        use_audio_meter=True,
        wake_mode=False,
    ):
        if wake_mode:
            print(
                "Wake recording is continuous."
            )
            return None

        with self._microphone_lock:
            audio = None

            try:
                if (
                    self.microphone is None
                    or self.recognizer is None
                    or self._closing
                    or self._stop_requested
                ):
                    return None

                with self.microphone as source:
                    self._calibrate_microphone(source)

                    if (
                        self._closing
                        or self._stop_requested
                    ):
                        return None

                    if use_audio_meter:
                        self.start_audio_meter()

                    print("🎤 Listening...")
                    print("🎙️ Speak your command...")

                    try:
                        audio = self.recognizer.listen(
                            source,
                            timeout=timeout,
                            phrase_time_limit=(
                                phrase_time_limit
                                if phrase_time_limit is not None
                                else self.MAX_PHRASE_SECONDS
                            ),
                        )
                    except sr.WaitTimeoutError:
                        print(
                            "Listening timed out."
                        )
                        return None

                    if (
                        self._closing
                        or self._stop_requested
                    ):
                        return None

                    if (
                        audio is None
                        or not audio.frame_data
                    ):
                        return None

                path = self._temporary_audio_path("command")

                with open(path, "wb") as file:
                    file.write(
                        audio.get_wav_data()
                    )

                self.last_audio = path

                print(f"Audio File : {path}")
                return path

            except OSError as error:
                print(
                    "Microphone / Audio Device Error : "
                    f"{error}"
                )
                return None

            except Exception as error:
                print(
                    "Audio Recording Error : "
                    f"{error}"
                )
                return None

            finally:
                self.stop_audio_meter()

    # ==================================================
    # GROQ TRANSCRIPTION
    # ==================================================

    def _transcribe_file(
        self,
        audio_file,
        wake_mode=False,
    ):
        if self._closing:
            return None

        if not audio_file:
            return None

        if self.groq is None:
            print(
                "Groq STT recognizer is unavailable."
            )
            return None

        try:
            if wake_mode:
                print(
                    "WARNING: Groq wake path is disabled."
                )
                return None

            print(
                "🧠 Sending command audio "
                "to Groq Whisper..."
            )

            text = self.groq.transcribe(audio_file)
            text = (text or "").strip()

            if not text:
                print(
                    "Groq Whisper returned "
                    "empty transcript."
                )
                return None

            text = " ".join(text.split())

            text = (
                text
                .replace(" ,", ",")
                .replace(" .", ".")
                .replace(" ?", "?")
                .replace(" !", "!")
                .strip()
                .lower()
            )

            if self._is_repetitive_garbage(text):
                print(
                    "Rejected repetitive ASR garbage."
                )
                return None

            print(
                f"Recognized Text : {text}"
            )
            return text

        except GroqSTTError as error:
            print(
                f"Groq STT Error : {error}"
            )
            return None

        except Exception as error:
            print(
                f"Groq Transcription Error : {error}"
            )
            return None

    # ==================================================
    # MANUAL LISTEN
    # ==================================================

    def listen(
        self,
        retries=1,
        timeout=None,
        phrase_time_limit=None,
        reset_stop=True,
        use_audio_meter=True,
    ):
        if reset_stop and not self._closing:
            self._stop_requested = False

        if self._closing:
            return None

        attempts = max(1, int(retries))

        for attempt in range(attempts):
            if (
                self._closing
                or self._stop_requested
            ):
                return None

            audio_file = self.record_audio(
                timeout=timeout,
                phrase_time_limit=phrase_time_limit,
                use_audio_meter=use_audio_meter,
                wake_mode=False,
            )

            print(
                f"Audio File : {audio_file}"
            )

            if audio_file is None:
                continue

            try:
                text = self._transcribe_file(
                    audio_file,
                    wake_mode=False,
                )

                if text:
                    return text

            finally:
                try:
                    os.remove(audio_file)
                except Exception:
                    pass

            print(
                "No valid speech detected. "
                f"Retry {attempt + 1}/{attempts}"
            )

        return None

    # ==================================================
    # CONTINUOUS WAKE LISTENER
    # ==================================================

    def listen_for_wake_word(
        self,
        retries=1,
    ):
        """
        Continuously listen until DHEEPTHI is detected.

        The physical microphone stays open.
        Only internal 4-second snapshots are analyzed.
        """

        if self._closing:
            return False

        if not self.load_model():
            return False

        self._stop_requested = False
        self.wake_word_active = True
        self._wake_standby_mode = True
        self._wake_detected = False

        print(
            "\n========== DHEEPTHI / FASTER-WHISPER =========="
        )
        print("DHEEPTHI standby active.")
        print("Wake STT : Faster-Whisper LOCAL")
        print(f"Wake Model : {self.WAKE_MODEL_NAME}")
        print("Wake Capture : CONTINUOUS")
        print(
            f"Internal Analysis Window : "
            f"{self.WAKE_ANALYSIS_SECONDS}s"
        )
        print(
            f"Analysis Interval : "
            f"{self.WAKE_ANALYSIS_INTERVAL}s"
        )
        print("MIC STOP BETWEEN WINDOWS : NO")
        print(
            "DHEEPTHI can appear anywhere "
            "inside the analyzed transcript."
        )
        print(
            f"Wake Dataset : "
            f"{len(self._wake_fuzzy_dataset)} entries"
        )
        print(
            "Wake Matching : "
            "EXACT + VARIATIONS + TOKEN + FUZZY"
        )
        print(
            "Generic 'deep' alone : DISABLED"
        )
        print("Groq : COMMANDS ONLY")
        print("Vosk : DISABLED")
        print("openWakeWord : DISABLED")
        print("===============================================\n")

        if not self._start_wake_stream():
            self.wake_word_active = False
            self._wake_standby_mode = False
            return False

        analysis_interval_samples = int(
            self.WAKE_ANALYSIS_INTERVAL
            * self.WAKE_SAMPLE_RATE
        )

        last_analysis_total_samples = 0

        try:
            while (
                self.wake_word_active
                and not self._closing
                and not self._stop_requested
            ):
                snapshot = self._consume_wake_audio()

                if snapshot is None:
                    threading.Event().wait(0.05)
                    continue

                current_total_samples = (
                    self._wake_total_samples
                )

                if (
                    last_analysis_total_samples > 0
                    and (
                        current_total_samples
                        - last_analysis_total_samples
                    ) < analysis_interval_samples
                ):
                    threading.Event().wait(0.05)
                    continue

                last_analysis_total_samples = (
                    current_total_samples
                )

                # The microphone remains OPEN during inference.
                text = self._analyze_continuous_wake_audio(
                    snapshot
                )

                if (
                    self._closing
                    or self._stop_requested
                    or not self.wake_word_active
                ):
                    return False

                if not text:
                    continue

                print(
                    f"DHEEPTHI Standby Input : "
                    f"{text}"
                )

                if self.contains_wake_word(text):
                    with self._wake_detection_lock:
                        if self._wake_detected:
                            return True

                        self._wake_detected = True

                    print(
                        "\n⚡ DHEEPTHI Wake Word Detected"
                    )
                    print(
                        f"Matched Transcript : {text}"
                    )
                    print(
                        "🛑 Breaking continuous "
                        "wake capture."
                    )

                    self.wake_word_active = False
                    return True

            return False

        finally:
            self.wake_word_active = False
            self._wake_standby_mode = False
            self._stop_wake_stream()

            print(
                "DHEEPTHI continuous "
                "wake listener stopped."
            )

    # ==================================================
    # COMPLETE WAKE -> COMMAND
    # ==================================================

    def listen_for_wake_command(
        self,
        retries=1,
    ):
        """
        Complete lifecycle:

        Continuous Faster-Whisper wake
                ↓
        DHEEPTHI detected
                ↓
        wake stream stopped
                ↓
        wake audio discarded
                ↓
        fresh command recording
                ↓
        Groq Whisper
        """

        if self._closing:
            return None

        if not self.load_model():
            return None

        self._stop_requested = False

        print(
            "\n========== DHEEPTHI =========="
        )
        print(
            "Wake Detection : Faster-Whisper LOCAL"
        )
        print(
            f"Wake Model : {self.WAKE_MODEL_NAME}"
        )
        print("Wake Capture : CONTINUOUS")
        print(
            "Mic stays open until "
            "DHEEPTHI is detected."
        )
        print(
            "Wake Matching : Dataset + Fuzzy"
        )
        print("Command STT : Groq Whisper")
        print("==============================")

        try:
            # ----------------------------------------------
            # STAGE 1 — continuous wake
            # ----------------------------------------------

            detected = self.listen_for_wake_word(
                retries=retries
            )

            if not detected:
                print(
                    "DHEEPTHI wake detection "
                    "stopped without detection."
                )
                return None

            if (
                self._closing
                or self._stop_requested
            ):
                return None

            # ----------------------------------------------
            # STAGE 2 — wake audio is discarded
            # ----------------------------------------------

            self._wake_standby_mode = False

            print(
                "\n========== COMMAND STAGE =========="
            )
            print("⚡ DHEEPTHI activated.")
            print("🗑️ Wake audio discarded.")
            print(
                "🎤 Starting FRESH command recording..."
            )
            print("🎙️ Speak your command...")

            # ----------------------------------------------
            # STAGE 3 — fresh command recording
            # ----------------------------------------------

            command = self.listen(
                retries=max(1, int(retries)),
                timeout=self.COMMAND_TIMEOUT,
                phrase_time_limit=(
                    self.COMMAND_PHRASE_TIME_LIMIT
                ),
                reset_stop=False,
                use_audio_meter=True,
            )

            if (
                self._closing
                or self._stop_requested
            ):
                return None

            if not command:
                print(
                    "❌ No command detected."
                )
                return None

            print(
                "\n========== DHEEPTHI COMMAND =========="
            )
            print(f"Command : {command}")
            print("========================================")

            return command

        finally:
            self._wake_standby_mode = False
            self.wake_word_active = False
            self._stop_wake_stream()

    # ==================================================
    # LISTEN AFTER WAKE
    # ==================================================

    def listen_after_wake_word(
        self,
        timeout=5,
        phrase_time_limit=20,
    ):
        self._stop_requested = False

        return self.listen(
            retries=1,
            timeout=timeout,
            phrase_time_limit=phrase_time_limit,
            reset_stop=False,
            use_audio_meter=True,
        )

    # ==================================================
    # LISTEN FOR COMMAND
    # ==================================================

    def listen_for_command(self):
        if self._closing:
            return None

        return self.listen_for_wake_command(
            retries=1
        )

    # ==================================================
    # STOP WAKE WORD
    # ==================================================

    def stop_wake_word(self):
        self._stop_requested = True
        self.wake_word_active = False
        self._wake_standby_mode = False

        try:
            self._stop_wake_stream()
        except Exception:
            pass

        self.stop_audio_meter()

        print(
            "DHEEPTHI Wake Word Mode stopped."
        )

    # ==================================================
    # PREPARE WAKE WORD
    # ==================================================

    def prepare_for_wake_word(self):
        if self._closing:
            return False

        if not self.load_model():
            return False

        self._stop_requested = False
        self.wake_word_active = True
        self._wake_standby_mode = True

        print(
            "DHEEPTHI Faster-Whisper "
            "continuous wake listener prepared."
        )

        return True

    # ==================================================
    # CONFIRMATION
    # ==================================================

    def listen_confirmation(
        self,
        retries=3,
    ):
        normalization = {
            "yep": "yes",
            "yup": "yes",
            "yeah": "yes",
            "yess": "yes",
            "yea": "yes",
            "you": "yes",
            "ok": "yes",
            "okay": "yes",
            "confirm": "yes",
            "sure": "yes",
            "correct": "yes",

            "nope": "no",
            "nah": "no",

            "cancel it": "cancel",
            "stop it": "stop",
        }

        for _ in range(max(1, int(retries))):
            text = self.listen(
                retries=1,
                timeout=self.COMMAND_TIMEOUT,
                phrase_time_limit=10,
                reset_stop=True,
                use_audio_meter=True,
            )

            if text is None:
                print(
                    "\nDidn't hear anything."
                )
                continue

            text = self.normalize_wake_text(text)

            for old, new in normalization.items():
                text = text.replace(old, new)

            if "yes" in text:
                return "yes"

            if "no" in text:
                return "no"

            if "cancel" in text:
                return "cancel"

            if "stop" in text:
                return "stop"

            print(
                "\nPlease say Yes, No or Cancel."
            )

        return None

    # ==================================================
    # LEVEL CALLBACK
    # ==================================================

    def set_level_callback(
        self,
        callback: Optional[Callable[[float], None]],
    ):
        self.level_callback = callback

    # ==================================================
    # CLEANUP
    # ==================================================

    def close(self):
        self._closing = True
        self._stop_requested = True
        self.wake_word_active = False
        self._wake_standby_mode = False

        try:
            self._stop_wake_stream()
        except Exception:
            pass

        try:
            sd.stop()
        except Exception:
            pass

        try:
            self.stop_audio_meter()
        except Exception:
            pass

        self.level_callback = None

        self.microphone = None
        self.recognizer = None

        self.model = None
        self._model_loaded = False

        groq = self.groq

        if groq is not None:
            try:
                groq.close()
            except Exception:
                pass

        self.groq = None

        print(
            "Speech Recognizer shutdown completed."
        )
