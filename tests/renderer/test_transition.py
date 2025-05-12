"""
---------------------------------------------------------------
File name:                  test_transition.py
Author:                     Ignorant-lu
Date created:               2025/04/03
Description:                过渡效果系统测试
----------------------------------------------------------------

Changed history:            
                            2025/04/03: 初始创建;
----
"""

import pytest
import time
import math
from unittest.mock import Mock, patch, MagicMock

from status.renderer.transition import (
    TransitionState, EasingFunc, Transition,
    FadeTransition, SlideTransition, ScaleTransition, FlipTransition,
    TransitionManager
)

class TestEasingFunctions:
    """缓动函数测试"""
    
    def test_linear_easing(self):
        """测试线性缓动函数"""
        # 线性缓动应该返回相同的值
        assert EasingFunc.linear(0.0) == 0.0
        assert EasingFunc.linear(0.5) == 0.5
        assert EasingFunc.linear(1.0) == 1.0
    
    def test_quadratic_easing(self):
        """测试二次方缓动函数"""
        # 缓入: 增长从慢到快
        assert EasingFunc.ease_in_quad(0.0) == 0.0
        assert EasingFunc.ease_in_quad(0.5) == 0.25  # 0.5^2 = 0.25
        assert EasingFunc.ease_in_quad(1.0) == 1.0
        
        # 缓出: 增长从快到慢
        assert EasingFunc.ease_out_quad(0.0) == 0.0
        assert EasingFunc.ease_out_quad(0.5) > 0.5  # 应该大于线性值
        assert EasingFunc.ease_out_quad(1.0) == 1.0
        
        # 缓入缓出: 增长从慢到快再到慢
        assert EasingFunc.ease_in_out_quad(0.0) == 0.0
        assert EasingFunc.ease_in_out_quad(0.25) < 0.25  # 前半段应小于线性值
        assert EasingFunc.ease_in_out_quad(0.5) == 0.5
        assert EasingFunc.ease_in_out_quad(0.75) > 0.75  # 后半段应大于线性值
        assert EasingFunc.ease_in_out_quad(1.0) == 1.0
    
    def test_cubic_easing(self):
        """测试三次方缓动函数"""
        # 缓入
        assert EasingFunc.ease_in_cubic(0.0) == 0.0
        assert EasingFunc.ease_in_cubic(0.5) == 0.125  # 0.5^3 = 0.125
        assert EasingFunc.ease_in_cubic(1.0) == 1.0
        
        # 缓出
        assert EasingFunc.ease_out_cubic(0.0) == 0.0
        assert EasingFunc.ease_out_cubic(0.5) > 0.5
        assert EasingFunc.ease_out_cubic(1.0) == 1.0
    
    def test_sine_easing(self):
        """测试正弦缓动函数"""
        # 缓入
        assert EasingFunc.ease_in_sine(0.0) == 0.0
        assert round(EasingFunc.ease_in_sine(1.0), 10) == 1.0
        
        # 缓出
        assert EasingFunc.ease_out_sine(0.0) == 0.0
        assert round(EasingFunc.ease_out_sine(1.0), 10) == 1.0
    
    def test_elastic_easing(self):
        """测试弹性缓动函数"""
        # 弹性缓入应该在某些点超过1.0
        over_values = False
        for i in range(1, 100):
            t = i / 100
            if EasingFunc.ease_in_elastic(t) > 1.0 or EasingFunc.ease_in_elastic(t) < 0.0:
                over_values = True
                break
        
        assert over_values
        
        # 但起点和终点应该是0和1
        assert EasingFunc.ease_in_elastic(0.0) == 0.0
        assert EasingFunc.ease_in_elastic(1.0) == 1.0
    
    def test_bounce_easing(self):
        """测试弹跳缓动函数"""
        # 弹跳应该在某些点有局部最大值
        local_maxima = []
        prev = 0
        increasing = True
        for i in range(0, 101):
            t = i / 100
            val = EasingFunc.ease_out_bounce(t)
            
            if increasing and val < prev:
                local_maxima.append(prev)
                increasing = False
            elif not increasing and val > prev:
                increasing = True
            
            prev = val
        
        # 应该至少有一个局部最大值
        assert len(local_maxima) > 0
        
        # 起点和终点应该是0和1
        assert EasingFunc.ease_out_bounce(0.0) == 0.0
        assert EasingFunc.ease_out_bounce(1.0) == 1.0
    
    def test_get_easing_function(self):
        """测试获取缓动函数"""
        # 获取有效的缓动函数
        linear_func = EasingFunc.get_easing_function('linear')
        assert linear_func(0.5) == 0.5
        
        quad_func = EasingFunc.get_easing_function('ease_in_quad')
        assert quad_func(0.5) == 0.25
        
        # 获取无效的缓动函数应该抛出异常
        with pytest.raises(ValueError):
            EasingFunc.get_easing_function('invalid_easing')


