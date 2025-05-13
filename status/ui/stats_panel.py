"""
---------------------------------------------------------------
File name:                  stats_panel.py
Author:                     Ignorant-lu
Date created:               2025/05/13
Description:                显示系统统计信息 (CPU, 内存等) 的 UI 面板。
----------------------------------------------------------------

Changed history:
                            2025/05/13: 初始创建;
                            2025/05/13: 添加展开/折叠功能和详细系统信息显示;
                            2025/05/13: 添加调试日志和临时样式修复;
----
"""

import logging
from typing import Dict, Any, Optional, List
import time
import datetime

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QToolButton, 
    QHBoxLayout, QFrame, QScrollArea, QSizePolicy, QApplication
)
from PySide6.QtCore import Qt, QPoint, QSize, QTimer, QEvent
from PySide6.QtGui import QFont, QIcon, QPixmap, QColor, QPalette, QBrush, QLinearGradient, QPaintEvent, QShowEvent

# 导入事件系统相关
from status.core.events import EventManager, SystemStatsUpdatedEvent, WindowPositionChangedEvent
from status.core.event_system import EventType, Event # 导入 Event
# 导入时间行为系统相关
from status.behavior.time_based_behavior import TimePeriod

logger = logging.getLogger(__name__)

# 面板位置常量
PANEL_OFFSET_X = 10  # 面板相对于主窗口的X轴偏移量
PANEL_OFFSET_Y = 5   # 面板相对于主窗口的Y轴偏移量
PANEL_POSITION = "right"

