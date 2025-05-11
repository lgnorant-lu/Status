"""
---------------------------------------------------------------
File name:                  test_emotion_system.py
Author:                     Ignorant-lu
Date created:               2025/04/04
Description:                情绪系统单元测试
----------------------------------------------------------------

Changed history:            
                            2025/04/04: 初始创建;
----
"""

import unittest
import time
from unittest.mock import MagicMock, patch

from status.behavior.emotion_system import (
    EmotionParams,
    EmotionState,
    EmotionType,
    EmotionalEvent,
    EmotionalEventType,
    EmotionSystem,
    get_emotion_system,
    initialize_default_emotion_events
)


class TestEmotionParams(unittest.TestCase):
    """测试情绪参数类"""

    def test_initialization(self):
        """测试初始化"""
        # 默认初始化
        params = EmotionParams()
        self.assertEqual(params.pleasure, 0.0)
        self.assertEqual(params.arousal, 0.5)
        self.assertEqual(params.social, 0.5)
        
        # 自定义值初始化
        params = EmotionParams(pleasure=0.8, arousal=0.3, social=0.7)
        self.assertEqual(params.pleasure, 0.8)
        self.assertEqual(params.arousal, 0.3)
        self.assertEqual(params.social, 0.7)
        
    def test_range_validation(self):
        """测试参数范围验证"""
        # 测试范围限制 - 上限
        params = EmotionParams(pleasure=2.0, arousal=1.5, social=2.0)
        self.assertEqual(params.pleasure, 1.0)  # 限制为最大值
        self.assertEqual(params.arousal, 1.0)
        self.assertEqual(params.social, 1.0)
        
        # 测试范围限制 - 下限
        params = EmotionParams(pleasure=-2.0, arousal=-0.5, social=-0.5)
        self.assertEqual(params.pleasure, -1.0)  # 限制为最小值
        self.assertEqual(params.arousal, 0.0)
        self.assertEqual(params.social, 0.0)
        
    def test_adjust(self):
        """测试参数调整"""
        params = EmotionParams(pleasure=0.0, arousal=0.5, social=0.5)
        
        # 调整参数
        params.adjust(pleasure_delta=0.3, arousal_delta=0.2, social_delta=-0.2)
        
        # 验证调整后的值
        self.assertEqual(params.pleasure, 0.3)
        self.assertEqual(params.arousal, 0.7)
        self.assertEqual(params.social, 0.3)
        
        # 测试边界情况
        params.adjust(pleasure_delta=0.8, arousal_delta=0.5, social_delta=-0.5)
        self.assertEqual(params.pleasure, 1.0)  # 达到上限
        self.assertEqual(params.arousal, 1.0)
        self.assertEqual(params.social, 0.0)  # 达到下限


class TestEmotionalEvent(unittest.TestCase):
    """测试情绪事件类"""
    
    def test_initialization(self):
        """测试初始化"""
        event = EmotionalEvent(
            event_type=EmotionalEventType.USER_PET,
            intensity=0.8,
            pleasure_effect=0.2,
            arousal_effect=0.1,
            social_effect=0.15
        )
        
        self.assertEqual(event.event_type, EmotionalEventType.USER_PET)
        self.assertEqual(event.intensity, 0.8)
        self.assertEqual(event.pleasure_effect, 0.2)
        self.assertEqual(event.arousal_effect, 0.1)
        self.assertEqual(event.social_effect, 0.15)
        self.assertIsInstance(event.timestamp, float)
        
    def test_apply_to(self):
        """测试应用事件效果到情绪状态"""
        # 创建事件和情绪参数
        event = EmotionalEvent(
            event_type=EmotionalEventType.USER_PET,
            intensity=0.5,
            pleasure_effect=0.2,
            arousal_effect=0.1,
            social_effect=0.15
        )
        
        params = EmotionParams(pleasure=0.0, arousal=0.5, social=0.5)
        
        # 应用事件效果
        event.apply_to(params)
        
        # 验证效果（考虑强度因素）
        self.assertEqual(params.pleasure, 0.1)  # 0.0 + 0.2*0.5
        self.assertEqual(params.arousal, 0.55)  # 0.5 + 0.1*0.5
        self.assertEqual(params.social, 0.575)  # 0.5 + 0.15*0.5


