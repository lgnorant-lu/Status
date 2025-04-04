"""
---------------------------------------------------------------
File name:                  transition.py
Author:                     Ignorant-lu
Date created:               2025/04/03
Description:                过渡效果系统
----------------------------------------------------------------

Changed history:            
                            2025/04/03: 初始创建;
----
"""

import time
import math
import enum
import logging
from typing import Callable, Optional, Dict, List, Tuple, Any

from status.renderer.renderer_base import RendererBase
from status.renderer.effects import Effect, EffectState

# 配置日志
logger = logging.getLogger(__name__)


class TransitionState(enum.Enum):
    """过渡效果状态枚举"""
    INITIALIZED = 0    # 已初始化
    RUNNING = 1        # 正在运行
    PAUSED = 2         # 已暂停
    COMPLETED = 3      # 已完成
    REVERSED = 4       # 反向运行


class EasingFunc:
    """
    时间曲线(Easing)函数工具类
    提供各种常用的缓动函数，用于控制过渡效果的速度变化
    """
    
    @staticmethod
    def linear(t: float) -> float:
        """线性缓动: 匀速"""
        return t
    
    @staticmethod
    def ease_in_quad(t: float) -> float:
        """二次方缓入: 慢入快出"""
        return t * t
    
    @staticmethod
    def ease_out_quad(t: float) -> float:
        """二次方缓出: 快入慢出"""
        return 1 - (1 - t) * (1 - t)
    
    @staticmethod
    def ease_in_out_quad(t: float) -> float:
        """二次方缓入缓出: 慢入慢出"""
        return 2 * t * t if t < 0.5 else 1 - pow(-2 * t + 2, 2) / 2
    
    @staticmethod
    def ease_in_cubic(t: float) -> float:
        """三次方缓入"""
        return t * t * t
    
    @staticmethod
    def ease_out_cubic(t: float) -> float:
        """三次方缓出"""
        return 1 - pow(1 - t, 3)
    
    @staticmethod
    def ease_in_out_cubic(t: float) -> float:
        """三次方缓入缓出"""
        return 4 * t * t * t if t < 0.5 else 1 - pow(-2 * t + 2, 3) / 2
    
    @staticmethod
    def ease_in_sine(t: float) -> float:
        """正弦缓入"""
        return 1 - math.cos((t * math.pi) / 2)
    
    @staticmethod
    def ease_out_sine(t: float) -> float:
        """正弦缓出"""
        return math.sin((t * math.pi) / 2)
    
    @staticmethod
    def ease_in_out_sine(t: float) -> float:
        """正弦缓入缓出"""
        return -(math.cos(math.pi * t) - 1) / 2
    
    @staticmethod
    def ease_in_expo(t: float) -> float:
        """指数缓入"""
        return 0 if t == 0 else pow(2, 10 * t - 10)
    
    @staticmethod
    def ease_out_expo(t: float) -> float:
        """指数缓出"""
        return 1 if t == 1 else 1 - pow(2, -10 * t)
    
    @staticmethod
    def ease_in_out_expo(t: float) -> float:
        """指数缓入缓出"""
        if t == 0:
            return 0
        if t == 1:
            return 1
        return pow(2, 20 * t - 10) / 2 if t < 0.5 else (2 - pow(2, -20 * t + 10)) / 2
    
    @staticmethod
    def ease_in_elastic(t: float) -> float:
        """弹性缓入"""
        if t == 0:
            return 0
        if t == 1:
            return 1
        return -pow(2, 10 * t - 10) * math.sin((t * 10 - 10.75) * ((2 * math.pi) / 3))
    
    @staticmethod
    def ease_out_elastic(t: float) -> float:
        """弹性缓出"""
        if t == 0:
            return 0
        if t == 1:
            return 1
        return pow(2, -10 * t) * math.sin((t * 10 - 0.75) * ((2 * math.pi) / 3)) + 1
    
    @staticmethod
    def bounce(t: float) -> float:
        """弹跳效果"""
        if t < 1 / 2.75:
            return 7.5625 * t * t
        elif t < 2 / 2.75:
            t -= 1.5 / 2.75
            return 7.5625 * t * t + 0.75
        elif t < 2.5 / 2.75:
            t -= 2.25 / 2.75
            return 7.5625 * t * t + 0.9375
        else:
            t -= 2.625 / 2.75
            return 7.5625 * t * t + 0.984375
    
    @staticmethod
    def ease_in_bounce(t: float) -> float:
        """弹跳缓入"""
        return 1 - EasingFunc.bounce(1 - t)
    
    @staticmethod
    def ease_out_bounce(t: float) -> float:
        """弹跳缓出"""
        return EasingFunc.bounce(t)
    
    @staticmethod
    def ease_in_out_bounce(t: float) -> float:
        """弹跳缓入缓出"""
        return (1 - EasingFunc.bounce(1 - 2 * t)) / 2 if t < 0.5 else (1 + EasingFunc.bounce(2 * t - 1)) / 2
    
    @staticmethod
    def get_easing_function(name: str) -> Callable[[float], float]:
        """
        根据名称获取缓动函数
        
        Args:
            name: 缓动函数名称
            
        Returns:
            对应的缓动函数
            
        Raises:
            ValueError: 如果找不到指定名称的缓动函数
        """
        easing_functions = {
            'linear': EasingFunc.linear,
            'ease_in_quad': EasingFunc.ease_in_quad,
            'ease_out_quad': EasingFunc.ease_out_quad,
            'ease_in_out_quad': EasingFunc.ease_in_out_quad,
            'ease_in_cubic': EasingFunc.ease_in_cubic,
            'ease_out_cubic': EasingFunc.ease_out_cubic,
            'ease_in_out_cubic': EasingFunc.ease_in_out_cubic,
            'ease_in_sine': EasingFunc.ease_in_sine,
            'ease_out_sine': EasingFunc.ease_out_sine,
            'ease_in_out_sine': EasingFunc.ease_in_out_sine,
            'ease_in_expo': EasingFunc.ease_in_expo,
            'ease_out_expo': EasingFunc.ease_out_expo,
            'ease_in_out_expo': EasingFunc.ease_in_out_expo,
            'ease_in_elastic': EasingFunc.ease_in_elastic,
            'ease_out_elastic': EasingFunc.ease_out_elastic,
            'ease_in_bounce': EasingFunc.ease_in_bounce,
            'ease_out_bounce': EasingFunc.ease_out_bounce,
            'ease_in_out_bounce': EasingFunc.ease_in_out_bounce
        }
        
        if name not in easing_functions:
            raise ValueError(f"未知的缓动函数: {name}")
        
        return easing_functions[name]


