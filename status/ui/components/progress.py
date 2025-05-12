"""
---------------------------------------------------------------
File name:                  progress.py
Author:                     Ignorant-lu
Date created:               2025/04/05
Description:                UI进度指示器组件
----------------------------------------------------------------

Changed history:            
                            2025/04/05: 初始创建;
----
"""

import logging
from typing import Optional, Callable, Union, Any, Dict, List
from enum import Enum

from PySide6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, QSize, QPoint
from PySide6.QtGui import QColor, QPainter, QPaintEvent, QPen, QBrush, QIcon
from PySide6.QtWidgets import (QWidget, QProgressBar, QVBoxLayout, QHBoxLayout, 
                               QLabel, QSizePolicy, QGraphicsOpacityEffect, QFrame)

logger = logging.getLogger(__name__)

# 进度指示器样式定义
PROGRESS_STYLE = """
/* 进度条样式 */
QProgressBar {
    background-color: #2A2A2A;
    border-radius: 4px;
    text-align: center;
    color: #E6E6E6;
    font-size: 12px;
}

QProgressBar::chunk {
    background-color: #1A6E8E;
    border-radius: 4px;
}

/* 进度条（成功）样式 */
QProgressBar.success::chunk {
    background-color: #2D8C46;
}

/* 进度条（警告）样式 */
QProgressBar.warning::chunk {
    background-color: #D89C00;
}

/* 进度条（错误）样式 */
QProgressBar.error::chunk {
    background-color: #9E2B25;
}
"""

class ProgressStatus(Enum):
    """进度状态枚举"""
    DEFAULT = "default"    # 默认蓝色
    SUCCESS = "success"    # 成功绿色
    WARNING = "warning"    # 警告黄色
    ERROR = "error"        # 错误红色

class ProgressType(Enum):
    """进度条类型枚举"""
    DETERMINATE = "determinate"      # 确定进度
    INDETERMINATE = "indeterminate"  # 不确定进度

class ProgressBar(QWidget):
    """进度条组件"""
    
    # 声明类属性，解决mypy错误
    _label: Optional[QLabel] = None
    _percentage_label: Optional[QLabel] = None
    _progress_bar: QProgressBar
    _header_layout: Optional[QHBoxLayout] = None
    _layout: QVBoxLayout
    _type: ProgressType
    
    def __init__(self, 
                 parent: Optional[QWidget] = None,
                 value: int = 0,
                 max_value: int = 100,
                 height: int = 6,
                 show_percentage: bool = True,
                 label: str = "",
                 status: ProgressStatus = ProgressStatus.DEFAULT,
                 progress_type: ProgressType = ProgressType.DETERMINATE):
        """
        初始化进度条
        
        Args:
            parent: 父组件
            value: 初始值
            max_value: 最大值
            height: 进度条高度
            show_percentage: 是否显示百分比
            label: 标签文本
            status: 进度条状态
            progress_type: 进度条类型
        """
        super().__init__(parent)
        
        # 保存类型属性
        self._type = progress_type
        self._animation = None
        
        # 创建布局
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(4)
        
        # 如果有标签，添加标签
        if label:
            self._header_layout = QHBoxLayout()
            self._label = QLabel(label, self)
            self._label.setStyleSheet("color: #E6E6E6; font-size: 14px;")
            self._header_layout.addWidget(self._label)
            
            # 如果显示百分比，添加百分比标签
            if show_percentage:
                self._percentage_label = QLabel(f"{value}%", self)
                self._percentage_label.setStyleSheet("color: #AAAAAA; font-size: 14px;")
                self._percentage_label.setAlignment(Qt.AlignmentFlag.AlignRight)
                self._header_layout.addWidget(self._percentage_label)
                
            self._layout.addLayout(self._header_layout)
        
        # 创建进度条
        self._progress_bar = QProgressBar(self)
        self._progress_bar.setRange(0, max_value)
        self._progress_bar.setValue(value)
        self._progress_bar.setFixedHeight(height)
        self._progress_bar.setTextVisible(False)  # 不显示内置文本
        self._progress_bar.setStyleSheet(PROGRESS_STYLE)
        
        # 设置状态
        self.setStatus(status)
        
        self._layout.addWidget(self._progress_bar)
        
        # 如果是不确定类型，设置初始动画
        if self._type == ProgressType.INDETERMINATE:
            self._setup_indeterminate_mode()
            
    def _setup_indeterminate_mode(self):
        """设置不确定模式的动画效果"""
        # 设置范围为0-100
        self._progress_bar.setRange(0, 0)  # 设置为0-0使Qt显示忙碌状态
        
        if self._percentage_label:
            self._percentage_label.setText("")  # 清空百分比标签
            
    def _setup_determinate_mode(self):
        """设置确定模式"""
        # 恢复正常范围
        self._progress_bar.setRange(0, 100)
        self._progress_bar.setValue(0)
        
        if self._percentage_label:
            self._percentage_label.setText("0%")
            
    def setType(self, progress_type: ProgressType):
        """设置进度条类型"""
        if self._type == progress_type:
            return
            
        self._type = progress_type
        
        if progress_type == ProgressType.INDETERMINATE:
            self._setup_indeterminate_mode()
        else:
            self._setup_determinate_mode()
        
    def setValue(self, value: int):
        """设置当前值"""
        self._progress_bar.setValue(value)
        if self._percentage_label:
            percentage = int((value / self._progress_bar.maximum()) * 100)
            self._percentage_label.setText(f"{percentage}%")
            
    def value(self) -> int:
        """获取当前值"""
        return self._progress_bar.value()
        
    def setMaximum(self, max_value: int):
        """设置最大值"""
        self._progress_bar.setMaximum(max_value)
        
    def maximum(self) -> int:
        """获取最大值"""
        return self._progress_bar.maximum()
        
    def setStatus(self, status: ProgressStatus):
        """设置进度条状态（颜色）"""
        self._progress_bar.setProperty("class", status.value)
        self._progress_bar.style().unpolish(self._progress_bar)
        self._progress_bar.style().polish(self._progress_bar)
        
    def setLabel(self, text: str):
        """设置标签文本"""
        if self._label:
            self._label.setText(text)