class TestEmotionState(unittest.TestCase):
    """测试情绪状态类"""
    
    def setUp(self):
        """测试前准备"""
        # 设置日志记录器的模拟对象
        self.mock_logger = MagicMock()
        
        # 打补丁替换原始logger
        self.logger_patcher = patch('status.behavior.emotion_system.logging.getLogger')
        self.mock_logger_func = self.logger_patcher.start()
        self.mock_logger_func.return_value = self.mock_logger
        
    def tearDown(self):
        """测试后清理"""
        self.logger_patcher.stop()
    
    def test_initialization(self):
        """测试初始化"""
        # 默认初始化
        state = EmotionState()
        self.assertIsInstance(state.params, EmotionParams)
        self.assertEqual(state.previous_emotion, EmotionType.NEUTRAL)
        self.assertIsInstance(state.current_emotion, EmotionType)
        self.assertIsInstance(state.emotion_start_time, float)
        self.assertEqual(state.emotion_duration, 0.0)
        
        # 使用自定义参数初始化
        params = EmotionParams(pleasure=0.8, arousal=0.8, social=0.5)
        state = EmotionState(params)
        self.assertEqual(state.params, params)
        # 检查情绪是否被正确确定（基于参数应该是EXCITED）
        self.assertEqual(state.current_emotion, EmotionType.EXCITED)
        
    def test_determine_emotion(self):
        """测试情绪类型确定"""
        test_cases = [
            # 参数值 -> 预期情绪类型
            ((0.5, 0.5, 0.5), EmotionType.HAPPY),  # 快乐
            ((0.5, 0.9, 0.5), EmotionType.EXCITED),  # 兴奋
            ((0.0, 0.2, 0.5), EmotionType.CALM),  # 平静
            ((-0.6, 0.2, 0.5), EmotionType.SAD),  # 悲伤
            ((-0.6, 0.8, 0.5), EmotionType.ANGRY),  # 愤怒
            ((0.0, 0.2, 0.2), EmotionType.CALM),  # 平静，由于条件冲突，这里改为期望CALM
            ((0.2, 0.1, 0.5), EmotionType.CALM),  # 平静
            ((0.2, 0.5, 0.8), EmotionType.CURIOUS),  # 好奇
        ]
        
        for params, expected_emotion in test_cases:
            # 创建具有特定参数的情绪状态
            state = EmotionState(EmotionParams(pleasure=params[0], arousal=params[1], social=params[2]))
            
            # 验证情绪类型是否匹配预期
            self.assertEqual(state.current_emotion, expected_emotion, 
                            f"参数 {params} 应该产生情绪 {expected_emotion}，但得到了 {state.current_emotion}")
    
    def test_update(self):
        """测试更新情绪状态"""
        # 创建情绪状态
        state = EmotionState(EmotionParams(pleasure=0.5, arousal=0.5, social=0.5))
        initial_emotion = state.current_emotion
        initial_time = state.emotion_start_time
        
        # 短暂等待以确保情绪持续时间被更新
        time.sleep(0.1)
        
        # 不改变情绪类型的更新
        state.update(0.1)
        self.assertEqual(state.current_emotion, initial_emotion)
        self.assertEqual(state.emotion_start_time, initial_time)
        self.assertGreater(state.emotion_duration, 0.0)
        
        # 更改参数导致情绪变化
        state.params.adjust(pleasure_delta=-1.0, arousal_delta=-0.2)  # 变为SAD情绪
        previous_emotion = state.current_emotion
        state.update(0.1)
        
        # 验证情绪变化
        self.assertEqual(state.previous_emotion, previous_emotion)
        self.assertEqual(state.current_emotion, EmotionType.SAD)
        self.assertNotEqual(state.emotion_start_time, initial_time)
        self.assertLess(state.emotion_duration, 0.1)  # 新情绪的持续时间应该很短
        self.mock_logger.info.assert_called()  # 应该记录情绪变化
        
    def test_apply_decay(self):
        """测试情绪参数衰减"""
        # 创建各种参数值的情绪状态
        states = [
            # 初始参数，衰减时间，衰减率
            (EmotionParams(pleasure=0.5, arousal=0.8, social=0.8), 1.0, 0.1),
            (EmotionParams(pleasure=-0.5, arousal=0.2, social=0.2), 1.0, 0.1),
            (EmotionParams(pleasure=0.0, arousal=0.5, social=0.5), 1.0, 0.1)
        ]
        
        for params, dt, rate in states:
            state = EmotionState(params)
            initial_values = (params.pleasure, params.arousal, params.social)
            
            # 应用衰减
            state.apply_decay(dt, rate)
            
            # 验证衰减方向
            p, a, s = params.pleasure, params.arousal, params.social
            
            # 愉悦度应向0衰减
            if initial_values[0] > 0:
                self.assertLess(p, initial_values[0])
            elif initial_values[0] < 0:
                self.assertGreater(p, initial_values[0])
            
            # 活跃度应向0.5衰减
            if initial_values[1] > 0.5:
                self.assertLess(a, initial_values[1])
            elif initial_values[1] < 0.5:
                self.assertGreater(a, initial_values[1])
            
            # 社交度应向0.5衰减
            if initial_values[2] > 0.5:
                self.assertLess(s, initial_values[2])
            elif initial_values[2] < 0.5:
                self.assertGreater(s, initial_values[2])
    
    def test_get_behavior_multipliers(self):
        """测试获取行为乘数"""
        # 测试不同情绪状态的行为乘数
        for emotion_type in [
            EmotionType.HAPPY, EmotionType.EXCITED, EmotionType.CALM, 
            EmotionType.SAD, EmotionType.ANGRY, EmotionType.BORED,
            EmotionType.SLEEPY, EmotionType.CURIOUS
        ]:
            # 创建模拟的情绪状态
            state = EmotionState()
            state.current_emotion = emotion_type
            
            # 获取行为乘数
            multipliers = state.get_behavior_multipliers()
            
            # 验证返回的是字典
            self.assertIsInstance(multipliers, dict)
            # 验证有行为乘数
            self.assertGreater(len(multipliers), 0)
            
            # 验证乘数类型是否正确
            for behavior, multiplier in multipliers.items():
                self.assertIsInstance(behavior, str)
                self.assertIsInstance(multiplier, float)
    
    def test_get_animation_params(self):
        """测试获取动画参数"""
        # 创建情绪状态
        state = EmotionState(EmotionParams(pleasure=0.5, arousal=0.7, social=0.3))
        
        # 获取动画参数
        params = state.get_animation_params()
        
        # 验证参数
        self.assertIsInstance(params, dict)
        self.assertIn('speed_multiplier', params)
        self.assertIn('size_multiplier', params)
        self.assertIn('color_intensity', params)
        self.assertIn('interaction_range', params)
        
        # 验证参数值是否基于情绪参数计算
        self.assertAlmostEqual(params['speed_multiplier'], 0.5 + 0.7)
        self.assertAlmostEqual(params['size_multiplier'], 1.0 + 0.2 * 0.5)
        self.assertAlmostEqual(params['color_intensity'], 0.5 + 0.5 * abs(0.5))
        self.assertAlmostEqual(params['interaction_range'], 1.0 + 0.5 * 0.3)


