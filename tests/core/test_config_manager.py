"""
---------------------------------------------------------------
File name:                  test_config_manager.py
Author:                     Ignorant-lu
Date created:               2025/04/04
Description:                配置管理器测试
----------------------------------------------------------------

Changed history:            
                            2025/04/04: 初始创建;
----
"""

import os
import json
import tempfile
import threading
import time
import pytest
from unittest.mock import Mock, patch, MagicMock

from status.config import ConfigurationManager, ConfigChangeType, ConfigValidationError, config_manager

class TestConfigurationManager:
    """配置管理器测试用例"""
    
    @pytest.fixture
    def setup_config_files(self):
        """准备测试配置文件"""
        # 创建临时文件夹
        temp_dir = tempfile.TemporaryDirectory()
        
        # 创建临时配置文件路径
        config_path = os.path.join(temp_dir.name, "config.json")
        default_config_path = os.path.join(temp_dir.name, "default_config.json")
        schema_path = os.path.join(temp_dir.name, "config_schema.json")
        
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
            },
            "audio": {
                "enabled": True,
                "volume": 0.8
            }
        }
        
        # 测试配置模式
        test_schema = {
            "type": "object",
            "properties": {
                "app": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "version": {"type": "string"},
                        "debug": {"type": "boolean"}
                    }
                },
                "display": {
                    "type": "object",
                    "properties": {
                        "width": {"type": "integer", "minimum": 320},
                        "height": {"type": "integer", "minimum": 240}
                    }
                },
                "audio": {
                    "type": "object",
                    "properties": {
                        "enabled": {"type": "boolean"},
                        "volume": {"type": "number", "minimum": 0, "maximum": 1}
                    }
                }
            }
        }
        
        # 写入测试文件
        with open(config_path, 'w') as f:
            json.dump(test_config, f)
            
        with open(default_config_path, 'w') as f:
            json.dump(test_default_config, f)
            
        with open(schema_path, 'w') as f:
            json.dump(test_schema, f)
        
        # 返回文件路径和临时目录
        yield {
            "temp_dir": temp_dir,
            "config_path": config_path,
            "default_config_path": default_config_path,
            "schema_path": schema_path,
            "test_config": test_config,
            "test_default_config": test_default_config,
            "test_schema": test_schema
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
        
        # 返回实例
        yield instance
        
        # 恢复原始单例
        ConfigurationManager._instance = original_instance
    
    def test_singleton_pattern(self):
        """测试单例模式实现"""
        cm1 = ConfigurationManager()
        cm2 = ConfigurationManager()
        assert cm1 is cm2, "ConfigurationManager should be a singleton"
        
        # 验证全局实例
        assert config_manager is ConfigurationManager._instance
    
    def test_initialization(self, mock_config_manager):
        """测试初始化方法"""
        cm = mock_config_manager
        
        # 验证默认属性
        assert isinstance(cm.config, dict)
        assert isinstance(cm.default_config, dict)
        assert isinstance(cm.schema, dict)
        assert cm.config_path == "config.json"
        assert cm.schema_path == "config_schema.json"
        assert cm.auto_reload is False
        assert cm.reload_interval == 5
        assert cm.reload_thread is None
    
    def test_initialize_with_paths(self, mock_config_manager, setup_config_files):
        """测试使用自定义路径初始化"""
        cm = mock_config_manager
        files = setup_config_files
        
        # 初始化配置管理器
        with patch('os.path.exists', return_value=True):
            with patch('builtins.open', create=True):
                result = cm.initialize(
                    config_path=files["config_path"],
                    schema_path=files["schema_path"],
                    auto_reload=True,
                    reload_interval=2
                )
        
        # 验证路径设置
        assert cm.config_path == files["config_path"]
        assert cm.schema_path == files["schema_path"]
        assert cm.auto_reload is True
        assert cm.reload_interval == 2

    def test_basic_config_loading(self, mock_config_manager, setup_config_files):
        """测试基本配置加载"""
        cm = mock_config_manager
        files = setup_config_files
        
        # 替换默认路径和加载方法
        original_path = cm.config_path
        cm.config_path = files["config_path"]
        
        # 模拟load_default_config
        with patch.object(cm, 'load_default_config', return_value=True):
            with patch.object(cm, '_start_file_monitoring'):
                # 加载配置
                result = cm.load_config()
                
                # 验证配置加载
                assert result is True
                assert cm.config is not None
                assert "app" in cm.config
                assert cm.config["app"]["name"] == "Test App"
        
        # 恢复原始路径
        cm.config_path = original_path 

    def test_get_nested_config(self, mock_config_manager):
        """测试获取嵌套配置项"""
        cm = mock_config_manager
        
        # 设置测试配置
        cm.config = {
            "app": {
                "name": "Test App",
                "settings": {
                    "debug": True,
                    "logging": {
                        "level": "info"
                    }
                }
            }
        }
        
        # 测试一级嵌套
        assert cm.get("app.name") == "Test App"
        
        # 测试二级嵌套
        assert cm.get("app.settings.debug") is True
        
        # 测试三级嵌套
        assert cm.get("app.settings.logging.level") == "info"
        
        # 测试不存在的路径
        assert cm.get("app.version") is None
        assert cm.get("app.settings.non_existent") is None
        assert cm.get("non_existent.path") is None
        
        # 测试默认值
        assert cm.get("app.version", "0.1.0") == "0.1.0"

    def test_set_nested_config(self, mock_config_manager):
        """测试设置嵌套配置项"""
        cm = mock_config_manager
        
        # 初始化空配置
        cm.config = {}
        
        # 模拟保存方法
        with patch.object(cm, 'save_config', return_value=True):
            # 设置一级嵌套
            assert cm.set("app.name", "Test App") is True
            assert cm.config["app"]["name"] == "Test App"
            
            # 设置二级嵌套
            assert cm.set("app.settings.debug", True) is True
            assert cm.config["app"]["settings"]["debug"] is True
            
            # 设置三级嵌套
            assert cm.set("app.settings.logging.level", "info") is True
            assert cm.config["app"]["settings"]["logging"]["level"] == "info"
            
            # 尝试在非字典类型上设置属性
            cm.config["app"]["version"] = "0.1.0"
            assert cm.set("app.version.build", "123") is False

    def test_config_reset(self, mock_config_manager):
        """测试重置配置功能"""
        cm = mock_config_manager
        
        # 设置测试配置和默认配置
        cm.config = {
            "app": {
                "name": "Custom App",
                "version": "0.2.0",
                "debug": True
            },
            "display": {
                "width": 1024,
                "height": 768
            }
        }
        
        cm.default_config = {
            "app": {
                "name": "Default App",
                "version": "0.1.0",
                "debug": False
            },
            "display": {
                "width": 800,
                "height": 600
            },
            "audio": {
                "enabled": True
            }
        }
        
        # 模拟保存方法
        with patch.object(cm, 'save_config', return_value=True):
            # 重置单个配置项
            assert cm.reset("app.name") is True
            assert cm.config["app"]["name"] == "Default App"
            assert cm.config["app"]["version"] == "0.2.0"  # 其他项不受影响
            
            # 重置包含嵌套项的配置节
            assert cm.reset("app") is True
            assert cm.config["app"] == cm.default_config["app"]
            
            # 重置不存在于默认配置中的项（应删除该项）
            cm.config["custom"] = {"setting": "value"}
            assert cm.reset("custom") is True
            assert "custom" not in cm.config
            
            # 重置所有配置
            cm.config["extra"] = "value"  # 添加额外项
            assert cm.reset() is True
            assert cm.config == cm.default_config

    def test_delete_config_item(self, mock_config_manager):
        """测试删除配置项功能"""
        cm = mock_config_manager
        
        # 设置测试配置
        cm.config = {
            "app": {
                "name": "Test App",
                "settings": {
                    "debug": True,
                    "logging": {
                        "level": "info"
                    }
                }
            }
        }
        
        # 模拟保存方法
        with patch.object(cm, 'save_config', return_value=True):
            # 删除叶子节点
            assert cm.delete("app.settings.logging.level") is True
            assert "level" not in cm.config["app"]["settings"]["logging"]
            
            # 删除中间节点
            assert cm.delete("app.settings.logging") is True
            assert "logging" not in cm.config["app"]["settings"]
            
            # 删除不存在的项
            assert cm.delete("non_existent.path") is True  # 不存在的项视为删除成功
            
            # 删除根节点项
            assert cm.delete("app") is True
            assert "app" not in cm.config
            
            # 尝试删除空路径
            assert cm.delete("") is False

    def test_merge_configs(self, mock_config_manager):
        """测试配置合并功能"""
        cm = mock_config_manager
        
        # 基础配置
        base_config = {
            "app": {
                "name": "Base App",
                "version": "0.1.0",
                "debug": False
            },
            "display": {
                "width": 800,
                "height": 600
            }
        }
        
        # 覆盖配置
        override_config = {
            "app": {
                "name": "Override App",
                "debug": True
            },
            "audio": {
                "enabled": True
            }
        }
        
        # 测试合并
        merged = cm._merge_configs(base_config, override_config)
        
        # 验证已覆盖的项
        assert merged["app"]["name"] == "Override App"
        assert merged["app"]["debug"] is True
        
        # 验证未覆盖的项保持不变
        assert merged["app"]["version"] == "0.1.0"
        assert merged["display"]["width"] == 800
        assert merged["display"]["height"] == 600
        
        # 验证新增的项
        assert "audio" in merged
        assert merged["audio"]["enabled"] is True
        
        # 测试受保护键
        cm.protected_keys.add("app.name")
        protected_merged = cm._merge_configs(base_config, override_config)
        assert protected_merged["app"]["name"] == "Base App"  # 保持原值

    def test_register_unregister_callback(self, mock_config_manager):
        """测试注册和注销回调函数"""
        cm = mock_config_manager
        
        # 创建测试回调
        callback1 = Mock()
        callback2 = Mock()
        
        # 注册全局回调
        cm.register_change_callback(callback1)
        assert "" in cm.change_callbacks
        assert callback1 in cm.change_callbacks[""]
        
        # 注册特定键的回调
        cm.register_change_callback(callback2, "app.name")
        assert "app.name" in cm.change_callbacks
        assert callback2 in cm.change_callbacks["app.name"]
        
        # 注销特定回调
        result = cm.unregister_change_callback(callback2, "app.name")
        assert result is True
        assert callback2 not in cm.change_callbacks["app.name"]
        
        # 尝试注销不存在的回调
        result = cm.unregister_change_callback(callback2, "non_existent")
        assert result is False
        
        # 注销全局回调
        result = cm.unregister_change_callback(callback1)
        assert result is True
        assert callback1 not in cm.change_callbacks[""] 