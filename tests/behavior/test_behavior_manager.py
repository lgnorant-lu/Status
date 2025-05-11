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
                            2025/05/17: 修复缩进错误;
----
"""

import unittest
from unittest.mock import Mock, patch, MagicMock

# 导入行为管理器
from status.behavior.behavior_manager import BehaviorManager
from status.behavior.basic_behaviors import BasicBehavior, BehaviorType

# 使用BasicBehavior而不是不存在的Behavior类
class TestBehavior(unittest.TestCase):
    """测试行为基类"""

    def setUp(self):
        # 创建一个具体行为类用于测试
        class ConcreteBehavior(BasicBehavior):
            # __init__ 只接受 BasicBehavior.__init__ 接受的参数
            def __init__(self, name, duration=0.0, loop=False, behavior_type=BehaviorType.CUSTOM):
                super().__init__(name, duration=duration, loop=loop, behavior_type=behavior_type)
                # entity 和 params 将在 start 方法中处理
                self.entity = None # 初始化为 None
                self._update_count = 0
                self._completed = False
                self.completion_callbacks = [] # 初始化回调列表
                # is_running 和 completion_callbacks 由 BasicBehavior 或后续方法处理
                # self.is_running = False
                # self.completion_callbacks = []
            
            def start(self, params=None):
                # 调用父类的 start 来处理 params 和基本启动逻辑
                super().start(params)
                # 从 params 中获取 entity
                self.entity = self.params.get('entity') if self.params else None

                if self.entity: # 确保 entity 存在才设置属性
                    self.entity.on_start_called = True
                # is_running 会由 super().start(params) 设置
                
            def update(self, dt):
                if not self.is_running:
                    return True # 如果未运行，则认为已完成（或不处理）
                if not self.entity:
                    # 如果没有 entity 但行为在运行，这是一个潜在问题，但为了测试简单，
                    # 我们可能允许它继续，或者根据行为设计决定是否应该完成/错误。
                    # 这里我们假设它不应该立即完成，除非 BasicBehavior.update 处理它。
                    pass

                if self.entity: # 只在 entity 存在时更新 mock 属性
                    self.entity.on_update_called = True
                    self.entity.update_delta = dt
                
                self._update_count += 1
                if not self._completed and self._update_count >= 5: # 仅在首次达到条件时标记完成并调用回调
                    self._completed = True
                    self.on_completed() # 完成时调用回调
                
                # BasicBehavior.update 处理 duration/loop，并返回是否完成。
                # 如果我们想让 ConcreteBehavior 的完成逻辑优先，可以这样做：
                if self._completed and not self.loop: # 如果我们的逻辑认为已完成且不循环
                    self.is_running = False # 确保停止运行
                    return True # 报告完成
                
                # 否则，让 BasicBehavior.update 决定（例如，如果 duration 过期了）
                # 但我们的 ConcreteBehavior 并没有使用 duration。
                # 为了这个测试类的目的，我们主要关心 _update_count 逻辑。
                # 如果 self.duration > 0，super().update(dt) 可能会在 _update_count < 5 之前返回 True。
                # 为了使 ConcreteBehavior 的完成逻辑 (_update_count) 独立，我们不调用 super().update()
                # 或者，我们需要确保 ConcreteBehavior 的 duration 设置得足够长。
                # 目前这个测试类主要测试自定义完成逻辑。
                return self._completed
                
            def stop(self):
                if self.entity: # 确保 entity 存在
                    self.entity.on_stop_called = True
                # 如果停止时行为未完成，根据需要决定是否触发 on_completed
                # current_is_running = self.is_running # 检查 super().stop() 之前的状态
                super().stop()
                # if current_is_running and not self._completed: # 如果正在运行时被外部停止且未完成
                #    self._completed = True # 标记为完成
                #    self.on_completed() # 也可以触发回调
            
            def is_completed(self):
                return self._completed
            
            def add_completion_callback(self, callback):
                self.completion_callbacks.append(callback)
                
            def on_completed(self):
                for callback in self.completion_callbacks:
                    callback()
                
        self.behavior_class = ConcreteBehavior
        self.entity = Mock() # 这是测试中使用的模拟 entity
        # 实例化时不再传递 entity 或 params
        self.behavior = self.behavior_class("test_behavior", duration=0.0, loop=False)
        # entity 和 params 将在调用 start 时传递
        
    def test_init(self):
        """测试行为初始化"""
        self.assertEqual(self.behavior.name, "test_behavior")
        # self.assertEqual(self.behavior.params, {"param1": "value1"}) # params 在 init 时应为空
        self.assertEqual(self.behavior.params, {})
        self.assertFalse(self.behavior.is_running)
        # self.assertEqual(len(self.behavior.completion_callbacks), 0) # completion_callbacks 已移除
        
    def test_start_method(self):
        """测试start方法"""
        start_params = {'entity': self.entity, 'param1': 'value1'}
        self.behavior.start(params=start_params)
        self.assertTrue(self.entity.on_start_called)
        self.assertTrue(self.behavior.is_running)
        self.assertEqual(self.behavior.params, start_params) # 验证 params 被正确设置
        
    def test_update_method(self):
        """测试update方法"""
        # 需要先 start 并提供 entity
        self.behavior.start(params={'entity': self.entity})
        delta_time = 0.016
        self.behavior.update(delta_time)
        self.assertTrue(self.entity.on_update_called)
        self.assertEqual(self.entity.update_delta, delta_time)
        
    def test_stop_method(self):
        """测试stop方法"""
        self.behavior.start(params={'entity': self.entity}) # 需要 entity
        self.behavior.stop()
        self.assertTrue(self.entity.on_stop_called)
        self.assertFalse(self.behavior.is_running)
        
    def test_completion(self):
        """测试行为完成检测"""
        self.behavior.start(params={'entity': self.entity}) # 需要 entity
        # 初始状态应该是未完成
        self.assertFalse(self.behavior.is_completed())
        
        # 更新5次后应该完成
        delta_time = 0.016
        for _ in range(5):
            self.behavior.update(delta_time)
            
        self.assertTrue(self.behavior.is_completed())
        
    def test_completion_callback(self):
        """测试完成回调"""
        callback1 = Mock()
        callback2 = Mock()

        self.behavior.add_completion_callback(callback1)
        self.behavior.add_completion_callback(callback2)
        
        # 行为通过 update 完成
        self.behavior.start(params={'entity': self.entity}) 
        for _ in range(5):
            self.behavior.update(0.016)
        
        # 验证回调被调用
        callback1.assert_called_once()
        callback2.assert_called_once()


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


if __name__ == '__main__':
    unittest.main() 