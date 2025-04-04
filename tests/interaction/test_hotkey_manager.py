"""
---------------------------------------------------------------
File name:                  test_hotkey_manager.py
Author:                     Ignorant-lu
Date created:               2025/04/03
Description:                桌宠热键管理器测试
----------------------------------------------------------------

Changed history:            
                            2025/04/03: 初始创建;
----
"""

import unittest
from unittest.mock import Mock, patch, call
import sys
import threading
import time

from status.interaction.hotkey import HotkeyManager
from status.interaction.interaction_event import InteractionEvent, InteractionEventType


class TestHotkeyManager(unittest.TestCase):
    """测试热键管理器类"""
    
    def setUp(self):
        """每个测试前初始化"""
        # 模拟事件管理器
        self.mock_event_manager = Mock()
        
        # 创建热键管理器并模拟其平台处理器初始化
        with patch('status.interaction.hotkey.EventManager.get_instance', return_value=self.mock_event_manager):
            with patch.object(HotkeyManager, '_init_platform_handler'):
                self.hotkey_manager = HotkeyManager()
                # 手动设置模拟的平台处理器
                self.hotkey_manager.platform_handler = Mock()
                # 初始化信号
                self.hotkey_manager.hotkey_triggered_signal = Mock()
    
    def test_start_listener(self):
        """测试启动热键监听器"""
        # 模拟平台处理器启动方法
        self.hotkey_manager.platform_handler.start.return_value = True
        
        # 启动监听器
        result = self.hotkey_manager.start()
        
        # 验证结果
        self.assertTrue(result)
        self.hotkey_manager.platform_handler.start.assert_called_once()
        
        # 验证线程启动
        self.assertTrue(self.hotkey_manager.running)
        self.assertIsNotNone(self.hotkey_manager.listener_thread)
    
    def test_start_listener_fails(self):
        """测试启动热键监听器失败的情况"""
        # 清除平台处理器，模拟未初始化的情况
        self.hotkey_manager.platform_handler = None
        
        # 启动监听器
        result = self.hotkey_manager.start()
        
        # 验证结果应该失败
        self.assertFalse(result)
        
        # 验证线程未启动
        self.assertFalse(self.hotkey_manager.running)
        self.assertIsNone(self.hotkey_manager.listener_thread)
    
    def test_stop_listener(self):
        """测试停止热键监听器"""
        # 先设置运行状态
        self.hotkey_manager.running = True
        self.hotkey_manager.listener_thread = Mock()
        
        # 停止监听器
        self.hotkey_manager.stop()
        
        # 验证结果
        self.assertFalse(self.hotkey_manager.running)
        self.hotkey_manager.platform_handler.stop.assert_called_once()
    
    def test_register_hotkey(self):
        """测试注册热键"""
        # 定义测试热键
        key_combo = "Ctrl+Alt+T"
        callback = Mock()
        
        # 模拟平台处理器的注册方法返回成功
        self.hotkey_manager.platform_handler.register_hotkey.return_value = True
        
        # 注册热键
        result = self.hotkey_manager.register_hotkey(key_combo, callback)
        
        # 验证结果
        self.assertTrue(result)
        self.hotkey_manager.platform_handler.register_hotkey.assert_called_once_with(key_combo)
        self.assertEqual(self.hotkey_manager.hotkeys[key_combo], callback)
    
    def test_register_hotkey_fails(self):
        """测试注册热键失败的情况"""
        # 定义测试热键
        key_combo = "Ctrl+Alt+T"
        callback = Mock()
        
        # 模拟平台处理器的注册方法返回失败
        self.hotkey_manager.platform_handler.register_hotkey.return_value = False
        
        # 注册热键
        result = self.hotkey_manager.register_hotkey(key_combo, callback)
        
        # 验证结果
        self.assertFalse(result)
        self.hotkey_manager.platform_handler.register_hotkey.assert_called_once_with(key_combo)
        self.assertNotIn(key_combo, self.hotkey_manager.hotkeys)
    
    def test_unregister_hotkey(self):
        """测试注销热键"""
        # 定义测试热键
        key_combo = "Ctrl+Alt+T"
        callback = Mock()
        
        # 先注册热键
        self.hotkey_manager.hotkeys[key_combo] = callback
        
        # 模拟平台处理器的注销方法返回成功
        self.hotkey_manager.platform_handler.unregister_hotkey.return_value = True
        
        # 注销热键
        result = self.hotkey_manager.unregister_hotkey(key_combo)
        
        # 验证结果
        self.assertTrue(result)
        self.hotkey_manager.platform_handler.unregister_hotkey.assert_called_once_with(key_combo)
        self.assertNotIn(key_combo, self.hotkey_manager.hotkeys)
    
    def test_unregister_nonexistent_hotkey(self):
        """测试注销不存在的热键"""
        # 定义测试热键
        key_combo = "Ctrl+Alt+T"
        
        # 注销不存在的热键
        result = self.hotkey_manager.unregister_hotkey(key_combo)
        
        # 验证结果
        self.assertFalse(result)
        self.hotkey_manager.platform_handler.unregister_hotkey.assert_not_called()
    
    def test_is_hotkey_registered(self):
        """测试检查热键是否已注册"""
        # 定义测试热键
        key_combo = "Ctrl+Alt+T"
        callback = Mock()
        
        # 先注册热键
        self.hotkey_manager.hotkeys[key_combo] = callback
        
        # 检查热键是否已注册
        result = self.hotkey_manager.is_hotkey_registered(key_combo)
        
        # 验证结果
        self.assertTrue(result)
        
        # 检查不存在的热键
        result = self.hotkey_manager.is_hotkey_registered("Ctrl+Shift+X")
        
        # 验证结果
        self.assertFalse(result)
    
    def test_on_hotkey_callback(self):
        """测试热键回调处理"""
        # 定义测试热键
        key_combo = "Ctrl+Alt+T"
        callback = Mock()
        
        # 先注册热键
        self.hotkey_manager.hotkeys[key_combo] = callback
        
        # 触发热键回调
        self.hotkey_manager._on_hotkey_callback(key_combo)
        
        # 验证结果
        callback.assert_called_once()
        
        # 验证信号发射
        self.hotkey_manager.hotkey_triggered_signal.emit.assert_called_once_with(key_combo)
        
        # 验证事件发布
        self.assertTrue(self.mock_event_manager.post_event.called, "Event manager post_event方法未被调用")
        # 验证事件类型和数据是否正确
        event = self.mock_event_manager.post_event.call_args[0][0]
        self.assertEqual(event.event_type, InteractionEventType.HOTKEY_TRIGGERED)
        self.assertEqual(event.data.get("key_combination"), key_combo)
    
    def test_handle_event(self):
        """测试处理交互事件"""
        # 创建测试事件
        event = InteractionEvent(
            event_type=InteractionEventType.HOTKEY_TRIGGERED,
            data={"key_combination": "Ctrl+Alt+T"}
        )
        
        # 使用日志监控来验证handle_event正确处理HOTKEY_TRIGGERED事件
        with patch('status.interaction.hotkey.logger') as mock_logger:
            # 处理事件
            self.hotkey_manager.handle_event(event)
            
            # 验证事件被正确记录
            mock_logger.debug.assert_called_once()
    
    def test_shutdown(self):
        """测试关闭热键管理器"""
        # 先注册几个热键
        self.hotkey_manager.hotkeys = {
            "Ctrl+Alt+T": Mock(),
            "Ctrl+Shift+X": Mock()
        }
        
        # 模拟运行状态
        self.hotkey_manager.running = True
        self.hotkey_manager.listener_thread = Mock()
        
        # 模拟注销方法
        with patch.object(self.hotkey_manager, 'unregister_hotkey') as mock_unregister:
            # 设置注销返回值
            mock_unregister.return_value = True
            
            # 关闭热键管理器
            self.hotkey_manager.shutdown()
            
            # 验证注销调用
            calls = [call("Ctrl+Alt+T"), call("Ctrl+Shift+X")]
            mock_unregister.assert_has_calls(calls, any_order=True)
        
        # 验证停止调用
        self.assertFalse(self.hotkey_manager.running)
        self.hotkey_manager.platform_handler.stop.assert_called_once()


if __name__ == '__main__':
    unittest.main() 