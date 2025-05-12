"""
---------------------------------------------------------------
File name:                  emotion_system.py
Author:                     Ignorant-lu
Date created:               2025/04/04
Description:                桌宠情绪系统
----------------------------------------------------------------

Changed history:            
                            2025/04/04: 初始创建;
                            2025/05/18: 修复类型注解和函数调用问题;
----
"""

import time
import math
import random
import logging
from collections import deque
from enum import Enum, auto
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, Callable, Set, Union, Any
from unittest.mock import Mock
from status.core.events import Event, EventType, EventManager
from status.utils.decay import exponential_decay


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
            pleasure_effect: 对愉悦度的基础影响
            arousal_effect: 对活跃度的基础影响
            social_effect: 对社交度的基础影响
        """
        self.event_type = event_type
        self.intensity = max(0.0, min(1.0, intensity)) # Store passed intensity
        self.pleasure_effect = pleasure_effect # Store base pleasure effect
        self.arousal_effect = arousal_effect   # Store base arousal effect
        self.social_effect = social_effect     # Store base social effect
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
        EmotionType.BORED: lambda p, a, s: -0.3 < p < 0.3 and a < 0.3 and s < 0.15,
        EmotionType.SLEEPY: lambda p, a, s: -0.3 < p < 0.3 and a < 0.08,
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
    
    def __init__(self, entity=None, initial_state: Optional[EmotionState] = None,
                 initial_emotions: Optional[Dict[str, float]] = None,
                 emotion_decay_rate: float = 0.1,
                 event_emotion_mapping: Optional[Dict[EventType, Dict[str, float]]] = None,
                 short_term_memory_duration: float = 60.0,
                 long_term_mood_influence: float = 0.2):
        """初始化情绪系统
        
        Args:
            entity: 关联的实体对象
            initial_state: 初始情绪状态，如果为None则创建默认状态
            initial_emotions: 初始情绪字典
            emotion_decay_rate: 情绪衰减率
            event_emotion_mapping: 事件到情绪影响的映射
            short_term_memory_duration: 短期记忆持续时间
            long_term_mood_influence: 长期情绪影响权重
        """
        self.entity = entity
        self.emotion_state = initial_state or EmotionState()
        self.event_mappings = self.DEFAULT_EVENT_MAPPINGS.copy()
        self.last_update_time = time.time()
        self.decay_rate = emotion_decay_rate
        self.max_event_history = 20  # 事件历史最大长度
        self.logger = logging.getLogger("EmotionSystem")
        self.logger.info("情绪系统已初始化")
        self.emotions: Dict[str, EmotionState] = {}
        self.current_mood: float = 0.5 # Example: Neutral mood
        self.short_term_decay_time = short_term_memory_duration
        self.long_term_mood_influence = long_term_mood_influence
        # 定义带类型注解的recent_events，避免重复定义
        self.recent_events: List[Tuple[float, EmotionalEvent]] = []

        if initial_emotions:
            for name, value in initial_emotions.items():
                self.emotions[name] = EmotionState(EmotionParams(pleasure=value, arousal=value, social=value))
        else:
            self._initialize_default_emotions()
    
    def _initialize_default_emotions(self):
        """初始化默认情绪状态"""
        self.emotions = {
            "joy": EmotionState(EmotionParams(pleasure=0.8, arousal=0.6, social=0.7)),
            "sadness": EmotionState(EmotionParams(pleasure=-0.7, arousal=0.3, social=0.4)),
            "anger": EmotionState(EmotionParams(pleasure=-0.6, arousal=0.8, social=0.3)),
            "fear": EmotionState(EmotionParams(pleasure=-0.6, arousal=0.7, social=0.3)),
            "surprise": EmotionState(EmotionParams(pleasure=0.5, arousal=0.8, social=0.6)),
            "disgust": EmotionState(EmotionParams(pleasure=-0.6, arousal=0.5, social=0.3)),
            "neutral": EmotionState(EmotionParams(pleasure=0.0, arousal=0.5, social=0.5))
        }
        self.logger.debug("初始化默认情绪状态")
    
    def update(self, dt: Optional[float] = None):
        """更新情绪系统状态

        Args:
            dt: 时间增量（秒）。如果为None，则尝试使用内部计时器（如果实现）。
        """
        current_time = time.time() # Get current time
        if dt is None:
            # If dt is not provided, calculate it from last_update_time
            # This makes the method more robust if called without dt
            actual_dt = current_time - self.last_update_time
        else:
            actual_dt = dt

        if self.emotion_state:
            if self.decay_rate > 0 and actual_dt > 0:
                self.emotion_state.apply_decay(actual_dt, self.decay_rate)
            
            self.emotion_state.update(actual_dt)
            
            self._handle_special_conditions(actual_dt)
        
        self.last_update_time = current_time # Update last_update_time

    def _handle_special_conditions(self, dt: float):
        """处理特殊情绪条件，如长时间不活动导致无聊等"""
        # ... (implementation of _handle_special_conditions) ...
        pass

    def process_event(self, event_type: Optional[EmotionalEventType], intensity: float = 1.0, custom_effects: Optional[Dict[str, float]] = None):
        """处理外部情绪事件

        Args:
            event_type: 情绪事件类型
            intensity: 事件强度
            custom_effects: 自定义情绪效果字典 (pleasure, arousal, social)
        """
        if not self.emotion_state:
            self.logger.warning("当前情绪状态未初始化，无法处理事件")
            return False # Explicitly return False

        event_to_apply: Optional[EmotionalEvent] = None
        effects_to_use = custom_effects if custom_effects is not None else {}

        if custom_effects is not None:
            if event_type is None:
                self.logger.debug(f"处理自定义效果事件 (无特定类型, 强度: {intensity})")
                # Pass through to create EmotionalEvent with custom effects and external intensity

            event_to_apply = EmotionalEvent(
                event_type=event_type if event_type else EmotionalEventType.STATE_CHANGE, # Use a default if None
                intensity=intensity, # Pass the external intensity
                pleasure_effect=effects_to_use.get('pleasure', 0.0), # Pass base effect
                arousal_effect=effects_to_use.get('arousal', 0.0),   # Pass base effect
                social_effect=effects_to_use.get('social', 0.0)     # Pass base effect
            )
        elif event_type is not None and event_type in self.event_mappings:
            base_event = self.event_mappings[event_type]
            event_to_apply = EmotionalEvent(
                event_type=base_event.event_type,
                intensity=intensity, # Pass the external intensity
                pleasure_effect=base_event.pleasure_effect, # Pass base effect from mapping
                arousal_effect=base_event.arousal_effect,   # Pass base effect from mapping
                social_effect=base_event.social_effect     # Pass base effect from mapping
            )
        else:
            if event_type is None:
                self.logger.warning("处理事件失败：event_type 为 None 且未提供 custom_effects。")
            else:
                self.logger.warning(f"未找到事件类型 {event_type.name} 的映射，且未提供自定义效果")
            return False # Explicitly return False

        if event_to_apply:
            log_event_name = event_type.name if event_type else "CUSTOM_EFFECTS"
            self.logger.debug(f"处理事件: {log_event_name} (强度: {intensity}), 效果: P={event_to_apply.pleasure_effect:.2f}, A={event_to_apply.arousal_effect:.2f}, S={event_to_apply.social_effect:.2f}")
            event_to_apply.apply_to(self.emotion_state.params)
            self.emotion_state.update(0)
            
            # Add to recent_events
            self.recent_events.append((time.time(), event_to_apply))
            if len(self.recent_events) > self.max_event_history:
                self.recent_events.pop(0)
            return True
        
        return False

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

    def _update_short_term_mood(self, current_time: float) -> None:
        """更新短期情绪，考虑最近事件的衰减影响"""
        # Use deque's automatic removal of old items if maxlen is set properly
        # Or manually remove if maxlen isn't used or needs finer control
        # Manual removal example:
        while self.recent_events and current_time - self.recent_events[0][0] > self.short_term_decay_time:
            self.recent_events.pop(0)

        # --- Calculate mood based on recent events --- 
        mood_shift = 0.0
        # Add type hint for loop variable
        timestamp: float 
        event: EmotionalEvent
        for timestamp, event in self.recent_events:
            if event.event_type in self.event_mappings:
                # 获取事件对应的情绪事件对象
                base_event = self.event_mappings[event.event_type]
                # 修复调用：添加dt参数，计算时间差作为dt
                time_elapsed = current_time - timestamp
                time_decay = exponential_decay(value=1.0, decay_rate=0.1, dt=time_elapsed)
                
                # 计算特定事件的情绪影响
                pleasure_effect = base_event.pleasure_effect
                arousal_effect = base_event.arousal_effect
                social_effect = base_event.social_effect
                
                # 使用各个效果的总和来计算心情偏移
                if pleasure_effect > 0:
                    mood_shift += pleasure_effect * time_decay * 0.1  # Scale factor
                elif pleasure_effect < 0:
                    mood_shift -= abs(pleasure_effect) * time_decay * 0.1  # Scale factor
                
                if arousal_effect != 0:
                    # 活跃度有小影响
                    mood_shift += arousal_effect * time_decay * 0.05
                
                if social_effect > 0:
                    # 积极社交效果提升心情
                    mood_shift += social_effect * time_decay * 0.07
                
        # Apply mood shift to current mood (can be more complex)
        # self.current_mood += mood_shift # Direct application (can drift easily)
        # Example: Move towards a target mood based on shift
        target_mood = 0.5 + mood_shift # Target around neutral 0.5
        target_mood = max(0.0, min(1.0, target_mood)) # Clamp to [0, 1]
        # Smoothly update towards target mood
        self.current_mood += (target_mood - self.current_mood) * 0.1 # Smoothing factor
        self.current_mood = max(0.0, min(1.0, self.current_mood)) # Clamp final mood


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