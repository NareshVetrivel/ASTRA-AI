"""
File Indexer Module

Scans important user folders and
stores valid files inside the
SQLite database.

Filtering is handled by
FileFilter.

ASTRA-AI V1
"""

import os

from pathlib import Path
from datetime import datetime

from automation.file_filter import FileFilter
from database.database_manager import DatabaseManager


class FileIndexer:
    """
    Index important user files
    into SQLite.
    """

    def __init__(self):

        self.database = DatabaseManager()

        self.home = Path.home()

        # ---------------------------------
        # User Scan Folders
        # ---------------------------------

        self.scan_folders = self.get_scan_folders()

    # --------------------------------------------------
    # Scan Folder List
    # --------------------------------------------------

    def get_scan_folders(self):
        """
        Return folders that should
        be indexed.

        Includes:

        • User folders

        • Local Disk E (if available)
        """

        folders = [

            self.home / "Desktop",

            self.home / "Documents",

            self.home / "Downloads",

            self.home / "Pictures",

            self.home / "Videos",

            self.home / "Music"

        ]

        # ---------------------------------
        # Scan Local Disk E
        # ---------------------------------

        e_drive = Path("E:/")

        if e_drive.exists():

            folders.append(e_drive)

        folders = [

            folder

            for folder in folders

            if folder.exists()

        ]

        # Remove duplicates

        return list(

            dict.fromkeys(folders)

        )

    # --------------------------------------------------
    # Index Files
    # --------------------------------------------------

    def index_files(self):
        """
        Scan configured folders and
        index valid files.
        """

        print("\n==============================")
        print("ASTRA File Indexer")
        print("==============================")

        if self.database.file_count() > 0:

            print("\nFiles already indexed.")
            print("Skipping indexing...")

            return

        print("\nScanning folders...\n")

        total_files = 0

        for folder in self.scan_folders:

            print(f"Scanning : {folder}")

            count = self.scan_folder(folder)

            total_files += count

            print(f"Indexed : {count} files\n")

        print("--------------------------------")

        print(
            f"Total Indexed Files : {total_files}"
        )

        print("\nIndexing Completed.")

    # --------------------------------------------------
    # Scan Folder
    # --------------------------------------------------

    def scan_folder(
        self,
        folder
    ):
        """
        Recursively scan a folder and
        store valid files.

        Returns
        -------
        int
            Number of indexed files.
        """

        indexed_files = 0

        for root, dirs, files in os.walk(folder):

            for file in files:

                try:

                    full_path = os.path.join(
                        root,
                        file
                    )

                    # -------------------------
                    # Smart File Filter
                    # -------------------------

                    if not FileFilter.is_valid_file(
                        full_path
                    ):

                        continue

                    # -------------------------
                    # Skip Duplicates
                    # -------------------------

                    if self.database.file_exists(
                        full_path
                    ):

                        continue

                    file_path = Path(full_path)

                    file_size = os.path.getsize(
                        full_path
                    )

                    last_modified = (
                        datetime.fromtimestamp(
                            os.path.getmtime(
                                full_path
                            )
                        ).isoformat()
                    )

                    # -------------------------
                    # Store Database
                    # -------------------------

                    self.database.insert_file(

                        name=file_path.stem,

                        extension=file_path.suffix,

                        full_path=full_path,

                        file_size=file_size,

                        last_modified=last_modified

                    )

                    indexed_files += 1

                    if indexed_files % 50 == 0:

                        print(

                            f"Indexed {indexed_files} files..."

                        )

                except PermissionError:

                    continue

                except FileNotFoundError:

                    continue

                except OSError:

                    continue

                except Exception as error:

                    print(
                        f"Index Error : {error}"
                    )

        return indexed_files
    
    # --------------------------------------------------
    # Show Summary
    # --------------------------------------------------

    def show_summary(self):
        """
        Display indexed files summary.
        """

        files = self.database.get_all_files()

        print("\n====================================")
        print("ASTRA Indexed Files")
        print("====================================")

        for name, extension, full_path in files:

            print(f"{name}{extension}")

            print(f" -> {full_path}")

        print("\n------------------------------------")

        print(
            f"Total Files : {len(files)}"
        )

    # --------------------------------------------------
    # Reindex Files
    # --------------------------------------------------

    def reindex(self):
        """
        Clear previous index and
        rebuild the file database.
        """

        print("\nClearing previous index...")

        self.database.clear_files()

        print("Database Cleared.")

        print("\nRebuilding File Index...\n")

        self.index_files()

    # --------------------------------------------------
    # Close Database
    # --------------------------------------------------

    def close(self):
        """
        Close database connection.
        """

        self.database.close()