"""
---------------------------------------------------------------
File name:                  emotion_system.py
Author:                     Ignorant-lu
Date created:               2025/04/04
Description:                桌宠情绪系统
----------------------------------------------------------------

Changed history:            
                            2025/04/04: 初始创建;
----
"""

import time
import math
import random
import logging
from enum import Enum, auto
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, Callable, Set, Union
from unittest.mock import Mock


class EmotionType(Enum):
    """情绪类型枚举"""
    HAPPY = auto()       # 快乐
    EXCITED = auto()     # 兴奋
    CALM = auto()        # 平静
    SAD = auto()         # 悲伤
    ANGRY = auto()       # 愤怒
    BORED = auto()       # 无聊
    SLEEPY = auto()      # 困倦
    CURIOUS = auto()     # 好奇
    NEUTRAL = auto()     # 中性


class EmotionalEventType(Enum):
    """情绪事件类型枚举"""
    # 用户交互事件
    USER_PET = auto()           # 用户抚摸
    USER_CLICK = auto()         # 用户点击
    USER_DRAG = auto()          # 用户拖拽
    USER_IGNORE = auto()        # 用户忽视
    USER_FREQUENT_INTERACT = auto()  # 用户频繁互动
    
    # 系统事件
    TASK_COMPLETE = auto()      # 任务完成
    TASK_FAIL = auto()          # 任务失败
    RESOURCE_LOW = auto()       # 资源不足
    RESOURCE_RESTORE = auto()   # 资源恢复
    STATE_CHANGE = auto()       # 状态变化
    
    # 环境事件
    TIME_MORNING = auto()       # 早晨时间
    TIME_NIGHT = auto()         # 夜晚时间
    SCREEN_BUSY = auto()        # 屏幕繁忙
    SCREEN_IDLE = auto()        # 屏幕空闲
    SYSTEM_STARTUP = auto()     # 系统启动
    SYSTEM_SHUTDOWN = auto()    # 系统关闭


@dataclass
class EmotionParams:
    """情绪参数数据类"""
    pleasure: float = 0.0    # 愉悦度 [-1.0, 1.0]
    arousal: float = 0.5     # 活跃度 [0.0, 1.0]
    social: float = 0.5      # 社交度 [0.0, 1.0]
    
    def __post_init__(self):
        """验证参数范围"""
        self.pleasure = max(-1.0, min(1.0, self.pleasure))
        self.arousal = max(0.0, min(1.0, self.arousal))
        self.social = max(0.0, min(1.0, self.social))
    
    def adjust(self, pleasure_delta: float = 0.0, arousal_delta: float = 0.0, social_delta: float = 0.0):
        """调整情绪参数
        
        Args:
            pleasure_delta: 愉悦度变化
            arousal_delta: 活跃度变化
            social_delta: 社交度变化
        """
        self.pleasure = max(-1.0, min(1.0, self.pleasure + pleasure_delta))
        self.arousal = max(0.0, min(1.0, self.arousal + arousal_delta))
        self.social = max(0.0, min(1.0, self.social + social_delta))


class EmotionalEvent:
    """情绪事件类"""
    
    def __init__(self, event_type: EmotionalEventType, intensity: float = 1.0,
                 pleasure_effect: float = 0.0, arousal_effect: float = 0.0, social_effect: float = 0.0):
        """初始化情绪事件
        
        Args:
            event_type: 事件类型
            intensity: 事件强度 [0.0, 1.0]
            pleasure_effect: 对愉悦度的影响
            arousal_effect: 对活跃度的影响
            social_effect: 对社交度的影响
        """
        self.event_type = event_type
        self.intensity = max(0.0, min(1.0, intensity))
        self.pleasure_effect = pleasure_effect
        self.arousal_effect = arousal_effect
        self.social_effect = social_effect
        self.timestamp = time.time()
    
    def apply_to(self, emotion_state: EmotionParams):
        """将事件效果应用到情绪状态
        
        Args:
            emotion_state: 情绪状态对象
        """
        # 应用效果时考虑强度
        emotion_state.adjust(
            pleasure_delta=self.pleasure_effect * self.intensity,
            arousal_delta=self.arousal_effect * self.intensity,
            social_delta=self.social_effect * self.intensity
        )


