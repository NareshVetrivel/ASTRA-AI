"""
ui/widgets/mic_widget.py

ASTRA-AI
Premium Microphone Widget

PART 1
---------------------------------
Foundation
"""

from PySide6.QtCore import (
    Qt,
    QRectF,
    QTimer,
    Property,
    QPropertyAnimation,
    QEasingCurve
)

from PySide6.QtWidgets import (
    QWidget,
    QPushButton,
    QLabel,
    QHBoxLayout,
    QVBoxLayout,
    QStackedLayout,
    QSizePolicy,
    QGraphicsDropShadowEffect
)

from PySide6.QtGui import (
    QPainter,
    QColor,
    QPen
)

from PySide6.QtSvg import QSvgRenderer

import os


# ==========================================================
# Wave Widget
# ==========================================================

class WaveWidget(QWidget):

    def __init__(self, parent=None):

        super().__init__(parent)

        self.setFixedSize(150, 70)

        self.audio_level = 0.0

        self.base_levels = [

            8,
            16,
            28,
            40,
            28,
            16,
            8

        ]

    # ------------------------------------------------------

    def update_level(
        self,
        level
    ):

        target = max(
            0.0,
            min(level, 1.0)
        )

        # Smooth animation

        self.audio_level = (

            self.audio_level * 0.75

            +

            target * 0.25

        )

        self.update()

    # ------------------------------------------------------

    def paintEvent(self, event):

        painter = QPainter(self)

        painter.setRenderHint(
            QPainter.Antialiasing,
            True
        )

        painter.setRenderHint(
            QPainter.SmoothPixmapTransform,
            True
        )

        painter.setPen(Qt.NoPen)

        painter.setBrush(
            QColor("#8B5CF6")
        )

        if self.objectName() == "leftWave":

            x = 36

        else:

            x = 8

        for base in self.base_levels:

            height = base + (

                self.audio_level

                * base

                * 2.2

            )

            painter.drawRoundedRect(

                x,

                (70 - height) / 2,

                8,

                height,

                4,

                4

            )

            x += 16

# ==========================================================
# Premium Microphone Button
# ==========================================================

