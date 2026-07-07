from voice.speech_recognition import SpeechRecognizer


def main():
    recognizer = SpeechRecognizer()

    text = recognizer.listen()

    if text:
        print(f"You said: {text}")
    else:
        print("No speech recognized.")


if __name__ == "__main__":
    main()