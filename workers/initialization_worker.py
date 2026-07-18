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

    # ----------------------------------
    # Signals
    # ----------------------------------

    status_changed = Signal(str)

    finished_success = Signal()

    finished_error = Signal(str)

    # ----------------------------------
    # Constructor
    # ----------------------------------

    def __init__(
        self,
        parent=None
    ):

        super().__init__(parent)

    # ----------------------------------
    # Run Worker
    # ----------------------------------

    def run(self):
        """
        Execute startup tasks.
        """

        try:

            # --------------------------
            # Application Scan
            # --------------------------

            self.status_changed.emit(
                "Scanning Applications..."
            )

            scanner = ApplicationScanner()

            scanner.scan()

            scanner.close()

            # --------------------------
            # File Indexing
            # --------------------------

            self.status_changed.emit(
                "Indexing Files..."
            )

            indexer = FileIndexer()

            indexer.index_files()

            indexer.close()

            # --------------------------
            # Initialization Completed
            # --------------------------

            self.status_changed.emit(
                "Initialization Completed."
            )

            self.finished_success.emit()

        except Exception as error:

            self.finished_error.emit(
                str(error)
            )