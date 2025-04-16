"""
---------------------------------------------------------------
File name:                  animation.py
Author:                     Ignorant-lu
Date created:               2025/04/03
Description:                基本动画系统，支持属性动画和过渡效果
----------------------------------------------------------------

Changed history:            
                            2025/04/03: 初始创建;
----
"""

from typing import Dict, List, Tuple, Any, Optional, Callable, Union
import math
import enum
import time

# 导入 QImage 用于类型提示
from PyQt6.QtGui import QImage

from status.renderer.drawable import Drawable

class EasingType(enum.Enum):
    """缓动类型枚举"""
    LINEAR = 0          # 线性
    EASE_IN = 1         # 缓入
    EASE_OUT = 2        # 缓出
    EASE_IN_OUT = 3     # 缓入缓出
    QUAD_IN = 4         # 二次缓入
    QUAD_OUT = 5        # 二次缓出
    QUAD_IN_OUT = 6     # 二次缓入缓出
    CUBIC_IN = 7        # 三次缓入
    CUBIC_OUT = 8       # 三次缓出
    CUBIC_IN_OUT = 9    # 三次缓入缓出
    BOUNCE_IN = 10      # 弹跳缓入
    BOUNCE_OUT = 11     # 弹跳缓出
    ELASTIC_IN = 12     # 弹性缓入
    ELASTIC_OUT = 13    # 弹性缓出

class AnimationState(enum.Enum):
    """动画状态枚举"""
    IDLE = 0            # 空闲
    PLAYING = 1         # 播放中
    PAUSED = 2          # 暂停
    COMPLETED = 3       # 完成

class Animator:
    """动画器基类"""
    
    def __init__(self, duration: float, loop: bool = False, delay: float = 0.0, auto_start: bool = True):
        """初始化动画器
        
        Args:
            duration: 动画持续时间（秒）
            loop: 是否循环播放
            delay: 延迟开始时间（秒）
            auto_start: 是否自动开始播放
        """
        self.duration = max(0.001, duration)  # 避免除零错误
        self.loop = loop
        self.delay = delay
        self.elapsed_time: float = 0.0
        self.state = AnimationState.IDLE
        self.completion_callback = None
        
        if auto_start:
            self.play()
    
    def play(self) -> None:
        """开始播放动画"""
        if self.state == AnimationState.COMPLETED:
            self.elapsed_time = 0
            
        self.state = AnimationState.PLAYING
    
    def pause(self) -> None:
        """暂停播放动画"""
        if self.state == AnimationState.PLAYING:
            self.state = AnimationState.PAUSED
    
    def stop(self) -> None:
        """停止播放动画"""
        self.state = AnimationState.IDLE
        self.elapsed_time = 0
    
    def resume(self) -> None:
        """恢复播放动画"""
        if self.state == AnimationState.PAUSED:
            self.state = AnimationState.PLAYING
    
    def set_completion_callback(self, callback: Callable[[], None]) -> None:
        """设置动画完成回调
        
        Args:
            callback: 回调函数
        """
        self.completion_callback = callback
    
    def is_playing(self) -> bool:
        """检查是否正在播放
        
        Returns:
            bool: 是否正在播放
        """
        return self.state == AnimationState.PLAYING
    
    def is_completed(self) -> bool:
        """检查是否已完成
        
        Returns:
            bool: 是否已完成
        """
        return self.state == AnimationState.COMPLETED
    
    def get_progress(self) -> float:
        """获取动画进度
        
        Returns:
            float: 进度值（0.0-1.0）
        """
        if self.elapsed_time <= self.delay:
            return 0.0
            
        time = self.elapsed_time - self.delay
        if self.loop:
            time = time % self.duration
            
        progress = min(time / self.duration, 1.0)
        return progress
    
    def update(self, dt: float) -> None:
        """更新动画状态
        
        Args:
            dt: 时间增量（秒）
        """
        if self.state != AnimationState.PLAYING:
            return
            
        self.elapsed_time += dt
        
        # 检查延迟
        if self.elapsed_time <= self.delay:
            return
            
        # 检查完成
        if not self.loop and self.elapsed_time - self.delay >= self.duration:
            self.state = AnimationState.COMPLETED
            
            # 调用完成回调
            if self.completion_callback:
                self.completion_callback()
                
        self._update_animation(dt)
    
    def _update_animation(self, dt: float) -> None:
        """更新动画逻辑，由子类实现
        
        Args:
            dt: 时间增量（秒）
        """
        pass
    
    def _apply_easing(self, progress: float, easing_type: EasingType) -> float:
        """应用缓动函数
        
        Args:
            progress: 线性进度值（0.0-1.0）
            easing_type: 缓动类型
            
        Returns:
            float: 缓动后的进度值
        """
        if easing_type == EasingType.LINEAR:
            return progress
        elif easing_type == EasingType.EASE_IN:
            return progress * progress
        elif easing_type == EasingType.EASE_OUT:
            return progress * (2 - progress)
        elif easing_type == EasingType.EASE_IN_OUT:
            return progress * progress * (3 - 2 * progress)
        elif easing_type == EasingType.QUAD_IN:
            return progress * progress
        elif easing_type == EasingType.QUAD_OUT:
            return progress * (2 - progress)
        elif easing_type == EasingType.QUAD_IN_OUT:
            if progress < 0.5:
                return 2 * progress * progress
            else:
                return -1 + (4 - 2 * progress) * progress
        elif easing_type == EasingType.CUBIC_IN:
            return progress * progress * progress
        elif easing_type == EasingType.CUBIC_OUT:
            p = progress - 1
            return p * p * p + 1
        elif easing_type == EasingType.CUBIC_IN_OUT:
            if progress < 0.5:
                return 4 * progress * progress * progress
            else:
                return (progress - 1) * (2 * progress - 2) * (2 * progress - 2) + 1
        elif easing_type == EasingType.BOUNCE_OUT:
            if progress < (1 / 2.75):
                return 7.5625 * progress * progress
            elif progress < (2 / 2.75):
                progress -= (1.5 / 2.75)
                return 7.5625 * progress * progress + 0.75
            elif progress < (2.5 / 2.75):
                progress -= (2.25 / 2.75)
                return 7.5625 * progress * progress + 0.9375
            else:
                progress -= (2.625 / 2.75)
                return 7.5625 * progress * progress + 0.984375
        elif easing_type == EasingType.BOUNCE_IN:
            return 1 - self._apply_easing(1 - progress, EasingType.BOUNCE_OUT)
        elif easing_type == EasingType.ELASTIC_OUT:
            if progress == 0 or progress == 1:
                return progress
            p = 0.3
            s = p / 4
            return pow(2, -10 * progress) * math.sin((progress - s) * (2 * math.pi) / p) + 1
        elif easing_type == EasingType.ELASTIC_IN:
            if progress == 0 or progress == 1:
                return progress
            p = 0.3
            s = p / 4
            return -(pow(2, 10 * (progress - 1)) * math.sin((progress - 1 - s) * (2 * math.pi) / p))
        else:
            # 默认返回线性
            return progress

