"""
---------------------------------------------------------------
File name:                  basic_behaviors.py
Author:                     Ignorant-lu
Date created:               2025/04/04
Description:                基础行为系统
----------------------------------------------------------------

Changed history:            
                            2025/04/04: 初始创建;
                            2025/04/04: 添加注册表和基础行为抽象;
                            2025/04/04: 补充跳跃、移动等具体行为;
                            2025/05/15: PyQt6导入改为PySide6以统一项目Qt库使用;
                            2025/05/16: 修复JumpBehavior中start_time可能为None的类型错误;
                            2025/05/16: 修复文件编码问题;
                            2025/05/16: 修复MoveBehavior中target_x/target_y为None导致的类型错误;
                            2025/05/16: 添加FallBehavior、SleepBehavior和PlayAnimationBehavior类;
                            2025/05/16: 修复_on_update方法参数，调整类以匹配测试;
                            2025/05/16: 修复测试失败问题;
----
"""

import time
import random
import logging
import inspect
import math
from typing import Dict, Any, Callable, Optional, List, Type, Tuple, Union
from enum import Enum, auto
import threading

from PySide6.QtCore import QPointF, QPoint, QRect


class BehaviorType(Enum):
    """行为类型枚举"""
    IDLE = auto()  # 空闲
    LOCOMOTION = auto()  # 移动
    INTERACTION = auto()  # 互动
    EMOTION = auto()  # 情绪表达
    SYSTEM = auto()  # 系统行为
    CUSTOM = auto()  # 自定义


class BehaviorRegistry:
    """行为注册表
    
    单例模式，用于管理所有注册的行为类型
    """
    _instance = None
    
    @staticmethod
    def get_instance():
        """获取单例实例"""
        if BehaviorRegistry._instance is None:
            BehaviorRegistry._instance = BehaviorRegistry()
        return BehaviorRegistry._instance
    
    def __init__(self):
        """初始化"""
        if BehaviorRegistry._instance is not None:
            raise RuntimeError("BehaviorRegistry is a singleton!")
        self.behaviors = {}
        self.logger = logging.getLogger("BehaviorRegistry")
    
    def register(self, behavior_id: str, behavior_class: Type["BasicBehavior"], **kwargs) -> None:
        """注册行为类
        
        Args:
            behavior_id: 行为唯一标识符
            behavior_class: 行为类
            **kwargs: 创建行为实例时的默认参数
        """
        if behavior_id in self.behaviors:
            self.logger.warning(f"行为ID '{behavior_id}' 已存在，将被覆盖")
        
        self.behaviors[behavior_id] = (behavior_class, kwargs)
        self.logger.debug(f"注册行为: {behavior_id} -> {behavior_class.__name__}")
    
    def unregister(self, behavior_id: str) -> None:
        """注销行为类
        
        Args:
            behavior_id: 行为唯一标识符
        
        Raises:
            ValueError: 如果行为ID不存在
        """
        if behavior_id not in self.behaviors:
            raise ValueError(f"行为ID '{behavior_id}' 不存在")
        
        del self.behaviors[behavior_id]
        self.logger.debug(f"注销行为: {behavior_id}")
    
    def create(self, behavior_id: str, **kwargs) -> "BasicBehavior":
        """创建行为实例
        
        Args:
            behavior_id: 行为唯一标识符
            **kwargs: 传递给行为构造函数的参数，会覆盖注册时的默认参数
        
        Returns:
            BasicBehavior: 行为实例
        
        Raises:
            ValueError: 如果行为ID不存在
        """
        if behavior_id not in self.behaviors:
            raise ValueError(f"行为ID '{behavior_id}' 不存在")
        
        behavior_class, default_params = self.behaviors[behavior_id]
        
        # 合并默认参数和传入的参数
        params = default_params.copy()
        params.update(kwargs)
        
        return behavior_class(**params)


