"""
ASTRA-AI
Premium Conversation Panel

Compact WhatsApp-style message bubbles
ChatGPT-style adaptive composer
"""

from __future__ import annotations

import random

from typing import Callable, Optional

from PySide6.QtCore import (
    Qt,
    Signal,
    QTimer,
    QPropertyAnimation,
    QEasingCurve,
)

from PySide6.QtGui import (
    QColor,
    QFont,
    QFontMetrics,
)

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QPlainTextEdit,
    QScrollArea,
    QFrame,
    QSizePolicy,
    QGraphicsDropShadowEffect,
)


# ==============================================================
# Message Bubble
# ==============================================================


class MessageBubble(QFrame):

    MAX_BUBBLE_WIDTH = 360

    MIN_BUBBLE_WIDTH = 72

    HORIZONTAL_PADDING = 28

    VERTICAL_PADDING = 20

    def __init__(
        self,
        message: str,
        is_user: bool = False,
        parent: Optional[QWidget] = None,
    ):

        super().__init__(
            parent
        )

        self.message = str(
            message
        )

        self.is_user = is_user

        self.setObjectName(
            "UserMessage"
            if is_user
            else "AssistantMessage"
        )

        # ------------------------------------------------------
        # IMPORTANT
        #
        # Bubble should NEVER expand to fill the row.
        # It must stay compact and grow only when content grows.
        # ------------------------------------------------------

        self.setSizePolicy(
            QSizePolicy.Fixed,
            QSizePolicy.Fixed
        )

        self.setMinimumWidth(
            self.MIN_BUBBLE_WIDTH
        )

        self.setMaximumWidth(
            self.MAX_BUBBLE_WIDTH
        )

        self.setMinimumHeight(
            0
        )

        # ======================================================
        # LAYOUT
        # ======================================================

        layout = QVBoxLayout(
            self
        )

        layout.setContentsMargins(
            14,
            10,
            14,
            10,
        )

        layout.setSpacing(
            5
        )

        # ======================================================
        # SENDER
        # ======================================================

        sender = QLabel(
            "You"
            if is_user
            else "ASTRA"
        )

        sender.setObjectName(
            "MessageSender"
        )

        sender.setSizePolicy(
            QSizePolicy.Fixed,
            QSizePolicy.Fixed
        )

        # ======================================================
        # MESSAGE
        # ======================================================

        text = QLabel(
            self.message
        )

        text.setObjectName(
            "MessageText"
        )

        text.setWordWrap(
            True
        )

        text.setAlignment(
            Qt.AlignLeft |
            Qt.AlignVCenter
        )

        text.setTextInteractionFlags(
            Qt.TextSelectableByMouse
        )

        text.setSizePolicy(
            QSizePolicy.Fixed,
            QSizePolicy.Fixed
        )

        # ------------------------------------------------------
        # Add widgets
        # ------------------------------------------------------

        layout.addWidget(
            sender
        )

        layout.addWidget(
            text
        )

        self.sender_label = sender

        self.text_label = text

        # ======================================================
        # STYLE
        # ======================================================

        self.setStyleSheet(
            """
            QFrame#UserMessage {

                background: #F0E8FF;

                border: 1px solid #DDD0FF;

                border-radius: 16px;

            }

            QFrame#AssistantMessage {

                background: #F7F7FA;

                border: 1px solid #E6E6EC;

                border-radius: 16px;

            }

            QLabel#MessageSender {

                color: #7C3AED;

                font-family: "Poppins";

                font-size: 11px;

                font-weight: 700;

                background: transparent;

            }

            QLabel#MessageText {

                color: #1F2937;

                font-family: "Poppins";

                font-size: 13px;

                background: transparent;

            }

            """
        )

        # ======================================================
        # COMPACT SIZE CALCULATION
        # ======================================================

        self._update_compact_size()


    # ==========================================================
    # COMPACT SIZE
    # ==========================================================

    def _update_compact_size(
        self
    ):

        try:

            # --------------------------------------------------
            # Font used by message text
            # --------------------------------------------------

            font = QFont(
                "Poppins",
                13
            )

            metrics = QFontMetrics(
                font
            )

            # --------------------------------------------------
            # Calculate longest natural line.
            # --------------------------------------------------

            lines = self.message.split(
                "\n"
            )

            longest_width = 0

            for line in lines:

                width = metrics.horizontalAdvance(
                    line
                )

                longest_width = max(
                    longest_width,
                    width
                )

            # --------------------------------------------------
            # Sender width
            # --------------------------------------------------

            sender_font = QFont(
                "Poppins",
                11,
                QFont.Bold
            )

            sender_metrics = QFontMetrics(
                sender_font
            )

            sender_width = sender_metrics.horizontalAdvance(
                "ASTRA"
                if not self.is_user
                else "You"
            )

            # --------------------------------------------------
            # Content width
            # --------------------------------------------------

            content_width = max(
                longest_width,
                sender_width
            )

            natural_width = (
                content_width
                +
                self.HORIZONTAL_PADDING
            )

            # --------------------------------------------------
            # Minimum width
            # --------------------------------------------------

            natural_width = max(
                self.MIN_BUBBLE_WIDTH,
                natural_width
            )

            # --------------------------------------------------
            # Maximum width
            # --------------------------------------------------

            natural_width = min(
                self.MAX_BUBBLE_WIDTH,
                natural_width
            )

            # --------------------------------------------------
            # Set width FIRST.
            #
            # QLabel then knows exactly how much space it has
            # and can wrap long messages correctly.
            # --------------------------------------------------

            self.setFixedWidth(
                natural_width
            )

            # --------------------------------------------------
            # Message label width
            # --------------------------------------------------

            inner_width = max(
                40,
                natural_width
                -
                self.HORIZONTAL_PADDING
            )

            self.text_label.setFixedWidth(
                inner_width
            )

            self.sender_label.adjustSize()

            # --------------------------------------------------
            # Force label recalculation.
            # --------------------------------------------------

            self.text_label.adjustSize()

            # --------------------------------------------------
            # For wrapped text, calculate required height.
            # --------------------------------------------------

            text_height = (
                self.text_label.height()
            )

            sender_height = (
                self.sender_label.height()
            )

            layout_margins = (
                self.layout().contentsMargins().top()
                +
                self.layout().contentsMargins().bottom()
            )

            spacing = (
                self.layout().spacing()
            )

            required_height = (
                text_height
                +
                sender_height
                +
                layout_margins
                +
                spacing
            )

            required_height = max(
                58,
                required_height
            )

            self.setFixedHeight(
                required_height
            )

            # --------------------------------------------------
            # Recalculate once after width is known.
            # --------------------------------------------------

            QTimer.singleShot(
                0,
                self._finalize_size
            )

        except RuntimeError:

            pass


    # ==========================================================
    # FINALIZE SIZE
    # ==========================================================

    def _finalize_size(
        self
    ):

        try:

            self.text_label.adjustSize()

            self.sender_label.adjustSize()

            text_height = (
                self.text_label.height()
            )

            sender_height = (
                self.sender_label.height()
            )

            margins = (
                self.layout().contentsMargins()
            )

            spacing = (
                self.layout().spacing()
            )

            height = (
                text_height
                +
                sender_height
                +
                margins.top()
                +
                margins.bottom()
                +
                spacing
            )

            self.setFixedHeight(
                max(
                    58,
                    height
                )
            )

        except RuntimeError:

            pass