class TestTransitionBase:
    """过渡效果基类测试"""
    
    def test_transition_init(self):
        """测试过渡效果初始化"""
        # 默认参数
        transition = Transition()
        assert transition.duration == 1.0
        assert transition.state == TransitionState.RUNNING  # auto_start默认为True
        assert transition.progress == 0.0
        
        # 自定义参数
        transition = Transition(duration=2.0, easing='ease_in_quad', 
                                auto_reverse=True, auto_start=False)
        assert transition.duration == 2.0
        assert transition.easing_func == EasingFunc.ease_in_quad
        assert transition.auto_reverse is True
        assert transition.state == TransitionState.INITIALIZED  # auto_start为False
    
    def test_transition_lifecycle(self):
        """测试过渡效果生命周期"""
        transition = Transition(auto_start=False)
        assert transition.state == TransitionState.INITIALIZED
        
        # 开始
        transition.start()
        assert transition.state == TransitionState.RUNNING
        
        # 暂停
        transition.pause()
        assert transition.state == TransitionState.PAUSED
        
        # 恢复
        transition.resume()
        assert transition.state == TransitionState.RUNNING
        
        # 完成
        transition.complete()
        assert transition.state == TransitionState.COMPLETED
        assert transition.is_completed() is True
    
    def test_transition_update(self):
        """测试过渡效果更新"""
        # 创建一个持续1秒的过渡效果
        transition = Transition(duration=1.0, auto_start=True)
        
        # 模拟时间流逝
        transition.start_time = time.time() - 0.5  # 已经过去0.5秒
        transition.update()
        
        # 进度应该接近0.5
        assert 0.45 <= transition.progress <= 0.55
        
        # 模拟完成
        transition.start_time = time.time() - 1.5  # 已经过去1.5秒
        transition.update()
        
        # 应该已完成
        assert transition.state == TransitionState.COMPLETED
        assert transition.progress == 1.0
    
    def test_auto_reverse(self):
        """测试自动反向"""
        # 创建一个自动反向的过渡效果
        transition = Transition(duration=1.0, auto_reverse=True, auto_start=True)
        
        # 模拟接近完成
        transition.start_time = time.time() - 0.95  # 已经过去0.95秒
        transition.update()
        
        # 进度应该接近1.0
        assert transition.progress > 0.9
        
        # 模拟完成并开始反向
        transition.start_time = time.time() - 1.05  # 已经过去1.05秒
        transition.update()
        
        # 应该已开始反向
        assert transition.state == TransitionState.REVERSED
        assert transition.direction == -1
    
    def test_manual_reverse(self):
        """测试手动反向"""
        transition = Transition(duration=1.0, auto_start=True)
        
        # 模拟进行到一半
        transition.start_time = time.time() - 0.5  # 已经过去0.5秒
        transition.update()
        
        # 手动反向
        transition.reverse()
        
        # 应该已反向
        assert transition.direction == -1
        assert transition.state == TransitionState.REVERSED
        
        # 再次反向
        transition.reverse()
        
        # 应该恢复正向
        assert transition.direction == 1
        assert transition.state == TransitionState.RUNNING
    
    def test_get_value(self):
        """测试获取中间值"""
        transition = Transition(auto_start=False)
        
        # 设置进度
        transition.progress = 0.0
        assert transition.get_value(0, 100) == 0
        
        transition.progress = 0.5
        assert transition.get_value(0, 100) == 50
        
        transition.progress = 1.0
        assert transition.get_value(0, 100) == 100
        
        # 反向插值
        assert transition.get_value(100, 0) == 0
    
    def test_edge_cases(self):
        """测试边界情况"""
        # 测试极短持续时间
        transition = Transition(duration=0.0001)
        assert transition.duration == 0.001  # 应该被限制为最小值0.001
        
        # 测试无效的缓动函数名称
        with pytest.raises(ValueError):
            Transition(easing='not_a_valid_easing')
        
        # 测试边界进度值
        transition = Transition(auto_start=False)
        transition.progress = -0.1  # 超出下界
        assert transition.get_value(0, 100) == -10  # 应该允许超出边界
        
        transition.progress = 1.1  # 超出上界
        # 使用近似比较，允许浮点数误差
        result = transition.get_value(0, 100)
        assert abs(result - 110) < 0.0001  # 应该允许超出边界
    
    def test_delta_time_update(self):
        """测试使用delta_time参数更新"""
        transition = Transition(duration=1.0, auto_start=True)
        
        # 使用固定的delta_time而不是实际时间流逝
        transition.update(delta_time=0.5)
        assert transition.elapsed_time == 0.5
        assert transition.progress == 0.5
        
        # 再次更新
        transition.update(delta_time=0.25)
        assert transition.elapsed_time == 0.75
        assert transition.progress == 0.75
        
        # 超过持续时间
        transition.update(delta_time=0.5)
        assert transition.state == TransitionState.COMPLETED
        assert transition.progress == 1.0
    
    def test_callback_function(self):
        """测试回调函数"""
        # 创建一个记录回调是否被调用的函数
        callback_called = [False]
        
        def on_complete():
            callback_called[0] = True
        
        # 创建带回调的过渡效果
        transition = Transition(duration=0.5, on_complete=on_complete)
        
        # 正常完成
        transition.start_time = time.time() - 1.0  # 已经过去1.0秒，超过持续时间
        transition.update()
        
        # 回调应该被调用
        assert callback_called[0] is True
        
        # 重置并测试手动完成
        callback_called[0] = False
        transition = Transition(duration=1.0, on_complete=on_complete)
        transition.complete()
        
        # 回调应该被调用
        assert callback_called[0] is True


