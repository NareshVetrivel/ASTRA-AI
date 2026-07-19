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
import zipfile

from pathlib import Path


class FileManager:
    """
    Manage user files.
    """

    def __init__(self):

        self.home = Path.home()

        self.default_search_locations = [

            self.home / "Desktop",

            self.home / "Documents",

            self.home / "Downloads",

            self.home / "Pictures",

            self.home / "Videos",

            self.home / "Music",

            Path("E:/")

        ]

    # --------------------------------------------------
    # Find File
    # --------------------------------------------------

    def find_file(
        self,
        filename
    ):
        """
        Search file recursively.

        Returns
        -------
        Path | None
        """

        if not filename:

            return None

        filename = filename.lower().strip()

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

        file_path = self.find_file(filename)

        if file_path is None:

            print("\nFile not found.")

            return False

        try:

            os.remove(file_path)

            print(

                "\nDeleted :"

            )

            print(file_path)

            return True

        except Exception as error:

            print(error)

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

        file_path = self.find_file(

            old_name

        )

        if file_path is None:

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

            file_path.rename(

                new_file

            )

            print(

                "\nRenamed :"

            )

            print(new_file)

            return True

        except Exception as error:

            print(error)

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
        Create a new empty file
        inside Documents folder.
        """

        if not filename:

            return False

        try:

            documents = self.home / "Documents"

            documents.mkdir(
                exist_ok=True
            )

            file_path = (

                documents

                /

                f"{filename}{extension}"

            )

            if file_path.exists():

                print(

                    "\nFile already exists."

                )

                return False

            file_path.touch()

            print(

                "\nCreated File :"

            )

            print(file_path)

            return True

        except Exception as error:

            print(error)

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

        file_path = self.find_file(filename)

        if file_path is None:

            print("\nFile not found.")

            return False

        destination = Path(destination)

        if not destination.exists():

            print("\nDestination folder not found.")

            return False

        try:

            shutil.copy2(

                file_path,

                destination / file_path.name

            )

            print(

                "\nCopied :"

            )

            print(file_path)

            print(

                "\nTo :"

            )

            print(destination)

            return True

        except Exception as error:

            print(error)

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

        file_path = self.find_file(filename)

        if file_path is None:

            print("\nFile not found.")

            return False

        destination = Path(destination)

        if not destination.exists():

            print("\nDestination folder not found.")

            return False

        try:

            shutil.move(

                str(file_path),

                str(

                    destination

                    /

                    file_path.name

                )

            )

            print(

                "\nMoved :"

            )

            print(file_path)

            print(

                "\nTo :"

            )

            print(destination)

            return True

        except Exception as error:

            print(error)

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

        file_path = self.find_file(filename)

        if file_path is None:

            print("\nFile not found.")

            return False

        zip_path = file_path.with_suffix(".zip")

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

            print(

                "\nZIP Created :"

            )

            print(zip_path)

            return True

        except Exception as error:

            print(error)

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

        file_path = self.find_file(filename)

        if file_path is None:

            print("\nZIP file not found.")

            return False

        if file_path.suffix.lower() != ".zip":

            print("\nSelected file is not a ZIP archive.")

            return False

        extract_folder = file_path.parent / file_path.stem

        try:

            with zipfile.ZipFile(file_path, "r") as archive:

                archive.extractall(extract_folder)

            print("\nZIP Extracted :")
            print(extract_folder)

            return True

        except Exception as error:

            print(error)

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

        results = []

        extension = extension.lower()

        if not extension.startswith("."):

            extension = "." + extension

        for location in self.default_search_locations:

            if not location.exists():

                continue

            try:

                for root, _, files in os.walk(location):

                    for file in files:

                        if Path(file).suffix.lower() == extension:

                            results.append(

                                str(Path(root) / file)

                            )

            except Exception:

                continue

        return results

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

        results = []

        minimum_size = minimum_size_mb * 1024 * 1024

        for location in self.default_search_locations:

            if not location.exists():

                continue

            try:

                for root, _, files in os.walk(location):

                    for file in files:

                        file_path = Path(root) / file

                        try:

                            if file_path.stat().st_size >= minimum_size:

                                results.append(

                                    str(file_path)

                                )

                        except Exception:

                            continue

            except Exception:

                continue

        return results

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

        results = []

        limit = datetime.now() - timedelta(days=days)

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

                                results.append(

                                    str(file_path)

                                )

                        except Exception:

                            continue

            except Exception:

                continue

        return results

    # --------------------------------------------------
    # Show Search Results
    # --------------------------------------------------

    @staticmethod
    def show_search_results(results):
        """
        Display search results.
        """

        if not results:

            print("\nNo files found.")

            return

        print("\n==============================")
        print("Search Results")
        print("==============================")

        for file in results:

            print(file)

        print("\n------------------------------")
        print(f"Total Files : {len(results)}")