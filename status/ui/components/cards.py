"""
---------------------------------------------------------------
File name:                  cards.py
Author:                     Ignorant-lu
Date created:               2025/04/05
Description:                UI卡片组件
----------------------------------------------------------------

Changed history:            
                            2025/04/05: 初始创建;
----
"""

import logging
from typing import Optional, List, Callable, Union

try:
    from PyQt6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QRect
    from PyQt6.QtGui import QColor, QPainter, QPen, QBrush, QPaintEvent, QResizeEvent
    from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                                QPushButton, QFrame, QSizePolicy, QLayout,
                                QScrollArea, QGraphicsDropShadowEffect)
    HAS_PYQT = True
except ImportError:
    HAS_PYQT = False
    # 创建占位类以避免导入错误
    class QWidget:
        pass
    class QFrame:
        pass
    class QLayout:
        pass

logger = logging.getLogger(__name__)

# 卡片样式定义
CARD_STYLE = """
/* 卡片容器样式 */
QFrame.card {
    background-color: #252525;
    border-radius: 6px;
    border: 1px solid #323232;
}

QFrame.card.hoverable:hover {
    border: 1px solid #404040;
}

/* 卡片头部样式 */
QFrame.card-header {
    background-color: #252525;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    border-bottom: 1px solid #323232;
    padding: 12px 16px;
}

/* 卡片内容样式 */
QFrame.card-content {
    background-color: transparent;
    padding: 16px;
}

/* 卡片标题样式 */
QLabel.card-title {
    font-size: 16px;
    font-weight: bold;
    color: #E6E6E6;
}

/* 卡片副标题样式 */
QLabel.card-subtitle {
    font-size: 14px;
    color: #AAAAAA;
}
"""

class Card(QFrame):
    """卡片容器组件"""
    
    def __init__(self, 
                 parent: Optional[QWidget] = None,
                 title: str = "",
                 subtitle: str = "",
                 width: int = 0,
                 height: int = 0,
                 shadow: bool = True,
                 hoverable: bool = False,
                 padding: int = 16):
        """
        初始化卡片容器
        
        Args:
            parent: 父组件
            title: 卡片标题（如果提供）
            subtitle: 卡片副标题（如果提供）
            width: 卡片宽度（0表示自适应）
            height: 卡片高度（0表示自适应）
            shadow: 是否显示阴影
            hoverable: 是否启用悬停效果
            padding: 内边距
        """
        if not HAS_PYQT:
            logger.error("PyQt6未安装，无法创建UI组件")
            return
            
        super().__init__(parent)
        
        # 设置基本属性
        self.setObjectName("card")
        self.setProperty("class", "card")
        if hoverable:
            self.setProperty("class", "card hoverable")
        self.setStyleSheet(CARD_STYLE)
        
        # 设置阴影效果
        if shadow:
            self._setup_shadow()
            
        # 设置尺寸
        if width > 0:
            self.setMinimumWidth(width)
            if height > 0:
                self.setFixedSize(width, height)
        if height > 0:
            self.setMinimumHeight(height)
            
        # 创建主布局
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)
        
        # 创建标题（如果提供）
        if title or subtitle:
            self._header = CardHeader(title, subtitle, self)
            self._layout.addWidget(self._header)
            
        # 创建内容区域
        self._content = CardContent(padding, self)
        self._layout.addWidget(self._content)
        
    def _setup_shadow(self):
        """设置阴影效果"""
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(0, 0, 0, 80))
        shadow.setOffset(0, 3)
        self.setGraphicsEffect(shadow)
        
    def setTitle(self, title: str):
        """设置卡片标题"""
        if hasattr(self, '_header'):
            self._header.setTitle(title)
        else:
            self._header = CardHeader(title, "", self)
            self._layout.insertWidget(0, self._header)
            
    def setSubtitle(self, subtitle: str):
        """设置卡片副标题"""
        if hasattr(self, '_header'):
            self._header.setSubtitle(subtitle)
        else:
            self._header = CardHeader("", subtitle, self)
            self._layout.insertWidget(0, self._header)
            
    def contentLayout(self) -> QLayout:
        """获取内容区域布局以添加子组件"""
        return self._content.layout()
        
    def addWidget(self, widget: QWidget):
        """添加组件到内容区域"""
        self._content.layout().addWidget(widget)
        
    def addLayout(self, layout: QLayout):
        """添加布局到内容区域"""
        self._content.layout().addLayout(layout)
        
    def addStretch(self, stretch: int = 0):
        """添加弹性空间"""
        self._content.layout().addStretch(stretch)
        
    def clear(self):
        """清空内容区域"""
        layout = self._content.layout()
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

