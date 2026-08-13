"""
Playwright Browser Automation

ASTRA-AI V1
Production Ready
"""

import os
import subprocess
import time
from pathlib import Path
from urllib.parse import quote_plus
from automation.keyboard_controller import KeyboardController

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

    def __init__(
        self,
        profile="Default",
        user_data_dir=None
    ):

        self.profile = profile

        # --------------------------------------------------
        # ASTRA Dedicated Chrome Profile
        # --------------------------------------------------
        #
        # Chrome versions with modern remote-debugging
        # restrictions should use a separate user-data-dir
        # for CDP automation.
        #
        # This is NOT Guest mode.
        #
        # The user can login to the professional/public
        # Google account once inside this ASTRA profile.
        # --------------------------------------------------

        self.USER_DATA_DIR = (
            user_data_dir
            or
            r"C:\ASTRA_AI_BROWSER"
        )

        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None

        self.keyboard = KeyboardController()

        # Prevent duplicate cleanup
        self._closed = False

    # --------------------------------------------------
    # Reset Browser State
    # --------------------------------------------------

    def _reset_browser(self):
        """
        Clear stale browser/page references.

        IMPORTANT:
        This method does NOT start another CDP connection.
        The Playwright driver lifecycle is managed separately.
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
    # Restart Playwright Driver
    # --------------------------------------------------

    def _restart_playwright(self):
        """
        Restart the Playwright driver after a broken
        Node.js transport / EPIPE failure.

        The Chrome browser itself is not intentionally
        closed here. We only restart the Python ↔
        Playwright Node driver connection.
        """

        print(
            "Restarting Playwright driver..."
        )

        try:

            if self.playwright:

                self.playwright.stop()

        except Exception as error:

            print(
                f"Playwright stop warning : {error}"
            )

        self.playwright = None

        self._reset_browser()

        self._closed = False

        try:

            self.playwright = sync_playwright().start()

            print(
                "Playwright driver restarted."
            )

            return True

        except Exception as error:

            print(
                f"Playwright restart failed : {error}"
            )

            self.playwright = None

            return False

    # --------------------------------------------------
    # Launch Managed Chrome
    # --------------------------------------------------

    def _launch_chrome(self):

        chrome = self._chrome_path()

        if chrome is None:

            raise FileNotFoundError(
                "Google Chrome not found."
            )

        command = [

            chrome,

            f"--remote-debugging-port={self.DEBUG_PORT}",

            f"--user-data-dir={self.USER_DATA_DIR}",

            f"--profile-directory={self.profile}",

            "--new-window",

            "--start-maximized",

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
        Ensure one usable Playwright/CDP browser connection.

        Strategy:

            1. Reuse current live page.
            2. Reuse current live context/browser.
            3. Connect to Chrome CDP only when no usable connection exists.
            4. Launch ASTRA-managed Chrome only when CDP is unavailable.

        IMPORTANT:
            Normal browser actions must not repeatedly create CDP
            connections.
        """

        # --------------------------------------------------
        # 1. Reuse existing live page
        # --------------------------------------------------

        try:

            if self.page and not self.page.is_closed():

                return True

        except Exception:

            self.page = None

        # --------------------------------------------------
        # 2. Reuse existing browser/context
        # --------------------------------------------------

        try:

            if self.browser:

                contexts = self.browser.contexts

                if contexts:

                    self.context = contexts[-1]

                    pages = self.context.pages

                    for candidate in reversed(pages):

                        try:

                            if not candidate.is_closed():

                                self.page = candidate

                                return True

                        except Exception:

                            continue

        except Exception as error:

            print(
                f"Existing browser reference unavailable : {error}"
            )

            # Clear only Python references.
            # Do NOT restart Playwright here.
            self.browser = None
            self.context = None
            self.page = None

        # --------------------------------------------------
        # 3. Start Playwright if required
        # --------------------------------------------------

        try:

            self._start_playwright()

        except Exception as error:

            print(
                f"Playwright start error : {error}"
            )

            return False

        # --------------------------------------------------
        # 4. Connect to existing Chrome CDP
        # --------------------------------------------------

        try:

            print(
                "Connecting to existing Chrome "
                f"CDP : {self.DEBUG_PORT}"
            )

            self._connect_cdp()

            print(
                "Connected to existing Chrome."
            )

        except Exception:

            print(
                "Existing Chrome CDP unavailable."
            )

            # --------------------------------------------------
            # Launch ASTRA managed Chrome
            # --------------------------------------------------

            try:

                print(
                    "Launching managed Chrome "
                    f"with profile : {self.profile}"
                )

                self._launch_chrome()

            except Exception as error:

                print(
                    f"Chrome Launch Error : {error}"
                )

                self.browser = None
                self.context = None
                self.page = None

                return False

            # --------------------------------------------------
            # Wait for CDP
            # --------------------------------------------------

            connected = False

            for _ in range(30):

                try:

                    self._connect_cdp()

                    connected = True

                    print(
                        "Connected to managed Chrome."
                    )

                    break

                except Exception:

                    time.sleep(0.5)

            if not connected:

                print(
                    "Unable to connect to Chrome CDP "
                    f"on port {self.DEBUG_PORT}."
                )

                self.browser = None
                self.context = None
                self.page = None

                return False

        # --------------------------------------------------
        # 5. Select browser context
        # --------------------------------------------------

        try:

            contexts = self.browser.contexts

            if not contexts:

                print(
                    "Chrome connected, but no browser "
                    "context was found."
                )

                return False

            self.context = contexts[-1]

        except Exception as error:

            print(
                f"Browser Context Error : {error}"
            )

            self.browser = None
            self.context = None
            self.page = None

            return False

        # --------------------------------------------------
        # 6. Select existing page
        # --------------------------------------------------

        try:

            pages = self.context.pages

            self.page = None

            for candidate in reversed(pages):

                try:

                    if not candidate.is_closed():

                        self.page = candidate

                        break

                except Exception:

                    continue

            # --------------------------------------------------
            # No usable page
            # --------------------------------------------------

            if self.page is None:

                if not self._create_page():

                    print(
                        "Unable to create initial Chrome tab."
                    )

                    self.page = None

                    return False

        except Exception as error:

            print(
                f"Browser page selection error : {error}"
            )

            self.page = None

            return False

        # --------------------------------------------------
        # 7. Final validation
        # --------------------------------------------------

        try:

            if not self.page:

                return False

            if self.page.is_closed():

                self.page = None

                return False

        except Exception:

            self.page = None

            return False

        print(
            "Playwright Ready."
        )

        print(
            f"Chrome Profile : {self.profile}"
        )

        print(
            f"CDP Port : {self.DEBUG_PORT}"
        )

        return True

    # --------------------------------------------------
    # Safely Create Browser Tab
    # --------------------------------------------------

    def _create_page(self):
        """
        Safely create a new browser tab using the existing
        Playwright browser context.

        This method NEVER reconnects CDP and NEVER restarts
        the Playwright driver.
        """

        if not self.context:

            print(
                "Browser context unavailable."
            )

            return False

        try:

            # --------------------------------------------------
            # Verify context is still accessible
            # --------------------------------------------------

            pages = self.context.pages

            # --------------------------------------------------
            # Create new page
            # --------------------------------------------------

            new_page = self.context.new_page()

            self.page = new_page

            print(
                "New Playwright page created."
            )

            return True

        except Exception as error:

            message = str(error)

            print(
                f"Page creation error : {message}"
            )

            # --------------------------------------------------
            # IMPORTANT:
            #
            # Do NOT reconnect here.
            # Do NOT restart Playwright here.
            # Do NOT treat EPIPE as a normal retry.
            # --------------------------------------------------

            self.page = None

            if (
                "Target closed" in message
                or
                "Target page" in message
                or
                "context or browser has been closed" in message
            ):

                print(
                    "Browser target is no longer available."
                )

            return False

    # --------------------------------------------------
    # Create New Browser Tab
    # --------------------------------------------------

    def new_tab(self):
        """
        Create a new browser tab using the existing
        Chrome/CDP browser session.

        The existing Chrome profile and browser process
        are preserved.
        """

        if not self._connect():

            return False

        try:

            if not self.context:

                print(
                    "Browser context unavailable."
                )

                return False

            # --------------------------------------------------
            # Create the tab.
            #
            # _create_page() now handles target creation safely.
            # --------------------------------------------------

            if self._create_page():

                print(
                    "New Chrome tab created."
                )

                return True

            print(
                "Failed to create new Chrome tab."
            )

            return False

        except Exception as error:

            print(
                f"New Tab Error : {error}"
            )

            self._reset_browser()

            return False

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
        Execute a browser action safely.

        IMPORTANT:
            EPIPE / broken-pipe errors are NOT automatically
            retried or followed by a CDP reconnect.

        Only normal Playwright target errors are allowed
        one controlled retry.
        """

        try:

            return action(*args)

        except Exception as error:

            message = str(error)

            # --------------------------------------------------
            # EPIPE / broken pipe
            #
            # NEVER reconnect automatically.
            #
            # These errors belong to the Playwright Node
            # transport and retrying immediately can create
            # another CDP connection while the old transport
            # is already broken.
            # --------------------------------------------------

            if (
                "EPIPE" in message
                or
                "broken pipe" in message.lower()
                or
                "write after end" in message.lower()
            ):

                print(
                    "Playwright transport error detected."
                )

                print(
                    f"Playwright Transport Error : {message}"
                )

                print(
                    "Automatic CDP reconnect skipped."
                )

                return False

            # --------------------------------------------------
            # Normal browser target errors
            # --------------------------------------------------

            recoverable_error = (

                "Target page" in message

                or

                "Target closed" in message

                or

                "context or browser has been closed" in message

            )

            if not recoverable_error:

                raise

            print(
                "Playwright browser target became unavailable."
            )

            print(
                f"Playwright Target Error : {message}"
            )

            # --------------------------------------------------
            # Clear stale page references only.
            #
            # Do NOT restart Playwright.
            # Do NOT create another CDP connection here.
            # --------------------------------------------------

            self.page = None

            # --------------------------------------------------
            # Try to reuse an already existing context.
            # --------------------------------------------------

            try:

                if self.context:

                    pages = self.context.pages

                    for candidate in reversed(pages):

                        try:

                            if not candidate.is_closed():

                                self.page = candidate

                                break

                        except Exception:

                            continue

            except Exception as reconnect_error:

                print(
                    f"Browser target recovery failed : "
                    f"{reconnect_error}"
                )

                self.page = None

            # --------------------------------------------------
            # If no usable page exists, fail safely.
            # Do not create a second CDP connection.
            # --------------------------------------------------

            if self.page is None:

                print(
                    "No usable browser page available."
                )

                return False

            # --------------------------------------------------
            # Retry the browser action exactly once.
            # --------------------------------------------------

            print(
                "Retrying browser action on existing page..."
            )

            try:

                return action(*args)

            except Exception as retry_error:

                print(
                    f"Browser retry failed : {retry_error}"
                )

                return False

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
        query,
        new_tab=False
    ):

        if not self._connect():
            return False

        def _search(search_query):

            # --------------------------------------------------
            # Separate user command → new tab
            #
            # Multi-command → reuse current tab
            # --------------------------------------------------

            if new_tab:

                if not self._create_page():

                    return False

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
        query,
        new_tab=False
    ):
        if not self._connect():
            return False

        def _search(search_query):

            # --------------------------------------------------
            # Separate user command → new tab
            #
            # Multi-command → reuse current tab
            # --------------------------------------------------

            if new_tab:

                if not self._create_page():

                    return False

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
    # Click Google Search Result
    # --------------------------------------------------

    def click_search_result(
        self,
        index=0
    ):
        """
        Click a Google search result by zero-based index.

        Examples:

            index=0
                -> first result

            index=1
                -> second result

            index=2
                -> third result

        Returns
        -------
        bool
            True when the result was successfully clicked.
        """

        if not self._connect():

            return False

        def _click(result_index):

            try:

                result_index = int(
                    result_index
                )

            except (
                TypeError,
                ValueError
            ):

                result_index = 0

            if result_index < 0:

                result_index = 0

            # ------------------------------------------------
            # Google organic search result selectors.
            #
            # We intentionally prefer result containers
            # rather than arbitrary links on the page.
            # ------------------------------------------------

            result_selectors = [

                "div.MjjYud",

                "div.tF2Cxc",

            ]

            result = None

            for selector in result_selectors:

                locator = self.page.locator(
                    selector
                )

                count = locator.count()

                if count > result_index:

                    result = locator.nth(
                        result_index
                    )

                    break

            if result is None:

                print(
                    "Google search result not found."
                )

                return False

            # ------------------------------------------------
            # Find the result link.
            # ------------------------------------------------

            link = result.locator(
                "a"
            ).first

            link.wait_for(
                state="visible",
                timeout=15000
            )

            link.scroll_into_view_if_needed()

            # ------------------------------------------------
            # Capture current URL before click.
            # ------------------------------------------------

            previous_url = self.page.url

            print(
                f"Clicking Google result : "
                f"{result_index + 1}"
            )

            link.click(
                force=True
            )

            # ------------------------------------------------
            # Wait for navigation when possible.
            # ------------------------------------------------

            try:

                self.page.wait_for_load_state(
                    "domcontentloaded",
                    timeout=30000
                )

            except TimeoutError:

                # Some pages keep loading resources
                # indefinitely. DOMContentLoaded timeout
                # should not automatically mean failure.
                pass

            self.page.wait_for_timeout(
                1000
            )

            current_url = self.page.url

            # ------------------------------------------------
            # Verify navigation.
            # ------------------------------------------------

            if current_url != previous_url:

                print(
                    f"Google result opened : "
                    f"{current_url}"
                )

                return True

            # ------------------------------------------------
            # Sometimes Google opens the same URL or the
            # page navigation is delayed.
            # Verify that the page is still alive.
            # ------------------------------------------------

            if (
                self.page
                and
                not self.page.is_closed()
            ):

                print(
                    "Google result click completed."
                )

                return True

            return False

        try:

            return self._retry_action(
                _click,
                index
            )

        except TimeoutError:

            print(
                "Google result click timed out."
            )

            return False

        except Error as error:

            print(
                f"Google Result Playwright Error : "
                f"{error}"
            )

            return False

        except Exception as error:

            print(
                f"Google Result Click Error : "
                f"{error}"
            )

            return False

    # --------------------------------------------------
    # Play YouTube
    # --------------------------------------------------

    def play_youtube(
        self,
        query,
        new_tab=False
    ):

        if not self.youtube_search(
            query,
            new_tab=new_tab
        ):

            return False

        def _play(search_query):

            print(
                f"Selecting YouTube video : {search_query}"
            )

            # --------------------------------------------------
            # Wait for YouTube search results to appear.
            #
            # YouTube is dynamic, so do not depend on only one
            # exact thumbnail selector.
            # --------------------------------------------------

            self.page.wait_for_timeout(2000)

            video_selectors = [

                "ytd-video-renderer a#thumbnail",

                "ytd-video-renderer #thumbnail",

                "ytd-video-renderer h3 a",

            ]

            first_video = None

            for selector in video_selectors:

                try:

                    locator = self.page.locator(
                        selector
                    )

                    count = locator.count()

                    print(
                        f"YouTube selector : "
                        f"{selector} | count : {count}"
                    )

                    if count > 0:

                        first_video = locator.first

                        break

                except Exception:

                    continue

            # --------------------------------------------------
            # No video found
            # --------------------------------------------------

            if first_video is None:

                print(
                    "No YouTube video result found."
                )

                return False

            # --------------------------------------------------
            # Wait until selected result is visible.
            # --------------------------------------------------

            try:

                first_video.wait_for(
                    state="visible",
                    timeout=15000
                )

            except TimeoutError:

                print(
                    "YouTube video result was found "
                    "but did not become visible."
                )

                return False

            # --------------------------------------------------
            # Scroll result into view.
            # --------------------------------------------------

            try:

                first_video.scroll_into_view_if_needed()

            except Exception:

                pass

            self.page.wait_for_timeout(
                1000
            )

            # --------------------------------------------------
            # Click first video.
            # --------------------------------------------------

            print(
                "Clicking first YouTube video..."
            )

            first_video.click(
                force=True,
                timeout=15000
            )

            # --------------------------------------------------
            # Wait for video page.
            #
            # Do NOT use networkidle because YouTube keeps
            # background network activity alive.
            # --------------------------------------------------

            try:

                self.page.wait_for_load_state(
                    "domcontentloaded",
                    timeout=15000
                )

            except TimeoutError:

                pass

            # --------------------------------------------------
            # Give YouTube player time to initialize.
            # --------------------------------------------------

            self.page.wait_for_timeout(
                4000
            )

            # --------------------------------------------------
            # Verify YouTube video player exists.
            # --------------------------------------------------

            try:

                player = self.page.locator(
                    "#movie_player video.html5-main-video"
                ).first

                player.wait_for(
                    state="attached",
                    timeout=15000
                )

                print(
                    "YouTube video player detected."
                )

            except TimeoutError:

                print(
                    "YouTube video player was not detected."
                )

                return False

            # --------------------------------------------------
            # Move mouse away.
            # --------------------------------------------------

            try:

                self.page.mouse.move(
                    0,
                    0
                )

            except Exception:

                pass

            # --------------------------------------------------
            # Fullscreen
            #
            # Required workflow:
            #
            #   1. Focus YouTube player
            #   2. Press F  -> YouTube fullscreen
            #   3. Press F11 -> Chrome fullscreen
            # --------------------------------------------------

            try:

                self.page.wait_for_timeout(
                    1000
                )

                # --------------------------------------------------
                # Bring the current YouTube page to the foreground.
                #
                # We do this AFTER navigation/video loading, not during
                # page creation, so it does not recreate the earlier
                # Target page / EPIPE issue.
                # --------------------------------------------------

                try:

                    self.page.bring_to_front()

                except Exception as error:

                    print(
                        f"Browser focus warning : {error}"
                    )

                self.page.wait_for_timeout(
                    500
                )

                # --------------------------------------------------
                # Focus the actual YouTube player.
                # --------------------------------------------------

                player = self.page.locator(
                    "#movie_player"
                ).first

                try:

                    player.focus()

                except Exception as error:

                    print(
                        f"YouTube player focus warning : {error}"
                    )

                self.page.wait_for_timeout(
                    500
                )

                # --------------------------------------------------
                # Press F through Playwright.
                #
                # This sends the key event directly to the focused
                # YouTube page/player.
                # --------------------------------------------------

                print(
                    "Pressing F for YouTube fullscreen..."
                )

                self.page.keyboard.press(
                    "f"
                )

                self.page.wait_for_timeout(
                    1500
                )

                # --------------------------------------------------
                # Press F11 through the OS keyboard controller.
                #
                # F11 is a browser/window-level shortcut, so keep
                # this outside Playwright page.keyboard.
                # --------------------------------------------------

                print(
                    "Pressing F11 for browser fullscreen..."
                )

                self.keyboard.press_key(
                    "f11"
                )

                self.page.wait_for_timeout(
                    1500
                )

            except Exception as error:

                print(
                    f"Fullscreen keyboard warning : {error}"
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

        if self._closed:

            return

        self._closed = True

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

        self.context = None

        self.browser = None

        self.page = None

        print(
            "Playwright shutdown completed."
        )