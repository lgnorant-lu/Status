"""
---------------------------------------------------------------
File name:                  test_plugin_manager.py
Author:                     Ignorant-lu
Date created:               2025/05/14
Description:                测试插件管理器
----------------------------------------------------------------

Changed history:            
                            2025/05/14: 初始创建;
----
"""

import unittest
import os
import tempfile
import shutil
from unittest.mock import patch, MagicMock

from status.plugin.plugin_base import PluginBase
from status.plugin.plugin_manager import PluginManager, PluginError, PluginNotFoundError, PluginLoadError, DependencyError


class MockPlugin(PluginBase):
    """用于测试的模拟插件"""
    
    def __init__(self, plugin_id: str, name: str = "", version: str = "1.0.0", dependencies: list = None):
        """初始化模拟插件
        
        Args:
            plugin_id: 插件ID
            name: 插件名称，默认与ID相同
            version: 插件版本
            dependencies: 依赖的插件ID列表
        """
        if not name:
            name = plugin_id
            
        super().__init__(plugin_id, name, version, f"测试插件: {name}")
        
        # 设置依赖
        if dependencies:
            for dep_id in dependencies:
                self.add_dependency(dep_id)
                
        # 模拟方法返回值
        self.load_result = True
        self.enable_result = True
        self.disable_result = True
        self.unload_result = True
        
        # 模拟方法调用次数
        self.load_called = 0
        self.enable_called = 0
        self.disable_called = 0
        self.unload_called = 0
    
    def load(self) -> bool:
        """模拟加载方法
        
        Returns:
            bool: 加载是否成功
        """
        self.load_called += 1
        return self.load_result
    
    def enable(self) -> bool:
        """模拟启用方法
        
        Returns:
            bool: 启用是否成功
        """
        self.enable_called += 1
        return self.enable_result
    
    def disable(self) -> bool:
        """模拟禁用方法
        
        Returns:
            bool: 禁用是否成功
        """
        self.disable_called += 1
        return self.disable_result
    
    def unload(self) -> bool:
        """模拟卸载方法
        
        Returns:
            bool: 卸载是否成功
        """
        self.unload_called += 1
        return self.unload_result


