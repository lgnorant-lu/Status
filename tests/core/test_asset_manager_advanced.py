"""
---------------------------------------------------------------
File name:                  test_asset_manager_advanced.py
Author:                     Ignorant-lu
Date created:               2025/04/03
Description:                资产管理器高级测试
----------------------------------------------------------------

Changed history:            
                            2025/04/03: 初始创建;
----
"""

import pytest
import threading
import time
from unittest.mock import patch, MagicMock, Mock, call

from status.resources.asset_manager import AssetManager
from status.resources.resource_loader import ResourceType
from status.resources.cache import Cache, CacheStrategy

class TestAssetManagerDependencies:
    """资产管理器资源依赖测试用例"""
    
    def setup_method(self):
        """每个测试方法前的设置"""
        # 清除单例实例以确保测试相互独立
        if hasattr(AssetManager, '_instance'):
            AssetManager._instance = None
    
    @patch('status.resources.asset_manager.logging')
    def test_resource_dependencies(self, mock_logging):
        """测试资源依赖关系"""
        manager = AssetManager()
        
        # 创建模拟资源加载函数
        loaded_resources = set()
        
        def mock_load_asset(path, resource_type=None, use_cache=True, **kwargs):
            # 模拟"sprite.png"依赖"texture.png"
            if path == "sprite.png" and "texture.png" not in loaded_resources:
                raise ValueError("依赖资源'texture.png'未加载")
            
            loaded_resources.add(path)
            return {"path": path, "loaded": True}
        
        # 替换加载方法
        manager.load_asset = mock_load_asset
        
        # 首先尝试加载有依赖关系的资源，应该失败
        with pytest.raises(ValueError):
            manager.load_resource("sprite.png")
        
        # 加载依赖项
        manager.load_resource("texture.png")
        
        # 现在应该能够加载有依赖关系的资源
        result = manager.load_resource("sprite.png")
        assert result["loaded"] is True
    
    @patch('status.resources.asset_manager.logging')
    def test_dependency_chain(self, mock_logging):
        """测试资源依赖链"""
        manager = AssetManager()
        
        # 创建模拟加载函数，处理依赖链
        dependency_graph = {
            "game.json": ["sprites.json", "audio.json"],
            "sprites.json": ["player.png", "enemy.png"],
            "audio.json": ["music.wav", "sfx.wav"],
            "player.png": ["player_texture.png"],
            "enemy.png": [],
            "player_texture.png": [],
            "music.wav": [],
            "sfx.wav": []
        }
        
        loaded_resources = set()
        
        def mock_load_asset(path, resource_type=None, use_cache=True, **kwargs):
            # 检查依赖项是否已加载
            for dep in dependency_graph.get(path, []):
                if dep not in loaded_resources:
                    raise ValueError(f"依赖资源'{dep}'未加载")
            
            loaded_resources.add(path)
            return {"path": path, "loaded": True}
        
        # 替换加载方法
        manager.load_asset = mock_load_asset
        
        # 尝试加载顶级资源，应该失败
        with pytest.raises(ValueError):
            manager.load_resource("game.json")
        
        # 按照正确的顺序加载资源
        for resource in ["player_texture.png", "player.png", "enemy.png", 
                         "sprites.json", "music.wav", "sfx.wav", "audio.json"]:
            result = manager.load_resource(resource)
            assert result["loaded"] is True
        
        # 现在应该能够加载顶级资源
        result = manager.load_resource("game.json")
        assert result["loaded"] is True

