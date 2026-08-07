"""
ASTRA-AI
Premium Left Status Panel
Review 1 Production UI
"""

from PySide6.QtCore import Qt

from PySide6.QtWidgets import (
    QWidget,
    QLabel,
    QVBoxLayout,
    QGridLayout,
    QSizePolicy,
)

from ui.widgets.status_tile import StatusTileWidget


class LeftPanelWidget(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setObjectName("LeftPanel")

        self.setMinimumWidth(360)
        self.setMaximumWidth(370)

        self.setSizePolicy(
            QSizePolicy.Fixed,
            QSizePolicy.Expanding
        )

        self.build_ui()

    # ---------------------------------------------------------
    # Build UI
    # ---------------------------------------------------------

    def build_ui(self):

        self.setStyleSheet("""

        QWidget#LeftPanel{

            background:transparent;
            border:none;

        }

        """)

        root = QVBoxLayout(self)

        root.setContentsMargins(
            6,
            8,
            6,
            8
        )

        root.setSpacing(16)

        # -------------------------------------------------
        # Title
        # -------------------------------------------------

        title = QLabel("SYSTEM STATUS")

        title.setAlignment(
            Qt.AlignLeft |
            Qt.AlignVCenter
        )

        title.setStyleSheet("""

        color:#7C3AED;

        font-size:20px;

        font-weight:700;

        padding-left:18px;

        background:transparent;

        """)

        root.addWidget(title)

        # -------------------------------------------------
        # Dashboard Grid
        # -------------------------------------------------

        self.grid_container = QWidget()

        self.grid_container.setStyleSheet("""

        background:transparent;

        """)

        self.grid = QGridLayout(self.grid_container)

        self.grid.setSizeConstraint(
            QGridLayout.SetMinimumSize
        )

        self.grid.setContentsMargins(
            0,
            0,
            0,
            0
        )

        self.grid.setHorizontalSpacing(12)

        self.grid.setVerticalSpacing(12)

        self.grid.setContentsMargins(
            0,
            0,
            0,
            0
        )

        self.grid.setSpacing(12)

        root.addWidget(
            self.grid_container,
            stretch=1
        )

        # -------------------------------------------------
        # Dashboard Tiles
        # -------------------------------------------------

        self.listening = StatusTileWidget(
            title="Listening",
            status="Idle",
            icon="🎤"
        )

        self.thinking = StatusTileWidget(
            title="Thinking",
            status="Inactive",
            icon="🧠"
        )

        self.speaking = StatusTileWidget(
            title="Speaking",
            status="Silent",
            icon="🔊"
        )

        self.whisper = StatusTileWidget(
            title="Whisper",
            status="Loaded",
            icon="⚡"
        )

        self.automation = StatusTileWidget(
            title="Automation",
            status="Ready",
            icon="🤖"
        )

        self.browser = StatusTileWidget(
            title="Browser",
            status="Standby",
            icon="🌐"
        )

        self.database = StatusTileWidget(
            title="Database",
            status="Connected",
            icon="🗄"
        )

        self.internet = StatusTileWidget(
            title="Internet",
            status="Online",
            icon="📶"
        )

        # -------------------------------------------------
        # 2 × 4 Premium Dashboard
        # -------------------------------------------------

        self.grid.addWidget(self.listening, 0, 0)
        self.grid.addWidget(self.thinking, 0, 1)

        self.grid.addWidget(self.speaking, 1, 0)
        self.grid.addWidget(self.whisper, 1, 1)

        self.grid.addWidget(self.automation, 2, 0)
        self.grid.addWidget(self.browser, 2, 1)

        self.grid.addWidget(self.database, 3, 0)
        self.grid.addWidget(self.internet, 3, 1)

        # -------------------------------------------------
        # Equal Dashboard Stretch
        # -------------------------------------------------

        for column in range(2):
            self.grid.setColumnStretch(column, 1)

        for row in range(4):
            self.grid.setRowStretch(row, 1)

    # ---------------------------------------------------------
    # Public API
    # ---------------------------------------------------------

    def set_listening(self, status):

        if self.listening.status != status:

            self.listening.update_status(status)


    def set_thinking(self, status):

        if self.thinking.status != status:

            self.thinking.update_status(status)


    def set_speaking(self, status):

        if self.speaking.status != status:

            self.speaking.update_status(status)


    def set_whisper(self, status):

        if self.whisper.status != status:

            self.whisper.update_status(status)


    def set_automation(self, status):

        if self.automation.status != status:

            self.automation.update_status(status)


    def set_browser(self, status):

        if self.browser.status != status:

            self.browser.update_status(status)


    def set_database(self, status):

        if self.database.status != status:

            self.database.update_status(status)


    def set_internet(self, status):

        if self.internet.status != status:

            self.internet.update_status(status)

    # ---------------------------------------------------------
    # Generic Backend Updater
    # ---------------------------------------------------------

    def update_status(
        self,
        module,
        status
    ):
        """
        Generic updater used by MainWindow.
        """

        cards = {

            "listening": self.listening,

            "thinking": self.thinking,

            "speaking": self.speaking,

            "whisper": self.whisper,

            "automation": self.automation,

            "browser": self.browser,

            "database": self.database,

            "internet": self.internet,

        }

        card = cards.get(
            module.lower()
        )

        if card and card.status != status:

            card.update_status(status)

    # ---------------------------------------------------------
    # Enable / Disable All Tiles
    # ---------------------------------------------------------

    def set_all_enabled(
        self,
        enabled=True
    ):

        for tile in [

            self.listening,

            self.thinking,

            self.speaking,

            self.whisper,

            self.automation,

            self.browser,

            self.database,

            self.internet,

        ]:

            tile.set_card_enabled(enabled)

    # ---------------------------------------------------------
    # Dashboard Reset
    # ---------------------------------------------------------

    def reset(self):

        self.set_listening("Idle")

        self.set_thinking("Inactive")

        self.set_speaking("Silent")

        self.set_whisper("Loaded")

        self.set_automation("Ready")

        self.set_browser("Standby")

        self.set_database("Connected")

        self.set_internet("Online")