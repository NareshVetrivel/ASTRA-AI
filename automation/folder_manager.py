"""
Folder Manager Module

Provides folder-related automation
for ASTRA-AI.

Features
--------
- Open Folder
- Open Special Folder
- Create Folder
- Rename Folder
- Delete Folder
- Move Folder
- Copy Folder
- Empty Recycle Bin

ASTRA-AI V1
"""

import os
import shutil
import subprocess

from pathlib import Path


class FolderManager:
    """
    Perform folder operations.
    """

    def __init__(self):

        self.home = Path.home()

        # ---------------------------------
        # Special Folder Mapping
        # ---------------------------------

        self.special_folders = {

            "desktop": self.resolve_folder(
                os.path.expandvars(r"%USERPROFILE%\Desktop"),
                os.path.expandvars(r"%OneDrive%\Desktop")
            ),

            "documents": self.resolve_folder(
                os.path.expandvars(r"%USERPROFILE%\Documents"),
                os.path.expandvars(r"%OneDrive%\Documents")
            ),

            "downloads": self.resolve_folder(
                os.path.expandvars(r"%USERPROFILE%\Downloads"),
                os.path.expandvars(r"%OneDrive%\Downloads")
            ),

            "pictures": self.resolve_folder(
                os.path.expandvars(r"%USERPROFILE%\Pictures"),
                os.path.expandvars(r"%OneDrive%\Pictures")
            ),

            "videos": self.resolve_folder(
                os.path.expandvars(r"%USERPROFILE%\Videos"),
                os.path.expandvars(r"%OneDrive%\Videos")
            ),

            "music": self.resolve_folder(
                os.path.expandvars(r"%USERPROFILE%\Music"),
                os.path.expandvars(r"%OneDrive%\Music")
            ),

            "this pc": "shell:MyComputerFolder",

            "computer": "shell:MyComputerFolder",

            "my computer": "shell:MyComputerFolder",

            "recycle bin": "shell:RecycleBinFolder",

            "trash": "shell:RecycleBinFolder",

            "e drive": Path("E:/"),

            "d drive": Path("D:/"),

            "c drive": Path("C:/")

        }

    # --------------------------------------------------
    # Resolve Special Folder
    # --------------------------------------------------

    def resolve_folder(self, *locations):
        """
        Return the first existing folder.
        """

        for location in locations:

            path = Path(location)

            if path.exists():

                print(f"Resolved Folder : {path}")

                return path

        return None

    # --------------------------------------------------
    # Create Folder
    # --------------------------------------------------

    def create_folder(
        self,
        folder_path
    ):
        """
        Create a new folder.

        Parameters
        ----------
        folder_path : str

        Returns
        -------
        bool
        """

        if not folder_path:

            return False

        try:

            path = Path(folder_path)

            path.mkdir(
                parents=True,
                exist_ok=True
            )

            print(
                f"Folder Created : {path}"
            )

            return True

        except Exception as error:

            print(
                f"Create Folder Error : {error}"
            )

            return False

    # --------------------------------------------------
    # Rename Folder
    # --------------------------------------------------

    def rename_folder(
        self,
        source_folder,
        new_name
    ):
        """
        Rename an existing folder.

        Parameters
        ----------
        source_folder : str

        new_name : str

        Returns
        -------
        bool
        """

        if not source_folder or not new_name:

            return False

        try:

            source = Path(source_folder)

            if not source.exists():

                return False

            destination = source.parent / new_name

            source.rename(destination)

            print(
                f"Folder Renamed : {destination}"
            )

            return True

        except Exception as error:

            print(
                f"Rename Folder Error : {error}"
            )

            return False

    # --------------------------------------------------
    # Delete Folder
    # --------------------------------------------------

    def delete_folder(
        self,
        folder_path
    ):
        """
        Delete a folder recursively.

        Parameters
        ----------
        folder_path : str

        Returns
        -------
        bool
        """

        if not folder_path:

            return False

        try:

            path = Path(folder_path)

            if not path.exists():

                return False

            shutil.rmtree(path)

            print(
                f"Folder Deleted : {path}"
            )

            return True

        except Exception as error:

            print(
                f"Delete Folder Error : {error}"
            )

            return False

    # --------------------------------------------------
    # Move Folder
    # --------------------------------------------------

    def move_folder(
        self,
        source_folder,
        destination_folder
    ):
        """
        Move a folder.

        Parameters
        ----------
        source_folder : str

        destination_folder : str

        Returns
        -------
        bool
        """

        if not source_folder or not destination_folder:

            return False

        try:

            source = Path(source_folder)

            destination = Path(destination_folder)

            if not source.exists():

                return False

            shutil.move(

                str(source),

                str(destination)

            )

            print(

                f"Folder Moved : {source}"

            )

            return True

        except Exception as error:

            print(

                f"Move Folder Error : {error}"

            )

            return False

    # --------------------------------------------------
    # Copy Folder
    # --------------------------------------------------

    def copy_folder(
        self,
        source_folder,
        destination_folder
    ):
        """
        Copy a folder.

        Parameters
        ----------
        source_folder : str

        destination_folder : str

        Returns
        -------
        bool
        """

        if not source_folder or not destination_folder:

            return False

        try:

            source = Path(source_folder)

            destination = Path(destination_folder)

            if not source.exists():

                return False

            destination = destination / source.name

            shutil.copytree(

                source,

                destination,

                dirs_exist_ok=True

            )

            print(

                f"Folder Copied : {destination}"

            )

            return True

        except Exception as error:

            print(

                f"Copy Folder Error : {error}"

            )

            return False

    # --------------------------------------------------
    # Empty Recycle Bin
    # --------------------------------------------------

    def empty_recycle_bin(self):
        """
        Empty Windows Recycle Bin.

        Returns
        -------
        bool
        """

        try:

            subprocess.run(

                [
                    "powershell",
                    "-Command",
                    "Clear-RecycleBin -Force"
                ],

                check=True,

                capture_output=True

            )

            print(

                "Recycle Bin Emptied."

            )

            return True

        except Exception as error:

            print(

                f"Recycle Bin Error : {error}"

            )

            return False

    # --------------------------------------------------
    # Open Folder
    # --------------------------------------------------

    def open_folder(
        self,
        folder_name
    ):
        """
        Open a special folder.

        Parameters
        ----------
        folder_name : str

        Returns
        -------
        bool
        """

        if not folder_name:

            return False

        folder_name = folder_name.lower().strip()

        if folder_name not in self.special_folders:

            return False

        folder = self.special_folders[folder_name]

        try:

            # Windows Shell Locations

            if isinstance(folder, str):

                subprocess.Popen(

                    [
                        "explorer",
                        folder
                    ]

                )

                return True

            # Normal Folder

            if folder is not None and folder.exists():

                os.startfile(str(folder))

                return True

            return False

        except Exception as error:

            print(

                f"Folder Open Error : {error}"

            )

            return False