"""
---------------------------------------------------------------
File name:                  system_state_adapter.py
Author:                     Ignorant-lu
Date created:               2025/05/13
Description:                系统状态适配器，连接系统监控和宠物状态机
----------------------------------------------------------------

Changed history:            
                            2025/05/13: 初始创建;
----
"""

import logging
from typing import Dict, Any, Optional

from status.core.component_base import ComponentBase
from status.core.events import EventManager, SystemStatsUpdatedEvent, Event, EventType
from status.behavior.pet_state_machine import PetStateMachine
from status.behavior.pet_state import PetState

class SystemStateAdapter(ComponentBase):
    """系统状态适配器，监听系统统计数据事件并更新宠物状态机"""
    
    def __init__(self, pet_state_machine: PetStateMachine):
        """初始化适配器
        
        Args:
            pet_state_machine: 宠物状态机实例
        """
        super().__init__()
        self.logger = logging.getLogger("Status.Behavior.SystemStateAdapter")
        self.event_manager = EventManager.get_instance()
        
        self.pet_state_machine = pet_state_machine
        
        # 上次更新的资源使用率，用于记录日志
        self._last_cpu_usage = 0.0
        self._last_memory_usage = 0.0
        self._last_gpu_usage = 0.0
        self._last_disk_usage = 0.0
        self._last_network_usage = 0.0
    
    def _initialize(self) -> bool:
        """初始化适配器
        
        Returns:
            bool: 初始化是否成功
        """
        # 注册事件监听器，监听系统统计数据更新事件
        self.event_manager.register_handler(EventType.SYSTEM_STATS_UPDATED, self._on_system_stats_updated)
        
        self.logger.info("系统状态适配器初始化完成")
        return True
    
    def _update(self, dt: float) -> None:
        """更新适配器
        
        Args:
            dt: 时间增量（秒）
        """
        # 大部分逻辑通过事件处理，此处不需要额外操作
        pass
    
    def _on_system_stats_updated(self, event: Event) -> None:
        """处理系统统计数据更新事件
        
        Args:
            event: 系统统计数据更新事件
        """
        # 确保事件是SystemStatsUpdatedEvent类型
        if not isinstance(event, SystemStatsUpdatedEvent):
            self.logger.warning(f"收到非预期的事件类型: {type(event)}")
            return
            
        # 提取系统资源使用数据
        stats_data = event.stats_data
        
        # 获取CPU使用率
        cpu_usage = stats_data.get("cpu_usage", 0.0)
        
        # 获取内存使用率
        memory_usage = stats_data.get("memory_usage", 0.0)
        
        # 获取GPU使用率（如果有）
        gpu_usage = stats_data.get("gpu_usage", 0.0)
        
        # 获取磁盘使用率（如果有）
        disk_usage = stats_data.get("disk_usage", 0.0)
        
        # 获取网络使用率（如果有）
        network_usage = stats_data.get("network_usage", 0.0)
        
        # 检查CPU和内存数据有效性
        if not isinstance(cpu_usage, (int, float)) or not isinstance(memory_usage, (int, float)):
            self.logger.warning(f"系统统计数据格式无效: CPU={cpu_usage}, Memory={memory_usage}")
            return
            
        # 记录变化较大的数据（减少日志量）
        if abs(cpu_usage - self._last_cpu_usage) > 5.0 or abs(memory_usage - self._last_memory_usage) > 5.0:
            self.logger.debug(f"系统负载: CPU={cpu_usage:.1f}%, Memory={memory_usage:.1f}%")
            
            # 记录GPU使用率（如果有）
            if gpu_usage > 0:
                self.logger.debug(f"GPU使用率: {gpu_usage:.1f}%")
            
            # 记录磁盘使用率（如果有）
            if disk_usage > 0:
                self.logger.debug(f"磁盘使用率: {disk_usage:.1f}%")
            
            # 记录网络使用率（如果有）
            if network_usage > 0:
                self.logger.debug(f"网络使用率: {network_usage:.1f}%")
            
            self._last_cpu_usage = cpu_usage
            self._last_memory_usage = memory_usage
            self._last_gpu_usage = gpu_usage
            self._last_disk_usage = disk_usage
            self._last_network_usage = network_usage
            
        # 更新宠物状态机
        # 将所有系统资源指标传递给状态机
        state_changed = self.pet_state_machine.update(
            cpu_usage=cpu_usage, 
            memory_usage=memory_usage,
            gpu_usage=gpu_usage,
            disk_usage=disk_usage,
            network_usage=network_usage
        )
        
        # 如果状态发生变化，记录日志
        if state_changed:
            current_state = self.pet_state_machine.get_state()
            self.logger.info(f"宠物状态更新为: {current_state.name} (CPU: {cpu_usage:.1f}%, Memory: {memory_usage:.1f}%)")
    
    def set_thresholds(self, cpu_threshold: Optional[float] = None, memory_threshold: Optional[float] = None) -> None:
        """设置CPU和内存使用率阈值
        
        Args:
            cpu_threshold: CPU使用率阈值，None表示不修改
            memory_threshold: 内存使用率阈值，None表示不修改
        """
        if cpu_threshold is not None:
            self.pet_state_machine.cpu_threshold = cpu_threshold
            self.logger.info(f"CPU使用率阈值已设置为: {cpu_threshold}%")
            
        if memory_threshold is not None:
            self.pet_state_machine.memory_threshold = memory_threshold
            self.logger.info(f"内存使用率阈值已设置为: {memory_threshold}%") 