# ==============================================================
# Message Composer
# ==============================================================


class MessageComposer(QPlainTextEdit):

    send_requested = Signal()

    MIN_HEIGHT = 42

    MAX_HEIGHT = 105

    def __init__(
        self,
        parent: Optional[QWidget] = None,
    ):

        super().__init__(
            parent
        )

        self.setObjectName(
            "MessageInput"
        )

        self.setMinimumHeight(
            self.MIN_HEIGHT
        )

        self.setMaximumHeight(
            self.MAX_HEIGHT
        )

        self.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Fixed
        )

        self.setHorizontalScrollBarPolicy(
            Qt.ScrollBarAlwaysOff
        )

        self.setVerticalScrollBarPolicy(
            Qt.ScrollBarAlwaysOff
        )

        self.textChanged.connect(
            self._update_height
        )

        QTimer.singleShot(
            0,
            self._update_height
        )


    # ==========================================================
    # Adaptive Height
    # ==========================================================

    def _update_height(
        self
    ):

        try:

            document_height = (
                self.document()
                .documentLayout()
                .documentSize()
                .height()
            )

            frame_height = (
                self.frameWidth() * 2
            )

            margins = (
                self.contentsMargins().top()
                +
                self.contentsMargins().bottom()
            )

            required_height = int(
                document_height
                +
                frame_height
                +
                margins
                +
                8
            )

            required_height = max(
                self.MIN_HEIGHT,
                required_height
            )

            required_height = min(
                self.MAX_HEIGHT,
                required_height
            )

            self.setFixedHeight(
                required_height
            )

            if (
                document_height
                >
                self.MAX_HEIGHT - 20
            ):

                self.setVerticalScrollBarPolicy(
                    Qt.ScrollBarAsNeeded
                )

            else:

                self.setVerticalScrollBarPolicy(
                    Qt.ScrollBarAlwaysOff
                )

            self.updateGeometry()

        except RuntimeError:

            pass


    # ==========================================================
    # Keyboard
    # ==========================================================

    def keyPressEvent(
        self,
        event
    ):

        if event.key() in (
            Qt.Key_Return,
            Qt.Key_Enter,
        ):

            if event.modifiers() & Qt.ShiftModifier:

                super().keyPressEvent(
                    event
                )

                return

            self.send_requested.emit()

            event.accept()

            return

        super().keyPressEvent(
            event
        )


