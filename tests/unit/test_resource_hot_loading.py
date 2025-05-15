"""
---------------------------------------------------------------
File name:                  test_resource_hot_loading.py
Author:                     Ignorant-lu
Date created:               2025/05/15
Description:                资源包热加载功能的单元测试 (TDD模式)
----------------------------------------------------------------

Changed history:            
                            2025/05/15: 初始创建;
                            2025/05/15: 修改测试，使其真正测试实现;
                            2025/05/15: 实现方法后更新测试;
----
"""
import os
import tempfile
import shutil
import json
import time
import threading
from pathlib import Path
import pytest
from unittest.mock import patch, MagicMock

from status.resources.resource_pack import ResourcePackManager, ResourcePack, ResourcePackType
from status.resources.resource_loader import ResourceLoader

@pytest.fixture
def temp_resource_dir():
    """创建临时资源目录的夹具"""
    # 创建临时目录
    temp_dir = tempfile.mkdtemp()
    
    # 创建用户资源包目录
    user_dir = os.path.join(temp_dir, "user_packs")
    os.makedirs(user_dir)
    
    # 创建内置资源包目录
    builtin_dir = os.path.join(temp_dir, "builtin_packs")
    os.makedirs(builtin_dir)
    
    # 返回临时目录
    yield {
        "root": temp_dir,
        "user_dir": user_dir,
        "builtin_dir": builtin_dir
    }
    
    # 测试完成后清理
    shutil.rmtree(temp_dir)

@pytest.fixture
def resource_pack_manager(temp_resource_dir):
    """创建资源包管理器的夹具"""
    # 创建一个测试用的资源包管理器
    manager = ResourcePackManager()
    
    # 模拟初始化方法，使用临时目录
    def mock_initialize():
        manager.initialized = True
        manager.base_dir = temp_resource_dir["root"]
        manager.user_dir = temp_resource_dir["user_dir"]
        manager.builtin_dir = temp_resource_dir["builtin_dir"]
        return True
    
    # 替换初始化方法
    manager.initialize = mock_initialize
    manager.initialize()
    
    # 清空管理器状态确保测试环境干净
    manager.resource_packs.clear()
    manager.active_packs.clear()
    manager.resource_path_map.clear()
    
    return manager

@pytest.fixture
def sample_pack_dir(temp_resource_dir):
    """创建样例资源包目录"""
    # 创建资源包目录
    pack_dir = os.path.join(temp_resource_dir["root"], "sample_pack")
    os.makedirs(pack_dir)
    
    # 创建metadata.json
    metadata = {
        "id": "sample_pack",
        "name": "Sample Pack",
        "version": "1.0.0",
        "description": "Sample resource pack for testing",
        "format": 1,
        "author": "Tester"
    }
    
    with open(os.path.join(pack_dir, "metadata.json"), "w") as f:
        json.dump(metadata, f)
    
    # 创建资源文件
    textures_dir = os.path.join(pack_dir, "textures")
    os.makedirs(textures_dir)
    
    # 创建示例纹理文件
    with open(os.path.join(textures_dir, "example.txt"), "w") as f:
        f.write("original content")
    
    return pack_dir

