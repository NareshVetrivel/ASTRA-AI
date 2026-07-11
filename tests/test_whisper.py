"""
Unit Test for Whisper Recognizer
"""

from voice.whisper_recognizer import WhisperRecognizer


def main():

    recognizer = WhisperRecognizer()

    while True:

        print("\n==============================")
        print("ASTRA Whisper Test")
        print("==============================")

        text = recognizer.listen()

        if text:

            print(f"\nResult : {text}")

        else:

            print("\nNo Speech Detected.")

        choice = input("\nContinue? (y/n): ")

        if choice.lower() != "y":
            break


if __name__ == "__main__":
    main()