class BasicBehavior:
    """基础行为类
    
    所有具体行为的基类
    """
    
    def __init__(self, name: str = "", duration: float = 0, loop: bool = False, behavior_type: BehaviorType = BehaviorType.CUSTOM):
        """初始化
        
        Args:
            name: 行为名称
            duration: 行为持续时间（秒），0表示无限
            loop: 是否循环执行
            behavior_type: 行为类型
        """
        self.name = name or self.__class__.__name__
        self.duration = duration
        self.loop = loop
        self.behavior_type = behavior_type
        self.is_running = False
        self.start_time = None
        self.params = {}
        self.logger = logging.getLogger(f"Behavior.{self.name}")
    
    def start(self, params: Optional[Dict[str, Any]] = None) -> None:
        """启动行为
        
        Args:
            params: 行为参数
        """
        self.params = params or {}
        self.start_time = time.time()
        self.is_running = True
        self._on_start()
        self.logger.debug(f"行为启动: {self.name}")
    
    def stop(self) -> None:
        """停止行为"""
        if self.is_running:
            self.is_running = False
            self._on_stop()
            self.logger.debug(f"行为停止: {self.name}")
    
    def update(self, dt: float) -> bool:
        """更新行为状态
        
        Args:
            dt: 时间增量（秒）
        
        Returns:
            bool: 行为是否完成
        """
        if not self.is_running:
            return True
        
        # 计算经过的时间
        elapsed_time = time.time() - self.start_time if self.start_time is not None else 0
        
        # 检查是否达到持续时间
        if self.duration > 0 and elapsed_time >= self.duration:
            if self.loop:
                # 重置开始时间，继续循环
                self.start_time = time.time()
                self._on_loop()
                self.logger.debug(f"行为循环: {self.name}")
                result = self._on_update(dt)
                return False
            else:
                # 行为结束
                self.is_running = False
                self._on_finish()
                self._on_complete()  # 调用完成回调
                self.logger.debug(f"行为完成: {self.name}")
                return True
        
        # 更新行为
        result = self._on_update(dt)
        return result
    
    def _on_start(self) -> None:
        """行为开始时调用"""
        pass
    
    def _on_stop(self) -> None:
        """行为停止时调用"""
        pass
    
    def _on_finish(self) -> None:
        """行为完成时调用"""
        pass
    
    def _on_loop(self) -> None:
        """行为循环时调用"""
        pass
    
    def _on_update(self, dt: float) -> bool:
        """行为更新时调用
        
        Args:
            dt: 时间增量（秒）
        
        Returns:
            bool: 行为是否完成
        """
        return False
    
    def _on_complete(self) -> None:
        """行为完成后调用，用于测试"""
        pass


class IdleBehavior(BasicBehavior):
    """空闲行为基类"""
    
    def __init__(self, animation_name: str = "idle", **kwargs):
        """初始化
        
        Args:
            animation_name: 动画名称
            **kwargs: 传递给父类的参数
        """
        # 从kwargs中移除可能的loop参数，避免冲突
        loop = kwargs.pop('loop', True)  # 默认为True
        super().__init__(name="闲置", behavior_type=BehaviorType.IDLE, loop=loop, **kwargs)
        self.animation_name = animation_name
    
    def _on_start(self) -> None:
        """行为开始时调用"""
        # 获取实体
        entity = self.params.get("entity")
        if entity and hasattr(entity, "set_animation"):
            entity.set_animation(self.animation_name)
    
    def _on_update(self, dt: float) -> bool:
        """行为更新时调用
        
        Args:
            dt: 时间增量（秒）
        
        Returns:
            bool: 行为是否完成
        """
        # 闲置行为不做任何事情
        return False


