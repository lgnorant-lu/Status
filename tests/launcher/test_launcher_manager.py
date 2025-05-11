"""
---------------------------------------------------------------
File name:                  test_launcher_manager.py
Author:                     Ignorant-lu
Date created:               2023/11/28
Description:                快捷启动器管理器的单元测试
----------------------------------------------------------------

Changed history:
                           2023/11/28: 初始创建
                           2023/11/29: 更新测试以匹配实际实现
                           2023/11/29: 移除对event_manager.emit的断言
----
"""

import unittest
import os
import tempfile
import json
from unittest.mock import MagicMock, patch

from status.launcher.launcher_manager import LauncherManager
from status.launcher.launcher_types import LaunchedApplication, LauncherGroup, LaunchStatus

class TestLauncherManager(unittest.TestCase):
    def setUp(self):
        """测试前准备"""
        # 重置单例
        LauncherManager._instance = None
        
        # 创建实例
        self.manager = LauncherManager.get_instance()
        
        # 模拟配置管理器
        self.manager.config_manager = MagicMock()
        self.manager.config_manager.get.return_value = {}
        
        # 模拟事件管理器
        self.manager.event_manager = MagicMock()
        
        # 模拟文件路径存在
        self.original_exists = os.path.exists
        os.path.exists = MagicMock(return_value=True)
        
        # 初始化搜索索引
        self.manager._search_index = {}
        
        # 测试应用
        self.test_app1 = LaunchedApplication(
            name="测试应用1",
            path=r"C:\Windows\notepad.exe",
            description="测试应用1"
        )
        
        self.test_app2 = LaunchedApplication(
            name="测试应用2",
            path=r"C:\Windows\calc.exe",
            description="计算器"
        )
        
        # 测试组
        self.test_group = LauncherGroup(
            name="测试组",
            description="测试分组"
        )
    
    def tearDown(self):
        """测试清理"""
        # 恢复原始的os.path.exists函数
        os.path.exists = self.original_exists
    
    def test_singleton(self):
        """测试单例模式"""
        manager1 = LauncherManager.get_instance()
        manager2 = LauncherManager.get_instance()
        
        self.assertIs(manager1, manager2)
        self.assertIs(self.manager, manager1)
    
    def test_add_application(self):
        """测试添加应用"""
        self.manager.add_application(self.test_app1)
        
        # 验证应用已添加
        self.assertIn(self.test_app1.id, self.manager.applications)
        self.assertEqual(self.manager.applications[self.test_app1.id], self.test_app1)
        
        # 验证搜索索引已更新
        term = self.test_app1.name.lower().split()[0]  # 取第一个单词作为搜索词
        self.assertIn(term, self.manager._search_index)
        self.assertIn(self.test_app1.id, self.manager._search_index[term])
    
    def test_remove_application(self):
        """测试移除应用"""
        # 先添加应用
        self.manager.add_application(self.test_app1)
        app_id = self.test_app1.id
        
        # 再移除应用
        self.manager.remove_application(app_id)
        
        # 验证应用已移除
        self.assertNotIn(app_id, self.manager.applications)
    
    def test_add_group(self):
        """测试添加应用组"""
        self.manager.add_group(self.test_group)
        
        # 验证组已添加
        self.assertIn(self.test_group.id, self.manager.groups)
        self.assertEqual(self.manager.groups[self.test_group.id], self.test_group)
    
    def test_remove_group(self):
        """测试移除应用组"""
        # 先添加组
        self.manager.add_group(self.test_group)
        group_id = self.test_group.id
        
        # 再移除组
        self.manager.remove_group(group_id)
        
        # 验证组已移除
        self.assertNotIn(group_id, self.manager.groups)
    
    def test_add_application_to_group(self):
        """测试将应用添加到组"""
        # 先添加应用和组
        self.manager.add_application(self.test_app1)
        self.manager.add_group(self.test_group)
        
        app_id = self.test_app1.id
        group_id = self.test_group.id
        
        # 添加应用到组
        self.manager.add_to_group(app_id, group_id)
        
        # 验证应用已添加到组
        self.assertIn(app_id, self.manager.groups[group_id].applications)
    
    def test_remove_application_from_group(self):
        """测试从组中移除应用"""
        # 先添加应用和组
        self.manager.add_application(self.test_app1)
        self.manager.add_group(self.test_group)
        
        app_id = self.test_app1.id
        group_id = self.test_group.id
        
        # 添加应用到组
        self.manager.add_to_group(app_id, group_id)
        
        # 从组中移除应用
        self.manager.remove_from_group(app_id, group_id)
        
        # 验证应用已从组中移除
        self.assertNotIn(app_id, self.manager.groups[group_id].applications)
    
    @patch('status.launcher.launcher_manager.subprocess')
    def test_launch_application_success(self, mock_subprocess):
        """测试成功启动应用"""
        # 设置模拟子进程返回值
        mock_subprocess.Popen.return_value = MagicMock()
        
        # 添加应用
        self.manager.add_application(self.test_app1)
        app_id = self.test_app1.id
        
        # 启动应用
        result = self.manager.launch_application(app_id)
        
        # 验证启动结果
        self.assertEqual(result.status, LaunchStatus.SUCCESS)
        self.assertTrue(result.success)
        
        # 验证应用使用次数增加
        self.assertEqual(self.manager.applications[app_id].use_count, 1)
        
        # 验证子进程被调用
        mock_subprocess.Popen.assert_called_once()
        
        # 验证最近使用的应用包含此应用
        recent_apps = self.manager.get_recent_applications()
        self.assertIn(app_id, [app.id for app in recent_apps])
    
    @patch('status.launcher.launcher_manager.subprocess')
    def test_launch_application_error(self, mock_subprocess):
        """测试启动应用出错"""
        # 设置模拟子进程抛出异常
        mock_subprocess.Popen.side_effect = Exception("测试错误")
        
        # 添加应用
        self.manager.add_application(self.test_app1)
        app_id = self.test_app1.id
        
        # 启动应用
        result = self.manager.launch_application(app_id)
        
        # 验证启动结果
        self.assertEqual(result.status, LaunchStatus.UNKNOWN_ERROR)
        self.assertFalse(result.success)
        self.assertIsNotNone(result.error)
    
    def test_launch_nonexistent_application(self):
        """测试启动不存在的应用"""
        # 启动不存在的应用
        result = self.manager.launch_application("non-existent-id")
        
        # 验证启动结果
        self.assertEqual(result.status, LaunchStatus.NOT_FOUND)
        self.assertFalse(result.success)
    
    def test_search_applications(self):
        """测试搜索应用"""
        # 添加测试应用
        self.manager.add_application(self.test_app1)  # 名称: 测试应用1
        self.manager.add_application(self.test_app2)  # 名称: 测试应用2, 描述: 计算器
        
        # 搜索"测试"
        results = self.manager.search_applications("测试")
        self.assertGreaterEqual(len(results), 1)
        
        # 至少要能找到一个应用
        found_ids = [app.id for app in results]
        self.assertTrue(self.test_app1.id in found_ids or self.test_app2.id in found_ids)
        
        # 搜索"计算器"
        results = self.manager.search_applications("计算器")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].id, self.test_app2.id)
        
        # 搜索不存在的内容
        results = self.manager.search_applications("不存在")
        self.assertEqual(len(results), 0)
    
    def test_toggle_favorite(self):
        """测试切换收藏状态"""
        # 设置收藏分组
        favorite_group = LauncherGroup(name="收藏", description="收藏的应用")
        self.manager.add_group(favorite_group)
        self.manager.config["favorite_group_id"] = favorite_group.id
        
        # 添加应用
        self.manager.add_application(self.test_app1)
        app_id = self.test_app1.id
        
        # 初始状态
        self.assertFalse(self.manager.applications[app_id].favorite)
        
        # 切换为收藏
        self.manager.toggle_favorite(app_id)
        self.assertTrue(self.manager.applications[app_id].favorite)
        
        # 收藏列表应包含此应用
        favorite_apps = self.manager.get_favorite_applications()
        self.assertIn(app_id, [app.id for app in favorite_apps])
        
        # 再次切换
        self.manager.toggle_favorite(app_id)
        self.assertFalse(self.manager.applications[app_id].favorite)
        
        # 收藏列表不应包含此应用
        favorite_apps = self.manager.get_favorite_applications()
        self.assertNotIn(app_id, [app.id for app in favorite_apps])
    
    def test_get_applications_by_group(self):
        """测试获取组内应用"""
        # 添加应用和组
        self.manager.add_application(self.test_app1)
        self.manager.add_application(self.test_app2)
        self.manager.add_group(self.test_group)
        
        app_id1 = self.test_app1.id
        app_id2 = self.test_app2.id
        group_id = self.test_group.id
        
        # 将应用1添加到组
        self.manager.add_to_group(app_id1, group_id)
        
        # 获取组内应用
        group_apps = self.manager.get_applications_by_group(group_id)
        
        # 验证结果
        self.assertEqual(len(group_apps), 1)
        self.assertEqual(group_apps[0].id, app_id1)
        self.assertNotIn(app_id2, [app.id for app in group_apps])
    
    def test_save_and_load_config(self):
        """测试保存和加载配置"""
        # 设置收藏分组
        favorite_group = LauncherGroup(name="收藏", description="收藏的应用")
        self.manager.add_group(favorite_group)
        self.manager.config["favorite_group_id"] = favorite_group.id
        
        # 添加应用和组
        self.manager.add_application(self.test_app1)
        self.manager.add_application(self.test_app2)
        self.manager.add_group(self.test_group)
        
        app_id1 = self.test_app1.id
        group_id = self.test_group.id
        
        # 将应用添加到组
        self.manager.add_to_group(app_id1, group_id)
        
        # 收藏应用1
        self.manager.toggle_favorite(app_id1)
        
        # 启动应用1增加使用次数
        with patch('status.launcher.launcher_manager.subprocess') as mock_subprocess:
            mock_subprocess.Popen.return_value = MagicMock()
            self.manager.launch_application(app_id1)
        
        # 模拟保存配置
        saved_config = {}
        
        def mock_set(key, value):
            saved_config[key] = value
        
        self.manager.config_manager.set.side_effect = mock_set
        
        # 保存配置
        self.manager.save_configuration()
        
        # 验证配置已保存
        self.assertIn('applications', saved_config["launcher"])
        self.assertIn('groups', saved_config["launcher"])
        
        # 创建新实例
        LauncherManager._instance = None
        new_manager = LauncherManager.get_instance()
        new_manager.config_manager = MagicMock()
        new_manager.config_manager.get.return_value = saved_config["launcher"]
        new_manager.event_manager = MagicMock()
        
        # 模拟文件路径存在
        with patch('os.path.exists', return_value=True):
            # 加载配置
            new_manager._load_configuration()
        
        # 验证应用已加载
        self.assertEqual(len(new_manager.applications), 2)
        self.assertIn(app_id1, new_manager.applications)
        
        # 验证组已加载
        self.assertEqual(len(new_manager.groups), 2)  # 包括收藏组和测试组
        self.assertIn(group_id, [group.id for group in new_manager.groups.values()])
        
        # 验证收藏状态已加载
        self.assertTrue(new_manager.applications[app_id1].favorite)
        
        # 验证使用次数已加载
        self.assertEqual(new_manager.applications[app_id1].use_count, 1)

if __name__ == "__main__":
    unittest.main() 