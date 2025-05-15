"""
---------------------------------------------------------------
File name:                  test_placeholder_factory_cache_stats.py
Author:                     Ignorant-lu
Date created:               2025/05/15
Description:                占位符工厂缓存统计功能的单元测试 (TDD模式)
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
class TestPlaceholderFactoryCacheStats:
    """测试占位符工厂的缓存统计功能"""
    
    def test_cache_stats_basic(self, factory):
        """测试基本缓存统计功能"""
        # 初始状态下，缓存应该为空
        stats = factory.get_cache_stats()
        assert stats["total_requests"] == 0
        assert stats["cache_hits"] == 0
        assert stats["cache_misses"] == 0
        assert stats["hit_rate"] == 0.0
    
    @patch('importlib.import_module')
    def test_cache_stats_tracking(self, mock_import_module, factory):
        """测试缓存统计追踪"""
        # 创建模拟的Animation对象
        mock_animation_instance = Animation(name="test", frames=[])
        
        # 创建模拟的占位符模块
        mock_placeholder_module = MagicMock()
        mock_placeholder_module.create_animation.return_value = mock_animation_instance
        mock_import_module.return_value = mock_placeholder_module
        
        # 第一次调用
        factory.get_animation(PetState.HAPPY)
        
        # 检查统计
        stats = factory.get_cache_stats()
        assert stats["total_requests"] == 1
        assert stats["cache_hits"] == 0
        assert stats["cache_misses"] == 1
        assert stats["hit_rate"] == 0.0
        
        # 第二次调用同一状态
        factory.get_animation(PetState.HAPPY)
        
        # 检查统计更新
        stats = factory.get_cache_stats()
        assert stats["total_requests"] == 2
        assert stats["cache_hits"] == 1
        assert stats["cache_misses"] == 1
        assert stats["hit_rate"] == 0.5  # 1次命中，1次未命中
    
    @patch('importlib.import_module')
    def test_cache_stats_multiple_states(self, mock_import_module, factory):
        """测试多状态下的缓存统计"""
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
        
        # 请求多种状态的动画
        factory.get_animation(PetState.HAPPY)
        factory.get_animation(PetState.HAPPY)
        factory.get_animation(PetState.SAD)
        factory.get_animation(PetState.HAPPY)
        factory.get_animation(PetState.SAD)
        
        # 检查统计 - 应该有5次请求，3次命中
        stats = factory.get_cache_stats()
        assert stats["total_requests"] == 5
        assert stats["cache_hits"] == 3
        assert stats["cache_misses"] == 2
        assert stats["hit_rate"] == 0.6  # 3次命中，2次未命中
    
    def test_reset_stats(self, factory):
        """测试重置统计数据功能"""
        # 设置一些初始数据
        factory._stats = {
            "total_requests": 10,
            "cache_hits": 6,
            "cache_misses": 4,
            "hit_rate": 0.6
        }
        
        # 重置统计
        factory.reset_cache_stats()
        
        # 检查统计已重置
        stats = factory.get_cache_stats()
        assert stats["total_requests"] == 0
        assert stats["cache_hits"] == 0
        assert stats["cache_misses"] == 0
        assert stats["hit_rate"] == 0.0 