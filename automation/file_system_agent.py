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
    Orchestrate file and folder operations.

    The agent is responsible for:

        1. Resolving files and folders.
        2. Validating targets.
        3. Calling existing automation modules.
        4. Returning a consistent result structure.

    Existing FileManager, FolderManager and FileFinder
    implementations remain responsible for the actual
    filesystem operations.
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
    # Result Helper
    # ==================================================

    @staticmethod
    def _result(
        success: bool,
        action: str,
        message: str,
        **extra: Any,
    ) -> dict:
        """
        Build a consistent agent response.
        """

        result = {
            "success": success,
            "action": action,
            "message": message,
        }

        result.update(extra)

        return result

    # ==================================================
    # Path Helpers
    # ==================================================

    @staticmethod
    def _clean(value: Optional[str]) -> str:
        """
        Normalize a user-provided value.
        """

        if value is None:
            return ""

        return str(value).strip().strip('"').strip("'")

    @staticmethod
    def _path_exists(path: Optional[str | Path]) -> bool:
        """
        Check whether a path exists.
        """

        if not path:
            return False

        try:
            return Path(path).exists()

        except (OSError, ValueError):
            return False

    # ==================================================
    # Special Folder Resolution
    # ==================================================

    def resolve_special_folder(
        self,
        name: str,
    ) -> Optional[str]:
        """
        Resolve a known Windows special folder.

        Examples:

            Desktop
            Documents
            Downloads
            Pictures
            Videos
            Music
            C drive
            D drive
            E drive
            This PC
            Recycle Bin
        """

        name = self._clean(name).lower()

        if not name:
            return None

        special_folders = getattr(
            self.folder_manager,
            "special_folders",
            {},
        )

        folder = special_folders.get(name)

        if folder is None:
            return None

        # Windows shell location.
        if isinstance(folder, str):
            if folder.startswith("shell:"):
                return folder

            if self._path_exists(folder):
                return str(Path(folder))

            return None

        try:
            if folder.exists():
                return str(folder)

        except (OSError, AttributeError):
            pass

        return None

    # ==================================================
    # File Resolution
    # ==================================================

    def resolve_file(
        self,
        filename: str,
        selection: Optional[int | str] = None,
    ) -> Optional[str]:
        r"""
        Resolve a file.

        If multiple files match and no selection is supplied,
        do not silently choose one. The caller must inspect
        find_file_candidates() / resolve_file_selection().
        """

        result = self.resolve_file_selection(
            filename,
            selection,
        )

        if result.get("success"):
            return result.get("path")

        if result.get("requires_selection"):
            print(
                "\nMultiple files found:\n"
            )

            for candidate in result.get("candidates", []):
                print(
                    f"{candidate['index']}. "
                    f"{candidate['name']}"
                )
                print(
                    f"   {candidate['path']}"
                )

            return None

        print(
            f"File Resolution Failed : {filename}"
        )

        return None

    # ==================================================
    # Multiple File Candidate Resolution
    # ==================================================

    def find_file_candidates(
        self,
        filename: str,
    ) -> list[dict]:
        """
        Find matching files without allowing an unrestricted filesystem
        walk to block ASTRA for several minutes.

        Search order:
            1. User folders
            2. OneDrive user folders
            3. E: drive

        Exact matches are preferred over partial matches.

        The scan is bounded by:
            - maximum candidates
            - maximum files inspected
            - maximum scan time

        This keeps voice/UI interaction responsive while still checking
        the most relevant locations first.
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

        unique_locations: list[Path] = []
        seen_locations: set[str] = set()

        for location in locations:
            try:
                resolved = location.resolve()
                key = str(resolved).lower()

                if key in seen_locations:
                    continue

                if not resolved.exists() or not resolved.is_dir():
                    continue

                seen_locations.add(key)
                unique_locations.append(resolved)

            except (OSError, RuntimeError):
                continue

        exact: dict[str, Path] = {}
        partial: dict[str, Path] = {}

        # --------------------------------------------------
        # Safety limits
        # --------------------------------------------------
        # These prevent commands such as "copy demo" from walking
        # an entire large drive indefinitely.
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

            if timed_out or len(exact) >= max_candidates:
                break

            try:
                for root, dirs, files in os.walk(
                    location,
                    topdown=True,
                ):

                    # Keep the walk away from known huge/system folders.
                    dirs[:] = [
                        directory
                        for directory in dirs
                        if directory.lower() not in excluded_directories
                    ]

                    for file_name in files:

                        files_scanned += 1

                        if (
                            files_scanned >= max_files_scanned
                            or (
                                time.monotonic() - started_at
                                >= max_scan_seconds
                            )
                        ):
                            timed_out = True
                            break

                        try:
                            path = (
                                Path(root) / file_name
                            ).resolve()

                            actual_name = path.name.lower()
                            actual_stem = path.stem.lower()

                            if (
                                search_name == actual_name
                                or search_name == actual_stem
                            ):
                                exact[str(path).lower()] = path

                            elif (
                                search_name in actual_name
                                or search_name in actual_stem
                            ):
                                partial[str(path).lower()] = path

                            if len(exact) >= max_candidates:
                                break

                        except (
                            PermissionError,
                            FileNotFoundError,
                            OSError,
                            RuntimeError,
                        ):
                            continue

                    if timed_out or len(exact) >= max_candidates:
                        break

            except (
                PermissionError,
                FileNotFoundError,
                OSError,
                RuntimeError,
            ):
                continue

        # Exact matches always win.
        matches = list(exact.values())

        # Only use partial matches when there are no exact matches.
        if not matches:
            matches = list(partial.values())

        matches = matches[:max_candidates]

        # --------------------------------------------------
        # FileFinder/database fallback
        # --------------------------------------------------
        # If the bounded filesystem search found nothing, use the
        # existing indexed finder instead of silently failing.
        if not matches:
            try:
                path = self.file_finder.find_file(filename)

                if path:
                    candidate = Path(path).resolve()

                    if candidate.exists() and candidate.is_file():
                        matches.append(candidate)

            except Exception:
                pass

        matches.sort(
            key=lambda item: str(item).lower()
        )

        return [
            {
                "index": index,
                "name": path.name,
                "path": str(path),
            }
            for index, path in enumerate(
                matches,
                start=1,
            )
        ]

    def resolve_file_selection(

        self,
        filename: str,
        selection: Optional[int | str] = None,
    ) -> dict:
        """
        Resolve a file with explicit multiple-match handling.

        One match:
            returns selected path.

        Multiple matches without a selection:
            returns requires_selection=True and all candidates.

        A supplied numeric selection:
            returns the exact selected path.
        """

        candidates = self.find_file_candidates(filename)

        print("\n========== FILE SELECTION DEBUG ==========")
        print(f"Search filename : {filename}")
        print(f"Candidates found: {len(candidates)}")

        for candidate in candidates:
            print(
                f"{candidate.get('index')}. "
                f"{candidate.get('name')} -> "
                f"{candidate.get('path')}"
            )

        print("==========================================\n")

        if not candidates:
            return self._result(
                False,
                "resolve_file",
                f"File not found: {filename}",
                candidates=[],
                requires_selection=False,
            )

        if len(candidates) == 1:
            return self._result(
                True,
                "resolve_file",
                f"File resolved: {candidates[0]['path']}",
                path=candidates[0]["path"],
                candidates=candidates,
                requires_selection=False,
            )

        if selection is None:
            return self._result(
                False,
                "resolve_file",
                (
                    f"Multiple files found for '{filename}'. "
                    "Please select one."
                ),
                candidates=candidates,
                requires_selection=True,
            )

        try:
            selected_index = int(
                str(selection).strip()
            )

        except (TypeError, ValueError):
            return self._result(
                False,
                "resolve_file",
                "Invalid file selection.",
                candidates=candidates,
                requires_selection=True,
            )

        if not 1 <= selected_index <= len(candidates):
            return self._result(
                False,
                "resolve_file",
                (
                    f"Invalid selection. Choose a number "
                    f"between 1 and {len(candidates)}."
                ),
                candidates=candidates,
                requires_selection=True,
            )

        selected = candidates[selected_index - 1]

        return self._result(
            True,
            "resolve_file",
            f"File selected: {selected['path']}",
            path=selected["path"],
            candidates=candidates,
            selected_index=selected_index,
            requires_selection=False,
        )

    # ==================================================
    # Folder Resolution
    # ==================================================

    def resolve_folder(
        self,
        folder_name: str,
    ) -> Optional[str]:
        """
        Resolve a folder using:

            1. Direct path
            2. Special folder mapping
            3. Home directory lookup
            4. Common user folders
        """

        folder_name = self._clean(folder_name)

        if not folder_name:
            return None

        # ----------------------------------------------
        # Direct path
        # ----------------------------------------------

        direct_path = Path(folder_name).expanduser()

        try:
            if direct_path.exists() and direct_path.is_dir():
                return str(direct_path.resolve())

        except (OSError, RuntimeError):
            pass

        # ----------------------------------------------
        # Special folders
        # ----------------------------------------------

        special = self.resolve_special_folder(
            folder_name
        )

        if special:
            return special

        # ----------------------------------------------
        # Common folders
        # ----------------------------------------------

        common_folders = {
            "desktop": self.home / "Desktop",
            "documents": self.home / "Documents",
            "downloads": self.home / "Downloads",
            "pictures": self.home / "Pictures",
            "videos": self.home / "Videos",
            "music": self.home / "Music",
        }

        normalized = folder_name.lower()

        if normalized in common_folders:
            path = common_folders[normalized]

            if path.exists():
                return str(path.resolve())

        # ----------------------------------------------
        # Search direct children of home
        # ----------------------------------------------

        try:
            for child in self.home.iterdir():

                if not child.is_dir():
                    continue

                if child.name.lower() == normalized:
                    return str(child.resolve())

        except (OSError, PermissionError):
            pass

        return None

    # ==================================================
    # Generic Target Resolution
    # ==================================================

    def resolve_target(
        self,
        target: str,
        target_type: str = "auto",
    ) -> Optional[str]:
        """
        Resolve either a file or folder.

        target_type:

            file
            folder
            auto
        """

        target = self._clean(target)
        target_type = self._clean(target_type).lower()

        if not target:
            return None

        if target_type == "file":
            return self.resolve_file(target)

        if target_type == "folder":
            return self.resolve_folder(target)

        # ----------------------------------------------
        # Auto detection
        # ----------------------------------------------

        direct_path = Path(target).expanduser()

        try:
            if direct_path.exists():
                return str(direct_path.resolve())

        except (OSError, RuntimeError):
            pass

        # Try file first.
        file_path = self.resolve_file(target)

        if file_path:
            return file_path

        # Then folder.
        return self.resolve_folder(target)

    # ==================================================
    # File Operations
    # ==================================================

    def open_file(
        self,
        filename: str,
        selection: Optional[int | str] = None,
    ) -> dict:
        """
        Find and open a file.
        """

        path_result = self.resolve_file_selection(
            filename,
            selection,
        )

        if path_result.get("requires_selection"):
            return path_result

        path = path_result.get("path")

        if not path:
            return self._result(
                False,
                "open_file",
                f"File not found: {filename}",
                candidates=path_result.get("candidates", []),
            )

        try:
            success = self.file_manager.open_file(path)

            if success:
                return self._result(
                    True,
                    "open_file",
                    f"File opened: {path}",
                    path=path,
                )

        except Exception as error:
            return self._result(
                False,
                "open_file",
                f"Unable to open file: {error}",
                path=path,
            )

        return self._result(
            False,
            "open_file",
            f"Unable to open file: {path}",
            path=path,
        )

    def create_file(
        self,
        file_path: str,
        content: str = "",
    ) -> dict:
        """
        Create a file.

        Delegates the actual operation to FileManager.
        """

        file_path = self._clean(file_path)

        if not file_path:
            return self._result(
                False,
                "create_file",
                "File path is required.",
            )

        try:
            success = self.file_manager.create_file(
                file_path,
                content,
            )

            if success:
                return self._result(
                    True,
                    "create_file",
                    f"File created: {file_path}",
                    path=file_path,
                )

        except Exception as error:
            return self._result(
                False,
                "create_file",
                f"Unable to create file: {error}",
                path=file_path,
            )

        return self._result(
            False,
            "create_file",
            f"Unable to create file: {file_path}",
            path=file_path,
        )

    def rename_file(
        self,
        filename: str,
        new_name: str,
        selection: Optional[int | str] = None,
    ) -> dict:
        """
        Rename an existing file.
        """

        filename = self._clean(filename)
        new_name = self._clean(new_name)

        if not filename or not new_name:
            return self._result(
                False,
                "rename_file",
                "Source file and new name are required.",
            )

        path_result = self.resolve_file_selection(
            filename,
            selection,
        )

        if path_result.get("requires_selection"):
            return path_result

        path = path_result.get("path")

        if not path:
            return self._result(
                False,
                "rename_file",
                f"File not found: {filename}",
                candidates=path_result.get("candidates", []),
            )

        try:
            success = self.file_manager.rename_file(
                path,
                new_name,
            )

            return self._result(
                success,
                "rename_file",
                (
                    f"File renamed: {new_name}"
                    if success
                    else f"Unable to rename file: {path}"
                ),
                path=path,
                new_name=new_name,
                selected_index=path_result.get("selected_index"),
            )

        except Exception as error:
            return self._result(
                False,
                "rename_file",
                f"Rename failed: {error}",
                path=path,
                new_name=new_name,
            )

    def copy_file(
        self,
        filename: str,
        destination: str,
        selection: Optional[int | str] = None,
    ) -> dict:
        """
        Copy a file to a destination folder.
        """

        filename = self._clean(filename)
        destination = self._clean(destination)

        if not filename or not destination:
            return self._result(
                False,
                "copy_file",
                "Source file and destination are required.",
            )

        source_result = self.resolve_file_selection(
            filename,
            selection,
        )

        if source_result.get("requires_selection"):
            return source_result

        source = source_result.get("path")

        if not source:
            return self._result(
                False,
                "copy_file",
                f"File not found: {filename}",
                candidates=source_result.get("candidates", []),
            )

        destination_path = self.resolve_folder(
            destination
        )

        if not destination_path:
            return self._result(
                False,
                "copy_file",
                f"Destination folder not found: {destination}",
            )

        try:
            success = self.file_manager.copy_file(
                source,
                destination_path,
            )

            return self._result(
                success,
                "copy_file",
                (
                    "File copied successfully."
                    if success
                    else "Unable to copy file."
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

    def move_file(
        self,
        filename: str,
        destination: str,
        selection: Optional[int | str] = None,
    ) -> dict:
        """
        Move a file to a destination folder.
        """

        filename = self._clean(filename)
        destination = self._clean(destination)

        if not filename or not destination:
            return self._result(
                False,
                "move_file",
                "Source file and destination are required.",
            )

        source_result = self.resolve_file_selection(
            filename,
            selection,
        )

        if source_result.get("requires_selection"):
            return source_result

        source = source_result.get("path")

        if not source:
            return self._result(
                False,
                "move_file",
                f"File not found: {filename}",
                candidates=source_result.get("candidates", []),
            )

        destination_path = self.resolve_folder(
            destination
        )

        if not destination_path:
            return self._result(
                False,
                "move_file",
                f"Destination folder not found: {destination}",
            )

        try:
            success = self.file_manager.move_file(
                source,
                destination_path,
            )

            return self._result(
                success,
                "move_file",
                (
                    "File moved successfully."
                    if success
                    else "Unable to move file."
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

    def delete_file(
        self,
        filename: str,
        selection: Optional[int | str] = None,
    ) -> dict:
        """
        Delete an existing file.
        """

        filename = self._clean(filename)

        if not filename:
            return self._result(
                False,
                "delete_file",
                "File name is required.",
            )

        path_result = self.resolve_file_selection(
            filename,
            selection,
        )

        if path_result.get("requires_selection"):
            return path_result

        path = path_result.get("path")

        if not path:
            return self._result(
                False,
                "delete_file",
                f"File not found: {filename}",
                candidates=path_result.get("candidates", []),
            )

        try:
            success = self.file_manager.delete_file(
                path
            )

            return self._result(
                success,
                "delete_file",
                (
                    f"File deleted: {path}"
                    if success
                    else f"Unable to delete file: {path}"
                ),
                path=path,
                selected_index=path_result.get("selected_index"),
            )

        except Exception as error:
            return self._result(
                False,
                "delete_file",
                f"Delete failed: {error}",
                path=path,
            )

    # ==================================================
    # Folder Operations
    # ==================================================

    def open_folder(
        self,
        folder_name: str,
    ) -> dict:
        """
        Open a folder.
        """

        folder = self.resolve_folder(
            folder_name
        )

        # Special shell folder.
        if folder and folder.startswith("shell:"):
            try:
                success = self.folder_manager.open_folder(
                    folder_name
                )

                return self._result(
                    success,
                    "open_folder",
                    (
                        f"Folder opened: {folder_name}"
                        if success
                        else f"Unable to open folder: {folder_name}"
                    ),
                    folder=folder_name,
                )

            except Exception as error:
                return self._result(
                    False,
                    "open_folder",
                    f"Open folder failed: {error}",
                )

        if not folder:
            return self._result(
                False,
                "open_folder",
                f"Folder not found: {folder_name}",
            )

        try:
            success = self.folder_manager.open_folder(
                Path(folder).name
            )

            return self._result(
                success,
                "open_folder",
                (
                    f"Folder opened: {folder}"
                    if success
                    else f"Unable to open folder: {folder}"
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

    def create_folder(
        self,
        folder_path: str,
    ) -> dict:
        """
        Create a folder.
        """

        folder_path = self._clean(folder_path)

        if not folder_path:
            return self._result(
                False,
                "create_folder",
                "Folder path is required.",
            )

        try:
            success = self.folder_manager.create_folder(
                folder_path
            )

            return self._result(
                success,
                "create_folder",
                (
                    f"Folder created: {folder_path}"
                    if success
                    else f"Unable to create folder: {folder_path}"
                ),
                path=folder_path,
            )

        except Exception as error:
            return self._result(
                False,
                "create_folder",
                f"Create folder failed: {error}",
                path=folder_path,
            )

    def rename_folder(
        self,
        folder_name: str,
        new_name: str,
    ) -> dict:
        """
        Rename an existing folder.
        """

        folder_name = self._clean(folder_name)
        new_name = self._clean(new_name)

        if not folder_name or not new_name:
            return self._result(
                False,
                "rename_folder",
                "Source folder and new name are required.",
            )

        source = self.resolve_folder(
            folder_name
        )

        if not source or source.startswith("shell:"):
            return self._result(
                False,
                "rename_folder",
                f"Folder not found: {folder_name}",
            )

        try:
            success = self.folder_manager.rename_folder(
                source,
                new_name,
            )

            return self._result(
                success,
                "rename_folder",
                (
                    f"Folder renamed to: {new_name}"
                    if success
                    else f"Unable to rename folder: {source}"
                ),
                source=source,
                new_name=new_name,
            )

        except Exception as error:
            return self._result(
                False,
                "rename_folder",
                f"Rename folder failed: {error}",
                source=source,
                new_name=new_name,
            )

    def copy_folder(
        self,
        folder_name: str,
        destination: str,
    ) -> dict:
        """
        Copy a folder to a destination.
        """

        folder_name = self._clean(folder_name)
        destination = self._clean(destination)

        if not folder_name or not destination:
            return self._result(
                False,
                "copy_folder",
                "Source folder and destination are required.",
            )

        source = self.resolve_folder(
            folder_name
        )

        if not source or source.startswith("shell:"):
            return self._result(
                False,
                "copy_folder",
                f"Folder not found: {folder_name}",
            )

        destination_path = self.resolve_folder(
            destination
        )

        if not destination_path:
            return self._result(
                False,
                "copy_folder",
                f"Destination folder not found: {destination}",
            )

        try:
            success = self.folder_manager.copy_folder(
                source,
                destination_path,
            )

            return self._result(
                success,
                "copy_folder",
                (
                    "Folder copied successfully."
                    if success
                    else "Unable to copy folder."
                ),
                source=source,
                destination=destination_path,
            )

        except Exception as error:
            return self._result(
                False,
                "copy_folder",
                f"Copy folder failed: {error}",
                source=source,
                destination=destination_path,
            )

    def move_folder(
        self,
        folder_name: str,
        destination: str,
    ) -> dict:
        """
        Move a folder to a destination.
        """

        folder_name = self._clean(folder_name)
        destination = self._clean(destination)

        if not folder_name or not destination:
            return self._result(
                False,
                "move_folder",
                "Source folder and destination are required.",
            )

        source = self.resolve_folder(
            folder_name
        )

        if not source or source.startswith("shell:"):
            return self._result(
                False,
                "move_folder",
                f"Folder not found: {folder_name}",
            )

        destination_path = self.resolve_folder(
            destination
        )

        if not destination_path:
            return self._result(
                False,
                "move_folder",
                f"Destination folder not found: {destination}",
            )

        try:
            success = self.folder_manager.move_folder(
                source,
                destination_path,
            )

            return self._result(
                success,
                "move_folder",
                (
                    "Folder moved successfully."
                    if success
                    else "Unable to move folder."
                ),
                source=source,
                destination=destination_path,
            )

        except Exception as error:
            return self._result(
                False,
                "move_folder",
                f"Move folder failed: {error}",
                source=source,
                destination=destination_path,
            )

    def delete_folder(
        self,
        folder_name: str,
    ) -> dict:
        """
        Delete an existing folder.
        """

        folder_name = self._clean(folder_name)

        if not folder_name:
            return self._result(
                False,
                "delete_folder",
                "Folder name is required.",
            )

        source = self.resolve_folder(
            folder_name
        )

        if not source or source.startswith("shell:"):
            return self._result(
                False,
                "delete_folder",
                f"Folder not found: {folder_name}",
            )

        try:
            success = self.folder_manager.delete_folder(
                source
            )

            return self._result(
                success,
                "delete_folder",
                (
                    f"Folder deleted: {source}"
                    if success
                    else f"Unable to delete folder: {source}"
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
    # Generic Action Executor
    # ==================================================

    def execute(
        self,
        action: str,
        parameters: Optional[dict] = None,
    ) -> dict:
        """
        Execute a filesystem action.

        This provides one stable entry point for
        CommandDispatcher and MultiCommandExecutor.

        Supports multiple parameter aliases so that
        planner,
        dispatcher,
        tests,
        and direct API calls can use
        different parameter names.
        """

        action = self._clean(action).lower()
        parameters = parameters or {}

        try:

            # Optional explicit candidate selection. This is used
            # when a filename exists in more than one location.
            selection = parameters.get("selection")

            if selection is None:
                selection = parameters.get("selected_index")

            if selection is None:
                selection = parameters.get("file_selection")

            # --------------------------------------------------
            # FILE OPERATIONS
            # --------------------------------------------------

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

            # --------------------------------------------------

            if action == "create_file":

                file_path = (
                    parameters.get("file_path")
                    or parameters.get("path")
                    or parameters.get("filename")
                    or parameters.get("file")
                    or parameters.get("entity")
                )

                content = parameters.get(
                    "content",
                    ""
                )

                return self.create_file(
                    file_path,
                    content,
                )

            # --------------------------------------------------

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

            # --------------------------------------------------

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

            # --------------------------------------------------

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

            # --------------------------------------------------

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

            # --------------------------------------------------
            # ZIP OPERATIONS
            # --------------------------------------------------

            if action in ("compress_file", "compress_zip"):

                filename = (
                    parameters.get("filename")
                    or parameters.get("file")
                    or parameters.get("file_path")
                    or parameters.get("source")
                    or parameters.get("entity")
                )

                source_result = self.resolve_file_selection(
                    filename,
                    selection,
                )

                if source_result.get("requires_selection"):
                    return source_result

                source = source_result.get("path")

                if not source:
                    return source_result

                success = self.file_manager.compress_file(
                    source
                )

                return self._result(
                    success,
                    action,
                    (
                        "ZIP archive created successfully."
                        if success
                        else "Unable to create ZIP archive."
                    ),
                    path=source,
                )

            # --------------------------------------------------

            if action in ("extract_zip", "unzip"):

                filename = (
                    parameters.get("filename")
                    or parameters.get("file")
                    or parameters.get("zip_file")
                    or parameters.get("source")
                    or parameters.get("entity")
                )

                source_result = self.resolve_file_selection(
                    filename,
                    selection,
                )

                if source_result.get("requires_selection"):
                    return source_result

                source = source_result.get("path")

                if not source:
                    return source_result

                success = self.file_manager.extract_zip(
                    source
                )

                return self._result(
                    success,
                    action,
                    (
                        "ZIP archive extracted successfully."
                        if success
                        else "Unable to extract ZIP archive."
                    ),
                    path=source,
                    selected_index=source_result.get("selected_index"),
                )

            # --------------------------------------------------
            # FOLDER OPERATIONS
            # --------------------------------------------------

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

            # --------------------------------------------------

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

            # --------------------------------------------------

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
                    or parameters.get("destination")
                    or parameters.get("destination_name")
                )

                return self.rename_folder(
                    source,
                    new_name,
                )

            # --------------------------------------------------

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

            # --------------------------------------------------

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

            # --------------------------------------------------

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

            # --------------------------------------------------
            # UNSUPPORTED ACTION
            # --------------------------------------------------

            return self._result(
                False,
                action,
                f"Unsupported filesystem action: {action}",
            )

        except Exception as error:

            return self._result(
                False,
                action,
                f"Filesystem action failed: {error}",
            )

    # ==================================================
    # Close
    # ==================================================

    def close(self):
        """
        Close resources owned by the agent.
        """

        try:
            self.file_finder.close()

        except Exception:
            pass

        try:
            self.file_manager.close()

        except Exception:
            pass