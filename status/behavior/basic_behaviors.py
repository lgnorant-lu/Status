"""
---------------------------------------------------------------
File name:                  basic_behaviors.py
Author:                     Ignorant-lu
Date created:               2025/04/04
Description:                桌宠基础行为集实现
----------------------------------------------------------------

Changed history:            
                            2025/04/04: 初始创建;
----
"""

import time
import logging
import random
from abc import ABC, abstractmethod
from PyQt6.QtCore import QRect, QPoint

from status.behavior.environment_sensor import EnvironmentSensor


class BasicBehavior(ABC):
    """基础行为抽象类
    
    所有具体行为的基类，定义行为的通用接口和属性
    """
    
    def __init__(self, name, duration=None, loop=False):
        """初始化基础行为
        
        Args:
            name (str): 行为名称
            duration (float, optional): 行为持续时间，None表示无限
            loop (bool, optional): 是否循环执行
        """
        self.name = name
        self.duration = duration  # 行为持续时间，None表示无限
        self.loop = loop  # 是否循环执行
        self.is_running = False
        self.start_time = None
        self.params = {}
        self.logger = logging.getLogger(f"Behavior.{self.__class__.__name__}")
        
    def start(self, params=None):
        """开始执行行为
        
        Args:
            params (dict, optional): 行为参数
        """
        self.is_running = True
        self.start_time = time.time()
        self.params = params or {}
        self.logger.debug(f"开始行为: {self.name} 参数: {self.params}")
        self._on_start()
        
    def update(self, dt):
        """更新行为状态
        
        Args:
            dt (float): 时间增量（秒）
        
        Returns:
            bool: 行为是否已完成
        """
        if not self.is_running:
            return True
            
        if self.duration is not None:
            elapsed = time.time() - self.start_time
            if elapsed >= self.duration:
                if self.loop:
                    self.start_time = time.time()  # 重置开始时间
                    self.logger.debug(f"重置循环行为: {self.name}")
                else:
                    self.logger.debug(f"行为完成: {self.name} (持续时间: {elapsed:.2f}秒)")
                    self._on_complete()
                    self.is_running = False
                    return True
                    
        self._on_update(dt)
        return False
        
    def stop(self):
        """停止行为执行"""
        if self.is_running:
            self.logger.debug(f"停止行为: {self.name}")
            self._on_stop()
            self.is_running = False
            
    def _on_start(self):
        """行为开始时的回调"""
        pass
        
    def _on_update(self, dt):
        """行为更新时的回调
        
        Args:
            dt (float): 时间增量（秒）
        """
        pass
        
    def _on_stop(self):
        """行为停止时的回调"""
        pass
        
    def _on_complete(self):
        """行为完成时的回调"""
        pass


class BehaviorRegistry:
    """行为注册表
    
    管理所有已注册的行为类，实现单例模式
    """
    
    _instance = None
    
    @classmethod
    def get_instance(cls):
        """获取单例实例
        
        Returns:
            BehaviorRegistry: 行为注册表实例
        """
        if cls._instance is None:
            cls._instance = BehaviorRegistry()
        return cls._instance
        
    def __init__(self):
        """初始化行为注册表"""
        self.behaviors = {}
        self.logger = logging.getLogger("BehaviorRegistry")
        
    def register(self, behavior_id, behavior_class, **default_params):
        """注册行为类
        
        Args:
            behavior_id (str): 行为唯一标识符
            behavior_class (class): 行为类
            **default_params: 行为默认参数
        """
        self.behaviors[behavior_id] = (behavior_class, default_params)
        self.logger.debug(f"注册行为: {behavior_id} 类: {behavior_class.__name__}")
        
    def create(self, behavior_id, **params):
        """创建行为实例
        
        Args:
            behavior_id (str): 行为唯一标识符
            **params: 覆盖默认参数的参数
            
        Returns:
            BasicBehavior: 创建的行为实例
        
        Raises:
            ValueError: 未找到指定ID的行为
        """
        if behavior_id not in self.behaviors:
            raise ValueError(f"未找到行为: {behavior_id}")
            
        behavior_class, default_params = self.behaviors[behavior_id]
        merged_params = {**default_params, **params}
        self.logger.debug(f"创建行为: {behavior_id} 参数: {merged_params}")
        return behavior_class(**merged_params)


class IdleBehavior(BasicBehavior):
    """闲置行为
    
    桌宠的默认闲置状态，可以播放闲置动画
    """
    
    def __init__(self, animation_name="idle", duration=None, loop=True):
        """初始化闲置行为
        
        Args:
            animation_name (str, optional): 动画名称
            duration (float, optional): 持续时间
            loop (bool, optional): 是否循环
        """
        super().__init__(name="闲置", duration=duration, loop=loop)
        self.animation_name = animation_name
        
    def _on_start(self):
        """开始闲置动画"""
        # 在这里我们会调用动画系统播放闲置动画
        # 这部分将在动画系统实现后集成
        self.logger.debug(f"播放闲置动画: {self.animation_name}")


