from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QLabel,
    QPushButton,
    QVBoxLayout
)
from PySide6.QtCore import Qt

from config import settings
from voice.whisper_recognizer import WhisperRecognizer
from planner.intent_detector import IntentDetector
from planner.entity_extractor import EntityExtractor
from planner.text_extractor import TextExtractor
from planner.command_dispatcher import CommandDispatcher
from automation.keyboard_controller import KeyboardController
from automation.mouse_controller import MouseController
from automation.window_controller import WindowController
from automation.system_controller import SystemController
from automation.app_launcher import AppLauncher
from automation.app_closer import AppCloser
from voice.text_to_speech import TextToSpeech

class MainWindow(QMainWindow):
    """
    Main window for the ASTRA-AI desktop application.
    """

    def __init__(self):
        super().__init__()

        # Core Modules
        self.recognizer = WhisperRecognizer()
        self.tts = TextToSpeech()

        self.intent_detector = IntentDetector()
        self.entity_extractor = EntityExtractor()
        self.text_extractor = TextExtractor()

        self.app_launcher = AppLauncher()
        self.app_closer = AppCloser()

        self.keyboard_controller = KeyboardController()
        self.mouse_controller = MouseController()
        self.window_controller = WindowController()
        self.system_controller = SystemController()

        self.dispatcher = CommandDispatcher(
            tts=self.tts,
            app_launcher=self.app_launcher,
            app_closer=self.app_closer,
            keyboard_controller=self.keyboard_controller,
            mouse_controller=self.mouse_controller,
            window_controller=self.window_controller,
            system_controller=self.system_controller
        )
        # Window Settings
        self.setWindowTitle(settings.WINDOW_TITLE)
        self.setMinimumSize(
            settings.WINDOW_WIDTH,
            settings.WINDOW_HEIGHT
        )

        # Build UI
        self.setup_ui()

    def setup_ui(self):
        """
        Create the user interface.
        """

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)

        # Status Label
        self.status_label = QLabel(
            f"Status : {settings.DEFAULT_STATUS}"
        )
        self.status_label.setAlignment(Qt.AlignCenter)

        # Conversation Label
        self.conversation_label = QLabel(
            settings.WELCOME_MESSAGE
        )
        self.conversation_label.setAlignment(Qt.AlignCenter)
        self.conversation_label.setWordWrap(True)

        # Microphone Button
        self.microphone_button = QPushButton(
            settings.MIC_BUTTON_TEXT
        )

        self.microphone_button.setFixedSize(100, 100)

        self.microphone_button.clicked.connect(
            self.start_listening
        )

        # Add Widgets
        layout.addWidget(self.status_label)

        layout.addSpacing(20)

        layout.addWidget(self.conversation_label)

        layout.addSpacing(20)

        layout.addWidget(
            self.microphone_button,
            alignment=Qt.AlignCenter
        )

        central_widget.setLayout(layout)

    def process_command(self, text):
        """
        Process the recognized command.
        """

        intent = self.intent_detector.detect_intent(text)

        entity = self.entity_extractor.extract_application(text)

        typed_text = self.text_extractor.extract_text(text)

        # Show Analysis
        self.conversation_label.setText(
            f"You Said:\n\n{text}\n\n"
            f"Intent : {intent}\n"
            f"Entity : {entity}\n"
            f"Text   : {typed_text}"
        )

        dispatcher_result = self.dispatcher.dispatch(
            intent=intent,
            entity=entity,
            typed_text=typed_text
        )

        if dispatcher_result["success"]:

            self.status_label.setText(
                dispatcher_result["status"]
            )

            return

        else:

            self.tts.speak(
                "Sorry. I could not understand your command."
            )
            self.status_label.setText(
                "Status : No Action"
            )

    def start_listening(self):
        """
        Start listening when microphone button is clicked.
        """

        self.status_label.setText(
            "Status : Listening..."
        )

        text = self.recognizer.listen()
        
        if text:

            self.status_label.setText(
                "Status : Processing..."
            )

            self.process_command(text)

        else:

            self.conversation_label.setText(
                "Sorry!\n\nI couldn't understand."
            )

            self.tts.speak(
                "Sorry. I could not hear you."
            )

            self.status_label.setText(
                "Status : Failed"
            )