"""
Database Manager Module

Handles all SQLite database operations
for ASTRA-AI.

Supports:

- Installed applications
- Application aliases
- Indexed files
- Indexed folders
- File and folder synchronization
- Thread-safe database access

ASTRA-AI V1
"""

import sqlite3
import threading

from pathlib import Path
from datetime import datetime


class DatabaseManager:
    """
    Thread-safe SQLite Database Manager.
    """

    def __init__(self):

        # --------------------------------------
        # Database Lock
        # --------------------------------------

        self.lock = threading.RLock()

        # --------------------------------------
        # Project Root
        # --------------------------------------

        project_root = (
            Path(__file__)
            .resolve()
            .parent
            .parent
        )

        # --------------------------------------
        # Database Path
        # --------------------------------------

        self.database_path = (
            project_root /
            "database" /
            "astra.db"
        )

        # --------------------------------------
        # Ensure Database Directory Exists
        # --------------------------------------

        self.database_path.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        # --------------------------------------
        # Connect Database
        #
        # check_same_thread=False is required
        # because:
        #
        # - Main application uses SQLite
        # - InitializationWorker uses SQLite
        # - Watchdog FileMonitor uses SQLite
        # --------------------------------------

        self.connection = sqlite3.connect(
            self.database_path,
            check_same_thread=False,
            timeout=30
        )

        # Improve SQLite behavior for
        # concurrent read/write operations.
        self.connection.execute(
            "PRAGMA journal_mode=WAL"
        )

        self.connection.execute(
            "PRAGMA synchronous=NORMAL"
        )

        self.cursor = self.connection.cursor()

        # --------------------------------------
        # Create Required Tables
        # --------------------------------------

        self.create_tables()

    # ==================================================
    # INTERNAL HELPERS
    # ==================================================

    def _normalize_path(
        self,
        full_path
    ):
        """
        Return a normalized absolute path.
        """

        try:

            return str(
                Path(full_path)
                .resolve()
            )

        except Exception:

            return str(
                Path(full_path)
            )

    # --------------------------------------------------
    # Commit
    # --------------------------------------------------

    def commit(self):
        """
        Commit all pending database changes.
        """

        with self.lock:

            self.connection.commit()

    # --------------------------------------------------
    # Batch Commit
    # --------------------------------------------------

    def batch_commit(self):
        """
        Commit pending bulk inserts.
        """

        with self.lock:

            self.connection.commit()

    # ==================================================
    # DATABASE SETUP
    # ==================================================

    def create_tables(self):
        """
        Create all required ASTRA-AI tables.
        """

        with self.lock:

            # --------------------------------------
            # Installed Applications
            # --------------------------------------

            self.cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS applications (

                    id INTEGER PRIMARY KEY AUTOINCREMENT,

                    name TEXT UNIQUE NOT NULL,

                    exe_name TEXT NOT NULL,

                    full_path TEXT NOT NULL,

                    source TEXT,

                    last_scanned TEXT

                )
                """
            )

            # --------------------------------------
            # Application Aliases
            # --------------------------------------

            self.cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS aliases (

                    id INTEGER PRIMARY KEY AUTOINCREMENT,

                    alias TEXT UNIQUE NOT NULL,

                    application_name TEXT NOT NULL

                )
                """
            )

            # --------------------------------------
            # Indexed Files
            # --------------------------------------

            self.cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS files (

                    id INTEGER PRIMARY KEY AUTOINCREMENT,

                    name TEXT NOT NULL,

                    extension TEXT,

                    full_path TEXT UNIQUE,

                    file_size INTEGER,

                    last_modified TEXT,

                    last_scanned TEXT

                )
                """
            )

            # --------------------------------------
            # Indexed Folders
            # --------------------------------------

            self.cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS folders (

                    id INTEGER PRIMARY KEY AUTOINCREMENT,

                    name TEXT NOT NULL,

                    full_path TEXT UNIQUE,

                    last_modified TEXT,

                    last_scanned TEXT

                )
                """
            )

            # --------------------------------------
            # Useful Indexes
            # --------------------------------------

            self.cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS
                idx_files_name
                ON files(name)
                """
            )

            self.cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS
                idx_files_path
                ON files(full_path)
                """
            )

            self.cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS
                idx_folders_name
                ON folders(name)
                """
            )

            self.cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS
                idx_folders_path
                ON folders(full_path)
                """
            )

            self.connection.commit()

    # ==================================================
    # APPLICATION METHODS
    # ==================================================

    def insert_application(
        self,
        name,
        exe_name,
        full_path,
        source="SCANNER"
    ):
        """
        Insert or update an application.
        """

        try:

            with self.lock:

                self.cursor.execute(
                    """
                    INSERT OR REPLACE INTO
                    applications
                    (
                        name,
                        exe_name,
                        full_path,
                        source,
                        last_scanned
                    )
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        name.lower(),
                        exe_name,
                        self._normalize_path(
                            full_path
                        ),
                        source,
                        datetime.now().isoformat()
                    )
                )

                self.connection.commit()

            return True

        except Exception as error:

            print(
                f"Application Insert Error : {error}"
            )

            return False

    # --------------------------------------------------

    def insert_alias(
        self,
        alias,
        application_name
    ):
        """
        Store application alias.
        """

        try:

            with self.lock:

                self.cursor.execute(
                    """
                    INSERT OR REPLACE INTO
                    aliases
                    (
                        alias,
                        application_name
                    )
                    VALUES (?, ?)
                    """,
                    (
                        alias.lower(),
                        application_name.lower()
                    )
                )

                self.connection.commit()

            return True

        except Exception as error:

            print(
                f"Alias Insert Error : {error}"
            )

            return False

    # --------------------------------------------------

    def get_application(
        self,
        name
    ):
        """
        Return application details.
        """

        with self.lock:

            self.cursor.execute(
                """
                SELECT
                    name,
                    exe_name,
                    full_path
                FROM applications
                WHERE name = ?
                """,
                (
                    name.lower(),
                )
            )

            return self.cursor.fetchone()

    # --------------------------------------------------

    def get_alias(
        self,
        alias
    ):
        """
        Return application alias.
        """

        with self.lock:

            self.cursor.execute(
                """
                SELECT
                    application_name
                FROM aliases
                WHERE alias = ?
                """,
                (
                    alias.lower(),
                )
            )

            return self.cursor.fetchone()

    # --------------------------------------------------

    def get_all_applications(self):
        """
        Return all applications.
        """

        with self.lock:

            self.cursor.execute(
                """
                SELECT
                    name,
                    exe_name,
                    full_path
                FROM applications
                ORDER BY name
                """
            )

            return self.cursor.fetchall()

    # --------------------------------------------------

    def application_exists(
        self,
        name
    ):
        """
        Check whether application exists.
        """

        with self.lock:

            self.cursor.execute(
                """
                SELECT 1
                FROM applications
                WHERE name = ?
                """,
                (
                    name.lower(),
                )
            )

            return (
                self.cursor.fetchone()
                is not None
            )

    # --------------------------------------------------

    def application_count(self):
        """
        Return total applications.
        """

        with self.lock:

            self.cursor.execute(
                """
                SELECT COUNT(*)
                FROM applications
                """
            )

            return self.cursor.fetchone()[0]

    # ==================================================
    # FILE METHODS
    # ==================================================

    def insert_file(
        self,
        name,
        extension,
        full_path,
        file_size,
        last_modified,
        commit=True
    ):
        """
        Insert or update indexed file.
        """

        try:

            full_path = (
                self._normalize_path(
                    full_path
                )
            )

            with self.lock:

                self.cursor.execute(
                    """
                    INSERT INTO files
                    (
                        name,
                        extension,
                        full_path,
                        file_size,
                        last_modified,
                        last_scanned
                    )
                    VALUES (?, ?, ?, ?, ?, ?)

                    ON CONFLICT(full_path)
                    DO UPDATE SET

                        name = excluded.name,

                        extension = excluded.extension,

                        file_size = excluded.file_size,

                        last_modified = excluded.last_modified,

                        last_scanned = excluded.last_scanned
                    """,
                    (
                        name.lower(),
                        extension.lower(),
                        full_path,
                        file_size,
                        last_modified,
                        datetime.now().isoformat()
                    )
                )

                if commit:

                    self.connection.commit()

            return True

        except Exception as error:

            print(
                f"File Insert Error : {error}"
            )

            return False

    # --------------------------------------------------

    def get_file(
        self,
        name
    ):
        """
        Return indexed file.
        """

        with self.lock:

            self.cursor.execute(
                """
                SELECT
                    name,
                    extension,
                    full_path
                FROM files
                WHERE name LIKE ?
                LIMIT 1
                """,
                (
                    f"%{name.lower()}%",
                )
            )

            return self.cursor.fetchone()

    # --------------------------------------------------

    def get_file_by_path(
        self,
        full_path
    ):
        """
        Return indexed file
        using its full path.
        """

        full_path = (
            self._normalize_path(
                full_path
            )
        )

        with self.lock:

            self.cursor.execute(
                """
                SELECT
                    name,
                    extension,
                    full_path
                FROM files
                WHERE full_path = ?
                """,
                (
                    full_path,
                )
            )

            return self.cursor.fetchone()

    # --------------------------------------------------

    def search_files(
        self,
        keyword
    ):
        """
        Search matching files.
        """

        with self.lock:

            self.cursor.execute(
                """
                SELECT
                    name,
                    extension,
                    full_path
                FROM files
                WHERE name LIKE ?
                ORDER BY name
                LIMIT 20
                """,
                (
                    f"%{keyword.lower()}%",
                )
            )

            return self.cursor.fetchall()

    # --------------------------------------------------

    def get_all_files(self):
        """
        Return all indexed files.
        """

        with self.lock:

            self.cursor.execute(
                """
                SELECT
                    name,
                    extension,
                    full_path
                FROM files
                ORDER BY name
                """
            )

            return self.cursor.fetchall()

    # --------------------------------------------------

    def search_by_extension(
        self,
        extension
    ):
        """
        Search files by extension.
        """

        extension = extension.lower()

        if not extension.startswith("."):

            extension = "." + extension

        with self.lock:

            self.cursor.execute(
                """
                SELECT
                    name,
                    extension,
                    full_path
                FROM files
                WHERE extension = ?
                ORDER BY name
                """,
                (
                    extension,
                )
            )

            return self.cursor.fetchall()

    # --------------------------------------------------

    def file_exists(
        self,
        full_path
    ):
        """
        Check whether file exists
        in database.
        """

        full_path = (
            self._normalize_path(
                full_path
            )
        )

        with self.lock:

            self.cursor.execute(
                """
                SELECT 1
                FROM files
                WHERE full_path = ?
                """,
                (
                    full_path,
                )
            )

            return (
                self.cursor.fetchone()
                is not None
            )

    # --------------------------------------------------

    def search_by_size(
        self,
        minimum_size_mb
    ):
        """
        Search files larger than
        the given size.
        """

        minimum_size = (
            minimum_size_mb
            * 1024
            * 1024
        )

        with self.lock:

            self.cursor.execute(
                """
                SELECT
                    name,
                    extension,
                    full_path
                FROM files
                WHERE file_size >= ?
                ORDER BY file_size DESC
                """,
                (
                    minimum_size,
                )
            )

            return self.cursor.fetchall()

    # --------------------------------------------------

    def search_by_date(
        self,
        days
    ):
        """
        Search recently modified files.
        """

        with self.lock:

            self.cursor.execute(
                """
                SELECT
                    name,
                    extension,
                    full_path
                FROM files
                WHERE
                    julianday('now') -
                    julianday(last_modified) <= ?
                ORDER BY last_modified DESC
                """,
                (
                    days,
                )
            )

            return self.cursor.fetchall()

    # --------------------------------------------------

    def file_count(self):
        """
        Return total indexed files.
        """

        with self.lock:

            self.cursor.execute(
                """
                SELECT COUNT(*)
                FROM files
                """
            )

            return self.cursor.fetchone()[0]

    # --------------------------------------------------

    def update_file_name(
        self,
        old_path,
        new_name,
        new_path
    ):
        """
        Update renamed file.
        """

        try:

            old_path = (
                self._normalize_path(
                    old_path
                )
            )

            new_path = (
                self._normalize_path(
                    new_path
                )
            )

            new_file = Path(
                new_path
            )

            if new_file.exists():

                file_size = (
                    new_file.stat()
                    .st_size
                )

                last_modified = (
                    datetime.fromtimestamp(
                        new_file.stat()
                        .st_mtime
                    )
                    .isoformat()
                )

            else:

                file_size = None

                last_modified = (
                    datetime.now()
                    .isoformat()
                )

            with self.lock:

                self.cursor.execute(
                    """
                    UPDATE files
                    SET

                        name = ?,

                        extension = ?,

                        full_path = ?,

                        file_size = ?,

                        last_modified = ?,

                        last_scanned = ?

                    WHERE full_path = ?
                    """,
                    (
                        (
                            new_name
                            or
                            new_file.stem
                        ).lower(),

                        new_file.suffix.lower(),

                        new_path,

                        file_size,

                        last_modified,

                        datetime.now().isoformat(),

                        old_path
                    )
                )

                self.connection.commit()

            return True

        except Exception as error:

            print(
                f"Update File Name Error : {error}"
            )

            return False

    # --------------------------------------------------

    def update_file_path(
        self,
        old_path,
        new_path
    ):
        """
        Update moved file path.
        """

        try:

            old_path = (
                self._normalize_path(
                    old_path
                )
            )

            new_path = (
                self._normalize_path(
                    new_path
                )
            )

            new_file = Path(
                new_path
            )

            if new_file.exists():

                file_size = (
                    new_file.stat()
                    .st_size
                )

                last_modified = (
                    datetime.fromtimestamp(
                        new_file.stat()
                        .st_mtime
                    )
                    .isoformat()
                )

            else:

                file_size = None

                last_modified = (
                    datetime.now()
                    .isoformat()
                )

            with self.lock:

                self.cursor.execute(
                    """
                    UPDATE files
                    SET

                        name = ?,

                        extension = ?,

                        full_path = ?,

                        file_size = ?,

                        last_modified = ?,

                        last_scanned = ?

                    WHERE full_path = ?
                    """,
                    (
                        new_file.stem.lower(),

                        new_file.suffix.lower(),

                        new_path,

                        file_size,

                        last_modified,

                        datetime.now().isoformat(),

                        old_path
                    )
                )

                self.connection.commit()

            return True

        except Exception as error:

            print(
                f"Update File Path Error : {error}"
            )

            return False

    # --------------------------------------------------

    def delete_file(
        self,
        full_path
    ):
        """
        Remove file from database.
        """

        try:

            full_path = (
                self._normalize_path(
                    full_path
                )
            )

            with self.lock:

                self.cursor.execute(
                    """
                    DELETE FROM files
                    WHERE full_path = ?
                    """,
                    (
                        full_path,
                    )
                )

                self.connection.commit()

            return True

        except Exception as error:

            print(
                f"Delete File DB Error : {error}"
            )

            return False

    # --------------------------------------------------

    def refresh_file(
        self,
        file_path,
        commit=True
    ):
        """
        Insert or refresh one file entry.
        """

        try:

            file = Path(
                file_path
            )

            if not file.exists():

                return False

            if not file.is_file():

                return False

            return self.insert_file(

                name=file.stem,

                extension=file.suffix,

                full_path=str(file),

                file_size=(
                    file.stat()
                    .st_size
                ),

                last_modified=(
                    datetime.fromtimestamp(
                        file.stat()
                        .st_mtime
                    )
                    .isoformat()
                ),

                commit=commit
            )

        except Exception as error:

            print(
                f"Refresh File Error : {error}"
            )

            return False

    # --------------------------------------------------

    def delete_missing_file(
        self,
        full_path
    ):
        """
        Remove missing file
        from database.
        """

        return self.delete_file(
            full_path
        )

    # --------------------------------------------------

    def clear_files(self):
        """
        Remove only indexed files.
        """

        with self.lock:

            self.cursor.execute(
                """
                DELETE FROM files
                """
            )

            self.connection.commit()

    # ==================================================
    # FOLDER METHODS
    # ==================================================

    def insert_folder(
        self,
        name,
        full_path,
        last_modified=None,
        commit=True
    ):
        """
        Insert or update indexed folder.
        """

        try:

            full_path = (
                self._normalize_path(
                    full_path
                )
            )

            folder_path = Path(
                full_path
            )

            if last_modified is None:

                if folder_path.exists():

                    last_modified = (
                        datetime.fromtimestamp(
                            folder_path.stat()
                            .st_mtime
                        )
                        .isoformat()
                    )

                else:

                    last_modified = (
                        datetime.now()
                        .isoformat()
                    )

            with self.lock:

                self.cursor.execute(
                    """
                    INSERT INTO folders
                    (
                        name,
                        full_path,
                        last_modified,
                        last_scanned
                    )
                    VALUES (?, ?, ?, ?)

                    ON CONFLICT(full_path)
                    DO UPDATE SET

                        name = excluded.name,

                        last_modified =
                        excluded.last_modified,

                        last_scanned =
                        excluded.last_scanned
                    """,
                    (
                        name.lower(),

                        full_path,

                        last_modified,

                        datetime.now().isoformat()
                    )
                )

                if commit:

                    self.connection.commit()

            return True

        except Exception as error:

            print(
                f"Folder Insert Error : {error}"
            )

            return False

    # --------------------------------------------------

    def refresh_folder(
        self,
        folder_path,
        commit=True
    ):
        """
        Insert or refresh one folder entry.
        """

        try:

            folder = Path(
                folder_path
            )

            if not folder.exists():

                return False

            if not folder.is_dir():

                return False

            return self.insert_folder(

                name=folder.name,

                full_path=str(folder),

                last_modified=(
                    datetime.fromtimestamp(
                        folder.stat()
                        .st_mtime
                    )
                    .isoformat()
                ),

                commit=commit
            )

        except Exception as error:

            print(
                f"Refresh Folder Error : {error}"
            )

            return False

    # --------------------------------------------------

    def get_folder(
        self,
        name
    ):
        """
        Return indexed folder.
        """

        with self.lock:

            self.cursor.execute(
                """
                SELECT
                    name,
                    full_path
                FROM folders
                WHERE name LIKE ?
                LIMIT 1
                """,
                (
                    f"%{name.lower()}%",
                )
            )

            return self.cursor.fetchone()

    # --------------------------------------------------

    def get_folder_by_path(
        self,
        full_path
    ):
        """
        Return folder using its path.
        """

        full_path = (
            self._normalize_path(
                full_path
            )
        )

        with self.lock:

            self.cursor.execute(
                """
                SELECT
                    name,
                    full_path
                FROM folders
                WHERE full_path = ?
                """,
                (
                    full_path,
                )
            )

            return self.cursor.fetchone()

    # --------------------------------------------------

    def search_folders(
        self,
        keyword
    ):
        """
        Search matching folders.
        """

        with self.lock:

            self.cursor.execute(
                """
                SELECT
                    name,
                    full_path
                FROM folders
                WHERE name LIKE ?
                ORDER BY name
                LIMIT 20
                """,
                (
                    f"%{keyword.lower()}%",
                )
            )

            return self.cursor.fetchall()

    # --------------------------------------------------

    def get_all_folders(self):
        """
        Return all indexed folders.
        """

        with self.lock:

            self.cursor.execute(
                """
                SELECT
                    name,
                    full_path
                FROM folders
                ORDER BY name
                """
            )

            return self.cursor.fetchall()

    # --------------------------------------------------

    def folder_exists(
        self,
        full_path
    ):
        """
        Check whether folder exists
        in database.
        """

        full_path = (
            self._normalize_path(
                full_path
            )
        )

        with self.lock:

            self.cursor.execute(
                """
                SELECT 1
                FROM folders
                WHERE full_path = ?
                """,
                (
                    full_path,
                )
            )

            return (
                self.cursor.fetchone()
                is not None
            )

    # --------------------------------------------------

    def folder_count(self):
        """
        Return total indexed folders.
        """

        with self.lock:

            self.cursor.execute(
                """
                SELECT COUNT(*)
                FROM folders
                """
            )

            return self.cursor.fetchone()[0]

    # --------------------------------------------------

    def update_folder_name(
        self,
        old_path,
        new_name,
        new_path
    ):
        """
        Update renamed folder.
        """

        try:

            old_path = (
                self._normalize_path(
                    old_path
                )
            )

            new_path = (
                self._normalize_path(
                    new_path
                )
            )

            with self.lock:

                self.cursor.execute(
                    """
                    UPDATE folders
                    SET

                        name = ?,

                        full_path = ?,

                        last_modified = ?,

                        last_scanned = ?

                    WHERE full_path = ?
                    """,
                    (
                        new_name.lower(),

                        new_path,

                        datetime.now().isoformat(),

                        datetime.now().isoformat(),

                        old_path
                    )
                )

                self.connection.commit()

            return True

        except Exception as error:

            print(
                f"Update Folder Name Error : {error}"
            )

            return False

    # --------------------------------------------------

    def update_folder_path(
        self,
        old_path,
        new_path
    ):
        """
        Update moved folder path.
        """

        try:

            old_path = (
                self._normalize_path(
                    old_path
                )
            )

            new_path = (
                self._normalize_path(
                    new_path
                )
            )

            folder = Path(
                new_path
            )

            with self.lock:

                self.cursor.execute(
                    """
                    UPDATE folders
                    SET

                        name = ?,

                        full_path = ?,

                        last_modified = ?,

                        last_scanned = ?

                    WHERE full_path = ?
                    """,
                    (
                        folder.name.lower(),

                        new_path,

                        (
                            datetime.fromtimestamp(
                                folder.stat()
                                .st_mtime
                            )
                            .isoformat()

                            if folder.exists()

                            else

                            datetime.now()
                            .isoformat()
                        ),

                        datetime.now().isoformat(),

                        old_path
                    )
                )

                self.connection.commit()

            return True

        except Exception as error:

            print(
                f"Update Folder Path Error : {error}"
            )

            return False

    # --------------------------------------------------

    def delete_folder(
        self,
        full_path
    ):
        """
        Remove folder from database.
        """

        try:

            full_path = (
                self._normalize_path(
                    full_path
                )
            )

            with self.lock:

                self.cursor.execute(
                    """
                    DELETE FROM folders
                    WHERE full_path = ?
                    """,
                    (
                        full_path,
                    )
                )

                self.connection.commit()

            return True

        except Exception as error:

            print(
                f"Delete Folder DB Error : {error}"
            )

            return False

    # --------------------------------------------------

    def delete_missing_folder(
        self,
        full_path
    ):
        """
        Remove missing folder
        from database.
        """

        return self.delete_folder(
            full_path
        )

    # --------------------------------------------------

    def clear_folders(self):
        """
        Remove only indexed folders.
        """

        with self.lock:

            self.cursor.execute(
                """
                DELETE FROM folders
                """
            )

            self.connection.commit()

    # ==================================================
    # CLEANUP / SYNCHRONIZATION
    # ==================================================

    def remove_missing_files(
        self,
        commit=True
    ):
        """
        Remove database entries for
        files that no longer exist.
        """

        try:

            with self.lock:

                self.cursor.execute(
                    """
                    SELECT full_path
                    FROM files
                    """
                )

                paths = (
                    self.cursor.fetchall()
                )

                removed_count = 0

                for (full_path,) in paths:

                    if not Path(
                        full_path
                    ).is_file():

                        self.cursor.execute(
                            """
                            DELETE FROM files
                            WHERE full_path = ?
                            """,
                            (
                                full_path,
                            )
                        )

                        removed_count += 1

                if commit:

                    self.connection.commit()

            return removed_count

        except Exception as error:

            print(
                f"Remove Missing Files Error : "
                f"{error}"
            )

            return 0

    # --------------------------------------------------

    def remove_missing_folders(
        self,
        commit=True
    ):
        """
        Remove database entries for
        folders that no longer exist.
        """

        try:

            with self.lock:

                self.cursor.execute(
                    """
                    SELECT full_path
                    FROM folders
                    """
                )

                paths = (
                    self.cursor.fetchall()
                )

                removed_count = 0

                for (full_path,) in paths:

                    if not Path(
                        full_path
                    ).is_dir():

                        self.cursor.execute(
                            """
                            DELETE FROM folders
                            WHERE full_path = ?
                            """,
                            (
                                full_path,
                            )
                        )

                        removed_count += 1

                if commit:

                    self.connection.commit()

            return removed_count

        except Exception as error:

            print(
                f"Remove Missing Folders Error : "
                f"{error}"
            )

            return 0

    # ==================================================
    # DATABASE CLEANUP
    # ==================================================

    def clear_database(self):
        """
        Remove all stored ASTRA data.
        """

        with self.lock:

            self.cursor.execute(
                """
                DELETE FROM applications
                """
            )

            self.cursor.execute(
                """
                DELETE FROM aliases
                """
            )

            self.cursor.execute(
                """
                DELETE FROM files
                """
            )

            self.cursor.execute(
                """
                DELETE FROM folders
                """
            )

            self.connection.commit()

    # ==================================================
    # CLOSE DATABASE
    # ==================================================

    def close(self):
        """
        Close SQLite connection safely.
        """

        try:

            with self.lock:

                if self.connection:

                    self.connection.commit()

                    self.connection.close()

                    self.connection = None

        except Exception:

            pass