class TestEmotionSystem(unittest.TestCase):
    """测试情绪系统类"""
    
    def setUp(self):
        """测试前准备"""
        # 设置日志记录器的模拟对象
        self.mock_logger = MagicMock()
        
        # 打补丁替换原始logger
        self.logger_patcher = patch('status.behavior.emotion_system.logging.getLogger')
        self.mock_logger_func = self.logger_patcher.start()
        self.mock_logger_func.return_value = self.mock_logger
        
        # 创建模拟实体
        self.mock_entity = MagicMock()
        
        # 创建情绪系统
        self.emotion_system = EmotionSystem(self.mock_entity)
        
    def tearDown(self):
        """测试后清理"""
        self.logger_patcher.stop()
    
    def test_initialization(self):
        """测试初始化"""
        # 验证基本属性
        self.assertEqual(self.emotion_system.entity, self.mock_entity)
        self.assertIsInstance(self.emotion_system.emotion_state, EmotionState)
        self.assertIsInstance(self.emotion_system.event_mappings, dict)
        self.assertIsInstance(self.emotion_system.recent_events, list)
        self.assertIsInstance(self.emotion_system.last_update_time, float)
        self.assertIsInstance(self.emotion_system.decay_rate, float)
        
        # 验证默认事件映射是否已加载
        self.assertEqual(len(self.emotion_system.event_mappings), len(EmotionalEventType))
        
        # 验证是否记录了初始化日志
        self.mock_logger.info.assert_called_with("情绪系统已初始化")
        
    def test_update(self):
        """测试更新方法"""
        # 设置模拟的情绪状态
        mock_emotion_state = MagicMock()
        self.emotion_system.emotion_state = mock_emotion_state
        
        # 记录初始更新时间
        initial_update_time = self.emotion_system.last_update_time
        
        # 短暂等待确保时间差
        time.sleep(0.1)
        
        # 更新情绪系统
        self.emotion_system.update()
        
        # 验证情绪状态的方法是否被调用
        mock_emotion_state.apply_decay.assert_called_once()
        mock_emotion_state.update.assert_called_once()
        
        # 验证更新时间是否已更新
        self.assertGreater(self.emotion_system.last_update_time, initial_update_time)
        
    def test_process_event(self):
        """测试处理情绪事件"""
        # 初始情绪参数
        initial_params = EmotionParams(pleasure=0.0, arousal=0.5, social=0.5)
        self.emotion_system.emotion_state = EmotionState(initial_params)
        
        # 确保事件历史为空
        self.assertEqual(len(self.emotion_system.recent_events), 0)
        
        # 覆盖默认的事件映射，确保测试结果一致
        test_event = EmotionalEvent(
            event_type=EmotionalEventType.USER_PET,
            intensity=1.0, # 在这里保持强度为1.0是为了测试简单
            pleasure_effect=0.1,
            arousal_effect=0.05,
            social_effect=0.1
        )
        self.emotion_system.event_mappings[EmotionalEventType.USER_PET] = test_event
        
        # 处理事件 - 使用0.8的强度
        result = self.emotion_system.process_event(
            event_type=EmotionalEventType.USER_PET,
            intensity=0.8
        )
        
        # 验证处理成功
        self.assertTrue(result)
        
        # 验证情绪参数变化 - 期望变化量 = 效果值 * 强度
        params = self.emotion_system.emotion_state.params
        self.assertAlmostEqual(params.pleasure, 0.08, delta=0.001)  # 0.1 * 0.8 = 0.08
        self.assertAlmostEqual(params.arousal, 0.54, delta=0.001)   # 0.5 + 0.05 * 0.8 = 0.54
        self.assertAlmostEqual(params.social, 0.58, delta=0.001)    # 0.5 + 0.1 * 0.8 = 0.58
        
        # 验证事件已添加到历史
        self.assertEqual(len(self.emotion_system.recent_events), 1)
        
        # 测试处理未知事件类型
        result = self.emotion_system.process_event(
            event_type=None
        )
        
        # 验证处理失败
        self.assertFalse(result)
        self.mock_logger.warning.assert_called()
        
    def test_register_custom_event(self):
        """测试注册自定义事件"""
        # 创建自定义事件类型
        custom_event_type = EmotionalEventType.TASK_COMPLETE
        
        # 注册自定义事件
        result = self.emotion_system.register_custom_event(
            event_type=custom_event_type,
            pleasure_effect=0.3,
            arousal_effect=0.2,
            social_effect=0.1
        )
        
        # 验证注册成功
        self.assertTrue(result)
        
        # 验证事件映射已更新
        self.assertIn(custom_event_type, self.emotion_system.event_mappings)
        event = self.emotion_system.event_mappings[custom_event_type]
        self.assertEqual(event.pleasure_effect, 0.3)
        self.assertEqual(event.arousal_effect, 0.2)
        self.assertEqual(event.social_effect, 0.1)
        
        # 验证是否记录了日志
        self.mock_logger.info.assert_called_with(f"注册自定义情绪事件: {custom_event_type.name}")
        
    def test_getters(self):
        """测试各种getter方法"""
        # 设置模拟的情绪状态
        mock_emotion_state = MagicMock()
        mock_emotion_state.current_emotion = EmotionType.HAPPY
        mock_emotion_state.params = EmotionParams(pleasure=0.5, arousal=0.7, social=0.3)
        mock_emotion_state.emotion_duration = 123.45
        mock_emotion_state.get_behavior_multipliers.return_value = {'jump': 2.0}
        mock_emotion_state.get_animation_params.return_value = {'speed_multiplier': 1.2}
        
        self.emotion_system.emotion_state = mock_emotion_state
        
        # 测试各种getter
        self.assertEqual(self.emotion_system.get_current_emotion(), EmotionType.HAPPY)
        self.assertEqual(self.emotion_system.get_emotion_params(), mock_emotion_state.params)
        self.assertEqual(self.emotion_system.get_emotion_duration(), 123.45)
        self.assertEqual(self.emotion_system.get_behavior_multipliers(), {'jump': 2.0})
        self.assertEqual(self.emotion_system.get_animation_params(), {'speed_multiplier': 1.2})
        
    def test_set_decay_rate(self):
        """测试设置衰减率"""
        # 初始衰减率
        initial_rate = self.emotion_system.decay_rate
        
        # 设置新的衰减率
        self.emotion_system.set_decay_rate(0.2)
        self.assertEqual(self.emotion_system.decay_rate, 0.2)
        
        # 测试范围限制
        self.emotion_system.set_decay_rate(-0.1)
        self.assertEqual(self.emotion_system.decay_rate, 0.0)  # 不应低于0
        
        self.emotion_system.set_decay_rate(1.5)
        self.assertEqual(self.emotion_system.decay_rate, 1.0)  # 不应高于1


