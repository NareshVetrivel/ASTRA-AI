from __future__ import annotations

import os
import shutil
from pathlib import Path
from typing import Any, Optional


class FileSystemAgent:
    """
    Central filesystem execution layer for ASTRA-AI.

    IMPORTANT FLOW
    ==============

    First request:
        command
            ->
        candidate search
            ->
        UI selection

    After user selection:
        selected_path / selection_path
            ->
        confirmation
            ->
        confirmed execution

    Once an exact selected path is available, this class MUST NOT
    search for the same file/folder again.
    """

    def __init__(
        self,
        file_finder,
        file_manager,
        folder_manager,
    ):
        self.file_finder = file_finder
        self.file_manager = file_manager
        self.folder_manager = folder_manager

        self.home = Path.home()

    # ==================================================
    # MAIN EXECUTION
    # ==================================================

    def execute(
        self,
        intent: str,
        entities: dict[str, Any] | None = None,
        *,
        selection: Optional[int | str] = None,
        preflight: bool = False,
        **kwargs,
    ) -> dict:
        """
        Execute a filesystem operation.

        If selected_path / selection_path is present, that exact path
        is used directly. Candidate searching is skipped completely.
        """

        intent = self._clean(intent).lower()
        entities = dict(entities or {})

        if selection is not None:
            entities["selection"] = selection

        print("\n========== FILE SYSTEM AGENT ==========")
        print(f"Intent    : {intent}")
        print(f"Preflight : {preflight}")
        print(f"Entities  : {entities}")
        print("=======================================\n")

        selected_path = self._get_selected_path(entities)

        if selected_path:
            print("========== EXACT PATH MODE ==========")
            print(f"Selected Path : {selected_path}")
            print("Candidate search skipped.")
            print("=====================================\n")

        try:
            if intent == "open_file":
                return self.open_file(
                    self._get_source_value(entities),
                    selected_path=selected_path,
                    selection=selection,
                )

            if intent == "open_folder":
                return self.open_folder(
                    self._get_source_value(entities),
                    selected_path=selected_path,
                    selection=selection,
                )

            if intent == "create_file":
                return self.create_file(
                    self._get_target_value(entities),
                )

            if intent == "create_folder":
                return self.create_folder(
                    self._get_target_value(entities),
                )

            if intent == "rename_file":
                return self.rename_file(
                    self._get_source_value(entities),
                    self._get_new_name(entities),
                    selected_path=selected_path,
                    selection=selection,
                )

            if intent == "rename_folder":
                return self.rename_folder(
                    self._get_source_value(entities),
                    self._get_new_name(entities),
                    selected_path=selected_path,
                    selection=selection,
                )

            if intent == "copy_file":
                return self.copy_file(
                    self._get_source_value(entities),
                    self._get_destination(entities),
                    selected_path=selected_path,
                    selection=selection,
                )

            if intent == "copy_folder":
                return self.copy_folder(
                    self._get_source_value(entities),
                    self._get_destination(entities),
                    selected_path=selected_path,
                    selection=selection,
                )

            if intent == "move_file":
                return self.move_file(
                    self._get_source_value(entities),
                    self._get_destination(entities),
                    selected_path=selected_path,
                    selection=selection,
                )

            if intent == "move_folder":
                return self.move_folder(
                    self._get_source_value(entities),
                    self._get_destination(entities),
                    selected_path=selected_path,
                    selection=selection,
                )

            if intent == "delete_file":
                return self.delete_file(
                    self._get_source_value(entities),
                    selected_path=selected_path,
                    selection=selection,
                )

            if intent == "delete_folder":
                return self.delete_folder(
                    self._get_source_value(entities),
                    selected_path=selected_path,
                    selection=selection,
                )

            return self._result(
                False,
                intent or "unknown",
                f"Unsupported filesystem intent: {intent}",
            )

        except Exception as error:

            print(
                f"FileSystemAgent Execution Error : {error}"
            )

            return self._result(
                False,
                intent or "unknown",
                f"Filesystem operation failed: {error}",
            )

    # ==================================================
    # ENTITY HELPERS
    # ==================================================

    def _get_selected_path(
        self,
        entities: dict[str, Any],
    ) -> Optional[str]:
        """
        Return the exact path selected by the user.

        Priority:
            selected_path
            selection_path
            resolved_path
            exact_path

        Only an existing filesystem path is accepted.
        """

        for key in (
            "selected_path",
            "selection_path",
            "resolved_path",
            "exact_path",
        ):
            value = entities.get(key)

            if not isinstance(value, str):
                continue

            value = self._clean(value)

            if not value:
                continue

            try:
                path = Path(value).expanduser()

                if path.exists():
                    return str(path.resolve())

            except (
                OSError,
                ValueError,
                RuntimeError,
            ):
                continue

        return None

    def _get_source_value(
        self,
        entities: dict[str, Any],
    ) -> str:
        """
        Get the original source query.

        The exact selected path is handled separately so that the
        original source name remains available for initial searching.
        """

        for key in (
            "source",
            "source_path",
            "target",
            "path",
            "file_path",
            "folder_path",
            "filename",
            "foldername",
            "file",
            "folder",
            "old_name",
            "entity",
            "name",
        ):
            value = entities.get(key)

            if isinstance(value, str):
                value = self._clean(value)

                if value:
                    return value

        return ""

    def _get_target_value(
        self,
        entities: dict[str, Any],
    ) -> str:

        for key in (
            "target",
            "path",
            "file_path",
            "folder_path",
            "name",
            "entity",
            "filename",
            "foldername",
        ):
            value = entities.get(key)

            if isinstance(value, str):
                value = self._clean(value)

                if value:
                    return value

        return ""

    def _get_destination(
        self,
        entities: dict[str, Any],
    ) -> str:

        for key in (
            "destination",
            "destination_path",
            "to",
        ):
            value = entities.get(key)

            if isinstance(value, str):
                value = self._clean(value)

                if value:
                    return value

        return ""

    def _get_new_name(
        self,
        entities: dict[str, Any],
    ) -> str:

        for key in (
            "new_name",
            "destination_name",
            "rename_to",
            "new_path",
        ):
            value = entities.get(key)

            if isinstance(value, str):
                value = self._clean(value)

                if value:
                    return value

        return ""

    # ==================================================
    # GENERIC HELPERS
    # ==================================================

    @staticmethod
    def _clean(
        value: Any,
    ) -> str:

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
    def _result(
        success: bool,
        action: str,
        message: str,
        **data,
    ) -> dict:

        return {
            "success": bool(success),
            "action": action,
            "message": message,
            **data,
        }

    # ==================================================
    # SPECIAL FOLDER RESOLUTION
    # ==================================================

    def resolve_special_folder(
        self,
        name: str,
    ) -> Optional[str]:

        name = self._clean(name).lower()

        if not name:
            return None

        aliases = {
            "desktop": "desktop",
            "disktop": "desktop",
            "desk top": "desktop",
            "documents": "documents",
            "document": "documents",
            "downloads": "downloads",
            "download": "downloads",
            "donwload": "downloads",
            "donwloads": "downloads",
            "downlod": "downloads",
            "pictures": "pictures",
            "picture": "pictures",
            "photos": "pictures",
            "videos": "videos",
            "video": "videos",
            "music": "music",
        }

        name = aliases.get(
            name,
            name,
        )

        special_folders = getattr(
            self.folder_manager,
            "special_folders",
            {},
        )

        folder = special_folders.get(name)

        if folder is not None:

            if isinstance(folder, str):

                if folder.startswith("shell:"):
                    return folder

                if self._path_exists(folder):
                    return str(Path(folder))

            else:

                try:
                    if folder.exists():
                        return str(folder)

                except (
                    OSError,
                    AttributeError,
                ):
                    pass

        common_folders = {
            "desktop": self.home / "Desktop",
            "documents": self.home / "Documents",
            "downloads": self.home / "Downloads",
            "pictures": self.home / "Pictures",
            "videos": self.home / "Videos",
            "music": self.home / "Music",
        }

        candidate = common_folders.get(name)

        if candidate:

            try:
                if candidate.exists():
                    return str(candidate.resolve())

            except (
                OSError,
                RuntimeError,
            ):
                pass

        one_drive = self.home / "OneDrive"

        one_drive_folders = {
            "desktop": one_drive / "Desktop",
            "documents": one_drive / "Documents",
            "downloads": one_drive / "Downloads",
            "pictures": one_drive / "Pictures",
        }

        candidate = one_drive_folders.get(name)

        if candidate:

            try:
                if candidate.exists():
                    return str(candidate.resolve())

            except (
                OSError,
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
    ) -> Optional[str]:

        filename = self._clean(filename)

        if not filename:
            return None

        direct_path = Path(
            filename
        ).expanduser()

        try:

            if (
                direct_path.exists()
                and direct_path.is_file()
            ):
                return str(
                    direct_path.resolve()
                )

        except (
            OSError,
            RuntimeError,
        ):
            pass

        try:

            path = self.file_finder.find_file(
                filename
            )

            if (
                path
                and self._path_exists(path)
                and Path(path).is_file()
            ):
                return str(
                    Path(path).resolve()
                )

        except Exception as error:

            print(
                f"File Resolution Error : {error}"
            )

        return None

    # ==================================================
    # FOLDER RESOLUTION
    # ==================================================

    def resolve_folder(
        self,
        folder_name: str,
    ) -> Optional[str]:

        folder_name = self._clean(
            folder_name
        )

        if not folder_name:
            return None

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

        special = self.resolve_special_folder(
            folder_name
        )

        if special:
            return special

        common_roots = [
            self.home,
            self.home / "Desktop",
            self.home / "Documents",
            self.home / "Downloads",
            self.home / "Pictures",
            self.home / "Videos",
            self.home / "Music",
            self.home / "OneDrive",
        ]

        target = folder_name.lower()

        for root in common_roots:

            try:

                if not root.exists():
                    continue

                if (
                    root.name.lower()
                    == target
                    and root.is_dir()
                ):
                    return str(
                        root.resolve()
                    )

                for child in root.iterdir():

                    try:

                        if (
                            child.is_dir()
                            and child.name.lower()
                            == target
                        ):
                            return str(
                                child.resolve()
                            )

                    except (
                        PermissionError,
                        OSError,
                    ):
                        continue

            except (
                PermissionError,
                OSError,
            ):
                continue

        return None

    # ==================================================
    # FILE CANDIDATES
    # ==================================================

    def find_file_candidates(
        self,
        filename: str,
    ) -> list[dict]:

        filename = self._clean(filename)

        if not filename:
            return []

        matches: dict[str, Path] = {}

        direct = Path(
            filename
        ).expanduser()

        try:

            if (
                direct.exists()
                and direct.is_file()
            ):
                matches[
                    str(direct.resolve())
                ] = direct.resolve()

        except (
            OSError,
            RuntimeError,
        ):
            pass

        try:

            path = self.file_finder.find_file(
                filename
            )

            if (
                path
                and Path(path).exists()
                and Path(path).is_file()
            ):

                resolved = Path(
                    path
                ).resolve()

                matches[
                    str(resolved)
                ] = resolved

        except Exception:
            pass

        return [
            {
                "index": index,
                "name": path.name,
                "path": str(path),
            }
            for index, path in enumerate(
                sorted(
                    matches.values(),
                    key=lambda item: str(item).lower(),
                ),
                start=1,
            )
        ]

    # ==================================================
    # FOLDER CANDIDATES
    # ==================================================

    def find_folder_candidates(
        self,
        folder_name: str,
        max_candidates: int = 50,
    ) -> list[dict]:

        folder_name = self._clean(
            folder_name
        )

        if not folder_name:
            return []

        normalized = folder_name.lower()

        matches: dict[str, Path] = {}

        direct = Path(
            folder_name
        ).expanduser()

        try:

            if (
                direct.exists()
                and direct.is_dir()
            ):

                resolved = direct.resolve()

                matches[
                    str(resolved)
                ] = resolved

        except (
            OSError,
            RuntimeError,
        ):
            pass

        roots = [
            self.home,
            self.home / "Desktop",
            self.home / "Documents",
            self.home / "Downloads",
            self.home / "Pictures",
            self.home / "Videos",
            self.home / "Music",
            self.home / "OneDrive",
        ]

        for root in roots:

            try:

                if (
                    not root.exists()
                    or not root.is_dir()
                ):
                    continue

                for current_root, dirs, _ in os.walk(
                    root
                ):

                    for directory in list(dirs):

                        if (
                            directory.lower()
                            == normalized
                        ):

                            path = (
                                Path(current_root)
                                / directory
                            )

                            try:

                                resolved = path.resolve()

                                matches[
                                    str(resolved)
                                ] = resolved

                                if (
                                    len(matches)
                                    >= max_candidates
                                ):
                                    break

                            except (
                                OSError,
                                RuntimeError,
                            ):
                                continue

                    if (
                        len(matches)
                        >= max_candidates
                    ):
                        break

            except (
                PermissionError,
                OSError,
            ):
                continue

            if (
                len(matches)
                >= max_candidates
            ):
                break

        return [
            {
                "index": index,
                "name": path.name,
                "path": str(path),
            }
            for index, path in enumerate(
                sorted(
                    matches.values(),
                    key=lambda item: str(item).lower(),
                ),
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
        selected_path: Optional[str] = None,
    ) -> dict:

        if selected_path:

            path = Path(
                selected_path
            ).expanduser()

            try:

                if (
                    path.exists()
                    and path.is_file()
                ):

                    resolved = str(
                        path.resolve()
                    )

                    return self._result(
                        True,
                        "resolve_file",
                        f"Exact file selected: {resolved}",
                        path=resolved,
                        selected_path=resolved,
                        requires_selection=False,
                    )

            except (
                OSError,
                RuntimeError,
            ):
                pass

        candidates = self.find_file_candidates(
            filename
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

        if len(candidates) == 1:

            return self._result(
                True,
                "resolve_file",
                "File resolved successfully.",
                path=candidates[0]["path"],
                selected_index=1,
                candidates=candidates,
                requires_selection=False,
            )

        if selection is None:

            return self._result(
                False,
                "resolve_file",
                (
                    f"Please select the file for "
                    f"'{filename}'."
                ),
                candidates=candidates,
                requires_selection=True,
            )

        try:

            selection = int(selection)

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
            1 <= selection <= len(candidates)
        ):

            return self._result(
                False,
                "resolve_file",
                "Selected file number is out of range.",
                candidates=candidates,
                requires_selection=True,
            )

        selected = candidates[
            selection - 1
        ]

        return self._result(
            True,
            "resolve_file",
            "File selected successfully.",
            path=selected["path"],
            selected_index=selection,
            selected_path=selected["path"],
            candidates=candidates,
            requires_selection=False,
        )

    # ==================================================
    # FOLDER SELECTION
    # ==================================================

    def resolve_folder_selection(
        self,
        folder_name: str,
        selection: Optional[int | str] = None,
        selected_path: Optional[str] = None,
    ) -> dict:

        if selected_path:

            path = Path(
                selected_path
            ).expanduser()

            try:

                if (
                    path.exists()
                    and path.is_dir()
                ):

                    resolved = str(
                        path.resolve()
                    )

                    print(
                        "\n========== EXACT FOLDER SELECTION =========="
                    )

                    print(
                        f"Selected folder : {resolved}"
                    )

                    print(
                        "Candidate search skipped."
                    )

                    print(
                        "============================================\n"
                    )

                    return self._result(
                        True,
                        "resolve_folder",
                        (
                            "Exact folder selected "
                            "successfully."
                        ),
                        path=resolved,
                        selected_path=resolved,
                        requires_selection=False,
                    )

            except (
                OSError,
                RuntimeError,
            ):
                pass

        candidates = self.find_folder_candidates(
            folder_name
        )

        print(
            "\n========== FOLDER SELECTION DEBUG =========="
        )

        print(
            f"Search folder : {folder_name}"
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
            "============================================\n"
        )

        if not candidates:

            return self._result(
                False,
                "resolve_folder",
                f"Folder not found: {folder_name}",
                candidates=[],
                requires_selection=False,
            )

        if len(candidates) == 1:

            return self._result(
                True,
                "resolve_folder",
                "Folder resolved successfully.",
                path=candidates[0]["path"],
                selected_index=1,
                candidates=candidates,
                requires_selection=False,
            )

        if selection is None:

            return self._result(
                False,
                "resolve_folder",
                (
                    f"Please select the folder for "
                    f"'{folder_name}'."
                ),
                candidates=candidates,
                requires_selection=True,
            )

        try:

            selection = int(selection)

        except (
            TypeError,
            ValueError,
        ):

            return self._result(
                False,
                "resolve_folder",
                "Invalid folder selection.",
                candidates=candidates,
                requires_selection=True,
            )

        if not (
            1 <= selection <= len(candidates)
        ):

            return self._result(
                False,
                "resolve_folder",
                "Selected folder number is out of range.",
                candidates=candidates,
                requires_selection=True,
            )

        selected = candidates[
            selection - 1
        ]

        return self._result(
            True,
            "resolve_folder",
            "Folder selected successfully.",
            path=selected["path"],
            selected_index=selection,
            selected_path=selected["path"],
            candidates=candidates,
            requires_selection=False,
        )

    # ==================================================
    # OPEN OPERATIONS
    # ==================================================

    def open_file(
        self,
        filename: str,
        *,
        selected_path: Optional[str] = None,
        selection: Optional[int | str] = None,
    ) -> dict:

        result = self.resolve_file_selection(
            filename,
            selection,
            selected_path,
        )

        if result.get("requires_selection"):
            return result

        path = result.get("path")

        if not path:
            return result

        try:

            os.startfile(path)

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

    def open_folder(
        self,
        folder_name: str,
        *,
        selected_path: Optional[str] = None,
        selection: Optional[int | str] = None,
    ) -> dict:

        result = self.resolve_folder_selection(
            folder_name,
            selection,
            selected_path,
        )

        if result.get("requires_selection"):
            return result

        path = result.get("path")

        if not path:
            return result

        try:

            os.startfile(path)

            return self._result(
                True,
                "open_folder",
                f"Folder opened: {path}",
                path=path,
            )

        except Exception as error:

            return self._result(
                False,
                "open_folder",
                f"Unable to open folder: {error}",
                path=path,
            )

    # ==================================================
    # CREATE OPERATIONS
    # ==================================================

    def create_file(
        self,
        path: str,
    ) -> dict:

        path = self._clean(path)

        if not path:

            return self._result(
                False,
                "create_file",
                "File name is required.",
            )

        try:

            target = Path(
                path
            ).expanduser()

            # ----------------------------------------------
            # Convert relative path to absolute path
            # ----------------------------------------------

            if not target.is_absolute():

                target = (
                    Path.cwd()
                    / target
                )

            target = target.resolve()

            # ----------------------------------------------
            # Prevent conflict with existing item
            # ----------------------------------------------

            if target.exists():

                if target.is_file():

                    return self._result(
                        False,
                        "create_file",
                        (
                            f"Cannot create file '{target.name}'. "
                            "A file with this name already exists."
                        ),
                        path=str(
                            target
                        ),
                        exists=True,
                    )

                if target.is_dir():

                    return self._result(
                        False,
                        "create_file",
                        (
                            f"Cannot create file '{target.name}'. "
                            "A folder with the same name already exists."
                        ),
                        path=str(
                            target
                        ),
                        exists=True,
                    )

                return self._result(
                    False,
                    "create_file",
                    (
                        f"Cannot create file '{target.name}'. "
                        "An item with the same name already exists."
                    ),
                    path=str(
                        target
                    ),
                    exists=True,
                )

            # ----------------------------------------------
            # Ensure parent directory exists
            # ----------------------------------------------

            target.parent.mkdir(
                parents=True,
                exist_ok=True,
            )

            # ----------------------------------------------
            # Create actual file
            # ----------------------------------------------

            target.touch(
                exist_ok=False
            )

            # ----------------------------------------------
            # Verify actual creation
            # ----------------------------------------------

            if not target.exists():

                return self._result(
                    False,
                    "create_file",
                    (
                        f"File creation failed. "
                        f"The file '{target.name}' was not found "
                        "after the operation."
                    ),
                    path=str(
                        target
                    ),
                )

            if not target.is_file():

                return self._result(
                    False,
                    "create_file",
                    (
                        f"File creation failed. "
                        f"'{target.name}' is not a file."
                    ),
                    path=str(
                        target
                    ),
                )

            return self._result(
                True,
                "create_file",
                (
                    f"File created successfully: "
                    f"{target.name}"
                ),
                path=str(
                    target
                ),
            )

        except FileExistsError:

            return self._result(
                False,
                "create_file",
                (
                    f"Cannot create file '{Path(path).name}'. "
                    "An item with this name already exists."
                ),
                path=str(
                    Path(path)
                ),
            )

        except PermissionError:

            return self._result(
                False,
                "create_file",
                (
                    f"Permission denied. "
                    f"Cannot create file '{Path(path).name}'."
                ),
                path=str(
                    Path(path)
                ),
            )

        except Exception as error:

            return self._result(
                False,
                "create_file",
                (
                    f"Unable to create file '{Path(path).name}': "
                    f"{error}"
                ),
                path=str(
                    Path(path)
                ),
            )

    def create_folder(
        self,
        path: str,
    ) -> dict:

        path = self._clean(path)

        if not path:

            return self._result(
                False,
                "create_folder",
                "Folder name is required.",
            )

        try:

            target = Path(
                path
            ).expanduser()

            # ----------------------------------------------
            # Convert relative path to absolute path
            # ----------------------------------------------

            if not target.is_absolute():

                target = (
                    Path.cwd()
                    / target
                )

            target = target.resolve()

            # ----------------------------------------------
            # Prevent duplicate creation
            # ----------------------------------------------

            if target.exists():

                if target.is_dir():

                    return self._result(
                        False,
                        "create_folder",
                        (
                            f"Cannot create folder '{target.name}'. "
                            "A folder with this name already exists."
                        ),
                        path=str(
                            target
                        ),
                        exists=True,
                    )

                if target.is_file():

                    return self._result(
                        False,
                        "create_folder",
                        (
                            f"Cannot create folder '{target.name}'. "
                            "A file with the same name already exists."
                        ),
                        path=str(
                            target
                        ),
                        exists=True,
                    )

                return self._result(
                    False,
                    "create_folder",
                    (
                        f"Cannot create folder '{target.name}'. "
                        "An item with the same name already exists."
                    ),
                    path=str(
                        target
                    ),
                    exists=True,
                )

            # ----------------------------------------------
            # Create actual folder
            # ----------------------------------------------

            target.mkdir(
                parents=True,
                exist_ok=False,
            )

            # ----------------------------------------------
            # Verify actual creation
            # ----------------------------------------------

            if not target.exists():

                return self._result(
                    False,
                    "create_folder",
                    (
                        f"Folder creation failed. "
                        f"The folder '{target.name}' was not found "
                        "after the operation."
                    ),
                    path=str(
                        target
                    ),
                )

            if not target.is_dir():

                return self._result(
                    False,
                    "create_folder",
                    (
                        f"Folder creation failed. "
                        f"'{target.name}' is not a folder."
                    ),
                    path=str(
                        target
                    ),
                )

            return self._result(
                True,
                "create_folder",
                (
                    f"Folder created successfully: "
                    f"{target.name}"
                ),
                path=str(
                    target
                ),
            )

        except FileExistsError:

            return self._result(
                False,
                "create_folder",
                (
                    f"Cannot create folder '{Path(path).name}'. "
                    "An item with this name already exists."
                ),
                path=str(
                    Path(path)
                ),
            )

        except PermissionError:

            return self._result(
                False,
                "create_folder",
                (
                    f"Permission denied. "
                    f"Cannot create folder '{Path(path).name}'."
                ),
                path=str(
                    Path(path)
                ),
            )

        except Exception as error:

            return self._result(
                False,
                "create_folder",
                (
                    f"Unable to create folder '{Path(path).name}': "
                    f"{error}"
                ),
                path=str(
                    Path(path)
                ),
            )

    # ==================================================
    # RENAME OPERATIONS
    # ==================================================

    def rename_file(
        self,
        filename: str,
        new_name: str,
        *,
        selected_path: Optional[str] = None,
        selection: Optional[int | str] = None,
    ) -> dict:

        if not new_name:

            return self._result(
                False,
                "rename_file",
                "New file name is required.",
            )

        result = self.resolve_file_selection(
            filename,
            selection,
            selected_path,
        )

        if result.get("requires_selection"):
            return result

        source = result.get("path")

        if not source:
            return result

        try:

            source_path = Path(source)

            target = (
                source_path.parent
                / new_name
            )

            source_path.rename(target)

            return self._result(
                True,
                "rename_file",
                f"File renamed to: {target.name}",
                path=str(
                    target.resolve()
                ),
                source=str(source_path),
                new_path=str(
                    target.resolve()
                ),
            )

        except Exception as error:

            return self._result(
                False,
                "rename_file",
                f"Rename failed: {error}",
                source=source,
            )

    def rename_folder(
        self,
        folder_name: str,
        new_name: str,
        *,
        selected_path: Optional[str] = None,
        selection: Optional[int | str] = None,
    ) -> dict:

        if not new_name:

            return self._result(
                False,
                "rename_folder",
                "New folder name is required.",
            )

        result = self.resolve_folder_selection(
            folder_name,
            selection,
            selected_path,
        )

        if result.get("requires_selection"):
            return result

        source = result.get("path")

        if not source:
            return result

        try:

            source_path = Path(source)

            target = (
                source_path.parent
                / new_name
            )

            source_path.rename(target)

            return self._result(
                True,
                "rename_folder",
                f"Folder renamed to: {target.name}",
                path=str(
                    target.resolve()
                ),
                source=str(source_path),
                new_path=str(
                    target.resolve()
                ),
            )

        except Exception as error:

            return self._result(
                False,
                "rename_folder",
                f"Rename failed: {error}",
                source=source,
            )

    # ==================================================
    # COPY OPERATIONS
    # ==================================================

    def copy_file(
        self,
        filename: str,
        destination: str,
        *,
        selected_path: Optional[str] = None,
        selection: Optional[int | str] = None,
    ) -> dict:

        result = self.resolve_file_selection(
            filename,
            selection,
            selected_path,
        )

        if result.get("requires_selection"):
            return result

        source = result.get("path")

        destination_path = self.resolve_folder(
            destination
        )

        if not source:
            return result

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

            success = self.file_manager.copy_file(
                source,
                destination_path,
            )

            target = str(
                Path(destination_path)
                / Path(source).name
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
                destination=target,
                path=target,
            )

        except Exception as error:

            return self._result(
                False,
                "copy_file",
                f"Copy failed: {error}",
                source=source,
                destination=destination_path,
            )

    def copy_folder(
        self,
        folder_name: str,
        destination: str,
        *,
        selected_path: Optional[str] = None,
        selection: Optional[int | str] = None,
    ) -> dict:

        result = self.resolve_folder_selection(
            folder_name,
            selection,
            selected_path,
        )

        if result.get("requires_selection"):
            return result

        source = result.get("path")

        destination_path = self.resolve_folder(
            destination
        )

        if not source:
            return result

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

            success = self._copy_folder(
                source,
                destination_path,
            )

            target = str(
                Path(destination_path)
                / Path(source).name
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
                destination=target,
                path=target,
            )

        except Exception as error:

            return self._result(
                False,
                "copy_folder",
                f"Copy failed: {error}",
                source=source,
                destination=destination_path,
            )

    # ==================================================
    # MOVE OPERATIONS
    # ==================================================

    def move_file(
        self,
        filename: str,
        destination: str,
        *,
        selected_path: Optional[str] = None,
        selection: Optional[int | str] = None,
    ) -> dict:

        result = self.resolve_file_selection(
            filename,
            selection,
            selected_path,
        )

        if result.get("requires_selection"):
            return result

        source = result.get("path")

        destination_path = self.resolve_folder(
            destination
        )

        if not source:
            return result

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

            success = self.file_manager.move_file(
                source,
                destination_path,
            )

            target = str(
                Path(destination_path)
                / Path(source).name
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
                destination=target,
                path=target,
            )

        except Exception as error:

            return self._result(
                False,
                "move_file",
                f"Move failed: {error}",
                source=source,
                destination=destination_path,
            )

    def move_folder(
        self,
        folder_name: str,
        destination: str,
        *,
        selected_path: Optional[str] = None,
        selection: Optional[int | str] = None,
    ) -> dict:

        result = self.resolve_folder_selection(
            folder_name,
            selection,
            selected_path,
        )

        if result.get("requires_selection"):
            return result

        source = result.get("path")

        destination_path = self.resolve_folder(
            destination
        )

        if not source:
            return result

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

            success = self._move_folder(
                source,
                destination_path,
            )

            target = str(
                Path(destination_path)
                / Path(source).name
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
                destination=target,
                path=target,
            )

        except Exception as error:

            return self._result(
                False,
                "move_folder",
                f"Move failed: {error}",
                source=source,
                destination=destination_path,
            )

    # ==================================================
    # DELETE OPERATIONS
    # ==================================================

    def delete_file(
        self,
        filename: str,
        *,
        selected_path: Optional[str] = None,
        selection: Optional[int | str] = None,
    ) -> dict:

        result = self.resolve_file_selection(
            filename,
            selection,
            selected_path,
        )

        if result.get("requires_selection"):
            return result

        path = result.get("path")

        if not path:
            return result

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
                selected_index=result.get(
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

    def delete_folder(
        self,
        folder_name: str,
        *,
        selected_path: Optional[str] = None,
        selection: Optional[int | str] = None,
    ) -> dict:

        result = self.resolve_folder_selection(
            folder_name,
            selection,
            selected_path,
        )

        if result.get("requires_selection"):
            return result

        path = result.get("path")

        if not path:
            return result

        try:

            success = self._delete_folder(
                path
            )

            return self._result(
                success,
                "delete_folder",
                (
                    f"Folder deleted: {path}"
                    if success
                    else f"Unable to delete folder: {path}"
                ),
                path=path,
                selected_index=result.get(
                    "selected_index"
                ),
            )

        except Exception as error:

            return self._result(
                False,
                "delete_folder",
                f"Delete failed: {error}",
                path=path,
            )

    # ==================================================
    # FOLDER EXECUTION HELPERS
    # ==================================================

    def _copy_folder(
        self,
        source: str,
        destination: str,
    ) -> bool:

        source_path = Path(source)
        destination_path = Path(destination)

        if not (
            source_path.exists()
            and source_path.is_dir()
        ):
            return False

        target = (
            destination_path
            / source_path.name
        )

        if target.exists():
            return False

        if hasattr(
            self.folder_manager,
            "copy_folder",
        ):

            try:

                result = self.folder_manager.copy_folder(
                    source,
                    destination,
                )

                return bool(result)

            except Exception as error:

                print(
                    f"FolderManager Copy Error : {error}"
                )

        shutil.copytree(
            source_path,
            target,
        )

        return target.exists()

    def _move_folder(
        self,
        source: str,
        destination: str,
    ) -> bool:

        source_path = Path(source)
        destination_path = Path(destination)

        if not (
            source_path.exists()
            and source_path.is_dir()
        ):
            return False

        target = (
            destination_path
            / source_path.name
        )

        if target.exists():
            return False

        if hasattr(
            self.folder_manager,
            "move_folder",
        ):

            try:

                result = self.folder_manager.move_folder(
                    source,
                    destination,
                )

                return bool(result)

            except Exception as error:

                print(
                    f"FolderManager Move Error : {error}"
                )

        shutil.move(
            str(source_path),
            str(destination_path),
        )

        return target.exists()

    def _delete_folder(
        self,
        path: str,
    ) -> bool:

        target = Path(path)

        if not (
            target.exists()
            and target.is_dir()
        ):
            return False

        if hasattr(
            self.folder_manager,
            "delete_folder",
        ):

            try:

                result = self.folder_manager.delete_folder(
                    path
                )

                return bool(result)

            except Exception as error:

                print(
                    f"FolderManager Delete Error : {error}"
                )

        shutil.rmtree(target)

        return not target.exists()