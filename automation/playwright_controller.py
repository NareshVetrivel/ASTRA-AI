"""
Playwright Browser Automation

ASTRA-AI V1
Production Ready

Features
--------
- Persistent Playwright driver
- Chrome CDP connection
- Managed ASTRA Chrome fallback
- Manual Chrome close recovery
- Stale page/context/browser recovery
- Playwright transport recovery
- Thread-safe browser operations
- Single browser operation lock
- Google search
- YouTube search and playback
- Google result clicking
- Safe Chrome reconnection
- Crash-safe browser recovery
"""

import socket
import subprocess
import threading
import time
from pathlib import Path
from urllib.parse import quote_plus

from automation.keyboard_controller import KeyboardController

from playwright.sync_api import (
    sync_playwright,
    TimeoutError as PlaywrightTimeoutError,
)


class PlaywrightController:

    DEBUG_PORT = 9222
    CDP_HOST = "127.0.0.1"

    CONNECT_TIMEOUT = 20.0
    NAVIGATION_TIMEOUT = 60000
    SELECTOR_TIMEOUT = 20000

    def __init__(
        self,
        profile="Default",
        user_data_dir=None,
    ):

        self.profile = profile or "Default"

        # --------------------------------------------------
        # ASTRA Dedicated Chrome Profile
        # --------------------------------------------------

        self.USER_DATA_DIR = (
            user_data_dir
            or r"C:\ASTRA_AI_BROWSER"
        )

        # --------------------------------------------------
        # Playwright State
        # --------------------------------------------------

        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None

        # --------------------------------------------------
        # Keyboard Controller
        # --------------------------------------------------

        self.keyboard = KeyboardController()

        # --------------------------------------------------
        # Chrome Process
        # --------------------------------------------------

        self._chrome_process = None
        self._managed_chrome = False

        # --------------------------------------------------
        # State Flags
        # --------------------------------------------------

        self._closed = False
        self._restarting = False

        # --------------------------------------------------
        # Thread Safety
        # --------------------------------------------------

        self._lock = threading.RLock()

    # ======================================================
    # CDP URL
    # ======================================================

    @property
    def _cdp_url(self):

        return (
            f"http://{self.CDP_HOST}:"
            f"{self.DEBUG_PORT}"
        )

    # ======================================================
    # Reset Browser State
    # ======================================================

    def _reset_browser(self):

        self.page = None
        self.context = None
        self.browser = None

    # ======================================================
    # Check CDP Port
    # ======================================================

    def _is_cdp_available(self):

        try:

            with socket.create_connection(
                (
                    self.CDP_HOST,
                    self.DEBUG_PORT,
                ),
                timeout=0.5,
            ):

                return True

        except OSError:

            return False

    # ======================================================
    # Managed Chrome Process Alive
    # ======================================================

    def _managed_process_alive(self):

        process = self._chrome_process

        if process is None:

            return False

        try:

            return process.poll() is None

        except Exception:

            return False

    # ======================================================
    # Refresh Managed Chrome State
    # ======================================================

    def _refresh_managed_chrome_state(self):

        if (
            self._chrome_process is not None
            and not self._managed_process_alive()
        ):

            print(
                "Managed Chrome process is no longer alive."
            )

            self._chrome_process = None
            self._managed_chrome = False

    # ======================================================
    # Error Message
    # ======================================================

    @staticmethod
    def _error_message(error):

        return str(error).lower()

    # ======================================================
    # Transport Error Detection
    # ======================================================

    @classmethod
    def _is_transport_error(
        cls,
        error,
    ):

        message = cls._error_message(error)

        errors = (

            "epipe",
            "broken pipe",
            "write after end",
            "pipe has been ended",
            "transport closed",
            "connection closed",
            "connection reset",
            "connection aborted",
            "socket hang up",
            "channel closed",
            "driver process exited",
            "connection refused",
            "connection lost",
            "browser_type.connect_over_cdp",

        )

        return any(
            item in message
            for item in errors
        )

    # ======================================================
    # Target Error Detection
    # ======================================================

    @classmethod
    def _is_target_error(
        cls,
        error,
    ):

        message = cls._error_message(error)

        errors = (

            "target closed",
            "target page",
            "page has been closed",
            "page is closed",
            "browser has been closed",
            "context has been closed",
            "context or browser has been closed",
            "execution context was destroyed",
            "target page, context or browser has been closed",

        )

        return any(
            item in message
            for item in errors
        )

    # ======================================================
    # Connection Error Detection
    # ======================================================

    @classmethod
    def _is_connection_error(
        cls,
        error,
    ):

        return (
            cls._is_transport_error(error)
            or cls._is_target_error(error)
        )

    # ======================================================
    # Validate Current Browser Connection
    # ======================================================

    def _browser_is_alive(self):

        if self.browser is None:

            return False

        # If CDP itself disappeared,
        # all current Playwright references are stale.

        if not self._is_cdp_available():

            print(
                "Chrome CDP is unavailable. "
                "Clearing stale browser references."
            )

            self._reset_browser()

            return False

        try:

            contexts = self.browser.contexts

            if contexts is None:

                self._reset_browser()

                return False

            return True

        except Exception as error:

            print(
                f"Browser validation failed : {error}"
            )

            self._reset_browser()

            return False

    # ======================================================
    # Chrome Executable
    # ======================================================

    def _chrome_path(self):

        paths = [

            r"C:\Program Files\Google\Chrome\Application\chrome.exe",

            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",

            str(
                Path.home()
                / "AppData"
                / "Local"
                / "Google"
                / "Chrome"
                / "Application"
                / "chrome.exe"
            ),

        ]

        for path in paths:

            if Path(path).exists():

                return path

        return None

    # ======================================================
    # Start Playwright
    # ======================================================

    def _start_playwright(self):

        if self.playwright is not None:

            return True

        try:

            self.playwright = (
                sync_playwright().start()
            )

            self._closed = False

            print(
                "Playwright driver started."
            )

            return True

        except Exception as error:

            print(
                f"Playwright start error : {error}"
            )

            self.playwright = None

            return False

    # ======================================================
    # Stop Playwright Driver
    # ======================================================

    def _stop_playwright_driver(self):

        old_playwright = self.playwright

        self.playwright = None

        if old_playwright is None:

            return

        try:

            old_playwright.stop()

        except Exception as error:

            print(
                f"Playwright stop warning : {error}"
            )

    # ======================================================
    # Restart Playwright Driver
    # ======================================================

    def _restart_playwright(self):

        with self._lock:

            if self._restarting:

                return False

            self._restarting = True

            try:

                print(
                    "Restarting Playwright driver..."
                )

                self._reset_browser()

                self._stop_playwright_driver()

                time.sleep(0.5)

                if not self._start_playwright():

                    return False

                print(
                    "Playwright driver restarted."
                )

                return True

            finally:

                self._restarting = False

    # ======================================================
    # Launch Managed Chrome
    # ======================================================

    def _launch_chrome(self):

        self._refresh_managed_chrome_state()

        if self._is_cdp_available():

            print(
                "Chrome CDP is already available."
            )

            return True

        if self._managed_process_alive():

            print(
                "Managed Chrome process already running."
            )

            return True

        chrome = self._chrome_path()

        if chrome is None:

            raise FileNotFoundError(
                "Google Chrome executable not found."
            )

        Path(
            self.USER_DATA_DIR
        ).mkdir(
            parents=True,
            exist_ok=True,
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

        self._chrome_process = subprocess.Popen(
            command,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

        self._managed_chrome = True

        print(
            "Managed Chrome launched."
        )

        return True

    # ======================================================
    # Wait For CDP
    # ======================================================

    def _wait_for_cdp(
        self,
        timeout=None,
    ):

        if timeout is None:

            timeout = self.CONNECT_TIMEOUT

        deadline = (
            time.monotonic()
            + timeout
        )

        while time.monotonic() < deadline:

            self._refresh_managed_chrome_state()

            if self._is_cdp_available():

                return True

            time.sleep(0.25)

        return False

    # ======================================================
    # Connect CDP
    # ======================================================

    def _connect_cdp(self):

        if self.playwright is None:

            raise RuntimeError(
                "Playwright driver is not started."
            )

        self.browser = (
            self.playwright.chromium.connect_over_cdp(
                self._cdp_url
            )
        )

        return self.browser is not None

    # ======================================================
    # Select Context
    # ======================================================

    def _select_context(self):

        if self.browser is None:

            return False

        try:

            contexts = self.browser.contexts

            if not contexts:

                self.context = None

                return False

            self.context = contexts[-1]

            return True

        except Exception as error:

            print(
                f"Context selection error : {error}"
            )

            self.context = None

            return False

    # ======================================================
    # Find Existing Live Page
    # ======================================================

    def _find_live_page(self):

        if self.browser is None:

            return False

        try:

            if not self._select_context():

                self.page = None

                return False

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
                f"Live page lookup warning : {error}"
            )

        self.page = None

        return False

    # ======================================================
    # Create New Page
    # ======================================================

    def _create_page(self):

        if not self._browser_is_alive():

            return False

        if self.context is None:

            if not self._select_context():

                return False

        try:

            if self.context is None:

                return False

            self.page = (
                self.context.new_page()
            )

            print(
                "New Playwright page created."
            )

            return True

        except Exception as error:

            print(
                f"Page creation error : {error}"
            )

            # IMPORTANT:
            # Manual Chrome close often appears here.
            # Clear ALL stale objects immediately.

            if self._is_connection_error(error):

                print(
                    "Stale Chrome connection detected "
                    "during page creation."
                )

                self._reset_browser()

            else:

                self.page = None

            return False

    # ======================================================
    # Ensure Playwright Driver
    # ======================================================

    def _ensure_playwright(self):

        if self.playwright is not None:

            return True

        return self._start_playwright()

    # ======================================================
    # Connect To Browser
    # ======================================================

    def _connect(self):

        with self._lock:

            if self._closed:

                self._closed = False

            self._refresh_managed_chrome_state()

            # --------------------------------------------------
            # 1. IMPORTANT: Detect Manual Chrome Close
            # --------------------------------------------------

            if self.browser is not None:

                if not self._browser_is_alive():

                    print(
                        "Previous browser connection is stale."
                    )

                    self._reset_browser()

            # --------------------------------------------------
            # 2. Reuse Current Live Page
            # --------------------------------------------------

            if self.page is not None:

                try:

                    if (
                        not self.page.is_closed()
                        and self._is_cdp_available()
                    ):

                        return True

                except Exception:

                    pass

                self.page = None

            # --------------------------------------------------
            # 3. Reuse Browser + Existing Page
            # --------------------------------------------------

            if self._browser_is_alive():

                if self._find_live_page():

                    return True

                if self._create_page():

                    return True

                # Existing browser object failed.
                # Clear and reconnect.

                self._reset_browser()

            # --------------------------------------------------
            # 4. Ensure Playwright Driver
            # --------------------------------------------------

            if not self._ensure_playwright():

                return False

            # --------------------------------------------------
            # 5. If CDP Exists, Connect To It
            # --------------------------------------------------

            if self._is_cdp_available():

                try:

                    print(
                        "Connecting to existing Chrome CDP..."
                    )

                    self._connect_cdp()

                    print(
                        "Connected to Chrome CDP."
                    )

                except Exception as error:

                    print(
                        f"Existing CDP connection failed : "
                        f"{error}"
                    )

                    self._reset_browser()

                    # Restart Playwright transport if needed

                    if self._is_transport_error(error):

                        if not self._restart_playwright():

                            return False

            # --------------------------------------------------
            # 6. Chrome Missing -> Launch Fresh Chrome
            # --------------------------------------------------

            if self.browser is None:

                try:

                    if not self._launch_chrome():

                        return False

                except Exception as error:

                    print(
                        f"Chrome launch error : {error}"
                    )

                    return False

                if not self._wait_for_cdp():

                    print(
                        "Chrome CDP did not become available."
                    )

                    return False

                connected = False

                for attempt in range(3):

                    try:

                        self._connect_cdp()

                        connected = True

                        print(
                            "Connected to Chrome CDP."
                        )

                        break

                    except Exception as error:

                        print(
                            f"CDP connection attempt "
                            f"{attempt + 1} failed : "
                            f"{error}"
                        )

                        self._reset_browser()

                        if self._is_transport_error(error):

                            if not self._restart_playwright():

                                return False

                        time.sleep(0.75)

                if not connected:

                    self._reset_browser()

                    print(
                        "Unable to connect to Chrome."
                    )

                    return False

            # --------------------------------------------------
            # 7. Reuse Existing Chrome Tab
            # --------------------------------------------------

            if self._find_live_page():

                print(
                    "Playwright Ready."
                )

                return True

            # --------------------------------------------------
            # 8. Create Fresh Tab
            # --------------------------------------------------

            if not self._create_page():

                # One final full recovery.
                # This handles:
                #
                # Chrome manually closed
                # CDP stale
                # Context stale
                # Browser stale

                print(
                    "Page creation failed. "
                    "Performing full browser recovery."
                )

                self._reset_browser()

                if self._is_cdp_available():

                    try:

                        self._connect_cdp()

                    except Exception as error:

                        print(
                            f"Recovery CDP error : {error}"
                        )

                        self._reset_browser()

                if self.browser is None:

                    if not self._launch_chrome():

                        return False

                    if not self._wait_for_cdp():

                        return False

                    try:

                        self._connect_cdp()

                    except Exception as error:

                        print(
                            f"Final CDP recovery failed : "
                            f"{error}"
                        )

                        self._reset_browser()

                        return False

                if self._find_live_page():

                    return True

                if not self._create_page():

                    print(
                        "Unable to create Chrome tab."
                    )

                    return False

            print(
                "Playwright Ready."
            )

            return True

    # ======================================================
    # Recover Browser Connection
    # ======================================================

    def _recover_connection(
        self,
        restart_driver=False,
    ):

        with self._lock:

            print(
                "Recovering browser connection..."
            )

            self._reset_browser()

            if restart_driver:

                if not self._restart_playwright():

                    return False

            return self._connect()

    # ======================================================
    # Retry Browser Action
    # ======================================================

    def _retry_action(
        self,
        action,
        *args,
    ):

        with self._lock:

            try:

                return action(*args)

            except Exception as error:

                print(
                    f"Browser action error : {error}"
                )

                if not self._is_connection_error(error):

                    raise

                restart_driver = (
                    self._is_transport_error(error)
                )

                if not self._recover_connection(
                    restart_driver=restart_driver,
                ):

                    return False

                try:

                    return action(*args)

                except Exception as retry_error:

                    print(
                        f"Browser retry failed : "
                        f"{retry_error}"
                    )

                    self._reset_browser()

                    return False

    # ======================================================
    # New Tab
    # ======================================================

    def new_tab(self):

        with self._lock:

            if not self._connect():

                return False

            if self._create_page():

                return True

            # Recovery after stale context/browser

            self._reset_browser()

            if not self._connect():

                return False

            return self._create_page()

    # ======================================================
    # Normalize URL
    # ======================================================

    @staticmethod
    def normalize_url(url):

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

        if "." not in url:

            return (
                "https://www.google.com/search?q="
                + quote_plus(url)
            )

        return "https://" + url

    # ======================================================
    # Bring Page To Front
    # ======================================================

    def _bring_page_to_front(self):

        if self.page is None:

            return False

        try:

            if self.page.is_closed():

                return False

            self.page.bring_to_front()

            return True

        except Exception:

            return False

    # ======================================================
    # Open Website
    # ======================================================

    def open_website(
        self,
        website,
    ):

        if not website:

            return False

        with self._lock:

            if not self._connect():

                return False

            url = self.normalize_url(
                website
            )

            if not url:

                return False

            def _open():

                self.page.goto(
                    url,
                    wait_until="domcontentloaded",
                    timeout=self.NAVIGATION_TIMEOUT,
                )

                self._bring_page_to_front()

                print(
                    f"Opening : {url}"
                )

                return True

            try:

                return self._retry_action(
                    _open
                )

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
        new_tab=False,
    ):

        if not query:

            return False

        with self._lock:

            if not self._connect():

                return False

            if new_tab:

                if not self._create_page():

                    self._reset_browser()

                    if not self._connect():

                        return False

                    if not self._create_page():

                        return False

            search_url = (
                "https://www.google.com/search?q="
                + quote_plus(
                    str(query)
                )
            )

            def _search():

                self.page.goto(
                    search_url,
                    wait_until="domcontentloaded",
                    timeout=self.NAVIGATION_TIMEOUT,
                )

                self._bring_page_to_front()

                print(
                    f"Searching Google : {query}"
                )

                return True

            try:

                return self._retry_action(
                    _search
                )

            except Exception as error:

                print(
                    f"Google search error : {error}"
                )

                return False

    # ======================================================
    # YouTube Search
    # ======================================================

    def youtube_search(
        self,
        query,
        new_tab=False,
    ):

        if not query:

            return False

        with self._lock:

            if not self._connect():

                return False

            if new_tab:

                if not self._create_page():

                    self._reset_browser()

                    if not self._connect():

                        return False

                    if not self._create_page():

                        return False

            search_url = (
                "https://www.youtube.com/results"
                "?search_query="
                + quote_plus(
                    str(query)
                )
            )

            def _search():

                self.page.goto(
                    search_url,
                    wait_until="domcontentloaded",
                    timeout=self.NAVIGATION_TIMEOUT,
                )

                self.page.wait_for_selector(
                    "ytd-video-renderer",
                    timeout=self.SELECTOR_TIMEOUT,
                )

                self._bring_page_to_front()

                print(
                    f"YouTube Search : {query}"
                )

                return True

            try:

                return self._retry_action(
                    _search
                )

            except Exception as error:

                print(
                    f"YouTube search error : {error}"
                )

                return False

    # ======================================================
    # Click Google Search Result
    # ======================================================

    def click_search_result(
        self,
        index=0,
    ):

        with self._lock:

            if not self._connect():

                return False

            try:

                index = max(
                    int(index),
                    0,
                )

            except (
                TypeError,
                ValueError,
            ):

                index = 0

            def _click():

                selectors = [

                    "div.MjjYud",

                    "div.tF2Cxc",

                ]

                result = None

                for selector in selectors:

                    locator = self.page.locator(
                        selector
                    )

                    count = locator.count()

                    if count > index:

                        result = locator.nth(
                            index
                        )

                        break

                if result is None:

                    print(
                        "Google search result not found."
                    )

                    return False

                link = (
                    result.locator("a").first
                )

                link.wait_for(
                    state="visible",
                    timeout=15000,
                )

                link.scroll_into_view_if_needed()

                previous_url = self.page.url

                link.click(
                    timeout=15000,
                    force=True,
                )

                try:

                    self.page.wait_for_load_state(
                        "domcontentloaded",
                        timeout=30000,
                    )

                except PlaywrightTimeoutError:

                    pass

                self._bring_page_to_front()

                return (
                    self.page.url != previous_url
                    or not self.page.is_closed()
                )

            try:

                return self._retry_action(
                    _click
                )

            except Exception as error:

                print(
                    f"Google result click error : "
                    f"{error}"
                )

                return False

    # ======================================================
    # Play YouTube
    # ======================================================

    def play_youtube(
        self,
        query,
        new_tab=False,
    ):

        if not query:

            return False

        with self._lock:

            if not self.youtube_search(
                query,
                new_tab=new_tab,
            ):

                return False

            def _play():

                selectors = [

                    "ytd-video-renderer a#thumbnail",

                    "ytd-video-renderer h3 a",

                    "ytd-video-renderer #thumbnail",

                ]

                video = None

                for selector in selectors:

                    locator = self.page.locator(
                        selector
                    )

                    if locator.count() > 0:

                        video = locator.first

                        break

                if video is None:

                    print(
                        "No YouTube video found."
                    )

                    return False

                video.wait_for(
                    state="visible",
                    timeout=15000,
                )

                video.scroll_into_view_if_needed()

                video.click(
                    timeout=15000,
                    force=True,
                )

                try:

                    self.page.wait_for_load_state(
                        "domcontentloaded",
                        timeout=20000,
                    )

                except PlaywrightTimeoutError:

                    pass

                player = (
                    self.page.locator(
                        "video.html5-main-video"
                    ).first
                )

                player.wait_for(
                    state="attached",
                    timeout=15000,
                )

                self._bring_page_to_front()

                try:

                    self.page.keyboard.press("f")

                except Exception as error:

                    print(
                        f"YouTube fullscreen warning : "
                        f"{error}"
                    )

                try:

                    self.keyboard.press_key(
                        "f11"
                    )

                except Exception as error:

                    print(
                        f"Browser fullscreen warning : "
                        f"{error}"
                    )

                print(
                    f"Playing : {query}"
                )

                return True

            try:

                return self._retry_action(
                    _play
                )

            except Exception as error:

                print(
                    f"Play error : {error}"
                )

                return False

    # ======================================================
    # Current URL
    # ======================================================

    def current_url(self):

        with self._lock:

            if not self._connect():

                return None

            try:

                return self._retry_action(
                    lambda: self.page.url
                )

            except Exception as error:

                print(
                    f"Current URL error : {error}"
                )

                return None

    # ======================================================
    # Refresh
    # ======================================================

    def refresh(self):

        with self._lock:

            if not self._connect():

                return False

            def _refresh():

                self.page.reload(
                    wait_until="domcontentloaded",
                    timeout=self.NAVIGATION_TIMEOUT,
                )

                self._bring_page_to_front()

                return True

            try:

                return self._retry_action(
                    _refresh
                )

            except Exception as error:

                print(
                    f"Refresh error : {error}"
                )

                return False

    # ======================================================
    # Close
    # ======================================================

    def close(self):

        with self._lock:

            if self._closed:

                return

            self._closed = True

            print(
                "Shutting down Playwright controller..."
            )

            self._reset_browser()

            self._stop_playwright_driver()

            print(
                "Playwright shutdown completed."
            )