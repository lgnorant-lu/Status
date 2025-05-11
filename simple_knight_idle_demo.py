import sys
import os
from PyQt6.QtWidgets import QApplication, QLabel, QWidget
from PyQt6.QtCore import Qt, QTimer, QPoint
from PyQt6.QtGui import QPixmap, QPainter, QGuiApplication

# 修正图片路径，优先查找根目录下frame_01.png~frame_08.png，否则查找assets/sprites/idle/
def get_idle_frame_paths():
    root_dir = os.path.dirname(__file__)
    paths = []
    for i in range(1, 9):
        root_path = os.path.join(root_dir, f'frame_{i:02d}.png')
        asset_path = os.path.join(root_dir, 'assets', 'sprites', 'idle', f'frame_{i:02d}.png')
        if os.path.exists(root_path):
            paths.append(root_path)
        elif os.path.exists(asset_path):
            paths.append(asset_path)
        else:
            paths.append(None)
    return paths

IDLE_FRAME_PATHS = get_idle_frame_paths()
IDLE_FRAME_COUNT = 8
FRAME_SIZE = (64, 64)
FRAME_INTERVAL_MS = 120

class KnightIdleWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(*FRAME_SIZE)
        self.idle_frames = self.load_idle_frames()
        self.current_frame = 0
        self.label = QLabel(self)
        self.label.setGeometry(0, 0, *FRAME_SIZE)
        self.label.setScaledContents(True)
        self.update_frame()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.next_frame)
        self.timer.start(FRAME_INTERVAL_MS)
        self.dragging = False
        self.drag_pos = QPoint()

    def load_idle_frames(self):
        frames = []
        for path in IDLE_FRAME_PATHS:
            if path and os.path.exists(path):
                frames.append(QPixmap(path))
            else:
                pix = QPixmap(*FRAME_SIZE)
                pix.fill(Qt.GlobalColor.transparent)
                frames.append(pix)
        return frames

    def update_frame(self):
        self.label.setPixmap(self.idle_frames[self.current_frame])

    def next_frame(self):
        self.current_frame = (self.current_frame + 1) % len(self.idle_frames)
        self.update_frame()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.dragging = True
            self.drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if self.dragging and event.buttons() & Qt.MouseButton.LeftButton:
            new_pos = event.globalPosition().toPoint() - self.drag_pos
            screen = QGuiApplication.primaryScreen().availableGeometry()
            x = max(screen.left(), min(new_pos.x(), screen.right() - self.width()))
            y = max(screen.top(), min(new_pos.y(), screen.bottom() - self.height()))
            self.move(x, y)
            event.accept()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.dragging = False
            event.accept()

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.flash_window()
            event.accept()

    def flash_window(self):
        orig = self.windowOpacity()
        self.setWindowOpacity(0.5)
        QTimer.singleShot(100, lambda: self.setWindowOpacity(orig))

if __name__ == '__main__':
    app = QApplication(sys.argv)
    knight = KnightIdleWidget()
    knight.move(200, 200)
    knight.show()
    print('KnightIdleWidget launched. If you do not see a window, check all screens and taskbar.')
    sys.exit(app.exec())