# ==============================================================
# Premium Red Close Button
# ==============================================================


class PremiumCloseButton(QPushButton):

    def __init__(
        self,
        parent: Optional[QWidget] = None,
    ):

        super().__init__(
            "×",
            parent
        )

        self.setObjectName(
            "PremiumCloseButton"
        )

        self.setFixedSize(
            38,
            38
        )

        self.setCursor(
            Qt.PointingHandCursor
        )

        self.setFocusPolicy(
            Qt.NoFocus
        )

        self.setToolTip(
            "Close conversation"
        )

        self.NORMAL_STYLE = """
        QPushButton#PremiumCloseButton {

            background: #EF4444;

            color: white;

            border: 2px solid #FCA5A5;

            border-radius: 19px;

            font-family: "Segoe UI";

            font-size: 22px;

            font-weight: 500;

            padding: 0px;

        }

        QPushButton#PremiumCloseButton:hover {

            background: #DC2626;

            color: white;

            border: 2px solid #F87171;

        }

        QPushButton#PremiumCloseButton:pressed {

            background: #B91C1C;

            color: white;

            border: 2px solid #EF4444;

        }
        """

        self.setStyleSheet(
            self.NORMAL_STYLE
        )

        # ------------------------------------------------------
        # Red Glow
        # ------------------------------------------------------

        self.shadow = QGraphicsDropShadowEffect(
            self
        )

        self.shadow.setOffset(
            0,
            0
        )

        self.shadow.setBlurRadius(
            0
        )

        self.shadow.setColor(
            QColor(
                239,
                68,
                68,
                0
            )
        )

        self.setGraphicsEffect(
            self.shadow
        )

        self.glow_animation = QPropertyAnimation(
            self.shadow,
            b"blurRadius",
            self
        )

        self.glow_animation.setDuration(
            180
        )

        self.glow_animation.setEasingCurve(
            QEasingCurve.OutCubic
        )


    # ==========================================================
    # Hover Enter
    # ==========================================================

    def enterEvent(
        self,
        event
    ):

        self.glow_animation.stop()

        self.shadow.setColor(
            QColor(
                239,
                68,
                68,
                190
            )
        )

        self.glow_animation.setStartValue(
            self.shadow.blurRadius()
        )

        self.glow_animation.setEndValue(
            22
        )

        self.glow_animation.start()

        super().enterEvent(
            event
        )


    # ==========================================================
    # Hover Leave
    # ==========================================================

    def leaveEvent(
        self,
        event
    ):

        self.glow_animation.stop()

        self.glow_animation.setStartValue(
            self.shadow.blurRadius()
        )

        self.glow_animation.setEndValue(
            0
        )

        self.glow_animation.start()

        super().leaveEvent(
            event
        )


    # ==========================================================
    # Cleanup
    # ==========================================================

    def hideEvent(
        self,
        event
    ):

        if self.glow_animation is not None:

            self.glow_animation.stop()

        super().hideEvent(
            event
        )


