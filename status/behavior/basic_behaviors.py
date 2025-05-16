"""
---------------------------------------------------------------
File name:                  basic_behaviors.py
Author:                     Ignorant-lu
Date created:               2025/04/05
Description:                基础行为定义
----------------------------------------------------------------

Changed history:            
                            2025/04/05: 初始创建;
                            2025/05/12: 添加类型注解;
                            2025/05/13: 修复类型不兼容问题;
                            2025/05/13: 解决子类继承参数传递问题;
                            2025/05/13: 修复decay导入问题;
----
"""

import logging
import time
import random
import math
from typing import Optional, Dict, List, Any, Tuple, Callable, cast, Type, Union
from enum import Enum, auto

from PySide6.QtCore import QPointF, QPoint, QRect
from PySide6.QtGui import QColor

from status.core.component_base import ComponentBase
from status.utils.vector import Vector2D
from status.behavior.environment_sensor import EnvironmentSensor
from status.utils.decay import ExponentialDecay


class BehaviorType(Enum):
    """行为类型枚举"""
    IDLE = auto()  # 空闲
    LOCOMOTION = auto()  # 移动
    INTERACTION = auto()  # 互动
    EMOTION = auto()  # 情绪表达
    SYSTEM = auto()  # 系统行为
    CUSTOM = auto()  # 自定义
    WALK = auto()  # 走路


class BehaviorBase(ComponentBase):
    """行为基类，所有行为都应继承自此类"""
    
    def __init__(self, name: str, duration: Optional[float] = None, params: Optional[Dict[str, Any]] = None):
        """初始化行为
        
        Args:
            name: 行为名称
            duration: 行为持续时间(秒)，None表示无限持续
            params: 行为参数
        """
        super().__init__()
        self.name = name
        
        # 行为持续时间
        self.duration: Optional[float] = duration
        
        # 行为参数
        self.params: Dict[str, Any] = params or {}
        
        # 行为状态
        self.is_active: bool = False
        self.is_complete: bool = False
        self.is_interrupted: bool = False
        
        # 计时器
        self.elapsed_time: float = 0.0
        
        # 优先级
        self.priority: float = self.params.get('priority', 5.0)  # 1-10，10最高
        
        # 对象引用
        self.entity: Any = None
        
        # 行为类型
        self.behavior_type: BehaviorType = BehaviorType.CUSTOM
        
        # 循环标志
        self.loop: bool = False
        
        # 时间相关
        self.start_time: Optional[float] = None
        self.time_needed: Optional[float] = None
        
        # 位置相关
        self.start_x: Optional[float] = None
        self.start_y: Optional[float] = None
        self.current_x: Optional[float] = None
        self.current_y: Optional[float] = None
        self.target_x: Optional[float] = None
        self.target_y: Optional[float] = None
        
        # 环境传感器
        self.environment_sensor: Optional[EnvironmentSensor] = None
        
        # 运行状态 - 添加测试需要的属性
        self.is_running: bool = False
    
    def start(self, params: Optional[Dict[str, Any]] = None) -> None:
        """启动行为
        
        Args:
            params: 行为参数，可覆盖初始化时设定的参数
        """
        # 合并参数
        if params:
            self.params.update(params)
        
        # 设置开始时间
        self.start_time = time.time()
        self.is_running = True
        self.is_active = True
        self.is_complete = False
        self.is_interrupted = False
        self.elapsed_time = 0.0
        
        # 调用子类的开始回调
        self._on_start()
        
    def update(self, dt: float) -> bool:  # type: ignore[override]
        """更新行为
        
        Args:
            dt: 时间增量(秒)
        
        Returns:
            bool: 行为是否完成
        """
        # 如果行为未运行，立即返回已完成
        if not self.is_running:
            return True
        
        # 更新计时器
        self.elapsed_time += dt
        
        # 检查持续时间
        if self.duration is not None and self.start_time is not None:
            if time.time() - self.start_time >= self.duration:
                if self.loop:
                    self.start_time = time.time() # 重置开始时间
                    self._on_update(dt)  # 调用 _on_update 以执行其逻辑
                    return False  # 返回 False 表示行为仍在继续（新循环）
                else:
                    # 完成行为
                    self.is_running = False
                    self.is_active = False
                    self.is_complete = True
                    self._on_complete()
                    return True
        
        # 调用子类的更新方法
        should_continue = self._on_update(dt)
        
        # 如果子类指示应该停止
        if not should_continue:
            self.is_running = False
            self.is_active = False
            self.is_complete = True
            self._on_complete()
            return True
        
        return False
    
    def stop(self) -> None:
        """停止行为"""
        if self.is_running:
            self.is_running = False
            self.is_active = False
            self.is_interrupted = True
            
            # 调用子类的结束回调
            self._on_stop()
    
    def _on_start(self) -> None:
        """开始行为时的回调，子类应重写此方法"""
        pass
    
    def _on_update(self, dt: float) -> bool:
        """更新行为时的回调，子类应重写此方法
        
        Args:
            dt: 时间增量(秒)
        
        Returns:
            bool: 是否继续行为
        """
        return True
    
    def _on_stop(self) -> None:
        """停止行为时的回调，子类应重写此方法"""
        pass
        
    def _on_complete(self) -> None:
        """完成时的回调，子类可重写此方法"""
        pass
    
    def set_entity(self, entity: Any) -> None:
        """设置关联的实体
        
        Args:
            entity: 行为关联的实体
        """
        self.entity = entity


