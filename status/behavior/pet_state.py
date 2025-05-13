"""
---------------------------------------------------------------
File name:                  pet_state.py
Author:                     Ignorant-lu
Date created:               2025/05/13
Description:                定义宠物状态的枚举
----------------------------------------------------------------
"""

from enum import Enum, auto

class PetState(Enum):
    """宠物可能的状态"""
    IDLE = auto()  # 空闲状态
    BUSY = auto()  # 忙碌状态 (例如，基于CPU负载)
    # 可以根据需要添加更多状态，如：
    # INTERACTING = auto() # 交互中
    # SLEEPING = auto()    # 睡眠中
    # VERY_BUSY = auto()   # 非常忙碌 