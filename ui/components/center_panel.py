"""
ui/components/center_panel.py

ASTRA-AI
Center Hero Panel

PART 1
- Responsive Layout
- Avatar Section
- Halo Container
"""

from PySide6.QtCore import Qt

from PySide6.QtWidgets import (
    QWidget,
    QLabel,
    QVBoxLayout,
    QSizePolicy,
    QFrame,
    QStackedLayout,
    QGraphicsDropShadowEffect,
)

from PySide6.QtGui import QColor


class CenterPanelWidget(QWidget):
    """
    Center Hero Section

    Layout

        Top Spacer

        Avatar

        Mic (Part 2)

        CTA Button (Part 2)
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setObjectName("centerPanel")

        self.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Expanding
        )

        self.build_ui()

    # ----------------------------------------------------
    # UI
    # ----------------------------------------------------

    def build_ui(self):

        self.setStyleSheet("""

        QWidget#centerPanel{

            background:transparent;
            border:none;

        }

        """)

        self.main_layout = QVBoxLayout(self)

        self.main_layout.setContentsMargins(
            25,
            20,
            25,
            25
        )

        self.main_layout.setSpacing(18)

        self.main_layout.setAlignment(Qt.AlignCenter)

        # -------------------------------
        # Top Spacer
        # -------------------------------

        self.main_layout.addStretch(1)

        # -------------------------------
        # Hero Section
        # -------------------------------

        self.build_hero_section()

        # -------------------------------
        # Mic Section
        # -------------------------------

        self.build_mic_section()

        # -------------------------------
        # CTA
        # -------------------------------

        self.build_cta()

        self.main_layout.addStretch(2)

    # ----------------------------------------------------
    # Hero Section
    # ----------------------------------------------------

    def build_hero_section(self):

        self.hero_container = QWidget()

        self.hero_container.setObjectName("heroContainer")

        self.hero_container.setMinimumHeight(620)

        self.hero_container.setMaximumHeight(700)

        self.hero_container.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Expanding
        )

        self.hero_container.setStyleSheet("""

        QWidget#heroContainer{

        background:qradialgradient(

            cx:0.5,
            cy:0.44,
            radius:1.22,

            stop:0 rgba(255,255,255,215),

            stop:0.18 rgba(250,246,255,170),

            stop:0.38 rgba(238,228,255,105),

            stop:0.60 rgba(220,205,255,55),

            stop:0.82 rgba(205,190,255,20),

            stop:1 rgba(255,255,255,0)

        );

        border:none;

        }

        """)

        self.stack = QStackedLayout(self.hero_container)

        self.stack.setStackingMode(
            QStackedLayout.StackAll
        )

        self.build_glow_background()

        self.build_avatar_layer()

        self.main_layout.addWidget(
            self.hero_container,
            stretch=8
        )

    # ----------------------------------------------------
    # Glow Background
    # ----------------------------------------------------

    def build_glow_background(self):

        self.glow_container = QFrame()

        self.glow_container.setObjectName(
            "glowContainer"
        )

        self.glow_container.setFixedSize(
            660,
            660
        )

        self.glow_container.setStyleSheet("""

        QFrame#glowContainer{

        background:transparent;

        border:14px solid rgba(255,255,255,255);

        border-radius:330px;

        }

        """)

        glow = QGraphicsDropShadowEffect()

        glow.setOffset(0)

        glow.setBlurRadius(360)

        glow.setOffset(0)

        glow.setColor(
            QColor(255,255,255,255)
        )

        self.glow_container.setGraphicsEffect(glow)

        self.stack.addWidget(
            self.glow_container
        )

        # ----------------------------------
        # Outer Halo Ring
        # ----------------------------------

        self.outer_ring = QFrame()

        self.outer_ring.setFixedSize(720,720)

        self.outer_ring.setStyleSheet("""

        QFrame{

        background:transparent;

        border:5px solid rgba(255,255,255,185);

        border-radius:360px;

        }

        """)

        outer_glow = QGraphicsDropShadowEffect()

        outer_glow.setBlurRadius(340)

        outer_glow.setOffset(0)

        outer_glow.setColor(
            QColor(255,255,255,255)
        )

        self.outer_ring.setGraphicsEffect(
            outer_glow
        )

        self.stack.addWidget(
            self.outer_ring
        )

        # ----------------------------------
        # Ultra Glow Ring
        # ----------------------------------

        self.ultra_ring = QFrame()

        self.ultra_ring.setFixedSize(685, 685)

        self.ultra_ring.setStyleSheet("""

        QFrame{

        background:transparent;

        border:2px solid rgba(255,255,255,220);

        border-radius:342px;

        }

        """)

        ultra = QGraphicsDropShadowEffect()

        ultra.setBlurRadius(420)

        ultra.setOffset(0)

        ultra.setColor(
            QColor(255,255,255,255)
        )

        self.ultra_ring.setGraphicsEffect(
            ultra
        )

        self.stack.addWidget(
            self.ultra_ring
        )

    # ----------------------------------------------------
    # Avatar Layer
    # ----------------------------------------------------

    def build_avatar_layer(self):

        self.avatar_container = QWidget()

        self.avatar_container.setAttribute(
            Qt.WA_TranslucentBackground
        )

        self.avatar_container.setFixedSize(
            640,
            640
        )

        layout = QVBoxLayout(self.avatar_container)

        layout.setContentsMargins(
            0,
            0,
            0,
            0
        )

        layout.setAlignment(Qt.AlignCenter)

        self.avatar_placeholder = QLabel()

        self.avatar_placeholder.setFixedSize(
            430,
            560
        )

        self.avatar_placeholder.setStyleSheet("""

        QLabel{

            background:transparent;

            border:none;

        }

        """)

        layout.addWidget(
            self.avatar_placeholder,
            alignment=Qt.AlignCenter
        )

        self.stack.addWidget(
            self.avatar_container
        )

    # ----------------------------------------------------
    # Backend Hooks
    # ----------------------------------------------------

    def set_avatar_state(self, state):
        """
        Reserved for future animated avatar.
        """
        pass

    def update_status(self, text: str):
        """
        Future backend hook.
        """
        pass

    # ----------------------------------------------------

    def build_mic_section(self):

        from ui.widgets.mic_widget import MicWidget

        self.mic_widget = MicWidget()

        self.main_layout.addWidget(
            self.mic_widget,
            alignment=Qt.AlignCenter
        )

    # ----------------------------------------------------

    def build_cta(self):

        self.cta_label = QLabel(
            "CLICK MICROPHONE TO INTERACT"
        )

        self.cta_label.setAlignment(Qt.AlignCenter)

        self.cta_label.setStyleSheet("""

        QLabel{

        background:qlineargradient(
        x1:0,
        y1:0,
        x2:1,
        y2:1,

        stop:0 rgba(255,255,255,.95),
        stop:1 rgba(245,240,255,.88)
        );

        border:1px solid rgba(167,139,250,.35);

        border-radius:24px;

        padding:14px 36px;

        color:#7C3AED;

        font-size:15px;

        font-weight:800;

        }
        """)

        self.main_layout.addWidget(
            self.cta_label,
            alignment=Qt.AlignCenter
        )

    # ----------------------------------------------------
    # Public API
    # ----------------------------------------------------

    def set_listening(self, listening: bool):

        if hasattr(self, "mic_widget"):

            if hasattr(self.mic_widget, "set_listening"):
                self.mic_widget.set_listening(listening)

    def set_avatar_state(self, state):

        if hasattr(self.avatar_widget, "set_state"):
            self.avatar_widget.set_state(state)

    def update_status(self, text):
        """
        Reserved for backend integration.
        """
        pass