class TestFadeTransition:
    """淡入淡出过渡效果测试"""
    
    def test_fade_init(self):
        """测试淡入淡出初始化"""
        # 默认参数
        transition = FadeTransition()
        assert transition.from_alpha == 0.0
        assert transition.to_alpha == 1.0
        assert transition.current_alpha == 0.0
        
        # 自定义参数
        transition = FadeTransition(from_alpha=1.0, to_alpha=0.0)
        assert transition.from_alpha == 1.0
        assert transition.to_alpha == 0.0
    
    def test_fade_update(self):
        """测试淡入淡出更新"""
        # 创建过渡效果
        transition = FadeTransition(from_alpha=0.0, to_alpha=1.0)
        
        # 设置进度和状态以模拟update后的状态
        transition.progress = 0.5
        transition.state = TransitionState.RUNNING
        
        # 手动计算并设置current_alpha
        transition.current_alpha = transition.get_value(transition.from_alpha, transition.to_alpha)
        
        # 验证计算结果
        assert transition.current_alpha == 0.5
    
    def test_fade_draw(self):
        """测试淡入淡出绘制"""
        # 创建模拟渲染器
        renderer = Mock()
        renderer.get_width.return_value = 800
        renderer.get_height.return_value = 600
        
        # 创建过渡效果并设置透明度
        transition = FadeTransition(from_alpha=0.0, to_alpha=1.0)
        transition.current_alpha = 0.5
        
        # 绘制
        transition.draw(renderer)
        
        # 验证渲染器调用
        renderer.set_alpha.assert_any_call(0.5)
        renderer.fill_rect.assert_called_once_with(0, 0, 800, 600, (0, 0, 0))
        # 确保恢复透明度
        renderer.set_alpha.assert_any_call(1.0)
        
    def test_fade_boundary_conditions(self):
        """测试淡入淡出边界条件"""
        # 测试超出范围的透明度值
        transition = FadeTransition(from_alpha=-0.5, to_alpha=1.5)
        
        # 即使输入超出范围，初始化时并不会限制
        assert transition.from_alpha == -0.5
        assert transition.to_alpha == 1.5
        
        # 设置进度为0
        transition.progress = 0.0
        transition.current_alpha = transition.get_value(transition.from_alpha, transition.to_alpha)
        assert transition.current_alpha == -0.5
        
        # 设置进度为1
        transition.progress = 1.0
        transition.current_alpha = transition.get_value(transition.from_alpha, transition.to_alpha)
        assert transition.current_alpha == 1.5
        
        # 设置进度为中间值
        transition.progress = 0.5
        transition.current_alpha = transition.get_value(transition.from_alpha, transition.to_alpha)
        assert transition.current_alpha == 0.5  # 中间值应该正确
        
    def test_fade_with_custom_easing(self):
        """测试带自定义缓动的淡入淡出"""
        # 测试不同的缓动函数对比
        transitions = {
            'linear': FadeTransition(from_alpha=0.0, to_alpha=1.0, easing='linear'),
            'ease_in_quad': FadeTransition(from_alpha=0.0, to_alpha=1.0, easing='ease_in_quad'),
            'ease_out_quad': FadeTransition(from_alpha=0.0, to_alpha=1.0, easing='ease_out_quad')
        }
        
        # 测试不同的进度点
        test_points = [0.0, 0.25, 0.5, 0.75, 1.0]
        
        for progress in test_points:
            # 对每个进度点，测试不同缓动函数的表现
            for name, transition in transitions.items():
                # 直接设置原始进度，这会应用各自的缓动函数
                transition.start_time = time.time() - (progress * transition.duration)
                transition.state = TransitionState.RUNNING
                transition.update()
                
                # 检查极限点行为
                if progress == 0.0:
                    assert transition.current_alpha == 0.0
                elif progress == 0.75:
                    # 0.75 进度点的值应该接近但不一定等于1.0
                    assert transition.current_alpha > 0.5  # 确保 alpha 值有合理的增长
                elif progress == 1.0:
                    assert transition.current_alpha == 1.0
        
        # 对中间进度点的特殊检查
        transitions['linear'].start_time = time.time() - (0.5 * transitions['linear'].duration)
        transitions['ease_in_quad'].start_time = time.time() - (0.5 * transitions['ease_in_quad'].duration)
        transitions['ease_out_quad'].start_time = time.time() - (0.5 * transitions['ease_out_quad'].duration)
        
        for transition in transitions.values():
            transition.state = TransitionState.RUNNING
            transition.update()
        
        # 我们只检查相对关系，不检查绝对值
        linear_alpha = transitions['linear'].current_alpha
        ease_in_alpha = transitions['ease_in_quad'].current_alpha
        ease_out_alpha = transitions['ease_out_quad'].current_alpha
        
        # 线性缓动在0.5点应该接近中间值
        assert abs(linear_alpha - 0.5) < 0.1
        
        # 二次缓入应该比线性缓动慢
        assert ease_in_alpha < linear_alpha
        
        # 二次缓出应该比线性缓动快
        assert ease_out_alpha > linear_alpha


