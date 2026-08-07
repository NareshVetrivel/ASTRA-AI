"""
ASTRA-AI
Premium Right Status Panel
Review 1 Production UI
"""

from PySide6.QtCore import (
    Qt,
    QTimer,
)

import psutil
import subprocess

from ui.widgets.status_metric_tile import StatusMetricTile

from PySide6.QtWidgets import (
    QWidget,
    QLabel,
    QVBoxLayout,
    QGridLayout,
    QSizePolicy,
)


class RightPanelWidget(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setObjectName("RightPanel")

        self.setMinimumWidth(360)
        self.setMaximumWidth(370)

        self.setSizePolicy(
            QSizePolicy.Fixed,
            QSizePolicy.Expanding
        )

        self.build_ui()

        # -------------------------------------------------
        # Live System Monitor
        # -------------------------------------------------

        self.monitor_timer = QTimer(self)

        self.monitor_timer.timeout.connect(
            self.update_system_metrics
        )

        self.monitor_timer.start(2000)

        self.update_system_metrics()

    # ---------------------------------------------------------
    # Build UI
    # ---------------------------------------------------------

    def build_ui(self):

        self.setStyleSheet("""

        QWidget#RightPanel{

            background:transparent;
            border:none;

        }

        """)

        root = QVBoxLayout(self)

        root.setContentsMargins(
            20,
            8,
            10,
            8
        )

        root.setSpacing(16)

        # -------------------------------------------------
        # Title
        # -------------------------------------------------

        title = QLabel("QUICK STATUS")

        title.setAlignment(
            Qt.AlignLeft |
            Qt.AlignVCenter
        )

        title.setContentsMargins(
            10,
            0,
            0,
            0
        )

        title.setStyleSheet("""

        color:#7C3AED;

        font-size:20px;

        font-weight:700;

        padding-left:4px;

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

        self.grid.setContentsMargins(
            10,
            0,
            0,
            0
        )

        self.grid.setHorizontalSpacing(14)

        self.grid.setVerticalSpacing(14)

        self.grid.setAlignment(
            Qt.AlignTop | Qt.AlignLeft
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
        # 2 × 4 Premium Dashboard
        # -------------------------------------------------

        self.grid.addWidget(self.health,       0, 0)
        self.grid.addWidget(self.cpu,          0, 1)

        self.grid.addWidget(self.memory,       1, 0)
        self.grid.addWidget(self.storage,      1, 1)

        self.grid.addWidget(self.battery,      2, 0)
        self.grid.addWidget(self.temperature,  2, 1)

        self.grid.addWidget(self.network,      3, 0)
        self.grid.addWidget(self.processes,    3, 1)

        # -------------------------------------------------
        # Equal Grid Stretch
        # -------------------------------------------------

        for column in range(2):
            self.grid.setColumnStretch(column, 1)

        for row in range(4):
            self.grid.setRowStretch(row, 1)

    # ---------------------------------------------------------
    # Public API
    # ---------------------------------------------------------

    def set_cpu(self, value):

        if self.cpu.value != value:

            self.cpu.set_value(value)


    def set_memory(self, value):

        if self.memory.value != value:

            self.memory.set_value(value)


    def set_storage(self, value):

        if self.storage.value != value:

            self.storage.set_value(value)


    def set_battery(self, value):

        if self.battery.value != value:

            self.battery.set_value(value)


    def set_temperature(self, value):

        if self.temperature.value != value:

            self.temperature.set_value(value)


    def set_network(self, value):

        if self.network.value != value:

            self.network.set_value(value)


    def set_processes(self, value):

        if self.processes.value != value:

            self.processes.set_value(value)


    # ---------------------------------------------------------
    # Live System Monitor
    # ---------------------------------------------------------

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

                if "SSID" in line and "BSSID" not in line:

                    return line.split(":")[1].strip()

        except Exception:

            pass

        return "Not Connected"

    def update_system_metrics(self):

        try:

            cpu = psutil.cpu_percent(interval=None)

            memory = psutil.virtual_memory().percent

            disk = psutil.disk_usage("/").percent

            process_count = len(psutil.pids())

            self.set_cpu(f"{cpu:.0f}%")

            self.set_memory(f"{memory:.0f}%")

            self.set_storage(f"{disk:.0f}%")

            self.set_processes(str(process_count))

            # -------------------------
            # Battery
            # -------------------------

            battery = psutil.sensors_battery()

            if battery:

                if battery.power_plugged:

                    battery_text = f"⚡ {battery.percent:.0f}%"

                else:

                    battery_text = f"{battery.percent:.0f}%"

                self.set_battery(
                    battery_text
                )

            else:

                self.set_battery("N/A")

            # -------------------------
            # Health
            # -------------------------

            if cpu < 40 and memory < 60:

                if self.health.value != "Optimal":

                    self.health.set_value(
                        "Optimal",
                        "#16A34A"
                    )

            elif cpu < 75:

                if self.health.value != "Good":

                    self.health.set_value(
                        "Good",
                        "#2563EB"
                    )

            else:

                if self.health.value != "Busy":

                    self.health.set_value(
                        "Busy",
                        "#F59E0B"
                    )

            # -------------------------
            # WiFi Name
            # -------------------------

            if not hasattr(self, "_wifi_counter"):

                self._wifi_counter = 0

            self._wifi_counter += 1

            # 10 seconds-ku once dhaan CMD execute pannuvom
            if self._wifi_counter >= 5:

                self._wifi_counter = 0

                wifi = self.get_wifi_name()

                self.set_temperature(wifi)

            # -------------------------
            # Network Speed
            # -------------------------

            net1 = psutil.net_io_counters()

            if not hasattr(self, "_last_bytes"):

                self._last_bytes = net1.bytes_recv

            speed = (net1.bytes_recv - self._last_bytes) / 1024 / 1024

            self._last_bytes = net1.bytes_recv

            self.set_network(f"{speed:.2f} MB/s")

        except Exception as error:

            print(
                "Right Panel Error:",
                error
            )