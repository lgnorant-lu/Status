"""
---------------------------------------------------------------
File name:                  test_app.py
Author:                     Ignorant-lu
Date created:               2025/04/04
Description:                应用主类测试
----------------------------------------------------------------

Changed history:            
                            2025/04/04: 初始创建;
----
"""

import os
import pytest
from unittest.mock import MagicMock, patch

from status.core.app import Application

class TestApplication:
    """应用主类测试用例"""

    def test_singleton_pattern(self):
        """测试单例模式实现"""
        app1 = Application()
        app2 = Application()
        assert app1 is app2, "Application should be a singleton"

    def test_init(self):
        """测试应用初始化"""
        app = Application()
        assert app.running is False, "Application should not be running initially"
        assert isinstance(app.config, dict), "config should be a dictionary"
        assert isinstance(app.modules, dict), "modules should be a dictionary"

    def test_get_set_config(self):
        """测试配置获取和设置"""
        app = Application()
        
        # 测试获取默认值
        assert app.get_config("non_existent_key", "default") == "default"
        
        # 测试设置和获取值
        app.set_config("test_key", "test_value")
        assert app.get_config("test_key") == "test_value"
        
        # 测试无默认值的获取
        assert app.get_config("non_existent_key") is None

    def test_register_get_module(self):
        """测试模块注册和获取"""
        app = Application()
        
        # 创建模拟模块
        mock_module = MagicMock()
        mock_module.name = "test_module"
        
        # 注册模块
        app.register_module("test_module", mock_module)
        
        # 测试模块获取
        assert app.get_module("test_module") is mock_module
        assert app.get_module("non_existent_module") is None

    @patch('status.core.app.logging')
    def test_initialization_sequence(self, mock_logging):
        """测试初始化序列"""
        app = Application()
        
        # 创建模拟依赖模块
        app.resource_manager = MagicMock()
        app.event_system = MagicMock()
        app.monitor_system = MagicMock()
        app.renderer = MagicMock()
        app.scene_manager = MagicMock()
        
        # 测试初始化成功
        assert app.initialize() is True
        assert mock_logging.getLogger().info.called
        
        # 测试异常处理
        app.resource_manager.configure = MagicMock(side_effect=Exception("Test exception"))
        app.initialized = False  # 重置初始化状态
        assert app.initialize() is False  # 应当返回False表示初始化失败
        assert mock_logging.getLogger().error.called

    @patch('status.core.app.logging')
    def test_shutdown(self, mock_logging):
        """测试应用关闭"""
        app = Application()
        app.running = True
        
        # 模拟依赖模块
        app.resource_manager = MagicMock()
        app.event_system = MagicMock()
        app.monitor_system = MagicMock()
        app.renderer = MagicMock()
        app.scene_manager = MagicMock()
        
        # 执行关闭
        app.shutdown()
        
        # 验证结果
        assert app.running is False
        assert mock_logging.getLogger().info.called

    @pytest.mark.skip(reason="需要实际实现后测试")
    def test_run(self):
        """测试应用运行（需要实际实现后测试）"""
        pass 