"""
tests/test_wake_word.py

ASTRA-AI
========

CONTINUOUS LIVE WAKE WORD DATA COLLECTION TEST
----------------------------------------------

Purpose
-------
Test voice/wake_word.py independently before integrating
wake-word detection into main_window.py.

This test intentionally runs continuously.

The microphone remains available until the user presses
Ctrl+C.

Every time DHEEPTHI is detected:

    detection
        ↓
    print captured text
        ↓
    re-arm detector
        ↓
    continue listening

Therefore one detection does NOT terminate this test.

IMPORTANT
---------
main_window.py is NOT loaded.

Groq is NOT loaded.

Faster-Whisper is NOT loaded.

This file is ONLY for testing Vosk wake-word matching
and collecting real recognition behaviour.

Run from project root:

    python -m tests.test_wake_word

Stop:

    Ctrl+C


DATA COLLECTION
---------------

Try both positive and negative phrases.

POSITIVE:
    Dheepthi
    Deepthi
    Deepti
    Deepthy
    Deeptee
    Dhepti
    Dhepthi
    Dheethi
    Dhethi

    Deep thi
    Deep tea
    Deep thee
    Deep tee
    Deep ti

    Dheep thi
    Dheep tea
    Dheep thee
    Dheep tee
    Dheep ti

    Deep deep
    Deep thee
    Deep the
    Thee the
    The the

    Hey Dheepthi
    Hello Dheepthi
    Hi Dheepthi

NEGATIVE / FALSE-DETECTION TESTS:
    Deep sleep
    Deep water
    Deep voice
    Deep breath
    Deep thought
    Deep thoughts
    Sleep deeply
    Hello
    Hi
    Hey
    Good morning
    How are you
    Deep
    A deep
    My lord
    Added day
    The
    The the

IMPORTANT
---------
Do NOT intentionally pronounce the wake word unnaturally.

Speak normally.

The purpose is to discover what Vosk actually captures.
"""


from __future__ import annotations

import signal
import sys
import threading
import time

from voice.wake_word import WakeWordDetector


# ==========================================================
# TEST STATE
# ==========================================================

running = True

detector: WakeWordDetector | None = None

detection_count = 0

detection_lock = threading.Lock()


# ==========================================================
# Ctrl+C Handler
# ==========================================================

def handle_shutdown(signum, frame):
    """
    Stop the continuous test.

    Ctrl+C is the ONLY normal way to end the test.
    """

    global running

    if not running:
        return

    print(
        "\n\n"
        "============================================================"
    )

    print(
        "Ctrl+C received."
    )

    print(
        "Stopping continuous wake-word test..."
    )

    print(
        "============================================================"
    )

    running = False

    current_detector = detector

    if current_detector is not None:

        try:
            current_detector.stop()

        except Exception:
            pass


# ==========================================================
# Detection Callback
# ==========================================================

def on_detected(text: str = ""):
    """
    Called whenever the detector recognizes DHEEPTHI.

    IMPORTANT
    ---------
    Detection does NOT end the test.

    The detector stops its current wake session after
    detection by design.

    We immediately re-arm it so the next utterance can
    also be tested.
    """

    global detection_count
    global running
    global detector

    with detection_lock:

        detection_count += 1

        current_count = detection_count

    print(
        "\n"
        "============================================================"
    )

    print(
        f"WAKE DETECTION #{current_count}"
    )

    print(
        "============================================================"
    )

    print(
        f"Captured text : {text}"
    )

    print(
        "Result        : MATCH / ACTIVATED"
    )

    print(
        "------------------------------------------------------------"
    )

    if not running:
        return

    current_detector = detector

    if current_detector is None:
        return

    # ------------------------------------------------------
    # Small delay.
    #
    # The previous microphone stream must completely close
    # before a fresh stream is opened.
    # ------------------------------------------------------

    time.sleep(0.10)

    if not running:
        return

    try:

        success = current_detector.start()

        if success:

            print(
                "🔄 Wake detector re-armed."
            )

            print(
                "🎤 Listening for next wake phrase..."
            )

        else:

            print(
                "⚠️ Failed to re-arm wake detector."
            )

    except Exception as error:

        print(
            "Wake detector re-arm error:"
        )

        print(
            f"    {type(error).__name__}: {error}"
        )


