from PyQt5.QtWidgets import QSystemTrayIcon, QMenu, QAction, QMessageBox, QLabel, QWidgetAction, QColorDialog
from PyQt5.QtGui import QIcon, QPainter, QPen, QColor
from PyQt5.QtCore import QTimer
import os
import sys

class CrosshairMenu(QMenu):
    def __init__(self, app, crosshair, version):
        super().__init__()
        self.app = app
        self.crosshair = crosshair
        self.version = version
        self.rainbow_offset = 0

        if not QSystemTrayIcon.isSystemTrayAvailable():
            QMessageBox.critical(None, "Error", "System tray is not available.")
            app.quit()
            return

        icon_path = self.resource_path("icon.ico")
        self.tray_icon = QSystemTrayIcon(QIcon(icon_path), app)
        self.initMenu()

        self.animation_timer = QTimer(self)
        self.animation_timer.timeout.connect(self.updateAnimation)
        self.animation_timer.start(50)

    def resource_path(self, relative_path):
        if hasattr(sys, '_MEIPASS'):
            return os.path.join(sys._MEIPASS, relative_path)
        return os.path.join(os.path.abspath("."), relative_path)

    def initMenu(self):
        self.setStyleSheet("""
            QMenu { 
                background-color: #2b2b2b; 
                color: #cccccc; 
                font-size: 16px;
                border-radius: 8px;
                padding: 4px;
            }
            QMenu::item { 
                padding: 4px 25px 4px 20px;
            }
            QMenu::item:selected { 
                background-color: #3a3a3a; 
            }
        """)

        h1_style = """
            background-color: #1a1a1a;
            font-weight: bold;
            color: #ffffff;
            padding: 8px 33px 8px 33px;
            font-size: 14px;
        """
        self.main_title_label = QLabel(f"Nao's Custom Crosshair [v{self.version}]")
        self.main_title_label.setStyleSheet(h1_style)
        self.main_title_label_widget = QWidgetAction(self)
        self.main_title_label_widget.setDefaultWidget(self.main_title_label)
        self.addAction(self.main_title_label_widget)

        self.crosshair_name_action = QAction(f"Current Crosshair: {self.crosshair.crosshair_name}")
        self.crosshair_name_action.setEnabled(False)
        self.addAction(self.crosshair_name_action)
        
        self.addSeparator()

        self.toggle_crosshair_preset_action = QAction("Next Crosshair")
        self.toggle_crosshair_preset_action.triggered.connect(self.nextCrosshair)
        self.addAction(self.toggle_crosshair_preset_action)

        self.previous_crosshair_preset_action = QAction("Previous Crosshair")
        self.previous_crosshair_preset_action.triggered.connect(self.previousCrosshair)
        self.addAction(self.previous_crosshair_preset_action)

        self.open_folder_action = QAction("Open Crosshairs Folder")
        self.open_folder_action.triggered.connect(self.openCrosshairsFolder)
        self.addAction(self.open_folder_action)

        self.addSeparator()

        self.exit_action = QAction("Quit")
        self.exit_action.triggered.connect(self.app.quit)
        self.addAction(self.exit_action)

        self.tray_icon.setContextMenu(self)
        self.tray_icon.setToolTip("Nao's Custom Crosshair")
        self.tray_icon.show()

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        pen = QPen()
        pen.setWidth(2)
        color = QColor.fromHsv(self.rainbow_offset, 255, 255)
        pen.setColor(color)
        painter.setPen(pen)
        painter.drawRect(self.rect().adjusted(2, 2, -2, -2))

    def updateAnimation(self):
        self.rainbow_offset = (self.rainbow_offset + 5) % 360
        self.update()

    def mouseReleaseEvent(self, event):
        action = self.actionAt(event.pos())
        if action and action.text().strip() != "Quit":
            action.trigger()
            event.accept()
        else:
            super().mouseReleaseEvent(event)

    def updateCrosshairName(self):
        self.crosshair_name_action.setText(f"Current Crosshair: {self.crosshair.crosshair_name}")

    def nextCrosshair(self):
        self.crosshair.nextCrosshair()
        self.updateCrosshairName()

    def previousCrosshair(self):
        self.crosshair.previousCrosshair()
        self.updateCrosshairName()

    def openCrosshairsFolder(self):
        import subprocess
        import os
        crosshairs_dir = os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])), "crosshairs")  # Open the crosshairs folder
        subprocess.Popen(f'explorer "{crosshairs_dir}"')