class PropertyAnimation(Animator):
    """属性动画类，用于平滑过渡对象属性"""
    
    def __init__(self, target: Any, property_name: str, start_value: Any, end_value: Any,
                duration: float, easing: EasingType = EasingType.LINEAR, loop: bool = False,
                delay: float = 0.0, auto_start: bool = True):
        """初始化属性动画
        
        Args:
            target: 目标对象
            property_name: 属性名称
            start_value: 起始值
            end_value: 结束值
            duration: 动画持续时间（秒）
            easing: 缓动类型
            loop: 是否循环播放
            delay: 延迟开始时间（秒）
            auto_start: 是否自动开始播放
        """
        super().__init__(duration, loop, delay, auto_start)
        
        self.target = target
        self.property_name = property_name
        self.start_value = start_value
        self.end_value = end_value
        self.easing = easing
        
        # 检查属性类型
        self._check_property_type()
    
    def _check_property_type(self) -> None:
        """检查属性类型，确定差值方法"""
        # 尝试获取当前属性值
        try:
            current_value = getattr(self.target, self.property_name)
        except AttributeError:
            raise ValueError(f"目标对象 {self.target} 没有属性 {self.property_name}")
            
        # 根据类型判断插值方法
        if isinstance(self.start_value, (int, float)) and isinstance(self.end_value, (int, float)):
            self._interpolate = self._interpolate_number
        elif isinstance(self.start_value, tuple) and isinstance(self.end_value, tuple):
            if len(self.start_value) == len(self.end_value):
                if all(isinstance(x, (int, float)) for x in self.start_value + self.end_value):
                    self._interpolate = self._interpolate_tuple
                else:
                    raise ValueError("元组中的所有元素必须是数字")
            else:
                raise ValueError("起始值和结束值的元组长度必须相同")
        else:
            raise ValueError(f"不支持的属性类型: {type(self.start_value)}, {type(self.end_value)}")
    
    def _interpolate_number(self, progress: float) -> Union[int, float]:
        """数值插值
        
        Args:
            progress: 进度值（0.0-1.0）
            
        Returns:
            Union[int, float]: 插值结果
        """
        result = self.start_value + progress * (self.end_value - self.start_value)
        if isinstance(self.start_value, int) and isinstance(self.end_value, int):
            return int(round(result))
        return result
    
    def _interpolate_tuple(self, progress: float) -> Tuple:
        """元组插值
        
        Args:
            progress: 进度值（0.0-1.0）
            
        Returns:
            Tuple: 插值结果
        """
        result = []
        for i in range(len(self.start_value)):
            start = self.start_value[i]
            end = self.end_value[i]
            value = start + progress * (end - start)
            
            if isinstance(start, int) and isinstance(end, int):
                value = int(round(value))
                
            result.append(value)
            
        return tuple(result)
    
    def _update_animation(self, dt: float) -> None:
        """更新动画逻辑
        
        Args:
            dt: 时间增量（秒）
        """
        progress = self.get_progress()
        eased_progress = self._apply_easing(progress, self.easing)
        
        # 计算当前值
        current_value = self._interpolate(eased_progress)
        
        # 更新属性
        setattr(self.target, self.property_name, current_value)

