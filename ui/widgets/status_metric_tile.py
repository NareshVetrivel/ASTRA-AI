"""
ASTRA-AI
Premium Status Metric Tile
Review-1 Production
"""

from __future__ import annotations

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

try:
    import shiboken6
except ImportError:
    shiboken6 = None


class StatusMetricTile(QFrame):

    def __init__(
        self,
        title,
        value,
        icon="📊",
        color="#16A34A",
        parent=None,
    ):
        super().__init__(parent)

        self.title = title
        self.value = value
        self.icon = icon
        self.value_color = color

        self.setObjectName(
            "MetricTile"
        )

        self.setCursor(
            Qt.PointingHandCursor
        )

        self.setAttribute(
            Qt.WA_Hover,
            True
        )

        # -------------------------------------------------
        # Fixed tile size
        # -------------------------------------------------

        self.setMinimumSize(
            150,
            118
        )

        self.setMaximumSize(
            150,
            118
        )

        self.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Fixed
        )

        # -------------------------------------------------
        # Styles
        #
        # IMPORTANT:
        # Qt stylesheet rgba alpha uses integer values.
        # Do NOT use .98 / .95 here.
        # -------------------------------------------------

        self.NORMAL_STYLE = """
        QFrame#MetricTile {

            background: qlineargradient(
                x1: 0,
                y1: 0,
                x2: 1,
                y2: 1,

                stop: 0 rgba(255, 255, 255, 250),
                stop: 1 rgba(245, 243, 255, 242)
            );

            border: 1px solid #DDD6FE;

            border-radius: 20px;
        }
        """

        self.HOVER_STYLE = """
        QFrame#MetricTile {

            background: rgba(255, 255, 255, 255);

            border: 2px solid #C4B5FD;

            border-radius: 20px;
        }
        """

        self.ICON_NORMAL_STYLE = """
        QLabel {

            background: #EEF2FF;

            border: 1px solid #DDD6FE;

            border-radius: 23px;

            font-size: 22px;
        }
        """

        self.ICON_HOVER_STYLE = """
        QLabel {

            background: #EDE9FE;

            border: 2px solid #C4B5FD;

            border-radius: 23px;

            font-size: 24px;
        }
        """

        # -------------------------------------------------
        # Runtime state
        # -------------------------------------------------

        self._hovered = False

        self.shadow = None

        self.hover_animation = None

        # -------------------------------------------------
        # Build UI
        # -------------------------------------------------

        self.build_ui()

    # =====================================================
    # Shadow
    # =====================================================

    def _create_shadow(self):
        """
        Create a fresh shadow effect.

        Qt owns the graphics effect after setGraphicsEffect().
        A Python wrapper can therefore become invalid if Qt
        deletes/replaces the underlying C++ object.

        This method safely creates a new effect whenever needed.
        """

        shadow = QGraphicsDropShadowEffect()

        shadow.setBlurRadius(
            22
        )

        shadow.setOffset(
            0,
            5
        )

        shadow.setColor(
            QColor(
                124,
                58,
                237,
                28
            )
        )

        shadow.setParent(
            self
        )

        self.shadow = shadow

        self.setGraphicsEffect(
            shadow
        )

        return shadow

    # -----------------------------------------------------

    def _shadow_is_valid(self):
        """
        Check whether the Python wrapper still points to a
        valid Qt C++ QGraphicsDropShadowEffect.
        """

        if self.shadow is None:
            return False

        if shiboken6 is None:
            return True

        try:
            return shiboken6.isValid(
                self.shadow
            )

        except Exception:
            return False

    # -----------------------------------------------------

    def _ensure_shadow(self):
        """
        Return a valid shadow object.

        If Qt already deleted the previous effect, create
        a fresh one instead of allowing a RuntimeError.
        """

        if self._shadow_is_valid():

            return self.shadow

        try:

            self._create_shadow()

        except Exception as error:

            print(
                f"Metric Tile Shadow Error : {error}"
            )

            self.shadow = None

        return self.shadow

    # =====================================================
    # Build UI
    # =====================================================

    def build_ui(self):

        self.setStyleSheet(
            self.NORMAL_STYLE
        )

        # -------------------------------------------------
        # Shadow
        # -------------------------------------------------

        self._create_shadow()

        # -------------------------------------------------
        # Hover animation
        #
        # Only blurRadius is animated.
        # Short duration keeps the UI responsive.
        # -------------------------------------------------

        self.hover_animation = QPropertyAnimation(
            self.shadow,
            b"blurRadius",
            self
        )

        self.hover_animation.setDuration(
            120
        )

        self.hover_animation.setEasingCurve(
            QEasingCurve.OutCubic
        )

        # -------------------------------------------------
        # Root Layout
        # -------------------------------------------------

        root = QVBoxLayout(
            self
        )

        root.setContentsMargins(
            14,
            10,
            14,
            10
        )

        root.setSpacing(
            6
        )

        root.setAlignment(
            Qt.AlignCenter
        )

        # =================================================
        # Icon
        # =================================================

        self.icon_label = QLabel(
            self.icon
        )

        self.icon_label.setAlignment(
            Qt.AlignCenter
        )

        self.icon_label.setFixedSize(
            46,
            46
        )

        self.icon_label.setStyleSheet(
            self.ICON_NORMAL_STYLE
        )

        root.addWidget(
            self.icon_label,
            alignment=Qt.AlignCenter
        )

        # =================================================
        # Title
        # =================================================

        self.title_label = QLabel(
            self.title
        )

        self.title_label.setAlignment(
            Qt.AlignCenter
        )

        self.title_label.setWordWrap(
            True
        )

        self.title_label.setStyleSheet(
            """
            QLabel {

                color: #111827;

                font-size: 14px;

                font-weight: 700;

                background: transparent;

                border: none;
            }
            """
        )

        root.addWidget(
            self.title_label
        )

        # =================================================
        # Value
        # =================================================

        self.value_label = QLabel()

        self.value_label.setAlignment(
            Qt.AlignCenter
        )

        root.addWidget(
            self.value_label
        )

        self.update_value(
            self.value,
            self.value_color
        )

    # =====================================================
    # Update Value
    # =====================================================

    def update_value(
        self,
        value,
        color=None,
    ):

        self.value = value

        if color is not None:

            self.value_color = color

        self.value_label.setText(
            str(value)
        )

        self.value_label.setStyleSheet(
            f"""
            QLabel {{

                color: {self.value_color};

                font-size: 12px;

                font-weight: 700;

                background: transparent;

                border: none;
            }}
            """
        )

    # =====================================================
    # Public API
    # =====================================================

    def set_title(
        self,
        title
    ):

        self.title = title

        self.title_label.setText(
            title
        )

    # -----------------------------------------------------

    def set_icon(
        self,
        icon
    ):

        self.icon = icon

        self.icon_label.setText(
            icon
        )

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

        self.setEnabled(
            enabled
        )

        self.setWindowOpacity(
            1.0 if enabled else 0.55
        )

    # =====================================================
    # Hover Animation
    # =====================================================

    def _animate_shadow(
        self,
        end_value
    ):
        """
        Safely animate shadow blur.

        If the old QGraphicsEffect was deleted by Qt,
        recreate it before accessing it.
        """

        shadow = self._ensure_shadow()

        if shadow is None:
            return

        try:

            if self.hover_animation is not None:

                self.hover_animation.stop()

        except RuntimeError:

            self.hover_animation = None

        # -------------------------------------------------
        # Recreate animation if its target was deleted.
        # -------------------------------------------------

        if (
            self.hover_animation is None
            or (
                shiboken6 is not None
                and not shiboken6.isValid(
                    self.hover_animation
                )
            )
        ):

            self.hover_animation = QPropertyAnimation(
                shadow,
                b"blurRadius",
                self
            )

            self.hover_animation.setDuration(
                120
            )

            self.hover_animation.setEasingCurve(
                QEasingCurve.OutCubic
            )

        try:

            current_value = shadow.blurRadius()

        except RuntimeError:

            shadow = self._create_shadow()

            if shadow is None:
                return

            current_value = 22

            self.hover_animation = QPropertyAnimation(
                shadow,
                b"blurRadius",
                self
            )

            self.hover_animation.setDuration(
                120
            )

            self.hover_animation.setEasingCurve(
                QEasingCurve.OutCubic
            )

        self.hover_animation.setStartValue(
            current_value
        )

        self.hover_animation.setEndValue(
            end_value
        )

        self.hover_animation.start()

    # =====================================================
    # Hover Enter
    # =====================================================

    def enterEvent(
        self,
        event
    ):

        self._hovered = True

        # -------------------------------------------------
        # Shadow
        # -------------------------------------------------

        self._animate_shadow(
            36
        )

        # -------------------------------------------------
        # Hover shadow appearance
        # -------------------------------------------------

        shadow = self._ensure_shadow()

        if shadow is not None:

            try:

                shadow.setOffset(
                    0,
                    7
                )

                shadow.setColor(
                    QColor(
                        124,
                        58,
                        237,
                        65
                    )
                )

            except RuntimeError:

                pass

        # -------------------------------------------------
        # Card
        # -------------------------------------------------

        self.setStyleSheet(
            self.HOVER_STYLE
        )

        # -------------------------------------------------
        # Icon
        # -------------------------------------------------

        self.icon_label.setStyleSheet(
            self.ICON_HOVER_STYLE
        )

        super().enterEvent(
            event
        )

    # =====================================================
    # Hover Leave
    # =====================================================

    def leaveEvent(
        self,
        event
    ):

        self._hovered = False

        # -------------------------------------------------
        # Shadow
        # -------------------------------------------------

        self._animate_shadow(
            22
        )

        # -------------------------------------------------
        # Restore shadow
        # -------------------------------------------------

        shadow = self._ensure_shadow()

        if shadow is not None:

            try:

                shadow.setOffset(
                    0,
                    5
                )

                shadow.setColor(
                    QColor(
                        124,
                        58,
                        237,
                        28
                    )
                )

            except RuntimeError:

                pass

        # -------------------------------------------------
        # Card
        # -------------------------------------------------

        self.setStyleSheet(
            self.NORMAL_STYLE
        )

        # -------------------------------------------------
        # Icon
        # -------------------------------------------------

        self.icon_label.setStyleSheet(
            self.ICON_NORMAL_STYLE
        )

        super().leaveEvent(
            event
        )