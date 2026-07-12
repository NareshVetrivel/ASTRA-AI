"""
Mouse Controller Module

Provides mouse automation using PyAutoGUI.
"""

import pyautogui


class MouseController:
    """
    Controls mouse actions using PyAutoGUI.
    """

    def __init__(self):
        """
        Initialize mouse controller.
        """

        # Move mouse to top-left corner
        # to stop the program.
        pyautogui.FAILSAFE = True

        # Small pause after every action.
        pyautogui.PAUSE = 0.2

    def left_click(self):
        """
        Perform a left mouse click.

        Returns
        -------
        bool
        """

        try:

            pyautogui.click()

            return True

        except Exception as error:

            print(f"Mouse Error : {error}")

            return False

    def right_click(self):
        """
        Perform a right mouse click.

        Returns
        -------
        bool
        """

        try:

            pyautogui.rightClick()

            return True

        except Exception as error:

            print(f"Mouse Error : {error}")

            return False

    def double_click(self):
        """
        Perform a double mouse click.

        Returns
        -------
        bool
        """

        try:

            pyautogui.doubleClick()

            return True

        except Exception as error:

            print(f"Mouse Error : {error}")

            return False

    def scroll_up(self, clicks=500):
        """
        Scroll upward.

        Parameters
        ----------
        clicks : int

        Returns
        -------
        bool
        """

        try:

            pyautogui.scroll(clicks)

            return True

        except Exception as error:

            print(f"Mouse Error : {error}")

            return False

    def scroll_down(self, clicks=500):
        """
        Scroll downward.

        Parameters
        ----------
        clicks : int

        Returns
        -------
        bool
        """

        try:

            pyautogui.scroll(-clicks)

            return True

        except Exception as error:

            print(f"Mouse Error : {error}")

            return False

    def move_to(self, x, y, duration=0.5):
        """
        Move mouse to an absolute position.

        Parameters
        ----------
        x : int

        y : int

        duration : float

        Returns
        -------
        bool
        """

        try:

            pyautogui.moveTo(
                x,
                y,
                duration=duration
            )

            return True

        except Exception as error:

            print(f"Mouse Error : {error}")

            return False

    def move_relative(
        self,
        x_offset,
        y_offset,
        duration=0.3
    ):
        """
        Move mouse relative to
        current position.

        Parameters
        ----------
        x_offset : int

        y_offset : int

        duration : float

        Returns
        -------
        bool
        """

        try:

            pyautogui.moveRel(
                x_offset,
                y_offset,
                duration=duration
            )

            return True

        except Exception as error:

            print(f"Mouse Error : {error}")

            return False

    def get_position(self):
        """
        Get current mouse position.

        Returns
        -------
        tuple | None
        """

        try:

            return pyautogui.position()

        except Exception as error:

            print(f"Mouse Error : {error}")

            return None