class MultiPropertyAnimation(Animator):
    """多属性动画类，同时动画多个属性"""
    
    def __init__(self, duration: float, easing: EasingType = EasingType.LINEAR, loop: bool = False,
                delay: float = 0.0, auto_start: bool = True):
        """初始化多属性动画
        
        Args:
            duration: 动画持续时间（秒）
            easing: 缓动类型
            loop: 是否循环播放
            delay: 延迟开始时间（秒）
            auto_start: 是否自动开始播放
        """
        super().__init__(duration, loop, delay, auto_start)
        
        self.animations: List[PropertyAnimation] = []
        self.easing = easing
    
    def add_property(self, target: Any, property_name: str, start_value: Any, end_value: Any) -> None:
        """添加属性动画
        
        Args:
            target: 目标对象
            property_name: 属性名称
            start_value: 起始值
            end_value: 结束值
        """
        # 创建属性动画，但不自动开始
        animation = PropertyAnimation(
            target, property_name, start_value, end_value,
            self.duration, self.easing, self.loop, self.delay, False
        )
        self.animations.append(animation)
    
    def _update_animation(self, dt: float) -> None:
        """更新动画逻辑
        
        Args:
            dt: 时间增量（秒）
        """
        for animation in self.animations:
            animation.elapsed_time = self.elapsed_time
            animation._update_animation(dt)

class SequenceAnimation(Animator):
    """序列动画类，按顺序播放多个动画"""
    
    def __init__(self, animations: List[Animator], loop: bool = False, auto_start: bool = True):
        """初始化序列动画
        
        Args:
            animations: 动画列表
            loop: 是否循环播放
            auto_start: 是否自动开始播放
        """
        # 计算总持续时间
        total_duration = sum(anim.duration + anim.delay for anim in animations)
        
        super().__init__(total_duration, loop, 0.0, auto_start)
        
        self.animations = animations
        self.current_index = 0
    
    def _update_animation(self, dt: float) -> None:
        """更新动画逻辑
        
        Args:
            dt: 时间增量（秒）
        """
        if not self.animations:
            return
            
        # 计算当前动画
        time_passed = 0
        for i, animation in enumerate(self.animations):
            animation_duration = animation.duration + animation.delay
            
            if time_passed + animation_duration >= self.elapsed_time or i == len(self.animations) - 1:
                # 找到当前动画
                self.current_index = i
                
                # 更新当前动画的时间
                animation.elapsed_time = self.elapsed_time - time_passed
                animation.state = AnimationState.PLAYING
                animation._update_animation(dt)
                
                # 确保之前的动画都已完成
                for j in range(i):
                    prev_anim = self.animations[j]
                    prev_anim.elapsed_time = prev_anim.duration + prev_anim.delay
                    prev_anim.state = AnimationState.COMPLETED
                    prev_anim._update_animation(0)
                
                # 确保之后的动画都未开始
                for j in range(i + 1, len(self.animations)):
                    next_anim = self.animations[j]
                    next_anim.elapsed_time = 0
                    next_anim.state = AnimationState.IDLE
                
                break
                
            time_passed += animation_duration

