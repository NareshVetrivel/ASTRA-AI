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

        # Launch Application
        if intent == "launch_application" and entity:
            
            app_name = entity.replace(".exe", "")

            self.tts.speak(
                f"Opening {app_name}"
            )

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

            app_name = entity.replace(".exe", "")

            self.tts.speak(
                f"Closing {app_name}"
            )

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

        elif intent == "type_text" and typed_text:

            self.tts.speak(
                "Typing your text."
            )

            success = self.keyboard_controller.type_text(
                typed_text
            )

            if success:

                self.status_label.setText(
                    "Status : Typing Completed"
                )

            else:

                self.status_label.setText(
                    "Status : Typing Failed"
                )

        elif intent == "copy":

            self.tts.speak(
                "Copying."
            )

            success = self.keyboard_controller.copy()

            if success:

                self.status_label.setText(
                    "Status : Copy Completed"
                )

            else:

                self.status_label.setText(
                "Status : Copy Failed"
                )

        elif intent == "paste":

            self.tts.speak(
                "Pasting."
            )

            success = self.keyboard_controller.paste()

            if success:

                self.status_label.setText(
                    "Status : Paste Completed"
                )

            else:

                self.status_label.setText(
                    "Status : Paste Failed"
                )

        elif intent == "cut":

            self.tts.speak(
                "Cutting."
            )

            success = self.keyboard_controller.cut()

            if success:

                self.status_label.setText(
                    "Status : Cut Completed"
                )

            else:

                self.status_label.setText(
                    "Status : Cut Failed"
                )

        elif intent == "undo":

            self.tts.speak(
                "Undoing."
            )

            success = self.keyboard_controller.undo()

            if success:

                self.status_label.setText(
                    "Status : Undo Completed"
                )

            else:

                self.status_label.setText(
                    "Status : Undo Failed"
                )

        elif intent == "redo":

            self.tts.speak(
                "Redoing."
            )

            success = self.keyboard_controller.redo()

            if success:

                self.status_label.setText(
                    "Status : Redo Completed"
                )

            else:

                self.status_label.setText(
                    "Status : Redo Failed"
                )

        elif intent == "press_enter":

            self.tts.speak(
                "Pressing Enter."
            )

            success = self.keyboard_controller.press_key("enter")

            if success:

                self.status_label.setText(
                    "Status : Enter Pressed"
                )

            else:

                self.status_label.setText(
                    "Status : Enter Failed"
                )

        elif intent == "press_tab":

            self.tts.speak(
                "Pressing Tab."
            )

            success = self.keyboard_controller.press_key("tab")

            if success:

                self.status_label.setText(
                    "Status : Tab Pressed"
                )

            else:

                self.status_label.setText(
                    "Status : Tab Failed"
                )

        elif intent == "select_all":

            self.tts.speak(
                "Selecting all."
            )

            success = self.keyboard_controller.hotkey(
                "ctrl",
                "a"
            )

            if success:
            
                self.status_label.setText(
                    "Status : Select All Completed"
                )

            else:
        
                self.status_label.setText(
                    "Status : Select All Failed"
                )

        elif intent == "save_file":

            self.tts.speak(
                "Saving file."
            )

            success = self.keyboard_controller.hotkey(
                "ctrl",
                "s"
            )

            if success:

                self.status_label.setText(
                    "Status : File Saved"
                )

            else:

                self.status_label.setText(
                    "Status : Save Failed"
                )

        elif intent == "print_file":

            self.tts.speak(
                "Opening print dialog."
            )

            success = self.keyboard_controller.hotkey(
                "ctrl",
                "p"
            )

            if success:

                self.status_label.setText(
                    "Status : Print Dialog Opened"
                )

            else:

                self.status_label.setText(
                    "Status : Print Failed"
                )

        elif intent == "left_click":

            self.tts.speak(
                "Left clicking."
            )

            success = self.mouse_controller.left_click()

            if success:

                self.status_label.setText(
                    "Status : Left Click Completed"
                )

            else:

                self.status_label.setText(
                    "Status : Left Click Failed"
                )

        elif intent == "right_click":

            self.tts.speak(
                "Right clicking."
            )

            success = self.mouse_controller.right_click()

            if success:

                self.status_label.setText(
                    "Status : Right Click Completed"
                )

            else:

                self.status_label.setText(
                    "Status : Right Click Failed"
                )

        elif intent == "double_click":

            self.tts.speak(
                "Double clicking."
            )

            success = self.mouse_controller.double_click()

            if success:

                self.status_label.setText(
                    "Status : Double Click Completed"
                )

            else:

                self.status_label.setText(
                    "Status : Double Click Failed"
                )

        elif intent == "scroll_up":

            self.tts.speak(
                "Scrolling up."
            )

            success = self.mouse_controller.scroll_up()

            if success:

                self.status_label.setText(
                    "Status : Scroll Up Completed"
                )

            else:

                self.status_label.setText(
                    "Status : Scroll Up Failed"
                )

        elif intent == "scroll_down":

            self.tts.speak(
                "Scrolling down."
            )

            success = self.mouse_controller.scroll_down()

            if success:

                self.status_label.setText(
                    "Status : Scroll Down Completed"
                )

            else:

                self.status_label.setText(
                    "Status : Scroll Down Failed"
            )

        elif intent == "minimize_window":

            self.tts.speak(
                "Minimizing window."
            )

            success = self.window_controller.minimize_window()

            if success:

                self.status_label.setText(
                    "Status : Window Minimized"
                )

            else:

                self.status_label.setText(
                    "Status : Minimize Failed"
                )

        elif intent == "maximize_window":

            self.tts.speak(
                "Maximizing window."
            )

            success = self.window_controller.maximize_window()

            if success:

                self.status_label.setText(
                    "Status : Window Maximized"
                )

            else:

                self.status_label.setText(
                    "Status : Maximize Failed"
                )

        elif intent == "restore_window":

            self.tts.speak(
                "Restoring window."
            )

            success = self.window_controller.restore_window()

            if success:

                self.status_label.setText(
                    "Status : Window Restored"
                )

            else:

                self.status_label.setText(
                    "Status : Restore Failed"
                )

        elif intent == "close_window":

            self.tts.speak(
                "Closing window."
            )

            success = self.window_controller.close_window()

            if success:

                self.status_label.setText(
                    "Status : Window Closed"
                )

            else:

                self.status_label.setText(
                    "Status : Close Failed"
                )

        # -----------------------------
        # System Automation
        # -----------------------------

        elif intent == "volume_up":

            self.tts.speak(
            "Increasing volume."
            )

            success = self.system_controller.volume_up()

            if success:

                self.status_label.setText(
                    "Status : Volume Increased"
                )

            else:

                self.status_label.setText(
                    "Status : Volume Up Failed"
                )


        elif intent == "volume_down":

            self.tts.speak(
                "Decreasing volume."
            )

            success = self.system_controller.volume_down()

            if success:

                self.status_label.setText(
                    "Status : Volume Decreased"
                )

            else:

                self.status_label.setText(
                    "Status : Volume Down Failed"
                )


        elif intent == "mute":

            self.tts.speak(
                "Muting audio."
            )

            success = self.system_controller.mute()

            if success:

                self.status_label.setText(
                    "Status : Audio Toggled"
                )

            else:

                self.status_label.setText(
                    "Status : Mute Failed"
                )


        elif intent == "lock_screen":

            self.tts.speak(
                "Locking computer."
            )

            success = self.system_controller.lock_screen()

            if success:

                self.status_label.setText(
                    "Status : System Locked"
                )

            else:

                self.status_label.setText(
                    "Status : Lock Failed"
                )

        elif intent == "take_screenshot":

            self.tts.speak(
                "Taking screenshot."
            )

            success = self.system_controller.take_screenshot()

            if success:

                self.status_label.setText(
                    "Status : Screenshot Saved"
                )

            else:

                self.status_label.setText(
                    "Status : Screenshot Failed"
                )


        elif intent == "open_task_manager":

            self.tts.speak(
                "Opening Task Manager."
            )

            success = self.system_controller.open_task_manager()

            if success:
            
                self.status_label.setText(
                    "Status : Task Manager Opened"
                )

            else:

                self.status_label.setText(
                    "Status : Task Manager Failed"
                )


        elif intent == "open_file_explorer":

            self.tts.speak(
                "Opening File Explorer."
            )

            success = self.system_controller.open_file_explorer()

            if success:

                self.status_label.setText(
                    "Status : File Explorer Opened"
            )

            else:

                self.status_label.setText(
                    "Status : File Explorer Failed"
                )

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