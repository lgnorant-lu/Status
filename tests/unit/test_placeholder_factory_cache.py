"""
---------------------------------------------------------------
File name:                  test_placeholder_factory_cache.py
Author:                     Ignorant-lu
Date created:               2025/05/15
Description:                占位符工厂缓存机制的单元测试 (TDD模式)
----------------------------------------------------------------

Changed history:            
                            2025/05/15: 初始创建;
----
"""
import pytest
from unittest.mock import patch, MagicMock, call
from status.pet_assets.placeholder_factory import PlaceholderFactory
from status.behavior.pet_state import PetState
from status.animation.animation import Animation

@pytest.fixture
def factory():
    """提供一个PlaceholderFactory实例"""
    return PlaceholderFactory()

@pytest.mark.unit
class TestPlaceholderFactoryCache:
    """测试占位符工厂的缓存机制"""
    
    @patch('importlib.import_module')
    def test_animation_is_cached(self, mock_import_module, factory, qt_app):
        """测试动画是否被缓存 - 同一状态第二次请求不应重新加载"""
        # 创建模拟的Animation对象
        mock_animation_instance = Animation(name="test", frames=[])
        
        # 创建模拟的占位符模块
        mock_placeholder_module = MagicMock()
        mock_placeholder_module.create_animation.return_value = mock_animation_instance
        mock_import_module.return_value = mock_placeholder_module
        
        # 第一次调用
        animation1 = factory.get_animation(PetState.HAPPY)
        
        # 第二次调用同一状态
        animation2 = factory.get_animation(PetState.HAPPY)
        
        # 验证结果
        assert animation1 == animation2
        # importlib.import_module应该只被调用一次，说明使用了缓存
        mock_import_module.assert_called_once()
        # create_animation也应该只被调用一次
        mock_placeholder_module.create_animation.assert_called_once()
        
    @patch('importlib.import_module')
    def test_different_states_not_cached_together(self, mock_import_module, factory, qt_app):
        """测试不同状态有独立的缓存"""
        # 为不同状态创建不同模块
        mock_modules = {
            "status.pet_assets.placeholders.happy_placeholder": MagicMock(),
            "status.pet_assets.placeholders.sad_placeholder": MagicMock()
        }
        
        # 为不同状态创建不同动画
        mock_animations = {
            "happy": Animation(name="happy", frames=[]),
            "sad": Animation(name="sad", frames=[])
        }
        
        # 设置模块行为
        mock_modules["status.pet_assets.placeholders.happy_placeholder"].create_animation.return_value = mock_animations["happy"]
        mock_modules["status.pet_assets.placeholders.sad_placeholder"].create_animation.return_value = mock_animations["sad"]
        
        # 配置import_module返回对应模块
        def side_effect_import(module_path):
            if module_path in mock_modules:
                return mock_modules[module_path]
            raise ImportError(f"意外的模块路径: {module_path}")
        
        mock_import_module.side_effect = side_effect_import
        
        # 请求不同状态的动画
        happy_animation = factory.get_animation(PetState.HAPPY)
        sad_animation = factory.get_animation(PetState.SAD)
        
        # 再次请求，测试各自的缓存
        happy_animation2 = factory.get_animation(PetState.HAPPY)
        sad_animation2 = factory.get_animation(PetState.SAD)
        
        # 验证结果
        assert happy_animation == happy_animation2
        assert sad_animation == sad_animation2
        assert happy_animation != sad_animation
        
        # 检查导入模块的调用
        assert mock_import_module.call_count == 2
        mock_import_module.assert_has_calls([
            call("status.pet_assets.placeholders.happy_placeholder"),
            call("status.pet_assets.placeholders.sad_placeholder")
        ], any_order=True)
        
        # 每个模块的create_animation应该只被调用一次
        mock_modules["status.pet_assets.placeholders.happy_placeholder"].create_animation.assert_called_once()
        mock_modules["status.pet_assets.placeholders.sad_placeholder"].create_animation.assert_called_once()
        
    def test_cache_size_limit(self, factory, monkeypatch, qt_app):
        """测试缓存大小限制 - 当缓存超过限制时，应移除最早的条目"""
        # 如果缓存限制为5，测试加载6个不同状态时情况
        mock_animations = {}
        loaded_modules = []
        
        # 创建一个记录加载次数的函数
        def mock_import_module(module_path):
            loaded_modules.append(module_path)
            mock_module = MagicMock()
            state_name = module_path.split('.')[-1].replace('_placeholder', '').upper()
            mock_module.create_animation.return_value = Animation(name=state_name.lower(), frames=[])
            return mock_module
            
        monkeypatch.setattr('importlib.import_module', mock_import_module)
        
        # 模拟超过缓存限制的多个状态
        test_states = [
            PetState.IDLE, PetState.BUSY, PetState.CLICKED, 
            PetState.MORNING, PetState.NIGHT, PetState.HAPPY
        ]
        
        # 首次加载所有状态
        for state in test_states:
            factory.get_animation(state)
            
        # 清除记录，重新获取第一个状态
        loaded_modules.clear()
        factory.get_animation(PetState.IDLE)
        
        # 如果实现了缓存限制，IDLE应该已被清出缓存并需要重新加载
        assert len(loaded_modules) == 1
        assert "status.pet_assets.placeholders.idle_placeholder" in loaded_modules
        
    def test_clear_cache(self, factory, monkeypatch, qt_app):
        """测试清除缓存功能"""
        loaded_modules = []
        
        def mock_import_module(module_path):
            loaded_modules.append(module_path)
            mock_module = MagicMock()
            mock_module.create_animation.return_value = Animation(name="test", frames=[])
            return mock_module
            
        monkeypatch.setattr('importlib.import_module', mock_import_module)
        
        # 首次加载
        factory.get_animation(PetState.HAPPY)
        
        # 再次加载，应该使用缓存
        loaded_modules.clear()
        factory.get_animation(PetState.HAPPY)
        assert len(loaded_modules) == 0
        
        # 清除缓存
        factory.clear_cache()
        
        # 加载后应该重新导入
        loaded_modules.clear()
        factory.get_animation(PetState.HAPPY)
        assert len(loaded_modules) == 1 