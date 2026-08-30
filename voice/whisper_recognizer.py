"""
Whisper Speech Recognition Module

Offline Speech Recognition using Faster-Whisper.

DHEEPTHI Wake Word Support
---------------------------
DHEEPTHI is the AI assistant name.

This module handles:

    - Microphone recording
    - Natural speech capture
    - Silence / pause handling
    - Faster-Whisper transcription
    - Audio level monitoring
    - DHEEPTHI wake-word detection
    - Wake-word + command detection
    - Confirmation listening

Performance target:

    Intel i5
    8 GB RAM

The module is intentionally kept compatible with
the existing ASTRA-AI voice architecture.
"""

from __future__ import annotations

import os
import re
from difflib import SequenceMatcher

import numpy as np
import sounddevice as sd
import speech_recognition as sr

from faster_whisper import WhisperModel


class WhisperRecognizer:
    """
    Offline Speech Recognition using Faster-Whisper.

    Handles:

        - Microphone recording
        - Natural command capture
        - Ambient noise calibration
        - Silence detection
        - Faster-Whisper transcription
        - Audio level monitoring
        - DHEEPTHI wake-word detection
        - Wake-word + command detection
        - Confirmation listening
    """

    # ==================================================
    # Performance / Recording Configuration
    # ==================================================

    # Maximum duration of one spoken command.
    #
    # This replaces the old 6-second hard cutoff.
    MAX_PHRASE_SECONDS = 20

    # SpeechRecognition uses pause_threshold to decide when
    # the user has stopped speaking.
    #
    # Slightly higher value allows natural pauses.
    PAUSE_THRESHOLD = 0.75

    # Minimum amount of speech before SpeechRecognition
    # considers the phrase valid.
    PHRASE_THRESHOLD = 0.30

    # Amount of silence retained around speech.
    NON_SPEAKING_DURATION = 0.40

    # Initial ambient calibration duration.
    AMBIENT_CALIBRATION_SECONDS = 0.40

    # Minimum accepted energy threshold.
    MIN_ENERGY_THRESHOLD = 120

    # Maximum accepted energy threshold.
    MAX_ENERGY_THRESHOLD = 900

    # Faster-Whisper model.
    #
    # "base" + int8 is suitable for an i5 + 8 GB machine.
    WHISPER_MODEL = "base"

    # CPU configuration.
    CPU_THREADS = 4
    NUM_WORKERS = 1

    # ==================================================
    # Initialization
    # ==================================================

    def __init__(self):
        """
        Initialize Faster-Whisper and microphone resources.
        """

        self.recognizer = sr.Recognizer()

        # ---------------------------------
        # Dynamic Energy
        # ---------------------------------

        self.recognizer.dynamic_energy_threshold = True

        self.recognizer.energy_threshold = 180

        self.recognizer.dynamic_energy_adjustment_damping = 0.12

        self.recognizer.dynamic_energy_ratio = 1.5

        # ---------------------------------
        # Natural Speech Settings
        # ---------------------------------

        self.recognizer.pause_threshold = (
            self.PAUSE_THRESHOLD
        )

        self.recognizer.phrase_threshold = (
            self.PHRASE_THRESHOLD
        )

        self.recognizer.non_speaking_duration = (
            self.NON_SPEAKING_DURATION
        )

        self.recognizer.operation_timeout = None

        # ---------------------------------
        # Microphone
        # ---------------------------------

        self.microphone = sr.Microphone()

        # ---------------------------------
        # Faster-Whisper
        # ---------------------------------

        self.model = None

        # ---------------------------------
        # Real-Time Audio Level
        # ---------------------------------

        self.audio_level = 0.0

        self.audio_stream = None

        # ---------------------------------
        # UI Callback
        # ---------------------------------

        self.level_callback = None

        # ---------------------------------
        # Cleanup / Stop Control
        # ---------------------------------

        self._closing = False

        self._stop_requested = False

        self._noise_calibrated = False

        self.last_audio = None

        # ---------------------------------
        # DHEEPTHI Wake Word Variations
        # ---------------------------------

        self.wake_words = (

            # Strong / exact variants
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

            # Common Whisper word splitting
            "deep the",
            "deep thee",
            "deep tea",
            "deep thi",
            "deep tee",
            "deep ti",

            "dheep the",
            "dheep thee",
            "dheep tea",
            "dheep thi",
            "dheep tee",
            "dheep ti",

            # Common initial sound mistakes
            "beep the",
            "weep the",

            # Natural wake phrases
            "hey dheepthi",
            "hey deepthi",
            "hey deepti",
            "hey deepthee",

            "okay dheepthi",
            "okay deepthi",
            "okay deepti",

            "ok dheepthi",
            "ok deepthi",
            "ok deepti",
        )

        # ---------------------------------
        # Observed Faster-Whisper Phrases
        # ---------------------------------

        self.wake_phrase_variations = (

            "deeply",
            "deep please",
            "deep t",
            "deep ti",
            "deep thi",
            "deep thee",
            "deep tee",

            "deep deep wake up",
            "deepdeep wake up",
            "deep deep make up",
            "deepdeep make up",

            "deep-d",
            "deep d",
        )

        # ---------------------------------
        # Phrases That Must NOT Activate
        # ---------------------------------

        self.wake_reject_phrases = (

            "deep sleep",
            "sleep deeply",
            "deep thought",
            "deep thoughts",
            "deep water",
            "deep voice",
            "deep breath",
            "deep breathing",
        )

        self.wake_word_active = False

    # ==================================================
    # Load Faster-Whisper Model
    # ==================================================

    def load_model(self):
        """
        Load Faster-Whisper lazily.
        """

        if self.model is not None:

            return

        try:

            print(
                "\nLoading Faster-Whisper model..."
            )

            self.model = WhisperModel(

                self.WHISPER_MODEL,

                device="cpu",

                compute_type="int8",

                cpu_threads=self.CPU_THREADS,

                num_workers=self.NUM_WORKERS,
            )

            print(
                "Whisper model loaded successfully."
            )

        except Exception as error:

            print(
                f"Whisper Load Error : {error}"
            )

            raise

    # ==================================================
    # Real-Time Audio Meter
    # ==================================================

    def _audio_callback(
        self,
        indata,
        frames,
        time_info,
        status,
    ):
        """
        Update the UI audio-level meter.

        The callback intentionally does very little work so
        that it does not block the PortAudio callback thread.
        """

        if status:

            # Input overflow is diagnostic information.
            # Do not crash the recorder because of it.
            print(
                f"Audio Status : {status}"
            )

        try:

            if indata is None:

                return

            if len(indata) == 0:

                return

            rms = np.sqrt(
                np.mean(
                    np.square(indata)
                )
            )

            level = min(
                float(rms) * 22.0,
                1.0,
            )

            # Smooth UI level.
            self.audio_level = (

                self.audio_level * 0.80

                +

                level * 0.20
            )

            if self.level_callback is not None:

                try:

                    self.level_callback(
                        self.audio_level
                    )

                except Exception:

                    pass

        except Exception:

            pass

    # ==================================================
    # Start Audio Meter
    # ==================================================

    def start_audio_meter(self):
        """
        Start the optional UI audio meter.

        The meter is deliberately lightweight.
        """

        if self._closing:

            return

        if self.audio_stream is not None:

            return

        try:

            self.audio_stream = sd.InputStream(

                channels=1,

                samplerate=16000,

                blocksize=1024,

                dtype="float32",

                # Higher latency is safer on a modest
                # CPU and reduces callback pressure.
                latency="high",

                callback=self._audio_callback,
            )

            self.audio_stream.start()

        except Exception as error:

            print(
                f"Audio Meter Error : {error}"
            )

            self.audio_stream = None

    # ==================================================
    # Stop Audio Meter
    # ==================================================

    def stop_audio_meter(self):
        """
        Stop the UI audio meter safely.
        """

        if self.audio_stream is None:

            return

        try:

            self.audio_stream.stop()

        except Exception:

            pass

        try:

            self.audio_stream.close()

        except Exception:

            pass

        finally:

            self.audio_stream = None

        self.audio_level = 0.0

        if self.level_callback is not None:

            try:

                self.level_callback(
                    0.0
                )

            except Exception:

                pass

    # ==================================================
    # Microphone Calibration
    # ==================================================

    def _calibrate_microphone(
        self,
        source,
    ):
        """
        Perform ambient-noise calibration once.

        Calibration is intentionally short so the user does
        not experience a long delay every time they speak.
        """

        if self._noise_calibrated:

            return

        try:

            print(
                "🎧 Calibrating microphone..."
            )

            self.recognizer.adjust_for_ambient_noise(

                source,

                duration=self.AMBIENT_CALIBRATION_SECONDS,
            )

            calibrated_threshold = int(
                self.recognizer.energy_threshold
            )

            calibrated_threshold = max(

                self.MIN_ENERGY_THRESHOLD,

                min(
                    calibrated_threshold,
                    self.MAX_ENERGY_THRESHOLD,
                ),
            )

            self.recognizer.energy_threshold = (
                calibrated_threshold
            )

            self._noise_calibrated = True

            print(
                "🎧 Microphone calibrated."
            )

            print(
                f"Energy Threshold : "
                f"{self.recognizer.energy_threshold}"
            )

        except Exception as error:

            print(
                f"Microphone Calibration Error : "
                f"{error}"
            )

    # ==================================================
    # Record Audio
    # ==================================================

    def record_audio(self):
        """
        Record one complete natural speech phrase.

        The old implementation used:

            phrase_time_limit=6

        which could cut long commands.

        This implementation uses:

            - pause_threshold
            - phrase_threshold
            - non_speaking_duration
            - 20-second maximum phrase limit

        Therefore the user can naturally pause while speaking,
        while SpeechRecognition still ends the phrase after
        sufficient silence.

        Returns
        -------
        str | None
            Path to temporary WAV file.
        """

        audio = None

        try:

            if self.microphone is None:

                print(
                    "Microphone is unavailable."
                )

                return None

            with self.microphone as source:

                print(
                    "🎤 Listening..."
                )

                # ---------------------------------
                # Calibration
                # ---------------------------------

                self._calibrate_microphone(
                    source
                )

                # ---------------------------------
                # Stop Check
                # ---------------------------------

                if (

                    self._closing

                    or

                    self._stop_requested
                ):

                    print(
                        "Recording cancelled before capture."
                    )

                    return None

                # ---------------------------------
                # Audio Meter
                #
                # Start AFTER calibration so the
                # calibration period does not generate
                # unnecessary UI/audio-stream pressure.
                # ---------------------------------

                self.start_audio_meter()

                # ---------------------------------
                # Natural Phrase Capture
                # ---------------------------------

                print(
                    "🎙️ Speak your command..."
                )

                audio = self.recognizer.listen(

                    source,

                    timeout=None,

                    phrase_time_limit=(
                        self.MAX_PHRASE_SECONDS
                    ),
                )

                # ---------------------------------
                # Stop Check
                # ---------------------------------

                if (

                    self._closing

                    or

                    self._stop_requested
                ):

                    print(
                        "Recording stopped by shutdown request."
                    )

                    return None

                if audio is None:

                    print(
                        "No audio captured."
                    )

                    return None

                frame_data = audio.frame_data

                if not frame_data:

                    print(
                        "Captured audio is empty."
                    )

                    return None

                print(
                    "Audio captured successfully."
                )

                print(
                    "Audio Bytes :",
                    len(frame_data),
                )

            # ---------------------------------
            # Save WAV
            # ---------------------------------

            temp_file = os.path.abspath(
                "temp_audio.wav"
            )

            try:

                with open(
                    temp_file,
                    "wb",
                ) as file:

                    file.write(
                        audio.get_wav_data()
                    )

            except Exception as error:

                print(
                    f"Audio File Write Error : "
                    f"{error}"
                )

                return None

            self.last_audio = temp_file

            print(
                "Audio File :",
                temp_file,
            )

            try:

                print(
                    "File Size :",
                    os.path.getsize(
                        temp_file
                    ),
                )

            except Exception:

                pass

            return temp_file

        except sr.WaitTimeoutError:

            print(
                "Microphone listening timed out."
            )

            return None

        except OSError as error:

            print(
                f"Microphone / Audio Device Error : "
                f"{error}"
            )

            return None

        except Exception as error:

            print(
                f"Audio Recording Error : "
                f"{error}"
            )

            return None

        finally:

            self.stop_audio_meter()

    # ==================================================
    # Repetitive Garbage Detection
    # ==================================================

    @staticmethod
    def _is_repetitive_garbage(
        text: str,
    ) -> bool:
        """
        Detect obvious ASR hallucination/repetition.

        Examples:

            a a a a a a a
            a-a-a-a-a-a
            the the the the the

        This is deliberately conservative.
        """

        if not text:

            return True

        words = re.findall(
            r"[a-z]+",
            text.lower(),
        )

        if len(words) < 5:

            return False

        unique_words = set(words)

        # Entire transcript is one repeated word.
        if len(unique_words) == 1:

            return True

        counts: dict[str, int] = {}

        for word in words:

            counts[word] = (
                counts.get(word, 0) + 1
            )

        highest_count = max(
            counts.values()
        )

        # Extremely dominant repeated token.
        if (

            highest_count >= 8

            and

            highest_count / len(words) >= 0.80
        ):

            return True

        return False

    # ==================================================
    # Faster-Whisper Listen
    # ==================================================

    def listen(
        self,
        retries=1,
    ):
        """
        Record microphone audio and transcribe using
        Faster-Whisper.

        Returns
        -------
        str | None
        """

        audio_file = None

        # ---------------------------------
        # Reset transient stop request
        # ---------------------------------

        if not self._closing:

            self._stop_requested = False

        try:

            if self.model is None:

                print(
                    "Whisper model is not loaded."
                )

                return None

            for attempt in range(
                retries
            ):

                audio_file = (
                    self.record_audio()
                )

                print(
                    "Audio File :",
                    audio_file
                )

                if audio_file is None:

                    continue

                if not os.path.exists(
                    audio_file
                ):

                    print(
                        "Audio file does not exist."
                    )

                    continue

                try:

                    print(
                        "File Size :",
                        os.path.getsize(
                            audio_file
                        )
                    )

                except Exception:

                    pass

                # ---------------------------------
                # Transcription
                # ---------------------------------

                print(
                    "🧠 Transcribing..."
                )

                segments, _ = (
                    self.model.transcribe(

                        audio_file,

                        language="en",

                        # Better decoding than the previous
                        # beam_size=1 configuration.
                        beam_size=3,

                        best_of=3,

                        # VAD removes non-speech portions.
                        vad_filter=True,

                        vad_parameters={

                            "min_silence_duration_ms": 350,

                            "speech_pad_ms": 180,

                            "threshold": 0.45,
                        },

                        # Prevent previous transcript context
                        # from influencing the next command.
                        condition_on_previous_text=False,

                        temperature=0.0,

                        word_timestamps=False,
                    )
                )

                text = " ".join(

                    segment.text.strip()

                    for segment
                    in segments

                    if segment.text.strip()
                )

                text = " ".join(
                    text.split()
                )

                print(
                    "\n========== DEBUG =========="
                )

                print(
                    f"Recognized Text : {text}"
                )

                print(
                    "===========================\n"
                )

                # ---------------------------------
                # Normalize Transcript
                # ---------------------------------

                if text:

                    text = (

                        text

                        .replace(
                            "  ",
                            " ",
                        )

                        .replace(
                            " ,",
                            ",",
                        )

                        .replace(
                            " .",
                            ".",
                        )

                        .replace(
                            " ?",
                            "?",
                        )

                        .replace(
                            " !",
                            "!",
                        )

                        .strip()
                    )

                    # ---------------------------------
                    # Garbage Protection
                    # ---------------------------------

                    if self._is_repetitive_garbage(
                        text
                    ):

                        print(
                            "Rejected repetitive ASR "
                            "garbage."
                        )

                        text = ""

                    if text:

                        try:

                            os.remove(
                                audio_file
                            )

                        except Exception:

                            pass

                        return (
                            text
                            .strip()
                            .lower()
                        )

                print(
                    f"No valid speech detected. "
                    f"Retry {attempt + 1}/{retries}"
                )

                try:

                    if os.path.exists(
                        audio_file
                    ):

                        os.remove(
                            audio_file
                        )

                except Exception:

                    pass

                audio_file = None

            return None

        except Exception as error:

            self.stop_audio_meter()

            print(
                f"\nWhisper Error :",
                error
            )

            try:

                if (

                    audio_file

                    and

                    os.path.exists(
                        audio_file
                    )
                ):

                    os.remove(
                        audio_file
                    )

            except Exception:

                pass

            return None

        finally:

            self.stop_audio_meter()

    # ==================================================
    # Normalize Wake Word Text
    # ==================================================

    def normalize_wake_text(
        self,
        text,
    ):
        """
        Normalize text for DHEEPTHI detection.
        """

        if not text:

            return ""

        return (

            text

            .lower()

            .strip()

            .replace(
                ".",
                "",
            )

            .replace(
                ",",
                "",
            )

            .replace(
                "?",
                "",
            )

            .replace(
                "!",
                "",
            )
        )

    # ==================================================
    # Wake Word Similarity
    # ==================================================

    def wake_word_similarity(
        self,
        word,
    ):
        """
        Calculate similarity between a recognized word
        and the DHEEPTHI pronunciation family.
        """

        if not word:

            return 0.0

        word = (

            word

            .lower()

            .strip()

            .replace(
                "-",
                "",
            )

            .replace(
                "_",
                "",
            )
        )

        candidates = (

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

        best_score = 0.0

        for candidate in candidates:

            score = SequenceMatcher(

                None,

                word,

                candidate,
            ).ratio()

            if score > best_score:

                best_score = score

        return best_score

    # ==================================================
    # Check DHEEPTHI Wake Word
    # ==================================================

    def contains_wake_word(
        self,
        text,
    ):
        """
        Strong DHEEPTHI wake-word detection.
        """

        normalized = (
            self.normalize_wake_text(
                text
            )
        )

        if not normalized:

            return False

        # ---------------------------------
        # Reject obvious normal phrases
        # ---------------------------------

        for phrase in self.wake_reject_phrases:

            if normalized == phrase:

                return False

        # ---------------------------------
        # Exact known wake words
        # ---------------------------------

        for wake_word in self.wake_words:

            if wake_word in normalized:

                return True

        # ---------------------------------
        # Observed Whisper phrases
        # ---------------------------------

        for phrase in self.wake_phrase_variations:

            if phrase in normalized:

                if normalized in self.wake_reject_phrases:

                    return False

                return True

        # ---------------------------------
        # Tokenize
        # ---------------------------------

        words = re.findall(
            r"[a-z]+",
            normalized
        )

        if not words:

            return False

        # ---------------------------------
        # Fuzzy single-word detection
        # ---------------------------------

        for word in words:

            if len(word) < 5:

                continue

            score = (
                self.wake_word_similarity(
                    word
                )
            )

            if score >= 0.78:

                return True

        # ---------------------------------
        # "deep" based Whisper phrases
        # ---------------------------------

        if "deep" in words:

            deep_index = words.index(
                "deep"
            )

            remaining = words[
                deep_index + 1:
            ]

            allowed_following_words = {

                "the",
                "thee",
                "tea",
                "thi",
                "tee",
                "ti",
                "t",
                "please",
                "d",
            }

            if remaining:

                first_following = (
                    remaining[0]
                )

                if (
                    first_following
                    in
                    allowed_following_words
                ):

                    return True

            if (

                "wake" in remaining

                or

                "up" in remaining
            ):

                return True

            if (

                "make" in remaining

                and

                "up" in remaining
            ):

                return True

        # ---------------------------------
        # Joined transcription
        # ---------------------------------

        joined_candidates = (

            "deepdeep",
            "deepdee",
            "deepthi",
            "deepthee",
        )

        for candidate in joined_candidates:

            if candidate in normalized:

                return True

        return False

    # ==================================================
    # Remove DHEEPTHI Wake Word
    # ==================================================

    def remove_wake_word(
        self,
        text,
    ):
        """
        Remove DHEEPTHI and known Whisper wake-word
        variations from the beginning of a command.
        """

        if not text:

            return ""

        original = text.strip()

        normalized = (
            self.normalize_wake_text(
                original
            )
        )

        # ---------------------------------
        # Multi-word prefixes
        # ---------------------------------

        prefixes = (

            "hey dheepthi",
            "hey deepthi",
            "hey deepti",
            "hey deepthee",

            "okay dheepthi",
            "okay deepthi",
            "okay deepti",

            "ok dheepthi",
            "ok deepthi",
            "ok deepti",

            "deep deep wake up",
            "deepdeep wake up",

            "deep deep make up",
            "deepdeep make up",

            "deep please",

            "deep the",
            "deep thee",
            "deep tea",
            "deep thi",
            "deep tee",
            "deep ti",
            "deep t",
            "deep d",

            "dheep the",
            "dheep thee",
            "dheep tea",
            "dheep thi",
            "dheep tee",
            "dheep ti",

            "beep the",
            "weep the",
        )

        # ---------------------------------
        # Longest prefix first
        # ---------------------------------

        prefixes = sorted(
            prefixes,
            key=len,
            reverse=True,
        )

        for prefix in prefixes:

            if normalized.startswith(
                prefix
            ):

                words = original.split()

                prefix_count = len(
                    prefix.split()
                )

                return " ".join(
                    words[
                        prefix_count:
                    ]
                ).strip()

        # ---------------------------------
        # Single-word wake variants
        # ---------------------------------

        single_words = (

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
            "deeply",
        )

        words = original.split()

        if words:

            first_word = (
                words[0]
                .lower()
                .strip(
                    ".,!?-_"
                )
            )

            if first_word in single_words:

                return " ".join(
                    words[1:]
                ).strip()

            # ---------------------------------
            # Fuzzy first-word detection
            # ---------------------------------

            if len(first_word) >= 5:

                score = (
                    self.wake_word_similarity(
                        first_word
                    )
                )

                if score >= 0.78:

                    return " ".join(
                        words[1:]
                    ).strip()

        return original

    # ==================================================
    # Listen For DHEEPTHI
    # ==================================================

    def listen_for_wake_word(
        self,
        retries=1,
    ):
        """
        Continuously listen for DHEEPTHI.
        """

        self.wake_word_active = True

        print(
            "\n🟢 DHEEPTHI Wake Word Mode Active"
        )

        while (

            self.wake_word_active

            and

            not self._closing
        ):

            text = self.listen(
                retries=retries
            )

            if not text:

                continue

            print(
                f"Wake Word Input : {text}"
            )

            if self.contains_wake_word(
                text
            ):

                print(
                    "⚡ DHEEPTHI Wake Word Detected"
                )

                return True

        return False

    # ==================================================
    # Listen For Wake Word + Command
    # ==================================================

    def listen_for_wake_command(
        self,
        retries=1,
    ):
        """
        Listen for DHEEPTHI and return the command.

        Supports:

            "Dheepthi"

        followed by:

            "Start screen recording"

        And:

            "Dheepthi start screen recording"
        """

        self.wake_word_active = True

        while (

            self.wake_word_active

            and

            not self._closing
        ):

            text = self.listen(
                retries=retries
            )

            if not text:

                continue

            print(
                f"DHEEPTHI Wake Input : {text}"
            )

            if not self.contains_wake_word(
                text
            ):

                continue

            print(
                "⚡ DHEEPTHI Activated"
            )

            # ---------------------------------
            # Same Sentence Command
            # ---------------------------------

            command = (
                self.remove_wake_word(
                    text
                )
            )

            if command:

                print(
                    f"DHEEPTHI Command : "
                    f"{command}"
                )

                return command

            # ---------------------------------
            # Wake Word Only
            # ---------------------------------

            print(
                "🎤 DHEEPTHI is listening "
                "for your command..."
            )

            command = self.listen(
                retries=retries
            )

            if command:

                print(
                    f"DHEEPTHI Command : "
                    f"{command}"
                )

                return command

            print(
                "No command detected."
            )

        return None

    # ==================================================
    # Stop Wake Word Mode
    # ==================================================

    def stop_wake_word(
        self,
    ):
        """
        Stop DHEEPTHI wake-word listening and request
        active microphone operations to terminate.
        """

        self.wake_word_active = False

        self._stop_requested = True

        try:

            self.stop_audio_meter()

        except Exception:

            pass

        print(
            "DHEEPTHI Wake Word Mode stopped."
        )

    # ==================================================
    # Listen For Confirmation
    # ==================================================

    def listen_confirmation(
        self,
        retries=3,
    ):
        """
        Listen for:

            Yes
            No
            Cancel
            Stop
        """

        for _ in range(
            retries
        ):

            text = self.listen()

            if text is None:

                print(
                    "\nDidn't hear anything."
                )

                continue

            text = (

                text

                .lower()

                .strip()

                .replace(
                    ".",
                    "",
                )

                .replace(
                    ",",
                    "",
                )

                .replace(
                    "!",
                    "",
                )

                .replace(
                    "?",
                    "",
                )
            )

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

            for old, new in (
                normalization.items()
            ):

                text = text.replace(
                    old,
                    new
                )

            if "yes" in text:

                return "yes"

            if "no" in text:

                return "no"

            if "cancel" in text:

                return "cancel"

            if "stop" in text:

                return "stop"

            print(
                "\nPlease say"
            )

            print(
                "Yes, No or Cancel."
            )

        return None

    # ==================================================
    # Cleanup
    # ==================================================

    def close(self):
        """
        Release microphone resources safely.
        """

        self._closing = True

        self.wake_word_active = False

        self._stop_requested = True

        try:

            self.stop_audio_meter()

        except Exception:

            pass

        self.level_callback = None

        self.microphone = None

        self.recognizer = None

        print(
            "Whisper Recognizer shutdown completed."
        )