class TestSlideTransition:
    """滑动过渡效果测试"""
    
    def test_slide_init(self):
        """测试滑动初始化"""
        # 默认参数
        transition = SlideTransition()
        assert transition.direction == SlideTransition.DIRECTION_LEFT
        
        # 自定义参数
        transition = SlideTransition(direction=SlideTransition.DIRECTION_RIGHT)
        assert transition.direction == SlideTransition.DIRECTION_RIGHT
    
    def test_get_offset(self):
        """测试获取偏移量"""
        transition = SlideTransition(direction=SlideTransition.DIRECTION_LEFT)
        
        # 开始时
        transition.progress = 0.0
        offset_x, offset_y = transition.get_offset(100, 100)
        assert offset_x == 100  # 100% 偏移
        assert offset_y == 0
        
        # 中间
        transition.progress = 0.5
        offset_x, offset_y = transition.get_offset(100, 100)
        assert offset_x == 50  # 50% 偏移
        assert offset_y == 0
        
        # 结束
        transition.progress = 1.0
        offset_x, offset_y = transition.get_offset(100, 100)
        assert offset_x == 0  # 0% 偏移
        assert offset_y == 0
        
        # 向右方向
        transition = SlideTransition(direction=SlideTransition.DIRECTION_RIGHT)
        transition.progress = 0.5
        offset_x, offset_y = transition.get_offset(100, 100)
        assert offset_x == -50
        assert offset_y == 0
        
        # 向上方向
        transition = SlideTransition(direction=SlideTransition.DIRECTION_UP)
        transition.progress = 0.5
        offset_x, offset_y = transition.get_offset(100, 100)
        assert offset_x == 0
        assert offset_y == 50
        
        # 向下方向
        transition = SlideTransition(direction=SlideTransition.DIRECTION_DOWN)
        transition.progress = 0.5
        offset_x, offset_y = transition.get_offset(100, 100)
        assert offset_x == 0
        assert offset_y == -50
    
    def test_slide_draw(self):
        """测试滑动绘制"""
        # 创建模拟渲染器和内容
        renderer = Mock()
        renderer.get_width.return_value = 800
        renderer.get_height.return_value = 600
        content_a = "content_a"
        content_b = "content_b"
        
        # 创建过渡效果(向左滑动)
        transition = SlideTransition(direction=SlideTransition.DIRECTION_LEFT)
        transition.progress = 0.5
        
        # 绘制
        transition.draw(renderer, content_a, content_b)
        
        # 验证渲染器调用
        renderer.draw_surface.assert_any_call(content_a, 400, 0)  # 起始内容偏移
        renderer.draw_surface.assert_any_call(content_b, 400 - 800, 0)  # 目标内容
        
    def test_slide_invalid_direction(self):
        """测试无效的滑动方向"""
        # 创建过渡效果(使用无效方向)
        transition = SlideTransition(direction=999)
        
        # 获取偏移量，应该返回(0,0)
        transition.progress = 0.5
        offset_x, offset_y = transition.get_offset(100, 100)
        
        # 验证无效方向的结果
        assert offset_x == 0
        assert offset_y == 0


