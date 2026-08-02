"""
Application Closer Module

This module closes running Windows applications.
"""

import subprocess
from pathlib import Path


class AppCloser:
    """
    Close running Windows applications.
    """

    def close_application(
        self,
        application
    ):
        """
        Close the given application.

        Parameters
        ----------
        application : str

        Returns
        -------
        bool
        """

        if not application:

            return False

        try:

            application = application.strip()

            # -----------------------------
            # Full path -> exe name
            # -----------------------------

            if "\\" in application:

                application = Path(
                    application
                ).name

            # -----------------------------
            # Add .exe if missing
            # -----------------------------

            if (
                not application.lower().endswith(
                    ".exe"
                )
            ):

                application += ".exe"

            print(
                f"Closing : {application}"
            )

            result = subprocess.run(

                [

                    "taskkill",

                    "/IM",

                    application,

                    "/F"

                ],

                capture_output=True,

                text=True

            )

            if result.returncode == 0:

                print(
                    "Application closed."
                )

                return True

            print(
                result.stderr
            )

            return False

        except Exception as error:

            print(
                f"Close Error : {error}"
            )

            return False