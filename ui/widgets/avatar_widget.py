"""
ui/widgets/avatar_widget.py

ASTRA-AI Premium Avatar Widget (V2)

Architecture:
QWidget
    └── QLabel (Avatar PNG)
"""

import os

from PySide6.QtCore import (
    Qt,
    QSize
)

from PySide6.QtGui import (
    QPixmap,
    QColor
)

from PySide6.QtWidgets import (
    QWidget,
    QLabel,
    QVBoxLayout,
    QSizePolicy,
    QGraphicsDropShadowEffect
)


class AvatarWidget(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setObjectName("AvatarWidget")

        self.setAttribute(
            Qt.WA_TranslucentBackground
        )

        self.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Expanding
        )

        self.setMinimumSize(560, 700)

        # ------------------------------------
        # Avatar State
        # ------------------------------------

        self.current_state = "idle"

        # ------------------------------------
        # Main Layout
        # ------------------------------------

        self.layout = QVBoxLayout(self)

        self.layout.setContentsMargins(
            0,
            0,
            0,
            0
        )

        self.layout.setSpacing(0)

        self.layout.setAlignment(
            Qt.AlignCenter
        )

        # ------------------------------------
        # Avatar Label
        # ------------------------------------

        self.avatar_label = QLabel()

        self.avatar_label.setAlignment(
            Qt.AlignCenter
        )

        self.avatar_label.setMinimumSize(
            520,
            660
        )

        self.avatar_label.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Expanding
        )

        self.layout.addWidget(
            self.avatar_label,
            alignment=Qt.AlignCenter
        )

        # ------------------------------------
        # Shadow Effect
        # ------------------------------------

        self.shadow = QGraphicsDropShadowEffect()

        self.shadow.setBlurRadius(90)

        self.shadow.setOffset(0,0)

        self.shadow.setColor(
            QColor(170,130,255,120)
        )

        self.avatar_label.setGraphicsEffect(
            self.shadow
        )

        # ------------------------------------
        # Avatar Image
        # ------------------------------------

        self.avatar_pixmap = QPixmap()

        self.load_avatar()

    # ------------------------------------------------
    # Load Avatar
    # ------------------------------------------------

    def load_avatar(self):

        possible_paths = [

            "ui/assets/avatar.png",

            "ui/assets/avatar.webp",

            "ui/assets/avatar.jpg",

            "assets/avatar.png",

            "assets/avatar.webp",

            "assets/avatar.jpg"

        ]

        for path in possible_paths:

            if os.path.exists(path):

                self.avatar_pixmap = QPixmap(path)

                break

        self.update_avatar()

    # ------------------------------------------------

    def resizeEvent(self, event):

        super().resizeEvent(event)

        self.update_avatar()

    # ------------------------------------------------
    # Update Avatar
    # ------------------------------------------------

    def update_avatar(self):
        """
        Scale avatar smoothly whenever the widget resizes.
        """

        if self.avatar_pixmap.isNull():
            return

        target_width = int(self.width() * 0.97)
        target_height = int(self.height() * 0.97)

        scaled = self.avatar_pixmap.scaled(
            QSize(
                target_width,
                target_height
            ),
            Qt.KeepAspectRatioByExpanding,
            Qt.SmoothTransformation
        )

        self.avatar_label.setPixmap(scaled)

        self.avatar_label.setScaledContents(False)

    # ------------------------------------------------
    # Avatar State
    # ------------------------------------------------

    def set_state(self, state: str):
        """
        idle
        listening
        thinking
        speaking
        success
        error
        """

        self.current_state = state.lower()

        if state == "listening":

            self.shadow.setBlurRadius(120)

            self.shadow.setColor(
                QColor("#8B5CF6")
            )

        elif state == "thinking":

            self.shadow.setBlurRadius(125)

            self.shadow.setColor(
                QColor("#F59E0B")
            )

        elif state == "speaking":

            self.shadow.setBlurRadius(130)

            self.shadow.setColor(
                QColor("#3B82F6")
            )

        elif state == "success":

            self.shadow.setBlurRadius(120)

            self.shadow.setColor(
                QColor("#22C55E")
            )

        elif state == "error":

            self.shadow.setBlurRadius(120)

            self.shadow.setColor(
                QColor("#EF4444")
            )

        else:

            self.shadow.setBlurRadius(85)

            self.shadow.setOffset(0,0)

            self.shadow.setColor(
                QColor(180,150,255,150)
            )

    # ------------------------------------------------
    # Change Avatar
    # ------------------------------------------------

    def set_avatar(self, image_path: str):

        if os.path.exists(image_path):

            self.avatar_pixmap = QPixmap(image_path)

            self.update_avatar()

    # ------------------------------------------------
    # Placeholder Hooks
    # ------------------------------------------------

    def set_mouth_open(self, value: float):
        """
        Future Lip-Sync Hook.
        """
        pass

    def set_eye_state(self, closed: bool):
        """
        Future Blink Hook.
        """
        pass

    def set_expression(self, expression: str):
        """
        Future Expression Hook.
        """
        pass

    # ------------------------------------------------
    # Public API
    # ------------------------------------------------

    def current_avatar_state(self):

        return self.current_state