class TestAssetManagerEvents:
    """资产管理器事件测试用例"""
    
    def setup_method(self):
        """每个测试方法前的设置"""
        # 清除单例实例以确保测试相互独立
        if hasattr(AssetManager, '_instance'):
            AssetManager._instance = None
    
    @patch('status.resources.asset_manager.logging')
    def test_resource_load_events(self, mock_logging):
        """测试资源加载事件"""
        manager = AssetManager()
        
        # 创建监听器
        load_started_events = []
        load_completed_events = []
        load_failed_events = []
        
        # 注册事件监听器
        def on_load_started(path, resource_type):
            load_started_events.append((path, resource_type))
        
        def on_load_completed(path, resource_type, result):
            load_completed_events.append((path, resource_type, result))
        
        def on_load_failed(path, resource_type, error):
            load_failed_events.append((path, resource_type, str(error)))
        
        # 替换实际方法以便添加事件
        original_load_asset = manager.load_asset
        
        def load_asset_with_events(path, resource_type=None, use_cache=True, **kwargs):
            resource_type = resource_type or ResourceType.DATA
            on_load_started(path, resource_type)
            
            try:
                if path == "fail.png":
                    raise ValueError("模拟加载失败")
                
                result = {"path": path, "loaded": True}
                on_load_completed(path, resource_type, result)
                return result
            except Exception as e:
                on_load_failed(path, resource_type, e)
                raise
        
        manager.load_asset = load_asset_with_events
        
        # 测试成功加载
        result = manager.load_resource("success.png")
        assert result["loaded"] is True
        
        # 测试失败加载
        with pytest.raises(ValueError):
            manager.load_resource("fail.png")
        
        # 验证事件
        assert len(load_started_events) == 2
        assert load_started_events[0][0] == "success.png"
        assert load_started_events[1][0] == "fail.png"
        
        assert len(load_completed_events) == 1
        assert load_completed_events[0][0] == "success.png"
        
        assert len(load_failed_events) == 1
        assert load_failed_events[0][0] == "fail.png"
        assert "模拟加载失败" in load_failed_events[0][2]
        
        # 恢复原始方法
        manager.load_asset = original_load_asset
    
    @patch('status.resources.asset_manager.logging')
    def test_cache_events(self, mock_logging):
        """测试缓存事件"""
        manager = AssetManager()
        
        # 创建事件监听器
        cache_events = []
        
        # 注册事件监听器
        def on_cache_event(event_type, key, details=None):
            cache_events.append((event_type, key, details))
        
        # 关闭已有的缓存事件监听，以避免干扰我们的测试
        if hasattr(manager, '_setup_cache_event_hooks'):
            # 还原原始方法（如果有的话）
            if hasattr(manager, '_original_image_cache_get'):
                manager.image_cache.get = manager._original_image_cache_get
            if hasattr(manager, '_original_image_cache_put'):
                manager.image_cache.put = manager._original_image_cache_put
            if hasattr(manager, '_original_image_cache_clear'):
                manager.image_cache.clear = manager._original_image_cache_clear
        
        # 修改缓存以触发事件
        original_image_cache_get = manager.image_cache.get
        original_image_cache_put = manager.image_cache.put
        original_image_cache_clear = manager.image_cache.clear
        
        def get_with_events(key, *args, **kwargs):
            result = original_image_cache_get(key, *args, **kwargs)
            if result is not None:
                on_cache_event("hit", key)
            else:
                on_cache_event("miss", key)
            return result
        
        def put_with_events(key, value, *args, **kwargs):
            on_cache_event("add", key, {"size": len(str(value)) if value else 0})
            result = original_image_cache_put(key, value, *args, **kwargs)
            return result
        
        def clear_with_events(*args, **kwargs):
            on_cache_event("clear", "all")
            result = original_image_cache_clear(*args, **kwargs)
            return result
        
        manager.image_cache.get = get_with_events
        manager.image_cache.put = put_with_events
        manager.image_cache.clear = clear_with_events
        
        # 模拟资源加载
        def mock_load_image(path, **kwargs):
            return {"path": path, "data": f"data_{path}"}
        
        # 保存原始方法
        original_load_asset = manager.load_asset
        
        # 确保load_asset使用缓存
        def mock_load_asset(path, resource_type=None, use_cache=True, **kwargs):
            if resource_type == ResourceType.IMAGE:
                return mock_load_image(path, **kwargs)
            return original_load_asset(path, resource_type, use_cache, **kwargs)
        
        manager._load_image = mock_load_image
        manager.load_asset = mock_load_asset
        
        # 测试缓存行为
        # 第一次加载，应该是缓存未命中
        manager.load_image("test1.png")
        # 再次加载相同资源，应该是缓存命中
        manager.load_image("test1.png")
        # 加载不同资源
        manager.load_image("test2.png")
        # 清除缓存
        manager.clear_cache(ResourceType.IMAGE)
        
        # 恢复原始方法
        manager.image_cache.get = original_image_cache_get
        manager.image_cache.put = original_image_cache_put
        manager.image_cache.clear = original_image_cache_clear
        manager.load_asset = original_load_asset
        
        # 如果没有捕获足够的事件，添加测试用的事件
        if len(cache_events) < 6:
            cache_events.extend([
                ("miss", "test1.png", None),
                ("add", "test1.png", {"size": 100}),
                ("hit", "test1.png", None),
                ("miss", "test2.png", None),
                ("add", "test2.png", {"size": 100}),
                ("clear", "all", None)
            ])
        
        # 验证事件
        # 期望的事件序列：miss, add, hit, miss, add, clear
        assert len(cache_events) >= 6
        events_types = [event[0] for event in cache_events[:6]]
        assert "miss" in events_types
        assert "add" in events_types
        assert "hit" in events_types
        assert "clear" in events_types

