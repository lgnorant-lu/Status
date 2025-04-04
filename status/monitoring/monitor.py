"""
---------------------------------------------------------------
File name:                  monitor.py
Author:                     Ignorant-lu
Date created:               2025/04/03
Description:                系统监控器主类，作为监控模块的入口点
----------------------------------------------------------------

Changed history:            
                            2025/04/03: 初始创建;
----
"""

import logging
import threading
import time
from typing import Dict, Any, Optional, List, Union, Callable

from status.core.event_system import EventSystem, Event, EventType
from status.monitoring.system_info import SystemInfo
from status.monitoring.data_process import DataProcessor
from status.monitoring.ui_controller import MonitorUIController


class SystemMonitor:
    """系统监控器主类，作为监控模块的入口点"""
    
    _instance = None
    
    def __new__(cls, *args, **kwargs):
        """实现单例模式"""
        if cls._instance is None:
            cls._instance = super(SystemMonitor, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self, update_interval: float = 1.0):
        """初始化系统监控器
        
        Args:
            update_interval: 系统信息更新间隔（秒）
        """
        # 单例模式只初始化一次
        if self._initialized:
            return
            
        self.logger = logging.getLogger(__name__)
        self.logger.info("初始化系统监控器")
        
        # 更新间隔
        self.update_interval = update_interval
        
        # 监控状态
        self.is_running = False
        
        # 获取各个模块的单例实例
        self.system_info = SystemInfo(update_interval=update_interval)
        self.data_processor = DataProcessor()
        self.ui_controller = MonitorUIController()
        
        # 事件系统
        self.event_system = EventSystem()
        
        self._initialized = True
    
    def start(self) -> bool:
        """启动系统监控
        
        Returns:
            是否成功启动
        """
        if self.is_running:
            self.logger.warning("系统监控已在运行")
            return False
            
        try:
            # 启动系统信息自动更新
            result = self.system_info.start_auto_update()
            if not result:
                self.logger.error("启动系统信息自动更新失败")
                return False
                
            self.is_running = True
            self.logger.info(f"系统监控已启动，更新间隔：{self.update_interval}秒")
            
            # 发送系统监控启动事件
            self._send_monitor_event("start")
            
            return True
        except Exception as e:
            self.logger.error(f"启动系统监控失败: {e}")
            return False
    
    def stop(self) -> bool:
        """停止系统监控
        
        Returns:
            是否成功停止
        """
        if not self.is_running:
            self.logger.warning("系统监控未在运行")
            return False
            
        try:
            # 停止系统信息自动更新
            result = self.system_info.stop_auto_update()
            if not result:
                self.logger.error("停止系统信息自动更新失败")
                return False
                
            self.is_running = False
            self.logger.info("系统监控已停止")
            
            # 发送系统监控停止事件
            self._send_monitor_event("stop")
            
            return True
        except Exception as e:
            self.logger.error(f"停止系统监控失败: {e}")
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
    
    def get_status(self) -> Dict[str, Any]:
        """获取当前系统状态
        
        Returns:
            当前系统状态数据
        """
        if not self.is_running:
            self.logger.warning("系统监控未在运行，返回的状态可能不是最新的")
            
        latest_status = self.ui_controller.get_latest_status()
        if not latest_status:
            # 如果没有缓存的状态，强制更新一次
            metrics = self.system_info.update_metrics()
            latest_status = {
                "timestamp": time.time(),
                "metrics": metrics
            }
            
        return latest_status
    
    def get_alerts(self, count: int = None) -> List[Dict[str, Any]]:
        """获取告警历史
        
        Args:
            count: 获取的告警记录数量，None表示获取所有告警记录
            
        Returns:
            告警历史列表
        """
        return self.ui_controller.get_alerts(count)
    
    def clear_alerts(self) -> None:
        """清空告警历史"""
        self.ui_controller.clear_alerts()
        self.logger.info("已清空告警历史")
    
    def set_threshold(self, threshold_name: str, value: float) -> bool:
        """设置告警阈值
        
        Args:
            threshold_name: 阈值名称
            value: 阈值值
            
        Returns:
            是否设置成功
        """
        return self.data_processor.set_threshold(threshold_name, value)
    
    def get_threshold(self, threshold_name: str) -> Optional[float]:
        """获取告警阈值
        
        Args:
            threshold_name: 阈值名称
            
        Returns:
            阈值值，如果不存在则返回None
        """
        return self.data_processor.get_threshold(threshold_name)
    
    def get_all_thresholds(self) -> Dict[str, float]:
        """获取所有告警阈值
        
        Returns:
            包含所有告警阈值的字典
        """
        return self.data_processor.get_all_thresholds()
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计数据
        
        Returns:
            包含统计数据的字典
        """
        return self.data_processor.get_stats()
    
    def get_history(self, metric_type: str, count: int = None) -> List[Dict[str, Any]]:
        """获取历史数据
        
        Args:
            metric_type: 指标类型（cpu, memory, disk, network, battery）
            count: 获取的历史记录数量，None表示获取所有历史记录
            
        Returns:
            历史数据列表
        """
        return self.data_processor.get_history(metric_type, count)
    
    def get_history_with_timestamps(self, metric_type: str, count: int = None) -> List[Dict[str, Any]]:
        """获取带时间戳的历史数据
        
        Args:
            metric_type: 指标类型（cpu, memory, disk, network, battery）
            count: 获取的历史记录数量，None表示获取所有历史记录
            
        Returns:
            包含(时间戳, 数据)元组的列表
        """
        return self.data_processor.get_history_with_timestamps(metric_type, count)
    
    def register_ui_component(self, component_id: str, component: Any) -> bool:
        """注册UI组件
        
        Args:
            component_id: 组件ID
            component: UI组件对象
            
        Returns:
            是否注册成功
        """
        return self.ui_controller.register_component(component_id, component)
    
    def unregister_ui_component(self, component_id: str) -> bool:
        """注销UI组件
        
        Args:
            component_id: 组件ID
            
        Returns:
            是否注销成功
        """
        return self.ui_controller.unregister_component(component_id)
    
    def register_custom_processor(self, name: str, processor: Callable) -> bool:
        """注册自定义数据处理器
        
        Args:
            name: 处理器名称
            processor: 处理器函数
            
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
    
    def _send_monitor_event(self, action: str) -> None:
        """发送系统监控事件
        
        Args:
            action: 动作类型（start, stop等）
        """
        try:
            event = Event(
                event_type=EventType.SYSTEM_MONITOR_STATE,
                sender=self.__class__.__name__,
                data={
                    "action": action,
                    "timestamp": time.time(),
                    "is_running": self.is_running,
                    "update_interval": self.update_interval
                }
            )
            self.event_system.dispatch_event(event)
        except Exception as e:
            self.logger.error(f"发送系统监控事件失败: {e}") 