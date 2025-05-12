"""
---------------------------------------------------------------
File name:                  scene_transition.py
Author:                     Ignorant-lu
Date created:               2025/04/03
Description:                场景转场模块，提供场景切换时的视觉效果
----------------------------------------------------------------

Changed history:            
                            2025/04/03: 初始创建;
                            2025/04/03: 添加对过渡效果系统的支持;
                            2025/05/18: 修复类型错误，解决命名冲突问题;
----
"""

from abc import ABC, abstractmethod
from enum import Enum
from typing import Tuple, Any, Optional, Dict, Callable, Type, cast, Union
import math

from status.renderer.renderer_base import RendererBase
from status.renderer.animation import EasingType, Animator
# 重命名导入的类以避免命名冲突
from status.renderer.transition import TransitionManager as RTTransitionManager 
from status.renderer.transition import Transition, FadeTransition as FadeEffect
from status.renderer.transition import SlideTransition as SlideEffect
from status.renderer.transition import ScaleTransition, FlipTransition

# 定义Transition效果的联合类型，用于解决类型兼容性问题
TransitionEffectType = Union[FadeEffect, SlideEffect, ScaleTransition, FlipTransition]

class TransitionState(Enum):
    """转场状态枚举"""
    IDLE = 0      # 空闲
    ENTERING = 1  # 进入中
    LEAVING = 2   # 离开中
    COMPLETED = 3 # 完成

class SceneTransition(ABC):
    """场景转场基类"""
    
    def __init__(self, duration: float = 0.5, easing: EasingType = EasingType.EASE_IN_OUT):
        """初始化转场效果
        
        Args:
            duration: 转场持续时间（秒）
            easing: 缓动类型
        """
        self.duration = duration
        self.easing = easing
        self.state = TransitionState.IDLE
        self.elapsed_time = 0.0
        self.progress = 0.0  # 0.0到1.0之间的进度值
        
    def start_transition(self, is_entering: bool) -> None:
        """开始转场动画
        
        Args:
            is_entering: 是否为进入动画
        """
        self.state = TransitionState.ENTERING if is_entering else TransitionState.LEAVING
        self.elapsed_time = 0.0
        self.progress = 0.0
        
    def update(self, delta_time: float) -> bool:
        """更新转场动画
        
        Args:
            delta_time: 时间增量（秒）
            
        Returns:
            bool: 转场动画是否完成
        """
        if self.state == TransitionState.IDLE or self.state == TransitionState.COMPLETED:
            return True
            
        self.elapsed_time += delta_time
        
        # 计算进度
        raw_progress = min(self.elapsed_time / self.duration, 1.0)
        
        # 应用缓动函数 - 修复None参数问题
        animator = Animator(duration=self.duration)  # 创建实例时添加必要的duration参数
        self.progress = animator._apply_easing(raw_progress, self.easing)
        
        # 检查完成状态
        if raw_progress >= 1.0:
            self.state = TransitionState.COMPLETED
            self.progress = 1.0
            return True
            
        return False
        
    def render(self, renderer: RendererBase, current_scene: Any, next_scene: Any) -> None:
        """渲染转场效果
        
        Args:
            renderer: 渲染器
            current_scene: 当前场景
            next_scene: 下一个场景
        """
        if self.state == TransitionState.IDLE:
            # 直接渲染当前场景
            if current_scene:
                current_scene.render(renderer)
            return
        
        # 渲染转场效果
        self._render_transition(renderer, current_scene, next_scene)
    
    @abstractmethod
    def _render_transition(self, renderer: RendererBase, current_scene: Any, next_scene: Any) -> None:
        """渲染转场效果的具体实现
        
        Args:
            renderer: 渲染器
            current_scene: 当前场景
            next_scene: 下一个场景
        """
        pass

