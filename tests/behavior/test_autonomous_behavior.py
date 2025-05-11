"""
---------------------------------------------------------------
File name:                  test_autonomous_behavior.py
Author:                     Ignorant-lu
Date created:               2025/04/04
Description:                自主行为生成系统的单元测试
----------------------------------------------------------------

Changed history:            
                            2025/04/04: 初始创建;
----
"""

import os
import time
import unittest
from unittest.mock import MagicMock, patch
from datetime import datetime

from status.behavior.autonomous_behavior import (
    AutonomousBehaviorGenerator,
    EntityUpdater,
    AutonomousBehaviorConfig,
    create_autonomous_behavior_generator
)


class MockEntity:
    """模拟实体类，用于测试"""
    
    def __init__(self):
        self.behavior_manager = MagicMock()
        self.state_machine = MagicMock()
        self.decision_maker = MagicMock()
        self.environment_sensor = MagicMock()
        
        # 设置状态机当前状态
        self.state_machine.current_state.name = 'idle'
        
        # 设置行为管理器get_current_behavior方法
        self.behavior_manager.get_current_behavior.return_value = None
        self.behavior_manager.execute_behavior.return_value = True


class TestAutonomousBehaviorGenerator(unittest.TestCase):
    """自主行为生成器测试"""
    
    def setUp(self):
        """测试前准备"""
        self.mock_entity = MockEntity()
        
        # 测试配置
        self.test_config = {
            'idle_timeout': 1.0,  # 缩短测试超时时间
            'max_history_size': 5,
            'random_factor': 0.1,  # 减少随机性
            'behavior_weights': {
                'idle': 10.0,
                'move_random': 5.0,
            },
            'state_behavior_map': {
                'idle': ['idle', 'move_random'],
                'moving': ['move_random'],
            }
        }
        
        self.generator = AutonomousBehaviorGenerator(self.mock_entity, self.test_config)

    def test_initialization(self):
        """测试初始化"""
        self.assertEqual(self.generator.entity, self.mock_entity)
        self.assertEqual(self.generator.idle_timeout, 1.0)
        self.assertEqual(self.generator.max_history_size, 5)
        self.assertEqual(set(self.generator.behavior_weights.keys()), {'idle', 'move_random'})
        self.assertEqual(set(self.generator.state_behavior_map.keys()), {'idle', 'moving'})
        self.assertEqual(len(self.generator.behavior_history), 0)

    def test_generate_behavior(self):
        """测试行为生成"""
        # 测试生成行为
        behavior_id, params = self.generator.generate_behavior()
        
        # 验证生成的行为是有效的
        self.assertIn(behavior_id, ['idle', 'move_random'])
        self.assertIsInstance(params, dict)
        
        # 测试10次行为生成，确保不会发生异常
        for _ in range(10):
            behavior_id, params = self.generator.generate_behavior()
            self.assertIn(behavior_id, ['idle', 'move_random'])

    def test_update_when_idle(self):
        """测试闲置状态下的更新"""
        # 设置为闲置状态
        self.mock_entity.state_machine.current_state.name = 'idle'
        
        # 模拟上次行为时间已超过闲置超时
        self.generator.last_behavior_time = time.time() - 2.0
        
        # 更新
        result = self.generator.update()
        
        # 验证是否生成并执行了新行为
        self.assertTrue(result)
        self.mock_entity.behavior_manager.execute_behavior.assert_called_once()
        
        # 检查历史记录是否已更新
        self.assertEqual(len(self.generator.behavior_history), 1)

    def test_update_when_busy(self):
        """测试正在执行行为时的更新"""
        # 设置正在执行非闲置行为
        self.mock_entity.behavior_manager.get_current_behavior.return_value = {'name': '跳跃'}
        
        # 更新
        result = self.generator.update()
        
        # 验证是否没有生成新行为
        self.assertFalse(result)
        self.mock_entity.behavior_manager.execute_behavior.assert_not_called()

    def test_update_within_timeout(self):
        """测试在闲置超时内的更新"""
        # 设置上次行为时间刚刚发生
        self.generator.last_behavior_time = time.time()
        
        # 更新
        result = self.generator.update()
        
        # 验证是否没有生成新行为
        self.assertFalse(result)
        self.mock_entity.behavior_manager.execute_behavior.assert_not_called()

    def test_history_decay(self):
        """测试历史记录衰减"""
        # 添加历史记录
        self.generator._update_behavior_history('idle', {})
        self.generator._update_behavior_history('move_random', {})
        
        # 计算衰减因子
        decay_idle = self.generator._calculate_history_decay('idle')
        decay_move = self.generator._calculate_history_decay('move_random')
        decay_unknown = self.generator._calculate_history_decay('unknown')
        
        # 验证：最近执行的行为（move_random）衰减更强，未执行过的行为没有衰减
        self.assertLess(decay_move, decay_idle)
        self.assertEqual(decay_unknown, 1.0)

    def test_environment_multiplier(self):
        """测试环境因素乘数"""
        # 模拟环境感知器返回窗口位置
        window_pos = MagicMock()
        window_pos.y.return_value = 10  # 靠近顶部
        window_pos.height.return_value = 100
        self.mock_entity.environment_sensor.get_window_position.return_value = window_pos
        self.mock_entity.environment_sensor.get_screen_boundaries.return_value = {'height': 1080}
        
        # 计算乘数
        multiplier = self.generator._calculate_environment_multiplier('fall')
        
        # 验证：靠近顶部时，下落行为乘数应该增加
        self.assertGreater(multiplier, 1.0)

    def test_time_multiplier(self):
        """测试时间因素乘数"""
        # 测试特定时间行为
        with patch('datetime.datetime') as mock_dt:
            # 模拟晚上时间
            mock_dt.now.return_value = datetime(2025, 4, 4, 23, 0)
            
            # 在测试前添加特定时间行为到生成器
            self.generator.special_time_behaviors = [
                {'condition': lambda: True,  # 总是满足条件
                 'behavior': 'sleep', 'weight_multiplier': 2.0}
            ]
            
            # 测试睡眠行为乘数
            multiplier = self.generator._calculate_time_multiplier('sleep')
            
            # 验证：条件满足时，睡眠行为乘数应该增加
            self.assertGreater(multiplier, 1.0)

    def test_weighted_random_choice(self):
        """测试加权随机选择"""
        # 测试权重字典
        weights = {'a': 10.0, 'b': 5.0, 'c': 1.0}
        
        # 执行多次选择，统计结果
        results = {}
        for _ in range(1000):
            choice = self.generator._weighted_random_choice(weights)
            results[choice] = results.get(choice, 0) + 1
            
        # 验证：权重高的选项应该出现得更频繁
        self.assertGreater(results.get('a', 0), results.get('b', 0))
        self.assertGreater(results.get('b', 0), results.get('c', 0))

    def test_generate_behavior_params(self):
        """测试生成行为参数"""
        # 测试移动行为
        params = self.generator._generate_behavior_params('move_random')
        self.assertIn('speed', params)
        self.assertTrue(50 <= params['speed'] <= 150)
        
        # 测试跳跃行为
        params = self.generator._generate_behavior_params('jump')
        self.assertIn('height', params)
        self.assertTrue(30 <= params['height'] <= 100)
        
        # 测试舞蹈行为
        params = self.generator._generate_behavior_params('dance')
        self.assertIn('duration', params)
        self.assertTrue(3.0 <= params['duration'] <= 8.0)

    def test_update_behavior_history(self):
        """测试更新行为历史记录"""
        # 填充历史记录
        for i in range(10):
            self.generator._update_behavior_history(f'behavior_{i}', {})
            
        # 验证历史记录大小不超过最大值
        self.assertLessEqual(len(self.generator.behavior_history), self.generator.max_history_size)
        
        # 验证最新的行为在最后
        self.assertEqual(self.generator.behavior_history[-1][0], 'behavior_9')

    def test_set_idle_timeout(self):
        """测试设置闲置超时时间"""
        # 设置新的闲置超时
        self.generator.set_idle_timeout(5.0)
        self.assertEqual(self.generator.idle_timeout, 5.0)
        
        # 测试设置负值
        self.generator.set_idle_timeout(-1.0)
        self.assertGreater(self.generator.idle_timeout, 0)  # 应该被限制为正值

    def test_get_behavior_probability(self):
        """测试获取行为生成概率"""
        # 获取概率
        prob_idle = self.generator.get_behavior_probability('idle')
        prob_move = self.generator.get_behavior_probability('move_random')
        prob_unknown = self.generator.get_behavior_probability('unknown')
        
        # 验证：配置的权重较高的行为概率应该更高，未知行为概率为0
        self.assertGreater(prob_idle, prob_move)
        self.assertEqual(prob_unknown, 0.0)
        
        # 验证概率总和为1
        self.assertAlmostEqual(prob_idle + prob_move, 1.0)


