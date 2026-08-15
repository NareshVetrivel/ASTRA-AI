"""
ASTRA-AI
Premium Right Status Panel
Review 1 Production UI
"""

from PySide6.QtCore import (
    Qt,
    QTimer,
    QPropertyAnimation,
    QEasingCurve,
)

from PySide6.QtGui import QColor

from PySide6.QtWidgets import (
    QWidget,
    QLabel,
    QVBoxLayout,
    QGridLayout,
    QSizePolicy,
    QGraphicsOpacityEffect,
)

import psutil
import subprocess

from ui.widgets.status_metric_tile import StatusMetricTile


class RightPanelWidget(QWidget):

    def __init__(self, parent=None):

        super().__init__(parent)

        self.setObjectName(
            "RightPanel"
        )

        self.setMinimumWidth(
            360
        )

        self.setMaximumWidth(
            370
        )

        self.setSizePolicy(
            QSizePolicy.Fixed,
            QSizePolicy.Expanding
        )

        # -------------------------------------------------
        # Fade State
        # -------------------------------------------------

        self._fade_effect = None

        self._fade_animation = None

        self._fade_hidden = False

        self._tile_effects_disabled = False

        # -------------------------------------------------
        # Build UI
        # -------------------------------------------------

        self.build_ui()

        # -------------------------------------------------
        # Live System Monitor
        # -------------------------------------------------

        self.monitor_timer = QTimer(
            self
        )

        self.monitor_timer.timeout.connect(
            self.update_system_metrics
        )

        self.monitor_timer.start(
            2000
        )

        self.update_system_metrics()

    # =====================================================
    # Build UI
    # =====================================================

    def build_ui(self):

        self.setStyleSheet("""

        QWidget#RightPanel{

            background:transparent;

            border:none;

        }

        """)

        root = QVBoxLayout(
            self
        )

        root.setContentsMargins(
            20,
            8,
            10,
            8
        )

        root.setSpacing(
            16
        )

        # -------------------------------------------------
        # Title
        # -------------------------------------------------

        self.title = QLabel(
            "QUICK STATUS"
        )

        self.title.setAlignment(
            Qt.AlignLeft |
            Qt.AlignVCenter
        )

        self.title.setContentsMargins(
            10,
            0,
            0,
            0
        )

        self.title.setStyleSheet("""

        color:#7C3AED;

        font-size:20px;

        font-weight:700;

        padding-left:4px;

        background:transparent;

        """)

        root.addWidget(
            self.title
        )

        # -------------------------------------------------
        # Dashboard Grid
        # -------------------------------------------------

        self.grid_container = QWidget()

        self.grid_container.setStyleSheet("""

        background:transparent;

        """)

        self.grid = QGridLayout(
            self.grid_container
        )

        self.grid.setContentsMargins(
            10,
            0,
            0,
            0
        )

        self.grid.setHorizontalSpacing(
            14
        )

        self.grid.setVerticalSpacing(
            14
        )

        self.grid.setAlignment(
            Qt.AlignTop |
            Qt.AlignLeft
        )

        root.addWidget(
            self.grid_container,
            stretch=1,
            alignment=Qt.AlignTop
        )

        # -------------------------------------------------
        # Metric Tiles
        # -------------------------------------------------

        self.health = StatusMetricTile(
            title="Health",
            value="Optimal",
            icon="💚",
            color="#16A34A"
        )

        self.cpu = StatusMetricTile(
            title="CPU",
            value="0%",
            icon="🖥️",
            color="#2563EB"
        )

        self.memory = StatusMetricTile(
            title="Memory",
            value="0%",
            icon="💾",
            color="#9333EA"
        )

        self.storage = StatusMetricTile(
            title="Storage",
            value="0%",
            icon="💽",
            color="#F97316"
        )

        self.battery = StatusMetricTile(
            title="Battery",
            value="--",
            icon="🔋",
            color="#16A34A"
        )

        self.temperature = StatusMetricTile(
            title="WiFi",
            value="Unknown",
            icon="📡",
            color="#2563EB"
        )

        self.network = StatusMetricTile(
            title="Speed",
            value="0 Mbps",
            icon="🚀",
            color="#7C3AED"
        )

        self.processes = StatusMetricTile(
            title="Processes",
            value="0",
            icon="⚙️",
            color="#0891B2"
        )

        # -------------------------------------------------
        # Dashboard
        # -------------------------------------------------

        self.grid.addWidget(
            self.health,
            0,
            0
        )

        self.grid.addWidget(
            self.cpu,
            0,
            1
        )

        self.grid.addWidget(
            self.memory,
            1,
            0
        )

        self.grid.addWidget(
            self.storage,
            1,
            1
        )

        self.grid.addWidget(
            self.battery,
            2,
            0
        )

        self.grid.addWidget(
            self.temperature,
            2,
            1
        )

        self.grid.addWidget(
            self.network,
            3,
            0
        )

        self.grid.addWidget(
            self.processes,
            3,
            1
        )

        # -------------------------------------------------
        # Equal Grid Stretch
        # -------------------------------------------------

        for column in range(2):

            self.grid.setColumnStretch(
                column,
                1
            )

        for row in range(4):

            self.grid.setRowStretch(
                row,
                1
            )

        # -------------------------------------------------
        # Store Metric Tiles
        # -------------------------------------------------

        self._metric_tiles = [

            self.health,

            self.cpu,

            self.memory,

            self.storage,

            self.battery,

            self.temperature,

            self.network,

            self.processes,

        ]

    # =====================================================
    # Fade Helpers
    # =====================================================

    def _disable_tile_effects(self):

        """
        Temporarily remove StatusMetricTile graphics
        effects while the parent opacity animation runs.

        This keeps the fade animation independent from the
        child drop-shadow effects.
        """

        if self._tile_effects_disabled:

            return

        for tile in self._metric_tiles:

            try:

                tile.setGraphicsEffect(
                    None
                )

            except Exception:

                pass

        self._tile_effects_disabled = True

    # -----------------------------------------------------

    def _restore_tile_effects(self):

        """
        Restore the original StatusMetricTile shadow
        effects after the fade animation completes.
        """

        if not self._tile_effects_disabled:

            return

        for tile in self._metric_tiles:

            try:

                shadow = getattr(
                    tile,
                    "shadow",
                    None
                )

                if shadow is not None:

                    tile.setGraphicsEffect(
                        shadow
                    )

            except Exception:

                pass

        self._tile_effects_disabled = False

    # =====================================================
    # Fade Out
    # =====================================================

    def fade_out(
        self,
        duration=650
    ):

        """
        Fade the complete Right Status Panel out.

        Used when Conversation Panel opens.
        """

        # -------------------------------------------------
        # Stop previous animation
        # -------------------------------------------------

        if self._fade_animation is not None:

            try:

                self._fade_animation.stop()

            except Exception:

                pass

        # -------------------------------------------------
        # Already hidden
        # -------------------------------------------------

        if self._fade_hidden:

            return

        # -------------------------------------------------
        # Disable nested tile graphics effects
        # -------------------------------------------------

        self._disable_tile_effects()

        # -------------------------------------------------
        # Create opacity effect
        # -------------------------------------------------

        if self._fade_effect is None:

            self._fade_effect = (
                QGraphicsOpacityEffect(
                    self
                )
            )

            self._fade_effect.setOpacity(
                1.0
            )

            self.setGraphicsEffect(
                self._fade_effect
            )

        else:

            self._fade_effect.setOpacity(
                1.0
            )

        # -------------------------------------------------
        # Animation
        # -------------------------------------------------

        self._fade_animation = (
            QPropertyAnimation(
                self._fade_effect,
                b"opacity",
                self
            )
        )

        self._fade_animation.setDuration(
            duration
        )

        self._fade_animation.setStartValue(
            1.0
        )

        self._fade_animation.setEndValue(
            0.0
        )

        self._fade_animation.setEasingCurve(
            QEasingCurve.InOutCubic
        )

        self._fade_animation.finished.connect(
            self._fade_out_finished
        )

        self._fade_animation.start()

    # =====================================================
    # Fade Out Finished
    # =====================================================

    def _fade_out_finished(self):

        self._fade_hidden = True

        if self._fade_effect is not None:

            self._fade_effect.setOpacity(
                0.0
            )

    # =====================================================
    # Fade In
    # =====================================================

    def fade_in(
        self,
        duration=650
    ):

        """
        Fade the complete Right Status Panel back in.

        Used when Conversation Panel closes.
        """

        # -------------------------------------------------
        # Stop previous animation
        # -------------------------------------------------

        if self._fade_animation is not None:

            try:

                self._fade_animation.stop()

            except Exception:

                pass

        # -------------------------------------------------
        # Create effect if required
        # -------------------------------------------------

        if self._fade_effect is None:

            self._fade_effect = (
                QGraphicsOpacityEffect(
                    self
                )
            )

            self._fade_effect.setOpacity(
                0.0
            )

            self.setGraphicsEffect(
                self._fade_effect
            )

        else:

            self._fade_effect.setOpacity(
                0.0
            )

        # -------------------------------------------------
        # Keep child effects disabled during fade
        # -------------------------------------------------

        self._disable_tile_effects()

        # -------------------------------------------------
        # Animation
        # -------------------------------------------------

        self._fade_animation = (
            QPropertyAnimation(
                self._fade_effect,
                b"opacity",
                self
            )
        )

        self._fade_animation.setDuration(
            duration
        )

        self._fade_animation.setStartValue(
            0.0
        )

        self._fade_animation.setEndValue(
            1.0
        )

        self._fade_animation.setEasingCurve(
            QEasingCurve.InOutCubic
        )

        self._fade_animation.finished.connect(
            self._fade_in_finished
        )

        self._fade_animation.start()

    # =====================================================
    # Fade In Finished
    # =====================================================

    def _fade_in_finished(self):

        self._fade_hidden = False

        if self._fade_effect is not None:

            self._fade_effect.setOpacity(
                1.0
            )

        # -------------------------------------------------
        # Remove parent opacity effect
        # -------------------------------------------------

        try:

            self.setGraphicsEffect(
                None
            )

        except Exception:

            pass

        self._fade_effect = None

        # -------------------------------------------------
        # Restore tile shadows
        # -------------------------------------------------

        self._restore_tile_effects()

        self.update()

    # =====================================================
    # Public API
    # =====================================================

    def set_cpu(
        self,
        value
    ):

        if self.cpu.value != value:

            self.cpu.set_value(
                value
            )

    # -----------------------------------------------------

    def set_memory(
        self,
        value
    ):

        if self.memory.value != value:

            self.memory.set_value(
                value
            )

    # -----------------------------------------------------

    def set_storage(
        self,
        value
    ):

        if self.storage.value != value:

            self.storage.set_value(
                value
            )

    # -----------------------------------------------------

    def set_battery(
        self,
        value
    ):

        if self.battery.value != value:

            self.battery.set_value(
                value
            )

    # -----------------------------------------------------

    def set_temperature(
        self,
        value
    ):

        if self.temperature.value != value:

            self.temperature.set_value(
                value
            )

    # -----------------------------------------------------

    def set_network(
        self,
        value
    ):

        if self.network.value != value:

            self.network.set_value(
                value
            )

    # -----------------------------------------------------

    def set_processes(
        self,
        value
    ):

        if self.processes.value != value:

            self.processes.set_value(
                value
            )

    # =====================================================
    # WiFi
    # =====================================================

    def get_wifi_name(self):

        try:

            output = subprocess.check_output(
                "netsh wlan show interfaces",
                shell=True,
                text=True,
                encoding="utf-8",
                errors="ignore"
            )

            for line in output.splitlines():

                if (
                    "SSID" in line
                    and
                    "BSSID" not in line
                ):

                    return (
                        line.split(
                            ":",
                            1
                        )[1].strip()
                    )

        except Exception:

            pass

        return "Not Connected"

    # =====================================================
    # Live System Monitor
    # =====================================================

    def update_system_metrics(self):

        try:

            cpu = psutil.cpu_percent(
                interval=None
            )

            memory = (
                psutil.virtual_memory()
                .percent
            )

            disk = (
                psutil.disk_usage("/")
                .percent
            )

            process_count = len(
                psutil.pids()
            )

            self.set_cpu(
                f"{cpu:.0f}%"
            )

            self.set_memory(
                f"{memory:.0f}%"
            )

            self.set_storage(
                f"{disk:.0f}%"
            )

            self.set_processes(
                str(process_count)
            )

            # -------------------------------------------------
            # Battery
            # -------------------------------------------------

            battery = (
                psutil.sensors_battery()
            )

            if battery:

                if battery.power_plugged:

                    battery_text = (
                        f"⚡ {battery.percent:.0f}%"
                    )

                else:

                    battery_text = (
                        f"{battery.percent:.0f}%"
                    )

                self.set_battery(
                    battery_text
                )

            else:

                self.set_battery(
                    "N/A"
                )

            # -------------------------------------------------
            # Health
            # -------------------------------------------------

            if cpu < 40 and memory < 60:

                if (
                    self.health.value
                    != "Optimal"
                ):

                    self.health.set_value(
                        "Optimal",
                        "#16A34A"
                    )

            elif cpu < 75:

                if (
                    self.health.value
                    != "Good"
                ):

                    self.health.set_value(
                        "Good",
                        "#2563EB"
                    )

            else:

                if (
                    self.health.value
                    != "Busy"
                ):

                    self.health.set_value(
                        "Busy",
                        "#F59E0B"
                    )

            # -------------------------------------------------
            # WiFi
            # -------------------------------------------------

            if not hasattr(
                self,
                "_wifi_counter"
            ):

                self._wifi_counter = 0

            self._wifi_counter += 1

            if self._wifi_counter >= 5:

                self._wifi_counter = 0

                wifi = (
                    self.get_wifi_name()
                )

                self.set_temperature(
                    wifi
                )

            # -------------------------------------------------
            # Network Speed
            # -------------------------------------------------

            net1 = (
                psutil.net_io_counters()
            )

            if not hasattr(
                self,
                "_last_bytes"
            ):

                self._last_bytes = (
                    net1.bytes_recv
                )

            speed = (
                (
                    net1.bytes_recv
                    -
                    self._last_bytes
                )
                / 1024
                / 1024
            )

            self._last_bytes = (
                net1.bytes_recv
            )

            self.set_network(
                f"{speed:.2f} MB/s"
            )

        except Exception as error:

            print(
                "Right Panel Error:",
                error
            )