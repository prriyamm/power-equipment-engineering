"""Draw the application icon (app/assets/icon.png) with Qt. Run once; the PNG is committed."""
import sys
from pathlib import Path

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QGuiApplication, QImage, QLinearGradient, QPainter, QPainterPath, QPen

app = QGuiApplication(sys.argv)
size = 512
img = QImage(size, size, QImage.Format_ARGB32)
img.fill(Qt.transparent)
p = QPainter(img)
p.setRenderHint(QPainter.Antialiasing)
g = QLinearGradient(0, 0, size, size)
g.setColorAt(0, QColor("#2f6fd6"))
g.setColorAt(1, QColor("#1f2a37"))
p.setBrush(g)
p.setPen(Qt.NoPen)
p.drawRoundedRect(QRectF(16, 16, size - 32, size - 32), 96, 96)
# three phase bars
for i, c in enumerate(("#d64545", "#f0c419", "#2e9d5b")):
    p.setBrush(QColor(c))
    p.drawRoundedRect(QRectF(96, 300 + i * 46, 320, 28), 12, 12)
# lightning bolt
bolt = QPainterPath()
for k, (x, y) in enumerate(((290, 70), (170, 250), (250, 250), (210, 420), (350, 210), (265, 210), (320, 70))):
    (bolt.moveTo if k == 0 else bolt.lineTo)(QPointF(x, y))
bolt.closeSubpath()
p.setBrush(QColor("#ffffff"))
p.setPen(QPen(QColor("#1f2a37"), 10))
p.drawPath(bolt)
p.end()
out = Path(__file__).parent / "assets" / "icon.png"
img.save(str(out))
print(out)
