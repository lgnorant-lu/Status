"""
---------------------------------------------------------------
File name:                  pet_state_machine.py
Author:                     Ignorant-lu
Date created:               2025/05/13
Description:                宠物状态机，根据输入更新宠物状态
----------------------------------------------------------------
"""

import logging
from .pet_state import PetState # 使用相对导入

logger = logging.getLogger(__name__)

DEFAULT_BUSY_THRESHOLD = 30.0

class PetStateMachine:
    """管理宠物状态转换"""

    def __init__(self, busy_threshold: float = DEFAULT_BUSY_THRESHOLD):
        """初始化状态机

        Args:
            busy_threshold: CPU使用率达到多少时认为是 BUSY 状态
        """
        self.current_state = PetState.IDLE
        self.busy_threshold = busy_threshold
        logger.info(f"状态机初始化完成，初始状态: {self.current_state}, 忙碌阈值: {self.busy_threshold}")

    def update(self, cpu_usage: float) -> bool:
        """根据CPU使用率更新状态

        Args:
            cpu_usage: 当前CPU使用率 (0-100)

        Returns:
            bool: 状态是否发生了改变
        """
        previous_state = self.current_state
        
        # 实现状态转换逻辑
        if cpu_usage >= self.busy_threshold:
            self.current_state = PetState.BUSY
        else:
            self.current_state = PetState.IDLE
            
        logger.debug(f"Update: CPU={cpu_usage:.1f}, Threshold={self.busy_threshold}, State={self.current_state}")
        
        state_changed = self.current_state != previous_state
        if state_changed:
            logger.info(f"状态从 {previous_state.name} 变为 {self.current_state.name}")
        return state_changed

    def get_state(self) -> PetState:
        """获取当前状态"""
        return self.current_state 