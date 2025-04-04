"""
---------------------------------------------------------------
File name:                  test_environment_config.py
Author:                     Ignorant-lu
Date created:               2025/04/04
Description:                配置环境功能测试
----------------------------------------------------------------

Changed history:            
                            2025/04/04: 初始创建;
----
"""

import os
import json
import tempfile
import pytest
from unittest.mock import Mock, patch, MagicMock

from status.config import ConfigurationManager, ConfigEnvironment, ConfigChangeType, ConfigValidationError, config_manager

class TestEnvironmentConfig:
    """配置环境功能测试用例"""
    
    @pytest.fixture
    def setup_env_files(self):
        """准备环境配置文件"""
        # 创建临时文件夹
        temp_dir = tempfile.TemporaryDirectory()
        
        # 创建临时配置文件路径
        config_path = os.path.join(temp_dir.name, "config.json")
        default_config_path = os.path.join(temp_dir.name, "default_config.json")
        
        # 环境配置文件
        dev_config_path = os.path.join(temp_dir.name, "config.development.json")
        test_config_path = os.path.join(temp_dir.name, "config.testing.json")
        prod_config_path = os.path.join(temp_dir.name, "config.production.json")
        
        # 测试用户配置
        user_config = {
            "app": {
                "name": "User App",
                "theme": "dark"
            }
        }
        
        # 测试默认配置
        default_config = {
            "app": {
                "name": "Default App",
                "version": "0.1.0",
                "theme": "light",
                "debug": False
            },
            "display": {
                "width": 800,
                "height": 600
            }
        }
        
        # 开发环境配置
        dev_config = {
            "app": {
                "debug": True,
                "log_level": "debug"
            },
            "development": {
                "enable_inspector": True
            }
        }
        
        # 测试环境配置
        test_config = {
            "app": {
                "name": "Test App",
                "log_level": "info"
            },
            "testing": {
                "mock_services": True
            }
        }
        
        # 生产环境配置
        prod_config = {
            "app": {
                "log_level": "warning"
            },
            "performance": {
                "optimize": True
            }
        }
        
        # 写入测试文件
        with open(config_path, 'w') as f:
            json.dump(user_config, f)
            
        with open(default_config_path, 'w') as f:
            json.dump(default_config, f)
            
        with open(dev_config_path, 'w') as f:
            json.dump(dev_config, f)
            
        with open(test_config_path, 'w') as f:
            json.dump(test_config, f)
            
        with open(prod_config_path, 'w') as f:
            json.dump(prod_config, f)
        
        # 返回文件路径和临时目录
        yield {
            "temp_dir": temp_dir,
            "config_path": config_path,
            "default_config_path": default_config_path,
            "dev_config_path": dev_config_path,
            "test_config_path": test_config_path,
            "prod_config_path": prod_config_path,
            "user_config": user_config,
            "default_config": default_config,
            "dev_config": dev_config,
            "test_config": test_config,
            "prod_config": prod_config
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
        
        # 恢复原始单例
        ConfigurationManager._instance = original_instance
    
    def test_load_environment_configs(self, mock_config_manager, setup_env_files):
        """测试加载环境配置"""
        cm = mock_config_manager
        files = setup_env_files
        
        # 设置环境配置模板
        cm.env_config_template = os.path.join(files["temp_dir"].name, "config.{}.json")
        
        # 手动调用环境配置加载
        cm._load_environment_configs()
        
        # 验证环境配置已加载
        assert len(cm.env_configs) == 3
        assert ConfigEnvironment.DEVELOPMENT in cm.env_configs
        assert ConfigEnvironment.TESTING in cm.env_configs
        assert ConfigEnvironment.PRODUCTION in cm.env_configs
        
        # 验证环境配置内容
        assert cm.env_configs[ConfigEnvironment.DEVELOPMENT]["app"]["debug"] is True
        assert cm.env_configs[ConfigEnvironment.TESTING]["app"]["name"] == "Test App"
        assert cm.env_configs[ConfigEnvironment.PRODUCTION]["app"]["log_level"] == "warning"
    
    def test_get_environment_config(self, mock_config_manager, setup_env_files):
        """测试获取环境配置"""
        cm = mock_config_manager
        files = setup_env_files
        
        # 设置环境配置
        cm.env_configs = {
            ConfigEnvironment.DEVELOPMENT: files["dev_config"],
            ConfigEnvironment.TESTING: files["test_config"],
            ConfigEnvironment.PRODUCTION: files["prod_config"]
        }
        
        # 获取当前环境配置
        cm.environment = ConfigEnvironment.DEVELOPMENT
        env_config = cm.get_environment_config()
        assert env_config == files["dev_config"]
        
        # 获取指定环境配置
        env_config = cm.get_environment_config(ConfigEnvironment.TESTING)
        assert env_config == files["test_config"]
        
        # 获取不存在的环境配置
        cm.env_configs.clear()
        env_config = cm.get_environment_config()
        assert env_config == {}
    
    def test_set_environment(self, mock_config_manager, setup_env_files):
        """测试设置当前环境"""
        cm = mock_config_manager
        files = setup_env_files
        
        # 设置初始环境和配置
        cm.environment = ConfigEnvironment.DEVELOPMENT
        cm.config = {"initial": "config"}
        
        # 模拟重载配置
        with patch.object(cm, 'reload_config', return_value=True):
            # 切换到测试环境
            result = cm.set_environment(ConfigEnvironment.TESTING)
            
            # 验证环境已切换
            assert result is True
            assert cm.environment == ConfigEnvironment.TESTING
            
            # 验证重载配置被调用
            cm.reload_config.assert_called_once()
    
    def test_environment_fallback(self, mock_config_manager, setup_env_files):
        """测试环境切换失败时的回退"""
        cm = mock_config_manager
        files = setup_env_files
        
        # 设置初始环境
        cm.environment = ConfigEnvironment.DEVELOPMENT
        
        # 模拟重载配置失败
        with patch.object(cm, 'reload_config', return_value=False):
            # 尝试切换到生产环境
            result = cm.set_environment(ConfigEnvironment.PRODUCTION)
            
            # 验证环境切换失败
            assert result is False
            assert cm.environment == ConfigEnvironment.DEVELOPMENT  # 保持原环境
    
    def test_config_loading_with_environment(self, mock_config_manager, setup_env_files):
        """测试包含环境配置的加载过程"""
        cm = mock_config_manager
        files = setup_env_files
        
        # 设置配置路径
        cm.config_path = files["config_path"]
        cm.default_config_path = files["default_config_path"]
        
        # 设置环境
        cm.environment = ConfigEnvironment.TESTING
        
        # 预先设置环境配置
        cm.env_configs = {
            ConfigEnvironment.TESTING: files["test_config"]
        }
        
        # 模拟_merge_configs方法来检查传入的参数
        original_merge = cm._merge_configs
        merge_calls = []
        
        def mock_merge(base, override):
            merge_calls.append((base, override))
            return original_merge(base, override)
            
        cm._merge_configs = mock_merge
        
        # 模拟load_default_config方法
        with patch.object(cm, 'load_default_config', return_value=True):
            # 手动设置默认配置
            cm.default_config = files["default_config"]
            
            # 加载配置
            result = cm.load_config()
            
            # 验证加载成功
            assert result is True
            
            # 验证合并顺序:
            # 1. 默认配置与环境配置合并
            # 2. 结果与用户配置合并
            assert len(merge_calls) >= 2
            
            # 检查第一次合并 - 默认配置与环境配置
            first_base, first_override = merge_calls[0]
            assert "app" in first_base
            assert first_base["app"]["name"] == "Default App"  # 默认配置
            assert "app" in first_override
            assert first_override["app"]["name"] == "Test App"  # 测试环境配置
            
            # 检查配置结果
            assert cm.config["app"]["name"] == "User App"  # 用户配置优先
            assert cm.config["app"]["debug"] is False  # 默认配置
            assert "testing" in cm.config  # 测试环境特定配置
            assert cm.config["testing"]["mock_services"] is True
    
    def test_environment_specific_features(self, mock_config_manager, setup_env_files):
        """测试不同环境的特定功能"""
        cm = mock_config_manager
        files = setup_env_files
        
        # 设置配置路径和环境配置
        cm.config_path = files["config_path"]
        cm.default_config_path = files["default_config_path"]
        cm.env_configs = {
            ConfigEnvironment.DEVELOPMENT: files["dev_config"],
            ConfigEnvironment.TESTING: files["test_config"],
            ConfigEnvironment.PRODUCTION: files["prod_config"]
        }
        
        # 设置默认配置
        cm.default_config = files["default_config"]
        
        # 测试开发环境特性
        cm.environment = ConfigEnvironment.DEVELOPMENT
        with patch.object(cm, '_merge_configs', side_effect=lambda base, override: {**base, **override}):
            cm.load_config()
            assert cm.get("app.debug") is True
            assert cm.get("development.enable_inspector") is True
            assert cm.get("testing.mock_services") is None
            
        # 测试测试环境特性
        cm.environment = ConfigEnvironment.TESTING
        with patch.object(cm, '_merge_configs', side_effect=lambda base, override: {**base, **override}):
            cm.load_config()
            assert cm.get("app.name") == "User App"  # 用户配置优先
            assert cm.get("testing.mock_services") is True
            assert cm.get("development.enable_inspector") is None
            
        # 测试生产环境特性
        cm.environment = ConfigEnvironment.PRODUCTION
        with patch.object(cm, '_merge_configs', side_effect=lambda base, override: {**base, **override}):
            cm.load_config()
            assert cm.get("app.log_level") == "warning"
            assert cm.get("performance.optimize") is True
            assert cm.get("development.enable_inspector") is None 