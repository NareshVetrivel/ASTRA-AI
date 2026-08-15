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
import time

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
                os.path.expandvars(
                    r"%USERPROFILE%\Desktop"
                ),
                os.path.expandvars(
                    r"%OneDrive%\Desktop"
                )
            ),

            "documents": self.resolve_folder(
                os.path.expandvars(
                    r"%USERPROFILE%\Documents"
                ),
                os.path.expandvars(
                    r"%OneDrive%\Documents"
                )
            ),

            "downloads": self.resolve_folder(
                os.path.expandvars(
                    r"%USERPROFILE%\Downloads"
                ),
                os.path.expandvars(
                    r"%OneDrive%\Downloads"
                )
            ),

            "pictures": self.resolve_folder(
                os.path.expandvars(
                    r"%USERPROFILE%\Pictures"
                ),
                os.path.expandvars(
                    r"%OneDrive%\Pictures"
                )
            ),

            "videos": self.resolve_folder(
                os.path.expandvars(
                    r"%USERPROFILE%\Videos"
                ),
                os.path.expandvars(
                    r"%OneDrive%\Videos"
                )
            ),

            "music": self.resolve_folder(
                os.path.expandvars(
                    r"%USERPROFILE%\Music"
                ),
                os.path.expandvars(
                    r"%OneDrive%\Music"
                )
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

    # ==================================================
    # Resolve Special Folder
    # ==================================================

    def resolve_folder(
        self,
        *locations
    ):
        """
        Return the first existing folder.
        """

        for location in locations:

            try:

                path = Path(location)

                if path.exists():

                    print(
                        f"Resolved Folder : {path}"
                    )

                    return path

            except Exception:

                continue

        return None

    # ==================================================
    # Create Folder
    # ==================================================

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

            path = Path(
                os.path.expandvars(
                    os.path.expanduser(
                        str(folder_path).strip()
                    )
                )
            )

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

    # ==================================================
    # Rename Folder
    # ==================================================

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

            source = Path(
                os.path.expandvars(
                    os.path.expanduser(
                        str(source_folder).strip()
                    )
                )
            )

            new_name = str(
                new_name
            ).strip()

            if not source.exists():

                print(
                    "\nFolder not found."
                )

                return False

            if not source.is_dir():

                print(
                    "\nSource is not a folder."
                )

                return False

            # -----------------------------------------
            # Prevent invalid Windows folder names
            # -----------------------------------------

            invalid_characters = (
                '\\/:*?"<>|'
            )

            if any(
                character in new_name
                for character in invalid_characters
            ):

                print(
                    "\nInvalid folder name."
                )

                return False

            destination = (
                source.parent
                /
                new_name
            )

            if destination.exists():

                print(
                    "\nDestination folder already exists."
                )

                return False

            source.rename(
                destination
            )

            print(
                f"Folder Renamed : {destination}"
            )

            return True

        except Exception as error:

            print(
                f"Rename Folder Error : {error}"
            )

            return False

    # ==================================================
    # Confirmation
    # ==================================================

    def confirm_delete(
        self,
        folder_path
    ):
        """
        Ask user for confirmation before
        recursively deleting a folder.

        Returns
        -------
        bool
        """

        print("\n================================")
        print("Delete Folder")
        print("--------------------------------")
        print(folder_path)
        print("--------------------------------")
        print("WARNING : This will delete the")
        print("folder and all contents inside it.")
        print("--------------------------------")
        print("Say Yes")
        print("or")
        print("Say No")
        print("================================")

        try:

            answer = input(
                "\nConfirm (yes/no): "
            ).strip().lower()

        except (EOFError, KeyboardInterrupt):

            print(
                "\nConfirmation cancelled."
            )

            return False

        if answer in (
            "yes",
            "y",
            "yeah",
            "yep",
            "ok",
            "okay",
            "confirm"
        ):

            return True

        print(
            "\nFolder deletion cancelled."
        )

        return False

    # ==================================================
    # Delete Folder
    # ==================================================

    def delete_folder(
        self,
        folder_path
    ):
        """
        Delete a folder recursively.

        A confirmation is required before
        deletion.

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

            path = Path(
                os.path.expandvars(
                    os.path.expanduser(
                        str(folder_path).strip()
                    )
                )
            )

            if not path.exists():

                print(
                    "\nFolder not found."
                )

                return False

            if not path.is_dir():

                print(
                    "\nPath is not a folder."
                )

                return False

            # -----------------------------------------
            # Safety Protection
            # -----------------------------------------

            resolved = path.resolve()

            protected_paths = {

                Path(
                    os.environ.get(
                        "USERPROFILE",
                        str(self.home)
                    )
                ).resolve(),

                Path("C:/").resolve(),

                Path("D:/").resolve(),

                Path("E:/").resolve()

            }

            if resolved in protected_paths:

                print(
                    "\nProtected system/location folder."
                )

                print(
                    "Deletion blocked."
                )

                return False

            # -----------------------------------------
            # Confirmation
            # -----------------------------------------

            if not self.confirm_delete(
                resolved
            ):

                return False

            # -----------------------------------------
            # Delete
            # -----------------------------------------

            shutil.rmtree(
                resolved
            )

            print(
                f"Folder Deleted : {resolved}"
            )

            return True

        except Exception as error:

            print(
                f"Delete Folder Error : {error}"
            )

            return False

    # ==================================================
    # Move Folder
    # ==================================================

    def move_folder(
        self,
        source_folder,
        destination_folder
    ):
        """
        Move a folder safely.

        Verifies source/destination, prevents self-nesting, prevents
        overwriting an existing target, performs the move, and verifies
        the resulting filesystem state.
        """

        if not source_folder or not destination_folder:
            return False

        try:
            source = Path(
                os.path.expandvars(
                    os.path.expanduser(
                        str(source_folder).strip()
                    )
                )
            ).resolve()

            destination = Path(
                os.path.expandvars(
                    os.path.expanduser(
                        str(destination_folder).strip()
                    )
                )
            ).resolve()

            if not source.exists():
                print("\nSource folder not found.")
                return False

            if not source.is_dir():
                print("\nSource is not a folder.")
                return False

            if not destination.exists():
                print("\nDestination folder not found.")
                return False

            if not destination.is_dir():
                print("\nDestination is not a folder.")
                return False

            if source == destination:
                print("\nSource and destination are the same folder.")
                return False

            # Prevent moving folder into itself.
            try:
                destination.relative_to(source)
                print("\nCannot move a folder into itself.")
                return False
            except ValueError:
                pass

            target = destination / source.name

            if target.exists():
                print("\nDestination folder already exists.")
                return False

            shutil.move(
                str(source),
                str(destination)
            )

            # shutil.move(source, destination) creates destination/source.
            if not target.exists() or not target.is_dir():
                print("\nMove verification failed.")
                return False

            if source.exists():
                print("\nMove verification failed: original folder still exists.")
                return False

            print(f"Folder Moved : {target}")
            return True

        except Exception as error:
            print(f"Move Folder Error : {error}")
            return False

    # ==================================================
    # Copy Folder
    # ==================================================

    def copy_folder(
        self,
        source_folder,
        destination_folder
    ):
        """
        Copy a folder safely.

        Prevents self-copying and overwrite, then verifies the target.
        """

        if not source_folder or not destination_folder:
            return False

        try:
            source = Path(
                os.path.expandvars(
                    os.path.expanduser(
                        str(source_folder).strip()
                    )
                )
            ).resolve()

            destination = Path(
                os.path.expandvars(
                    os.path.expanduser(
                        str(destination_folder).strip()
                    )
                )
            ).resolve()

            if not source.exists():
                print("\nSource folder not found.")
                return False

            if not source.is_dir():
                print("\nSource is not a folder.")
                return False

            if not destination.exists():
                print("\nDestination folder not found.")
                return False

            if not destination.is_dir():
                print("\nDestination is not a folder.")
                return False

            if source == destination:
                print("\nSource and destination are the same folder.")
                return False

            # Prevent copying a folder into itself.
            try:
                destination.relative_to(source)
                print("\nCannot copy a folder into itself.")
                return False
            except ValueError:
                pass

            target = destination / source.name

            if target.exists():
                print("\nDestination folder already exists.")
                return False

            shutil.copytree(
                source,
                target
            )

            if not target.exists() or not target.is_dir():
                print("\nCopy verification failed.")
                return False

            print(f"Folder Copied : {target}")
            return True

        except Exception as error:
            print(f"Copy Folder Error : {error}")
            return False

    # ==================================================
    # Empty Recycle Bin
    # ==================================================

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

                capture_output=True,

                text=True

            )

            print(
                "\nRecycle Bin Emptied."
            )

            return True

        except Exception as error:

            print(
                f"\nRecycle Bin Error : {error}"
            )

            return False

    # ==================================================
    # Open Folder
    # ==================================================

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

        folder_name = str(
            folder_name
        ).lower().strip()

        # -----------------------------------------
        # Direct Path Support
        # -----------------------------------------

        try:

            direct_path = Path(
                os.path.expandvars(
                    os.path.expanduser(
                        folder_name
                    )
                )
            )

            if direct_path.exists():

                if direct_path.is_dir():

                    os.startfile(
                        str(direct_path.resolve())
                    )

                    return True

                return False

        except Exception:

            pass

        # -----------------------------------------
        # Special Folder
        # -----------------------------------------

        if folder_name not in self.special_folders:

            return False

        folder = self.special_folders[
            folder_name
        ]

        try:

            # -----------------------------------------
            # Windows Shell Locations
            # -----------------------------------------

            if isinstance(
                folder,
                str
            ):

                subprocess.Popen(

                    [
                        "explorer",
                        folder
                    ]

                )

                return True

            # -----------------------------------------
            # Normal Folder
            # -----------------------------------------

            if (
                folder is not None
                and
                folder.exists()
            ):

                os.startfile(
                    str(folder)
                )

                return True

            return False

        except Exception as error:

            print(
                f"Folder Open Error : {error}"
            )

            return False