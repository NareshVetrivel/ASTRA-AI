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
        system_controller,
        file_finder,
        folder_manager,
        file_manager,
        browser_controller
    ):

        self.tts = tts

        self.app_launcher = app_launcher
        self.app_closer = app_closer

        self.keyboard = keyboard_controller
        self.mouse = mouse_controller
        self.window = window_controller
        self.system = system_controller
        self.file_finder = file_finder

        self.folder_manager = folder_manager
        self.file_manager = file_manager
        self.browser = browser_controller
        

    def dispatch(
        self,
        intent,
        entity=None,
        typed_text=None,
        browser=None,
        website=None,
        search_query=None,
        profile=None
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

                # Website takes priority
                if website:

                    self.tts.speak(
                        f"Opening {website}"
                    )

                    return {

                        "success": self.browser.open_website(
                            website,
                            browser or entity
                        ),

                        "status": "Status : Website Opened"

                    }

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
            # Arrow Up
            # -------------------------

            elif intent == "arrow_up":

                self.tts.speak(
                    "Moving up."
                )

                success = self.keyboard.arrow_up()

                return {

                    "success": success,

                    "status":
                    (
                        "Status : Arrow Up Pressed"
                        if success
                        else
                        "Status : Arrow Up Failed"
                    )

                }

            # -------------------------
            # Arrow Down
            # -------------------------

            elif intent == "arrow_down":

                self.tts.speak(
                    "Moving down."
                )

                success = self.keyboard.arrow_down()

                return {

                    "success": success,

                    "status":
                    (
                        "Status : Arrow Down Pressed"
                        if success
                        else
                        "Status : Arrow Down Failed"
                    )

                }

            # -------------------------
            # Arrow Left
            # -------------------------

            elif intent == "arrow_left":

                self.tts.speak(
                    "Moving left."
                )

                success = self.keyboard.arrow_left()

                return {

                    "success": success,

                    "status":
                    (
                        "Status : Arrow Left Pressed"
                        if success
                        else
                        "Status : Arrow Left Failed"
                    )

                }

            # -------------------------
            # Arrow Right
            # -------------------------

            elif intent == "arrow_right":

                self.tts.speak(
                    "Moving right."
                )

                success = self.keyboard.arrow_right()

                return {

                    "success": success,

                    "status":
                    (
                        "Status : Arrow Right Pressed"
                        if success
                        else
                        "Status : Arrow Right Failed"
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
            # Home
            # -------------------------

            elif intent == "home":

                self.tts.speak(
                    "Pressing Home."
                )

                success = self.keyboard.home()

                return {

                    "success": success,

                    "status":
                    (
                        "Status : Home Pressed"
                        if success
                        else
                        "Status : Home Failed"
                    )

                }

            # -------------------------
            # End
            # -------------------------

            elif intent == "end":

                self.tts.speak(
                    "Pressing End."
                )

                success = self.keyboard.end()

                return {

                    "success": success,

                    "status":
                    (
                        "Status : End Pressed"
                        if success
                        else
                        "Status : End Failed"
                    )

                }

            # -------------------------
            # Page Up
            # -------------------------

            elif intent == "page_up":

                self.tts.speak(
                    "Pressing Page Up."
                )

                success = self.keyboard.page_up()

                return {

                    "success": success,

                    "status":
                    (
                        "Status : Page Up Pressed"
                        if success
                        else
                        "Status : Page Up Failed"
                    )

                }

            # -------------------------
            # Page Down
            # -------------------------

            elif intent == "page_down":

                self.tts.speak(
                    "Pressing Page Down."
                )

                success = self.keyboard.page_down()

                return {

                    "success": success,

                    "status":
                    (
                        "Status : Page Down Pressed"
                        if success
                        else
                        "Status : Page Down Failed"
                    )

                }

            # -------------------------
            # Escape
            # -------------------------

            elif intent == "escape":

                self.tts.speak(
                    "Pressing Escape."
                )

                success = self.keyboard.escape()

                return {

                    "success": success,

                    "status":
                    (
                        "Status : Escape Pressed"
                        if success
                        else
                        "Status : Escape Failed"
                    )

                }

            # -------------------------
            # Space
            # -------------------------

            elif intent == "space":

                self.tts.speak(
                    "Pressing Space."
                )

                success = self.keyboard.space()

                return {

                    "success": success,

                    "status":
                    (
                        "Status : Space Pressed"
                        if success
                        else
                        "Status : Space Failed"
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

            # -------------------------
            # Open File
            # -------------------------

            elif (
                intent == "open_file"
                and entity
            ):

                self.tts.speak(
                    f"Opening {entity}"
                )

                success = self.file_finder.open_file(
                    entity
                )

                return {

                    "success": success,

                    "status":
                    (
                        "Status : File Opened"
                        if success
                        else
                        "Status : File Not Found"
                    )

                }

            # -------------------------
            # Open Folder
            # -------------------------

            elif (

                intent == "open_folder"

                and entity

            ):

                self.tts.speak(

                    f"Opening {entity}"

                )

                success = (

                    self.folder_manager

                    .open_folder(entity)

                )

                return {

                    "success": success,

                    "status":

                    (

                        "Status : Folder Opened"

                        if success

                        else

                        "Status : Folder Not Found"

                    )

                }

            # -------------------------
            # Create File
            # -------------------------

            elif (
                intent == "create_file"
                and entity
            ):

                self.tts.speak(
                    f"Creating {entity}"
                )

                success = self.file_manager.create_file(
                    entity
                )

                return {

                    "success": success,

                    "status":
                    (
                        "Status : File Created"
                        if success
                        else
                        "Status : Create Failed"
                    )

                }

            # -------------------------
            # Delete File
            # -------------------------

            elif (
                intent == "delete_file"
                and entity
            ):

                self.tts.speak(
                    f"Deleting {entity}"
                )

                success = self.file_manager.delete_file(
                    entity
                )

                return {

                    "success": success,

                    "status":
                    (
                        "Status : File Deleted"
                        if success
                        else
                        "Status : Delete Failed"
                    )

                }

            # -------------------------
            # Rename File
            # -------------------------

            elif intent == "rename_file":

                return {

                    "success": False,

                    "status":

                    "Status : Pending"

                }

            # -------------------------
            # Copy File
            # -------------------------

            elif intent == "copy_file":

                return {

                    "success": False,

                    "status":

                    "Status : Pending"

                }

            # -------------------------
            # Move File
            # -------------------------

            elif intent == "move_file":

                return {

                    "success": False,

                    "status":

                    "Status : Pending"

                }

            # -------------------------
            # Compress File
            # -------------------------

            elif (
                intent == "compress_file"
                and entity
            ):

                success = self.file_manager.compress_file(
                    entity
                )

                return {

                    "success": success,

                    "status":
                    (
                        "Status : ZIP Created"
                        if success
                        else
                        "Status : Compression Failed"
                    )

                }

            # -------------------------
            # Extract ZIP
            # -------------------------

            elif (
                intent == "extract_zip"
                and entity
            ):

                success = self.file_manager.extract_zip(
                    entity
                )

                return {

                    "success": success,

                    "status":
                    (
                        "Status : ZIP Extracted"
                        if success
                        else
                        "Status : Extraction Failed"
                    )

                }

            # -------------------------
            # Create Folder
            # -------------------------

            elif (

                intent == "create_folder"

                and entity

            ):

                success = (

                    self.folder_manager

                    .create_folder(entity)

                )

                return {

                    "success": success,

                    "status":

                    (

                        "Status : Folder Created"

                        if success

                        else

                        "Status : Create Failed"

                    )

                }
            
            # -------------------------
            # Rename Folder
            # -------------------------

            elif intent == "rename_folder":

                return {

                    "success": False,

                    "status":

                    "Status : Pending"

                }
            
            # -------------------------
            # Delete Folder
            # -------------------------

            elif (

                intent == "delete_folder"

                and entity

            ):

                success = (

                    self.folder_manager

                    .delete_folder(entity)

                )

                return {

                    "success": success,

                    "status":

                    (

                        "Status : Folder Deleted"

                        if success

                        else

                        "Status : Delete Failed"

                    )

                }
            
            # -------------------------
            # Move Folder
            # -------------------------

            elif intent == "move_folder":

                return {

                    "success": False,

                    "status":

                    "Status : Pending"

                }
            
            # -------------------------
            # Copy Folder
            # -------------------------

            elif intent == "copy_folder":

                return {

                    "success": False,

                    "status":

                    "Status : Pending"

                }
            
            # -------------------------
            # Empty Recycle Bin
            # -------------------------

            elif intent == "empty_recycle_bin":

                success = (

                    self.folder_manager

                    .empty_recycle_bin()

                )

                return {

                    "success": success,

                    "status":

                    (

                        "Status : Recycle Bin Emptied"

                        if success

                        else

                        "Status : Failed"

                    )

                }

            # -------------------------
            # Search by Extension
            # -------------------------

            elif intent == "search_extension":

                return {

                    "success": False,

                    "status":

                    "Status : Pending"

                }


            # -------------------------
            # Search by Date
            # -------------------------

            elif intent == "search_date":

                return {

                    "success": False,

                    "status":

                    "Status : Pending"

                }

            # -------------------------
            # Open Website
            # -------------------------

            elif intent == "open_website":

                if not website:

                    return {

                        "success": False,

                        "status": "Status : Invalid Website"

                    }

                self.tts.speak(

                    f"Opening {website}"

                )

                success = self.browser.open_website(

                    website,

                    browser or "chrome"

                )

                return {

                    "success": success,

                    "status":

                    (

                        "Status : Website Opened"

                        if success

                        else

                        "Status : Website Failed"

                    )

                }

            # -------------------------
            # Google Home
            # -------------------------

            elif intent == "open_google":

                success = self.browser.open_google(
                    browser or "chrome"
                )

                return {

                    "success": success,

                    "status": "Status : Google Opened"

                }

            # -------------------------
            # Youtube Home
            # -------------------------

            elif intent == "open_youtube":

                success = self.browser.open_youtube(
                    browser or "chrome"
                )

                return {

                    "success": success,

                    "status": "Status : YouTube Opened"

                }

            # -------------------------
            # Google Search
            # -------------------------

            elif intent == "google_search":

                self.tts.speak(
                    f"Searching {search_query}"
                )

                success = self.browser.google_search(

                    search_query,

                    browser or "chrome"

                )

                return {

                    "success": success,

                    "status":

                    (

                        "Status : Search Completed"

                        if success

                        else

                        "Status : Search Failed"

                    )

                }

            # -------------------------
            # YouTube Search
            # -------------------------

            elif intent == "youtube_search":

                self.tts.speak(

                    f"Searching YouTube for {search_query}"

                )

                success = self.browser.youtube_search(

                    search_query,

                    browser or "chrome"

                )

                return {

                    "success": success,

                    "status":

                    (

                        "Status : YouTube Search"

                        if success

                        else

                        "Status : Search Failed"

                    )

                }

            # -------------------------
            # Play YouTube
            # -------------------------

            elif intent == "play_youtube":

                query = search_query or entity

                self.tts.speak(
                    f"Playing {query} on YouTube."
                )

                success = self.browser.play_youtube(

                    query,

                    browser or "chrome"

                )

                return {

                    "success": success,

                    "status":

                    (

                        "Status : Playing Video"

                        if success

                        else

                        "Status : Play Failed"

                    )

                }

            # -------------------------
            # New Tab
            # -------------------------

            elif intent == "new_tab":

                success = self.browser.new_tab()

                return {
                    "success": success,
                    "status": "Status : New Tab"
                }

            # -------------------------
            # Close Tab
            # -------------------------

            elif intent == "close_tab":

                success = self.browser.close_tab()

                return {
                    "success": success,
                    "status": "Status : Tab Closed"
                }

            # -------------------------
            # Next Tab
            # -------------------------

            elif intent == "next_tab":

                success = self.browser.next_tab()

                return {
                    "success": success,
                    "status": "Status : Next Tab"
                }

            # -------------------------
            # Previous Tab
            # -------------------------

            elif intent == "previous_tab":

                success = self.browser.previous_tab()

                return {
                    "success": success,
                    "status": "Status : Previous Tab"
                }

            # -------------------------
            # Refresh 
            # -------------------------

            elif intent == "refresh":

                success = self.browser.refresh()

                return {
                    "success": success,
                    "status": "Status : Page Refreshed"
                }

            # -------------------------
            # Downloads
            # -------------------------

            elif intent == "browser_downloads":

                success = self.browser.open_downloads()

                return {
                    "success": success,
                    "status": "Status : Downloads Opened"
                }

            # -------------------------
            # History
            # -------------------------

            elif intent == "browser_history":

                success = self.browser.open_history()

                return {
                    "success": success,
                    "status": "Status : History Opened"
                }

            # -------------------------
            # Bookmark Bar
            # -------------------------

            elif intent == "browser_bookmarks":

                success = self.browser.show_bookmarks()

                return {
                    "success": success,
                    "status": "Status : Bookmark Bar"
                }

            # -------------------------
            # Bookmark Page
            # -------------------------

            elif intent == "bookmark_page":

                success = self.browser.bookmark_page()

                return {
                    "success": success,
                    "status": "Status : Page Bookmarked"
                }

            # -------------------------
            # Address Bar
            # -------------------------

            elif intent == "address_bar":

                success = self.browser.focus_address_bar()

                return {
                    "success": success,
                    "status": "Status : Address Bar"
                }

            # -------------------------
            # Browser Back
            # -------------------------

            elif intent == "browser_back":

                success = self.browser.back()

                return {
                    "success": success,
                    "status": "Status : Back"
                }

            # -------------------------
            # Browser Forward
            # -------------------------

            elif intent == "browser_forward":

                success = self.browser.forward()

                return {
                    "success": success,
                    "status": "Status : Forward"
                }

            # -------------------------
            # Private Window
            # -------------------------

            elif intent == "private_window":

                success = self.browser.private_window()

                return {
                    "success": success,
                    "status": "Status : Private Window"
                }

            # -------------------------
            # Open Chrome Profile
            # -------------------------

            elif intent == "open_chrome_profile":

                self.tts.speak(
                    f"Opening {profile} profile."
                )

                success = self.browser.open_profile(
                    profile,
                    website
                )

                return {

                    "success": success,

                    "status":
                    (
                        "Status : Chrome Profile Opened"
                        if success
                        else
                        "Status : Profile Failed"
                    )

                }

            # -------------------------
            # Search by Size
            # -------------------------

            elif intent == "search_size":

                return {

                    "success": False,

                    "status":

                    "Status : Pending"

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