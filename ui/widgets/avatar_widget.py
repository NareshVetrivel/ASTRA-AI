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
Temporary display
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


GOODBYE FLOW
------------

Window X Button
    ↓
GOODBYE IMAGE
    ↓
4 Seconds
    ↓
goodbye_finished signal
    ↓
Main Window closes


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
goodbye
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
    """
    Central ASTRA-AI avatar state widget.

    The widget controls only avatar presentation.

    Application shutdown is NOT performed here.

    For the goodbye flow:

        set_state("goodbye")
            ↓
        goodbye.png displayed
            ↓
        4 second timer
            ↓
        goodbye_finished emitted
            ↓
        MainWindow performs final shutdown
    """

    # ========================================================
    # TIMING
    # ========================================================

    IDLE_CHANGE_INTERVAL = 4000

    SUCCESS_DISPLAY_INTERVAL = 3000

    ERROR_DISPLAY_INTERVAL = 3000

    # Goodbye image remains visible for 4 seconds.
    GOODBYE_DISPLAY_INTERVAL = 4000

    # ========================================================
    # SIGNALS
    # ========================================================

    state_changed = Signal(str)

    # Emitted ONLY after the goodbye image has remained
    # visible for GOODBYE_DISPLAY_INTERVAL.
    goodbye_finished = Signal()

    # ========================================================
    # INITIALIZATION
    # ========================================================

    def __init__(self, parent=None):

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

        # ====================================================
        # STATE
        # ====================================================

        self.current_state = "hello"

        self.current_image_path = None

        self.current_pixmap = QPixmap()

        self.image_cache = {}

        # ----------------------------------------------------
        # State generation
        #
        # Every state transition increments this value.
        #
        # This prevents an older timer callback from affecting
        # a newer avatar state.
        # ----------------------------------------------------

        self._state_generation = 0

        self._success_generation = None

        self._error_generation = None

        self._goodbye_generation = None

        # ====================================================
        # PROJECT ROOT
        # ====================================================

        self.project_root = (
            Path(__file__).resolve().parents[2]
        )

        # ====================================================
        # IMAGE PATHS
        # ====================================================

        # ----------------------------------------------------
        # HELLO
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
        # LISTENING
        # ----------------------------------------------------

        self.listening_image_path = (

            self.project_root
            / "ui"
            / "assets"
            / "avatars"
            / "listening"
            / "listening.png"

        )

        # ----------------------------------------------------
        # THINKING LAPTOP
        # ----------------------------------------------------

        self.thinking_laptop_image_path = (

            self.project_root
            / "ui"
            / "assets"
            / "avatars"
            / "thinking"
            / "thinking_laptop.png"

        )

        # ----------------------------------------------------
        # THINKING AI
        # ----------------------------------------------------

        self.thinking_ai_image_path = (

            self.project_root
            / "ui"
            / "assets"
            / "avatars"
            / "thinking"
            / "thinking_ai.png"

        )

        # ----------------------------------------------------
        # SPEAKING
        # ----------------------------------------------------

        self.speaking_image_path = (

            self.project_root
            / "ui"
            / "assets"
            / "avatars"
            / "speaking"
            / "speaking.png"

        )

        # ----------------------------------------------------
        # SUCCESS
        # ----------------------------------------------------

        self.success_image_path = (

            self.project_root
            / "ui"
            / "assets"
            / "avatars"
            / "success"
            / "success.png"

        )

        # ----------------------------------------------------
        # ERROR
        # ----------------------------------------------------

        self.error_image_path = (

            self.project_root
            / "ui"
            / "assets"
            / "avatars"
            / "error"
            / "error.png"

        )

        # ----------------------------------------------------
        # GOODBYE
        #
        # Required file:
        #
        # ui/assets/avatars/goodbye/goodbye.png
        # ----------------------------------------------------

        self.goodbye_image_path = (

            self.project_root
            / "ui"
            / "assets"
            / "avatars"
            / "goodbye"
            / "goodbye.png"

        )

        # ----------------------------------------------------
        # IDLE PRIMARY
        # ----------------------------------------------------

        self.idle_primary_path = (

            self.project_root
            / "ui"
            / "assets"
            / "avatars"
            / "idle"
            / "idle_primary.png"

        )

        # ----------------------------------------------------
        # RANDOM IDLE IMAGES
        # ----------------------------------------------------

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
        # LOAD AVATAR CACHE
        # ====================================================

        self._load_avatar_cache()

        # ====================================================
        # TIMERS
        # ====================================================

        # ----------------------------------------------------
        # IDLE SLIDESHOW TIMER
        # ----------------------------------------------------

        self.idle_timer = QTimer(
            self
        )

        self.idle_timer.setInterval(
            self.IDLE_CHANGE_INTERVAL
        )

        self.idle_timer.timeout.connect(
            self._show_random_idle
        )

        # ----------------------------------------------------
        # SUCCESS TIMER
        # ----------------------------------------------------

        self.success_timer = QTimer(
            self
        )

        self.success_timer.setSingleShot(
            True
        )

        self.success_timer.setInterval(
            self.SUCCESS_DISPLAY_INTERVAL
        )

        self.success_timer.timeout.connect(
            self._return_to_idle_after_success
        )

        # ----------------------------------------------------
        # ERROR TIMER
        # ----------------------------------------------------

        self.error_timer = QTimer(
            self
        )

        self.error_timer.setSingleShot(
            True
        )

        self.error_timer.setInterval(
            self.ERROR_DISPLAY_INTERVAL
        )

        self.error_timer.timeout.connect(
            self._return_to_idle_after_error
        )

        # ----------------------------------------------------
        # GOODBYE TIMER
        #
        # IMPORTANT:
        #
        # This timer DOES NOT close the application.
        #
        # It only emits goodbye_finished after 4 seconds.
        #
        # MainWindow owns the actual shutdown.
        # ----------------------------------------------------

        self.goodbye_timer = QTimer(
            self
        )

        self.goodbye_timer.setSingleShot(
            True
        )

        self.goodbye_timer.setInterval(
            self.GOODBYE_DISPLAY_INTERVAL
        )

        self.goodbye_timer.timeout.connect(
            self._finish_goodbye
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

            self.goodbye_image_path,

            self.idle_primary_path,

            *self.idle_image_paths,

        ]

        print(
            "[AVATAR CACHE] Loading avatar images..."
        )

        for image_path in all_image_paths:

            if not image_path.exists():

                print(
                    "[AVATAR ERROR] Image not found:"
                )

                print(
                    image_path
                )

                continue

            pixmap = QPixmap(
                str(image_path)
            )

            if pixmap.isNull():

                print(
                    "[AVATAR ERROR] Failed to cache:"
                )

                print(
                    image_path
                )

                continue

            self.image_cache[
                image_path
            ] = pixmap

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
        # Avatar Label
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

            print(
                image_path
            )

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
        Invalidate all callbacks belonging to the previous state.

        Returns
        -------
        int
            New state generation number.
        """

        self._state_generation += 1

        self._success_generation = None

        self._error_generation = None

        self._goodbye_generation = None

        self._stop_all_timers()

        return self._state_generation

    def _activate_state(
        self,
        state: str,
        image_path: Path,
    ):
        """
        Activate a permanent avatar state.
        """

        self._begin_state_transition()

        loaded = self._load_image(
            image_path
        )

        if not loaded:

            return False

        self.current_state = state

        self.state_changed.emit(
            state
        )

        print(
            f"[AVATAR] {state.upper()} "
            "state active."
        )

        return True

    # ========================================================
    # TIMER CONTROL
    # ========================================================

    def _stop_idle_timer(self):

        if hasattr(
            self,
            "idle_timer",
        ):

            self.idle_timer.stop()

    def _stop_success_timer(self):

        if hasattr(
            self,
            "success_timer",
        ):

            self.success_timer.stop()

    def _stop_error_timer(self):

        if hasattr(
            self,
            "error_timer",
        ):

            self.error_timer.stop()

    def _stop_goodbye_timer(self):

        if hasattr(
            self,
            "goodbye_timer",
        ):

            self.goodbye_timer.stop()

    def _stop_all_temporary_timers(self):

        self._stop_success_timer()

        self._stop_error_timer()

        self._stop_goodbye_timer()

    def _stop_all_timers(self):

        self._stop_idle_timer()

        self._stop_success_timer()

        self._stop_error_timer()

        self._stop_goodbye_timer()

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

        SPEAKING remains active until another state is
        explicitly requested.
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

        generation = (
            self._begin_state_transition()
        )

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

        self._success_generation = (
            generation
        )

        self.state_changed.emit(
            "success"
        )

        print(
            "[AVATAR] SUCCESS state active."
        )

        print(
            "[AVATAR] SUCCESS will return "
            "to IDLE after "
            f"{self.SUCCESS_DISPLAY_INTERVAL / 1000:.0f} seconds."
        )

        self.success_timer.start()

        return True

    def _return_to_idle_after_success(self):
        """
        Return to idle only when the success timer belongs
        to the currently active state.
        """

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

        generation = (
            self._begin_state_transition()
        )

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

        self._error_generation = (
            generation
        )

        self.state_changed.emit(
            "error"
        )

        print(
            "[AVATAR] ERROR state active."
        )

        print(
            "[AVATAR] ERROR will return "
            "to IDLE after "
            f"{self.ERROR_DISPLAY_INTERVAL / 1000:.0f} seconds."
        )

        self.error_timer.start()

        return True

    def _return_to_idle_after_error(self):
        """
        Return to idle only when the error timer belongs
        to the currently active state.
        """

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
    # GOODBYE
    # ========================================================

    def _load_goodbye(self):
        """
        Activate GOODBYE state.

        Flow:

            goodbye.png
                ↓
            4 seconds
                ↓
            goodbye_finished signal

        This method NEVER closes the application itself.
        """

        generation = (
            self._begin_state_transition()
        )

        loaded = self._load_image(
            self.goodbye_image_path
        )

        if not loaded:

            print(
                "[AVATAR ERROR] "
                "Unable to activate GOODBYE state."
            )

            return False

        self.current_state = "goodbye"

        self._goodbye_generation = (
            generation
        )

        self.state_changed.emit(
            "goodbye"
        )

        print(
            "[AVATAR] GOODBYE state active."
        )

        print(
            "[AVATAR] GOODBYE image displayed."
        )

        print(
            "[AVATAR] GOODBYE will remain visible "
            "for "
            f"{self.GOODBYE_DISPLAY_INTERVAL / 1000:.0f} seconds."
        )

        # Start only AFTER the goodbye image has been
        # successfully displayed.
        self.goodbye_timer.start()

        return True

    def _finish_goodbye(self):
        """
        Finish the goodbye presentation.

        Do NOT return to idle.

        Emit goodbye_finished so MainWindow can continue
        the actual shutdown.
        """

        if self.current_state != "goodbye":

            return

        if (
            self._goodbye_generation
            != self._state_generation
        ):

            return

        print(
            "[AVATAR] GOODBYE completed."
        )

        print(
            "[AVATAR] Emitting goodbye_finished."
        )

        self.goodbye_finished.emit()

    # ========================================================
    # IDLE
    # ========================================================

    def _start_idle(self):
        """
        Start the idle avatar flow.

        First:

            idle_primary.png

        Then every IDLE_CHANGE_INTERVAL:

            random idle image
        """

        self._begin_state_transition()

        loaded = self._load_image(
            self.idle_primary_path
        )

        if not loaded:

            return False

        self.current_state = "idle"

        self.state_changed.emit(
            "idle"
        )

        print(
            "[AVATAR] IDLE PRIMARY active."
        )

        print(
            "[AVATAR] Image will switch every "
            f"{self.IDLE_CHANGE_INTERVAL / 1000:.0f} seconds."
        )

        # Keep idle_primary visible first.
        self.idle_timer.start()

        return True

    # ========================================================
    # RANDOM IDLE
    # ========================================================

    def _get_random_idle_image(self):
        """
        Return a random cached idle image.

        Prevent immediate repetition when more than one
        idle image is available.
        """

        available_images = [

            image_path

            for image_path
            in self.idle_image_paths

            if image_path
            in self.image_cache

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

        if (
            len(available_images) > 1
            and self.current_image_path
            == random_image
        ):

            other_images = [

                image_path

                for image_path
                in available_images

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
        Change idle image only while the avatar is actually
        in the idle state.
        """

        if self.current_state != "idle":

            self._stop_idle_timer()

            print(
                "[AVATAR] Idle timer stopped because "
                "current state is: "
                f"{self.current_state}"
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
        """
        Set avatar state.

        Supported states:

            hello
            idle
            listening
            thinking_laptop
            thinking_ai
            speaking
            success
            error
            goodbye
        """

        requested_state = (
            state or ""
        ).strip().lower()

        if not requested_state:

            return

        print(
            "[AVATAR] Requested state: "
            f"{requested_state}"
        )

        # ----------------------------------------------------
        # Avoid unnecessary permanent-state reloads.
        #
        # Temporary states are intentionally allowed to
        # restart their timers.
        # ----------------------------------------------------

        if (
            requested_state
            == self.current_state
            and
            requested_state not in {
                "success",
                "error",
                "goodbye",
            }
        ):

            return

        state_handlers = {

            "hello":
                self._load_hello,

            "idle":
                self._start_idle,

            "listening":
                self._load_listening,

            "thinking_laptop":
                self._load_thinking_laptop,

            "thinking_ai":
                self._load_thinking_ai,

            "speaking":
                self._load_speaking,

            "success":
                self._load_success,

            "error":
                self._load_error,

            "goodbye":
                self._load_goodbye,

        }

        handler = state_handlers.get(
            requested_state
        )

        if handler is None:

            print(
                "[AVATAR] State "
                f"'{requested_state}' "
                "is not implemented. "
                "Keeping current avatar image."
            )

            return

        # ----------------------------------------------------
        # Do not restart an already active idle slideshow.
        # ----------------------------------------------------

        if (
            requested_state == "idle"
            and
            self.current_state == "idle"
            and
            self.idle_timer.isActive()
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

        self.set_state(
            state
        )

    def set_listening(
        self,
        listening: bool,
    ):

        if listening:

            self.set_state(
                "listening"
            )

        else:

            self.set_state(
                "idle"
            )

    def set_thinking_laptop(self):

        self.set_state(
            "thinking_laptop"
        )

    def set_thinking_ai(self):

        self.set_state(
            "thinking_ai"
        )

    def set_speaking(self):

        self.set_state(
            "speaking"
        )

    def set_success(self):

        self.set_state(
            "success"
        )

    def set_error(self):

        self.set_state(
            "error"
        )

    def set_idle(self):

        self.set_state(
            "idle"
        )

    def set_goodbye(self):
        """
        Activate goodbye state.

        MainWindow must connect:

            avatar.goodbye_finished

        to the final application shutdown logic.
        """

        self.set_state(
            "goodbye"
        )

    # ========================================================
    # STATE QUERY
    # ========================================================

    def current_avatar_state(self):

        return self.current_state

    # ========================================================
    # GOODBYE STATUS
    # ========================================================

    def is_goodbye_active(self):
        """
        Return True when goodbye presentation is active.
        """

        return (
            self.current_state
            == "goodbye"
        )

    # ========================================================
    # STOP / CLEANUP
    # ========================================================

    def stop(self):
        """
        Stop all avatar timers.

        Does not change the current avatar image/state.
        """

        self._state_generation += 1

        self._success_generation = None

        self._error_generation = None

        self._goodbye_generation = None

        self._stop_all_timers()

        print(
            "[AVATAR] Avatar timers stopped."
        )

    # ========================================================
    # CLOSE EVENT
    # ========================================================

    def closeEvent(
        self,
        event,
    ):
        """
        Stop avatar timers when the avatar widget itself
        is destroyed.
        """

        self.stop()

        super().closeEvent(
            event
        )