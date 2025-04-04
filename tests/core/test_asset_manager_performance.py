"""
---------------------------------------------------------------
File name:                  test_asset_manager_performance.py
Author:                     Ignorant-lu
Date created:               2025/04/03
Description:                资产管理器性能测试
----------------------------------------------------------------

Changed history:            
                            2025/04/03: 初始创建;
----
"""

import os
import time
import pytest
import threading
import concurrent.futures
import random
from unittest.mock import patch, MagicMock, Mock

from status.resources.asset_manager import AssetManager
from status.resources.resource_loader import ResourceType
from status.resources.cache import Cache, CacheStrategy

class TestAssetManagerPerformance:
    """资产管理器性能测试用例"""
    
    def setup_method(self):
        """每个测试方法前的设置"""
        # 清除单例实例以确保测试相互独立
        if hasattr(AssetManager, '_instance'):
            AssetManager._instance = None
    
    @patch('status.resources.asset_manager.logging')
    def test_concurrent_loading(self, mock_logging):
        """测试并发加载资源"""
        # 跳过集成测试以避免CI/CD延迟，除非明确启用
        pytest.skip("跳过耗时的性能测试，除非明确启用")
        
        manager = AssetManager()
        
        # 模拟资源加载
        def mock_load_resource(path):
            # 模拟不同加载时间
            time.sleep(random.uniform(0.01, 0.05))
            return {"path": path, "data": f"data_{path}"}
        
        # 替换实际的资源加载方法
        manager._load_image = lambda path, **kwargs: mock_load_resource(path)
        
        # 生成一系列资源路径
        resource_paths = [f"resource_{i}.png" for i in range(100)]
        
        # 测量并发加载时间
        start_time = time.time()
        
        # 使用线程池并发加载资源
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(manager.load_image, path) for path in resource_paths]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        end_time = time.time()
        concurrent_time = end_time - start_time
        
        # 测量顺序加载时间
        start_time = time.time()
        sequential_results = [manager.load_image(path) for path in resource_paths]
        end_time = time.time()
        sequential_time = end_time - start_time
        
        # 确认所有资源都已加载
        assert len(results) == len(resource_paths)
        
        # 记录时间比较
        print(f"\n并发加载时间: {concurrent_time:.2f}秒")
        print(f"顺序加载时间: {sequential_time:.2f}秒")
        print(f"性能提升: {sequential_time / concurrent_time:.2f}倍")
        
        # 验证并发加载明显快于顺序加载
        assert concurrent_time < sequential_time
    
    @patch('status.resources.asset_manager.logging')
    def test_cache_hit_performance(self, mock_logging):
        """测试缓存命中率对性能的影响"""
        # 跳过集成测试以避免CI/CD延迟，除非明确启用
        pytest.skip("跳过耗时的性能测试，除非明确启用")
        
        manager = AssetManager()
        
        # 模拟资源加载，有一定的加载时间
        def mock_load_resource(path, use_cache=True):
            if not use_cache:
                time.sleep(0.02)  # 模拟从磁盘加载的时间
            return {"path": path, "data": f"data_{path}"}
        
        # 替换实际的资源加载方法
        manager._load_image = lambda path, **kwargs: mock_load_resource(path, False)
        
        # 生成一系列资源路径
        resource_paths = [f"resource_{i % 20}.png" for i in range(1000)]  # 有重复路径
        
        # 预热缓存
        for i in range(20):
            manager.load_image(f"resource_{i}.png", use_cache=True)
        
        # 测量有缓存的加载时间
        start_time = time.time()
        with_cache_results = [manager.load_image(path, use_cache=True) for path in resource_paths]
        end_time = time.time()
        with_cache_time = end_time - start_time
        
        # 清除缓存
        manager.clear_cache()
        
        # 测量无缓存的加载时间
        start_time = time.time()
        no_cache_results = [manager.load_image(path, use_cache=False) for path in resource_paths]
        end_time = time.time()
        no_cache_time = end_time - start_time
        
        # 获取缓存统计信息
        cache_stats = manager.get_cache_stats()
        
        # 记录结果
        print(f"\n有缓存加载时间: {with_cache_time:.2f}秒")
        print(f"无缓存加载时间: {no_cache_time:.2f}秒")
        print(f"性能提升: {no_cache_time / with_cache_time:.2f}倍")
        print(f"缓存命中率: {cache_stats['image']['hits'] / (cache_stats['image']['hits'] + cache_stats['image']['misses']):.2%}")
        
        # 验证有缓存的加载明显快于无缓存
        assert with_cache_time < no_cache_time
    
    @patch('status.resources.asset_manager.logging')
    def test_cache_strategy_performance(self, mock_logging):
        """测试不同缓存策略的性能比较"""
        # 跳过集成测试以避免CI/CD延迟，除非明确启用
        pytest.skip("跳过耗时的性能测试，除非明确启用")
        
        # 创建包含不同缓存策略的资产管理器实例
        strategies = [
            (CacheStrategy.LRU, "LRU"),
            (CacheStrategy.FIFO, "FIFO"),
            (CacheStrategy.LFU, "LFU"),
            (CacheStrategy.TTL, "TTL")
        ]
        
        results = {}
        
        for strategy, name in strategies:
            # 清除单例实例
            if hasattr(AssetManager, '_instance'):
                AssetManager._instance = None
            
            # 创建新实例
            manager = AssetManager()
            
            # 替换缓存为指定策略
            max_size = 50
            manager.image_cache = Cache(max_size=max_size, strategy=strategy)
            
            # 模拟资源加载
            def mock_load_resource(path, **kwargs):
                time.sleep(0.01)  # 模拟从磁盘加载的时间
                return {"path": path, "data": f"data_{path}"}
            
            manager._load_image = mock_load_resource
            
            # 为LRU/LFU策略生成符合其特性的访问模式
            if strategy in [CacheStrategy.LRU, CacheStrategy.LFU]:
                # 创建偏向的访问模式，前10个资源被频繁访问
                resource_paths = []
                for _ in range(200):
                    if random.random() < 0.8:  # 80%的概率访问热点资源
                        resource_paths.append(f"hot_resource_{random.randint(0, 9)}.png")
                    else:
                        resource_paths.append(f"cold_resource_{random.randint(0, 100)}.png")
            else:
                # 对于FIFO和TTL，使用均匀分布
                resource_paths = [f"resource_{random.randint(0, 100)}.png" for _ in range(200)]
            
            # 测量加载时间
            start_time = time.time()
            for path in resource_paths:
                manager.load_image(path)
            end_time = time.time()
            
            # 计算命中率
            stats = manager.get_cache_stats()
            hits = stats["image"]["hits"]
            misses = stats["image"]["misses"]
            hit_rate = hits / (hits + misses) if (hits + misses) > 0 else 0
            
            results[name] = {
                "time": end_time - start_time,
                "hit_rate": hit_rate,
                "hits": hits,
                "misses": misses
            }
        
        # 输出结果比较
        print("\n不同缓存策略性能比较:")
        for name, data in results.items():
            print(f"{name}: 时间 {data['time']:.2f}秒, 命中率 {data['hit_rate']:.2%}, "
                  f"命中 {data['hits']}, 未命中 {data['misses']}")
        
        # 验证结果符合预期
        # 对于偏向的访问模式，LFU和LRU应该有更高的命中率
        if CacheStrategy.LRU in [s[0] for s in strategies] and CacheStrategy.FIFO in [s[0] for s in strategies]:
            assert results["LRU"]["hit_rate"] > results["FIFO"]["hit_rate"]
    
    @patch('status.resources.asset_manager.logging')
    def test_memory_usage(self, mock_logging):
        """测试内存使用情况"""
        # 跳过集成测试以避免CI/CD延迟，除非明确启用
        pytest.skip("跳过耗时的性能测试，除非明确启用")
        
        try:
            import psutil
            process = psutil.Process(os.getpid())
        except ImportError:
            pytest.skip("psutil未安装，跳过内存使用测试")
        
        # 创建资产管理器
        manager = AssetManager()
        
        # 记录初始内存使用
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # 创建大型模拟资源
        large_resource_size = 1 * 1024 * 1024  # 1MB
        large_resource = bytearray(large_resource_size)
        
        # 模拟资源加载函数，返回大型资源
        def mock_load_resource(path, **kwargs):
            return large_resource
        
        manager._load_image = mock_load_resource
        
        # 加载多个大型资源
        resources_count = 20
        resource_paths = [f"large_resource_{i}.png" for i in range(resources_count)]
        
        for path in resource_paths:
            manager.load_image(path)
        
        # 记录加载后内存使用
        after_loading_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # 清除缓存
        manager.clear_cache()
        
        # 强制垃圾回收
        import gc
        gc.collect()
        
        # 记录清除后内存使用
        after_clearing_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # 计算内存增加和释放
        memory_increase = after_loading_memory - initial_memory
        memory_released = after_loading_memory - after_clearing_memory
        
        # 输出结果
        print(f"\n初始内存使用: {initial_memory:.2f} MB")
        print(f"加载后内存使用: {after_loading_memory:.2f} MB")
        print(f"清除后内存使用: {after_clearing_memory:.2f} MB")
        print(f"内存增加: {memory_increase:.2f} MB")
        print(f"内存释放: {memory_released:.2f} MB")
        
        # 验证内存有显著增加和释放
        assert memory_increase > 0
        assert memory_released > 0
        
        # 验证释放的内存与加载的资源大小相关
        expected_memory_usage = resources_count * large_resource_size / 1024 / 1024  # MB
        # 允许50%的误差，因为内存分配和垃圾回收存在系统差异
        assert memory_released > expected_memory_usage * 0.5 