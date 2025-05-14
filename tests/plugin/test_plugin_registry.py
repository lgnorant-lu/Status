"""
---------------------------------------------------------------
File name:                  test_plugin_registry.py
Author:                     Ignorant-lu
Date created:               2025/05/14
Description:                测试插件注册表
----------------------------------------------------------------

Changed history:            
                            2025/05/14: 初始创建;
----
"""

import unittest
from unittest.mock import MagicMock

from status.plugin.plugin_registry import PluginRegistry, ExtensionHandler, ExtensionPoint, PluginType


class TestExtensionHandler(unittest.TestCase):
    """测试ExtensionHandler类"""
    
    def setUp(self):
        """测试前准备"""
        self.extension_point = "test_extension_point"
        self.handler = ExtensionHandler(self.extension_point, "Test Extension Point")
    
    def test_register_extension(self):
        """测试注册扩展"""
        # 注册扩展
        extension = MagicMock()
        self.handler.register_extension("plugin_a", extension)
        
        # 验证结果
        self.assertIn("plugin_a", self.handler.extensions)
        self.assertEqual(self.handler.extensions["plugin_a"], extension)
    
    def test_register_existing_extension(self):
        """测试注册已存在的扩展"""
        # 注册扩展
        extension1 = MagicMock()
        extension2 = MagicMock()
        self.handler.register_extension("plugin_a", extension1)
        self.handler.register_extension("plugin_a", extension2)
        
        # 验证结果
        self.assertEqual(self.handler.extensions["plugin_a"], extension2)
    
    def test_unregister_extension(self):
        """测试注销扩展"""
        # 注册扩展
        extension = MagicMock()
        self.handler.register_extension("plugin_a", extension)
        
        # 注销扩展
        result = self.handler.unregister_extension("plugin_a")
        
        # 验证结果
        self.assertTrue(result)
        self.assertNotIn("plugin_a", self.handler.extensions)
    
    def test_unregister_nonexistent_extension(self):
        """测试注销不存在的扩展"""
        # 注销不存在的扩展
        result = self.handler.unregister_extension("nonexistent")
        
        # 验证结果
        self.assertFalse(result)
    
    def test_get_extension(self):
        """测试获取扩展"""
        # 注册扩展
        extension = MagicMock()
        self.handler.register_extension("plugin_a", extension)
        
        # 获取扩展
        result = self.handler.get_extension("plugin_a")
        
        # 验证结果
        self.assertEqual(result, extension)
    
    def test_get_nonexistent_extension(self):
        """测试获取不存在的扩展"""
        # 获取不存在的扩展
        result = self.handler.get_extension("nonexistent")
        
        # 验证结果
        self.assertIsNone(result)
    
    def test_get_all_extensions(self):
        """测试获取所有扩展"""
        # 注册扩展
        extension1 = MagicMock()
        extension2 = MagicMock()
        self.handler.register_extension("plugin_a", extension1)
        self.handler.register_extension("plugin_b", extension2)
        
        # 获取所有扩展
        extensions = self.handler.get_all_extensions()
        
        # 验证结果
        self.assertEqual(len(extensions), 2)
        self.assertIn("plugin_a", extensions)
        self.assertIn("plugin_b", extensions)
        self.assertEqual(extensions["plugin_a"], extension1)
        self.assertEqual(extensions["plugin_b"], extension2)


