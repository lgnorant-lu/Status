"""
---------------------------------------------------------------
File name:                  test_system_state_adapter.py
Author:                     Ignorant-lu
Date created:               2025/05/13
Description:                测试系统状态适配器
----------------------------------------------------------------

Changed history:            
                            2025/05/13: 初始创建;
----
"""

import unittest
from unittest.mock import MagicMock, patch

from status.behavior.system_state_adapter import SystemStateAdapter
from status.behavior.pet_state_machine import PetStateMachine
from status.behavior.pet_state import PetState
from status.core.events import SystemStatsUpdatedEvent, EventType

class TestSystemStateAdapter(unittest.TestCase):
    """测试系统状态适配器"""

    def setUp(self):
        """每个测试方法执行前设置"""
        # 模拟宠物状态机
        self.mock_state_machine = MagicMock(spec=PetStateMachine)
        self.mock_state_machine.update.return_value = False
        self.mock_state_machine.get_state.return_value = PetState.IDLE
        self.mock_state_machine.cpu_threshold = 30.0
        self.mock_state_machine.memory_threshold = 80.0
        
        # 模拟事件系统 (EventSystem)
        self.event_system_mock_returned_by_get_instance = MagicMock()
        self.get_instance_patcher = patch('status.behavior.system_state_adapter.EventSystem.get_instance', 
                                          return_value=self.event_system_mock_returned_by_get_instance)
        self.mock_get_instance_call = self.get_instance_patcher.start() # This mock is for the get_instance call itself.

        # 模拟日志记录器
        self.logger_patcher = patch('status.behavior.system_state_adapter.logging.getLogger')
        self.mock_logger_get_logger_func = self.logger_patcher.start() # This is the mock for the getLogger function
        self.mock_logger_instance_for_adapter = MagicMock() # This is the logger instance we want the adapter to use
        self.mock_logger_get_logger_func.return_value = self.mock_logger_instance_for_adapter
        
        # 创建被测试对象 (事件系统和日志记录器已被mock)
        # SystemStateAdapter.__init__ will call the patched logging.getLogger 
        # and its self.logger should become self.mock_logger_instance_for_adapter.
        self.adapter = SystemStateAdapter(self.mock_state_machine)
        # self.adapter.logger = self.mock_logger # This line is redundant and removed
        
        # 重置mock对象，清除构造函数中可能的调用
        self.mock_logger_instance_for_adapter.reset_mock() # Reset the logger instance used by the adapter
        # self.mock_state_machine.reset_mock() # Already done by MagicMock spec or individually set
        # self.event_system_mock_returned_by_get_instance.reset_mock() # Reset if needed, or check specific calls

    def tearDown(self):
        """每个测试方法执行后清理"""
        self.get_instance_patcher.stop() # Ensure patches are stopped
        self.logger_patcher.stop()

    def test_initialization(self):
        """测试适配器能否正确初始化并注册事件处理器"""
        # mock_logger = MagicMock() # No longer needed here
        # mock_get_logger.return_value = mock_logger # No longer needed here

        # Diagnostic prints and assertion
        print(f"DEBUG: self.adapter.event_system is {self.adapter.event_system}")
        print(f"DEBUG: Expected mock (self.event_system_mock_returned_by_get_instance) is {self.event_system_mock_returned_by_get_instance}")
        self.assertIs(self.adapter.event_system, self.event_system_mock_returned_by_get_instance, 
                      "Adapter's event_system should be the mock returned by get_instance during __init__")

        # 调用初始化 (现在是 activate)
        result = self.adapter.activate()

        # 断言
        self.assertTrue(result, "初始化应该成功")
        
        # 检查 EventSystem.get_instance 是否在 __init__ 中被调用过 (由 patch 对象 self.mock_get_instance_call 记录)
        # 注意：如果 __init__ 和 _initialize 都调用，这里会是 call_count == 2 (如果 _initialize 中的调用也被 patch 的话)
        # 但我们修改了 _initialize 不再调用 get_instance，所以 __init__ 中的调用应该是唯一的一次。
        self.mock_get_instance_call.assert_called_once() 
        
        # 检查 self.adapter.event_system (即 self.event_system_mock_returned_by_get_instance) 上的 register_handler 是否被调用
        self.event_system_mock_returned_by_get_instance.register_handler.assert_called_once_with(
            EventType.SYSTEM_STATS_UPDATED,
            self.adapter._on_system_stats_updated
        )
        # 检查日志
        called_infos = [call_args[0] for call_args, _ in self.mock_logger_instance_for_adapter.info.call_args_list]
        self.assertIn("系统状态适配器初始化完成", called_infos, "初始化完成的日志消息未找到")

    def test_handle_stats_event(self):
        """测试处理系统统计数据事件"""
        # 创建模拟事件
        event = SystemStatsUpdatedEvent(stats_data={
            "cpu_usage": 50.0,
            "memory_usage": 60.0
        })
        
        # 调用事件处理方法
        self.adapter._on_system_stats_updated(event)
        
        # 验证是否调用了状态机的update方法
        self.mock_state_machine.update.assert_called_once_with(
            cpu_usage=50.0, 
            memory_usage=60.0,
            gpu_usage=0.0,      # 适配器会使用默认值
            disk_usage=0.0,     # 适配器会使用默认值
            network_usage=0.0   # 适配器会使用默认值
        )

    def test_handle_stats_event_invalid_data(self):
        """测试处理无效的系统统计数据事件"""
        # 创建包含无效数据的模拟事件
        event = SystemStatsUpdatedEvent(stats_data={
            "cpu_usage": "invalid",  # 无效类型
            "memory_usage": 60.0
        })
        
        # 调用事件处理方法
        self.adapter._on_system_stats_updated(event)
        
        # 验证是否记录了警告日志
        self.mock_logger_instance_for_adapter.warning.assert_called_once()
        
        # 验证没有调用状态机的update方法
        self.mock_state_machine.update.assert_not_called()

    def test_handle_state_change(self):
        """测试状态变化处理"""
        # 模拟状态机返回状态已改变
        self.mock_state_machine.update.return_value = True
        self.mock_state_machine.get_state.return_value = PetState.BUSY
        
        # 创建模拟事件
        event = SystemStatsUpdatedEvent(stats_data={
            "cpu_usage": 70.0,
            "memory_usage": 50.0
        })
        
        # 调用事件处理方法
        self.adapter._on_system_stats_updated(event)
        
        # 验证是否获取了当前状态
        self.mock_state_machine.get_state.assert_called_once()
        
        # 验证是否记录了状态变化日志
        self.mock_logger_instance_for_adapter.info.assert_called() # 首先检查 info 是否至少被调用过一次
        expected_log_message = "宠物状态更新为: MODERATE_LOAD (CPU: 70.0%, Memory: 50.0%)"
        # print(f"DEBUG: Actual logger info calls: {self.mock_logger.info.call_args_list}") # Temporary debug
        self.mock_logger_instance_for_adapter.info.assert_called_with(expected_log_message)

    def test_set_thresholds(self):
        """测试设置阈值"""
        # 调用设置阈值方法
        self.adapter.set_thresholds(cpu_threshold=40.0, memory_threshold=70.0)
        
        # 验证是否修改了状态机的阈值
        self.assertEqual(self.mock_state_machine.cpu_threshold, 40.0)
        self.assertEqual(self.mock_state_machine.memory_threshold, 70.0)
        
        # 验证是否记录了日志
        self.assertEqual(self.mock_logger_instance_for_adapter.info.call_count, 2)

if __name__ == '__main__':
    unittest.main() 