class EmotionState:
    """情绪状态类"""
    
    # 情绪类型判定阈值
    EMOTION_THRESHOLDS = {
        EmotionType.HAPPY: lambda p, a, s: p > 0.3 and 0.3 < a < 0.7,
        EmotionType.EXCITED: lambda p, a, s: p > 0.3 and a > 0.7,
        EmotionType.CALM: lambda p, a, s: -0.3 < p < 0.3 and a < 0.3,
        EmotionType.SAD: lambda p, a, s: p < -0.3 and a < 0.4,
        EmotionType.ANGRY: lambda p, a, s: p < -0.3 and a > 0.6,
        EmotionType.BORED: lambda p, a, s: -0.3 < p < 0.3 and a < 0.3 and s < 0.25,  # 调整社交度阈值，避免与CALM冲突
        EmotionType.SLEEPY: lambda p, a, s: -0.3 < p < 0.3 and a < 0.08,  # 调低活跃度阈值，避免与CALM冲突
        EmotionType.CURIOUS: lambda p, a, s: -0.1 < p < 0.5 and 0.3 < a < 0.7 and s > 0.6,
        EmotionType.NEUTRAL: lambda p, a, s: -0.2 < p < 0.2 and 0.4 < a < 0.6 and 0.4 < s < 0.6
    }
    
    def __init__(self, initial_params: Optional[EmotionParams] = None):
        """初始化情绪状态
        
        Args:
            initial_params: 初始情绪参数，如果为None则使用默认值
        """
        self.params = initial_params or EmotionParams()
        self.previous_emotion = EmotionType.NEUTRAL
        self.emotion_start_time = time.time()
        self.emotion_duration = 0.0
        self.logger = logging.getLogger("EmotionState")
        self.current_emotion = self._determine_emotion()
    
    def _determine_emotion(self) -> EmotionType:
        """根据当前参数确定情绪类型
        
        Returns:
            当前的情绪类型
        """
        p, a, s = self.params.pleasure, self.params.arousal, self.params.social
        
        # 检查每种情绪类型的条件
        matching_emotions = []
        for emotion_type, condition in self.EMOTION_THRESHOLDS.items():
            if condition(p, a, s):
                matching_emotions.append(emotion_type)
        
        if not matching_emotions:
            return EmotionType.NEUTRAL
        
        # 如果有多个匹配的情绪，且current_emotion已经定义，则尝试保持当前情绪以增加稳定性
        if hasattr(self, 'current_emotion') and self.current_emotion in matching_emotions:
            return self.current_emotion
        
        # 否则随机选择一个匹配的情绪
        return random.choice(matching_emotions)
    
    def update(self, dt: float):
        """更新情绪状态
        
        Args:
            dt: 时间增量（秒）
        """
        # 重新确定当前情绪
        new_emotion = self._determine_emotion()
        
        # 如果情绪发生变化，记录新情绪的开始时间
        if new_emotion != self.current_emotion:
            self.previous_emotion = self.current_emotion
            self.current_emotion = new_emotion
            self.emotion_start_time = time.time()
            self.logger.info(f"情绪变化: {self.previous_emotion.name} -> {self.current_emotion.name}")
        
        # 更新情绪持续时间
        self.emotion_duration = time.time() - self.emotion_start_time
    
    def apply_decay(self, dt: float, decay_rate: float = 0.1):
        """应用情绪参数衰减
        
        Args:
            dt: 时间增量（秒）
            decay_rate: 衰减率
        """
        # 计算衰减量
        decay_amount = dt * decay_rate
        
        # 愉悦度向0衰减
        if self.params.pleasure > 0:
            self.params.pleasure = max(0, self.params.pleasure - decay_amount)
        elif self.params.pleasure < 0:
            self.params.pleasure = min(0, self.params.pleasure + decay_amount)
        
        # 活跃度向0.5衰减
        if self.params.arousal > 0.5:
            self.params.arousal = max(0.5, self.params.arousal - decay_amount)
        elif self.params.arousal < 0.5:
            self.params.arousal = min(0.5, self.params.arousal + decay_amount)
        
        # 社交度向0.5衰减
        if self.params.social > 0.5:
            self.params.social = max(0.5, self.params.social - decay_amount)
        elif self.params.social < 0.5:
            self.params.social = min(0.5, self.params.social + decay_amount)
    
    def get_behavior_multipliers(self) -> Dict[str, float]:
        """获取行为选择的乘数
        
        Returns:
            行为ID到乘数的映射
        """
        # 基于当前情绪为不同行为提供权重乘数
        multipliers = {}
        
        if self.current_emotion == EmotionType.HAPPY:
            multipliers.update({
                'dance': 2.0,
                'jump': 1.5,
                'wave': 1.5,
                'idle': 0.8
            })
        elif self.current_emotion == EmotionType.EXCITED:
            multipliers.update({
                'jump': 2.0,
                'dance': 1.8,
                'move_random': 1.5,
                'wave': 1.5,
                'sleep': 0.2
            })
        elif self.current_emotion == EmotionType.CALM:
            multipliers.update({
                'idle': 2.0,
                'move_random': 0.8,
                'sleep': 1.2
            })
        elif self.current_emotion == EmotionType.SAD:
            multipliers.update({
                'idle': 2.5,
                'sleep': 1.5,
                'move_random': 0.5,
                'dance': 0.1,
                'jump': 0.2
            })
        elif self.current_emotion == EmotionType.ANGRY:
            multipliers.update({
                'jump': 1.5,
                'fall': 1.2,
                'move_random': 1.3,
                'sleep': 0.3,
                'wave': 0.4
            })
        elif self.current_emotion == EmotionType.BORED:
            multipliers.update({
                'idle': 3.0,
                'sleep': 2.0,
                'move_random': 0.5,
                'dance': 0.5,
                'jump': 0.5
            })
        elif self.current_emotion == EmotionType.SLEEPY:
            multipliers.update({
                'sleep': 5.0,
                'idle': 2.0,
                'move_random': 0.3,
                'jump': 0.1,
                'dance': 0.1
            })
        elif self.current_emotion == EmotionType.CURIOUS:
            multipliers.update({
                'move_random': 2.0,
                'jump': 1.3,
                'idle': 0.7,
                'sleep': 0.4
            })
        
        return multipliers
    
    def get_animation_params(self) -> Dict[str, float]:
        """获取动画参数修饰符
        
        Returns:
            参数名到值的映射
        """
        # 基于情绪参数计算动画修饰符
        p, a, s = self.params.pleasure, self.params.arousal, self.params.social
        
        return {
            'speed_multiplier': 0.5 + a,  # 基于活跃度调整速度
            'size_multiplier': 1.0 + 0.2 * p,  # 高愉悦度略微放大
            'color_intensity': 0.5 + 0.5 * abs(p),  # 情绪强度影响颜色强度
            'interaction_range': 1.0 + 0.5 * s  # 社交度影响交互范围
        }