class JumpBehavior(BasicBehavior):
    """跳跃行为"""
    
    def __init__(self, height: float = 50, **kwargs):
        """初始化
        
        Args:
            height: 跳跃高度
            **kwargs: 传递给父类的参数
        """
        super().__init__(name="跳跃", behavior_type=BehaviorType.LOCOMOTION, **kwargs)
        self.height = height
        self.original_y = 0
        self.current_y = 0
        self.entity = None
        self.start_y = 0
        self.environment_sensor = None  # 新增: 存储环境传感器实例
    
    def _on_start(self) -> None:
        """行为开始时调用"""
        self.entity = self.params.get("entity")
        
        # 新增: 获取并存储环境传感器实例
        self.environment_sensor = self.params.get("environment_sensor")
        if not self.environment_sensor:
            try:
                from status.behavior.environment_sensor import EnvironmentSensor
                self.environment_sensor = EnvironmentSensor.get_instance()
            except (ImportError, AttributeError):
                self.logger.warning("无法获取环境传感器实例")
                pass

        if self.environment_sensor:
            window_rect = self.environment_sensor.get_window_position()
            if window_rect and isinstance(window_rect, QRect):
                self.start_y = window_rect.y()
        else:
            self.start_y = 100
        
        if self.entity:
            self.original_y = self.entity.y
    
    def _on_update(self, dt: float) -> bool:
        """行为更新时调用
        
        Args:
            dt: 时间增量（秒）
        
        Returns:
            bool: 行为是否完成
        """
        if not self.entity:
            return True
            
        # 修改: 使用存储的环境传感器实例
        if self.environment_sensor:
            self.environment_sensor.get_window_position()
        
        if self.start_time is None:
            progress = 0
        else:
            progress = (time.time() - self.start_time) / self.duration if self.duration else 0
        
        if progress <= 1:
            jump_factor = math.sin(progress * math.pi)
            self.current_y = self.original_y - (self.height * jump_factor)
            self.entity.y = self.current_y
            return False
        else:
            self.entity.y = self.original_y
            return True
    
    def _on_finish(self) -> None:
        """行为完成时调用"""
        if self.entity:
            self.entity.y = self.original_y