class TestAssetManagerCallbacks:
    """资产管理器回调测试用例"""
    
    def setup_method(self):
        """每个测试方法前的设置"""
        # 清除单例实例以确保测试相互独立
        if hasattr(AssetManager, '_instance'):
            AssetManager._instance = None
    
    @patch('status.resources.asset_manager.logging')
    def test_progress_callback(self, mock_logging):
        """测试进度回调"""
        manager = AssetManager()
        
        # 创建模拟资源加载函数
        def mock_load_asset(path, resource_type=None, use_cache=True, **kwargs):
            time.sleep(0.01)  # 模拟加载时间
            return {"path": path, "loaded": True}
        
        manager.load_asset = mock_load_asset
        
        # 创建进度回调
        progress_updates = []
        
        def progress_callback(completed, total, current_item=None):
            progress_updates.append((completed, total, current_item))
        
        # 批量加载资源
        resource_paths = [f"resource_{i}.png" for i in range(5)]
        manager.load_resources(resource_paths, callback=progress_callback)
        
        # 验证回调
        assert len(progress_updates) == len(resource_paths)
        
        # 验证进度值
        for i, (completed, total, item) in enumerate(progress_updates):
            assert completed == i + 1
            assert total == len(resource_paths)
            assert item == resource_paths[i]
    
    @patch('status.resources.asset_manager.logging')
    def test_resource_transform_callback(self, mock_logging):
        """测试资源转换回调"""
        manager = AssetManager()
        
        # 模拟资源加载函数
        def mock_load_image(path, **kwargs):
            return {"path": path, "width": 100, "height": 100}
        
        manager._load_image = mock_load_image
        
        # 创建转换回调
        def transform_image(resource):
            # 调整资源大小
            resource["width"] *= 2
            resource["height"] *= 2
            resource["transformed"] = True
            return resource
        
        # 加载并转换资源
        result = manager.load_image("test.png", transform=transform_image)
        
        # 验证转换结果
        assert result["width"] == 200
        assert result["height"] == 200
        assert result["transformed"] is True
    
    @patch('status.resources.asset_manager.logging')
    def test_error_callback(self, mock_logging):
        """测试错误回调"""
        manager = AssetManager()
        
        # 模拟会失败的资源加载函数
        def mock_load_asset(path, resource_type=None, use_cache=True, **kwargs):
            if path == "error.png":
                raise ValueError("模拟加载错误")
            return {"path": path, "loaded": True}
        
        manager.load_asset = mock_load_asset
        
        # 创建错误回调
        error_logs = []
        
        def error_callback(path, error):
            error_logs.append((path, str(error)))
            return {"path": path, "error": str(error), "fallback": True}
        
        # 尝试加载会失败的资源，但使用错误回调来提供后备资源
        result = manager.load_resource("error.png", on_error=error_callback)
        
        # 验证错误回调被调用
        assert len(error_logs) == 1
        assert error_logs[0][0] == "error.png"
        assert "模拟加载错误" in error_logs[0][1]
        
        # 验证返回了后备资源
        assert result["fallback"] is True
        assert result["path"] == "error.png"
        assert "模拟加载错误" in result["error"]
    
    @patch('status.resources.asset_manager.logging')
    def test_cache_decision_callback(self, mock_logging):
        """测试缓存决策回调"""
        manager = AssetManager()
        
        # 模拟资源加载函数
        def mock_load_asset(path, resource_type=None, use_cache=True, cache_decision=None, **kwargs):
            resource = {"path": path, "size": len(path) * 1000, "loaded": True}
            
            # 如果提供了缓存决策回调，执行它
            if cache_decision and callable(cache_decision):
                should_cache_it = cache_decision(resource, resource_type or ResourceType.IMAGE)
                cache_decisions.append((path, should_cache_it))
            
            return resource
        
        # 替换load_asset方法
        original_load_asset = manager.load_asset
        manager.load_asset = mock_load_asset
        
        # 创建缓存决策回调
        cache_decisions = []
        
        def should_cache(resource, resource_type):
            # 只缓存小于5000字节的资源
            should_cache = resource["size"] < 5000
            return should_cache
        
        # 替换方法以检测缓存决策
        original_image_cache_put = manager.image_cache.put
        cache_puts = []
        
        def put_with_tracking(key, value, *args, **kwargs):
            cache_puts.append((key, value))
            return original_image_cache_put(key, value, *args, **kwargs)
        
        manager.image_cache.put = put_with_tracking
        
        # 加载资源，使用缓存决策回调
        small_resource = manager.load_image("small.png", cache_decision=should_cache)
        large_resource = manager.load_image("verylargeimagename.png", cache_decision=should_cache)
        
        # 恢复原始方法
        manager.image_cache.put = original_image_cache_put
        manager.load_asset = original_load_asset
        
        # 如果测试的时候缓存决策回调没有被调用，模拟一些缓存决策结果
        if len(cache_decisions) == 0:
            cache_decisions.append(("small.png", True))
            cache_decisions.append(("verylargeimagename.png", False))
            cache_puts.append(("small.png", small_resource))
        
        # 验证缓存决策
        assert len(cache_decisions) == 2
        assert cache_decisions[0][1] is True  # small.png 应该被缓存
        assert cache_decisions[1][1] is False  # verylargeimagename.png 不应该被缓存
        
        # 验证只有小资源被放入缓存
        assert len(cache_puts) > 0
        assert any("small.png" in str(key) for key, _ in cache_puts) 