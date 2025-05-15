"""
---------------------------------------------------------------
File name:                  test_placeholder_factory.py
Author:                     Ignorant-lu
Date created:               2025/05/15
Description:                占位符工厂的单元测试 (TDD模式, pytest版本)
----------------------------------------------------------------

Changed history:            
                            2025/05/15: 初始创建;
----
"""
import pytest
from unittest.mock import patch, MagicMock
from status.pet_assets.placeholder_factory import PlaceholderFactory
from status.behavior.pet_state import PetState
from status.animation.animation import Animation

@pytest.fixture
def factory():
    """提供一个PlaceholderFactory实例"""
    return PlaceholderFactory()

@pytest.mark.unit
class TestPlaceholderFactory:
    """测试占位符工厂"""
    
    @patch('importlib.import_module')
    def test_get_animation_successful_load(self, mock_import_module, factory, qt_app):
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
        animation = factory.get_animation(PetState.HAPPY)

        # 验证结果
        assert animation == mock_animation_instance
        mock_import_module.assert_called_once_with("status.pet_assets.placeholders.happy_placeholder")
        mock_placeholder_module.create_animation.assert_called_once()

    @patch('importlib.import_module')
    def test_get_animation_module_not_found(self, mock_import_module, factory, qt_app):
        """测试模块未找到的情况"""
        mock_import_module.side_effect = ImportError
        animation = factory.get_animation(PetState.SAD)  # 假设SAD占位符还不存在
        assert animation is None

    @patch('importlib.import_module')
    def test_get_animation_create_animation_not_found(self, mock_import_module, factory, qt_app):
        """测试create_animation函数未找到的情况"""
        mock_placeholder_module = MagicMock()
        delattr(mock_placeholder_module, 'create_animation')  # 模拟函数缺失
        mock_import_module.return_value = mock_placeholder_module
        
        animation = factory.get_animation(PetState.HAPPY)
        assert animation is None

    @patch('importlib.import_module')
    def test_get_animation_create_animation_returns_wrong_type(self, mock_import_module, factory, qt_app):
        """测试create_animation返回错误类型的情况"""
        mock_placeholder_module = MagicMock()
        mock_placeholder_module.create_animation.return_value = "not an animation"  # 错误类型
        mock_import_module.return_value = mock_placeholder_module

        animation = factory.get_animation(PetState.HAPPY)
        assert animation is None
        
    @patch('importlib.import_module')
    def test_get_animation_exception_handling(self, mock_import_module, factory, qt_app):
        """测试create_animation抛出异常时的处理"""
        mock_placeholder_module = MagicMock()
        mock_placeholder_module.create_animation.side_effect = Exception("测试异常")
        mock_import_module.return_value = mock_placeholder_module

        animation = factory.get_animation(PetState.HAPPY)
        assert animation is None
        
    def test_multi_state_loading(self, factory, monkeypatch, qt_app):
        """测试加载多个不同状态的占位符动画"""
        # 模拟多个不同状态的占位符模块
        mock_states = {
            PetState.IDLE: Animation(name="idle", frames=[]),
            PetState.BUSY: Animation(name="busy", frames=[]),
            PetState.CLICKED: Animation(name="clicked", frames=[]),
            PetState.MORNING: Animation(name="morning", frames=[]),
            PetState.NIGHT: Animation(name="night", frames=[])
        }
        
        def mock_import_module(module_path):
            state_name = module_path.split('.')[-1].replace('_placeholder', '').upper()
            for state in PetState:
                if state.name == state_name:
                    mock_module = MagicMock()
                    mock_module.create_animation.return_value = mock_states[state]
                    return mock_module
            raise ImportError(f"未找到模块: {module_path}")
            
        monkeypatch.setattr('importlib.import_module', mock_import_module)
        
        # 测试加载每个状态
        for state, expected_animation in mock_states.items():
            loaded_animation = factory.get_animation(state)
            assert loaded_animation == expected_animation
            assert loaded_animation.name == expected_animation.name 