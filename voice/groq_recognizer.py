"""
Groq Speech Recognition Module
==============================

Online Speech-to-Text using Groq Whisper.

Primary model:
    whisper-large-v3-turbo

Purpose:
    - Keep Groq STT isolated from the existing local
      Faster-Whisper recognizer.
    - Accept an existing WAV/audio file.
    - Send the audio to Groq.
    - Return a clean transcript.
    - Expose rate-limit/network failures clearly so
      the caller can fall back to local Whisper.

IMPORTANT:
    This module does NOT modify or depend on the existing
    whisper_recognizer.py implementation.
"""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any

from groq import Groq


class GroqSTTError(Exception):
    """Base exception for Groq Speech-to-Text failures."""


class GroqSTTRateLimitError(GroqSTTError):
    """Raised when Groq rate limits are reached."""


class GroqSTTConfigurationError(GroqSTTError):
    """Raised when Groq STT configuration is missing or invalid."""


class GroqRecognizer:
    """
    Groq-based Speech-to-Text recognizer.

    This class is intentionally independent from the existing
    Faster-Whisper recognizer so that the local recognizer can
    remain available as a fallback.

    Environment variables:

        GROQ_API_KEY
            Groq API key.

        GROQ_STT_MODEL
            Optional model name.
            Defaults to whisper-large-v3-turbo.
    """

    DEFAULT_MODEL = "whisper-large-v3-turbo"

    # Maximum useful transcript length protection.
    MAX_TEXT_LENGTH = 10000

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
    ) -> None:
        """
        Initialize the Groq STT client.

        Parameters
        ----------
        api_key:
            Optional API key. If omitted, GROQ_API_KEY from
            environment variables is used.

        model:
            Optional Groq STT model. If omitted,
            GROQ_STT_MODEL is used, then the default model.
        """

        self.api_key = (
            api_key
            or os.getenv("GROQ_API_KEY", "").strip()
        )

        self.model = (
            model
            or os.getenv(
                "GROQ_STT_MODEL",
                self.DEFAULT_MODEL,
            ).strip()
            or self.DEFAULT_MODEL
        )

        if not self.api_key:
            raise GroqSTTConfigurationError(
                "GROQ_API_KEY is not configured."
            )

        self.client = Groq(
            api_key=self.api_key
        )

        print(
            f"Groq STT Ready | Model : {self.model}"
        )

    # ==================================================
    # File Validation
    # ==================================================

    def _validate_audio_file(
        self,
        audio_file: str | Path,
    ) -> Path:
        """
        Validate the supplied audio file.
        """

        path = Path(
            audio_file
        ).resolve()

        if not path.exists():

            raise GroqSTTError(
                f"Audio file does not exist: {path}"
            )

        if not path.is_file():

            raise GroqSTTError(
                f"Audio path is not a file: {path}"
            )

        if path.stat().st_size <= 0:

            raise GroqSTTError(
                f"Audio file is empty: {path}"
            )

        return path

    # ==================================================
    # Transcript Cleanup
    # ==================================================

    @staticmethod
    def normalize_text(
        text: str | None,
    ) -> str:
        """
        Clean and normalize the returned transcript.

        This does NOT attempt to change the meaning of the
        user's command.
        """

        if not text:

            return ""

        text = str(text)

        # Normalize whitespace.
        text = " ".join(
            text.split()
        )

        # Remove accidental whitespace before punctuation.
        text = re.sub(
            r"\s+([,.!?;:])",
            r"\1",
            text,
        )

        return text.strip()

    # ==================================================
    # Basic Garbage Detection
    # ==================================================

    @staticmethod
    def _is_repetitive_garbage(
        text: str,
    ) -> bool:
        """
        Detect obvious repeated-token transcription garbage.

        Examples:

            a a a a a a
            A-A-A-A-A-A
            the the the the

        This is deliberately conservative. It should reject
        obvious ASR garbage without trying to interpret normal
        user speech.
        """

        if not text:

            return True

        words = re.findall(
            r"[A-Za-z]+",
            text.lower(),
        )

        if len(words) < 5:

            return False

        unique_words = set(words)

        if len(unique_words) == 1:

            return True

        # Very strong repeated single-token pattern.
        counts: dict[str, int] = {}

        for word in words:

            counts[word] = (
                counts.get(word, 0) + 1
            )

        highest_count = max(
            counts.values()
        )

        if (
            highest_count >= 8
            and highest_count / len(words) >= 0.80
        ):

            return True

        return False

    # ==================================================
    # Groq Error Classification
    # ==================================================

    @staticmethod
    def _raise_groq_error(
        error: Exception,
    ) -> None:
        """
        Convert common Groq failures into useful ASTRA-level
        exceptions.

        The raw exception is retained as the cause.
        """

        status_code = getattr(
            error,
            "status_code",
            None,
        )

        if status_code == 429:

            raise GroqSTTRateLimitError(
                "Groq STT rate limit reached."
            ) from error

        error_text = str(
            error
        ).lower()

        if (
            "rate limit" in error_text
            or "too many requests" in error_text
            or "429" in error_text
        ):

            raise GroqSTTRateLimitError(
                "Groq STT rate limit reached."
            ) from error

        raise GroqSTTError(
            f"Groq STT request failed: {error}"
        ) from error

    # ==================================================
    # Transcribe Audio
    # ==================================================

    def transcribe(
        self,
        audio_file: str | Path,
    ) -> str:
        """
        Transcribe an existing audio file using Groq Whisper.

        Parameters
        ----------
        audio_file:
            Path to a WAV/audio file.

        Returns
        -------
        str
            Clean transcript.

        Raises
        ------
        GroqSTTRateLimitError
            When Groq rate limits are reached.

        GroqSTTError
            For other Groq or audio failures.
        """

        path = self._validate_audio_file(
            audio_file
        )

        print(
            "\n🧠 Sending audio to Groq STT..."
        )

        print(
            f"Audio File : {path}"
        )

        print(
            f"Audio Size : {path.stat().st_size} bytes"
        )

        try:

            with path.open(
                "rb"
            ) as audio:

                transcription = (
                    self.client.audio.transcriptions.create(
                        file=audio,
                        model=self.model,
                        response_format="text",
                        language="en",
                        temperature=0.0,
                    )
                )

            # Depending on SDK response handling,
            # response may behave as a string or expose
            # a text attribute.
            if isinstance(
                transcription,
                str,
            ):

                text = transcription

            else:

                text = getattr(
                    transcription,
                    "text",
                    "",
                )

            text = self.normalize_text(
                text
            )

            if not text:

                print(
                    "Groq STT returned empty transcript."
                )

                return ""

            if self._is_repetitive_garbage(
                text
            ):

                print(
                    "Groq STT rejected obvious repetitive "
                    "transcription garbage."
                )

                return ""

            if len(text) > self.MAX_TEXT_LENGTH:

                text = text[
                    : self.MAX_TEXT_LENGTH
                ].rstrip()

            print(
                "\n========== GROQ STT =========="
            )

            print(
                f"Transcript : {text}"
            )

            print(
                "==============================\n"
            )

            return text

        except GroqSTTError:

            raise

        except Exception as error:

            self._raise_groq_error(
                error
            )

            # Defensive fallback for static type checkers.
            return ""

    # ==================================================
    # Alias
    # ==================================================

    def listen(
        self,
        audio_file: str | Path,
    ) -> str | None:
        """
        Compatibility alias.

        This method expects an already-recorded audio file.
        Microphone recording remains the responsibility of
        the existing ASTRA speech-recognition layer.
        """

        try:

            text = self.transcribe(
                audio_file
            )

            return text or None

        except GroqSTTError as error:

            print(
                f"Groq STT Error : {error}"
            )

            return None

    # ==================================================
    # Health Check
    # ==================================================

    def is_configured(self) -> bool:
        """
        Return True when a Groq API key is configured.
        """

        return bool(
            self.api_key
        )

    def get_model(self) -> str:
        """
        Return the currently configured STT model.
        """

        return self.model

    # ==================================================
    # Safe Representation
    # ==================================================

    def __repr__(self) -> str:
        """
        Safe representation that never exposes the API key.
        """

        return (
            f"GroqRecognizer("
            f"model={self.model!r}, "
            f"configured={self.is_configured()!r}"
            f")"
        )