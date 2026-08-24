"""
Initialization Worker

Runs startup tasks in a
background thread to keep
the UI responsive.

ASTRA-AI V1
"""

from PySide6.QtCore import (
    QThread,
    Signal
)

from automation.application_scanner import (
    ApplicationScanner
)

from automation.file_indexer import (
    FileIndexer
)


class InitializationWorker(QThread):
    """
    Background initialization worker.

    Responsibilities:

    - Load Whisper model
    - Scan installed applications
    - Synchronize file index

    Live File Monitor is intentionally
    NOT started here.

    MainWindow owns the FileMonitor so
    only one monitor runs during the
    ASTRA application lifetime.
    """

    status_changed = Signal(str)

    progress_changed = Signal(int)

    finished_success = Signal()

    finished_error = Signal(str)

    def __init__(
        self,
        recognizer,
        parent=None
    ):

        super().__init__(parent)

        self.recognizer = recognizer

        self._stop_requested = False

    # -------------------------------------------------
    # Stop Request
    # -------------------------------------------------

    def stop(self):
        """
        Request graceful stop.
        """

        self._stop_requested = True

    # -------------------------------------------------
    # Check Stop
    # -------------------------------------------------

    def should_stop(self):
        """
        Return True when initialization
        should stop safely.
        """

        return (

            self._stop_requested

            or

            self.isInterruptionRequested()

        )

    # -------------------------------------------------
    # Run
    # -------------------------------------------------

    def run(self):

        scanner = None

        indexer = None

        try:

            print(
                "\n========== INITIALIZATION =========="
            )

            if self.should_stop():

                return

            # ------------------------------------------
            # Starting
            # ------------------------------------------

            self.progress_changed.emit(0)

            self.status_changed.emit(
                "Starting ASTRA..."
            )

            if self.should_stop():

                return

            # ------------------------------------------
            # Load Whisper Model
            # ------------------------------------------

            self.progress_changed.emit(10)

            self.status_changed.emit(
                "Loading Whisper Model..."
            )

            print(
                "Loading Whisper model..."
            )

            self.recognizer.load_model()

            if self.should_stop():

                return

            print(
                "Whisper model loaded."
            )

            # ------------------------------------------
            # Scan Applications
            # ------------------------------------------

            self.progress_changed.emit(30)

            self.status_changed.emit(
                "Scanning Applications..."
            )

            print(
                "Scanning applications..."
            )

            scanner = ApplicationScanner()

            scanner.scan()

            if self.should_stop():

                return

            print(
                "Application scan completed."
            )

            # ------------------------------------------
            # Preparing File Index
            # ------------------------------------------

            self.progress_changed.emit(55)

            self.status_changed.emit(
                "Preparing File Index..."
            )

            if self.should_stop():

                return

            # ------------------------------------------
            # File Indexing / Synchronization
            # ------------------------------------------

            self.progress_changed.emit(70)

            self.status_changed.emit(
                "Indexing Files..."
            )

            print(
                "Indexing files..."
            )

            indexer = FileIndexer()

            indexer.index_files()

            if self.should_stop():

                return

            print(
                "File indexing completed."
            )

            # ------------------------------------------
            # Important
            # ------------------------------------------
            #
            # Live File Monitor is NOT started here.
            #
            # MainWindow owns and starts the
            # FileMonitor after initialization
            # completes successfully.
            #
            # This prevents duplicate watchdog
            # observers and duplicate database
            # event processing.
            # ------------------------------------------

            # ------------------------------------------
            # Preparing ASTRA
            # ------------------------------------------

            self.progress_changed.emit(95)

            self.status_changed.emit(
                "Preparing ASTRA..."
            )

            print(
                "Initialization worker completed."
            )

            if self.should_stop():

                return

            # ------------------------------------------
            # Completed
            # ------------------------------------------

            print(
                "Initialization completed."
            )

            self.status_changed.emit(
                "Initialization Complete"
            )

            self.progress_changed.emit(100)

            print(
                "====================================\n"
            )

            self.finished_success.emit()

        except Exception as error:

            import traceback

            traceback.print_exc()

            if not self.should_stop():

                self.finished_error.emit(
                    str(error)
                )

        finally:

            # ------------------------------------------
            # Close Application Scanner
            # ------------------------------------------

            try:

                if scanner:

                    scanner.close()

            except Exception:

                pass

            # ------------------------------------------
            # Close File Indexer
            # ------------------------------------------

            try:

                if indexer:

                    indexer.close()

            except Exception:

                pass