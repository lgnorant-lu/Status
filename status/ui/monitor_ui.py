"""
---------------------------------------------------------------
File name:                  monitor_ui.py
Author:                     Ignorant-lu
Date created:               2025/04/03
Description:                系统监控GUI界面
----------------------------------------------------------------

Changed history:            
                            2025/04/03: 初始创建;
----
"""

import logging
from typing import Dict, List, Any, Optional, Callable
import time

try:
    from PyQt6.QtCore import Qt, QTimer, QSize
    from PyQt6.QtGui import QFont, QColor, QPainter, QPixmap
    from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, 
                               QLabel, QTabWidget, QGroupBox, 
                               QProgressBar, QPushButton, QSplitter)
    HAS_PYQT = True
except ImportError:
    HAS_PYQT = False

from status.monitoring.monitor import SystemMonitor
from status.core.event_system import EventSystem, Event, EventType
from status.renderer.pyqt_renderer import PyQtRenderer
from status.renderer.primitives import Rectangle, Circle, Line
from status.renderer.drawable import Drawable


class MonitorGaugeWidget(QWidget):
    """自定义仪表盘小部件，用于显示CPU、内存等百分比指标"""
    
    def __init__(self, title: str, parent=None):
        """初始化仪表盘小部件
        
        Args:
            title: 仪表盘标题
            parent: 父级窗口
        """
        super().__init__(parent)
        if not HAS_PYQT:
            return
            
        self.title = title
        self.value = 0
        self.min_value = 0
        self.max_value = 100
        self.warning_threshold = 70
        self.critical_threshold = 90
        self.theme_color = QColor(120, 180, 240)  # 默认为蓝色
        self.setMinimumSize(150, 150)
        
    def setValue(self, value: float) -> None:
        """设置当前值
        
        Args:
            value: 当前值
        """
        self.value = max(self.min_value, min(value, self.max_value))
        self.update()
        
    def setThresholds(self, warning: float, critical: float) -> None:
        """设置阈值
        
        Args:
            warning: 警告阈值
            critical: 危险阈值
        """
        self.warning_threshold = warning
        self.critical_threshold = critical
        self.update()
        
    def setThemeColor(self, color: QColor) -> None:
        """设置主题颜色
        
        Args:
            color: 颜色对象
        """
        self.theme_color = color
        self.update()
        
    def paintEvent(self, event) -> None:
        """绘制事件"""
        if not HAS_PYQT:
            return
            
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # 计算绘制区域
        width = self.width()
        height = self.height()
        rect = min(width, height)
        margin = 10
        x = (width - rect) // 2 + margin
        y = (height - rect) // 2 + margin
        diameter = rect - 2 * margin
        
        # 绘制背景圆环
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(40, 40, 40))
        painter.drawEllipse(x, y, diameter, diameter)
        
        # 计算当前值对应的弧度
        start_angle = 135 * 16  # QPainter角度单位是1/16度
        span_angle = -270 * 16  # 负值表示顺时针方向
        current_angle = int(span_angle * (self.value - self.min_value) / (self.max_value - self.min_value))
        
        # 确定颜色
        if self.value >= self.critical_threshold:
            color = QColor(255, 50, 50)  # 红色
        elif self.value >= self.warning_threshold:
            color = QColor(255, 200, 50)  # 黄色
        else:
            color = self.theme_color
            
        # 绘制进度弧
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(color)
        painter.drawPie(x, y, diameter, diameter, start_angle, current_angle)
        
        # 绘制内圆（中空）
        inner_margin = diameter // 3
        painter.setBrush(QColor(30, 30, 30))
        painter.drawEllipse(x + inner_margin//2, y + inner_margin//2, 
                          diameter - inner_margin, diameter - inner_margin)
        
        # 绘制文本
        painter.setPen(Qt.GlobalColor.white)
        painter.setFont(QFont("Arial", diameter // 10, QFont.Weight.Bold))
        
        # 绘制标题
        painter.drawText(x, y, diameter, diameter // 4, 
                        Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignBottom, 
                        self.title)
                        
        # 绘制数值
        painter.setFont(QFont("Arial", diameter // 6, QFont.Weight.Bold))
        painter.setPen(color)
        painter.drawText(x, y + diameter // 6, diameter, diameter // 2, 
                        Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignCenter, 
                        f"{int(self.value)}%")


class MonitorChartWidget(QWidget):
    """自定义图表小部件，用于显示历史趋势"""
    
    def __init__(self, title: str, parent=None):
        """初始化图表小部件
        
        Args:
            title: 图表标题
            parent: 父级窗口
        """
        super().__init__(parent)
        if not HAS_PYQT:
            return
            
        self.title = title
        self.data_points = []
        self.max_points = 60  # 默认显示60个数据点
        self.min_value = 0
        self.max_value = 100
        self.warning_threshold = 70
        self.critical_threshold = 90
        self.theme_color = QColor(120, 180, 240)  # 默认为蓝色
        self.setMinimumSize(300, 150)
        
    def addDataPoint(self, value: float) -> None:
        """添加数据点
        
        Args:
            value: 数据值
        """
        self.data_points.append(value)
        if len(self.data_points) > self.max_points:
            self.data_points = self.data_points[-self.max_points:]
        self.update()
        
    def setThresholds(self, warning: float, critical: float) -> None:
        """设置阈值
        
        Args:
            warning: 警告阈值
            critical: 危险阈值
        """
        self.warning_threshold = warning
        self.critical_threshold = critical
        self.update()
        
    def setThemeColor(self, color: QColor) -> None:
        """设置主题颜色
        
        Args:
            color: 颜色对象
        """
        self.theme_color = color
        self.update()
        
    def paintEvent(self, event) -> None:
        """绘制事件"""
        if not HAS_PYQT:
            return
            
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # 计算绘制区域
        width = self.width()
        height = self.height()
        margin = 20
        chart_width = width - 2 * margin
        chart_height = height - 2 * margin
        
        # 绘制标题
        painter.setPen(Qt.GlobalColor.white)
        painter.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        painter.drawText(margin, 5, chart_width, 20, 
                        Qt.AlignmentFlag.AlignHCenter, self.title)
        
        # 绘制背景
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(40, 40, 40))
        painter.drawRect(margin, margin, chart_width, chart_height)
        
        # 绘制阈值线
        warning_y = margin + chart_height - (chart_height * self.warning_threshold / 100)
        critical_y = margin + chart_height - (chart_height * self.critical_threshold / 100)
        
        painter.setPen(QColor(255, 200, 50))  # 黄色警告线
        painter.drawLine(margin, warning_y, margin + chart_width, warning_y)
        
        painter.setPen(QColor(255, 50, 50))  # 红色危险线
        painter.drawLine(margin, critical_y, margin + chart_width, critical_y)
        
        # 如果没有数据，直接返回
        if not self.data_points:
            return
            
        # 绘制折线图
        point_width = chart_width / (self.max_points - 1) if self.max_points > 1 else chart_width
        points = []
        
        for i, value in enumerate(self.data_points):
            normalized_value = max(self.min_value, min(value, self.max_value))
            x = margin + (i * point_width)
            y = margin + chart_height - (chart_height * normalized_value / 100)
            points.append((x, y))
            
        # 设置线条颜色和宽度
        painter.setPen(self.theme_color)
        painter.setPen(painter.pen().color().lighter())
        
        # 绘制连线
        for i in range(1, len(points)):
            x1, y1 = points[i-1]
            x2, y2 = points[i]
            painter.drawLine(int(x1), int(y1), int(x2), int(y2))
            
        # 绘制点
        for x, y in points:
            painter.setPen(Qt.PenStyle.NoPen)
            
            # 根据值选择颜色
            value = self.data_points[points.index((x, y))]
            if value >= self.critical_threshold:
                painter.setBrush(QColor(255, 50, 50))  # 红色
            elif value >= self.warning_threshold:
                painter.setBrush(QColor(255, 200, 50))  # 黄色
            else:
                painter.setBrush(self.theme_color)
                
            painter.drawEllipse(int(x) - 3, int(y) - 3, 6, 6)


class MonitorUIWindow(QWidget):
    """系统监控UI窗口"""
    
    def __init__(self, parent=None):
        """初始化监控UI窗口
        
        Args:
            parent: 父级窗口
        """
        super().__init__(parent)
        
        self.logger = logging.getLogger(__name__)
        
        if not HAS_PYQT:
            self.logger.error("PyQt6未安装，无法创建系统监控UI")
            return
            
        # 获取系统监控器实例
        self.monitor = SystemMonitor()
        
        # 创建UI
        self._init_ui()
        
        # 启动更新定时器
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_ui)
        self.update_timer.start(1000)  # 每秒更新一次
        
        # 注册事件处理
        self.event_system = EventSystem()
        self.event_system.register_handler(
            EventType.SYSTEM_STATUS_UPDATE,
            self._handle_system_status_update
        )
        
        self.logger.info("系统监控UI已初始化")
        
    def _init_ui(self):
        """初始化UI布局"""
        # 设置窗口属性
        self.setWindowTitle("Hollow-ming 系统监控")
        self.resize(800, 600)
        
        # 创建主布局
        main_layout = QVBoxLayout()
        
        # 创建标题栏
        title_layout = QHBoxLayout()
        title_label = QLabel("Hollow-ming 系统监控")
        title_label.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        
        # 添加控制按钮
        start_button = QPushButton("启动监控")
        start_button.clicked.connect(self._start_monitor)
        stop_button = QPushButton("停止监控")
        stop_button.clicked.connect(self._stop_monitor)
        title_layout.addWidget(start_button)
        title_layout.addWidget(stop_button)
        
        main_layout.addLayout(title_layout)
        
        # 创建标签页
        tab_widget = QTabWidget()
        
        # 创建概览页
        overview_tab = QWidget()
        self._create_overview_tab(overview_tab)
        tab_widget.addTab(overview_tab, "概览")
        
        # 创建CPU页
        cpu_tab = QWidget()
        self._create_cpu_tab(cpu_tab)
        tab_widget.addTab(cpu_tab, "CPU")
        
        # 创建内存页
        memory_tab = QWidget()
        self._create_memory_tab(memory_tab)
        tab_widget.addTab(memory_tab, "内存")
        
        # 创建磁盘页
        disk_tab = QWidget()
        self._create_disk_tab(disk_tab)
        tab_widget.addTab(disk_tab, "磁盘")
        
        # 创建网络页
        network_tab = QWidget()
        self._create_network_tab(network_tab)
        tab_widget.addTab(network_tab, "网络")
        
        # 添加标签页到主布局
        main_layout.addWidget(tab_widget)
        
        # 创建状态栏
        status_layout = QHBoxLayout()
        self.status_label = QLabel("系统监控未启动")
        status_layout.addWidget(self.status_label)
        status_layout.addStretch()
        
        # 添加时间标签
        self.time_label = QLabel(time.strftime("%Y-%m-%d %H:%M:%S"))
        status_layout.addWidget(self.time_label)
        
        main_layout.addLayout(status_layout)
        
        # 设置主布局
        self.setLayout(main_layout)
        
        # 存储UI组件引用
        self.tabs = tab_widget
        
    def _create_overview_tab(self, tab):
        """创建概览标签页
        
        Args:
            tab: 标签页窗口
        """
        layout = QVBoxLayout()
        
        # 创建顶部仪表盘区域
        gauges_layout = QHBoxLayout()
        
        # CPU仪表盘
        self.cpu_gauge = MonitorGaugeWidget("CPU")
        self.cpu_gauge.setThemeColor(QColor(120, 180, 240))  # 蓝色
        gauges_layout.addWidget(self.cpu_gauge)
        
        # 内存仪表盘
        self.memory_gauge = MonitorGaugeWidget("内存")
        self.memory_gauge.setThemeColor(QColor(180, 120, 240))  # 紫色
        gauges_layout.addWidget(self.memory_gauge)
        
        # 磁盘仪表盘
        self.disk_gauge = MonitorGaugeWidget("磁盘")
        self.disk_gauge.setThemeColor(QColor(240, 180, 120))  # 橙色
        gauges_layout.addWidget(self.disk_gauge)
        
        # 网络仪表盘（可选）
        self.network_gauge = MonitorGaugeWidget("网络")
        self.network_gauge.setThemeColor(QColor(120, 240, 180))  # 绿色
        gauges_layout.addWidget(self.network_gauge)
        
        layout.addLayout(gauges_layout)
        
        # 创建图表区域
        charts_layout = QHBoxLayout()
        
        # CPU历史图表
        self.cpu_chart = MonitorChartWidget("CPU历史")
        self.cpu_chart.setThemeColor(QColor(120, 180, 240))  # 蓝色
        charts_layout.addWidget(self.cpu_chart)
        
        # 内存历史图表
        self.memory_chart = MonitorChartWidget("内存历史")
        self.memory_chart.setThemeColor(QColor(180, 120, 240))  # 紫色
        charts_layout.addWidget(self.memory_chart)
        
        layout.addLayout(charts_layout)
        
        # 添加系统基本信息
        info_group = QGroupBox("系统信息")
        info_layout = QVBoxLayout()
        
        self.system_info_label = QLabel("加载中...")
        info_layout.addWidget(self.system_info_label)
        
        info_group.setLayout(info_layout)
        layout.addWidget(info_group)
        
        # 设置标签页布局
        tab.setLayout(layout)
        
    def _create_cpu_tab(self, tab):
        """创建CPU标签页
        
        Args:
            tab: 标签页窗口
        """
        # 将在具体实现中添加
        layout = QVBoxLayout()
        label = QLabel("CPU详细信息将在下一版本中实现...")
        layout.addWidget(label)
        tab.setLayout(layout)
        
    def _create_memory_tab(self, tab):
        """创建内存标签页
        
        Args:
            tab: 标签页窗口
        """
        # 将在具体实现中添加
        layout = QVBoxLayout()
        label = QLabel("内存详细信息将在下一版本中实现...")
        layout.addWidget(label)
        tab.setLayout(layout)
        
    def _create_disk_tab(self, tab):
        """创建磁盘标签页
        
        Args:
            tab: 标签页窗口
        """
        # 将在具体实现中添加
        layout = QVBoxLayout()
        label = QLabel("磁盘详细信息将在下一版本中实现...")
        layout.addWidget(label)
        tab.setLayout(layout)
        
    def _create_network_tab(self, tab):
        """创建网络标签页
        
        Args:
            tab: 标签页窗口
        """
        # 将在具体实现中添加
        layout = QVBoxLayout()
        label = QLabel("网络详细信息将在下一版本中实现...")
        layout.addWidget(label)
        tab.setLayout(layout)
        
    def _handle_system_status_update(self, event: Event) -> None:
        """处理系统状态更新事件
        
        Args:
            event: 系统状态更新事件
        """
        if event.event_type != EventType.SYSTEM_STATUS_UPDATE:
            return
            
        # UI更新将在UI线程中进行，这里只记录信息
        self.logger.debug("收到系统状态更新事件")
        
    def update_ui(self):
        """更新UI显示"""
        if not self.monitor.is_running:
            self.status_label.setText("系统监控未启动")
            return
            
        try:
            # 更新状态栏
            self.status_label.setText("系统监控运行中")
            self.time_label.setText(time.strftime("%Y-%m-%d %H:%M:%S"))
            
            # 获取最新系统状态
            status = self.monitor.get_status()
            metrics = status.get("metrics", {})
            
            # 更新概览页
            self._update_overview(metrics)
        except Exception as e:
            self.logger.error(f"更新UI失败: {e}")
        
    def _update_overview(self, metrics: Dict[str, Any]):
        """更新概览页信息
        
        Args:
            metrics: 系统指标数据
        """
        # 更新CPU信息
        cpu_data = metrics.get("cpu", {})
        if "percent_overall" in cpu_data:
            self.cpu_gauge.setValue(cpu_data["percent_overall"])
            self.cpu_chart.addDataPoint(cpu_data["percent_overall"])
        
        # 更新内存信息
        memory_data = metrics.get("memory", {})
        if "percent" in memory_data:
            self.memory_gauge.setValue(memory_data["percent"])
            self.memory_chart.addDataPoint(memory_data["percent"])
        
        # 更新磁盘信息
        disk_data = metrics.get("disk", {})
        if "partitions" in disk_data:
            # 简单处理：使用第一个分区的使用率
            for partition in disk_data["partitions"]:
                if partition.get("mountpoint") == "/" or partition.get("mountpoint") == "C:\\":
                    usage = partition.get("usage", {})
                    if "percent" in usage:
                        self.disk_gauge.setValue(usage["percent"])
                        break
        
        # 更新网络信息（这里简化处理，实际应用中需要计算网络使用率）
        network_data = metrics.get("network", {})
        if "interfaces" in network_data:
            # 简单示例：设置一个模拟值
            # 实际应用中应计算实际网络使用率
            self.network_gauge.setValue(30)  # 设置为30%作为示例
        
        # 更新系统信息标签
        system_info = []
        basic_info = self.monitor.system_info.get_basic_info()
        
        if basic_info:
            system_info.append(f"系统: {basic_info.get('system')} {basic_info.get('release')}")
            system_info.append(f"平台: {basic_info.get('platform')}")
            system_info.append(f"处理器: {basic_info.get('processor')}")
            system_info.append(f"CPU核心: {basic_info.get('cpu_count_physical')} 物理 / {basic_info.get('cpu_count_logical')} 逻辑")
            system_info.append(f"主机名: {basic_info.get('hostname')}")
            
        self.system_info_label.setText("\n".join(system_info))
        
    def _start_monitor(self):
        """启动监控"""
        if not self.monitor.is_running:
            result = self.monitor.start()
            if result:
                self.status_label.setText("系统监控已启动")
                self.logger.info("系统监控已启动")
            else:
                self.status_label.setText("启动系统监控失败")
                self.logger.error("启动系统监控失败")
                
    def _stop_monitor(self):
        """停止监控"""
        if self.monitor.is_running:
            result = self.monitor.stop()
            if result:
                self.status_label.setText("系统监控已停止")
                self.logger.info("系统监控已停止")
            else:
                self.status_label.setText("停止系统监控失败")
                self.logger.error("停止系统监控失败")
                
    def closeEvent(self, event):
        """窗口关闭事件
        
        Args:
            event: 关闭事件
        """
        # 停止定时器
        if hasattr(self, 'update_timer'):
            self.update_timer.stop()
            
        # 注销事件处理器
        if hasattr(self, 'event_system'):
            self.event_system.unregister_handler(
                EventType.SYSTEM_STATUS_UPDATE,
                self._handle_system_status_update
            )
            
        # 停止监控
        if hasattr(self, 'monitor') and self.monitor.is_running:
            self.monitor.stop()
            
        self.logger.info("系统监控UI已关闭")
        super().closeEvent(event) 