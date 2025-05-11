"""
---------------------------------------------------------------
File name:                  pyqt_renderer.py
Author:                     Ignorant-lu
Date created:               2025/04/15
Description:                PyQt6桌宠Idle动画窗口渲染模块，实现无边框、透明、可拖动、动画循环的桌宠主窗口。
----------------------------------------------------------------
Changed history:            
                            2025/04/15: 初始创建;
                            2025/04/15: 按全局规范补充头部与方法注释;
----
"""

import os
from PyQt6.QtWidgets import QWidget, QLabel, QApplication, QSystemTrayIcon, QMenu
from PyQt6.QtGui import QAction, QPixmap, QIcon, QGuiApplication
from PyQt6.QtCore import Qt, QTimer, QPoint
import sys

# 动画帧相关常量
FRAME_SIZE = (64, 64)

# 全局托盘对象引用，避免被GC
tray_icon_global = None

class AnimationState:
    def __init__(self, name, frame_paths, fps):
        self.name = name
        self.frame_paths = frame_paths
        self.fps = fps
        self.frames = self.load_frames()
        self.frame_count = len(self.frames)

    def load_frames(self):
        frames = []
        for path in self.frame_paths:
            if path and os.path.exists(path):
                frames.append(QPixmap(path))
            else:
                pix = QPixmap(*FRAME_SIZE)
                pix.fill(Qt.GlobalColor.transparent)
                frames.append(pix)
        return frames

class AnimationStateMachine:
    def __init__(self, state_configs, parent_widget):
        self.states = {}
        self.current_state = None
        self.current_frame = 0
        self.timer = QTimer(parent_widget)
        self.timer.timeout.connect(self.next_frame)
        self.parent_widget = parent_widget
        for name, cfg in state_configs.items():
            self.states[name] = AnimationState(name, cfg['frame_paths'], cfg['fps'])
        self.switch_state('idle')

    def switch_state(self, state_name):
        if state_name not in self.states:
            print(f"[调试] 未知状态: {state_name}")
            return
        self.current_state = self.states[state_name]
        self.current_frame = 0
        self.timer.stop()
        self.timer.start(1000 // self.current_state.fps)
        self.parent_widget.label.setPixmap(self.current_state.frames[self.current_frame])
        print(f"[调试] 切换到状态: {state_name}")

    def next_frame(self):
        self.current_frame = (self.current_frame + 1) % self.current_state.frame_count
        self.parent_widget.label.setPixmap(self.current_state.frames[self.current_frame])

class KnightIdleWidget(QWidget):
    """桌宠Idle动画窗口主类。

    支持无边框、透明、置顶、可拖动。
    Idle动画循环渲染。
    鼠标拖动、边界检测、双击闪烁反馈。
    托盘菜单与退出功能。
    """
    def __init__(self):
        """初始化窗口与动画。"""
        super().__init__()
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(*FRAME_SIZE)
        self.label = QLabel(self)
        self.label.setGeometry(0, 0, *FRAME_SIZE)
        self.label.setScaledContents(True)

        # 动画状态配置（MVP：Idle+Walk）
        state_configs = {
            'idle': {
                'frame_paths': [os.path.abspath(f"assets/sprites/idle/frame_{i:02d}.png") for i in range(1, 9)],
                'fps': 8
            },
            'walk': {
                'frame_paths': [os.path.abspath(f"assets/sprites/walk/frame_{i:02d}.png") for i in range(1, 7)],
                'fps': 10
            }
        }
        self.anim_sm = AnimationStateMachine(state_configs, self)
        # 默认Idle，测试可手动切换
        # self.anim_sm.switch_state('walk')

        # 托盘菜单与退出功能
        global tray_icon_global
        print("[调试] 创建托盘对象")
        icon_path = os.path.abspath("assets/sprites/idle/frame_01.png")
        print("[调试] 托盘icon_path:", icon_path, "exists:", os.path.exists(icon_path))
        tray_icon_global = QSystemTrayIcon(QIcon(icon_path), QApplication.instance())
        self.tray = tray_icon_global
        print("[调试] 设置托盘图标")
        menu = QMenu()
        show_action = QAction("显示", self)
        def on_show():
            print("[调试] 触发显示菜单项")
            self.show()
        show_action.triggered.connect(on_show)
        exit_action = QAction("退出", self)
        def on_exit():
            print("[调试] 触发退出菜单项")
            self.exit_app()
        exit_action.triggered.connect(on_exit)
        menu.addAction(show_action)
        menu.addAction(exit_action)
        self.tray.setContextMenu(menu)
        print("[调试] 设置托盘菜单并显示")
        self.tray.show()
        self.tray.activated.connect(self._on_tray_activated)

    def switch_animation_state(self, state_name):
        self.anim_sm.switch_state(state_name)

    def mousePressEvent(self, event):
        """鼠标左键按下：准备拖动。

        Args:
            event (QMouseEvent): 鼠标事件
        """
        if event.button() == Qt.MouseButton.LeftButton:
            self.dragging = True
            self.drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        """鼠标拖动：移动窗口，自动边界检测。

        Args:
            event (QMouseEvent): 鼠标事件
        """
        if hasattr(self, 'dragging') and self.dragging and event.buttons() & Qt.MouseButton.LeftButton:
            new_pos = event.globalPosition().toPoint() - self.drag_pos
            screen = QGuiApplication.primaryScreen().availableGeometry()
            x = max(screen.left(), min(new_pos.x(), screen.right() - self.width()))
            y = max(screen.top(), min(new_pos.y(), screen.bottom() - self.height()))
            self.move(x, y)
            event.accept()

    def mouseReleaseEvent(self, event):
        """鼠标释放：结束拖动。

        Args:
            event (QMouseEvent): 鼠标事件
        """
        if event.button() == Qt.MouseButton.LeftButton:
            if hasattr(self, 'dragging'):
                self.dragging = False
            event.accept()

    def mouseDoubleClickEvent(self, event):
        """鼠标双击：闪烁反馈。

        Args:
            event (QMouseEvent): 鼠标事件
        """
        if event.button() == Qt.MouseButton.LeftButton:
            self.flash_window()
            event.accept()

    def flash_window(self):
        """窗口闪烁效果
        
        Args:
            event (QMouseEvent): 鼠标事件
        """
        orig = self.windowOpacity()
        self.setWindowOpacity(0.5)
        QTimer.singleShot(100, lambda: self.setWindowOpacity(orig))

    def exit_app(self):
        self.close()
        QApplication.instance().quit()

    def _on_tray_activated(self, reason):
        print(f"[调试] 托盘激活事件: reason={reason}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = KnightIdleWidget()
    win.show()
    sys.exit(app.exec())
