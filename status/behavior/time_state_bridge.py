"""
---------------------------------------------------------------
File name:                  time_state_bridge.py
Author:                     Ignorant-lu
Date created:               2025/05/14
Description:                时间状态桥接器，连接时间系统和宠物状态机
----------------------------------------------------------------

Changed history:            
                            2025/05/14: 初始创建;
                            2025/05/14: 修复信号连接问题;
                            2025/05/14: 改进与TimeSignals的连接;
----
"""

import logging
from typing import Dict, Optional, Any

from status.behavior.time_based_behavior import TimeBasedBehaviorSystem, TimePeriod, SpecialDate
from status.behavior.pet_state_machine import PetStateMachine, PetState
from status.core.component_base import ComponentBase
from status.core.event_system import EventSystem, EventType, Event


class TimeStateBridge(ComponentBase):
    """时间状态桥接器
    
    将TimeBasedBehaviorSystem的时间状态转换为PetStateMachine的宠物状态
    """
    
    def __init__(self, 
                 pet_state_machine: Optional[PetStateMachine] = None,
                 time_system: Optional[TimeBasedBehaviorSystem] = None):
        """初始化时间状态桥接器
        
        Args:
            pet_state_machine: 宠物状态机实例，None则自动获取
            time_system: 时间行为系统实例，None则自动创建
        """
        super().__init__()
        
        self.logger = logging.getLogger("Status.Behavior.TimeStateBridge")
        
        # 状态机与时间系统
        self._pet_state_machine = pet_state_machine
        self._time_system = time_system
        
        # 时间周期到宠物状态的映射
        self.period_to_state = {
            TimePeriod.MORNING: PetState.MORNING,
            TimePeriod.NOON: PetState.NOON,
            TimePeriod.AFTERNOON: PetState.AFTERNOON,
            TimePeriod.EVENING: PetState.EVENING,
            TimePeriod.NIGHT: PetState.NIGHT
        }
        
        # 特殊日期名称到宠物状态的映射
        self.special_date_to_state = {
            "新年": PetState.NEW_YEAR,
            "元旦": PetState.NEW_YEAR,
            "情人节": PetState.VALENTINE,
            "春节": PetState.NEW_YEAR,
            "Birth of Status-Ming!": PetState.BIRTHDAY,
            # 可以添加更多特殊日期到状态的映射
        }
        
        # 事件系统
        self.event_system = None
        
        self.logger.info("时间状态桥接器初始化完成")
    
    def _initialize(self) -> bool:
        """初始化组件
        
        Returns:
            bool: 初始化是否成功
        """
        try:
            # 获取事件系统实例
            self.event_system = EventSystem.get_instance()
            
            # 获取状态机，如果未指定
            if self._pet_state_machine is None:
                # 当前暂不支持从事件系统获取状态机
                self.logger.warning("未指定状态机实例，桥接器功能将受限")
            
            # 创建或获取时间系统，如果未指定
            if self._time_system is None:
                self._time_system = TimeBasedBehaviorSystem()
                self._time_system._initialize()
                self.logger.info("已创建时间行为系统实例")
            
            # 连接时间系统的信号
            if self._time_system is not None and hasattr(self._time_system, 'signals') and self._time_system.signals is not None:
                try:
                    self._time_system.signals.time_period_changed.connect(self._on_time_period_changed)
                    self.logger.debug("已连接时间段变化信号")
                    
                    self._time_system.signals.special_date_triggered.connect(self._on_special_date_triggered)
                    self.logger.debug("已连接特殊日期信号")
                except Exception as e:
                    self.logger.error(f"连接时间系统信号时出错: {e}")
            else:
                self.logger.warning("时间系统不存在或不包含signals属性，无法连接信号")
            
            # 注册事件处理器
            if self.event_system:
                self.event_system.register_handler(EventType.TIME_PERIOD_CHANGED, self._on_time_event)
                self.event_system.register_handler(EventType.SPECIAL_DATE, self._on_special_date_event)
                self.logger.debug("已注册事件处理器")
            
            # 获取当前时间段并设置初始状态
            if self._time_system and self._pet_state_machine:
                current_period = self._time_system.get_current_period()
                self._update_pet_time_state(current_period)
                self.logger.info(f"已设置初始时间状态: {current_period.name}")
            
            return True
        except Exception as e:
            self.logger.error(f"时间状态桥接器初始化失败: {e}")
            return False
    
    def _shutdown(self) -> bool:
        """关闭组件
        
        Returns:
            bool: 关闭是否成功
        """
        try:
            # 取消连接信号
            if self._time_system is not None and hasattr(self._time_system, 'signals') and self._time_system.signals is not None:
                try:
                    self._time_system.signals.time_period_changed.disconnect(self._on_time_period_changed)
                except (TypeError, RuntimeError) as e:
                    # 忽略未连接的信号错误
                    self.logger.debug(f"断开时间段变化信号时出现非严重错误: {e}")
                
                try:
                    self._time_system.signals.special_date_triggered.disconnect(self._on_special_date_triggered)
                except (TypeError, RuntimeError) as e:
                    # 忽略未连接的信号错误
                    self.logger.debug(f"断开特殊日期信号时出现非严重错误: {e}")
            
            # 注销事件处理器
            if self.event_system:
                self.event_system.unregister_handler(EventType.TIME_PERIOD_CHANGED, self._on_time_event)
                self.event_system.unregister_handler(EventType.SPECIAL_DATE, self._on_special_date_event)
            
            return True
        except Exception as e:
            self.logger.error(f"关闭时间状态桥接器失败: {e}")
            return False
    
    def _on_time_period_changed(self, new_period: TimePeriod, old_period: TimePeriod) -> None:
        """处理时间段变化
        
        Args:
            new_period: 新的时间段
            old_period: 旧的时间段
        """
        self.logger.info(f"时间段从 {old_period.name if old_period else 'None'} 变为 {new_period.name}")
        
        # 更新宠物状态
        self._update_pet_time_state(new_period)
    
    def _on_special_date_triggered(self, name: str, description: str) -> None:
        """处理特殊日期触发
        
        Args:
            name: 特殊日期名称
            description: 特殊日期描述
        """
        self.logger.info(f"特殊日期触发: {name} - {description}")
        
        # 更新宠物状态
        self._update_pet_special_date_state(name)
    
    def _update_pet_time_state(self, period: TimePeriod) -> None:
        """根据时间段更新宠物状态
        
        Args:
            period: 时间段
        """
        if self._pet_state_machine is None:
            self.logger.warning("未指定状态机实例，无法更新宠物时间状态")
            return
        
        # 获取对应的宠物状态
        if period in self.period_to_state:
            pet_state = self.period_to_state[period]
            
            # 更新状态机中的时间状态
            self._pet_state_machine.update_time_state(pet_state)
            self.logger.debug(f"已更新宠物时间状态: {pet_state.name}")
    
    def _update_pet_special_date_state(self, special_date_name: str) -> None:
        """根据特殊日期更新宠物状态
        
        Args:
            special_date_name: 特殊日期名称
        """
        if self._pet_state_machine is None:
            self.logger.warning("未指定状态机实例，无法更新宠物特殊日期状态")
            return
        
        # 获取对应的宠物状态
        if special_date_name in self.special_date_to_state:
            pet_state = self.special_date_to_state[special_date_name]
            
            # 更新状态机中的特殊日期状态
            self._pet_state_machine.set_special_date(pet_state)
            self.logger.debug(f"已更新宠物特殊日期状态: {pet_state.name}")
    
    def _on_time_event(self, event: Event) -> None:
        """处理时间事件
        
        Args:
            event: 事件对象
        """
        if not event.data or 'period' not in event.data:
            return
        
        try:
            # 获取时间段名称
            period_name = event.data['period']
            
            # 转换为TimePeriod枚举
            for period in TimePeriod:
                if period.name == period_name:
                    self._update_pet_time_state(period)
                    break
        except Exception as e:
            self.logger.error(f"处理时间事件失败: {e}")
    
    def _on_special_date_event(self, event: Event) -> None:
        """处理特殊日期事件
        
        Args:
            event: 事件对象
        """
        if not event.data or 'name' not in event.data:
            return
        
        try:
            # 获取特殊日期名称
            special_date_name = event.data['name']
            
            # 更新宠物特殊日期状态
            self._update_pet_special_date_state(special_date_name)
        except Exception as e:
            self.logger.error(f"处理特殊日期事件失败: {e}")
    
    def get_current_time_state(self) -> Optional[PetState]:
        """获取当前的时间状态
        
        Returns:
            Optional[PetState]: 当前时间状态，如果未设置则为None
        """
        if self._pet_state_machine is None or self._time_system is None:
            return None
        
        current_period = self._time_system.get_current_period()
        
        if current_period in self.period_to_state:
            return self.period_to_state[current_period]
        
        return None 