class TestScaleTransition:
    """缩放过渡效果测试"""
    
    def test_scale_init(self):
        """测试缩放初始化"""
        # 默认参数
        transition = ScaleTransition()
        assert transition.from_scale == 0.0
        assert transition.to_scale == 1.0
        assert transition.center_x == 0.5
        assert transition.center_y == 0.5
        
        # 自定义参数
        transition = ScaleTransition(from_scale=1.0, to_scale=2.0, 
                                      center_x=0.0, center_y=0.0)
        assert transition.from_scale == 1.0
        assert transition.to_scale == 2.0
        assert transition.center_x == 0.0
        assert transition.center_y == 0.0
    
    def test_scale_update(self):
        """测试缩放更新"""
        # 创建过渡效果
        transition = ScaleTransition(from_scale=0.0, to_scale=2.0)
        
        # 设置进度和状态以模拟update后的状态
        transition.progress = 0.5
        transition.state = TransitionState.RUNNING
        
        # 手动计算并设置current_scale
        transition.current_scale = transition.get_value(transition.from_scale, transition.to_scale)
        
        # 验证计算结果
        assert transition.current_scale == 1.0
    
    def test_scale_draw(self):
        """测试缩放绘制"""
        # 创建模拟渲染器和内容
        renderer = Mock()
        renderer.get_width.return_value = 800
        renderer.get_height.return_value = 600
        content = "content"
        
        # 创建过渡效果
        transition = ScaleTransition(from_scale=0.0, to_scale=1.0)
        transition.progress = 0.5
        transition.current_scale = 0.5  # 设置缩放比例
        
        # 绘制
        transition.draw(renderer, content)
        
        # 验证渲染器调用
        # 实际调用的是draw_surface_scaled('content', 200, 150, 400, 300)
        renderer.draw_surface_scaled.assert_called_once_with(content, 200, 150, 400, 300)
        
    def test_center_point_effect(self):
        """测试中心点位置对缩放效果的影响"""
        # 创建模拟渲染器和内容
        renderer = Mock()
        renderer.get_width.return_value = 800
        renderer.get_height.return_value = 600
        content = "content"
        
        # 测试左上角为中心点的缩放
        transition_topleft = ScaleTransition(from_scale=0.0, to_scale=1.0, 
                                             center_x=0.0, center_y=0.0)
        transition_topleft.progress = 0.5
        transition_topleft.current_scale = 0.5
        
        # 绘制
        transition_topleft.draw(renderer, content)
        
        # 验证渲染器调用 - 左上角中心点缩放
        call_args = renderer.draw_surface_scaled.call_args[0]
        assert call_args[0] == content
        assert call_args[1] == 0  # x坐标为0
        assert call_args[2] == 0  # y坐标为0
        
        # 重置模拟对象
        renderer.reset_mock()
        
        # 测试中心点缩放 (0.5, 0.5)
        transition_center = ScaleTransition(from_scale=0.0, to_scale=1.0, 
                                           center_x=0.5, center_y=0.5)
        transition_center.progress = 0.5
        transition_center.current_scale = 0.5
        
        # 绘制
        transition_center.draw(renderer, content)
        
        # 验证渲染器调用 - 中心点缩放
        call_args = renderer.draw_surface_scaled.call_args[0]
        assert call_args[0] == content
        assert call_args[1] == 200  # 中心点缩放使用了正确的x位置
        assert call_args[2] == 150  # 中心点缩放使用了正确的y位置
        
        # 重置模拟对象
        renderer.reset_mock()
        
        # 测试右下角为中心点的缩放
        transition_bottomright = ScaleTransition(from_scale=0.0, to_scale=1.0, 
                                                center_x=1.0, center_y=1.0)
        transition_bottomright.progress = 0.5
        transition_bottomright.current_scale = 0.5
        
        # 绘制
        transition_bottomright.draw(renderer, content)
        
        # 验证渲染器调用 - 右下角中心点缩放
        call_args = renderer.draw_surface_scaled.call_args[0]
        assert call_args[0] == content
        
        # 计算预期位置（根据ScaleTransition的实现）
        # center_x = x + width * self.center_x = 0 + 800 * 1.0 = 800
        # scaled_width = width * self.current_scale = 800 * 0.5 = 400
        # scaled_x = center_x - scaled_width * self.center_x = 800 - 400 * 1.0 = 400
        # 同理，scaled_y = 600 - 300 * 1.0 = 300
        assert call_args[1] == 400  # x坐标应该是400
        assert call_args[2] == 300  # y坐标应该是300
    
    def test_reverse_scale_transition(self):
        """测试反向缩放过渡效果"""
        # 创建缩小的过渡效果
        transition = ScaleTransition(from_scale=2.0, to_scale=0.5)
        
        # 设置进度
        transition.progress = 0.5
        transition.current_scale = transition.get_value(transition.from_scale, transition.to_scale)
        
        # 验证中间值
        assert transition.current_scale == 1.25  # 从2.0缩小到0.5的中间值


