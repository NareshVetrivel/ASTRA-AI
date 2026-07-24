"""
Playwright Browser Automation

ASTRA-AI V1
Production Ready
"""

import subprocess
import time
from pathlib import Path
from urllib.parse import quote_plus

from playwright.sync_api import (
    sync_playwright,
    Error,
    TimeoutError,
)


class PlaywrightController:
    """
    Browser automation using Playwright
    connected to Chrome through CDP.
    """

    DEBUG_PORT = 9222

    USER_DATA_DIR = r"C:\ASTRA_AI_BROWSER"

    def __init__(self, profile="Default"):

        self.profile = profile

        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None

    # --------------------------------------------------
    # Reset Browser State
    # --------------------------------------------------

    def _reset_browser(self):
        """
        Clear all browser references.
        """

        self.browser = None
        self.context = None
        self.page = None

    # --------------------------------------------------
    # Chrome Executable
    # --------------------------------------------------

    def _chrome_path(self):

        paths = [

            r"C:\Program Files\Google\Chrome\Application\chrome.exe",

            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",

        ]

        for path in paths:

            if Path(path).exists():
                return path

        return None

    # --------------------------------------------------
    # Start Playwright
    # --------------------------------------------------

    def _start_playwright(self):

        if self.playwright is None:

            self.playwright = sync_playwright().start()

    # --------------------------------------------------
    # Launch Managed Chrome
    # --------------------------------------------------

    def _launch_chrome(self):

        chrome = self._chrome_path()

        if chrome is None:

            raise FileNotFoundError(
                "Google Chrome not found."
            )

        Path(self.USER_DATA_DIR).mkdir(
            parents=True,
            exist_ok=True
        )

        command = [

            chrome,

            f"--remote-debugging-port={self.DEBUG_PORT}",

            f"--user-data-dir={self.USER_DATA_DIR}",

            f"--profile-directory={self.profile}",

            "--new-window",

            "--no-first-run",

            "--no-default-browser-check",

            "--disable-popup-blocking",

        ]

        subprocess.Popen(command)

    # --------------------------------------------------
    # Connect CDP
    # --------------------------------------------------

    def _connect_cdp(self):

        self.browser = (

            self.playwright.chromium.connect_over_cdp(

                f"http://127.0.0.1:{self.DEBUG_PORT}"

            )

        )

    # --------------------------------------------------
    # Ensure Browser Connection
    # --------------------------------------------------

    def _connect(self):
        """
        Ensure browser connection is alive.
        Automatically reconnect if browser
        was closed manually.
        """

        try:

            if (
                self.page
                and
                not self.page.is_closed()
            ):

                return True

        except Exception:

            self._reset_browser()

        self._start_playwright()

        try:

            self._connect_cdp()

        except Exception:

            print("Launching managed Chrome...")

            self._launch_chrome()

            connected = False

            for _ in range(20):

                try:

                    self._connect_cdp()

                    connected = True

                    break

                except Exception:

                    time.sleep(0.5)

            if not connected:

                print(
                    "Unable to connect to Chrome CDP."
                )

                return False

        try:

            if self.browser.contexts:

                self.context = self.browser.contexts[0]

            else:

                self.context = self.browser.new_context()

            if self.context.pages:

                self.page = self.context.pages[-1]

            else:

                self.page = self.context.new_page()

                self.page.goto(
                    "https://www.google.com",
                    wait_until="domcontentloaded"
                )

        except Exception:

            self._reset_browser()

            return False

        print("Playwright Ready.")

        return True

    # --------------------------------------------------
    # Normalize URL
    # --------------------------------------------------

    @staticmethod
    def normalize_url(url):

        url = url.strip()

        if url.startswith((
            "http://",
            "https://"
        )):

            return url

        return "https://" + url

    # --------------------------------------------------
    # Retry Browser Action
    # --------------------------------------------------

    def _retry_action(self, action, *args):
        """
        Execute a browser action.

        If the browser was closed manually,
        reconnect automatically and retry once.
        """

        try:

            return action(*args)

        except Exception as error:

            message = str(error)

            if (
                "Target page" in message
                or "Target closed" in message
                or "context or browser has been closed" in message
            ):

                print("Browser disconnected.")
                print("Reconnecting...")

                self._reset_browser()

                if self._connect():

                    return action(*args)

            raise error

    # --------------------------------------------------
    # Open Website
    # --------------------------------------------------

    def open_website(
        self,
        website
    ):

        if not self._connect():
            return False

        def _open(site):

            url = self.normalize_url(site)

            self.page.goto(
                url,
                wait_until="domcontentloaded",
                timeout=60000
            )

            print(f"Opening : {url}")

            return True

        try:

            return self._retry_action(
                _open,
                website
            )

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
        query
    ):

        if not self._connect():
            return False

        def _search(search_query):

            url = (
                "https://www.google.com/search?q="
                + quote_plus(search_query)
            )

            self.page.goto(
                url,
                wait_until="domcontentloaded",
                timeout=60000
            )

            print(
                f"Searching Google : {search_query}"
            )

            return True

        try:

            return self._retry_action(
                _search,
                query
            )

        except Exception as error:

            print(
                f"Google Search Error : {error}"
            )

            return False

    # --------------------------------------------------
    # YouTube Search
    # --------------------------------------------------

    def youtube_search(
        self,
        query
    ):

        if not self._connect():
            return False

        def _search(search_query):

            url = (
                "https://www.youtube.com/results?search_query="
                + quote_plus(search_query)
            )

            self.page.goto(
                url,
                wait_until="domcontentloaded",
                timeout=60000
            )

            self.page.wait_for_selector(
                "ytd-video-renderer",
                timeout=20000
            )

            print(
                f"YouTube Search : {search_query}"
            )

            return True

        try:

            return self._retry_action(
                _search,
                query
            )

        except Exception as error:

            print(
                f"YouTube Search Error : {error}"
            )

            return False

    # --------------------------------------------------
    # Play YouTube
    # --------------------------------------------------

    def play_youtube(
        self,
        query
    ):

        if not self.youtube_search(query):
            return False

        def _play(search_query):

            first_video = self.page.locator(
                "ytd-video-renderer a#thumbnail"
            ).first

            first_video.wait_for(
                state="visible",
                timeout=15000
            )

            first_video.scroll_into_view_if_needed()

            first_video.click()

            self.page.wait_for_url(
                "**/watch*",
                timeout=15000
            )

            print(
                f"Playing : {search_query}"
            )

            return True

        try:

            return self._retry_action(
                _play,
                query
            )

        except TimeoutError:

            print(
                "Video page did not load."
            )

            return False

        except Error as error:

            print(
                f"Playwright Error : {error}"
            )

            return False

        except Exception as error:

            print(
                f"Play Error : {error}"
            )

            return False

    # --------------------------------------------------
    # Current URL
    # --------------------------------------------------

    def current_url(self):

        if not self._connect():
            return None

        try:

            return self.page.url

        except Exception:

            self._reset_browser()

            return None

    # --------------------------------------------------
    # Refresh Page
    # --------------------------------------------------

    def refresh(self):

        if not self._connect():
            return False

        try:

            self.page.reload(
                wait_until="domcontentloaded"
            )

            return True

        except Exception as error:

            print(
                f"Refresh Error : {error}"
            )

            self._reset_browser()

            return False

    # --------------------------------------------------
    # Close Browser Controller
    # --------------------------------------------------

    def close(self):
        """
        Gracefully shutdown Playwright.
        """

        try:

            if (
                self.page
                and
                not self.page.is_closed()
            ):

                self.page.close()

        except Exception:

            pass

        try:

            if self.context:

                self.context.close()

        except Exception:

            pass

        try:

            if self.browser:

                self.browser.close()

        except Exception:

            pass

        try:

            if self.playwright:

                self.playwright.stop()

        except Exception:

            pass

        self._reset_browser()

        self.playwright = None

        print(
            "Playwright shutdown completed."
        )