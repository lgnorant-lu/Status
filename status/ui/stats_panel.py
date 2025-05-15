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
from status.core.events import EventManager, SystemStatsUpdatedEvent, WindowPositionChangedEvent, get_app_instance as get_core_app_instance
from status.core.event_system import EventType, Event # 导入 Event
# 导入时间行为系统相关
from status.behavior.time_based_behavior import TimePeriod # Removed get_time_data and DEFAULT_TIME_PERIOD_STR
from status.monitoring.system_monitor import get_time_data # Added import for get_time_data

logger = logging.getLogger(__name__)
# 定义一个模块级别的默认字符串，如果 time_based_behavior.py 中确实没有
DEFAULT_TIME_PERIOD_STR_LOCAL = "未知"

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
        self.event_manager = EventManager() # This is LegacyEventManagerAdapter.get_instance
        logger.info(f"[StatsPanel.__init__] EventManager type: {type(self.event_manager)}, id: {id(self.event_manager)}")
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
        """更新面板上显示的统计数据。"""
        logger.debug(f"DEBUG_PANEL_UPDATE_DATA_ENTRY: update_data called with data keys: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}, data: {str(data)[:200]}")

        # 更新主要统计数据 (CPU, 内存)
        cpu_usage = data.get('cpu')
        logger.debug(f"DEBUG_PANEL_CPU_RAW: cpu_usage from data.get('cpu'): {cpu_usage} (type: {type(cpu_usage)})")
        
        if cpu_usage is not None and isinstance(cpu_usage, (float, int)):
            color = "#80D8FF" # Default blue
            if cpu_usage > 90: color = "#FF6060" # Red for high
            elif cpu_usage > 70: color = "#FFC107" # Amber for medium
            self.cpu_label.setStyleSheet(f"color: {color}; font-size: 12px;")
            self.cpu_label.setText(f"CPU: {cpu_usage:.1f}%")
        elif isinstance(cpu_usage, str) and cpu_usage in ["warning", "error", "critical"]:
            if cpu_usage == "warning":
                self.cpu_label.setStyleSheet("color: #FFC107; font-size: 12px;") 
                self.cpu_label.setText("CPU: 预警!")
            elif cpu_usage == "error":
                self.cpu_label.setStyleSheet("color: #FF8080; font-size: 12px;") 
                self.cpu_label.setText("CPU: 错误!")
            elif cpu_usage == "critical":
                self.cpu_label.setStyleSheet("color: #FF6060; font-size: 12px;") 
                self.cpu_label.setText("CPU: 危险!")
        else: 
            # Fallback for None or other unexpected types for cpu_usage
            logger.debug(f"DEBUG_PANEL_CPU_FALLBACK: cpu_usage is None or unexpected type. Value: '{cpu_usage}', Type: {type(cpu_usage)}")
            self.cpu_label.setStyleSheet("color: #E0E0E0; font-size: 12px;") # Default/fallback style
            self.cpu_label.setText("CPU: --%") # Fallback text for other cases

        # 内存使用率
        memory_usage = data.get('memory')
        logger.debug(f"DEBUG_PANEL_MEM_RAW: memory_usage from data.get('memory'): {memory_usage} (type: {type(memory_usage)})")
        if memory_usage is not None and isinstance(memory_usage, (float, int)):
            color = "#80FFD8"
            if memory_usage > 90: color = "#FF6060"
            elif memory_usage > 75: color = "#FFCC60" # Original amber for memory
            self.memory_label.setStyleSheet(f"color: {color}; font-size: 12px;")
            self.memory_label.setText(f"内存: {memory_usage:.1f}%")
        elif isinstance(memory_usage, str) and memory_usage in ["warning", "error", "critical"]:
            if memory_usage == "warning":
                self.memory_label.setStyleSheet("color: #FFCC60; font-size: 12px;")
                self.memory_label.setText("内存: 预警!")
            elif memory_usage == "error":
                self.memory_label.setStyleSheet("color: #FF8080; font-size: 12px;")
                self.memory_label.setText("内存: 错误!")
            elif memory_usage == "critical":
                self.memory_label.setStyleSheet("color: #FF6060; font-size: 12px;")
                self.memory_label.setText("内存: 危险!")
        else: 
            logger.debug(f"DEBUG_PANEL_MEM_FALLBACK: memory_usage is None or not float/int. Type: {type(memory_usage)}")
            self.memory_label.setText("内存: --%")
        
        logger.debug(f"DEBUG_PANEL_UPDATE: In update_data. Checking expansion: self.is_expanded={self.is_expanded}, self.detailed_info_frame_exists={self.detailed_info_frame is not None}")
        if self.is_expanded and self.detailed_info_frame:
            # Log the data being passed to _update_detailed_info
            logger.info(f"[StatsPanel.update_data] Panel is expanded. Calling _update_detailed_info. Current is_expanded: {self.is_expanded}")
            logger.debug(f"DEBUG_PANEL_CALL_DETAIL: Calling _update_detailed_info with data: {data}")
            self._update_detailed_info(data)
        elif not self.is_expanded:
            logger.info(f"[StatsPanel.update_data] Panel is NOT expanded. _update_detailed_info will NOT be called. Current is_expanded: {self.is_expanded}")
        
        logger.debug(f"DEBUG_PANEL_UPDATE: update_data FINISHED. cpu_label='{self.cpu_label.text()}', memory_label='{self.memory_label.text()}'")

    def _update_detailed_info(self, data: Dict[str, Any]):
        """更新详细信息区域
        
        将详细信息更新逻辑独立出来，减少主方法的复杂度
        
        Args:
            data: 统计数据字典
        """
        logger.debug(f"DEBUG_PANEL_DETAIL_START: _update_detailed_info CALLED. Incoming data keys: {list(data.keys())}")
        # 确保所有标签都存在 (excluding time labels that are now handled by _update_time_ui)
        if not all([self.cpu_cores_label, self.memory_details_label, self.disk_label, 
                    self.network_label, self.disk_io_label, self.network_speed_label, 
                    self.gpu_label]): # Removed time_period_label, special_date_label, upcoming_dates_label from this check
            logger.warning("StatsPanel: 部分核心详细信息标签未初始化，跳过更新。")
            # Time labels are checked in _update_time_ui or implicitly by their existence.
            # return # Do not return, still attempt to update what's available and time data.

        # 1. CPU 核心使用率
        cpu_cores_usage = data.get('cpu_cores') 
        if self.cpu_cores_label:
            if cpu_cores_usage is not None and isinstance(cpu_cores_usage, list):
                cores_text = ", ".join([f"{usage:.1f}%" for usage in cpu_cores_usage])
                self.cpu_cores_label.setText(f"CPU 核心: {cores_text}")
            else:
                self.cpu_cores_label.setText("CPU 核心: 加载中...")

        # 2. 内存详细信息
        memory_details = data.get('memory_details')
        if self.memory_details_label:
            if memory_details is not None and isinstance(memory_details, dict):
                mem_text = f"总: {memory_details.get('total_mb', '?')}MB, 可用: {memory_details.get('available_mb', '?')}MB, 已用: {memory_details.get('used_mb', '?')}MB"
                self.memory_details_label.setText(f"内存详情: {mem_text}")
            else:
                self.memory_details_label.setText("内存详情: 加载中...")

        # 3. 磁盘使用情况
        disk_info_list = data.get('disk') 
        if self.disk_label:
            if disk_info_list and isinstance(disk_info_list, list) and disk_info_list[0]: # Check disk_info_list[0] is not None
                main_disk = disk_info_list[0]
                if main_disk: # Ensure main_disk is not None
                    disk_text = f"{main_disk.get('mountpoint', '?')}: {main_disk.get('used_gb', '?')}GB / {main_disk.get('total_gb', '?')}GB ({main_disk.get('percent', '?')}%) "
                    self.disk_label.setText(f"磁盘: {disk_text}")
                else:
                    self.disk_label.setText("磁盘: 数据错误")
            else:
                self.disk_label.setText("磁盘: 加载中...")

        # 4. 网络信息 (总量)
        network_info = data.get('network') 
        if self.network_label:
            if network_info and isinstance(network_info, dict):
                net_text = f"已发送: {network_info.get('sent_mb', '?')}MB, 已接收: {network_info.get('recv_mb', '?')}MB"
                self.network_label.setText(f"网络: {net_text}")
            else:
                self.network_label.setText("网络: 加载中...")

        # 5. 磁盘IO速度
        disk_io_speed = data.get('disk_io') 
        if self.disk_io_label:
            if disk_io_speed and isinstance(disk_io_speed, dict):
                read_kbps = disk_io_speed.get('read_kbps', 0) # Changed from read_mbps
                write_kbps = disk_io_speed.get('write_kbps', 0) # Changed from write_mbps
                read_speed_str = f"{read_kbps/1024:.1f} MB/s" if read_kbps >= 1024 else f"{read_kbps:.1f} KB/s"
                write_speed_str = f"{write_kbps/1024:.1f} MB/s" if write_kbps >= 1024 else f"{write_kbps:.1f} KB/s"
                self.disk_io_label.setText(f"磁盘读写: 读 {read_speed_str}, 写 {write_speed_str}")
            else:
                self.disk_io_label.setText("磁盘IO: 加载中...")

        # 6. 网络速度
        network_speed = data.get('network_speed')
        if self.network_speed_label:
            if network_speed and isinstance(network_speed, dict):
                up_kbps = network_speed.get('upload_kbps', 0)
                down_kbps = network_speed.get('download_kbps', 0)
                up_speed_str = f"{up_kbps/1024:.1f} MB/s" if up_kbps >= 1024 else f"{up_kbps:.1f} KB/s"
                down_speed_str = f"{down_kbps/1024:.1f} MB/s" if down_kbps >= 1024 else f"{down_kbps:.1f} KB/s"
                self.network_speed_label.setText(f"网络速度: ↑ {up_speed_str}, ↓ {down_speed_str}")
            else:
                self.network_speed_label.setText("网络速度: 加载中...")

        # 7. GPU 信息 (如果可用)
        gpu_info = data.get('gpu')
        if self.gpu_label:
            if gpu_info and isinstance(gpu_info, list) and gpu_info: 
                gpu_texts = []
                for i, gpu_item in enumerate(gpu_info): # Renamed gpu to gpu_item
                    if isinstance(gpu_item, dict): # Ensure gpu_item is a dict
                        name = gpu_item.get('name', f'GPU{i}')
                        load = gpu_item.get('load_percent', gpu_item.get('load')) # Accommodate 'load' or 'load_percent'
                        mem_used = gpu_item.get('memory_used_mb', gpu_item.get('memoryUsed'))
                        mem_total = gpu_item.get('memory_total_mb', gpu_item.get('memoryTotal'))
                        temp = gpu_item.get('temperature_c', gpu_item.get('temperature'))
                        
                        text_parts = [name]
                        if load is not None: text_parts.append(f"负载:{float(load):.0f}%")
                        if mem_used is not None and mem_total is not None: text_parts.append(f"显存:{mem_used}/{mem_total}MB")
                        if temp is not None: text_parts.append(f"温度:{temp}°C")
                        gpu_texts.append(" - ".join(text_parts))
                    else:
                        gpu_texts.append(f"GPU{i}: invalid_data")

                self.gpu_label.setText("GPU: " + "; ".join(gpu_texts) if gpu_texts else "GPU: 无有效数据")
            elif gpu_info and isinstance(gpu_info, dict) and gpu_info.get("error"): # Handle GPUtil error case
                 self.gpu_label.setText(f"GPU: {gpu_info.get('error')}")
            else:
                self.gpu_label.setText("GPU: 加载中...")
        
        # --- Time related information ---
        # Extract time data from the incoming 'data' if present
        event_time_data = {}
        has_event_time_data = False
        if 'period' in data: # Check if key exists
            event_time_data['period'] = data.get('period')
            has_event_time_data = True
        if 'special_date' in data: # Check if key exists
            event_time_data['special_date'] = data.get('special_date')
            has_event_time_data = True
        if 'upcoming_dates' in data: # Check if key exists
            event_time_data['upcoming_dates'] = data.get('upcoming_dates')
            has_event_time_data = True

        if has_event_time_data:
            logger.debug(f"DEBUG_PANEL_DETAIL_TIME: _update_detailed_info has event time data: {event_time_data}")
            # Update self._time_data and then the UI via self.update_time_data -> _update_time_ui
            self.update_time_data(event_time_data) 
        else:
            # If event data doesn't have its own time info, but panel is expanded,
            # ensure the time UI reflects the latest self._time_data (which would be from a periodic refresh).
            if hasattr(self, '_time_data') and self.is_expanded: # self.is_expanded check might be redundant as _update_detailed_info is called when expanded
                 logger.debug(f"DEBUG_PANEL_DETAIL_TIME: No time data in event stats, ensuring UI reflects current self._time_data by calling _update_time_ui directly using: {self._time_data}")
                 self._update_time_ui(self._time_data) # Ensure consistency

        logger.debug(f"DEBUG_PANEL_DETAIL: _update_detailed_info FINISHED. disk_io_label='{self.disk_io_label.text() if self.disk_io_label else 'None'}'")

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
        # if not self.is_expanded:
        #     logger.debug("StatsPanel 未展开，仅存储时间数据不更新UI")
        #     return
        # Always update UI if expanded, when specific time data comes through this method.
        if self.is_expanded:
            logger.debug(f"StatsPanel is expanded, calling _update_time_ui with merged data: {self._time_data}")
            self._update_time_ui(self._time_data)
            
    def _update_time_ui(self, time_data: Dict[str, Any]): # Added type hint for time_data
        """更新时间UI显示

        Args:
            time_data: 时间数据字典 (should be self._time_data which is kept up-to-date)
        """
        logger.debug(f"_update_time_ui CALLED with: {time_data}")
        
        # 如果面板未展开，不更新UI - This check might be redundant if called only when expanded
        # However, keeping it for safety if called from other places without check.
        if not self.is_expanded:
            logger.debug("面板未展开，不更新时间UI from _update_time_ui")
            return
            
        # 更新时间段标签
        # period_name = time_data.get('period', DEFAULT_TIME_PERIOD_STR_LOCAL) # Use local default
        # Always use the period from time_data for UI consistency
        period_name = time_data.get('period')
        if self.time_period_label:
            if period_name:
                color = "#E0E0E0" # Default
                if period_name == TimePeriod.MORNING.name: color = "#FFE0A0"
                elif period_name == TimePeriod.NOON.name: color = "#FFCC80"
                elif period_name == TimePeriod.AFTERNOON.name: color = "#80D0FF"
                elif period_name == TimePeriod.EVENING.name: color = "#FFA080"
                elif period_name == TimePeriod.NIGHT.name: color = "#A080FF"
                self.time_period_label.setText(f"当前时段: {period_name}")
                self.time_period_label.setStyleSheet(f"color: {color}; font-size: 12px; font-weight: bold;")
                logger.debug(f"_update_time_ui: 已更新时间段标签: {period_name}")
            else:
                self.time_period_label.setText(f"当前时段: {DEFAULT_TIME_PERIOD_STR_LOCAL}")
                self.time_period_label.setStyleSheet(f"color: #E0E0E0; font-size: 12px; font-weight: bold;")
                logger.debug(f"_update_time_ui: 时间段信息为None或缺失, 设置为默认.")
        
        # 更新特殊日期标签
        special_date = time_data.get('special_date')
        if self.special_date_label:
            if special_date and isinstance(special_date, dict):
                special_date_text = f"{special_date.get('name', '未知')}: {special_date.get('description', '')}"
                self.special_date_label.setText(special_date_text)
                self.special_date_label.setStyleSheet("color: #FF8080; font-size: 11px;")
                self.special_date_label.show()
                logger.debug(f"_update_time_ui: 已更新特殊日期标签: {special_date.get('name')}")
            else:
                self.special_date_label.setText("今天没有特殊日期")
                self.special_date_label.setStyleSheet("color: #A0A0A0; font-size: 11px;")
                logger.debug("_update_time_ui: 今天没有特殊日期或数据格式不正确.")
        
        # 更新即将到来的特殊日期标签
        upcoming = time_data.get('upcoming_dates')
        if self.upcoming_dates_label:
            if upcoming and isinstance(upcoming, list):
                upcoming_text = "即将到来: "
                upcoming_text += ", ".join([f"{d.get('name', 'N/A')} ({d.get('date', 'N/A')})" for d in upcoming[:3] if isinstance(d, dict)])
                self.upcoming_dates_label.setText(upcoming_text)
                self.upcoming_dates_label.setStyleSheet("color: #80C080; font-size: 11px;")
                self.upcoming_dates_label.show()
                logger.debug(f"_update_time_ui: 已更新即将到来的特殊日期标签: {len(upcoming)}个")
            else:
                self.upcoming_dates_label.setText("近期没有特殊日期")
                self.upcoming_dates_label.setStyleSheet("color: #A0A0A0; font-size: 11px;")
                logger.debug("_update_time_ui: 近期没有特殊日期或数据格式不正确.")
        
        # 调整大小
        # self.adjustSize() # adjustSize might be too broad here; let the caller decide if needed.
        logger.debug("_update_time_ui 完成")

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
        if event.type == EventType.SYSTEM_STATS_UPDATED:
            stats_data_from_event = event.data
            if not isinstance(stats_data_from_event, dict):
                logger.error(f"StatsPanel received SYSTEM_STATS_UPDATED but event.data is not a dict: {type(stats_data_from_event)}. Event data: {str(stats_data_from_event)[:200]}")
                return

            logger.debug(f"StatsPanel received SYSTEM_STATS_UPDATED. Data keys: {list(stats_data_from_event.keys())}")
            
            self.update_data(stats_data_from_event) # This will call _update_detailed_info if expanded
            
            # REMOVED: Time data processing here, as it's handled by _update_detailed_info if panel is expanded
            # and if it receives stats_data_from_event which should contain time info.
            # Specific time events (TIME_PERIOD_CHANGED, SPECIAL_DATE) will call update_time_data directly.
            
            # logger.debug(f"StatsPanel 时间数据更新完成，面板展开状态: {self.is_expanded}")
        else:
            logger.warning(f"StatsPanel 收到非预期的事件类型: {event.type.name if event and hasattr(event, 'type') else 'Unknown event type'}")
    
    def handle_window_position_changed(self, event: Event):
        """处理 WindowPositionChangedEvent 事件，更新面板位置。"""
        if event.type == EventType.WINDOW_POSITION_CHANGED:
            actual_event_data = event.data # This should now be the WindowPositionChangedEvent instance
            if isinstance(actual_event_data, WindowPositionChangedEvent):
                parent_pos = actual_event_data.position
                parent_size = actual_event_data.size
                if parent_pos and parent_size: # Ensure they are not None
                    self.parent_window_pos = parent_pos
                    self.parent_window_size = parent_size
                    # logger.debug(f"StatsPanel: Parent window moved/resized to Pos:{parent_pos}, Size:{parent_size}")
                    if self.isVisible():
                        # logger.debug(f"StatsPanel: visible, updating position.")
                        self.update_position(parent_pos, parent_size)
                    else:
                        # logger.debug(f"StatsPanel: not visible, position will update on show.")
                        pass # Position will be updated when shown
                else:
                    logger.warning("handle_window_position_changed: Received None for parent_pos or parent_size.")                    
            else:
                logger.warning(f"handle_window_position_changed: event.data is not WindowPositionChangedEvent, type: {type(actual_event_data)}. Event: {event}")

    def update_position(self, parent_pos: QPoint, parent_size: QSize):
        """根据父窗口位置和大小，更新面板位置。
        
        Args:
            parent_pos: 父窗口位置
            parent_size: 父窗口大小
        """
        panel_size = self.sizeHint()
        
        # 获取当前显示器的几何信息
        # 修复多显示器支持：使用QApplication.screenAt方法获取鼠标所在的屏幕
        cursor_pos = QApplication.primaryScreen().geometry().center()  # 默认使用主屏幕
        parent_center = QPoint(parent_pos.x() + parent_size.width() // 2, 
                               parent_pos.y() + parent_size.height() // 2)
        
        # 获取包含父窗口中心的屏幕
        screen = QApplication.screenAt(parent_center)
        if not screen:
            # 如果找不到包含父窗口中心的屏幕，使用主屏幕
            screen = QApplication.primaryScreen()
        
        # 获取对应屏幕的可用几何信息
        screen_geometry = screen.availableGeometry()
        
        # 计算新位置
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
        
        # 避免频繁移动导致的闪烁，仅在位置变化较大时才更新
        current_pos = self.pos()
        if (abs(current_pos.x() - new_pos.x()) > 2 or 
            abs(current_pos.y() - new_pos.y()) > 2):
            # 移动面板
            self.move(new_pos)
            logger.debug(f"StatsPanel.update_position: 移动到 {new_pos}")
        else:
            logger.debug("StatsPanel.update_position: 位置变化很小，保持不变")
    
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