# ==========================================================
# Audio Level Callback
# ==========================================================

def on_level(level: float):
    """
    Receive microphone audio level.

    We intentionally do not print every level because
    doing so would flood the terminal.

    The callback is still installed so the test also
    verifies that audio-level processing remains active.
    """

    pass


# ==========================================================
# Print Dataset Test Cases
# ==========================================================

def print_dataset_cases():
    """
    Print positive and negative test phrases.

    These are NOT automatically fed to Vosk.

    They are examples for the user to speak naturally
    during the live microphone test.
    """

    print(
        "\n"
        "============================================================"
    )

    print(
        "POSITIVE / WAKE-WORD TEST CASES"
    )

    print(
        "============================================================"
    )

    positive_cases = (
        "Dheepthi",
        "Deepthi",
        "Deepti",
        "Deepthy",
        "Deeptee",
        "Dhepti",
        "Dhepthi",
        "Dheethi",
        "Dhethi",
        "Deep thi",
        "Deep tea",
        "Deep thee",
        "Deep tee",
        "Deep ti",
        "Dheep thi",
        "Dheep tea",
        "Dheep thee",
        "Dheep tee",
        "Dheep ti",
        "Deep deep",
        "Deep deep thi",
        "Deep deep tea",
        "Deep deep thee",
        "Deep thee",
        "Deep the",
        "Thee the",
        "The the",
        "Hey Dheepthi",
        "Hello Dheepthi",
        "Hi Dheepthi",
    )

    for phrase in positive_cases:

        print(
            f"    + {phrase}"
        )

    print(
        "\n"
        "============================================================"
    )

    print(
        "NEGATIVE / FALSE-DETECTION TEST CASES"
    )

    print(
        "============================================================"
    )

    negative_cases = (
        "Deep sleep",
        "Sleep deeply",
        "Deep water",
        "Deep voice",
        "Deep breath",
        "Deep breathing",
        "Deep thought",
        "Deep thoughts",
        "Hello",
        "Hi",
        "Hey",
        "Good morning",
        "How are you",
        "Deep",
        "A deep",
        "My lord",
        "Added day",
        "The",
        "The the",
    )

    for phrase in negative_cases:

        print(
            f"    - {phrase}"
        )


# ==========================================================
# Main
# ==========================================================

