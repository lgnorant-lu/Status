"""
---------------------------------------------------------------
File name:                  test_import_export.py
Author:                     Ignorant-lu
Date created:               2023/11/29
Description:                测试启动器的导入/导出功能
----------------------------------------------------------------

Changed history:            
                            2023/11/29: 初始创建;
                            2023/11/29: 修复测试问题;
----
"""

import os
import json
import unittest
import tempfile
from datetime import datetime
from unittest.mock import patch, MagicMock

from status.launcher.launcher_types import LaunchedApplication, LauncherGroup, LaunchMode
from status.launcher.launcher_manager import LauncherManager


class TestImportExport(unittest.TestCase):
    """测试启动器的导入/导出功能"""

    def setUp(self):
        """测试前设置"""
        # 创建LauncherManager实例
        self.manager = LauncherManager()
        
        # 模拟配置管理器
        self.config_manager_mock = MagicMock()
        self.manager.config_manager = self.config_manager_mock
        
        # 创建示例应用
        self.app1 = LaunchedApplication(
            name="测试应用1",
            path="C:\\test\\app1.exe",
            icon_path="C:\\test\\icon1.ico",
            arguments=["-arg1", "--arg2=value"],
            description="测试应用1描述",
            tags=["测试", "应用1"],
            launch_mode=LaunchMode.NORMAL,
            environment_variables={"TEST_VAR1": "value1", "TEST_VAR2": "value2"}
        )
        
        self.app2 = LaunchedApplication(
            name="测试应用2",
            path="C:\\test\\app2.exe",
            arguments=[],
            launch_mode=LaunchMode.MINIMIZED
        )
        
        # 创建示例分组
        self.group1 = LauncherGroup(
            name="测试分组1",
            icon="group_icon.png",
            description="测试分组1描述"
        )
        
    @patch('os.path.exists')
    def test_export_applications(self, mock_exists):
        """测试导出应用程序"""
        # 模拟路径存在
        mock_exists.return_value = True
        
        # 手动添加应用和分组
        self.manager.applications[self.app1.id] = self.app1
        self.manager.applications[self.app2.id] = self.app2
        self.manager.groups[self.group1.id] = self.group1
        
        # 创建临时文件
        with tempfile.NamedTemporaryFile(delete=False, suffix='.json') as temp_file:
            temp_path = temp_file.name
            
        try:
            # 导出所有应用
            result = self.manager.export_applications(temp_path)
            self.assertTrue(result, "导出所有应用应该成功")
            
            # 验证导出文件
            with open(temp_path, 'r', encoding='utf-8') as f:
                export_data = json.load(f)
                
            # 检查导出数据格式
            self.assertIn("applications", export_data)
            self.assertIn("format_version", export_data)
            self.assertIn("export_time", export_data)
            
            # 检查应用数量
            self.assertEqual(len(export_data["applications"]), 2)
            
            # 检查第一个应用的属性
            exported_app1 = next((app for app in export_data["applications"] 
                               if app["name"] == "测试应用1"), None)
            self.assertIsNotNone(exported_app1)
            self.assertEqual(exported_app1["path"], "C:\\test\\app1.exe")
            self.assertEqual(exported_app1["icon_path"], "C:\\test\\icon1.ico")
            self.assertEqual(exported_app1["launch_mode"], "NORMAL")
            self.assertEqual(len(exported_app1["environment_variables"]), 2)
            
            # 只导出指定应用
            result = self.manager.export_applications(temp_path, [self.app1.id])
            self.assertTrue(result, "导出指定应用应该成功")
            
            # 验证导出文件
            with open(temp_path, 'r', encoding='utf-8') as f:
                export_data = json.load(f)
                
            # 检查应用数量
            self.assertEqual(len(export_data["applications"]), 1)
            self.assertEqual(export_data["applications"][0]["name"], "测试应用1")
            
        finally:
            # 删除临时文件
            if os.path.exists(temp_path):
                os.unlink(temp_path)
                
    @patch('os.path.exists')
    def test_import_applications(self, mock_exists):
        """测试导入应用程序"""
        # 模拟路径存在
        mock_exists.return_value = True
        
        # 创建导出数据
        export_data = {
            "applications": [
                {
                    "id": "imported_app_1",
                    "name": "导入测试应用1",
                    "path": "C:\\import\\app1.exe",
                    "icon_path": "C:\\import\\icon1.ico",
                    "arguments": ["-test"],
                    "description": "导入测试描述",
                    "launch_mode": "MAXIMIZED",
                    "environment_variables": {
                        "IMPORT_VAR": "import_value"
                    },
                    "tags": ["导入", "测试"],
                    "favorite": True,
                    "working_directory": "C:\\import"
                },
                {
                    "id": "imported_app_2",
                    "name": "导入测试应用2",
                    "path": "C:\\import\\app2.exe",
                    "launch_mode": "NORMAL"
                }
            ],
            "format_version": "1.0",
            "export_time": datetime.now().isoformat()
        }
        
        # 创建临时文件
        with tempfile.NamedTemporaryFile(delete=False, mode='w', suffix='.json', encoding='utf-8') as temp_file:
            temp_path = temp_file.name
            json.dump(export_data, temp_file, ensure_ascii=False)
            
        try:
            # 清空应用列表
            self.manager.applications = {}
            
            # 导入应用
            success_count, fail_count, errors = self.manager.import_applications(temp_path)
            
            # 验证结果
            self.assertEqual(success_count, 2, "应该成功导入2个应用")
            self.assertEqual(fail_count, 0, "不应该有导入失败")
            self.assertEqual(len(errors), 0, "不应该有错误消息")
            
            # 验证导入的应用
            self.assertEqual(len(self.manager.applications), 2)
            
            # 检查第一个应用
            app1 = self.manager.get_application("imported_app_1")
            self.assertIsNotNone(app1)
            self.assertEqual(app1.name, "导入测试应用1")
            self.assertEqual(app1.path, "C:\\import\\app1.exe")
            self.assertEqual(app1.launch_mode, LaunchMode.MAXIMIZED)
            self.assertEqual(app1.environment_variables["IMPORT_VAR"], "import_value")
            self.assertTrue(app1.favorite)
            
            # 检查第二个应用
            app2 = self.manager.get_application("imported_app_2")
            self.assertIsNotNone(app2)
            self.assertEqual(app2.name, "导入测试应用2")
            
            # 测试导入无效文件格式
            with tempfile.NamedTemporaryFile(delete=False, mode='w', suffix='.json', encoding='utf-8') as invalid_file:
                invalid_path = invalid_file.name
                json.dump({"invalid": "format"}, invalid_file)
                
            success_count, fail_count, errors = self.manager.import_applications(invalid_path)
            self.assertEqual(success_count, 0)
            self.assertEqual(fail_count, 0)
            self.assertEqual(len(errors), 1)
            
            # 清理无效文件
            os.unlink(invalid_path)
            
        finally:
            # 删除临时文件
            if os.path.exists(temp_path):
                os.unlink(temp_path)
                
    @patch('os.path.exists')
    def test_export_import_group(self, mock_exists):
        """测试导出和导入分组"""
        # 模拟路径存在
        mock_exists.return_value = True
        
        # 手动添加应用和分组
        self.manager.applications[self.app1.id] = self.app1
        self.manager.groups[self.group1.id] = self.group1
        self.group1.add_application(self.app1.id)
        
        # 创建临时文件
        with tempfile.NamedTemporaryFile(delete=False, suffix='.json') as temp_file:
            temp_path = temp_file.name
            
        try:
            # 导出分组
            result = self.manager.export_group(self.group1.id, temp_path)
            self.assertTrue(result, "导出分组应该成功")
            
            # 验证导出文件
            with open(temp_path, 'r', encoding='utf-8') as f:
                export_data = json.load(f)
                
            # 检查导出数据格式
            self.assertIn("group", export_data)
            self.assertIn("applications", export_data)
            
            # 检查分组数据
            self.assertEqual(export_data["group"]["name"], "测试分组1")
            self.assertEqual(export_data["group"]["icon"], "group_icon.png")
            
            # 检查应用数量
            self.assertEqual(len(export_data["applications"]), 1)
            self.assertEqual(export_data["applications"][0]["name"], "测试应用1")
            
            # 清空管理器
            self.manager.applications = {}
            self.manager.groups = {}
            
            # 导入分组
            success, group_id, success_count, fail_count = self.manager.import_group(temp_path)
            
            # 验证结果
            self.assertTrue(success)
            self.assertIsNotNone(group_id)
            self.assertEqual(success_count, 1)
            self.assertEqual(fail_count, 0)
            
            # 验证导入的分组
            imported_group = self.manager.get_group(group_id)
            self.assertIsNotNone(imported_group)
            self.assertEqual(imported_group.name, "测试分组1")
            
            # 验证导入的应用
            self.assertEqual(len(self.manager.applications), 1)
            
            # 验证应用在分组中
            self.assertEqual(len(imported_group.applications), 1)
            
        finally:
            # 删除临时文件
            if os.path.exists(temp_path):
                os.unlink(temp_path)


if __name__ == '__main__':
    unittest.main() 