"""
---------------------------------------------------------------
File name:                  interaction_state_adapter.py
Author:                     Ignorant-lu
Date created:               2025/05/13
Description:                交互状态适配器，将用户交互转换为宠物状态
----------------------------------------------------------------

Changed history:            
                            2025/05/13: 初始创建;
----
"""

import logging
import time
from typing import Dict, Optional, Any, Set, List, Tuple

from status.core.component_base import ComponentBase
from status.core.event_system import EventSystem, EventType, Event
from status.behavior.pet_state import PetState
from status.behavior.pet_state_machine import PetStateMachine
from status.interaction.interaction_zones import InteractionType
from status.behavior.interaction_tracker import InteractionPattern

class InteractionStateAdapter(ComponentBase):
    """交互状态适配器
    
    将用户交互转换为宠物状态，连接交互系统和状态机
    """
    
    def __init__(self, 
                 pet_state_machine: Optional[PetStateMachine] = None,
                 interaction_timeout: float = 5.0):
        """初始化交互状态适配器
        
        Args:
            pet_state_machine: 宠物状态机实例，如果为None则尝试从事件系统获取
            interaction_timeout: 交互状态超时时间（秒）
        """
        super().__init__()
        
        # 组件基本状态
        self.is_active = True
        
        # 状态机实例
        self._pet_state_machine = pet_state_machine
        
        # 交互状态超时时间（秒）
        self.interaction_timeout = interaction_timeout
        
        # 当前交互状态
        self.current_interaction_state: Optional[PetState] = None
        
        # 最后交互时间
        self.last_interaction_time: float = 0.0
        
        # 交互类型到状态的映射
        self.interaction_to_state: Dict[str, PetState] = {
            # 基本交互类型
            InteractionType.CLICK.name: PetState.CLICKED,
            InteractionType.DOUBLE_CLICK.name: PetState.CLICKED,
            InteractionType.DRAG.name: PetState.DRAGGED,
            InteractionType.HOVER.name: PetState.PETTED,
            
            # 区域特定交互类型 (根据区域ID确定)
            "head_CLICK": PetState.HEAD_CLICKED,
            "body_CLICK": PetState.BODY_CLICKED,
            "tail_CLICK": PetState.TAIL_CLICKED,
            
            "head_HOVER": PetState.HEAD_PETTED,
            "body_HOVER": PetState.BODY_PETTED,
            "tail_HOVER": PetState.TAIL_PETTED,
        }
        
        # 交互频率到状态的映射
        self.pattern_to_state: Dict[InteractionPattern, PetState] = {
            InteractionPattern.RARE: PetState.IDLE,
            InteractionPattern.OCCASIONAL: PetState.HAPPY,
            InteractionPattern.REGULAR: PetState.HAPPY,
            InteractionPattern.FREQUENT: PetState.HAPPY,
            InteractionPattern.EXCESSIVE: PetState.ANGRY  # 过度打扰会生气
        }
        
        self.logger.info("交互状态适配器初始化完成")
    
    def _initialize(self) -> bool:
        """初始化组件
        
        Returns:
            bool: 初始化是否成功
        """
        # 获取事件系统实例（如果尚未设置）
        if not hasattr(self, 'event_system') or self.event_system is None:
            self.event_system = EventSystem.get_instance()
        
        # 如果未指定状态机，尝试从事件系统获取
        if self._pet_state_machine is None:
            # 初始化未能获取到状态机实例，等待事件总线上有状态机事件时再获取
            self.logger.debug("未指定状态机实例，将等待状态机事件")
            
        # 注册事件监听
        self.event_system.register_handler(EventType.USER_INTERACTION, self._on_user_interaction)
        self.event_system.register_handler(EventType.STATE_CHANGED, self._on_state_changed)
        
        # 启动定时任务，定期检查交互状态超时
        self._setup_timeout_check()
        
        return True
    
    def _shutdown(self) -> bool:
        """关闭组件
        
        Returns:
            bool: 关闭是否成功
        """
        # 注销事件监听
        self.event_system.unregister_handler(EventType.USER_INTERACTION, self._on_user_interaction)
        self.event_system.unregister_handler(EventType.STATE_CHANGED, self._on_state_changed)
        
        # 清除交互状态
        if self._pet_state_machine is not None:
            self._pet_state_machine.set_interaction_state(None)
        
        return True
    
    def _setup_timeout_check(self) -> None:
        """设置超时检查
        
        创建一个定时器，定期检查交互状态是否超时
        """
        import threading
        
        def check_timeout():
            while self.is_active:
                # 检查是否有活动的交互状态，且是否超时
                if (self.current_interaction_state is not None and 
                    time.time() - self.last_interaction_time > self.interaction_timeout):
                    # 清除交互状态
                    self.clear_interaction_state()
                
                # 休眠一段时间
                time.sleep(1.0)
        
        # 创建并启动线程
        timeout_thread = threading.Thread(target=check_timeout)
        timeout_thread.daemon = True
        timeout_thread.start()
        
        self.logger.debug(f"已启动交互状态超时检查线程，超时时间: {self.interaction_timeout}秒")
    
    def _on_user_interaction(self, event: Any) -> None:
        """处理用户交互事件
        
        Args:
            event: 交互事件
        """
        if not hasattr(event, 'data'):
            return
            
        data = event.data
        if 'interaction_type' not in data or 'zone_id' not in data:
            return
            
        # 获取交互类型和区域ID
        interaction_type = data['interaction_type']
        zone_id = data['zone_id']
        
        # 记录最后交互时间
        self.last_interaction_time = time.time()
        
        # 获取对应的状态
        pet_state = self._get_state_from_interaction(interaction_type, zone_id)
        
        if pet_state is not None:
            # 更新当前交互状态
            self.current_interaction_state = pet_state
            
            # 更新状态机
            if self._pet_state_machine is not None:
                self._pet_state_machine.set_interaction_state(pet_state)
                self.logger.debug(f"设置交互状态: {pet_state.name}")
            else:
                self.logger.warning("未找到状态机实例，无法设置交互状态")
    
    def _on_state_changed(self, event: Any) -> None:
        """处理状态变化事件
        
        主要用于获取状态机实例（如果尚未获取）
        
        Args:
            event: 状态变化事件
        """
        if self._pet_state_machine is None and hasattr(event, 'sender'):
            sender = event.sender
            if isinstance(sender, PetStateMachine):
                self._pet_state_machine = sender
                self.logger.debug("已从事件获取状态机实例")
    
    def _get_state_from_interaction(self, interaction_type: str, zone_id: str) -> Optional[PetState]:
        """根据交互类型和区域ID获取对应的宠物状态
        
        Args:
            interaction_type: 交互类型（InteractionType枚举的name属性）
            zone_id: 交互区域ID
            
        Returns:
            Optional[PetState]: 对应的宠物状态，如果没有匹配项则返回None
        """
        # 首先尝试获取区域特定的交互状态
        zone_specific_key = f"{zone_id}_{interaction_type}"
        if zone_specific_key in self.interaction_to_state:
            return self.interaction_to_state[zone_specific_key]
        
        # 如果没有区域特定的映射，尝试使用通用交互类型
        if interaction_type in self.interaction_to_state:
            return self.interaction_to_state[interaction_type]
        
        return None
    
    def get_state_for_pattern(self, pattern: InteractionPattern) -> Optional[PetState]:
        """根据交互模式获取对应的宠物状态
        
        Args:
            pattern: 交互模式
            
        Returns:
            Optional[PetState]: 对应的宠物状态，如果没有匹配项则返回None
        """
        return self.pattern_to_state.get(pattern)
    
    def clear_interaction_state(self) -> None:
        """清除当前交互状态"""
        if self.current_interaction_state is not None:
            self.current_interaction_state = None
            
            # 更新状态机
            if self._pet_state_machine is not None:
                self._pet_state_machine.set_interaction_state(None)
                self.logger.debug("已清除交互状态")
    
    def set_interaction_timeout(self, timeout: float) -> None:
        """设置交互状态超时时间
        
        Args:
            timeout: 超时时间（秒）
        """
        self.interaction_timeout = timeout
        self.logger.debug(f"设置交互状态超时时间: {timeout}秒")
    
    def register_interaction_to_state(self, 
                                    interaction_type: str, 
                                    zone_id: Optional[str], 
                                    state: PetState) -> None:
        """注册交互类型到宠物状态的映射
        
        Args:
            interaction_type: 交互类型
            zone_id: 交互区域ID，如果为None则适用于所有区域
            state: 对应的宠物状态
        """
        if zone_id is None:
            # 通用交互映射
            self.interaction_to_state[interaction_type] = state
        else:
            # 区域特定交互映射
            self.interaction_to_state[f"{zone_id}_{interaction_type}"] = state
            
        self.logger.debug(f"注册交互到状态映射: {interaction_type} ({zone_id}) -> {state.name}") 