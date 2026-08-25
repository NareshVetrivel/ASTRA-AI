"""
ui/widgets/avatar_widget.py

ASTRA-AI Avatar Widget

CURRENT IMPLEMENTATION:
    - HELLO IMAGE ONLY
    - No image detection
    - No transparent border detection
    - No cropping
    - No timers
    - No shuffle
    - No video
    - No other avatar images

The hello image is directly scaled to fill the
entire available AvatarWidget area.
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import (
    Qt,
    Signal,
)

from PySide6.QtGui import (
    QPixmap,
)

from PySide6.QtWidgets import (
    QWidget,
    QLabel,
    QVBoxLayout,
    QSizePolicy,
)


# ============================================================
# AVATAR WIDGET
# ============================================================

class AvatarWidget(QWidget):

    # ========================================================
    # SIGNAL
    # ========================================================

    state_changed = Signal(str)

    # ========================================================
    # INITIALIZATION
    # ========================================================

    def __init__(
        self,
        parent=None,
    ):
        super().__init__(parent)

        self.setObjectName(
            "AvatarWidget"
        )

        self.setAttribute(
            Qt.WidgetAttribute.WA_TranslucentBackground
        )

        self.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding,
        )

        self.setMinimumSize(
            1,
            1,
        )

        # ----------------------------------------------------
        # CURRENT STATE
        # ----------------------------------------------------

        self.current_state = "hello"

        self.current_image_path = None

        self.current_pixmap = QPixmap()

        # ----------------------------------------------------
        # PROJECT PATH
        # ----------------------------------------------------

        self.project_root = (
            Path(__file__)
            .resolve()
            .parents[2]
        )

        # ----------------------------------------------------
        # HELLO IMAGE PATH ONLY
        # ----------------------------------------------------

        self.hello_image_path = (
            self.project_root
            / "ui"
            / "assets"
            / "avatars"
            / "hello"
            / "hello.png"
        )

        # ----------------------------------------------------
        # BUILD UI
        # ----------------------------------------------------

        self._build_ui()

        # ----------------------------------------------------
        # LOAD HELLO IMAGE
        # ----------------------------------------------------

        self._load_hello()

    # ========================================================
    # BUILD UI
    # ========================================================

    def _build_ui(
        self,
    ):

        self.main_layout = QVBoxLayout(
            self
        )

        self.main_layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        self.main_layout.setSpacing(
            0
        )

        self.main_layout.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        # ----------------------------------------------------
        # AVATAR LABEL
        # ----------------------------------------------------

        self.avatar_label = QLabel(
            self
        )

        self.avatar_label.setObjectName(
            "avatarLabel"
        )

        self.avatar_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        self.avatar_label.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding,
        )

        self.avatar_label.setMinimumSize(
            1,
            1,
        )

        # ----------------------------------------------------
        # IMPORTANT
        #
        # Image directly fills QLabel.
        #
        # No crop.
        # No detection.
        # No aspect-ratio calculation.
        # ----------------------------------------------------

        self.avatar_label.setScaledContents(
            True
        )

        self.avatar_label.setStyleSheet(
            """
            QLabel#avatarLabel {
                background: transparent;
                border: none;
                padding: 0px;
                margin: 0px;
            }
            """
        )

        self.main_layout.addWidget(
            self.avatar_label,
            1,
        )

    # ========================================================
    # LOAD HELLO IMAGE
    # ========================================================

    def _load_hello(
        self,
    ):

        if not self.hello_image_path.exists():

            print(
                "[AVATAR ERROR] HELLO image not found:"
            )

            print(
                self.hello_image_path
            )

            return False

        pixmap = QPixmap(
            str(
                self.hello_image_path
            )
        )

        if pixmap.isNull():

            print(
                "[AVATAR ERROR] Failed to load HELLO image."
            )

            return False

        # ----------------------------------------------------
        # DIRECT ORIGINAL IMAGE
        #
        # No processing.
        # No crop.
        # No detection.
        # ----------------------------------------------------

        self.current_pixmap = pixmap

        self.current_image_path = (
            self.hello_image_path
        )

        self.avatar_label.setPixmap(
            self.current_pixmap
        )

        self.current_state = "hello"

        self.state_changed.emit(
            "hello"
        )

        print(
            "[AVATAR] HELLO image loaded."
        )

        print(
            f"[AVATAR] Image size: "
            f"{pixmap.width()} x {pixmap.height()}"
        )

        return True

    # ========================================================
    # SET STATE
    # ========================================================

    def set_state(
        self,
        state: str,
    ):
        """
        Current version uses HELLO image only.

        Any requested state keeps displaying
        the HELLO image.
        """

        requested_state = (
            state or ""
        ).strip().lower()

        if not requested_state:

            return

        self.current_state = "hello"

        self.state_changed.emit(
            "hello"
        )

        print(
            f"[AVATAR] Requested state: "
            f"{requested_state}"
        )

        print(
            "[AVATAR] HELLO image remains active."
        )

    # ========================================================
    # COMPATIBILITY
    # ========================================================

    def set_avatar_state(
        self,
        state: str,
    ):

        self.set_state(
            state
        )

    # ========================================================
    # LISTENING
    # ========================================================

    def set_listening(
        self,
        listening: bool,
    ):

        self.set_state(
            "hello"
        )

    # ========================================================
    # THINKING LAPTOP
    # ========================================================

    def set_thinking_laptop(
        self,
    ):

        self.set_state(
            "hello"
        )

    # ========================================================
    # THINKING AI
    # ========================================================

    def set_thinking_ai(
        self,
    ):

        self.set_state(
            "hello"
        )

    # ========================================================
    # SPEAKING
    # ========================================================

    def set_speaking(
        self,
    ):

        self.set_state(
            "hello"
        )

    # ========================================================
    # SUCCESS
    # ========================================================

    def set_success(
        self,
    ):

        self.set_state(
            "hello"
        )

    # ========================================================
    # ERROR
    # ========================================================

    def set_error(
        self,
    ):

        self.set_state(
            "hello"
        )

    # ========================================================
    # CURRENT STATE
    # ========================================================

    def current_avatar_state(
        self,
    ):

        return self.current_state

    # ========================================================
    # STOP
    # ========================================================

    def stop(
        self,
    ):

        pass

    # ========================================================
    # CLEANUP
    # ========================================================

    def closeEvent(
        self,
        event,
    ):

        self.stop()

        super().closeEvent(
            event
        )