"""
---------------------------------------------------------------
File name:                  time_state_adapter.py
Author:                     Ignorant-lu
Date created:               2025/05/13
Description:                时间状态适配器，连接TimeBasedBehaviorSystem和PetStateMachine
----------------------------------------------------------------

Changed history:            
                            2025/05/13: 初始创建;
                            2025/05/13: 修复事件处理注册问题;
                            2025/05/13: 修复特殊日期状态设置;
----
"""

import logging
from typing import Dict, Optional, Tuple

from status.core.component_base import ComponentBase
from status.core.event_system import EventSystem, EventType, Event
from status.behavior.time_based_behavior import TimeBasedBehaviorSystem, TimePeriod
from status.behavior.pet_state_machine import PetStateMachine
from status.behavior.pet_state import PetState


class TimeStateAdapter(ComponentBase):
    """时间状态适配器，将TimeBasedBehaviorSystem的时间状态转换为PetStateMachine可用的状态"""
    
    def __init__(self, pet_state_machine: PetStateMachine, time_behavior_system: TimeBasedBehaviorSystem):
        """初始化适配器
        
        Args:
            pet_state_machine: 宠物状态机实例
            time_behavior_system: 时间行为系统实例
        """
        super().__init__()
        self.logger = logging.getLogger("Status.Behavior.TimeStateAdapter")
        self.event_system = EventSystem.get_instance()
        
        self.pet_state_machine = pet_state_machine
        self.time_behavior_system = time_behavior_system
        
        # 将TimePeriod映射到PetState
        self.period_to_state = {
            TimePeriod.MORNING: PetState.MORNING,
            TimePeriod.NOON: PetState.NOON,
            TimePeriod.AFTERNOON: PetState.AFTERNOON,
            TimePeriod.EVENING: PetState.EVENING,
            TimePeriod.NIGHT: PetState.NIGHT,
        }
        
        # 用于跟踪是否是特殊日期
        self.is_current_special_date = False
    
    def _initialize(self) -> bool:
        """初始化适配器
        
        Returns:
            bool: 初始化是否成功
        """
        # 注册事件监听器，监听场景变化事件（时间段变化、特殊日期检测）
        # 确保这里明确调用事件系统的 register_handler 方法
        self.event_system.register_handler(EventType.SCENE_CHANGE, self._on_scene_change)
        
        # 立即同步当前时间状态
        self._sync_time_state()
        
        # 检查今天是否是特殊日期
        self._check_special_date()
        
        self.logger.info("时间状态适配器初始化完成")
        return True
    
    def _update(self, dt: float) -> None:
        """更新适配器
        
        Args:
            dt: 时间增量（秒）
        """
        # 大部分逻辑通过事件处理，此处不需要额外操作
        pass
    
    def _on_scene_change(self, event: Event) -> None:
        """处理场景变化事件
        
        Args:
            event: 场景变化事件
        """
        self.logger.debug(f"收到场景变化事件: {event.data}")
        
        # 检查事件数据是否包含所需信息
        if not event.data:
            return
            
        # 检查事件是否包含时间段变化
        if 'new_period' in event.data:
            self._handle_period_change(event.data)
            
        # 检查事件是否包含特殊日期检测
        elif 'name' in event.data and 'date' in event.data:
            self._handle_special_date(event.data)
    
    def _handle_period_change(self, data: Dict) -> None:
        """处理时间段变化
        
        Args:
            data: 事件数据
        """
        new_period = data.get('new_period')
        if not new_period or not isinstance(new_period, TimePeriod):
            return
            
        # 将TimePeriod转换为PetState
        pet_state = self.period_to_state.get(new_period)
        if not pet_state:
            self.logger.warning(f"无法将时间段 {new_period} 转换为宠物状态")
            return
            
        # 更新宠物状态机的时间状态
        changed = self.pet_state_machine.update_time_state(pet_state)
        if changed:
            self.logger.info(f"已更新宠物状态机的时间状态为: {pet_state.name}")
    
    def _handle_special_date(self, data: Dict) -> None:
        """处理特殊日期检测
        
        Args:
            data: 事件数据
        """
        special_day_name = data.get('name')
        if not special_day_name:
            return
            
        # 设置特殊日期状态
        self.is_current_special_date = True
        
        # 根据特殊日期名称选择对应的状态
        special_state = self._get_special_date_state(special_day_name)
        
        # 更新宠物状态机的特殊日期状态
        changed = self.pet_state_machine.set_special_date(special_state)
        if changed:
            self.logger.info(f"已设置特殊日期状态: {special_day_name}")
    
    def _sync_time_state(self) -> None:
        """同步当前时间状态到宠物状态机"""
        # 获取当前时间段
        current_period = self.time_behavior_system.get_current_period()
        if not current_period:
            return
            
        # 将TimePeriod转换为PetState
        pet_state = self.period_to_state.get(current_period)
        if not pet_state:
            self.logger.warning(f"无法将时间段 {current_period} 转换为宠物状态")
            return
            
        # 更新宠物状态机的时间状态
        self.pet_state_machine.update_time_state(pet_state)
        self.logger.info(f"初始化时同步时间状态为: {pet_state.name}")
    
    def _check_special_date(self) -> None:
        """检查今天是否是特殊日期"""
        is_special, name = self.time_behavior_system.is_special_date()
        if is_special and name is not None:
            self.is_current_special_date = True
            
            # 根据特殊日期名称选择对应的状态
            special_state = self._get_special_date_state(name)
            
            # 更新宠物状态机的特殊日期状态
            self.pet_state_machine.set_special_date(special_state)
            self.logger.info(f"初始化时设置特殊日期状态: {name}")
        else:
            self.is_current_special_date = False
            self.pet_state_machine.set_special_date(None)
    
    def _get_special_date_state(self, date_name: str) -> PetState:
        """根据特殊日期名称返回对应的宠物状态
        
        Args:
            date_name: 特殊日期名称
            
        Returns:
            PetState: 对应的宠物状态
        """
        # 根据特殊日期名称映射到具体的特殊日期状态
        special_date_map = {
            "Status Ming": PetState.NEW_YEAR,  # Ming 诞辰!为 2003/05/19，暂时用NEW_YEAR代替
            "New Year": PetState.NEW_YEAR,
            "Valentine's Day": PetState.VALENTINE,
            "Christmas": PetState.NEW_YEAR,  # 暂时没有专门的圣诞节状态，用NEW_YEAR代替
            "Labor Day": PetState.NEW_YEAR,  # 暂时用NEW_YEAR代替
            "National Day": PetState.NEW_YEAR,  # 暂时用NEW_YEAR代替
            # 可以添加更多映射
        }
        
        # 返回映射的状态，如果没有对应映射则默认使用NEW_YEAR状态
        return special_date_map.get(date_name, PetState.NEW_YEAR)