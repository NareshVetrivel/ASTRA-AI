"""
Whisper Speech Recognition Module

Offline Speech Recognition using Faster-Whisper.
"""

import os
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

    def load_model(self):
        """
        Load Faster-Whisper model.
        """

        if self.model is not None:
            return

        print("\nLoading Faster-Whisper model...")

        self.model = WhisperModel(
            "base",
            device="cpu",
            compute_type="int8"
        )

        print("Whisper model loaded successfully.")

    def record_audio(self):
        """
        Record audio from microphone.

        Returns:
            str | None
        """

        try:

            with self.microphone as source:

                print("🎤 Listening...")

                self.recognizer.adjust_for_ambient_noise(
                    source,
                    duration=0.5
                )

                audio = self.recognizer.listen(
                    source,
                    timeout=None,
                    phrase_time_limit=10
                )
                print("Audio captured successfully.")
                print("Audio Bytes :", len(audio.frame_data))

            temp_file = "temp_audio.wav"

            with open(temp_file, "wb") as file:

                file.write(audio.get_wav_data())

            return temp_file

        except sr.WaitTimeoutError:

            print("\nListening Timeout.")

            return None

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

        try:

            if self.model is None:

                print("Whisper model not loaded.")

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

                    beam_size=5,

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

                    return text

                print(

                    f"No speech detected. Retry "

                    f"{attempt + 1}/{retries}"

                )

            return None

        except Exception as error:

            print(

                f"\nWhisper Error : {error}"

            )

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

        valid = {

            "yes",

            "no",

            "cancel",

            "stop"

        }

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