class BehaviorRegistry:
    """行为注册表
    
    单例模式，用于管理所有注册的行为类型
    """
    _instance = None
    
    @staticmethod
    def get_instance():
        """获取行为注册表实例"""
        if BehaviorRegistry._instance is None:
            BehaviorRegistry._instance = BehaviorRegistry()
        return BehaviorRegistry._instance
    
    def __init__(self):
        """初始化行为注册表"""
        if BehaviorRegistry._instance is not None:
            raise RuntimeError("BehaviorRegistry已经初始化，请使用get_instance()获取实例")
        
        self.behaviors: Dict[str, Tuple[Type[BehaviorBase], Dict[str, Any]]] = {}
    
    def register(self, behavior_id: str, behavior_class: Type[BehaviorBase], **kwargs) -> None:
        """注册行为类型
        
        Args:
            behavior_id: 行为ID
            behavior_class: 行为类
            **kwargs: 行为默认参数
        """
        self.behaviors[behavior_id] = (behavior_class, kwargs)
        logging.debug(f"注册行为: {behavior_id}")
    
    def unregister(self, behavior_id: str) -> None:
        """取消注册行为类型
        
        Args:
            behavior_id: 行为ID
        
        Raises:
            KeyError: 行为ID不存在
        """
        if behavior_id in self.behaviors:
            del self.behaviors[behavior_id]
            logging.debug(f"取消注册行为: {behavior_id}")
        else:
            raise KeyError(f"行为ID不存在: {behavior_id}")
    
    def create(self, behavior_id: str, **kwargs) -> BehaviorBase:
        """创建行为实例
        
        Args:
            behavior_id: 行为ID
            **kwargs: 行为参数，将覆盖默认参数
        
        Returns:
            BehaviorBase: 行为实例
        
        Raises:
            ValueError: 行为ID不存在
        """
        if behavior_id not in self.behaviors:
            raise ValueError(f"行为ID不存在: {behavior_id}")
        
        behavior_class, default_kwargs = self.behaviors[behavior_id]
        
        # 合并默认参数和传入参数
        params = default_kwargs.copy()
        params.update(kwargs)
        
        return behavior_class(**params)


