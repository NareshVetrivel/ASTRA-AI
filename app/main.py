import sys

from PySide6.QtWidgets import QApplication

from automation.application_scanner import ApplicationScanner

from ui.main_window import MainWindow


def main():

    scanner = ApplicationScanner()

    scanner.scan()

    app = QApplication(sys.argv)

    window = MainWindow()

    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":

    main()