class DrawableAnimator:
    """可绘制对象动画器，提供常用动画创建功能"""
    
    @staticmethod
    def move_to(drawable: Drawable, x: float, y: float, duration: float, 
               easing: EasingType = EasingType.EASE_OUT, delay: float = 0.0) -> MultiPropertyAnimation:
        """移动到指定位置
        
        Args:
            drawable: 可绘制对象
            x: 目标X坐标
            y: 目标Y坐标
            duration: 动画持续时间（秒）
            easing: 缓动类型
            delay: 延迟开始时间（秒）
            
        Returns:
            MultiPropertyAnimation: 多属性动画对象
        """
        multi_anim = MultiPropertyAnimation(duration, easing, False, delay)
        multi_anim.add_property(drawable, "x", drawable.x, x)
        multi_anim.add_property(drawable, "y", drawable.y, y)
        return multi_anim
    
    @staticmethod
    def scale_to(drawable: Drawable, scale_x: float, scale_y: float, duration: float,
                easing: EasingType = EasingType.EASE_OUT, delay: float = 0.0) -> MultiPropertyAnimation:
        """缩放到指定比例
        
        Args:
            drawable: 可绘制对象
            scale_x: 目标X缩放比例
            scale_y: 目标Y缩放比例
            duration: 动画持续时间（秒）
            easing: 缓动类型
            delay: 延迟开始时间（秒）
            
        Returns:
            MultiPropertyAnimation: 多属性动画对象
        """
        multi_anim = MultiPropertyAnimation(duration, easing, False, delay)
        multi_anim.add_property(drawable, "scale_x", drawable.scale_x, scale_x)
        multi_anim.add_property(drawable, "scale_y", drawable.scale_y, scale_y)
        return multi_anim
    
    @staticmethod
    def rotate_to(drawable: Drawable, angle: float, duration: float,
                easing: EasingType = EasingType.EASE_OUT, delay: float = 0.0) -> PropertyAnimation:
        """旋转到指定角度
        
        Args:
            drawable: 可绘制对象
            angle: 目标角度（度）
            duration: 动画持续时间（秒）
            easing: 缓动类型
            delay: 延迟开始时间（秒）
            
        Returns:
            PropertyAnimation: 属性动画对象
        """
        return PropertyAnimation(drawable, "rotation", drawable.rotation, angle,
                                 duration, easing, False, delay)
    
    @staticmethod
    def fade_to(drawable: Drawable, opacity: float, duration: float,
               easing: EasingType = EasingType.EASE_OUT, delay: float = 0.0) -> PropertyAnimation:
        """淡入淡出到指定不透明度
        
        Args:
            drawable: 可绘制对象
            opacity: 目标不透明度（0.0-1.0）
            duration: 动画持续时间（秒）
            easing: 缓动类型
            delay: 延迟开始时间（秒）
            
        Returns:
            PropertyAnimation: 属性动画对象
        """
        return PropertyAnimation(drawable, "opacity", drawable.opacity, opacity,
                                 duration, easing, False, delay)
    
    @staticmethod
    def fade_in(drawable: Drawable, duration: float = 0.5,
               easing: EasingType = EasingType.EASE_OUT, delay: float = 0.0) -> PropertyAnimation:
        """淡入（从透明到不透明）
        
        Args:
            drawable: 可绘制对象
            duration: 动画持续时间（秒）
            easing: 缓动类型
            delay: 延迟开始时间（秒）
            
        Returns:
            PropertyAnimation: 属性动画对象
        """
        drawable.opacity = 0.0
        drawable.set_visible(True)
        return DrawableAnimator.fade_to(drawable, 1.0, duration, easing, delay)
    
    @staticmethod
    def fade_out(drawable: Drawable, duration: float = 0.5,
                easing: EasingType = EasingType.EASE_OUT, delay: float = 0.0,
                hide_when_done: bool = True) -> PropertyAnimation:
        """淡出（从不透明到透明）
        
        Args:
            drawable: 可绘制对象
            duration: 动画持续时间（秒）
            easing: 缓动类型
            delay: 延迟开始时间（秒）
            hide_when_done: 动画完成后是否隐藏对象
            
        Returns:
            PropertyAnimation: 属性动画对象
        """
        anim = DrawableAnimator.fade_to(drawable, 0.0, duration, easing, delay)
        
        if hide_when_done:
            def on_complete():
                drawable.set_visible(False)
                
            anim.set_completion_callback(on_complete)
            
        return anim