def main():
    """
    Start continuous live Vosk testing.

    The function does NOT finish after a wake detection.

    It remains alive until Ctrl+C.
    """

    global detector
    global running
    global detection_count

    # ------------------------------------------------------
    # Reset state.
    # ------------------------------------------------------

    running = True
    detection_count = 0

    # ------------------------------------------------------
    # Install Ctrl+C handler.
    # ------------------------------------------------------

    signal.signal(
        signal.SIGINT,
        handle_shutdown,
    )

    if hasattr(signal, "SIGTERM"):

        signal.signal(
            signal.SIGTERM,
            handle_shutdown,
        )

    # ======================================================
    # Header
    # ======================================================

    print(
        "\n"
        "============================================================"
    )

    print(
        "        ASTRA-AI CONTINUOUS WAKE WORD TEST"
    )

    print(
        "============================================================"
    )

    print(
        "\n"
        "main_window.py : NOT LOADED"
    )

    print(
        "Groq           : NOT LOADED"
    )

    print(
        "Faster-Whisper : NOT LOADED"
    )

    print(
        "Wake Engine    : Vosk"
    )

    print(
        "Mode           : LOCAL / OFFLINE"
    )

    print(
        "Test Mode      : CONTINUOUS"
    )

    print(
        "\nWake Word:"
    )

    print(
        "    DHEEPTHI"
    )

    # ======================================================
    # Dataset examples
    # ======================================================

    print_dataset_cases()

    # ======================================================
    # Instructions
    # ======================================================

    print(
        "\n"
        "============================================================"
    )

    print(
        "LIVE TEST INSTRUCTIONS"
    )

    print(
        "============================================================"
    )

    print(
        "\nSpeak naturally."
    )

    print(
        "Do NOT force the pronunciation."
    )

    print(
        "\nFor every phrase Vosk recognizes, watch:"
    )

    print(
        "    Wake Partial : ..."
    )

    print(
        "    Wake STT     : ..."
    )

    print(
        "\nIf the wake matcher accepts a phrase:"
    )

    print(
        "    WAKE DETECTION #N"
    )

    print(
        "    Captured text : ..."
    )

    print(
        "\nAfter detection the microphone will automatically"
    )

    print(
        "re-arm and continue listening."
    )

    print(
        "\nThe test stops ONLY with:"
    )

    print(
        "    Ctrl+C"
    )

    print(
        "============================================================\n"
    )

    # ======================================================
    # Create Detector
    # ======================================================

    detector = WakeWordDetector(
        on_detected=on_detected,
        level_callback=on_level,
    )

    # ======================================================
    # Load Model
    # ======================================================

    print(
        "Loading Vosk model..."
    )

    if not detector.load_model():

        print(
            "\n"
            "============================================================"
        )

        print(
            "ERROR"
        )

        print(
            "============================================================"
        )

        print(
            "Vosk model could not be loaded."
        )

        print(
            "Check the model path."
        )

        print(
            "============================================================"
        )

        detector = None

        return 1

    print(
        "\nVosk model loaded successfully."
    )

    # ======================================================
    # Start Background Detector
    # ======================================================

    print(
        "\n"
        "============================================================"
    )

    print(
        "STARTING CONTINUOUS MICROPHONE LISTENER"
    )

    print(
        "============================================================"
    )

    try:

        if not detector.start():

            print(
                "\nERROR:"
            )

            print(
                "Could not start wake-word detector."
            )

            return 1

    except Exception as error:

        print(
            "\n"
            "Wake detector start error:"
        )

        print(
            f"{type(error).__name__}: {error}"
        )

        return 1

    print(
        "\n🎤 MICROPHONE ACTIVE"
    )

    print(
        "🎧 Vosk listening continuously"
    )

    print(
        "🗣️ Speak naturally"
    )

    print(
        "🔄 Detection will automatically re-arm"
    )

    print(
        "🛑 Press Ctrl+C to stop"
    )

    print(
        "\n"
        "------------------------------------------------------------"
    )

    # ======================================================
    # CONTINUOUS WAIT LOOP
    # ======================================================
    #
    # IMPORTANT:
    #
    # Do NOT use:
    #
    #     while detector.is_running():
    #
    # because detector.is_running() becomes False
    # immediately after one wake detection.
    #
    # We intentionally keep OUR OWN test loop alive.
    #
    # The detector is re-armed by on_detected().
    #
    # ======================================================

    try:

        while running:

            time.sleep(0.20)

    except KeyboardInterrupt:

        handle_shutdown(
            signal.SIGINT,
            None,
        )

    finally:

        print(
            "\n"
            "============================================================"
        )

        print(
            "FINAL CLEANUP"
        )

        print(
            "============================================================"
        )

        current_detector = detector

        if current_detector is not None:

            try:

                current_detector.stop()

            except Exception as error:

                print(
                    f"Detector stop error: {error}"
                )

            try:

                current_detector.close()

            except Exception as error:

                print(
                    f"Detector close error: {error}"
                )

        print(
            "\n"
            "============================================================"
        )

        print(
            "WAKE WORD TEST FINISHED"
        )

        print(
            "============================================================"
        )

        print(
            f"Total wake detections : {detection_count}"
        )

        print(
            "\n"
            "Use the captured Vosk text above to improve"
        )

        print(
            "the DHEEPTHI matching dataset."
        )

        print(
            "\n"
            "main_window.py was NOT modified."
        )

        print(
            "============================================================\n"
        )

    return 0


# ==========================================================
# Entry Point
# ==========================================================

if __name__ == "__main__":

    sys.exit(
        main()
    )