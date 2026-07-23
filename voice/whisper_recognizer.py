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

    def listen(self):
        """
        Listen from microphone and convert
        speech into text.

        Returns:
            str | None
        """

        try:

            audio_file = self.record_audio()

            print("Audio File :", audio_file)

            if audio_file:
                print("File Size :", os.path.getsize(audio_file))

            if audio_file is None:
                return None

            print("🧠 Transcribing...")

            segments, _ = self.model.transcribe(
                audio_file,
                beam_size=5,
                language="en",
                vad_filter=False
            )

            text_parts = []

            for segment in segments:
                text_parts.append(segment.text)

            text = " ".join(text_parts).strip()

            print("\n========== DEBUG ==========")
            print(f"Recognized Text : {text}")
            print("===========================\n")

            #if os.path.exists(audio_file):
                #os.remove(audio_file)

            if text == "":
                return None

            return text

        except Exception as error:

            print(f"\nWhisper Error : {error}")

            return None