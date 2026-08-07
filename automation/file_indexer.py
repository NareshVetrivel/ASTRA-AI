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

        # ---------------------------------
        # Cache Existing Indexed Files
        # ---------------------------------

        self.indexed_paths = {

            file[2]

            for file in self.database.get_all_files()

        }

    # --------------------------------------------------
    # Scan Folder List
    # --------------------------------------------------

    def get_scan_folders(self):
        """
        Return folders that should
        be indexed.

        Includes:

        • User folders

        • Entire Local Disk E
        (if available)
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
        # Entire Local Disk E
        # ---------------------------------

        e_drive = Path("E:/")

        if e_drive.exists():

            print("\nDetected Local Disk E")

            folders.append(
                e_drive
            )

        # ---------------------------------
        # Keep Existing Folders Only
        # ---------------------------------

        folders = [

            folder

            for folder in folders

            if folder.exists()

        ]

        # ---------------------------------
        # Remove Duplicates
        # ---------------------------------

        unique_folders = []

        visited = set()

        for folder in folders:

            folder = folder.resolve()

            if folder not in visited:

                visited.add(folder)

                unique_folders.append(folder)

        return unique_folders

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

            # ---------------------------------
            # Commit once per folder
            # (Much faster than committing
            # every single file.)
            # ---------------------------------

            self.database.batch_commit()

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

        MAX_DEPTH = 2

        for root, dirs, files in os.walk(folder):

            # ---------------------------------
            # Skip unwanted directories before
            # entering them (huge speed boost)
            # ---------------------------------

            dirs[:] = [

                directory

                for directory in dirs

                if not FileFilter.should_skip_directory(

                    os.path.join(
                        root,
                        directory
                    )

                )

            ]

            relative = Path(root).relative_to(folder)

            if len(relative.parts) >= MAX_DEPTH:

                dirs[:] = []

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
                    # Skip Duplicates (Memory Cache)
                    # -------------------------

                    if full_path in self.indexed_paths:

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

                        last_modified=last_modified,

                        commit=False

                    )

                    self.indexed_paths.add(
                        full_path
                    )

                    indexed_files += 1

                    if False:

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