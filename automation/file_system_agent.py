"""
ASTRA-AI File System Agent

Central orchestration layer for file and folder automation.

The agent reuses the existing:
    - FileFinder
    - FileManager
    - FolderManager

It does not replace the existing automation modules.

ASTRA-AI V1
"""

from __future__ import annotations

import os
import time
from pathlib import Path
from typing import Optional, Any

from automation.file_finder import FileFinder
from automation.file_manager import FileManager
from automation.folder_manager import FolderManager


class FileSystemAgent:
    """
    Central orchestration layer for ASTRA file/folder automation.

    Responsibilities:
        1. Resolve files and folders.
        2. Validate targets.
        3. Delegate actual operations.
        4. Return consistent result dictionaries.
    """

    def __init__(
        self,
        file_finder: Optional[FileFinder] = None,
        file_manager: Optional[FileManager] = None,
        folder_manager: Optional[FolderManager] = None,
    ):
        self.file_finder = file_finder or FileFinder()
        self.file_manager = file_manager or FileManager()
        self.folder_manager = folder_manager or FolderManager()

        self.home = Path.home()

    # ==================================================
    # RESULT HELPER
    # ==================================================

    @staticmethod
    def _result(
        success: bool,
        action: str,
        message: str,
        **extra: Any,
    ) -> dict:
        """
        Build a consistent result structure.
        """

        result = {
            "success": bool(success),
            "action": action,
            "message": message,
        }

        result.update(extra)

        return result

    # ==================================================
    # BASIC HELPERS
    # ==================================================

    @staticmethod
    def _clean(
        value: Optional[str],
    ) -> str:
        """
        Clean user-provided text/path values.
        """

        if value is None:
            return ""

        return (
            str(value)
            .strip()
            .strip('"')
            .strip("'")
        )

    @staticmethod
    def _path_exists(
        path: Optional[str | Path],
    ) -> bool:
        """
        Check whether a filesystem path exists.
        """

        if not path:
            return False

        try:
            return Path(path).exists()

        except (
            OSError,
            ValueError,
            RuntimeError,
        ):
            return False

    @staticmethod
    def _is_real_directory(
        path: Optional[str | Path],
    ) -> bool:
        """
        Check whether a path is a real directory.
        """

        if not path:
            return False

        try:
            return Path(path).is_dir()

        except (
            OSError,
            ValueError,
            RuntimeError,
        ):
            return False

    # ==================================================
    # SPECIAL FOLDER RESOLUTION
    # ==================================================

    def resolve_special_folder(
        self,
        name: str,
    ) -> Optional[str]:
        """
        Resolve Windows special folders.

        Examples:
            desktop
            documents
            downloads
            pictures
            videos
            music
            this pc
            my computer
            c drive
            d drive
            e drive
            recycle bin
        """

        name = self._clean(name).lower()

        if not name:
            return None

        special_folders = getattr(
            self.folder_manager,
            "special_folders",
            {},
        )

        if not isinstance(
            special_folders,
            dict,
        ):
            special_folders = {}

        # Direct lookup.
        folder = special_folders.get(name)

        # Normalize common aliases.
        if folder is None:

            aliases = {
                "desktop": "desktop",
                "documents": "documents",
                "downloads": "downloads",
                "pictures": "pictures",
                "videos": "videos",
                "music": "music",
                "this pc": "this pc",
                "my computer": "my computer",
                "c drive": "c drive",
                "d drive": "d drive",
                "e drive": "e drive",
                "recycle bin": "recycle bin",
                "trash": "recycle bin",
            }

            alias = aliases.get(name)

            if alias:
                folder = special_folders.get(alias)

        if folder is None:
            return None

        # Windows shell location.
        if isinstance(
            folder,
            str,
        ):

            if folder.lower().startswith(
                "shell:"
            ):
                return folder

            if self._path_exists(folder):
                try:
                    return str(
                        Path(folder).resolve()
                    )
                except (
                    OSError,
                    RuntimeError,
                ):
                    return str(folder)

            return None

        try:

            if folder.exists():
                return str(
                    Path(folder).resolve()
                )

        except (
            OSError,
            AttributeError,
            RuntimeError,
        ):
            pass

        return None

    # ==================================================
    # FILE RESOLUTION
    # ==================================================

    def resolve_file(
        self,
        filename: str,
        selection: Optional[int | str] = None,
    ) -> Optional[str]:
        """
        Resolve a file.

        Multiple matches are never silently selected.
        """

        result = self.resolve_file_selection(
            filename,
            selection,
        )

        if result.get("success"):
            return result.get("path")

        if result.get("requires_selection"):

            print(
                "\n========== FILE SELECTION =========="
            )

            for candidate in result.get(
                "candidates",
                [],
            ):
                print(
                    f"{candidate['index']}. "
                    f"{candidate['name']}"
                )
                print(
                    f"   {candidate['path']}"
                )

            print(
                "====================================\n"
            )

            return None

        print(
            f"File Resolution Failed : {filename}"
        )

        return None

    # ==================================================
    # FILE CANDIDATES
    # ==================================================

    def find_file_candidates(
        self,
        filename: str,
    ) -> list[dict]:
        """
        Search for files using bounded filesystem scanning.

        Exact filename/stem matches have priority.
        """

        filename = self._clean(filename)

        if not filename:
            return []

        search_name = filename.lower().strip()

        locations = [
            self.home / "Desktop",
            self.home / "Documents",
            self.home / "Downloads",
            self.home / "Pictures",
            self.home / "Videos",
            self.home / "Music",

            self.home / "OneDrive" / "Desktop",
            self.home / "OneDrive" / "Documents",
            self.home / "OneDrive" / "Downloads",
            self.home / "OneDrive" / "Pictures",
            self.home / "OneDrive" / "Videos",
            self.home / "OneDrive" / "Music",

            Path("E:/"),
        ]

        unique_locations = []
        seen_locations = set()

        for location in locations:

            try:

                resolved = location.resolve()
                key = str(
                    resolved
                ).lower()

                if key in seen_locations:
                    continue

                if not resolved.exists():
                    continue

                if not resolved.is_dir():
                    continue

                seen_locations.add(key)
                unique_locations.append(
                    resolved
                )

            except (
                OSError,
                RuntimeError,
            ):
                continue

        exact = {}
        partial = {}

        max_candidates = 50
        max_files_scanned = 100_000
        max_scan_seconds = 4.0

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

        for location in unique_locations:

            if timed_out:
                break

            if len(exact) >= max_candidates:
                break

            try:

                for root, dirs, files in os.walk(
                    location,
                    topdown=True,
                ):

                    dirs[:] = [
                        directory
                        for directory in dirs
                        if directory.lower()
                        not in excluded_directories
                    ]

                    for file_name in files:

                        files_scanned += 1

                        if (
                            files_scanned
                            >= max_files_scanned
                        ):
                            timed_out = True
                            break

                        if (
                            time.monotonic()
                            - started_at
                            >= max_scan_seconds
                        ):
                            timed_out = True
                            break

                        try:

                            path = (
                                Path(root)
                                / file_name
                            ).resolve()

                            actual_name = (
                                path.name.lower()
                            )

                            actual_stem = (
                                path.stem.lower()
                            )

                            key = str(
                                path
                            ).lower()

                            if (
                                search_name
                                == actual_name
                                or
                                search_name
                                == actual_stem
                            ):
                                exact[key] = path

                            elif (
                                search_name
                                in actual_name
                                or
                                search_name
                                in actual_stem
                            ):
                                partial[key] = path

                            if (
                                len(exact)
                                >= max_candidates
                            ):
                                break

                        except (
                            PermissionError,
                            FileNotFoundError,
                            OSError,
                            RuntimeError,
                        ):
                            continue

                    if timed_out:
                        break

                    if (
                        len(exact)
                        >= max_candidates
                    ):
                        break

            except (
                PermissionError,
                FileNotFoundError,
                OSError,
                RuntimeError,
            ):
                continue

        matches = list(
            exact.values()
        )

        if not matches:
            matches = list(
                partial.values()
            )

        matches = matches[
            :max_candidates
        ]

        # Database/index fallback.
        if not matches:

            try:

                path = (
                    self.file_finder
                    .find_file(filename)
                )

                if path:

                    candidate = (
                        Path(path)
                        .resolve()
                    )

                    if (
                        candidate.exists()
                        and
                        candidate.is_file()
                    ):
                        matches.append(
                            candidate
                        )

            except Exception:
                pass

        matches.sort(
            key=lambda item:
            str(item).lower()
        )

        return [
            {
                "index": index,
                "name": path.name,
                "path": str(path),
            }
            for index, path
            in enumerate(
                matches,
                start=1,
            )
        ]

    # ==================================================
    # FILE SELECTION
    # ==================================================

    def resolve_file_selection(
        self,
        filename: str,
        selection: Optional[int | str] = None,
        force_selection: bool = False,
    ) -> dict:
        """
        Resolve a file with explicit selection handling.
        """

        candidates = (
            self.find_file_candidates(
                filename
            )
        )

        print(
            "\n========== FILE SELECTION DEBUG =========="
        )

        print(
            f"Search filename : {filename}"
        )

        print(
            f"Candidates found: {len(candidates)}"
        )

        for candidate in candidates:

            print(
                f"{candidate['index']}. "
                f"{candidate['name']} -> "
                f"{candidate['path']}"
            )

        print(
            "==========================================\n"
        )

        if not candidates:

            return self._result(
                False,
                "resolve_file",
                f"File not found: {filename}",
                candidates=[],
                requires_selection=False,
            )

        # --------------------------------------------------
        # Force UI selection for destructive / file-transfer
        # operations even when only one candidate exists.
        # --------------------------------------------------

        if len(candidates) == 1 and force_selection:

            if selection is None:

                return self._result(
                    False,
                    "resolve_file",
                    (
                        f"File found for '{filename}'. "
                        "Please select the file."
                    ),
                    candidates=candidates,
                    requires_selection=True,
                )

        # --------------------------------------------------
        # Normal single-file resolution
        # --------------------------------------------------

        if len(candidates) == 1:

            return self._result(
                True,
                "resolve_file",
                (
                    f"File resolved: "
                    f"{candidates[0]['path']}"
                ),
                path=candidates[0]["path"],
                candidates=candidates,
                requires_selection=False,
            )

        if selection is None:

            return self._result(
                False,
                "resolve_file",
                (
                    f"Multiple files found "
                    f"for '{filename}'. "
                    "Please select one."
                ),
                candidates=candidates,
                requires_selection=True,
            )

        try:

            selected_index = int(
                str(selection).strip()
            )

        except (
            TypeError,
            ValueError,
        ):

            return self._result(
                False,
                "resolve_file",
                "Invalid file selection.",
                candidates=candidates,
                requires_selection=True,
            )

        if not (
            1
            <= selected_index
            <= len(candidates)
        ):

            return self._result(
                False,
                "resolve_file",
                (
                    "Invalid selection. "
                    f"Choose between 1 and "
                    f"{len(candidates)}."
                ),
                candidates=candidates,
                requires_selection=True,
            )

        selected = candidates[
            selected_index - 1
        ]

        return self._result(
            True,
            "resolve_file",
            (
                f"File selected: "
                f"{selected['path']}"
            ),
            path=selected["path"],
            candidates=candidates,
            selected_index=selected_index,
            requires_selection=False,
        )

    # ==================================================
    # FOLDER RESOLUTION
    # ==================================================

    def resolve_folder(
        self,
        folder_name: str,
    ) -> Optional[str]:
        """
        Resolve a folder reliably.

        Search order:

            1. Direct filesystem path
            2. Special Windows folder
            3. Common user folder
            4. Home directory
            5. OneDrive user folders
            6. Bounded recursive search
            7. FolderManager resolver, if available
        """

        folder_name = self._clean(
            folder_name
        )

        if not folder_name:
            return None

        normalized = (
            folder_name
            .lower()
            .strip()
            .rstrip("\\/")
        )

        # --------------------------------------------------
        # 1. Direct path
        # --------------------------------------------------

        direct_path = Path(
            folder_name
        ).expanduser()

        try:

            if (
                direct_path.exists()
                and direct_path.is_dir()
            ):

                return str(
                    direct_path.resolve()
                )

        except (
            OSError,
            RuntimeError,
        ):
            pass

        # --------------------------------------------------
        # 2. Special folders
        # --------------------------------------------------

        special = (
            self.resolve_special_folder(
                folder_name
            )
        )

        if special:
            return special

        # --------------------------------------------------
        # 3. Common folders
        # --------------------------------------------------

        common_folders = {

            "desktop":
                self.home / "Desktop",

            "documents":
                self.home / "Documents",

            "downloads":
                self.home / "Downloads",

            "pictures":
                self.home / "Pictures",

            "videos":
                self.home / "Videos",

            "music":
                self.home / "Music",

            "onedrive":
                self.home / "OneDrive",

        }

        common = common_folders.get(
            normalized
        )

        if common:

            try:

                if common.is_dir():

                    return str(
                        common.resolve()
                    )

            except (
                OSError,
                RuntimeError,
            ):
                pass

        # --------------------------------------------------
        # 4. Home direct children
        # --------------------------------------------------

        try:

            for child in self.home.iterdir():

                try:

                    if not child.is_dir():
                        continue

                    if (
                        child.name.lower()
                        == normalized
                    ):

                        return str(
                            child.resolve()
                        )

                except (
                    OSError,
                    RuntimeError,
                ):
                    continue

        except (
            OSError,
            PermissionError,
        ):
            pass

        # --------------------------------------------------
        # 5. OneDrive direct children
        # --------------------------------------------------

        onedrive = (
            self.home / "OneDrive"
        )

        if onedrive.is_dir():

            try:

                for child in onedrive.iterdir():

                    try:

                        if not child.is_dir():
                            continue

                        if (
                            child.name.lower()
                            == normalized
                        ):

                            return str(
                                child.resolve()
                            )

                    except (
                        OSError,
                        RuntimeError,
                    ):
                        continue

            except (
                OSError,
                PermissionError,
            ):
                pass

        # --------------------------------------------------
        # 6. Bounded recursive folder search
        # --------------------------------------------------

        search_roots = [
            self.home,
            self.home / "OneDrive",
        ]

        # E drive is included because your ASTRA
        # initialization already indexes E:.
        if Path("E:/").exists():
            search_roots.append(
                Path("E:/")
            )

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

        started_at = time.monotonic()

        max_scan_seconds = 3.0
        max_directories = 25_000
        directories_scanned = 0

        seen_roots = set()

        for root in search_roots:

            try:

                root = root.resolve()

            except (
                OSError,
                RuntimeError,
            ):
                continue

            root_key = str(
                root
            ).lower()

            if root_key in seen_roots:
                continue

            seen_roots.add(
                root_key
            )

            if not root.is_dir():
                continue

            try:

                for current_root, dirs, _files in os.walk(
                    root,
                    topdown=True,
                ):

                    directories_scanned += 1

                    if (
                        directories_scanned
                        >= max_directories
                    ):
                        break

                    if (
                        time.monotonic()
                        - started_at
                        >= max_scan_seconds
                    ):
                        break

                    dirs[:] = [
                        directory
                        for directory in dirs
                        if directory.lower()
                        not in excluded_directories
                    ]

                    for directory in dirs:

                        if (
                            directory.lower()
                            == normalized
                        ):

                            candidate = (
                                Path(current_root)
                                / directory
                            )

                            try:

                                if candidate.is_dir():

                                    return str(
                                        candidate.resolve()
                                    )

                            except (
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

        # --------------------------------------------------
        # 7. FolderManager fallback
        # --------------------------------------------------

        manager_resolver = getattr(
            self.folder_manager,
            "resolve_folder",
            None,
        )

        if callable(
            manager_resolver
        ):

            try:

                resolved = (
                    manager_resolver(
                        folder_name
                    )
                )

                if (
                    resolved
                    and self._is_real_directory(
                        resolved
                    )
                ):

                    return str(
                        Path(resolved)
                        .resolve()
                    )

            except Exception:
                pass

        return None

    # ==================================================
    # GENERIC TARGET RESOLUTION
    # ==================================================

    def resolve_target(
        self,
        target: str,
        target_type: str = "auto",
    ) -> Optional[str]:

        target = self._clean(
            target
        )

        target_type = (
            self._clean(
                target_type
            ).lower()
        )

        if not target:
            return None

        if target_type == "file":
            return self.resolve_file(
                target
            )

        if target_type == "folder":
            return self.resolve_folder(
                target
            )

        # Direct path.
        direct = Path(
            target
        ).expanduser()

        try:

            if direct.exists():

                return str(
                    direct.resolve()
                )

        except (
            OSError,
            RuntimeError,
        ):
            pass

        file_path = self.resolve_file(
            target
        )

        if file_path:
            return file_path

        return self.resolve_folder(
            target
        )

    # ==================================================
    # FILE OPERATIONS
    # ==================================================

    def open_file(
        self,
        filename: str,
        selection: Optional[int | str] = None,
    ) -> dict:

        path_result = (
            self.resolve_file_selection(
                filename,
                selection,
            )
        )

        if path_result.get(
            "requires_selection"
        ):
            return path_result

        path = path_result.get(
            "path"
        )

        if not path:

            return self._result(
                False,
                "open_file",
                f"File not found: {filename}",
                candidates=path_result.get(
                    "candidates",
                    [],
                ),
            )

        try:

            success = (
                self.file_manager
                .open_file(path)
            )

            return self._result(
                success,
                "open_file",
                (
                    f"File opened: {path}"
                    if success
                    else
                    f"Unable to open file: {path}"
                ),
                path=path,
            )

        except Exception as error:

            return self._result(
                False,
                "open_file",
                f"Unable to open file: {error}",
                path=path,
            )

    # --------------------------------------------------

    def create_file(
        self,
        file_path: str,
        content: str = "",
    ) -> dict:

        file_path = self._clean(
            file_path
        )

        if not file_path:

            return self._result(
                False,
                "create_file",
                "File path is required.",
            )

        try:

            success = (
                self.file_manager
                .create_file(
                    file_path,
                    content,
                )
            )

            return self._result(
                success,
                "create_file",
                (
                    f"File created: {file_path}"
                    if success
                    else
                    f"Unable to create file: {file_path}"
                ),
                path=file_path,
            )

        except Exception as error:

            return self._result(
                False,
                "create_file",
                f"Unable to create file: {error}",
                path=file_path,
            )

    # --------------------------------------------------

    def rename_file(
        self,
        filename: str,
        new_name: str,
        selection: Optional[int | str] = None,
    ) -> dict:

        filename = self._clean(
            filename
        )

        new_name = self._clean(
            new_name
        )

        if not filename or not new_name:

            return self._result(
                False,
                "rename_file",
                "Source file and new name are required.",
            )

        path_result = (
            self.resolve_file_selection(
                filename,
                selection,
            )
        )

        if path_result.get(
            "requires_selection"
        ):
            return path_result

        path = path_result.get(
            "path"
        )

        if not path:

            return self._result(
                False,
                "rename_file",
                f"File not found: {filename}",
                candidates=path_result.get(
                    "candidates",
                    [],
                ),
            )

        try:

            success = (
                self.file_manager
                .rename_file(
                    path,
                    new_name,
                )
            )

            return self._result(
                success,
                "rename_file",
                (
                    f"File renamed: {new_name}"
                    if success
                    else
                    f"Unable to rename file: {path}"
                ),
                path=path,
                new_name=new_name,
                selected_index=path_result.get(
                    "selected_index"
                ),
            )

        except Exception as error:

            return self._result(
                False,
                "rename_file",
                f"Rename failed: {error}",
                path=path,
                new_name=new_name,
            )

    # --------------------------------------------------

    def copy_file(
        self,
        filename: str,
        destination: str,
        selection: Optional[int | str] = None,
    ) -> dict:

        filename = self._clean(
            filename
        )

        destination = self._clean(
            destination
        )

        if not filename or not destination:

            return self._result(
                False,
                "copy_file",
                "Source file and destination are required.",
            )

        source_result = (
            self.resolve_file_selection(
                filename,
                selection,
            )
        )

        if source_result.get(
            "requires_selection"
        ):
            return source_result

        source = source_result.get(
            "path"
        )

        if not source:

            return self._result(
                False,
                "copy_file",
                f"File not found: {filename}",
            )

        destination_path = (
            self.resolve_folder(
                destination
            )
        )

        if not destination_path:

            return self._result(
                False,
                "copy_file",
                (
                    "Destination folder "
                    f"not found: {destination}"
                ),
            )

        try:

            success = (
                self.file_manager
                .copy_file(
                    source,
                    destination_path,
                )
            )

            return self._result(
                success,
                "copy_file",
                (
                    "File copied successfully."
                    if success
                    else
                    "Unable to copy file."
                ),
                source=source,
                destination=destination_path,
            )

        except Exception as error:

            return self._result(
                False,
                "copy_file",
                f"Copy failed: {error}",
                source=source,
                destination=destination_path,
            )

    # --------------------------------------------------

    def move_file(
        self,
        filename: str,
        destination: str,
        selection: Optional[int | str] = None,
    ) -> dict:

        filename = self._clean(
            filename
        )

        destination = self._clean(
            destination
        )

        if not filename or not destination:

            return self._result(
                False,
                "move_file",
                "Source file and destination are required.",
            )

        source_result = (
            self.resolve_file_selection(
                filename,
                selection,
            )
        )

        if source_result.get(
            "requires_selection"
        ):
            return source_result

        source = source_result.get(
            "path"
        )

        if not source:

            return self._result(
                False,
                "move_file",
                f"File not found: {filename}",
            )

        destination_path = (
            self.resolve_folder(
                destination
            )
        )

        if not destination_path:

            return self._result(
                False,
                "move_file",
                (
                    "Destination folder "
                    f"not found: {destination}"
                ),
            )

        try:

            success = (
                self.file_manager
                .move_file(
                    source,
                    destination_path,
                )
            )

            return self._result(
                success,
                "move_file",
                (
                    "File moved successfully."
                    if success
                    else
                    "Unable to move file."
                ),
                source=source,
                destination=destination_path,
            )

        except Exception as error:

            return self._result(
                False,
                "move_file",
                f"Move failed: {error}",
                source=source,
                destination=destination_path,
            )

    # --------------------------------------------------

    def delete_file(
        self,
        filename: str,
        selection: Optional[int | str] = None,
    ) -> dict:

        filename = self._clean(
            filename
        )

        if not filename:

            return self._result(
                False,
                "delete_file",
                "File name is required.",
            )

        path_result = (
            self.resolve_file_selection(
                filename,
                selection,
            )
        )

        if path_result.get(
            "requires_selection"
        ):
            return path_result

        path = path_result.get(
            "path"
        )

        if not path:

            return self._result(
                False,
                "delete_file",
                f"File not found: {filename}",
            )

        try:

            success = (
                self.file_manager
                .delete_file(path)
            )

            return self._result(
                success,
                "delete_file",
                (
                    f"File deleted: {path}"
                    if success
                    else
                    f"Unable to delete file: {path}"
                ),
                path=path,
                selected_index=path_result.get(
                    "selected_index"
                ),
            )

        except Exception as error:

            return self._result(
                False,
                "delete_file",
                f"Delete failed: {error}",
                path=path,
            )

    # ==================================================
    # FOLDER OPERATIONS
    # ==================================================

    def open_folder(
        self,
        folder_name: str,
    ) -> dict:

        folder = (
            self.resolve_folder(
                folder_name
            )
        )

        if not folder:

            return self._result(
                False,
                "open_folder",
                f"Folder not found: {folder_name}",
            )

        # Shell location.
        if folder.lower().startswith(
            "shell:"
        ):

            try:

                success = (
                    self.folder_manager
                    .open_folder(
                        folder_name
                    )
                )

                return self._result(
                    success,
                    "open_folder",
                    (
                        f"Folder opened: {folder_name}"
                        if success
                        else
                        f"Unable to open folder: {folder_name}"
                    ),
                    folder=folder_name,
                )

            except Exception as error:

                return self._result(
                    False,
                    "open_folder",
                    f"Open folder failed: {error}",
                )

        try:

            # Prefer the complete resolved path.
            success = (
                self.folder_manager
                .open_folder(folder)
            )

            # Compatibility fallback for managers
            # expecting only a folder name.
            if not success:

                success = (
                    self.folder_manager
                    .open_folder(
                        Path(folder).name
                    )
                )

            return self._result(
                success,
                "open_folder",
                (
                    f"Folder opened: {folder}"
                    if success
                    else
                    f"Unable to open folder: {folder}"
                ),
                path=folder,
            )

        except Exception as error:

            return self._result(
                False,
                "open_folder",
                f"Open folder failed: {error}",
                path=folder,
            )

    # --------------------------------------------------

    def create_folder(
        self,
        folder_path: str,
    ) -> dict:

        folder_path = self._clean(
            folder_path
        )

        if not folder_path:

            return self._result(
                False,
                "create_folder",
                "Folder path is required.",
            )

        try:

            success = (
                self.folder_manager
                .create_folder(
                    folder_path
                )
            )

            # Verify filesystem state.
            created_path = Path(
                folder_path
            ).expanduser()

            exists_after = (
                created_path.exists()
                and created_path.is_dir()
            )

            final_success = (
                bool(success)
                and exists_after
            )

            return self._result(
                final_success,
                "create_folder",
                (
                    f"Folder created: {folder_path}"
                    if final_success
                    else
                    f"Unable to create folder: {folder_path}"
                ),
                path=str(
                    created_path
                ),
            )

        except Exception as error:

            return self._result(
                False,
                "create_folder",
                f"Create folder failed: {error}",
                path=folder_path,
            )

    # --------------------------------------------------

    def rename_folder(
        self,
        folder_name: str,
        new_name: str,
    ) -> dict:

        folder_name = self._clean(
            folder_name
        )

        new_name = self._clean(
            new_name
        )

        if not folder_name or not new_name:

            return self._result(
                False,
                "rename_folder",
                "Source folder and new name are required.",
            )

        source = (
            self.resolve_folder(
                folder_name
            )
        )

        if not source:

            return self._result(
                False,
                "rename_folder",
                f"Folder not found: {folder_name}",
            )

        if source.lower().startswith(
            "shell:"
        ):

            return self._result(
                False,
                "rename_folder",
                (
                    "Windows shell folders "
                    "cannot be renamed by path."
                ),
            )

        source_path = Path(
            source
        )

        if not source_path.is_dir():

            return self._result(
                False,
                "rename_folder",
                f"Source is not a folder: {source}",
            )

        # Preserve source parent.
        destination_path = (
            source_path.parent / new_name
        )

        if destination_path.exists():

            return self._result(
                False,
                "rename_folder",
                (
                    "A folder with the new name "
                    "already exists."
                ),
                source=source,
                destination=str(
                    destination_path
                ),
            )

        try:

            print(
                "\n========== FOLDER RENAME =========="
            )

            print(
                f"Source      : {source}"
            )

            print(
                f"New name    : {new_name}"
            )

            print(
                f"Destination : {destination_path}"
            )

            print(
                "====================================\n"
            )

            success = (
                self.folder_manager
                .rename_folder(
                    source,
                    new_name,
                )
            )

            # Verify actual filesystem result.
            renamed_exists = (
                destination_path.exists()
                and destination_path.is_dir()
            )

            source_exists = (
                source_path.exists()
            )

            final_success = (
                bool(success)
                and renamed_exists
                and not source_exists
            )

            return self._result(
                final_success,
                "rename_folder",
                (
                    f"Folder renamed to: {new_name}"
                    if final_success
                    else
                    f"Unable to rename folder: {source}"
                ),
                source=source,
                new_name=new_name,
                destination=str(
                    destination_path
                ),
            )

        except Exception as error:

            return self._result(
                False,
                "rename_folder",
                f"Rename folder failed: {error}",
                source=source,
                new_name=new_name,
            )

    # --------------------------------------------------

    def copy_folder(
        self,
        folder_name: str,
        destination: str,
    ) -> dict:

        folder_name = self._clean(
            folder_name
        )

        destination = self._clean(
            destination
        )

        if not folder_name or not destination:

            return self._result(
                False,
                "copy_folder",
                (
                    "Source folder and destination "
                    "are required."
                ),
            )

        source = (
            self.resolve_folder(
                folder_name
            )
        )

        if not source:

            return self._result(
                False,
                "copy_folder",
                f"Folder not found: {folder_name}",
            )

        if source.lower().startswith(
            "shell:"
        ):

            return self._result(
                False,
                "copy_folder",
                (
                    "Windows shell folders "
                    "cannot be copied directly."
                ),
            )

        destination_path = (
            self.resolve_folder(
                destination
            )
        )

        if not destination_path:

            return self._result(
                False,
                "copy_folder",
                (
                    "Destination folder "
                    f"not found: {destination}"
                ),
            )

        try:

            success = (
                self.folder_manager
                .copy_folder(
                    source,
                    destination_path,
                )
            )

            # Typical copy result:
            expected = (
                Path(destination_path)
                / Path(source).name
            )

            copied_exists = (
                expected.exists()
                and expected.is_dir()
            )

            final_success = (
                bool(success)
                and copied_exists
            )

            return self._result(
                final_success,
                "copy_folder",
                (
                    "Folder copied successfully."
                    if final_success
                    else
                    "Unable to copy folder."
                ),
                source=source,
                destination=destination_path,
                copied_path=str(
                    expected
                ),
            )

        except Exception as error:

            return self._result(
                False,
                "copy_folder",
                f"Copy folder failed: {error}",
                source=source,
                destination=destination_path,
            )

    # --------------------------------------------------

    def move_folder(
        self,
        folder_name: str,
        destination: str,
    ) -> dict:

        folder_name = self._clean(
            folder_name
        )

        destination = self._clean(
            destination
        )

        if not folder_name or not destination:

            return self._result(
                False,
                "move_folder",
                (
                    "Source folder and destination "
                    "are required."
                ),
            )

        source = (
            self.resolve_folder(
                folder_name
            )
        )

        if not source:

            return self._result(
                False,
                "move_folder",
                f"Folder not found: {folder_name}",
            )

        if source.lower().startswith(
            "shell:"
        ):

            return self._result(
                False,
                "move_folder",
                (
                    "Windows shell folders "
                    "cannot be moved directly."
                ),
            )

        destination_path = (
            self.resolve_folder(
                destination
            )
        )

        if not destination_path:

            return self._result(
                False,
                "move_folder",
                (
                    "Destination folder "
                    f"not found: {destination}"
                ),
            )

        try:

            success = (
                self.folder_manager
                .move_folder(
                    source,
                    destination_path,
                )
            )

            expected = (
                Path(destination_path)
                / Path(source).name
            )

            moved_exists = (
                expected.exists()
                and expected.is_dir()
            )

            source_exists = (
                Path(source).exists()
            )

            final_success = (
                bool(success)
                and moved_exists
                and not source_exists
            )

            return self._result(
                final_success,
                "move_folder",
                (
                    "Folder moved successfully."
                    if final_success
                    else
                    "Unable to move folder."
                ),
                source=source,
                destination=destination_path,
                moved_path=str(
                    expected
                ),
            )

        except Exception as error:

            return self._result(
                False,
                "move_folder",
                f"Move folder failed: {error}",
                source=source,
                destination=destination_path,
            )

    # --------------------------------------------------

    def delete_folder(
        self,
        folder_name: str,
    ) -> dict:

        folder_name = self._clean(
            folder_name
        )

        if not folder_name:

            return self._result(
                False,
                "delete_folder",
                "Folder name is required.",
            )

        source = (
            self.resolve_folder(
                folder_name
            )
        )

        if not source:

            return self._result(
                False,
                "delete_folder",
                f"Folder not found: {folder_name}",
            )

        if source.lower().startswith(
            "shell:"
        ):

            return self._result(
                False,
                "delete_folder",
                (
                    "Windows shell folders "
                    "cannot be deleted directly."
                ),
            )

        try:

            success = (
                self.folder_manager
                .delete_folder(
                    source
                )
            )

            deleted = not Path(
                source
            ).exists()

            final_success = (
                bool(success)
                and deleted
            )

            return self._result(
                final_success,
                "delete_folder",
                (
                    f"Folder deleted: {source}"
                    if final_success
                    else
                    f"Unable to delete folder: {source}"
                ),
                path=source,
            )

        except Exception as error:

            return self._result(
                False,
                "delete_folder",
                f"Delete folder failed: {error}",
                path=source,
            )

    # ==================================================
    # GENERIC EXECUTOR
    # ==================================================

    def execute(
        self,
        action: str,
        parameters: Optional[dict] = None,
    ) -> dict:
        """
        Stable entry point used by CommandDispatcher.
        """

        action = self._clean(
            action
        ).lower()

        parameters = parameters or {}

        try:

            # --------------------------------------------------
            # Selection
            # --------------------------------------------------

            selection = parameters.get(
                "selection"
            )

            if selection is None:

                selection = (
                    parameters.get(
                        "selected_index"
                    )
                )

            if selection is None:

                selection = (
                    parameters.get(
                        "file_selection"
                    )
                )

            # ==================================================
            # FILE ACTIONS
            # ==================================================

            if action == "open_file":

                filename = (
                    parameters.get("filename")
                    or parameters.get("file")
                    or parameters.get("file_path")
                    or parameters.get("path")
                    or parameters.get("entity")
                )

                return self.open_file(
                    filename,
                    selection,
                )

            if action == "create_file":

                file_path = (
                    parameters.get("file_path")
                    or parameters.get("path")
                    or parameters.get("filename")
                    or parameters.get("file")
                    or parameters.get("entity")
                )

                return self.create_file(
                    file_path,
                    parameters.get(
                        "content",
                        "",
                    ),
                )

            if action == "rename_file":

                source = (
                    parameters.get("file_path")
                    or parameters.get("filename")
                    or parameters.get("file")
                    or parameters.get("source")
                    or parameters.get("source_path")
                    or parameters.get("entity")
                )

                new_name = (
                    parameters.get("new_name")
                    or parameters.get("newName")
                    or parameters.get("destination")
                    or parameters.get("destination_name")
                )

                return self.rename_file(
                    source,
                    new_name,
                    selection,
                )

            if action == "copy_file":

                source = (
                    parameters.get("file_path")
                    or parameters.get("filename")
                    or parameters.get("file")
                    or parameters.get("source")
                    or parameters.get("source_path")
                    or parameters.get("entity")
                )

                destination = (
                    parameters.get("destination")
                    or parameters.get("destination_folder")
                    or parameters.get("destination_path")
                    or parameters.get("target")
                    or parameters.get("target_folder")
                )

                return self.copy_file(
                    source,
                    destination,
                    selection,
                )

            if action == "move_file":

                source = (
                    parameters.get("file_path")
                    or parameters.get("filename")
                    or parameters.get("file")
                    or parameters.get("source")
                    or parameters.get("source_path")
                    or parameters.get("entity")
                )

                destination = (
                    parameters.get("destination")
                    or parameters.get("destination_folder")
                    or parameters.get("destination_path")
                    or parameters.get("target")
                    or parameters.get("target_folder")
                )

                return self.move_file(
                    source,
                    destination,
                    selection,
                )

            if action == "delete_file":

                filename = (
                    parameters.get("file_path")
                    or parameters.get("filename")
                    or parameters.get("file")
                    or parameters.get("path")
                    or parameters.get("source")
                    or parameters.get("entity")
                )

                return self.delete_file(
                    filename,
                    selection,
                )

            # ==================================================
            # ZIP ACTIONS
            # ==================================================

            if action in (
                "compress_file",
                "compress_zip",
            ):

                filename = (
                    parameters.get("filename")
                    or parameters.get("file")
                    or parameters.get("file_path")
                    or parameters.get("source")
                    or parameters.get("entity")
                )

                source_result = (
                    self.resolve_file_selection(
                        filename,
                        selection,
                    )
                )

                if source_result.get(
                    "requires_selection"
                ):
                    return source_result

                source = source_result.get(
                    "path"
                )

                if not source:
                    return source_result

                success = (
                    self.file_manager
                    .compress_file(
                        source
                    )
                )

                return self._result(
                    success,
                    action,
                    (
                        "ZIP archive created successfully."
                        if success
                        else
                        "Unable to create ZIP archive."
                    ),
                    path=source,
                )

            if action in (
                "extract_zip",
                "unzip",
            ):

                filename = (
                    parameters.get("filename")
                    or parameters.get("file")
                    or parameters.get("zip_file")
                    or parameters.get("source")
                    or parameters.get("entity")
                )

                source_result = (
                    self.resolve_file_selection(
                        filename,
                        selection,
                    )
                )

                if source_result.get(
                    "requires_selection"
                ):
                    return source_result

                source = source_result.get(
                    "path"
                )

                if not source:
                    return source_result

                success = (
                    self.file_manager
                    .extract_zip(
                        source
                    )
                )

                return self._result(
                    success,
                    action,
                    (
                        "ZIP archive extracted successfully."
                        if success
                        else
                        "Unable to extract ZIP archive."
                    ),
                    path=source,
                    selected_index=source_result.get(
                        "selected_index"
                    ),
                )

            # ==================================================
            # FOLDER ACTIONS
            # ==================================================

            if action == "open_folder":

                folder = (
                    parameters.get("folder_path")
                    or parameters.get("path")
                    or parameters.get("folder")
                    or parameters.get("folder_name")
                    or parameters.get("entity")
                )

                return self.open_folder(
                    folder
                )

            if action == "create_folder":

                folder_path = (
                    parameters.get("folder_path")
                    or parameters.get("path")
                    or parameters.get("folder")
                    or parameters.get("folder_name")
                    or parameters.get("entity")
                )

                return self.create_folder(
                    folder_path
                )

            if action == "rename_folder":

                source = (
                    parameters.get("folder_path")
                    or parameters.get("folder")
                    or parameters.get("folder_name")
                    or parameters.get("source")
                    or parameters.get("source_path")
                    or parameters.get("entity")
                )

                new_name = (
                    parameters.get("new_name")
                    or parameters.get("newName")
                    or parameters.get("destination_name")
                    or parameters.get("destination")
                )

                return self.rename_folder(
                    source,
                    new_name,
                )

            if action == "copy_folder":

                source = (
                    parameters.get("folder_path")
                    or parameters.get("folder")
                    or parameters.get("folder_name")
                    or parameters.get("source")
                    or parameters.get("source_path")
                    or parameters.get("entity")
                )

                destination = (
                    parameters.get("destination")
                    or parameters.get("destination_folder")
                    or parameters.get("destination_path")
                    or parameters.get("target")
                    or parameters.get("target_folder")
                )

                return self.copy_folder(
                    source,
                    destination,
                )

            if action == "move_folder":

                source = (
                    parameters.get("folder_path")
                    or parameters.get("folder")
                    or parameters.get("folder_name")
                    or parameters.get("source")
                    or parameters.get("source_path")
                    or parameters.get("entity")
                )

                destination = (
                    parameters.get("destination")
                    or parameters.get("destination_folder")
                    or parameters.get("destination_path")
                    or parameters.get("target")
                    or parameters.get("target_folder")
                )

                return self.move_folder(
                    source,
                    destination,
                )

            if action == "delete_folder":

                folder = (
                    parameters.get("folder_path")
                    or parameters.get("path")
                    or parameters.get("folder")
                    or parameters.get("folder_name")
                    or parameters.get("source")
                    or parameters.get("entity")
                )

                return self.delete_folder(
                    folder
                )

            # ==================================================
            # UNSUPPORTED
            # ==================================================

            return self._result(
                False,
                action,
                (
                    "Unsupported filesystem "
                    f"action: {action}"
                ),
            )

        except Exception as error:

            return self._result(
                False,
                action,
                (
                    "Filesystem action "
                    f"failed: {error}"
                ),
            )

    # ==================================================
    # CLOSE
    # ==================================================

    def close(self):
        """
        Release resources owned by the agent.
        """

        try:

            self.file_finder.close()

        except Exception:
            pass

        try:

            self.file_manager.close()

        except Exception:
            pass

        try:

            self.folder_manager.close()

        except Exception:
            pass