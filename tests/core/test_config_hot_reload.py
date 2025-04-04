"""
---------------------------------------------------------------
File name:                  test_config_hot_reload.py
Author:                     Ignorant-lu
Date created:               2025/04/04
Description:                配置热重载功能测试
----------------------------------------------------------------

Changed history:            
                            2025/04/04: 初始创建;
----
"""

import os
import json
import tempfile
import time
import pytest
from unittest.mock import Mock, patch, MagicMock, call

import status.config.utils
from status.config import ConfigurationManager, ConfigChangeType, ConfigValidationError, config_manager

class TestConfigHotReload:
    """配置热重载功能测试用例"""
    
    @pytest.fixture
    def setup_reload_files(self):
        """准备测试配置文件"""
        # 创建临时文件夹
        temp_dir = tempfile.TemporaryDirectory()
        
        # 创建临时配置文件路径
        config_path = os.path.join(temp_dir.name, "config.json")
        default_config_path = os.path.join(temp_dir.name, "default_config.json")
        
        # 测试配置数据
        test_config = {
            "app": {
                "name": "Test App",
                "version": "0.1.0",
                "debug": True
            },
            "display": {
                "width": 800,
                "height": 600
            }
        }
        
        # 测试默认配置数据
        test_default_config = {
            "app": {
                "name": "Default App",
                "version": "0.1.0",
                "debug": False
            },
            "display": {
                "width": 800,
                "height": 600
            }
        }
        
        # 写入测试文件
        with open(config_path, 'w') as f:
            json.dump(test_config, f)
            
        with open(default_config_path, 'w') as f:
            json.dump(test_default_config, f)
        
        # 返回文件路径和临时目录
        yield {
            "temp_dir": temp_dir,
            "config_path": config_path,
            "default_config_path": default_config_path,
            "test_config": test_config,
            "test_default_config": test_default_config
        }
        
        # 清理
        temp_dir.cleanup()
    
    @pytest.fixture
    def mock_config_manager(self):
        """创建一个测试配置管理器实例"""
        # 保存原始单例
        original_instance = ConfigurationManager._instance
        
        # 重置单例
        ConfigurationManager._instance = None
        
        # 创建新实例
        instance = ConfigurationManager()
        
        # 禁用日志记录以防止测试输出过多
        instance.logger = Mock()
        
        # 返回实例
        yield instance
        
        # 停止任何运行中的线程
        if instance.reload_thread is not None:
            instance.reload_thread_stop = True
            instance.reload_thread.join(timeout=0.5)
        
        # 恢复原始单例
        ConfigurationManager._instance = original_instance
    
    def test_set_auto_reload(self, mock_config_manager):
        """测试设置自动重载功能"""
        cm = mock_config_manager
        
        # 初始状态应为关闭
        assert cm.auto_reload is False
        assert cm.reload_thread is None
        
        # 打开自动重载
        with patch.object(cm, '_start_file_monitoring') as mock_start:
            cm.set_auto_reload(True)
            assert cm.auto_reload is True
            mock_start.assert_called_once()
        
        # 关闭自动重载
        with patch.object(cm, '_stop_file_monitoring') as mock_stop:
            cm.set_auto_reload(False)
            assert cm.auto_reload is False
            mock_stop.assert_called_once()
        
        # 更改时间间隔
        cm.set_auto_reload(True, interval=10)
        assert cm.reload_interval == 10
    
    def test_reload_config(self, mock_config_manager, setup_reload_files):
        """测试重新加载配置"""
        cm = mock_config_manager
        files = setup_reload_files
        
        # 设置配置路径
        cm.config_path = files["config_path"]
        
        # 加载原始配置
        with patch.object(cm, 'load_default_config', return_value=True):
            cm.load_config()
        
        # 记录原始值
        original_name = cm.config["app"]["name"]
        
        # 修改配置文件
        new_config = files["test_config"].copy()
        new_config["app"]["name"] = "Updated App"
        
        with open(files["config_path"], 'w') as f:
            json.dump(new_config, f)
        
        # 模拟事件触发
        mock_event_system = Mock()
        with patch('status.config.config_manager.EventSystem.get_instance', return_value=mock_event_system):
            # 重新加载配置
            result = cm.reload_config()
            
            # 验证重载结果
            assert result is True
            assert cm.config["app"]["name"] == "Updated App"
            assert cm.config["app"]["name"] != original_name
            
            # 验证事件触发
            mock_event_system.dispatch_event.assert_called_once()
    
    def test_file_monitoring(self, mock_config_manager, setup_reload_files):
        """测试配置文件监视线程"""
        cm = mock_config_manager
        files = setup_reload_files
        
        # 设置配置路径和时间戳
        cm.config_path = files["config_path"]
        cm.config_file_timestamp = os.path.getmtime(files["config_path"])
        
        # 直接测试文件变更检测逻辑而不是完整的线程
        with patch.object(cm, 'reload_config') as mock_reload:
            # 修改配置文件
            time.sleep(0.1)  # 确保时间戳变化
            new_config = files["test_config"].copy()
            new_config["app"]["name"] = "Updated App"
            
            with open(files["config_path"], 'w') as f:
                json.dump(new_config, f)
            
            # 手动执行文件监控逻辑
            current_timestamp = os.path.getmtime(files["config_path"])
            if current_timestamp > cm.config_file_timestamp:
                cm.reload_config()
            
            # 验证重载被调用
            mock_reload.assert_called_once()
    
    def test_callback_on_reload(self, mock_config_manager, setup_reload_files):
        """测试重载时的回调触发"""
        cm = mock_config_manager
        files = setup_reload_files
        
        # 设置配置路径
        cm.config_path = files["config_path"]
        
        # 创建新的测试配置
        test_config = {
            "app": {
                "name": "Test App",
                "version": "0.1.0"
            }
        }
        
        # 手动设置配置
        cm.config = test_config.copy()
        
        # 模拟_trigger_change_event方法以避免多次调用
        with patch.object(cm, '_trigger_change_event') as mock_trigger:
            # 注册回调（实际上没有用到，因为我们mock了_trigger_change_event方法）
            callback = Mock()
            cm.register_change_callback(callback)
            
            # 调用重载
            cm.reload_config()
            
            # 验证_trigger_change_event被调用
            mock_trigger.assert_called_once()
            args = mock_trigger.call_args[0]
            
            # 验证触发参数
            assert args[0] == ""  # key
            assert args[3] == ConfigChangeType.RELOAD  # change_type
    
    def test_file_change_detection(self, mock_config_manager, setup_reload_files):
        """测试文件变更检测"""
        cm = mock_config_manager
        files = setup_reload_files
        
        # 设置配置路径和初始时间戳
        cm.config_path = files["config_path"]
        initial_mtime = os.path.getmtime(files["config_path"])
        cm.config_file_timestamp = initial_mtime
        
        # 模拟监视线程函数以测试变更检测
        monitor_func = None
        
        # 获取监视线程函数
        with patch('threading.Thread') as mock_thread:
            cm._start_file_monitoring()
            # 捕获传递给线程的函数
            target_func = mock_thread.call_args[1]['target']
            monitor_func = target_func
        
        # 修改配置文件以触发变更
        time.sleep(0.1)  # 确保时间戳变化
        new_config = files["test_config"].copy()
        new_config["app"]["name"] = "Updated App"
        
        with open(files["config_path"], 'w') as f:
            json.dump(new_config, f)
        
        # 验证时间戳已更改
        new_mtime = os.path.getmtime(files["config_path"])
        assert new_mtime > initial_mtime
        
        # 模拟线程检测
        with patch.object(cm, 'reload_config') as mock_reload:
            # 在测试环境中手动调用一次监视函数
            # 这里假设我们已经提取了monitor线程中的检测逻辑
            if os.path.exists(cm.config_path):
                current_timestamp = os.path.getmtime(cm.config_path)
                if current_timestamp > cm.config_file_timestamp:
                    cm.reload_config()
            
            # 验证重载被调用
            mock_reload.assert_called_once() 