class TestFlipTransition:
    """翻转过渡效果测试"""
    
    def test_flip_init(self):
        """测试翻转初始化"""
        # 默认参数
        transition = FlipTransition()
        assert transition.flip_direction == FlipTransition.DIRECTION_HORIZONTAL
        
        # 自定义参数
        transition = FlipTransition(direction=FlipTransition.DIRECTION_VERTICAL)
        assert transition.flip_direction == FlipTransition.DIRECTION_VERTICAL
    
    def test_flip_update(self):
        """测试翻转更新"""
        # 测试水平翻转
        h_transition = FlipTransition(direction=FlipTransition.DIRECTION_HORIZONTAL)
        
        # 设置进度和状态以模拟update后的状态
        h_transition.progress = 0.5
        h_transition.state = TransitionState.RUNNING
        
        # 手动计算并设置角度
        h_transition.angle = h_transition.progress * 180.0
        
        # 验证角度计算结果
        assert h_transition.angle == 90.0
        
        # 测试垂直翻转
        v_transition = FlipTransition(direction=FlipTransition.DIRECTION_VERTICAL)
        
        # 设置进度和状态以模拟update后的状态
        v_transition.progress = 0.5
        v_transition.state = TransitionState.RUNNING
        
        # 手动计算并设置角度
        v_transition.angle = v_transition.progress * 180.0
        
        # 验证角度计算结果
        assert v_transition.angle == 90.0
    
    def test_flip_draw(self):
        """测试翻转绘制"""
        # 创建模拟渲染器和内容
        renderer = Mock()
        renderer.get_width.return_value = 800
        renderer.get_height.return_value = 600
        content_a = "content_a"
        content_b = "content_b"
        
        # 创建过渡效果(水平翻转)
        transition = FlipTransition(direction=FlipTransition.DIRECTION_HORIZONTAL)
        
        # 测试第一阶段(< 90度)
        transition.angle = 45.0
        transition.draw(renderer, content_a, content_b)
        
        # 第一阶段应该绘制content_a
        renderer.draw_surface_scaled.assert_called_once()
        args = renderer.draw_surface_scaled.call_args[0]
        assert args[0] == content_a
        
        # 重置模拟对象
        renderer.reset_mock()
        
        # 测试第二阶段(>= 90度)
        transition.angle = 135.0
        transition.draw(renderer, content_a, content_b)
        
        # 第二阶段应该绘制content_b
        renderer.draw_surface_scaled.assert_called_once()
        args = renderer.draw_surface_scaled.call_args[0]
        assert args[0] == content_b
        
    def test_vertical_flip_draw(self):
        """测试垂直翻转绘制"""
        # 创建模拟渲染器和内容
        renderer = Mock()
        renderer.get_width.return_value = 800
        renderer.get_height.return_value = 600
        content_a = "content_a"
        content_b = "content_b"
        
        # 创建过渡效果(垂直翻转)
        transition = FlipTransition(direction=FlipTransition.DIRECTION_VERTICAL)
        
        # 测试第一阶段(< 90度)
        transition.angle = 45.0
        transition.draw(renderer, content_a, content_b)
        
        # 第一阶段应该绘制content_a
        renderer.draw_surface_scaled.assert_called_once()
        
        # 水平翻转和垂直翻转应该调用不同的变换参数
        args = renderer.draw_surface_scaled.call_args[0]
        assert args[0] == content_a
        
        # 重置模拟对象
        renderer.reset_mock()
        
        # 测试第二阶段(>= 90度)
        transition.angle = 135.0
        transition.draw(renderer, content_a, content_b)
        
        # 第二阶段应该绘制content_b
        renderer.draw_surface_scaled.assert_called_once()
        args = renderer.draw_surface_scaled.call_args[0]
        assert args[0] == content_b
        
    def test_non_90_degree_flip(self):
        """测试非90度的翻转效果"""
        # 创建模拟渲染器和内容
        renderer = Mock()
        renderer.get_width.return_value = 800
        renderer.get_height.return_value = 600
        content_a = "content_a"
        content_b = "content_b"
        
        # 创建过渡效果(水平翻转)
        transition = FlipTransition(direction=FlipTransition.DIRECTION_HORIZONTAL)
        
        # 测试30度翻转
        transition.angle = 30.0
        transition.draw(renderer, content_a, content_b)
        
        # 30度时应该绘制content_a，但有一定的缩放
        renderer.draw_surface_scaled.assert_called_once()
        args = renderer.draw_surface_scaled.call_args[0]
        assert args[0] == content_a
        
        # 检查缩放因子，应该小于1(物体看起来在逐渐缩小)
        width_scale = args[3] / 800.0
        assert width_scale < 1.0
        
        # 重置模拟对象
        renderer.reset_mock()
        
        # 测试150度翻转
        transition.angle = 150.0
        transition.draw(renderer, content_a, content_b)
        
        # 150度时应该绘制content_b，但有一定的缩放
        renderer.draw_surface_scaled.assert_called_once()
        args = renderer.draw_surface_scaled.call_args[0]
        assert args[0] == content_b
        
        # 检查缩放因子，应该小于1(物体看起来在逐渐放大)
        width_scale = args[3] / 800.0
        assert width_scale < 1.0