class FadeTransition(SceneTransition):
    """淡入淡出转场效果"""
    
    def _render_transition(self, renderer: RendererBase, current_scene: Any, next_scene: Any) -> None:
        """渲染淡入淡出效果
        
        Args:
            renderer: 渲染器
            current_scene: 当前场景
            next_scene: 下一个场景
        """
        if self.state == TransitionState.ENTERING:
            # 进入动画：先渲染当前场景，再渲染下一场景（逐渐显示）
            if current_scene:
                current_scene.render(renderer)
            
            if next_scene:
                # 保存当前透明度
                original_opacity = renderer.get_opacity()
                
                # 设置新的透明度
                renderer.set_opacity(self.progress)
                
                # 渲染下一个场景
                next_scene.render(renderer)
                
                # 恢复透明度
                renderer.set_opacity(original_opacity)
                
        elif self.state == TransitionState.LEAVING:
            # 离开动画：先渲染下一场景，再渲染当前场景（逐渐消失）
            if next_scene:
                next_scene.render(renderer)
            
            if current_scene:
                # 保存当前透明度
                original_opacity = renderer.get_opacity()
                
                # 设置新的透明度（反向）
                renderer.set_opacity(1.0 - self.progress)
                
                # 渲染当前场景
                current_scene.render(renderer)
                
                # 恢复透明度
                renderer.set_opacity(original_opacity)

class SlideTransition(SceneTransition):
    """滑动转场效果"""
    
    def __init__(self, direction: str = "left", duration: float = 0.5, 
                easing: EasingType = EasingType.EASE_IN_OUT):
        """初始化滑动转场效果
        
        Args:
            direction: 滑动方向，可选值："left", "right", "up", "down"
            duration: 转场持续时间（秒）
            easing: 缓动类型
        """
        super().__init__(duration, easing)
        self.direction = direction
    
    def _render_transition(self, renderer: RendererBase, current_scene: Any, next_scene: Any) -> None:
        """渲染滑动效果
        
        Args:
            renderer: 渲染器
            current_scene: 当前场景
            next_scene: 下一个场景
        """
        # 获取视口大小
        viewport_size = renderer.get_viewport_size()
        width, height = viewport_size
        
        # 计算滑动位移
        x_offset, y_offset = 0.0, 0.0  # 使用浮点数
        if self.direction == "left":
            x_offset = float(width) * (1.0 - self.progress)
        elif self.direction == "right":
            x_offset = -float(width) * (1.0 - self.progress)
        elif self.direction == "up":
            y_offset = float(height) * (1.0 - self.progress)
        elif self.direction == "down":
            y_offset = -float(height) * (1.0 - self.progress)
        
        # 保存当前变换
        renderer.save_state()
        
        if self.state == TransitionState.ENTERING:
            # 先渲染当前场景
            if current_scene:
                current_scene.render(renderer)
            
            # 渲染下一场景，带位移
            if next_scene:
                renderer.translate(x_offset, y_offset)
                next_scene.render(renderer)
        
        elif self.state == TransitionState.LEAVING:
            # 先渲染下一场景
            if next_scene:
                next_scene.render(renderer)
            
            # 渲染当前场景，带位移（反向）
            if current_scene:
                if self.direction == "left":
                    renderer.translate(-float(width) * self.progress, 0.0)
                elif self.direction == "right":
                    renderer.translate(float(width) * self.progress, 0.0)
                elif self.direction == "up":
                    renderer.translate(0.0, -float(height) * self.progress)
                elif self.direction == "down":
                    renderer.translate(0.0, float(height) * self.progress)
                
                current_scene.render(renderer)
        
        # 恢复变换
        renderer.restore_state()

