"""
---------------------------------------------------------------
File name:                  test_scene_transition.py
Author:                     Ignorant-lu
Date created:               2025/04/03
Description:                场景转场系统测试，包括与过渡效果系统的集成测试
----------------------------------------------------------------

Changed history:            
                            2025/04/03: 初始创建;
----
"""

import pytest
import unittest.mock as mock
from unittest.mock import MagicMock, patch

from status.scenes.scene_transition import (
    TransitionState,
    SceneTransition,
    TransitionEffectBridge,
    TransitionManager,
    FadeTransition,
    SlideTransition
)
from status.renderer.transition import (
    FadeTransition as FadeEffect,
    SlideTransition as SlideEffect,
    ScaleTransition,
    FlipTransition
)

class TestSceneTransition:
    """测试基础场景转场功能"""
    
    def test_transition_state(self):
        """测试转场状态枚举"""
        assert TransitionState.IDLE.name == "IDLE"
        assert TransitionState.ENTERING.name == "ENTERING"
        assert TransitionState.LEAVING.name == "LEAVING"
        assert TransitionState.COMPLETED.name == "COMPLETED"
    
    def test_transition_lifecycle(self):
        """测试基础转场生命周期"""
        # 创建一个具体的转场子类
        transition = FadeTransition(duration=0.5)
        
        # 初始状态
        assert transition.state == TransitionState.IDLE
        assert transition.progress == 0.0
        
        # 开始进入转场
        transition.start_transition(True)
        assert transition.state == TransitionState.ENTERING
        
        # 半程更新
        result = transition.update(0.25)
        assert transition.progress == 0.5
        assert not result  # 未完成
        
        # 完成进入
        result = transition.update(0.25)
        assert transition.progress == 1.0
        assert result  # 已完成
        assert transition.state == TransitionState.COMPLETED
        
        # 重置并开始离开转场
        transition.progress = 0.0
        transition.state = TransitionState.IDLE
        transition.start_transition(False)
        assert transition.state == TransitionState.LEAVING
        
        # 完成离开
        result = transition.update(0.5)
        assert transition.progress == 1.0
        assert result
        assert transition.state == TransitionState.COMPLETED

class TestTransitionEffectBridge:
    """测试过渡效果系统桥接类"""
    
    def test_bridge_initialization(self):
        """测试桥接类初始化"""
        # 创建一个桥接对象
        bridge = TransitionEffectBridge(
            effect_type="fade", 
            duration=0.8,
            easing="ease_in_out_cubic",
            from_alpha=0.0,
            to_alpha=1.0
        )
        
        # 验证初始化是否正确
        assert bridge.duration == 0.8
        assert bridge.transition_easing == "ease_in_out_cubic"
        assert bridge.state == TransitionState.IDLE
        assert isinstance(bridge.effect, FadeEffect)
    
    def test_bridge_lifecycle(self):
        """测试桥接类生命周期"""
        # 创建一个桥接对象
        bridge = TransitionEffectBridge(
            effect_type="fade", 
            duration=0.5
        )
        
        # 创建模拟对象跟踪效果调用
        bridge.effect = MagicMock()
        
        # 开始转场
        bridge.start_transition(True)
        bridge.effect.start.assert_called_once()
        assert bridge.state == TransitionState.ENTERING
        
        # 更新转场
        bridge.update(0.25)
        bridge.effect.update.assert_called_with(0.25)
    
    def test_fade_effect_bridge(self):
        """测试淡入淡出桥接效果"""
        # 创建一个模拟渲染器
        renderer = MagicMock()
        renderer.get_viewport_size.return_value = (800, 600)
        renderer.create_surface.return_value = "mock_surface"
        
        # 创建场景模拟对象
        current_scene = MagicMock()
        next_scene = MagicMock()
        
        # 创建一个桥接对象，使用实际的FadeEffect
        bridge = TransitionEffectBridge(
            effect_type="fade", 
            duration=0.5,
            from_alpha=0.0,
            to_alpha=1.0
        )
        
        # 启动转场
        bridge.start_transition(True)
        
        # 手动设置属性以模拟过渡进度
        bridge.effect.progress = 0.5
        bridge.effect.current_alpha = 0.5
        
        # 测试渲染
        bridge._render_fade_transition(renderer, current_scene, next_scene)
        
        # 验证场景渲染调用
        current_scene.render.assert_called_once_with(renderer)
        next_scene.render.assert_called_once_with(renderer)
        
        # 验证渲染器操作
        renderer.set_target.assert_called_once_with("mock_surface")
        renderer.reset_target.assert_called_once()
        renderer.set_opacity.assert_any_call(0.5)  # 验证设置了不透明度
        renderer.draw_surface.assert_called_once_with("mock_surface", 0, 0)
    
    def test_slide_effect_bridge(self):
        """测试滑动桥接效果"""
        # 创建一个模拟渲染器
        renderer = MagicMock()
        renderer.get_viewport_size.return_value = (800, 600)
        renderer.create_surface.return_value = "mock_surface"
        
        # 创建场景模拟对象
        current_scene = MagicMock()
        next_scene = MagicMock()
        
        # 创建一个桥接对象，使用模拟的SlideEffect
        bridge = TransitionEffectBridge(
            effect_type="slide", 
            duration=0.5,
            direction=SlideEffect.DIRECTION_LEFT
        )
        
        # 模拟效果
        bridge.effect = MagicMock()
        
        # 启动转场
        bridge.start_transition(True)
        
        # 测试渲染
        bridge._render_slide_transition(renderer, current_scene, next_scene)
        
        # 验证场景渲染调用
        current_scene.render.assert_called_once_with(renderer)
        next_scene.render.assert_called_once_with(renderer)
        
        # 验证渲染器操作
        assert renderer.set_target.call_count == 2
        assert renderer.reset_target.call_count == 2
        
        # 验证效果的draw方法被调用
        bridge.effect.draw.assert_called_once_with(
            renderer, "mock_surface", "mock_surface", 0, 0, 800, 600
        )

