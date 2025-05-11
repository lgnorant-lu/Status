"""
---------------------------------------------------------------
File name:                  test_scheduler.py
Author:                     Ignorant-lu
Date created:               2025/04/05
Description:                提醒调度器测试模块
----------------------------------------------------------------

Changed history:            
                            2025/04/05: 初始创建;
----
"""
import unittest
import time
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

from status.reminder.scheduler import ReminderScheduler

class TestReminderScheduler(unittest.TestCase):
    """测试提醒调度器类"""
    
    def setUp(self):
        """测试前准备"""
        self.config = {
            'scan_interval': 1  # 设置为1秒以加快测试
        }
        self.scheduler = ReminderScheduler(self.config)
    
    def tearDown(self):
        """测试后清理"""
        if self.scheduler.is_running():
            self.scheduler.stop()
    
    def test_init(self):
        """测试初始化"""
        self.assertEqual(self.scheduler.scan_interval, 1)
        self.assertFalse(self.scheduler.running)
        self.assertIsNone(self.scheduler.thread)
        self.assertEqual(len(self.scheduler.timers), 0)
        self.assertIn('on_reminder_triggered', self.scheduler.callbacks)
        self.assertIn('on_reminder_added', self.scheduler.callbacks)
        self.assertIn('on_reminder_removed', self.scheduler.callbacks)
        self.assertIn('on_scheduler_error', self.scheduler.callbacks)
    
    def test_start_stop(self):
        """测试启动和停止"""
        # 测试启动
        result = self.scheduler.start()
        self.assertTrue(result)
        self.assertTrue(self.scheduler.running)
        self.assertIsNotNone(self.scheduler.thread)
        
        # 再次启动应该返回False
        result = self.scheduler.start()
        self.assertFalse(result)
        
        # 测试停止
        result = self.scheduler.stop()
        self.assertTrue(result)
        self.assertFalse(self.scheduler.running)
        
        # 再次停止应该返回False
        result = self.scheduler.stop()
        self.assertFalse(result)
    
    def test_is_running(self):
        """测试运行状态检查"""
        self.assertFalse(self.scheduler.is_running())
        
        self.scheduler.start()
        self.assertTrue(self.scheduler.is_running())
        
        self.scheduler.stop()
        self.assertFalse(self.scheduler.is_running())
    
    def test_schedule_reminder_future(self):
        """测试调度未来提醒"""
        reminder_id = "test_reminder"
        reminder_time = datetime.now() + timedelta(seconds=2)
        reminder_data = {'title': '测试提醒'}
        
        # 注册触发回调模拟
        callback_mock = MagicMock()
        self.scheduler.register_callback('on_reminder_triggered', callback_mock)
        
        # 调度提醒
        result = self.scheduler.schedule_reminder(reminder_id, reminder_time, reminder_data)
        self.assertTrue(result)
        self.assertIn(reminder_id, self.scheduler.timers)
        
        # 启动调度器
        self.scheduler.start()
        
        # 等待提醒触发
        time.sleep(3)
        
        # 验证回调被调用
        callback_mock.assert_called_once()
        call_args = callback_mock.call_args[0][0]
        self.assertEqual(call_args['reminder_id'], reminder_id)
        self.assertEqual(call_args['data'], reminder_data)
    
    def test_schedule_reminder_past(self):
        """测试调度过去的提醒"""
        reminder_id = "test_past_reminder"
        reminder_time = datetime.now() - timedelta(seconds=5)
        reminder_data = {'title': '过去的提醒'}
        
        # 注册触发回调模拟
        callback_mock = MagicMock()
        self.scheduler.register_callback('on_reminder_triggered', callback_mock)
        
        # 调度过去的提醒应立即触发
        result = self.scheduler.schedule_reminder(reminder_id, reminder_time, reminder_data)
        self.assertTrue(result)
        
        # 验证回调被立即调用
        callback_mock.assert_called_once()
        call_args = callback_mock.call_args[0][0]
        self.assertEqual(call_args['reminder_id'], reminder_id)
        self.assertEqual(call_args['data'], reminder_data)
    
    def test_cancel_reminder(self):
        """测试取消提醒"""
        reminder_id = "test_reminder"
        reminder_time = datetime.now() + timedelta(seconds=60)
        reminder_data = {'title': '测试提醒'}
        
        # 调度提醒
        self.scheduler.schedule_reminder(reminder_id, reminder_time, reminder_data)
        self.assertIn(reminder_id, self.scheduler.timers)
        
        # 注册移除回调模拟
        callback_mock = MagicMock()
        self.scheduler.register_callback('on_reminder_removed', callback_mock)
        
        # 取消提醒
        result = self.scheduler.cancel_reminder(reminder_id)
        self.assertTrue(result)
        self.assertNotIn(reminder_id, self.scheduler.timers)
        
        # 验证回调被调用
        callback_mock.assert_called_once()
        call_args = callback_mock.call_args[0][0]
        self.assertEqual(call_args['reminder_id'], reminder_id)
        
        # 尝试取消不存在的提醒
        result = self.scheduler.cancel_reminder("non_existent")
        self.assertFalse(result)
    
    def test_register_unregister_callback(self):
        """测试注册和取消注册回调"""
        callback = MagicMock()
        
        # 注册回调
        result = self.scheduler.register_callback('on_reminder_triggered', callback)
        self.assertTrue(result)
        self.assertIn(callback, self.scheduler.callbacks['on_reminder_triggered'])
        
        # 注册不存在的事件类型
        result = self.scheduler.register_callback('non_existent_event', callback)
        self.assertFalse(result)
        
        # 取消注册回调
        result = self.scheduler.unregister_callback('on_reminder_triggered', callback)
        self.assertTrue(result)
        self.assertNotIn(callback, self.scheduler.callbacks['on_reminder_triggered'])
        
        # 取消注册不存在的事件类型
        result = self.scheduler.unregister_callback('non_existent_event', callback)
        self.assertFalse(result)
        
        # 取消注册不存在的回调
        result = self.scheduler.unregister_callback('on_reminder_triggered', callback)
        self.assertFalse(result)
    
    @patch('threading.Timer')
    def test_trigger_reminder(self, mock_timer):
        """测试触发提醒"""
        # 设置模拟定时器的行为
        timer_instance = MagicMock()
        mock_timer.return_value = timer_instance
        
        # 注册触发回调模拟
        trigger_callback = MagicMock()
        self.scheduler.register_callback('on_reminder_triggered', trigger_callback)
        
        # 调度提醒
        reminder_id = "test_reminder"
        reminder_data = {'title': '测试提醒'}
        reminder_time = datetime.now() + timedelta(seconds=10)
        
        self.scheduler.schedule_reminder(reminder_id, reminder_time, reminder_data)
        
        # 模拟定时器回调，直接调用_trigger_reminder
        self.scheduler._trigger_reminder(reminder_id, reminder_data)
        
        # 验证触发回调被调用
        trigger_callback.assert_called_once()
        call_args = trigger_callback.call_args[0][0]
        self.assertEqual(call_args['reminder_id'], reminder_id)
        self.assertEqual(call_args['data'], reminder_data)
        
        # 确保提醒被从定时器列表中移除
        self.assertNotIn(reminder_id, self.scheduler.timers)

if __name__ == '__main__':
    unittest.main() 