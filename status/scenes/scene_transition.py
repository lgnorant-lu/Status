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
----
"""

from abc import ABC, abstractmethod
from enum import Enum
from typing import Tuple, Any, Optional, Dict, Callable, Type

from status.renderer.renderer_base import RendererBase
from status.renderer.animation import EasingType
from status.renderer.transition import TransitionManager, Transition, FadeTransition as FadeEffect
from status.renderer.transition import SlideTransition as SlideEffect
from status.renderer.transition import ScaleTransition, FlipTransition

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
        
        # 应用缓动函数
        from status.renderer.animation import Animator
        self.progress = Animator._apply_easing(None, raw_progress, self.easing)
        
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
        x_offset, y_offset = 0, 0
        if self.direction == "left":
            x_offset = width * (1.0 - self.progress)
        elif self.direction == "right":
            x_offset = -width * (1.0 - self.progress)
        elif self.direction == "up":
            y_offset = height * (1.0 - self.progress)
        elif self.direction == "down":
            y_offset = -height * (1.0 - self.progress)
        
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
                    renderer.translate(-width * self.progress, 0)
                elif self.direction == "right":
                    renderer.translate(width * self.progress, 0)
                elif self.direction == "up":
                    renderer.translate(0, -height * self.progress)
                elif self.direction == "down":
                    renderer.translate(0, height * self.progress)
                
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
    
    def __init__(self, pattern_path: str = None, duration: float = 0.5, 
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
    
    def __init__(self, effect_type: str, duration: float = 0.5, easing: str = 'ease_in_out_cubic', **effect_kwargs):
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
        self.effect.start()
    
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
        self.effect.update(delta_time)
        
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
                
                # 根据进度渲染
                original_opacity = renderer.get_opacity()
                renderer.set_opacity(self.effect.current_alpha)
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
                
                # 根据进度渲染
                original_opacity = renderer.get_opacity()
                renderer.set_opacity(1.0 - self.effect.current_alpha)
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
        
        # 使用SlideEffect渲染
        self.effect.draw(renderer, current_scene_surface, next_scene_surface, 0, 0, width, height)
    
    def _render_scale_transition(self, renderer: RendererBase, current_scene: Any, next_scene: Any) -> None:
        """渲染缩放效果"""
        width, height = renderer.get_viewport_size()
        
        # 根据进入/退出状态决定渲染行为
        if self.state == TransitionState.ENTERING:
            # 先渲染当前场景
            if current_scene:
                current_scene.render(renderer)
            
            # 使用缩放效果渲染下一场景
            if next_scene:
                # 先创建目标场景的内容
                next_scene_surface = renderer.create_surface()
                renderer.set_target(next_scene_surface)
                next_scene.render(renderer)
                renderer.reset_target()
                
                # 使用缩放效果渲染
                self.effect.draw(renderer, next_scene_surface, 0, 0, width, height)
        
        elif self.state == TransitionState.LEAVING:
            # 先创建两个场景的内容
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
                
                # 先渲染下一场景
                renderer.draw_surface(next_scene_surface, 0, 0)
            
            # 使用缩放效果渲染当前场景
            if current_scene_surface:
                # 反转缩放方向，直接创建一个新的ScaleTransition而不使用TransitionManager
                from status.renderer.transition import ScaleTransition
                inverted_effect = ScaleTransition(
                    from_scale=1.0,
                    to_scale=0.0,
                    duration=self.duration,
                    easing=self.transition_easing,
                    auto_start=False
                )
                inverted_effect.progress = self.effect.progress
                inverted_effect.current_scale = 1.0 - self.effect.current_scale
                
                # 使用反转效果渲染
                inverted_effect.draw(renderer, current_scene_surface, 0, 0, width, height)
    
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
        
        # 使用FlipEffect渲染
        self.effect.draw(renderer, current_scene_surface, next_scene_surface, 0, 0, width, height)

class TransitionManager:
    """转场管理器，负责管理和提供转场效果"""
    
    # 单例模式
    _instance = None
    
    @classmethod
    def get_instance(cls):
        """获取单例实例"""
        if cls._instance is None:
            cls._instance = TransitionManager()
        return cls._instance
    
    def __init__(self):
        """初始化转场管理器"""
        if TransitionManager._instance is not None:
            raise RuntimeError("TransitionManager is a singleton, use get_instance() instead")
        
        # 注册默认转场效果
        self.transitions = {
            "fade": FadeTransition,
            "slide_left": lambda duration=0.5, easing=EasingType.EASE_IN_OUT: 
                SlideTransition("left", duration, easing),
            "slide_right": lambda duration=0.5, easing=EasingType.EASE_IN_OUT: 
                SlideTransition("right", duration, easing),
            "slide_up": lambda duration=0.5, easing=EasingType.EASE_IN_OUT: 
                SlideTransition("up", duration, easing),
            "slide_down": lambda duration=0.5, easing=EasingType.EASE_IN_OUT: 
                SlideTransition("down", duration, easing),
            "zoom_in": lambda duration=0.5, easing=EasingType.EASE_IN_OUT: 
                ZoomTransition(True, duration, easing),
            "zoom_out": lambda duration=0.5, easing=EasingType.EASE_IN_OUT: 
                ZoomTransition(False, duration, easing),
            "dissolve": DissolveTransition,
        }
        
        # 默认转场效果
        self.default_transition = "fade"
        
    def register_transition(self, name: str, transition_factory) -> None:
        """注册新的转场效果
        
        Args:
            name: 转场效果名称
            transition_factory: 转场效果工厂函数或类
        """
        self.transitions[name] = transition_factory
        
    def get_transition(self, name: str = None, **kwargs) -> SceneTransition:
        """获取指定的转场效果
        
        Args:
            name: 转场效果名称
            **kwargs: 传递给转场效果构造函数的参数
            
        Returns:
            SceneTransition: 转场效果实例
        """
        if name is None:
            name = self.default_transition
            
        if name not in self.transitions:
            raise ValueError(f"Unknown transition effect: {name}")
            
        # 获取转场效果工厂
        factory = self.transitions[name]
        
        # 创建转场效果实例
        if callable(factory):
            return factory(**kwargs)
        else:
            return factory
    
    def set_default_transition(self, name: str) -> None:
        """设置默认转场效果
        
        Args:
            name: 转场效果名称
        """
        if name not in self.transitions:
            raise ValueError(f"Unknown transition effect: {name}")
            
        self.default_transition = name 
    
    # 添加别名方法以兼容测试
    def create_transition(self, name: str = None, **kwargs) -> SceneTransition:
        """创建指定的转场效果（get_transition方法的别名）
        
        Args:
            name: 转场效果名称
            **kwargs: 传递给转场效果构造函数的参数
            
        Returns:
            SceneTransition: 转场效果实例
        """
        return self.get_transition(name, **kwargs)
        
    def create_default_transition(self, **kwargs) -> SceneTransition:
        """创建默认转场效果
        
        Args:
            **kwargs: 传递给转场效果构造函数的参数
            
        Returns:
            SceneTransition: 默认转场效果实例
        """
        return self.get_transition(None, **kwargs)
    
    def register_effect_transition(self, name: str, effect_type: str, **default_kwargs) -> None:
        """
        注册一个基于新过渡效果系统的转场效果
        
        Args:
            name: 转场效果名称
            effect_type: 过渡效果类型，如'fade', 'slide', 'scale', 'flip'
            **default_kwargs: 默认参数
        """
        def transition_factory(**kwargs):
            merged_kwargs = {**default_kwargs, **kwargs}
            return TransitionEffectBridge(effect_type, **merged_kwargs)
        
        self.register_transition(name, transition_factory)
    
    def register_default_transitions(self) -> None:
        """注册默认的转场效果"""
        # 原有的转场效果
        self.register_transition("fade", lambda **kwargs: FadeTransition(**kwargs))
        self.register_transition("slide", lambda **kwargs: SlideTransition(**kwargs))
        self.register_transition("zoom", lambda **kwargs: ZoomTransition(**kwargs))
        self.register_transition("dissolve", lambda **kwargs: DissolveTransition(**kwargs))
        
        # 导入FlipTransition常量
        from status.renderer.transition import FlipTransition
        
        # 新的基于过渡效果系统的转场效果
        self.register_effect_transition("fade2", "fade", duration=0.5, easing="ease_in_out_cubic")
        self.register_effect_transition("slide2", "slide", duration=0.5, easing="ease_out_cubic", direction=SlideEffect.DIRECTION_LEFT)
        self.register_effect_transition("scale", "scale", duration=0.5, easing="ease_out_cubic", from_scale=0.0, to_scale=1.0)
        self.register_effect_transition("flip_h", "flip", duration=0.8, easing="ease_in_out_cubic", direction=FlipTransition.DIRECTION_HORIZONTAL)
        self.register_effect_transition("flip_v", "flip", duration=0.8, easing="ease_in_out_cubic", direction=FlipTransition.DIRECTION_VERTICAL)
        
        # 设置默认转场效果
        self.set_default_transition("fade")