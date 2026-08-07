"""
ASTRA-AI
Premium Header V3
--------------------------------------------

Features
✓ Glass Header
✓ Premium Logo Glow
✓ Dynamic Greeting
✓ Live Clock
✓ Responsive Layout
✓ Clean Architecture
"""

import os
from datetime import datetime

from PySide6.QtCore import (
    Qt,
    QSize,
    QTimer,
)

from PySide6.QtGui import (
    QColor,
    QFont,
    QPixmap,
)

from PySide6.QtWidgets import (
    QFrame,
    QLabel,
    QPushButton,
    QSizePolicy,
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QGraphicsDropShadowEffect,
)


class HeaderWidget(QFrame):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setObjectName("HeaderWidget")

        self.username = "Naresh"

        self.setFixedHeight(126)

        self.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Fixed
        )

        self.setStyleSheet("""

        QFrame#HeaderWidget{

            background:qlineargradient(

                x1:0,
                y1:0,
                x2:1,
                y2:1,

                stop:0   rgba(255,250,255,235),
                stop:0.18 rgba(250,245,255,230),
                stop:0.45 rgba(243,238,255,220),
                stop:0.72 rgba(240,236,255,225),
                stop:1   rgba(255,252,255,235)

            );

            border:2px solid rgba(255,255,255,210);

            border-radius:32px;

        }

        """)

        shadow = QGraphicsDropShadowEffect(self)

        shadow.setBlurRadius(40)

        shadow.setOffset(0, 12)

        shadow.setColor(
            QColor(170, 155, 255, 60)
        )

        self.setGraphicsEffect(shadow)

        self.build_ui()

        self.start_clock()

    # ==========================================================
    # BUILD UI
    # ==========================================================

    def build_ui(self):

        self.main_layout = QHBoxLayout(self)

        self.main_layout.setContentsMargins(
            38,
            14,
            38,
            14
        )

        self.main_layout.setSpacing(34)

        self.build_left_section()

        self.build_center_section()

        self.build_right_section()

        self.main_layout.addLayout(
            self.left_layout
        )

        self.main_layout.addSpacing(40)

        self.main_layout.addStretch()

        self.main_layout.addLayout(
            self.center_layout
        )

        self.main_layout.addStretch()

        self.main_layout.addLayout(
            self.right_layout
        )

    # ==========================================================
    # LEFT SECTION
    # ==========================================================

    def build_left_section(self):

        self.left_layout = QHBoxLayout()
        self.left_layout.setSpacing(14)
        self.left_layout.setAlignment(Qt.AlignVCenter)

        # ---------------- Logo ----------------

        self.logo = QLabel()

        self.logo.setFixedSize(100, 100)

        self.logo.setAlignment(Qt.AlignCenter)

        self.logo.setStyleSheet("""
        QLabel{
            background:transparent;
        }
        """)

        glow = QGraphicsDropShadowEffect()

        glow.setBlurRadius(90)

        glow.setOffset(0,0)

        glow.setColor(
            QColor(146, 96, 255, 210)
        )

        self.logo.setGraphicsEffect(glow)

        self.load_logo()

        # ---------------- Brand ----------------

        brand_layout = QVBoxLayout()

        brand_layout.setSpacing(3)

        brand_layout.setAlignment(
            Qt.AlignLeft |
            Qt.AlignVCenter
        )

        self.title = QLabel("ASTRA-AI")

        self.title.setFont(
            QFont(
                "Segoe UI Variable",
                31,
                QFont.Bold
            )
        )

        self.title.setStyleSheet("""
        color:#1F2937;
        background:transparent;
        """)

        self.subtitle = QLabel(
            "Your Personal AI Desktop Assistant"
        )

        self.subtitle.setFont(
            QFont(
                "Segoe UI",
                14
            )
        )

        self.subtitle.setStyleSheet("""
        color:#64748B;
        background:transparent;
        """)

        brand_layout.addWidget(self.title)

        brand_layout.addWidget(self.subtitle)

        self.left_layout.addWidget(self.logo)

        self.left_layout.addLayout(brand_layout)

    # ==========================================================
    # CENTER SECTION
    # ==========================================================

    def build_center_section(self):

        self.center_layout = QVBoxLayout()

        self.center_layout.setAlignment(Qt.AlignCenter)

        self.greeting_label = QLabel()

        self.greeting_label.setAlignment(Qt.AlignCenter)

        self.greeting_label.setFont(
            QFont(
                "Segoe UI Variable",
                22,
                QFont.Bold
            )
        )

        self.greeting_label.setStyleSheet("""
        color:#111827;
        background:transparent;
        """)

        self.center_layout.addWidget(
            self.greeting_label,
            alignment=Qt.AlignCenter
        )

    # ==========================================================
    # RIGHT SECTION
    # ==========================================================

    def build_right_section(self):

        self.right_layout = QHBoxLayout()

        self.right_layout.setSpacing(10)

        self.right_layout.setAlignment(
            Qt.AlignRight |
            Qt.AlignVCenter
        )

        # ---------------- Time ----------------

        self.time_chip = QLabel()

        # ---------------- Date ----------------

        self.date_chip = QLabel()

        # ---------------- Day ----------------

        self.day_chip = QLabel()

        chips = [
            self.time_chip,
            self.date_chip,
            self.day_chip
        ]

        for chip in chips:

            chip.setMinimumHeight(42)

            chip.setMinimumWidth(120)

            chip.setAlignment(Qt.AlignCenter)

            chip.setStyleSheet("""

            QLabel{

                background:qlineargradient(

                    x1:0,
                    y1:0,
                    x2:1,
                    y2:1,

                    stop:0 rgba(255,255,255,245),

                    stop:1 rgba(246,243,255,225)

                );

                border:1px solid rgba(255,255,255,220);

                border-radius:18px;

                color:#374151;

                padding:8px 18px;

                font-size:13px;

                font-weight:600;

            }

            """)

            chip_shadow = QGraphicsDropShadowEffect()

            chip_shadow.setBlurRadius(20)

            chip_shadow.setOffset(0,5)

            chip_shadow.setColor(

                QColor(180,170,255,35)

            )

            chip.setGraphicsEffect(
                chip_shadow
            )

        self.day_chip.setMinimumWidth(95)

        # ---------------- Power Button ----------------

        self.power_button = QPushButton("⏻")

        self.power_button.setCursor(
            Qt.PointingHandCursor
        )

        self.power_button.setFixedSize(
            QSize(
                64,
                64
            )
        )

        self.power_button.setStyleSheet("""

        QPushButton{

            background:qlineargradient(
                x1:0,
                y1:0,
                x2:1,
                y2:1,

                stop:0 white,
                stop:1 #FFF6F7
            );

            border:2px solid rgba(255,80,80,.18);

            border-radius:22px;

            color:#EF4444;

            font-size:24px;

            font-weight:700;

        }

        QPushButton:hover{

            border:2px solid #EF4444;

            background:#FFF2F2;

        }

        QPushButton:pressed{

            background:#FFE5E5;

        }

        """)

        power_glow = QGraphicsDropShadowEffect()

        power_glow.setBlurRadius(28)

        power_glow.setOffset(0,4)

        power_glow.setColor(

            QColor(255,120,140,70)

        )

        self.power_button.setGraphicsEffect(
            power_glow
        )

        self.right_layout.addWidget(self.time_chip)

        self.right_layout.addWidget(self.date_chip)

        self.right_layout.addWidget(self.day_chip)

        self.right_layout.addSpacing(8)

        self.right_layout.addWidget(self.power_button)

    # ==========================================================
    # LOAD LOGO
    # ==========================================================

    def load_logo(self):

        logo_paths = [

            "ui/assets/astra_logo.png",

            "assets/astra_logo.png",

            "ui/assets/logo.png",

            "assets/logo.png"

        ]

        for path in logo_paths:

            if os.path.exists(path):

                pix = QPixmap(path)

                pix = pix.scaled(
                    94,
                    94,
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation
                )

                self.logo.setPixmap(pix)

                return

    # ==========================================================
    # LIVE CLOCK
    # ==========================================================

    def start_clock(self):

        self.timer = QTimer(self)

        self.timer.timeout.connect(
            self.update_datetime
        )

        self.timer.start(1000)

        self.update_datetime()

    # ==========================================================
    # UPDATE DATE / TIME / GREETING
    # ==========================================================

    def update_datetime(self):

        now = datetime.now()

        hour = now.hour

        if 5 <= hour < 12:

            greeting = "Good Morning"

        elif 12 <= hour < 17:

            greeting = "Good Afternoon"

        elif 17 <= hour < 21:

            greeting = "Good Evening"

        else:

            greeting = "Good Night"

        self.greeting_label.setText(
            f"{greeting}, {self.username} 👋"
        )

        self.time_chip.setText(
            "🕒 " +
            now.strftime("%I:%M:%S %p")
        )

        self.date_chip.setText(
            "📅 " +
            now.strftime("%d %b %Y")
        )

        self.day_chip.setText(
            "☀ " +
            now.strftime("%A")
        )

    # ==========================================================
    # PUBLIC API
    # ==========================================================

    def set_username(self, username):

        self.username = username

        self.update_datetime()

    # ----------------------------------------------------------

    def set_tagline(self, text):

        self.subtitle.setText(text)

    # ----------------------------------------------------------

    def set_logo(self, image_path):

        if os.path.exists(image_path):

            pix = QPixmap(image_path)

            pix = pix.scaled(
                94,
                94,
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )

            self.logo.setPixmap(pix)

    # ----------------------------------------------------------

    def set_power_callback(self, callback):

        self.power_button.clicked.connect(
            callback
        )

    # ----------------------------------------------------------

    def set_power_enabled(self, enabled=True):

        self.power_button.setEnabled(enabled)

    # ----------------------------------------------------------

    def set_title(self, title):

        self.title.setText(title)

    # ----------------------------------------------------------

    def set_greeting(self, text):

        self.greeting_label.setText(text)