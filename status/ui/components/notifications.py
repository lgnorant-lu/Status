"""
---------------------------------------------------------------
File name:                  notifications.py
Author:                     Ignorant-lu
Date created:               2025/04/05
Description:                UI通知组件
----------------------------------------------------------------

Changed history:            
                            2025/04/05: 初始创建;
----
"""

import logging
import uuid
from typing import Optional, Dict, List, Callable
from enum import Enum

try:
    from PyQt6.QtCore import (Qt, QTimer, QPropertyAnimation, QEasingCurve, 
                             QPoint, QSize, QRect, pyqtSignal)
    from PyQt6.QtGui import QColor, QPainter, QPaintEvent, QPen, QIcon, QFont
    from PyQt6.QtWidgets import (QWidget, QLabel, QPushButton, QHBoxLayout, 
                                QVBoxLayout, QFrame, QApplication, QGraphicsOpacityEffect)
    HAS_PYQT = True
except ImportError:
    HAS_PYQT = False
    # 创建占位类以避免导入错误
    class QWidget:
        pass
    class QFrame:
        pass
    class Enum:
        pass
    class pyqtSignal:
        pass

logger = logging.getLogger(__name__)

class NotificationType(Enum):
    """通知类型枚举"""
    INFO = "info"          # 信息通知（蓝色）
    SUCCESS = "success"    # 成功通知（绿色）
    WARNING = "warning"    # 警告通知（黄色）
    ERROR = "error"        # 错误通知（红色）

# 通知样式定义
NOTIFICATION_STYLE = """
/* 通知容器样式 */
QFrame.notification {
    border-radius: 6px;
    padding: 12px;
}

/* 信息通知样式 */
QFrame.notification.info {
    background-color: #1A3E4E;
    border-left: 4px solid #1A6E8E;
}

/* 成功通知样式 */
QFrame.notification.success {
    background-color: #1C3B28;
    border-left: 4px solid #2D8C46;
}

/* 警告通知样式 */
QFrame.notification.warning {
    background-color: #4E3A1A;
    border-left: 4px solid #D89C00;
}

/* 错误通知样式 */
QFrame.notification.error {
    background-color: #4E1A1A;
    border-left: 4px solid #9E2B25;
}

/* 通知标题样式 */
QLabel.notification-title {
    font-size: 14px;
    font-weight: bold;
    color: #E6E6E6;
}

/* 通知消息样式 */
QLabel.notification-message {
    font-size: 13px;
    color: #CCCCCC;
}

/* 通知关闭按钮样式 */
QPushButton.notification-close {
    background-color: transparent;
    border: none;
    color: #AAAAAA;
    font-size: 16px;
}

QPushButton.notification-close:hover {
    color: #E6E6E6;
}
"""