class MoveBehavior(BasicBehavior):
    """移动行为"""
    
    def __init__(self, target_x: Optional[float] = None, target_y: Optional[float] = None, 
                 speed: float = 100, random_direction: bool = False, direction: Optional[Tuple[float, float]] = None, **kwargs):
        """初始化
        
        Args:
            target_x: 目标X坐标，None表示不移动X
            target_y: 目标Y坐标，None表示不移动Y
            speed: 移动速度（像素/秒）
            random_direction: 是否随机方向移动
            direction: 移动方向，格式为(x, y)，例如(1, 0)表示向右移动
            **kwargs: 传递给父类的参数
        """
        super().__init__(name="移动", behavior_type=BehaviorType.LOCOMOTION, **kwargs)
        self.target_x = target_x
        self.target_y = target_y
        self.speed = speed
        self.random_direction = random_direction
        self.direction = direction
        self.start_x = 0
        self.start_y = 0
        self.entity = None
        self.distance = 0
        self.time_needed = 0
        self.current_position = None
        self.target_position = None
        self.environment_sensor = None  # 新增: 存储环境传感器实例
    
    def _on_start(self) -> None:
        """行为开始时调用"""
        self.entity = self.params.get("entity")
        
        # 新增: 获取并存储环境传感器实例
        self.environment_sensor = self.params.get("environment_sensor")
        if not self.environment_sensor:
            try:
                from status.behavior.environment_sensor import EnvironmentSensor
                self.environment_sensor = EnvironmentSensor.get_instance()
            except (ImportError, AttributeError):
                self.logger.warning("无法获取环境传感器实例")
                pass

        if self.environment_sensor:
            window_rect = self.environment_sensor.get_window_position()
            if window_rect and isinstance(window_rect, QRect):
                self.start_x = window_rect.x() + window_rect.width() / 2
                self.start_y = window_rect.y() + window_rect.height() / 2
        else:
            self.start_x = 100
            self.start_y = 100
        
        if self.entity:
            self.start_x = self.entity.x
            self.start_y = self.entity.y
        
        self.current_position = QPoint(int(self.start_x), int(self.start_y))
        
        if self.direction:
            distance = self.speed * (self.duration if self.duration > 0 else 2)
            self.target_x = self.start_x + self.direction[0] * distance
            self.target_y = self.start_y + self.direction[1] * distance
        elif self.random_direction:
            self._choose_random_direction()
            if self.direction is None:
                self.direction = (1, 0)
        
        if self.target_x is None:
            self.target_x = self.start_x
        if self.target_y is None:
            self.target_y = self.start_y
        
        if not isinstance(self.target_x, (int, float)) or not isinstance(self.target_y, (int, float)):
            self.target_x = self.start_x
            self.target_y = self.start_y
        
        self.target_position = QPoint(int(self.target_x), int(self.target_y))
        
        dx = self.target_x - self.start_x
        dy = self.target_y - self.start_y
        self.distance = math.sqrt(dx**2 + dy**2)
        self.time_needed = self.distance / self.speed if self.speed > 0 else 0
        
        if self.duration == 0:
            self.duration = self.time_needed
    
    def _choose_random_direction(self):
        """选择随机方向"""
        # 随机选择方向（上、下、左、右）
        directions = ['up', 'down', 'left', 'right']
        direction_name = random.choice(directions)
        
        # 计算目标坐标
        distance = self.speed * 2  # 移动距离是速度的两倍
        
        if direction_name == 'up':
            self.direction = (0, -1)
            self.target_x = self.start_x
            self.target_y = self.start_y - distance
        elif direction_name == 'down':
            self.direction = (0, 1)
            self.target_x = self.start_x
            self.target_y = self.start_y + distance
        elif direction_name == 'left':
            self.direction = (-1, 0)
            self.target_x = self.start_x - distance
            self.target_y = self.start_y
        elif direction_name == 'right':
            self.direction = (1, 0)
            self.target_x = self.start_x + distance
            self.target_y = self.start_y
    
    def _on_update(self, dt: float) -> bool:
        """行为更新时调用
        
        Args:
            dt: 时间增量（秒）
        
        Returns:
            bool: 行为是否完成
        """
        if not self.entity or self.distance == 0:
            return True
        
        # 修改: 使用存储的环境传感器实例
        if self.environment_sensor:
            self.environment_sensor.get_window_position()
        
        if self.start_time is None:
            progress = 0
        else:
            progress = min((time.time() - self.start_time) / self.time_needed if self.time_needed else 1, 1)
        
        if (isinstance(self.start_x, (int, float)) and 
            isinstance(self.start_y, (int, float)) and
            isinstance(self.target_x, (int, float)) and
            isinstance(self.target_y, (int, float))):
            
            current_x = self.start_x + (self.target_x - self.start_x) * progress
            current_y = self.start_y + (self.target_y - self.start_y) * progress
            
            self.entity.x = current_x
            self.entity.y = current_y
            
            self.current_position = QPoint(int(current_x), int(current_y))
        else:
            self.logger.warning("移动行为坐标无效，结束行为")
            return True
        
        return progress >= 1
    
    def _on_finish(self) -> None:
        """行为完成时调用"""
        if self.entity:
            self.entity.x = self.target_x
            self.entity.y = self.target_y


