"""
测试配置管理器
"""

import unittest
import os
import json
import tempfile
from unittest.mock import patch, MagicMock

from status.core.config import ConfigManager, ConfigEventType
from status.core.config.config_types import DEFAULT_CONFIG


class TestConfigManager(unittest.TestCase):
    """测试配置管理器"""
    
    def setUp(self):
        """测试前准备"""
        # 重置单例
        ConfigManager._instance = None
        self.manager = ConfigManager.get_instance()
        
        # 创建临时目录
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_file = os.path.join(self.temp_dir.name, "test_config.json")
    
    def tearDown(self):
        """测试后清理"""
        # 重置单例
        ConfigManager._instance = None
        
        # 删除临时目录
        self.temp_dir.cleanup()
    
    def test_singleton(self):
        """测试单例模式"""
        manager1 = ConfigManager.get_instance()
        manager2 = ConfigManager.get_instance()
        self.assertIs(manager1, manager2)
    
    def test_load_default_config(self):
        """测试加载默认配置"""
        self.manager.load_default_config()
        self.assertEqual(self.manager.config, DEFAULT_CONFIG)
    
    def test_get_simple_key(self):
        """测试获取简单配置项"""
        # 设置测试配置
        self.manager.config = {
            "test_key": "test_value",
            "test_dict": {
                "nested_key": "nested_value"
            }
        }
        
        # 测试获取存在的键
        self.assertEqual(self.manager.get("test_key"), "test_value")
        
        # 测试获取不存在的键
        self.assertIsNone(self.manager.get("non_existent_key"))
        
        # 测试获取不存在的键并指定默认值
        self.assertEqual(self.manager.get("non_existent_key", "default"), "default")
    
    def test_get_nested_key(self):
        """测试获取嵌套配置项"""
        # 设置测试配置
        self.manager.config = {
            "parent": {
                "child": {
                    "grandchild": "value"
                }
            }
        }
        
        # 测试获取嵌套键
        self.assertEqual(self.manager.get("parent.child.grandchild"), "value")
        
        # 测试获取不存在的嵌套键
        self.assertIsNone(self.manager.get("parent.non_existent"))
        self.assertIsNone(self.manager.get("parent.child.non_existent"))
        self.assertIsNone(self.manager.get("non_existent.child"))
        
        # 测试获取不存在的嵌套键并指定默认值
        self.assertEqual(self.manager.get("parent.non_existent", "default"), "default")
    
    def test_set_simple_key(self):
        """测试设置简单配置项"""
        # 设置测试配置
        self.manager.config = {}
        
        # 测试设置键值
        self.assertTrue(self.manager.set("test_key", "test_value"))
        self.assertEqual(self.manager.config["test_key"], "test_value")
        
        # 测试更新键值
        self.assertTrue(self.manager.set("test_key", "updated_value"))
        self.assertEqual(self.manager.config["test_key"], "updated_value")


if __name__ == "__main__":
    unittest.main()
