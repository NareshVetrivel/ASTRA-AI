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

import os
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

            # --------------------------------------------------
            # ASTRA Main Browser Session
            #
            # Uses the user's real Chrome User Data directory
            # and the professional Default profile.
            #
            # CDP Port:
            #     9222
            #
            # This single controller is reused for:
            #     - YouTube
            #     - Google Search
            #     - Search Result Click
            #     - Multi-command browser automation
            # --------------------------------------------------

            self.playwright = PlaywrightController(
                profile="Default"
            )

        else:

            self.playwright = None

        # Prevent duplicate shutdown
        self._closed = False

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

            "naresh senthil": "Default"

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
        Open or attach to a browser.

        Chrome:
            Uses the ASTRA Playwright session on CDP 9222
            with the user's Default professional profile.

        Other browsers:
            Keep the existing subprocess launch behavior.
        """

        if not browser:

            browser = "chrome"

        browser = browser.lower().strip()

        if not self.browser_exists(browser):

            print(
                f"{browser} not found."
            )

            return False

        # --------------------------------------------------
        # Chrome → Existing ASTRA Playwright Session
        # --------------------------------------------------

        if (
            browser == "chrome"
            and
            self.playwright
        ):

            try:

                # Connect to existing Chrome :9222.
                # If unavailable, PlaywrightController will
                # launch the configured Default profile.

                success = self.playwright._connect()

                if success:

                    print(
                        "Chrome ready through "
                        "Playwright CDP : 9222"
                    )

                    # --------------------------------------------------
                    # Bring the connected Chrome page to the front.
                    # --------------------------------------------------

                    try:

                        if (
                            self.playwright.page
                            and
                            not self.playwright.page.is_closed()
                        ):

                            self.playwright.page.bring_to_front()

                            print(
                                "Chrome page brought to front."
                            )

                    except Exception as error:

                        print(
                            f"Chrome foreground warning : {error}"
                        )

                    return True

                print(
                    "Unable to connect to ASTRA Chrome."
                )

                return False

            except Exception as error:

                print(
                    f"Playwright Chrome Error : {error}"
                )

                return False

        # --------------------------------------------------
        # Non-Chrome browsers → Existing behavior
        # --------------------------------------------------

        try:

            command = [
                self.browser_paths[browser],
                "--new-window"
            ]

            subprocess.Popen(
                command
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

        profile_name = profile_name.lower().strip()

        # Dispatcher may already pass "Default", "Profile 1", etc.
        if profile_name.lower() == "default":
            profile = "Default"

        elif profile_name.lower() == "profile 1":
            profile = "Profile 1"

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

        real_user_data = os.path.join(
            os.environ["LOCALAPPDATA"],
            "Google",
            "Chrome",
            "User Data"
        )

        command = [
            chrome,
            f"--user-data-dir={real_user_data}",
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

            success = self.open_chrome_profile(
                "Default",
                url
            )

            if success:
                print(f"Opening : {url}")

            return success

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
        browser="chrome",
        new_tab=False
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

            if self.playwright:

                success = (
                    self.playwright
                    .google_search(
                        query,
                        new_tab=new_tab
                    )
                )

                if success:

                    print(
                        f"Searching Google : {query}"
                    )

                return success

            # ----------------------------------------------
            # Fallback when Playwright is unavailable
            # ----------------------------------------------

            success = self.open_chrome_profile(
                "Default",
                search_url
            )

            if success:

                print(
                    f"Searching Google : {query}"
                )

            return success

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
        browser="chrome",
        new_tab=False
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

            if self.playwright:

                success = (
                    self.playwright
                    .youtube_search(
                        query,
                        new_tab=new_tab
                    )
                )

                if success:

                    print(
                        f"YouTube Search : {query}"
                    )

                return success

            # ----------------------------------------------
            # Fallback
            # ----------------------------------------------

            success = self.open_chrome_profile(
                "Default",
                search_url
            )

            if success:

                print(
                    f"YouTube Search : {query}"
                )

            return success

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
        browser="chrome",
        new_tab=False
    ):
        """
        Play first YouTube result using the
        main ASTRA Chrome session.

        Uses:
            Chrome Default profile
            CDP port 9222

        This keeps YouTube automation inside
        the same browser session used by
        other browser and multi-command tasks.
        """

        if not query:

            return False

        if self.playwright:

            try:

                return (
                    self.playwright
                    .play_youtube(
                        query,
                        new_tab=new_tab
                    )
                )

            except Exception as error:

                print(
                    f"Playwright Failed : {error}"
                )

        # --------------------------------------------------
        # Fallback
        # --------------------------------------------------

        return self.youtube_search(
            query,
            browser,
            new_tab=new_tab
        )

    # --------------------------------------------------
    # Click Google Search Result
    # --------------------------------------------------

    def click_search_result(
        self,
        index=0,
        browser="chrome"
    ):
        """
        Click a Google search result using Playwright.

        Parameters
        ----------
        index:
            Zero-based search result index.

            0 = first result
            1 = second result
            2 = third result

        browser:
            Browser name.

        Returns
        -------
        bool
            True when the result was clicked successfully.
        """

        try:

            if index is None:

                index = 0

            try:

                index = int(index)

            except (
                TypeError,
                ValueError
            ):

                index = 0

            if index < 0:

                index = 0

            # --------------------------------------------------
            # Prefer the existing Playwright controller.
            # --------------------------------------------------

            if self.playwright:

                return (
                    self.playwright
                    .click_search_result(index)
                )

            # --------------------------------------------------
            # Fallback
            #
            # If Playwright is unavailable, do not perform a
            # blind mouse click because we cannot reliably know
            # which Google result is the requested result.
            # --------------------------------------------------

            print(
                "Playwright is unavailable. "
                "Cannot safely click search result."
            )

            return False

        except Exception as error:

            print(
                f"Search Result Click Error : {error}"
            )

            return False

    # --------------------------------------------------
    # New Tab
    # --------------------------------------------------

    def new_tab(self):
        """
        Open a new browser tab using the active
        Playwright browser session.
        """

        if self.playwright:

            try:

                return self.playwright.new_tab()

            except Exception as error:

                print(
                    f"Playwright New Tab Error : {error}"
                )

        # Fallback
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
        Cleanup browser resources safely.
        """

        if self._closed:
            return

        self._closed = True

        try:

            if self.playwright:

                self.playwright.close()

                self.playwright = None

        except Exception as error:

            print(
                f"Playwright Cleanup Error : {error}"
            )

        try:

            if self.database:

                self.database.close()

                self.database = None

        except Exception as error:

            print(f"Database Cleanup Error : {error}")