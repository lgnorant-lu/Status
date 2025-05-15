"""
---------------------------------------------------------------
File name:                  test_resource_loader.py
Author:                     Ignorant-lu
Date created:               2025/05/16
Description:                测试资源加载器功能
----------------------------------------------------------------

Changed history:            
                            2025/05/16: 初始创建;
"""

import pytest
import os
from unittest.mock import patch, MagicMock

from status.resources.resource_loader import ResourceLoader, LRUCache # 确保导入LRUCache用于可能的检查
from status.resources import ResourceType
from status.core.types import PathLike # 假设 ResourceLoader 中使用了这个

# 如果 ResourceLoader 依赖于一个 Manager 协议，并且在测试中mock它，确保定义或导入
# from typing import Protocol, Optional, List
# @runtime_checkable
# class ResourceManager(Protocol):
#     def has_resource(self, path: str) -> bool: ...
#     def get_resource_content(self, path: str) -> Optional[bytes]: ...
#     def get_resource_path(self, path: str) -> Optional[str]: ...
#     def list_resources(self, prefix: str = "") -> List[str]: ...
#     def reload(self) -> bool: ...
#     def initialize(self) -> bool: ...


@pytest.fixture
def resource_loader_instance(monkeypatch):
    """Fixture to provide a ResourceLoader instance with a mocked manager."""
    loader = ResourceLoader()

    # 确保缓存是实际的LRUCache实例。这是一个防止LRUCache在更广泛范围内意外mock的防护措施。
    from status.resources.resource_loader import LRUCache as ActualLRUCache
    loader._image_cache = ActualLRUCache(capacity=100)  # 使用capacity关键字
    loader._sound_cache = ActualLRUCache(capacity=50)
    loader._font_cache = ActualLRUCache(capacity=20)
    loader._json_cache = ActualLRUCache(capacity=100)
    loader._text_cache = ActualLRUCache(capacity=100)
    loader._general_cache = ActualLRUCache(capacity=100)

    # Mock the internal manager to control resource content directly
    mock_manager = MagicMock()
    # Simulate _load_default_manager not finding/setting a real manager initially
    # or directly set the mocked manager
    monkeypatch.setattr(loader, '_manager', mock_manager)
    monkeypatch.setattr(loader, 'base_path', '.') # Set a dummy base_path
    
    # Reset stats for each test using this fixture
    loader._load_stats = {
        "total_loads": 0,
        "cache_hits": 0,
        "cache_misses": 0,
        "by_type": {},
        "errors": 0
    }
    # loader.clear_cache() # Explicitly re-initializing caches above makes this redundant for setup
    return loader