class CardHeader(QFrame):
    """卡片头部组件"""
    
    def __init__(self,
                 title: str = "",
                 subtitle: str = "",
                 parent: Optional[QWidget] = None,
                 action_button: Optional[QPushButton] = None):
        """
        初始化卡片头部
        
        Args:
            title: 标题文本
            subtitle: 副标题文本
            parent: 父组件
            action_button: 操作按钮（如果需要）
        """
        if not HAS_PYQT:
            logger.error("PyQt6未安装，无法创建UI组件")
            return
            
        super().__init__(parent)
        
        # 设置基本属性
        self.setObjectName("cardHeader")
        self.setProperty("class", "card-header")
        self.setStyleSheet(CARD_STYLE)
        
        # 创建布局
        self._layout = QHBoxLayout(self)
        self._layout.setContentsMargins(16, 12, 16, 12)
        
        # 创建标题部分
        self._title_layout = QVBoxLayout()
        self._layout.addLayout(self._title_layout)
        
        # 创建标题标签
        if title:
            self._title_label = QLabel(title, self)
            self._title_label.setProperty("class", "card-title")
            self._title_layout.addWidget(self._title_label)
        else:
            self._title_label = None
            
        # 创建副标题标签
        if subtitle:
            self._subtitle_label = QLabel(subtitle, self)
            self._subtitle_label.setProperty("class", "card-subtitle")
            self._title_layout.addWidget(self._subtitle_label)
        else:
            self._subtitle_label = None
            
        # 添加弹性空间
        self._layout.addStretch(1)
        
        # 添加操作按钮（如果提供）
        if action_button:
            self._layout.addWidget(action_button)
            
    def setTitle(self, title: str):
        """设置标题文本"""
        if self._title_label:
            self._title_label.setText(title)
        else:
            self._title_label = QLabel(title, self)
            self._title_label.setProperty("class", "card-title")
            self._title_layout.insertWidget(0, self._title_label)
            
    def setSubtitle(self, subtitle: str):
        """设置副标题文本"""
        if self._subtitle_label:
            self._subtitle_label.setText(subtitle)
        else:
            self._subtitle_label = QLabel(subtitle, self)
            self._subtitle_label.setProperty("class", "card-subtitle")
            self._title_layout.addWidget(self._subtitle_label)
            
    def addAction(self, button: QPushButton):
        """添加操作按钮"""
        self._layout.addWidget(button)

class CardContent(QFrame):
    """卡片内容区域组件"""
    
    def __init__(self,
                 padding: int = 16,
                 parent: Optional[QWidget] = None,
                 scrollable: bool = False):
        """
        初始化卡片内容区域
        
        Args:
            padding: 内边距
            parent: 父组件
            scrollable: 是否可滚动
        """
        if not HAS_PYQT:
            logger.error("PyQt6未安装，无法创建UI组件")
            return
            
        super().__init__(parent)
        
        # 设置基本属性
        self.setObjectName("cardContent")
        self.setProperty("class", "card-content")
        self.setStyleSheet(CARD_STYLE)
        
        # 如果需要滚动，创建滚动区域
        if scrollable:
            # 创建滚动区域
            self._scroll_area = QScrollArea(self)
            self._scroll_area.setWidgetResizable(True)
            self._scroll_area.setFrameShape(QFrame.Shape.NoFrame)
            
            # 创建内容容器
            self._content_widget = QWidget(self._scroll_area)
            self._layout = QVBoxLayout(self._content_widget)
            self._layout.setContentsMargins(padding, padding, padding, padding)
            self._layout.setSpacing(8)
            
            # 设置滚动区域内容
            self._scroll_area.setWidget(self._content_widget)
            
            # 设置卡片内容布局
            main_layout = QVBoxLayout(self)
            main_layout.setContentsMargins(0, 0, 0, 0)
            main_layout.addWidget(self._scroll_area)
        else:
            # 创建常规布局
            self._layout = QVBoxLayout(self)
            self._layout.setContentsMargins(padding, padding, padding, padding)
            self._layout.setSpacing(8)
            
    def layout(self) -> QLayout:
        """获取内容布局以添加子组件"""
        return self._layout

