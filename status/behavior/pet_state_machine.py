"""
---------------------------------------------------------------
File name:                  pet_state_machine.py
Author:                     Ignorant-lu
Date created:               2025/05/13
Description:                宠物状态机，根据输入更新宠物状态
----------------------------------------------------------------
"""

import logging
from status.behavior.pet_state import PetState

logger = logging.getLogger(__name__)

class PetStateMachine:
    """管理桌宠状态的简单状态机"""

    def __init__(self, cpu_threshold: float = 30.0, memory_threshold: float = 80.0):
        """初始化状态机

        Args:
            cpu_threshold (float): CPU使用率阈值，高于此值进入BUSY状态。
            memory_threshold (float): 内存使用率阈值，高于此值进入MEMORY_WARNING状态。
        """
        self.current_state = PetState.IDLE
        self.cpu_threshold = cpu_threshold
        self.memory_threshold = memory_threshold
        logger.info(f"状态机初始化完成。当前状态: {self.current_state.name}, CPU阈值: {self.cpu_threshold}%, 内存阈值: {self.memory_threshold}%")

    def update(self, cpu_usage: float, memory_usage: float) -> bool:
        """根据系统使用率更新状态

        Args:
            cpu_usage (float): 当前 CPU 使用率。
            memory_usage (float): 当前内存使用率。

        Returns:
            bool: 如果状态发生改变则返回 True，否则返回 False。
        """
        previous_state = self.current_state
        new_state = previous_state

        # 1. 检查内存警告 (最高优先级)
        if memory_usage >= self.memory_threshold:
            new_state = PetState.MEMORY_WARNING
        else:
            # 2. 如果内存正常，则根据 CPU 使用率判断 IDLE/BUSY
            if cpu_usage >= self.cpu_threshold:
                new_state = PetState.BUSY
            else:
                # 只有在 CPU 低于阈值且内存也低于阈值时才进入 IDLE
                # （如果之前是 MEMORY_WARNING，现在内存恢复了，且 CPU 低，则变为 IDLE）
                new_state = PetState.IDLE

        # 检查状态是否真的改变
        state_changed = new_state != previous_state
        if state_changed:
            logger.info(f"状态从 {previous_state.name} 变为 {new_state.name} (CPU: {cpu_usage:.1f}%, Mem: {memory_usage:.1f}%)")
            self.current_state = new_state
        
        return state_changed

    def get_state(self) -> PetState:
        """获取当前状态"""
        return self.current_state 