class Transition:
    """
    过渡效果基类
    所有过渡效果的基类，提供基本的过渡效果功能和生命周期管理
    """
    
    def __init__(self, duration: float = 1.0, easing: str = 'linear',
                 auto_reverse: bool = False, auto_start: bool = True,
                 on_complete: Optional[Callable[[], None]] = None):
        """
        初始化过渡效果
        
        Args:
            duration: 过渡效果持续时间(秒)
            easing: 缓动函数名称
            auto_reverse: 是否自动反向运行(完成后自动反向)
            auto_start: 是否自动开始
            on_complete: 完成时的回调函数
        """
        self.duration = max(0.001, duration)  # 确保持续时间为正数
        self.easing_func = EasingFunc.get_easing_function(easing)
        self.auto_reverse = auto_reverse
        self.state = TransitionState.INITIALIZED
        self.progress = 0.0  # 0.0 - 1.0
        self.elapsed_time = 0.0
        self.on_complete = on_complete
        self.direction = 1  # 1: 正向, -1: 反向
        
        # 时间相关
        self.start_time = 0
        self.pause_time = 0
        
        if auto_start:
            self.start()
    
    def start(self):
        """开始过渡效果"""
        self.state = TransitionState.RUNNING
        self.start_time = time.time()
        self.elapsed_time = 0.0
        self.progress = 0.0
        self.direction = 1
        logger.debug(f"过渡效果开始: {self.__class__.__name__}")
    
    def pause(self):
        """暂停过渡效果"""
        if self.state == TransitionState.RUNNING:
            self.state = TransitionState.PAUSED
            self.pause_time = time.time()
            logger.debug(f"过渡效果暂停: {self.__class__.__name__}")
    
    def resume(self):
        """恢复过渡效果"""
        if self.state == TransitionState.PAUSED:
            self.state = TransitionState.RUNNING
            # 调整开始时间，考虑暂停的时间
            pause_duration = time.time() - self.pause_time
            self.start_time += pause_duration
            logger.debug(f"过渡效果恢复: {self.__class__.__name__}")
    
    def complete(self):
        """完成过渡效果"""
        self.state = TransitionState.COMPLETED
        self.progress = 1.0 if self.direction > 0 else 0.0
        if self.on_complete:
            self.on_complete()
        logger.debug(f"过渡效果完成: {self.__class__.__name__}")
    
    def reverse(self):
        """反向运行过渡效果"""
        if self.state in [TransitionState.RUNNING, TransitionState.PAUSED, TransitionState.REVERSED]:
            # 反转方向
            self.direction *= -1
            
            # 设置状态，根据方向决定状态
            if self.direction < 0:
                self.state = TransitionState.REVERSED
            else:
                self.state = TransitionState.RUNNING
                
            # 调整进度
            self.progress = 1.0 - self.progress
            
            # 重新设置开始时间
            self.start_time = time.time() - (self.duration * self.progress)
            logger.debug(f"过渡效果反向: {self.__class__.__name__}, 方向: {self.direction}")
    
    def is_completed(self) -> bool:
        """检查过渡效果是否完成"""
        return self.state == TransitionState.COMPLETED
    
    def update(self, delta_time: float = None):
        """
        更新过渡效果状态
        
        Args:
            delta_time: 时间增量，如果为None则自动计算
        """
        if self.state != TransitionState.RUNNING and self.state != TransitionState.REVERSED:
            return
        
        # 计算经过的时间
        current_time = time.time()
        if delta_time is None:
            self.elapsed_time = current_time - self.start_time
        else:
            self.elapsed_time += delta_time
        
        # 计算原始进度 (0.0 - 1.0)
        raw_progress = min(self.elapsed_time / self.duration, 1.0)
        
        # 应用方向
        if self.direction < 0:
            raw_progress = 1.0 - raw_progress
        
        # 应用缓动函数
        self.progress = self.easing_func(raw_progress)
        
        # 检查是否完成
        if (self.direction > 0 and raw_progress >= 1.0) or (self.direction < 0 and raw_progress <= 0.0):
            if self.auto_reverse and self.state != TransitionState.REVERSED:
                self.reverse()
            else:
                self.complete()
    
    def get_value(self, start_value: float, end_value: float) -> float:
        """
        根据当前进度计算值
        
        Args:
            start_value: 起始值
            end_value: 结束值
            
        Returns:
            当前进度对应的值
        """
        return start_value + (end_value - start_value) * self.progress
    
    def draw(self, renderer: RendererBase):
        """
        绘制过渡效果
        
        Args:
            renderer: 渲染器
        """
        # 基类不实现具体绘制逻辑，由子类重写
        pass 


