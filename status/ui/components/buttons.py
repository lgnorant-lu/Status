"""
---------------------------------------------------------------
File name:                  buttons.py
Author:                     Ignorant-lu
Date created:               2025/04/05
Description:                UI按钮组件
----------------------------------------------------------------

Changed history:            
                            2025/04/05: 初始创建;
----
"""

import logging
from typing import Optional, Callable, Union, List, Tuple, Dict, Any

# MODIFIED: Direct imports from PySide6
from PySide6.QtCore import Qt, QSize, Signal, QPropertyAnimation, QEasingCurve, Property
from PySide6.QtGui import QIcon, QColor, QPalette, QMouseEvent, QPainter, QPen, QPaintEvent, QResizeEvent
from PySide6.QtWidgets import QPushButton, QWidget, QGraphicsOpacityEffect, QSizePolicy, QGraphicsDropShadowEffect, QGraphicsEffect

logger = logging.getLogger(__name__)

# 按钮样式定义
BUTTON_STYLE = """
/* 主按钮样式 */
QPushButton.primary {
    background-color: #1A6E8E;
    color: #E6E6E6;
    border: none;
    border-radius: 4px;
    padding: 8px 16px;
    font-weight: 500;
}

QPushButton.primary:hover {
    background-color: #2580A0;
}

QPushButton.primary:pressed {
    background-color: #155970;
}

QPushButton.primary:disabled {
    background-color: #1A6E8E;
    opacity: 0.4;
}

/* 次按钮样式 */
QPushButton.secondary {
    background-color: transparent;
    color: #1A6E8E;
    border: 1px solid #1A6E8E;
    border-radius: 4px;
    padding: 8px 16px;
    font-weight: 500;
}

QPushButton.secondary:hover {
    background-color: rgba(26, 110, 142, 0.1);
}

QPushButton.secondary:pressed {
    background-color: rgba(26, 110, 142, 0.2);
}

QPushButton.secondary:disabled {
    color: #1A6E8E;
    border-color: #1A6E8E;
    opacity: 0.4;
}

/* 文本按钮样式 */
QPushButton.text {
    background-color: transparent;
    color: #1A6E8E;
    border: none;
    padding: 8px 16px;
    font-weight: 500;
}

QPushButton.text:hover {
    text-decoration: underline;
}

QPushButton.text:pressed {
    color: #155970;
}

QPushButton.text:disabled {
    color: #1A6E8E;
    opacity: 0.4;
}

/* 图标按钮样式 */
QPushButton.icon {
    background-color: transparent;
    border: none;
    padding: 8px;
}

QPushButton.icon:hover {
    background-color: rgba(255, 255, 255, 0.1);
    border-radius: 4px;
}

QPushButton.icon:pressed {
    background-color: rgba(255, 255, 255, 0.15);
}

QPushButton.icon:disabled {
    opacity: 0.4;
}
"""

