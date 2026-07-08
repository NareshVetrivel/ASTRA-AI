"""
Application Closer Module

This module closes running Windows applications.
"""

import subprocess


class AppCloser:
    """
    Close running Windows applications.
    """

    def close_application(self, application):
        """
        Close the given application.

        Parameters:
            application (str)

        Returns:
            bool
        """

        if not application:
            return False

        try:

            subprocess.run(
                [
                    "taskkill",
                    "/IM",
                    application,
                    "/F"
                ],
                check=True,
                capture_output=True,
                text=True
            )

            return True

        except subprocess.CalledProcessError:

            return False

        except Exception as error:

            print(f"Error : {error}")

            return False