class TestPluginRegistry(unittest.TestCase):
    """测试PluginRegistry类"""
    
    def setUp(self):
        """测试前准备"""
        self.registry = PluginRegistry()
        
        # 清空现有数据
        self.registry.plugin_types.clear()
        self.registry.extension_handlers.clear()
        self.registry.plugin_extensions.clear()
    
    def test_singleton(self):
        """测试单例模式"""
        registry1 = PluginRegistry()
        registry2 = PluginRegistry()
        self.assertIs(registry1, registry2)
    
    def test_register_plugin_type(self):
        """测试注册插件类型"""
        # 注册插件类型
        self.registry.register_plugin_type("plugin_a", "type1")
        
        # 验证结果
        self.assertIn("type1", self.registry.plugin_types)
        self.assertIn("plugin_a", self.registry.plugin_types["type1"])
    
    def test_register_plugin_type_multiple(self):
        """测试注册多个插件类型"""
        # 注册插件类型
        self.registry.register_plugin_type("plugin_a", "type1")
        self.registry.register_plugin_type("plugin_a", "type2")
        self.registry.register_plugin_type("plugin_b", "type1")
        
        # 验证结果
        self.assertIn("type1", self.registry.plugin_types)
        self.assertIn("type2", self.registry.plugin_types)
        self.assertIn("plugin_a", self.registry.plugin_types["type1"])
        self.assertIn("plugin_a", self.registry.plugin_types["type2"])
        self.assertIn("plugin_b", self.registry.plugin_types["type1"])
    
    def test_unregister_plugin_type(self):
        """测试注销插件类型"""
        # 注册插件类型
        self.registry.register_plugin_type("plugin_a", "type1")
        
        # 注销插件类型
        result = self.registry.unregister_plugin_type("plugin_a", "type1")
        
        # 验证结果
        self.assertTrue(result)
        self.assertNotIn("type1", self.registry.plugin_types)
    
    def test_unregister_plugin_type_with_multiple_plugins(self):
        """测试注销有多个插件的类型"""
        # 注册插件类型
        self.registry.register_plugin_type("plugin_a", "type1")
        self.registry.register_plugin_type("plugin_b", "type1")
        
        # 注销插件类型
        result = self.registry.unregister_plugin_type("plugin_a", "type1")
        
        # 验证结果
        self.assertTrue(result)
        self.assertIn("type1", self.registry.plugin_types)
        self.assertNotIn("plugin_a", self.registry.plugin_types["type1"])
        self.assertIn("plugin_b", self.registry.plugin_types["type1"])
    
    def test_unregister_nonexistent_plugin_type(self):
        """测试注销不存在的插件类型"""
        # 注销不存在的插件类型
        result = self.registry.unregister_plugin_type("nonexistent", "type1")
        
        # 验证结果
        self.assertFalse(result)
    
    def test_get_plugins_by_type(self):
        """测试获取特定类型的所有插件"""
        # 注册插件类型
        self.registry.register_plugin_type("plugin_a", "type1")
        self.registry.register_plugin_type("plugin_b", "type1")
        self.registry.register_plugin_type("plugin_c", "type2")
        
        # 获取特定类型的所有插件
        plugins = self.registry.get_plugins_by_type("type1")
        
        # 验证结果
        self.assertEqual(len(plugins), 2)
        self.assertIn("plugin_a", plugins)
        self.assertIn("plugin_b", plugins)
        self.assertNotIn("plugin_c", plugins)
    
    def test_get_plugins_by_nonexistent_type(self):
        """测试获取不存在类型的所有插件"""
        # 获取不存在类型的所有插件
        plugins = self.registry.get_plugins_by_type("nonexistent")
        
        # 验证结果
        self.assertEqual(len(plugins), 0)
    
    def test_get_plugin_types(self):
        """测试获取插件的所有类型"""
        # 注册插件类型
        self.registry.register_plugin_type("plugin_a", "type1")
        self.registry.register_plugin_type("plugin_a", "type2")
        self.registry.register_plugin_type("plugin_b", "type1")
        
        # 获取插件的所有类型
        types = self.registry.get_plugin_types("plugin_a")
        
        # 验证结果
        self.assertEqual(len(types), 2)
        self.assertIn("type1", types)
        self.assertIn("type2", types)
    
    def test_get_nonexistent_plugin_types(self):
        """测试获取不存在插件的所有类型"""
        # 获取不存在插件的所有类型
        types = self.registry.get_plugin_types("nonexistent")
        
        # 验证结果
        self.assertEqual(len(types), 0)
    
    def test_register_extension_point(self):
        """测试注册扩展点"""
        # 注册扩展点
        handler = self.registry.register_extension_point("ext_point1", "Extension Point 1")
        
        # 验证结果
        self.assertIn("ext_point1", self.registry.extension_handlers)
        self.assertEqual(self.registry.extension_handlers["ext_point1"], handler)
        self.assertEqual(handler.extension_point, "ext_point1")
        self.assertEqual(handler.description, "Extension Point 1")
    
    def test_register_existing_extension_point(self):
        """测试注册已存在的扩展点"""
        # 注册扩展点
        handler1 = self.registry.register_extension_point("ext_point1", "Extension Point 1")
        handler2 = self.registry.register_extension_point("ext_point1", "Extension Point 1 New")
        
        # 验证结果
        self.assertIs(handler1, handler2)
        self.assertEqual(handler1.description, "Extension Point 1")
    
    def test_unregister_extension_point(self):
        """测试注销扩展点"""
        # 注册扩展点
        self.registry.register_extension_point("ext_point1")
        
        # 注销扩展点
        result = self.registry.unregister_extension_point("ext_point1")
        
        # 验证结果
        self.assertTrue(result)
        self.assertNotIn("ext_point1", self.registry.extension_handlers)
    
    def test_unregister_extension_point_with_extensions(self):
        """测试注销有扩展的扩展点"""
        # 注册扩展点
        handler = self.registry.register_extension_point("ext_point1")
        
        # 注册扩展
        handler.register_extension("plugin_a", MagicMock())
        
        # 注销扩展点
        result = self.registry.unregister_extension_point("ext_point1")
        
        # 验证结果
        self.assertFalse(result)
        self.assertIn("ext_point1", self.registry.extension_handlers)
    
    def test_unregister_nonexistent_extension_point(self):
        """测试注销不存在的扩展点"""
        # 注销不存在的扩展点
        result = self.registry.unregister_extension_point("nonexistent")
        
        # 验证结果
        self.assertFalse(result)
    
    def test_get_extension_handler(self):
        """测试获取扩展点处理器"""
        # 注册扩展点
        handler = self.registry.register_extension_point("ext_point1")
        
        # 获取扩展点处理器
        result = self.registry.get_extension_handler("ext_point1")
        
        # 验证结果
        self.assertEqual(result, handler)
    
    def test_get_nonexistent_extension_handler(self):
        """测试获取不存在的扩展点处理器"""
        # 获取不存在的扩展点处理器
        result = self.registry.get_extension_handler("nonexistent")
        
        # 验证结果
        self.assertIsNone(result)
    
    def test_register_extension(self):
        """测试注册扩展"""
        # 注册扩展点
        self.registry.register_extension_point("ext_point1")
        
        # 注册扩展
        extension = MagicMock()
        result = self.registry.register_extension("plugin_a", "ext_point1", extension)
        
        # 验证结果
        self.assertTrue(result)
        self.assertIn("plugin_a", self.registry.plugin_extensions)
        self.assertIn("ext_point1", self.registry.plugin_extensions["plugin_a"])
        self.assertEqual(
            self.registry.extension_handlers["ext_point1"].get_extension("plugin_a"),
            extension
        )
    
    def test_register_extension_nonexistent_extension_point(self):
        """测试注册到不存在的扩展点"""
        # 注册扩展
        extension = MagicMock()
        result = self.registry.register_extension("plugin_a", "nonexistent", extension)
        
        # 验证结果
        self.assertFalse(result)
        self.assertNotIn("plugin_a", self.registry.plugin_extensions)
    
    def test_unregister_extension(self):
        """测试注销扩展"""
        # 注册扩展点和扩展
        self.registry.register_extension_point("ext_point1")
        extension = MagicMock()
        self.registry.register_extension("plugin_a", "ext_point1", extension)
        
        # 注销扩展
        result = self.registry.unregister_extension("plugin_a", "ext_point1")
        
        # 验证结果
        self.assertTrue(result)
        self.assertNotIn("plugin_a", self.registry.plugin_extensions)
        self.assertIsNone(
            self.registry.extension_handlers["ext_point1"].get_extension("plugin_a")
        )
    
    def test_unregister_extension_multiple_extension_points(self):
        """测试注销有多个扩展点的扩展"""
        # 注册扩展点和扩展
        self.registry.register_extension_point("ext_point1")
        self.registry.register_extension_point("ext_point2")
        extension1 = MagicMock()
        extension2 = MagicMock()
        self.registry.register_extension("plugin_a", "ext_point1", extension1)
        self.registry.register_extension("plugin_a", "ext_point2", extension2)
        
        # 注销扩展
        result = self.registry.unregister_extension("plugin_a", "ext_point1")
        
        # 验证结果
        self.assertTrue(result)
        self.assertIn("plugin_a", self.registry.plugin_extensions)
        self.assertNotIn("ext_point1", self.registry.plugin_extensions["plugin_a"])
        self.assertIn("ext_point2", self.registry.plugin_extensions["plugin_a"])
        self.assertIsNone(
            self.registry.extension_handlers["ext_point1"].get_extension("plugin_a")
        )
        self.assertEqual(
            self.registry.extension_handlers["ext_point2"].get_extension("plugin_a"),
            extension2
        )
    
    def test_unregister_extension_nonexistent_extension_point(self):
        """测试从不存在的扩展点注销扩展"""
        # 注销扩展
        result = self.registry.unregister_extension("plugin_a", "nonexistent")
        
        # 验证结果
        self.assertFalse(result)
    
    def test_unregister_all_plugin_extensions(self):
        """测试注销插件的所有扩展"""
        # 注册扩展点和扩展
        self.registry.register_extension_point("ext_point1")
        self.registry.register_extension_point("ext_point2")
        extension1 = MagicMock()
        extension2 = MagicMock()
        self.registry.register_extension("plugin_a", "ext_point1", extension1)
        self.registry.register_extension("plugin_a", "ext_point2", extension2)
        
        # 注册插件类型
        self.registry.register_plugin_type("plugin_a", "type1")
        
        # 注销插件的所有扩展
        self.registry.unregister_all_plugin_extensions("plugin_a")
        
        # 验证结果
        self.assertNotIn("plugin_a", self.registry.plugin_extensions)
        self.assertIsNone(
            self.registry.extension_handlers["ext_point1"].get_extension("plugin_a")
        )
        self.assertIsNone(
            self.registry.extension_handlers["ext_point2"].get_extension("plugin_a")
        )
        self.assertNotIn("plugin_a", self.registry.get_plugins_by_type("type1"))
    
    def test_unregister_all_nonexistent_plugin_extensions(self):
        """测试注销不存在插件的所有扩展"""
        # 注销不存在插件的所有扩展
        self.registry.unregister_all_plugin_extensions("nonexistent")
        
        # 没有异常说明测试通过
    
    def test_get_all_extension_points(self):
        """测试获取所有扩展点"""
        # 注册扩展点
        self.registry.register_extension_point("ext_point1", "Extension Point 1")
        self.registry.register_extension_point("ext_point2", "Extension Point 2")
        
        # 获取所有扩展点
        extension_points = self.registry.get_all_extension_points()
        
        # 验证结果
        self.assertEqual(len(extension_points), 2)
        self.assertIn("ext_point1", extension_points)
        self.assertIn("ext_point2", extension_points)
        self.assertEqual(extension_points["ext_point1"], "Extension Point 1")
        self.assertEqual(extension_points["ext_point2"], "Extension Point 2")
    
    def test_get_plugin_extension_points(self):
        """测试获取插件注册的所有扩展点"""
        # 注册扩展点和扩展
        self.registry.register_extension_point("ext_point1")
        self.registry.register_extension_point("ext_point2")
        extension1 = MagicMock()
        extension2 = MagicMock()
        self.registry.register_extension("plugin_a", "ext_point1", extension1)
        self.registry.register_extension("plugin_a", "ext_point2", extension2)
        
        # 获取插件注册的所有扩展点
        extension_points = self.registry.get_plugin_extension_points("plugin_a")
        
        # 验证结果
        self.assertEqual(len(extension_points), 2)
        self.assertIn("ext_point1", extension_points)
        self.assertIn("ext_point2", extension_points)
    
    def test_get_nonexistent_plugin_extension_points(self):
        """测试获取不存在插件注册的所有扩展点"""
        # 获取不存在插件注册的所有扩展点
        extension_points = self.registry.get_plugin_extension_points("nonexistent")
        
        # 验证结果
        self.assertEqual(len(extension_points), 0)


if __name__ == "__main__":
    unittest.main() 