VERSION = "0.3.2"

import sys
import threading
import os
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QIcon # Import QIcon
from overlay import CrosshairOverlay
from menu import CrosshairMenu

def main():
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon(os.path.join(os.path.dirname(os.path.abspath(__file__)), "icon.ico")))
    
    crosshair = CrosshairOverlay()
    crosshair.show()

    menu = CrosshairMenu(app, crosshair, VERSION)
    menu.show()
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