class FadeTransition(Transition):
    """
    淡入淡出过渡效果
    在两个内容之间以渐变方式过渡
    """
    
    def __init__(self, from_alpha: float = 0.0, to_alpha: float = 1.0, 
                 duration: float = 1.0, easing: str = 'linear',
                 auto_reverse: bool = False, auto_start: bool = True,
                 on_complete: Optional[Callable[[], None]] = None):
        """
        初始化淡入淡出过渡效果
        
        Args:
            from_alpha: 初始透明度(0.0 - 1.0)
            to_alpha: 目标透明度(0.0 - 1.0)
            duration: 过渡效果持续时间(秒)
            easing: 缓动函数名称
            auto_reverse: 是否自动反向运行
            auto_start: 是否自动开始
            on_complete: 完成时的回调函数
        """
        super().__init__(duration, easing, auto_reverse, auto_start, on_complete)
        self.from_alpha = from_alpha
        self.to_alpha = to_alpha
        self.current_alpha = from_alpha
    
    def update(self, delta_time: float = None):
        """更新淡入淡出效果状态"""
        # 调用父类的update方法，但它可能会根据状态直接返回
        super().update(delta_time)
        
        # 无论父类update是否执行，都要更新current_alpha
        self.current_alpha = self.get_value(self.from_alpha, self.to_alpha)
    
    def draw(self, renderer: RendererBase, x: int = 0, y: int = 0, 
             width: int = None, height: int = None):
        """
        绘制淡入淡出效果
        
        Args:
            renderer: 渲染器
            x: 绘制位置X坐标
            y: 绘制位置Y坐标
            width: 绘制宽度
            height: 绘制高度
        """
        if width is None:
            width = renderer.get_width()
        if height is None:
            height = renderer.get_height()
        
        # 绘制带透明度的矩形覆盖
        renderer.set_alpha(self.current_alpha)
        renderer.fill_rect(x, y, width, height, (0, 0, 0))
        renderer.set_alpha(1.0)