class BaseButton(QPushButton):
    """基础按钮类，为所有按钮类型提供共享功能"""
    
    def __init__(self, 
                 text: str = "", 
                 parent: Optional[QWidget] = None,
                 on_click: Optional[Callable] = None):
        """
        初始化按钮
        
        Args:
            text: 按钮文本
            parent: 父组件
            on_click: 点击事件回调函数
        """
        super().__init__(text, parent)
        
        # 设置尺寸策略
        self.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
        
        # 连接回调函数
        if on_click:
            self.clicked.connect(on_click)
            
        # 设置动画效果
        self._setup_animations()
        
    def _setup_animations(self):
        """设置按钮动画效果"""
        # 缩放动画设置
        self._scale_factor = 1.0
        
    def enterEvent(self, event):
        """鼠标进入事件"""
        super().enterEvent(event)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        
    def leaveEvent(self, event):
        """鼠标离开事件"""
        super().leaveEvent(event)
        self.setCursor(Qt.CursorShape.ArrowCursor)
        
    def mousePressEvent(self, event: QMouseEvent):
        """鼠标按下事件，添加按下效果"""
        if event.button() == Qt.MouseButton.LeftButton:
            self._scale_factor = 0.95
            self.update()
        super().mousePressEvent(event)
        
    def mouseReleaseEvent(self, event: QMouseEvent):
        """鼠标释放事件，恢复效果"""
        if event.button() == Qt.MouseButton.LeftButton:
            self._scale_factor = 1.0
            self.update()
        super().mouseReleaseEvent(event)
        
    def setEnabled(self, enabled: bool):
        """设置按钮启用状态"""
        super().setEnabled(enabled)
        # 更新透明度以反映禁用状态
        
        # 先清除当前效果（如果有）
        current_effect = self.graphicsEffect()
        if current_effect is not None:
            current_effect.setParent(None)  # 断开父对象连接
        
        # 仅在禁用时设置新效果
        if not enabled:
            opacity = 0.4
            effect = QGraphicsOpacityEffect(self)
            effect.setOpacity(opacity)
            super().setGraphicsEffect(effect)

    def set_shadow(self, blur_radius: int = 10, x_offset: int = 0, y_offset: int = 5, color: str = "#000000") -> None:
        """设置阴影效果"""
        # 先清除当前效果（如果有）
        current_effect = self.graphicsEffect()
        if current_effect is not None:
            current_effect.setParent(None)  # 断开父对象连接
            
        # 创建并设置新效果
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(blur_radius)
        shadow.setOffset(x_offset, y_offset)
        shadow.setColor(QColor(color))
        super().setGraphicsEffect(shadow)

    def clear_shadow(self) -> None:
        """清除阴影效果"""
        current_effect = self.graphicsEffect()
        if current_effect is not None:
            current_effect.setParent(None)  # 断开父对象连接而不是传递None

class PrimaryButton(BaseButton):
    """主要按钮，用于强调主要操作"""
    
    def __init__(self, 
                 text: str = "", 
                 parent: Optional[QWidget] = None,
                 on_click: Optional[Callable] = None):
        """
        初始化主要按钮
        
        Args:
            text: 按钮文本
            parent: 父组件
            on_click: 点击事件回调函数
        """
        super().__init__(text, parent, on_click)
        self.setProperty("class", "primary")
        self.setStyleSheet(BUTTON_STYLE)
        
class SecondaryButton(BaseButton):
    """次要按钮，用于次要操作"""
    
    def __init__(self, 
                 text: str = "", 
                 parent: Optional[QWidget] = None,
                 on_click: Optional[Callable] = None):
        """
        初始化次要按钮
        
        Args:
            text: 按钮文本
            parent: 父组件
            on_click: 点击事件回调函数
        """
        super().__init__(text, parent, on_click)
        self.setProperty("class", "secondary")
        self.setStyleSheet(BUTTON_STYLE)

class TextButton(BaseButton):
    """文本按钮，用于不太强调的操作"""
    
    def __init__(self, 
                 text: str = "", 
                 parent: Optional[QWidget] = None,
                 on_click: Optional[Callable] = None):
        """
        初始化文本按钮
        
        Args:
            text: 按钮文本
            parent: 父组件
            on_click: 点击事件回调函数
        """
        super().__init__(text, parent, on_click)
        self.setProperty("class", "text")
        self.setStyleSheet(BUTTON_STYLE)

class IconButton(BaseButton):
    """图标按钮，只显示图标，通常用于工具栏或紧凑界面"""
    
    def __init__(self, 
                 icon: Union[QIcon, str], 
                 parent: Optional[QWidget] = None,
                 on_click: Optional[Callable] = None,
                 size: int = 32,
                 tooltip: str = ""):
        """
        初始化图标按钮
        
        Args:
            icon: 按钮图标或图标路径
            parent: 父组件
            on_click: 点击事件回调函数
            size: 按钮大小
            tooltip: 鼠标悬停提示
        """
        super().__init__("", parent, on_click)
        
        # 设置图标
        if isinstance(icon, str):
            self.setIcon(QIcon(icon))
        else:
            self.setIcon(icon)
            
        # 设置大小
        self.setFixedSize(size, size)
        icon_size = int(size * 0.6)  # 图标大小为按钮大小的60%
        self.setIconSize(QSize(icon_size, icon_size))
        
        # 设置工具提示
        if tooltip:
            self.setToolTip(tooltip)
            
        # 设置样式
        self.setProperty("class", "icon")
        self.setStyleSheet(BUTTON_STYLE)
        
        # 图标按钮不显示文本
        self.setText("") 