class CardFooter(QFrame):
    """卡片底部组件"""
    
    def __init__(self,
                 parent: Optional[QWidget] = None,
                 buttons: Optional[List[QPushButton]] = None,
                 alignment: Qt.AlignmentFlag = Qt.AlignmentFlag.AlignRight):
        """
        初始化卡片底部
        
        Args:
            parent: 父组件
            buttons: 底部按钮列表
            alignment: 按钮对齐方式
        """
        if not HAS_PYQT:
            logger.error("PyQt6未安装，无法创建UI组件")
            return
            
        super().__init__(parent)
        
        # 设置基本属性
        self.setObjectName("cardFooter")
        self.setProperty("class", "card-footer")
        
        # 添加自定义样式
        style = """
        QFrame.card-footer {
            background-color: #1F1F1F;
            border-bottom-left-radius: 6px;
            border-bottom-right-radius: 6px;
            border-top: 1px solid #323232;
            padding: 12px 16px;
        }
        
        QPushButton.footer-button {
            min-width: 80px;
            padding: 8px 16px;
        }
        """
        self.setStyleSheet(CARD_STYLE + style)
        
        # 创建布局
        self._layout = QHBoxLayout(self)
        self._layout.setContentsMargins(16, 12, 16, 12)
        self._layout.setSpacing(8)
        
        # 根据对齐方式添加弹性空间
        if alignment == Qt.AlignmentFlag.AlignRight:
            self._layout.addStretch(1)
        elif alignment == Qt.AlignmentFlag.AlignCenter:
            self._layout.addStretch(1)
            
        # 添加按钮（如果提供）
        if buttons:
            for button in buttons:
                button.setProperty("class", "footer-button")
                self._layout.addWidget(button)
                
        # 如果居中对齐，添加尾部弹性空间
        if alignment == Qt.AlignmentFlag.AlignCenter:
            self._layout.addStretch(1)
            
    def addButton(self, button: QPushButton):
        """添加按钮"""
        button.setProperty("class", "footer-button")
        self._layout.addWidget(button)
        
    def clearButtons(self):
        """清空所有按钮"""
        for i in range(self._layout.count()):
            item = self._layout.itemAt(i)
            if item and item.widget():
                item.widget().deleteLater()
        # 重新添加弹性空间
        self._layout.addStretch(1)

class ExpandableCard(Card):
    """可展开卡片组件"""
    
    def __init__(self, 
                 parent: Optional[QWidget] = None,
                 title: str = "",
                 subtitle: str = "",
                 expanded: bool = False,
                 width: int = 0,
                 height: int = 0,
                 shadow: bool = True,
                 padding: int = 16):
        """
        初始化可展开卡片
        
        Args:
            parent: 父组件
            title: 卡片标题
            subtitle: 卡片副标题
            expanded: 初始是否展开
            width: 卡片宽度（0表示自适应）
            height: 卡片高度（0表示自适应）
            shadow: 是否显示阴影
            padding: 内边距
        """
        super().__init__(parent, title, subtitle, width, height, shadow, False, padding)
        
        # 添加展开/折叠按钮
        self._expand_button = QPushButton("▼" if expanded else "▶", self)
        self._expand_button.setFixedSize(24, 24)
        self._expand_button.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                color: #AAAAAA;
            }
            QPushButton:hover {
                color: #E6E6E6;
            }
        """)
        self._expand_button.clicked.connect(self._toggle_expand)
        
        # 将按钮添加到头部
        if hasattr(self, '_header'):
            self._header.addAction(self._expand_button)
            
        # 设置内容区域初始可见性
        self._content.setVisible(expanded)
        self._expanded = expanded
        
    def _toggle_expand(self):
        """切换展开/折叠状态"""
        self._expanded = not self._expanded
        self._expand_button.setText("▼" if self._expanded else "▶")
        self._content.setVisible(self._expanded)
        
    def setExpanded(self, expanded: bool):
        """设置展开状态"""
        if expanded != self._expanded:
            self._toggle_expand()
            
    def isExpanded(self) -> bool:
        """获取当前展开状态"""
        return self._expanded 