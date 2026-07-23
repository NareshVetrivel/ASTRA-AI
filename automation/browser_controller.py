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
try:
    from automation.playwright_controller import PlaywrightController
except ImportError:
    PlaywrightController = None


class BrowserController:
    """
    Browser automation controller.
    """

    def __init__(self):

        self.database = DatabaseManager()

        self.browser_paths = self.load_browser_paths()

        self.keyboard = KeyboardController()

        if PlaywrightController:
            self.playwright = PlaywrightController(
                profile="Default"
            )
        else:
            self.playwright = None

        # ---------------------------------
        # Chrome Profiles
        # ---------------------------------

        self.chrome_profiles = {

            "naresh": "Default",

            "nares": "Default",

            "nareesh": "Default",

            "naresh s": "Default",

            "naresh profile": "Default",

            "college": "Profile 1",

            "college profile": "Profile 1",

            "naresh senthil": "Profile 1",

            "ragxii": "Profile 12",

            "ragxii profile": "Profile 12"

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

        if not browser:
            return False

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

        if not browser:
            return None

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

            command = [
                self.browser_paths[browser],
                "--new-window"
            ]

            if browser == "chrome":
                command.append("--remote-debugging-port=9222")

            subprocess.Popen(command)

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

        profile_name = profile_name.lower().strip()

        # Dispatcher may already pass "Default", "Profile 1", etc.
        if profile_name in {
            "default",
            "profile 1",
            "profile 12"
        }:
            profile = profile_name.title().replace("Profile", "Profile")

        else:
            profile = None

            for alias, folder in self.chrome_profiles.items():

                if alias in profile_name:

                    profile = folder

                    break

        if not profile:

            print("Unknown Chrome profile.")

            return False

        chrome = self.browser_paths.get("chrome")

        if not chrome:

            return False

        command = [
            chrome,
            "--user-data-dir=C:\\ASTRA_AI_BROWSER",
            f"--profile-directory={profile}",
            "--remote-debugging-port=9222",
            "--new-window",
            "--no-first-run",
            "--no-default-browser-check"
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
    # Open Profile (Alias)
    # --------------------------------------------------

    def open_profile(
        self,
        profile_name,
        url=None
    ):
        """
        Alias for opening Chrome profile.
        """

        return self.open_chrome_profile(
            profile_name,
            url
        )

    # --------------------------------------------------
    # Normalize URL
    # --------------------------------------------------

    @staticmethod
    def normalize_url(url):

        url = url.strip().lower()

        if url.startswith("http://"):

            return url

        if url.startswith("https://"):

            return url

        if "." not in url:

            return (
                "https://www.google.com/search?q="
                + quote_plus(url)
            )

        return "https://" + url

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

        browser_path = self.get_browser_path(browser)

        if not browser_path:

            print(f"Browser path not found : {browser}")

            return False

        try:

            subprocess.Popen([
                browser_path,
                url
            ])

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
        
        browser_path = self.get_browser_path(browser)

        if not browser_path:

            return False

        search_url = (

            "https://www.google.com/search?q="

            + quote_plus(query)

        )

        try:

            subprocess.Popen([
                browser_path,
                search_url
            ])

            print(

                f"Searching Google : {query}"

            )

            return True

        except Exception as error:

            print(

                f"Google Search Error : {error}"

            )

            return False

    def open_google(
        self,
        browser="chrome"
    ):
        """
        Open Google homepage.
        """

        return self.open_website(
            "google.com",
            browser
        )

    # --------------------------------------------------
    # YouTube Search
    # --------------------------------------------------

    def youtube_search(
        self,
        query,
        browser="chrome"
    ):
        """
        Search YouTube.
        """

        if not query:
            return False

        browser = browser.lower()

        if not self.browser_exists(browser):
            return False
        
        browser_path = self.get_browser_path(browser)

        if not browser_path:

            return False

        search_url = (
            "https://www.youtube.com/results?search_query="
            + quote_plus(query)
        )

        try:

            subprocess.Popen([
                browser_path,
                search_url
            ])

            print(f"YouTube Search : {query}")

            return True

        except Exception as error:

            print(error)

            return False

    def open_youtube(
        self,
        browser="chrome"
    ):
        """
        Open YouTube homepage.
        """

        return self.open_website(
            "youtube.com",
            browser
        )

    # --------------------------------------------------
    # Play YouTube Video
    # --------------------------------------------------

    def play_youtube(
        self,
        query,
        browser="chrome"
    ):
        """
        Play first YouTube result.
        """

        if self.playwright:

            try:
                if not query:
                    return False

                return self.playwright.play_youtube(query)

            except Exception as error:

                print(f"Playwright Failed : {error}")

        # Fallback
        return self.youtube_search(query, browser)

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

        if self.playwright:
            self.playwright.close()

        self.database.close()