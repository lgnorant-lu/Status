"""
---------------------------------------------------------------
File name:                  test_reminder_store.py
Author:                     Ignorant-lu
Date created:               2025/04/05
Description:                提醒存储测试模块
----------------------------------------------------------------

Changed history:            
                            2025/04/05: 初始创建;
----
"""
import unittest
import os
import json
import tempfile
import shutil
from datetime import datetime, timedelta

from status.reminder.reminder_store import ReminderStore

class TestReminderStore(unittest.TestCase):
    """测试提醒存储类"""
    
    def setUp(self):
        """测试前准备"""
        # 创建临时目录
        self.temp_dir = tempfile.mkdtemp()
        self.storage_path = os.path.join(self.temp_dir, "reminders.json")
        
        # 创建存储实例
        self.store = ReminderStore({
            'storage_path': self.storage_path
        })
    
    def tearDown(self):
        """测试后清理"""
        # 删除临时目录
        shutil.rmtree(self.temp_dir)
    
    def test_init(self):
        """测试初始化"""
        # 检查存储路径是否已设置
        self.assertEqual(self.store.storage_path, self.storage_path)
        
        # 检查内存中的提醒是否为空
        self.assertEqual(len(self.store.reminders), 0)
    
    def test_add_reminder(self):
        """测试添加提醒"""
        # 添加提醒
        reminder_id = "test_reminder"
        reminder = {
            'title': '测试提醒',
            'message': '这是一条测试提醒',
            'time': datetime.now() + timedelta(hours=1),
            'active': True
        }
        
        result = self.store.add_reminder(reminder_id, reminder)
        
        # 验证添加结果
        self.assertTrue(result)
        self.assertIn(reminder_id, self.store.reminders)
        
        # 验证文件存储
        self.assertTrue(os.path.exists(self.storage_path))
        
        # 验证文件内容
        with open(self.storage_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            self.assertIn(reminder_id, data)
    
    def test_update_reminder(self):
        """测试更新提醒"""
        # 添加提醒
        reminder_id = "test_reminder"
        reminder = {
            'title': '测试提醒',
            'message': '这是一条测试提醒',
            'time': datetime.now() + timedelta(hours=1),
            'active': True
        }
        
        self.store.add_reminder(reminder_id, reminder)
        
        # 更新提醒
        updated_reminder = reminder.copy()
        updated_reminder['title'] = '更新后的标题'
        
        result = self.store.update_reminder(reminder_id, updated_reminder)
        
        # 验证更新结果
        self.assertTrue(result)
        self.assertEqual(self.store.reminders[reminder_id]['title'], '更新后的标题')
        
        # 验证文件更新
        with open(self.storage_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            self.assertEqual(data[reminder_id]['title'], '更新后的标题')
    
    def test_delete_reminder(self):
        """测试删除提醒"""
        # 添加提醒
        reminder_id = "test_reminder"
        reminder = {
            'title': '测试提醒',
            'message': '这是一条测试提醒',
            'time': datetime.now() + timedelta(hours=1),
            'active': True
        }
        
        self.store.add_reminder(reminder_id, reminder)
        
        # 删除提醒
        result = self.store.delete_reminder(reminder_id)
        
        # 验证删除结果
        self.assertTrue(result)
        self.assertNotIn(reminder_id, self.store.reminders)
        
        # 验证文件更新
        with open(self.storage_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            self.assertNotIn(reminder_id, data)
    
    def test_get_reminder(self):
        """测试获取提醒"""
        # 添加提醒
        reminder_id = "test_reminder"
        reminder = {
            'title': '测试提醒',
            'message': '这是一条测试提醒',
            'time': datetime.now() + timedelta(hours=1),
            'active': True
        }
        
        self.store.add_reminder(reminder_id, reminder)
        
        # 获取提醒
        result = self.store.get_reminder(reminder_id)
        
        # 验证获取结果
        self.assertIsNotNone(result)
        self.assertEqual(result['title'], reminder['title'])
        
        # 获取不存在的提醒
        result = self.store.get_reminder("non_existent")
        self.assertIsNone(result)
    
    def test_get_all_reminders(self):
        """测试获取所有提醒"""
        # 添加多个提醒
        reminders = {
            "reminder1": {
                'title': '提醒1',
                'time': datetime.now() + timedelta(hours=1)
            },
            "reminder2": {
                'title': '提醒2',
                'time': datetime.now() + timedelta(hours=2)
            }
        }
        
        for reminder_id, reminder in reminders.items():
            self.store.add_reminder(reminder_id, reminder)
        
        # 获取所有提醒
        result = self.store.get_all_reminders()
        
        # 验证获取结果
        self.assertEqual(len(result), 2)
        self.assertIn("reminder1", result)
        self.assertIn("reminder2", result)
    
    def test_get_active_reminders(self):
        """测试获取激活状态的提醒"""
        # 添加活动和非活动提醒
        now = datetime.now()
        reminders = {
            "active1": {
                'title': '活动提醒1',
                'time': now + timedelta(hours=1),
                'active': True
            },
            "active2": {
                'title': '活动提醒2',
                'time': now + timedelta(hours=2),
                'active': True
            },
            "inactive": {
                'title': '非活动提醒',
                'time': now + timedelta(hours=3),
                'active': False
            },
            "expired": {
                'title': '过期提醒',
                'time': now - timedelta(hours=1),
                'active': True
            }
        }
        
        for reminder_id, reminder in reminders.items():
            self.store.add_reminder(reminder_id, reminder)
        
        # 获取活动提醒
        result = self.store.get_active_reminders()
        
        # 验证获取结果
        self.assertEqual(len(result), 2)
        self.assertIn("active1", result)
        self.assertIn("active2", result)
        self.assertNotIn("inactive", result)
        self.assertNotIn("expired", result)
    
    def test_get_expired_reminders(self):
        """测试获取过期提醒"""
        # 添加未过期和过期提醒
        now = datetime.now()
        reminders = {
            "future1": {
                'title': '未来提醒1',
                'time': now + timedelta(hours=1)
            },
            "future2": {
                'title': '未来提醒2',
                'time': now + timedelta(hours=2)
            },
            "expired1": {
                'title': '过期提醒1',
                'time': now - timedelta(hours=1)
            },
            "expired2": {
                'title': '过期提醒2',
                'time': now - timedelta(hours=2)
            }
        }
        
        for reminder_id, reminder in reminders.items():
            self.store.add_reminder(reminder_id, reminder)
        
        # 获取过期提醒
        result = self.store.get_expired_reminders()
        
        # 验证获取结果
        self.assertEqual(len(result), 2)
        self.assertIn("expired1", result)
        self.assertIn("expired2", result)
        self.assertNotIn("future1", result)
        self.assertNotIn("future2", result)
    
    def test_clear_expired_reminders(self):
        """测试清除过期提醒"""
        # 添加未过期和过期提醒
        now = datetime.now()
        reminders = {
            "future1": {
                'title': '未来提醒1',
                'time': now + timedelta(hours=1)
            },
            "expired1": {
                'title': '过期提醒1',
                'time': now - timedelta(hours=1)
            },
            "expired2": {
                'title': '过期提醒2',
                'time': now - timedelta(hours=2)
            }
        }
        
        for reminder_id, reminder in reminders.items():
            self.store.add_reminder(reminder_id, reminder)
        
        # 清除过期提醒
        count = self.store.clear_expired_reminders()
        
        # 验证清除结果
        self.assertEqual(count, 2)
        self.assertEqual(len(self.store.reminders), 1)
        self.assertIn("future1", self.store.reminders)
        self.assertNotIn("expired1", self.store.reminders)
        self.assertNotIn("expired2", self.store.reminders)

if __name__ == '__main__':
    unittest.main() 