class MicrophoneButton(QPushButton):

    def __init__(self, parent=None):

        super().__init__(parent)

        self.setCursor(
            Qt.PointingHandCursor
        )

        self.setFixedSize(
            150,
            150
        )

        self.setFlat(True)

        self.setStyleSheet("""

        QPushButton{

            background:transparent;

            border:none;

        }

        QPushButton:hover{

            background:transparent;

        }

        QPushButton:pressed{

            background:transparent;

        }

        """)

        # -----------------------------------------
        # States
        # -----------------------------------------

        self._listening = False

        self.audio_level = 0.0

        self.glow_radius = 0.0

        # -----------------------------------------
        # Ripple Animation
        # -----------------------------------------

        self._ripple_radius = 0.0

        self.ripple_animation = QPropertyAnimation(
            self,
            b"rippleRadius"
        )

        self.ripple_animation.setDuration(900)

        self.ripple_animation.setStartValue(0)

        self.ripple_animation.setEndValue(42)

        self.ripple_animation.setEasingCurve(
            QEasingCurve.OutCubic
        )

        self.ripple_animation.finished.connect(
            self.restart_ripple
        )

        # -----------------------------------------
        # Glow
        # -----------------------------------------

        self.shadow = QGraphicsDropShadowEffect()

        self.shadow.setBlurRadius(28)

        self.shadow.setOffset(0)

        self.shadow.setColor(
            QColor(124, 58, 237, 0)
        )

        self.setGraphicsEffect(
            self.shadow
        )

        # -----------------------------------------
        # SVG
        # -----------------------------------------

        svg_path = os.path.abspath(
            "ui/assets/icons/mic_trace.svg"
        )

        self.svg = QSvgRenderer(svg_path)

        if not self.svg.isValid():

            print(
                "Warning : mic_trace.svg not found."
            )

        # -----------------------------------------
        # Live Glow Timer
        # -----------------------------------------

        self.glow_timer = QTimer(self)

        self.glow_timer.timeout.connect(
            self.animate_glow
        )

        self.glow_timer.start(33)

    # ------------------------------------------------------
    # Hover Events
    # ------------------------------------------------------

    def enterEvent(self, event):

        if not self._listening:

            self.shadow.setBlurRadius(40)

            self.shadow.setColor(
                QColor(124, 58, 237, 180)
            )

        self.update()

        super().enterEvent(event)

    def leaveEvent(self, event):

        if not self._listening:

            self.shadow.setBlurRadius(28)

            self.shadow.setColor(
                QColor(124, 58, 237, 0)
            )

        self.update()

        super().leaveEvent(event)

    # ------------------------------------------------------
    # Listening State
    # ------------------------------------------------------

    def set_listening(
        self,
        listening
    ):

        self._listening = listening

        if listening:

            self.shadow.setBlurRadius(60)

            self.shadow.setColor(
                QColor(124, 58, 237, 220)
            )

            self.ripple_animation.start()

        else:

            self.ripple_animation.stop()

            self._ripple_radius = 0

            self.shadow.setBlurRadius(28)

            self.shadow.setColor(
                QColor(124, 58, 237, 0)
            )

            self.audio_level = 0.0

        self.update()

    # ------------------------------------------------------
    # Audio Level
    # ------------------------------------------------------

    def update_level(
        self,
        level
    ):

        self.audio_level = (

            self.audio_level * 0.75

            +

            max(
                0.0,
                min(level, 1.0)
            ) * 0.25

        )

    # ------------------------------------------------------
    # Live Glow Animation
    # ------------------------------------------------------

    def animate_glow(self):

        if self._listening:

            target = 16 + (

                self.audio_level * 30

            )

            self.glow_radius += (

                target - self.glow_radius

            ) * 0.22

            duration = int(

                950

                -

                self.audio_level * 500

            )

            duration = max(
                320,
                duration
            )

            if (

                self.ripple_animation.state()

                !=

                QPropertyAnimation.Running

            ):

                self.ripple_animation.setDuration(
                    duration
                )

                self.ripple_animation.start()

        else:

            self.glow_radius *= 0.88

            if self.glow_radius < 0.2:

                self.glow_radius = 0

        self.update()

    # ------------------------------------------------------
    # Ripple Property
    # ------------------------------------------------------

    def getRippleRadius(self):

        return self._ripple_radius

    def setRippleRadius(self, value):

        self._ripple_radius = value

        self.update()

    rippleRadius = Property(
        float,
        getRippleRadius,
        setRippleRadius
    )

    # ------------------------------------------------------

    def restart_ripple(self):

        if self._listening:

            duration = int(

                950

                -

                self.audio_level * 500

            )

            duration = max(
                320,
                duration
            )

            self.ripple_animation.setDuration(
                duration
            )

            self.ripple_animation.start()

        else:

            self._ripple_radius = 0

            self.update()

    # ------------------------------------------------------
    # Enabled / Disabled State
    # ------------------------------------------------------

    def setEnabled(self, enabled: bool):

        super().setEnabled(enabled)

        if enabled:

            self.setCursor(
                Qt.PointingHandCursor
            )

            self.shadow.setColor(
                QColor(124, 58, 237, 0)
            )

        else:

            self.setCursor(
                Qt.ForbiddenCursor
            )

            self.shadow.setColor(
                QColor(90, 90, 90, 70)
            )

        self.update()

    # ------------------------------------------------------
    # Paint
    # ------------------------------------------------------

    def paintEvent(self, event):

        painter = QPainter(self)

        painter.setRenderHint(
            QPainter.Antialiasing,
            True
        )

        painter.setRenderHint(
            QPainter.SmoothPixmapTransform,
            True
        )

        painter.setPen(Qt.NoPen)

        # --------------------------------------
        # Ripple Ring
        # --------------------------------------

        if self._listening:

            ripple_color = QColor(
                124,
                58,
                237,
                45
            )

            painter.setBrush(Qt.NoBrush)

            painter.setPen(
                QPen(
                    ripple_color,
                    2
                )
            )

            painter.drawEllipse(

                QRectF(

                    18 - self._ripple_radius,

                    18 - self._ripple_radius,

                    114 + self._ripple_radius * 2,

                    114 + self._ripple_radius * 2

                )

            )

        # --------------------------------------
        # Live Circular Glow
        # --------------------------------------

        if self.glow_radius > 0:

            glow_color = QColor(
                124,
                58,
                237,
                45
            )

            painter.setBrush(glow_color)

            painter.drawEllipse(

                QRectF(

                    18 - self.glow_radius,

                    18 - self.glow_radius,

                    114 + self.glow_radius * 2,

                    114 + self.glow_radius * 2

                )

            )

        # --------------------------------------
        # Outer Ring
        # --------------------------------------

        painter.setPen(

            QPen(

                QColor(
                    255,
                    255,
                    255,
                    235
                ),

                8

            )

        )

        painter.setBrush(Qt.NoBrush)

        painter.drawEllipse(

            QRectF(

                8,

                8,

                134,

                134

            )

        )

        # --------------------------------------
        # Main Circle
        # --------------------------------------

        painter.setPen(Qt.NoPen)

        if self.isEnabled():

            color = QColor("#7C3AED")

        else:

            color = QColor("#9CA3AF")

        painter.setBrush(color)

        painter.drawEllipse(

            QRectF(

                18,

                18,

                114,

                114

            )

        )

        # --------------------------------------
        # SVG
        # --------------------------------------

        if self.svg.isValid():

            if not self.isEnabled():

                painter.setOpacity(0.45)

            self.svg.render(

                painter,

                QRectF(

                    49,

                    37,

                    52,

                    76

                )

            )

            painter.setOpacity(1.0)

