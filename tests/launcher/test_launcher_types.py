"""
---------------------------------------------------------------
File name:                  test_launcher_types.py
Author:                     Ignorant-lu
Date created:               2023/11/28
Description:                快捷启动器数据类型的单元测试
----------------------------------------------------------------

Changed history:
                           2023/11/28: 初始创建
                           2023/11/29: 修复属性名称和方法名称
----
"""

import unittest
import os
import json
from datetime import datetime
from pathlib import Path
from unittest.mock import patch, MagicMock

from status.launcher.launcher_types import (
    LaunchStatus, 
    LaunchResult, 
    LaunchedApplication, 
    LauncherGroup
)

class TestLaunchResult(unittest.TestCase):
    def test_init(self):
        """测试LaunchResult初始化"""
        result = LaunchResult(LaunchStatus.SUCCESS, "启动成功")
        self.assertEqual(result.status, LaunchStatus.SUCCESS)
        self.assertEqual(result.message, "启动成功")
        self.assertIsNone(result.error)
        self.assertIsInstance(result.timestamp, datetime)
    
    def test_success(self):
        """测试成功状态判断"""
        success_result = LaunchResult(LaunchStatus.SUCCESS, "启动成功")
        self.assertTrue(success_result.success)
        
        error_result = LaunchResult(LaunchStatus.EXECUTION_ERROR, "启动失败", Exception("测试错误"))
        self.assertFalse(error_result.success)
    
    def test_str_representation(self):
        """测试字符串表示"""
        result = LaunchResult(LaunchStatus.SUCCESS, "启动成功")
        str_repr = str(result)
        self.assertIn("启动成功", str_repr)
        
        error_result = LaunchResult(LaunchStatus.NOT_FOUND, "应用不存在")
        str_repr = str(error_result)
        self.assertIn("NOT_FOUND", str_repr)
        self.assertIn("应用不存在", str_repr)

class TestLaunchedApplication(unittest.TestCase):
    def setUp(self):
        """测试前准备"""
        # 模拟文件存在性检查
        self.patcher = patch('os.path.exists', return_value=True)
        self.mock_exists = self.patcher.start()
        
        self.app = LaunchedApplication(
            name="测试应用",
            path=r"C:\Windows\notepad.exe",
            icon_path=r"C:\Windows\notepad.exe",
            arguments=["test.txt"],
            description="测试应用描述",
            tags=["测试", "编辑器"],
            working_directory=r"C:\Windows"
        )
    
    def tearDown(self):
        """测试清理"""
        self.patcher.stop()
    
    def test_init(self):
        """测试LaunchedApplication初始化"""
        self.assertEqual(self.app.name, "测试应用")
        self.assertEqual(self.app.path, r"C:\Windows\notepad.exe")
        self.assertEqual(self.app.arguments, ["test.txt"])
        self.assertEqual(self.app.description, "测试应用描述")
        self.assertEqual(self.app.tags, ["测试", "编辑器"])
        self.assertEqual(self.app.working_directory, r"C:\Windows")
        self.assertEqual(self.app.use_count, 0)
        self.assertFalse(self.app.favorite)
        self.assertIsNotNone(self.app.id)
    
    def test_to_dict(self):
        """测试转换为字典"""
        app_dict = self.app.to_dict()
        self.assertEqual(app_dict["name"], "测试应用")
        self.assertEqual(app_dict["path"], r"C:\Windows\notepad.exe")
        self.assertEqual(app_dict["description"], "测试应用描述")
        self.assertEqual(app_dict["tags"], ["测试", "编辑器"])
        self.assertEqual(app_dict["working_directory"], r"C:\Windows")
        self.assertEqual(app_dict["use_count"], 0)
        self.assertEqual(app_dict["favorite"], False)
    
    def test_from_dict(self):
        """测试从字典创建应用"""
        app_dict = self.app.to_dict()
        new_app = LaunchedApplication.from_dict(app_dict)
        
        self.assertEqual(new_app.name, self.app.name)
        self.assertEqual(new_app.path, self.app.path)
        self.assertEqual(new_app.description, self.app.description)
        self.assertEqual(new_app.tags, self.app.tags)
        self.assertEqual(new_app.id, self.app.id)
    
    def test_increase_usage_count(self):
        """测试增加使用次数"""
        initial_count = self.app.use_count
        self.app.increase_usage_count()
        self.assertEqual(self.app.use_count, initial_count + 1)
        self.assertIsNotNone(self.app.last_used)
    
    def test_toggle_favorite(self):
        """测试切换收藏状态"""
        self.assertFalse(self.app.favorite)
        
        result = self.app.toggle_favorite()
        self.assertTrue(self.app.favorite)
        self.assertTrue(result)
        
        result = self.app.toggle_favorite()
        self.assertFalse(self.app.favorite)
        self.assertFalse(result)

