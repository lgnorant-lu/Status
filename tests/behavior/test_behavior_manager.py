"""
---------------------------------------------------------------
File name:                  test_behavior_manager.py
Author:                     Ignorant-lu
Date created:               2025/04/04
Description:                行为管理器单元测试
----------------------------------------------------------------

Changed history:            
                            2025/04/04: 初始创建;
                            2025/04/04: 修复导入问题;
                            2025/05/13: 修复缩进错误;
                            2025/05/16: 修复行为历史记录上限问题;
----
"""

import unittest
from unittest.mock import Mock, patch, MagicMock

# 导入行为管理器
from status.behavior.behavior_manager import BehaviorManager
from status.behavior.basic_behaviors import BasicBehavior, BehaviorType # BasicBehavior is used for spec
# from status.behavior.behavior_manager import MAX_HISTORY_SIZE # MAX_HISTORY_SIZE is not defined in module

class TestBehaviorManager(unittest.TestCase):
    """测试行为管理器"""

    def setUp(self):
        # 模拟BehaviorRegistry
        self.registry_patcher = patch('status.behavior.basic_behaviors.BehaviorRegistry')
        self.mock_registry_class = self.registry_patcher.start()
        self.mock_registry = MagicMock()
        self.mock_registry_class.get_instance.return_value = self.mock_registry
        
        # 设置模拟行为
        self.mock_behavior = MagicMock()
        self.mock_behavior.name = "test_behavior"
        self.mock_behavior.is_running = True # Assume it starts running
        # Add the public update method to the mock, which BehaviorManager will call
        self.mock_behavior.update = MagicMock() 
        
        # 配置行为创建
        self.mock_registry.create.return_value = self.mock_behavior
        
        # 创建测试实体
        self.entity = Mock()
        
        # 创建BehaviorManager实例
        self.behavior_manager = BehaviorManager(self.entity)
        
    def tearDown(self):
        self.registry_patcher.stop()
        
    def test_initialization(self):
        """测试初始化"""
        self.assertEqual(self.behavior_manager.entity, self.entity)
        self.assertIsNone(self.behavior_manager.current_behavior)
        self.assertEqual(len(self.behavior_manager.behavior_history), 0)
        
    def test_execute_behavior(self):
        """测试执行行为"""
        # 执行行为
        result = self.behavior_manager.execute_behavior("test_behavior", {"param1": "value1"})
        
        # 验证行为注册表的使用
        self.mock_registry.create.assert_called_once_with("test_behavior", param1="value1")
        
        # 验证行为启动
        self.mock_behavior.start.assert_called_once_with({"param1": "value1"})
        
        # 验证结果
        self.assertTrue(result)
        self.assertEqual(self.behavior_manager.current_behavior, self.mock_behavior)
        self.assertEqual(len(self.behavior_manager.behavior_history), 1)
        self.assertEqual(self.behavior_manager.behavior_history[0]['behavior_id'], "test_behavior")
        
    def test_execute_behavior_with_current_behavior(self):
        """测试执行行为时已有当前行为"""
        # 设置当前行为
        current_behavior = MagicMock()
        self.behavior_manager.current_behavior = current_behavior
        
        # 执行新行为
        result = self.behavior_manager.execute_behavior("test_behavior", {"param1": "value1"})
        
        # 验证旧行为停止，新行为启动
        current_behavior.stop.assert_called_once()
        self.mock_behavior.start.assert_called_once_with({"param1": "value1"})
        
        # 验证结果
        self.assertTrue(result)
        self.assertEqual(self.behavior_manager.current_behavior, self.mock_behavior)
        
    def test_execute_behavior_failure(self):
        """测试执行行为失败"""
        # 配置注册表抛出异常
        self.mock_registry.create.side_effect = ValueError("行为不存在")
        
        # 执行不存在的行为
        result = self.behavior_manager.execute_behavior("nonexistent_behavior")
        
        # 验证结果
        self.assertFalse(result)
        self.assertIsNone(self.behavior_manager.current_behavior)
        
    def test_update_with_incomplete_behavior(self):
        """测试更新未完成的行为"""
        # 设置当前行为
        self.behavior_manager.current_behavior = self.mock_behavior
        self.mock_behavior.is_running = True # Ensure it's marked as running
        
        # 配置模拟行为的 update 方法返回 False (未完成)
        self.mock_behavior.update.return_value = False 
        
        # 更新行为管理器
        dt = 0.1
        self.behavior_manager.update(dt)
        
        # 验证行为的 update 方法被调用
        self.mock_behavior.update.assert_called_once_with(dt)
        
        # 验证当前行为未改变
        self.assertEqual(self.behavior_manager.current_behavior, self.mock_behavior)
        
    def test_update_with_completed_behavior(self):
        """测试更新已完成的行为"""
        # 设置当前行为
        self.behavior_manager.current_behavior = self.mock_behavior
        self.mock_behavior.is_running = True # Ensure it's marked as running

        # 配置模拟行为的 update 方法返回 True (已完成)
        self.mock_behavior.update.return_value = True
        
        # 更新行为管理器
        dt = 0.1
        self.behavior_manager.update(dt)
        
        # 验证行为的 update 方法被调用
        self.mock_behavior.update.assert_called_once_with(dt)
        
        # 验证当前行为已设为None
        self.assertIsNone(self.behavior_manager.current_behavior)
        
    def test_stop_current_behavior(self):
        """测试停止当前行为"""
        # 设置当前行为
        current_behavior = MagicMock()
        self.behavior_manager.current_behavior = current_behavior
        
        # 停止行为
        result = self.behavior_manager.stop_current_behavior()
        
        # 验证行为停止
        current_behavior.stop.assert_called_once()
        self.assertIsNone(self.behavior_manager.current_behavior)
        self.assertTrue(result)
        
    def test_stop_current_behavior_without_behavior(self):
        """测试在没有当前行为时停止"""
        # 确保没有当前行为
        self.behavior_manager.current_behavior = None
        
        # 停止行为
        result = self.behavior_manager.stop_current_behavior()
        
        # 验证结果
        self.assertFalse(result)
        
    def test_get_current_behavior(self):
        """测试获取当前行为信息"""
        # 设置当前行为
        mock_behavior = MagicMock()
        mock_behavior.name = "current_test_behavior"
        mock_behavior.is_running = True
        mock_behavior.duration = 10.0  # 显式设置 duration
        mock_behavior.loop = False     # 显式设置 loop
        mock_behavior.params = {"key": "value"}
        self.behavior_manager.current_behavior = mock_behavior
        
        behavior_info = self.behavior_manager.get_current_behavior()
        
        self.assertIsNotNone(behavior_info)
        if behavior_info: # 添加显式检查以帮助Linter并增强代码健壮性
            self.assertEqual(behavior_info['name'], "current_test_behavior")
            self.assertTrue(behavior_info['running'])
            self.assertEqual(behavior_info['duration'], 10.0)
            self.assertEqual(behavior_info['params'], {"key": "value"})
            if 'loop' in behavior_info: 
                self.assertEqual(behavior_info['loop'], False)
        
    def test_get_current_behavior_without_behavior(self):
        """测试在没有当前行为时获取行为信息"""
        # 确保没有当前行为
        self.behavior_manager.current_behavior = None
        
        # 获取当前行为信息
        behavior_info = self.behavior_manager.get_current_behavior()
        
        # 验证结果
        self.assertIsNone(behavior_info)
        
    def test_get_available_behaviors(self):
        """测试获取可用行为列表"""
        # 配置注册表行为列表
        self.mock_registry.behaviors = {"behavior1": None, "behavior2": None}
        
        # 获取可用行为
        behaviors = self.behavior_manager.get_available_behaviors()
        
        # 验证结果
        self.assertEqual(set(behaviors), {"behavior1", "behavior2"})

    def test_behavior_history_limit(self):
        """测试行为历史记录达到上限时的处理"""
        # The limit is hardcoded as 20 in BehaviorManager.execute_behavior
        hardcoded_max_history = 20
        
        # 执行 max_history + 5 个行为
        for i in range(hardcoded_max_history + 5):
            behavior_id = f"test_behavior_{i}"
            # 每次都创建一个新的 mock behavior 实例，因为 manager 会 stop 旧的
            mock_b = MagicMock(spec=BasicBehavior)
            mock_b.name = behavior_id
            mock_b.is_running = True
            mock_b.update = MagicMock(return_value=True) # Assume it completes immediately for history logging
            self.mock_registry.create.return_value = mock_b
            
            self.behavior_manager.execute_behavior(behavior_id, {"index": i})
            # 为了让历史记录有意义，我们假设行为会立即完成，这样manager就会记录它
            # BehaviorManager.update() 实际上是在行为完成后，并且 current_behavior is None 时，才会记录历史。
            # 在 execute_behavior 内部，如果旧行为存在，会stop它，然后start新行为。
            # 历史记录是在 execute_behavior 成功启动新行为后立即添加的。

        self.assertEqual(len(self.behavior_manager.behavior_history), hardcoded_max_history)
        # 验证历史记录中的最后一个行为是正确的（最新的）
        self.assertEqual(self.behavior_manager.behavior_history[-1]['behavior_id'], f"test_behavior_{hardcoded_max_history + 4}")
        # 验证历史记录中的第一个行为是正确的（第6个被执行的行为，因为前5个被挤掉了）
        self.assertEqual(self.behavior_manager.behavior_history[0]['behavior_id'], f"test_behavior_5")

    def test_execute_behavior_start_fails(self):
        """测试当行为的 start() 方法失败时的处理"""
        # 配置 mock_behavior.start() 以引发通用异常
        self.mock_behavior.start.side_effect = Exception("Start failed miserably")
        # registry.create 仍然成功返回这个 mock_behavior
        self.mock_registry.create.return_value = self.mock_behavior

        result = self.behavior_manager.execute_behavior("test_behavior_start_fails")

        self.assertFalse(result, "execute_behavior should return False if start() fails.")
        # 验证 current_behavior 在 start() 失败后被清除了
        self.assertIsNone(self.behavior_manager.current_behavior, 
                          "current_behavior should be None if start() throws after creation.")
        # 可以选择性地检查日志记录，但这需要更复杂的模拟设置
        # self.behavior_manager.logger.error.assert_called_with("执行行为时发生未知错误: Start failed miserably")


if __name__ == '__main__':
    unittest.main() 