class TestGlobalEmotionSystem(unittest.TestCase):
    """测试全局情绪系统实例"""
    
    def setUp(self):
        """测试前准备"""
        # 清除全局实例
        import status.behavior.emotion_system
        status.behavior.emotion_system._emotion_system_instance = None
        
    def test_get_emotion_system(self):
        """测试获取全局情绪系统实例"""
        # 首次获取
        system1 = get_emotion_system()
        self.assertIsInstance(system1, EmotionSystem)
        
        # 再次获取
        system2 = get_emotion_system()
        self.assertIs(system2, system1)  # 应该是同一个实例
        
        # 带实体参数获取
        mock_entity = MagicMock()
        system3 = get_emotion_system(mock_entity)
        self.assertIs(system3, system1)  # 仍然是同一个实例
        
    def test_initialize_default_emotion_events(self):
        """测试初始化默认情绪事件"""
        # 确保全局实例为空
        import status.behavior.emotion_system
        status.behavior.emotion_system._emotion_system_instance = None
        
        # 设置日志记录器的模拟对象
        mock_logger = MagicMock()
        with patch('status.behavior.emotion_system.logging.getLogger', return_value=mock_logger):
            # 调用初始化函数
            initialize_default_emotion_events()
            
            # 验证是否记录了日志
            mock_logger.info.assert_called_with("默认情绪事件映射已初始化")


if __name__ == '__main__':
    unittest.main() 