class ZoomTransition(SceneTransition):
    """缩放转场效果"""
    
    def __init__(self, zoom_in: bool = True, duration: float = 0.5, 
                easing: EasingType = EasingType.EASE_IN_OUT):
        """初始化缩放转场效果
        
        Args:
            zoom_in: 是否为缩小到放大效果（True）或放大到缩小效果（False）
            duration: 转场持续时间（秒）
            easing: 缓动类型
        """
        super().__init__(duration, easing)
        self.zoom_in = zoom_in
    
    def _render_transition(self, renderer: RendererBase, current_scene: Any, next_scene: Any) -> None:
        """渲染缩放效果
        
        Args:
            renderer: 渲染器
            current_scene: 当前场景
            next_scene: 下一个场景
        """
        # 获取视口中心
        viewport_size = renderer.get_viewport_size()
        center_x, center_y = viewport_size[0] / 2, viewport_size[1] / 2
        
        # 保存当前变换
        renderer.save_state()
        
        if self.state == TransitionState.ENTERING:
            # 先渲染当前场景
            if current_scene:
                current_scene.render(renderer)
            
            # 渲染下一场景，带缩放
            if next_scene:
                scale = self.progress if self.zoom_in else 2.0 - self.progress
                
                # 设置变换中心点
                renderer.translate(center_x, center_y)
                renderer.scale(scale, scale)
                renderer.translate(-center_x, -center_y)
                
                # 设置透明度
                original_opacity = renderer.get_opacity()
                renderer.set_opacity(self.progress)
                
                next_scene.render(renderer)
                
                # 恢复透明度
                renderer.set_opacity(original_opacity)
        
        elif self.state == TransitionState.LEAVING:
            # 先渲染下一场景
            if next_scene:
                next_scene.render(renderer)
            
            # 渲染当前场景，带缩放
            if current_scene:
                scale = 1.0 + self.progress if self.zoom_in else 1.0 - 0.5 * self.progress
                
                # 设置变换中心点
                renderer.translate(center_x, center_y)
                renderer.scale(scale, scale)
                renderer.translate(-center_x, -center_y)
                
                # 设置透明度
                original_opacity = renderer.get_opacity()
                renderer.set_opacity(1.0 - self.progress)
                
                current_scene.render(renderer)
                
                # 恢复透明度
                renderer.set_opacity(original_opacity)
        
        # 恢复变换
        renderer.restore_state()

class DissolveTransition(SceneTransition):
    """溶解转场效果"""
    
    def __init__(self, pattern_path: Optional[str] = None, duration: float = 0.5, 
                easing: EasingType = EasingType.EASE_IN_OUT):
        """初始化溶解转场效果
        
        Args:
            pattern_path: 溶解纹理路径（可选）
            duration: 转场持续时间（秒）
            easing: 缓动类型
        """
        super().__init__(duration, easing)
        self.pattern_path = pattern_path
        self.pattern = None
        
    def _render_transition(self, renderer: RendererBase, current_scene: Any, next_scene: Any) -> None:
        """渲染溶解效果
        
        Args:
            renderer: 渲染器
            current_scene: 当前场景
            next_scene: 下一个场景
        """
        # 延迟加载溶解纹理
        if self.pattern_path and not self.pattern:
            from status.resources.asset_manager import AssetManager
            asset_manager = AssetManager.get_instance()
            self.pattern = asset_manager.load_image(self.pattern_path)
        
        # 渲染两个场景到离屏缓冲区
        viewport_size = renderer.get_viewport_size()
        
        if self.state == TransitionState.ENTERING:
            # 先渲染当前场景
            if current_scene:
                current_scene.render(renderer)
            
            # 使用溶解效果渲染下一场景
            if next_scene:
                if self.pattern:
                    # 使用纹理进行溶解（如果有纹理）
                    renderer.set_dissolve_effect(self.pattern, self.progress)
                    next_scene.render(renderer)
                    renderer.clear_effects()
                else:
                    # 简单透明度溶解（无纹理时）
                    original_opacity = renderer.get_opacity()
                    renderer.set_opacity(self.progress)
                    next_scene.render(renderer)
                    renderer.set_opacity(original_opacity)
        
        elif self.state == TransitionState.LEAVING:
            # 先渲染下一场景
            if next_scene:
                next_scene.render(renderer)
            
            # 使用溶解效果渲染当前场景
            if current_scene:
                if self.pattern:
                    # 使用纹理进行溶解
                    renderer.set_dissolve_effect(self.pattern, 1.0 - self.progress)
                    current_scene.render(renderer)
                    renderer.clear_effects()
                else:
                    # 简单透明度溶解
                    original_opacity = renderer.get_opacity()
                    renderer.set_opacity(1.0 - self.progress)
                    current_scene.render(renderer)
                    renderer.set_opacity(original_opacity)