class Notification(QFrame):
    """通知组件"""
    
    closed = pyqtSignal(str)  # 通知关闭信号，传递通知ID
    
    def __init__(self, 
                 parent: Optional[QWidget] = None,
                 title: str = "",
                 message: str = "",
                 notification_type: NotificationType = NotificationType.INFO,
                 duration: int = 5000,  # 持续时间（毫秒），0表示不自动关闭
                 closable: bool = True,
                 width: int = 300):
        """
        初始化通知组件
        
        Args:
            parent: 父组件
            title: 通知标题
            message: 通知消息
            notification_type: 通知类型
            duration: 持续时间（毫秒），0表示不自动关闭
            closable: 是否可关闭
            width: 通知宽度
        """
        if not HAS_PYQT:
            logger.error("PyQt6未安装，无法创建UI组件")
            return
            
        super().__init__(parent)
        
        # 生成唯一ID
        self._id = str(uuid.uuid4())
        
        # 设置基本属性
        self.setObjectName(f"notification_{self._id}")
        self.setProperty("class", f"notification {notification_type.value}")
        self.setStyleSheet(NOTIFICATION_STYLE)
        self.setFixedWidth(width)
        
        # 创建主布局
        self._layout = QHBoxLayout(self)
        self._layout.setContentsMargins(12, 12, 12, 12)
        self._layout.setSpacing(12)
        
        # 创建内容布局
        self._content_layout = QVBoxLayout()
        self._content_layout.setSpacing(4)
        
        # 添加标题（如果提供）
        if title:
            self._title_label = QLabel(title, self)
            self._title_label.setProperty("class", "notification-title")
            self._content_layout.addWidget(self._title_label)
            
        # 添加消息
        self._message_label = QLabel(message, self)
        self._message_label.setProperty("class", "notification-message")
        self._message_label.setWordWrap(True)
        self._content_layout.addWidget(self._message_label)
        
        self._layout.addLayout(self._content_layout)
        
        # 添加关闭按钮（如果可关闭）
        if closable:
            self._close_button = QPushButton("×", self)
            self._close_button.setProperty("class", "notification-close")
            self._close_button.setCursor(Qt.CursorShape.PointingHandCursor)
            self._close_button.setFixedSize(16, 16)
            self._close_button.clicked.connect(self.close)
            self._layout.addWidget(self._close_button, 0, Qt.AlignmentFlag.AlignTop)
        
        # 设置定时器（如果需要自动关闭）
        if duration > 0:
            QTimer.singleShot(duration, self.close)
            
        # 初始透明度效果
        self._opacity_effect = QGraphicsOpacityEffect(self)
        self._opacity_effect.setOpacity(0.0)
        self.setGraphicsEffect(self._opacity_effect)
        
        # 创建显示动画
        self._show_animation = QPropertyAnimation(self._opacity_effect, b"opacity")
        self._show_animation.setDuration(250)
        self._show_animation.setStartValue(0.0)
        self._show_animation.setEndValue(1.0)
        self._show_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        
        # 创建隐藏动画
        self._hide_animation = QPropertyAnimation(self._opacity_effect, b"opacity")
        self._hide_animation.setDuration(250)
        self._hide_animation.setStartValue(1.0)
        self._hide_animation.setEndValue(0.0)
        self._hide_animation.setEasingCurve(QEasingCurve.Type.InCubic)
        self._hide_animation.finished.connect(self._on_hide_finished)
        
        # 立即开始显示动画
        self._show_animation.start()
    
    def _on_hide_finished(self):
        """隐藏动画完成后处理"""
        # 发射关闭信号
        self.closed.emit(self._id)
        # 标记为删除
        self.deleteLater()
    
    def getId(self) -> str:
        """获取通知ID"""
        return self._id
    
    def close(self):
        """关闭通知"""
        self._hide_animation.start()
    
    def setTitle(self, title: str):
        """设置标题"""
        if hasattr(self, '_title_label'):
            self._title_label.setText(title)
        else:
            self._title_label = QLabel(title, self)
            self._title_label.setProperty("class", "notification-title")
            self._content_layout.insertWidget(0, self._title_label)
    
    def setMessage(self, message: str):
        """设置消息"""
        self._message_label.setText(message)
        
    def setType(self, notification_type: NotificationType):
        """设置通知类型"""
        self.setProperty("class", f"notification {notification_type.value}")
        self.style().unpolish(self)
        self.style().polish(self)

