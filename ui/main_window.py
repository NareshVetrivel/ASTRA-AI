import os
import re

from PySide6.QtCore import (
    Qt,
    QCoreApplication,
    QThread,
    Signal,
    Slot,
    QTimer,
    QPropertyAnimation,
    QEasingCurve,
    QPoint,
)

from PySide6.QtGui import (
    QColor,
    QFont,
    QIcon,
)

from PySide6.QtWidgets import (
    QApplication,
    QGraphicsDropShadowEffect,
    QGraphicsOpacityEffect,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QProgressBar,
    QVBoxLayout,
    QWidget,
)

from config import settings

from ui.styles.theme import Theme

from ui.components.header import HeaderWidget
from ui.components.left_panel import LeftPanelWidget
from ui.components.center_panel import CenterPanelWidget
from ui.components.right_panel import RightPanelWidget
from ui.widgets.conversation_panel import ConversationPanel

from ui.widgets.background_widget import BackgroundWidget
from ui.widgets.mic_widget import MicWidget
from ui.widgets.file_selection_panel import FileSelectionPanel

from voice.whisper_recognizer import WhisperRecognizer
from voice.text_to_speech import TextToSpeech

from planner.intent_detector import IntentDetector
from planner.entity_extractor import EntityExtractor
from planner.text_extractor import TextExtractor
from planner.command_normalizer import CommandNormalizer
from planner.command_dispatcher import CommandDispatcher
from ai.gemini_client import GeminiClient
from planner.multi_command_planner import MultiCommandPlanner
from planner.multi_command_executor import MultiCommandExecutor

from automation.keyboard_controller import KeyboardController
from automation.mouse_controller import MouseController
from automation.window_controller import WindowController
from automation.system_controller import SystemController
from automation.app_launcher import AppLauncher
from automation.app_closer import AppCloser
from automation.file_finder import FileFinder
from automation.folder_manager import FolderManager
from automation.file_manager import FileManager
from automation.browser_controller import BrowserController

from workers.initialization_worker import InitializationWorker


# =====================================================
# Voice Worker
# =====================================================

class VoiceWorker(QThread):

    command_ready = Signal(str)

    finished = Signal()

    audio_level = Signal(float)

    def __init__(
        self,
        recognizer,
        tts,
        wake_word_mode=False
    ):

        super().__init__()

        self.recognizer = recognizer

        self._stop = False

        self.tts = tts

        self.wake_word_mode = wake_word_mode

        self.recognizer.level_callback = (
            self.audio_level.emit
        )

    def run(self):

        try:

            if (
                self._stop
                or self.isInterruptionRequested()
            ):

                return

            # ---------------------------------
            # DHEEPTHI Wake Word Mode
            # ---------------------------------

            if self.wake_word_mode:

                print(
                    "\n========== DHEEPTHI =========="
                )

                print(
                    "DHEEPTHI is waiting for wake word..."
                )

                command = (
                    self.recognizer.listen_for_wake_command(
                        retries=1
                    )
                )

            # ---------------------------------
            # Manual Microphone Mode
            # ---------------------------------

            else:

                # IMPORTANT:
                # Do not speak while the microphone is active.
                # Speaking here causes Whisper to capture ASTRA's
                # own voice and can trigger feedback / false commands.

                self.msleep(180)

                if (
                    self._stop
                    or self.isInterruptionRequested()
                ):

                    return

                command = self.recognizer.listen(
                    retries=2
                )

            # ---------------------------------
            # Stop Check
            # ---------------------------------

            if (
                self._stop
                or self.isInterruptionRequested()
            ):

                return

            # ---------------------------------
            # Command Ready
            # ---------------------------------

            if command:

                print(
                    f"Command Ready : {command}"
                )

                self.command_ready.emit(
                    command
                )

        finally:

            self.finished.emit()

    def stop(self):
        """
        Request the voice worker to stop safely.

        The recognizer is asked to stop first so that
        any active wake-word/audio operation can return.
        """

        self._stop = True

        self.requestInterruption()

        # ---------------------------------
        # Stop recognizer operations
        # ---------------------------------

        try:

            self.recognizer.stop_wake_word()

        except Exception as error:

            print(
                f"Recognizer Wake Stop Error : {error}"
            )

        try:

            self.recognizer.stop_audio_meter()

        except Exception as error:

            print(
                f"Recognizer Meter Stop Error : {error}"
            )

# =====================================================
# Main Window
# =====================================================

