"""
ASTRA-AI
Premium Status Metric Tile
Review-1 Production
"""

from PySide6.QtCore import (
    Qt,
    QPropertyAnimation,
    QEasingCurve,
)

from PySide6.QtGui import QColor

from PySide6.QtWidgets import (
    QFrame,
    QLabel,
    QVBoxLayout,
    QSizePolicy,
    QGraphicsDropShadowEffect,
)


class StatusMetricTile(QFrame):

    def __init__(
        self,
        title,
        value,
        icon="📊",
        color="#16A34A",
        parent=None
    ):
        super().__init__(parent)

        self.title = title
        self.value = value
        self.icon = icon
        self.value_color = color

        self.setObjectName("MetricTile")

        self.setCursor(Qt.PointingHandCursor)

        self.setAttribute(
            Qt.WA_Hover,
            True
        )

        self.setMinimumSize(150, 118)
        self.setMaximumSize(150, 118)

        self.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Fixed
        )

        self.NORMAL_STYLE = """
        QFrame#MetricTile{

            background:qlineargradient(
                x1:0,
                y1:0,
                x2:1,
                y2:1,

                stop:0 rgba(255,255,255,.98),
                stop:1 rgba(245,243,255,.95)
            );

            border:1px solid #DDD6FE;

            border-radius:20px;
        }
        """

        self.HOVER_STYLE = """
        QFrame#MetricTile{

            background:white;

            border:2px solid #C4B5FD;

            border-radius:20px;
        }
        """

        self.ICON_NORMAL_STYLE = """
        QLabel{

            background:#EEF2FF;

            border:1px solid #DDD6FE;

            border-radius:23px;

            font-size:22px;
        }
        """

        self.ICON_HOVER_STYLE = """
        QLabel{

            background:#EDE9FE;

            border:2px solid #C4B5FD;

            border-radius:23px;

            font-size:24px;
        }
        """

        self.build_ui()

    # ---------------------------------------------------------

    def build_ui(self):

        self.setStyleSheet(
            self.NORMAL_STYLE
        )

        self.shadow = QGraphicsDropShadowEffect(self)

        self.shadow.setBlurRadius(22)

        self.shadow.setOffset(0,5)

        self.shadow.setColor(
            QColor(124,58,237,28)
        )

        self.setGraphicsEffect(
            self.shadow
        )

        self.hover_animation = QPropertyAnimation(
            self.shadow,
            b"blurRadius"
        )

        self.hover_animation.setDuration(120)

        self.hover_animation.setEasingCurve(
            QEasingCurve.OutCubic
        )

        root = QVBoxLayout(self)

        root.setContentsMargins(
            14,
            10,
            14,
            10
        )

        root.setSpacing(6)

        root.setAlignment(Qt.AlignCenter)

        # -------------------------------------------------
        # Icon
        # -------------------------------------------------

        self.icon_label = QLabel(self.icon)

        self.icon_label.setAlignment(
            Qt.AlignCenter
        )

        self.icon_label.setFixedSize(46,46)

        self.icon_label.setStyleSheet(
            self.ICON_NORMAL_STYLE
        )

        root.addWidget(
            self.icon_label,
            alignment=Qt.AlignCenter
        )

        # -------------------------------------------------
        # Title
        # -------------------------------------------------

        self.title_label = QLabel(self.title)

        self.title_label.setAlignment(
            Qt.AlignCenter
        )

        self.title_label.setWordWrap(True)

        self.title_label.setStyleSheet("""

        color:#111827;

        font-size:14px;

        font-weight:700;

        background:transparent;

        """)

        root.addWidget(self.title_label)

        # -------------------------------------------------
        # Value
        # -------------------------------------------------

        self.value_label = QLabel()

        self.value_label.setAlignment(
            Qt.AlignCenter
        )

        root.addWidget(self.value_label)

        self.update_value(
            self.value,
            self.value_color
        )

    # -----------------------------------------------------
    # Update Value
    # -----------------------------------------------------

    def update_value(
        self,
        value,
        color=None
    ):

        self.value = value

        if color is not None:

            self.value_color = color

        self.value_label.setText(str(value))

        self.value_label.setStyleSheet(

            f"color:{self.value_color};"

            "font-size:12px;"

            "font-weight:700;"

            "background:transparent;"

        )

    # -----------------------------------------------------
    # Public API
    # -----------------------------------------------------

    def set_title(self, title):

        self.title = title

        self.title_label.setText(title)

    # -----------------------------------------------------

    def set_icon(self, icon):

        self.icon = icon

        self.icon_label.setText(icon)

    # -----------------------------------------------------

    def set_value(
        self,
        value,
        color=None
    ):

        self.update_value(
            value,
            color
        )

    # -----------------------------------------------------

    def set_card_enabled(
        self,
        enabled
    ):

        self.setEnabled(enabled)

        self.setWindowOpacity(
            1.0 if enabled else 0.55
        )

    # -----------------------------------------------------
    # Hover Enter
    # -----------------------------------------------------

    def enterEvent(self, event):

        self.hover_animation.stop()

        self.hover_animation.setStartValue(
            self.shadow.blurRadius()
        )

        self.hover_animation.setEndValue(42)

        self.hover_animation.start()

        self.shadow.setOffset(0, 8)

        self.shadow.setColor(
            QColor(124,58,237,80)
        )

        self.setStyleSheet(
            self.HOVER_STYLE
        )

        self.icon_label.setStyleSheet(
            self.ICON_HOVER_STYLE
        )

        super().enterEvent(event)

    # -----------------------------------------------------
    # Hover Leave
    # -----------------------------------------------------

    def leaveEvent(self, event):

        self.hover_animation.stop()

        self.hover_animation.setStartValue(
            self.shadow.blurRadius()
        )

        self.hover_animation.setEndValue(22)

        self.hover_animation.start()

        self.shadow.setOffset(0, 4)

        self.shadow.setColor(
            QColor(124,58,237,28)
        )

        self.setStyleSheet(
            self.NORMAL_STYLE
        )

        self.icon_label.setStyleSheet(
            self.ICON_NORMAL_STYLE
        )

        super().leaveEvent(event)