class MoveBehavior(BasicBehavior):
    """移动行为
    
    使桌宠在屏幕上移动，可以是定向移动或随机移动
    """
    
    def __init__(self, speed=100, direction=None, random_direction=False, duration=5, loop=False):
        """初始化移动行为
        
        Args:
            speed (int, optional): 移动速度（像素/秒）
            direction (tuple, optional): 移动方向 (dx, dy)，None表示随机方向
            random_direction (bool, optional): 是否使用随机方向
            duration (float, optional): 持续时间
            loop (bool, optional): 是否循环
        """
        super().__init__(name="移动", duration=duration, loop=loop)
        self.speed = speed
        self.direction = direction
        self.random_direction = random_direction
        self.current_position = None
        self.target_position = None
        self.env_sensor = EnvironmentSensor.get_instance()
        
    def _on_start(self):
        """开始移动行为"""
        # 获取当前位置
        self.current_position = self.env_sensor.get_window_position()
        
        # 如果需要随机方向，则生成随机方向
        if self.random_direction or self.direction is None:
            angle = random.uniform(0, 2 * 3.14159)
            dx = self.speed * math.cos(angle)
            dy = self.speed * math.sin(angle)
            self.direction = (dx, dy)
            
        # 计算目标位置
        distance = self.speed * self.duration if self.duration else self.speed * 5
        target_x = self.current_position.x() + int(self.direction[0] * distance / self.speed)
        target_y = self.current_position.y() + int(self.direction[1] * distance / self.speed)
        
        # 确保目标位置在屏幕范围内
        screen_bounds = self.env_sensor.get_screen_boundaries()
        target_x = max(screen_bounds['x'], min(target_x, screen_bounds['x'] + screen_bounds['width'] - self.current_position.width()))
        target_y = max(screen_bounds['y'], min(target_y, screen_bounds['y'] + screen_bounds['height'] - self.current_position.height()))
        
        self.target_position = QPoint(target_x, target_y)
        self.logger.debug(f"开始移动: 从 ({self.current_position.x()}, {self.current_position.y()}) 到 ({target_x}, {target_y})")
        
    def _on_update(self, dt):
        """更新移动状态
        
        Args:
            dt (float): 时间增量（秒）
        """
        current_pos = self.env_sensor.get_window_position()
        
        # 计算当前位置到目标位置的方向向量
        dx = self.target_position.x() - current_pos.x()
        dy = self.target_position.y() - current_pos.y()
        
        # 计算距离
        distance = (dx**2 + dy**2)**0.5
        
        # 如果已经非常接近目标位置，则直接设置为目标位置
        if distance < 5:
            # 这里应该调用窗口移动到目标位置的API
            self.logger.debug(f"到达目标位置: ({self.target_position.x()}, {self.target_position.y()})")
            return
            
        # 标准化方向向量
        if distance > 0:
            dx /= distance
            dy /= distance
            
        # 计算这一帧要移动的距离
        move_distance = self.speed * dt
        
        # 计算新位置
        new_x = current_pos.x() + int(dx * move_distance)
        new_y = current_pos.y() + int(dy * move_distance)
        
        # 这里应该调用窗口移动到新位置的API
        self.logger.debug(f"移动到: ({new_x}, {new_y})")


class JumpBehavior(BasicBehavior):
    """跳跃行为
    
    使桌宠执行跳跃动作
    """
    
    def __init__(self, height=50, duration=1.0, loop=False):
        """初始化跳跃行为
        
        Args:
            height (int, optional): 跳跃高度（像素）
            duration (float, optional): 持续时间
            loop (bool, optional): 是否循环
        """
        super().__init__(name="跳跃", duration=duration, loop=loop)
        self.height = height
        self.start_y = None
        self.env_sensor = EnvironmentSensor.get_instance()
        
    def _on_start(self):
        """开始跳跃行为"""
        current_pos = self.env_sensor.get_window_position()
        self.start_y = current_pos.y()
        self.logger.debug(f"开始跳跃: 初始高度 {self.start_y} 目标高度 {self.start_y - self.height}")
        
    def _on_update(self, dt):
        """更新跳跃状态
        
        Args:
            dt (float): 时间增量（秒）
        """
        if self.start_y is None:
            return
            
        current_pos = self.env_sensor.get_window_position()
        
        # 计算跳跃进度 (0-1)
        progress = (time.time() - self.start_time) / self.duration if self.duration else 0
        progress = min(1.0, progress)
        
        # 使用正弦函数模拟跳跃曲线（上升然后下降）
        jump_factor = math.sin(progress * math.pi)
        
        # 计算当前应该的Y坐标
        new_y = self.start_y - int(self.height * jump_factor)
        
        # 这里应该调用窗口移动到新位置的API
        self.logger.debug(f"跳跃高度: {new_y} (进度: {progress:.2f})")
        
    def _on_complete(self):
        """完成跳跃，确保回到原始高度"""
        current_pos = self.env_sensor.get_window_position()
        
        # 确保桌宠回到初始高度
        if self.start_y is not None and current_pos.y() != self.start_y:
            # 这里应该调用窗口移动到原始高度的API
            self.logger.debug(f"跳跃完成，恢复到初始高度: {self.start_y}")


