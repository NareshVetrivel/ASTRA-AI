"""
Whisper Speech Recognition Module

Offline Speech Recognition using Faster-Whisper.

DHEEPTHI Wake Word Support
---------------------------
DHEEPTHI is the AI assistant name.

Supported wake words:
    - dheepthi
    - hey dheepthi
    - okay dheepthi
    - ok dheepthi
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
        - Faster-Whisper transcription
        - Audio level monitoring
        - DHEEPTHI wake-word detection
        - Wake-word + command detection
        - Confirmation listening
    """

    def __init__(self):
        """
        Initialize Whisper model and microphone.
        """

        self.recognizer = sr.Recognizer()

        self.recognizer.dynamic_energy_threshold = True

        self.recognizer.energy_threshold = 180

        self.recognizer.dynamic_energy_adjustment_damping = 0.12

        self.recognizer.dynamic_energy_ratio = 1.5

        self.recognizer.pause_threshold = 0.55

        self.recognizer.non_speaking_duration = 0.35

        self.recognizer.operation_timeout = None

        self.microphone = sr.Microphone()

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

        # Used to interrupt active
        # microphone operations safely.
        self._stop_requested = False

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
        # Phrases that must NOT activate
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

        self.wake_word_active = False

    # ==================================================
    # Load Faster-Whisper Model
    # ==================================================

    def load_model(self):

        if self.model is not None:

            return

        try:

            print(
                "\nLoading Faster-Whisper model..."
            )

            self.model = WhisperModel(

                "base",

                device="cpu",

                compute_type="int8",

                cpu_threads=6,

                num_workers=1

            )

            print(
                "Whisper model loaded successfully."
            )

        except Exception as error:

            import traceback

            traceback.print_exc()

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
        time,
        status
    ):

        if status:

            print(
                f"Audio Status : {status}"
            )

        rms = np.sqrt(
            np.mean(
                np.square(indata)
            )
        )

        level = min(
            float(rms) * 22.0,
            1.0
        )

        # ---------------------------------
        # Smooth Audio Level
        # ---------------------------------

        self.audio_level = (

            self.audio_level * 0.75

            +

            level * 0.25

        )

        # ---------------------------------
        # Send Level To UI
        # ---------------------------------

        if self.level_callback is not None:

            self.level_callback(
                self.audio_level
            )

    # ==================================================
    # Start Audio Meter
    # ==================================================

    def start_audio_meter(self):

        if self._closing:

            return

        if self.audio_stream is not None:

            return

        try:

            self.audio_stream = sd.InputStream(

                channels=1,

                samplerate=16000,

                blocksize=512,

                dtype="float32",

                latency="low",

                callback=self._audio_callback

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

        if self.audio_stream is None:

            return

        try:

            self.audio_stream.stop()

            self.audio_stream.close()

        except Exception:

            pass

        finally:

            self.audio_stream = None

        self.audio_level = 0.0

        if self.level_callback is not None:

            self.level_callback(
                0.0
            )

    # ==================================================
    # Record Audio
    # ==================================================

    def record_audio(self):
        """
        Record audio from microphone safely.

        Uses a short microphone timeout so that the
        shutdown flag can be checked continuously.

        Returns
        -------
        str | None
            Path to temporary WAV file.
        """

        try:

            with self.microphone as source:

                print(
                    "🎤 Listening..."
                )

                self.start_audio_meter()

                # ---------------------------------
                # Ambient Noise Calibration
                # ---------------------------------

                if not hasattr(
                    self,
                    "_noise_calibrated"
                ):

                    self.recognizer.adjust_for_ambient_noise(

                        source,

                        duration=0.3

                    )

                    self.recognizer.energy_threshold = max(

                        150,

                        int(
                            self.recognizer.energy_threshold
                            * 0.85
                        )

                    )

                    self._noise_calibrated = True

                # ---------------------------------
                # Stop Check Before Listening
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
                # Wait for Speech
                #
                # IMPORTANT:
                # timeout=1 prevents the microphone
                # from blocking forever.
                # ---------------------------------

                audio = None

                while (

                    not self._closing

                    and

                    not self._stop_requested

                ):

                    try:

                        audio = self.recognizer.listen(

                            source,

                            timeout=1,

                            phrase_time_limit=6

                        )

                        # ---------------------------------
                        # Speech captured
                        # ---------------------------------

                        break

                    except sr.WaitTimeoutError:

                        # ---------------------------------
                        # No speech during this 1-second
                        # window.
                        #
                        # Loop again so shutdown flags
                        # can be checked.
                        # ---------------------------------

                        continue

                # ---------------------------------
                # Shutdown / Stop Requested
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

                # ---------------------------------
                # Safety Check
                # ---------------------------------

                if audio is None:

                    return None

                print(
                    "Audio captured successfully."
                )

                print(
                    "Audio Bytes :",
                    len(
                        audio.frame_data
                    )
                )

            # ---------------------------------
            # Save Temporary Audio
            # ---------------------------------

            temp_file = os.path.abspath(
                "temp_audio.wav"
            )

            with open(
                temp_file,
                "wb"
            ) as file:

                file.write(
                    audio.get_wav_data()
                )

            self.last_audio = temp_file

            return temp_file

        except Exception as error:

            print(
                f"Audio Recording Error : {error}"
            )

            return None

        finally:

            self.stop_audio_meter()

    # ==================================================
    # Faster-Whisper Listen
    # ==================================================

    def listen(
        self,
        retries=1
    ):
        """
        Listen from microphone and convert
        speech into text using Faster-Whisper.

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

                if audio_file:

                    print(
                        "File Size :",
                        os.path.getsize(
                            audio_file
                        )
                    )

                if audio_file is None:

                    continue

                print(
                    "🧠 Transcribing..."
                )

                segments, _ = (
                    self.model.transcribe(

                        audio_file,

                        language="en",

                        beam_size=1,

                        best_of=1,

                        vad_filter=True,

                        vad_parameters={

                            "min_silence_duration_ms": 180,

                            "speech_pad_ms": 120,

                            "threshold": 0.45

                        },

                        condition_on_previous_text=False,

                        temperature=0.0,

                        word_timestamps=False

                    )
                )

                text = " ".join(

                    segment.text.strip()

                    for segment in segments

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

                if text:

                    text = (

                        text

                        .replace(
                            "  ",
                            " "
                        )

                        .replace(
                            " ,",
                            ","
                        )

                        .replace(
                            " .",
                            "."
                        )

                        .replace(
                            " ?",
                            "?"
                        )

                        .replace(
                            " !",
                            "!"
                        )

                        .strip()

                    )

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

                    f"No speech detected. Retry "

                    f"{attempt + 1}/{retries}"

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

            return None

        except Exception as error:

            self.stop_audio_meter()

            print(
                f"\nWhisper Error : {error}"
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

    # ==================================================
    # Normalize Wake Word Text
    # ==================================================

    def normalize_wake_text(
        self,
        text
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
                ""
            )

            .replace(
                ",",
                ""
            )

            .replace(
                "?",
                ""
            )

            .replace(
                "!",
                ""
            )

        )

    # ==================================================
    # Wake Word Similarity
    # ==================================================

    def wake_word_similarity(
        self,
        word
    ):
        """
        Calculate similarity between a Whisper-generated
        word and the DHEEPTHI pronunciation family.

        This is intentionally used only for wake-word
        candidates, not for normal command detection.
        """

        if not word:

            return 0.0

        word = (
            word
            .lower()
            .strip()
            .replace("-", "")
            .replace("_", "")
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
                candidate
            ).ratio()

            if score > best_score:

                best_score = score

        return best_score

    # ==================================================
    # Check DHEEPTHI Wake Word
    # ==================================================

    def contains_wake_word(
        self,
        text
    ):
        """
        Strong DHEEPTHI wake-word detection.

        Handles:
            dheepthi
            deepthi
            deepti
            deepthee
            deep the
            deep tea
            deeply
            deep please
            deep t
            deep deep wake up
            deepdeep make up

        Normal phrases such as:
            deep sleep
            deep thought
            deep water

        are rejected to reduce false activation.
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

                # Do not accept if the complete
                # phrase is an explicitly rejected
                # normal expression.

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

            # Ignore very short words.
            if len(word) < 5:

                continue

            score = (
                self.wake_word_similarity(
                    word
                )
            )

            # High similarity threshold.
            #
            # This catches things like:
            #
            # deepthee
            # deepthi
            # deeply
            # deeptee
            #
            # without accepting "deep" alone.

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

            # ---------------------------------
            # Deep + pronunciation endings
            # ---------------------------------

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

            # ---------------------------------
            # "deep deep wake up"
            # ---------------------------------

            if (
                "wake" in remaining
                or
                "up" in remaining
            ):

                return True

            # ---------------------------------
            # "deep deep make up"
            # ---------------------------------

            if (
                "make" in remaining
                and
                "up" in remaining
            ):

                return True

        # ---------------------------------
        # "deepdeep" / joined transcription
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
        text
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
            reverse=True
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
            # Fuzzy first-word wake detection
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
        retries=1
    ):
        """
        Continuously listen for DHEEPTHI.

        Returns
        -------
        bool
            True when DHEEPTHI is detected.
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
        retries=1
    ):
        """
        Listen for DHEEPTHI and return
        the command.

        Supports:

            "Dheepthi"

        followed by:

            "Start screen recording"

        And:

            "Dheepthi start screen recording"

        Returns
        -------
        str | None
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
        self
    ):
        """
        Stop DHEEPTHI wake-word listening
        and request the active microphone operation
        to terminate as soon as possible.
        """

        # ---------------------------------
        # Stop Wake Loop
        # ---------------------------------

        self.wake_word_active = False

        # ---------------------------------
        # Request Current Recording Stop
        # ---------------------------------

        self._stop_requested = True

        # ---------------------------------
        # Stop Audio Meter
        # ---------------------------------

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
        retries=3
    ):
        """
        Listen for:

        Yes

        No

        Cancel

        Returns
        -------
        str | None
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
                    ""
                )

                .replace(
                    ",",
                    ""
                )

                .replace(
                    "!",
                    ""
                )

                .replace(
                    "?",
                    ""
                )

            )

            # ---------------------------------
            # Common Whisper Mistakes
            # ---------------------------------

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

                "stop it": "stop"

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

        This method is called during application shutdown.
        """

        # ---------------------------------
        # Prevent new microphone operations
        # ---------------------------------

        self._closing = True

        # ---------------------------------
        # Stop Wake Word Loop
        # ---------------------------------

        self.wake_word_active = False

        # ---------------------------------
        # Request Active Recording Stop
        # ---------------------------------

        self._stop_requested = True

        # ---------------------------------
        # Stop Audio Meter
        # ---------------------------------

        try:

            self.stop_audio_meter()

        except Exception:

            pass

        # ---------------------------------
        # Remove UI Callback
        # ---------------------------------

        self.level_callback = None

        # ---------------------------------
        # Release Microphone
        # ---------------------------------

        self.microphone = None

        # ---------------------------------
        # Release Recognizer
        # ---------------------------------

        self.recognizer = None

        print(
            "Whisper Recognizer shutdown completed."
        )