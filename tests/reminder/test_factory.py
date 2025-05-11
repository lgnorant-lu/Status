"""
---------------------------------------------------------------
File name:                  test_factory.py
Author:                     Ignorant-lu
Date created:               2025/04/05
Description:                提醒系统工厂测试模块
----------------------------------------------------------------

Changed history:            
                            2025/04/05: 初始创建;
----
"""
import unittest
from unittest.mock import MagicMock, patch

from status.reminder.factory import (
    create_reminder_system,
    create_minimal_reminder_system,
    create_debug_reminder_system,
    create_custom_reminder_system
)
from status.reminder.reminder_manager import ReminderManager
from status.reminder.reminder_store import ReminderStore
from status.reminder.scheduler import ReminderScheduler
from status.reminder.notification import NotificationRenderer

class TestReminderFactory(unittest.TestCase):
    """测试提醒系统工厂类"""
    
    def setUp(self):
        """测试前准备"""
        # 创建模拟补丁
        self.reminder_store_patcher = patch('status.reminder.factory.ReminderStore')
        self.scheduler_patcher = patch('status.reminder.factory.ReminderScheduler')
        self.notification_patcher = patch('status.reminder.factory.NotificationRenderer')
        self.manager_patcher = patch('status.reminder.factory.ReminderManager')
        
        # 启动补丁
        self.mock_store_class = self.reminder_store_patcher.start()
        self.mock_scheduler_class = self.scheduler_patcher.start()
        self.mock_notification_class = self.notification_patcher.start()
        self.mock_manager_class = self.manager_patcher.start()
        
        # 创建模拟实例
        self.mock_store = MagicMock(spec=ReminderStore)
        self.mock_scheduler = MagicMock(spec=ReminderScheduler)
        self.mock_notification = MagicMock(spec=NotificationRenderer)
        self.mock_manager = MagicMock(spec=ReminderManager)
        
        # 设置返回值
        self.mock_store_class.return_value = self.mock_store
        self.mock_scheduler_class.return_value = self.mock_scheduler
        self.mock_notification_class.return_value = self.mock_notification
        self.mock_manager_class.return_value = self.mock_manager
    
    def tearDown(self):
        """测试后清理"""
        # 停止补丁
        self.reminder_store_patcher.stop()
        self.scheduler_patcher.stop()
        self.notification_patcher.stop()
        self.manager_patcher.stop()
    
    def test_create_reminder_system(self):
        """测试创建标准提醒系统"""
        # 创建测试配置
        config = {
            'store_config': {'storage_path': 'test/path'},
            'scheduler_config': {'scan_interval': 10},
            'notification_config': {'max_notifications': 5},
            'auto_start': True
        }
        
        # 调用工厂方法
        manager = create_reminder_system(config)
        
        # 验证组件创建
        self.mock_store_class.assert_called_once_with(config['store_config'])
        self.mock_scheduler_class.assert_called_once_with(config['scheduler_config'])
        self.mock_notification_class.assert_called_once_with(config['notification_config'])
        
        # 验证管理器创建
        self.mock_manager_class.assert_called_once_with(
            config, 
            self.mock_store, 
            self.mock_scheduler, 
            self.mock_notification
        )
        
        # 验证管理器启动
        self.mock_manager.start.assert_called_once()
        
        # 验证返回的实例
        self.assertEqual(manager, self.mock_manager)
    
    def test_create_reminder_system_no_auto_start(self):
        """测试创建不自动启动的提醒系统"""
        config = {'auto_start': False}
        
        # 调用工厂方法
        manager = create_reminder_system(config)
        
        # 验证管理器未启动
        self.mock_manager.start.assert_not_called()
    
    def test_create_minimal_reminder_system(self):
        """测试创建最小化提醒系统"""
        # 调用工厂方法
        manager = create_minimal_reminder_system()
        
        # 验证组件创建时使用了正确的配置
        self.mock_store_class.assert_called_once()
        store_config = self.mock_store_class.call_args[0][0]
        self.assertEqual(store_config['storage_path'], 'data/minimal_reminders.json')
        
        self.mock_scheduler_class.assert_called_once()
        scheduler_config = self.mock_scheduler_class.call_args[0][0]
        self.assertEqual(scheduler_config['scan_interval'], 30)
        
        self.mock_notification_class.assert_called_once()
        notification_config = self.mock_notification_class.call_args[0][0]
        self.assertEqual(notification_config['max_notifications'], 3)
        
        # 验证管理器创建
        self.mock_manager_class.assert_called_once()
        
        # 验证管理器未启动（auto_start=False）
        self.mock_manager.start.assert_not_called()
    
    def test_create_debug_reminder_system(self):
        """测试创建调试提醒系统"""
        # 调用工厂方法
        manager = create_debug_reminder_system()
        
        # 验证组件创建时使用了正确的配置
        self.mock_store_class.assert_called_once()
        store_config = self.mock_store_class.call_args[0][0]
        self.assertEqual(store_config['storage_path'], 'data/debug_reminders.json')
        
        self.mock_scheduler_class.assert_called_once()
        scheduler_config = self.mock_scheduler_class.call_args[0][0]
        self.assertEqual(scheduler_config['scan_interval'], 5)
        
        self.mock_notification_class.assert_called_once()
        notification_config = self.mock_notification_class.call_args[0][0]
        self.assertEqual(notification_config['max_notifications'], 10)
        
        # 验证管理器创建
        self.mock_manager_class.assert_called_once()
        
        # 验证管理器已启动（auto_start=True）
        self.mock_manager.start.assert_called_once()
    
    def test_create_custom_reminder_system(self):
        """测试创建自定义提醒系统"""
        # 创建自定义模拟组件
        custom_store = MagicMock(spec=ReminderStore)
        custom_scheduler = MagicMock(spec=ReminderScheduler)
        custom_notification = MagicMock(spec=NotificationRenderer)
        
        # 创建测试配置
        config = {'auto_start': True}
        
        # 调用工厂方法
        manager = create_custom_reminder_system(
            store=custom_store,
            scheduler=custom_scheduler,
            notification_renderer=custom_notification,
            config=config
        )
        
        # 验证管理器创建使用了自定义组件
        self.mock_manager_class.assert_called_once_with(
            config, 
            custom_store, 
            custom_scheduler, 
            custom_notification
        )
        
        # 验证管理器已启动
        self.mock_manager.start.assert_called_once()
    
    def test_create_custom_reminder_system_partial(self):
        """测试创建部分自定义的提醒系统"""
        # 创建自定义模拟组件
        custom_store = MagicMock(spec=ReminderStore)
        
        # 调用工厂方法（只提供存储器）
        manager = create_custom_reminder_system(
            store=custom_store,
            config={'auto_start': False}
        )
        
        # 验证管理器创建使用了自定义存储器和默认的其他组件
        self.mock_manager_class.assert_called_once_with(
            {'auto_start': False}, 
            custom_store, 
            None, 
            None
        )
        
        # 验证管理器未启动
        self.mock_manager.start.assert_not_called()

if __name__ == '__main__':
    unittest.main() 