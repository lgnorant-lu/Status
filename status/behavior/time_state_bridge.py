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

from status.behavior.time_based_behavior import TimeBasedBehaviorSystem, TimePeriod, SpecialDate # Added SpecialDate import
from status.behavior.pet_state_machine import PetStateMachine, PetState, StateCategory # Added StateCategory
from status.core.component_base import ComponentBase
# EventSystem and related imports are now removed as they are not used.
# from status.core.event_system import EventSystem, EventType, Event


class TimeStateBridge(ComponentBase):
    """时间状态桥接器 (整合版)
    
    将TimeBasedBehaviorSystem的时间状态（时间段和特殊日期）转换为PetStateMachine的宠物状态，
    并通过 PetStateMachine.set_state() 进行设置。
    主要通过连接 TimeBasedBehaviorSystem 的信号来响应时间变化。
    """
    
    def __init__(self, 
                 pet_state_machine: PetStateMachine,
                 time_system: Optional[TimeBasedBehaviorSystem] = None):
        """初始化时间状态桥接器
        
        Args:
            pet_state_machine: 宠物状态机实例 (必需)
            time_system: 时间行为系统实例，None则自动创建并初始化
        """
        super().__init__()
        
        self.logger = logging.getLogger("Status.Behavior.TimeStateBridge")
        
        if pet_state_machine is None:
            # 在整合版本中，状态机是必需的，因为所有状态都通过它设置
            self.logger.error("PetStateMachine 实例未提供，TimeStateBridge 无法运行。")
            raise ValueError("PetStateMachine instance is required for TimeStateBridge.")

        self._pet_state_machine: PetStateMachine = pet_state_machine
        self._time_system: Optional[TimeBasedBehaviorSystem] = time_system
        
        # 时间周期到宠物状态的映射
        self.period_to_state_mapping: Dict[TimePeriod, PetState] = {
            TimePeriod.MORNING: PetState.MORNING,
            TimePeriod.NOON: PetState.NOON,
            TimePeriod.AFTERNOON: PetState.AFTERNOON,
            TimePeriod.EVENING: PetState.EVENING,
            TimePeriod.NIGHT: PetState.NIGHT,
        }
        
        # 特殊日期名称到宠物状态的映射 (从 TimeStateAdapter 和原 TimeStateBridge 整合)
        # 键为 TimeBasedBehaviorSystem.SpecialDate.name (str)
        self.special_date_to_state_mapping: Dict[str, PetState] = {
            "新年": PetState.NEW_YEAR,
            "元旦": PetState.NEW_YEAR,
            "情人节": PetState.VALENTINE,
            "春节": PetState.SPRING_FESTIVAL,
            "立春": PetState.LICHUN,
            "元宵节": PetState.HAPPY,
            "清明节": PetState.HAPPY,
            "劳动节": PetState.HAPPY,
            "端午节": PetState.HAPPY,
            "七夕节": PetState.HAPPY,
            "中秋节": PetState.HAPPY,
            "国庆节": PetState.HAPPY,
            "重阳节": PetState.HAPPY,
            "冬至": PetState.HAPPY,
            "平安夜": PetState.HAPPY,
            "圣诞节": PetState.HAPPY,
            "项目诞辰日": PetState.BIRTHDAY,
            "生日": PetState.BIRTHDAY,
        }
        
        self.logger.info("时间状态桥接器 (整合版) 初始化完成")
    
    def _initialize(self) -> bool:
        """初始化组件
        
        Returns:
            bool: 初始化是否成功
        """
        try:
            # 创建或获取时间系统，如果未指定
            if self._time_system is None:
                self.logger.info("未指定时间系统实例，将创建新的 TimeBasedBehaviorSystem。")
                self._time_system = TimeBasedBehaviorSystem()
            
            if not self._time_system.is_active: # 确保时间系统已初始化
                 self._time_system._initialize() # 调用其受保护的初始化（如果需要）

            # 连接时间系统的信号
            if self._time_system is not None and hasattr(self._time_system, 'signals') and self._time_system.signals is not None:
                try:
                    self._time_system.signals.time_period_changed.connect(self._on_time_period_changed)
                    self.logger.debug("已连接 time_period_changed 信号")
                    
                    self._time_system.signals.special_date_triggered.connect(self._on_special_date_triggered)
                    self.logger.debug("已连接 special_date_triggered 信号")
                except Exception as e:
                    self.logger.error(f"连接时间系统信号时出错: {e}")
                    return False # 初始化失败如果信号无法连接
            else:
                self.logger.warning("时间系统不存在或不包含signals属性，无法连接信号，桥接器功能将受限。")
                return False # 认为初始化失败，因为这是核心依赖

            # 获取当前时间段和特殊日期并设置初始状态
            self._sync_initial_states()
            
            return True
        except Exception as e:
            self.logger.error(f"时间状态桥接器初始化失败: {e}", exc_info=True)
            return False
            
    def _sync_initial_states(self):
        """同步当前的时间段和特殊日期状态到PetStateMachine。"""
        if not self._time_system:
            self.logger.warning("时间系统未初始化，无法同步初始状态。")
            return

        # 同步当前时间段
        current_period = self._time_system.get_current_period()
        self.logger.info(f"获取到初始时间段: {current_period.name if current_period else 'None'}")
        self._update_pet_time_state(current_period)

        # 同步当前特殊日期 (如果有)
        current_special_dates: list[SpecialDate] = self._time_system.get_current_special_dates() # Use get_current_special_dates
        if current_special_dates:
            for special_date_obj in current_special_dates:
                self.logger.info(f"获取到初始特殊日期: {special_date_obj.name}")
                self._update_pet_special_date_state(special_date_obj.name, special_date_obj.description)
        else:
            self.logger.info("启动时未检测到特殊日期。")
            # Optionally, ensure no special date is set in state machine if needed
            # self._pet_state_machine.set_special_date(None) # If PetStateMachine supports clearing special date


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
                    self.logger.debug(f"断开 time_period_changed 信号时出现非严重错误: {e}")
                
                try:
                    self._time_system.signals.special_date_triggered.disconnect(self._on_special_date_triggered)
                except (TypeError, RuntimeError) as e:
                    self.logger.debug(f"断开 special_date_triggered 信号时出现非严重错误: {e}")
            
            return True
        except Exception as e:
            self.logger.error(f"关闭时间状态桥接器失败: {e}", exc_info=True)
            return False
    
    def _on_time_period_changed(self, new_period: TimePeriod, old_period: Optional[TimePeriod]) -> None:
        """处理时间段变化信号
        
        Args:
            new_period: 新的时间段
            old_period: 旧的时间段 (可能为 None)
        """
        self.logger.info(f"时间段从 {old_period.name if old_period else '未知'} 变为 {new_period.name}")
        self._update_pet_time_state(new_period)
    
    def _on_special_date_triggered(self, name: str, description: str, date_info: Any) -> None: # date_info from signal
        """处理特殊日期触发信号
        
        Args:
            name: 特殊日期名称 (来自 TimeBasedBehaviorSystem.SpecialDate.name)
            description: 特殊日期描述
            date_info: 触发信号时传递的日期相关信息 (如 SpecialDate 对象本身)
        """
        self.logger.info(f"特殊日期触发: {name} - {description}")
        self._update_pet_special_date_state(name, description) # Pass description for potential use
    
    def _update_pet_time_state(self, period: Optional[TimePeriod]) -> None:
        """根据时间段更新宠物状态机中的时间状态
        
        Args:
            period: 时间段 (TimePeriod 枚举成员)
        """
        if period is None: # Removed UNKNOWN check as TimePeriod enum doesn't have it by default
            self.logger.debug(f"不处理无效的时间段: {period}")
            return

        target_pet_state = self.period_to_state_mapping.get(period) # Use renamed attribute
        
        if target_pet_state:
            self.logger.debug(f"时间段 {period.name} 映射到宠物状态 {target_pet_state.name}")
            try:
                # 使用 PetStateMachine 的特定方法
                changed = self._pet_state_machine.update_time_state(target_pet_state)
                if changed:
                    self.logger.info(f"已通过 PetStateMachine 更新时间状态为: {target_pet_state.name}")
                else:
                    self.logger.info(f"PetStateMachine 时间状态未改变，仍为: {target_pet_state.name}")
            except Exception as e:
                self.logger.error(f"通过 PetStateMachine 设置时间状态 {target_pet_state.name} 失败: {e}", exc_info=True)
        else:
            self.logger.warning(f"时间段 {period.name} 没有对应的宠物状态映射。")
    
    def _update_pet_special_date_state(self, special_date_name: str, description: Optional[str] = None) -> None:
        """根据特殊日期名称更新宠物状态机中的特殊日期状态
        
        Args:
            special_date_name: 特殊日期名称
            description: 特殊日期描述 (可选)
        """
        if self._pet_state_machine is None:
            self.logger.warning("未指定状态机实例，无法更新宠物特殊日期状态") # Corrected: use self.logger
            return
        
        pet_state = self.special_date_to_state_mapping.get(special_date_name) # Use renamed attribute
        
        if pet_state:
            self.logger.debug(f"特殊日期 \"{special_date_name}\" 映射到宠物状态 {pet_state.name}")
            try:
                # 使用 PetStateMachine 的特定方法
                changed = self._pet_state_machine.set_special_date(pet_state) 
                # set_special_date might not need description, or it could be logged/handled differently
                if changed:
                    self.logger.info(f"已通过 PetStateMachine 更新特殊日期状态为: {pet_state.name} (日期: {special_date_name})")
                else:
                    self.logger.info(f"PetStateMachine 特殊日期状态未改变，仍为: {pet_state.name} (日期: {special_date_name})")
            except Exception as e:
                self.logger.error(f"通过 PetStateMachine 设置特殊日期状态 {pet_state.name} (日期: {special_date_name}) 失败: {e}", exc_info=True)
        else:
            self.logger.warning(f"特殊日期 \"{special_date_name}\" 没有对应的宠物状态映射。")
    
    def get_current_time_state(self) -> Optional[PetState]:
        """获取当前时间系统对应的时间状态 (基于映射)
        注意: 这不直接查询状态机, 而是基于当前时间系统的时间段进行映射。
        主要用于测试或调试目的。
        """
        if not self._time_system:
            self.logger.warning("时间系统未初始化，无法获取当前时间状态。")
            return None
        
        current_period = self._time_system.get_current_period()
        
        if current_period in self.period_to_state_mapping:
            return self.period_to_state_mapping[current_period]
        
        return None 