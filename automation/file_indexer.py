"""
File Indexer Module

Scans important user folders and
stores valid files inside the
SQLite database.

The index is synchronized on every
ASTRA startup.

New files are added.
Existing files are refreshed.
Deleted files are removed from
the SQLite database.

Filtering is handled by FileFilter.

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

    Every indexing run synchronizes
    the database with the current
    file system state.
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

            str(
                Path(file[2]).resolve()
            )

            for file in self.database.get_all_files()

            if file[2]

        }

        # ---------------------------------
        # Paths Found During Current Scan
        # ---------------------------------

        self.scanned_paths = set()

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

            try:

                folder = folder.resolve()

            except Exception:

                continue

            if folder not in visited:

                visited.add(folder)

                unique_folders.append(
                    folder
                )

        return unique_folders

    # --------------------------------------------------
    # Index Files
    # --------------------------------------------------

    def index_files(self):
        """
        Scan configured folders and
        synchronize valid files with
        the SQLite database.

        Existing files are refreshed.

        New files are added.

        Missing files are removed.
        """

        print("\n==============================")
        print("ASTRA File Indexer")
        print("==============================")

        print(
            "\nSynchronizing file index..."
        )

        # Refresh folders in case
        # drives were connected after
        # object creation.

        self.scan_folders = (
            self.get_scan_folders()
        )

        # Reset current scan cache

        self.scanned_paths.clear()

        total_new = 0

        total_updated = 0

        # ---------------------------------
        # Scan All Configured Folders
        # ---------------------------------

        for folder in self.scan_folders:

            print(
                f"\nScanning : {folder}"
            )

            result = self.scan_folder(
                folder
            )

            total_new += (
                result["new"]
            )

            total_updated += (
                result["updated"]
            )

            # ---------------------------------
            # Commit Once Per Folder
            # ---------------------------------

            self.database.batch_commit()

            print(
                f"New     : {result['new']}"
            )

            print(
                f"Updated : {result['updated']}"
            )

        # ---------------------------------
        # Remove Missing Files
        # ---------------------------------

        removed = (
            self.remove_missing_files()
        )

        # Final database commit

        self.database.batch_commit()

        print("\n--------------------------------")

        print(
            f"New Files     : {total_new}"
        )

        print(
            f"Updated Files : {total_updated}"
        )

        print(
            f"Removed Files : {removed}"
        )

        print(
            f"Total Indexed : "
            f"{self.database.file_count()}"
        )

        print(
            "\nFile synchronization completed."
        )

    # --------------------------------------------------
    # Scan Folder
    # --------------------------------------------------

    def scan_folder(
        self,
        folder
    ):
        """
        Recursively scan a folder and
        synchronize valid files.

        Returns
        -------

        dict
            {
                "new": int,
                "updated": int
            }
        """

        new_files = 0

        updated_files = 0

        # Keep existing performance
        # limitation for large drives.

        MAX_DEPTH = 2

        try:

            folder = Path(
                folder
            ).resolve()

        except Exception:

            return {

                "new": 0,
                "updated": 0

            }

        for root, dirs, files in os.walk(
            folder,
            topdown=True
        ):

            # ---------------------------------
            # Skip Unwanted Directories
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

            # ---------------------------------
            # Maximum Scan Depth
            # ---------------------------------

            try:

                relative = (
                    Path(root).relative_to(
                        folder
                    )
                )

                if (
                    len(relative.parts)
                    >= MAX_DEPTH
                ):

                    dirs[:] = []

            except Exception:

                pass

            # ---------------------------------
            # Scan Files
            # ---------------------------------

            for filename in files:

                try:

                    full_path = (
                        Path(root) /
                        filename
                    )

                    # -------------------------
                    # Resolve Path
                    # -------------------------

                    try:

                        normalized_path = str(
                            full_path.resolve()
                        )

                    except Exception:

                        normalized_path = str(
                            full_path
                        )

                    # -------------------------
                    # Smart File Filter
                    # -------------------------

                    if not FileFilter.is_valid_file(

                        normalized_path

                    ):

                        continue

                    # -------------------------
                    # File Metadata
                    # -------------------------

                    file_path = Path(
                        normalized_path
                    )

                    file_size = (
                        file_path.stat().st_size
                    )

                    last_modified = (
                        datetime.fromtimestamp(

                            file_path.stat().st_mtime

                        ).isoformat()
                    )

                    # -------------------------
                    # Track Current File
                    # -------------------------

                    self.scanned_paths.add(
                        normalized_path
                    )

                    # -------------------------
                    # Existing File
                    # -------------------------

                    if (

                        normalized_path
                        in self.indexed_paths

                    ):

                        # Refresh metadata
                        # without removing the
                        # existing entry.

                        self.database.insert_file(

                            name=file_path.stem,

                            extension=file_path.suffix,

                            full_path=normalized_path,

                            file_size=file_size,

                            last_modified=last_modified,

                            commit=False

                        )

                        updated_files += 1

                        continue

                    # -------------------------
                    # New File
                    # -------------------------

                    success = (
                        self.database.insert_file(

                            name=file_path.stem,

                            extension=file_path.suffix,

                            full_path=normalized_path,

                            file_size=file_size,

                            last_modified=last_modified,

                            commit=False

                        )
                    )

                    if success:

                        self.indexed_paths.add(
                            normalized_path
                        )

                        new_files += 1

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

        return {

            "new": new_files,

            "updated": updated_files

        }

    # --------------------------------------------------
    # Remove Missing Files
    # --------------------------------------------------

    def remove_missing_files(self):
        """
        Remove database entries for
        files that no longer exist
        on the system.

        This handles files manually
        deleted outside ASTRA.
        """

        removed_files = 0

        database_files = (
            self.database.get_all_files()
        )

        print(
            "\nChecking for removed files..."
        )

        for file in database_files:

            try:

                full_path = file[2]

                if not full_path:

                    continue

                file_path = Path(
                    full_path
                )

                # ---------------------------------
                # Remove If File No Longer Exists
                # ---------------------------------

                if not file_path.exists():

                    success = (
                        self.database.delete_file(

                            full_path

                        )
                    )

                    if success:

                        removed_files += 1

                        self.indexed_paths.discard(

                            str(
                                full_path
                            )

                        )

            except Exception as error:

                print(
                    f"Missing File Check Error : "
                    f"{error}"
                )

        return removed_files

    # --------------------------------------------------
    # Refresh Single File
    # --------------------------------------------------

    def refresh_file(
        self,
        file_path
    ):
        """
        Add or refresh a single file
        in the database.

        Can be used by future file
        monitoring components.
        """

        try:

            file_path = Path(
                file_path
            )

            if not file_path.exists():

                return False

            try:

                normalized_path = str(
                    file_path.resolve()
                )

            except Exception:

                normalized_path = str(
                    file_path
                )

            # ---------------------------------
            # File Filter
            # ---------------------------------

            if not FileFilter.is_valid_file(

                normalized_path

            ):

                return False

            file_path = Path(
                normalized_path
            )

            success = (
                self.database.insert_file(

                    name=file_path.stem,

                    extension=file_path.suffix,

                    full_path=normalized_path,

                    file_size=(
                        file_path.stat().st_size
                    ),

                    last_modified=(
                        datetime.fromtimestamp(

                            file_path.stat().st_mtime

                        ).isoformat()
                    )

                )
            )

            if success:

                self.indexed_paths.add(
                    normalized_path
                )

            return success

        except Exception as error:

            print(
                f"Refresh File Error : {error}"
            )

            return False

    # --------------------------------------------------
    # Remove Single File
    # --------------------------------------------------

    def remove_file(
        self,
        file_path
    ):
        """
        Remove one file from the
        database index.

        Useful when ASTRA deletes
        a file directly.
        """

        try:

            file_path = Path(
                file_path
            )

            try:

                normalized_path = str(
                    file_path.resolve()
                )

            except Exception:

                normalized_path = str(
                    file_path
                )

            success = (
                self.database.delete_file(

                    normalized_path

                )
            )

            if success:

                self.indexed_paths.discard(

                    normalized_path

                )

            return success

        except Exception as error:

            print(
                f"Remove File Error : {error}"
            )

            return False

    # --------------------------------------------------
    # Show Summary
    # --------------------------------------------------

    def show_summary(self):
        """
        Display indexed files summary.
        """

        files = (
            self.database.get_all_files()
        )

        print("\n====================================")
        print("ASTRA Indexed Files")
        print("====================================")

        for name, extension, full_path in files:

            print(
                f"{name}{extension}"
            )

            print(
                f" -> {full_path}"
            )

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

        print(
            "\nClearing previous index..."
        )

        self.database.clear_files()

        self.indexed_paths.clear()

        self.scanned_paths.clear()

        print(
            "Database Cleared."
        )

        print(
            "\nRebuilding File Index..."
        )

        self.index_files()

    # --------------------------------------------------
    # Close Database
    # --------------------------------------------------

    def close(self):
        """
        Close database connection.
        """

        self.database.close()