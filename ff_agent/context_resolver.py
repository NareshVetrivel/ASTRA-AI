from __future__ import annotations

from typing import Any

from ff_agent.models import AgentContext, ResolutionResult


class ContextResolver:
    """
    Resolves and validates file/folder context before execution.

    This class does not perform filesystem operations directly.
    Existing ASTRA automation components remain responsible for
    searching and executing operations.
    """

    MOVE_INTENTS = {
        "move_file",
        "move_folder",
        "copy_file",
        "copy_folder",
    }

    CREATE_INTENTS = {
        "create_file",
        "create_folder",
    }

    RENAME_INTENTS = {
        "rename_file",
        "rename_folder",
    }

    DELETE_INTENTS = {
        "delete_file",
        "delete_folder",
    }

    SEARCH_INTENTS = {
        "search_file",
        "search_folder",
    }

    OPEN_INTENTS = {
        "open_file",
        "open_folder",
    }

    SOURCE_KEYS = (
        "source",
        "source_path",
        "from",
        "foldername",
        "folder_name",
        "filename",
        "file_name",
        "file",
        "folder",
        "old_name",
        "target",
        "entity",
        "name",
    )

    DESTINATION_KEYS = (
        "destination",
        "destination_path",
        "to",
    )

    TARGET_KEYS = (
        "target",
        "path",
        "file_path",
        "folder_path",
        "name",
        "entity",
        "foldername",
        "folder_name",
        "filename",
        "file_name",
        "file",
        "folder",
        "old_name",
        "source",
        "source_path",
    )

    NEW_NAME_KEYS = (
        "new_name",
        "new_path",
        "rename_to",
        "destination_name",
    )

    def resolve(
        self,
        command: str,
        intent: str,
        entities: dict[str, Any] | None = None,
    ) -> ResolutionResult:
        """
        Convert planner entities into a normalized AgentContext.
        """

        normalized_entities = self._normalize_entities(
            entities or {}
        )

        source = self._get_first(
            normalized_entities,
            *self.SOURCE_KEYS,
        )

        destination = self._get_first(
            normalized_entities,
            *self.DESTINATION_KEYS,
        )

        target = self._get_first(
            normalized_entities,
            *self.TARGET_KEYS,
        )

        context = AgentContext(
            command=command,
            intent=intent,
            entities=normalized_entities,
            source=source,
            destination=destination,
            target=target,
        )

        self._apply_context_aliases(context)

        missing_fields = self._find_missing_fields(
            context
        )

        if missing_fields:
            return ResolutionResult(
                success=False,
                context=context,
                message=self._build_missing_message(
                    intent,
                    missing_fields,
                ),
                needs_clarification=True,
                clarification_type="missing_information",
                missing_fields=missing_fields,
            )

        candidates = self._extract_candidates(
            normalized_entities
        )

        if len(candidates) > 1:
            return ResolutionResult(
                success=False,
                context=context,
                message=(
                    "I found multiple possible files or folders. "
                    "Please select the correct one."
                ),
                needs_clarification=True,
                clarification_type="ambiguous_target",
                candidates=candidates,
            )

        return ResolutionResult(
            success=True,
            context=context,
            message=(
                "File and folder context resolved successfully."
            ),
            candidates=candidates,
        )

    def _normalize_entities(
        self,
        entities: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Normalize entity keys without destroying original information.
        """

        normalized: dict[str, Any] = {}

        for key, value in entities.items():
            normalized_key = (
                str(key)
                .strip()
                .lower()
                .replace(" ", "_")
            )

            if isinstance(value, str):
                normalized[normalized_key] = (
                    value.strip()
                )
            else:
                normalized[normalized_key] = value

        entity = normalized.get("entity")

        if isinstance(entity, str):
            normalized["entity"] = (
                self._clean_entity_value(entity)
            )

        return normalized

    def _apply_context_aliases(
        self,
        context: AgentContext,
    ) -> None:
        """
        Apply compatibility aliases between the existing entity
        extraction pipeline and the File & Folder Agent.

        The existing ASTRA entity extractor can return keys such as:

            foldername
            filename
            folder
            file
            old_name
            destination_name

        The agent internally works with:

            source
            destination
            target
            new_name

        This method preserves the original entities while ensuring
        the normalized context is complete.
        """

        entities = context.entities

        if not context.source:
            context.source = self._get_first(
                entities,
                *self.SOURCE_KEYS,
            )

        if not context.target:
            context.target = self._get_first(
                entities,
                *self.TARGET_KEYS,
            )

        if not context.destination:
            context.destination = self._get_first(
                entities,
                *self.DESTINATION_KEYS,
            )

        if context.source and not context.target:
            context.target = context.source

        if context.target and not context.source:
            if context.intent in (
                self.MOVE_INTENTS
                | self.RENAME_INTENTS
                | self.DELETE_INTENTS
            ):
                context.source = context.target

        if context.intent in self.RENAME_INTENTS:
            new_name = self._get_first(
                entities,
                *self.NEW_NAME_KEYS,
            )

            if new_name:
                entities["new_name"] = new_name

    def _clean_entity_value(
        self,
        value: str,
    ) -> str:
        """
        Remove command words accidentally included in an entity.

        Examples:
            "open downloads" -> "downloads"
            "open file test" -> "test"
            "open folder projects" -> "projects"

        Normal multi-word file and folder names remain unchanged.
        """

        cleaned = value.strip()

        prefixes = (
            "open the folder ",
            "open the file ",
            "open folder ",
            "open file ",
            "open the ",
            "open ",
        )

        lowered = cleaned.lower()

        for prefix in prefixes:
            if lowered.startswith(prefix):
                return cleaned[len(prefix):].strip()

        return cleaned

    def _get_first(
        self,
        entities: dict[str, Any],
        *keys: str,
    ) -> str | None:
        """
        Return the first non-empty string-like entity value.
        """

        for key in keys:
            value = entities.get(key)

            if value is None:
                continue

            if isinstance(value, str):
                value = value.strip()

                if value:
                    return value

        return None

    def _find_missing_fields(
        self,
        context: AgentContext,
    ) -> list[str]:
        """
        Determine which information is required for the given intent.
        """

        missing: list[str] = []

        if context.intent in self.MOVE_INTENTS:
            if not context.source and not context.target:
                missing.append("source")

            if not context.destination:
                missing.append("destination")

        elif context.intent in self.CREATE_INTENTS:
            if not context.target:
                missing.append("name_or_path")

        elif context.intent in self.RENAME_INTENTS:
            if not context.target and not context.source:
                missing.append("target")

            new_name = self._get_first(
                context.entities,
                *self.NEW_NAME_KEYS,
            )

            if not new_name:
                missing.append("new_name")

        elif context.intent in self.DELETE_INTENTS:
            if not context.target and not context.source:
                missing.append("target")

        elif context.intent in self.SEARCH_INTENTS:
            search_query = self._get_first(
                context.entities,
                "query",
                "search_query",
                "target",
                "name",
                "entity",
                "foldername",
                "folder_name",
                "filename",
                "file_name",
                "file",
                "folder",
            )

            if not search_query:
                missing.append("search_query")

        elif context.intent in self.OPEN_INTENTS:
            if not context.target:
                missing.append("target")

        return missing

    def _extract_candidates(
        self,
        entities: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """
        Extract possible ambiguity candidates if upstream logic
        already provides them.
        """

        raw_candidates = entities.get("candidates")

        if not raw_candidates:
            return []

        if not isinstance(raw_candidates, list):
            return []

        candidates: list[dict[str, Any]] = []

        for item in raw_candidates:
            if isinstance(item, dict):
                candidates.append(item)

            elif isinstance(item, str):
                candidates.append(
                    {
                        "path": item,
                        "name": item,
                    }
                )

        return candidates

    def _build_missing_message(
        self,
        intent: str,
        missing_fields: list[str],
    ) -> str:
        """
        Build a user-friendly clarification message.
        """

        readable_fields = ", ".join(
            field.replace("_", " ")
            for field in missing_fields
        )

        return (
            f"I need more information to "
            f"{intent.replace('_', ' ')}. "
            f"Missing: {readable_fields}."
        )