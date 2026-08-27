"""
Browser Controller Module

Provides browser automation for
ASTRA-AI.

Supported Browsers
------------------
- Google Chrome
- Microsoft Edge

Features
--------
- Browser Detection
- Persistent Playwright Chrome Session
- Safe Chrome Recovery
- Open Browser
- Open Website
- Google Search
- YouTube Search
- Play YouTube
- Google Search Result Click
- Browser Tab Controls

ASTRA-AI V1
"""

import subprocess
import threading
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

    Chrome automation is handled through one persistent
    PlaywrightController instance.

    Important:
    BrowserController does not directly manipulate internal
    Playwright state such as page/context/browser wherever
    possible.

    This prevents stale page references from being reused by
    higher-level application actions.
    """

    def __init__(self):

        # --------------------------------------------------
        # Thread Safety
        # --------------------------------------------------

        self._lock = threading.RLock()

        # --------------------------------------------------
        # Database
        # --------------------------------------------------

        self.database = DatabaseManager()

        self.browser_paths = self.load_browser_paths()

        # --------------------------------------------------
        # Keyboard
        # --------------------------------------------------

        self.keyboard = KeyboardController()

        # --------------------------------------------------
        # Persistent ASTRA Chrome Session
        # --------------------------------------------------

        if PlaywrightController:

            self.playwright = PlaywrightController(
                profile="Default"
            )

        else:

            self.playwright = None

        # --------------------------------------------------
        # Shutdown State
        # --------------------------------------------------

        self._closed = False

        # --------------------------------------------------
        # Chrome Profile Aliases
        # --------------------------------------------------

        self.chrome_profiles = {

            "naresh": "Default",
            "nares": "Default",
            "nareesh": "Default",
            "naresh s": "Default",
            "naresh profile": "Default",
            "college": "Profile 1",
            "college profile": "Profile 1",
            "naresh senthil": "Default",

        }

    # ======================================================
    # Load Browser Paths
    # ======================================================

    def load_browser_paths(self):
        """
        Load browser executable paths from the application
        database.
        """

        browsers = {}

        try:

            applications = (
                self.database
                .get_all_applications()
            )

        except Exception as error:

            print(
                f"Browser database load error : {error}"
            )

            return browsers

        for name, exe_name, full_path in applications:

            if not name:

                continue

            lower = str(name).lower().strip()

            if lower in {

                "chrome",
                "google chrome",

            }:

                browsers["chrome"] = full_path

            elif lower in {

                "edge",
                "microsoft edge",

            }:

                browsers["edge"] = full_path

        return browsers

    # ======================================================
    # Browser Exists
    # ======================================================

    def browser_exists(
        self,
        browser,
    ):
        """
        Check whether the requested browser exists.
        """

        if not browser:

            return False

        browser = (
            str(browser)
            .lower()
            .strip()
        )

        # Chrome can be controlled by Playwright even when
        # database lookup was incomplete.
        if browser == "chrome":

            if self.playwright:

                return True

        return browser in self.browser_paths

    # ======================================================
    # Get Browser Path
    # ======================================================

    def get_browser_path(
        self,
        browser,
    ):
        """
        Return browser executable path.
        """

        if not browser:

            return None

        return self.browser_paths.get(
            str(browser)
            .lower()
            .strip()
        )

    # ======================================================
    # Ensure Chrome
    # ======================================================

    def _ensure_chrome(self):
        """
        Safely prepare the persistent ASTRA Chrome session.

        BrowserController intentionally delegates connection
        management to PlaywrightController.
        """

        if self._closed:

            print(
                "Browser controller is closed."
            )

            return False

        if not self.playwright:

            print(
                "Playwright is unavailable."
            )

            return False

        try:

            return bool(
                self.playwright.ensure_browser()
            )

        except AttributeError:

            # Compatibility with the previous controller
            # while transitioning to the updated API.

            try:

                return bool(
                    self.playwright._connect()
                )

            except Exception as error:

                print(
                    f"Chrome connection error : {error}"
                )

                return False

        except Exception as error:

            print(
                f"Chrome connection error : {error}"
            )

            return False

    # ======================================================
    # Safely Bring Chrome Forward
    # ======================================================

    def _bring_chrome_to_front(self):
        """
        Bring ASTRA Chrome page forward.

        A foreground failure must never destroy the entire
        command. It is only a UI operation.
        """

        if not self.playwright:

            return False

        try:

            method = getattr(
                self.playwright,
                "bring_to_front",
                None,
            )

            if callable(method):

                return bool(method())

        except Exception as error:

            print(
                f"Chrome foreground warning : {error}"
            )

        return False

    # ======================================================
    # Open Browser
    # ======================================================

    def open_browser(
        self,
        browser="chrome",
    ):
        """
        Open or prepare a browser.

        Chrome:
            Uses the persistent ASTRA Playwright session.

        Other browsers:
            Uses normal subprocess launch.
        """

        if not browser:

            browser = "chrome"

        browser = (
            str(browser)
            .lower()
            .strip()
        )

        with self._lock:

            # ----------------------------------------------
            # Chrome
            # ----------------------------------------------

            if browser == "chrome":

                if not self._ensure_chrome():

                    print(
                        "Unable to prepare ASTRA Chrome."
                    )

                    return False

                print(
                    "Chrome ready through "
                    "Playwright CDP."
                )

                # Foreground failure is non-fatal.
                self._bring_chrome_to_front()

                return True

            # ----------------------------------------------
            # Other Browser
            # ----------------------------------------------

            if not self.browser_exists(browser):

                print(
                    f"{browser} not found."
                )

                return False

            browser_path = (
                self.get_browser_path(browser)
            )

            if not browser_path:

                print(
                    f"Browser path not found : {browser}"
                )

                return False

            try:

                subprocess.Popen(
                    [
                        browser_path,
                        "--new-window",
                    ]
                )

                print(
                    f"{browser.title()} launched."
                )

                return True

            except Exception as error:

                print(
                    f"Browser launch error : {error}"
                )

                return False

    # ======================================================
    # Open Chrome Profile
    # ======================================================

    def open_chrome_profile(
        self,
        profile_name,
        url=None,
    ):
        """
        Handle Chrome profile request.

        ASTRA V1 maintains one persistent managed Chrome
        session to prevent duplicate CDP connections.

        Profile aliases are still validated for command
        compatibility.
        """

        if not profile_name:

            return False

        profile_name = (
            str(profile_name)
            .lower()
            .strip()
        )

        # ----------------------------------------------
        # Resolve Profile Alias
        # ----------------------------------------------

        if profile_name == "default":

            profile = "Default"

        elif profile_name == "profile 1":

            profile = "Profile 1"

        else:

            profile = None

            for alias, folder in (
                self.chrome_profiles.items()
            ):

                if alias in profile_name:

                    profile = folder

                    break

        if not profile:

            print(
                "Unknown Chrome profile."
            )

            return False

        # ----------------------------------------------
        # Prepare Existing ASTRA Session
        # ----------------------------------------------

        if not self._ensure_chrome():

            return False

        # ----------------------------------------------
        # Optional URL
        # ----------------------------------------------

        if url:

            return self.open_website(
                url,
                browser="chrome",
            )

        self._bring_chrome_to_front()

        print(
            "Opened ASTRA Chrome session "
            f"for profile request : {profile}"
        )

        return True

    # ======================================================
    # Open Profile Alias
    # ======================================================

    def open_profile(
        self,
        profile_name,
        url=None,
    ):
        """
        Alias for opening Chrome profile.
        """

        return self.open_chrome_profile(
            profile_name,
            url,
        )

    # ======================================================
    # Normalize URL
    # ======================================================

    @staticmethod
    def normalize_url(url):
        """
        Convert user input into a valid browser URL.

        Examples:

            google.com
            -> https://google.com

            github.com
            -> https://github.com

            hello world
            -> Google search URL
        """

        url = str(url).strip()

        if not url:

            return ""

        lower_url = url.lower()

        if lower_url.startswith(
            (
                "http://",
                "https://",
            )
        ):

            return url

        # Search phrase rather than domain.
        if "." not in url:

            return (
                "https://www.google.com/search?q="
                + quote_plus(url)
            )

        return "https://" + url

    # ======================================================
    # Open Website
    # ======================================================

    def open_website(
        self,
        website,
        browser="chrome",
    ):
        """
        Open website using the selected browser.
        """

        if not website:

            return False

        browser = (
            str(browser)
            .lower()
            .strip()
        )

        url = self.normalize_url(
            website
        )

        if not url:

            return False

        with self._lock:

            # ----------------------------------------------
            # Chrome -> Playwright
            # ----------------------------------------------

            if browser == "chrome":

                if not self._ensure_chrome():

                    return False

                try:

                    success = bool(
                        self.playwright.open_website(
                            url
                        )
                    )

                    if success:

                        print(
                            f"Opening : {url}"
                        )

                    return success

                except Exception as error:

                    print(
                        f"Website error : {error}"
                    )

                    return False

            # ----------------------------------------------
            # Other Browser
            # ----------------------------------------------

            if not self.browser_exists(browser):

                print(
                    f"{browser} not found."
                )

                return False

            browser_path = (
                self.get_browser_path(browser)
            )

            if not browser_path:

                return False

            try:

                subprocess.Popen(
                    [
                        browser_path,
                        "--new-window",
                        url,
                    ]
                )

                print(
                    f"Opening : {url}"
                )

                return True

            except Exception as error:

                print(
                    f"Website error : {error}"
                )

                return False

    # ======================================================
    # Google Search
    # ======================================================

    def google_search(
        self,
        query,
        browser="chrome",
        new_tab=False,
    ):
        """
        Search Google.
        """

        if not query:

            return False

        browser = (
            str(browser)
            .lower()
            .strip()
        )

        with self._lock:

            if browser == "chrome":

                if not self._ensure_chrome():

                    return False

                try:

                    success = bool(
                        self.playwright.google_search(
                            query,
                            new_tab=new_tab,
                        )
                    )

                    if success:

                        print(
                            f"Searching Google : {query}"
                        )

                    return success

                except Exception as error:

                    print(
                        f"Google search error : {error}"
                    )

                    return False

            search_url = (
                "https://www.google.com/search?q="
                + quote_plus(
                    str(query)
                )
            )

            return self.open_website(
                search_url,
                browser,
            )

    # ======================================================
    # Open Google
    # ======================================================

    def open_google(
        self,
        browser="chrome",
    ):
        """
        Open Google homepage.
        """

        return self.open_website(
            "https://www.google.com",
            browser,
        )

    # ======================================================
    # YouTube Search
    # ======================================================

    def youtube_search(
        self,
        query,
        browser="chrome",
        new_tab=False,
    ):
        """
        Search YouTube.
        """

        if not query:

            return False

        browser = (
            str(browser)
            .lower()
            .strip()
        )

        with self._lock:

            if browser == "chrome":

                if not self._ensure_chrome():

                    return False

                try:

                    success = bool(
                        self.playwright.youtube_search(
                            query,
                            new_tab=new_tab,
                        )
                    )

                    if success:

                        print(
                            f"YouTube search : {query}"
                        )

                    return success

                except Exception as error:

                    print(
                        f"YouTube search error : {error}"
                    )

                    return False

            search_url = (
                "https://www.youtube.com/results"
                "?search_query="
                + quote_plus(
                    str(query)
                )
            )

            return self.open_website(
                search_url,
                browser,
            )

    # ======================================================
    # Open YouTube
    # ======================================================

    def open_youtube(
        self,
        browser="chrome",
    ):
        """
        Open YouTube homepage.
        """

        return self.open_website(
            "https://www.youtube.com",
            browser,
        )

    # ======================================================
    # Play YouTube Video
    # ======================================================

    def play_youtube(
        self,
        query,
        browser="chrome",
        new_tab=False,
    ):
        """
        Search and play the first YouTube result.
        """

        if not query:

            return False

        browser = (
            str(browser)
            .lower()
            .strip()
        )

        with self._lock:

            if browser == "chrome":

                if not self._ensure_chrome():

                    return False

                try:

                    return bool(
                        self.playwright.play_youtube(
                            query,
                            new_tab=new_tab,
                        )
                    )

                except Exception as error:

                    print(
                        f"Playwright YouTube error : "
                        f"{error}"
                    )

                    return False

            return self.youtube_search(
                query,
                browser,
                new_tab=new_tab,
            )

    # ======================================================
    # Click Google Search Result
    # ======================================================

    def click_search_result(
        self,
        index=0,
        browser="chrome",
    ):
        """
        Click Google search result.

        Result index is zero-based:

            0 -> first result
            1 -> second result
        """

        browser = (
            str(browser)
            .lower()
            .strip()
        )

        if browser != "chrome":

            print(
                "Search result clicking currently "
                "requires Chrome Playwright automation."
            )

            return False

        try:

            if index is None:

                index = 0

            index = int(index)

            if index < 0:

                index = 0

        except (
            TypeError,
            ValueError,
        ):

            index = 0

        with self._lock:

            if not self._ensure_chrome():

                return False

            try:

                return bool(
                    self.playwright.click_search_result(
                        index
                    )
                )

            except Exception as error:

                print(
                    f"Search result click error : "
                    f"{error}"
                )

                return False

    # ======================================================
    # New Tab
    # ======================================================

    def new_tab(self):
        """
        Open a new browser tab.
        """

        with self._lock:

            if self.playwright:

                try:

                    if self._ensure_chrome():

                        return bool(
                            self.playwright.new_tab()
                        )

                except Exception as error:

                    print(
                        f"Playwright new tab error : "
                        f"{error}"
                    )

            return self.keyboard.new_tab()

    # ======================================================
    # Close Tab
    # ======================================================

    def close_tab(self):
        """
        Close current browser tab.

        Keyboard fallback is intentionally used because
        the user may be controlling another foreground tab.
        """

        return self.keyboard.close_tab()

    # ======================================================
    # Next Tab
    # ======================================================

    def next_tab(self):

        return self.keyboard.next_tab()

    # ======================================================
    # Previous Tab
    # ======================================================

    def previous_tab(self):

        return self.keyboard.previous_tab()

    # ======================================================
    # Refresh
    # ======================================================

    def refresh(self):
        """
        Refresh active ASTRA Chrome page.
        """

        with self._lock:

            if self.playwright:

                try:

                    if self._ensure_chrome():

                        return bool(
                            self.playwright.refresh()
                        )

                except Exception as error:

                    print(
                        f"Playwright refresh error : "
                        f"{error}"
                    )

            return self.keyboard.refresh()

    # ======================================================
    # Open Downloads
    # ======================================================

    def open_downloads(self):

        return self.keyboard.downloads()

    # ======================================================
    # Open History
    # ======================================================

    def open_history(self):

        return self.keyboard.history()

    # ======================================================
    # Show Bookmarks
    # ======================================================

    def show_bookmarks(self):

        return self.keyboard.bookmarks()

    # ======================================================
    # Bookmark Current Page
    # ======================================================

    def bookmark_page(self):

        return self.keyboard.bookmark_page()

    # ======================================================
    # Address Bar
    # ======================================================

    def focus_address_bar(self):

        return self.keyboard.address_bar()

    # ======================================================
    # Browser Back
    # ======================================================

    def back(self):

        return self.keyboard.back()

    # ======================================================
    # Browser Forward
    # ======================================================

    def forward(self):

        return self.keyboard.forward()

    # ======================================================
    # Private Window
    # ======================================================

    def private_window(self):

        return self.keyboard.private_window()

    # ======================================================
    # Open URL In Current Tab
    # ======================================================

    def open_url_current_tab(
        self,
        website,
    ):
        """
        Open URL in current ASTRA browser tab.
        """

        if not website:

            return False

        url = self.normalize_url(
            website
        )

        if not url:

            return False

        with self._lock:

            if self.playwright:

                try:

                    if self._ensure_chrome():

                        return bool(
                            self.playwright.open_website(
                                url
                            )
                        )

                except Exception as error:

                    print(
                        f"Playwright current tab error : "
                        f"{error}"
                    )

            # Keyboard fallback.
            if not self.focus_address_bar():

                return False

            self.keyboard.type_text(
                url
            )

            self.keyboard.press_key(
                "enter"
            )

            return True

    # ======================================================
    # Google Search Current Tab
    # ======================================================

    def search_current_tab(
        self,
        query,
    ):
        """
        Perform Google search in current browser tab.
        """

        if not query:

            return False

        with self._lock:

            if self.playwright:

                try:

                    if self._ensure_chrome():

                        return bool(
                            self.playwright.google_search(
                                query,
                                new_tab=False,
                            )
                        )

                except Exception as error:

                    print(
                        f"Playwright current search error : "
                        f"{error}"
                    )

            search_url = (
                "https://www.google.com/search?q="
                + quote_plus(
                    str(query)
                )
            )

            return self.open_url_current_tab(
                search_url
            )

    # ======================================================
    # Close
    # ======================================================

    def close(self):
        """
        Cleanup BrowserController resources.

        PlaywrightController handles its own safe shutdown.
        Chrome itself is not intentionally closed here.
        """

        with self._lock:

            if self._closed:

                return

            self._closed = True

            print(
                "Shutting down BrowserController..."
            )

            # ----------------------------------------------
            # Playwright Cleanup
            # ----------------------------------------------

            try:

                if self.playwright:

                    self.playwright.close()

                    self.playwright = None

            except Exception as error:

                print(
                    f"Playwright cleanup error : "
                    f"{error}"
                )

            # ----------------------------------------------
            # Database Cleanup
            # ----------------------------------------------

            try:

                if self.database:

                    self.database.close()

                    self.database = None

            except Exception as error:

                print(
                    f"Database cleanup error : "
                    f"{error}"
                )

            print(
                "BrowserController shutdown completed."
            )