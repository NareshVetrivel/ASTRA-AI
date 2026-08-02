"""
File Manager Module

Provides file management operations
for ASTRA-AI.

Supported Operations
--------------------

• Delete File
• Rename File
• Copy File
• Move File
• Compress File
• Extract ZIP

ASTRA-AI V1
"""

import os
import shutil
from send2trash import send2trash
import zipfile
import pyautogui

from pathlib import Path

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

    # --------------------------------------------------
    # Text To Speech
    # --------------------------------------------------

    def set_tts(self, tts):
        """
        Attach TTS module.
        """

        self.tts = tts

    # --------------------------------------------------
    # Success Message
    # --------------------------------------------------

    def success(self, message):
        """
        Print + Speak success message.
        """

        print("\n===================================")
        print(message)
        print("===================================")

        if self.tts:

            try:

                self.tts.speak(message)

            except Exception:

                pass

    # --------------------------------------------------
    # Error Message
    # --------------------------------------------------

    def error(self, message):
        """
        Print + Speak error message.
        """

        print("\n===================================")
        print(message)
        print("===================================")

        if self.tts:

            try:

                self.tts.speak(message)

            except Exception:

                pass

    # --------------------------------------------------
    # Confirmation
    # --------------------------------------------------

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

        print(f"{action}")

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

            answer = self.whisper.listen_confirmation()

            if answer is None:

                print(
                    "\nConfirmation timeout."
                )

                return False

        if answer in [

            "yes",

            "yeah",

            "ok",

            "okay",

            "confirm",

            "delete"

        ]:

            return True

        self.error("Operation cancelled.")

        return False

    # --------------------------------------------------
    # Refresh Database
    # --------------------------------------------------

    def refresh_database(
        self,
        file_path
    ):
        """
        Refresh one file
        inside database.
        """

        self.database.refresh_file(

            str(file_path)

        )

    # --------------------------------------------------
    # Remove Database Entry
    # --------------------------------------------------

    def remove_database_entry(
        self,
        file_path
    ):
        """
        Remove file
        from database.
        """

        self.database.delete_file(

            str(file_path)

        )

    # --------------------------------------------------
    # Validate File Name
    # --------------------------------------------------

    def _validate_filename(
        self,
        filename
    ):
        """
        Validate filename.
        """

        if not filename:

            return None

        filename = filename.strip()

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

    # --------------------------------------------------
    # Validate Destination
    # --------------------------------------------------

    def _validate_destination(
        self,
        destination
    ):
        """
        Validate destination folder.
        """

        if not destination:
            return None

        destination = destination.strip().lower()

        home = Path.home()

        common_folders = {

            "desktop": home / "Desktop",
            "documents": home / "Documents",
            "downloads": home / "Downloads",
            "pictures": home / "Pictures",
            "videos": home / "Videos",
            "music": home / "Music",

        }

        if destination in common_folders:

            folder = common_folders[destination]

            if folder.exists():
                return folder

            # OneDrive fallback

            one_drive = home / "OneDrive" / folder.name

            if one_drive.exists():
                return one_drive

        folder = Path(destination)

        if not folder.exists():

            self.error("Destination folder not found.")

            return None

        if not folder.is_dir():

            self.error("Destination is not a valid folder.")

            return None

        return folder

    # --------------------------------------------------
    # Find File
    # --------------------------------------------------

    def find_file(
        self,
        filename
    ):
        """
        Search file using database first,
        then fallback to recursive search.

        Returns
        -------
        Path | None
        """

        filename = self._validate_filename(
            filename
        )

        if filename is None:

            return None

        # ---------------------------------
        # Database Search
        # ---------------------------------

        # Always refresh FileFinder so newly created files
        # are immediately searchable.

        self.file_finder.close()

        self.file_finder = FileFinder()

        path = self.file_finder.find_file(
            filename
        )

        if path:

            file_path = Path(path)

            if file_path.exists():

                return file_path

        # ---------------------------------
        # Fallback Recursive Search
        # ---------------------------------

        filename = filename.lower()

        for location in self.default_search_locations:

            if not location.exists():

                continue

            try:

                for root, _, files in os.walk(location):

                    for file in files:

                        file_path = Path(root) / file

                        name = file_path.stem.lower()

                        if (

                            filename == name

                            or

                            filename in name

                        ):

                            print(
                                "\nFound File :"
                            )

                            print(file_path)

                            return file_path

            except Exception:

                continue

        return None

    # --------------------------------------------------
    # Delete File
    # --------------------------------------------------

    def delete_file(
        self,
        filename
    ):
        """
        Delete a file.
        """

        filename = self._validate_filename(
            filename
        )

        if filename is None:

            return False

        file_path = self.find_file(
            filename
        )

        if file_path is None:

            self.error(
                "File not found."
            )

            return False

        try:

            if not self.confirm_action(

                "Delete File",

                file_path

            ):

                return False

            send2trash(

                str(file_path)

            )

            self.remove_database_entry(

                file_path

            )

            self.success("File deleted successfully.")

            print(file_path)

            return True

        except Exception as error:

            self.error(
                f"Delete failed : {error}"
            )

            return False

    # --------------------------------------------------
    # Open File
    # --------------------------------------------------

    def open_file(
        self,
        filename
    ):
        """
        Open a file.
        """

        filename = self._validate_filename(
            filename
        )

        if filename is None:

            return False

        file_path = self.find_file(
            filename
        )

        if file_path is None:

            self.error("File not found.")

            return False

        if not file_path.exists():

            print(
                "\nFile does not exist."
            )

            self.remove_database_entry(
                file_path
            )

            return False

        try:

            os.startfile(
                str(file_path)
            )

            self.success(
                "File opened successfully."
            )

            print(file_path)

            return True

        except Exception as error:

            self.error(
                f"Open failed : {error}"
            )

            return False

    # --------------------------------------------------
    # Rename File
    # --------------------------------------------------

    def rename_file(
        self,
        old_name,
        new_name
    ):
        """
        Rename a file.
        """

        old_name = self._validate_filename(
            old_name
        )

        new_name = self._validate_filename(
            new_name
        )

        if old_name is None or new_name is None:

            return False

        file_path = self.find_file(
            old_name
        )

        if file_path is None:

            self.error(
                "File not found."
            )

            return False

        try:

            new_file = (
                file_path.parent
                /
                (
                    new_name
                    +
                    file_path.suffix
                )
            )

            if new_file.exists():

                self.error("File already exists.")

                return False

            old_path = str(file_path)

            file_path.rename(
                new_file
            )

            self.database.update_file_name(

                old_path,

                new_file.stem,

                str(new_file)

            )

            self.success("File renamed successfully.")

            print(new_file)

            return True

        except Exception as error:

            self.error(
                f"Rename failed : {error}"
            )

            return False
        
    # --------------------------------------------------
    # Create File
    # --------------------------------------------------

    def create_file(
        self,
        filename,
        extension=".txt"
    ):
        """
        Create a new text file.
        """

        filename = self._validate_filename(
            filename
        )

        if filename is None:

            return False

        try:

            documents = self._validate_destination("documents")

            if documents is None:

                self.error("Documents folder not found.")

                return False

            documents.mkdir(
                parents=True,
                exist_ok=True
            )

            file_path = documents / f"{filename}{extension}"

            if file_path.exists():

                self.error(
                    "File already exists."
                )

                return False

            file_path.touch()

            # Wait until Windows creates the file

            import time

            time.sleep(0.2)

            self.refresh_database(
                file_path
            )

            # Reload FileFinder database connection

            self.file_finder.close()

            self.file_finder = FileFinder()

            self.success(
                "File created successfully."
            )

            print(file_path)

            return True

        except Exception as error:

            self.error(
                f"File creation failed : {error}"
            )

            return False

    # --------------------------------------------------
    # Copy File
    # --------------------------------------------------

    def copy_file(
        self,
        filename,
        destination
    ):
        """
        Copy a file to destination folder.
        """

        filename = self._validate_filename(
            filename
        )

        destination = self._validate_destination(
            destination
        )

        if filename is None or destination is None:

            return False

        file_path = self.find_file(
            filename
        )

        if file_path is None:

            self.error(
                "File not found."
            )

            return False

        destination_file = (
            destination /
            file_path.name
        )

        if destination_file.exists():

            self.error("File already exists in destination.")

            return False

        try:

            shutil.copy2(
                file_path,
                destination_file
            )

            self.refresh_database(
                destination_file
            )

            self.success("File copied successfully.")
            
            print(file_path)

            print(
                "\nTo :"
            )

            print(destination_file)

            return True

        except Exception as error:

            self.error(
                f"Copy failed : {error}"
            )

            return False

    # --------------------------------------------------
    # Move File
    # --------------------------------------------------

    def move_file(
        self,
        filename,
        destination
    ):
        """
        Move file to destination folder.
        """

        filename = self._validate_filename(
            filename
        )

        destination = self._validate_destination(
            destination
        )

        if filename is None or destination is None:

            return False

        file_path = self.find_file(
            filename
        )

        if file_path is None:

            self.error(
                "File not found."
            )

            return False

        destination_file = (
            destination /
            file_path.name
        )

        if destination_file.exists():

            self.error(
                "File already exists in destination."
            )

            return False

        try:

            old_path = str(file_path)

            shutil.move(

                old_path,

                str(destination_file)

            )

            self.database.update_file_path(

                old_path,

                str(destination_file)

            )

            self.success("File moved successfully.")

            print(destination_file)

            return True

        except Exception as error:

            self.error(
                f"Move failed : {error}"
            )

            return False

    # --------------------------------------------------
    # Compress File
    # --------------------------------------------------

    def compress_file(
        self,
        filename
    ):
        """
        Compress file into ZIP archive.
        """

        filename = self._validate_filename(
            filename
        )

        if filename is None:

            return False

        file_path = self.find_file(
            filename
        )

        if file_path is None:

            self.error(
                "File not found."
            )

            return False

        zip_path = file_path.with_suffix(
            ".zip"
        )

        if zip_path.exists():

            self.error("ZIP archive already exists.")

            return False

        try:

            with zipfile.ZipFile(
                zip_path,
                "w",
                zipfile.ZIP_DEFLATED
            ) as archive:

                archive.write(
                    file_path,
                    arcname=file_path.name
                )

            self.refresh_database(
                zip_path
            )

            self.success("ZIP archive created successfully.")

            print(zip_path)

            return True

        except Exception as error:

            self.error(
                f"ZIP creation failed : {error}"
            )

            return False
        
    # --------------------------------------------------
    # Extract ZIP
    # --------------------------------------------------

    def extract_zip(
        self,
        filename
    ):
        """
        Extract ZIP archive.
        """

        filename = self._validate_filename(
            filename
        )

        if filename is None:

            return False

        filename = filename.replace(".zip", "")
        filename = filename.replace(" zip", "")
        filename = filename.replace("extract", "")
        filename = filename.strip()

        # First search the ZIP archive itself

        file_path = self.find_file(filename + ".zip")

        # Fallback

        if file_path is None:

            file_path = self.find_file(filename)

            if (
                file_path is not None
                and
                file_path.suffix.lower() != ".zip"
            ):

                zip_candidate = file_path.with_suffix(".zip")

                if zip_candidate.exists():

                    file_path = zip_candidate

        if file_path is None:

            self.error(
                "ZIP file not found."
            )

            return False

        if file_path.suffix.lower() != ".zip":

            self.error("Selected file is not a ZIP archive.")

            return False

        extract_folder = (
            file_path.parent /
            file_path.stem
        )

        if extract_folder.exists():

            self.error("Extraction folder already exists.")

            return False

        try:

            with zipfile.ZipFile(
                file_path,
                "r"
            ) as archive:

                archive.extractall(
                    extract_folder
                )

            for root, _, files in os.walk(

                extract_folder

            ):

                for file in files:

                    self.refresh_database(

                        Path(root) / file

                    )

            self.success("ZIP extracted successfully.")

            print(extract_folder)

            return True

        except Exception as error:

            self.error(
                f"ZIP extraction failed : {error}"
            )

            return False

    # --------------------------------------------------
    # Search By Extension
    # --------------------------------------------------

    def search_by_extension(
        self,
        extension
    ):
        """
        Search files by extension.

        Returns
        -------
        list
        """

        if not extension:

            return []

        extension = extension.strip().lower()

        if not extension.startswith("."):

            extension = "." + extension

        results = []

        for location in self.default_search_locations:

            if not location.exists():

                continue

            try:

                for root, _, files in os.walk(location):

                    for file in files:

                        file_path = Path(root) / file

                        if file_path.suffix.lower() == extension:

                            results.append(str(file_path))

            except Exception:

                continue

        return sorted(

            results,

            key=str.lower

        )

    # --------------------------------------------------
    # Search By Size
    # --------------------------------------------------

    def search_by_size(
        self,
        minimum_size_mb
    ):
        """
        Search files larger than
        the given size (MB).

        Returns
        -------
        list
        """

        if minimum_size_mb < 0:

            return []

        minimum_size = minimum_size_mb * 1024 * 1024

        results = []

        for location in self.default_search_locations:

            if not location.exists():

                continue

            try:

                for root, _, files in os.walk(location):

                    for file in files:

                        file_path = Path(root) / file

                        try:

                            if file_path.stat().st_size >= minimum_size:

                                results.append(str(file_path))

                        except Exception:

                            continue

            except Exception:

                continue

        return sorted(

            results,

            key=str.lower

        )

    # --------------------------------------------------
    # Search By Date
    # --------------------------------------------------

    def search_by_date(
        self,
        days
    ):
        """
        Search recently modified files.

        Returns
        -------
        list
        """

        from datetime import datetime, timedelta

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

            limit = now - timedelta(days=days)

        results = []

        for location in self.default_search_locations:

            if not location.exists():

                continue

            try:

                for root, _, files in os.walk(location):

                    for file in files:

                        file_path = Path(root) / file

                        try:

                            modified = datetime.fromtimestamp(
                                file_path.stat().st_mtime
                            )

                            if modified >= limit:

                                results.append(str(file_path))

                        except Exception:

                            continue

            except Exception:

                continue

        return sorted(

            results,

            key=str.lower

        )

    # --------------------------------------------------
    # Show Search Results
    # --------------------------------------------------

    @staticmethod
    def show_search_results(results, search_pattern=None):
        """
        Open Windows File Explorer and perform
        a native Explorer search.
        """

        import time

        from automation.keyboard_controller import KeyboardController

        if not results:

            print("\nNo matching files found.")
            return

        if search_pattern is None:

            first = Path(results[0])

            search_pattern = "*" + first.suffix.lower()

            # Explorer expects *.pdf, *.txt...
            if not search_pattern.startswith("*."):
                search_pattern = "*." + first.suffix.lower().replace(".", "")

        try:

            keyboard = KeyboardController()

            # Open Explorer

            os.startfile("explorer.exe")

            print("Explorer launched")

            # Wait for Explorer window
            time.sleep(4)

            # Wait until Explorer becomes active

            if not keyboard.activate_window(2):

                print("Warning : Explorer may not have received focus.")

            time.sleep(1)

            # Focus Explorer

            pyautogui.press("alt")

            time.sleep(0.5)

            # Address/Search Bar

            keyboard.hotkey(
                "ctrl",
                "l"
            )

            time.sleep(0.8)

            keyboard.hotkey(
                "ctrl",
                "e"
            )

            print("Ctrl + E pressed")

            time.sleep(0.8)

            search_text = f"*{search_pattern.lstrip('*')}"

            print("Searching :", search_text)

            # Direct typing is more reliable in Explorer

            # Clear existing text

            pyautogui.hotkey("ctrl", "a")

            time.sleep(0.2)

            pyautogui.press("backspace")

            time.sleep(0.2)

            pyautogui.write(
                search_text,
                interval=0.04
            )

            print("Typed :", search_text)

            time.sleep(2)

            pyautogui.press("enter")

            print("Search executed.")

            time.sleep(3)

        except Exception as error:

            print(f"\nExplorer Search Error : {error}")