class TestPluginManager(unittest.TestCase):
    """测试PluginManager类"""
    
    def setUp(self):
        """测试前准备"""
        # 创建一个临时插件目录
        self.temp_dir = tempfile.mkdtemp()
        
        # 创建一个新的PluginManager实例
        self.plugin_manager = PluginManager()
        
        # 清空现有数据
        self.plugin_manager.plugins.clear()
        self.plugin_manager.enabled_plugins.clear()
        self.plugin_manager.plugin_paths.clear()
        self.plugin_manager.plugin_configs.clear()
        
        # 添加临时目录作为插件路径
        self.plugin_manager.add_plugin_path(self.temp_dir)
        
        # 创建模拟插件
        self.mock_plugin_a = MockPlugin("plugin_a", "Plugin A")
        self.mock_plugin_b = MockPlugin("plugin_b", "Plugin B", dependencies=["plugin_a"])
        self.mock_plugin_c = MockPlugin("plugin_c", "Plugin C", dependencies=["plugin_b"])
    
    def tearDown(self):
        """测试后清理"""
        # 删除临时目录
        shutil.rmtree(self.temp_dir)
    
    def test_singleton(self):
        """测试单例模式"""
        manager1 = PluginManager()
        manager2 = PluginManager()
        self.assertIs(manager1, manager2)
    
    def test_register_plugin(self):
        """测试注册插件"""
        # 注册插件
        self.plugin_manager.register_plugin(self.mock_plugin_a)
        
        # 验证插件已注册
        self.assertIn("plugin_a", self.plugin_manager.plugins)
        self.assertEqual(self.plugin_manager.plugins["plugin_a"], self.mock_plugin_a)
        
        # 验证依赖
        self.assertEqual(self.mock_plugin_a.get_dependencies(), [])
    
    def test_register_plugin_with_dependencies(self):
        """测试注册带依赖的插件"""
        # 注册插件
        self.plugin_manager.register_plugin(self.mock_plugin_b)
        
        # 验证插件已注册
        self.assertIn("plugin_b", self.plugin_manager.plugins)
        
        # 验证依赖
        self.assertEqual(self.mock_plugin_b.get_dependencies(), ["plugin_a"])
    
    def test_unregister_plugin(self):
        """测试注销插件"""
        # 注册插件
        self.plugin_manager.register_plugin(self.mock_plugin_a)
        
        # 注销插件
        result = self.plugin_manager.unregister_plugin("plugin_a")
        
        # 验证结果
        self.assertTrue(result)
        self.assertNotIn("plugin_a", self.plugin_manager.plugins)
    
    def test_unregister_nonexistent_plugin(self):
        """测试注销不存在的插件"""
        # 注销不存在的插件
        result = self.plugin_manager.unregister_plugin("nonexistent")
        
        # 验证结果
        self.assertFalse(result)
    
    def test_load_plugin(self):
        """测试加载插件"""
        # 注册插件
        self.plugin_manager.register_plugin(self.mock_plugin_a)
        
        # 加载插件
        result = self.plugin_manager.load_plugin("plugin_a")
        
        # 验证结果
        self.assertTrue(result)
        self.assertTrue(self.mock_plugin_a.is_loaded)
        self.assertEqual(self.mock_plugin_a.load_called, 1)
    
    def test_load_nonexistent_plugin(self):
        """测试加载不存在的插件"""
        # 加载不存在的插件
        with self.assertRaises(PluginNotFoundError):
            self.plugin_manager.load_plugin("nonexistent")
    
    def test_load_plugin_failure(self):
        """测试加载插件失败"""
        # 注册插件
        self.plugin_manager.register_plugin(self.mock_plugin_a)
        
        # 设置加载失败
        self.mock_plugin_a.load_result = False
        
        # 加载插件
        with self.assertRaises(PluginLoadError):
            self.plugin_manager.load_plugin("plugin_a")
        
        # 验证结果
        self.assertFalse(self.mock_plugin_a.is_loaded)
    
    def test_load_plugin_with_dependencies(self):
        """测试加载带依赖的插件"""
        # 注册插件
        self.plugin_manager.register_plugin(self.mock_plugin_a)
        self.plugin_manager.register_plugin(self.mock_plugin_b)
        
        # 加载插件
        result = self.plugin_manager.load_plugin("plugin_b")
        
        # 验证结果
        self.assertTrue(result)
        self.assertTrue(self.mock_plugin_a.is_loaded)
        self.assertTrue(self.mock_plugin_b.is_loaded)
        self.assertEqual(self.mock_plugin_a.load_called, 1)
        self.assertEqual(self.mock_plugin_b.load_called, 1)
    
    def test_load_plugin_missing_dependency(self):
        """测试加载缺少依赖的插件"""
        # 注册插件B，但不注册其依赖插件A
        self.plugin_manager.register_plugin(self.mock_plugin_b)
        
        # 加载插件
        with self.assertRaises(DependencyError):
            self.plugin_manager.load_plugin("plugin_b")
    
    def test_enable_plugin(self):
        """测试启用插件"""
        # 注册并加载插件
        self.plugin_manager.register_plugin(self.mock_plugin_a)
        self.plugin_manager.load_plugin("plugin_a")
        
        # 启用插件
        result = self.plugin_manager.enable_plugin("plugin_a")
        
        # 验证结果
        self.assertTrue(result)
        self.assertTrue(self.mock_plugin_a.is_enabled)
        self.assertEqual(self.mock_plugin_a.enable_called, 1)
        self.assertIn("plugin_a", self.plugin_manager.enabled_plugins)
    
    def test_enable_nonexistent_plugin(self):
        """测试启用不存在的插件"""
        # 启用不存在的插件
        with self.assertRaises(PluginNotFoundError):
            self.plugin_manager.enable_plugin("nonexistent")
    
    def test_enable_not_loaded_plugin(self):
        """测试启用未加载的插件"""
        # 注册插件，但不加载
        self.plugin_manager.register_plugin(self.mock_plugin_a)
        
        # 启用插件应该自动加载
        result = self.plugin_manager.enable_plugin("plugin_a")
        
        # 验证结果
        self.assertTrue(result)
        self.assertTrue(self.mock_plugin_a.is_loaded)
        self.assertTrue(self.mock_plugin_a.is_enabled)
        self.assertEqual(self.mock_plugin_a.load_called, 1)
        self.assertEqual(self.mock_plugin_a.enable_called, 1)
    
    def test_enable_plugin_failure(self):
        """测试启用插件失败"""
        # 注册并加载插件
        self.plugin_manager.register_plugin(self.mock_plugin_a)
        self.plugin_manager.load_plugin("plugin_a")
        
        # 设置启用失败
        self.mock_plugin_a.enable_result = False
        
        # 启用插件
        with self.assertRaises(PluginError):
            self.plugin_manager.enable_plugin("plugin_a")
        
        # 验证结果
        self.assertFalse(self.mock_plugin_a.is_enabled)
        self.assertNotIn("plugin_a", self.plugin_manager.enabled_plugins)
    
    def test_enable_plugin_with_dependencies(self):
        """测试启用带依赖的插件"""
        # 注册插件
        self.plugin_manager.register_plugin(self.mock_plugin_a)
        self.plugin_manager.register_plugin(self.mock_plugin_b)
        
        # 启用插件B，应该自动启用插件A
        result = self.plugin_manager.enable_plugin("plugin_b")
        
        # 验证结果
        self.assertTrue(result)
        self.assertTrue(self.mock_plugin_a.is_enabled)
        self.assertTrue(self.mock_plugin_b.is_enabled)
        self.assertIn("plugin_a", self.plugin_manager.enabled_plugins)
        self.assertIn("plugin_b", self.plugin_manager.enabled_plugins)
    
    def test_disable_plugin(self):
        """测试禁用插件"""
        # 注册、加载并启用插件
        self.plugin_manager.register_plugin(self.mock_plugin_a)
        self.plugin_manager.load_plugin("plugin_a")
        self.plugin_manager.enable_plugin("plugin_a")
        
        # 禁用插件
        result = self.plugin_manager.disable_plugin("plugin_a")
        
        # 验证结果
        self.assertTrue(result)
        self.assertFalse(self.mock_plugin_a.is_enabled)
        self.assertEqual(self.mock_plugin_a.disable_called, 1)
        self.assertNotIn("plugin_a", self.plugin_manager.enabled_plugins)
    
    def test_disable_nonexistent_plugin(self):
        """测试禁用不存在的插件"""
        # 禁用不存在的插件
        result = self.plugin_manager.disable_plugin("nonexistent")
        
        # 验证结果
        self.assertFalse(result)
    
    def test_disable_plugin_with_dependents(self):
        """测试禁用有依赖者的插件"""
        # 注册、加载并启用插件
        self.plugin_manager.register_plugin(self.mock_plugin_a)
        self.plugin_manager.register_plugin(self.mock_plugin_b)
        self.plugin_manager.enable_plugin("plugin_b")  # 这会自动启用插件A
        
        # 禁用插件A，应该失败因为插件B依赖它
        with self.assertRaises(DependencyError):
            self.plugin_manager.disable_plugin("plugin_a")
        
        # 验证结果
        self.assertTrue(self.mock_plugin_a.is_enabled)
        self.assertIn("plugin_a", self.plugin_manager.enabled_plugins)
    
    def test_unload_plugin(self):
        """测试卸载插件"""
        # 注册并加载插件
        self.plugin_manager.register_plugin(self.mock_plugin_a)
        self.plugin_manager.load_plugin("plugin_a")
        
        # 卸载插件
        result = self.plugin_manager.unload_plugin("plugin_a")
        
        # 验证结果
        self.assertTrue(result)
        self.assertFalse(self.mock_plugin_a.is_loaded)
        self.assertEqual(self.mock_plugin_a.unload_called, 1)
    
    def test_unload_enabled_plugin(self):
        """测试卸载已启用的插件"""
        # 注册、加载并启用插件
        self.plugin_manager.register_plugin(self.mock_plugin_a)
        self.plugin_manager.enable_plugin("plugin_a")
        
        # 卸载插件，应该先禁用再卸载
        result = self.plugin_manager.unload_plugin("plugin_a")
        
        # 验证结果
        self.assertTrue(result)
        self.assertFalse(self.mock_plugin_a.is_enabled)
        self.assertFalse(self.mock_plugin_a.is_loaded)
        self.assertEqual(self.mock_plugin_a.disable_called, 1)
        self.assertEqual(self.mock_plugin_a.unload_called, 1)
    
    def test_unload_plugin_with_dependents(self):
        """测试卸载有依赖者的插件"""
        # 注册、加载插件
        self.plugin_manager.register_plugin(self.mock_plugin_a)
        self.plugin_manager.register_plugin(self.mock_plugin_b)
        self.plugin_manager.load_plugin("plugin_b")  # 这会自动加载插件A
        
        # 卸载插件A，应该失败因为插件B依赖它
        with self.assertRaises(DependencyError):
            self.plugin_manager.unload_plugin("plugin_a")
        
        # 验证结果
        self.assertTrue(self.mock_plugin_a.is_loaded)
    
    def test_get_plugin(self):
        """测试获取插件"""
        # 注册插件
        self.plugin_manager.register_plugin(self.mock_plugin_a)
        
        # 获取插件
        plugin = self.plugin_manager.get_plugin("plugin_a")
        
        # 验证结果
        self.assertEqual(plugin, self.mock_plugin_a)
    
    def test_get_nonexistent_plugin(self):
        """测试获取不存在的插件"""
        # 获取不存在的插件
        plugin = self.plugin_manager.get_plugin("nonexistent")
        
        # 验证结果
        self.assertIsNone(plugin)
    
    def test_get_all_plugins(self):
        """测试获取所有插件"""
        # 注册插件
        self.plugin_manager.register_plugin(self.mock_plugin_a)
        self.plugin_manager.register_plugin(self.mock_plugin_b)
        
        # 获取所有插件
        plugins = self.plugin_manager.get_all_plugins()
        
        # 验证结果
        self.assertEqual(len(plugins), 2)
        self.assertIn("plugin_a", plugins)
        self.assertIn("plugin_b", plugins)
    
    def test_get_enabled_plugins(self):
        """测试获取已启用的插件"""
        # 注册并启用插件
        self.plugin_manager.register_plugin(self.mock_plugin_a)
        self.plugin_manager.register_plugin(self.mock_plugin_b)
        self.plugin_manager.enable_plugin("plugin_a")
        
        # 获取已启用的插件
        plugins = self.plugin_manager.get_enabled_plugins()
        
        # 验证结果
        self.assertEqual(len(plugins), 1)
        self.assertIn("plugin_a", plugins)
        self.assertNotIn("plugin_b", plugins)
    
    def test_set_plugin_config(self):
        """测试设置插件配置"""
        # 注册插件
        self.plugin_manager.register_plugin(self.mock_plugin_a)
        
        # 设置配置
        config = {"key": "value"}
        self.plugin_manager.set_plugin_config("plugin_a", config)
        
        # 验证结果
        self.assertEqual(self.mock_plugin_a.get_config(), config)
    
    def test_set_plugin_config_before_registration(self):
        """测试在注册前设置插件配置"""
        # 设置配置
        config = {"key": "value"}
        self.plugin_manager.set_plugin_config("plugin_a", config)
        
        # 注册插件
        self.plugin_manager.register_plugin(self.mock_plugin_a)
        
        # 验证结果
        self.assertEqual(self.mock_plugin_a.get_config(), config)
    
    def test_get_plugin_config(self):
        """测试获取插件配置"""
        # 注册插件并设置配置
        self.plugin_manager.register_plugin(self.mock_plugin_a)
        config = {"key": "value"}
        self.mock_plugin_a.set_config(config)
        
        # 获取配置
        result = self.plugin_manager.get_plugin_config("plugin_a")
        
        # 验证结果
        self.assertEqual(result, config)
    
    def test_get_nonexistent_plugin_config(self):
        """测试获取不存在的插件配置"""
        # 获取不存在的插件配置
        result = self.plugin_manager.get_plugin_config("nonexistent")
        
        # 验证结果
        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main() 