class TestTransitionManager:
    """测试转场管理器"""
    
    def test_singleton_pattern(self):
        """测试单例模式实现"""
        manager1 = TransitionManager.get_instance()
        manager2 = TransitionManager.get_instance()
        
        assert manager1 is manager2
    
    def test_register_and_create_transition(self):
        """测试注册和创建转场效果"""
        manager = TransitionManager.get_instance()
        
        # 注册一个测试转场效果
        manager.register_transition("test_fade", lambda **kwargs: FadeTransition(**kwargs))
        
        # 创建转场效果
        transition = manager.create_transition("test_fade", duration=0.3)
        
        # 验证创建的对象
        assert isinstance(transition, FadeTransition)
        assert transition.duration == 0.3
    
    def test_register_effect_transition(self):
        """测试注册基于过渡效果系统的转场效果"""
        manager = TransitionManager.get_instance()
        
        # 注册一个基于过渡效果系统的转场效果
        manager.register_effect_transition(
            "test_effect_fade", 
            "fade", 
            duration=0.7,
            from_alpha=0.2,
            to_alpha=0.9
        )
        
        # 创建转场效果
        transition = manager.create_transition("test_effect_fade")
        
        # 验证创建的对象
        assert isinstance(transition, TransitionEffectBridge)
        assert transition.duration == 0.7
        assert isinstance(transition.effect, FadeEffect)
        assert transition.effect.from_alpha == 0.2
        assert transition.effect.to_alpha == 0.9
    
    def test_default_transitions(self):
        """测试默认转场效果注册"""
        manager = TransitionManager.get_instance()
        
        # 重置转场效果，以防其他测试影响
        manager._transitions = {}
        manager._default_transition = None
        
        # 注册默认转场效果
        manager.register_default_transitions()
        
        # 验证基本转场效果
        transition1 = manager.create_transition("fade")
        assert isinstance(transition1, FadeTransition)
        
        # 验证基于过渡效果系统的转场效果
        transition2 = manager.create_transition("fade2")
        assert isinstance(transition2, TransitionEffectBridge)
        assert isinstance(transition2.effect, FadeEffect)
        
        transition3 = manager.create_transition("flip_h")
        assert isinstance(transition3, TransitionEffectBridge)
        assert isinstance(transition3.effect, FlipTransition)
        assert transition3.effect.flip_direction == FlipTransition.DIRECTION_HORIZONTAL
        
        # 验证默认转场效果
        default_transition = manager.create_default_transition()
        assert isinstance(default_transition, FadeTransition) 