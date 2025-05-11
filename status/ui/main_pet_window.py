"""
---------------------------------------------------------------
File name:                  main_pet_window.py
Author:                     Ignorant-lu
Date created:               2025/04/16
Description:                桌宠主窗口 UI 实现
----------------------------------------------------------------

Changed history:            
                            2025/04/16: 基于 simple_knight_idle_demo.py 创建;
----
"""
import sys
import os
import logging
from PyQt6.QtWidgets import QApplication, QLabel, QWidget
from PyQt6.QtCore import Qt, QTimer, QPoint
from PyQt6.QtGui import QPixmap, QPainter, QGuiApplication, QImage

logger = logging.getLogger("HollowMing.UI.MainPetWindow")

# 默认窗口大小，可以从配置读取
DEFAULT_WIDTH = 150 
DEFAULT_HEIGHT = 150

class MainPetWindow(QWidget):
    """桌宠主窗口类，实现无边框、透明、可拖动等特性。"""
    def __init__(self, initial_position: QPoint = QPoint(200, 200)):
        super().__init__()
        
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool # Tool 类型窗口通常不在任务栏显示
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        # self.setFixedSize(DEFAULT_WIDTH, DEFAULT_HEIGHT) # 尺寸由内容决定或外部设置
        self.setMinimumSize(50, 50) # 设置一个最小尺寸
        
        # 用于显示的 QPixmap
        self._pixmap = None 
        
        # 拖动相关
        self.dragging = False
        self.drag_pos = QPoint()
        
        # 初始位置
        self.move(initial_position)
        
        logger.info("MainPetWindow initialized.")

    def set_pixmap(self, pixmap: QPixmap):
        """设置要显示的 QPixmap，并根据图像调整窗口大小。"""
        if pixmap and not pixmap.isNull():
            self._pixmap = pixmap
            self.setFixedSize(self._pixmap.size()) # 根据Pixmap调整窗口大小
            self.update() # 请求重绘
        else:
            logger.warning("Attempted to set an invalid or null pixmap.")
            self._pixmap = None
            self.setFixedSize(DEFAULT_WIDTH, DEFAULT_HEIGHT) # 无图像时恢复默认大小
            self.update()
            
    def set_image(self, image: QImage):
        """设置要显示的 QImage。"""
        if image and not image.isNull():
           self.set_pixmap(QPixmap.fromImage(image))
        else:
            self.set_pixmap(None)

    def paintEvent(self, event):
        """绘制事件，将缓存的 Pixmap 绘制到窗口上。"""
        if self._pixmap:
            painter = QPainter(self)
            painter.drawPixmap(0, 0, self._pixmap)
            painter.end()
        # else: # 如果没有pixmap，则绘制透明背景（默认行为）
        #     super().paintEvent(event) 

    def mousePressEvent(self, event):
        """处理鼠标按下事件，用于窗口拖动。"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.dragging = True
            # 计算鼠标点击位置相对于窗口左上角的偏移
            self.drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        """处理鼠标移动事件，用于窗口拖动，并限制在屏幕内。"""
        if self.dragging and event.buttons() & Qt.MouseButton.LeftButton:
            new_pos = event.globalPosition().toPoint() - self.drag_pos
            
            # 获取可用屏幕区域 (排除任务栏等)
            screen = QGuiApplication.primaryScreen().availableGeometry()
            
            # 限制窗口在屏幕边界内
            x = max(screen.left(), min(new_pos.x(), screen.right() - self.width()))
            y = max(screen.top(), min(new_pos.y(), screen.bottom() - self.height()))
            
            self.move(x, y)
            event.accept()

    def mouseReleaseEvent(self, event):
        """处理鼠标释放事件，结束窗口拖动。"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.dragging = False
            event.accept()

    def mouseDoubleClickEvent(self, event):
        """处理鼠标双击事件（示例：关闭）。"""
        if event.button() == Qt.MouseButton.LeftButton:
            logger.info("Window double-clicked. Closing application.")
            QApplication.quit() # 示例：双击关闭
            event.accept()

# --- 简单的测试入口 --- (如果直接运行此文件)
if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    app = QApplication(sys.argv)
    
    # 创建一个测试用的 QPixmap
    test_pixmap = QPixmap(100, 150)
    test_pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(test_pixmap)
    painter.setBrush(Qt.GlobalColor.cyan)
    painter.drawEllipse(0, 0, 100, 150)
    painter.end()
    
    window = MainPetWindow()
    window.set_pixmap(test_pixmap)
    window.show()
    
    sys.exit(app.exec()) 