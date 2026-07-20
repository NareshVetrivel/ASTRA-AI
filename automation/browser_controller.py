"""
Browser Controller Module

Provides browser automation for
ASTRA-AI.

Supported Browsers
------------------
- Google Chrome
- Microsoft Edge

Features (Part 1)
-----------------
- Browser Detection
- Open Browser
- Open Website
- Google Search

ASTRA-AI V1
"""

import subprocess
from urllib.parse import quote_plus

from database.database_manager import DatabaseManager
from automation.keyboard_controller import KeyboardController


class BrowserController:
    """
    Browser automation controller.
    """

    def __init__(self):

        self.database = DatabaseManager()

        self.browser_paths = self.load_browser_paths()

        self.keyboard = KeyboardController()

        # ---------------------------------
        # Chrome Profiles
        # ---------------------------------

        self.chrome_profiles = {

            "naresh": "Default",

            "naresh s": "Default",

            "college": "Profile 1",

            "naresh senthil": "Profile 1",

            "ragxii": "Profile 12"

        }

    # --------------------------------------------------
    # Load Browser Paths
    # --------------------------------------------------

    def load_browser_paths(self):
        """
        Load browser executable paths
        from the application database.
        """

        browsers = {}

        applications = self.database.get_all_applications()

        for name, exe_name, full_path in applications:

            lower = name.lower()

            if lower in {

                "chrome",
                "google chrome"

            }:

                browsers["chrome"] = full_path

            elif lower in {

                "edge",
                "microsoft edge"

            }:

                browsers["edge"] = full_path

        return browsers

    # --------------------------------------------------
    # Browser Exists
    # --------------------------------------------------

    def browser_exists(
        self,
        browser
    ):
        """
        Check whether browser exists.
        """

        return browser.lower() in self.browser_paths

    # --------------------------------------------------
    # Get Browser Path
    # --------------------------------------------------

    def get_browser_path(
        self,
        browser
    ):
        """
        Return executable path.
        """

        return self.browser_paths.get(
            browser.lower()
        )

    # --------------------------------------------------
    # Open Browser
    # --------------------------------------------------

    def open_browser(
        self,
        browser="chrome"
    ):
        """
        Launch browser.
        """

        browser = browser.lower()

        if not self.browser_exists(browser):

            print(
                f"{browser} not found."
            )

            return False

        try:

            subprocess.Popen(

            [

            self.browser_paths[browser],

            "--new-window"

            ]

            )

            print(

                f"{browser.title()} launched."

            )

            return True

        except Exception as error:

            print(

                f"Browser Launch Error : {error}"

            )

            return False

    # --------------------------------------------------
    # Open Chrome Profile
    # --------------------------------------------------

    def open_chrome_profile(
        self,
        profile_name,
        url=None
    ):
        """
        Open Chrome using a specific profile.
        """

        if not profile_name:

            return False

        profile_name = profile_name.lower()

        profile = self.chrome_profiles.get(profile_name)

        if not profile:

            print("Unknown Chrome profile.")

            return False

        chrome = self.browser_paths.get("chrome")

        if not chrome:

            return False

        command = [

            chrome,

            f'--profile-directory={profile}'

        ]

        if url:

            command.append(

                self.normalize_url(url)

            )

        try:

            subprocess.Popen(command)

            print(

                f"Opened {profile_name} profile."

            )

            return True

        except Exception as error:

            print(error)

            return False

    # --------------------------------------------------
    # Normalize URL
    # --------------------------------------------------

    @staticmethod
    def normalize_url(
        url
    ):
        """
        Convert website text
        into valid URL.
        """

        url = url.strip().lower()

        if url.startswith(

            "http://"

        ):

            return url

        if url.startswith(

            "https://"

        ):

            return url

        if "." not in url:

            url += ".com"

        return f"https://{url}"

    # --------------------------------------------------
    # Open Website
    # --------------------------------------------------

    def open_website(
        self,
        website,
        browser="chrome"
    ):
        """
        Open website using
        selected browser.
        """

        if not website:

            return False

        browser = browser.lower()

        if not self.browser_exists(browser):

            return False

        url = self.normalize_url(
            website
        )

        try:

            subprocess.Popen(

            [
            self.browser_paths[browser],

            "--new-tab",

            url

            ]
            )

            print(

                f"Opening : {url}"

            )

            return True

        except Exception as error:

            print(

                f"Website Error : {error}"

            )

            return False

    # --------------------------------------------------
    # Google Search
    # --------------------------------------------------

    def google_search(
        self,
        query,
        browser="chrome"
    ):
        """
        Search Google.
        """

        if not query:

            return False

        browser = browser.lower()

        if not self.browser_exists(browser):

            return False

        search_url = (

            "https://www.google.com/search?q="

            + quote_plus(query)

        )

        try:

            subprocess.Popen(
            [
            self.browser_paths[browser],

            "--new-tab",

            search_url

            ]
            )

            print(

                f"Searching Google : {query}"

            )

            return True

        except Exception as error:

            print(

                f"Google Search Error : {error}"

            )

            return False

    # --------------------------------------------------
    # New Tab
    # --------------------------------------------------

    def new_tab(self):
        """
        Open a new browser tab.
        """

        return self.keyboard.new_tab()

    # --------------------------------------------------
    # Close Tab
    # --------------------------------------------------

    def close_tab(self):
        """
        Close current browser tab.
        """

        return self.keyboard.close_tab()

    # --------------------------------------------------
    # Next Tab
    # --------------------------------------------------

    def next_tab(self):
        """
        Switch to next browser tab.
        """

        return self.keyboard.next_tab()

    # --------------------------------------------------
    # Previous Tab
    # --------------------------------------------------

    def previous_tab(self):
        """
        Switch to previous browser tab.
        """

        return self.keyboard.previous_tab()

    # --------------------------------------------------
    # Refresh
    # --------------------------------------------------

    def refresh(self):
        """
        Refresh current page.
        """

        return self.keyboard.refresh()

    # --------------------------------------------------
    # Open Downloads
    # --------------------------------------------------

    def open_downloads(self):
        """
        Open browser downloads page.
        """

        return self.keyboard.downloads()

    # --------------------------------------------------
    # Open History
    # --------------------------------------------------

    def open_history(self):
        """
        Open browser history.
        """

        return self.keyboard.history()

    # --------------------------------------------------
    # Show Bookmarks
    # --------------------------------------------------

    def show_bookmarks(self):
        """
        Show bookmark bar.
        """

        return self.keyboard.bookmarks()

    # --------------------------------------------------
    # Bookmark Current Page
    # --------------------------------------------------

    def bookmark_page(self):
        """
        Bookmark current page.
        """

        return self.keyboard.bookmark_page()

    # --------------------------------------------------
    # Address Bar
    # --------------------------------------------------

    def focus_address_bar(self):
        """
        Focus browser address bar.
        """

        return self.keyboard.address_bar()

    # --------------------------------------------------
    # Browser Back
    # --------------------------------------------------

    def back(self):
        """
        Go back.
        """

        return self.keyboard.back()

    # --------------------------------------------------
    # Browser Forward
    # --------------------------------------------------

    def forward(self):
        """
        Go forward.
        """

        return self.keyboard.forward()

    # --------------------------------------------------
    # Private Window
    # --------------------------------------------------

    def private_window(self):
        """
        Open Incognito / InPrivate window.
        """

        return self.keyboard.private_window()

    # --------------------------------------------------
    # Open URL in Current Tab
    # --------------------------------------------------

    def open_url_current_tab(
        self,
        website
    ):
        """
        Open website in current tab.
        """

        if not website:

            return False

        website = self.normalize_url(
            website
        )

        if not self.focus_address_bar():

            return False

        self.keyboard.type_text(
            website
        )

        self.keyboard.press_key(
            "enter"
        )

        return True

    # --------------------------------------------------
    # Google Search Current Tab
    # --------------------------------------------------

    def search_current_tab(
        self,
        query
    ):
        """
        Perform Google search
        in current browser tab.
        """

        if not query:

            return False

        search_url = (

            "https://www.google.com/search?q="

            + quote_plus(query)

        )

        return self.open_url_current_tab(
            search_url
        )

    # --------------------------------------------------
    # Close
    # --------------------------------------------------

    def close(self):
        """
        Close database.
        """

        self.database.close()