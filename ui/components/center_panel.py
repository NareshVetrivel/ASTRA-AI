"""
ui/components/center_panel.py

ASTRA-AI
Center Avatar Panel

Image-based avatar state flow:

    App Opens
        ↓
    HELLO
        ↓
    IDLE PRIMARY
        ↓
    RANDOM IDLE IMAGES

Supported states:

    hello
    idle
    listening
    thinking
    thinking_laptop
    thinking_ai
    speaking
    success
    error

The microphone remains controlled by main_window.py.
"""

from __future__ import annotations

from PySide6.QtCore import Qt

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QSizePolicy,
)

from ui.widgets.avatar_widget import AvatarWidget


# ============================================================
# CENTER PANEL
# ============================================================

class CenterPanelWidget(QWidget):
    """
    ASTRA center avatar panel.

    This panel is responsible only for forwarding avatar state
    requests to AvatarWidget.

    AvatarWidget handles:

        - HELLO -> IDLE transition
        - Idle primary image
        - Random idle image shuffle
        - State image switching
        - Temporary success/error return to idle
        - Timer cleanup
    """

    def __init__(
        self,
        parent=None,
    ):
        super().__init__(parent)

        self.setObjectName(
            "centerPanel"
        )

        self.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding,
        )

        self.current_state = "hello"

        self.build_ui()

    # ========================================================
    # UI
    # ========================================================

    def build_ui(
        self,
    ):
        """
        Build the center avatar panel.
        """

        self.setStyleSheet(
            """
            QWidget#centerPanel {
                background: transparent;
                border: none;
            }
            """
        )

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

        self.build_avatar()

    # ========================================================
    # AVATAR
    # ========================================================

    def build_avatar(
        self,
    ):
        """
        Create the image-based ASTRA avatar.
        """

        self.avatar_widget = AvatarWidget(
            parent=self,
        )

        self.avatar_widget.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding,
        )

        self.avatar_widget.setMinimumSize(
            1,
            1,
        )

        self.main_layout.addWidget(
            self.avatar_widget,
            1,
            Qt.AlignmentFlag.AlignCenter,
        )

        # ----------------------------------------------------
        # STATE SYNCHRONIZATION
        # ----------------------------------------------------

        if hasattr(
            self.avatar_widget,
            "state_changed",
        ):
            self.avatar_widget.state_changed.connect(
                self._on_avatar_state_changed
            )

        try:

            self.current_state = (
                self.avatar_widget.current_avatar_state()
            )

        except Exception:

            self.current_state = "hello"

        print(
            "[AVATAR] Image AvatarWidget created."
        )

        print(
            "[AVATAR] Initial avatar flow started."
        )

        print(
            "[AVATAR] HELLO -> IDLE PRIMARY -> RANDOM IDLE"
        )

    # ========================================================
    # STATE CHANGED
    # ========================================================

    def _on_avatar_state_changed(
        self,
        state: str,
    ):
        """
        Keep CenterPanel state synchronized with AvatarWidget.
        """

        self.current_state = state

        print(
            f"[CENTER PANEL] Avatar state: {state}"
        )

    # ========================================================
    # SET AVATAR STATE
    # ========================================================

    def set_avatar_state(
        self,
        state: str,
    ):
        """
        Change the current avatar state.

        Supported states:

            hello
            idle
            listening
            thinking
            thinking_laptop
            thinking_ai
            speaking
            success
            error
        """

        state = (
            state or ""
        ).strip().lower()

        if not state:

            print(
                "[AVATAR] Empty state received."
            )

            return

        if not hasattr(
            self,
            "avatar_widget",
        ):

            print(
                "[AVATAR] Avatar widget unavailable."
            )

            return

        # ----------------------------------------------------
        # NORMALIZE GENERIC THINKING
        # ----------------------------------------------------

        # Existing backend may still send "thinking".
        #
        # Default generic thinking to AI thinking so existing
        # calls do not break.

        if state == "thinking":

            state = "thinking_ai"

        print(
            f"[AVATAR] Requested state: {state}"
        )

        self.avatar_widget.set_state(
            state
        )

        self.current_state = state

    # ========================================================
    # LISTENING COMPATIBILITY
    # ========================================================

    def set_listening(
        self,
        listening: bool,
    ):
        """
        Compatibility method for main_window.py.
        """

        if listening:

            self.set_avatar_state(
                "listening"
            )

        else:

            self.set_avatar_state(
                "idle"
            )

    # ========================================================
    # THINKING LAPTOP
    # ========================================================

    def set_thinking_laptop(
        self,
    ):
        """
        Show laptop/system command processing avatar.
        """

        self.set_avatar_state(
            "thinking_laptop"
        )

    # ========================================================
    # THINKING AI
    # ========================================================

    def set_thinking_ai(
        self,
    ):
        """
        Show AI processing avatar.
        """

        self.set_avatar_state(
            "thinking_ai"
        )

    # ========================================================
    # GENERIC THINKING COMPATIBILITY
    # ========================================================

    def set_thinking(
        self,
    ):
        """
        Compatibility method.

        Generic thinking defaults to thinking_ai.
        """

        self.set_thinking_ai()

    # ========================================================
    # SPEAKING
    # ========================================================

    def set_speaking(
        self,
    ):
        """
        Show speaking avatar.
        """

        self.set_avatar_state(
            "speaking"
        )

    # ========================================================
    # SUCCESS
    # ========================================================

    def set_success(
        self,
    ):
        """
        Show success avatar.

        AvatarWidget controls automatic return to idle.
        """

        self.set_avatar_state(
            "success"
        )

    # ========================================================
    # ERROR
    # ========================================================

    def set_error(
        self,
    ):
        """
        Show error avatar.

        AvatarWidget controls automatic return to idle.
        """

        self.set_avatar_state(
            "error"
        )

    # ========================================================
    # IDLE
    # ========================================================

    def set_idle(
        self,
    ):
        """
        Switch avatar to idle.

        AvatarWidget will:

            idle_primary.png
                ↓
            random idle images
        """

        self.set_avatar_state(
            "idle"
        )

    # ========================================================
    # STOP AVATAR
    # ========================================================

    def stop_avatar(
        self,
    ):
        """
        Stop avatar timers safely.
        """

        if not hasattr(
            self,
            "avatar_widget",
        ):

            return

        self.avatar_widget.stop()

        print(
            "[AVATAR] Avatar stopped."
        )

    # ========================================================
    # STATUS COMPATIBILITY
    # ========================================================

    def update_status(
        self,
        text: str,
    ):
        """
        Compatibility method for existing backend calls.

        The center panel does not display separate status text,
        but existing backend code can safely continue calling it.
        """

        print(
            f"[AVATAR] Status update: {text}"
        )

    # ========================================================
    # CLEANUP
    # ========================================================

    def closeEvent(
        self,
        event,
    ):
        """
        Stop avatar timers before closing.
        """

        self.stop_avatar()

        super().closeEvent(
            event
        )