class EmotionSystem:
    """情绪系统类"""
    
    # 默认情绪事件映射
    DEFAULT_EVENT_MAPPINGS = {
        EmotionalEventType.USER_PET: EmotionalEvent(
            EmotionalEventType.USER_PET, 
            pleasure_effect=0.1, 
            arousal_effect=0.05, 
            social_effect=0.1
        ),
        EmotionalEventType.USER_CLICK: EmotionalEvent(
            EmotionalEventType.USER_CLICK, 
            pleasure_effect=0.05, 
            arousal_effect=0.1, 
            social_effect=0.05
        ),
        EmotionalEventType.USER_DRAG: EmotionalEvent(
            EmotionalEventType.USER_DRAG, 
            pleasure_effect=0.0, 
            arousal_effect=0.15, 
            social_effect=0.05
        ),
        EmotionalEventType.USER_IGNORE: EmotionalEvent(
            EmotionalEventType.USER_IGNORE, 
            pleasure_effect=-0.1, 
            arousal_effect=-0.05, 
            social_effect=-0.1
        ),
        EmotionalEventType.USER_FREQUENT_INTERACT: EmotionalEvent(
            EmotionalEventType.USER_FREQUENT_INTERACT, 
            pleasure_effect=-0.05, 
            arousal_effect=0.2, 
            social_effect=-0.05
        ),
        EmotionalEventType.TASK_COMPLETE: EmotionalEvent(
            EmotionalEventType.TASK_COMPLETE, 
            pleasure_effect=0.2, 
            arousal_effect=0.1, 
            social_effect=0.0
        ),
        EmotionalEventType.TASK_FAIL: EmotionalEvent(
            EmotionalEventType.TASK_FAIL, 
            pleasure_effect=-0.2, 
            arousal_effect=0.05, 
            social_effect=-0.05
        ),
        EmotionalEventType.RESOURCE_LOW: EmotionalEvent(
            EmotionalEventType.RESOURCE_LOW, 
            pleasure_effect=-0.1, 
            arousal_effect=-0.1, 
            social_effect=0.0
        ),
        EmotionalEventType.RESOURCE_RESTORE: EmotionalEvent(
            EmotionalEventType.RESOURCE_RESTORE, 
            pleasure_effect=0.15, 
            arousal_effect=0.1, 
            social_effect=0.0
        ),
        EmotionalEventType.STATE_CHANGE: EmotionalEvent(
            EmotionalEventType.STATE_CHANGE, 
            pleasure_effect=0.0, 
            arousal_effect=0.1, 
            social_effect=0.0
        ),
        EmotionalEventType.TIME_MORNING: EmotionalEvent(
            EmotionalEventType.TIME_MORNING, 
            pleasure_effect=0.1, 
            arousal_effect=0.2, 
            social_effect=0.1
        ),
        EmotionalEventType.TIME_NIGHT: EmotionalEvent(
            EmotionalEventType.TIME_NIGHT, 
            pleasure_effect=0.05, 
            arousal_effect=-0.3, 
            social_effect=-0.1
        ),
        EmotionalEventType.SCREEN_BUSY: EmotionalEvent(
            EmotionalEventType.SCREEN_BUSY, 
            pleasure_effect=-0.05, 
            arousal_effect=0.1, 
            social_effect=-0.05
        ),
        EmotionalEventType.SCREEN_IDLE: EmotionalEvent(
            EmotionalEventType.SCREEN_IDLE, 
            pleasure_effect=0.05, 
            arousal_effect=-0.1, 
            social_effect=0.05
        ),
        EmotionalEventType.SYSTEM_STARTUP: EmotionalEvent(
            EmotionalEventType.SYSTEM_STARTUP, 
            pleasure_effect=0.2, 
            arousal_effect=0.3, 
            social_effect=0.1
        ),
        EmotionalEventType.SYSTEM_SHUTDOWN: EmotionalEvent(
            EmotionalEventType.SYSTEM_SHUTDOWN, 
            pleasure_effect=0.0, 
            arousal_effect=-0.2, 
            social_effect=-0.1
        )
    }
    
    def __init__(self, entity=None, initial_state: Optional[EmotionState] = None):
        """初始化情绪系统
        
        Args:
            entity: 关联的实体对象
            initial_state: 初始情绪状态，如果为None则创建默认状态
        """
        self.entity = entity
        self.emotion_state = initial_state or EmotionState()
        self.event_mappings = self.DEFAULT_EVENT_MAPPINGS.copy()
        self.recent_events = []  # 最近的事件历史
        self.last_update_time = time.time()
        self.decay_rate = 0.05  # 情绪衰减率
        self.max_event_history = 20  # 事件历史最大长度
        self.logger = logging.getLogger("EmotionSystem")
        self.logger.info("情绪系统已初始化")
    
    def update(self, dt: float = None):
        """更新情绪系统
        
        Args:
            dt: 时间增量（秒），如果为None则计算自上次更新的时间
        """
        current_time = time.time()
        
        # 计算时间增量
        if dt is None:
            dt = current_time - self.last_update_time
        
        # 应用情绪衰减
        self.emotion_state.apply_decay(dt, self.decay_rate)
        
        # 更新情绪状态
        self.emotion_state.update(dt)
        
        # 处理特殊情况，如长时间无交互
        self._handle_special_conditions(dt)
        
        # 更新最后更新时间
        self.last_update_time = current_time
    
    def _handle_special_conditions(self, dt: float):
        """处理特殊条件下的情绪变化
        
        Args:
            dt: 时间增量（秒）
        """
        # 示例：长时间没有事件，增加无聊情绪
        try:
            if not self.recent_events and not isinstance(self.emotion_state.emotion_duration, Mock) and self.emotion_state.emotion_duration > 60:
                # 增加无聊情绪
                if self.emotion_state.current_emotion != EmotionType.BORED:
                    self.emotion_state.params.adjust(
                        pleasure_delta=-0.2 * dt,
                        arousal_delta=-0.3 * dt
                    )
                    self.logger.debug("长时间无事件，增加无聊情绪")
                
            # 示例：多个事件在短时间内，增加兴奋情绪
            if len(self.recent_events) > 5:
                # 检查最近的事件是否都在短时间内发生
                now = time.time()
                recent_time_window = 10  # 10秒内
                recent_count = sum(1 for event in self.recent_events 
                                  if now - event.timestamp < recent_time_window)
                
                if recent_count > 3:
                    self.emotion_state.params.adjust(
                        arousal_delta=0.2 * dt,
                        pleasure_delta=0.1 * dt
                    )
                    self.logger.debug("短时间内多个事件，增加兴奋情绪")
        except Exception as e:
            self.logger.warning(f"处理特殊条件时发生错误: {e}")
    
    def process_event(self, event_type: EmotionalEventType, intensity: float = 1.0, custom_effects: Dict = None):
        """处理情绪事件
        
        Args:
            event_type: 事件类型
            intensity: 事件强度 [0.0, 1.0]
            custom_effects: 自定义事件效果 {'pleasure': float, 'arousal': float, 'social': float}
            
        Returns:
            bool: 事件是否成功处理
        """
        # 获取事件模板
        if event_type not in self.event_mappings:
            self.logger.warning(f"未知情绪事件类型: {event_type}")
            return False
        
        template_event = self.event_mappings[event_type]
        
        # 创建事件实例
        event = EmotionalEvent(
            event_type=event_type,
            intensity=intensity,
            pleasure_effect=custom_effects.get('pleasure', template_event.pleasure_effect) if custom_effects else template_event.pleasure_effect,
            arousal_effect=custom_effects.get('arousal', template_event.arousal_effect) if custom_effects else template_event.arousal_effect,
            social_effect=custom_effects.get('social', template_event.social_effect) if custom_effects else template_event.social_effect
        )
        
        # 应用事件效果
        event.apply_to(self.emotion_state.params)
        
        # 添加到事件历史
        self.recent_events.append(event)
        if len(self.recent_events) > self.max_event_history:
            self.recent_events.pop(0)
        
        self.logger.debug(f"处理情绪事件: {event_type.name}, 强度: {intensity:.2f}")
        
        # 更新情绪状态
        self.emotion_state.update(0)
        
        return True
    
    def register_custom_event(self, event_type: EmotionalEventType, pleasure_effect: float = 0.0,
                              arousal_effect: float = 0.0, social_effect: float = 0.0):
        """注册自定义事件效果
        
        Args:
            event_type: 事件类型
            pleasure_effect: 对愉悦度的影响
            arousal_effect: 对活跃度的影响
            social_effect: 对社交度的影响
            
        Returns:
            bool: 是否成功注册
        """
        self.event_mappings[event_type] = EmotionalEvent(
            event_type=event_type,
            pleasure_effect=pleasure_effect,
            arousal_effect=arousal_effect,
            social_effect=social_effect
        )
        
        self.logger.info(f"注册自定义情绪事件: {event_type.name}")
        return True
    
    def get_current_emotion(self) -> EmotionType:
        """获取当前情绪类型
        
        Returns:
            当前的情绪类型
        """
        return self.emotion_state.current_emotion
    
    def get_emotion_params(self) -> EmotionParams:
        """获取当前情绪参数
        
        Returns:
            当前的情绪参数
        """
        return self.emotion_state.params
    
    def get_emotion_duration(self) -> float:
        """获取当前情绪持续时间(秒)
        
        Returns:
            当前情绪持续时间
        """
        return self.emotion_state.emotion_duration
    
    def get_behavior_multipliers(self) -> Dict[str, float]:
        """获取行为选择的乘数
        
        Returns:
            行为ID到乘数的映射
        """
        return self.emotion_state.get_behavior_multipliers()
    
    def get_animation_params(self) -> Dict[str, float]:
        """获取动画参数修饰符
        
        Returns:
            参数名到值的映射
        """
        return self.emotion_state.get_animation_params()
    
    def set_decay_rate(self, rate: float):
        """设置情绪衰减率
        
        Args:
            rate: 衰减率 [0.0, 1.0]
        """
        self.decay_rate = max(0.0, min(1.0, rate))
        self.logger.debug(f"设置情绪衰减率: {self.decay_rate}")


# 创建情绪系统的全局实例
_emotion_system_instance = None

def get_emotion_system(entity=None):
    """获取全局情绪系统实例
    
    Args:
        entity: 关联的实体对象
        
    Returns:
        EmotionSystem: 情绪系统实例
    """
    global _emotion_system_instance
    if _emotion_system_instance is None:
        _emotion_system_instance = EmotionSystem(entity)
    return _emotion_system_instance


# 初始化默认事件映射的函数
def initialize_default_emotion_events():
    """初始化默认情绪事件映射"""
    system = get_emotion_system()
    # 已在EmotionSystem初始化中设置默认事件映射
    logging.getLogger("EmotionSystem").info("默认情绪事件映射已初始化") 