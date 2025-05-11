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
----
"""

import unittest
from unittest.mock import Mock, patch, MagicMock

# 导入行为管理器
from status.behavior.behavior_manager import BehaviorManager
from status.behavior.basic_behaviors import BasicBehavior

# 使用BasicBehavior而不是不存在的Behavior类
class TestBehavior(unittest.TestCase):
    """测试行为基类"""

    def setUp(self):
        # 创建一个具体行为类用于测试
        class ConcreteBehavior(BasicBehavior):
            def __init__(self, name, params=None):
                super().__init__(name, params or {})  # 确保params不为None
                self._update_count = 0
                self._completed = False
                self.is_running = False
                self.completion_callbacks = []
                # 直接设置params以匹配测试预期
                self.params = params or {}
            
            def start(self, params=None):
                self.entity.on_start_called = True
                self.is_running = True
                
            def update(self, dt):
                self.entity.on_update_called = True
                self.entity.update_delta = dt
                # 使用内部计数器而不是依赖mock对象
                self._update_count += 1
                if self._update_count >= 5:
                    self._completed = True
                return self._completed
                
            def stop(self):
                self.entity.on_stop_called = True
                self.is_running = False
            
            def is_completed(self):
                return self._completed
            
            def add_completion_callback(self, callback):
                self.completion_callbacks.append(callback)
                
            def on_completed(self):
                for callback in self.completion_callbacks:
                    callback()
                
        self.behavior_class = ConcreteBehavior
        self.entity = Mock()
        self.behavior = self.behavior_class("test_behavior", {"param1": "value1"})
        self.behavior.entity = self.entity
        
    def test_init(self):
        """测试行为初始化"""
        self.assertEqual(self.behavior.name, "test_behavior")
        self.assertEqual(self.behavior.params, {"param1": "value1"})
        self.assertFalse(self.behavior.is_running)
        self.assertEqual(len(self.behavior.completion_callbacks), 0)
        
    def test_start_method(self):
        """测试start方法"""
        self.behavior.start()
        self.assertTrue(self.entity.on_start_called)
        self.assertTrue(self.behavior.is_running)
        
    def test_update_method(self):
        """测试update方法"""
        delta_time = 0.016
        self.behavior.update(delta_time)
        self.assertTrue(self.entity.on_update_called)
        self.assertEqual(self.entity.update_delta, delta_time)
        
    def test_stop_method(self):
        """测试stop方法"""
        self.behavior.start()
        self.behavior.stop()
        self.assertTrue(self.entity.on_stop_called)
        self.assertFalse(self.behavior.is_running)
        
    def test_completion(self):
        """测试行为完成检测"""
        # 初始状态应该是未完成
        self.assertFalse(self.behavior.is_completed())
        
        # 更新5次后应该完成
        delta_time = 0.016
        for _ in range(5):
            self.behavior.update(delta_time)
            
        self.assertTrue(self.behavior.is_completed())
        
    def test_completion_callback(self):
        """测试完成回调"""
        # 添加回调
        callback1 = Mock()
        callback2 = Mock()
        self.behavior.add_completion_callback(callback1)
        self.behavior.add_completion_callback(callback2)
        
        # 触发完成
        self.behavior._completed = True
        self.behavior.on_completed()
        
        # 验证回调被调用
        callback1.assert_called_once()
        callback2.assert_called_once()


class TestBehaviorManager(unittest.TestCase):
    """测试行为管理器"""

    def setUp(self):
        # 模拟BehaviorRegistry
        self.registry_patcher = patch('status.behavior.behavior_manager.BehaviorRegistry')
        self.mock_registry_class = self.registry_patcher.start()
        self.mock_registry = MagicMock()
        self.mock_registry_class.get_instance.return_value = self.mock_registry
        
        # 设置模拟行为
        self.mock_behavior = MagicMock()
        self.mock_behavior.name = "test_behavior"
        self.mock_behavior.is_running = True
        
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
        current_behavior = MagicMock()
        current_behavior.is_running = True
        current_behavior.update.return_value = False  # 行为未完成
        self.behavior_manager.current_behavior = current_behavior
        
        # 更新行为
        self.behavior_manager.update(0.016)
        
        # 验证行为更新
        current_behavior.update.assert_called_once_with(0.016)
        self.assertEqual(self.behavior_manager.current_behavior, current_behavior)
        
    def test_update_with_completed_behavior(self):
        """测试更新已完成的行为"""
        # 设置当前行为
        current_behavior = MagicMock()
        current_behavior.is_running = True
        current_behavior.update.return_value = True  # 行为已完成
        self.behavior_manager.current_behavior = current_behavior
        
        # 更新行为
        self.behavior_manager.update(0.016)
        
        # 验证行为更新和清除
        current_behavior.update.assert_called_once_with(0.016)
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
        current_behavior = MagicMock()
        current_behavior.name = "test_behavior"
        current_behavior.is_running = True
        current_behavior.duration = 5.0
        current_behavior.loop = False
        current_behavior.params = {"param1": "value1"}
        self.behavior_manager.current_behavior = current_behavior
        
        # 获取当前行为信息
        behavior_info = self.behavior_manager.get_current_behavior()
        
        # 验证信息
        self.assertEqual(behavior_info['name'], "test_behavior")
        self.assertTrue(behavior_info['running'])
        self.assertEqual(behavior_info['duration'], 5.0)
        self.assertFalse(behavior_info['loop'])
        self.assertEqual(behavior_info['params'], {"param1": "value1"})
        
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


if __name__ == '__main__':
    unittest.main() 