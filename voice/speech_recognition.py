import speech_recognition as sr


class SpeechRecognizer:
    """
    Handles speech-to-text conversion
    for the ASTRA-AI application.
    """

    def __init__(self):
        self.recognizer = sr.Recognizer()

    def listen(self):
        """
        Listen to the user's voice
        and return the recognized text.
        """

        try:
            with sr.Microphone() as source:

                print("🎤 Listening...")

                self.recognizer.adjust_for_ambient_noise(
                    source,
                    duration=1
                )

                audio = self.recognizer.listen(source)

                text = self.recognizer.recognize_google(audio)

                return text

        except Exception as error:

            print(f"Error : {error}")

            return None