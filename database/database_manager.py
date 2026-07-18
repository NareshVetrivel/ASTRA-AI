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

        project_root = Path(__file__).resolve().parent.parent

        self.database_path = (
            project_root /
            "database" /
            "astra.db"
        )

        self.connection = sqlite3.connect(
            self.database_path
        )

        self.cursor = self.connection.cursor()

        self.create_tables()

    # --------------------------------------------------
    # Create Tables
    # --------------------------------------------------

    def create_tables(self):

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

        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS aliases (

                id INTEGER PRIMARY KEY AUTOINCREMENT,

                alias TEXT UNIQUE NOT NULL,

                application_name TEXT NOT NULL

            )
            """
        )

        self.connection.commit()

    # --------------------------------------------------
    # Commit
    # --------------------------------------------------

    def commit(self):

        self.connection.commit()

    # --------------------------------------------------
    # Insert Application
    # --------------------------------------------------

    def insert_application(
        self,
        name,
        exe_name,
        full_path,
        source="scanner"
    ):

        try:

            self.cursor.execute(
                """
                INSERT OR REPLACE INTO applications
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
                f"Database Insert Error : {error}"
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

        try:

            self.cursor.execute(
                """
                INSERT OR REPLACE INTO aliases
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
    # Get Application
    # --------------------------------------------------

    def get_application(
        self,
        name
    ):

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

        self.cursor.execute(
            """
            SELECT application_name
            FROM aliases
            WHERE alias = ?
            """,
            (
                alias.lower(),
            )
        )

        return self.cursor.fetchone()

    # --------------------------------------------------
    # Get All Applications
    # --------------------------------------------------

    def get_all_applications(self):

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
    # Application Exists
    # --------------------------------------------------

    def application_exists(
        self,
        name
    ):

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
    # Database Count
    # --------------------------------------------------

    def application_count(self):

        self.cursor.execute(
            """
            SELECT COUNT(*)
            FROM applications
            """
        )

        return self.cursor.fetchone()[0]

    # --------------------------------------------------
    # Clear Database
    # --------------------------------------------------

    def clear_database(self):

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

        self.commit()

    # --------------------------------------------------
    # Close Database
    # --------------------------------------------------

    def close(self):

        self.connection.close()