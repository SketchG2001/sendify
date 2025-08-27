import sys
from PyQt6.QtWidgets import QApplication
from ui_main import MainUI

def main():
    app = QApplication(sys.argv)
    main_window = MainUI()
    main_window.show()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()