class ProgressIndicator(QWidget):
    """加载指示器组件"""
    
    def __init__(self, 
                 parent: Optional[QWidget] = None,
                 size: int = 32,
                 color: QColor = QColor(26, 110, 142),  # 主题蓝色
                 line_width: int = 3,
                 speed: int = 80):
        """
        初始化加载指示器
        
        Args:
            parent: 父组件
            size: 组件大小
            color: 指示器颜色
            line_width: 线宽
            speed: 旋转速度（毫秒/帧）
        """
        super().__init__(parent)
        
        # 保存属性
        self._color = color
        self._size = size
        self._line_width = line_width
        self._angle = 0
        self._speed = speed
        self._is_running = False
        
        # 设置尺寸
        self.setFixedSize(size, size)
        
        # 创建定时器
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._update_rotation)
        
    def _update_rotation(self):
        """更新旋转角度"""
        self._angle = (self._angle + 10) % 360
        self.update()
        
    def paintEvent(self, event: QPaintEvent):
        """绘制事件"""
        if not self._is_running:
            return
            
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # 计算尺寸
        width = self.width()
        height = self.height()
        
        # 设置画笔
        pen = QPen(self._color)
        pen.setWidth(self._line_width)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        
        # 绘制圆弧
        painter.translate(width/2, height/2)
        painter.rotate(self._angle)
        
        rect = QSize(width - self._line_width*2, height - self._line_width*2)
        
        # 绘制8个弧段，透明度逐渐减小
        for i in range(8):
            opacity = 1.0 - (i * 0.1)
            painter.setOpacity(opacity)
            painter.drawArc(int(-rect.width()/2), int(-rect.height()/2), 
                         int(rect.width()), int(rect.height()), 
                         i * 45 * 16, 30 * 16)
                            
        painter.end()
        
    def start(self):
        """开始旋转"""
        if not self._is_running:
            self._is_running = True
            self._timer.start(self._speed)
            self.update()
            
    def stop(self):
        """停止旋转"""
        if self._is_running:
            self._is_running = False
            self._timer.stop()
            self.update()
            
    def isRunning(self) -> bool:
        """检查是否正在运行"""
        return self._is_running
        
    def setColor(self, color: QColor):
        """设置颜色"""
        self._color = color
        self.update()

class LoadingWidget(QWidget):
    """加载组件，包含加载指示器和文本"""
    
    def __init__(self, 
                 parent: Optional[QWidget] = None,
                 text: str = "加载中...",
                 size: int = 32,
                 color: QColor = QColor(26, 110, 142)):
        """
        初始化加载组件
        
        Args:
            parent: 父组件
            text: 加载文本
            size: 指示器大小
            color: 指示器颜色
        """
        super().__init__(parent)
        
        # 创建布局
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # 创建加载指示器
        self._indicator = ProgressIndicator(self, size, color)
        self._layout.addWidget(self._indicator, 0, Qt.AlignmentFlag.AlignCenter)
        
        # 创建文本标签
        self._label = QLabel(text, self)
        self._label.setStyleSheet("color: #AAAAAA; font-size: 14px;")
        self._label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._layout.addWidget(self._label, 0, Qt.AlignmentFlag.AlignCenter)
        
        # 初始启动指示器
        self._indicator.start()
        
    def setText(self, text: str):
        """设置文本"""
        self._label.setText(text)
        
    def start(self):
        """开始加载"""
        self._indicator.start()
        self.setVisible(True)
        
    def stop(self):
        """停止加载"""
        self._indicator.stop()
        
    def setVisible(self, visible: bool):
        """设置可见性"""
        super().setVisible(visible)
        if visible:
            self._indicator.start()
        else:
            self._indicator.stop()