class MainWindow(QMainWindow):
    """
    ASTRA-AI Main Window
    """

    def __init__(self):

        super().__init__()

        self._closing = False

        # ----------------------------------
        # Backend
        # ----------------------------------

        self.recognizer = None

        self.tts = None

        self.intent_detector = None

        self.entity_extractor = None

        self.text_extractor = None

        self.command_normalizer = None

        self.dispatcher = None

        self.multi_command_planner = None

        self.multi_command_executor = None

        self.app_launcher = None

        self.app_closer = None

        self.keyboard_controller = None

        self.mouse_controller = None

        self.window_controller = None

        self.system_controller = None

        self.file_finder = None

        self.folder_manager = None

        self.file_manager = None

        self.browser_controller = None

        self.gemini = None

        # ----------------------------------
        # Runtime
        # ----------------------------------

        self.last_application = None

        self.typing_mode = False

        self.loading_finished = False

        self.voice_worker = None
        self.worker = None

        # ----------------------------------
        # Voice Worker State
        # ----------------------------------

        self.current_voice_mode = None

        # "wake"   -> DHEEPTHI standby listener
        # "manual" -> microphone button listener

        self.manual_listening_requested = False

        # ----------------------------------
        # DHEEPTHI Wake Word Mode
        # ----------------------------------

        self.wake_word_enabled = True

        self.wake_word_running = False

        # Prevent multiple mic clicks
        self.processing_voice = False

        # ----------------------------------
        # Pending File Selection
        # ----------------------------------
        # When a file operation matches multiple files, the
        # dispatcher returns candidates instead of selecting
        # the first match. MainWindow keeps the original
        # command here and applies the user's numeric choice
        # to that exact operation.
        self._pending_file_selection = None

        self._file_selection_candidates = []

        self._file_selection_operation = None

        self._loading_overlay_deleted = False

        # ----------------------------------
        # Conversation Panel
        # ----------------------------------

        self.conversation_panel = None

        self.conversation_panel_open = False

        # Lightweight position animation.
        # Only the panel position is animated instead of
        # continuously animating the complete QRect geometry.
        self.conversation_animation = None

        # Prevent repeated clicks while the panel is moving.
        self.conversation_animating = False

        # Used to know whether the current animation is opening
        # or closing the conversation panel.
        self.conversation_animation_mode = None

        self.conversation_overlay_effect = None

        # ----------------------------------
        # Pending Confirmation
        # ----------------------------------
        # CommandDispatcher returns a non-blocking confirmation
        # request. MainWindow owns the microphone confirmation flow.
        self._pending_confirmation = None

        # ----------------------------------
        # Window
        # ----------------------------------

        self.setWindowTitle("ASTRA-AI")

        icon_path = os.path.abspath(
            "ui/assets/astra_logo.png"
        )

        if os.path.exists(icon_path):

            icon = QIcon(icon_path)

            self.setWindowIcon(icon)

            QApplication.instance().setWindowIcon(icon)

        self.resize(1600, 900)

        self.setMinimumSize(1400, 850)

        self.setStyleSheet(
            Theme.get_stylesheet()
        )

        # ----------------------------------
        # Build UI
        # ----------------------------------

        self.setup_ui()

    def setup_ui(self):
        """
        Build the main user interface.
        """

        # --------------------------------------------------
        # Background
        # --------------------------------------------------

        self.background = BackgroundWidget()

        self.setCentralWidget(
            self.background
        )

        # --------------------------------------------------
        # Transparent Content
        # --------------------------------------------------

        self.content = QWidget()

        self.content.setObjectName(
            "mainContent"
        )

        self.content.setStyleSheet("""

        QWidget#mainContent{

            background:transparent;

        }

        """)

        self.background.setContentWidget(
            self.content
        )

        # --------------------------------------------------
        # Root Layout
        # --------------------------------------------------

        self.root_layout = QVBoxLayout(
            self.content
        )

        self.root_layout.setContentsMargins(
            28,
            14,
            28,
            0
        )

        self.root_layout.setSpacing(0)

        # --------------------------------------------------
        # Header
        # --------------------------------------------------

        self.header_widget = HeaderWidget()

        # --------------------------------------------------
        # Conversation Button
        # --------------------------------------------------
        # Header-la irukkura existing right-side button
        # ippo application close button illa.
        #
        # It opens / closes the Conversation Panel.
        # --------------------------------------------------

        self.header_widget.set_conversation_callback(
            self.toggle_conversation_panel
        )

        self.root_layout.addWidget(
            self.header_widget
        )

        self.root_layout.addSpacing(26)

        # --------------------------------------------------
        # Body Layout
        # --------------------------------------------------

        self.body_layout = QHBoxLayout()

        self.body_layout.setContentsMargins(
            28,
            0,
            28,
            8
        )

        self.body_layout.setSpacing(26)

        # --------------------------------------------------
        # Left Panel
        # --------------------------------------------------

        self.left_panel = LeftPanelWidget()

        self.body_layout.addWidget(
            self.left_panel,
            0,
            Qt.AlignTop
        )

        # --------------------------------------------------
        # Center Panel
        # --------------------------------------------------

        self.center_container = QWidget()

        self.center_layout = QVBoxLayout(
            self.center_container
        )

        self.center_layout.setContentsMargins(
            0,
            0,
            0,
            0
        )

        self.center_layout.setSpacing(10)

        # --------------------------------------------------
        # File / Folder Selection Glass Panel
        # --------------------------------------------------
        # IMPORTANT:
        # Do NOT add this panel to center_layout.
        #
        # It is positioned manually above the microphone so it
        # does not push the microphone/halo/avatar downward.
        # --------------------------------------------------

        self.file_selection_panel = FileSelectionPanel(
            self.center_container
        )

        self.file_selection_panel.hide()

        self.file_selection_panel.selection_requested.connect(
            self._on_file_selection_clicked
        )

        self.file_selection_panel.cancelled.connect(
            self._on_file_selection_cancelled
        )

        # --------------------------------------------------
        # Flexible Space
        # --------------------------------------------------

        self.center_layout.addStretch()

        # --------------------------------------------------
        # Microphone
        # --------------------------------------------------

        self.mic_widget = MicWidget()

        self.center_layout.addWidget(
            self.mic_widget,
            alignment=Qt.AlignBottom | Qt.AlignHCenter
        )

        self.center_layout.addSpacing(12)

        self.body_layout.addWidget(

            self.center_container,

            1

        )

        # --------------------------------------------------
        # Right Panel
        # --------------------------------------------------

        self.right_panel = RightPanelWidget()

        self.body_layout.addWidget(

            self.right_panel,

            0,

            Qt.AlignTop

        )

        # --------------------------------------------------
        # Conversation Panel
        # --------------------------------------------------
        # The panel is created once and reused.
        # It does NOT participate in body_layout.
        #
        # This is important because the panel must slide
        # independently from the main UI.
        # --------------------------------------------------

        self.conversation_panel = ConversationPanel(
            self
        )

        # Conversation header button -> open / close
        self.conversation_panel.close_requested.connect(
            self.close_conversation_panel
        )

        self.conversation_panel.hide()

        self.conversation_panel_open = False

        self.root_layout.addLayout(

            self.body_layout,

            1

        )

        # --------------------------------------------------
        # Dummy References
        # --------------------------------------------------

        self.status_label = QLabel()

        self.status_label.setText(
            "Status : Ready"
        )

        self.conversation_label = QLabel()

        self.microphone_button = self.mic_widget.button()

        self.microphone_button.clicked.connect(

            self.start_listening

        )

        # --------------------------------------------------
        # Loading Overlay
        # --------------------------------------------------

        self.loading_overlay = QWidget(self)

        self.loading_overlay.setStyleSheet("""

        QWidget{

            background-color: rgb(247,242,255);

        }

        """)

        self.loading_overlay.setGeometry(self.rect())

        self.loading_overlay.raise_()

        self.loading_overlay.show()

        # --------------------------------------------------
        # Overlay Layout
        # --------------------------------------------------

        overlay_layout = QVBoxLayout(
            self.loading_overlay
        )

        overlay_layout.setAlignment(
            Qt.AlignCenter
        )

        overlay_layout.setSpacing(18)

        # --------------------------------------------------
        # Logo
        # --------------------------------------------------

        self.loading_logo = QLabel()

        icon = QApplication.windowIcon()

        pixmap = icon.pixmap(180, 180)

        self.loading_logo.setPixmap(pixmap)

        self.loading_logo.setAlignment(
            Qt.AlignCenter
        )

        glow = QGraphicsDropShadowEffect()

        glow.setBlurRadius(80)

        glow.setOffset(0)

        glow.setColor(
            QColor(124,58,237,180)
        )

        self.loading_logo.setGraphicsEffect(
            glow
        )

        overlay_layout.addWidget(
            self.loading_logo,
            alignment=Qt.AlignCenter
        )

        # --------------------------------------------------
        # Percentage
        # --------------------------------------------------

        self.loading_percent = QLabel(
            "0%"
        )

        self.loading_percent.setAlignment(
            Qt.AlignCenter
        )

        self.loading_percent.setFont(
            QFont(
                "Segoe UI",
                24,
                QFont.Bold
            )
        )

        self.loading_percent.setStyleSheet("""

        color:#6A40FF;

        background:transparent;

        """)

        overlay_layout.addWidget(
            self.loading_percent
        )

        # --------------------------------------------------
        # Progress Bar
        # --------------------------------------------------

        self.loading_bar = QProgressBar()

        self.loading_bar.setRange(
            0,
            100
        )

        self.loading_bar.setValue(0)

        self.loading_bar.setFixedWidth(420)

        self.loading_bar.setFixedHeight(10)

        self.loading_bar.setTextVisible(False)

        self.loading_bar.setStyleSheet("""

        QProgressBar{

            border:none;

            border-radius:5px;

            background:#E5E7EB;

        }

        QProgressBar::chunk{

            border-radius:5px;

            background:#7C3AED;

        }

        """)

        overlay_layout.addWidget(
            self.loading_bar,
            alignment=Qt.AlignCenter
        )

        # --------------------------------------------------
        # Status
        # --------------------------------------------------

        self.loading_status = QLabel(
            "Starting ASTRA..."
        )

        self.loading_status.setAlignment(
            Qt.AlignCenter
        )

        self.loading_status.setFont(
            QFont(
                "Segoe UI",
                11
            )
        )

        self.loading_status.setStyleSheet("""

        color:#666;

        background:transparent;

        """)

        overlay_layout.addWidget(
            self.loading_status
        )

        # --------------------------------------------------
        # Overlay Opacity
        # (Used only while closing overlay)
        # --------------------------------------------------

        self.overlay_opacity = QGraphicsOpacityEffect()

        self.loading_overlay.setGraphicsEffect(
            self.overlay_opacity
        )

        self.overlay_opacity.setOpacity(1.0)

        # --------------------------------------------------
        # Disable Mic Until Initialization Completes
        # --------------------------------------------------

        self.microphone_button.setEnabled(False)

        # --------------------------------------------------
        # Initial UI State
        # --------------------------------------------------

        try:

            self.left_panel.set_listening(
                "Offline"
            )

            self.left_panel.set_thinking(
                "Initializing"
            )

            self.left_panel.set_speaking(
                "Silent"
            )

        except Exception:

            pass

        # --------------------------------------------------
        # Initial Conversation
        # --------------------------------------------------

        self.conversation_label.setText(

            "Initializing ASTRA-AI..."

        )

        # --------------------------------------------------
        # Force Initial Paint
        # --------------------------------------------------

        self.setUpdatesEnabled(True)

        self.update()

        QApplication.processEvents()

    # --------------------------------------------------
    # Create Backend
    # --------------------------------------------------

    def create_backend(self):
        """
        Create all backend modules.
        """

        print("\n========== BACKEND ==========")

        # ------------------------------------------
        # Speech Recognition
        # ------------------------------------------

        self.recognizer = WhisperRecognizer()

        print("Whisper Recognizer Created.")

        # Whisper model will be loaded inside
        # InitializationWorker.

        # ------------------------------------------
        # Voice
        # ------------------------------------------

        self.tts = TextToSpeech()

        # ------------------------------------------
        # NLP
        # ------------------------------------------

        self.intent_detector = IntentDetector()

        self.entity_extractor = EntityExtractor()

        self.text_extractor = TextExtractor()

        # ------------------------------------------
        # Command Normalization
        # ------------------------------------------

        self.command_normalizer = CommandNormalizer()

        # ------------------------------------------
        # Automation Modules
        # ------------------------------------------

        self.app_launcher = AppLauncher()

        self.app_closer = AppCloser()

        self.keyboard_controller = KeyboardController()

        self.mouse_controller = MouseController()

        self.window_controller = WindowController()

        self.system_controller = SystemController()

        self.file_finder = FileFinder()

        self.folder_manager = FolderManager()

        self.file_manager = FileManager(
            whisper=self.recognizer
        )

        self.browser_controller = BrowserController()

        # ------------------------------------------
        # Gemini AI
        # ------------------------------------------

        self.gemini = GeminiClient()

        # ------------------------------------------
        # Multi-Command Planning
        # ------------------------------------------

        self.multi_command_planner = MultiCommandPlanner(
            gemini_client=self.gemini
        )

        # ------------------------------------------
        # Dispatcher
        # ------------------------------------------

        self.dispatcher = CommandDispatcher(

            tts=self.tts,

            app_launcher=self.app_launcher,

            app_closer=self.app_closer,

            keyboard_controller=self.keyboard_controller,

            mouse_controller=self.mouse_controller,

            window_controller=self.window_controller,

            system_controller=self.system_controller,

            file_finder=self.file_finder,

            folder_manager=self.folder_manager,

            file_manager=self.file_manager,

            browser_controller=self.browser_controller,

            whisper=self.recognizer,

            gemini_client=self.gemini

        )

        # ------------------------------------------
        # Multi-Command Executor
        # ------------------------------------------

        self.multi_command_executor = MultiCommandExecutor(
            dispatcher=self.dispatcher
        )

        print("Backend Ready.")

        print("=============================\n")

    # --------------------------------------------------
    # Speech Completion / Non-Blocking UI Helpers
    # --------------------------------------------------

    def _unlock_after_speech(
        self,
        restart_wake=True
    ):
        """
        Keep the microphone locked while ASTRA is speaking,
        without blocking the Qt GUI thread.

        This replaces blocking calls to
        ``tts.wait_until_done()`` inside the UI thread.
        """

        def check_speech():

            if self._closing:
                return

            try:
                speaking = (
                    self.tts is not None
                    and self.tts.speaking()
                )
            except Exception:
                speaking = False

            if speaking:
                QTimer.singleShot(
                    60,
                    check_speech
                )
                return

            self.unlock_microphone()

            try:
                self.left_panel.set_speaking(
                    "Silent"
                )
            except Exception:
                pass

            if (
                restart_wake
                and self.wake_word_enabled
                and not self.manual_listening_requested
                and not self._pending_file_selection
            ):
                QTimer.singleShot(
                    350,
                    self.start_wake_word_worker
                )

        # Give the TTS worker a moment to start before polling.
        QTimer.singleShot(
            120,
            check_speech
        )

    def _extract_selection_number(
        self,
        text
    ):
        """
        Extract a numeric file-selection answer.

        Accepts:
            1
            2.
            number 2
            option 2
            choose 2
            select number 2
        """

        if text is None:
            return None

        cleaned = str(text).strip().lower()

        match = re.search(
            r"\b(?:number|option|choice|select|choose)\s*(\d+)\b",
            cleaned
        )

        if match:
            return int(match.group(1))

        match = re.fullmatch(
            r"(?:the\s+)?(\d+)[\s\.!?]*",
            cleaned
        )

        if match:
            return int(match.group(1))

        # Whisper may return a spoken number.
        spoken_numbers = {
            "zero": 0,
            "one": 1,
            "two": 2,
            "three": 3,
            "four": 4,
            "five": 5,
            "six": 6,
            "seven": 7,
            "eight": 8,
            "nine": 9,
            "ten": 10,
        }

        for word, number in spoken_numbers.items():

            if re.search(
                rf"\b{word}\b",
                cleaned
            ):
                return number

        return None

    def _wait_for_speech_then_start_selection(
        self
    ):
        """
        Start the numeric selection listener only after ASTRA
        has completely stopped speaking.
        """

        if not self._pending_file_selection:
            return

        def check():

            if not self._pending_file_selection:
                return

            if self.tts is not None:

                try:
                    if self.tts.speaking():
                        QTimer.singleShot(
                            80,
                            check
                        )
                        return
                except Exception:
                    pass

            self.status_label.setText(
                "Status : Waiting for File Selection"
            )

            try:
                self.left_panel.set_listening(
                    "Select File Number"
                )

                self.left_panel.set_thinking(
                    "Waiting for Selection"
                )

                self.left_panel.set_speaking(
                    "Silent"
                )

                self.mic_widget.show_listening()

                self.mic_widget.set_listening(
                    True
                )

            except Exception:
                pass

            self.manual_listening_requested = True

            # --------------------------------------------------
            # Lock microphone while ASTRA is preparing the
            # selection listener.
            # --------------------------------------------------

            self.lock_microphone()

            QTimer.singleShot(
                180,
                lambda: self._start_file_selection_listener()
            )

        QTimer.singleShot(
            120,
            check
        )

    def _start_file_selection_listener(self):
        """
        Start microphone listening specifically for a pending
        file-selection number.

        This method is called only after ASTRA has stopped speaking.
        """

        if self._closing:
            return

        if not self._pending_file_selection:
            return

        # --------------------------------------------------
        # Safety: never start another worker if one is alive.
        # --------------------------------------------------

        if self.voice_worker is not None:

            try:

                if self.voice_worker.isRunning():
                    return

            except Exception:
                pass

        self.status_label.setText(
            "Status : Listening for File Selection"
        )

        try:

            self.left_panel.set_listening(
                "Listening for Number"
            )

            self.left_panel.set_thinking(
                "Waiting for Selection"
            )

            self.left_panel.set_speaking(
                "Silent"
            )

            self.mic_widget.show_listening()

            self.mic_widget.set_listening(
                True
            )

        except Exception:
            pass

        # --------------------------------------------------
        # Start manual listener.
        # --------------------------------------------------

        self.start_voice_worker(
            wake_word_mode=False
        )

    def _handle_pending_file_selection(
        self,
        text
    ):
        """
        Handle the numeric selection for a pending file operation.

        The original dispatcher payload is preserved so that the
        selected number resumes the exact same operation instead of
        sending the number back through intent detection.
        """

        pending = self._pending_file_selection

        if not pending:
            return False

        selection = self._extract_selection_number(
            text
        )

        candidates = pending.get(
            "candidates",
            []
        )

        # --------------------------------------------------
        # No candidates
        # --------------------------------------------------

        if not candidates:

            self._pending_file_selection = None

            self.clear_file_selection()

            message = (
                "The file selection list is no longer available. "
                "Please repeat the command."
            )

            self.mic_widget.update_ai_message(
                message
            )

            self.status_label.setText(
                "Status : File Selection Expired"
            )

            try:

                self.tts.speak(
                    message
                )

            except Exception:
                pass

            self._unlock_after_speech(
                restart_wake=True
            )

            return True

        # --------------------------------------------------
        # Invalid / unclear selection
        # --------------------------------------------------

        if selection is None:

            message = (
                "Please say the number of the file "
                "you want to select."
            )

            self.mic_widget.update_ai_message(
                message
            )

            self.status_label.setText(
                "Status : Waiting for File Selection"
            )

            try:

                self.left_panel.set_listening(
                    "Waiting for Number"
                )

                self.left_panel.set_thinking(
                    "Select File"
                )

                self.left_panel.set_speaking(
                    "Speaking"
                )

            except Exception:
                pass

            try:

                self.tts.speak(
                    message
                )

            except Exception:
                pass

            self._wait_for_speech_then_start_selection()

            return True

        # --------------------------------------------------
        # Range validation
        # --------------------------------------------------

        if not (
            1 <= selection <= len(candidates)
        ):

            message = (
                f"That selection is invalid. "
                f"Please choose a number between "
                f"1 and {len(candidates)}."
            )

            self.mic_widget.update_ai_message(
                message
            )

            self.status_label.setText(
                "Status : Invalid File Selection"
            )

            try:

                self.tts.speak(
                    message
                )

            except Exception:
                pass

            self._wait_for_speech_then_start_selection()

            return True

        # --------------------------------------------------
        # Preserve the COMPLETE dispatcher payload
        # --------------------------------------------------

        pending_command = dict(
            pending
        )

        # --------------------------------------------------
        # Consume pending state BEFORE dispatching.
        # This prevents duplicate microphone events from
        # executing the same selection twice.
        # --------------------------------------------------

        self._pending_file_selection = None

        self.clear_file_selection()

        # --------------------------------------------------
        # Selected candidate
        # --------------------------------------------------

        selected_candidate = candidates[
            selection - 1
        ]

        if isinstance(
            selected_candidate,
            dict
        ):

            selected_name = (
                selected_candidate.get(
                    "name"
                )
                or selected_candidate.get(
                    "filename"
                )
                or "file"
            )

            selected_path = (
                selected_candidate.get(
                    "path"
                )
                or ""
            )

        else:

            selected_name = str(
                selected_candidate
            )

            selected_path = ""

        # --------------------------------------------------
        # UI
        # --------------------------------------------------

        self.status_label.setText(
            "Status : Executing Selected File"
        )

        self.mic_widget.update_ai_message(
            f"Selected option {selection}. Executing..."
        )

        self.conversation_label.setText(
            f"Selected File\n\n"
            f"{selection}. {selected_name}"
            + (
                f"\n\nLocation:\n{selected_path}"
                if selected_path
                else ""
            )
        )

        try:

            self.left_panel.set_listening(
                "Idle"
            )

            self.left_panel.set_thinking(
                "Executing"
            )

            self.left_panel.set_speaking(
                "Silent"
            )

        except Exception:
            pass

        # --------------------------------------------------
        # Resume ORIGINAL dispatcher command
        # --------------------------------------------------

        payload = pending_command.get(
            "payload"
        )

        if isinstance(
            payload,
            dict
        ):

            payload = dict(
                payload
            )

        else:

            # Backward-compatible fallback for old pending
            # structures already stored by MainWindow.
            payload = {
                "intent": pending_command.get(
                    "intent"
                ),
                "entity": pending_command.get(
                    "entity"
                ),
                "typed_text": pending_command.get(
                    "typed_text"
                ),
                "browser": pending_command.get(
                    "browser"
                ),
                "website": pending_command.get(
                    "website"
                ),
                "search_query": pending_command.get(
                    "search_query"
                ),
                "profile": pending_command.get(
                    "profile"
                ),
                "user_text": pending_command.get(
                    "user_text"
                ),
                "multi_command": pending_command.get(
                    "multi_command",
                    False
                ),
            }

        try:

            result = self.dispatcher.dispatch(

                intent=payload.get(
                    "intent"
                ),

                entity=payload.get(
                    "entity"
                ),

                typed_text=payload.get(
                    "typed_text"
                ),

                browser=payload.get(
                    "browser"
                ),

                website=payload.get(
                    "website"
                ),

                search_query=payload.get(
                    "search_query"
                ),

                profile=payload.get(
                    "profile"
                ),

                user_text=payload.get(
                    "user_text"
                ),

                multi_command=payload.get(
                    "multi_command",
                    False
                ),

                selection=selection

            )

        except Exception as error:

            print(
                f"Selected File Dispatch Error : {error}"
            )

            result = {
                "success": False,
                "status": "Status : File Selection Failed",
                "message": (
                    "I could not complete the selected "
                    "file operation."
                )
            }

        # --------------------------------------------------
        # Use ONE result handler only
        # --------------------------------------------------

        self._handle_dispatch_result(

            result,

            payload.get(
                "user_text",
                str(text)
            ),

            payload.get(
                "intent"
            ),

            payload.get(
                "entity"
            ),

        )

        return True

    def _finish_dispatch_result(
        self,
        result,
        text,
        intent=None,
        entity=None
    ):
        """
        Backward-compatible wrapper.

        All dispatcher results now use one centralized result
        handler so file selection and confirmation state cannot
        diverge between two different flows.
        """

        self._handle_dispatch_result(
            result,
            text,
            intent,
            entity,
        )

    # --------------------------------------------------
    # Confirmation Helpers
    # --------------------------------------------------

    def _parse_confirmation(self, text):
        """
        Parse a YES/NO confirmation answer.

        Returns:
            True  -> explicit yes
            False -> explicit no
            None  -> unclear answer
        """

        if text is None:
            return None

        cleaned = re.sub(
            r"[^a-z0-9\s]",
            " ",
            str(text).strip().lower()
        )

        cleaned = re.sub(
            r"\s+",
            " ",
            cleaned
        )

        yes_patterns = (
            "yes",
            "yeah",
            "yep",
            "yup",
            "sure",
            "okay",
            "ok",
            "confirm",
            "confirmed",
            "do it",
            "go ahead",
            "proceed",
            "continue",
            "please do",
            "affirmative",
        )

        no_patterns = (
            "no",
            "nope",
            "nah",
            "cancel",
            "cancel it",
            "stop",
            "dont",
            "do not",
            "negative",
            "abort",
        )

        if cleaned in yes_patterns:
            return True

        if cleaned in no_patterns:
            return False

        # Whisper often returns a short phrase such as
        # "yes please" or "no please".
        yes_prefixes = (
            "yes ",
            "yeah ",
            "yep ",
            "sure ",
            "okay ",
            "ok ",
            "confirm ",
            "go ahead ",
            "please do ",
        )

        no_prefixes = (
            "no ",
            "nope ",
            "cancel ",
            "stop ",
            "dont ",
            "do not ",
        )

        if cleaned.startswith(yes_prefixes):
            return True

        if cleaned.startswith(no_prefixes):
            return False

        return None

    def _start_confirmation_listener_after_prompt(self):
        """
        Start the microphone only after the confirmation prompt
        has completely finished speaking.
        """

        if self._closing:
            return

        if not self._pending_confirmation:
            return

        if self.voice_worker is not None:
            try:
                if self.voice_worker.isRunning():
                    return
            except Exception:
                pass

        self.manual_listening_requested = True

        self.status_label.setText(
            "Status : Waiting for Confirmation"
        )

        try:
            self.mic_widget.show_listening()
            self.mic_widget.set_listening(True)

            self.left_panel.set_listening(
                "Say Yes or No"
            )
            self.left_panel.set_thinking(
                "Waiting for Confirmation"
            )
            self.left_panel.set_speaking(
                "Silent"
            )
        except Exception:
            pass

        QApplication.processEvents()

        QTimer.singleShot(
            80,
            lambda: self.start_voice_worker(
                wake_word_mode=False
            )
        )

    def _wait_for_confirmation_prompt(self):
        """
        Wait asynchronously until ASTRA finishes the confirmation
        prompt. The Qt GUI thread is never blocked.
        """

        if self._closing:
            return

        if not self._pending_confirmation:
            return

        try:
            speaking = (
                self.tts is not None
                and self.tts.speaking()
            )
        except Exception:
            speaking = False

        if speaking:
            QTimer.singleShot(
                60,
                self._wait_for_confirmation_prompt
            )
            return

        self._start_confirmation_listener_after_prompt()

    def _begin_confirmation_flow(self, result):
        """
        Store the dispatcher confirmation payload and ask the user
        for YES/NO through the existing voice worker.

        CommandDispatcher never listens for confirmation itself.
        """

        self._pending_confirmation = {
            "action": result.get(
                "confirmation_action",
                result.get("intent")
            ),
            "payload": result.get(
                "confirmation_payload",
                {}
            ),
            "message": result.get(
                "confirmation_message",
                result.get(
                    "message",
                    "Please confirm."
                )
            ),
        }

        self.manual_listening_requested = True
        self.lock_microphone()

        message = self._pending_confirmation["message"]

        self.status_label.setText(
            "Status : Confirmation Required"
        )

        self.mic_widget.update_ai_message(
            message
        )

        self.conversation_label.setText(
            f"Confirmation Required\n\n{message}\n\n"
            "Please say Yes or No."
        )

        try:
            self.left_panel.set_listening(
                "Waiting for Confirmation"
            )
            self.left_panel.set_thinking(
                "Confirmation Required"
            )
            self.left_panel.set_speaking(
                "Speaking"
            )
            self.mic_widget.show_listening()
            self.mic_widget.set_listening(False)
        except Exception:
            pass

        # The dispatcher did not speak this confirmation.
        # MainWindow owns TTS and waits asynchronously before
        # starting Whisper, preventing ASTRA from hearing itself.
        try:
            self.tts.speak(
                f"{message} Please say yes or no."
            )
        except Exception as error:
            print(
                f"Confirmation TTS Error : {error}"
            )

        QTimer.singleShot(
            100,
            self._wait_for_confirmation_prompt
        )

    def _cancel_pending_confirmation(self):
        """
        Cancel the pending operation without executing it.
        """

        self._pending_confirmation = None
        self.manual_listening_requested = False

        self.status_label.setText(
            "Status : Cancelled"
        )

        self.mic_widget.update_ai_message(
            "Operation cancelled."
        )

        self.conversation_label.setText(
            "Operation Cancelled"
        )

        try:
            self.left_panel.set_listening(
                "Idle"
            )
            self.left_panel.set_thinking(
                "Inactive"
            )
            self.left_panel.set_speaking(
                "Speaking"
            )
        except Exception:
            pass

        try:
            self.tts.speak(
                "Operation cancelled."
            )
        except Exception:
            pass

        self._unlock_after_speech(
            restart_wake=True
        )

    def _handle_confirmation_response(self, text):
        """
        Handle a YES/NO answer for the pending confirmation.

        Returns True when the input was consumed by the
        confirmation flow.
        """

        if not self._pending_confirmation:
            return False

        answer = self._parse_confirmation(text)

        # ---------------------------------
        # Unclear answer
        # ---------------------------------

        if answer is None:

            message = (
                "I did not understand. "
                "Please say yes or no."
            )

            self.mic_widget.update_ai_message(
                message
            )

            self.status_label.setText(
                "Status : Confirmation Required"
            )

            try:
                self.left_panel.set_listening(
                    "Waiting for Confirmation"
                )
                self.left_panel.set_thinking(
                    "Say Yes or No"
                )
                self.left_panel.set_speaking(
                    "Speaking"
                )
            except Exception:
                pass

            try:
                self.tts.speak(
                    message
                )
            except Exception:
                pass

            # Keep the pending confirmation and listen again
            # only after TTS has stopped.
            QTimer.singleShot(
                100,
                self._wait_for_confirmation_prompt
            )

            return True

        # ---------------------------------
        # NO
        # ---------------------------------

        if answer is False:

            self._cancel_pending_confirmation()

            return True

        # ---------------------------------
        # YES
        # ---------------------------------

        pending = self._pending_confirmation

        self._pending_confirmation = None
        self.manual_listening_requested = False

        self.status_label.setText(
            "Status : Executing Confirmed Action"
        )

        self.mic_widget.update_ai_message(
            "Confirmed. Executing..."
        )

        try:
            self.left_panel.set_listening(
                "Idle"
            )
            self.left_panel.set_thinking(
                "Executing"
            )
            self.left_panel.set_speaking(
                "Silent"
            )
        except Exception:
            pass

        payload = dict(
            pending.get(
                "payload",
                {}
            )
        )

        action = pending.get(
            "action"
        )

        try:

            result = self.dispatcher.execute_confirmed_action(
                action,
                payload
            )

        except Exception as error:

            print(
                f"Confirmed Action Error : {error}"
            )

            result = {
                "success": False,
                "status": "Status : Confirmation Execution Failed",
                "message": (
                    "I could not complete the confirmed action."
                ),
            }

        self._handle_dispatch_result(
            result,
            payload.get(
                "user_text",
                ""
            ),
            payload.get(
                "intent",
                action
            ),
            payload.get("entity"),
        )

        return True

    def _handle_dispatch_result(
        self,
        result,
        text,
        intent=None,
        entity=None,
    ):
        """
        Apply a CommandDispatcher result to the UI.

        This centralizes confirmation, multi-file selection,
        success, and failure handling so both normal commands and
        confirmed commands follow the same lifecycle.
        """

        result = result or {}

        # ---------------------------------
        # Confirmation Required
        # ---------------------------------

        if result.get(
            "requires_confirmation"
        ) or result.get(
            "confirmation_required"
        ):

            self._begin_confirmation_flow(
                result
            )

            return

        # ---------------------------------
        # File Selection Required
        # ---------------------------------

        if result.get(
            "requires_selection"
        ):

            candidates = result.get(
                "candidates",
                []
            )

            if not candidates:

                failure_message = (
                    "I could not find any selectable files."
                )

                self.mic_widget.update_ai_message(
                    failure_message
                )

                self.status_label.setText(
                    "Status : File Selection Failed"
                )

                try:

                    self.tts.speak(
                        failure_message
                    )

                except Exception:
                    pass

                self._unlock_after_speech(
                    restart_wake=True
                )

                return

            # ---------------------------------
            # IMPORTANT:
            # Preserve the exact payload created by
            # CommandDispatcher.
            # ---------------------------------

            pending_payload = result.get(
                "pending_payload"
            )

            if not isinstance(
                pending_payload,
                dict
            ):

                # Backward-compatible fallback
                pending_payload = {
                    "intent": intent,
                    "entity": entity,
                    "typed_text": result.get(
                        "typed_text"
                    ),
                    "browser": result.get(
                        "browser"
                    ),
                    "website": result.get(
                        "website"
                    ),
                    "search_query": result.get(
                        "search_query"
                    ),
                    "profile": result.get(
                        "profile"
                    ),
                    "user_text": text,
                    "multi_command": False,
                }

            else:

                pending_payload = dict(
                    pending_payload
                )

            # Make sure current command context exists.
            pending_payload.setdefault(
                "intent",
                intent
            )

            pending_payload.setdefault(
                "entity",
                entity
            )

            pending_payload.setdefault(
                "user_text",
                text
            )

            # ---------------------------------
            # Store selection state
            # ---------------------------------

            self._pending_file_selection = {

                "payload": pending_payload,

                "candidates": candidates,

                "operation": result.get(
                    "pending_action",
                    "file"
                ),

            }

            # ---------------------------------
            # Show candidates ONLY in UI.
            # Do not read the full paths through TTS.
            # ---------------------------------

            self.show_file_selection(

                candidates,

                operation=result.get(
                    "pending_action",
                    "file"
                )

            )

            # ---------------------------------
            # Short voice prompt
            # ---------------------------------

            message = (
                f"I found {len(candidates)} matching "
                f"{result.get('pending_action', 'file')}s. "
                "Please say the number you want."
            )

            self.mic_widget.update_ai_message(
                message
            )

            self.status_label.setText(
                "Status : Waiting for File Selection"
            )

            try:

                self.left_panel.set_listening(
                    "Waiting for File Number"
                )

                self.left_panel.set_thinking(
                    "Select a File"
                )

                self.left_panel.set_speaking(
                    "Speaking"
                )

            except Exception:
                pass

            # ---------------------------------
            # MainWindow owns TTS + microphone
            # lifecycle.
            # ---------------------------------

            try:

                self.tts.speak(
                    message
                )

            except Exception as error:

                print(
                    f"File Selection Prompt Error : {error}"
                )

            # Start microphone only AFTER TTS ends.
            self._wait_for_speech_then_start_selection()

            return

        # ---------------------------------
        # Success
        # ---------------------------------

        if result.get(
            "success",
            False
        ):

            reply = result.get(
                "message",
                result.get(
                    "status",
                    "Done."
                )
            )

            self.mic_widget.update_ai_message(
                reply
            )

            self.status_label.setText(
                result.get(
                    "status",
                    "Status : Completed"
                )
            )

            self.conversation_label.setText(
                f"Executed Successfully\n\n{text}"
            )

            if (
                intent == "launch_application"
                and entity
            ):

                self.last_application = entity

                if (
                    "notepad" in entity.lower()
                    or "word" in entity.lower()
                ):
                    self.typing_mode = True

            try:
                self.left_panel.set_listening(
                    "Idle"
                )
                self.left_panel.set_thinking(
                    "Inactive"
                )
                self.left_panel.set_speaking(
                    "Speaking"
                )
                self.right_panel.update_system_metrics()
            except Exception:
                pass

            # Dispatcher normally speaks successful replies itself.
            # Wait asynchronously instead of blocking the GUI.
            self._unlock_after_speech(
                restart_wake=True
            )

            QTimer.singleShot(
                1400,
                lambda: self.left_panel.set_speaking(
                    "Silent"
                )
            )

            return

        # ---------------------------------
        # Failed / Cancelled
        # ---------------------------------

        failure_reply = result.get(
            "message",
            "Sorry, I could not complete that request."
        )

        self.mic_widget.update_ai_message(
            failure_reply
        )

        self.status_label.setText(
            result.get(
                "status",
                "Status : No Action"
            )
        )

        self.conversation_label.setText(
            f"Command Failed\n\n{text}\n\n"
            f"{result.get('status', '')}"
        )

        try:
            self.left_panel.set_listening(
                "Idle"
            )
            self.left_panel.set_thinking(
                "Inactive"
            )
            self.left_panel.set_speaking(
                "Speaking"
            )
        except Exception:
            pass

        # Avoid speaking twice if the dispatcher already has TTS
        # running. If it is not speaking, provide the failure reply.
        try:
            if (
                self.tts is not None
                and not self.tts.speaking()
            ):
                self.tts.speak(
                    failure_reply
                )
        except Exception:
            pass

        self._unlock_after_speech(
            restart_wake=True
        )

        QTimer.singleShot(
            1400,
            lambda: self.left_panel.set_speaking(
                "Silent"
            )
        )

    # --------------------------------------------------
    # Process Command
    # --------------------------------------------------

    def process_command(
        self,
        text
    ):
        """
        Process the recognized voice command.

        Once a command is received, the microphone is
        immediately locked so the user cannot trigger
        another microphone action while ASTRA is processing.
        """

        # ------------------------------------------
        # Lock microphone immediately
        # ------------------------------------------

        self.lock_microphone()

        # ------------------------------------------
        # Pending YES/NO confirmation
        # ------------------------------------------
        # Confirmation answers must never go through intent
        # detection. The original command payload is stored in
        # _pending_confirmation and is executed only after YES.
        if self._pending_confirmation:

            if not text:
                return

            if self._handle_confirmation_response(
                text
            ):
                return

        # ------------------------------------------
        # Pending numeric file selection
        # ------------------------------------------
        # A selection answer must not go through intent
        # detection again. Otherwise "2" can be treated as
        # a new/unknown command and the original operation
        # starts over.
        if self._pending_file_selection:

            if not text:
                return

            if self._handle_pending_file_selection(
                text
            ):
                return

        # ------------------------------------------
        # Normalize text
        # ------------------------------------------

        if not text:

            self.unlock_microphone()

            return

        text = text.strip()

        if not text:

            self.unlock_microphone()

            return

        # ------------------------------------------
        # Command Normalization
        # ------------------------------------------

        original_text = text

        if self.command_normalizer:

            text = self.command_normalizer.normalize(
                text
            )

            if text != original_text:

                print(
                    "\n========== COMMAND NORMALIZER =========="
                )

                print(
                    f"Original   : {original_text}"
                )

                print(
                    f"Normalized : {text}"
                )

                print(
                    "========================================\n"
                )

        # ------------------------------------------
        # Normalization Result Check
        # ------------------------------------------

        if not text:

            self.unlock_microphone()

            return

        # ------------------------------------------
        # Reset Conversation
        # ------------------------------------------

        self.mic_widget.show_conversation(
            text,
            "Thinking..."
        )

        # ------------------------------------------
        # Thinking State
        # ------------------------------------------

        try:

            self.left_panel.set_listening(
                "Idle"
            )

            self.left_panel.set_thinking(
                "Thinking"
            )

            self.left_panel.set_speaking(
                "Silent"
            )

        except Exception:

            pass

        # ------------------------------------------
        # Multi-Command Detection
        # ------------------------------------------

        if (
            self.multi_command_planner
            and
            self.multi_command_executor
            and
            self.multi_command_planner.is_multi_command(
                text
            )
        ):

            print(
                "\n========== MULTI COMMAND =========="
            )

            print(
                f"Command : {text}"
            )

            try:

                self.status_label.setText(
                    "Status : Planning..."
                )

                self.mic_widget.update_ai_message(
                    "Planning your command..."
                )

                try:

                    self.left_panel.set_listening(
                        "Idle"
                    )

                    self.left_panel.set_thinking(
                        "Planning"
                    )

                    self.left_panel.set_speaking(
                        "Silent"
                    )

                except Exception:

                    pass

                # ----------------------------------
                # Create Action Plan
                # ----------------------------------

                plan = (
                    self.multi_command_planner
                    .create_plan(
                        text
                    )
                )

                print(
                    "\n---------- ACTION PLAN ----------"
                )

                print(
                    self.multi_command_planner
                    .plan_to_json(
                        plan
                    )
                )

                print(
                    "---------------------------------\n"
                )

                # ----------------------------------
                # Execute Action Plan
                # ----------------------------------

                self.status_label.setText(
                    "Status : Executing..."
                )

                result = (
                    self.multi_command_executor
                    .execute(
                        plan
                    )
                )

                print(
                    "\n---------- EXECUTION RESULT ----------"
                )

                print(
                    result
                )

                print(
                    "--------------------------------------\n"
                )

                # ----------------------------------
                # Success
                # ----------------------------------

                if result.get(
                    "success",
                    False
                ):

                    completed_steps = result.get(
                        "completed_steps",
                        0
                    )

                    total_steps = result.get(
                        "total_steps",
                        plan.total_steps
                    )

                    reply = (
                        f"Completed all "
                        f"{completed_steps} "
                        f"steps successfully."
                    )

                    self.mic_widget.update_ai_message(
                        reply
                    )

                    self.status_label.setText(
                        "Status : Multi-Command Completed"
                    )

                    self.conversation_label.setText(
                        f"Multi-Command Completed\n\n"
                        f"{text}\n\n"
                        f"Steps : "
                        f"{completed_steps}/{total_steps}"
                    )

                    try:

                        self.left_panel.set_listening(
                            "Idle"
                        )

                        self.left_panel.set_thinking(
                            "Inactive"
                        )

                        self.left_panel.set_speaking(
                            "Speaking"
                        )

                        self.right_panel.update_system_metrics()

                    except Exception:

                        pass

                    self.tts.speak(
                        reply
                    )

                    self._unlock_after_speech(
                        restart_wake=True
                    )

                    QTimer.singleShot(
                        1400,
                        lambda: (
                            self.left_panel
                            .set_speaking(
                                "Silent"
                            )
                        )
                    )

                    # _unlock_after_speech() owns microphone
                    # unlock + wake-word restart.

                    return

                # ----------------------------------
                # Multi-command Failed
                # ----------------------------------

                failed_step = result.get(
                    "failed_step"
                )

                if failed_step:

                    failed_action = failed_step.get(
                        "action",
                        "unknown action"
                    )

                    failure_message = (
                        f"I completed "
                        f"{result.get('completed_steps', 0)} "
                        f"step(s), but failed at "
                        f"{failed_action}."
                    )

                else:

                    failure_message = (
                        "I could not complete "
                        "the multi-step command."
                    )

                self.mic_widget.update_ai_message(
                    failure_message
                )

                self.status_label.setText(
                    "Status : Multi-Command Failed"
                )

                self.conversation_label.setText(
                    f"Multi-Command Failed\n\n"
                    f"{text}\n\n"
                    f"{result.get('status', '')}"
                )

                try:

                    self.left_panel.set_listening(
                        "Idle"
                    )

                    self.left_panel.set_thinking(
                        "Inactive"
                    )

                    self.left_panel.set_speaking(
                        "Speaking"
                    )

                except Exception:

                    pass

                self.tts.speak(
                    failure_message
                )

                self._unlock_after_speech(
                    restart_wake=True
                )

                QTimer.singleShot(
                    1400,
                    lambda: (
                        self.left_panel
                        .set_speaking(
                            "Silent"
                        )
                    )
                )

                return

            except Exception as error:

                print(
                    "\nMulti-Command Error :",
                    error
                )

                error_message = (
                    "I could not plan or "
                    "execute that multi-step command."
                )

                self.mic_widget.update_ai_message(
                    error_message
                )

                self.status_label.setText(
                    "Status : Multi-Command Error"
                )

                try:

                    self.left_panel.set_listening(
                        "Idle"
                    )

                    self.left_panel.set_thinking(
                        "Inactive"
                    )

                    self.left_panel.set_speaking(
                        "Speaking"
                    )

                except Exception:

                    pass

                self.tts.speak(
                    error_message
                )

                self._unlock_after_speech(
                    restart_wake=True
                )

                return

        # ------------------------------------------
        # Detect Intent
        # ------------------------------------------

        intent = self.intent_detector.detect_intent(
            text
        )

        # ------------------------------------------
        # Typing Mode
        # ------------------------------------------

        if (

            intent == "type_text"

            and

            self.typing_mode

        ):

            self.keyboard_controller.type_text(
                text
            )

            self.tts.speak(
                "Typed successfully."
            )

            self._unlock_after_speech(
                restart_wake=True
            )

            self.status_label.setText(
                "Status : Typed"
            )

            self.mic_widget.update_ai_message(
                "Typed successfully."
            )

            # ---------------------------------
            # Command completed
            # ---------------------------------
            # Keep the microphone locked until TTS finishes.
            # _unlock_after_speech() handles the unlock and
            # DHEEPTHI restart.

            try:

                self.left_panel.set_listening(
                    "Idle"
                )

                self.left_panel.set_thinking(
                    "Inactive"
                )

                self.left_panel.set_speaking(
                    "Silent"
                )

            except Exception:

                pass

            return

        # ------------------------------------------
        # Unknown Command
        # ------------------------------------------

        if intent == "ai_chat":

            self.lock_microphone()

            ai_reply = self.gemini.generate_response(
                text
            )

            self.mic_widget.update_ai_message(
                ai_reply
            )

            try:

                self.left_panel.set_thinking(
                    "Inactive"
                )

                self.left_panel.set_speaking(
                    "Speaking"
                )

            except Exception:

                pass

            self.tts.speak(
                ai_reply
            )

            self._unlock_after_speech(
                restart_wake=True
            )

            self.status_label.setText(
                "Status : Gemini AI"
            )

            QTimer.singleShot(

                1400,

                lambda: self.left_panel.set_speaking(
                    "Silent"
                )

            )

            return
        
        # ---------------------------------
        # System Automation Commands
        # ---------------------------------

        if intent in {

            "set_volume",

            "set_brightness"

        }:

            entity = self.entity_extractor.extract_percentage(
                text
            )

        elif intent in {

            "volume_up",

            "volume_down",

            "mute",

            "lock_screen",

            "take_screenshot",

            "open_task_manager",

            "open_file_explorer",

            "brightness_up",

            "brightness_down",

            "shutdown",

            "restart",

            "sleep",

            "sign_out",

            "open_settings",

            "open_cmd",

            "open_powershell",

            "open_control_panel",

            "open_camera",

            "capture_photo",

            "start_screen_recording",

            "stop_screen_recording"

        }:

            entity = None

        # ---------------------------------
        # File Commands
        # ---------------------------------

        elif intent in {

            "open_file",

            "create_file",

            "delete_file"

        }:

            entity = self.entity_extractor.extract_file_query(
                text
            )

        elif intent == "compress_file":

            entity = self.entity_extractor.extract_compress_file(
                text
            )

        elif intent == "extract_zip":

            entity = self.entity_extractor.extract_extract_zip(
                text
            )

        elif intent == "rename_file":

            entity = self.entity_extractor.extract_rename_file(
                text
            )

        elif intent == "copy_file":

            entity = self.entity_extractor.extract_copy_file(
                text
            )

        elif intent == "move_file":

            entity = self.entity_extractor.extract_move_file(
                text
            )

        elif intent == "search_extension":

            entity = self.entity_extractor.extract_search_extension(
                text
            )

        elif intent == "search_size":

            entity = self.entity_extractor.extract_search_size(
                text
            )

        elif intent == "search_date":

            entity = self.entity_extractor.extract_search_date(
                text
            )

        # ---------------------------------
        # Browser Commands
        # ---------------------------------

        elif intent in {

            "launch_application",

            "create_word_document",

            "create_excel_workbook",

            "create_powerpoint_presentation",

            "open_website",

            "open_google",

            "open_youtube",

            "google_search",

            "youtube_search",

            "play_youtube",

            "new_tab",

            "close_tab",

            "next_tab",

            "previous_tab",

            "refresh",

            "browser_downloads",

            "browser_history",

            "browser_bookmarks",

            "bookmark_page",

            "address_bar",

            "browser_back",

            "browser_forward",

            "private_window",

            "open_chrome_profile",

        }:

            if intent in {

                "launch_application",

                "create_word_document",

                "create_excel_workbook",

                "create_powerpoint_presentation"

            }:

                entity = self.entity_extractor.extract_application(
                    text
                )

            elif intent == "open_website":

                entity = self.entity_extractor.extract_website(
                    text
                )

            elif intent == "open_google":

                entity = "google.com"

            elif intent == "open_youtube":

                entity = "youtube.com"

            elif intent == "google_search":

                entity = self.entity_extractor.extract_search_query(
                    text
                )

            elif intent == "youtube_search":

                entity = self.entity_extractor.extract_youtube_query(
                    text
                )

            elif intent == "play_youtube":

                entity = self.entity_extractor.extract_youtube_query(
                    text
                )

            else:

                entity = None

        # ---------------------------------
        # Folder Commands
        # ---------------------------------

        elif intent in {

            "open_folder",

            "create_folder",

            "delete_folder",

            "rename_folder",

            "move_folder",

            "copy_folder",

            "empty_recycle_bin"

        }:

            entity = self.entity_extractor.extract_folder(
                text
            )

        # ---------------------------------
        # Application Commands
        # ---------------------------------

        else:

            entity = self.entity_extractor.extract_application(
                text
            )

        # ---------------------------------
        # Extract Additional Information
        # ---------------------------------

        typed_text = self.text_extractor.extract_text(
            text
        )

        browser = self.entity_extractor.extract_browser(
            text
        )

        website = self.entity_extractor.extract_website(
            text
        )

        if intent == "google_search":

            search_query = self.entity_extractor.extract_search_query(
                text
            )

        elif intent in {

            "youtube_search",

            "play_youtube"

        }:

            search_query = self.entity_extractor.extract_youtube_query(
                text
            )

        else:

            search_query = None

        profile = self.entity_extractor.extract_profile(
            text
        )

        # ---------------------------------
        # Debug Information
        # ---------------------------------

        self.conversation_label.setText(

            f"You Said:\n\n{text}\n\n"

            f"Intent : {intent}\n"

            f"Entity : {entity}\n"

            f"Browser : {browser}\n"

            f"Website : {website}\n"

            f"Search Query : {search_query}\n"

            f"Profile : {profile}\n"

            f"Text : {typed_text}"

        )

        if getattr(settings, "DEBUG", False):

            print("\n========== ASTRA ==========")

            print(f"Text    : {text}")

            print(f"Intent  : {intent}")

            print(f"Entity  : {entity}")

            print(f"Browser : {browser}")

            print(f"Website : {website}")

            print(f"Search  : {search_query}")

            print(f"Profile : {profile}")

            print(f"Typing  : {typed_text}")

            print("===========================\n")

        # ---------------------------------
        # Future Compound Commands
        # ---------------------------------

        if (

            intent == "launch_application"

            and

            typed_text

        ):

            print(

                "Compound Command Detected."

            )

        self.status_label.setText(
            "Status : Executing..."
        )

        try:

            # Still processing command
            self.left_panel.set_listening(
                "Idle"
            )

            self.left_panel.set_thinking(
                "Thinking"
            )

            self.left_panel.set_speaking(
                "Silent"
            )

        except Exception:

            pass

        # ---------------------------------
        # Execute Command
        # ---------------------------------

        result = self.dispatcher.dispatch(

            intent=intent,

            entity=entity,

            typed_text=typed_text,

            browser=browser,

            website=website,

            search_query=search_query,

            profile=profile,

            user_text=text

        )
        # ---------------------------------
        # Handle Dispatcher Result
        # ---------------------------------

        self._handle_dispatch_result(
            result,
            text,
            intent,
            entity,
        )

    # --------------------------------------------------
    # Position File Selection Panel
    # --------------------------------------------------

    def _position_file_selection_panel(self):
        """
        Position the File/Folder Selection Panel at the
        bottom-center, directly above the ACTUAL microphone
        button.

        IMPORTANT:
            - MicWidget is NOT moved.
            - MicWidget size is NOT changed.
            - User message area is NOT changed.
            - ASTRA response area is NOT changed.
            - Only the floating file-selection panel is moved.
            - The panel follows the real microphone button,
            not the large MicWidget container.
        """

        panel = getattr(
            self,
            "file_selection_panel",
            None
        )

        mic_button = getattr(
            self,
            "microphone_button",
            None
        )

        center = getattr(
            self,
            "center_container",
            None
        )

        if (
            panel is None
            or mic_button is None
            or center is None
        ):
            return

        try:

            # --------------------------------------------------
            # Panel must be visible
            # --------------------------------------------------

            if not panel.isVisible():
                return

            # --------------------------------------------------
            # Make sure layouts are updated first.
            # --------------------------------------------------

            layout = center.layout()

            if layout is not None:
                layout.activate()

            QApplication.processEvents()

            # --------------------------------------------------
            # Panel Width
            # --------------------------------------------------

            available_width = center.width()

            panel_width = min(
                700,
                max(
                    500,
                    available_width - 30
                )
            )

            panel.setFixedWidth(
                panel_width
            )

            # --------------------------------------------------
            # Recalculate panel height.
            # --------------------------------------------------

            panel.adjustSize()

            QApplication.processEvents()

            # --------------------------------------------------
            # ACTUAL MICROPHONE BUTTON POSITION
            #
            # IMPORTANT:
            #
            # Do NOT use:
            #
            #     self.mic_widget.height()
            #
            # because MicWidget contains the complete
            # left / center / right conversation area.
            #
            # Instead use the real microphone button.
            # --------------------------------------------------

            mic_top_left = mic_button.mapTo(
                center,
                QPoint(0, 0)
            )

            mic_x = mic_top_left.x()

            mic_y = mic_top_left.y()

            mic_width = mic_button.width()

            # --------------------------------------------------
            # Center panel relative to ACTUAL microphone.
            #
            # This also keeps the panel aligned with the mic
            # if the internal 3-column microphone area changes.
            # --------------------------------------------------

            x = (
                mic_x
                + (mic_width - panel.width()) // 2
            )

            # --------------------------------------------------
            # Small visual gap.
            #
            # Panel:
            #
            #   ┌──────────────────────┐
            #   │ File Selection       │
            #   └──────────────────────┘
            #
            #              6 px
            #
            #              🎤
            #
            # --------------------------------------------------

            gap = 6

            y = (
                mic_y
                - panel.height()
                - gap
            )

            # --------------------------------------------------
            # Horizontal safety boundary
            # --------------------------------------------------

            x = max(
                8,
                min(
                    x,
                    center.width()
                    - panel.width()
                    - 8
                )
            )

            # --------------------------------------------------
            # Vertical safety boundary
            # --------------------------------------------------

            y = max(
                8,
                y
            )

            # --------------------------------------------------
            # Final geometry
            #
            # ONLY THE FILE PANEL MOVES.
            # --------------------------------------------------

            panel.setGeometry(
                x,
                y,
                panel.width(),
                panel.height()
            )

            # --------------------------------------------------
            # Keep panel above background/avatar layer.
            # --------------------------------------------------

            panel.raise_()

            panel.update()

        except RuntimeError:

            # Qt object may already be closing/deleted.
            return

        except Exception as error:

            print(
                f"File Selection Position Error : {error}"
            )

    # --------------------------------------------------
    # File Selection UI
    # --------------------------------------------------

    def show_file_selection(
        self,
        candidates,
        operation="file"
    ):
        """
        Show file/folder candidates in the glassmorphism
        FileSelectionPanel.

        The panel floats directly above the microphone
        without changing the microphone, halo, or avatar
        layout position.
        """

        if not candidates:
            return

        self._file_selection_candidates = list(
            candidates
        )

        self._file_selection_operation = (
            operation or "file"
        )

        try:

            # --------------------------------------------------
            # Prepare panel content
            # --------------------------------------------------

            self.file_selection_panel.show_candidates(
                candidates,
                operation=operation
            )

            # --------------------------------------------------
            # Main UI status
            # --------------------------------------------------

            self.status_label.setText(
                f"Status : Select {operation.title()}"
            )

            # --------------------------------------------------
            # Short AI message beside microphone
            # --------------------------------------------------

            message = (
                f"I found {len(candidates)} matching "
                f"{operation}s. Please say the number you want."
            )

            self.mic_widget.update_ai_message(
                message
            )

            # --------------------------------------------------
            # Keep conversation area clean.
            # Full file paths remain ONLY inside the panel.
            # --------------------------------------------------

            self.conversation_label.setText(
                f"{operation.title()} Selection\n\n"
                f"{len(candidates)} matching items found.\n\n"
                "Choose a number from the panel."
            )

            # --------------------------------------------------
            # Left status cards
            # --------------------------------------------------

            try:

                self.left_panel.set_listening(
                    "Waiting for File Number"
                )

                self.left_panel.set_thinking(
                    "Select a File"
                )

                self.left_panel.set_speaking(
                    "Silent"
                )

            except Exception:
                pass

            # --------------------------------------------------
            # Show panel
            # --------------------------------------------------

            self.file_selection_panel.show()

            # --------------------------------------------------
            # Let Qt calculate the panel's final size.
            # --------------------------------------------------

            QApplication.processEvents()

            self.file_selection_panel.adjustSize()

            QApplication.processEvents()

            # --------------------------------------------------
            # Position panel relative to microphone.
            #
            # IMPORTANT:
            # Use delayed positioning because the microphone
            # geometry may finish updating only after this
            # event loop pass.
            # --------------------------------------------------

            QTimer.singleShot(
                0,
                self._position_file_selection_panel
            )

            # --------------------------------------------------
            # Second positioning pass.
            #
            # This handles final layout/paint geometry and
            # keeps the panel locked to the microphone.
            # --------------------------------------------------

            QTimer.singleShot(
                80,
                self._position_file_selection_panel
            )

            self.file_selection_panel.raise_()

            self.file_selection_panel.update()

            self.center_container.update()

            self.update()

        except Exception as error:

            print(
                f"File Selection Panel Error : {error}"
            )

    def clear_file_selection(self):
        """
        Clear the current filesystem selection state
        and hide the glass selection panel.
        """

        self._file_selection_candidates = []

        self._file_selection_operation = None

        # --------------------------------------------------
        # Hide the dedicated file/folder selection UI
        # --------------------------------------------------

        try:

            self.file_selection_panel.hide_panel()

        except Exception as error:

            print(
                f"File Selection Panel Hide Error : {error}"
            )

    # --------------------------------------------------
    # File Selection Button Click
    # --------------------------------------------------

    def _on_file_selection_clicked(
        self,
        selection_index
    ):
        """
        Handle a direct UI selection.

        Example:
            User clicks option 2
            -> selection_index = 2
            -> same pending voice command is resumed
            -> no second intent detection
        """

        if self._closing:
            return

        if not self._pending_file_selection:
            return

        try:

            selection_index = int(
                selection_index
            )

        except (
            TypeError,
            ValueError
        ):

            return

        print(
            f"File Selection UI Choice : {selection_index}"
        )

        # --------------------------------------------------
        # Reuse the SAME pending-command selection flow
        # --------------------------------------------------

        self._handle_pending_file_selection(
            str(selection_index)
        )


    # --------------------------------------------------
    # File Selection Cancel
    # --------------------------------------------------

    def _on_file_selection_cancelled(
        self
    ):
        """
        Cancel the currently pending file/folder selection.
        """

        if self._closing:
            return

        if not self._pending_file_selection:
            return

        print(
            "File Selection UI Cancelled."
        )

        self._pending_file_selection = None

        self.clear_file_selection()

        self.status_label.setText(
            "Status : File Selection Cancelled"
        )

        self.mic_widget.update_ai_message(
            "File selection cancelled."
        )

        self.conversation_label.setText(
            "File Selection Cancelled"
        )

        try:

            self.left_panel.set_listening(
                "Idle"
            )

            self.left_panel.set_thinking(
                "Inactive"
            )

            self.left_panel.set_speaking(
                "Speaking"
            )

        except Exception:
            pass

        try:

            self.tts.speak(
                "File selection cancelled."
            )

        except Exception:
            pass

        self._unlock_after_speech(
            restart_wake=True
        )

    # --------------------------------------------------
    # Start Initialization
    # --------------------------------------------------

    def start_initialization(self):
        """
        Start background initialization.
        """

        self.status_label.setText(
            "Status : Initializing..."
        )

        self.microphone_button.setEnabled(False)

        self.loading_bar.setValue(0)

        self.loading_percent.setText("0%")

        self.loading_status.setText(
            "Starting ASTRA..."
        )

        self.worker = InitializationWorker(
            recognizer=self.recognizer
        )

        self.worker.status_changed.connect(
            self.update_initialization_status
        )

        self.worker.progress_changed.connect(
            self.update_loading_progress
        )

        self.worker.finished_success.connect(
            self.initialization_completed
        )

        self.worker.finished_error.connect(
            self.initialization_failed
        )

        self.worker.start()

    # --------------------------------------------------
    # Update Initialization Status
    # --------------------------------------------------

    def update_initialization_status(
        self,
        message
    ):
        """
        Update loading status.
        """

        self.status_label.setText(
            f"Status : {message}"
        )

        self.loading_status.setText(
            message
        )

        try:

            self.left_panel.set_thinking(
                message
            )

        except Exception:

            pass

    # --------------------------------------------------
    # Update Loading Progress
    # --------------------------------------------------

    def update_loading_progress(
        self,
        value
    ):
        """
        Smooth loading progress.
        """

        current = self.loading_bar.value()

        # Never move backwards

        if value < current:

            return

        self.progress_animation = QPropertyAnimation(

            self.loading_bar,

            b"value"

        )

        self.progress_animation.setStartValue(
            current
        )

        self.progress_animation.setEndValue(
            value
        )

        self.progress_animation.setDuration(

            max(
                250,
                (value - current) * 18
            )

        )

        self.progress_animation.setEasingCurve(

            QEasingCurve.Linear

        )

        self.progress_animation.valueChanged.connect(

            lambda v: self.loading_percent.setText(

                f"{int(v)}%"

            )

        )

        self.progress_animation.start()

    # --------------------------------------------------
    # Initialization Completed
    # --------------------------------------------------

    def initialization_completed(self):
        """
        Called when initialization finishes.
        UI will open ONLY after progress reaches 100%.
        """

        self.status_label.setText(
            "Status : Ready"
        )

        self.loading_status.setText(
            "Initialization Complete"
        )

        # Already completed?
        if self.loading_finished:
            return

        self.loading_finished = True

        # Wait until animation reaches 100%

        def wait_for_completion():

            if self.loading_bar.value() >= 100:

                self.finish_loading_animation()

            else:

                QTimer.singleShot(
                    30,
                    wait_for_completion
                )

        wait_for_completion()

    # --------------------------------------------------
    # Finish Loading Animation
    # --------------------------------------------------

    def finish_loading_animation(self):
        """
        Remove loading overlay safely.

        The overlay is detached from MainWindow before
        deleteLater() so resizeEvent() can never access
        a QWidget that has already been deleted.
        """

        overlay = getattr(
            self,
            "loading_overlay",
            None
        )

        if overlay is None:
            self.enable_main_ui()
            return

        try:

            if not overlay.isVisible():
                self.loading_overlay = None
                self.enable_main_ui()
                return

        except RuntimeError:

            # Qt object has already been deleted.
            self.loading_overlay = None
            self.enable_main_ui()
            return

        fade = QPropertyAnimation(
            self.overlay_opacity,
            b"opacity"
        )

        fade.setDuration(350)

        fade.setStartValue(1.0)

        fade.setEndValue(0.0)

        fade.setEasingCurve(
            QEasingCurve.OutCubic
        )

        def remove_overlay():

            try:
                overlay.hide()

            except RuntimeError:
                pass

            # IMPORTANT:
            # Remove the Python reference BEFORE deleteLater().
            # This prevents resizeEvent() from touching the
            # deleted QWidget.

            self.loading_overlay = None

            try:
                overlay.deleteLater()

            except RuntimeError:
                pass

            self.enable_main_ui()

        fade.finished.connect(
            remove_overlay
        )

        fade.start()

        self.fade_animation = fade

    # --------------------------------------------------
    # Enable Main UI
    # --------------------------------------------------

    def enable_main_ui(self):
        """
        Enable ASTRA after loading.
        """

        self.microphone_button.setEnabled(True)

        self.status_label.setText(
            "Status : Ready"
        )

        self.conversation_label.setText(

            "Welcome to ASTRA-AI\n\n"

            "Click the microphone to start."

        )

        try:

            self.mic_widget.set_enabled(True)

            self.left_panel.set_listening(
                "Waiting for DHEEPTHI"
            )

            self.left_panel.set_thinking(
                "Inactive"
            )

            self.left_panel.set_speaking(
                "Silent"
            )

        except Exception:

            pass

        # ----------------------------------
        # Start DHEEPTHI Wake Word Mode
        # ----------------------------------

        if self.wake_word_enabled:

            QTimer.singleShot(
                500,
                self.start_wake_word_worker
            )

    # --------------------------------------------------
    # Initialization Failed
    # --------------------------------------------------

    def initialization_failed(
        self,
        error
    ):
        """
        Called when initialization fails.
        """

        self.status_label.setText(
            "Status : Initialization Failed"
        )

        self.loading_status.setText(
            "Initialization Failed"
        )

        self.microphone_button.setEnabled(False)

        self.conversation_label.setText(

            f"Initialization Error\n\n{error}"

        )

        try:

            self.left_panel.set_listening(
                "Offline"
            )

            self.left_panel.set_thinking(
                "Error"
            )

            self.left_panel.set_speaking(
                "Silent"
            )

        except Exception:

            pass

    # --------------------------------------------------
    # Lock Microphone
    # --------------------------------------------------

    def lock_microphone(
        self
    ):
        """
        Lock the microphone button while ASTRA
        is listening or processing a command.
        """

        self.processing_voice = True

        # ---------------------------------
        # Disable button
        # ---------------------------------

        self.microphone_button.setEnabled(
            False
        )

        # ---------------------------------
        # Explicit blocked cursor
        # ---------------------------------

        self.microphone_button.setCursor(
            Qt.ForbiddenCursor
        )

        # ---------------------------------
        # Keep MicWidget disabled state
        # ---------------------------------

        try:

            self.mic_widget.setEnabled(
                False
            )

        except Exception:

            pass

        QApplication.processEvents()


    # --------------------------------------------------
    # Unlock Microphone
    # --------------------------------------------------

    def unlock_microphone(
        self
    ):
        """
        Unlock the microphone button after the
        current voice operation is completely finished.
        """

        self.processing_voice = False

        # ---------------------------------
        # Enable button
        # ---------------------------------

        self.microphone_button.setEnabled(
            True
        )

        # ---------------------------------
        # Normal cursor
        # ---------------------------------

        self.microphone_button.setCursor(
            Qt.PointingHandCursor
        )

        # ---------------------------------
        # Restore MicWidget state
        # ---------------------------------

        try:

            self.mic_widget.setEnabled(
                True
            )

            self.mic_widget._listening = False

            self.mic_widget.update()

        except Exception:

            pass

        QApplication.processEvents()

    # --------------------------------------------------
    # Start Listening
    # --------------------------------------------------

    def start_listening(self):
        """
        Start manual voice recognition.

        Manual microphone lifecycle:

            Mic Click
                ↓
            Stop DHEEPTHI wake listener
                ↓
            Show "Listening" immediately
                ↓
            ASTRA says "Listening"
                ↓
            Wait until TTS finishes
                ↓
            Start the actual microphone listener
                ↓
            Capture one command
                ↓
            Disable microphone while ASTRA processes / speaks
                ↓
            Restart DHEEPTHI after the task is complete

        The GUI thread is never blocked waiting for the wake-word
        worker. This is important because blocking QThread.wait()
        from the Qt GUI thread can make the window appear as
        "Not Responding".
        """

        if self._closing:
            return

        # ---------------------------------
        # Already processing
        # ---------------------------------

        if self.processing_voice:
            return

        # ---------------------------------
        # Manual listening already requested
        # ---------------------------------

        if self.manual_listening_requested:
            return

        # ---------------------------------
        # Request Manual Mode
        # ---------------------------------

        self.manual_listening_requested = True

        # Lock immediately so the user cannot start another
        # microphone action while the mode is switching.
        self.lock_microphone()

        # ---------------------------------
        # Update UI immediately
        # ---------------------------------
        # The user asked for the first manual click to show
        # "Listening", not "Preparing".
        #
        # The actual audio capture is still delayed until
        # ASTRA finishes saying "Listening", preventing Whisper
        # from capturing ASTRA's own voice.
        # ---------------------------------

        self.status_label.setText(
            "Status : Listening..."
        )

        try:
            self.mic_widget.show_listening()

            self.mic_widget.set_listening(
                False
            )

            self.left_panel.set_listening(
                "Listening"
            )

            self.left_panel.set_thinking(
                "Inactive"
            )

            self.left_panel.set_speaking(
                "Silent"
            )

        except Exception:
            pass

        QApplication.processEvents()

        # ---------------------------------
        # Stop DHEEPTHI Wake Worker
        # ---------------------------------
        # IMPORTANT:
        # Do NOT call voice_worker.wait() here.
        # The GUI must remain responsive.
        #
        # listening_finished() will continue the manual flow
        # after the wake worker has actually finished.
        # ---------------------------------

        if self.voice_worker is not None:

            try:

                if self.voice_worker.isRunning():

                    if self.current_voice_mode == "wake":

                        print(
                            "Stopping DHEEPTHI listener for manual microphone..."
                        )

                        try:
                            self.voice_worker.stop()

                        except Exception as error:
                            print(
                                f"Wake Worker Stop Error : {error}"
                            )

                        return

                    # Manual worker is already running.
                    self.manual_listening_requested = False
                    self.unlock_microphone()
                    return

            except Exception as error:

                print(
                    f"Voice Worker State Error : {error}"
                )

        # ---------------------------------
        # No wake worker is running.
        # Start the manual prompt now.
        # ---------------------------------

        self._begin_manual_listening_prompt()

    # --------------------------------------------------
    # Begin Manual Listening Prompt
    # --------------------------------------------------

    def _begin_manual_listening_prompt(self):
        """
        Start the manual-listening TTS prompt.

        This is called only after the wake-word worker has
        stopped, so ASTRA cannot speak while the wake listener
        still owns the microphone.
        """

        if self._closing:
            return

        if not self.manual_listening_requested:
            return

        # ---------------------------------
        # Safety: wake worker must be gone
        # ---------------------------------

        if self.voice_worker is not None:

            try:

                if self.voice_worker.isRunning():

                    return

            except Exception:
                pass

        # ---------------------------------
        # Keep the UI in Listening state
        # ---------------------------------

        self.status_label.setText(
            "Status : Listening..."
        )

        try:

            self.mic_widget.show_listening()

            self.mic_widget.set_listening(
                False
            )

            self.left_panel.set_listening(
                "Listening"
            )

            self.left_panel.set_thinking(
                "Inactive"
            )

            self.left_panel.set_speaking(
                "Speaking"
            )

        except Exception:
            pass

        # ---------------------------------
        # ASTRA Voice Prompt
        # ---------------------------------
        # Only the word "Listening" is used.
        # No "Sollunga" prompt is generated here.
        # ---------------------------------

        try:

            if self.tts is not None:

                self.tts.speak(
                    "Listening"
                )

        except Exception as error:

            print(
                f"Listening Prompt TTS Error : {error}"
            )

            # If TTS fails, start microphone directly.
            self._start_manual_listener_after_prompt()

            return

        # ---------------------------------
        # Wait asynchronously for TTS
        # ---------------------------------

        QTimer.singleShot(
            100,
            self._wait_for_manual_listening_prompt
        )

    # --------------------------------------------------
    # Wait For Manual Listening Prompt
    # --------------------------------------------------

    def _wait_for_manual_listening_prompt(self):
        """
        Wait asynchronously until ASTRA finishes saying
        "Listening".

        The microphone remains disabled at the backend while
        TTS is speaking. This prevents Whisper from hearing
        ASTRA's own voice.
        """

        if self._closing:
            return

        if not self.manual_listening_requested:
            return

        try:

            speaking = (
                self.tts is not None
                and self.tts.speaking()
            )

        except Exception:

            speaking = False

        if speaking:

            QTimer.singleShot(
                60,
                self._wait_for_manual_listening_prompt
            )

            return

        # ---------------------------------
        # TTS finished
        # ---------------------------------

        self._start_manual_listener_after_prompt()

    # --------------------------------------------------
    # Start Manual Listener After Prompt
    # --------------------------------------------------

    def _start_manual_listener_after_prompt(self):
        """
        Start the actual microphone listener only after
        ASTRA's "Listening" prompt has completely finished.
        """

        if self._closing:
            return

        if not self.manual_listening_requested:
            return

        # ---------------------------------
        # Safety: existing worker
        # ---------------------------------

        if self.voice_worker is not None:

            try:

                if self.voice_worker.isRunning():
                    return

            except Exception:
                pass

        # ---------------------------------
        # Update UI
        # ---------------------------------

        self.status_label.setText(
            "Status : Listening..."
        )

        try:

            self.mic_widget.show_listening()

            self.mic_widget.set_listening(
                True
            )

            self.left_panel.set_listening(
                "Listening"
            )

            self.left_panel.set_thinking(
                "Inactive"
            )

            self.left_panel.set_speaking(
                "Silent"
            )

        except Exception:
            pass

        QApplication.processEvents()

        # ---------------------------------
        # Start Manual Worker
        # ---------------------------------

        QTimer.singleShot(
            50,
            lambda: self.start_voice_worker(
                wake_word_mode=False
            )
        )

    def listening_finished(self):
        """
        Handle completion of both:

        1. DHEEPTHI wake-word listening
        2. Manual microphone listening

        IMPORTANT:
        This method never blocks the Qt GUI thread with
        QThread.wait(). The worker's finished signal already
        tells us that its run() method has returned.
        """

        finished_mode = self.current_voice_mode

        current_worker = self.voice_worker

        self.voice_worker = None

        self.current_voice_mode = None

        # ---------------------------------
        # Stop Audio UI
        # ---------------------------------

        try:

            self.mic_widget.update_audio_level(
                0.0
            )

            self.mic_widget._listening = False

            self.mic_widget.update()

        except Exception:
            pass

        # ---------------------------------
        # Non-blocking Worker Cleanup
        # ---------------------------------

        if current_worker:

            try:

                current_worker.deleteLater()

            except Exception as error:

                print(
                    f"Voice Worker Cleanup Error : {error}"
                )

        # ==================================================
        # MANUAL MICROPHONE MODE
        # ==================================================

        if finished_mode == "manual":

            print(
                "Manual microphone listening finished."
            )

            self.manual_listening_requested = False

            self.wake_word_running = False

            # --------------------------------------------------
            # Pending YES/NO confirmation
            # --------------------------------------------------
            # process_command() can receive the confirmation request
            # while the manual worker is still unwinding. Start the
            # confirmation listener only after this worker has fully
            # finished, otherwise two voice workers could overlap.
            if self._pending_confirmation:

                print(
                    "Manual listening finished. "
                    "Pending confirmation is active."
                )

                self.status_label.setText(
                    "Status : Waiting for Confirmation"
                )

                try:
                    self.left_panel.set_listening(
                        "Say Yes or No"
                    )

                    self.left_panel.set_thinking(
                        "Waiting for Confirmation"
                    )

                    self.left_panel.set_speaking(
                        "Silent"
                    )
                except Exception:
                    pass

                QTimer.singleShot(
                    120,
                    self._wait_for_confirmation_prompt
                )

                return

            # --------------------------------------------------
            # Pending file selection
            # --------------------------------------------------

            if self._pending_file_selection:

                print(
                    "Manual listening finished. "
                    "Pending file selection is active."
                )

                self.status_label.setText(
                    "Status : Waiting for File Selection"
                )

                try:

                    self.left_panel.set_listening(
                        "Select File Number"
                    )

                    self.left_panel.set_thinking(
                        "Waiting for Selection"
                    )

                    self.left_panel.set_speaking(
                        "Silent"
                    )

                    self.mic_widget.show_listening()

                    self.mic_widget.set_listening(
                        False
                    )

                except Exception:
                    pass

                # ----------------------------------
                # Start selection listener only after
                # the previous manual worker has fully
                # finished.
                # ----------------------------------

                QTimer.singleShot(
                    150,
                    self._wait_for_speech_then_start_selection
                )

                return

            # --------------------------------------------------
            # Normal manual command
            # --------------------------------------------------
            # DO NOT unlock or restart wake-word mode here.
            # process_command() owns the command lifecycle and
            # _unlock_after_speech() will unlock + restart wake
            # only after processing/TTS has completed.
            # --------------------------------------------------

            self.status_label.setText(
                "Status : Processing..."
            )

            try:

                self.left_panel.set_listening(
                    "Idle"
                )

                self.left_panel.set_thinking(
                    "Thinking"
                )

                self.left_panel.set_speaking(
                    "Silent"
                )

            except Exception:
                pass

            return

        # ==================================================
        # DHEEPTHI WAKE WORD MODE
        # ==================================================

        if finished_mode == "wake":

            self.wake_word_running = False

            # ---------------------------------
            # Manual microphone has priority
            # ---------------------------------

            if self.manual_listening_requested:

                print(
                    "Wake listener stopped for manual microphone."
                )

                QTimer.singleShot(
                    0,
                    self._begin_manual_listening_prompt
                )

                return

            # ---------------------------------
            # Wake-word command is being processed.
            # ---------------------------------

            if self.processing_voice:

                return

            # ---------------------------------
            # Normal Wake Word Loop
            # ---------------------------------

            if self.wake_word_enabled:

                try:

                    self.left_panel.set_listening(
                        "Waiting for DHEEPTHI"
                    )

                    self.left_panel.set_thinking(
                        "Inactive"
                    )

                    self.left_panel.set_speaking(
                        "Silent"
                    )

                except Exception:
                    pass

                QTimer.singleShot(
                    700,
                    lambda: (
                        self.start_wake_word_worker()
                        if self.wake_word_enabled
                        and not self.manual_listening_requested
                        and not self.processing_voice
                        else None
                    )
                )

            return

        # ---------------------------------
        # Unknown / Safety
        # ---------------------------------

        if not self.processing_voice:

            self.manual_listening_requested = False

            QTimer.singleShot(
                120,
                self.unlock_microphone
            )

    def start_voice_worker(
        self,
        wake_word_mode=False
    ):
        """
        Start a voice worker in either:

        wake_word_mode=True
            -> DHEEPTHI standby

        wake_word_mode=False
            -> Manual microphone
        """

        # ---------------------------------
        # Existing worker check
        # ---------------------------------

        if self.voice_worker is not None:

            if self.voice_worker.isRunning():

                return

        # ---------------------------------
        # Set Worker Mode
        # ---------------------------------

        if wake_word_mode:

            self.current_voice_mode = "wake"

        else:

            self.current_voice_mode = "manual"

        # ---------------------------------
        # Create Worker
        # ---------------------------------

        self.voice_worker = VoiceWorker(

            self.recognizer,

            self.tts,

            wake_word_mode=wake_word_mode

        )

        # ---------------------------------
        # Signals
        # ---------------------------------

        self.voice_worker.command_ready.connect(
            self.process_command
        )

        self.voice_worker.audio_level.connect(
            self.update_audio_wave
        )

        self.voice_worker.finished.connect(
            self.listening_finished
        )

        # ---------------------------------
        # Start
        # ---------------------------------

        self.voice_worker.start()

        if wake_word_mode:

            self.wake_word_running = True

            print(
                "DHEEPTHI wake listener started."
            )

        else:

            print(
                "Manual microphone listener started."
            )

    # --------------------------------------------------
    # Start DHEEPTHI Wake Word Worker
    # --------------------------------------------------

    def start_wake_word_worker(self):

        if not self.wake_word_enabled:

            return

        # ---------------------------------
        # Manual microphone has priority
        # ---------------------------------

        if self.manual_listening_requested:

            return

        if self.processing_voice:

            return

        # ---------------------------------
        # Existing Worker
        # ---------------------------------

        if self.voice_worker is not None:

            if self.voice_worker.isRunning():

                return

        # ---------------------------------
        # Start Wake Mode
        # ---------------------------------

        self.wake_word_running = True

        self.current_voice_mode = "wake"

        self.status_label.setText(
            "Status : Waiting for DHEEPTHI"
        )

        try:

            self.left_panel.set_listening(
                "Waiting for DHEEPTHI"
            )

            self.left_panel.set_thinking(
                "Inactive"
            )

            self.left_panel.set_speaking(
                "Silent"
            )

        except Exception:

            pass

        self.start_voice_worker(
            wake_word_mode=True
        )

    # --------------------------------------------------
    # Audio Wave Update
    # --------------------------------------------------

    @Slot(float)
    def update_audio_wave(
        self,
        level
    ):

        try:

            self.mic_widget.update_audio_level(
                level
            )

        except Exception:

            pass

    # --------------------------------------------------
    # Premium Background
    # --------------------------------------------------

    def enable_premium_background(self):

        try:

            self.background.fast_mode = False

            self.background.update()

        except Exception:

            pass

    # --------------------------------------------------
    # Conversation Panel Geometry
    # --------------------------------------------------

    def _position_conversation_panel(self):
        """
        Keep the ConversationPanel in the exact same
        position and size as the existing RightPanel.

        IMPORTANT:
            This method only synchronizes the final geometry.
            During animation we animate only the panel position,
            which is much lighter than continuously animating
            the complete geometry rectangle.
        """

        panel = getattr(
            self,
            "conversation_panel",
            None
        )

        right_panel = getattr(
            self,
            "right_panel",
            None
        )

        if panel is None or right_panel is None:
            return

        try:

            # ----------------------------------------------
            # Get RightPanel position in MainWindow coords
            # ----------------------------------------------

            top_left = right_panel.mapTo(
                self,
                right_panel.rect().topLeft()
            )

            geometry = right_panel.geometry()

            geometry.moveTopLeft(
                top_left
            )

            # ----------------------------------------------
            # Exact same size + position
            # ----------------------------------------------

            panel.setGeometry(
                geometry
            )

            panel.raise_()

        except RuntimeError:

            return

        except Exception as error:

            print(
                "Conversation Panel Position Error:",
                error
            )

    # --------------------------------------------------
    # Open Conversation Panel
    # --------------------------------------------------

    def open_conversation_panel(self):
        """
        Open ConversationPanel over the existing RightPanel.

        Lightweight animation:
            RIGHT -> LEFT

        The panel starts just outside the right edge and
        slides into the exact RightPanel position.

        Only the position is animated. This avoids the extra
        repaint/layout work caused by animating QRect geometry.
        """

        if self._closing:
            return

        panel = getattr(
            self,
            "conversation_panel",
            None
        )

        right_panel = getattr(
            self,
            "right_panel",
            None
        )

        if panel is None or right_panel is None:
            return

        # ----------------------------------------------
        # Already open / currently animating
        # ----------------------------------------------

        if self.conversation_panel_open:
            return

        if self.conversation_animating:
            return

        # ----------------------------------------------
        # Stop previous animation safely
        # ----------------------------------------------

        if self.conversation_animation is not None:

            try:
                self.conversation_animation.stop()

            except Exception:
                pass

            self.conversation_animation = None

        # ----------------------------------------------
        # Calculate exact final position
        # ----------------------------------------------

        try:

            top_left = right_panel.mapTo(
                self,
                right_panel.rect().topLeft()
            )

            final_geometry = right_panel.geometry()

            final_geometry.moveTopLeft(
                top_left
            )

        except Exception as error:

            print(
                "Conversation Geometry Error:",
                error
            )

            self._position_conversation_panel()

            final_geometry = panel.geometry()

        # ----------------------------------------------
        # Start position
        #
        # Same Y position as RightPanel.
        # Only X is outside the window.
        # ----------------------------------------------

        final_pos = final_geometry.topLeft()

        start_pos = QPoint(
            self.width() + 8,
            final_pos.y()
        )

        # ----------------------------------------------
        # Set exact size first
        # ----------------------------------------------

        panel.setGeometry(
            final_geometry
        )

        panel.move(
            start_pos
        )

        # ----------------------------------------------
        # Show panel
        # ----------------------------------------------

        panel.show()

        panel.raise_()

        # ----------------------------------------------
        # Hide existing RightPanel quickly
        # ----------------------------------------------

        try:

            right_panel.fade_out(
                duration=180
            )

        except Exception as error:

            print(
                "RightPanel Fade Out Error:",
                error
            )

        # ----------------------------------------------
        # Animation state
        # ----------------------------------------------

        self.conversation_animating = True

        self.conversation_animation_mode = "open"

        # ----------------------------------------------
        # Lightweight POSITION animation
        # ----------------------------------------------

        animation = QPropertyAnimation(
            panel,
            b"pos",
            self
        )

        animation.setDuration(
            220
        )

        animation.setStartValue(
            start_pos
        )

        animation.setEndValue(
            final_pos
        )

        animation.setEasingCurve(
            QEasingCurve.OutCubic
        )

        animation.finished.connect(
            self._conversation_open_finished
        )

        self.conversation_animation = animation

        self.conversation_panel_open = True

        animation.start()

    # --------------------------------------------------
    # Conversation Open Finished
    # --------------------------------------------------

    def _conversation_open_finished(self):
        """
        Finalize conversation panel opening.

        The final position is synchronized once after the
        animation completes.
        """

        panel = getattr(
            self,
            "conversation_panel",
            None
        )

        if panel is None:
            return

        try:

            # ----------------------------------------------
            # One final alignment pass
            # ----------------------------------------------

            self._position_conversation_panel()

            panel.raise_()

        except Exception as error:

            print(
                "Conversation Open Finish Error:",
                error
            )

        finally:

            self.conversation_animating = False

            self.conversation_animation_mode = None

            self.conversation_animation = None

    # --------------------------------------------------
    # Close Conversation Panel
    # --------------------------------------------------

    def close_conversation_panel(self):
        """
        Close the ConversationPanel.

        Lightweight animation:
            LEFT -> RIGHT

        Only the panel position is animated.
        """

        if self._closing:
            return

        panel = getattr(
            self,
            "conversation_panel",
            None
        )

        if panel is None:
            return

        if not self.conversation_panel_open:
            return

        # ----------------------------------------------
        # Prevent repeated close clicks
        # ----------------------------------------------

        if self.conversation_animating:
            return

        # ----------------------------------------------
        # Stop previous animation safely
        # ----------------------------------------------

        if self.conversation_animation is not None:

            try:
                self.conversation_animation.stop()

            except Exception:
                pass

            self.conversation_animation = None

        # ----------------------------------------------
        # Current position
        # ----------------------------------------------

        current_pos = panel.pos()

        # ----------------------------------------------
        # Move only horizontally outside the window
        # ----------------------------------------------

        end_pos = QPoint(
            self.width() + 8,
            current_pos.y()
        )

        # ----------------------------------------------
        # Animation state
        # ----------------------------------------------

        self.conversation_animating = True

        self.conversation_animation_mode = "close"

        # ----------------------------------------------
        # Lightweight POSITION animation
        # ----------------------------------------------

        animation = QPropertyAnimation(
            panel,
            b"pos",
            self
        )

        animation.setDuration(
            220
        )

        animation.setStartValue(
            current_pos
        )

        animation.setEndValue(
            end_pos
        )

        animation.setEasingCurve(
            QEasingCurve.InCubic
        )

        animation.finished.connect(
            self._conversation_close_finished
        )

        self.conversation_animation = animation

        # ----------------------------------------------
        # Bring RightPanel back immediately but softly
        # ----------------------------------------------

        if self.right_panel is not None:

            try:

                self.right_panel.fade_in(
                    duration=180
                )

            except Exception as error:

                print(
                    "RightPanel Fade In Error:",
                    error
                )

        animation.start()

    # --------------------------------------------------
    # Conversation Close Finished
    # --------------------------------------------------

    def _conversation_close_finished(self):
        """
        Finalize conversation panel closing.
        """

        panel = getattr(
            self,
            "conversation_panel",
            None
        )

        if panel is None:
            return

        try:

            panel.hide()

            # ----------------------------------------------
            # Restore exact RightPanel alignment
            # ----------------------------------------------

            self._position_conversation_panel()

        except Exception as error:

            print(
                "Conversation Close Finish Error:",
                error
            )

        finally:

            self.conversation_panel_open = False

            self.conversation_animating = False

            self.conversation_animation_mode = None

            self.conversation_animation = None

    # --------------------------------------------------
    # Toggle Conversation Panel
    # --------------------------------------------------

    def toggle_conversation_panel(self):
        """
        Header conversation button callback.

        Closed:
            -> Open

        Open:
            -> Close

        While animation is running:
            -> Ignore additional clicks

        This prevents animation stacking and keeps the UI
        responsive on lower-spec systems.
        """

        if self._closing:
            return

        # ----------------------------------------------
        # Ignore repeated clicks during animation
        # ----------------------------------------------

        if self.conversation_animating:
            return

        if self.conversation_panel_open:

            self.close_conversation_panel()

        else:

            self.open_conversation_panel()

    # --------------------------------------------------
    # Resize Event
    # --------------------------------------------------

    def resizeEvent(
        self,
        event
    ):

        super().resizeEvent(
            event
        )

        # --------------------------------------------------
        # Loading overlay
        # --------------------------------------------------

        overlay = getattr(
            self,
            "loading_overlay",
            None
        )

        if overlay is not None:

            try:

                if overlay.isVisible():

                    overlay.setGeometry(
                        self.rect()
                    )

            except RuntimeError:

                self.loading_overlay = None

        # --------------------------------------------------
        # Conversation Panel
        # --------------------------------------------------

        conversation_panel = getattr(
            self,
            "conversation_panel",
            None
        )

        if conversation_panel is not None:

            try:

                if conversation_panel.isVisible():

                    # ------------------------------------------
                    # Never disturb an active animation.
                    # ------------------------------------------

                    if not self.conversation_animating:

                        self._position_conversation_panel()

            except RuntimeError:

                pass

        # --------------------------------------------------
        # File Selection Panel
        # --------------------------------------------------

        panel = getattr(
            self,
            "file_selection_panel",
            None
        )

        if panel is not None:

            try:

                if panel.isVisible():

                    QTimer.singleShot(
                        0,
                        self._position_file_selection_panel
                    )

                    QTimer.singleShot(
                        80,
                        self._position_file_selection_panel
                    )

            except RuntimeError:

                pass

    # --------------------------------------------------
    # Initialize Application
    # --------------------------------------------------

    def initialize_application(self):
        """
        Initialize ASTRA.
        """

        self.enable_premium_background()

        QTimer.singleShot(
            50,
            self.create_backend
        )

        QTimer.singleShot(
            100,
            self.start_initialization
        )

    # --------------------------------------------------
    # Close Event
    # --------------------------------------------------

    def closeEvent(
        self,
        event
    ):
        """
        Safely shut down all background workers
        and backend resources before destroying
        the main window.
        """

        self._closing = True

        print(
            "\n========== ASTRA SHUTDOWN =========="
        )

        # ---------------------------------
        # Disable future wake-word restarts
        # ---------------------------------

        self.manual_listening_requested = False

        self.wake_word_enabled = False

        self.wake_word_running = False

        # ---------------------------------
        # Stop pending Qt timers from
        # starting another voice worker
        # ---------------------------------

        try:

            QCoreApplication.processEvents()

        except Exception:

            pass

        # ==================================================
        # Voice Worker
        # ==================================================

        voice_worker = self.voice_worker

        if voice_worker is not None:

            try:

                if voice_worker.isRunning():

                    print(
                        "Stopping VoiceWorker..."
                    )

                    voice_worker.stop()

                    # ---------------------------------
                    # Wait longer than recognizer's
                    # phrase_time_limit (6 seconds)
                    # ---------------------------------

                    if not voice_worker.wait(
                        8000
                    ):

                        print(
                            "VoiceWorker did not stop within 8 seconds."
                        )

                    else:

                        print(
                            "VoiceWorker stopped successfully."
                        )

                # ---------------------------------
                # Clear reference only after stop
                # ---------------------------------

                self.voice_worker = None

            except Exception as error:

                print(
                    f"VoiceWorker Cleanup Error : {error}"
                )

        # ==================================================
        # Initialization Worker
        # ==================================================

        initialization_worker = self.worker

        if initialization_worker is not None:

            try:

                if initialization_worker.isRunning():

                    print(
                        "Stopping InitializationWorker..."
                    )

                    initialization_worker.stop()

                    initialization_worker.requestInterruption()

                    if not initialization_worker.wait(
                        5000
                    ):

                        print(
                            "InitializationWorker did not stop within 5 seconds."
                        )

                    else:

                        print(
                            "InitializationWorker stopped successfully."
                        )

                self.worker = None

            except Exception as error:

                print(
                    f"InitializationWorker Cleanup Error : {error}"
                )

        # ==================================================
        # Gemini
        # ==================================================

        try:

            if self.gemini:

                self.gemini.close()

        except Exception as error:

            print(
                f"Gemini Cleanup Error : {error}"
            )

        # ==================================================
        # Text To Speech
        # ==================================================

        try:

            if self.tts:

                self.tts.close()

        except Exception as error:

            print(
                f"TTS Cleanup Error : {error}"
            )

        # ==================================================
        # Browser
        # ==================================================

        try:

            if self.browser_controller:

                self.browser_controller.close()

        except Exception as error:

            print(
                f"Browser Cleanup Error : {error}"
            )

        print(
            "========== ASTRA SHUTDOWN COMPLETE ==========\n"
        )

        # ---------------------------------
        # Destroy Main Window only after
        # worker cleanup
        # ---------------------------------

        super().closeEvent(
            event
        )