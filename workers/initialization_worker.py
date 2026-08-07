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

            print("\n========== INITIALIZATION ==========")

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
            # Scan Applications
            # ------------------------------------------

            self.progress_changed.emit(10)

            self.status_changed.emit(
                "Scanning Applications..."
            )

            print("Scanning applications...")

            scanner = ApplicationScanner()

            scanner.scan()

            if self.should_stop():
                return

            print("Application scan completed.")

            # ------------------------------------------
            # Preparing
            # ------------------------------------------

            self.progress_changed.emit(40)

            self.status_changed.emit(
                "Preparing File Index..."
            )

            if self.should_stop():
                return

            # ------------------------------------------
            # File Indexing
            # ------------------------------------------

            self.progress_changed.emit(55)

            self.status_changed.emit(
                "Indexing Files..."
            )

            print("Indexing files...")

            indexer = FileIndexer()

            indexer.index_files()

            if self.should_stop():
                return

            print("File indexing completed.")

            # ------------------------------------------
            # Preparing ASTRA
            # ------------------------------------------

            self.progress_changed.emit(90)

            self.status_changed.emit(
                "Preparing ASTRA..."
            )

            print("Initialization worker completed.")

            if self.should_stop():
                return

            # ------------------------------------------
            # Completed
            # ------------------------------------------

            print("Initialization completed.")

            self.status_changed.emit(
                "Initialization Complete"
            )

            self.progress_changed.emit(100)

            print("====================================\n")

            self.finished_success.emit()

        except Exception as error:

            import traceback

            traceback.print_exc()

            if not self.should_stop():

                self.finished_error.emit(
                    str(error)
                )

        finally:

            try:

                if scanner:

                    scanner.close()

            except Exception:
                pass

            try:

                if indexer:

                    indexer.close()

            except Exception:
                pass