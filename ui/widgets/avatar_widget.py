"""
ui/widgets/avatar_widget.py

ASTRA-AI Avatar Widget

AVATAR FLOW
-----------

App Open
    ↓
HELLO IMAGE
    ↓
IDLE PRIMARY
    ↓
RANDOM IDLE IMAGES


COMMAND FLOW
------------

Listening
    ↓
Thinking Laptop / Thinking AI
    ↓
Success / Error
    ↓
Idle


AI / GEMINI FLOW
----------------

Listening
    ↓
Thinking AI
    ↓
Speaking
    ↓
Success / Error
    ↓
Idle


SUPPORTED STATES
----------------

hello
idle
listening
thinking_laptop
thinking_ai
speaking
success
error
"""

from __future__ import annotations

import random
from pathlib import Path

from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QPixmap
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

    # --------------------------------------------------------
    # Timing
    # --------------------------------------------------------

    IDLE_CHANGE_INTERVAL = 4000
    SUCCESS_DISPLAY_INTERVAL = 3000
    ERROR_DISPLAY_INTERVAL = 3000

    # --------------------------------------------------------
    # Signals
    # --------------------------------------------------------

    state_changed = Signal(str)

    # ========================================================
    # INITIALIZATION
    # ========================================================

    def __init__(self, parent=None):

        super().__init__(parent)

        self.setObjectName("AvatarWidget")

        self.setAttribute(
            Qt.WidgetAttribute.WA_TranslucentBackground
        )

        self.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding,
        )

        self.setMinimumSize(1, 1)

        # ----------------------------------------------------
        # State
        # ----------------------------------------------------

        self.current_state = "hello"
        self.current_image_path = None
        self.current_pixmap = QPixmap()
        self.image_cache = {}

        # State generation prevents old timer callbacks from
        # overriding a newer avatar state.
        self._state_generation = 0
        self._success_generation = None
        self._error_generation = None

        # ----------------------------------------------------
        # Project Root
        # ----------------------------------------------------

        self.project_root = (
            Path(__file__).resolve().parents[2]
        )

        # ====================================================
        # IMAGE PATHS
        # ====================================================

        self.hello_image_path = (
            self.project_root
            / "ui"
            / "assets"
            / "avatars"
            / "hello"
            / "hello.png"
        )

        self.listening_image_path = (
            self.project_root
            / "ui"
            / "assets"
            / "avatars"
            / "listening"
            / "listening.png"
        )

        self.thinking_laptop_image_path = (
            self.project_root
            / "ui"
            / "assets"
            / "avatars"
            / "thinking"
            / "thinking_laptop.png"
        )

        self.thinking_ai_image_path = (
            self.project_root
            / "ui"
            / "assets"
            / "avatars"
            / "thinking"
            / "thinking_ai.png"
        )

        self.speaking_image_path = (
            self.project_root
            / "ui"
            / "assets"
            / "avatars"
            / "speaking"
            / "speaking.png"
        )

        self.success_image_path = (
            self.project_root
            / "ui"
            / "assets"
            / "avatars"
            / "success"
            / "success.png"
        )

        self.error_image_path = (
            self.project_root
            / "ui"
            / "assets"
            / "avatars"
            / "error"
            / "error.png"
        )

        self.idle_primary_path = (
            self.project_root
            / "ui"
            / "assets"
            / "avatars"
            / "idle"
            / "idle_primary.png"
        )

        self.idle_image_paths = []

        for index in range(1, 10):

            self.idle_image_paths.append(
                self.project_root
                / "ui"
                / "assets"
                / "avatars"
                / "idle"
                / f"idle_{index:02d}.png"
            )

        # ====================================================
        # LOAD CACHE
        # ====================================================

        self._load_avatar_cache()

        # ====================================================
        # TIMERS
        # ====================================================

        # Idle slideshow timer
        self.idle_timer = QTimer(self)
        self.idle_timer.setInterval(
            self.IDLE_CHANGE_INTERVAL
        )
        self.idle_timer.timeout.connect(
            self._show_random_idle
        )

        # Success auto return timer
        self.success_timer = QTimer(self)
        self.success_timer.setSingleShot(True)
        self.success_timer.setInterval(
            self.SUCCESS_DISPLAY_INTERVAL
        )
        self.success_timer.timeout.connect(
            self._return_to_idle_after_success
        )

        # Error auto return timer
        self.error_timer = QTimer(self)
        self.error_timer.setSingleShot(True)
        self.error_timer.setInterval(
            self.ERROR_DISPLAY_INTERVAL
        )
        self.error_timer.timeout.connect(
            self._return_to_idle_after_error
        )

        # ====================================================
        # BUILD UI
        # ====================================================

        self._build_ui()

        # ====================================================
        # INITIAL STATE
        # ====================================================

        self._load_hello()

    # ========================================================
    # CACHE
    # ========================================================

    def _load_avatar_cache(self):
        """
        Load all avatar images into RAM once.
        """

        all_image_paths = [
            self.hello_image_path,
            self.listening_image_path,
            self.thinking_laptop_image_path,
            self.thinking_ai_image_path,
            self.speaking_image_path,
            self.success_image_path,
            self.error_image_path,
            self.idle_primary_path,
            *self.idle_image_paths,
        ]

        print("[AVATAR CACHE] Loading avatar images...")

        for image_path in all_image_paths:

            if not image_path.exists():

                print(
                    "[AVATAR ERROR] Image not found:"
                )
                print(image_path)

                continue

            pixmap = QPixmap(str(image_path))

            if pixmap.isNull():

                print(
                    "[AVATAR ERROR] Failed to cache:"
                )
                print(image_path)

                continue

            self.image_cache[image_path] = pixmap

            print(
                "[AVATAR CACHE] Loaded: "
                f"{image_path.name}"
            )

        print(
            "[AVATAR CACHE] Ready: "
            f"{len(self.image_cache)} image(s)."
        )

    # ========================================================
    # UI
    # ========================================================

    def _build_ui(self):

        self.main_layout = QVBoxLayout(self)

        self.main_layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        self.main_layout.setSpacing(0)

        self.main_layout.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        self.avatar_label = QLabel(self)

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

        self.avatar_label.setMinimumSize(1, 1)

        self.avatar_label.setScaledContents(True)

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
    # IMAGE DISPLAY
    # ========================================================

    def _load_image(
        self,
        image_path: Path,
    ):
        """
        Display a cached avatar image.
        """

        pixmap = self.image_cache.get(
            image_path
        )

        if pixmap is None:

            print(
                "[AVATAR ERROR] Cached image unavailable:"
            )
            print(image_path)

            return False

        self.current_pixmap = pixmap
        self.current_image_path = image_path

        self.avatar_label.setPixmap(
            self.current_pixmap
        )

        print(
            "[AVATAR] Image displayed: "
            f"{image_path.name}"
        )

        return True

    # ========================================================
    # STATE ACTIVATION
    # ========================================================

    def _begin_state_transition(self):
        """
        Invalidate callbacks belonging to an older state.
        """

        self._state_generation += 1

        self._success_generation = None
        self._error_generation = None

        self._stop_all_timers()

        return self._state_generation

    def _activate_state(
        self,
        state: str,
        image_path: Path,
    ):
        """
        Activate a permanent state.

        This always stops the idle slideshow and all temporary
        timers before displaying the new state.
        """

        self._begin_state_transition()

        loaded = self._load_image(
            image_path
        )

        if not loaded:
            return False

        self.current_state = state

        self.state_changed.emit(state)

        print(
            f"[AVATAR] {state.upper()} state active."
        )

        return True

    # ========================================================
    # TIMER CONTROL
    # ========================================================

    def _stop_idle_timer(self):

        if hasattr(self, "idle_timer"):
            self.idle_timer.stop()

    def _stop_success_timer(self):

        if hasattr(self, "success_timer"):
            self.success_timer.stop()

    def _stop_error_timer(self):

        if hasattr(self, "error_timer"):
            self.error_timer.stop()

    def _stop_all_temporary_timers(self):

        self._stop_success_timer()
        self._stop_error_timer()

    def _stop_all_timers(self):

        self._stop_idle_timer()
        self._stop_success_timer()
        self._stop_error_timer()

    # ========================================================
    # HELLO
    # ========================================================

    def _load_hello(self):

        loaded = self._activate_state(
            "hello",
            self.hello_image_path,
        )

        return loaded

    # ========================================================
    # LISTENING
    # ========================================================

    def _load_listening(self):

        loaded = self._activate_state(
            "listening",
            self.listening_image_path,
        )

        if not loaded:

            print(
                "[AVATAR ERROR] "
                "Unable to activate LISTENING state."
            )

        return loaded

    # ========================================================
    # THINKING LAPTOP
    # ========================================================

    def _load_thinking_laptop(self):

        loaded = self._activate_state(
            "thinking_laptop",
            self.thinking_laptop_image_path,
        )

        if not loaded:

            print(
                "[AVATAR ERROR] "
                "Unable to activate THINKING LAPTOP state."
            )

        return loaded

    # ========================================================
    # THINKING AI
    # ========================================================

    def _load_thinking_ai(self):

        loaded = self._activate_state(
            "thinking_ai",
            self.thinking_ai_image_path,
        )

        if not loaded:

            print(
                "[AVATAR ERROR] "
                "Unable to activate THINKING AI state."
            )

        return loaded

    # ========================================================
    # SPEAKING
    # ========================================================

    def _load_speaking(self):
        """
        Activate SPEAKING state.

        Important:
        SPEAKING remains active until another state is explicitly
        requested. It does NOT have an automatic timeout.

        The TTS/controller must do:

            avatar.set_state("speaking")
            start_tts()
            wait until TTS finishes
            avatar.set_state("success") or avatar.set_state("idle")
        """

        loaded = self._activate_state(
            "speaking",
            self.speaking_image_path,
        )

        if not loaded:

            print(
                "[AVATAR ERROR] "
                "Unable to activate SPEAKING state."
            )

        return loaded

    # ========================================================
    # SUCCESS
    # ========================================================

    def _load_success(self):
        """
        Show success image temporarily.

        After SUCCESS_DISPLAY_INTERVAL,
        automatically return to idle.
        """

        generation = self._begin_state_transition()

        loaded = self._load_image(
            self.success_image_path
        )

        if not loaded:

            print(
                "[AVATAR ERROR] "
                "Unable to activate SUCCESS state."
            )

            return False

        self.current_state = "success"

        self._success_generation = generation

        self.state_changed.emit("success")

        print(
            "[AVATAR] SUCCESS state active."
        )

        print(
            "[AVATAR] SUCCESS will return "
            f"to IDLE after "
            f"{self.SUCCESS_DISPLAY_INTERVAL / 1000:.0f} seconds."
        )

        self.success_timer.start()

        return True

    def _return_to_idle_after_success(self):

        if self.current_state != "success":
            return

        if (
            self._success_generation
            != self._state_generation
        ):
            return

        print(
            "[AVATAR] SUCCESS completed -> IDLE."
        )

        self._start_idle()

    # ========================================================
    # ERROR
    # ========================================================

    def _load_error(self):
        """
        Show error image temporarily.

        After ERROR_DISPLAY_INTERVAL,
        automatically return to idle.
        """

        generation = self._begin_state_transition()

        loaded = self._load_image(
            self.error_image_path
        )

        if not loaded:

            print(
                "[AVATAR ERROR] "
                "Unable to activate ERROR state."
            )

            return False

        self.current_state = "error"

        self._error_generation = generation

        self.state_changed.emit("error")

        print(
            "[AVATAR] ERROR state active."
        )

        print(
            "[AVATAR] ERROR will return "
            f"to IDLE after "
            f"{self.ERROR_DISPLAY_INTERVAL / 1000:.0f} seconds."
        )

        self.error_timer.start()

        return True

    def _return_to_idle_after_error(self):

        if self.current_state != "error":
            return

        if (
            self._error_generation
            != self._state_generation
        ):
            return

        print(
            "[AVATAR] ERROR completed -> IDLE."
        )

        self._start_idle()

    # ========================================================
    # IDLE
    # ========================================================

    def _start_idle(self):

        self._begin_state_transition()

        loaded = self._load_image(
            self.idle_primary_path
        )

        if not loaded:
            return False

        self.current_state = "idle"

        self.state_changed.emit("idle")

        print(
            "[AVATAR] IDLE PRIMARY active."
        )

        print(
            "[AVATAR] Image will switch every "
            f"{self.IDLE_CHANGE_INTERVAL / 1000:.0f} seconds."
        )

        # idle_primary remains visible first.
        self.idle_timer.start()

        return True

    # ========================================================
    # RANDOM IDLE
    # ========================================================

    def _get_random_idle_image(self):

        available_images = [
            image_path
            for image_path in self.idle_image_paths
            if image_path in self.image_cache
        ]

        if not available_images:

            print(
                "[AVATAR ERROR] "
                "No cached idle shuffle images found."
            )

            return None

        random_image = random.choice(
            available_images
        )

        # Prevent immediate repetition.
        if (
            len(available_images) > 1
            and self.current_image_path == random_image
        ):

            other_images = [
                image_path
                for image_path in available_images
                if image_path
                != self.current_image_path
            ]

            if other_images:

                random_image = random.choice(
                    other_images
                )

        return random_image

    def _show_random_idle(self):
        """
        Idle timer is allowed to change the image ONLY while
        the current state is exactly 'idle'.

        Therefore it can never override:
            hello
            listening
            thinking_laptop
            thinking_ai
            speaking
            success
            error
        """

        if self.current_state != "idle":

            self._stop_idle_timer()

            print(
                "[AVATAR] Idle timer stopped because "
                f"current state is: {self.current_state}"
            )

            return

        random_image = (
            self._get_random_idle_image()
        )

        if random_image is None:
            return

        loaded = self._load_image(
            random_image
        )

        if not loaded:
            return

        print(
            "[AVATAR] Random IDLE image: "
            f"{random_image.name}"
        )

    # ========================================================
    # STATE ROUTER
    # ========================================================

    def set_state(
        self,
        state: str,
    ):

        requested_state = (
            state or ""
        ).strip().lower()

        if not requested_state:
            return

        print(
            "[AVATAR] Requested state: "
            f"{requested_state}"
        )

        # Avoid unnecessary permanent-state reloads.
        # Success and error are intentionally allowed to restart.
        if (
            requested_state == self.current_state
            and requested_state not in {
                "success",
                "error",
            }
        ):
            return

        state_handlers = {
            "hello": self._load_hello,
            "listening": self._load_listening,
            "thinking_laptop": (
                self._load_thinking_laptop
            ),
            "thinking_ai": (
                self._load_thinking_ai
            ),
            "speaking": self._load_speaking,
            "success": self._load_success,
            "error": self._load_error,
            "idle": self._start_idle,
        }

        handler = state_handlers.get(
            requested_state
        )

        if handler is None:

            print(
                f"[AVATAR] State '{requested_state}' "
                "is not implemented. "
                "Keeping current avatar image."
            )

            return

        # Do not restart an already running idle slideshow.
        if (
            requested_state == "idle"
            and self.current_state == "idle"
            and self.idle_timer.isActive()
        ):
            return

        handler()

    # ========================================================
    # COMPATIBILITY API
    # ========================================================

    def set_avatar_state(
        self,
        state: str,
    ):

        self.set_state(state)

    def set_listening(
        self,
        listening: bool,
    ):

        if listening:
            self.set_state("listening")
        else:
            self.set_state("idle")

    def set_thinking_laptop(self):

        self.set_state("thinking_laptop")

    def set_thinking_ai(self):

        self.set_state("thinking_ai")

    def set_speaking(self):

        self.set_state("speaking")

    def set_success(self):

        self.set_state("success")

    def set_error(self):

        self.set_state("error")

    def set_idle(self):

        self.set_state("idle")

    def current_avatar_state(self):

        return self.current_state

    # ========================================================
    # STOP / CLEANUP
    # ========================================================

    def stop(self):

        self._state_generation += 1

        self._success_generation = None
        self._error_generation = None

        self._stop_all_timers()

        print(
            "[AVATAR] Avatar timers stopped."
        )

    def closeEvent(
        self,
        event,
    ):

        self.stop()

        super().closeEvent(event)