class CircularProgress(QWidget):
    """环形进度条组件"""
    
    # 声明类属性，解决mypy错误
    _label: Optional[QLabel] = None
    _percentage_label: Optional[QLabel] = None
    _layout: QVBoxLayout
    _value: int
    _max_value: int
    _size: int
    _line_width: int
    _show_percentage: bool
    _status: ProgressStatus
    
    def __init__(self, 
                 parent: Optional[QWidget] = None,
                 value: int = 0,
                 max_value: int = 100,
                 size: int = 80,
                 line_width: int = 8,
                 show_percentage: bool = True,
                 label: str = "",
                 status: ProgressStatus = ProgressStatus.DEFAULT):
        """
        初始化环形进度条
        
        Args:
            parent: 父组件
            value: 当前值
            max_value: 最大值
            size: 组件大小
            line_width: 线宽
            show_percentage: 是否显示百分比
            label: 标签文本
            status: 进度条状态
        """
        super().__init__(parent)
        
        # 保存属性
        self._value = value
        self._max_value = max_value
        self._size = size
        self._line_width = line_width
        self._show_percentage = show_percentage
        self._status = status
        
        # 设置尺寸
        self.setMinimumSize(size, size)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        
        # 创建布局
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # 如果有标签，添加标签
        if label:
            self._label = QLabel(label, self)
            self._label.setStyleSheet("color: #E6E6E6; font-size: 14px;")
            self._label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self._layout.addWidget(self._label)
            
        # 如果显示百分比，添加百分比标签
        if show_percentage:
            self._percentage_label = QLabel(f"{value}%", self)
            self._percentage_label.setStyleSheet("color: #E6E6E6; font-size: 16px; font-weight: bold;")
            self._percentage_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self._layout.addWidget(self._percentage_label)
            
    def setValue(self, value: int):
        """设置当前值"""
        self._value = min(value, self._max_value)
        if self._percentage_label:
            percentage = int((self._value / self._max_value) * 100)
            self._percentage_label.setText(f"{percentage}%")
        self.update()
            
    def value(self) -> int:
        """获取当前值"""
        return self._value
        
    def setMaximum(self, max_value: int):
        """设置最大值"""
        self._max_value = max_value
        self.setValue(self._value)  # 更新百分比显示
        
    def maximum(self) -> int:
        """获取最大值"""
        return self._max_value
        
    def setStatus(self, status: ProgressStatus):
        """设置进度条状态（颜色）"""
        self._status = status
        self.update()
        
    def setLabel(self, text: str):
        """设置标签文本"""
        if self._label:
            self._label.setText(text)
            
    def paintEvent(self, event: QPaintEvent):
        """绘制事件"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # 获取颜色
        color = QColor(26, 110, 142)  # 默认蓝色
        if self._status == ProgressStatus.SUCCESS:
            color = QColor(45, 140, 70)  # 绿色
        elif self._status == ProgressStatus.WARNING:
            color = QColor(216, 156, 0)  # 黄色
        elif self._status == ProgressStatus.ERROR:
            color = QColor(158, 43, 37)  # 红色
            
        # 设置画笔和画刷
        painter.setPen(Qt.PenStyle.NoPen)
        
        # 计算布局尺寸
        rect_size = min(self.width(), self.height())
        x = (self.width() - rect_size) / 2
        y = (self.height() - rect_size) / 2
        
        # 首先绘制背景圆环
        painter.setBrush(QBrush(QColor(42, 42, 42)))  # 深灰色背景
        painter.drawEllipse(int(x + self._line_width/2), int(y + self._line_width/2), 
                         int(rect_size - self._line_width), int(rect_size - self._line_width))
        
        # 设置进度条圆环画笔
        pen = QPen(color)
        pen.setWidth(self._line_width)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        
        # 计算进度角度（-90是从顶部开始，一个完整圆是360度）
        angle = int(360 * (self._value / self._max_value))
        
        # 绘制进度环
        painter.drawArc(int(x + self._line_width/2), int(y + self._line_width/2), 
                      int(rect_size - self._line_width), int(rect_size - self._line_width), 
                      90 * 16, -angle * 16)  # Qt中的角度以1/16度为单位 

class ProgressBarBase(QFrame):
    def _setup_ui(self):
        self.value_label: Optional[QLabel] = None
        self.text_label: Optional[QLabel] = None
        self.icon_label: Optional[QLabel] = None

class HorizontalProgressBar(ProgressBarBase):
    # ... existing code ...
    pass

class CircularProgressBar(ProgressBarBase):
    pass

class GaugeProgressBar(ProgressBarBase):
    # ... existing code ...
    pass

class BatteryProgressBar(ProgressBarBase):
    # ... existing code ...
    def _create_labels(self):
        self.value_label: Optional[QLabel] = None
        self.icon_label: Optional[QLabel] = None
        # ... existing code ... 