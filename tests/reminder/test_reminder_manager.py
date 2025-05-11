"""
---------------------------------------------------------------
File name:                  test_reminder_manager.py
Author:                     Ignorant-lu
Date created:               2025/04/05
Description:                提醒管理器测试模块
----------------------------------------------------------------

Changed history:            
                            2025/04/05: 初始创建;
----
"""
import unittest
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta
import time

from status.reminder.reminder_manager import ReminderManager
from status.reminder.reminder_store import ReminderStore
from status.reminder.scheduler import ReminderScheduler
from status.reminder.notification import NotificationRenderer

class TestReminderManager(unittest.TestCase):
    """测试提醒管理器类"""
    
    def setUp(self):
        """测试前准备"""
        # 创建模拟组件
        self.mock_store = MagicMock(spec=ReminderStore)
        self.mock_scheduler = MagicMock(spec=ReminderScheduler)
        self.mock_notification = MagicMock(spec=NotificationRenderer)
        
        # 设置模拟行为
        self.mock_store.get_active_reminders.return_value = {}
        
        # 创建管理器实例
        self.manager = ReminderManager(
            config={},
            store=self.mock_store,
            scheduler=self.mock_scheduler,
            notification_renderer=self.mock_notification
        )
    
    def tearDown(self):
        """测试后清理"""
        # 如果管理器在运行中，停止它
        if hasattr(self, 'manager') and self.manager.is_running():
            self.manager.stop()
    
    def test_init(self):
        """测试初始化"""
        # 验证组件是否被正确设置
        self.assertEqual(self.manager.store, self.mock_store)
        self.assertEqual(self.manager.scheduler, self.mock_scheduler)
        self.assertEqual(self.manager.notification_renderer, self.mock_notification)
        
        # 验证是否加载了现有提醒
        self.mock_store.get_active_reminders.assert_called_once()
        
        # 验证回调是否已注册
        self.mock_scheduler.register_callback.assert_any_call(
            'on_reminder_triggered', self.manager._on_reminder_triggered)
        self.mock_scheduler.register_callback.assert_any_call(
            'on_scheduler_error', self.manager._on_scheduler_error)
    
    def test_init_with_active_reminders(self):
        """测试初始化时加载活动提醒"""
        # 重置模拟
        self.mock_store.reset_mock()
        self.mock_scheduler.reset_mock()
        
        # 设置模拟提醒数据
        now = datetime.now()
        reminder1 = {
            'title': '提醒1',
            'message': '这是提醒1',
            'time': now + timedelta(hours=1),
            'active': True
        }
        reminder2 = {
            'title': '提醒2',
            'message': '这是提醒2',
            'time': now + timedelta(hours=2),
            'active': True
        }
        
        self.mock_store.get_active_reminders.return_value = {
            'reminder1': reminder1,
            'reminder2': reminder2
        }
        
        # 创建新的管理器实例
        manager = ReminderManager(
            config={},
            store=self.mock_store,
            scheduler=self.mock_scheduler,
            notification_renderer=self.mock_notification
        )
        
        # 验证调度器为每个提醒调用了schedule_reminder
        self.assertEqual(self.mock_scheduler.schedule_reminder.call_count, 2)
        self.mock_scheduler.schedule_reminder.assert_any_call(
            'reminder1', reminder1['time'], reminder1)
        self.mock_scheduler.schedule_reminder.assert_any_call(
            'reminder2', reminder2['time'], reminder2)
    
    def test_start_stop(self):
        """测试启动和停止"""
        # 设置模拟行为
        self.mock_scheduler.start.return_value = True
        self.mock_scheduler.stop.return_value = True
        self.mock_scheduler.is_running.return_value = True  # 将side_effect改为固定返回值
        
        # 测试启动
        result = self.manager.start()
        self.assertTrue(result)
        self.mock_scheduler.start.assert_called_once()
        
        # 测试运行状态
        self.assertTrue(self.manager.is_running())
        self.mock_scheduler.is_running.assert_called()
        
        # 测试停止
        result = self.manager.stop()
        self.assertTrue(result)
        self.mock_scheduler.stop.assert_called_once()
        
        # 更新模拟行为以返回False
        self.mock_scheduler.is_running.return_value = False
        
        # 再次检查运行状态
        self.assertFalse(self.manager.is_running())
    
    def test_create_reminder(self):
        """测试创建提醒"""
        # 设置模拟行为
        self.mock_store.add_reminder.return_value = True
        self.mock_scheduler.schedule_reminder.return_value = True
        
        # 创建提醒
        now = datetime.now()
        reminder_time = now + timedelta(hours=1)
        
        with patch('uuid.uuid4', return_value='test-uuid'):
            reminder_id = self.manager.create_reminder(
                title="测试提醒",
                message="这是一个测试提醒",
                reminder_time=reminder_time,
                notification_type="info"
            )
        
        # 验证提醒ID
        self.assertEqual(reminder_id, "test-uuid")
        
        # 验证存储和调度调用
        self.mock_store.add_reminder.assert_called_once()
        self.mock_scheduler.schedule_reminder.assert_called_once()
        
        # 验证添加的提醒数据
        added_reminder = self.mock_store.add_reminder.call_args[0][1]
        self.assertEqual(added_reminder['title'], "测试提醒")
        self.assertEqual(added_reminder['message'], "这是一个测试提醒")
        self.assertEqual(added_reminder['time'], reminder_time)
        self.assertEqual(added_reminder['notification_type'], "info")
        self.assertTrue(added_reminder['active'])
    
    def test_update_reminder(self):
        """测试更新提醒"""
        # 设置模拟行为
        original_reminder = {
            'title': '原始标题',
            'message': '原始消息',
            'time': datetime.now() + timedelta(hours=1),
            'notification_type': 'info',
            'active': True
        }
        
        self.mock_store.get_reminder.return_value = original_reminder.copy()
        self.mock_store.update_reminder.return_value = True
        self.mock_scheduler.cancel_reminder.return_value = True
        self.mock_scheduler.schedule_reminder.return_value = True
        
        # 更新提醒
        new_time = datetime.now() + timedelta(hours=2)
        result = self.manager.update_reminder(
            reminder_id="test_reminder",
            title="更新后的标题",
            message="更新后的消息",
            reminder_time=new_time,
            notification_type="warning"
        )
        
        # 验证结果
        self.assertTrue(result)
        
        # 验证存储和调度调用
        self.mock_store.get_reminder.assert_called_once_with("test_reminder")
        self.mock_store.update_reminder.assert_called_once()
        self.mock_scheduler.cancel_reminder.assert_called_once_with("test_reminder")
        self.mock_scheduler.schedule_reminder.assert_called_once()
        
        # 验证更新的提醒数据
        updated_reminder = self.mock_store.update_reminder.call_args[0][1]
        self.assertEqual(updated_reminder['title'], "更新后的标题")
        self.assertEqual(updated_reminder['message'], "更新后的消息")
        self.assertEqual(updated_reminder['time'], new_time)
        self.assertEqual(updated_reminder['notification_type'], "warning")
    
    def test_delete_reminder(self):
        """测试删除提醒"""
        # 设置模拟行为
        self.mock_store.delete_reminder.return_value = True
        self.mock_scheduler.cancel_reminder.return_value = True
        
        # 删除提醒
        result = self.manager.delete_reminder("test_reminder")
        
        # 验证结果
        self.assertTrue(result)
        
        # 验证存储和调度调用
        self.mock_store.delete_reminder.assert_called_once_with("test_reminder")
        self.mock_scheduler.cancel_reminder.assert_called_once_with("test_reminder")
    
    def test_get_reminder(self):
        """测试获取提醒"""
        # 设置模拟行为
        expected_reminder = {
            'title': '测试提醒',
            'message': '这是一个测试提醒'
        }
        self.mock_store.get_reminder.return_value = expected_reminder
        
        # 获取提醒
        reminder = self.manager.get_reminder("test_reminder")
        
        # 验证结果
        self.assertEqual(reminder, expected_reminder)
        
        # 验证存储调用
        self.mock_store.get_reminder.assert_called_once_with("test_reminder")
    
    def test_get_all_reminders(self):
        """测试获取所有提醒"""
        # 设置模拟行为
        expected_reminders = {
            'reminder1': {'title': '提醒1'},
            'reminder2': {'title': '提醒2'}
        }
        self.mock_store.get_all_reminders.return_value = expected_reminders
        
        # 获取所有提醒
        reminders = self.manager.get_all_reminders()
        
        # 验证结果
        self.assertEqual(reminders, expected_reminders)
        
        # 验证存储调用
        self.mock_store.get_all_reminders.assert_called_once()
    
    def test_get_active_reminders(self):
        """测试获取活动提醒"""
        # 设置模拟行为
        expected_reminders = {
            'reminder1': {'title': '提醒1', 'active': True},
            'reminder2': {'title': '提醒2', 'active': True}
        }
        self.mock_store.get_active_reminders.return_value = expected_reminders
        
        # 获取活动提醒
        reminders = self.manager.get_active_reminders()
        
        # 验证结果
        self.assertEqual(reminders, expected_reminders)
        
        # 验证存储调用
        self.mock_store.get_active_reminders.assert_called()
    
    def test_clear_expired_reminders(self):
        """测试清理过期提醒"""
        # 设置模拟行为
        self.mock_store.clear_expired_reminders.return_value = 2
        
        # 清理过期提醒
        count = self.manager.clear_expired_reminders()
        
        # 验证结果
        self.assertEqual(count, 2)
        
        # 验证存储调用
        self.mock_store.clear_expired_reminders.assert_called_once()
    
    def test_on_reminder_triggered(self):
        """测试提醒触发回调"""
        # 设置模拟行为
        reminder = {
            'title': '测试提醒',
            'message': '这是一个测试提醒',
            'notification_type': 'info'
        }
        self.mock_store.get_reminder.return_value = reminder.copy()
        self.mock_notification.show_notification.return_value = "notification-123"
        
        # 触发提醒回调
        trigger_data = {
            'reminder_id': 'test_reminder',
            'data': reminder
        }
        
        # 注册回调模拟
        callback_mock = MagicMock()
        self.manager.register_callback('on_reminder_triggered', callback_mock)
        
        # 调用回调
        self.manager._on_reminder_triggered(trigger_data)
        
        # 验证通知被显示
        self.mock_notification.show_notification.assert_called_once_with(
            title='测试提醒',
            message='这是一个测试提醒',
            notification_type='info',
            data={'reminder_id': 'test_reminder'}
        )
        
        # 验证提醒被标记为已触发
        self.mock_store.update_reminder.assert_called_once()
        updated_reminder = self.mock_store.update_reminder.call_args[0][1]
        self.assertTrue(updated_reminder['triggered'])
        self.assertEqual(updated_reminder['notification_id'], "notification-123")
        
        # 验证触发回调被调用
        callback_mock.assert_called_once()
        call_args = callback_mock.call_args[0][0]
        self.assertEqual(call_args['reminder_id'], 'test_reminder')
        self.assertEqual(call_args['notification_id'], "notification-123")
    
    def test_register_unregister_callback(self):
        """测试注册和取消注册回调"""
        callback = MagicMock()
        
        # 注册回调
        result = self.manager.register_callback('on_reminder_created', callback)
        self.assertTrue(result)
        self.assertIn(callback, self.manager.callbacks['on_reminder_created'])
        
        # 注册不存在的事件类型
        result = self.manager.register_callback('non_existent_event', callback)
        self.assertFalse(result)
        
        # 取消注册回调
        result = self.manager.unregister_callback('on_reminder_created', callback)
        self.assertTrue(result)
        self.assertNotIn(callback, self.manager.callbacks['on_reminder_created'])
        
        # 取消注册不存在的事件类型
        result = self.manager.unregister_callback('non_existent_event', callback)
        self.assertFalse(result)
        
        # 取消注册不存在的回调
        result = self.manager.unregister_callback('on_reminder_created', callback)
        self.assertFalse(result)

if __name__ == '__main__':
    unittest.main() 