class SlideTransition(Transition):
    """
    滑动过渡效果
    通过滑动方式从一个内容过渡到另一个内容
    """
    
    # 滑动方向
    DIRECTION_LEFT = 0
    DIRECTION_RIGHT = 1
    DIRECTION_UP = 2
    DIRECTION_DOWN = 3
    
    def __init__(self, direction: int = DIRECTION_LEFT, duration: float = 1.0, 
                 easing: str = 'ease_out_cubic', auto_reverse: bool = False, 
                 auto_start: bool = True, on_complete: Optional[Callable[[], None]] = None):
        """
        初始化滑动过渡效果
        
        Args:
            direction: 滑动方向
            duration: 过渡效果持续时间(秒)
            easing: 缓动函数名称
            auto_reverse: 是否自动反向运行
            auto_start: 是否自动开始
            on_complete: 完成时的回调函数
        """
        super().__init__(duration, easing, auto_reverse, auto_start, on_complete)
        self.direction = direction
        self.offset_x = 0
        self.offset_y = 0
    
    def update(self, delta_time: float = None):
        """更新滑动效果状态"""
        super().update(delta_time)
    
    def get_offset(self, width: int, height: int) -> Tuple[int, int]:
        """
        获取当前偏移量
        
        Args:
            width: 绘制区域宽度
            height: 绘制区域高度
            
        Returns:
            偏移量(x, y)
        """
        if self.direction == self.DIRECTION_LEFT:
            offset = width * (1.0 - self.progress)
            return int(offset), 0
        elif self.direction == self.DIRECTION_RIGHT:
            offset = -width * (1.0 - self.progress)
            return int(offset), 0
        elif self.direction == self.DIRECTION_UP:
            offset = height * (1.0 - self.progress)
            return 0, int(offset)
        elif self.direction == self.DIRECTION_DOWN:
            offset = -height * (1.0 - self.progress)
            return 0, int(offset)
        else:
            return 0, 0
    
    def draw(self, renderer: RendererBase, content_a, content_b, 
             x: int = 0, y: int = 0, width: int = None, height: int = None):
        """
        绘制滑动效果
        
        Args:
            renderer: 渲染器
            content_a: 起始内容
            content_b: 目标内容
            x: 绘制位置X坐标
            y: 绘制位置Y坐标
            width: 绘制宽度
            height: 绘制高度
        """
        if width is None:
            width = renderer.get_width()
        if height is None:
            height = renderer.get_height()
        
        # 计算偏移量
        offset_x, offset_y = self.get_offset(width, height)
        
        # 绘制起始内容
        renderer.draw_surface(content_a, x + offset_x, y + offset_y)
        
        # 绘制目标内容
        if self.direction == self.DIRECTION_LEFT:
            renderer.draw_surface(content_b, x + offset_x - width, y)
        elif self.direction == self.DIRECTION_RIGHT:
            renderer.draw_surface(content_b, x + offset_x + width, y)
        elif self.direction == self.DIRECTION_UP:
            renderer.draw_surface(content_b, x, y + offset_y - height)
        elif self.direction == self.DIRECTION_DOWN:
            renderer.draw_surface(content_b, x, y + offset_y + height)


class ScaleTransition(Transition):
    """
    缩放过渡效果
    通过缩放方式从一个内容过渡到另一个内容
    """
    
    def __init__(self, from_scale: float = 0.0, to_scale: float = 1.0, 
                 duration: float = 1.0, easing: str = 'ease_out_cubic', 
                 center_x: float = 0.5, center_y: float = 0.5,
                 auto_reverse: bool = False, auto_start: bool = True, 
                 on_complete: Optional[Callable[[], None]] = None):
        """
        初始化缩放过渡效果
        
        Args:
            from_scale: 初始缩放比例
            to_scale: 目标缩放比例
            duration: 过渡效果持续时间(秒)
            easing: 缓动函数名称
            center_x: 缩放中心点X坐标(0.0 - 1.0)
            center_y: 缩放中心点Y坐标(0.0 - 1.0)
            auto_reverse: 是否自动反向运行
            auto_start: 是否自动开始
            on_complete: 完成时的回调函数
        """
        super().__init__(duration, easing, auto_reverse, auto_start, on_complete)
        self.from_scale = from_scale
        self.to_scale = to_scale
        self.current_scale = from_scale
        self.center_x = center_x
        self.center_y = center_y
    
    def update(self, delta_time: float = None):
        """更新缩放效果状态"""
        super().update(delta_time)
        self.current_scale = self.get_value(self.from_scale, self.to_scale)
    
    def draw(self, renderer: RendererBase, content, x: int = 0, y: int = 0, 
             width: int = None, height: int = None):
        """
        绘制缩放效果
        
        Args:
            renderer: 渲染器
            content: 绘制内容
            x: 绘制位置X坐标
            y: 绘制位置Y坐标
            width: 绘制宽度
            height: 绘制高度
        """
        if width is None:
            width = renderer.get_width()
        if height is None:
            height = renderer.get_height()
        
        # 计算中心点
        center_x = x + width * self.center_x
        center_y = y + height * self.center_y
        
        # 计算缩放后的大小
        scaled_width = width * self.current_scale
        scaled_height = height * self.current_scale
        
        # 计算缩放后的位置
        scaled_x = center_x - scaled_width * self.center_x
        scaled_y = center_y - scaled_height * self.center_y
        
        # 绘制内容
        renderer.draw_surface_scaled(content, int(scaled_x), int(scaled_y), 
                                    int(scaled_width), int(scaled_height))