# ==========================================================
# Main Mic Widget
# ==========================================================

class MicWidget(QWidget):

    def __init__(self, parent=None):

        super().__init__(parent)

        self.setAttribute(
            Qt.WA_TranslucentBackground
        )

        self.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Fixed
        )

        self.setMinimumHeight(250)
        self.setMaximumHeight(320)

        self.listening = False

        self.build_ui()

    # ------------------------------------------------------

    def build_ui(self):

        self.root_layout = QVBoxLayout(self)

        self.root_layout.setContentsMargins(
            0,
            0,
            0,
            0
        )

        self.root_layout.setSpacing(16)

        self.root_layout.setAlignment(
            Qt.AlignBottom | Qt.AlignHCenter
        )

        # ==================================================
        # Single Layout
        # (Mic Always Center)
        # ==================================================

        self.main_row = QWidget()

        main_layout = QHBoxLayout(self.main_row)

        main_layout.setContentsMargins(
            0,
            0,
            0,
            0
        )

        main_layout.setSpacing(24)

        main_layout.setAlignment(
            Qt.AlignCenter
        )

        # --------------------------------------------------
        # LEFT CONTAINER
        # --------------------------------------------------

        self.left_container = QWidget()

        left_layout = QVBoxLayout(self.left_container)

        left_layout.setContentsMargins(
            0,
            0,
            0,
            0
        )

        left_layout.setSpacing(0)

        left_layout.setAlignment(
            Qt.AlignCenter
        )

        self.left_wave = WaveWidget()

        self.left_wave.setObjectName(
            "leftWave"
        )

        self.user_label = QLabel()

        self.user_label.setWordWrap(True)

        self.user_label.setMaximumWidth(260)

        self.user_label.setAlignment(
            Qt.AlignRight | Qt.AlignVCenter
        )

        self.user_label.setStyleSheet("""

        background:transparent;

        color:#374151;

        font-size:14px;

        font-weight:600;

        """)

        self.user_label.hide()

        left_layout.addWidget(
            self.left_wave,
            alignment=Qt.AlignCenter
        )

        left_layout.addWidget(
            self.user_label,
            alignment=Qt.AlignCenter
        )

        # --------------------------------------------------
        # MIC
        # --------------------------------------------------

        self.mic_button = MicrophoneButton()

        # --------------------------------------------------
        # RIGHT CONTAINER
        # --------------------------------------------------

        self.right_container = QWidget()

        right_layout = QVBoxLayout(self.right_container)

        right_layout.setContentsMargins(
            0,
            0,
            0,
            0
        )

        right_layout.setSpacing(0)

        right_layout.setAlignment(
            Qt.AlignCenter
        )

        self.right_wave = WaveWidget()

        self.right_wave.setObjectName(
            "rightWave"
        )

        self.ai_label = QLabel()

        self.ai_label.setWordWrap(True)

        self.ai_label.setMaximumWidth(260)

        self.ai_label.setAlignment(
            Qt.AlignLeft | Qt.AlignVCenter
        )

        self.ai_label.setStyleSheet("""

        background:transparent;

        color:#7C3AED;

        font-size:14px;

        font-weight:600;

        """)

        self.ai_label.hide()

        right_layout.addWidget(
            self.right_wave,
            alignment=Qt.AlignCenter
        )

        right_layout.addWidget(
            self.ai_label,
            alignment=Qt.AlignCenter
        )

        main_layout.addWidget(
            self.left_container
        )

        main_layout.addWidget(
            self.mic_button
        )

        main_layout.addWidget(
            self.right_container
        )

        self.root_layout.addStretch()

        self.root_layout.addWidget(
            self.main_row,
            alignment=Qt.AlignBottom | Qt.AlignHCenter
        )

    # ======================================================
    # Backend API
    # ======================================================

    def button(self):
        """
        Return microphone button.
        """

        return self.mic_button

    # ------------------------------------------------------

    def show_conversation(
        self,
        user_text,
        ai_text=""
    ):
        """
        Show current conversation.
        This remains visible until the
        next microphone click.
        """

        self.user_label.setText(user_text)
        self.ai_label.setText(ai_text)

        self.left_wave.hide()
        self.right_wave.hide()

        self.user_label.show()
        self.ai_label.show()

        self.update()

    # ------------------------------------------------------

    def update_ai_message(
        self,
        text
    ):
        """
        Update AI reply.
        """

        self.ai_label.setText(
            text
        )

        self.update()

    # ------------------------------------------------------

    def show_listening(self):
        """
        Show idle/listening waves.

        DO NOT clear conversation here.
        Conversation is cleared only
        when a new listening session starts.
        """

        self.user_label.hide()

        self.ai_label.hide()

        self.left_wave.show()

        self.right_wave.show()

    # ------------------------------------------------------

    def set_listening(
        self,
        listening
    ):

        if self.listening == listening:

            return

        self.listening = listening

        self.mic_button.set_listening(
            listening
        )

        if listening:

            # Clear previous conversation
            self.user_label.clear()
            self.ai_label.clear()

            self.show_listening()

        self.left_wave.update_level(
            0.0
        )

        self.right_wave.update_level(
            0.0
        )

    # ------------------------------------------------------

    def update_audio_level(
        self,
        level
    ):

        if not self.listening:

            return

        self.left_wave.update_level(
            level
        )

        self.right_wave.update_level(
            level
        )

        self.mic_button.update_level(
            level
        )

    # ------------------------------------------------------

    def set_enabled(
        self,
        enabled
    ):

        self.mic_button.setEnabled(
            enabled
        )

    # ------------------------------------------------------

    def reset(self):

        self.show_listening()

        self.set_listening(False)

        self.left_wave.update_level(
            0.0
        )

        self.right_wave.update_level(
            0.0
        )

        self.mic_button.update_level(
            0.0
        )