class TransitionEffectBridge(SceneTransition):
    """过渡效果桥接类，用于将新的过渡效果系统与场景转场系统集成"""
    
    def __init__(self, effect_type: str, duration: float = 0.5, easing: str = 'ease_in_out_cubic', **effect_kwargs: Any) -> None:
        """
        初始化过渡效果桥接
        
        Args:
            effect_type: 过渡效果类型，如'fade', 'slide', 'scale', 'flip'
            duration: 过渡持续时间（秒）
            easing: 缓动类型
            **effect_kwargs: 传递给具体过渡效果的参数
        """
        # 调用父类初始化，但不使用父类的缓动类型，而是使用新系统的缓动函数
        super().__init__(duration, EasingType.LINEAR)  # 使用LINEAR作为占位符
        
        # 保存新的缓动类型
        self.transition_easing = easing
        
        # 过滤掉不支持的参数
        filtered_kwargs = {k: v for k, v in effect_kwargs.items() 
                          if k not in ['auto_start', 'auto_reverse', 'on_complete']}
        
        # 添加必要的参数
        filtered_kwargs['duration'] = duration
        filtered_kwargs['easing'] = easing
        filtered_kwargs['auto_start'] = False  # 始终使用False，由桥接类控制
        
        # 直接创建对应的过渡效果，而不是通过TransitionManager
        from status.renderer.transition import (
            FadeTransition as FadeEffect,
            SlideTransition as SlideEffect,
            ScaleTransition,
            FlipTransition
        )
        
        # 定义effect属性，使用Union类型表示可能的类型
        self.effect: TransitionEffectType
        
        # 根据效果类型创建相应的过渡效果实例
        if effect_type == 'fade':
            self.effect = FadeEffect(**filtered_kwargs)
        elif effect_type == 'slide':
            self.effect = SlideEffect(**filtered_kwargs)
        elif effect_type == 'scale':
            self.effect = ScaleTransition(**filtered_kwargs)
        elif effect_type == 'flip':
            # 确保direction参数的值正确设置
            # 对于flip过渡效果，direction参数需要是DIRECTION_HORIZONTAL或DIRECTION_VERTICAL枚举值
            if 'direction' in filtered_kwargs:
                # 如果direction已经是正确的枚举值，则直接使用
                if filtered_kwargs['direction'] in [FlipTransition.DIRECTION_HORIZONTAL, FlipTransition.DIRECTION_VERTICAL]:
                    pass  # 保持原样
                # 否则尝试将字符串转换为枚举值
                elif filtered_kwargs['direction'] in ['horizontal', 'h']:
                    filtered_kwargs['direction'] = FlipTransition.DIRECTION_HORIZONTAL
                elif filtered_kwargs['direction'] in ['vertical', 'v']:
                    filtered_kwargs['direction'] = FlipTransition.DIRECTION_VERTICAL
            
            self.effect = FlipTransition(**filtered_kwargs)
        else:
            raise ValueError(f"未知的过渡效果类型: {effect_type}")
        
        # 场景渲染目标
        self.current_scene_surface = None
        self.next_scene_surface = None
    
    def start_transition(self, is_entering: bool) -> None:
        """
        开始转场动画
        
        Args:
            is_entering: 是否为进入动画
        """
        super().start_transition(is_entering)
        
        # 启动过渡效果
        # 确保方法存在并且是可调用的
        if hasattr(self.effect, 'start') and callable(getattr(self.effect, 'start')):
            # 使用类型忽略注释，因为我们已经确保方法存在并且可调用
            start_method = getattr(self.effect, 'start')
            start_method()  # type: ignore
    
    def update(self, delta_time: float) -> bool:
        """
        更新转场动画
        
        Args:
            delta_time: 时间增量（秒）
            
        Returns:
            bool: 转场动画是否完成
        """
        # 更新父类状态
        result = super().update(delta_time)
        
        # 更新过渡效果
        if hasattr(self.effect, 'update') and callable(getattr(self.effect, 'update')):
            # 使用类型忽略注释，因为我们已经确保方法存在并且可调用
            update_method = getattr(self.effect, 'update')
            update_method(delta_time)  # type: ignore
        
        return result
    
    def _render_transition(self, renderer: RendererBase, current_scene: Any, next_scene: Any) -> None:
        """
        渲染转场效果
        
        Args:
            renderer: 渲染器
            current_scene: 当前场景
            next_scene: 下一个场景
        """
        # 获取视口大小
        width, height = renderer.get_viewport_size()
        
        # 使用过渡效果系统进行渲染
        if isinstance(self.effect, FadeEffect):
            self._render_fade_transition(renderer, current_scene, next_scene)
        elif isinstance(self.effect, SlideEffect):
            self._render_slide_transition(renderer, current_scene, next_scene)
        elif isinstance(self.effect, ScaleTransition):
            self._render_scale_transition(renderer, current_scene, next_scene)
        elif isinstance(self.effect, FlipTransition):
            self._render_flip_transition(renderer, current_scene, next_scene)
        else:
            # 默认行为：先渲染当前场景，再渲染下一场景
            if current_scene:
                current_scene.render(renderer)
            if next_scene:
                next_scene.render(renderer)
    
    def _render_fade_transition(self, renderer: RendererBase, current_scene: Any, next_scene: Any) -> None:
        """渲染淡入淡出效果"""
        if self.state == TransitionState.ENTERING:
            # 先渲染当前场景
            if current_scene:
                current_scene.render(renderer)
            
            # 使用淡入淡出效果渲染黑色遮罩
            if next_scene:
                # 先创建目标场景的内容
                next_scene_surface = renderer.create_surface()
                renderer.set_target(next_scene_surface)
                next_scene.render(renderer)
                renderer.reset_target()
                
                # 根据进度渲染 - 添加类型检查
                original_opacity = renderer.get_opacity()
                # 使用安全的属性访问方式
                opacity = getattr(self.effect, 'current_alpha', self.progress)
                renderer.set_opacity(opacity)
                renderer.draw_surface(next_scene_surface, 0, 0)
                renderer.set_opacity(original_opacity)
        
        elif self.state == TransitionState.LEAVING:
            # 先渲染下一场景
            if next_scene:
                next_scene.render(renderer)
            
            # 使用淡入淡出效果渲染当前场景
            if current_scene:
                # 先创建当前场景的内容
                current_scene_surface = renderer.create_surface()
                renderer.set_target(current_scene_surface)
                current_scene.render(renderer)
                renderer.reset_target()
                
                # 根据进度渲染 - 添加类型检查
                original_opacity = renderer.get_opacity()
                # 使用安全的属性访问方式
                opacity = getattr(self.effect, 'current_alpha', self.progress)
                renderer.set_opacity(1.0 - opacity)
                renderer.draw_surface(current_scene_surface, 0, 0)
                renderer.set_opacity(original_opacity)
    
    def _render_slide_transition(self, renderer: RendererBase, current_scene: Any, next_scene: Any) -> None:
        """渲染滑动效果"""
        width, height = renderer.get_viewport_size()
        
        # 创建场景表面
        if current_scene:
            current_scene_surface = renderer.create_surface()
            renderer.set_target(current_scene_surface)
            current_scene.render(renderer)
            renderer.reset_target()
        else:
            current_scene_surface = None
            
        if next_scene:
            next_scene_surface = renderer.create_surface()
            renderer.set_target(next_scene_surface)
            next_scene.render(renderer)
            renderer.reset_target()
        else:
            next_scene_surface = None
        
        # 使用SlideEffect渲染 - 修复参数调用
        # 为保证代码与不同签名的draw方法兼容，我们使用自定义渲染逻辑
        try:
            # 尝试使用简化的渲染逻辑
            # 首先渲染当前场景（如果有）
            if current_scene_surface:
                renderer.draw_surface(current_scene_surface, 0, 0)
                
            # 然后渲染下一个场景（如果有）
            if next_scene_surface:
                # 基于当前进度计算偏移量
                offset = self._calculate_slide_offset(width, height)
                renderer.draw_surface(next_scene_surface, offset[0], offset[1])
        except Exception as e:
            # 降级处理：出错时简单渲染
            if current_scene_surface:
                renderer.draw_surface(current_scene_surface, 0, 0)
            if next_scene_surface:
                renderer.draw_surface(next_scene_surface, 0, 0)
                
    def _calculate_slide_offset(self, width: int, height: int) -> Tuple[int, int]:
        """计算滑动偏移量
        
        Args:
            width: 视口宽度
            height: 视口高度
            
        Returns:
            滑动偏移量元组(x, y)
        """
        direction = getattr(self.effect, 'direction', getattr(self, 'direction', 'left'))
        progress = getattr(self.effect, 'current_progress', self.progress)
        
        # 确保数值在0-1之间
        progress = max(0.0, min(1.0, progress))
        
        # 根据方向计算偏移量
        if direction in ['left', 'right']:
            offset_x = width * (1.0 - progress) if direction == 'left' else -width * (1.0 - progress)
            return (int(offset_x), 0)
        else:  # 上/下
            offset_y = height * (1.0 - progress) if direction == 'up' else -height * (1.0 - progress)
            return (0, int(offset_y))
            
    def _render_scale_transition(self, renderer: RendererBase, current_scene: Any, next_scene: Any) -> None:
        """渲染缩放效果"""
        width, height = renderer.get_viewport_size()
        
        # 创建场景表面
        if current_scene:
            current_scene_surface = renderer.create_surface()
            renderer.set_target(current_scene_surface)
            current_scene.render(renderer)
            renderer.reset_target()
        else:
            current_scene_surface = None
            
        if next_scene:
            next_scene_surface = renderer.create_surface()
            renderer.set_target(next_scene_surface)
            next_scene.render(renderer)
            renderer.reset_target()
        else:
            next_scene_surface = None
        
        # 使用缩放效果渲染
        zoom_in = getattr(self.effect, 'zoom_in', getattr(self, 'zoom_in', True))
        progress = getattr(self.effect, 'current_progress', self.progress)
        
        # 确保数值在0-1之间
        progress = max(0.0, min(1.0, progress))
        
        if self.state == TransitionState.ENTERING:
            # 先渲染当前场景
            if current_scene_surface:
                renderer.draw_surface(current_scene_surface, 0, 0)
                
            # 使用缩放效果渲染下一个场景
            if next_scene_surface:
                # 计算缩放尺寸和位置
                if zoom_in:
                    # 从小到大
                    scale = progress
                    scaled_width = int(width * scale)
                    scaled_height = int(height * scale)
                    pos_x = int((width - scaled_width) / 2)
                    pos_y = int((height - scaled_height) / 2)
                else:
                    # 从大到小（反向缩放）
                    scale = 1.0 + (1.0 - progress)
                    scaled_width = int(width * scale)
                    scaled_height = int(height * scale)
                    pos_x = int((width - scaled_width) / 2)
                    pos_y = int((height - scaled_height) / 2)
                
                # 使用安全的属性访问方式
                original_opacity = renderer.get_opacity()
                renderer.set_opacity(progress)
                renderer.draw_surface_scaled(
                    next_scene_surface, 
                    pos_x, pos_y, 
                    scaled_width, scaled_height
                )
                renderer.set_opacity(original_opacity)
        
        elif self.state == TransitionState.LEAVING:
            # 先渲染下一场景
            if next_scene:
                next_scene.render(renderer)
            
            # 渲染当前场景，带缩放
            if current_scene_surface:
                scale = 1.0 + self.progress if zoom_in else 1.0 - 0.5 * self.progress
                
                # 设置变换中心点
                renderer.translate(width / 2, height / 2)
                renderer.scale(scale, scale)
                renderer.translate(-width / 2, -height / 2)
                
                # 设置透明度
                original_opacity = renderer.get_opacity()
                renderer.set_opacity(1.0 - self.progress)
                
                renderer.draw_surface(current_scene_surface, 0, 0)
                
                # 恢复变换
                renderer.restore_state()
    
    def _render_flip_transition(self, renderer: RendererBase, current_scene: Any, next_scene: Any) -> None:
        """渲染翻转效果"""
        width, height = renderer.get_viewport_size()
        
        # 创建场景表面
        if current_scene:
            current_scene_surface = renderer.create_surface()
            renderer.set_target(current_scene_surface)
            current_scene.render(renderer)
            renderer.reset_target()
        else:
            current_scene_surface = None
            
        if next_scene:
            next_scene_surface = renderer.create_surface()
            renderer.set_target(next_scene_surface)
            next_scene.render(renderer)
            renderer.reset_target()
        else:
            next_scene_surface = None
        
        # 简化的翻转渲染
        try:
            # 保存当前状态
            renderer.save_state()
            
            # 计算翻转角度
            angle = self.progress * 180.0  # 0 到 180 度
            
            if angle < 90:
                # 前半段翻转：当前场景逐渐消失
                if current_scene_surface:
                    # 设置缩放比例模拟透视效果
                    scale = math.cos(math.radians(angle))
                    
                    # 设置变换
                    center_x, center_y = width / 2, height / 2
                    renderer.translate(center_x, center_y)
                    renderer.scale(scale, 1.0)
                    renderer.translate(-center_x, -center_y)
                    
                    # 渲染
                    renderer.draw_surface(current_scene_surface, 0, 0)
            else:
                # 后半段翻转：下一场景逐渐出现
                if next_scene_surface:
                    # 设置缩放比例模拟透视效果
                    scale = math.cos(math.radians(180 - angle))
                    
                    # 设置变换
                    center_x, center_y = width / 2, height / 2
                    renderer.translate(center_x, center_y)
                    renderer.scale(scale, 1.0)
                    renderer.translate(-center_x, -center_y)
                    
                    # 渲染
                    renderer.draw_surface(next_scene_surface, 0, 0)
            
            # 恢复状态
            renderer.restore_state()
        except Exception as e:
            # 降级处理：出错时简单渲染
            if current_scene_surface:
                renderer.draw_surface(current_scene_surface, 0, 0)
            if next_scene_surface:
                renderer.draw_surface(next_scene_surface, 0, 0)

