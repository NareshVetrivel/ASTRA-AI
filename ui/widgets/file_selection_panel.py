from __future__ import annotations

from typing import Any, Iterable

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QFrame,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)


class FileSelectionPanel(QFrame):
    """
    Compact translucent glassmorphism panel for file/folder
    candidate selection.

    This widget is presentation-only:
        - Displays numbered candidates and full paths.
        - Does not perform TTS.
        - Does not control the microphone.
        - Emits selection_requested(index).
        - Remains hidden unless explicitly shown by MainWindow.

    MainWindow is responsible for placing this panel immediately
    above the microphone while keeping the central avatar/halo area
    unobstructed.
    """

    selection_requested = Signal(int)
    cancelled = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self._candidates: list[dict[str, Any]] = []
        self._operation: str = "file"
        self._title: str = "FILE OPTIONS"

        self._build_ui()
        self.hide()

    def _build_ui(self) -> None:
        """Build the compact translucent glassmorphism UI."""

        self.setObjectName("fileSelectionPanel")
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setFrameShape(QFrame.NoFrame)

        self.setStyleSheet(
            """
            QFrame#fileSelectionPanel {
                background-color: rgba(255, 255, 255, 48);
                border: 1px solid rgba(255, 255, 255, 90);
                border-radius: 20px;
            }

            QLabel#selectionTitle {
                background: transparent;
                color: #4c1d95;
                font-size: 15px;
                font-weight: 700;
                padding: 0px;
            }

            QLabel#selectionSubtitle {
                background: transparent;
                color: #6b7280;
                font-size: 11px;
                font-weight: 500;
                padding: 0px;
            }

            QScrollArea#candidateScroll {
                background: transparent;
                border: none;
            }

            QWidget#candidateContainer {
                background: transparent;
            }

            QFrame#candidateCard {
                background-color: rgba(255, 255, 255, 30);
                border: 1px solid rgba(139, 92, 246, 28);
                border-radius: 13px;
            }

            QFrame#candidateCard:hover {
                background-color: rgba(255, 255, 255, 60);
                border: 1px solid rgba(124, 58, 237, 60);
            }

            QLabel#candidateNumber {
                background-color: rgba(124, 58, 237, 205);
                color: white;
                border-radius: 15px;
                font-size: 13px;
                font-weight: 700;
            }

            QLabel#candidateName {
                background: transparent;
                color: #1f2937;
                font-size: 12px;
                font-weight: 700;
            }

            QLabel#candidatePath {
                background: transparent;
                color: #6b7280;
                font-size: 9px;
                font-weight: 500;
            }

            QPushButton#candidateButton {
                background-color: rgba(124, 58, 237, 10);
                border: 1px solid rgba(124, 58, 237, 38);
                border-radius: 8px;
                color: #6d28d9;
                font-size: 10px;
                font-weight: 700;
                padding: 5px 9px;
            }

            QPushButton#candidateButton:hover {
                background-color: rgba(124, 58, 237, 24);
            }

            QPushButton#cancelButton {
                background-color: rgba(239, 68, 68, 7);
                border: 1px solid rgba(239, 68, 68, 36);
                border-radius: 8px;
                color: #dc2626;
                font-size: 10px;
                font-weight: 700;
                padding: 5px 12px;
            }

            QPushButton#cancelButton:hover {
                background-color: rgba(239, 68, 68, 18);
            }
            """
        )

        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(24)
        shadow.setOffset(0, 6)
        shadow.setColor(QColor(91, 33, 182, 45))
        self.setGraphicsEffect(shadow)

        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(14, 11, 14, 10)
        self.main_layout.setSpacing(6)

        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(7)

        self.title_label = QLabel(self._title)
        self.title_label.setObjectName("selectionTitle")
        self.title_label.setAlignment(
            Qt.AlignLeft | Qt.AlignVCenter
        )
        header_layout.addWidget(self.title_label, 1)

        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.setObjectName("cancelButton")
        self.cancel_button.setCursor(Qt.PointingHandCursor)
        self.cancel_button.clicked.connect(
            self._on_cancel_clicked
        )
        header_layout.addWidget(self.cancel_button)

        self.main_layout.addLayout(header_layout)

        self.subtitle_label = QLabel(
            "Choose one option from the list."
        )
        self.subtitle_label.setObjectName("selectionSubtitle")
        self.subtitle_label.setWordWrap(True)
        self.main_layout.addWidget(self.subtitle_label)

        self.scroll_area = QScrollArea()
        self.scroll_area.setObjectName("candidateScroll")
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(
            Qt.ScrollBarAlwaysOff
        )
        self.scroll_area.setVerticalScrollBarPolicy(
            Qt.ScrollBarAsNeeded
        )
        self.scroll_area.setFrameShape(QFrame.NoFrame)

        self.candidate_container = QWidget()
        self.candidate_container.setObjectName(
            "candidateContainer"
        )

        self.candidate_layout = QVBoxLayout(
            self.candidate_container
        )
        self.candidate_layout.setContentsMargins(1, 1, 4, 1)
        self.candidate_layout.setSpacing(5)
        self.candidate_layout.setAlignment(Qt.AlignTop)

        self.scroll_area.setWidget(self.candidate_container)
        self.main_layout.addWidget(self.scroll_area, 1)

        self.footer_label = QLabel(
            "Say the option number to continue."
        )
        self.footer_label.setObjectName("selectionSubtitle")
        self.footer_label.setAlignment(Qt.AlignCenter)
        self.main_layout.addWidget(self.footer_label)

        self.setMinimumWidth(500)
        self.setMaximumWidth(700)
        self.setMinimumHeight(120)
        self.setMaximumHeight(285)

    def show_candidates(
        self,
        candidates: Iterable[Any],
        operation: str = "file",
    ) -> None:
        """Populate and show the selection panel."""

        self._candidates = [
            self._normalise_candidate(candidate, index)
            for index, candidate in enumerate(
                candidates,
                start=1,
            )
        ]

        self._operation = operation or "file"
        self._title = self._make_title(self._operation)

        self.title_label.setText(self._title)
        self.subtitle_label.setText(
            self._make_subtitle(len(self._candidates))
        )

        self._clear_candidate_widgets()

        for candidate in self._candidates:
            self._add_candidate_card(candidate)

        self.footer_label.setText(
            "Say the option number to continue."
        )

        self._update_panel_height()

        self.show()
        self.raise_()
        self.update()

    def hide_panel(self) -> None:
        """Hide the panel and clear candidates."""

        self._clear_candidate_widgets()
        self._candidates.clear()
        self.hide()

    def clear(self) -> None:
        """Clear candidates and hide the panel."""

        self.hide_panel()

    def candidates(self) -> list[dict[str, Any]]:
        """Return a copy of the current candidates."""

        return list(self._candidates)

    def is_selection_active(self) -> bool:
        """Return whether the panel is visible."""

        return self.isVisible()

    def select_index(self, selection: int) -> None:
        """Emit a selection for a 1-based candidate index."""

        try:
            index = int(selection)
        except (TypeError, ValueError):
            return

        if index < 1 or index > len(self._candidates):
            return

        self.selection_requested.emit(index)

    def _normalise_candidate(
        self,
        candidate: Any,
        index: int,
    ) -> dict[str, Any]:
        """Normalize supported candidate formats."""

        if isinstance(candidate, dict):
            name = (
                candidate.get("name")
                or candidate.get("filename")
                or candidate.get("folder")
                or candidate.get("title")
                or candidate.get("path")
                or "Unknown"
            )

            path = (
                candidate.get("path")
                or candidate.get("full_path")
                or candidate.get("file_path")
                or candidate.get("folder_path")
                or ""
            )

            candidate_type = (
                candidate.get("type")
                or candidate.get("kind")
                or "file"
            )

            result = dict(candidate)
            result.update(
                {
                    "index": index,
                    "name": str(name),
                    "path": str(path),
                    "type": str(candidate_type),
                }
            )
            return result

        if isinstance(candidate, (list, tuple)):
            name = (
                str(candidate[0])
                if len(candidate) > 0
                else "Unknown"
            )
            path = (
                str(candidate[1])
                if len(candidate) > 1
                else ""
            )

            return {
                "index": index,
                "name": name,
                "path": path,
                "type": "file",
            }

        value = str(candidate)

        return {
            "index": index,
            "name": value,
            "path": value,
            "type": "file",
        }

    def _add_candidate_card(
        self,
        candidate: dict[str, Any],
    ) -> None:
        """Create one compact candidate card."""

        card = QFrame(self.candidate_container)
        card.setObjectName("candidateCard")

        card_layout = QHBoxLayout(card)
        card_layout.setContentsMargins(8, 6, 8, 6)
        card_layout.setSpacing(8)

        number_label = QLabel(
            str(candidate["index"])
        )
        number_label.setObjectName("candidateNumber")
        number_label.setAlignment(Qt.AlignCenter)
        number_label.setFixedSize(30, 30)
        card_layout.addWidget(number_label)

        text_layout = QVBoxLayout()
        text_layout.setContentsMargins(0, 0, 0, 0)
        text_layout.setSpacing(1)

        name_label = QLabel(candidate["name"])
        name_label.setObjectName("candidateName")
        name_label.setWordWrap(True)
        text_layout.addWidget(name_label)

        path = candidate.get("path", "")

        if path:
            path_label = QLabel(f"Location: {path}")
            path_label.setObjectName("candidatePath")
            path_label.setWordWrap(True)
            text_layout.addWidget(path_label)

        card_layout.addLayout(text_layout, 1)

        select_button = QPushButton("Select")
        select_button.setObjectName("candidateButton")
        select_button.setCursor(Qt.PointingHandCursor)

        selection_index = int(candidate["index"])

        select_button.clicked.connect(
            lambda checked=False, index=selection_index:
            self.select_index(index)
        )

        card_layout.addWidget(select_button)

        self.candidate_layout.addWidget(card)

    def _clear_candidate_widgets(self) -> None:
        """Remove all candidate cards."""

        while self.candidate_layout.count() > 0:
            item = self.candidate_layout.takeAt(0)
            widget = item.widget()

            if widget is not None:
                widget.deleteLater()

    def _make_title(self, operation: str) -> str:
        """Build a compact operation title."""

        operation = (
            operation
            .replace("_", " ")
            .strip()
        )

        if not operation:
            return "FILE OPTIONS"

        return f"{operation.title()} Options"

    def _make_subtitle(self, count: int) -> str:
        """Build the candidate-count subtitle."""

        if count == 1:
            return "One matching item was found."

        return (
            f"{count} matching items were found. "
            "Choose the one you want."
        )

    def _update_panel_height(self) -> None:
        """
        Keep the panel compact so the MainWindow can place it
        above the microphone without covering the central halo/avatar.
        """

        count = len(self._candidates)

        if count <= 0:
            height = 120
        elif count == 1:
            height = 155
        elif count == 2:
            height = 195
        elif count == 3:
            height = 230
        elif count == 4:
            height = 260
        else:
            height = 285

        self.setFixedHeight(height)

    def _on_cancel_clicked(self) -> None:
        """Handle manual cancellation."""

        self.hide_panel()
        self.cancelled.emit()