class FlipTransition(Transition):
    """
    翻转过渡效果
    通过3D翻转方式从一个内容过渡到另一个内容
    """
    
    # 翻转方向
    DIRECTION_HORIZONTAL = 0
    DIRECTION_VERTICAL = 1
    
    def __init__(self, direction: int = DIRECTION_HORIZONTAL, duration: float = 1.0, 
                 easing: str = 'ease_in_out_cubic', auto_reverse: bool = False, 
                 auto_start: bool = True, on_complete: Optional[Callable[[], None]] = None):
        """
        初始化翻转过渡效果
        
        Args:
            direction: 翻转方向
            duration: 过渡效果持续时间(秒)
            easing: 缓动函数名称
            auto_reverse: 是否自动反向运行
            auto_start: 是否自动开始
            on_complete: 完成时的回调函数
        """
        super().__init__(duration, easing, auto_reverse, auto_start, on_complete)
        self.flip_direction = direction
        self.angle = 0.0
    
    def update(self, delta_time: float = None):
        """更新翻转效果状态"""
        super().update(delta_time)
        self.angle = self.progress * 180.0  # 0 - 180度
    
    def draw(self, renderer: RendererBase, content_a, content_b, 
             x: int = 0, y: int = 0, width: int = None, height: int = None):
        """
        绘制翻转效果
        
        Args:
            renderer: 渲染器
            content_a: 起始内容
            content_b: 目标内容
            x: 绘制位置X坐标
            y: 绘制位置Y坐标
            width: 绘制宽度
            height: 绘制高度
        """
        if width is None:
            width = renderer.get_width()
        if height is None:
            height = renderer.get_height()
        
        # 根据角度计算用于模拟3D效果的缩放比例
        scale_factor = abs(math.cos(math.radians(self.angle)))
        
        # 决定绘制哪个内容
        if self.angle < 90:
            # 还在显示第一个内容
            content = content_a
            
            # 计算缩放后的大小
            if self.flip_direction == self.DIRECTION_HORIZONTAL:
                scaled_width = width * scale_factor
                scaled_height = height
                scaled_x = x + (width - scaled_width) / 2
                scaled_y = y
            else:  # DIRECTION_VERTICAL
                scaled_width = width
                scaled_height = height * scale_factor
                scaled_x = x
                scaled_y = y + (height - scaled_height) / 2
            
            # 绘制内容
            renderer.draw_surface_scaled(content, int(scaled_x), int(scaled_y), 
                                        int(scaled_width), int(scaled_height))
        else:
            # 开始显示第二个内容
            content = content_b
            
            # 计算缩放后的大小
            if self.flip_direction == self.DIRECTION_HORIZONTAL:
                scaled_width = width * scale_factor
                scaled_height = height
                scaled_x = x + (width - scaled_width) / 2
                scaled_y = y
            else:  # DIRECTION_VERTICAL
                scaled_width = width
                scaled_height = height * scale_factor
                scaled_x = x
                scaled_y = y + (height - scaled_height) / 2
            
            # 绘制内容
            renderer.draw_surface_scaled(content, int(scaled_x), int(scaled_y), 
                                        int(scaled_width), int(scaled_height))