# ==============================================================
# Conversation Panel
# ==============================================================


class ConversationPanel(QWidget):

    send_requested = Signal(str)

    close_requested = Signal()

    MAX_WORDS = 5000

    GREETINGS = (
        "Welcome, Naresh! 👋",

        "Hey Naresh! Ready when you are. 🚀",

        "Welcome back, Naresh! 🤝",

        "Good to see you, Naresh! ✨",

        "Hi Naresh! What can I help you with today?",

        "Hello Naresh! ASTRA is ready. 💜",

        "Hey Naresh! Let's get things done. ⚡",

        "Welcome, Naresh! Your ASTRA friend is here. 🤖",
    )


    # ==========================================================
    # Constructor
    # ==========================================================

    def __init__(
        self,
        parent: Optional[QWidget] = None,
        user_name: str = "Naresh",
    ):

        super().__init__(
            parent
        )

        self.user_name = user_name

        self._message_widgets = []

        self._send_callback: Optional[
            Callable[[str], None]
        ] = None

        self._is_submitting = False

        self._has_opened_once = False

        self.setObjectName(
            "ConversationPanel"
        )

        self.setMinimumWidth(
            0
        )

        self.setMaximumWidth(
            16777215
        )

        self.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Expanding
        )

        self.build_ui()

        self.start_new_conversation()


    # ==========================================================
    # Build UI
    # ==========================================================

    def build_ui(
        self
    ):

        self.setStyleSheet(
            """
            QWidget#ConversationPanel {

                background: transparent;

                border: none;

            }

            QFrame#ConversationCard {

                background: rgba(
                    255,
                    255,
                    255,
                    250
                );

                border: 1px solid #DDD6FE;

                border-radius: 20px;

            }

            QLabel#WelcomeLabel {

                color: #171B2D;

                font-family: "Poppins";

                font-size: 21px;

                font-weight: 600;

                background: transparent;

            }

            QScrollArea#ConversationScroll {

                background: transparent;

                border: none;

            }

            QWidget#MessageContainer {

                background: transparent;

            }

            QFrame#ComposerFrame {

                background: #FFFFFF;

                border: 1px solid #E5E7EB;

                border-radius: 18px;

            }

            QPlainTextEdit#MessageInput {

                background: transparent;

                border: none;

                color: #1F2937;

                font-family: "Poppins";

                font-size: 13px;

                padding: 7px 8px 2px 8px;

            }

            QPlainTextEdit#MessageInput:focus {

                border: none;

            }

            QPushButton#SendButton {

                background: #7C3AED;

                color: white;

                border: none;

                border-radius: 17px;

                font-family: "Segoe UI";

                font-size: 14px;

                font-weight: 700;

                min-width: 34px;

                min-height: 34px;

                max-width: 34px;

                max-height: 34px;

            }

            QPushButton#SendButton:hover {

                background: #6D28D9;

            }

            QPushButton#SendButton:pressed {

                background: #5B21B6;

            }

            QPushButton#SendButton:disabled {

                background: #D1D5DB;

                color: white;

            }

            QLabel#WordCounter {

                color: #9CA3AF;

                font-family: "Poppins";

                font-size: 9px;

                background: transparent;

            }

            QLabel#WordCounter[limitReached="true"] {

                color: #DC2626;

                font-weight: 700;

            }

            """
        )

        # ======================================================
        # OUTER
        # ======================================================

        outer_layout = QVBoxLayout(
            self
        )

        outer_layout.setContentsMargins(
            0,
            0,
            0,
            0
        )

        outer_layout.setSpacing(
            0
        )

        # ======================================================
        # CARD
        # ======================================================

        self.chat_card = QFrame()

        self.chat_card.setObjectName(
            "ConversationCard"
        )

        self.chat_card.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Expanding
        )

        outer_layout.addWidget(
            self.chat_card
        )

        # ======================================================
        # CARD ROOT
        # ======================================================

        root = QVBoxLayout(
            self.chat_card
        )

        root.setContentsMargins(
            12,
            12,
            12,
            12
        )

        root.setSpacing(
            8
        )

        # ======================================================
        # CLOSE BUTTON
        # ======================================================

        header = QHBoxLayout()

        header.setContentsMargins(
            0,
            0,
            0,
            0
        )

        header.setSpacing(
            0
        )

        header.addStretch()

        self.close_button = PremiumCloseButton()

        self.close_button.clicked.connect(
            self._handle_close_clicked
        )

        header.addWidget(
            self.close_button,
            0,
            Qt.AlignRight |
            Qt.AlignTop
        )

        root.addLayout(
            header
        )

        # ======================================================
        # SCROLL AREA
        # ======================================================

        self.scroll_area = QScrollArea()

        self.scroll_area.setObjectName(
            "ConversationScroll"
        )

        self.scroll_area.setWidgetResizable(
            True
        )

        self.scroll_area.setFrameShape(
            QFrame.NoFrame
        )

        self.scroll_area.setHorizontalScrollBarPolicy(
            Qt.ScrollBarAlwaysOff
        )

        self.scroll_area.setVerticalScrollBarPolicy(
            Qt.ScrollBarAsNeeded
        )

        # ------------------------------------------------------
        # Message Container
        # ------------------------------------------------------

        self.message_container = QWidget()

        self.message_container.setObjectName(
            "MessageContainer"
        )

        self.message_layout = QVBoxLayout(
            self.message_container
        )

        self.message_layout.setContentsMargins(
            4,
            4,
            4,
            8
        )

        self.message_layout.setSpacing(
            10
        )

        self.message_layout.addStretch()

        self.scroll_area.setWidget(
            self.message_container
        )

        root.addWidget(
            self.scroll_area,
            stretch=1
        )

        # ======================================================
        # COMPOSER
        # ======================================================

        composer_frame = QFrame()

        composer_frame.setObjectName(
            "ComposerFrame"
        )

        composer_layout = QVBoxLayout(
            composer_frame
        )

        composer_layout.setContentsMargins(
            8,
            7,
            7,
            7
        )

        composer_layout.setSpacing(
            2
        )

        # ------------------------------------------------------
        # INPUT
        # ------------------------------------------------------

        self.message_input = MessageComposer()

        self.message_input.setObjectName(
            "MessageInput"
        )

        self.message_input.setPlaceholderText(
            "Ask ASTRA..."
        )

        self.message_input.setMinimumHeight(
            MessageComposer.MIN_HEIGHT
        )

        self.message_input.setMaximumHeight(
            MessageComposer.MAX_HEIGHT
        )

        self.message_input.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Fixed
        )

        self.message_input.textChanged.connect(
            self._on_text_changed
        )

        self.message_input.send_requested.connect(
            self.submit_message
        )

        composer_layout.addWidget(
            self.message_input
        )

        # ======================================================
        # BOTTOM ROW
        # ======================================================

        bottom_row = QHBoxLayout()

        bottom_row.setContentsMargins(
            0,
            0,
            0,
            0
        )

        bottom_row.setSpacing(
            4
        )

        # ------------------------------------------------------
        # WORD COUNTER
        # ------------------------------------------------------

        self.word_counter = QLabel(
            "0 / 5000 words"
        )

        self.word_counter.setObjectName(
            "WordCounter"
        )

        bottom_row.addWidget(
            self.word_counter
        )

        bottom_row.addStretch()

        # ------------------------------------------------------
        # SEND BUTTON
        # ------------------------------------------------------

        self.send_button = QPushButton(
            "➤"
        )

        self.send_button.setObjectName(
            "SendButton"
        )

        self.send_button.setToolTip(
            "Send message"
        )

        self.send_button.setCursor(
            Qt.PointingHandCursor
        )

        self.send_button.setFocusPolicy(
            Qt.NoFocus
        )

        self.send_button.clicked.connect(
            self.submit_message
        )

        self.send_button.setEnabled(
            False
        )

        bottom_row.addWidget(
            self.send_button
        )

        composer_layout.addLayout(
            bottom_row
        )

        root.addWidget(
            composer_frame
        )


    # ==========================================================
    # CLOSE
    # ==========================================================

    def _handle_close_clicked(
        self
    ):

        self.close_requested.emit()


    # ==========================================================
    # SHOW
    # ==========================================================

    def showEvent(
        self,
        event
    ):

        super().showEvent(
            event
        )

        if self._has_opened_once:

            self.start_new_conversation()

        self._has_opened_once = True

        QTimer.singleShot(
            0,
            self._focus_input
        )


    # ==========================================================
    # FOCUS
    # ==========================================================

    def _focus_input(
        self
    ):

        try:

            if self.isVisible():

                self.message_input.setFocus()

        except RuntimeError:

            pass


    # ==========================================================
    # NEW CONVERSATION
    # ==========================================================

    def start_new_conversation(
        self
    ):

        while self.message_layout.count():

            item = self.message_layout.takeAt(
                0
            )

            widget = item.widget()

            if widget is not None:

                widget.deleteLater()

        self._message_widgets.clear()

        # ------------------------------------------------------
        # Greeting
        # ------------------------------------------------------

        greeting = random.choice(
            self.GREETINGS
        )

        welcome = QLabel(
            greeting
        )

        welcome.setObjectName(
            "WelcomeLabel"
        )

        welcome.setAlignment(
            Qt.AlignCenter
        )

        welcome.setWordWrap(
            True
        )

        welcome.setFont(
            QFont(
                "Poppins",
                21,
                QFont.DemiBold
            )
        )

        # ------------------------------------------------------
        # Centered greeting container
        #
        # IMPORTANT:
        # No subtitle here.
        # ------------------------------------------------------

        welcome_box = QWidget()

        welcome_box.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Expanding
        )

        welcome_layout = QVBoxLayout(
            welcome_box
        )

        welcome_layout.setContentsMargins(
            20,
            20,
            20,
            20
        )

        welcome_layout.setSpacing(
            8
        )

        welcome_layout.addStretch(
            1
        )

        welcome_layout.addWidget(
            welcome,
            0,
            Qt.AlignCenter
        )

        welcome_layout.addStretch(
            1
        )

        self.message_layout.addWidget(
            welcome_box,
            1
        )

        # ------------------------------------------------------
        # Reset input
        # ------------------------------------------------------

        self.message_input.blockSignals(
            True
        )

        try:

            self.message_input.clear()

        finally:

            self.message_input.blockSignals(
                False
            )

        self.message_input.setFixedHeight(
            MessageComposer.MIN_HEIGHT
        )

        self._update_counter()

        self._scroll_to_bottom()


    # ==========================================================
    # CLEAR
    # ==========================================================

    def clear_conversation(
        self
    ):

        self.start_new_conversation()


    # ==========================================================
    # USER MESSAGE
    # ==========================================================

    def add_user_message(
        self,
        message: str
    ):

        self._add_message(
            message,
            True
        )


    # ==========================================================
    # ASSISTANT MESSAGE
    # ==========================================================

    def add_assistant_message(
        self,
        message: str
    ):

        self._add_message(
            message,
            False
        )


    # ==========================================================
    # ADD MESSAGE
    # ==========================================================

    def _add_message(
        self,
        message: str,
        is_user: bool
    ):

        message = str(
            message
        ).strip()

        if not message:

            return

        # ------------------------------------------------------
        # Remove welcome widget.
        # ------------------------------------------------------

        if self.message_layout.count() > 0:

            first_item = (
                self.message_layout.itemAt(
                    0
                )
            )

            first_widget = (
                first_item.widget()
                if first_item
                else None
            )

            if first_widget is not None:

                self.message_layout.takeAt(
                    0
                )

                first_widget.deleteLater()

        # ======================================================
        # BUBBLE
        # ======================================================

        bubble = MessageBubble(
            message,
            is_user
        )

        # ======================================================
        # ROW
        # ======================================================

        row = QHBoxLayout()

        row.setContentsMargins(
            4,
            0,
            4,
            0
        )

        row.setSpacing(
            4
        )

        if is_user:

            row.addStretch()

            row.addWidget(
                bubble,
                0,
                Qt.AlignRight
            )

        else:

            row.addWidget(
                bubble,
                0,
                Qt.AlignLeft
            )

            row.addStretch()

        # ======================================================
        # WRAPPER
        # ======================================================

        wrapper = QWidget()

        wrapper.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Fixed
        )

        wrapper.setStyleSheet(
            """
            QWidget {

                background: transparent;

            }
            """
        )

        wrapper.setLayout(
            row
        )

        # ======================================================
        # INSERT BEFORE FINAL STRETCH
        # ======================================================

        insert_index = max(
            0,
            self.message_layout.count() - 1
        )

        self.message_layout.insertWidget(
            insert_index,
            wrapper
        )

        self._message_widgets.append(
            bubble
        )

        self._scroll_to_bottom()


    # ==========================================================
    # SEND CALLBACK
    # ==========================================================

    def set_send_callback(
        self,
        callback: Optional[
            Callable[[str], None]
        ]
    ):

        self._send_callback = callback


    # ==========================================================
    # SUBMIT
    # ==========================================================

    def submit_message(
        self
    ):

        if self._is_submitting:

            return

        text = (
            self.message_input
            .toPlainText()
            .strip()
        )

        if not text:

            return

        # ------------------------------------------------------
        # 5000 word limit
        # ------------------------------------------------------

        if (
            self._word_count(text)
            >
            self.MAX_WORDS
        ):

            self._trim_to_word_limit()

            text = (
                self.message_input
                .toPlainText()
                .strip()
            )

        if not text:

            return

        self._is_submitting = True

        try:

            self.add_user_message(
                text
            )

            self.message_input.clear()

            self.message_input.setFixedHeight(
                MessageComposer.MIN_HEIGHT
            )

            self.send_requested.emit(
                text
            )

            if (
                self._send_callback
                is not None
            ):

                self._send_callback(
                    text
                )

        finally:

            self._is_submitting = False

            self._update_counter()


    # ==========================================================
    # WORD COUNT
    # ==========================================================

    @staticmethod
    def _word_count(
        text: str
    ) -> int:

        return len(
            text.split()
        )


    # ==========================================================
    # TEXT CHANGED
    # ==========================================================

    def _on_text_changed(
        self
    ):

        self._trim_to_word_limit()

        self._update_counter()


    # ==========================================================
    # TRIM TO LIMIT
    # ==========================================================

    def _trim_to_word_limit(
        self
    ):

        text = (
            self.message_input
            .toPlainText()
        )

        words = text.split()

        if len(words) <= self.MAX_WORDS:

            return

        trimmed = " ".join(
            words[
                :self.MAX_WORDS
            ]
        )

        cursor = (
            self.message_input
            .textCursor()
        )

        self.message_input.blockSignals(
            True
        )

        try:

            self.message_input.setPlainText(
                trimmed
            )

            cursor.setPosition(
                len(trimmed)
            )

            self.message_input.setTextCursor(
                cursor
            )

        finally:

            self.message_input.blockSignals(
                False
            )


    # ==========================================================
    # COUNTER
    # ==========================================================

    def _update_counter(
        self
    ):

        count = self._word_count(
            self.message_input
            .toPlainText()
        )

        self.word_counter.setText(
            f"{count} / {self.MAX_WORDS} words"
        )

        reached = (
            count >= self.MAX_WORDS
        )

        self.word_counter.setProperty(
            "limitReached",
            reached
        )

        self.word_counter.style().unpolish(
            self.word_counter
        )

        self.word_counter.style().polish(
            self.word_counter
        )

        has_text = bool(
            self.message_input
            .toPlainText()
            .strip()
        )

        self.send_button.setEnabled(
            has_text
        )


    # ==========================================================
    # AI RESPONSE
    # ==========================================================

    def show_ai_response(
        self,
        response: str
    ):

        self.add_assistant_message(
            response
        )


    # ==========================================================
    # ERROR
    # ==========================================================

    def show_error(
        self,
        message: str
    ):

        self.add_assistant_message(
            f"Sorry, {message}"
        )


    # ==========================================================
    # INPUT ENABLE
    # ==========================================================

    def set_input_enabled(
        self,
        enabled: bool
    ):

        self.message_input.setEnabled(
            enabled
        )

        has_text = bool(
            self.message_input
            .toPlainText()
            .strip()
        )

        self.send_button.setEnabled(
            enabled
            and has_text
        )


    # ==========================================================
    # SCROLL
    # ==========================================================

    def _scroll_to_bottom(
        self
    ):

        QTimer.singleShot(
            0,
            self._perform_scroll_to_bottom
        )


    # ==========================================================
    # PERFORM SCROLL
    # ==========================================================

    def _perform_scroll_to_bottom(
        self
    ):

        try:

            scrollbar = (
                self.scroll_area
                .verticalScrollBar()
            )

            scrollbar.setValue(
                scrollbar.maximum()
            )

        except RuntimeError:

            pass