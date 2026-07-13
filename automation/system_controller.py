"""
System Controller Module

Provides basic system automation
for Windows.
"""

import os
import time

import pyautogui
import ctypes

class SystemController:
    """
    Controls basic Windows
    system functions.
    """

    def __init__(self):
        """
        Initialize System Controller.
        """

        pyautogui.FAILSAFE = True
        pyautogui.PAUSE = 0.2

    def volume_up(self):
        """
        Increase system volume.

        Returns
        -------
        bool
        """

        try:

            pyautogui.press("volumeup")

            return True

        except Exception as error:

            print(f"Volume Up Error : {error}")

            return False

    def volume_down(self):
        """
        Decrease system volume.

        Returns
        -------
        bool
        """

        try:

            pyautogui.press("volumedown")

            return True

        except Exception as error:

            print(f"Volume Down Error : {error}")

            return False

    def mute(self):
        """
        Toggle mute.

        Returns
        -------
        bool
        """

        try:

            pyautogui.press("volumemute")

            return True

        except Exception as error:

            print(f"Mute Error : {error}")

            return False

    def lock_screen(self):
        """
        Lock Windows.

        Returns
        -------
        bool
        """

        try:

            ctypes.windll.user32.LockWorkStation()
            
            return True

        except Exception as error:

            print(f"Lock Screen Error : {error}")

            return False

    def take_screenshot(self):
        """
        Save screenshot.

        Returns
        -------
        str | None
        """

        try:

            timestamp = time.strftime(
                "%Y%m%d_%H%M%S"
            )

            filename = (
                f"screenshot_{timestamp}.png"
            )

            screenshot = pyautogui.screenshot()

            screenshot.save(filename)

            return filename

        except Exception as error:

            print(f"Screenshot Error : {error}")

            return None

    def open_task_manager(self):
        """
        Open Task Manager.

        Returns
        -------
        bool
        """

        try:

            pyautogui.hotkey(
                "ctrl",
                "shift",
                "esc"
            )

            return True

        except Exception as error:

            print(f"Task Manager Error : {error}")

            return False

    def open_file_explorer(self):
        """
        Open File Explorer.

        Returns
        -------
        bool
        """

        try:

            os.startfile("explorer.exe")

            return True

        except Exception as error:

            print(f"Explorer Error : {error}")

            return False