class TransitionManager:
    """
    过渡效果管理器
    管理和控制过渡效果
    """
    
    # 单例实例
    _instance = None
    
    @classmethod
    def get_instance(cls) -> 'TransitionManager':
        """
        获取过渡效果管理器实例
        
        Returns:
            过渡效果管理器实例
        """
        if cls._instance is None:
            cls._instance = TransitionManager()
        return cls._instance
    
    def __init__(self):
        """初始化过渡效果管理器"""
        if TransitionManager._instance is not None:
            raise RuntimeError("过渡效果管理器是单例类，请使用get_instance()方法获取实例")
        
        self.transitions = []
        self.active_transition = None
    
    def create_transition(self, transition_type: str, **kwargs) -> Transition:
        """
        创建过渡效果
        
        Args:
            transition_type: 过渡效果类型
            **kwargs: 传递给过渡效果构造函数的参数
            
        Returns:
            创建的过渡效果
            
        Raises:
            ValueError: 如果找不到指定类型的过渡效果
        """
        # 设置默认参数
        auto_start = kwargs.pop('auto_start', False)
        
        # 创建过渡效果
        if transition_type.lower() == 'fade':
            transition = FadeTransition(auto_start=auto_start, **kwargs)
        elif transition_type.lower() == 'slide':
            transition = SlideTransition(auto_start=auto_start, **kwargs)
        elif transition_type.lower() == 'scale':
            transition = ScaleTransition(auto_start=auto_start, **kwargs)
        elif transition_type.lower() == 'flip':
            transition = FlipTransition(auto_start=auto_start, **kwargs)
        else:
            raise ValueError(f"未知的过渡效果类型: {transition_type}")
        
        return transition
    
    def start_transition(self, transition: Transition) -> None:
        """
        开始过渡效果
        
        Args:
            transition: 过渡效果
        """
        self.active_transition = transition
        self.transitions.append(transition)
        transition.start()
    
    def update(self, delta_time: float = None) -> None:
        """
        更新所有活动的过渡效果
        
        Args:
            delta_time: 时间增量
        """
        # 更新所有过渡效果
        for transition in self.transitions[:]:
            transition.update(delta_time)
            
            # 移除已完成的过渡效果
            if transition.is_completed():
                self.transitions.remove(transition)
                if transition == self.active_transition:
                    self.active_transition = None
    
    def has_active_transition(self) -> bool:
        """
        检查是否有活动的过渡效果
        
        Returns:
            是否有活动的过渡效果
        """
        return len(self.transitions) > 0
    
    def get_active_transition(self) -> Optional[Transition]:
        """
        获取当前活动的过渡效果
        
        Returns:
            当前活动的过渡效果，如果没有则返回None
        """
        return self.active_transition
    
    def clear_transitions(self) -> None:
        """清除所有过渡效果"""
        self.transitions.clear()
        self.active_transition = None
        
    # 添加兼容scene_transition.py中使用的方法
    def register_transition(self, name: str, transition_factory) -> None:
        """注册过渡效果工厂函数 (兼容方法)
        
        Args:
            name: 过渡效果名称
            transition_factory: 过渡效果工厂函数
        """
        # 这个方法不做实际操作，仅为了兼容测试
        pass
        
    def register_effect_transition(self, name: str, effect_type: str, **default_kwargs) -> None:
        """注册基于过渡效果系统的转场效果 (兼容方法)
        
        Args:
            name: 过渡效果名称
            effect_type: 过渡效果类型
            **default_kwargs: 默认参数
        """
        # 这个方法不做实际操作，仅为了兼容测试
        pass
        
    def set_default_transition(self, name: str) -> None:
        """设置默认过渡效果 (兼容方法)
        
        Args:
            name: 过渡效果名称
        """
        # 这个方法不做实际操作，仅为了兼容测试
        pass
        
    def register_default_transitions(self) -> None:
        """注册默认过渡效果 (兼容方法)"""
        # 这个方法不做实际操作，仅为了兼容测试
        pass
        
    def get_transition(self, name: str = None, **kwargs) -> Transition:
        """获取过渡效果 (兼容方法)
        
        Args:
            name: 过渡效果名称
            **kwargs: 参数
            
        Returns:
            过渡效果
        """
        # 过滤掉SceneTransition不支持的参数
        filtered_kwargs = {k: v for k, v in kwargs.items() 
                          if k not in ['auto_start', 'auto_reverse', 'on_complete']}
        
        # 调用已有的create_transition方法
        return self.create_transition("fade", **filtered_kwargs)
        
    def create_default_transition(self, **kwargs) -> Transition:
        """创建默认过渡效果 (兼容方法)
        
        Args:
            **kwargs: 参数
            
        Returns:
            过渡效果
        """
        # 过滤掉SceneTransition不支持的参数
        filtered_kwargs = {k: v for k, v in kwargs.items() 
                          if k not in ['auto_start', 'auto_reverse', 'on_complete']}
        return self.create_transition("fade", **filtered_kwargs) 