class BasicBehavior(BehaviorBase):
    """基本行为，可用于自定义简单行为"""
    
    def __init__(self, name: str = "", duration: Optional[float] = 0.0,
                 priority: float = 0.0, trigger_condition: Optional[Callable[[], bool]] = None,
                 **kwargs):
        """初始化基本行为
        
        Args:
            name: 行为名称
            duration: 行为持续时间(秒)，0.0 或 None表示无限持续
            priority: 优先级（0-10）
            trigger_condition: 行为触发条件回调函数
        """
        actual_duration = duration if duration is not None else 0.0 # Default to 0.0 if None
        super().__init__(name, actual_duration, kwargs.get('params'))
        self.priority = priority
        self.trigger_condition = trigger_condition
        self.callbacks: List[Callable[[BasicBehavior], None]] = []
        
        # 直接设置属性，而不是通过构造函数传递
        self.behavior_type = kwargs.get('behavior_type', BehaviorType.CUSTOM)
        self.loop = kwargs.get('loop', False)
    
    def add_callback(self, callback: Callable):
        """添加回调函数
        
        Args:
            callback: 回调函数，接收行为实例作为参数
        """
        self.callbacks.append(callback)
    
    def remove_callback(self, callback: Callable):
        """移除回调函数
        
        Args:
            callback: 回调函数
        """
        if callback in self.callbacks:
            self.callbacks.remove(callback)
    
    def can_trigger(self) -> bool:
        """检查是否可以触发行为"""
        if self.trigger_condition is None:
            return True
        
        return self.trigger_condition()
    
    def _on_complete(self) -> None:
        """完成时的回调"""
        # 不再调用super()._on_complete()，因为父类的实现是空的
        for callback in self.callbacks:
            try:
                callback(self)
            except Exception as e:
                logging.error(f"回调函数执行失败: {e}")


class IdleBehavior(BehaviorBase):
    """闲置行为"""
    
    def __init__(self, animation_name: str = "idle", **kwargs):
        """初始化闲置行为
        
        Args:
            animation_name: 动画名称
            **kwargs: 传递给父类的参数
        """
        # 从kwargs中移除可能的loop参数，避免冲突
        duration = kwargs.pop('duration', None)
        params = kwargs.pop('params', None)
        
        super().__init__(name="闲置", duration=duration, params=params)
        # 直接设置属性，而不是通过构造函数传递
        self.behavior_type = BehaviorType.IDLE
        self.loop = kwargs.get('loop', True)  # 默认为True
        self.animation_name = animation_name
    
    def _on_start(self) -> None:
        """开始行为"""
        if self.entity:
            try:
                if hasattr(self.entity, 'play_animation'):
                    self.entity.play_animation(self.animation_name, loop=self.loop)
            except Exception as e:
                logging.error(f"播放动画失败: {e}")
    
    def _on_update(self, dt: float) -> bool:
        """更新行为
        
        Args:
            dt: 时间增量
        
        Returns:
            bool: 是否继续行为
        """
        # 闲置行为通常不需要更新逻辑
        return True


