"""
---------------------------------------------------------------
File name:                  pet_state.py
Author:                     Ignorant-lu
Date created:               2025/05/13
Description:                定义宠物状态的枚举
----------------------------------------------------------------

Changed history:            
                            2025/05/13: 初始创建;
                            2025/05/13: 添加时间相关状态;
                            2025/05/13: 细化CPU负载状态;
                            2025/05/13: 添加交互相关状态;
----
"""

from enum import Enum, auto

class PetState(Enum):
    """宠物状态枚举
    
    不同状态用于表示宠物的不同行为
    
    状态值的范围划分：
    - 1-50: 系统负载状态
    - 51-100: 特殊系统事件状态
    - 101-150: 时间相关状态
    - 151-200: 用户交互状态
    """
    
    # 基础状态
    IDLE = 1  # 空闲状态 (0-20% CPU)
    
    # 细化的CPU负载状态
    LIGHT_LOAD = 2      # 轻微负载 (20-40% CPU)
    MODERATE_LOAD = 3   # 中等负载 (40-60% CPU)
    HEAVY_LOAD = 4      # 高负载 (60-80% CPU)
    VERY_HEAVY_LOAD = 5 # 极重负载 (80-100% CPU)
    
    # 兼容旧版本的状态映射 (保留但内部使用上面的细分状态)
    BUSY = MODERATE_LOAD      # 忙碌状态 (等同于中等负载)
    VERY_BUSY = HEAVY_LOAD    # 非常忙碌状态 (等同于高负载)
    
    # 内存状态
    MEMORY_WARNING = 20    # 内存警告状态 (内存使用 > 70%)
    MEMORY_CRITICAL = 21   # 内存临界状态 (内存使用 > 90%)
    
    # 系统资源状态
    DISK_BUSY = 30         # 磁盘繁忙状态
    DISK_VERY_BUSY = 31    # 磁盘极度繁忙状态
    
    NETWORK_BUSY = 35      # 网络繁忙状态
    NETWORK_VERY_BUSY = 36 # 网络极度繁忙状态
    
    GPU_BUSY = 40          # GPU繁忙状态
    GPU_VERY_BUSY = 41     # GPU极度繁忙状态
    
    SYSTEM_IDLE = 45       # 系统完全空闲状态
    CPU_CRITICAL = VERY_HEAVY_LOAD # CPU临界状态 (等同于VERY_HEAVY_LOAD)
    
    # 特殊系统事件状态
    LOW_BATTERY = 51       # 低电量状态
    CHARGING = 52          # 充电状态
    FULLY_CHARGED = 53     # 电量充满状态
    SYSTEM_UPDATE = 54     # 系统更新状态
    SYSTEM_ERROR = 55      # 系统错误状态
    
    # 时间相关状态
    MORNING = 101          # 早晨状态
    NOON = 102             # 中午状态
    AFTERNOON = 103        # 下午状态
    EVENING = 104          # 晚上状态
    NIGHT = 105            # 深夜状态
    
    # 特殊日期状态
    BIRTHDAY = 121         # 生日状态
    NEW_YEAR = 122         # 新年状态
    VALENTINE = 123        # 情人节状态
    SPRING_FESTIVAL = 124  # 春节状态
    LICHUN = 125           # 立春状态
    
    # 用户交互状态
    HAPPY = 151            # 开心状态
    SAD = 152              # 难过状态
    ANGRY = 153            # 生气状态
    SLEEP = 154            # 睡眠状态
    PLAY = 155             # 玩耍状态
    CLICKED = 156          # 被点击状态
    DRAGGED = 157          # 被拖拽状态
    PETTED = 158           # 被抚摸状态
    HOVER = 159            # 鼠标悬停状态
    
    # 交互相关状态 (待后续行为系统细化或重新分类)
    # SLEEPING = 159         # 睡眠中
    # THINKING = 160         # 思考中
    # WALKING = 161          # 行走中
    # WORKING = 162          # 工作中
    
    # 身体区域交互状态 (待后续细化交互实现)
    # HEAD_CLICKED = 163     # 头部点击
    # BODY_CLICKED = 164     # 身体点击
    # TAIL_CLICKED = 165     # 尾部点击
    
    # HEAD_PETTED = 166       # 头部抚摸
    # BODY_PETTED = 167       # 身体抚摸
    # TAIL_PETTED = 168       # 尾部抚摸
    
    # 未来可以添加更多状态，例如：
    # INTERACTING = 4  # 交互状态
    # SLEEPING = 5     # 睡眠状态
    # EATING = 6       # (如果引入需求概念)
    # 可以根据需要添加更多状态，如：
    # INTERACTING = auto() # 交互中
    # SLEEPING = auto()    # 睡眠中
    # VERY_BUSY = auto()   # 非常忙碌 

    # @classmethod
    # def is_interaction_state(cls, state_id: int) -> bool:
    #     """判断是否为交互状态
        
    #     Args:
    #         state_id: 状态ID
            
    #     Returns:
    #         bool: 如果是交互状态则返回True
    #     """
    #     return state_id >= 151 and state_id < 160 