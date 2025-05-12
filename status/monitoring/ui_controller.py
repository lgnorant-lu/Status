"""
---------------------------------------------------------------
File name:                  ui_controller.py
Author:                     Ignorant-lu
Date created:               2025/04/04
Description:                系统监控UI控制器，管理监控界面显示与更新
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
from typing import Dict, List, Any, Optional, Union, cast

from status.core.event_system import EventSystem, Event, EventType

class MonitorUIController:
    """系统监控UI控制器，负责管理监控界面的显示与更新"""
    
    _instance = None
    _initialized: bool = False
    
    @classmethod
    def get_instance(cls) -> 'MonitorUIController':
        """获取单例实例"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def __new__(cls, *args, **kwargs):
        """创建单例实例"""
        if cls._instance is None:
            cls._instance = super(MonitorUIController, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """初始化UI控制器"""
        # 单例模式只初始化一次
        if self._initialized:
            return
            
        self.logger = logging.getLogger(__name__)
        self.logger.info("初始化系统监控UI控制器")
        
        # 事件系统
        self.event_system = EventSystem()
        
        # 注册系统状态更新事件处理器
        self.event_system.register_handler(
            EventType.SYSTEM_STATUS_UPDATE,
            self._handle_system_status_update
        )
        
        # UI组件注册表
        self.ui_components: Dict[str, Any] = {}
        
        # 最近一次系统状态
        self.latest_status: Optional[Dict[str, Any]] = None
        
        # 告警历史
        self.alerts: List[Dict[str, Any]] = []
        self.max_alerts = 100  # 最多保留100条告警记录
        
        # 线程锁
        self.lock = threading.RLock()
        
        self._initialized = True
    
    def _handle_system_status_update(self, event: Event) -> None:
        """处理系统状态更新事件
        
        Args:
            event: 系统状态更新事件
        """
        if event.type != EventType.SYSTEM_STATUS_UPDATE:
            return
            
        try:
            with self.lock:
                # 保存最新状态
                self.latest_status = event.data
                
                # 检查是否为告警事件
                if event.data.get("alert"):
                    self._handle_alert(event.data)
                
                # 通知所有UI组件更新
                self._update_ui_components(event.data)
        except Exception as e:
            self.logger.error(f"处理系统状态更新事件失败: {e}")
    
    def _handle_alert(self, alert_data: Dict[str, Any]) -> None:
        """处理告警事件
        
        Args:
            alert_data: 告警数据
        """
        try:
            # 添加到告警历史
            self.alerts.append(alert_data)
            
            # 控制告警历史数量
            if len(self.alerts) > self.max_alerts:
                self.alerts = self.alerts[-self.max_alerts:]
                
            self.logger.debug(f"收到系统告警: {alert_data.get('message')}")
        except Exception as e:
            self.logger.error(f"处理告警事件失败: {e}")
    
    def _update_ui_components(self, status_data: Dict[str, Any]) -> None:
        """更新所有UI组件
        
        Args:
            status_data: 系统状态数据
        """
        for component_id, component in self.ui_components.items():
            try:
                if hasattr(component, "update") and callable(component.update):
                    component.update(status_data)
            except Exception as e:
                self.logger.error(f"更新UI组件 '{component_id}' 失败: {e}")
    
    def register_component(self, component_id: str, component: Any) -> bool:
        """注册UI组件
        
        Args:
            component_id: 组件ID
            component: UI组件对象，必须实现update方法
            
        Returns:
            是否注册成功
        """
        if not hasattr(component, "update") or not callable(component.update):
            self.logger.error(f"无法注册UI组件 '{component_id}': 组件必须实现update方法")
            return False
            
        with self.lock:
            if component_id in self.ui_components:
                self.logger.warning(f"UI组件 '{component_id}' 已存在，将被覆盖")
                
            self.ui_components[component_id] = component
            self.logger.info(f"已注册UI组件: {component_id}")
            
            # 如果有最新状态，立即更新组件
            if self.latest_status:
                try:
                    component.update(self.latest_status)
                except Exception as e:
                    self.logger.error(f"初始更新UI组件 '{component_id}' 失败: {e}")
                    
            return True
    
    def unregister_component(self, component_id: str) -> bool:
        """注销UI组件
        
        Args:
            component_id: 组件ID
            
        Returns:
            是否注销成功
        """
        with self.lock:
            if component_id not in self.ui_components:
                self.logger.warning(f"UI组件 '{component_id}' 不存在")
                return False
                
            del self.ui_components[component_id]
            self.logger.info(f"已注销UI组件: {component_id}")
            return True
    
    def get_component(self, component_id: str) -> Optional[Any]:
        """获取UI组件
        
        Args:
            component_id: 组件ID
            
        Returns:
            UI组件对象，如果不存在则返回None
        """
        return self.ui_components.get(component_id)
    
    def get_all_components(self) -> Dict[str, Any]:
        """获取所有UI组件
        
        Returns:
            包含所有UI组件的字典
        """
        return self.ui_components.copy()
    
    def get_latest_status(self) -> Dict[str, Any]:
        """获取最新系统状态
        
        Returns:
            最新系统状态数据
        """
        return self.latest_status.copy() if self.latest_status else {}
    
    def get_alerts(self, count: Optional[int] = None) -> List[Dict[str, Any]]:
        """获取告警历史
        
        Args:
            count: 获取的告警记录数量，None表示获取所有告警记录
            
        Returns:
            告警历史列表
        """
        with self.lock:
            if count is None:
                return self.alerts.copy()
            else:
                return self.alerts[-count:]
    
    def clear_alerts(self) -> None:
        """清空告警历史"""
        with self.lock:
            self.alerts.clear()
            self.logger.info("已清空告警历史")
    
    def set_max_alerts(self, max_alerts: int) -> None:
        """设置最大告警记录数
        
        Args:
            max_alerts: 最大告警记录数
        """
        if max_alerts <= 0:
            self.logger.error("最大告警记录数必须大于0")
            return
            
        with self.lock:
            self.max_alerts = max_alerts
            
            # 控制现有告警历史数量
            if len(self.alerts) > self.max_alerts:
                self.alerts = self.alerts[-self.max_alerts:]
                
            self.logger.info(f"已设置最大告警记录数: {max_alerts}") 