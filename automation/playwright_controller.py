"""
Playwright Browser Automation

ASTRA-AI V1
"""

import subprocess
import time
from pathlib import Path
from urllib.parse import quote_plus

from playwright.sync_api import (
    sync_playwright,
    Error,
    TimeoutError
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
    # Chrome Executable
    # --------------------------------------------------

    def _chrome_path(self):

        paths = [

            r"C:\Program Files\Google\Chrome\Application\chrome.exe",

            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"

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

            "--disable-popup-blocking"

        ]

        subprocess.Popen(command)

    # --------------------------------------------------
    # Connect To CDP
    # --------------------------------------------------

    def _connect_cdp(self):

        self.browser = self.playwright.chromium.connect_over_cdp(

            f"http://127.0.0.1:{self.DEBUG_PORT}"

        )

    # --------------------------------------------------
    # Ensure Browser
    # --------------------------------------------------

    def _connect(self):

        try:

            if (

                self.page

                and

                not self.page.is_closed()

            ):

                return True

        except Exception:

            pass

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

        print("Playwright Ready.")

        return True

    # --------------------------------------------------
    # Normalize URL
    # --------------------------------------------------

    @staticmethod
    def normalize_url(url):

        url = url.strip()

        if url.startswith(("http://", "https://")):

            return url

        return "https://" + url

    # --------------------------------------------------
    # Open Website
    # --------------------------------------------------

    def open_website(
        self,
        website
    ):

        if not self._connect():
            return False

        try:

            url = self.normalize_url(
                website
            )

            self.page.goto(
                url,
                wait_until="domcontentloaded",
                timeout=60000
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
        query
    ):

        if not self._connect():
            return False

        try:

            url = (

                "https://www.google.com/search?q="

                + quote_plus(query)

            )

            self.page.goto(
                url,
                wait_until="domcontentloaded",
                timeout=60000
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
    # YouTube Search
    # --------------------------------------------------

    def youtube_search(
        self,
        query
    ):

        if not self._connect():
            return False

        try:

            url = (

                "https://www.youtube.com/results?search_query="

                + quote_plus(query)

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
                f"YouTube Search : {query}"
            )

            return True

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

        try:

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
                f"Playing : {query}"
            )

            return True

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

        return self.page.url

    # --------------------------------------------------
    # Refresh
    # --------------------------------------------------

    def refresh(self):

        if not self._connect():
            return False

        self.page.reload(
            wait_until="domcontentloaded"
        )

        return True

    # --------------------------------------------------
    # Close
    # --------------------------------------------------

    def close(self):

        try:

            if self.playwright:

                self.playwright.stop()

        except Exception:

            pass

        self.browser = None
        self.context = None
        self.page = None
        self.playwright = None