class FallBehavior(BasicBehavior):
    """下落行为"""
    
    def __init__(self, gravity: float = 9.8, max_speed: float = 500, **kwargs):
        """初始化
        
        Args:
            gravity: 重力加速度
            max_speed: 最大下落速度
            **kwargs: 传递给父类的参数
        """
        super().__init__(name="下落", behavior_type=BehaviorType.LOCOMOTION, **kwargs)
        self.gravity = gravity
        self.max_speed = max_speed
        self.entity = None
        self.original_y = 0
        self.velocity = 0
        self.ground_y = 0
        self.start_y = 0
        self.environment_sensor = None  # 新增: 存储环境传感器实例
    
    def _on_start(self) -> None:
        """行为开始时调用"""
        self.entity = self.params.get("entity")
        self.velocity = 0
        
        self.environment_sensor = self.params.get("environment_sensor")
        if not self.environment_sensor:
            try:
                from status.behavior.environment_sensor import EnvironmentSensor
                self.environment_sensor = EnvironmentSensor.get_instance()
            except (ImportError, AttributeError):
                self.logger.warning("无法获取环境传感器实例")
                pass

        # 优先从 params 获取 ground_y
        param_ground_y = self.params.get("ground_y")

        if self.environment_sensor:
            window_rect = self.environment_sensor.get_window_position()
            if window_rect and isinstance(window_rect, QRect):
                self.start_y = window_rect.y()
            
            if param_ground_y is not None:
                self.ground_y = param_ground_y
            else:
                screen_info = self.environment_sensor.get_screen_boundaries()
                if screen_info:
                    self.ground_y = screen_info['y'] + screen_info['height'] - 50
                else:
                    self.ground_y = 1000 # 默认值，如果传感器和params都没有提供
        else:
            self.start_y = 100 # 无传感器时的默认 start_y
            self.ground_y = param_ground_y if param_ground_y is not None else 1000

        if self.entity:
            self.original_y = self.entity.y
    
    def _on_update(self, dt: float) -> bool:
        """行为更新时调用"""
        self.logger.debug(f"FallBehavior _on_update called with dt: {dt}, current_velocity: {self.velocity}")
        if not self.entity:
            return True
            
        if self.environment_sensor:
            self.environment_sensor.get_window_position()
            self.environment_sensor.get_screen_boundaries()
        
        if self.entity.y >= self.ground_y:
            self.logger.debug(f"Entity at ground_y: {self.entity.y} >= {self.ground_y}")
            self.entity.y = self.ground_y
            return True
        
        # 使用传入的dt进行计算，除非它是无效的
        current_dt = dt
        if current_dt <= 0:
            self.logger.warning(f"Invalid dt: {dt} received. Using a small default.")
            current_dt = 0.01 # 使用一个小的默认值避免计算问题

        self.velocity += self.gravity * current_dt
        self.velocity = min(self.velocity, self.max_speed)
        self.logger.debug(f"Updated velocity: {self.velocity} (gravity: {self.gravity}, dt: {current_dt})")
        
        dy = self.velocity * current_dt
        new_y = self.entity.y + dy
        self.logger.debug(f"Position update: dy={dy}, new_y={new_y}")
        
        if new_y >= self.ground_y:
            self.entity.y = self.ground_y
            self.logger.debug(f"Entity reached ground. Final y: {self.entity.y}")
            return True
        else:
            self.entity.y = new_y
            return False
    
    def _on_finish(self) -> None:
        """行为完成时调用"""
        if self.entity:
            # 确保实体位于地面
            self.entity.y = self.ground_y


class SleepBehavior(BasicBehavior):
    """睡眠行为"""
    
    def __init__(self, duration: float = 5.0, animation_name: str = "sleep", **kwargs):
        """初始化
        
        Args:
            duration: 睡眠持续时间
            animation_name: 睡眠动画名称
            **kwargs: 传递给父类的参数
        """
        # 从kwargs中提取loop参数，默认为True
        loop = kwargs.pop('loop', True)
        super().__init__(name="睡眠", duration=duration, behavior_type=BehaviorType.EMOTION, loop=loop, **kwargs)
        self.animation_name = animation_name
        self.entity = None
        self.original_animation = None
    
    def _on_start(self) -> None:
        """行为开始时调用"""
        self.entity = self.params.get("entity")
        
        if not self.entity:
            return
        
        # 保存原始动画
        if hasattr(self.entity, "current_animation"):
            self.original_animation = self.entity.current_animation
        
        # 设置睡眠动画
        if hasattr(self.entity, "set_animation"):
            self.entity.set_animation(self.animation_name)
    
    def _on_update(self, dt: float) -> bool:
        """行为更新时调用
        
        Args:
            dt: 时间增量（秒）
        
        Returns:
            bool: 行为是否完成
        """
        # 睡眠行为不需要额外的更新逻辑
        return False
    
    def _on_finish(self) -> None:
        """行为完成时调用"""
        if self.entity and self.original_animation:
            # 恢复原始动画
            if hasattr(self.entity, "set_animation"):
                self.entity.set_animation(self.original_animation)