class TestResourceLoaderCaching:

    def test_load_resource_uses_internal_cache_by_default_and_explicitly(self, resource_loader_instance):
        """测试 ResourceLoader.load_resource 在 use_internal_cache=True (默认和显式) 时使用内部缓存"""
        loader = resource_loader_instance
        test_content = b"Hello World"
        test_path = "test_file.txt"
        
        loader._manager.get_resource_content.return_value = test_content

        # 场景1: 默认 use_internal_cache=True
        result1_default = loader.load_resource(test_path, ResourceType.TEXT, use_cache=True)
        assert result1_default == "Hello World"
        assert loader._text_cache.get(test_path) == "Hello World"
        assert loader._manager.get_resource_content.call_count == 1
        assert loader._load_stats["cache_misses"] == 1 # 第一次加载，内部缓存未命中
        assert loader._load_stats["cache_hits"] == 0

        result2_default = loader.load_resource(test_path, ResourceType.TEXT, use_cache=True)
        assert result2_default == "Hello World"
        assert loader._manager.get_resource_content.call_count == 1 # 不应再次调用底层加载
        assert loader._load_stats["cache_hits"] == 1 # 第二次加载，内部缓存命中
        assert loader._load_stats["cache_misses"] == 1
        
        # 重置 mock 和 stats 进行下一个场景测试
        loader._manager.get_resource_content.reset_mock()
        loader._load_stats["cache_hits"] = 0
        loader._load_stats["cache_misses"] = 0
        loader._text_cache.clear()

        # 场景2: 显式 use_internal_cache=True
        result1_explicit = loader.load_resource(test_path, ResourceType.TEXT, use_cache=True, use_internal_cache=True)
        assert result1_explicit == "Hello World"
        assert loader._text_cache.get(test_path) == "Hello World"
        assert loader._manager.get_resource_content.call_count == 1
        assert loader._load_stats["cache_misses"] == 1

        result2_explicit = loader.load_resource(test_path, ResourceType.TEXT, use_cache=True, use_internal_cache=True)
        assert result2_explicit == "Hello World"
        assert loader._manager.get_resource_content.call_count == 1 
        assert loader._load_stats["cache_hits"] == 1
        assert loader._load_stats["cache_misses"] == 1

    def test_load_resource_bypasses_internal_cache_when_specified(self, resource_loader_instance):
        """测试 ResourceLoader.load_resource 在 use_internal_cache=False 时旁路内部缓存"""
        loader = resource_loader_instance
        test_content = b"Bypass Test"
        test_path = "bypass_file.txt"

        loader._manager.get_resource_content.return_value = test_content

        # 第一次加载，不使用内部缓存
        result1 = loader.load_resource(test_path, ResourceType.TEXT, use_cache=True, use_internal_cache=False)
        assert result1 == "Bypass Test"
        assert loader._text_cache.get(test_path) is None # 不应存入内部缓存
        assert loader._manager.get_resource_content.call_count == 1
        # 因为 use_internal_cache=False，所以不应记录内部缓存的 miss 或 hit
        assert loader._load_stats["cache_misses"] == 0 
        assert loader._load_stats["cache_hits"] == 0

        # 第二次加载，仍然不使用内部缓存
        result2 = loader.load_resource(test_path, ResourceType.TEXT, use_cache=True, use_internal_cache=False)
        assert result2 == "Bypass Test"
        assert loader._text_cache.get(test_path) is None # 仍然不应在内部缓存中
        assert loader._manager.get_resource_content.call_count == 2 # 底层加载应该再次发生
        assert loader._load_stats["cache_misses"] == 0
        assert loader._load_stats["cache_hits"] == 0

    def test_specific_loaders_pass_use_internal_cache_flag(self, resource_loader_instance):
        """测试特定类型加载方法 (如 load_text) 正确传递 use_internal_cache 标志"""
        loader = resource_loader_instance
        test_content = b"Specific Loader Test"
        test_path = "specific.txt"
        loader._manager.get_resource_content.return_value = test_content

        # 使用 patch 来监控 load_resource 方法的调用
        with patch.object(loader, 'load_resource', wraps=loader.load_resource) as mock_load_resource_method:
            # 测试 load_text
            loader.load_text(test_path, use_internal_cache=False)
            mock_load_resource_method.assert_called_with(test_path, ResourceType.TEXT, use_cache=True, use_internal_cache=False, encoding='utf-8')
            
            mock_load_resource_method.reset_mock()
            loader.load_text(test_path, use_internal_cache=True) # 默认 use_cache=True
            mock_load_resource_method.assert_called_with(test_path, ResourceType.TEXT, use_cache=True, use_internal_cache=True, encoding='utf-8')

            # 测试 load_image (假设HAS_GUI为True，或者mock掉HAS_GUI检查)
            mock_load_resource_method.reset_mock()
            with patch('status.resources.resource_loader.HAS_GUI', True):
                loader.load_image(test_path, use_internal_cache=False)
                mock_load_resource_method.assert_called_with(test_path, ResourceType.IMAGE, use_cache=True, use_internal_cache=False)
                
                mock_load_resource_method.reset_mock()
                loader.load_image(test_path, use_internal_cache=True)
                mock_load_resource_method.assert_called_with(test_path, ResourceType.IMAGE, use_cache=True, use_internal_cache=True)

            # 可以为其他特定加载方法添加类似的测试: load_json, load_font, etc.

    def test_load_resource_stats_logic(self, resource_loader_instance):
        """更细致地测试加载统计在不同缓存场景下的准确性"""
        loader = resource_loader_instance
        test_content_1 = b"Stats Test 1"
        path_1 = "stats_file_1.txt"
        test_content_2 = b"Stats Test 2"
        path_2 = "stats_file_2.txt"

        loader._manager.get_resource_content.side_effect = [test_content_1, test_content_1, test_content_2, test_content_2]

        # 场景1: use_internal_cache=True
        # 第一次加载 path_1 (miss)
        loader.load_resource(path_1, ResourceType.TEXT, use_internal_cache=True)
        assert loader._load_stats["total_loads"] == 1
        assert loader._load_stats["cache_hits"] == 0
        assert loader._load_stats["cache_misses"] == 1
        assert loader._text_cache.get(path_1) is not None

        # 第二次加载 path_1 (hit)
        loader.load_resource(path_1, ResourceType.TEXT, use_internal_cache=True)
        assert loader._load_stats["total_loads"] == 2
        assert loader._load_stats["cache_hits"] == 1
        assert loader._load_stats["cache_misses"] == 1
        assert loader._manager.get_resource_content.call_count == 1 # path_1只加载一次

        # 场景2: use_internal_cache=False
        # 第一次加载 path_2 (内部缓存旁路)
        loader.load_resource(path_2, ResourceType.TEXT, use_internal_cache=False)
        assert loader._load_stats["total_loads"] == 3
        assert loader._load_stats["cache_hits"] == 1   # 不影响之前的统计
        assert loader._load_stats["cache_misses"] == 1 # 不应增加，因为没用内部缓存
        assert loader._text_cache.get(path_2) is None
        assert loader._manager.get_resource_content.call_count == 2 # path_1 + path_2

        # 第二次加载 path_2 (内部缓存旁路)
        loader.load_resource(path_2, ResourceType.TEXT, use_internal_cache=False)
        assert loader._load_stats["total_loads"] == 4
        assert loader._load_stats["cache_hits"] == 1
        assert loader._load_stats["cache_misses"] == 1
        assert loader._text_cache.get(path_2) is None
        assert loader._manager.get_resource_content.call_count == 3 # path_1 + path_2(第一次) + path_2(第二次)
        
    def test_load_resource_with_use_cache_false_and_internal_cache_true(self, resource_loader_instance):
        """测试当总体use_cache=False但use_internal_cache=True时的行为（理论上不应使用内部缓存）"""
        loader = resource_loader_instance
        test_content = b"Overall no cache"
        test_path = "no_cache_overall.txt"
        loader._manager.get_resource_content.return_value = test_content

        # 尽管 use_internal_cache=True, 但顶层 use_cache=False 会导致 actual_internal_cache_usage_enabled = False
        loader.load_resource(test_path, ResourceType.TEXT, use_cache=False, use_internal_cache=True)
        assert loader._manager.get_resource_content.call_count == 1
        assert loader._text_cache.get(test_path) is None # 不应存入内部缓存
        assert loader._load_stats["cache_hits"] == 0
        assert loader._load_stats["cache_misses"] == 0 # 因为 actual_internal_cache_usage_enabled 为 False

        loader.load_resource(test_path, ResourceType.TEXT, use_cache=False, use_internal_cache=True)
        assert loader._manager.get_resource_content.call_count == 2
        assert loader._text_cache.get(test_path) is None
        assert loader._load_stats["cache_hits"] == 0
        assert loader._load_stats["cache_misses"] == 0

# 可以添加更多测试，例如测试不同资源类型、kwargs对缓存键的影响（如果适用）等 