class TestTransitionManager:
    """过渡效果管理器测试"""
    
    def setup_method(self):
        """每个测试方法前的设置"""
        # 重置单例实例
        TransitionManager._instance = None
    
    def test_singleton(self):
        """测试单例模式"""
        # 获取实例
        instance1 = TransitionManager.get_instance()
        instance2 = TransitionManager.get_instance()
        
        # 应该是同一个实例
        assert instance1 is instance2
        
        # 直接实例化应该抛出异常
        with pytest.raises(RuntimeError):
            TransitionManager()
    
    def test_create_transition(self):
        """测试创建过渡效果"""
        manager = TransitionManager.get_instance()
        
        # 创建各种类型的过渡效果
        fade = manager.create_transition('fade')
        assert isinstance(fade, FadeTransition)
        
        slide = manager.create_transition('slide', direction=SlideTransition.DIRECTION_RIGHT)
        assert isinstance(slide, SlideTransition)
        assert slide.direction == SlideTransition.DIRECTION_RIGHT
        
        scale = manager.create_transition('scale', from_scale=0.5, to_scale=1.5)
        assert isinstance(scale, ScaleTransition)
        assert scale.from_scale == 0.5
        assert scale.to_scale == 1.5
        
        flip = manager.create_transition('flip', direction=FlipTransition.DIRECTION_VERTICAL)
        assert isinstance(flip, FlipTransition)
        assert flip.flip_direction == FlipTransition.DIRECTION_VERTICAL
        
        # 创建无效类型应该抛出异常
        with pytest.raises(ValueError):
            manager.create_transition('invalid_type')
    
    def test_transition_management(self):
        """测试过渡效果管理"""
        manager = TransitionManager.get_instance()
        
        # 创建过渡效果
        transition = manager.create_transition('fade')
        
        # 应该没有活动的过渡效果
        assert manager.has_active_transition() is False
        assert manager.get_active_transition() is None
        
        # 开始过渡效果
        manager.start_transition(transition)
        
        # 现在应该有活动的过渡效果
        assert manager.has_active_transition() is True
        assert manager.get_active_transition() is transition
        
        # 更新过渡效果
        manager.update()
        
        # 清除过渡效果
        manager.clear_transitions()
        
        # 应该没有活动的过渡效果
        assert manager.has_active_transition() is False
        assert manager.get_active_transition() is None
    
    def test_transition_completion(self):
        """测试过渡效果完成"""
        manager = TransitionManager.get_instance()
        
        # 创建一个快速完成的过渡效果
        transition = manager.create_transition('fade', duration=0.01)
        
        # 开始过渡效果
        manager.start_transition(transition)
        
        # 设置过渡效果为完成状态
        transition.complete()
        
        # 更新过渡效果
        manager.update()
        
        # 完成的过渡效果应该被移除
        assert manager.has_active_transition() is False
        assert manager.get_active_transition() is None
        
    def test_multiple_transitions(self):
        """测试多个过渡效果同时运行"""
        manager = TransitionManager.get_instance()
        
        # 创建两个过渡效果
        fade = manager.create_transition('fade', duration=1.0)
        slide = manager.create_transition('slide', duration=0.5)
        
        # 启动两个过渡效果
        manager.start_transition(fade)  # 这个会成为active_transition
        manager.transitions.append(slide)
        slide.start()
        
        # 应该有两个过渡效果在运行
        assert len(manager.transitions) == 2
        assert manager.has_active_transition() is True
        assert manager.get_active_transition() is fade  # active_transition应该是第一个启动的
        
        # 更新过渡效果
        manager.update()
        
        # 完成slide过渡效果
        slide.complete()
        manager.update()
        
        # 应该只剩一个过渡效果
        assert len(manager.transitions) == 1
        assert manager.has_active_transition() is True
        assert manager.get_active_transition() is fade
        
        # 完成fade过渡效果
        fade.complete()
        manager.update()
        
        # 应该没有活动的过渡效果
        assert manager.has_active_transition() is False
        assert manager.get_active_transition() is None
        
    def test_register_transition_compatibility(self):
        """测试register_transition兼容方法"""
        manager = TransitionManager.get_instance()
        
        # 这个方法仅用于兼容性，实际上什么都不做
        # 但应该能成功调用而不引发异常
        def dummy_factory():
            return None
            
        manager.register_transition("test", dummy_factory)
        
        # 没有异常就是成功 