class AnimationManager:
    """动画管理器，管理和更新所有动画"""
    
    def __init__(self):
        """初始化动画管理器"""
        self.animations: List[Animator] = []
        self.paused = False
    
    def add(self, animation: Animator) -> None:
        """添加动画
        
        Args:
            animation: 动画对象
        """
        if animation not in self.animations:
            self.animations.append(animation)
    
    def remove(self, animation: Animator) -> bool:
        """移除动画
        
        Args:
            animation: 动画对象
            
        Returns:
            bool: 是否成功移除
        """
        if animation in self.animations:
            self.animations.remove(animation)
            return True
        return False
    
    def clear(self) -> None:
        """清空所有动画"""
        self.animations.clear()
    
    def update(self, dt: float) -> None:
        """更新所有动画
        
        Args:
            dt: 时间增量（秒）
        """
        if self.paused:
            return
            
        # 创建副本，因为动画可能在更新过程中被移除
        animations = self.animations.copy()
        
        for animation in animations:
            animation.update(dt)
            
            # 如果动画已完成且不循环，移除它
            if animation.is_completed() and not animation.loop:
                self.animations.remove(animation)
    
    def pause(self) -> None:
        """暂停所有动画"""
        self.paused = True
        for animation in self.animations:
            animation.pause()
    
    def resume(self) -> None:
        """恢复所有动画"""
        self.paused = False
        for animation in self.animations:
            animation.resume()
    
    def stop_all(self) -> None:
        """停止所有动画"""
        for animation in self.animations:
            animation.stop()
        self.animations.clear()
    
    def count(self) -> int:
        """获取动画数量
        
        Returns:
            int: 动画数量
        """
        return len(self.animations)

class FrameAnimation(Animator):
    """帧序列动画类，用于播放一系列图像帧。"""
    
    def __init__(self, frames: List[QImage], fps: float = 12.0, loop: bool = True,
                 auto_start: bool = True):
        """初始化帧序列动画

        Args:
            frames (List[QImage]): 包含动画帧 (QImage 对象) 的列表。
            fps (float, optional): 动画的播放帧率 (每秒帧数). Defaults to 12.0.
            loop (bool, optional): 是否循环播放. Defaults to True.
            auto_start (bool, optional): 是否自动开始播放. Defaults to True.
        """
        if not frames:
            raise ValueError("帧列表不能为空")
            
        self.frames = frames
        self.frame_count = len(frames)
        self.fps = max(0.1, fps) # 保证fps大于0
        self.frame_duration = 1.0 / self.fps
        self.current_frame_index = 0
        
        # 总持续时间 = 帧数 * 每帧持续时间
        total_duration = self.frame_count * self.frame_duration
        
        # 调用父类初始化，但不设置延迟 (delay=0.0)
        super().__init__(duration=total_duration, loop=loop, delay=0.0, auto_start=auto_start)
        
        # 内部计时器，用于帧切换
        self._frame_timer = 0.0

    def _update_animation(self, dt: float) -> None:
        """更新动画逻辑，计算当前帧索引。"""
        # FrameAnimation 不需要缓动，它只按固定速率切换帧
        # 父类的 elapsed_time 已经处理了播放/暂停/循环
        
        # 使用 get_progress 获取考虑了循环和延迟的标准化时间
        # 注意：Animator 的 get_progress() 在循环时会重置，我们需要自己计时来确定帧
        # 暂时不依赖 Animator 的进度，而是独立计算帧索引
        
        self._frame_timer += dt
        
        # 计算应该前进多少帧
        frames_to_advance = math.floor(self._frame_timer / self.frame_duration)
        
        if frames_to_advance > 0:
            self._frame_timer = self._frame_timer % self.frame_duration # 保留余下的时间
            
            new_index = self.current_frame_index + frames_to_advance
            
            if self.loop:
                self.current_frame_index = new_index % self.frame_count
            else:
                self.current_frame_index = min(new_index, self.frame_count - 1)
                # 如果到达最后一帧且不循环，状态会在父类 update 中被设为 COMPLETED

    def get_current_frame(self) -> QImage:
        """获取当前应显示的 QImage 帧。"""
        # 添加边界检查以防万一
        if 0 <= self.current_frame_index < self.frame_count:
            return self.frames[self.current_frame_index]
        else:
            # 如果索引无效（理论上不应发生），返回第一帧或引发错误
            # logging.warning(f"FrameAnimation: 无效的帧索引 {self.current_frame_index}, 返回第一帧")
            return self.frames[0] 

    def reset(self) -> None:
        """重置动画到第一帧并停止。"""
        self.stop()
        self.current_frame_index = 0
        self._frame_timer = 0.0
        # 父类的 elapsed_time 已经在 stop() 中重置