class StatsPanel(QWidget):
    """用于显示系统统计信息 (如 CPU, 内存使用率) 的面板。"""
    layout: QVBoxLayout
    cpu_label: QLabel
    memory_label: QLabel
    
    # 详细信息标签
    cpu_cores_label: Optional[QLabel] = None
    memory_details_label: Optional[QLabel] = None
    disk_label: Optional[QLabel] = None
    network_label: Optional[QLabel] = None
    
    # 新增标签
    disk_io_label: Optional[QLabel] = None  # 磁盘IO
    network_speed_label: Optional[QLabel] = None  # 网络速度
    gpu_label: Optional[QLabel] = None  # GPU信息
    
    # 时间状态相关标签
    time_period_label: Optional[QLabel] = None  # 当前时间段
    special_date_label: Optional[QLabel] = None  # 特殊日期信息
    upcoming_dates_label: Optional[QLabel] = None  # 即将到来的特殊日期
    
    # 控制和状态
    is_expanded: bool = False
    expand_button: Optional[QToolButton] = None
    detailed_info_frame: Optional[QFrame] = None
    
    # 自动重定位相关
    panel_position: str = PANEL_POSITION
    parent_window_pos: Optional[QPoint] = None
    parent_window_size: Optional[QSize] = None
    
    def __init__(self, parent: QWidget | None = None):
        """初始化 StatsPanel。"""
        super().__init__(parent)
        
        # 临时调试：简化窗口标志，去除透明和无边框
        # self.setWindowFlags(Qt.WindowType.Tool | Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        # self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setWindowFlags(Qt.WindowType.Tool | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        
        # 初始默认为折叠状态
        self.is_expanded = False
        
        self._init_ui()
        self.hide() # 默认隐藏
        
        # 获取 EventManager 实例并注册处理器
        self.event_manager = EventManager.get_instance()
        self.event_manager.register_handler(EventType.SYSTEM_STATS_UPDATED, self.handle_stats_update)
        self.event_manager.register_handler(EventType.WINDOW_POSITION_CHANGED, self.handle_window_position_changed)
        
        # 注册时间事件处理器
        self.event_manager.register_handler(EventType.TIME_PERIOD_CHANGED, self.handle_time_period_changed)
        self.event_manager.register_handler(EventType.SPECIAL_DATE, self.handle_special_date)
        
        logger.info("StatsPanel 初始化完成并已注册事件处理器.")
        
        # 初始化时加载时间数据
        self._refresh_time_data()
        
        # 设置一个短延迟后再次刷新时间数据并处理时间段变化事件
        # 确保组件完全初始化并可访问所有模块
        QTimer.singleShot(1000, self._delayed_refresh)

    def _init_ui(self):
        """初始化面板的 UI 元素。"""
        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(4)
        self.layout = main_layout
        
        # 标题栏布局（标题 + 展开/折叠按钮）
        title_bar = QHBoxLayout()
        title_bar.setContentsMargins(0, 0, 0, 0)
        title_bar.setSpacing(5)
        
        # 标题标签
        title_label = QLabel("系统状态")
        title_label.setStyleSheet("font-weight: bold; color: #F0F0F0; font-size: 11px;")
        title_bar.addWidget(title_label)
        
        # 弹性空间
        title_bar.addStretch(1)
        
        # 展开/折叠按钮
        self.expand_button = QToolButton()
        self.expand_button.setText("▼") # 向下箭头表示展开
        self.expand_button.setStyleSheet("""
            QToolButton {
                color: #F0F0F0;
                background: transparent;
                border: none;
                font-size: 12px;
                font-weight: bold;
            }
            QToolButton:hover {
                color: #80C0FF;
            }
        """)
        self.expand_button.setFixedSize(18, 18)
        self.expand_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.expand_button.clicked.connect(self.toggle_expand_collapse)
        title_bar.addWidget(self.expand_button)
        
        # 添加标题栏到主布局
        main_layout.addLayout(title_bar)
        
        # 分隔线
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        separator.setStyleSheet("background-color: #5A5A5A;")
        separator.setFixedHeight(1)
        main_layout.addWidget(separator)
        
        # 基本信息区域
        basic_info = QVBoxLayout()
        basic_info.setContentsMargins(0, 4, 0, 4)
        basic_info.setSpacing(2)
        
        # CPU 使用率
        self.cpu_label = QLabel("CPU: --%")
        self.cpu_label.setStyleSheet("color: #80D8FF; font-size: 12px;")
        basic_info.addWidget(self.cpu_label)
        
        # 内存使用率
        self.memory_label = QLabel("内存: --%")
        self.memory_label.setStyleSheet("color: #80FFD8; font-size: 12px;")
        basic_info.addWidget(self.memory_label)
        
        # 将基本信息布局添加到主布局
        main_layout.addLayout(basic_info)
        
        # 创建详细信息框架（默认隐藏）
        self.detailed_info_frame = QFrame()
        self.detailed_info_frame.setFrameShape(QFrame.Shape.NoFrame)
        self.detailed_info_frame.setLineWidth(0)
        
        # 详细信息布局
        detailed_layout = QVBoxLayout(self.detailed_info_frame)
        detailed_layout.setContentsMargins(0, 5, 0, 0)
        detailed_layout.setSpacing(6)
        
        # 创建各个详细信息标签
        # CPU核心使用率
        self.cpu_cores_label = QLabel("CPU 核心: 加载中...")
        self.cpu_cores_label.setStyleSheet("color: #80D8FF; font-size: 11px;")
        self.cpu_cores_label.setWordWrap(True)
        detailed_layout.addWidget(self.cpu_cores_label)
        
        # 内存详情
        self.memory_details_label = QLabel("内存详情: 加载中...")
        self.memory_details_label.setStyleSheet("color: #80FFD8; font-size: 11px;")
        self.memory_details_label.setWordWrap(True)
        detailed_layout.addWidget(self.memory_details_label)
        
        # 磁盘使用情况
        self.disk_label = QLabel("磁盘: 加载中...")
        self.disk_label.setStyleSheet("color: #FFD080; font-size: 11px;")
        self.disk_label.setWordWrap(True)
        detailed_layout.addWidget(self.disk_label)
        
        # 网络信息
        self.network_label = QLabel("网络: 加载中...")
        self.network_label.setStyleSheet("color: #A0D0FF; font-size: 11px;")
        self.network_label.setWordWrap(True)
        detailed_layout.addWidget(self.network_label)
        
        # 新增: 磁盘IO信息
        self.disk_io_label = QLabel("磁盘IO: 加载中...")
        self.disk_io_label.setStyleSheet("color: #F0C080; font-size: 11px;")
        self.disk_io_label.setWordWrap(True)
        detailed_layout.addWidget(self.disk_io_label)
        
        # 新增: 网络速度信息
        self.network_speed_label = QLabel("网络速度: 加载中...")
        self.network_speed_label.setStyleSheet("color: #80B0FF; font-size: 11px;")
        self.network_speed_label.setWordWrap(True)
        detailed_layout.addWidget(self.network_speed_label)
        
        # 新增: GPU信息
        self.gpu_label = QLabel("GPU: 加载中...")
        self.gpu_label.setStyleSheet("color: #C080FF; font-size: 11px;")
        self.gpu_label.setWordWrap(True)
        detailed_layout.addWidget(self.gpu_label)
        
        # 添加分隔线
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        separator.setStyleSheet("background-color: #5A5A5A;")
        separator.setFixedHeight(1)
        detailed_layout.addWidget(separator)
        
        # 新增: 时间状态区域
        # 时间段
        self.time_period_label = QLabel("时间段: 未知")
        self.time_period_label.setStyleSheet("color: #FFE0A0; font-size: 11px;")
        self.time_period_label.setWordWrap(True)
        detailed_layout.addWidget(self.time_period_label)
        
        # 特殊日期
        self.special_date_label = QLabel("特殊日期: 无")
        self.special_date_label.setStyleSheet("color: #FFA0A0; font-size: 11px;")
        self.special_date_label.setWordWrap(True)
        detailed_layout.addWidget(self.special_date_label)
        
        # 即将到来的特殊日期
        self.upcoming_dates_label = QLabel("即将到来: 无")
        self.upcoming_dates_label.setStyleSheet("color: #A0FFA0; font-size: 11px;")
        self.upcoming_dates_label.setWordWrap(True)
        detailed_layout.addWidget(self.upcoming_dates_label)
        
        # 将详细信息框架添加到主布局，但默认隐藏
        main_layout.addWidget(self.detailed_info_frame)
        self.detailed_info_frame.setVisible(False)
        
        # 面板整体样式设置
        self.setStyleSheet("""
            StatsPanel {
                background-color: rgba(40, 44, 52, 230);
                border-radius: 6px;
                border: 1px solid rgba(60, 70, 80, 200);
            }
        """)
        
        # 临时调试：添加明显的背景色和边框
        # self.setStyleSheet("StatsPanel { background-color: red; border: 2px solid black; }")
        
        # 设置大小策略
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        self.setMinimumWidth(170)
        self.setMinimumHeight(85)  # 添加最小高度
        
        # 添加最大尺寸限制以避免窗口几何问题
        self.setMaximumWidth(320)  # 设置合理的最大宽度
        self.setMaximumHeight(600)  # 设置合理的最大高度
        
        logger.info("StatsPanel UI 初始化完成")

    # 添加showEvent方法用于调试
    def showEvent(self, event: QShowEvent):
        """当面板显示时调用"""
        logger.info(f"StatsPanel.showEvent triggered. Visible: {self.isVisible()}, Position: {self.pos()}, Size: {self.size()}")
        super().showEvent(event)

    # 添加paintEvent方法用于调试
    def paintEvent(self, event: QPaintEvent):
        """绘制面板时调用"""
        logger.debug(f"StatsPanel.paintEvent triggered. Rect: {event.rect()}, Visible: {self.isVisible()}")
        super().paintEvent(event)

    def update_data(self, data: Dict[str, Any]):
        """用新数据更新面板显示。"""
        logger.debug(f"StatsPanel 更新数据: {data}") # 修改日志级别以便查看数据
        
        # 基本信息更新
        cpu_usage = data.get('cpu_usage', None)
        memory_usage = data.get('memory_usage', None)
        
        if cpu_usage is not None:
            # 根据CPU使用率设置不同颜色
            if cpu_usage < 30:
                color = "#80D8FF"  # 低负载 - 蓝色
            elif cpu_usage < 70:
                color = "#FFCC80"  # 中负载 - 橙色
            else:
                color = "#FF8080"  # 高负载 - 红色
            
            self.cpu_label.setStyleSheet(f"color: {color}; font-size: 12px;")
            self.cpu_label.setText(f"CPU: {cpu_usage:.1f}%")
        else:
            self.cpu_label.setText("CPU: --%")
            
        if memory_usage is not None:
            # 根据内存使用率设置不同颜色
            if memory_usage < 50:
                color = "#80FFD8"  # 低使用率 - 绿色
            elif memory_usage < 80:
                color = "#FFCC80"  # 中使用率 - 橙色
            else:
                color = "#FF8080"  # 高使用率 - 红色
            
            self.memory_label.setStyleSheet(f"color: {color}; font-size: 12px;")
            self.memory_label.setText(f"Mem: {memory_usage:.1f}%")
        else:
            self.memory_label.setText("Mem: --%")
        
        # 如果展开状态，更新详细信息
        if self.is_expanded:
            # 更新CPU核心信息
            cpu_cores = data.get('cpu_cores_usage', [])
            if cpu_cores and self.cpu_cores_label is not None:
                cores_text = "CPU 核心: "
                for i, core in enumerate(cpu_cores):
                    if i > 0:
                        cores_text += " | "
                    
                    # 根据核心使用率设置不同颜色
                    if core < 30:
                        color_code = "80D8FF"  # 低负载 - 蓝色
                    elif core < 70:
                        color_code = "FFCC80"  # 中负载 - 橙色
                    else:
                        color_code = "FF8080"  # 高负载 - 红色
                    
                    cores_text += f"<span style='color: #{color_code}'>#{i}: {core:.1f}%</span>"
                
                self.cpu_cores_label.setText(cores_text)
                self.cpu_cores_label.setTextFormat(Qt.TextFormat.RichText)
            
            # 更新内存详情
            memory_details = data.get('memory_details', {})
            if memory_details and self.memory_details_label is not None:
                total_mb = memory_details.get('total_mb', 0)
                used_mb = memory_details.get('used_mb', 0)
                free_mb = memory_details.get('free_mb', 0)
                percent = memory_details.get('percent', 0)
                
                # 根据内存使用率设置颜色
                if percent < 50:
                    color_code = "80FFD8"  # 低使用率 - 绿色
                elif percent < 80:
                    color_code = "FFCC80"  # 中使用率 - 橙色
                else:
                    color_code = "FF8080"  # 高使用率 - 红色
                
                memory_text = f"内存: <span style='color: #{color_code}'>{used_mb} MB</span> / {total_mb} MB"
                memory_text += f"<br>({percent:.1f}% 使用, {free_mb} MB 空闲)"
                
                self.memory_details_label.setText(memory_text)
                self.memory_details_label.setTextFormat(Qt.TextFormat.RichText)
            
            # 更新磁盘信息
            disk_info = data.get('disk_usage_root', {})
            if disk_info and self.disk_label is not None:
                used_gb = disk_info.get('used_gb', 0)
                total_gb = disk_info.get('total_gb', 0)
                free_gb = disk_info.get('free_gb', 0)
                percent = disk_info.get('percent', 0)
                
                # 根据使用率设置颜色
                if percent < 50:
                    color_code = "FFD080"  # 低使用率
                elif percent < 80:
                    color_code = "FFCC80"  # 中使用率
                else:
                    color_code = "FF8080"  # 高使用率
                
                disk_text = f"磁盘: <span style='color: #{color_code}'>{used_gb} GB</span> / {total_gb} GB"
                disk_text += f"<br>({percent:.1f}% 使用, {free_gb} GB 空闲)"
                
                self.disk_label.setText(disk_text)
                self.disk_label.setTextFormat(Qt.TextFormat.RichText)
            
            # 更新网络信息
            network_info = data.get('network_info', {})
            if network_info and self.network_label is not None:
                sent_mb = network_info.get('sent_mb', 0)
                recv_mb = network_info.get('recv_mb', 0)
                
                network_text = f"网络: <span style='color: #D0A0FF'>↑{sent_mb} MB</span> 发送"
                network_text += f"<br><span style='color: #A0D0FF'>↓{recv_mb} MB</span> 接收"
                
                self.network_label.setText(network_text)
                self.network_label.setTextFormat(Qt.TextFormat.RichText)
                
            # 新增: 更新磁盘IO信息
            disk_io = data.get('disk_io_speed', {})
            if disk_io and self.disk_io_label is not None:
                read_kbps = disk_io.get('read_mbps', 0) * 1024  # convert MB/s to KB/s
                write_kbps = disk_io.get('write_mbps', 0) * 1024  # convert MB/s to KB/s
                
                # 转换为合适的单位和文本格式
                read_text = f"{read_kbps:.1f} KB/s" if read_kbps < 1024 else f"{read_kbps / 1024:.1f} MB/s"
                write_text = f"{write_kbps:.1f} KB/s" if write_kbps < 1024 else f"{write_kbps / 1024:.1f} MB/s"
                
                disk_io_text = f"磁盘IO: <span style='color: #80D0A0'>↓{read_text}</span> 读取"
                disk_io_text += f"<br><span style='color: #D0A080'>↑{write_text}</span> 写入"
                
                self.disk_io_label.setText(disk_io_text)
                self.disk_io_label.setTextFormat(Qt.TextFormat.RichText)
                
            # 新增: 更新网络速度信息
            network_speed = data.get('network_speed', {})
            if network_speed and self.network_speed_label is not None:
                upload_kbps = network_speed.get('upload_kbps', 0)
                download_kbps = network_speed.get('download_kbps', 0)
                
                # 转换为合适的单位和文本格式
                upload_text = f"{upload_kbps:.1f} KB/s" if upload_kbps < 1024 else f"{upload_kbps / 1024:.1f} MB/s"
                download_text = f"{download_kbps:.1f} KB/s" if download_kbps < 1024 else f"{download_kbps / 1024:.1f} MB/s"
                
                network_speed_text = f"网络速度: <span style='color: #D0A0FF'>↑{upload_text}</span> 上传"
                network_speed_text += f"<br><span style='color: #A0D0FF'>↓{download_text}</span> 下载"
                
                self.network_speed_label.setText(network_speed_text)
                self.network_speed_label.setTextFormat(Qt.TextFormat.RichText)
                
            # 新增: 更新GPU信息
            gpu_info = data.get('gpu_info', {})
            if gpu_info and self.gpu_label is not None and not gpu_info.get('error'):
                gpu_name = gpu_info.get('name', 'Unknown')
                gpu_load = gpu_info.get('load', 0)
                gpu_memory_total = gpu_info.get('memoryTotal', 0)
                gpu_memory_used = gpu_info.get('memoryUsed', 0)
                gpu_memory_percent = gpu_info.get('memoryUtil', 0)
                gpu_temp = gpu_info.get('temperature', 0)
                
                # 根据GPU负载设置颜色
                if gpu_load < 30:
                    load_color = "80D8FF"  # 低负载
                elif gpu_load < 70:
                    load_color = "FFCC80"  # 中负载
                else:
                    load_color = "FF8080"  # 高负载
                
                # 根据GPU内存使用率设置颜色
                if gpu_memory_percent < 30:
                    memory_color = "80FFD8"  # 低使用率
                elif gpu_memory_percent < 70:
                    memory_color = "FFCC80"  # 中使用率
                else:
                    memory_color = "FF8080"  # 高使用率
                
                # 根据GPU温度设置颜色
                if gpu_temp < 60:
                    temp_color = "80FFD8"  # 低温
                elif gpu_temp < 80:
                    temp_color = "FFCC80"  # 中温
                else:
                    temp_color = "FF8080"  # 高温
                
                # 生成GPU信息文本
                gpu_text = f"GPU: {gpu_name}<br>"
                gpu_text += f"负载: <span style='color: #{load_color}'>{gpu_load:.1f}%</span>"
                
                if gpu_memory_total > 0:
                    gpu_text += f"<br>显存: <span style='color: #{memory_color}'>{gpu_memory_used} MB</span> / {gpu_memory_total} MB ({gpu_memory_percent:.1f}%)"
                
                if gpu_temp > 0:
                    gpu_text += f"<br>温度: <span style='color: #{temp_color}'>{gpu_temp}°C</span>"
                
                self.gpu_label.setText(gpu_text)
                self.gpu_label.setTextFormat(Qt.TextFormat.RichText)
                self.gpu_label.setVisible(True)
            else:
                # 如果没有GPU信息，隐藏该标签
                if self.gpu_label is not None:
                    self.gpu_label.setVisible(False)
        
        # 调整大小，但要确保不频繁调整（可能导致闪烁）
        if data.get('cpu_cores_usage') or data.get('memory_details') or data.get('disk_usage_root') or data.get('network_info'):
            self.adjustSize()

    def update_time_data(self, data: Dict[str, Any]):
        """更新时间相关数据
        
        Args:
            data: 时间数据字典
        """
        logger.debug(f"StatsPanel 更新时间数据: {data}")
        
        # 存储时间数据，无论面板是否展开
        self._time_data = getattr(self, '_time_data', {})
        self._time_data.update(data)
        
        # 如果面板未展开，只更新数据不更新UI
        if not self.is_expanded:
            logger.debug("StatsPanel 未展开，仅存储时间数据不更新UI")
            return
            
        # 根据存储的数据更新UI
        self._update_time_ui(self._time_data)
    
    def _update_time_ui(self, time_data):
        """更新时间UI显示

        Args:
            time_data: 时间数据字典
        """
        logger.debug(f"更新时间UI: {time_data}")
        
        # 如果面板未展开，不更新UI
        if not self.is_expanded:
            logger.debug("面板未展开，不更新时间UI")
            return
            
        # 更新时间段标签
        if 'period' in time_data and self.time_period_label:
            period_name = time_data['period']
            
            # 根据时间段名称设置不同颜色
            if period_name == TimePeriod.MORNING.name:
                color = "#FFE0A0"  # 淡黄色
            elif period_name == TimePeriod.NOON.name:
                color = "#FFCC80"  # 橙色
            elif period_name == TimePeriod.AFTERNOON.name:
                color = "#80D0FF"  # 淡蓝色
            elif period_name == TimePeriod.EVENING.name:
                color = "#FFA080"  # 淡橙色
            elif period_name == TimePeriod.NIGHT.name:
                color = "#A080FF"  # 淡紫色
            else:
                color = "#E0E0E0"  # 默认浅灰色
                
            # 更新标签文字和颜色
            self.time_period_label.setText(f"当前时段: {period_name}")
            self.time_period_label.setStyleSheet(f"color: {color}; font-size: 12px; font-weight: bold;")
            logger.debug(f"已更新时间段标签: {period_name}")
        
        # 更新特殊日期标签
        if 'special_date' in time_data and self.special_date_label:
            special_date = time_data['special_date']
            if special_date:
                special_date_text = f"{special_date['name']}: {special_date['description']}"
                self.special_date_label.setText(special_date_text)
                self.special_date_label.setStyleSheet("color: #FF8080; font-size: 11px;")  # 特殊日期用红色表示
                self.special_date_label.show()
                logger.debug(f"已更新特殊日期标签: {special_date['name']}")
            else:
                self.special_date_label.setText("今天没有特殊日期")
                self.special_date_label.setStyleSheet("color: #A0A0A0; font-size: 11px;")
                logger.debug("今天没有特殊日期")
        
        # 更新即将到来的特殊日期标签
        if 'upcoming_dates' in time_data and self.upcoming_dates_label:
            upcoming = time_data['upcoming_dates']
            if upcoming:
                # 显示最多3个即将到来的特殊日期
                upcoming_text = "即将到来: "
                upcoming_text += ", ".join([f"{d['name']} ({d['date']})" for d in upcoming[:3]])
                self.upcoming_dates_label.setText(upcoming_text)
                self.upcoming_dates_label.setStyleSheet("color: #80C080; font-size: 11px;")
                self.upcoming_dates_label.show()
                logger.debug(f"已更新即将到来的特殊日期标签: {len(upcoming)}个")
            else:
                self.upcoming_dates_label.setText("近期没有特殊日期")
                self.upcoming_dates_label.setStyleSheet("color: #A0A0A0; font-size: 11px;")
                logger.debug("近期没有特殊日期")
        
        # 调整大小
        self.adjustSize()
        logger.debug("时间UI更新完成")

    def toggle_expand_collapse(self):
        """切换面板的展开/折叠状态。"""
        self.is_expanded = not self.is_expanded
        
        # 更新按钮文本
        if self.expand_button is not None:
            self.expand_button.setText("▲" if self.is_expanded else "▼")
        
        # 显示/隐藏详细信息区域
        if self.detailed_info_frame is not None:
            self.detailed_info_frame.setVisible(self.is_expanded)
        
        # 如果面板展开，尝试直接从全局实例获取时间数据
        if self.is_expanded:
            self._refresh_time_data()
            
            # 如果存在已存储的时间数据，则更新时间UI
            if hasattr(self, '_time_data'):
                logger.debug(f"更新展开后的时间UI，数据: {self._time_data}")
                self._update_time_ui(self._time_data)
        
        # 调整大小
        self.adjustSize()
        
        # 如果有父窗口位置信息，更新面板位置
        if self.parent_window_pos is not None and self.parent_window_size is not None:
            self.update_position(self.parent_window_pos, self.parent_window_size)
        
        logger.debug(f"StatsPanel {'展开' if self.is_expanded else '折叠'}")
    
    def _refresh_time_data(self):
        """直接从时间行为系统获取时间数据"""
        try:
            # 首先使用通用函数获取应用实例
            from status.core.events import get_app_instance
            from status.monitoring.system_monitor import get_time_data
            
            app = get_app_instance()
            time_data = {}
            
            # 尝试从应用实例获取时间数据
            if app and hasattr(app, 'time_behavior_system') and app.time_behavior_system and app.time_behavior_system.is_active:
                tbs = app.time_behavior_system
                logger.debug(f"时间行为系统: {tbs}, 已初始化: {tbs.is_initialized}, 已激活: {tbs.is_active}")
                
                # 获取当前时间段
                current_period = tbs.get_current_period()
                if current_period:
                    time_data['period'] = current_period.name
                    logger.info(f"StatsPanel 刷新时间段数据: {current_period.name}")
                
                # 获取当前特殊日期
                special_dates = tbs.get_current_special_dates()
                if special_dates:
                    first_date = special_dates[0]
                    time_data['special_date'] = {
                        'name': first_date.name,
                        'description': first_date.description
                    }
                    logger.info(f"StatsPanel 刷新特殊日期数据: {first_date.name}")
                
                # 获取即将到来的特殊日期
                upcoming_dates = tbs.get_upcoming_special_dates(days=7)
                if upcoming_dates:
                    upcoming_list = []
                    for date_obj, date_time in upcoming_dates[:3]:  # 只取前3个
                        upcoming_list.append({
                            'name': date_obj.name,
                            'date': date_time.strftime('%Y-%m-%d'),
                            'description': date_obj.description
                        })
                    time_data['upcoming_dates'] = upcoming_list
                    logger.info(f"StatsPanel 刷新即将到来的特殊日期数据: {len(upcoming_list)}个")
            else:
                # 如果应用实例无法获取或无时间行为系统，使用独立函数
                logger.debug("无法从应用实例获取时间数据，使用独立函数")
                time_data = get_time_data()
                logger.info(f"使用独立函数获取时间数据: {list(time_data.keys())}")
            
            # 更新时间数据
            if time_data:
                self.update_time_data(time_data)
                return True
            return False
        except Exception as e:
            logger.error(f"刷新时间数据失败: {e}", exc_info=True)
            return False

    def _delayed_refresh(self):
        """延迟刷新函数，在组件完全初始化后执行"""
        logger.debug("执行延迟刷新操作")
        
        # 尝试刷新时间数据
        success = self._refresh_time_data()
        
        if not success:
            # 如果刷新失败，则尝试创建一个简单的时间数据
            logger.debug("尝试使用当前时间创建基本时间段数据")
            try:
                from status.monitoring.system_monitor import get_current_time_period
                
                current_period = get_current_time_period()
                if current_period:
                    # 手动创建时间数据
                    time_data = {
                        'period': current_period.name
                    }
                    
                    # 更新时间数据
                    self.update_time_data(time_data)
                    
                    logger.info(f"延迟刷新: 使用基本时间段 {current_period.name}")
            except Exception as e:
                logger.error(f"创建基本时间段数据失败: {e}", exc_info=True)

    def show_panel(self, position: QPoint):
        """在指定位置显示面板。"""
        logger.debug(f"显示 StatsPanel 于 {position}")
        self.move(position)
        self.show()
        # 添加以下代码以确保面板显示在最前
        self.raise_()
        self.activateWindow()
        logger.info(f"StatsPanel.show_panel: after self.show() - Visible: {self.isVisible()}, Geometry: {self.geometry()}")

    def hide_panel(self):
        """隐藏面板。"""
        logger.debug("隐藏 StatsPanel")
        self.hide()

    def handle_stats_update(self, event: Event):
        """处理 SystemStatsUpdatedEvent 事件。"""
        if event.type == EventType.SYSTEM_STATS_UPDATED and isinstance(event, SystemStatsUpdatedEvent):
            logger.debug(f"StatsPanel 接收到事件: {event.type.name} with data keys: {list(event.stats_data.keys())}")
            
            # 检查是否包含时间数据
            time_keys = ['period', 'special_date', 'upcoming_dates']
            time_data_exists = any(key in event.stats_data for key in time_keys)
            logger.debug(f"事件中包含时间数据: {time_data_exists}")
            if time_data_exists:
                logger.debug(f"时间数据详情: {[k for k in time_keys if k in event.stats_data]}")
            
            self.update_data(event.stats_data)
            
            # 提取事件中的时间数据
            time_data = {}
            if 'period' in event.stats_data:
                time_data['period'] = event.stats_data['period']
                logger.info(f"StatsPanel 收到时间段数据: {event.stats_data['period']}")
            if 'special_date' in event.stats_data:
                time_data['special_date'] = event.stats_data['special_date']
                logger.info(f"StatsPanel 收到特殊日期数据: {event.stats_data['special_date']['name']}")
            if 'upcoming_dates' in event.stats_data:
                time_data['upcoming_dates'] = event.stats_data['upcoming_dates']
                dates_str = ', '.join([f"{d['name']} ({d['date']})" for d in event.stats_data['upcoming_dates'][:2]])
                logger.info(f"StatsPanel 收到即将到来的特殊日期: {dates_str}")
                
            # 如果有时间数据，就更新
            if time_data:
                logger.debug(f"更新时间数据: {time_data}")
                self.update_time_data(time_data)
                
                # 如果面板已展开，强制更新UI
                if self.is_expanded and hasattr(self, '_time_data'):
                    logger.debug(f"强制更新时间UI，面板已展开")
                    self._update_time_ui(self._time_data)
                
                logger.debug(f"StatsPanel 时间数据更新完成，面板展开状态: {self.is_expanded}")
            else:
                logger.warning("未在事件中找到任何时间数据")
        else:
            logger.warning(f"StatsPanel 收到非预期的事件类型: {event.type.name}")
    
    def handle_window_position_changed(self, event: Event):
        """处理 WindowPositionChangedEvent 事件，更新面板位置。"""
        if event.type == EventType.WINDOW_POSITION_CHANGED and isinstance(event, WindowPositionChangedEvent):
            # 存储父窗口位置信息
            self.parent_window_pos = event.position
            self.parent_window_size = event.size
            
            # 如果面板正在显示，更新位置
            if self.isVisible():
                self.update_position(event.position, event.size)
                logger.debug(f"StatsPanel 位置已更新，跟随窗口移动到: {event.position}")
    
    def update_position(self, parent_pos: QPoint, parent_size: QSize):
        """根据父窗口位置和大小，更新面板位置。
        
        Args:
            parent_pos: 父窗口位置
            parent_size: 父窗口大小
        """
        panel_size = self.sizeHint()
        screen_geometry = QApplication.primaryScreen().availableGeometry()
        new_pos = QPoint()
        
        # 根据设置的面板位置计算新位置
        if self.panel_position == "right":
            # 右侧
            new_pos.setX(parent_pos.x() + parent_size.width() + PANEL_OFFSET_X)
            new_pos.setY(parent_pos.y())
            
            # 检查是否超出屏幕右边界
            if new_pos.x() + panel_size.width() > screen_geometry.right():
                # 切换到左侧
                new_pos.setX(parent_pos.x() - panel_size.width() - PANEL_OFFSET_X)
        
        elif self.panel_position == "left":
            # 左侧
            new_pos.setX(parent_pos.x() - panel_size.width() - PANEL_OFFSET_X)
            new_pos.setY(parent_pos.y())
            
            # 检查是否超出屏幕左边界
            if new_pos.x() < screen_geometry.left():
                # 切换到右侧
                new_pos.setX(parent_pos.x() + parent_size.width() + PANEL_OFFSET_X)
        
        elif self.panel_position == "bottom":
            # 底部
            new_pos.setX(parent_pos.x())
            new_pos.setY(parent_pos.y() + parent_size.height() + PANEL_OFFSET_Y)
            
            # 检查是否超出屏幕底部
            if new_pos.y() + panel_size.height() > screen_geometry.bottom():
                # 切换到顶部
                new_pos.setY(parent_pos.y() - panel_size.height() - PANEL_OFFSET_Y)
        
        elif self.panel_position == "top":
            # 顶部
            new_pos.setX(parent_pos.x())
            new_pos.setY(parent_pos.y() - panel_size.height() - PANEL_OFFSET_Y)
            
            # 检查是否超出屏幕顶部
            if new_pos.y() < screen_geometry.top():
                # 切换到底部
                new_pos.setY(parent_pos.y() + parent_size.height() + PANEL_OFFSET_Y)
        
        # 最终检查，确保面板完全在屏幕内
        # 检查右边界
        if new_pos.x() + panel_size.width() > screen_geometry.right():
            new_pos.setX(screen_geometry.right() - panel_size.width())
        
        # 检查左边界
        if new_pos.x() < screen_geometry.left():
            new_pos.setX(screen_geometry.left())
        
        # 检查下边界
        if new_pos.y() + panel_size.height() > screen_geometry.bottom():
            new_pos.setY(screen_geometry.bottom() - panel_size.height())
        
        # 检查上边界
        if new_pos.y() < screen_geometry.top():
            new_pos.setY(screen_geometry.top())
        
        # 移动面板
        self.move(new_pos)
        logger.info(f"StatsPanel.update_position: Moved to {new_pos}. Panel Geometry: {self.geometry()}, Visible: {self.isVisible()}")
    
    def closeEvent(self, event):
        """处理窗口关闭事件，注销事件处理器。"""
        logger.debug("StatsPanel 关闭，注销事件处理器...")
        if hasattr(self, 'event_manager') and self.event_manager:
            try:
                self.event_manager.unregister_handler(EventType.SYSTEM_STATS_UPDATED, self.handle_stats_update)
                self.event_manager.unregister_handler(EventType.WINDOW_POSITION_CHANGED, self.handle_window_position_changed)
                
                # 注销时间事件处理器
                self.event_manager.unregister_handler(EventType.TIME_PERIOD_CHANGED, self.handle_time_period_changed)
                self.event_manager.unregister_handler(EventType.SPECIAL_DATE, self.handle_special_date)
                
                logger.info("StatsPanel 事件处理器已成功注销。")
            except Exception as e:
                logger.error(f"注销 StatsPanel 事件处理器时出错: {e}")
        super().closeEvent(event)
        
    def sizeHint(self):
        """提供面板大小的建议值。"""
        if self.is_expanded:
            # 展开时的建议大小，确保不超过最大限制
            return QSize(min(240, self.maximumWidth()), 
                        min(200, self.maximumHeight()))
        else:
            # 折叠时的建议大小
            return QSize(min(180, self.maximumWidth()), 
                        min(85, self.maximumHeight()))

    def handle_time_period_changed(self, event: Event):
        """处理时间段变化事件"""
        if event.type == EventType.TIME_PERIOD_CHANGED:
            logger.debug(f"StatsPanel 接收到时间段变化事件: {event.data}")
            
            # 更新时间数据
            self.update_time_data({
                'period': event.data.get('period', 'UNKNOWN')
            })
    
    def handle_special_date(self, event: Event):
        """处理特殊日期事件"""
        if event.type == EventType.SPECIAL_DATE:
            logger.debug(f"StatsPanel 接收到特殊日期事件: {event.data}")
            
            # 从事件数据中提取相关信息
            special_date = {
                'name': event.data.get('name', '未知'),
                'description': event.data.get('description', '')
            }
            
            # 更新时间数据
            self.update_time_data({
                'special_date': special_date
            })