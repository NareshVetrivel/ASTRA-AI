"""
Speech Recognition Module

Provides microphone listening and wake-word detection
for the ASTRA-AI application.
"""

from __future__ import annotations

import speech_recognition as sr


class SpeechRecognizer:
    """
    Handles microphone input and wake-word detection
    for the ASTRA-AI application.
    """

    # ==================================================
    # Initialization
    # ==================================================

    def __init__(self):

        self.recognizer = sr.Recognizer()

        # ---------------------------------
        # Wake Words
        # ---------------------------------

        self.wake_words = (
            "astra",
            "hey astra",
            "ok astra",
            "okay astra",
        )

        # ---------------------------------
        # Recognition Settings
        # ---------------------------------

        self.ambient_duration = 1

        self.pause_threshold = 0.8

        self.phrase_threshold = 0.3

        self.non_speaking_duration = 0.5

        self.recognizer.pause_threshold = (
            self.pause_threshold
        )

        self.recognizer.phrase_threshold = (
            self.phrase_threshold
        )

        self.recognizer.non_speaking_duration = (
            self.non_speaking_duration
        )

    # ==================================================
    # Ambient Noise Calibration
    # ==================================================

    def calibrate_microphone(
        self,
        source
    ):
        """
        Calibrate the microphone for ambient noise.
        """

        try:

            print(
                "🎧 Calibrating microphone..."
            )

            self.recognizer.adjust_for_ambient_noise(

                source,

                duration=self.ambient_duration

            )

            print(
                "🎧 Microphone calibrated."
            )

            return True

        except Exception as error:

            print(
                f"Microphone Calibration Error : "
                f"{error}"
            )

            return False

    # ==================================================
    # Normalize Text
    # ==================================================

    def normalize_text(
        self,
        text
    ):
        """
        Normalize recognized text.
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
    # Check Wake Word
    # ==================================================

    def contains_wake_word(
        self,
        text
    ):
        """
        Check whether recognized text contains
        a configured ASTRA wake word.

        Returns
        -------
        bool
        """

        normalized = (
            self.normalize_text(text)
        )

        if not normalized:

            return False

        for wake_word in self.wake_words:

            if wake_word in normalized:

                return True

        return False

    # ==================================================
    # Remove Wake Word
    # ==================================================

    def remove_wake_word(
        self,
        text
    ):
        """
        Remove the wake word from recognized text.

        Example
        -------
        "Hey ASTRA start screen recording"

        becomes

        "start screen recording"
        """

        if not text:

            return ""

        result = text.strip()

        normalized = (
            self.normalize_text(result)
        )

        for wake_word in sorted(
            self.wake_words,
            key=len,
            reverse=True
        ):

            if normalized.startswith(
                wake_word
            ):

                # Preserve the original
                # text after the wake word.

                words = result.split()

                wake_word_count = len(
                    wake_word.split()
                )

                remaining = words[
                    wake_word_count:
                ]

                return " ".join(
                    remaining
                ).strip()

        return result

    # ==================================================
    # Listen
    # ==================================================

    def listen(
        self
    ):
        """
        Listen to the user's voice
        and return recognized text.

        This method preserves the existing
        speech recognition behavior.
        """

        try:

            with sr.Microphone() as source:

                print(
                    "🎤 Listening..."
                )

                self.calibrate_microphone(
                    source
                )

                audio = (
                    self.recognizer.listen(
                        source
                    )
                )

                print(
                    "🧠 Recognizing..."
                )

                text = (
                    self.recognizer
                    .recognize_google(
                        audio
                    )
                )

                print(
                    f"Recognized Text : {text}"
                )

                return text

        except sr.UnknownValueError:

            print(
                "No speech detected."
            )

            return None

        except sr.RequestError as error:

            print(
                f"Speech Recognition Service Error : "
                f"{error}"
            )

            return None

        except Exception as error:

            print(
                f"Speech Recognition Error : "
                f"{error}"
            )

            return None

    # ==================================================
    # Listen For Wake Word
    # ==================================================

    def listen_for_wake_word(
        self
    ):
        """
        Continuously listen until a wake word
        is detected.

        Returns
        -------
        bool
            True when ASTRA wake word is detected.
        """

        try:

            with sr.Microphone() as source:

                print(
                    "🟢 ASTRA is listening "
                    "for wake word..."
                )

                self.calibrate_microphone(
                    source
                )

                while True:

                    try:

                        audio = (
                            self.recognizer.listen(
                                source,
                                timeout=None,
                                phrase_time_limit=5
                            )
                        )

                        text = (
                            self.recognizer
                            .recognize_google(
                                audio
                            )
                        )

                        print(
                            f"Wake Check : {text}"
                        )

                        if self.contains_wake_word(
                            text
                        ):

                            print(
                                "⚡ ASTRA wake word detected."
                            )

                            return True

                    except sr.UnknownValueError:

                        continue

                    except sr.RequestError as error:

                        print(
                            f"Wake Word Service Error : "
                            f"{error}"
                        )

                        return False

        except Exception as error:

            print(
                f"Wake Word Error : "
                f"{error}"
            )

            return False

    # ==================================================
    # Listen After Wake Word
    # ==================================================

    def listen_after_wake_word(
        self
    ):
        """
        Listen for the actual command after
        the ASTRA wake word has been detected.

        Returns
        -------
        str | None
            User command.
        """

        try:

            with sr.Microphone() as source:

                print(
                    "🎤 ASTRA activated. "
                    "Listening for command..."
                )

                audio = (
                    self.recognizer.listen(
                        source,
                        timeout=5,
                        phrase_time_limit=10
                    )
                )

                text = (
                    self.recognizer
                    .recognize_google(
                        audio
                    )
                )

                print(
                    f"Command After Wake Word : "
                    f"{text}"
                )

                return text

        except sr.WaitTimeoutError:

            print(
                "Command listening timed out."
            )

            return None

        except sr.UnknownValueError:

            print(
                "Command could not be understood."
            )

            return None

        except sr.RequestError as error:

            print(
                f"Command Recognition Service Error : "
                f"{error}"
            )

            return None

        except Exception as error:

            print(
                f"Command Listening Error : "
                f"{error}"
            )

            return None

    # ==================================================
    # Listen For Wake Word + Command
    # ==================================================

    def listen_for_command(
        self
    ):
        """
        Listen for a wake word and then capture
        the user's command.

        Supports:

        "Hey ASTRA"

        followed by:

        "Start screen recording"

        Also supports:

        "Hey ASTRA start screen recording"

        Returns
        -------
        str | None
            Final command without wake word.
        """

        try:

            with sr.Microphone() as source:

                print(
                    "🟢 ASTRA is waiting "
                    "for wake word..."
                )

                self.calibrate_microphone(
                    source
                )

                while True:

                    try:

                        audio = (
                            self.recognizer.listen(
                                source,
                                timeout=None,
                                phrase_time_limit=8
                            )
                        )

                        text = (
                            self.recognizer
                            .recognize_google(
                                audio
                            )
                        )

                        print(
                            f"Wake Input : {text}"
                        )

                        if not self.contains_wake_word(
                            text
                        ):

                            continue

                        print(
                            "⚡ ASTRA activated."
                        )

                        # ---------------------------------
                        # Command included with wake word
                        # ---------------------------------

                        command = (
                            self.remove_wake_word(
                                text
                            )
                        )

                        if command:

                            print(
                                f"Command : {command}"
                            )

                            return command

                        # ---------------------------------
                        # Wake word only
                        # ---------------------------------

                        print(
                            "🎤 Listening for command..."
                        )

                        command_audio = (
                            self.recognizer.listen(
                                source,
                                timeout=5,
                                phrase_time_limit=10
                            )
                        )

                        command = (
                            self.recognizer
                            .recognize_google(
                                command_audio
                            )
                        )

                        print(
                            f"Command : {command}"
                        )

                        return command

                    except sr.UnknownValueError:

                        continue

                    except sr.WaitTimeoutError:

                        continue

                    except sr.RequestError as error:

                        print(
                            f"Wake Word Service Error : "
                            f"{error}"
                        )

                        return None

        except Exception as error:

            print(
                f"Wake Command Error : "
                f"{error}"
            )

            return None