"""
Application Launcher Module

This module launches Windows applications.
"""

import subprocess


class AppLauncher:
    """
    Launch applications using subprocess.
    """

    def launch_application(self, application):

        """
        Launch the given application.

        Parameters:
            application (str)

        Returns:
            bool
        """

        if not application:
            return False

        try:

            subprocess.Popen(application)

            return True

        except Exception as error:

            print(f"Error : {error}")

            return False