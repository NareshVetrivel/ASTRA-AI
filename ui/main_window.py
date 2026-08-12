import os

from PySide6.QtCore import (
    Qt,
    QCoreApplication,
    QThread,
    Signal,
    Slot,
    QTimer,
    QPropertyAnimation,
    QEasingCurve,
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

from ui.widgets.background_widget import BackgroundWidget
from ui.widgets.mic_widget import MicWidget

from voice.whisper_recognizer import WhisperRecognizer
from voice.text_to_speech import TextToSpeech

from planner.intent_detector import IntentDetector
from planner.entity_extractor import EntityExtractor
from planner.text_extractor import TextExtractor
from planner.command_dispatcher import CommandDispatcher
from ai.gemini_client import GeminiClient

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

                self.tts.speak(
                    "Listening."
                )

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

        # ----------------------------------
        # Backend
        # ----------------------------------

        self.recognizer = None

        self.tts = None

        self.intent_detector = None

        self.entity_extractor = None

        self.text_extractor = None

        self.dispatcher = None

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

        self.header_widget.set_power_callback(
            self.close
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

        self.center_layout.setSpacing(0)

        self.center_layout.addStretch()

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

        print("Backend Ready.")

        print("=============================\n")

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
        # Normalize text
        # ------------------------------------------

        if not text:

            self.unlock_microphone()

            return

        text = text.strip()

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

            self.tts.wait_until_done()

            self.status_label.setText(
                "Status : Typed"
            )

            self.mic_widget.update_ai_message(
                "Typed successfully."
            )

            # ---------------------------------
            # Command completed
            # ---------------------------------

            self.unlock_microphone()

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

            self.tts.wait_until_done()

            self.unlock_microphone()

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
        # Success
        # ---------------------------------

        if result["success"]:

            # ---------------------------------
            # Conversation Reply
            # ---------------------------------

            reply = result.get(
                "message",
                result.get(
                    "status",
                    "Done."
                )
            )

            self.mic_widget.update_ai_message(reply)

            self.lock_microphone()

            self.tts.wait_until_done()

            self.unlock_microphone()

            if (

                intent == "launch_application"

                and

                entity

            ):

                self.last_application = entity

                if (

                    "notepad" in entity.lower()

                    or

                    "word" in entity.lower()

                ):

                    self.typing_mode = True

            self.status_label.setText(

                result["status"]

            )

            self.conversation_label.setText(

                f"Executed Successfully\n\n{text}"

            )

            try:

                # Automation completed
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

            # AI reply finished
            QTimer.singleShot(

                1400,

                lambda: self.left_panel.set_speaking(
                    "Silent"
                )

            )

            return

        # ---------------------------------
        # Failed
        # ---------------------------------

        self.mic_widget.update_ai_message(

            result.get(
                "message",
                "Sorry, I couldn't complete that request."
            )

        )

        self.lock_microphone()

        self.tts.speak(
            "Sorry. I could not understand your command."
        )

        self.tts.wait_until_done()

        self.unlock_microphone()

        self.status_label.setText(

            "Status : No Action"

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

        QTimer.singleShot(

            1400,

            lambda: self.left_panel.set_speaking(
                "Silent"
            )

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
        Remove loading overlay.
        """

        if not hasattr(self, "loading_overlay"):
            return

        if not self.loading_overlay.isVisible():
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

            self.loading_overlay.hide()

            self.loading_overlay.deleteLater()

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

        If DHEEPTHI wake-word listener is currently
        using the microphone, stop it first and then
        start manual microphone listening.
        """

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

        # ---------------------------------
        # Stop DHEEPTHI Wake Worker
        # ---------------------------------

        if self.voice_worker is not None:

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

                    # ---------------------------------
                    # Wait for microphone to release
                    # ---------------------------------

                    self.voice_worker.wait(3000)

                else:

                    # Manual worker already running

                    self.manual_listening_requested = False

                    return

        # ---------------------------------
        # Lock Microphone
        # ---------------------------------

        self.lock_microphone()

        self.status_label.setText(
            "Status : Listening..."
        )

        self.mic_widget.show_listening()

        try:

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

            100,

            lambda: self.start_voice_worker(
                wake_word_mode=False
            )

        )

    # --------------------------------------------------
    # Listening Finished
    # --------------------------------------------------

    def listening_finished(self):
        """
        Handle completion of both:

        1. DHEEPTHI wake-word listening
        2. Manual microphone listening
        """

        # ---------------------------------
        # Remember which worker finished
        # ---------------------------------

        finished_mode = (
            self.current_voice_mode
        )

        # ---------------------------------
        # Clear Current Worker
        # ---------------------------------

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

            # ---------------------------------
            # Only stop the visual listening
            # animation here.
            #
            # Do NOT unlock the microphone here.
            # Command processing still owns the lock.
            # ---------------------------------

            self.mic_widget._listening = False

            self.mic_widget.update()

        except Exception:

            pass

        # ---------------------------------
        # Cleanup Worker
        # ---------------------------------

        if current_worker:

            try:

                if current_worker.isRunning():

                    current_worker.wait(
                        3000
                    )

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

            self.status_label.setText(
                "Status : Ready"
            )

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

            # ---------------------------------
            # Unlock microphone
            # ---------------------------------

            QTimer.singleShot(

                120,

                self.unlock_microphone

            )

            # ---------------------------------
            # Return to DHEEPTHI standby
            # ---------------------------------

            if self.wake_word_enabled:

                QTimer.singleShot(

                    500,

                    self.start_wake_word_worker

                )

            return

        # ==================================================
        # DHEEPTHI WAKE WORD MODE
        # ==================================================

        if finished_mode == "wake":

            self.wake_word_running = False

            # ---------------------------------
            # If manual listening was requested,
            # DO NOT restart DHEEPTHI here.
            # ---------------------------------

            if self.manual_listening_requested:

                print(
                    "Wake listener stopped for manual microphone."
                )

                return

            # ---------------------------------
            # Normal Wake Word Loop
            # ---------------------------------

            if (
                self.wake_word_enabled
                and
                not self.manual_listening_requested
            ):

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
                        else None
                    )

                )

            return

        # ---------------------------------
        # Unknown / Safety
        # ---------------------------------

        self.manual_listening_requested = False

        QTimer.singleShot(

            120,

            self.unlock_microphone

        )

    # --------------------------------------------------
    # Start Voice Worker
    # --------------------------------------------------

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
    # Resize Event
    # --------------------------------------------------

    def resizeEvent(
        self,
        event
    ):

        super().resizeEvent(event)

        if hasattr(self, "loading_overlay"):

            self.loading_overlay.setGeometry(
                self.rect()
            )

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