class PlayAnimationBehavior(BasicBehavior):
    """播放动画行为"""
    
    def __init__(self, animation_name: str, duration: float = 1.0, frame_rate: float = 10, **kwargs):
        """初始化
        
        Args:
            animation_name: 动画名称
            duration: 动画持续时间
            frame_rate: 帧率
            **kwargs: 传递给父类的参数
        """
        super().__init__(name=f"播放动画:{animation_name}", duration=duration, behavior_type=BehaviorType.CUSTOM, **kwargs)
        self.animation_name = animation_name
        self.frame_rate = frame_rate
        self.entity = None
        self.renderer = None
        self.original_animation = None
    
    def _on_start(self) -> None:
        """行为开始时调用"""
        self.entity = self.params.get("entity")
        
        if not self.entity:
            return
        
        # 保存原始动画
        if hasattr(self.entity, "current_animation"):
            self.original_animation = self.entity.current_animation
        
        # 设置新动画
        if hasattr(self.entity, "set_animation"):
            self.entity.set_animation(self.animation_name, self.frame_rate)
    
    def _on_update(self, dt: float) -> bool:
        """行为更新时调用
        
        Args:
            dt: 时间增量（秒）
        
        Returns:
            bool: 行为是否完成
        """
        # 动画会自动播放，不需要额外的更新逻辑
        return False
    
    def _on_finish(self) -> None:
        """行为完成时调用"""
        if self.entity and self.original_animation and hasattr(self.entity, "set_animation"):
            # 恢复原始动画
            self.entity.set_animation(self.original_animation, self.frame_rate)


class FollowPathBehavior(BasicBehavior):
    """路径跟随行为"""
    
    def __init__(self, path: List[Tuple[float, float]], speed: float = 100, loop: bool = False, **kwargs):
        """初始化
        
        Args:
            path: 路径点列表，每个点是(x, y)坐标元组
            speed: 移动速度（像素/秒）
            loop: 是否循环路径
            **kwargs: 传递给父类的参数
        """
        super().__init__(name="FollowPath", behavior_type=BehaviorType.LOCOMOTION, loop=loop, **kwargs)
        self.path = path
        self.speed = speed
        self.current_point_index = 0
        self.entity = None
        self.start_pos = (0, 0)
        self.target_pos = (0, 0)
        self.segment_distance = 0
        self.segment_time = 0
        self.segment_start_time = 0
    
    def _on_start(self) -> None:
        """行为开始时调用"""
        self.entity = self.params.get("entity")
        
        if not self.entity or not self.path:
            return
        
        # 初始化起点为实体当前位置
        self.start_pos = (self.entity.x, self.entity.y)
        
        # 初始化第一个目标点
        self.current_point_index = 0
        self.target_pos = self.path[self.current_point_index]
        
        # 计算第一段的距离和时间
        self._calculate_segment()
        
        # 记录段起始时间
        self.segment_start_time = time.time()
    
    def _calculate_segment(self) -> None:
        """计算当前路径段的距离和时间"""
        dx = self.target_pos[0] - self.start_pos[0]
        dy = self.target_pos[1] - self.start_pos[1]
        self.segment_distance = math.sqrt(dx**2 + dy**2)
        self.segment_time = self.segment_distance / self.speed if self.speed > 0 else 0
    
    def _on_update(self, dt: float) -> bool:
        """行为更新时调用
        
        Args:
            dt: 时间增量（秒）
        
        Returns:
            bool: 行为是否完成
        """
        if not self.entity or not self.path:
            return True
        
        # 确保segment_start_time不为None
        if self.segment_start_time is None:
            segment_progress = 0
        else:
            # 计算当前段的进度
            elapsed = time.time() - self.segment_start_time
            segment_progress = min(elapsed / self.segment_time if self.segment_time > 0 else 1, 1)
        
        # 如果当前段完成，移动到下一段
        if segment_progress >= 1:
            self.start_pos = self.target_pos
            self.current_point_index += 1
            
            # 检查是否完成整个路径
            if self.current_point_index >= len(self.path):
                if self.loop:
                    # 循环路径，从头开始
                    self.current_point_index = 0
                else:
                    # 完成路径
                    return True
            
            # 更新目标点和段计算
            self.target_pos = self.path[self.current_point_index]
            self._calculate_segment()
            self.segment_start_time = time.time()
            segment_progress = 0
        
        # 线性插值计算当前位置
        current_x = self.start_pos[0] + (self.target_pos[0] - self.start_pos[0]) * segment_progress
        current_y = self.start_pos[1] + (self.target_pos[1] - self.start_pos[1]) * segment_progress
        
        # 更新实体位置
        self.entity.x = current_x
        self.entity.y = current_y
        
        return False


