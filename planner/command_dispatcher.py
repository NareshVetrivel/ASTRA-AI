"""
Command Dispatcher Module

Routes the detected intent
to the appropriate controller.
"""


class CommandDispatcher:

    """
    Central command dispatcher.
    """

    def __init__(
        self,
        tts,
        app_launcher,
        app_closer,
        keyboard_controller,
        mouse_controller,
        window_controller,
        system_controller
    ):

        self.tts = tts

        self.app_launcher = app_launcher
        self.app_closer = app_closer

        self.keyboard = keyboard_controller
        self.mouse = mouse_controller
        self.window = window_controller
        self.system = system_controller

    def dispatch(
        self,
        intent,
        entity=None,
        typed_text=None
    ):
        """
        Execute the detected intent.

        Returns
        -------
        dict
        """

        try:

            # -------------------------
            # Launch Application
            # -------------------------

            if (
                intent == "launch_application"
                and entity
            ):

                app_name = entity.replace(
                    ".exe",
                    ""
                )

                self.tts.speak(
                    f"Opening {app_name}"
                )

                success = (
                    self.app_launcher
                    .launch_application(entity)
                )

                return {

                    "success": success,

                    "status":
                    (
                        "Status : Application Opened"
                        if success
                        else
                        "Status : Launch Failed"
                    )

                }

            # -------------------------
            # Close Application
            # -------------------------

            elif (
                intent == "close_application"
                and entity
            ):

                app_name = entity.replace(
                    ".exe",
                    ""
                )

                self.tts.speak(
                    f"Closing {app_name}"
                )

                success = (
                    self.app_closer
                    .close_application(entity)
                )

                return {

                    "success": success,

                    "status":
                    (
                        "Status : Application Closed"
                        if success
                        else
                        "Status : Application Not Running"
                    )

                }

            # -------------------------
            # Type Text
            # -------------------------

            elif (
                intent == "type_text"
                and typed_text
            ):

                self.tts.speak(
                    "Typing your text."
                )

                success = self.keyboard.type_text(
                    typed_text
                )

                return {

                    "success": success,

                    "status":
                    (
                        "Status : Typing Completed"
                        if success
                        else
                        "Status : Typing Failed"
                    )

                }

            # -------------------------
            # Copy
            # -------------------------

            elif intent == "copy":

                self.tts.speak("Copying.")

                success = self.keyboard.copy()

                return {

                    "success": success,

                    "status":
                    (
                        "Status : Copy Completed"
                        if success
                        else
                        "Status : Copy Failed"
                    )

                }

            # -------------------------
            # Paste
            # -------------------------

            elif intent == "paste":

                self.tts.speak("Pasting.")

                success = self.keyboard.paste()

                return {

                    "success": success,

                    "status":
                    (
                        "Status : Paste Completed"
                        if success
                        else
                        "Status : Paste Failed"
                    )

                }

            # -------------------------
            # Cut
            # -------------------------

            elif intent == "cut":

                self.tts.speak("Cutting.")

                success = self.keyboard.cut()

                return {

                    "success": success,

                    "status":
                    (
                        "Status : Cut Completed"
                        if success
                        else
                        "Status : Cut Failed"
                    )

                }

            # -------------------------
            # Undo
            # -------------------------

            elif intent == "undo":

                self.tts.speak("Undoing.")

                success = self.keyboard.undo()

                return {

                    "success": success,

                    "status":
                    (
                        "Status : Undo Completed"
                        if success
                        else
                        "Status : Undo Failed"
                    )

                }

            # -------------------------
            # Redo
            # -------------------------

            elif intent == "redo":

                self.tts.speak("Redoing.")

                success = self.keyboard.redo()

                return {

                    "success": success,

                    "status":
                    (
                        "Status : Redo Completed"
                        if success
                        else
                        "Status : Redo Failed"
                    )

                }

            # -------------------------
            # Enter
            # -------------------------

            elif intent == "press_enter":

                self.tts.speak(
                    "Pressing Enter."
                )

                success = self.keyboard.press_key(
                    "enter"
                )

                return {

                    "success": success,

                    "status":
                    (
                        "Status : Enter Pressed"
                        if success
                        else
                        "Status : Enter Failed"
                    )

                }

            # -------------------------
            # Tab
            # -------------------------

            elif intent == "press_tab":

                self.tts.speak(
                    "Pressing Tab."
                )

                success = self.keyboard.press_key(
                    "tab"
                )

                return {

                    "success": success,

                    "status":
                    (
                        "Status : Tab Pressed"
                        if success
                        else
                        "Status : Tab Failed"
                    )

                }

            # -------------------------
            # Backspace
            # -------------------------

            elif intent == "backspace":

                self.tts.speak(
                    "Pressing Backspace."
                )

                success = self.keyboard.backspace()

                return {

                    "success": success,

                    "status":
                    (
                        "Status : Backspace Pressed"
                        if success
                        else
                        "Status : Backspace Failed"
                    )

                }


            # -------------------------
            # Delete
            # -------------------------

            elif intent == "delete":

                self.tts.speak(
                    "Pressing Delete."
                )

                success = self.keyboard.delete()

                return {

                    "success": success,

                    "status":
                    (
                        "Status : Delete Pressed"
                        if success
                        else
                        "Status : Delete Failed"
                    )

                }

            # -------------------------
            # Select All
            # -------------------------

            elif intent == "select_all":

                self.tts.speak(
                    "Selecting all."
                )

                success = self.keyboard.hotkey(
                    "ctrl",
                    "a"
                )

                return {

                    "success": success,

                    "status":
                    (
                        "Status : Select All Completed"
                        if success
                        else
                        "Status : Select All Failed"
                    )

                }

            # -------------------------
            # Save
            # -------------------------

            elif intent == "save_file":

                self.tts.speak(
                    "Saving file."
                )

                success = self.keyboard.hotkey(
                    "ctrl",
                    "s"
                )

                return {

                    "success": success,

                    "status":
                    (
                        "Status : File Saved"
                        if success
                        else
                        "Status : Save Failed"
                    )

                }

            # -------------------------
            # Print
            # -------------------------

            elif intent == "print_file":

                self.tts.speak(
                    "Opening print dialog."
                )

                success = self.keyboard.hotkey(
                    "ctrl",
                    "p"
                )

                return {

                    "success": success,

                    "status":
                    (
                        "Status : Print Dialog Opened"
                        if success
                        else
                        "Status : Print Failed"
                    )

                }

            # -------------------------
            # Left Click
            # -------------------------

            elif intent == "left_click":

                self.tts.speak(
                    "Left clicking."
                )

                success = self.mouse.left_click()

                return {

                    "success": success,

                    "status":
                    (
                        "Status : Left Click Completed"
                        if success
                        else
                        "Status : Left Click Failed"
                    )

                }

            # -------------------------
            # Right Click
            # -------------------------

            elif intent == "right_click":

                self.tts.speak(
                    "Right clicking."
                )

                success = self.mouse.right_click()

                return {

                    "success": success,

                    "status":
                    (
                        "Status : Right Click Completed"
                        if success
                        else
                        "Status : Right Click Failed"
                    )

                }

            # -------------------------
            # Double Click
            # -------------------------

            elif intent == "double_click":

                self.tts.speak(
                    "Double clicking."
                )

                success = self.mouse.double_click()

                return {

                    "success": success,

                    "status":
                    (
                        "Status : Double Click Completed"
                        if success
                        else
                        "Status : Double Click Failed"
                    )

                }

            # -------------------------
            # Scroll Up
            # -------------------------

            elif intent == "scroll_up":

                self.tts.speak(
                    "Scrolling up."
                )

                success = self.mouse.scroll_up()

                return {

                    "success": success,

                    "status":
                    (
                        "Status : Scroll Up Completed"
                        if success
                        else
                        "Status : Scroll Up Failed"
                    )

                }

            # -------------------------
            # Scroll Down
            # -------------------------

            elif intent == "scroll_down":

                self.tts.speak(
                    "Scrolling down."
                )

                success = self.mouse.scroll_down()

                return {

                    "success": success,

                    "status":
                    (
                        "Status : Scroll Down Completed"
                        if success
                        else
                        "Status : Scroll Down Failed"
                    )

                }

            # -------------------------
            # Minimize Window
            # -------------------------

            elif intent == "minimize_window":

                self.tts.speak(
                    "Minimizing window."
                )

                success = self.window.minimize_window()

                return {

                    "success": success,

                    "status":
                    (
                        "Status : Window Minimized"
                        if success
                        else
                        "Status : Minimize Failed"
                    )

                }


            # -------------------------
            # Maximize Window
            # -------------------------

            elif intent == "maximize_window":

                self.tts.speak(
                    "Maximizing window."
                )

                success = self.window.maximize_window()

                return {

                    "success": success,

                    "status":
                    (
                        "Status : Window Maximized"
                        if success
                        else
                        "Status : Maximize Failed"
                    )

                }


            # -------------------------
            # Restore Window
            # -------------------------

            elif intent == "restore_window":

                self.tts.speak(
                    "Restoring window."
                )

                success = self.window.restore_window()

                return {

                    "success": success,

                    "status":
                    (
                        "Status : Window Restored"
                        if success
                        else
                        "Status : Restore Failed"
                    )

                }


            # -------------------------
            # Close Window
            # -------------------------

            elif intent == "close_window":

                self.tts.speak(
                    "Closing window."
                )

                success = self.window.close_window()

                return {

                    "success": success,

                    "status":
                    (
                        "Status : Window Closed"
                        if success
                        else
                        "Status : Close Failed"
                    )

                }

            # -------------------------
            # Volume Up
            # -------------------------

            elif intent == "volume_up":

                self.tts.speak(
                    "Increasing volume."
                )

                success = self.system.volume_up()

                return {

                    "success": success,

                    "status":
                    (
                        "Status : Volume Increased"
                        if success
                        else
                        "Status : Volume Up Failed"
                    )

                }

            # -------------------------
            # Volume Down
            # -------------------------

            elif intent == "volume_down":

                self.tts.speak(
                    "Decreasing volume."
                )

                success = self.system.volume_down()

                return {

                    "success": success,

                    "status":
                    (
                        "Status : Volume Decreased"
                        if success
                        else
                        "Status : Volume Down Failed"
                    )

                }

            # -------------------------
            # Mute
            # -------------------------

            elif intent == "mute":

                self.tts.speak(
                    "Muting audio."
                )

                success = self.system.mute()

                return {

                    "success": success,

                    "status":
                    (
                        "Status : Audio Toggled"
                        if success
                        else
                        "Status : Mute Failed"
                    )

                }

            # -------------------------
            # Lock Screen
            # -------------------------

            elif intent == "lock_screen":

                self.tts.speak(
                    "Locking computer."
                )

                success = self.system.lock_screen()

                return {

                    "success": success,

                    "status":
                    (
                        "Status : System Locked"
                        if success
                        else
                        "Status : Lock Failed"
                    )

                }

            # -------------------------
            # Screenshot
            # -------------------------

            elif intent == "take_screenshot":

                self.tts.speak(
                    "Taking screenshot."
                )

                success = self.system.take_screenshot()

                return {

                    "success": bool(success),

                    "status":
                    (
                        "Status : Screenshot Saved"
                        if success
                        else
                        "Status : Screenshot Failed"
                    )

                }

            # -------------------------
            # Task Manager
            # -------------------------

            elif intent == "open_task_manager":

                self.tts.speak(
                    "Opening Task Manager."
                )

                success = self.system.open_task_manager()

                return {

                    "success": success,

                    "status":
                    (
                        "Status : Task Manager Opened"
                        if success
                        else
                        "Status : Task Manager Failed"
                    )

                }

            # -------------------------
            # File Explorer
            # -------------------------

            elif intent == "open_file_explorer":

                self.tts.speak(
                    "Opening File Explorer."
                )

                success = self.system.open_file_explorer()

                return {

                    "success": success,

                    "status":
                    (
                        "Status : File Explorer Opened"
                        if success
                        else
                        "Status : File Explorer Failed"
                    )

                }

            return {

                "success": False,

                "status":
                "Status : No Action"

            }

        except Exception as error:

            print(
                f"Dispatcher Error : {error}"
            )

            return {

                "success": False,

                "status":
                "Status : Dispatcher Error"

            }