class FallBehavior(BasicBehavior):
    """下落行为
    
    使桌宠执行下落动作，模拟重力效果
    """
    
    def __init__(self, gravity=980, duration=None, loop=False):
        """初始化下落行为
        
        Args:
            gravity (int, optional): 重力加速度（像素/秒²）
            duration (float, optional): 持续时间，None表示直到碰到底部
            loop (bool, optional): 是否循环
        """
        super().__init__(name="下落", duration=duration, loop=loop)
        self.gravity = gravity
        self.velocity = 0  # 初始速度为0
        self.start_y = None
        self.env_sensor = EnvironmentSensor.get_instance()
        
    def _on_start(self):
        """开始下落行为"""
        current_pos = self.env_sensor.get_window_position()
        self.start_y = current_pos.y()
        self.velocity = 0
        self.logger.debug(f"开始下落: 初始高度 {self.start_y}")
        
    def _on_update(self, dt):
        """更新下落状态
        
        Args:
            dt (float): 时间增量（秒）
        """
        current_pos = self.env_sensor.get_window_position()
        
        # 更新速度（加速度 * 时间）
        self.velocity += self.gravity * dt
        
        # 计算新位置
        new_y = current_pos.y() + int(self.velocity * dt)
        
        # 检查是否到达屏幕底部
        screen_bounds = self.env_sensor.get_screen_boundaries()
        bottom = screen_bounds['y'] + screen_bounds['height'] - current_pos.height()
        
        if new_y >= bottom:
            new_y = bottom
            self.velocity = 0
            self.logger.debug(f"到达底部: {new_y}")
            
            # 如果没有指定持续时间，则在到达底部时完成
            if self.duration is None:
                self._on_complete()
                self.is_running = False
                
        # 这里应该调用窗口移动到新位置的API
        self.logger.debug(f"下落到: {new_y} (速度: {self.velocity:.2f})")


class SleepBehavior(BasicBehavior):
    """睡眠行为
    
    使桌宠进入睡眠状态，可以播放睡眠动画
    """
    
    def __init__(self, animation_name="sleep", duration=None, loop=True):
        """初始化睡眠行为
        
        Args:
            animation_name (str, optional): 动画名称
            duration (float, optional): 持续时间
            loop (bool, optional): 是否循环
        """
        super().__init__(name="睡眠", duration=duration, loop=loop)
        self.animation_name = animation_name
        
    def _on_start(self):
        """开始睡眠动画"""
        # 在这里我们会调用动画系统播放睡眠动画
        # 这部分将在动画系统实现后集成
        self.logger.debug(f"播放睡眠动画: {self.animation_name}")


class PlayAnimationBehavior(BasicBehavior):
    """播放动画行为
    
    播放指定的动画序列
    """
    
    def __init__(self, animation_name, duration=None, loop=False):
        """初始化播放动画行为
        
        Args:
            animation_name (str): 动画名称
            duration (float, optional): 持续时间
            loop (bool, optional): 是否循环
        """
        super().__init__(name=f"播放动画:{animation_name}", duration=duration, loop=loop)
        self.animation_name = animation_name
        
    def _on_start(self):
        """开始播放动画"""
        # 在这里我们会调用动画系统播放指定动画
        # 这部分将在动画系统实现后集成
        self.logger.debug(f"播放动画: {self.animation_name}")


# 确保导入math模块
import math

# 初始化行为注册表并注册基础行为
def initialize_behaviors():
    """初始化行为注册表，注册所有基础行为"""
    registry = BehaviorRegistry.get_instance()
    
    # 注册闲置行为
    registry.register('idle', IdleBehavior, animation_name="idle", loop=True)
    
    # 注册移动行为
    registry.register('move', MoveBehavior, speed=100, duration=5)
    registry.register('move_random', MoveBehavior, speed=100, random_direction=True, duration=5)
    registry.register('move_left', MoveBehavior, speed=100, direction=(-1, 0), duration=3)
    registry.register('move_right', MoveBehavior, speed=100, direction=(1, 0), duration=3)
    registry.register('move_up', MoveBehavior, speed=100, direction=(0, -1), duration=3)
    registry.register('move_down', MoveBehavior, speed=100, direction=(0, 1), duration=3)
    
    # 注册跳跃行为
    registry.register('jump', JumpBehavior, height=50, duration=1.0)
    registry.register('high_jump', JumpBehavior, height=100, duration=1.5)
    
    # 注册下落行为
    registry.register('fall', FallBehavior)
    
    # 注册睡眠行为
    registry.register('sleep', SleepBehavior, animation_name="sleep", loop=True)
    
    # 注册播放动画行为（可以根据实际动画资源扩展）
    registry.register('play_animation', PlayAnimationBehavior, animation_name="default")
    registry.register('wave', PlayAnimationBehavior, animation_name="wave", duration=2.0)
    registry.register('nod', PlayAnimationBehavior, animation_name="nod", duration=1.5)
    registry.register('dance', PlayAnimationBehavior, animation_name="dance", duration=5.0, loop=True)
    
    return registry 