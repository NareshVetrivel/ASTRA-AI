from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QLabel,
    QPushButton,
    QVBoxLayout
)
from PySide6.QtCore import Qt

from config import settings
from voice.speech_recognition import SpeechRecognizer
from planner.intent_detector import IntentDetector
from planner.entity_extractor import EntityExtractor
from automation.app_launcher import AppLauncher
from automation.app_closer import AppCloser


class MainWindow(QMainWindow):
    """
    Main window for the NOVA-AI desktop application.
    """

    def __init__(self):
        super().__init__()

        # Core Modules
        self.recognizer = SpeechRecognizer()
        self.intent_detector = IntentDetector()
        self.entity_extractor = EntityExtractor()
        self.app_launcher = AppLauncher()
        self.app_closer = AppCloser()

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

        # Show Analysis
        self.conversation_label.setText(
            f"You Said:\n\n{text}\n\n"
            f"Intent : {intent}\n"
            f"Entity : {entity}"
        )

        # Launch Application
        if intent == "launch_application" and entity:

            success = self.app_launcher.launch_application(
                entity
            )

            if success:

                self.status_label.setText(
                    "Status : Application Opened"
                )

            else:

                self.status_label.setText(
                    "Status : Launch Failed"
                )

        # Close Application
        elif intent == "close_application" and entity:

            success = self.app_closer.close_application(
                entity
            )

            if success:

                self.status_label.setText(
                    "Status : Application Closed"
                )

            else:

                self.status_label.setText(
                    "Status : Application Not Running"
                )

        else:

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

            self.status_label.setText(
                "Status : Failed"
            )