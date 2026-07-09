"""
Unit Test for Text To Speech
"""

from voice.text_to_speech import TextToSpeech


def main():

    speaker = TextToSpeech()

    while True:

        print("\n==============================")
        print("ASTRA-AI Text To Speech Test")
        print("==============================")

        text = input("Enter Text : ")

        if text.lower() == "exit":

            print("Exiting Test...")

            break

        speaker.speak(text)


if __name__ == "__main__":
    main()