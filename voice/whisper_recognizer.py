"""
Whisper Speech Recognition Module

Offline Speech Recognition using Faster-Whisper.
"""

import os

import numpy as np
import sounddevice as sd

import speech_recognition as sr

from faster_whisper import WhisperModel


class WhisperRecognizer:
    """
    Offline Speech Recognition using Faster-Whisper.
    """

    def __init__(self):
        """
        Initialize Whisper model and microphone.
        """

        self.recognizer = sr.Recognizer()

        self.recognizer.dynamic_energy_threshold = True
        self.recognizer.energy_threshold = 250
        self.recognizer.pause_threshold = 0.8
        self.recognizer.non_speaking_duration = 0.5

        self.microphone = sr.Microphone()

        self.model = None

        # ---------------------------------
        # Real-Time Audio Level
        # ---------------------------------

        self.audio_level = 0.0

        self.audio_stream = None

        # UI callback
        self.level_callback = None

        # Cleanup Flag
        self._closing = False

    def load_model(self):

        if self.model is not None:

            return

        try:

            print("\nLoading Faster-Whisper model...")

            self.model = WhisperModel(

                "base",

                device="cpu",

                compute_type="int8"

            )

            print("Whisper model loaded successfully.")

        except Exception as error:

            import traceback

            traceback.print_exc()

            print(

                f"Whisper Load Error : {error}"

            )

            raise

    # --------------------------------------------------
    # Real-Time Audio Meter
    # --------------------------------------------------

    def _audio_callback(
        self,
        indata,
        frames,
        time,
        status
    ):

        if status:

            print(f"Audio Status : {status}")

        rms = np.sqrt(
            np.mean(
                np.square(indata)
            )
        )

        level = min(
            float(rms) * 15.0,
            1.0
        )

        # Smooth the audio level
        self.audio_level = (
            self.audio_level * 0.75
            +
            level * 0.25
        )

        # Send level to UI
        if self.level_callback is not None:
            self.level_callback(self.audio_level)


    # --------------------------------------------------
    # Start Audio Meter
    # --------------------------------------------------

    def start_audio_meter(self):

        if self._closing:
            return

        if self.audio_stream is not None:
            return

        try:

            self.audio_stream = sd.InputStream(

                channels=1,

                samplerate=16000,

                callback=self._audio_callback

            )

            self.audio_stream.start()

        except Exception as error:

            print(

                f"Audio Meter Error : {error}"

            )

            self.audio_stream = None


    # --------------------------------------------------
    # Stop Audio Meter
    # --------------------------------------------------

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
            self.level_callback(0.0)

    def record_audio(self):
        """
        Record audio from microphone.

        Returns:
            str | None
        """

        try:

            with self.microphone as source:

                print("🎤 Listening...")

                self.start_audio_meter()

                if not hasattr(self, "_noise_calibrated"):

                    self.recognizer.adjust_for_ambient_noise(
                        source,
                        duration=0.3
                    )

                    self._noise_calibrated = True

                audio = self.recognizer.listen(
                    source,
                    timeout=None,
                    phrase_time_limit=8
                )

                print("Audio captured successfully.")
                print("Audio Bytes :", len(audio.frame_data))

            temp_file = os.path.abspath(
                "temp_audio.wav"
            )

            with open(temp_file, "wb") as file:
                file.write(audio.get_wav_data())

            self.last_audio = temp_file

            return temp_file

        except sr.WaitTimeoutError:

            print("\nListening Timeout.")
            return None

        finally:

            self.stop_audio_meter()

    def listen(
        self,
        retries=1
    ):
        """
        Listen from microphone and convert
        speech into text.

        Returns:
            str | None
        """

        audio_file = None

        try:

            if self.model is None:

                print("Whisper model is not loaded.")

                return None

            for attempt in range(retries):

                audio_file = self.record_audio()

                print("Audio File :", audio_file)

                if audio_file:

                    print(
                        "File Size :",
                        os.path.getsize(audio_file)
                    )

                if audio_file is None:

                    continue

                print("🧠 Transcribing...")

                segments, _ = self.model.transcribe(

                    audio_file,

                    beam_size=1,

                    language="en",

                    vad_filter=True,

                    condition_on_previous_text=False
                )

                text = " ".join(

                    segment.text

                    for segment in segments

                ).strip()

                print("\n========== DEBUG ==========")

                print(

                    f"Recognized Text : {text}"

                )

                print("===========================\n")

                if text:

                    text = (

                        text

                        .replace("  ", " ")

                        .strip()

                    )

                    try:

                        os.remove(audio_file)

                    except Exception:

                        pass

                    return text

                print(

                    f"No speech detected. Retry "

                    f"{attempt + 1}/{retries}"

                )

                try:

                    if os.path.exists(audio_file):

                        os.remove(audio_file)

                except Exception:

                    pass

            return None

        except Exception as error:

            self.stop_audio_meter()

            print(

                f"\nWhisper Error : {error}"

            )

            try:

                if audio_file and os.path.exists(audio_file):

                    os.remove(audio_file)

            except Exception:

                pass

            return None

    # --------------------------------------------------
    # Listen For Confirmation
    # --------------------------------------------------

    def listen_confirmation(
        self,
        retries=3
    ):
        """
        Listen for

        Yes

        No

        Cancel

        Returns
        -------
        str | None
        """

        for _ in range(retries):

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
                .replace(".", "")
                .replace(",", "")
                .replace("!", "")
                .replace("?", "")
            )

            # -------------------------
            # Common Whisper Mistakes
            # -------------------------

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
                "\nPlease say"
            )

            print(
                "Yes, No or Cancel."
            )

        return None

    # --------------------------------------------------
    # Cleanup
    # --------------------------------------------------

    def close(self):
        """
        Release microphone resources.
        """

        self._closing = True

        self.stop_audio_meter()

        self.level_callback = None

        self.microphone = None

        self.recognizer = None

        print(
            "Whisper Recognizer shutdown completed."
        )