class TransitionManager:
    """转场管理器，负责管理和提供转场效果"""
    
    _instance = None
    
    @classmethod
    def get_instance(cls) -> 'TransitionManager':
        """获取转场管理器实例
        
        Returns:
            TransitionManager: 转场管理器实例
        """
        if cls._instance is None:
            cls._instance = TransitionManager()
        return cls._instance
    
    def __init__(self) -> None:
        """初始化转场管理器"""
        self.transitions: Dict[str, Callable[..., SceneTransition]] = {}
        self.default_transition = "fade"
        
        # 注册默认转场效果
        self.register_default_transitions()
    
    def register_transition(self, name: str, factory: Callable[..., SceneTransition]) -> None:
        """注册转场效果
        
        Args:
            name: 转场效果名称
            factory: 转场效果工厂函数，接受任意参数并返回SceneTransition实例
        """
        self.transitions[name] = factory
    
    def create_transition(self, name: str, **kwargs: Any) -> SceneTransition:
        """创建转场效果
        
        Args:
            name: 转场效果名称
            **kwargs: 传递给转场效果工厂函数的参数
            
        Returns:
            SceneTransition: 转场效果实例
            
        Raises:
            ValueError: 如果转场效果名称不存在
        """
        if name not in self.transitions:
            raise ValueError(f"未知的转场效果: {name}")
        
        # 调用工厂函数创建转场效果实例
        factory = self.transitions[name]
        return factory(**kwargs)
    
    def register_effect_transition(self, name: str, effect_type: str, **effect_params: Any) -> None:
        """注册基于过渡效果系统的转场效果
        
        Args:
            name: 转场效果名称
            effect_type: 过渡效果类型，如'fade', 'slide', 'scale', 'flip'
            **effect_params: 传递给过渡效果的参数
        """
        # 创建工厂函数
        def factory(**kwargs: Any) -> TransitionEffectBridge:
            # 合并参数
            params = effect_params.copy()
            params.update(kwargs)
            
            # 创建过渡效果
            return TransitionEffectBridge(effect_type, **params)
        
        # 注册工厂函数
        self.register_transition(name, factory)
    
    def set_default_transition(self, name: str) -> None:
        """设置默认转场效果
        
        Args:
            name: 默认转场效果名称
            
        Raises:
            ValueError: 如果转场效果名称不存在
        """
        if name not in self.transitions:
            raise ValueError(f"未知的转场效果: {name}")
        
        self.default_transition = name
    
    def get_default_transition(self, **kwargs: Any) -> SceneTransition:
        """获取默认转场效果
        
        Args:
            **kwargs: 传递给转场效果工厂函数的参数
            
        Returns:
            SceneTransition: 默认转场效果实例
        """
        return self.create_transition(self.default_transition, **kwargs)
    
    def register_default_transitions(self) -> None:
        """注册默认的转场效果"""
        # 原有的转场效果
        self.register_transition("fade", lambda **kwargs: FadeTransition(**kwargs))
        
        # 滑动效果，不同方向
        self.register_transition("slide", lambda **kwargs: SlideTransition(**kwargs))
        self.register_transition("slide_left", lambda **kwargs: SlideTransition(direction="left", **kwargs))
        self.register_transition("slide_right", lambda **kwargs: SlideTransition(direction="right", **kwargs))
        self.register_transition("slide_up", lambda **kwargs: SlideTransition(direction="up", **kwargs))
        self.register_transition("slide_down", lambda **kwargs: SlideTransition(direction="down", **kwargs))
        
        # 缩放效果
        self.register_transition("zoom", lambda **kwargs: ZoomTransition(**kwargs))
        self.register_transition("zoom_in", lambda **kwargs: ZoomTransition(zoom_in=True, **kwargs))
        self.register_transition("zoom_out", lambda **kwargs: ZoomTransition(zoom_in=False, **kwargs))
        
        # 溶解效果
        self.register_transition("dissolve", lambda **kwargs: DissolveTransition(**kwargs))
        
        # 导入FlipTransition常量
        from status.renderer.transition import FlipTransition
        
        # 新的基于过渡效果系统的转场效果 - 使用Union类型解决类型不兼容问题
        from typing import Any as AnyType, Union, cast
        
        # 使用Union类型来处理类型不兼容问题
        TransitionType = Union[FadeTransition, SlideTransition, ZoomTransition, DissolveTransition, TransitionEffectBridge]
        
        # 注册基于效果系统的过渡效果
        self.register_effect_transition("fade2", "fade", duration=0.5, easing="ease_in_out_cubic")
        self.register_effect_transition("slide2", "slide", duration=0.5, easing="ease_out_cubic", direction=SlideEffect.DIRECTION_LEFT)
        self.register_effect_transition("scale", "scale", duration=0.5, easing="ease_out_cubic", from_scale=0.0, to_scale=1.0)
        self.register_effect_transition("flip_h", "flip", duration=0.8, easing="ease_in_out_cubic", direction=FlipTransition.DIRECTION_HORIZONTAL)
        self.register_effect_transition("flip_v", "flip", duration=0.8, easing="ease_in_out_cubic", direction=FlipTransition.DIRECTION_VERTICAL)
        
        # 设置默认转场效果
        self.set_default_transition("fade")

    def _get_viewport_size(self, renderer: RendererBase) -> Tuple[int, int]:
        """获取视口大小
        
        Args:
            renderer: 渲染器
            
        Returns:
            Tuple[int, int]: 视口宽度和高度
        """
        viewport_size = renderer.get_viewport_size()
        # 确保返回整数
        width = int(viewport_size[0])
        height = int(viewport_size[1])
        return (width, height)