class NotificationManager(QWidget):
    """通知管理器，管理所有通知的显示"""
    
    _instance = None  # 单例实例
    
    @classmethod
    def instance(cls) -> 'NotificationManager':
        """获取单例实例"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def __init__(self, parent: Optional[QWidget] = None):
        """
        初始化通知管理器
        
        Args:
            parent: 父组件
        """
        if not HAS_PYQT:
            logger.error("PyQt6未安装，无法创建UI组件")
            return
            
        super().__init__(parent)
        
        # 检查是否已有实例
        if NotificationManager._instance is not None:
            logger.warning("NotificationManager是单例类，应使用instance()方法获取实例")
            return
            
        # 保存为单例实例
        NotificationManager._instance = self
        
        # 初始化通知容器和位置信息
        self._notifications: Dict[str, Notification] = {}
        self._next_position = 20  # 第一个通知的顶部位置（像素）
        self._spacing = 10  # 通知之间的间距（像素）
        
        # 设置基本属性
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | 
                          Qt.WindowType.Tool | 
                          Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        
        # 调整大小和位置
        self._update_geometry()
    
    def _update_geometry(self):
        """更新窗口几何形状"""
        # 获取主窗口或桌面大小
        desktop = QApplication.primaryScreen().availableGeometry()
        
        # 设置窗口大小和位置
        width = 320  # 通知宽度 + 边距
        height = desktop.height()
        x = desktop.width() - width - 20  # 右边缘 - 宽度 - 边距
        y = 40  # 顶部边距
        
        self.setGeometry(x, y, width, height)
    
    def show(self, notification_or_params):
        """
        显示通知
        
        Args:
            notification_or_params: 可以是Notification实例，或者是创建通知所需的参数字典
        
        Returns:
            str: 通知ID
        """
        if not HAS_PYQT:
            logger.error("PyQt6未安装，无法显示通知")
            return ""
            
        # 创建新通知或使用提供的通知
        if isinstance(notification_or_params, Notification):
            notification = notification_or_params
        else:
            # 从参数创建通知
            notification = Notification(
                parent=self,
                title=notification_or_params.get("title", ""),
                message=notification_or_params.get("message", ""),
                notification_type=notification_or_params.get("type", NotificationType.INFO),
                duration=notification_or_params.get("duration", 5000),
                closable=notification_or_params.get("closable", True),
                width=notification_or_params.get("width", 300)
            )
            
        # 连接关闭信号
        notification.closed.connect(self._on_notification_closed)
            
        # 添加到活动通知列表
        notification_id = notification.getId()
        self._notifications[notification_id] = notification
            
        # 显示通知
        self._add_notification(notification)
            
        return notification_id
    
    def _on_notification_closed(self, notification_id: str):
        """通知关闭处理"""
        # 移除通知
        if notification_id in self._notifications:
            notification = self._notifications.pop(notification_id)
            height = notification.height() + self._spacing
            
            # 更新所有后续通知的位置
            for other_notification in self._notifications.values():
                if other_notification.y() > notification.y():
                    other_notification.move(other_notification.x(), 
                                         other_notification.y() - height)
            
            # 更新下一个通知的位置
            self._next_position -= height
            
            # 如果没有更多通知，隐藏管理器
            if not self._notifications:
                self.hide()
    
    def closeNotification(self, notification_id: str):
        """关闭指定通知"""
        if notification_id in self._notifications:
            self._notifications[notification_id].close()
    
    def closeAllNotifications(self):
        """关闭所有通知"""
        # 复制通知ID列表，因为在迭代过程中字典会发生变化
        notification_ids = list(self._notifications.keys())
        for notification_id in notification_ids:
            self.closeNotification(notification_id)

# 便捷全局函数

def show_info(title: str, message: str, duration: int = 5000) -> str:
    """显示信息通知"""
    return NotificationManager.instance().showNotification(
        title, message, NotificationType.INFO, duration
    )

def show_success(title: str, message: str, duration: int = 5000) -> str:
    """显示成功通知"""
    return NotificationManager.instance().showNotification(
        title, message, NotificationType.SUCCESS, duration
    )

def show_warning(title: str, message: str, duration: int = 5000) -> str:
    """显示警告通知"""
    return NotificationManager.instance().showNotification(
        title, message, NotificationType.WARNING, duration
    )

def show_error(title: str, message: str, duration: int = 5000) -> str:
    """显示错误通知"""
    return NotificationManager.instance().showNotification(
        title, message, NotificationType.ERROR, duration
    ) 