"""
ui/widgets/background_widget.py

ASTRA-AI
Premium Background Widget
Phase 1
"""

from PySide6.QtWidgets import QWidget, QVBoxLayout

from PySide6.QtGui import (
    QPainter,
    QColor,
    QBrush,
    QRadialGradient,
    QLinearGradient,
    QPen,
)
from PySide6.QtCore import Qt


class BackgroundWidget(QWidget):

    def __init__(self, parent=None):

        super().__init__(parent)

        self.setAttribute(Qt.WA_StyledBackground, True)

        self.layout = QVBoxLayout(self)

        self.layout.setContentsMargins(
            0,
            0,
            0,
            0
        )

        self.layout.setSpacing(0)

        # -----------------------------------------
        # Fast Startup Mode
        # -----------------------------------------

        self.fast_mode = True

    # ------------------------------------------------
    # Public API
    # ------------------------------------------------

    def setContentWidget(self, widget):

        self.layout.addWidget(widget)

    # ------------------------------------------------
    # Helper
    # Fill Entire Widget
    # ------------------------------------------------

    def _fill_gradient(self, painter, gradient):

        painter.fillRect(
            self.rect(),
            QBrush(gradient)
        )

    # ------------------------------------------------
    # Draw Background Layers
    # ------------------------------------------------

    def _draw_background(self, painter, w, h):

        # ==================================================
        # BASE LAVENDER
        # ==================================================

        painter.fillRect(
            self.rect(),
            QColor(247, 242, 255)
        )

        # ==================================================
        # TOP PINK
        # ==================================================

        self._draw_radial_glow(

            painter,

            -80,

            -40,

            w * 1.05,

            [

                (0.00, QColor(255,165,228,255)),
                (0.18, QColor(255,185,235,235)),
                (0.42, QColor(250,220,255,170)),
                (0.75, QColor(255,245,255,35)),
                (1.00, QColor(255,255,255,0))

            ]

        )

        # ==================================================
        # TOP RIGHT BLUE
        # ==================================================

        self._draw_radial_glow(

            painter,

            w + 80,

            -40,

            w * 1.05,

            [

                (0.00, QColor(175,220,255,255)),
                (0.20, QColor(195,230,255,225)),
                (0.45, QColor(220,240,255,165)),
                (0.75, QColor(255,255,255,35)),
                (1.00, QColor(255,255,255,0))

            ]

        )

        # ==================================================
        # CENTER WHITE GLOW
        # ==================================================

        self._draw_radial_glow(

            painter,

            w / 2,

            h * 0.42,

            w * 0.72,

            [

                (0.00, QColor(255,255,255,205)),
                (0.20, QColor(255,250,255,145)),
                (0.45, QColor(248,242,255,75)),
                (0.70, QColor(240,235,255,30)),
                (1.00, QColor(255,255,255,0))

            ]

        )

        # ==================================================
        # BOTTOM LAVENDER
        # ==================================================

        self._draw_radial_glow(

            painter,

            w / 2,

            h * 1.02,

            w * 0.82,

            [

                (0.00, QColor(206,188,255,190)),
                (0.42, QColor(226,212,255,105)),
                (1.00, QColor(255,255,255,0))

            ]

        )

        # ==================================================
        # SOFT VERTICAL BLEND
        # ==================================================

        self._draw_linear(

            painter,

            0,

            0,

            0,

            h,

            [

                (0.00, QColor(255,255,255,40)),
                (0.45, QColor(255,255,255,0)),
                (1.00, QColor(210,205,255,40))

            ]

        )

        # ==================================================
        # CENTER PREMIUM BLOOM
        # ==================================================

        self._draw_radial_glow(

            painter,

            w / 2,

            h * 0.42,

            w * 0.42,

            [

                (0.00, QColor(255,255,255,150)),
                (0.25, QColor(250,245,255,95)),
                (0.55, QColor(238,230,255,45)),
                (1.00, QColor(255,255,255,0))

            ]

        )

        # ==================================================
        # FLOOR GLOW
        # ==================================================

        self._draw_radial_glow(

            painter,

            w / 2,

            h * 1.03,

            w * 0.65,

            [

                (0.00, QColor(210,198,255,140)),
                (0.45, QColor(228,220,255,70)),
                (1.00, QColor(255,255,255,0))

            ]

        )

        # ==================================================
        # SOFT VIGNETTE
        # ==================================================

        self._draw_radial_glow(

            painter,

            w / 2,

            h / 2,

            w * 0.95,

            [

                (0.70, QColor(255,255,255,0)),
                (1.00, QColor(188,176,255,32))

            ]

        )

        # ==================================================
        # LIGHT MIST
        # ==================================================

        self._draw_linear(

            painter,

            0,

            0,

            w,

            h,

            [

                (0.00, QColor(255,255,255,35)),
                (0.30, QColor(245,240,255,12)),
                (0.65, QColor(225,215,255,25)),
                (1.00, QColor(255,255,255,10))

            ]

        )

    # ------------------------------------------------
    # Helper
    # Radial Glow
    # ------------------------------------------------

    def _draw_radial_glow(

        self,

        painter,

        center_x,

        center_y,

        radius,

        colors

    ):

        gradient = QRadialGradient(

            center_x,

            center_y,

            radius

        )

        for stop, color in colors:

            gradient.setColorAt(

                stop,

                color

            )

        self._fill_gradient(

            painter,

            gradient

        )

    # ------------------------------------------------
    # Helper
    # Linear Blend
    # ------------------------------------------------

    def _draw_linear(

        self,

        painter,

        x1,

        y1,

        x2,

        y2,

        colors

    ):

        gradient = QLinearGradient(

            x1,

            y1,

            x2,

            y2

        )

        for stop, color in colors:

            gradient.setColorAt(

                stop,

                color

            )

        self._fill_gradient(

            painter,

            gradient

        )

    # ------------------------------------------------
    # Helper
    # Circle Glow
    # ------------------------------------------------

    def _draw_glow_circle(

        self,

        painter,

        x,

        y,

        radius,

        colors

    ):

        glow = QRadialGradient(

            x,

            y,

            radius

        )

        for stop, color in colors:

            glow.setColorAt(

                stop,

                color

            )

        painter.setBrush(

            QBrush(glow)

        )

        painter.setPen(

            Qt.NoPen

        )

        painter.drawEllipse(

            int(x - radius),

            int(y - radius),

            int(radius * 2),

            int(radius * 2)

        )

    # ------------------------------------------------
    # Helper
    # Ring
    # ------------------------------------------------

    def _draw_ring(

        self,

        painter,

        x,

        y,

        diameter,

        color,

        width

    ):

        painter.setBrush(

            Qt.NoBrush

        )

        pen = QPen(

            color

        )

        pen.setWidth(width)

        painter.setPen(pen)

        painter.drawEllipse(

            int(x - diameter / 2),

            int(y - diameter / 2),

            diameter,

            diameter

        )

    # ------------------------------------------------
    # Floating Stars & Particles
    # ------------------------------------------------

    def _draw_stars_and_particles(
        self,
        painter,
        w,
        h
    ):

        painter.setPen(Qt.NoPen)

        # =============================================
        # Floating Stars
        # =============================================

        stars = [

            (0.18,0.14,4),
            (0.25,0.22,3),
            (0.33,0.10,5),
            (0.42,0.28,3),
            (0.57,0.16,4),
            (0.63,0.26,3),
            (0.72,0.18,4),
            (0.80,0.12,3),

            (0.24,0.42,3),
            (0.37,0.48,5),
            (0.52,0.36,3),
            (0.68,0.45,4),
            (0.77,0.34,3),

            (0.30,0.70,4),
            (0.44,0.78,3),
            (0.60,0.72,5),
            (0.76,0.78,4)

        ]

        for sx, sy, r in stars:

            self._draw_glow_circle(

                painter,

                w * sx,

                h * sy,

                r * 3,

                [

                    (0.00, QColor(255,255,255,160)),
                    (0.45, QColor(250,240,255,80)),
                    (1.00, QColor(255,255,255,0))

                ]

            )

        # =============================================
        # Soft Particles
        # =============================================

        particles = [

            (0.12,0.62),
            (0.18,0.55),
            (0.26,0.32),
            (0.35,0.62),
            (0.48,0.22),
            (0.58,0.62),
            (0.70,0.52),
            (0.82,0.60),
            (0.88,0.32),

        ]

        for px, py in particles:

            self._draw_glow_circle(

                painter,

                w * px,

                h * py,

                3,

                [

                    (0.00, QColor(255,255,255,40)),
                    (1.00, QColor(255,255,255,0))

                ]

            )

    # ------------------------------------------------
    # Floor Effects
    # ------------------------------------------------

    def _draw_floor_effects(
        self,
        painter,
        w,
        h
    ):

        # =============================================
        # Floor Platform Glow
        # =============================================

        self._draw_radial_glow(

            painter,

            w * 0.50,

            h * 0.92,

            min(w, h) * 0.34,

            [

                (0.00, QColor(255,255,255,150)),
                (0.20, QColor(235,225,255,110)),
                (0.45, QColor(218,205,255,70)),
                (0.70, QColor(210,200,255,30)),
                (1.00, QColor(255,255,255,0))

            ]

        )

        # =============================================
        # Floor Fog
        # =============================================

        self._draw_linear(

            painter,

            0,

            h * 0.70,

            0,

            h,

            [

                (0.00, QColor(255,255,255,0)),
                (0.35, QColor(248,245,255,40)),
                (0.70, QColor(238,232,255,65)),
                (1.00, QColor(230,225,255,90))

            ]

        )

        # =============================================
        # Floor Rings
        # =============================================

        rings = [

            (520, 28, 26),
            (660, 22, 18),
            (820, 16, 12),
            (980, 12, 8)

        ]

        for diameter, alpha, width in rings:

            self._draw_ring(

                painter,

                w / 2,

                h * 0.93,

                diameter,

                QColor(255,255,255,alpha),

                width

            )

        # =============================================
        # Floor Center Bloom
        # =============================================

        self._draw_radial_glow(

            painter,

            w * 0.50,

            h * 0.93,

            220,

            [

                (0.00, QColor(255,255,255,110)),
                (0.35, QColor(235,225,255,65)),
                (1.00, QColor(255,255,255,0))

            ]

        )

    # ------------------------------------------------
    # Premium Halo
    # ------------------------------------------------

    def _draw_halo(
        self,
        painter,
        w,
        h
    ):

        cx = w * 0.50

        cy = h * 0.48

        # =============================================
        # Outer Glow
        # =============================================

        self._draw_radial_glow(

            painter,

            cx,

            cy,

            420,

            [

                (0.00, QColor(255,255,255,0)),
                (0.45, QColor(255,255,255,0)),
                (0.62, QColor(235,215,255,45)),
                (0.76, QColor(255,225,255,135)),
                (0.88, QColor(255,255,255,220)),
                (0.96, QColor(255,255,255,80)),
                (1.00, QColor(255,255,255,0))

            ]

        )

        # =============================================
        # Halo Rings
        # =============================================

        halo_rings = [

            (360,35,52),
            (382,80,34),
            (402,150,20),
            (418,255,7),
            (432,120,3),

        ]

        for diameter, alpha, width in halo_rings:

            self._draw_ring(

                painter,

                cx,

                cy,

                diameter,

                QColor(255,255,255,alpha),

                width

            )

        # =============================================
        # Inner Bloom
        # =============================================

        self._draw_radial_glow(

            painter,

            cx,

            cy,

            250,

            [

                (0.00, QColor(255,255,255,170)),
                (0.20, QColor(255,248,255,120)),
                (0.45, QColor(245,235,255,60)),
                (0.75, QColor(255,255,255,15)),
                (1.00, QColor(255,255,255,0))

            ]

        )

        # =============================================
        # Radial Rays
        # =============================================

        painter.save()

        painter.translate(cx, cy)

        for angle in range(0, 360, 3):

            painter.save()

            painter.rotate(angle)

            ray = QLinearGradient(
                0,
                0,
                0,
                -560
            )

            ray.setColorAt(0.00, QColor(255,255,255,0))
            ray.setColorAt(0.15, QColor(255,255,255,70))
            ray.setColorAt(0.45, QColor(250,242,255,42))
            ray.setColorAt(0.72, QColor(255,255,255,8))
            ray.setColorAt(1.00, QColor(255,255,255,0))

            painter.fillRect(
                -2,
                -700,
                4,
                560,
                QBrush(ray)
            )

            painter.restore()

        painter.restore()

    # ------------------------------------------------
    # Atmosphere Effects
    # ------------------------------------------------

    def _draw_atmosphere(
        self,
        painter,
        w,
        h
    ):

        # =============================================
        # Premium Glass Light Streaks
        # =============================================

        self._draw_linear(

            painter,

            0,

            0,

            w,

            h,

            [

                (0.00, QColor(255,255,255,0)),
                (0.22, QColor(255,255,255,22)),
                (0.34, QColor(255,255,255,0)),
                (0.66, QColor(255,255,255,14)),
                (1.00, QColor(255,255,255,0))

            ]

        )

        # =============================================
        # Floating Premium Particles
        # =============================================

        particles = [

            (0.36,0.26,5),
            (0.42,0.20,4),
            (0.58,0.20,4),
            (0.64,0.28,5),

            (0.32,0.48,4),
            (0.68,0.48,4),

            (0.40,0.66,5),
            (0.60,0.66,5),

        ]

        painter.setPen(Qt.NoPen)

        for px, py, r in particles:

            g = QRadialGradient(
                w * px,
                h * py,
                r * 8
            )

            g.setColorAt(
                0,
                QColor(255,255,255,120)
            )

            g.setColorAt(
                0.50,
                QColor(240,232,255,50)
            )

            g.setColorAt(
                1,
                QColor(255,255,255,0)
            )

            painter.setBrush(
                QBrush(g)
            )

            painter.drawEllipse(

                int(w * px - r * 4),

                int(h * py - r * 4),

                r * 8,

                r * 8

            )

        # =============================================
        # Soft Premium Fog
        # =============================================

        self._draw_linear(

            painter,

            0,

            h * 0.55,

            0,

            h,

            [

                (0.00, QColor(255,255,255,0)),
                (0.35, QColor(245,240,255,22)),
                (0.75, QColor(235,228,255,45)),
                (1.00, QColor(228,220,255,70))

            ]

        )

        # =============================================
        # Top Ambient Light
        # =============================================

        self._draw_linear(

            painter,

            0,

            0,

            0,

            h * 0.55,

            [

                (0.00, QColor(255,255,255,110)),
                (0.25, QColor(252,248,255,60)),
                (1.00, QColor(255,255,255,0))

            ]

        )

        # =============================================
        # Left Ambient Pink
        # =============================================

        self._draw_radial_glow(

            painter,

            -160,

            h * 0.26,

            w * 0.90,

            [

                (0.00, QColor(255,185,230,170)),
                (0.25, QColor(255,205,238,120)),
                (0.55, QColor(250,225,250,55)),
                (1.00, QColor(255,255,255,0))

            ]

        )

        # =============================================
        # Right Ambient Blue
        # =============================================

        self._draw_radial_glow(

            painter,

            w + 160,

            h * 0.26,

            w * 0.90,

            [

                (0.00, QColor(175,220,255,170)),
                (0.25, QColor(205,232,255,120)),
                (0.55, QColor(230,242,255,55)),
                (1.00, QColor(255,255,255,0))

            ]

        )

    # ------------------------------------------------
    # Final Effects
    # ------------------------------------------------

    def _draw_final_effects(
        self,
        painter,
        w,
        h
    ):

        # =============================================
        # Center Focus
        # =============================================

        self._draw_radial_glow(

            painter,

            w * 0.50,

            h * 0.44,

            min(w, h) * 0.42,

            [

                (0.00, QColor(255,255,255,180)),
                (0.25, QColor(250,246,255,95)),
                (0.60, QColor(240,232,255,35)),
                (1.00, QColor(255,255,255,0))

            ]

        )

        # =============================================
        # Edge Vignette
        # =============================================

        self._draw_radial_glow(

            painter,

            w / 2,

            h / 2,

            max(w, h) * 0.85,

            [

                (0.72, QColor(255,255,255,0)),
                (1.00, QColor(180,170,255,28))

            ]

        )

        # =============================================
        # Diamond Sparkles
        # =============================================

        sparkle_points = [

            (0.46,0.18),
            (0.54,0.18),

            (0.38,0.30),
            (0.62,0.30),

            (0.32,0.46),
            (0.68,0.46),

            (0.40,0.62),
            (0.60,0.62),

            (0.50,0.74),

        ]

        painter.setPen(Qt.NoPen)

        for px, py in sparkle_points:

            painter.setBrush(
                QColor(255,255,255,220)
            )

            painter.drawEllipse(

                int(w * px - 2),

                int(h * py - 2),

                4,

                4

            )

            self._draw_glow_circle(

                painter,

                w * px,

                h * py,

                18,

                [

                    (0.00, QColor(255,255,255,120)),
                    (1.00, QColor(255,255,255,0))

                ]

            )

        # =============================================
        # Center Cloud Bloom
        # =============================================

        self._draw_radial_glow(

            painter,

            w * 0.50,

            h * 0.44,

            min(w, h) * 0.82,

            [

                (0.00, QColor(255,255,255,165)),
                (0.28, QColor(250,246,255,95)),
                (0.58, QColor(242,236,255,45)),
                (1.00, QColor(255,255,255,0))

            ]

        )

        # =============================================
        # Final Color Harmony
        # =============================================

        self._draw_linear(

            painter,

            0,

            0,

            w,

            h,

            [

                (0.00, QColor(255,205,235,80)),
                (0.30, QColor(248,244,255,6)),
                (0.70, QColor(205,228,255,65)),
                (1.00, QColor(255,255,255,6))

            ]

        )

        # =============================================
        # Premium Finish
        # =============================================

        self._draw_linear(

            painter,

            0,

            0,

            0,

            h,

            [

                (0.00, QColor(255,255,255,35)),
                (0.35, QColor(255,248,255,10)),
                (0.50, QColor(255,255,255,0)),
                (1.00, QColor(220,215,255,30))

            ]

        )

    # ------------------------------------------------

    def paintEvent(self, event):

        super().paintEvent(event)

        painter = QPainter(self)

        painter.setRenderHint(
            QPainter.Antialiasing,
            True
        )

        painter.setRenderHint(
            QPainter.SmoothPixmapTransform,
            True
        )

        w = self.width()
        h = self.height()

        # -----------------------------------------
        # Base Background
        # -----------------------------------------

        self._draw_background(
            painter,
            w,
            h
        )

        # -----------------------------------------
        # Fast Startup
        # -----------------------------------------

        if self.fast_mode:
            return

        # -----------------------------------------
        # Premium Effects
        # -----------------------------------------

        self._draw_stars_and_particles(
            painter,
            w,
            h
        )

        self._draw_floor_effects(
            painter,
            w,
            h
        )

        self._draw_halo(
            painter,
            w,
            h
        )

        self._draw_atmosphere(
            painter,
            w,
            h
        )

        self._draw_final_effects(
            painter,
            w,
            h
        )