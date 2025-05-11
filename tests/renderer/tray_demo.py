from PyQt6.QtWidgets import QApplication, QSystemTrayIcon, QMenu
from PyQt6.QtGui import QIcon
import sys, os

app = QApplication(sys.argv)
icon_path = os.path.abspath("assets/sprites/idle/frame_01.png")
print("icon_path:", icon_path, "exists:", os.path.exists(icon_path))
tray = QSystemTrayIcon(QIcon(icon_path), app)
menu = QMenu()
menu.addAction("测试菜单")
tray.setContextMenu(menu)
tray.show()
sys.exit(app.exec())
