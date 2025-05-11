"""
---------------------------------------------------------------
File name:                  test_notification.py
Author:                     Ignorant-lu
Date created:               2025/04/05
Description:                通知渲染器测试模块
----------------------------------------------------------------

Changed history:            
                            2025/04/05: 初始创建;
----
"""
import unittest
import time
from unittest.mock import MagicMock, patch
from datetime import datetime

from status.reminder.notification import NotificationRenderer

class TestNotificationRenderer(unittest.TestCase):
    """测试通知渲染器类"""
    
    def setUp(self):
        """测试前准备"""
        self.config = {
            'max_notifications': 3,
            'styles': {
                'custom': {
                    'color': '#FF00FF',
                    'icon': 'custom-icon',
                    'duration': 3
                },
                'info': {
                    'duration': 2  # 覆盖默认值
                }
            }
        }
        self.renderer = NotificationRenderer(self.config)
    
    def tearDown(self):
        """测试后清理"""
        # 清理活动通知
        self.renderer.active_notifications = []
    
    def test_init(self):
        """测试初始化"""
        # 检查配置是否被正确加载
        self.assertEqual(self.renderer.max_notifications, 3)
        
        # 检查样式是否被正确合并
        self.assertIn('custom', self.renderer.default_styles)
        self.assertEqual(self.renderer.default_styles['custom']['color'], '#FF00FF')
        
        # 检查默认样式是否被正确覆盖
        self.assertEqual(self.renderer.default_styles['info']['duration'], 2)
        
        # 检查回调字典是否正确初始化
        self.assertIn('on_notification_show', self.renderer.callbacks)
        self.assertIn('on_notification_click', self.renderer.callbacks)
        self.assertIn('on_notification_close', self.renderer.callbacks)
        self.assertIn('on_notification_error', self.renderer.callbacks)
    
    @patch('time.time')
    def test_show_notification(self, mock_time):
        """测试显示通知"""
        mock_time.return_value = 1000.0
        
        # 模拟系统通知方法
        self.renderer._show_system_notification = MagicMock()
        self.renderer._show_app_notification = MagicMock()
        
        # 注册显示回调
        show_callback = MagicMock()
        self.renderer.register_callback('on_notification_show', show_callback)
        
        # 显示通知
        title = "测试标题"
        message = "测试消息"
        notification_id = self.renderer.show_notification(
            title=title,
            message=message,
            notification_type='info',
            data={'key': 'value'}
        )
        
        # 验证通知ID格式
        self.assertEqual(notification_id, "notification_1000000")
        
        # 验证系统和应用内通知方法被调用
        self.renderer._show_system_notification.assert_called_once()
        self.renderer._show_app_notification.assert_called_once()
        
        # 验证回调被调用
        show_callback.assert_called_once()
        call_args = show_callback.call_args[0][0]
        self.assertEqual(call_args['title'], title)
        self.assertEqual(call_args['message'], message)
        
        # 验证通知被添加到活动列表
        self.assertEqual(len(self.renderer.active_notifications), 1)
        self.assertEqual(self.renderer.active_notifications[0]['id'], notification_id)
    
    def test_show_notification_with_custom_type(self):
        """测试使用自定义类型显示通知"""
        # 显示自定义类型通知
        notification_id = self.renderer.show_notification(
            title="自定义通知",
            message="这是一个自定义通知",
            notification_type='custom'
        )
        
        # 验证自定义样式被应用
        notification = self.renderer.get_notification(notification_id)
        self.assertEqual(notification['style']['color'], '#FF00FF')
        self.assertEqual(notification['style']['icon'], 'custom-icon')
    
    def test_max_notifications_limit(self):
        """测试最大通知数限制"""
        # 显示4个通知（超过最大数量3）
        for i in range(4):
            self.renderer.show_notification(
                title=f"通知{i}",
                message=f"消息{i}"
            )
        
        # 验证只保留最新的3个
        self.assertEqual(len(self.renderer.active_notifications), 3)
        self.assertEqual(self.renderer.active_notifications[0]['title'], "通知1")
        self.assertEqual(self.renderer.active_notifications[1]['title'], "通知2")
        self.assertEqual(self.renderer.active_notifications[2]['title'], "通知3")
    
    def test_close_notification(self):
        """测试关闭通知"""
        # 显示通知
        notification_id = self.renderer.show_notification(
            title="测试通知",
            message="这是一个测试通知"
        )
        
        # 注册关闭回调
        close_callback = MagicMock()
        self.renderer.register_callback('on_notification_close', close_callback)
        
        # 关闭通知
        result = self.renderer.close_notification(notification_id)
        self.assertTrue(result)
        
        # 验证回调被调用
        close_callback.assert_called_once()
        call_args = close_callback.call_args[0][0]
        self.assertEqual(call_args['id'], notification_id)
        
        # 验证通知被移除
        self.assertEqual(len(self.renderer.active_notifications), 0)
        
        # 尝试关闭不存在的通知
        result = self.renderer.close_notification("non_existent")
        self.assertFalse(result)
    
    def test_close_all_notifications(self):
        """测试关闭所有通知"""
        # 显示多个通知
        for i in range(3):
            self.renderer.show_notification(
                title=f"通知{i}",
                message=f"消息{i}"
            )
        
        # 验证通知列表长度
        self.assertEqual(len(self.renderer.active_notifications), 3)
        
        # 注册关闭回调
        close_callback = MagicMock()
        self.renderer.register_callback('on_notification_close', close_callback)
        
        # 关闭所有通知
        count = self.renderer.close_all_notifications()
        self.assertEqual(count, 3)
        
        # 验证回调被调用3次
        self.assertEqual(close_callback.call_count, 3)
        
        # 验证所有通知被移除
        self.assertEqual(len(self.renderer.active_notifications), 0)
    
    def test_update_notification(self):
        """测试更新通知"""
        # 显示通知
        notification_id = self.renderer.show_notification(
            title="原始标题",
            message="原始消息",
            notification_type='info'
        )
        
        # 更新通知
        updates = {
            'title': '更新后的标题',
            'message': '更新后的消息',
            'type': 'warning'
        }
        
        result = self.renderer.update_notification(notification_id, updates)
        self.assertTrue(result)
        
        # 获取更新后的通知
        notification = self.renderer.get_notification(notification_id)
        self.assertEqual(notification['title'], '更新后的标题')
        self.assertEqual(notification['message'], '更新后的消息')
        self.assertEqual(notification['type'], 'warning')
        
        # 尝试更新不存在的通知
        result = self.renderer.update_notification("non_existent", updates)
        self.assertFalse(result)
    
    def test_get_notification(self):
        """测试获取通知"""
        # 显示通知
        notification_id = self.renderer.show_notification(
            title="测试通知",
            message="这是一个测试通知"
        )
        
        # 获取通知
        notification = self.renderer.get_notification(notification_id)
        self.assertIsNotNone(notification)
        self.assertEqual(notification['title'], "测试通知")
        
        # 获取不存在的通知
        notification = self.renderer.get_notification("non_existent")
        self.assertIsNone(notification)
    
    def test_get_all_notifications(self):
        """测试获取所有通知"""
        # 显示多个通知
        for i in range(3):
            self.renderer.show_notification(
                title=f"通知{i}",
                message=f"消息{i}"
            )
        
        # 获取所有通知
        notifications = self.renderer.get_all_notifications()
        self.assertEqual(len(notifications), 3)
        self.assertEqual(notifications[0]['title'], "通知0")
        self.assertEqual(notifications[1]['title'], "通知1")
        self.assertEqual(notifications[2]['title'], "通知2")
    
    def test_register_unregister_callback(self):
        """测试注册和取消注册回调"""
        callback = MagicMock()
        
        # 注册回调
        result = self.renderer.register_callback('on_notification_show', callback)
        self.assertTrue(result)
        self.assertIn(callback, self.renderer.callbacks['on_notification_show'])
        
        # 注册不存在的事件类型
        result = self.renderer.register_callback('non_existent_event', callback)
        self.assertFalse(result)
        
        # 取消注册回调
        result = self.renderer.unregister_callback('on_notification_show', callback)
        self.assertTrue(result)
        self.assertNotIn(callback, self.renderer.callbacks['on_notification_show'])
        
        # 取消注册不存在的事件类型
        result = self.renderer.unregister_callback('non_existent_event', callback)
        self.assertFalse(result)
        
        # 取消注册不存在的回调
        result = self.renderer.unregister_callback('on_notification_show', callback)
        self.assertFalse(result)
    
    def test_notification_with_callback(self):
        """测试带有回调的通知"""
        # 创建点击回调
        click_callback = MagicMock()
        
        # 显示带有回调的通知
        notification_id = self.renderer.show_notification(
            title="点击通知",
            message="点击这个通知",
            callback=click_callback
        )
        
        # 获取注册的on_notification_click回调
        registered_callbacks = self.renderer.callbacks['on_notification_click']
        self.assertTrue(len(registered_callbacks) > 0)
        
        # 模拟点击事件
        for callback in registered_callbacks:
            callback({'id': notification_id})
        
        # 验证原始回调被调用
        click_callback.assert_called_once()

if __name__ == '__main__':
    unittest.main() 