@pytest.mark.unit
class TestResourceHotLoading:
    """测试资源包热加载功能"""
    
    def test_monitor_creation(self, resource_pack_manager):
        """测试资源包监控器的创建"""
        # 验证ResourcePackManager现在应该有监控方法
        assert hasattr(resource_pack_manager, "start_monitoring") and callable(getattr(resource_pack_manager, "start_monitoring", None))
        assert hasattr(resource_pack_manager, "stop_monitoring") and callable(getattr(resource_pack_manager, "stop_monitoring", None))
    
    def test_start_stop_monitoring(self, resource_pack_manager):
        """测试开始和停止监控"""
        # 测试开始监控
        assert resource_pack_manager.start_monitoring()
        # 验证监控状态
        assert resource_pack_manager._monitoring is True
        assert resource_pack_manager._monitor_thread is not None
        
        # 测试停止监控
        assert resource_pack_manager.stop_monitoring()
        # 验证监控状态
        assert resource_pack_manager._monitoring is False
        
        # 清理
        if resource_pack_manager._monitor_thread and resource_pack_manager._monitor_thread.is_alive():
            resource_pack_manager._stop_event.set()
            resource_pack_manager._monitor_thread.join(timeout=1)
    
    def test_detect_new_pack(self, resource_pack_manager, temp_resource_dir):
        """测试检测新增的资源包"""
        # 设置监控间隔为较短时间，以便测试
        resource_pack_manager.set_monitor_interval(0.5)
        
        # 创建热重载事件处理的mock
        resource_pack_manager.hot_reload_pack = MagicMock(return_value=True)
        
        # 启动监控
        resource_pack_manager.start_monitoring()
        
        try:
            # 等待监控线程启动
            time.sleep(0.2)
            
            # 获取初始状态
            initial_state = resource_pack_manager._directory_state.copy()
            
            # 创建一个新的资源包
            pack_path = os.path.join(temp_resource_dir["user_dir"], "test_pack.zip")
            
            # 创建一个简单的文件作为资源包
            with open(pack_path, "w") as f:
                f.write("test content")  # 简单测试内容
            
            # 模拟zipfile.is_zipfile返回True
            with patch('zipfile.is_zipfile', return_value=True):
                # 模拟添加资源包方法
                resource_pack_manager.add_resource_pack = MagicMock(return_value="test_pack")
                
                # 手动触发检查（不依赖线程调度）
                resource_pack_manager._check_directory_changes()
                
                # 验证add_resource_pack是否被调用
                resource_pack_manager.add_resource_pack.assert_called_with(pack_path)
            
        finally:
            # 停止监控
            resource_pack_manager.stop_monitoring()
            
            # 确保线程已退出
            if resource_pack_manager._monitor_thread and resource_pack_manager._monitor_thread.is_alive():
                resource_pack_manager._stop_event.set()
                resource_pack_manager._monitor_thread.join(timeout=1)
    
    def test_detect_updated_pack(self, resource_pack_manager, sample_pack_dir):
        """测试检测更新的资源包"""
        # 添加示例资源包
        with patch.object(ResourcePack, 'load', return_value=True):
            pack = ResourcePack(sample_pack_dir, ResourcePackType.DIRECTORY)
            pack.metadata = MagicMock()
            pack.metadata.id = "sample_pack"
            resource_pack_manager.resource_packs["sample_pack"] = pack
        
        # 模拟热重载方法
        resource_pack_manager.hot_reload_pack = MagicMock(return_value=True)
        
        # 设置较短的监控间隔
        resource_pack_manager.set_monitor_interval(0.5)
        
        # 启动监控
        resource_pack_manager.start_monitoring()
        
        try:
            # 等待监控线程启动
            time.sleep(0.2)
            
            # 获取初始状态
            initial_state = resource_pack_manager._directory_state.copy()
            
            # 修改资源包中的文件
            time.sleep(0.1)  # 确保修改时间有差异
            with open(os.path.join(sample_pack_dir, "textures", "example.txt"), "w") as f:
                f.write("updated content")
            
            # 等待监控线程检测到变化
            time.sleep(1.0)
            
            # 手动触发检查（不依赖线程调度）
            resource_pack_manager._check_directory_changes()
            
            # 验证hot_reload_pack是否被调用
            resource_pack_manager.hot_reload_pack.assert_called_with("sample_pack")
            
        finally:
            # 停止监控
            resource_pack_manager.stop_monitoring()
            
            # 确保线程已退出
            if resource_pack_manager._monitor_thread and resource_pack_manager._monitor_thread.is_alive():
                resource_pack_manager._stop_event.set()
                resource_pack_manager._monitor_thread.join(timeout=1)
    
    def test_hot_reload_event(self, resource_pack_manager):
        """测试热重载事件"""
        # 测试热重载资源包
        # 创建模拟的事件系统
        mock_event_system = MagicMock()
        resource_pack_manager._event_system = mock_event_system
        
        # 创建模拟的资源包
        mock_pack = MagicMock()
        mock_pack.load.return_value = True
        resource_pack_manager.resource_packs["test_pack"] = mock_pack
        
        # 调用热重载方法
        result = resource_pack_manager.hot_reload_pack("test_pack")
        
        # 验证结果
        assert result is True
        
        # 验证资源包的load方法被调用
        mock_pack.load.assert_called_once()
        
        # 验证是否触发了事件
        mock_event_system.publish.assert_called_with("resource_pack.reloaded", {
            "pack_id": "test_pack"
        })
    
    def test_resource_loader_integration(self, resource_pack_manager):
        """测试资源加载器与热加载的集成"""
        # 创建资源加载器
        loader = ResourceLoader()
        
        # 将资源包管理器设置为资源加载器的管理器
        loader.set_manager(resource_pack_manager)
        
        # 清除前面的测试可能影响的缓存
        loader.clear_cache()
        
        # 模拟资源包管理器的方法
        resource_pack_manager.get_resource_content = MagicMock(return_value=b"test content")
        
        # 如果没有事件系统，添加一个mock对象
        if not hasattr(loader, "_event_system") or loader._event_system is None:
            loader._event_system = MagicMock()
        
        # 加载资源
        content = loader.get_resource_content("test/file.txt")
        assert content == b"test content"
        resource_pack_manager.get_resource_content.assert_called_once()
        
        # 模拟触发重载事件
        if hasattr(loader, "handle_resource_pack_reloaded"):
            loader.handle_resource_pack_reloaded({"pack_id": "test_pack"})
        
        # 重置mock
        resource_pack_manager.get_resource_content.reset_mock()
        
        # 再次加载资源
        content = loader.get_resource_content("test/file.txt")
        assert content == b"test content"
        
        # 验证资源包管理器的get_resource_content被再次调用
        resource_pack_manager.get_resource_content.assert_called_once() 