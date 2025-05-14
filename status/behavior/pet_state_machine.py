"""
---------------------------------------------------------------
File name:                  pet_state_machine.py
Author:                     Ignorant-lu
Date created:               2025/05/13
Description:                宠物状态机，根据输入更新宠物状态
----------------------------------------------------------------

Changed history:            
                            2025/05/13: 初始创建;
                            2025/05/13: 扩展支持时间相关状态;
                            2025/05/13: 更新以支持细化的CPU负载状态;
                            2025/05/13: 修复logger初始化问题;
----
"""

import logging
from typing import Dict, List, Optional, Set, Tuple, Union, Deque, Any
from enum import Enum
import time
from collections import deque

from status.behavior.pet_state import PetState
from status.core.event_system import EventSystem, EventType, Event

logger = logging.getLogger(__name__)

class StateCategory(Enum):
    """状态类别，用于状态优先级管理"""
    SYSTEM = 1       # 系统相关状态 (CPU, 内存等)
    TIME = 2         # 时间相关状态 (早晨，中午等)
    SPECIAL_DATE = 3 # 特殊日期状态 (节日等)
    INTERACTION = 4  # 交互相关状态 (用户点击等)


class PetStateMachine:
    """管理桌宠状态的状态机"""

    def __init__(self, 
                 cpu_light_threshold: float = 20.0,
                 cpu_moderate_threshold: float = 40.0,
                 cpu_heavy_threshold: float = 60.0, 
                 cpu_very_heavy_threshold: float = 80.0,
                 memory_warning_threshold: float = 70.0,
                 memory_critical_threshold: float = 90.0,
                 max_history_size: int = 50):
        """初始化状态机

        Args:
            cpu_light_threshold (float): CPU轻微负载阈值，高于此值进入LIGHT_LOAD状态。
            cpu_moderate_threshold (float): CPU中等负载阈值，高于此值进入MODERATE_LOAD状态。
            cpu_heavy_threshold (float): CPU高负载阈值，高于此值进入HEAVY_LOAD状态。
            cpu_very_heavy_threshold (float): CPU极重负载阈值，高于此值进入VERY_HEAVY_LOAD状态。
            memory_warning_threshold (float): 内存警告阈值，高于此值进入MEMORY_WARNING状态。
            memory_critical_threshold (float): 内存临界阈值，高于此值进入MEMORY_CRITICAL状态。
            max_history_size (int): 历史记录最大条目数，默认50。
        """
        # 初始化logger
        self.logger = logging.getLogger("Status.Behavior.PetStateMachine")
        
        # 当前活动状态（每个类别最多一个）
        self.active_states = {
            StateCategory.SYSTEM: PetState.IDLE,
            StateCategory.TIME: None,
            StateCategory.SPECIAL_DATE: None,
            StateCategory.INTERACTION: None
        }
        
        # CPU负载阈值
        self.cpu_light_threshold = cpu_light_threshold
        self.cpu_moderate_threshold = cpu_moderate_threshold
        self.cpu_heavy_threshold = cpu_heavy_threshold
        self.cpu_very_heavy_threshold = cpu_very_heavy_threshold
        
        # 向后兼容的阈值映射
        self.cpu_threshold = self.cpu_moderate_threshold
        self.cpu_very_busy_threshold = self.cpu_heavy_threshold
        self.cpu_critical_threshold = 95.0  # CPU临界状态阈值（极高）
        
        # 内存阈值
        self.memory_threshold = memory_warning_threshold
        self.memory_warning_threshold = memory_warning_threshold
        self.memory_critical_threshold = memory_critical_threshold
        
        # 其他系统资源阈值
        self.gpu_threshold = 70.0          # GPU忙碌阈值：70%
        self.gpu_very_busy_threshold = 90.0 # GPU极度繁忙阈值：90%
        
        self.disk_threshold = 70.0          # 磁盘忙碌阈值：70%
        self.disk_very_busy_threshold = 90.0 # 磁盘极度繁忙阈值：90%
        
        self.network_threshold = 70.0          # 网络忙碌阈值：70%
        self.network_very_busy_threshold = 90.0 # 网络极度繁忙阈值：90%
        
        self.system_idle_threshold = 5.0    # 系统完全空闲阈值：5%
        
        # 事件系统
        self.event_system = EventSystem.get_instance()
        
        # 状态优先级映射（数值越大优先级越高）
        self.state_priorities = {
            # 系统状态优先级 - CPU状态
            PetState.CPU_CRITICAL: 110,     # CPU临界状态
            PetState.VERY_HEAVY_LOAD: 100,  # CPU极重负载
            PetState.HEAVY_LOAD: 90,        # CPU高负载
            PetState.MODERATE_LOAD: 80,     # CPU中等负载
            PetState.LIGHT_LOAD: 70,        # CPU轻微负载
            PetState.IDLE: 10,              # CPU空闲
            
            # 兼容旧版本的状态映射
            PetState.BUSY: 80,              # 等同于MODERATE_LOAD
            PetState.VERY_BUSY: 90,         # 等同于HEAVY_LOAD
            
            # 系统状态优先级 - 内存状态
            PetState.MEMORY_CRITICAL: 120,  # 内存临界状态（最高优先级）
            PetState.MEMORY_WARNING: 105,   # 内存警告状态
            
            # 系统状态优先级 - 其他资源状态
            PetState.GPU_VERY_BUSY: 95,     # GPU极度繁忙状态
            PetState.GPU_BUSY: 85,          # GPU繁忙状态
            
            PetState.DISK_VERY_BUSY: 88,    # 磁盘极度繁忙状态
            PetState.DISK_BUSY: 75,         # 磁盘繁忙状态
            
            PetState.NETWORK_VERY_BUSY: 87, # 网络极度繁忙状态
            PetState.NETWORK_BUSY: 70,      # 网络繁忙状态
            
            PetState.SYSTEM_IDLE: 5,        # 系统完全空闲状态
            
            # 特殊日期状态优先级
            PetState.BIRTHDAY: 95,          # 生日状态
            PetState.NEW_YEAR: 95,          # 新年状态
            PetState.VALENTINE: 95,         # 情人节状态
            
            # 时间状态优先级
            PetState.MORNING: 20,
            PetState.NOON: 20,
            PetState.AFTERNOON: 20,
            PetState.EVENING: 20,
            PetState.NIGHT: 30,             # 夜晚优先级稍高
            
            # 用户交互状态优先级
            PetState.CLICKED: 150,          # 被点击状态 (最高优先级)
            PetState.DRAGGED: 150,          # 被拖拽状态
            PetState.PETTED: 150,           # 被抚摸状态
            PetState.HAPPY: 130,            # 开心状态
            PetState.SAD: 130,              # 难过状态
            PetState.ANGRY: 130,            # 生气状态
            PetState.PLAY: 130,             # 玩耍状态
            # PetState.SLEEP: 40              # 睡眠状态 (已移出交互类别，待重新设计)
        }
        
        # 状态类别映射
        self.state_to_category = {
            # 系统状态 - CPU状态
            PetState.IDLE: StateCategory.SYSTEM,
            PetState.LIGHT_LOAD: StateCategory.SYSTEM,
            PetState.MODERATE_LOAD: StateCategory.SYSTEM,
            PetState.HEAVY_LOAD: StateCategory.SYSTEM,
            PetState.VERY_HEAVY_LOAD: StateCategory.SYSTEM,
            PetState.CPU_CRITICAL: StateCategory.SYSTEM,
            
            # 兼容旧版本的状态映射
            PetState.BUSY: StateCategory.SYSTEM,
            PetState.VERY_BUSY: StateCategory.SYSTEM,
            
            # 系统状态 - 内存状态
            PetState.MEMORY_WARNING: StateCategory.SYSTEM,
            PetState.MEMORY_CRITICAL: StateCategory.SYSTEM,
            
            # 系统状态 - 其他资源状态
            PetState.GPU_BUSY: StateCategory.SYSTEM,
            PetState.GPU_VERY_BUSY: StateCategory.SYSTEM,
            PetState.DISK_BUSY: StateCategory.SYSTEM,
            PetState.DISK_VERY_BUSY: StateCategory.SYSTEM,
            PetState.NETWORK_BUSY: StateCategory.SYSTEM,
            PetState.NETWORK_VERY_BUSY: StateCategory.SYSTEM,
            PetState.SYSTEM_IDLE: StateCategory.SYSTEM,
            
            # 时间状态
            PetState.MORNING: StateCategory.TIME,
            PetState.NOON: StateCategory.TIME,
            PetState.AFTERNOON: StateCategory.TIME,
            PetState.EVENING: StateCategory.TIME,
            PetState.NIGHT: StateCategory.TIME,
            
            # 特殊日期状态
            PetState.BIRTHDAY: StateCategory.SPECIAL_DATE,
            PetState.NEW_YEAR: StateCategory.SPECIAL_DATE,
            PetState.VALENTINE: StateCategory.SPECIAL_DATE,
            
            # 用户交互状态
            PetState.CLICKED: StateCategory.INTERACTION,
            PetState.DRAGGED: StateCategory.INTERACTION,
            PetState.PETTED: StateCategory.INTERACTION,
            PetState.HAPPY: StateCategory.INTERACTION,
            PetState.SAD: StateCategory.INTERACTION,
            PetState.ANGRY: StateCategory.INTERACTION,
            # PetState.SLEEP: StateCategory.INTERACTION, # 已移出交互类别，待重新设计
            PetState.PLAY: StateCategory.INTERACTION
        }
        
        # 添加状态历史记录
        self.max_history_size = max_history_size
        self.state_history: Deque[Dict[str, Any]] = deque(maxlen=max_history_size)
        
        logger.info(f"状态机初始化完成。当前系统状态: {self.active_states[StateCategory.SYSTEM].name}")

    def update(self, cpu_usage: float, memory_usage: float, gpu_usage: float = 0.0, 
               disk_usage: float = 0.0, network_usage: float = 0.0) -> bool:
        """根据系统使用率更新状态

        Args:
            cpu_usage (float): 当前 CPU 使用率。
            memory_usage (float): 当前内存使用率。
            gpu_usage (float, optional): 当前 GPU 使用率。
            disk_usage (float, optional): 当前磁盘使用率。
            network_usage (float, optional): 当前网络使用率。

        Returns:
            bool: 如果状态发生改变则返回 True，否则返回 False。
        """
        previous_state = self.active_states[StateCategory.SYSTEM]
        
        # 处理各个系统资源
        cpu_state = self._process_cpu_load(cpu_usage)
        memory_state = self._process_memory_usage(memory_usage)
        gpu_state = self._process_gpu_usage(gpu_usage) if gpu_usage > 0 else None
        disk_state = self._process_disk_usage(disk_usage) if disk_usage > 0 else None
        network_state = self._process_network_usage(network_usage) if network_usage > 0 else None
        
        # 收集所有有效的系统状态
        system_states = [state for state in [cpu_state, memory_state, gpu_state, disk_state, network_state] if state is not None]
        
        # 特殊处理：如果CPU和内存都非常低，则设置为系统完全空闲状态
        if cpu_usage <= self.system_idle_threshold and memory_usage <= self.system_idle_threshold:
            system_states.append(PetState.SYSTEM_IDLE)
            
        # 如果没有任何状态，使用默认的IDLE状态
        if not system_states:
            system_states.append(PetState.IDLE)
            
        # 根据优先级选择最终状态
        new_state = self._select_highest_priority_state(system_states)

        # 检查状态是否真的改变
        state_changed = new_state != previous_state
        if state_changed:
            logger.info(f"系统状态从 {previous_state.name} 变为 {new_state.name} " + 
                        f"(CPU: {cpu_usage:.1f}%, Mem: {memory_usage:.1f}%, " + 
                        f"GPU: {gpu_usage:.1f}%, Disk: {disk_usage:.1f}%, Net: {network_usage:.1f}%)")
            self.active_states[StateCategory.SYSTEM] = new_state
            
            # 发布状态变化事件
            self._publish_state_changed_event(previous_state, new_state)
        
        return state_changed

    def _process_cpu_load(self, cpu_usage: float) -> PetState:
        """处理CPU负载并返回对应状态
        
        Args:
            cpu_usage (float): 当前CPU使用率。
            
        Returns:
            PetState: 对应的CPU负载状态。
        """
        if cpu_usage >= self.cpu_critical_threshold:
            return PetState.CPU_CRITICAL
        elif cpu_usage >= self.cpu_very_heavy_threshold:
            return PetState.VERY_HEAVY_LOAD
        elif cpu_usage >= self.cpu_heavy_threshold:
            return PetState.HEAVY_LOAD
        elif cpu_usage >= self.cpu_moderate_threshold:
            return PetState.MODERATE_LOAD
        elif cpu_usage >= self.cpu_light_threshold:
            return PetState.LIGHT_LOAD
        else:
            return PetState.IDLE
    
    def _process_memory_usage(self, memory_usage: float) -> Optional[PetState]:
        """处理内存使用率并返回对应状态
        
        Args:
            memory_usage (float): 当前内存使用率。
            
        Returns:
            Optional[PetState]: 对应的内存状态，如果未超过阈值则返回None。
        """
        if memory_usage >= self.memory_critical_threshold:
            return PetState.MEMORY_CRITICAL
        elif memory_usage >= self.memory_warning_threshold:
            return PetState.MEMORY_WARNING
        return None
    
    def _process_gpu_usage(self, gpu_usage: float) -> Optional[PetState]:
        """处理GPU使用率并返回对应状态
        
        Args:
            gpu_usage (float): 当前GPU使用率。
            
        Returns:
            Optional[PetState]: 对应的GPU状态，如果未超过阈值则返回None。
        """
        if gpu_usage >= self.gpu_very_busy_threshold:
            return PetState.GPU_VERY_BUSY
        elif gpu_usage >= self.gpu_threshold:
            return PetState.GPU_BUSY
        return None
    
    def _process_disk_usage(self, disk_usage: float) -> Optional[PetState]:
        """处理磁盘使用率并返回对应状态
        
        Args:
            disk_usage (float): 当前磁盘使用率。
            
        Returns:
            Optional[PetState]: 对应的磁盘状态，如果未超过阈值则返回None。
        """
        if disk_usage >= self.disk_very_busy_threshold:
            return PetState.DISK_VERY_BUSY
        elif disk_usage >= self.disk_threshold:
            return PetState.DISK_BUSY
        return None
    
    def _process_network_usage(self, network_usage: float) -> Optional[PetState]:
        """处理网络使用率并返回对应状态
        
        Args:
            network_usage (float): 当前网络使用率。
            
        Returns:
            Optional[PetState]: 对应的网络状态，如果未超过阈值则返回None。
        """
        if network_usage >= self.network_very_busy_threshold:
            return PetState.NETWORK_VERY_BUSY
        elif network_usage >= self.network_threshold:
            return PetState.NETWORK_BUSY
        return None
    
    def _select_highest_priority_state(self, states: List[PetState]) -> PetState:
        """从多个状态中选择优先级最高的状态
        
        Args:
            states (List[PetState]): 状态列表。
            
        Returns:
            PetState: 优先级最高的状态。
        """
        highest_priority = -1
        highest_priority_state = PetState.IDLE  # 默认
        
        for state in states:
            priority = self.state_priorities.get(state, 0)
            if priority > highest_priority:
                highest_priority = priority
                highest_priority_state = state
                
        return highest_priority_state

    def update_time_state(self, time_state: PetState) -> bool:
        """更新时间相关状态

        Args:
            time_state (PetState): 新的时间状态

        Returns:
            bool: 如果状态发生改变则返回 True，否则返回 False。
        """
        # 验证是否是有效的时间状态
        if self.state_to_category.get(time_state) != StateCategory.TIME:
            logger.warning(f"尝试设置无效的时间状态: {time_state}")
            return False
            
        previous_state = self.active_states[StateCategory.TIME]
        
        # 检查状态是否真的改变
        state_changed = time_state != previous_state
        if state_changed:
            if previous_state:
                logger.info(f"时间状态从 {previous_state.name} 变为 {time_state.name}")
            else:
                logger.info(f"时间状态设置为 {time_state.name}")
                
            self.active_states[StateCategory.TIME] = time_state
            
            # 发布状态变化事件
            self._publish_state_changed_event(previous_state, time_state)
        
        return state_changed

    def set_special_date(self, special_date: Optional[PetState] = None) -> bool:
        """设置特殊日期状态

        Args:
            special_date (Optional[PetState]): 特殊日期状态，如BIRTHDAY、NEW_YEAR等
                                             如果为None则清除特殊日期状态

        Returns:
            bool: 如果状态发生改变则返回 True，否则返回 False。
        """
        previous_state = self.active_states[StateCategory.SPECIAL_DATE]
        
        # 检查是否是有效的特殊日期状态
        if special_date is not None and self.state_to_category.get(special_date) != StateCategory.SPECIAL_DATE:
            logger.warning(f"尝试设置无效的特殊日期状态: {special_date}")
            return False
            
        # 检查状态是否真的改变
        state_changed = special_date != previous_state
        if state_changed:
            if special_date:
                logger.info(f"特殊日期状态已设置为: {special_date.name}")
            else:
                logger.info(f"特殊日期状态已清除")
                
            self.active_states[StateCategory.SPECIAL_DATE] = special_date
            
            # 发布状态变化事件
            self._publish_state_changed_event(previous_state, special_date)
        
        return state_changed
        
    def set_interaction_state(self, interaction_state: Optional[Union[PetState, int]]) -> None:
        """设置交互状态
        
        设置用户交互导致的状态，覆盖其他状态
        
        Args:
            interaction_state: 交互状态，可以是PetState枚举值或整数，None表示清除交互状态
        """
        if interaction_state is None:
            # 清除交互状态
            if self.active_states[StateCategory.INTERACTION] is not None:
                self.active_states[StateCategory.INTERACTION] = None
                logger.debug("清除交互状态")
                self._recalculate_active_state()
            return
            
        # 如果收到的是整数值，转换为PetState枚举
        if isinstance(interaction_state, int):
            try:
                interaction_state = PetState(interaction_state)
            except ValueError:
                logger.warning(f"无效的交互状态ID: {interaction_state}")
                return
                
        self.active_states[StateCategory.INTERACTION] = interaction_state
        logger.debug(f"设置交互状态: {interaction_state.name}")
        
        # 交互状态优先级高于其他状态
        self._recalculate_active_state()

    def _recalculate_active_state(self) -> None:
        """重新计算当前活动状态
        
        根据各类别状态的优先级重新计算当前应该显示的状态
        优先级：交互 > 特殊日期 > 系统 > 时间 > 默认
        """
        previous_state = self.active_states[StateCategory.SYSTEM]
        
        # 按优先级检查各类别状态
        if self.active_states[StateCategory.INTERACTION] is not None:
            self.active_states[StateCategory.SYSTEM] = self.active_states[StateCategory.INTERACTION]
        elif self.active_states[StateCategory.SPECIAL_DATE] is not None:
            self.active_states[StateCategory.SYSTEM] = self.active_states[StateCategory.SPECIAL_DATE]
        elif self.active_states[StateCategory.TIME] is not None:
            self.active_states[StateCategory.SYSTEM] = self.active_states[StateCategory.TIME]
        else:
            self.active_states[StateCategory.SYSTEM] = PetState.IDLE
            
        # 如果状态发生变化，发布事件
        if previous_state != self.active_states[StateCategory.SYSTEM]:
            self.logger.info(f"宠物状态变更: {previous_state.name if previous_state else 'None'} -> {self.active_states[StateCategory.SYSTEM].name}")
            self._publish_state_changed_event(previous_state, self.active_states[StateCategory.SYSTEM])

    def get_state(self) -> PetState:
        """获取当前的最高优先级状态

        Returns:
            PetState: 当前的最高优先级状态。
        """
        # 收集所有当前活动的状态
        active_states = [state for state in self.active_states.values() if state is not None]
        
        # 从所有活动状态中选择优先级最高的
        return self._select_highest_priority_state(active_states)

    def get_active_states(self) -> Dict[StateCategory, Optional[PetState]]:
        """获取当前所有活动状态
        
        Returns:
            Dict[StateCategory, Optional[PetState]]: 按类别的当前活动状态。
        """
        return self.active_states.copy()

    def _publish_state_changed_event(self, previous_state: Optional[PetState], current_state: Optional[PetState]) -> None:
        """发布状态变化事件
        
        Args:
            previous_state: 之前的状态
            current_state: 当前状态
        """
        if self.event_system:
            try:
                # 准备事件数据
                event_data = {
                    "previous_state": previous_state.value if previous_state else None,
                    "current_state": current_state.value if current_state else None,
                    "previous_state_name": previous_state.name if previous_state else None,
                    "current_state_name": current_state.name if current_state else None,
                    "timestamp": time.time()
                }
                
                # 记录到状态历史
                history_entry = event_data.copy()
                history_entry["datetime"] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(history_entry["timestamp"]))
                self.state_history.append(history_entry)
                
                # 发布状态变更事件
                self.event_system.dispatch_event(
                    EventType.STATE_CHANGED,  # 使用状态变化事件类型
                    sender=self,
                    data=event_data
                )
                self.logger.debug(f"已发布状态变化事件: {previous_state.name if previous_state else 'None'} -> {current_state.name if current_state else 'None'}")
            except Exception as e:
                self.logger.error(f"发布状态变化事件时出错: {e}")
                # 不抛出异常，避免影响状态机核心逻辑

    def get_state_history(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """获取状态变化历史
        
        Args:
            limit: 返回的历史记录数量限制，默认为None表示返回全部
            
        Returns:
            List[Dict[str, Any]]: 状态变化历史记录列表，按时间从新到旧排序
        """
        if limit is None or limit >= len(self.state_history):
            return list(self.state_history)
        else:
            return list(self.state_history)[:limit]

    def clear_state_history(self) -> None:
        """清空状态变化历史记录"""
        self.state_history.clear()
        self.logger.debug("状态历史记录已清空") 