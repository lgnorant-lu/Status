"""
---------------------------------------------------------------
File name:                  main_pet_window.py
Author:                     Ignorant-lu
Date created:               2025/04/16
Description:                桌宠主窗口，负责显示桌宠动画并处理窗口相关事件
----------------------------------------------------------------

Changed history:            
                            2025/04/16: 初始创建;
                            2025/04/17: 从PyQt6迁移到PySide6;
----
"""

import logging
import sys
from typing import Optional, Tuple

from PySide6.QtWidgets import QMainWindow, QWidget, QApplication, QVBoxLayout, QLabel
from PySide6.QtGui import (
    QPixmap, QPainter, QMouseEvent, QImage, QPaintEvent, QCursor,
    QResizeEvent, QMoveEvent, Qt
)
from PySide6.QtCore import QPoint, QSize, QRect, QTimer, Signal, Slot, QObject

logger = logging.getLogger(__name__)

class MainPetWindow(QMainWindow):
    """桌宠主窗口，负责显示桌宠动画并处理窗口相关行为"""
    
    # 信号
    clicked = Signal(QPoint)         # 点击信号，参数为点击位置
    double_clicked = Signal(QPoint)  # 双击信号，参数为点击位置
    dragged = Signal(QPoint)         # 拖拽信号，参数为拖拽位置
    dropped = Signal(QPoint)         # 放下信号，参数为放下位置
    size_changed = Signal(QSize)     # 大小改变信号，参数为新大小
    position_changed = Signal(QPoint)  # 位置改变信号，参数为新位置
    
    def __init__(self, parent=None):
        """初始化主窗口"""
        super().__init__(parent)
        
        self.setWindowTitle("Status Pet")
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |      # 无边框
            Qt.WindowType.Tool |                    # 工具窗口（不在任务栏显示）
            Qt.WindowType.WindowStaysOnTopHint     # 保持在最前
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)  # 透明背景
        
        # 创建一个中央部件来显示图像
        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)
        
        # 布局
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)  # 无边距
        
        # 图像标签
        self.image_label = QLabel(self.central_widget)
        self.image_label.setScaledContents(True)  # 图像自动缩放
        self.main_layout.addWidget(self.image_label)
        
        # 初始化变量
        self.image = None  # 当前显示的图像
        self.is_dragging = False  # 是否正在拖拽
        self.drag_start_pos = QPoint()  # 拖拽开始位置
        self.window_start_pos = QPoint()  # 窗口开始位置
        
        logger.debug("MainPetWindow初始化完成")
    
    def set_image(self, image) -> None:
        """设置要显示的图像
        
        Args:
            image: QImage、QPixmap或文件路径
        """
        pixmap = None
        
        # 转换各种类型到QPixmap
        if isinstance(image, QPixmap):
            pixmap = image
        elif isinstance(image, QImage):
            pixmap = QPixmap.fromImage(image)
        elif isinstance(image, str):
            # 尝试从文件加载
            pixmap = QPixmap(image)
            if pixmap.isNull():
                logger.error(f"无法加载图像: {image}")
                return
        else:
            logger.error(f"不支持的图像类型: {type(image)}")
            return
        
        # 更新图像
        self.image = pixmap
        self.image_label.setPixmap(pixmap)
        
        # 调整窗口大小以适应图像
        self.resize_to_image()
        
        # 更新
        self.update()
    
    def resize_to_image(self) -> None:
        """调整窗口大小以适应当前图像"""
        if self.image and not self.image.isNull():
            # 设置窗口大小为图像大小
            self.resize(self.image.size())
            logger.debug(f"窗口大小已调整为: {self.image.size()}")
    
    def mousePressEvent(self, event: QMouseEvent) -> None:
        """鼠标按下事件处理
        
        Args:
            event: 鼠标事件
        """
        if event.button() == Qt.MouseButton.LeftButton:
            # 记录拖拽开始位置
            self.is_dragging = True
            self.drag_start_pos = event.position().toPoint()
            self.window_start_pos = self.pos()
            
            # 发送点击信号
            self.clicked.emit(event.position().toPoint())
            
            # 设置鼠标形状为抓取
            self.setCursor(QCursor(Qt.CursorShape.ClosedHandCursor))
        
        super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        """鼠标移动事件处理
        
        Args:
            event: 鼠标事件
        """
        if self.is_dragging:
            # 计算拖拽位置
            delta = event.position().toPoint() - self.drag_start_pos
            new_pos = self.window_start_pos + delta
            
            # 移动窗口
            self.move(new_pos)
            
            # 发送拖拽信号
            self.dragged.emit(new_pos)
        
        super().mouseMoveEvent(event)
    
    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        """鼠标释放事件处理
        
        Args:
            event: 鼠标事件
        """
        if event.button() == Qt.MouseButton.LeftButton and self.is_dragging:
            self.is_dragging = False
            
            # 重置鼠标形状
            self.setCursor(QCursor(Qt.CursorShape.ArrowCursor))
            
            # 发送放下信号
            self.dropped.emit(event.position().toPoint())
        
        super().mouseReleaseEvent(event)
    
    def mouseDoubleClickEvent(self, event: QMouseEvent) -> None:
        """鼠标双击事件处理
        
        Args:
            event: 鼠标事件
        """
        if event.button() == Qt.MouseButton.LeftButton:
            # 发送双击信号
            self.double_clicked.emit(event.position().toPoint())
        
        super().mouseDoubleClickEvent(event)
    
    def resizeEvent(self, event: QResizeEvent) -> None:
        """窗口大小改变事件处理
        
        Args:
            event: 大小改变事件
        """
        # 发送大小改变信号
        self.size_changed.emit(event.size())
        
        super().resizeEvent(event)
    
    def moveEvent(self, event: QMoveEvent) -> None:
        """窗口位置改变事件处理
        
        Args:
            event: 移动事件
        """
        # 发送位置改变信号
        self.position_changed.emit(event.pos())
        
        super().moveEvent(event)

# 如果直接运行这个文件，则创建一个测试窗口
if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    window = MainPetWindow()
    
    # 测试用图像（实际上这里可能会因为没有真实路径而报错，但为了演示保留）
    test_image_path = "assets/images/characters/default/idle/idle_000.png"
    window.set_image(test_image_path)
    
    window.show()
    
    sys.exit(app.exec()) 