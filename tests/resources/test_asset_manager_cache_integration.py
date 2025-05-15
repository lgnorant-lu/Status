"""
---------------------------------------------------------------
File name:                  test_asset_manager_cache_integration.py
Author:                     Ignorant-lu
Date created:               2025/05/16
Description:                测试AssetManager与ResourceLoader的缓存集成
----------------------------------------------------------------

Changed history:            
                            2025/05/16: 初始创建;
"""

import pytest
from unittest.mock import patch, MagicMock, ANY
# import threading # 不再需要在这里，如果lock在conftest.py中

from status.resources.asset_manager import AssetManager
from status.resources.resource_loader import ResourceLoader # 用于mock的规范
from status.resources import ResourceType, ImageFormat # 导入ImageFormat，如果在_make_cache_key或测试中使用
from status.resources.cache import Cache # 用于直接检查缓存实例的类型提示

# Module-level lock 和 cleanup_asset_manager_singleton fixture 现在预期在conftest.py中

@pytest.fixture
def asset_manager_instance(monkeypatch):
    """提供一个全新的AssetManager实例，带有mock的ResourceLoader和EventManager。"""
    
    mock_loader_instance = MagicMock(spec=ResourceLoader)
    mock_loader_instance._get_resource_type = MagicMock(return_value=ResourceType.OTHER)
    
    patch_loader = patch('status.resources.resource_loader.ResourceLoader', return_value=mock_loader_instance)
    MockedRL = patch_loader.start()

    mock_event_manager_instance = MagicMock()
    patch_event_manager = patch('status.resources.asset_manager.EventManager', return_value=mock_event_manager_instance)
    MockedEM = patch_event_manager.start()

    am = AssetManager() 
    assert hasattr(am, 'loader'), "AssetManager实例应该在初始化后有一个'loader'属性"
    assert hasattr(am, 'image_cache'), "AssetManager实例应该在初始化后有一个'image_cache'属性"
    
    am.initialize(base_path="dummy_assets")
    am.clear_all_caches()

    yield am

    patch_loader.stop()
    patch_event_manager.stop()

class TestAssetManagerCacheIntegration:

    def test_load_asset_passes_use_internal_cache_false_to_loader(self, asset_manager_instance):
        """
        Tests AssetManager.load_asset 调用 ResourceLoader.load_resource 
        使用 use_internal_cache=False。
        """
        am = asset_manager_instance
        mock_loader = am.loader
        
        test_path = "image.png"
        test_content_bytes = b"fake image data"
        
        mock_loader._get_resource_type.return_value = ResourceType.IMAGE
        mock_loader.load_resource.return_value = test_content_bytes

        am.load_asset(test_path, resource_type=ResourceType.IMAGE, use_cache=False)

        mock_loader.load_resource.assert_called_once()
        call_args = mock_loader.load_resource.call_args
        assert call_args is not None
        args_list, kwargs_dict = call_args
        
        assert args_list[0] == test_path
        assert kwargs_dict.get('resource_type') == ResourceType.IMAGE
        assert kwargs_dict.get('use_internal_cache') is False
        # AssetManager's use_cache=True 是默认的，当AM决定加载时，它翻译为ResourceLoader的use_cache=True。
        assert kwargs_dict.get('use_cache') is True 

    def test_asset_manager_own_cache_works_with_loader_internal_cache_bypassed(self, asset_manager_instance):
        """
        Tests AssetManager的自己的缓存在ResourceLoader的内部缓存旁路时工作正常。
        """
        am = asset_manager_instance
        mock_loader = am.loader
        
        test_path = "data.json"
        resource_content_str = '{"key": "value"}'
        expected_data = {"key": "value"}

        mock_loader._get_resource_type.return_value = ResourceType.JSON
        mock_loader.load_resource.return_value = expected_data

        # 1st load: AssetManager缓存未命中，ResourceLoader被调用
        result1 = am.load_asset(test_path, resource_type=ResourceType.JSON, use_cache=True, encoding='utf-8')
        assert result1 == expected_data
        mock_loader.load_resource.assert_called_once_with(
            test_path, 
            resource_type=ResourceType.JSON, 
            use_cache=True, 
            use_internal_cache=False, # 关键检查
            compressed=False,
            compression_type='zlib',
            encoding='utf-8'
        )
        
        cache_key_kwargs = {'encoding': 'utf-8'}
        cache_key = am._make_cache_key(test_path, **cache_key_kwargs)
        assert am.other_cache.contains(cache_key)
        retrieved_from_cache = am.other_cache.get(cache_key)
        assert retrieved_from_cache == expected_data

        # 2nd load: AssetManager缓存命中，ResourceLoader不再被调用
        result2 = am.load_asset(test_path, resource_type=ResourceType.JSON, use_cache=True, encoding='utf-8')
        assert result2 == expected_data
        assert mock_loader.load_resource.call_count == 1
        
    def test_load_asset_with_no_am_cache_still_bypasses_rl_internal_cache(self, asset_manager_instance):
        """
        Tests that ResourceLoader的内部缓存被旁路，即使AssetManager的use_cache无效.
        """
        am = asset_manager_instance
        mock_loader = am.loader
        
        test_path = "another.txt"
        test_content_bytes = b"some text data"
        
        mock_loader._get_resource_type.return_value = ResourceType.TEXT
        mock_loader.load_resource.return_value = test_content_bytes

        am.load_asset(test_path, resource_type=ResourceType.TEXT, use_cache=False, encoding='utf-8') 

        mock_loader.load_resource.assert_called_once()
        call_args = mock_loader.load_resource.call_args
        assert call_args is not None
        _, kwargs_dict = call_args
        assert kwargs_dict.get('use_internal_cache') is False
        
        cache_key_kwargs = {'encoding': 'utf-8'}
        cache_key = am._make_cache_key(test_path, **cache_key_kwargs)
        assert not am.other_cache.contains(cache_key) 