class TestLauncherGroup(unittest.TestCase):
    def setUp(self):
        """测试前准备"""
        # 模拟文件存在性检查
        self.patcher = patch('os.path.exists', return_value=True)
        self.mock_exists = self.patcher.start()
        
        self.app1 = LaunchedApplication(name="应用1", path=r"C:\app1.exe")
        self.app2 = LaunchedApplication(name="应用2", path=r"C:\app2.exe")
        
        self.group = LauncherGroup(
            name="测试组",
            icon="group_icon.png",
            description="测试应用组"
        )
    
    def tearDown(self):
        """测试清理"""
        self.patcher.stop()
    
    def test_init(self):
        """测试LauncherGroup初始化"""
        self.assertEqual(self.group.name, "测试组")
        self.assertEqual(self.group.icon, "group_icon.png")
        self.assertEqual(self.group.description, "测试应用组")
        self.assertEqual(self.group.applications, [])
    
    def test_add_application(self):
        """测试添加应用"""
        self.group.add_application(self.app1.id)
        self.assertIn(self.app1.id, self.group.applications)
        
        # 添加重复应用，不应有变化
        result = self.group.add_application(self.app1.id)
        self.assertFalse(result)
        self.assertEqual(self.group.applications.count(self.app1.id), 1)
    
    def test_remove_application(self):
        """测试移除应用"""
        self.group.add_application(self.app1.id)
        self.group.add_application(self.app2.id)
        
        result = self.group.remove_application(self.app1.id)
        self.assertTrue(result)
        self.assertNotIn(self.app1.id, self.group.applications)
        self.assertIn(self.app2.id, self.group.applications)
        
        # 移除不存在的应用，应返回False
        result = self.group.remove_application("non-existent-id")
        self.assertFalse(result)
    
    def test_contains_application(self):
        """测试是否包含应用"""
        self.group.add_application(self.app1.id)
        
        self.assertTrue(self.group.contains_application(self.app1.id))
        self.assertFalse(self.group.contains_application(self.app2.id))
    
    def test_to_dict(self):
        """测试转换为字典"""
        self.group.add_application(self.app1.id)
        self.group.add_application(self.app2.id)
        
        group_dict = self.group.to_dict()
        self.assertEqual(group_dict["name"], "测试组")
        self.assertEqual(group_dict["icon"], "group_icon.png")
        self.assertEqual(group_dict["description"], "测试应用组")
        self.assertEqual(len(group_dict["applications"]), 2)
        self.assertIn(self.app1.id, group_dict["applications"])
        self.assertIn(self.app2.id, group_dict["applications"])
    
    def test_from_dict(self):
        """测试从字典创建组"""
        self.group.add_application(self.app1.id)
        group_dict = self.group.to_dict()
        
        new_group = LauncherGroup.from_dict(group_dict)
        self.assertEqual(new_group.name, self.group.name)
        self.assertEqual(new_group.icon, self.group.icon)
        self.assertEqual(new_group.description, self.group.description)
        self.assertEqual(new_group.applications, self.group.applications)

if __name__ == "__main__":
    unittest.main() 