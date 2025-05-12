"""
---------------------------------------------------------------
File name:                  monitor.py
Author:                     Ignorant-lu
Date created:               2025/04/04
Description:                系统监控器，整合系统信息收集和数据处理功能
----------------------------------------------------------------

Changed history:            
                            2025/04/04: 初始创建;
                            2025/05/15: 修复_initialized类型问题;
----
"""

import os
import time
import logging
import threading
from typing import Dict, List, Any, Optional, Tuple, Callable, Union, cast

from status.core.event_system import EventSystem, Event, EventType
from status.monitoring.system_info import SystemInfo
from status.monitoring.data_process import DataProcessor
from status.monitoring.ui_controller import MonitorUIController

class SystemMonitor:
    """系统监控器，整合系统信息收集和数据处理功能"""
    
    _instance = None
    _initialized: bool = False
    
    @classmethod
    def get_instance(cls) -> 'SystemMonitor':
        """获取单例实例"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def __new__(cls, *args, **kwargs):
        """创建单例实例"""
        if cls._instance is None:
            cls._instance = super(SystemMonitor, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self, update_interval: float = 1.0, max_history_size: int = 60):
        """初始化系统监控器
        
        Args:
            update_interval: 系统信息更新间隔（秒）
            max_history_size: 历史数据最大记录数
        """
        # 单例模式只初始化一次
        if self._initialized:
            return
            
        self.logger = logging.getLogger(__name__)
        self.logger.info("初始化系统监控器")
        
        # 创建系统信息收集器和数据处理器
        self.system_info = SystemInfo(update_interval)
        self.data_processor = DataProcessor(max_history_size)
        self.ui_controller = MonitorUIController()
        
        # 监控器配置
        self.update_interval = update_interval
        self.is_monitoring = False
        
        # 事件系统
        self.event_system = EventSystem()
        
        self._initialized = True
    
    def start_monitoring(self) -> bool:
        """启动系统监控
        
        Returns:
            是否成功启动
        """
        if self.is_monitoring:
            self.logger.warning("系统监控已在运行中")
            return False
            
            # 启动系统信息自动更新
        if self.system_info.start_auto_update():
            self.is_monitoring = True
            self.logger.info("系统监控已启动")
            
            # 发送监控状态变更事件
            self._send_state_event(True)
            return True
        else:
            self.logger.error("启动系统监控失败")
            return False
    
    def stop_monitoring(self) -> bool:
        """停止系统监控
        
        Returns:
            是否成功停止
        """
        if not self.is_monitoring:
            self.logger.warning("系统监控未在运行")
            return False
            
            # 停止系统信息自动更新
        if self.system_info.stop_auto_update():
            self.is_monitoring = False
            self.logger.info("系统监控已停止")
            
            # 发送监控状态变更事件
            self._send_state_event(False)
            return True
        else:
            self.logger.error("停止系统监控失败")
            return False
    
    def set_update_interval(self, interval: float) -> None:
        """设置更新间隔
        
        Args:
            interval: 更新间隔（秒）
        """
        if interval <= 0:
            self.logger.error("更新间隔必须大于0")
            return
            
        self.update_interval = interval
        self.system_info.set_update_interval(interval)
        self.logger.info(f"系统监控更新间隔已设置为 {interval} 秒")
    
    def get_current_metrics(self) -> Dict[str, Any]:
        """获取当前系统指标
        
        Returns:
            当前系统指标数据
        """
        return self.system_info.update_metrics()
    
    def get_system_info(self) -> Dict[str, Any]:
        """获取系统基本信息
        
        Returns:
            系统基本信息
        """
        return self.system_info.get_basic_info()
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计数据
        
        Returns:
            统计数据
        """
        return self.data_processor.get_stats()
    
    def get_history(self, metric_type: str, count: Optional[int] = None) -> List[Dict[str, Any]]:
        """获取历史数据
        
        Args:
            metric_type: 指标类型
            count: 返回的条目数量，None表示全部
            
        Returns:
            历史数据列表
        """
        return self.data_processor.get_history(metric_type, count)
    
    def get_history_with_timestamps(self, metric_type: str, count: Optional[int] = None) -> List[Tuple[float, Dict[str, Any]]]:
        """获取带时间戳的历史数据
        
        Args:
            metric_type: 指标类型
            count: 返回的条目数量，None表示全部
            
        Returns:
            (时间戳, 数据)元组列表
        """
        return self.data_processor.get_history_with_timestamps(metric_type, count)
    
    def get_cpu_history(self, count: Optional[int] = None) -> List[Dict[str, Any]]:
        """获取CPU历史数据
        
        Args:
            count: 返回的条目数量，None表示全部
            
        Returns:
            CPU历史数据列表
        """
        return self.get_history("cpu", count)
    
    def get_memory_history(self, count: Optional[int] = None) -> List[Dict[str, Any]]:
        """获取内存历史数据
        
        Args:
            count: 返回的条目数量，None表示全部
            
        Returns:
            内存历史数据列表
        """
        return self.get_history("memory", count)
    
    def get_cpu_usage_trend(self) -> List[Dict[str, Any]]:
        """获取CPU使用率趋势数据（包含时间戳）
        
        Returns:
            CPU使用率趋势数据列表
        """
        # 转换类型以满足返回值类型要求
        data = self.get_history_with_timestamps("cpu")
        return [{"timestamp": ts, "data": values} for ts, values in data]
    
    def set_threshold(self, threshold_name: str, value: float) -> bool:
        """设置监控阈值
        
        Args:
            threshold_name: 阈值名称
            value: 阈值值
            
        Returns:
            是否设置成功
        """
        return self.data_processor.set_threshold(threshold_name, value)
    
    def get_threshold(self, threshold_name: str) -> Optional[float]:
        """获取监控阈值
        
        Args:
            threshold_name: 阈值名称
            
        Returns:
            阈值值
        """
        return self.data_processor.get_threshold(threshold_name)
    
    def get_all_thresholds(self) -> Dict[str, float]:
        """获取所有监控阈值
        
        Returns:
            所有阈值的字典
        """
        return self.data_processor.get_all_thresholds()
    
    def _send_state_event(self, is_running: bool) -> None:
        """发送监控状态变更事件
        
        Args:
            is_running: 是否正在运行
        """
        try:
            event_data = {
                "is_running": is_running,
                "update_interval": self.update_interval,
                "timestamp": time.time(),
            }
            
            # 使用枚举类型
            self.event_system.dispatch_event(
                event_type=EventType.SYSTEM_MONITOR_STATE,
                sender=self,
                data=event_data
            )
        except Exception as e:
            self.logger.error(f"发送监控状态事件失败: {e}")
    
    def get_status(self) -> Dict[str, Any]:
        """获取当前系统状态
            
        Returns:
            当前系统状态数据
        """
        if not self.is_monitoring:
            self.logger.warning("系统监控未在运行，返回的状态可能不是最新的")
            
        status = {
            "system_info": self.system_info.get_basic_info(),
            "metrics": self.system_info.update_metrics(),
            "stats": self.data_processor.get_stats(),
            "monitoring": self.is_monitoring,
            "timestamp": time.time(),
        }
        
        return status
    
    def get_alerts(self, count: Optional[int] = None) -> List[Dict[str, Any]]:
        """获取告警历史
        
        Args:
            count: 获取的告警记录数量，None表示获取所有告警记录
            
        Returns:
            告警历史列表
        """
        if self.ui_controller:
            return self.ui_controller.get_alerts(count)
        return []
    
    def clear_alerts(self) -> None:
        """清空告警历史"""
        if self.ui_controller:
            self.ui_controller.clear_alerts()
            self.logger.info("已清空告警历史")
    
    def register_ui_component(self, component_id: str, component: Any) -> bool:
        """注册UI组件
        
        Args:
            component_id: 组件ID
            component: UI组件对象
            
        Returns:
            是否注册成功
        """
        if self.ui_controller:
            return self.ui_controller.register_component(component_id, component)
        return False
    
    def unregister_ui_component(self, component_id: str) -> bool:
        """注销UI组件
        
        Args:
            component_id: 组件ID
            
        Returns:
            是否注销成功
        """
        if self.ui_controller:
            return self.ui_controller.unregister_component(component_id)
        return False
    
    def register_custom_processor(self, name: str, processor: Callable[[float, Dict[str, Any], Dict[str, Any], Dict[str, Any]], None]) -> bool:
        """注册自定义数据处理器
        
        Args:
            name: 处理器名称
            processor: 处理函数
            
        Returns:
            是否注册成功
        """
        return self.data_processor.register_custom_processor(name, processor)
    
    def unregister_custom_processor(self, name: str) -> bool:
        """注销自定义数据处理器
        
        Args:
            name: 处理器名称
            
        Returns:
            是否注销成功
        """
        return self.data_processor.unregister_custom_processor(name)