class JumpBehavior(BehaviorBase):
    """跳跃行为"""
    
    def __init__(self, height: float = 50.0, **kwargs):
        """初始化跳跃行为
        
        Args:
            height: 跳跃高度
            **kwargs: 传递给父类的参数
        """
        duration = kwargs.pop('duration', 1.0) # Default duration 1.0s if not specified
        params = kwargs.pop('params', None)
        
        super().__init__(name="跳跃", duration=duration, params=params)
        self.behavior_type = BehaviorType.LOCOMOTION
        self.height = height
        self.original_y: float = 0.0
        # self.current_y is implicitly managed by entity's position, no need for separate state here
        # self.start_time: Optional[float] = None # start_time from BehaviorBase is used for duration checks, elapsed_time for progress
    
    def _on_start(self) -> None:
        """开始行为"""
        # self.start_time is managed by BehaviorBase.start()
        # self.elapsed_time is reset to 0.0 by BehaviorBase.start()
        
        if self.entity:
            try:
                if hasattr(self.entity, 'get_position'):
                    pos = self.entity.get_position()
                    if isinstance(pos, (list, tuple)) and len(pos) >= 2:
                        self.original_y = float(pos[1])
                    elif hasattr(pos, 'y'):
                        self.original_y = float(pos.y())  # type: ignore[attr-defined]
                    else:
                        logging.warning("跳跃行为：无法获取实体位置的Y坐标，默认为0.0")
                        self.original_y = 0.0
                else:
                    logging.warning("跳跃行为：实体没有get_position方法，original_y默认为0.0")
                    self.original_y = 0.0
                
                if hasattr(self.entity, 'play_animation'):
                    self.entity.play_animation('jump', loop=False)
            except Exception as e:
                logging.error(f"跳跃开始失败: {e}")
        else:
            logging.warning("跳跃行为：未设置实体.")
            self.original_y = 0.0 # Default if no entity
                
        # No need for EnvironmentSensor for basic jump mechanics
        # self.environment_sensor = EnvironmentSensor.get_instance()
    
    def _on_update(self, dt: float) -> bool:
        """更新行为
        
        Args:
            dt: 时间增量
        
        Returns:
            bool: 是否继续行为
        """
        if not self.entity or not hasattr(self.entity, 'set_position') or not hasattr(self.entity, 'get_position'):
            return False # Cannot operate without entity or its methods, complete immediately
        
        current_pos = self.entity.get_position()
        current_x: float
        if isinstance(current_pos, (list, tuple)) and len(current_pos) >= 2:
            current_x = float(current_pos[0])
        elif hasattr(current_pos, 'x'):
            current_x = float(current_pos.x()) # type: ignore[attr-defined]
        else:
            logging.warning("跳跃行为更新：无法获取实体当前X坐标.")
            return False # Complete if cannot get X
            
        progress = 0.0
        if self.duration is not None and self.duration > 0:
            progress = min(self.elapsed_time / self.duration, 1.0)
        elif self.duration == 0: # Consider 0 duration as instant if not None
             progress = 1.0
        # If self.duration is None, it means infinite. Jump behavior should have a duration.
        # For safety, if duration is None, we might make it complete instantly or log an error.
        # For now, an infinite duration jump doesn't make sense, so it completes based on duration check in BehaviorBase.update
        # The BehaviorBase.update() will handle completion if duration is met.
        # This _on_update should only return True if its own logic deems it incomplete within the duration timeframe.

        # The actual completion due to duration is handled by BehaviorBase.update() method.
        # This method just calculates the position based on progress.
        # It should return True if the animation/physics part of the jump is ongoing.
        # BehaviorBase.update will return True (completed) when duration is up.

        jump_y_offset = 0.0
        if progress < 1.0: # Still in the upward or downward motion of the jump arc
            jump_factor = math.sin(progress * math.pi) # Parabolic path (0 -> 1 -> 0)
            jump_y_offset = self.height * jump_factor
            self.entity.set_position(current_x, self.original_y - jump_y_offset)
            return True # Continue behavior (jump arc is in progress)
        else: # Progress is 1.0 or more, jump arc is finished or duration exceeded
            # Ensure final position is back at original_y (handled by _on_complete)
            # This _on_update should indicate its part is done if progress is 1.0
            return False # Indicate this update cycle considers the jump arc complete
    
    def _on_complete(self) -> None:
        """完成行为时的回调 (原 _on_finish 逻辑)"""
        # 恢复原始位置
        if self.entity and hasattr(self.entity, 'set_position') and hasattr(self.entity, 'get_position'):
            current_pos = self.entity.get_position()
            current_x: float
            if isinstance(current_pos, (list, tuple)) and len(current_pos) >=2:
                current_x = float(current_pos[0])
            elif hasattr(current_pos, 'x'):
                current_x = float(current_pos.x()) # type: ignore[attr-defined]
            else: # Should not happen if update worked, but for safety
                return 
            self.entity.set_position(current_x, self.original_y)
            logging.debug(f"跳跃行为完成，实体恢复到 Y: {self.original_y}")


