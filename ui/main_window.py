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


class MainWindow(QMainWindow):
    """
    Main window for the NOVA-AI desktop application.
    """

    def __init__(self):
        super().__init__()

        # Speech Recognizer
        self.recognizer = SpeechRecognizer()

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

        # Central Widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Main Layout
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)

        # -----------------------------
        # Status Label
        # -----------------------------
        self.status_label = QLabel(
            f"Status : {settings.DEFAULT_STATUS}"
        )
        self.status_label.setAlignment(Qt.AlignCenter)

        # -----------------------------
        # Conversation Label
        # -----------------------------
        self.conversation_label = QLabel(
            settings.WELCOME_MESSAGE
        )
        self.conversation_label.setAlignment(Qt.AlignCenter)
        self.conversation_label.setWordWrap(True)

        # -----------------------------
        # Microphone Button
        # -----------------------------
        self.microphone_button = QPushButton(
            settings.MIC_BUTTON_TEXT
        )
        self.microphone_button.setFixedSize(100, 100)

        # Button Click Event
        self.microphone_button.clicked.connect(
            self.start_listening
        )

        # -----------------------------
        # Add Widgets
        # -----------------------------
        layout.addWidget(self.status_label)

        layout.addSpacing(20)

        layout.addWidget(self.conversation_label)

        layout.addSpacing(20)

        layout.addWidget(
            self.microphone_button,
            alignment=Qt.AlignCenter
        )

        central_widget.setLayout(layout)

    def start_listening(self):
        """
        Start listening when the microphone
        button is clicked.
        """

        # Update Status
        self.status_label.setText(
            "Status : Listening..."
        )

        # Listen
        text = self.recognizer.listen()

        # If speech recognized
        if text:

            self.conversation_label.setText(
                f"You:\n\n{text}"
            )

            self.status_label.setText(
                "Status : Completed"
            )

        # If recognition failed
        else:

            self.conversation_label.setText(
                "Sorry!\n\nI couldn't understand."
            )

            self.status_label.setText(
                "Status : Failed"
            )