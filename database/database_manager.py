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
- Context-aware conversation memory
- Persistent user context
- Command history
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
        # --------------------------------------

        self.connection = sqlite3.connect(
            self.database_path,
            check_same_thread=False,
            timeout=30
        )

        # --------------------------------------
        # Improve SQLite Concurrency
        # --------------------------------------

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

    def _now(self):
        """
        Return current timestamp.
        """

        return datetime.now().isoformat()

    # --------------------------------------------------
    # Commit
    # --------------------------------------------------

    def commit(self):
        """
        Commit all pending database changes.
        """

        with self.lock:

            if self.connection:

                self.connection.commit()

    # --------------------------------------------------
    # Batch Commit
    # --------------------------------------------------

    def batch_commit(self):
        """
        Commit pending bulk inserts.
        """

        self.commit()

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

            # ======================================
            # CONTEXT-AWARE CONVERSATION MEMORY
            # ======================================

            self.cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS
                conversation_context (

                    id INTEGER
                    PRIMARY KEY AUTOINCREMENT,

                    user_command TEXT
                    NOT NULL,

                    assistant_response TEXT,

                    intent TEXT,

                    target TEXT,

                    context_data TEXT,

                    created_at TEXT
                    NOT NULL

                )
                """
            )

            # --------------------------------------
            # Persistent User Context
            # --------------------------------------

            self.cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS
                user_context (

                    id INTEGER
                    PRIMARY KEY AUTOINCREMENT,

                    context_key TEXT
                    UNIQUE NOT NULL,

                    context_value TEXT,

                    updated_at TEXT
                    NOT NULL

                )
                """
            )

            # --------------------------------------
            # Command History
            # --------------------------------------

            self.cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS
                command_history (

                    id INTEGER
                    PRIMARY KEY AUTOINCREMENT,

                    command TEXT
                    NOT NULL,

                    intent TEXT,

                    target TEXT,

                    status TEXT,

                    created_at TEXT
                    NOT NULL

                )
                """
            )

            # ======================================
            # INDEXES
            # ======================================

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

            self.cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS
                idx_context_created_at
                ON conversation_context(created_at)
                """
            )

            self.cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS
                idx_context_intent
                ON conversation_context(intent)
                """
            )

            self.cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS
                idx_history_created_at
                ON command_history(created_at)
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
                        self._now()
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
                        self._now()
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

        try:

            old_path = self._normalize_path(
                old_path
            )

            new_path = self._normalize_path(
                new_path
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

                last_modified = self._now()

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

                        self._now(),

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

        return self.update_file_name(
            old_path=old_path,
            new_name=Path(
                new_path
            ).stem,
            new_path=new_path
        )

    # --------------------------------------------------

    def delete_file(
        self,
        full_path
    ):

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

        try:

            file = Path(
                file_path
            )

            if (
                not file.exists()
                or
                not file.is_file()
            ):

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

        return self.delete_file(
            full_path
        )

    # --------------------------------------------------

    def clear_files(self):

        with self.lock:

            self.cursor.execute(
                "DELETE FROM files"
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

                    last_modified = self._now()

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

                        self._now()
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

        try:

            folder = Path(
                folder_path
            )

            if (
                not folder.exists()
                or
                not folder.is_dir()
            ):

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

        try:

            old_path = self._normalize_path(
                old_path
            )

            new_path = self._normalize_path(
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
                        new_name.lower(),

                        new_path,

                        self._now(),

                        self._now(),

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

        try:

            new_folder = Path(
                new_path
            )

            return self.update_folder_name(

                old_path=old_path,

                new_name=new_folder.name,

                new_path=new_path
            )

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

        return self.delete_folder(
            full_path
        )

    # --------------------------------------------------

    def clear_folders(self):

        with self.lock:

            self.cursor.execute(
                "DELETE FROM folders"
            )

            self.connection.commit()

    # ==================================================
    # CONTEXT-AWARE MEMORY METHODS
    # ==================================================

    def add_conversation_context(
        self,
        user_command,
        assistant_response=None,
        intent=None,
        target=None,
        context_data=None
    ):
        """
        Store one conversation interaction.

        context_data can contain additional
        information required for follow-up
        commands.
        """

        try:

            with self.lock:

                self.cursor.execute(
                    """
                    INSERT INTO
                    conversation_context
                    (
                        user_command,
                        assistant_response,
                        intent,
                        target,
                        context_data,
                        created_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        user_command,
                        assistant_response,
                        intent,
                        target,
                        context_data,
                        self._now()
                    )
                )

                self.connection.commit()

            return True

        except Exception as error:

            print(
                f"Conversation Context Error : "
                f"{error}"
            )

            return False

    # --------------------------------------------------

    def get_recent_context(
        self,
        limit=10
    ):
        """
        Return recent conversation context.

        Newest context is returned first.
        """

        try:

            limit = max(
                1,
                int(limit)
            )

            with self.lock:

                self.cursor.execute(
                    """
                    SELECT
                        id,
                        user_command,
                        assistant_response,
                        intent,
                        target,
                        context_data,
                        created_at
                    FROM conversation_context
                    ORDER BY id DESC
                    LIMIT ?
                    """,
                    (
                        limit,
                    )
                )

                return self.cursor.fetchall()

        except Exception as error:

            print(
                f"Get Recent Context Error : "
                f"{error}"
            )

            return []

    # --------------------------------------------------

    def get_latest_context(
        self
    ):
        """
        Return the latest conversation context.
        """

        contexts = (
            self.get_recent_context(
                limit=1
            )
        )

        if contexts:

            return contexts[0]

        return None

    # --------------------------------------------------

    def get_context_by_intent(
        self,
        intent,
        limit=10
    ):
        """
        Return recent context for
        a specific intent.
        """

        try:

            limit = max(
                1,
                int(limit)
            )

            with self.lock:

                self.cursor.execute(
                    """
                    SELECT
                        id,
                        user_command,
                        assistant_response,
                        intent,
                        target,
                        context_data,
                        created_at
                    FROM conversation_context
                    WHERE intent = ?
                    ORDER BY id DESC
                    LIMIT ?
                    """,
                    (
                        intent,
                        limit
                    )
                )

                return self.cursor.fetchall()

        except Exception as error:

            print(
                f"Get Context By Intent Error : "
                f"{error}"
            )

            return []

    # --------------------------------------------------

    def clear_conversation_context(
        self
    ):
        """
        Clear temporary conversation memory.
        """

        try:

            with self.lock:

                self.cursor.execute(
                    """
                    DELETE FROM
                    conversation_context
                    """
                )

                self.connection.commit()

            return True

        except Exception as error:

            print(
                f"Clear Conversation Context Error : "
                f"{error}"
            )

            return False

    # --------------------------------------------------

    def trim_conversation_context(
        self,
        keep_last=100
    ):
        """
        Keep only the latest context records.

        Prevents unlimited database growth.
        """

        try:

            keep_last = max(
                1,
                int(keep_last)
            )

            with self.lock:

                self.cursor.execute(
                    """
                    DELETE FROM conversation_context
                    WHERE id NOT IN
                    (
                        SELECT id
                        FROM conversation_context
                        ORDER BY id DESC
                        LIMIT ?
                    )
                    """,
                    (
                        keep_last,
                    )
                )

                self.connection.commit()

            return True

        except Exception as error:

            print(
                f"Trim Context Error : {error}"
            )

            return False

    # ==================================================
    # USER CONTEXT METHODS
    # ==================================================

    def set_user_context(
        self,
        context_key,
        context_value
    ):
        """
        Store persistent user context.

        Example:

        preferred_browser -> chrome
        last_opened_file -> report.pdf
        """

        try:

            context_key = (
                str(context_key)
                .strip()
                .lower()
            )

            with self.lock:

                self.cursor.execute(
                    """
                    INSERT INTO
                    user_context
                    (
                        context_key,
                        context_value,
                        updated_at
                    )
                    VALUES (?, ?, ?)

                    ON CONFLICT(context_key)
                    DO UPDATE SET

                        context_value =
                        excluded.context_value,

                        updated_at =
                        excluded.updated_at
                    """,
                    (
                        context_key,
                        str(context_value),

                        self._now()
                    )
                )

                self.connection.commit()

            return True

        except Exception as error:

            print(
                f"Set User Context Error : "
                f"{error}"
            )

            return False

    # --------------------------------------------------

    def get_user_context(
        self,
        context_key,
        default=None
    ):
        """
        Get one persistent context value.
        """

        try:

            context_key = (
                str(context_key)
                .strip()
                .lower()
            )

            with self.lock:

                self.cursor.execute(
                    """
                    SELECT context_value
                    FROM user_context
                    WHERE context_key = ?
                    """,
                    (
                        context_key,
                    )
                )

                result = (
                    self.cursor.fetchone()
                )

                if result:

                    return result[0]

                return default

        except Exception as error:

            print(
                f"Get User Context Error : "
                f"{error}"
            )

            return default

    # --------------------------------------------------

    def get_all_user_context(
        self
    ):
        """
        Return all persistent context.
        """

        try:

            with self.lock:

                self.cursor.execute(
                    """
                    SELECT
                        context_key,
                        context_value,
                        updated_at
                    FROM user_context
                    ORDER BY context_key
                    """
                )

                return self.cursor.fetchall()

        except Exception as error:

            print(
                f"Get All User Context Error : "
                f"{error}"
            )

            return []

    # --------------------------------------------------

    def delete_user_context(
        self,
        context_key
    ):
        """
        Delete one persistent context item.
        """

        try:

            context_key = (
                str(context_key)
                .strip()
                .lower()
            )

            with self.lock:

                self.cursor.execute(
                    """
                    DELETE FROM user_context
                    WHERE context_key = ?
                    """,
                    (
                        context_key,
                    )
                )

                self.connection.commit()

            return True

        except Exception as error:

            print(
                f"Delete User Context Error : "
                f"{error}"
            )

            return False

    # --------------------------------------------------

    def clear_user_context(
        self
    ):
        """
        Remove all persistent user context.
        """

        try:

            with self.lock:

                self.cursor.execute(
                    """
                    DELETE FROM user_context
                    """
                )

                self.connection.commit()

            return True

        except Exception as error:

            print(
                f"Clear User Context Error : "
                f"{error}"
            )

            return False

    # ==================================================
    # COMMAND HISTORY METHODS
    # ==================================================

    def add_command_history(
        self,
        command,
        intent=None,
        target=None,
        status="SUCCESS"
    ):
        """
        Store executed command history.
        """

        try:

            with self.lock:

                self.cursor.execute(
                    """
                    INSERT INTO
                    command_history
                    (
                        command,
                        intent,
                        target,
                        status,
                        created_at
                    )
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        command,
                        intent,
                        target,
                        status,
                        self._now()
                    )
                )

                self.connection.commit()

            return True

        except Exception as error:

            print(
                f"Command History Error : "
                f"{error}"
            )

            return False

    # --------------------------------------------------

    def get_recent_commands(
        self,
        limit=20
    ):
        """
        Return recently executed commands.
        """

        try:

            limit = max(
                1,
                int(limit)
            )

            with self.lock:

                self.cursor.execute(
                    """
                    SELECT
                        id,
                        command,
                        intent,
                        target,
                        status,
                        created_at
                    FROM command_history
                    ORDER BY id DESC
                    LIMIT ?
                    """,
                    (
                        limit,
                    )
                )

                return self.cursor.fetchall()

        except Exception as error:

            print(
                f"Get Recent Commands Error : "
                f"{error}"
            )

            return []

    # --------------------------------------------------

    def get_last_command(
        self
    ):
        """
        Return the most recently
        executed command.
        """

        commands = (
            self.get_recent_commands(
                limit=1
            )
        )

        if commands:

            return commands[0]

        return None

    # --------------------------------------------------

    def clear_command_history(
        self
    ):
        """
        Clear command execution history.
        """

        try:

            with self.lock:

                self.cursor.execute(
                    """
                    DELETE FROM command_history
                    """
                )

                self.connection.commit()

            return True

        except Exception as error:

            print(
                f"Clear Command History Error : "
                f"{error}"
            )

            return False

    # --------------------------------------------------

    def trim_command_history(
        self,
        keep_last=500
    ):
        """
        Prevent unlimited command
        history growth.
        """

        try:

            keep_last = max(
                1,
                int(keep_last)
            )

            with self.lock:

                self.cursor.execute(
                    """
                    DELETE FROM command_history
                    WHERE id NOT IN
                    (
                        SELECT id
                        FROM command_history
                        ORDER BY id DESC
                        LIMIT ?
                    )
                    """,
                    (
                        keep_last,
                    )
                )

                self.connection.commit()

            return True

        except Exception as error:

            print(
                f"Trim Command History Error : "
                f"{error}"
            )

            return False

    # ==================================================
    # CLEANUP / SYNCHRONIZATION
    # ==================================================

    def remove_missing_files(
        self,
        commit=True
    ):

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

    def clear_database(
        self
    ):
        """
        Remove all stored ASTRA data.
        """

        with self.lock:

            self.cursor.execute(
                "DELETE FROM applications"
            )

            self.cursor.execute(
                "DELETE FROM aliases"
            )

            self.cursor.execute(
                "DELETE FROM files"
            )

            self.cursor.execute(
                "DELETE FROM folders"
            )

            self.cursor.execute(
                "DELETE FROM conversation_context"
            )

            self.cursor.execute(
                "DELETE FROM user_context"
            )

            self.cursor.execute(
                "DELETE FROM command_history"
            )

            self.connection.commit()

    # ==================================================
    # CLOSE DATABASE
    # ==================================================

    def close(
        self
    ):
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