class MoveBehavior(BehaviorBase):
    """移动行为"""
    
    def __init__(self, target_x: Optional[float] = None, target_y: Optional[float] = None, 
                 speed: float = 100.0, random_direction: bool = False, direction: Optional[Tuple[float, float]] = None, **kwargs):
        """初始化移动行为
        
        Args:
            target_x: 目标X坐标
            target_y: 目标Y坐标
            speed: 移动速度
            random_direction: 是否随机方向
            direction: 移动方向向量
            **kwargs: 传递给父类的参数
        """
        duration = kwargs.pop('duration', None)
        params = kwargs.pop('params', None)
        
        super().__init__(name="移动", duration=duration, params=params)
        # 直接设置属性
        self.behavior_type = BehaviorType.LOCOMOTION
        self.target_x = target_x
        self.target_y = target_y
        self.speed = speed
        self.random_direction = random_direction
        self.direction = direction
        
        # 添加位置属性以支持单元测试
        self.current_position: Optional[QPointF] = None
        self.target_position: Optional[QPointF] = None
    
    def _on_start(self) -> None:
        """开始行为"""
        # 获取环境传感器
        self.environment_sensor = EnvironmentSensor.get_instance()
        
        # elapsed_time is reset to 0.0 by super().start(), which is called before this _on_start
        # So, we don't need to record elapsed_time_at_start, as it would be 0.

        # 获取当前位置
        if self.entity:
            try:
                if hasattr(self.entity, 'get_position'):
                    pos = self.entity.get_position()
                    if isinstance(pos, (list, tuple)) and len(pos) >= 2:
                        self.start_x = float(pos[0])
                        self.start_y = float(pos[1])
                    elif hasattr(pos, 'x') and hasattr(pos, 'y'):
                        self.start_x = float(pos.x())  # type: ignore[attr-defined]
                        self.start_y = float(pos.y())  # type: ignore[attr-defined]
                    else:
                        logging.warning("无法获取实体位置，使用(0,0)")
                        self.start_x = 0.0
                        self.start_y = 0.0
                else:
                    logging.warning("实体没有get_position方法，使用(0,0)")
                    self.start_x = 0.0
                    self.start_y = 0.0
                
                # 确保当前位置设定
                self.current_x = self.start_x
                self.current_y = self.start_y
                
                # 播放动画（如果支持）
                if hasattr(self.entity, 'play_animation'):
                    self.entity.play_animation('walk')
            except Exception as e:
                logging.error(f"移动开始失败: {e}")
        
        # 如果指定了方向
        if self.direction:
            distance = 0.0
            if self.duration is not None and self.duration > 0:
                distance = self.speed * self.duration
            else:
                distance = self.speed * 2.0
            
            if self.start_x is not None and self.start_y is not None:
                self.target_x = self.start_x + self.direction[0] * distance
                self.target_y = self.start_y + self.direction[1] * distance
        elif self.random_direction:
            # 随机选择方向
            self._choose_random_direction()
        
        # 设置位置属性以支持单元测试
        if self.current_x is not None and self.current_y is not None:
            self.current_position = QPointF(self.current_x, self.current_y)
        if self.target_x is not None and self.target_y is not None:
            self.target_position = QPointF(self.target_x, self.target_y)
            
        # 计算所需时间
        if (self.start_x is not None and self.start_y is not None and 
            self.target_x is not None and self.target_y is not None):
            distance = math.sqrt((self.target_x - self.start_x)**2 + (self.target_y - self.start_y)**2)
            self.time_needed = distance / self.speed if self.speed > 0 else 0.0
        else:
            self.time_needed = 1.0  # 默认1秒
            
        # 记录开始时间 (elapsed_time will be used for progress calculation)
        # self.start_time = time.time() # No longer relying on wall clock time for progress
    
    def _choose_random_direction(self) -> None:
        """选择随机方向"""
        # 获取屏幕边界
        screen_info = None
        if self.environment_sensor:
            try:
                screen_info = self.environment_sensor.get_primary_screen()
            except Exception as e:
                logging.error(f"获取屏幕信息失败: {e}")
                
        # 如果获取不到屏幕信息，使用默认值
        if not screen_info:
            screen_width = 1920
            screen_height = 1080
        else:
            screen_width = screen_info.get('width', 1920)
            screen_height = screen_info.get('height', 1080)
        
        if self.start_x is not None and self.start_y is not None:
            # 随机选择方向角度
            angle = random.uniform(0, 2 * math.pi)
            direction_x = math.cos(angle)
            direction_y = math.sin(angle)
            
            # 限制移动范围在屏幕内
            distance = random.uniform(100, 300)  # 随机移动距离
            
            self.target_x = self.start_x + direction_x * distance
            self.target_y = self.start_y + direction_y * distance
            
            # 限制在屏幕范围内
            self.target_x = max(0, min(self.target_x, screen_width))
            self.target_y = max(0, min(self.target_y, screen_height))
    
    def _on_update(self, dt: float) -> bool:
        """更新行为
        
        Args:
            dt: 时间增量
        
        Returns:
            bool: 是否继续行为
        """
        # 如果没有设置实体，无法执行
        if not self.entity or not hasattr(self.entity, 'set_position'):
            return False
        
        # 如果没有目标，无法执行
        if self.target_x is None or self.target_y is None:
            return False
        
        # 获取当前位置 (not strictly needed for calculation if start_x/y are reliable)
        # position = None
        # if hasattr(self.entity, 'get_position'):
        #     position = self.entity.get_position()
            
        # 计算移动进度 using elapsed_time from BehaviorBase
        # elapsed_time is updated by BehaviorBase.update() before this _on_update is called.
        progress = 0.0
        if self.time_needed is not None and self.time_needed > 0:
            # self.elapsed_time is managed by BehaviorBase and accumulates dt
            progress = min(self.elapsed_time / self.time_needed, 1.0)
        else:
            # If time_needed is 0 or None, consider progress complete instantly if target exists
            progress = 1.0 
        
        if (self.start_x is not None and 
            self.start_y is not None and 
            self.target_x is not None and 
            self.target_y is not None):
            # 计算当前位置
            self.current_x = self.start_x + (self.target_x - self.start_x) * progress
            self.current_y = self.start_y + (self.target_y - self.start_y) * progress
            
            # 设置新位置
            self.entity.set_position(self.current_x, self.current_y)
            
            # 检查是否完成
            return progress < 1.0
        else:
            return False
    
    def _on_finish(self) -> None:
        """完成行为"""
        # 停止动画（如果支持）
        if self.entity and hasattr(self.entity, 'play_animation'):
            try:
                self.entity.play_animation('idle')
            except Exception as e:
                logging.error(f"动画停止失败: {e}")


def initialize_behaviors():
    """初始化行为注册表，注册默认行为"""
    registry = BehaviorRegistry.get_instance()
    
    # 注册空闲行为
    registry.register("idle", IdleBehavior, animation_name="idle")
    
    # 注册移动行为
    registry.register("move", MoveBehavior)
    registry.register("move_random", MoveBehavior, random_direction=True)
    registry.register("move_left", MoveBehavior, direction=(-1, 0))
    registry.register("move_right", MoveBehavior, direction=(1, 0))
    registry.register("move_up", MoveBehavior, direction=(0, -1))
    registry.register("move_down", MoveBehavior, direction=(0, 1))
    
    # 注册跳跃行为
    registry.register("jump", JumpBehavior, height=50)
    registry.register("high_jump", JumpBehavior, height=100)
    
    # 注册特殊动画行为
    registry.register("wave", IdleBehavior, animation_name="wave")
    registry.register("nod", IdleBehavior, animation_name="nod")
    registry.register("dance", IdleBehavior, animation_name="dance")
    
    return registry 