class EmotionBehavior(BasicBehavior):
    """情绪表达行为"""
    
    def __init__(self, emotion: str, intensity: float = 1.0, **kwargs):
        """初始化
        
        Args:
            emotion: 情绪名称
            intensity: 情绪强度（0-1）
            **kwargs: 传递给父类的参数
        """
        super().__init__(name=f"Emotion_{emotion}", behavior_type=BehaviorType.EMOTION, **kwargs)
        self.emotion = emotion
        self.intensity = max(0, min(intensity, 1))  # 限制在0-1范围内
        self.entity = None
    
    def _on_start(self) -> None:
        """行为开始时调用"""
        self.entity = self.params.get("entity")
        
        if self.entity and hasattr(self.entity, "emotion_system"):
            # 触发情绪变化
            self.entity.emotion_system.apply_emotion(self.emotion, self.intensity)
    
    def _on_update(self, dt: float) -> bool:
        """行为更新时调用
        
        Args:
            dt: 时间增量（秒）
        
        Returns:
            bool: 行为是否完成
        """
        # 情绪行为通常是瞬时的
        return True


class AnimationBehavior(BasicBehavior):
    """动画行为"""
    
    def __init__(self, animation_name: str, frame_rate: float = 10, **kwargs):
        """初始化
        
        Args:
            animation_name: 动画名称
            frame_rate: 帧率（帧/秒）
            **kwargs: 传递给父类的参数
        """
        super().__init__(name=f"Animation_{animation_name}", behavior_type=BehaviorType.CUSTOM, **kwargs)
        self.animation_name = animation_name
        self.frame_rate = frame_rate
        self.entity = None
        self.renderer = None
        self.original_animation = None
    
    def _on_start(self) -> None:
        """行为开始时调用"""
        self.entity = self.params.get("entity")
        
        if not self.entity:
            return
        
        # 保存原始动画
        if hasattr(self.entity, "current_animation"):
            self.original_animation = self.entity.current_animation
        
        # 设置新动画
        if hasattr(self.entity, "set_animation"):
            self.entity.set_animation(self.animation_name, self.frame_rate)
    
    def _on_update(self, dt: float) -> bool:
        """行为更新时调用
        
        Args:
            dt: 时间增量（秒）
        
        Returns:
            bool: 行为是否完成
        """
        # 如果没有指定持续时间，动画会一直运行直到手动停止
        return False
    
    def _on_finish(self) -> None:
        """行为完成时调用"""
        if self.entity and self.original_animation and hasattr(self.entity, "set_animation"):
            # 恢复原始动画
            self.entity.set_animation(self.original_animation, self.frame_rate)


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
    
    # 注册下落行为
    registry.register("fall", FallBehavior)
    
    # 注册睡眠行为
    registry.register("sleep", SleepBehavior, duration=5.0)
    
    # 注册动画行为
    registry.register("play_animation", PlayAnimationBehavior, animation_name="idle")
    
    # 注册特殊动画行为
    registry.register("wave", PlayAnimationBehavior, animation_name="wave", duration=1.0)
    registry.register("nod", PlayAnimationBehavior, animation_name="nod", duration=0.5)
    registry.register("dance", PlayAnimationBehavior, animation_name="dance", duration=3.0)
    
    # 注册情绪行为
    registry.register("emotion", EmotionBehavior)
    
    # 注册路径跟随行为
    registry.register("follow_path", FollowPathBehavior)

    return registry 
