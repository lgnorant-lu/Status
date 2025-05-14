"""
---------------------------------------------------------------
File name:                  test_placeholder_factory.py
Author:                     Ignorant-lu
Date created:               2025/05/15
Description:                占位符工厂的单元测试
----------------------------------------------------------------

Changed history:            
                            2025/05/15: 初始创建;
----
"""
import unittest
import sys
from unittest.mock import patch, MagicMock
from PySide6.QtWidgets import QApplication
from status.pet_assets.placeholder_factory import PlaceholderFactory
from status.behavior.pet_state import PetState
from status.animation.animation import Animation

class TestPlaceholderFactory(unittest.TestCase):
    """测试占位符工厂"""
    
    @classmethod
    def setUpClass(cls):
        """创建一个QApplication实例，确保Qt环境正确设置"""
        # 检查是否已存在QApplication实例，如果不存在则创建
        if not QApplication.instance():
            cls.app = QApplication(sys.argv)
    
    def setUp(self):
        """每个测试前的设置"""
        self.factory = PlaceholderFactory()

    @patch('importlib.import_module')
    def test_get_animation_successful_load(self, mock_import_module):
        """测试成功加载动画"""
        # 创建模拟的Animation对象
        mock_animation_instance = Animation(name="test", frames=[])
        
        # 创建模拟的占位符模块
        mock_placeholder_module = MagicMock()
        mock_placeholder_module.create_animation.return_value = mock_animation_instance
        
        # 配置import_module返回我们的模拟模块
        def side_effect_import(module_path):
            if module_path == "status.pet_assets.placeholders.happy_placeholder":
                return mock_placeholder_module
            raise ImportError(f"意外的模块路径: {module_path}")
        
        mock_import_module.side_effect = side_effect_import

        # 调用待测方法
        animation = self.factory.get_animation(PetState.HAPPY)

        # 验证结果
        self.assertEqual(animation, mock_animation_instance)
        mock_import_module.assert_called_once_with("status.pet_assets.placeholders.happy_placeholder")
        mock_placeholder_module.create_animation.assert_called_once()

    @patch('importlib.import_module')
    def test_get_animation_module_not_found(self, mock_import_module):
        """测试模块未找到的情况"""
        mock_import_module.side_effect = ImportError
        animation = self.factory.get_animation(PetState.SAD) # 假设SAD占位符还不存在
        self.assertIsNone(animation)

    @patch('importlib.import_module')
    def test_get_animation_create_animation_not_found(self, mock_import_module):
        """测试create_animation函数未找到的情况"""
        mock_placeholder_module = MagicMock()
        del mock_placeholder_module.create_animation # 模拟函数缺失
        mock_import_module.return_value = mock_placeholder_module
        
        animation = self.factory.get_animation(PetState.HAPPY)
        self.assertIsNone(animation)

    @patch('importlib.import_module')
    def test_get_animation_create_animation_returns_wrong_type(self, mock_import_module):
        """测试create_animation返回错误类型的情况"""
        mock_placeholder_module = MagicMock()
        mock_placeholder_module.create_animation.return_value = "not an animation" # 错误类型
        mock_import_module.return_value = mock_placeholder_module

        animation = self.factory.get_animation(PetState.HAPPY)
        self.assertIsNone(animation)

if __name__ == '__main__':
    unittest.main() 