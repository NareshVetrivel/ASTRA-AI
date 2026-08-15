"""
File Manager Module

Provides file management operations
for ASTRA-AI.

Supported Operations
--------------------

• Find File
• Open File
• Create File
• Delete File
• Rename File
• Copy File
• Move File
• Compress File
• Extract ZIP
• Search By Extension
• Search By Size
• Search By Date

ASTRA-AI V1
"""

import os
import shutil
import time
import time
import zipfile

from pathlib import Path
from datetime import datetime, timedelta

from send2trash import send2trash

from automation.file_finder import FileFinder
from database.database_manager import DatabaseManager


class FileManager:
    """
    Manage user files.
    """

    def __init__(
        self,
        whisper=None
    ):

        self.home = Path.home()

        self.file_finder = FileFinder()

        self.database = DatabaseManager()

        self.whisper = whisper

        self.tts = None

        # --------------------------------------------------
        # Default Search Locations
        # --------------------------------------------------

        self.default_search_locations = [

            self._validate_destination("desktop"),

            self._validate_destination("documents"),

            self._validate_destination("downloads"),

            self._validate_destination("pictures"),

            self._validate_destination("videos"),

            self._validate_destination("music"),

            Path("E:/")

        ]

        self.default_search_locations = [

            folder

            for folder in self.default_search_locations

            if folder is not None

        ]

    # ======================================================
    # Text To Speech
    # ======================================================

    def set_tts(
        self,
        tts
    ):
        """
        Attach TTS module.
        """

        self.tts = tts

    # ======================================================
    # Success Message
    # ======================================================

    def success(
        self,
        message
    ):
        """
        Print + Speak success message.
        """

        print("\n===================================")
        print(message)
        print("===================================")

        if self.tts:

            try:

                self.tts.speak(
                    message
                )

            except Exception:

                pass

    # ======================================================
    # Error Message
    # ======================================================

    def error(
        self,
        message
    ):
        """
        Print + Speak error message.
        """

        print("\n===================================")
        print(message)
        print("===================================")

        if self.tts:

            try:

                self.tts.speak(
                    message
                )

            except Exception:

                pass

    # ======================================================
    # Confirmation
    # ======================================================

    def confirm_action(
        self,
        action,
        file_path
    ):
        """
        Ask confirmation before
        dangerous operations.
        """

        print("\n================================")
        print(action)
        print("--------------------------------")
        print(file_path)
        print("--------------------------------")
        print("Say Yes")
        print("or")
        print("Say No")
        print("================================")

        if self.whisper is None:

            answer = input(
                "\nConfirm (yes/no): "
            ).strip().lower()

        else:

            try:

                answer = (
                    self.whisper
                    .listen_confirmation()
                )

            except Exception:

                answer = None

            if answer is None:

                print(
                    "\nConfirmation timeout."
                )

                return False

            answer = str(
                answer
            ).strip().lower()

        if answer in [

            "yes",
            "yeah",
            "ok",
            "okay",
            "confirm",
            "delete"

        ]:

            return True

        self.error(
            "Operation cancelled."
        )

        return False

    # ======================================================
    # Refresh Database
    # ======================================================

    def refresh_database(
        self,
        file_path
    ):
        """
        Refresh one file inside database.
        """

        try:

            self.database.refresh_file(
                str(file_path)
            )

        except Exception as error:

            print(
                f"Database Refresh Warning : {error}"
            )

    # ======================================================
    # Remove Database Entry
    # ======================================================

    def remove_database_entry(
        self,
        file_path
    ):
        """
        Remove file from database.
        """

        try:

            self.database.delete_file(
                str(file_path)
            )

        except Exception as error:

            print(
                f"Database Delete Warning : {error}"
            )

    # ======================================================
    # Validate Simple File Name
    # ======================================================

    def _validate_filename(
        self,
        filename
    ):
        """
        Validate a simple filename.

        This method intentionally accepts only
        filename values, not full filesystem paths.
        """

        if filename is None:

            return None

        filename = str(
            filename
        ).strip()

        if not filename:

            return None

        invalid = '\\/:*?"<>|'

        for character in invalid:

            if character in filename:

                self.error(
                    "Invalid file name."
                )

                return None

        return filename

    # ======================================================
    # Resolve File Input
    # ======================================================

    def _resolve_file_input(
        self,
        file_input
    ):
        """
        Resolve either:

        1. A full/relative filesystem path
        2. A normal filename

        Existing full paths are returned directly.
        Otherwise FileFinder is used.
        """

        if file_input is None:

            return None

        value = str(
            file_input
        ).strip()

        if not value:

            return None

        # --------------------------------------------------
        # Direct Existing Path
        # --------------------------------------------------

        try:

            direct_path = (
                Path(value)
                .expanduser()
            )

            if direct_path.exists():

                if direct_path.is_file():

                    return direct_path.resolve()

                self.error(
                    "Path is not a file."
                )

                return None

        except Exception:

            pass

        # --------------------------------------------------
        # Normal Filename Search
        # --------------------------------------------------

        simple_name = (
            self._validate_filename(
                value
            )
        )

        if simple_name is None:

            return None

        return self.find_file(
            simple_name
        )

    # ======================================================
    # Validate Destination
    # ======================================================

    def _validate_destination(
        self,
        destination
    ):
        """
        Validate destination folder.

        Supports:

        • Desktop
        • Documents
        • Downloads
        • Pictures
        • Videos
        • Music
        • Absolute paths
        • Relative paths
        """

        if destination is None:

            return None

        destination = str(
            destination
        ).strip()

        if not destination:

            return None

        destination_lower = (
            destination.lower()
        )

        home = Path.home()

        common_folders = {

            "desktop":
                home / "Desktop",

            "documents":
                home / "Documents",

            "downloads":
                home / "Downloads",

            "pictures":
                home / "Pictures",

            "videos":
                home / "Videos",

            "music":
                home / "Music"

        }

        # --------------------------------------------------
        # Common Folder
        # --------------------------------------------------

        if destination_lower in common_folders:

            folder = common_folders[
                destination_lower
            ]

            if folder.exists():

                return folder

            # OneDrive fallback

            one_drive = (
                home
                /
                "OneDrive"
                /
                folder.name
            )

            if one_drive.exists():

                return one_drive

            self.error(
                "Destination folder not found."
            )

            return None

        # --------------------------------------------------
        # Direct Filesystem Path
        # --------------------------------------------------

        try:

            folder = Path(
                os.path.expandvars(
                    os.path.expanduser(
                        destination
                    )
                )
            )

        except Exception:

            self.error(
                "Invalid destination path."
            )

            return None

        if not folder.exists():

            self.error(
                "Destination folder not found."
            )

            return None

        if not folder.is_dir():

            self.error(
                "Destination is not a valid folder."
            )

            return None

        return folder.resolve()

    # ======================================================
    # Find File
    # ======================================================

    def find_file(
        self,
        filename
    ):
        """
        Search for a file using bounded filesystem scanning.

        Exact filename/stem matches are preferred. SQLite/FileFinder
        remains the fallback. The scan is bounded so a voice command
        cannot block ASTRA for several minutes.
        """

        if filename is None:
            return None

        value = str(filename).strip()

        if not value:
            return None

        # Direct path
        try:
            direct_path = Path(
                os.path.expandvars(
                    os.path.expanduser(value)
                )
            )

            if direct_path.exists():
                if direct_path.is_file():
                    return direct_path.resolve()
                return None

        except Exception:
            pass

        filename = self._validate_filename(value)

        if filename is None:
            return None

        search_name = filename.strip().lower()

        # Bounded filesystem search
        max_files_scanned = 40_000
        max_scan_seconds = 3.0

        started_at = time.monotonic()
        files_scanned = 0
        timed_out = False

        excluded_directories = {
            "$recycle.bin",
            "system volume information",
            "node_modules",
            ".git",
            "__pycache__",
            ".venv",
            "venv",
            "appdata",
            "windows",
            "program files",
            "program files (x86)",
        }

        for location in self.default_search_locations:

            if location is None or not location.exists():
                continue

            if (
                files_scanned >= max_files_scanned
                or time.monotonic() - started_at >= max_scan_seconds
            ):
                timed_out = True
                break

            try:
                for root, dirs, files in os.walk(
                    location,
                    topdown=True
                ):

                    dirs[:] = [
                        directory
                        for directory in dirs
                        if directory.lower()
                        not in excluded_directories
                    ]

                    for file in files:

                        files_scanned += 1

                        if (
                            files_scanned >= max_files_scanned
                            or (
                                time.monotonic() - started_at
                                >= max_scan_seconds
                            )
                        ):
                            timed_out = True
                            break

                        file_path = Path(root) / file

                        try:
                            actual_name = file_path.name.lower()
                            actual_stem = file_path.stem.lower()

                            if search_name == actual_name:
                                print("\nExact File Match :")
                                print(file_path)
                                return file_path.resolve()

                            if search_name == actual_stem:
                                print("\nExact File Stem Match :")
                                print(file_path)
                                return file_path.resolve()

                        except (
                            PermissionError,
                            FileNotFoundError,
                            OSError,
                            RuntimeError,
                        ):
                            continue

                    if timed_out:
                        break

            except (
                PermissionError,
                FileNotFoundError,
                OSError,
                RuntimeError,
            ):
                continue

        # SQLite/FileFinder fallback
        try:
            try:
                self.file_finder.close()
            except Exception:
                pass

            self.file_finder = FileFinder()

            path = self.file_finder.find_file(filename)

            if path:
                file_path = Path(path)

                if file_path.exists() and file_path.is_file():
                    print("\nDatabase File Match :")
                    print(file_path)
                    return file_path.resolve()

                try:
                    self.remove_database_entry(file_path)
                except Exception:
                    pass

        except Exception as error:
            print(f"FileFinder Warning : {error}")

        # Do not start another recursive scan after timeout.
        if timed_out:
            return None

        # Bounded partial-name fallback
        partial_started_at = time.monotonic()
        partial_timeout = 2.0

        for location in self.default_search_locations:

            if location is None or not location.exists():
                continue

            try:
                for root, dirs, files in os.walk(
                    location,
                    topdown=True
                ):

                    dirs[:] = [
                        directory
                        for directory in dirs
                        if directory.lower()
                        not in excluded_directories
                    ]

                    for file in files:

                        if (
                            time.monotonic() - partial_started_at
                            >= partial_timeout
                        ):
                            return None

                        file_path = Path(root) / file

                        try:
                            actual_name = file_path.name.lower()
                            actual_stem = file_path.stem.lower()

                            if (
                                search_name in actual_stem
                                or search_name in actual_name
                            ):
                                print("\nPartial File Match :")
                                print(file_path)
                                return file_path.resolve()

                        except (
                            PermissionError,
                            FileNotFoundError,
                            OSError,
                            RuntimeError,
                        ):
                            continue

            except (
                PermissionError,
                FileNotFoundError,
                OSError,
                RuntimeError,
            ):
                continue

        return None

    # ======================================================
    # Delete File
    # ======================================================

    def delete_file(
        self,
        filename
    ):
        """
        Delete a file.

        Supports filename and full path.

        Confirmation is handled by CommandDispatcher.
        """

        file_path = (
            self._resolve_file_input(
                filename
            )
        )

        if file_path is None:

            self.error(
                "File not found."
            )

            return False

        try:

            # --------------------------------------------------
            # Delete From Windows Recycle Bin
            # --------------------------------------------------

            send2trash(
                str(file_path)
            )

            # --------------------------------------------------
            # Remove From SQLite
            # --------------------------------------------------

            self.remove_database_entry(
                file_path
            )

            self.success(
                "File deleted successfully."
            )

            print(
                file_path
            )

            return True

        except Exception as error:

            self.error(
                f"Delete failed : {error}"
            )

            return False

    # ======================================================
    # Open File
    # ======================================================

    def open_file(
        self,
        filename
    ):
        """
        Open a file.

        Supports filename and full path.
        """

        file_path = (
            self._resolve_file_input(
                filename
            )
        )

        if file_path is None:

            self.error(
                "File not found."
            )

            return False

        if not file_path.exists():

            self.remove_database_entry(
                file_path
            )

            self.error(
                "File does not exist."
            )

            return False

        try:

            os.startfile(
                str(file_path)
            )

            self.success(
                "File opened successfully."
            )

            print(
                file_path
            )

            return True

        except Exception as error:

            self.error(
                f"Open failed : {error}"
            )

            return False

    # ======================================================
    # Rename File
    # ======================================================

    def rename_file(
        self,
        old_name,
        new_name
    ):
        """
        Rename a file safely.

        Features:
        • Finds the real file from filesystem/database
        • Preserves extension when omitted
        • Prevents overwrite
        • Performs physical rename
        • Verifies physical rename
        • Updates SQLite
        • Rolls back filesystem rename if required
        """

        # --------------------------------------------------
        # Resolve Existing File
        # --------------------------------------------------

        file_path = (
            self._resolve_file_input(
                old_name
            )
        )

        if file_path is None:

            self.error(
                f"File not found: {old_name}"
            )

            return False

        # --------------------------------------------------
        # Final Source Validation
        # --------------------------------------------------

        file_path = Path(
            file_path
        ).resolve()

        if not file_path.exists():

            self.error(
                f"File does not exist: {file_path}"
            )

            self.remove_database_entry(
                file_path
            )

            return False

        if not file_path.is_file():

            self.error(
                "Selected path is not a file."
            )

            return False

        # --------------------------------------------------
        # Validate New Name
        # --------------------------------------------------

        new_name = str(
            new_name or ""
        ).strip()

        # Remove accidental punctuation from STT
        new_name = new_name.rstrip(
            ".,!?;:"
        ).strip()

        if not new_name:

            self.error(
                "Invalid new file name."
            )

            return False

        invalid = '\\/:*?"<>|'

        if any(
            character in new_name
            for character in invalid
        ):

            self.error(
                "Invalid new file name."
            )

            return False

        # --------------------------------------------------
        # Build Destination Path
        # --------------------------------------------------

        new_name_path = Path(
            new_name
        )

        if new_name_path.suffix:

            final_name = new_name

        else:

            final_name = (
                new_name
                +
                file_path.suffix
            )

        new_file = (
            file_path.parent
            /
            final_name
        ).resolve()

        # --------------------------------------------------
        # Same File Check
        # --------------------------------------------------

        if new_file == file_path:

            self.error(
                "New file name is same as current name."
            )

            return False

        # --------------------------------------------------
        # Destination Exists
        # --------------------------------------------------

        if new_file.exists():

            self.error(
                f"File already exists: {new_file.name}"
            )

            return False

        old_path = str(
            file_path
        )

        new_path = str(
            new_file
        )

        print(
            "\n==================================="
        )
        print(
            "RENAME OPERATION"
        )
        print(
            "==================================="
        )
        print(
            f"Source      : {old_path}"
        )
        print(
            f"Destination : {new_path}"
        )
        print(
            "==================================="
        )

        # --------------------------------------------------
        # Physical Rename
        # --------------------------------------------------

        try:

            file_path.rename(
                new_file
            )

        except Exception as error:

            self.error(
                f"Physical rename failed : {error}"
            )

            return False

        # --------------------------------------------------
        # IMPORTANT:
        # Verify that the physical filesystem
        # actually contains the new file.
        # --------------------------------------------------

        if not new_file.exists():

            self.error(
                "Rename verification failed. New file was not created."
            )

            # Attempt rollback
            try:

                if (
                    file_path.exists()
                    is False
                    and
                    new_file.exists()
                ):

                    new_file.rename(
                        file_path
                    )

            except Exception:

                pass

            return False

        # --------------------------------------------------
        # Verify Old File Is Gone
        # --------------------------------------------------

        if file_path.exists():

            self.error(
                "Rename verification failed. Original file still exists."
            )

            # Try rollback / restore original state
            try:

                if new_file.exists():

                    new_file.rename(
                        file_path
                    )

            except Exception:

                pass

            return False

        # --------------------------------------------------
        # SQLite Update
        # --------------------------------------------------

        try:

            # Remove old database record
            self.remove_database_entry(
                old_path
            )

            # Add new database record
            self.refresh_database(
                new_file
            )

        except Exception as error:

            print(
                f"Database update warning : {error}"
            )

        # --------------------------------------------------
        # Final Physical Verification
        # --------------------------------------------------

        if (
            not new_file.exists()
            or
            file_path.exists()
        ):

            self.error(
                "Rename completed with filesystem verification failure."
            )

            return False

        # --------------------------------------------------
        # SUCCESS
        # --------------------------------------------------

        self.success(
            "File renamed successfully."
        )

        print(
            f"Old Path : {old_path}"
        )

        print(
            f"New Path : {new_path}"
        )

        return True

    # ======================================================
    # Create File
    # ======================================================

    def create_file(
        self,
        filename,
        extension=".txt",
        content=""
    ):
        """
        Create a new file.
        """

        if filename is None:

            self.error(
                "File name is required."
            )

            return False

        raw_filename = str(
            filename
        ).strip()

        if not raw_filename:

            self.error(
                "File name is required."
            )

            return False

        try:

            path_value = Path(
                os.path.expandvars(
                    os.path.expanduser(
                        raw_filename
                    )
                )
            )

            is_explicit_path = (

                path_value.is_absolute()

                or

                bool(
                    path_value.parent
                    !=
                    Path(".")
                )

                or

                (
                    len(raw_filename) >= 2
                    and
                    raw_filename[1] == ":"
                )

            )

            if is_explicit_path:

                file_path = path_value

                if not file_path.suffix:

                    extension_value = str(
                        extension or ".txt"
                    ).strip()

                    if not extension_value:

                        extension_value = ".txt"

                    if not extension_value.startswith("."):

                        extension_value = (
                            "."
                            +
                            extension_value
                        )

                    file_path = Path(
                        str(file_path)
                        +
                        extension_value
                    )

                name_only = file_path.name

                invalid = '\\/:*?"<>|'

                for character in invalid:

                    if character in name_only:

                        self.error(
                            "Invalid file name."
                        )

                        return False

            else:

                clean_name = (
                    self._validate_filename(
                        raw_filename
                    )
                )

                if clean_name is None:

                    return False

                documents = (
                    self._validate_destination(
                        "documents"
                    )
                )

                if documents is None:

                    self.error(
                        "Documents folder not found."
                    )

                    return False

                documents.mkdir(
                    parents=True,
                    exist_ok=True
                )

                extension_value = str(
                    extension or ".txt"
                ).strip()

                if not extension_value:

                    extension_value = ".txt"

                if not extension_value.startswith("."):

                    extension_value = (
                        "."
                        +
                        extension_value
                    )

                if clean_name.lower().endswith(
                    extension_value.lower()
                ):

                    file_path = (
                        documents
                        /
                        clean_name
                    )

                else:

                    file_path = (
                        documents
                        /
                        (
                            clean_name
                            +
                            extension_value
                        )
                    )

            parent = file_path.parent

            parent.mkdir(
                parents=True,
                exist_ok=True
            )

            if file_path.exists():

                self.error(
                    "File already exists."
                )

                return False

            with open(
                file_path,
                "w",
                encoding="utf-8"
            ) as file:

                if content is not None:

                    file.write(
                        str(content)
                    )

            time.sleep(
                0.2
            )

            self.refresh_database(
                file_path
            )

            try:

                self.file_finder.close()

            except Exception:

                pass

            self.file_finder = FileFinder()

            self.success(
                "File created successfully."
            )

            print(
                file_path
            )

            return True

        except Exception as error:

            self.error(
                f"File creation failed : {error}"
            )

            return False

    # ======================================================
    # Copy File
    # ======================================================

    def copy_file(
        self,
        filename,
        destination
    ):
        """
        Copy a file to destination folder.
        """

        file_path = (
            self._resolve_file_input(
                filename
            )
        )

        destination = (
            self._validate_destination(
                destination
            )
        )

        if file_path is None:

            self.error(
                "File not found."
            )

            return False

        if destination is None:

            return False

        # --------------------------------------------------
        # Final Source Validation
        # --------------------------------------------------

        if (
            not file_path.exists()
            or
            not file_path.is_file()
        ):

            self.error(
                "Source file does not exist."
            )

            return False

        destination_file = (
            destination
            /
            file_path.name
        )

        if destination_file.exists():

            self.error(
                "File already exists in destination."
            )

            return False

        try:

            shutil.copy2(
                file_path,
                destination_file
            )

            self.refresh_database(
                destination_file
            )

            self.success(
                "File copied successfully."
            )

            print(
                file_path
            )

            print(
                "\nTo :"
            )

            print(
                destination_file
            )

            return True

        except Exception as error:

            self.error(
                f"Copy failed : {error}"
            )

            return False

    # ======================================================
    # Move File
    # ======================================================

    def move_file(
        self,
        filename,
        destination
    ):
        """
        Move a file to destination folder.

        Updates the SQLite index after the
        filesystem move.
        """

        # --------------------------------------------------
        # Resolve File
        # --------------------------------------------------

        file_path = (
            self._resolve_file_input(
                filename
            )
        )

        if file_path is None:

            self.error(
                "File not found."
            )

            return False

        # --------------------------------------------------
        # Validate Destination
        # --------------------------------------------------

        destination = (
            self._validate_destination(
                destination
            )
        )

        if destination is None:

            return False

        # --------------------------------------------------
        # Destination File
        # --------------------------------------------------

        destination_file = (
            destination
            /
            file_path.name
        )

        # --------------------------------------------------
        # Same Location Check
        # --------------------------------------------------

        try:

            if (
                destination_file.resolve()
                ==
                file_path.resolve()
            ):

                self.error(
                    "File is already in the destination folder."
                )

                return False

        except Exception:

            pass

        # --------------------------------------------------
        # Destination Exists
        # --------------------------------------------------

        if destination_file.exists():

            self.error(
                "File already exists in destination."
            )

            return False

        old_path = str(
            file_path.resolve()
        )

        new_path = str(
            destination_file.resolve()
        )

        try:

            # --------------------------------------------------
            # Move Physical File
            # --------------------------------------------------

            shutil.move(
                old_path,
                new_path
            )

            # --------------------------------------------------
            # Update SQLite Safely
            #
            # Remove old path and refresh new path.
            # This avoids UNIQUE(full_path) conflicts.
            # --------------------------------------------------

            self.remove_database_entry(
                old_path
            )

            self.refresh_database(
                destination_file
            )

            self.success(
                "File moved successfully."
            )

            print(
                destination_file
            )

            return True

        except Exception as error:

            self.error(
                f"Move failed : {error}"
            )

            return False

    # ======================================================
    # Compress File
    # ======================================================

    def compress_file(
        self,
        filename
    ):
        """
        Compress a file into a ZIP archive.

        Supports:
        • Full filesystem path
        • Relative path
        • Normal filename
        • Filename without extension

        Example:
            compress_file("demo.txt")
            -> demo.zip
        """

        # --------------------------------------------------
        # Resolve Source File
        # --------------------------------------------------

        file_path = self._resolve_file_input(
            filename
        )

        if file_path is None:

            self.error(
                "File not found."
            )

            return False

        file_path = Path(
            file_path
        ).resolve()

        # --------------------------------------------------
        # Validate Source
        # --------------------------------------------------

        if not file_path.exists():

            self.error(
                "File does not exist."
            )

            return False

        if not file_path.is_file():

            self.error(
                "Selected path is not a file."
            )

            return False

        # --------------------------------------------------
        # ZIP Destination
        #
        # Example:
        # demo.txt -> demo.zip
        # report.pdf -> report.zip
        # --------------------------------------------------

        zip_path = (
            file_path.parent
            /
            f"{file_path.stem}.zip"
        ).resolve()

        # --------------------------------------------------
        # Prevent Overwrite
        # --------------------------------------------------

        if zip_path.exists():

            self.error(
                "ZIP archive already exists."
            )

            return False

        print(
            "\n==================================="
        )

        print(
            "ZIP COMPRESSION"
        )

        print(
            "==================================="
        )

        print(
            f"Source      : {file_path}"
        )

        print(
            f"ZIP Archive : {zip_path}"
        )

        print(
            "==================================="
        )

        # --------------------------------------------------
        # Create ZIP
        # --------------------------------------------------

        try:

            with zipfile.ZipFile(
                zip_path,
                mode="w",
                compression=zipfile.ZIP_DEFLATED
            ) as archive:

                archive.write(
                    file_path,
                    arcname=file_path.name
                )

            # --------------------------------------------------
            # Verify ZIP Physically Exists
            # --------------------------------------------------

            if not zip_path.exists():

                self.error(
                    "ZIP creation verification failed."
                )

                return False

            # --------------------------------------------------
            # Verify ZIP Is Valid
            # --------------------------------------------------

            if not zipfile.is_zipfile(
                zip_path
            ):

                self.error(
                    "Created file is not a valid ZIP archive."
                )

                try:

                    zip_path.unlink()

                except Exception:

                    pass

                return False

            # --------------------------------------------------
            # Refresh Database
            # --------------------------------------------------

            self.refresh_database(
                zip_path
            )

            # --------------------------------------------------
            # Refresh File Finder Cache
            # --------------------------------------------------

            try:

                self.file_finder.close()

            except Exception:

                pass

            try:

                self.file_finder = FileFinder()

            except Exception:

                pass

            # --------------------------------------------------
            # Success
            # --------------------------------------------------

            self.success(
                "ZIP archive created successfully."
            )

            print(
                f"ZIP File : {zip_path}"
            )

            return True

        except Exception as error:

            self.error(
                f"ZIP creation failed : {error}"
            )

            # --------------------------------------------------
            # Cleanup Partial ZIP
            # --------------------------------------------------

            try:

                if zip_path.exists():

                    zip_path.unlink()

            except Exception:

                pass

            return False


    # ======================================================
    # Extract ZIP
    # ======================================================

    def extract_zip(
        self,
        filename
    ):
        """
        Extract a ZIP archive.

        Supports:
        • Full ZIP path
        • ZIP filename
        • Filename without .zip
        • Voice-style input such as:
          "extract demo.zip"

        Extracts into a folder with the
        same name as the ZIP archive.

        Example:
            demo.zip
                ↓
            demo/
        """

        if filename is None:

            self.error(
                "ZIP file is required."
            )

            return False

        raw_filename = str(
            filename
        ).strip()

        if not raw_filename:

            self.error(
                "ZIP file is required."
            )

            return False

        # --------------------------------------------------
        # Remove common voice-command words
        # --------------------------------------------------

        clean_name = raw_filename.strip()

        prefixes = [
            "extract ",
            "unzip ",
            "extract zip ",
            "unzip file ",
            "extract file "
        ]

        lower_name = clean_name.lower()

        for prefix in prefixes:

            if lower_name.startswith(prefix):

                clean_name = clean_name[
                    len(prefix):
                ].strip()

                break

        # --------------------------------------------------
        # Direct Existing Path
        # --------------------------------------------------

        file_path = None

        try:

            direct_path = Path(
                os.path.expandvars(
                    os.path.expanduser(
                        clean_name
                    )
                )
            )

            if direct_path.exists():

                if direct_path.is_file():

                    file_path = (
                        direct_path.resolve()
                    )

                else:

                    self.error(
                        "Selected path is not a file."
                    )

                    return False

        except Exception:

            file_path = None

        # --------------------------------------------------
        # Search ZIP By Filename
        # --------------------------------------------------

        if file_path is None:

            search_name = clean_name

            if search_name.lower().endswith(
                ".zip"
            ):

                search_name = search_name[
                    :-4
                ]

            # Remove trailing "zip"
            search_name = search_name.strip()

            file_path = self.find_file(
                search_name + ".zip"
            )

        # --------------------------------------------------
        # Fallback Search
        # --------------------------------------------------

        if file_path is None:

            file_path = self.find_file(
                clean_name
            )

            if file_path is not None:

                file_path = Path(
                    file_path
                ).resolve()

                if (
                    file_path.suffix.lower()
                    != ".zip"
                ):

                    zip_candidate = (
                        file_path.with_suffix(
                            ".zip"
                        )
                    )

                    if zip_candidate.exists():

                        file_path = (
                            zip_candidate.resolve()
                        )

                    else:

                        file_path = None

        # --------------------------------------------------
        # ZIP Not Found
        # --------------------------------------------------

        if file_path is None:

            self.error(
                "ZIP file not found."
            )

            return False

        file_path = Path(
            file_path
        ).resolve()

        # --------------------------------------------------
        # Validate ZIP
        # --------------------------------------------------

        if not file_path.exists():

            self.error(
                "ZIP file does not exist."
            )

            return False

        if not file_path.is_file():

            self.error(
                "Selected path is not a file."
            )

            return False

        if file_path.suffix.lower() != ".zip":

            self.error(
                "Selected file is not a ZIP archive."
            )

            return False

        # --------------------------------------------------
        # Verify ZIP Integrity
        # --------------------------------------------------

        try:

            if not zipfile.is_zipfile(
                file_path
            ):

                self.error(
                    "The selected file is not a valid ZIP archive."
                )

                return False

        except Exception as error:

            self.error(
                f"ZIP validation failed : {error}"
            )

            return False

        # --------------------------------------------------
        # Extraction Folder
        #
        # demo.zip -> demo/
        # --------------------------------------------------

        extract_folder = (
            file_path.parent
            /
            file_path.stem
        ).resolve()

        # --------------------------------------------------
        # Prevent Existing Folder Overwrite
        # --------------------------------------------------

        if extract_folder.exists():

            self.error(
                "Extraction folder already exists."
            )

            return False

        print(
            "\n==================================="
        )

        print(
            "ZIP EXTRACTION"
        )

        print(
            "==================================="
        )

        print(
            f"ZIP File        : {file_path}"
        )

        print(
            f"Extract Folder  : {extract_folder}"
        )

        print(
            "==================================="
        )

        extracted_files = []

        # --------------------------------------------------
        # Extract Safely
        # --------------------------------------------------

        try:

            with zipfile.ZipFile(
                file_path,
                mode="r"
            ) as archive:

                # ------------------------------------------
                # ZIP Path Traversal Protection
                # ------------------------------------------

                for member in archive.infolist():

                    member_path = (
                        extract_folder
                        /
                        member.filename
                    ).resolve()

                    try:

                        member_path.relative_to(
                            extract_folder
                        )

                    except ValueError:

                        self.error(
                            "Unsafe ZIP archive detected."
                        )

                        return False

                # ------------------------------------------
                # Create Extraction Folder
                # ------------------------------------------

                extract_folder.mkdir(
                    parents=True,
                    exist_ok=False
                )

                # ------------------------------------------
                # Extract
                # ------------------------------------------

                archive.extractall(
                    extract_folder
                )

                # ------------------------------------------
                # Collect Extracted Files
                # ------------------------------------------

                for root, _, files in os.walk(
                    extract_folder
                ):

                    for file in files:

                        extracted_path = (
                            Path(root)
                            /
                            file
                        ).resolve()

                        if extracted_path.is_file():

                            extracted_files.append(
                                extracted_path
                            )

            # --------------------------------------------------
            # Verify Extraction
            # --------------------------------------------------

            if not extract_folder.exists():

                self.error(
                    "ZIP extraction verification failed."
                )

                return False

            # --------------------------------------------------
            # Refresh Database
            # --------------------------------------------------

            for extracted_file in extracted_files:

                try:

                    self.refresh_database(
                        extracted_file
                    )

                except Exception as error:

                    print(
                        f"Database refresh warning : {error}"
                    )

            # --------------------------------------------------
            # Refresh File Finder Cache
            # --------------------------------------------------

            try:

                self.file_finder.close()

            except Exception:

                pass

            try:

                self.file_finder = FileFinder()

            except Exception:

                pass

            # --------------------------------------------------
            # Success
            # --------------------------------------------------

            self.success(
                "ZIP archive extracted successfully."
            )

            print(
                f"Extracted To : {extract_folder}"
            )

            print(
                f"Files Extracted : {len(extracted_files)}"
            )

            return True

        except Exception as error:

            self.error(
                f"ZIP extraction failed : {error}"
            )

            # --------------------------------------------------
            # Cleanup Partial Extraction
            # --------------------------------------------------

            try:

                if extract_folder.exists():

                    shutil.rmtree(
                        extract_folder
                    )

            except Exception as cleanup_error:

                print(
                    f"Extraction cleanup warning : {cleanup_error}"
                )

            return False

    # ======================================================
    # Search By Extension
    # ======================================================

    def search_by_extension(
        self,
        extension
    ):
        """
        Search files by extension.

        Returns
        -------
        list[str]
        """

        if not extension:

            return []

        extension = str(
            extension
        ).strip().lower()

        if extension.startswith("*."):

            extension = extension[2:]

        if extension.startswith("."):

            extension = extension[1:]

        if not extension:

            return []

        extension = (
            "."
            +
            extension
        )

        results = []

        for location in (
            self.default_search_locations
        ):

            if location is None:

                continue

            if not location.exists():

                continue

            try:

                for root, _, files in os.walk(
                    location
                ):

                    for file in files:

                        file_path = (
                            Path(root)
                            /
                            file
                        )

                        try:

                            if (
                                file_path.suffix.lower()
                                ==
                                extension
                            ):

                                results.append(
                                    str(
                                        file_path.resolve()
                                    )
                                )

                        except Exception:

                            continue

            except Exception:

                continue

        return sorted(
            list(dict.fromkeys(results)),
            key=str.lower
        )

    # ======================================================
    # Search By Size
    # ======================================================

    def search_by_size(
        self,
        minimum_size_mb
    ):
        """
        Search files larger than
        or equal to the given size in MB.

        Returns
        -------
        list[str]
        """

        try:

            minimum_size_mb = float(
                minimum_size_mb
            )

        except Exception:

            return []

        if minimum_size_mb < 0:

            return []

        minimum_size = (
            minimum_size_mb
            *
            1024
            *
            1024
        )

        results = []

        for location in (
            self.default_search_locations
        ):

            if location is None:

                continue

            if not location.exists():

                continue

            try:

                for root, _, files in os.walk(
                    location
                ):

                    for file in files:

                        file_path = (
                            Path(root)
                            /
                            file
                        )

                        try:

                            if (
                                file_path.stat().st_size
                                >=
                                minimum_size
                            ):

                                results.append(
                                    str(
                                        file_path.resolve()
                                    )
                                )

                        except (
                            PermissionError,
                            FileNotFoundError,
                            OSError
                        ):

                            continue

            except (
                PermissionError,
                FileNotFoundError,
                OSError
            ):

                continue

        return sorted(
            list(dict.fromkeys(results)),
            key=str.lower
        )

    # ======================================================
    # Search By Date
    # ======================================================

    def search_by_date(
        self,
        days
    ):
        """
        Search recently modified files.

        days = 0
            Today only.

        days = 7
            Last 7 days.

        Returns
        -------
        list[str]
        """

        try:

            days = int(
                days
            )

        except Exception:

            return []

        if days < 0:

            return []

        now = datetime.now()

        if days == 0:

            limit = now.replace(
                hour=0,
                minute=0,
                second=0,
                microsecond=0
            )

        else:

            limit = (
                now
                -
                timedelta(
                    days=days
                )
            )

        results = []

        for location in (
            self.default_search_locations
        ):

            if location is None:

                continue

            if not location.exists():

                continue

            try:

                for root, _, files in os.walk(
                    location
                ):

                    for file in files:

                        file_path = (
                            Path(root)
                            /
                            file
                        )

                        try:

                            modified = (
                                datetime
                                .fromtimestamp(
                                    file_path
                                    .stat()
                                    .st_mtime
                                )
                            )

                            if modified >= limit:

                                results.append(
                                    str(
                                        file_path.resolve()
                                    )
                                )

                        except (
                            PermissionError,
                            FileNotFoundError,
                            OSError
                        ):

                            continue

            except (
                PermissionError,
                FileNotFoundError,
                OSError
            ):

                continue

        return sorted(
            list(dict.fromkeys(results)),
            key=str.lower
        )

    # ======================================================
    # Show Search Results
    # ======================================================

    @staticmethod
    def show_search_results(results, search_pattern=None):
        """
        Display actual search results.

        Search methods already return the real
        matching filesystem paths, so this method
        does not launch Windows Explorer.
        """

        if not results:

            print("\nNo matching files found.")

            return []

        normalized_results = []

        for result in results:

            if result is None:

                continue

            try:

                path = Path(
                    str(result)
                ).expanduser()

                if path.exists() and path.is_file():

                    normalized_results.append(
                        str(
                            path.resolve()
                        )
                    )

            except Exception:

                continue

        # Remove duplicates
        normalized_results = sorted(
            list(
                dict.fromkeys(
                    normalized_results
                )
            ),
            key=str.lower
        )

        if not normalized_results:

            print("\nNo matching files found.")

            return []

        print("\n===================================")
        print("ASTRA File Search Results")
        print("===================================")

        print(
            f"Total Results : {len(normalized_results)}"
        )

        print("-----------------------------------")

        for index, file_path in enumerate(
            normalized_results,
            start=1
        ):

            print(
                f"{index}. {file_path}"
            )

        print("-----------------------------------")
        print("Search completed successfully.")

        return normalized_results

    # ======================================================
    # Close
    # ======================================================

    def close(self):
        """
        Close internal resources.
        """

        try:

            self.file_finder.close()

        except Exception:

            pass

        try:

            self.database.close()

        except Exception:

            pass