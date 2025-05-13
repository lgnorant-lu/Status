"""
---------------------------------------------------------------
File name:                  pet_state.py
Author:                     Ignorant-lu
Date created:               2025/05/13
Description:                定义宠物状态的枚举
----------------------------------------------------------------
"""

from enum import Enum

class PetState(Enum):
    """定义桌宠可能的状态"""
    IDLE = 1         # 空闲状态
    BUSY = 2         # 忙碌状态 (例如，CPU 高负载)
    MEMORY_WARNING = 3 # 内存警告状态
    # 未来可以添加更多状态，例如：
    # INTERACTING = 4  # 交互状态
    # SLEEPING = 5     # 睡眠状态
    # EATING = 6       # (如果引入需求概念)
    # 可以根据需要添加更多状态，如：
    # INTERACTING = auto() # 交互中
    # SLEEPING = auto()    # 睡眠中
    # VERY_BUSY = auto()   # 非常忙碌 