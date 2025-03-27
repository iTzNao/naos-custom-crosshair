import sys
import os
import ctypes
import win32api
from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import Qt, QTimer, QPoint
from PyQt5.QtGui import QPainter, QPen, QColor

VK_RBUTTON = 0x02

class CrosshairOverlay(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Nao's Custom Crosshair Overlay")
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self.showFullScreen()
        try:
            hwnd = self.winId().__int__()
            ex_style = ctypes.windll.user32.GetWindowLongW(hwnd, -20)
            ctypes.windll.user32.SetWindowLongW(hwnd, -20, ex_style | 0x20 | 0x80000)
        except Exception as e:
            print("Error setting window style:", e)

        base_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
        crosshairs_dir = os.path.join(base_dir, "crosshairs")
        if not os.path.exists(crosshairs_dir):
            os.makedirs(crosshairs_dir)
        self.crosshair_files = [os.path.join(crosshairs_dir, f) for f in os.listdir(crosshairs_dir) if f.endswith(".ncc")]

        self.crosshair_color = QColor(255, 0, 0, 255)
        self.hue = 0
        self.current_preset = 0
        self.opacity = 1.0
        self.hide_on_ads = False
        self.hide_on_hipfire = False
        self.is_hidden = True
        self.shapes = []
        self.size = 1
        self.crosshair_name = "Unnamed Crosshair"

        self.rainbow_offset = 0

        self.loadCrosshairSettings()
        self.hide()

        timer = QTimer(self)
        timer.timeout.connect(self.updateCrosshair)
        timer.start(16)

        self.ads_timer = QTimer(self)
        self.ads_timer.timeout.connect(self.check_ads)
        self.ads_timer.start()

        self.rgb_timer = QTimer(self)
        self.rgb_timer.timeout.connect(self.updateRainbowOffset)
        self.rgb_timer.start(50)

    def loadCrosshairSettings(self):
        if self.current_preset >= 0 and self.current_preset < len(self.crosshair_files):
            filepath = self.crosshair_files[self.current_preset]
            try:
                with open(filepath, "r") as f:
                    self.shapes = []
                    self.size = 1
                    self.crosshair_name = "Unnamed Crosshair"
                    for line in f:
                        line = line.strip()
                        if line.startswith("//") or not line:
                            continue
                        if line.startswith("name="):
                            self.crosshair_name = line.split("=", 1)[1].strip()
                        elif line.startswith("size="):
                            self.size = int(line.split("=", 1)[1])
                        elif line.split()[0] in {"line", "circle", "triangle", "rectangle", "arc"}:
                            shape = {"type": line.split()[0], "params": {}}
                            for param in line.split()[1:]:
                                if "=" in param:
                                    key, value = param.split("=")
                                    shape["params"][key] = int(value) if key in {"x", "y", "x1", "y1", "x2", "y2", "width", "height", "weight", "radius", "start_angle", "span_angle", "hide_on_ads", "hide_on_hipfire", "rotation", "right_angle"} else value
                            self.shapes.append(shape)
            except Exception as e:
                print(f"Error loading settings from {filepath}: {e}")

    def updateCrosshair(self):
        self.update()

    def updateRainbowOffset(self):
        self.rainbow_offset = (self.rainbow_offset + 5) % 360

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        screen_rect = self.rect()
        center_x = screen_rect.width() // 2
        center_y = screen_rect.height() // 2

        is_ads_pressed = win32api.GetAsyncKeyState(VK_RBUTTON) & 0x8000

        for shape in self.shapes:
            hide_on_ads = shape["params"].get("hide_on_ads", 0) == 1
            hide_on_hipfire = shape["params"].get("hide_on_hipfire", 0) == 1

            if (hide_on_ads and is_ads_pressed) or (hide_on_hipfire and not is_ads_pressed):
                continue

            color_param = shape["params"].get("color", f"{self.crosshair_color.red()},{self.crosshair_color.green()},{self.crosshair_color.blue()}")
            if color_param.lower() == "rgb":
                color = QColor.fromHsv(self.rainbow_offset, 255, 255)
            else:
                color = QColor(*map(int, color_param.split(",")))

            weight = int(shape["params"].get("weight", 1))
            opacity = float(shape["params"].get("opacity", self.opacity))
            filled = shape["params"].get("filled", "1") == "1"  # Default to filled

            painter.setOpacity(opacity)
            pen = QPen(color)
            pen.setWidth(weight)
            painter.setPen(pen)

            if filled:
                painter.setBrush(color)
            else:
                painter.setBrush(Qt.NoBrush)

            rotation = int(shape["params"].get("rotation", 0)) % 360

            if shape["type"] == "line":
                x1 = shape["params"].get("x1", 0) * self.size
                y1 = shape["params"].get("y1", 0) * self.size
                x2 = shape["params"].get("x2", 0) * self.size
                y2 = shape["params"].get("y2", 0) * self.size
                painter.save()
                painter.translate(center_x, center_y)
                painter.rotate(rotation)
                painter.drawLine(x1, y1, x2, y2)
                painter.restore()
            elif shape["type"] == "circle":
                x = shape["params"].get("x", 0) * self.size
                y = shape["params"].get("y", 0) * self.size
                radius = int(shape["params"].get("radius", 1)) * self.size
                painter.save()
                painter.translate(center_x + x, center_y + y)
                painter.rotate(rotation)
                painter.drawEllipse(-radius, -radius, 2 * radius, 2 * radius)
                painter.restore()
            elif shape["type"] == "triangle":
                x = shape["params"].get("x", 0) * self.size
                y = shape["params"].get("y", 0) * self.size
                width = shape["params"].get("width", 1) * self.size
                height = shape["params"].get("height", 1) * self.size
                right_angle = shape["params"].get("right_angle", 0) == 1

                if right_angle:
                    points = [
                        QPoint(-width // 2, height // 2),  # Centered horizontally
                        QPoint(width // 2, height // 2),
                        QPoint(-width // 2, -height // 2),
                    ]
                else:
                    points = [
                        QPoint(0, -height // 2),
                        QPoint(-width // 2, height // 2),
                        QPoint(width // 2, height // 2),
                    ]

                painter.save()
                painter.translate(center_x + x, center_y + y)
                painter.rotate(rotation)
                painter.drawPolygon(*points)
                painter.restore()
            elif shape["type"] == "rectangle":
                x = shape["params"].get("x", 0) * self.size
                y = shape["params"].get("y", 0) * self.size
                width = shape["params"].get("width", 1) * self.size
                height = shape["params"].get("height", 1) * self.size

                painter.save()
                painter.translate(center_x + x, center_y + y)
                painter.rotate(rotation)
                painter.drawRect(-width // 2, -height // 2, width, height)
                painter.restore()
            elif shape["type"] == "arc":
                x = shape["params"].get("x", 0) * self.size
                y = shape["params"].get("y", 0) * self.size
                radius = int(shape["params"].get("radius", 1)) * self.size
                start_angle = int(shape["params"].get("start_angle", 0)) * 16
                span_angle = int(shape["params"].get("span_angle", 360)) * 16

                painter.save()
                painter.translate(center_x + x, center_y + y)
                painter.rotate(rotation)
                painter.drawArc(-radius, -radius, 2 * radius, 2 * radius, start_angle, span_angle)
                painter.restore()

    def nextCrosshair(self):
        self.current_preset = (self.current_preset + 1) % len(self.crosshair_files)
        self.loadCrosshairSettings()
        self.update()
        
    def previousCrosshair(self):
        self.current_preset = (self.current_preset - 1) % len(self.crosshair_files)
        self.loadCrosshairSettings()
        self.update()

    def check_ads(self):
        if not self.hide_on_ads and not self.hide_on_hipfire:
            return

        is_pressed = win32api.GetAsyncKeyState(VK_RBUTTON) & 0x8000
        if self.hide_on_hipfire:
            if is_pressed and self.is_hidden:
                self.show()
                self.is_hidden = False
            elif not is_pressed and not self.is_hidden:
                self.hide()
                self.is_hidden = True
        elif self.hide_on_ads:
            if is_pressed and not self.is_hidden:
                self.hide()
                self.is_hidden = True
            elif not is_pressed and self.is_hidden:
                self.show()
                self.is_hidden = False