class TestEntityUpdater(unittest.TestCase):
    """实体更新器测试"""
    
    def setUp(self):
        """测试前准备"""
        self.mock_entity = MockEntity()
        self.entity_updater = EntityUpdater(self.mock_entity)

    def test_initialization(self):
        """测试初始化"""
        self.assertEqual(self.entity_updater.entity, self.mock_entity)
        self.assertIsNone(self.entity_updater.autonomous_behavior_generator)

    def test_update(self):
        """测试更新方法"""
        # 设置自主行为生成器
        self.entity_updater.autonomous_behavior_generator = MagicMock()
        
        # 执行更新
        self.entity_updater.update(0.1)
        
        # 验证各系统是否被更新
        self.mock_entity.behavior_manager.update.assert_called_once_with(0.1)
        self.mock_entity.state_machine.update.assert_called_once()
        self.mock_entity.decision_maker.make_decision.assert_called_once()
        self.entity_updater.autonomous_behavior_generator.update.assert_called_once()


class TestAutonomousBehaviorConfig(unittest.TestCase):
    """自主行为生成器配置测试"""
    
    def test_get_default_config(self):
        """测试获取默认配置"""
        config = AutonomousBehaviorConfig.get_default_config()
        
        # 验证默认配置的关键字段
        self.assertIn('idle_timeout', config)
        self.assertIn('behavior_weights', config)
        self.assertIn('state_behavior_map', config)
        self.assertIn('special_time_behaviors', config)

    def test_save_and_load_config(self):
        """测试保存和加载配置"""
        # 创建测试配置
        test_config = {
            'idle_timeout': 5.0,
            'max_history_size': 5,
            'behavior_weights': {
                'test1': 1.0,
                'test2': 2.0
            }
        }
        
        # 测试文件路径
        test_file = 'test_config.json'
        
        try:
            # 保存配置
            result = AutonomousBehaviorConfig.save_to_file(test_config, test_file)
            self.assertTrue(result)
            self.assertTrue(os.path.exists(test_file))
            
            # 加载配置
            loaded_config = AutonomousBehaviorConfig.load_from_file(test_file)
            
            # 验证加载的配置
            self.assertEqual(loaded_config['idle_timeout'], 5.0)
            self.assertEqual(loaded_config['max_history_size'], 5)
            self.assertEqual(loaded_config['behavior_weights']['test1'], 1.0)
            self.assertEqual(loaded_config['behavior_weights']['test2'], 2.0)
            
        finally:
            # 清理测试文件
            if os.path.exists(test_file):
                os.remove(test_file)


class TestCreateAutonomousBehaviorGenerator(unittest.TestCase):
    """测试创建自主行为生成器函数"""
    
    def test_create_generator(self):
        """测试创建生成器"""
        mock_entity = MockEntity()
        
        # 创建生成器
        generator = create_autonomous_behavior_generator(mock_entity)
        
        # 验证生成器是否正确创建
        self.assertIsInstance(generator, AutonomousBehaviorGenerator)
        self.assertEqual(generator.entity, mock_entity)
        
        # 测试使用配置文件创建
        with patch('status.behavior.autonomous_behavior.AutonomousBehaviorConfig.load_from_file') as mock_load:
            mock_load.return_value = {'idle_timeout': 20.0}
            
            generator = create_autonomous_behavior_generator(mock_entity, 'config.json')
            
            # 验证是否尝试加载配置文件
            mock_load.assert_called_once_with('config.json')
            self.assertEqual(generator.idle_timeout, 20.0)


if __name__ == '__main__':
    unittest.main() 