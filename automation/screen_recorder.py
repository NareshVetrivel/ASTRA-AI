"""
Screen Recorder Module

Provides screen recording functionality
for ASTRA-AI on Windows.
"""

from __future__ import annotations

import threading
import time
from pathlib import Path

import cv2
import mss
import numpy as np


class ScreenRecorder:
    """
    Controls screen recording.
    """

    def __init__(self):

        self.recording = False

        self.thread = None

        self.output_path = None

        self.output_directory = (
            Path.cwd() / "screen_recordings"
        )

        self.output_directory.mkdir(
            parents=True,
            exist_ok=True
        )

        self._stop_event = threading.Event()

    # ==================================================
    # Start Recording
    # ==================================================

    def start_recording(self):
        """
        Start screen recording.

        Returns
        -------
        bool
            True if recording started.
        """

        if self.recording:

            return False

        self._stop_event.clear()

        timestamp = time.strftime(
            "%Y%m%d_%H%M%S"
        )

        filename = (
            f"screen_recording_{timestamp}.mp4"
        )

        self.output_path = (
            self.output_directory /
            filename
        )

        self.recording = True

        self.thread = threading.Thread(
            target=self._record_screen,
            daemon=True
        )

        self.thread.start()

        return True

    # ==================================================
    # Stop Recording
    # ==================================================

    def stop_recording(self):
        """
        Stop the current screen recording.

        Returns
        -------
        str | None
            Saved recording path.
        """

        if not self.recording:

            return None

        self._stop_event.set()

        if self.thread is not None:

            self.thread.join(
                timeout=5
            )

        self.recording = False

        if self.output_path is None:

            return None

        if not self.output_path.exists():

            return None

        return str(
            self.output_path
        )

    # ==================================================
    # Recording Worker
    # ==================================================

    def _record_screen(self):
        """
        Internal screen recording worker.
        """

        writer = None

        try:

            with mss.mss() as screen:

                monitor = screen.monitors[1]

                width = monitor["width"]

                height = monitor["height"]

                # ---------------------------------
                # Video Writer
                # ---------------------------------

                fourcc = cv2.VideoWriter_fourcc(
                    *"mp4v"
                )

                writer = cv2.VideoWriter(

                    str(
                        self.output_path
                    ),

                    fourcc,

                    20.0,

                    (
                        width,
                        height
                    )

                )

                if not writer.isOpened():

                    print(
                        "Screen Recording Error : "
                        "Unable to create video file."
                    )

                    self.recording = False

                    return

                # ---------------------------------
                # Capture Loop
                # ---------------------------------

                frame_interval = 1.0 / 20.0

                while not self._stop_event.is_set():

                    start_time = time.perf_counter()

                    screenshot = screen.grab(
                        monitor
                    )

                    frame = np.array(
                        screenshot
                    )

                    frame = cv2.cvtColor(
                        frame,
                        cv2.COLOR_BGRA2BGR
                    )

                    writer.write(
                        frame
                    )

                    elapsed = (
                        time.perf_counter()
                        - start_time
                    )

                    remaining = (
                        frame_interval
                        - elapsed
                    )

                    if remaining > 0:

                        time.sleep(
                            remaining
                        )

        except Exception as error:

            print(
                f"Screen Recording Error : {error}"
            )

        finally:

            if writer is not None:

                writer.release()

            self.recording = False

    # ==================================================
    # Status
    # ==================================================

    def is_recording(self):
        """
        Check recording state.

        Returns
        -------
        bool
        """

        return self.recording

    # ==================================================
    # Current Output
    # ==================================================

    def get_output_path(self):
        """
        Get current recording path.

        Returns
        -------
        str | None
        """

        if self.output_path is None:

            return None

        return str(
            self.output_path
        )