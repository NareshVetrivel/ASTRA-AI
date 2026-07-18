"""
Database Manager Module

Handles all SQLite database operations
for ASTRA-AI.
"""

import sqlite3
from pathlib import Path
from datetime import datetime


class DatabaseManager:
    """
    SQLite Database Manager.
    """

    def __init__(self):

        # Project Root
        project_root = Path(__file__).resolve().parent.parent

        # Database Path
        self.database_path = (
            project_root /
            "database" /
            "astra.db"
        )

        # Connect Database
        self.connection = sqlite3.connect(
            self.database_path
        )

        self.cursor = self.connection.cursor()

        # Create Required Tables
        self.create_tables()

    # --------------------------------------------------
    # Create Tables
    # --------------------------------------------------

    def create_tables(self):
        """
        Create required database tables.
        """

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

        self.commit()

    # --------------------------------------------------
    # Commit
    # --------------------------------------------------

    def commit(self):
        """
        Commit all pending database changes.
        """

        self.connection.commit()

    # --------------------------------------------------
    # Insert Application
    # --------------------------------------------------

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
                    full_path,
                    source,
                    datetime.now().isoformat()
                )
            )

            self.commit()

            return True

        except Exception as error:

            print(
                f"Application Insert Error : {error}"
            )

            return False

    # --------------------------------------------------
    # Insert Alias
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

            self.commit()

            return True

        except Exception as error:

            print(
                f"Alias Insert Error : {error}"
            )

            return False

    # --------------------------------------------------
    # Insert File
    # --------------------------------------------------

    def insert_file(
        self,
        name,
        extension,
        full_path,
        file_size,
        last_modified
    ):
        """
        Store indexed file.
        """

        try:

            self.cursor.execute(
                """
                INSERT OR REPLACE INTO
                files
                (
                    name,
                    extension,
                    full_path,
                    file_size,
                    last_modified,
                    last_scanned
                )
                VALUES (?, ?, ?, ?, ?, ?)
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

            self.commit()

            return True

        except Exception as error:

            print(
                f"File Insert Error : {error}"
            )

            return False
        
    # --------------------------------------------------
    # Get Application
    # --------------------------------------------------

    def get_application(
        self,
        name
    ):
        """
        Return application details.
        """

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
    # Get Alias
    # --------------------------------------------------

    def get_alias(
        self,
        alias
    ):
        """
        Return application alias.
        """

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
    # Get File
    # --------------------------------------------------

    def get_file(
        self,
        name
    ):
        """
        Return indexed file.
        """

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
    # Search Files
    # --------------------------------------------------

    def search_files(
        self,
        keyword
    ):
        """
        Search matching files.
        """

        self.cursor.execute(
            """
            SELECT
                name,
                extension,
                full_path
            FROM files
            WHERE
                name LIKE ?
            ORDER BY name
            LIMIT 20
            """,
            (
                f"%{keyword.lower()}%",
            )
        )

        return self.cursor.fetchall()

    # --------------------------------------------------
    # Get All Applications
    # --------------------------------------------------

    def get_all_applications(self):
        """
        Return all applications.
        """

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
    # Get All Files
    # --------------------------------------------------

    def get_all_files(self):
        """
        Return all indexed files.
        """

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
    # Application Exists
    # --------------------------------------------------

    def application_exists(
        self,
        name
    ):
        """
        Check application exists.
        """

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

        return self.cursor.fetchone() is not None

    # --------------------------------------------------
    # File Exists
    # --------------------------------------------------

    def file_exists(
        self,
        full_path
    ):
        """
        Check file exists.
        """

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

        return self.cursor.fetchone() is not None

    # --------------------------------------------------
    # Application Count
    # --------------------------------------------------

    def application_count(self):
        """
        Return total applications.
        """

        self.cursor.execute(
            """
            SELECT COUNT(*)
            FROM applications
            """
        )

        return self.cursor.fetchone()[0]

    # --------------------------------------------------
    # File Count
    # --------------------------------------------------

    def file_count(self):
        """
        Return total indexed files.
        """

        self.cursor.execute(
            """
            SELECT COUNT(*)
            FROM files
            """
        )

        return self.cursor.fetchone()[0]

    # --------------------------------------------------
    # Clear Files
    # --------------------------------------------------

    def clear_files(self):
        """
       Remove only indexed files.
        """

        self.cursor.execute(
            """
            DELETE FROM files
            """
        )

        self.commit()

    # --------------------------------------------------
    # Clear Database
    # --------------------------------------------------

    def clear_database(self):
        """
        Remove all stored data.
        """

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

        self.commit()

    # --------------------------------------------------
    # Close Database
    # --------------------------------------------------

    def close(self):
        """
        Close SQLite connection.
        """

        self.connection.close()