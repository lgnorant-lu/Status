"""
---------------------------------------------------------------
File name:                  test_config_diff.py
Author:                     Ignorant-lu
Date created:               2025/04/04
Description:                配置差异化保存功能测试
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
from status.config.utils import ConfigDiff

class TestConfigDiff:
    """配置差异化保存功能测试用例"""
    
    @pytest.fixture
    def setup_diff_files(self):
        """准备测试配置文件"""
        # 创建临时文件夹
        temp_dir = tempfile.TemporaryDirectory()
        
        # 创建临时配置文件路径
        config_path = os.path.join(temp_dir.name, "config.json")
        default_config_path = os.path.join(temp_dir.name, "default_config.json")
        
        # 测试默认配置
        default_config = {
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
        
        # 测试用户配置（只包含与默认值不同的部分）
        user_config = {
            "app": {
                "name": "User App",
                "debug": True
            },
            "display": {
                "width": 1024
            }
        }
        
        # 写入测试文件
        with open(config_path, 'w') as f:
            json.dump(user_config, f)
            
        with open(default_config_path, 'w') as f:
            json.dump(default_config, f)
        
        # 返回文件路径和临时目录
        yield {
            "temp_dir": temp_dir,
            "config_path": config_path,
            "default_config_path": default_config_path,
            "user_config": user_config,
            "default_config": default_config
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
    
    def test_get_diff(self):
        """测试获取配置差异"""
        # 默认配置
        default_config = {
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
        
        # 用户配置（完整配置）
        user_config = {
            "app": {
                "name": "User App",
                "version": "0.1.0",
                "debug": True
            },
            "display": {
                "width": 1024,
                "height": 600
            }
        }
        
        # 获取差异
        diff = ConfigDiff.get_diff(user_config, default_config)
        
        # 验证差异只包含与默认值不同的部分
        assert "app" in diff
        assert "name" in diff["app"]
        assert diff["app"]["name"] == "User App"
        assert "debug" in diff["app"]
        assert diff["app"]["debug"] is True
        assert "version" not in diff["app"]  # 相同值不应包含在差异中
        
        assert "display" in diff
        assert "width" in diff["display"]
        assert diff["display"]["width"] == 1024
        assert "height" not in diff["display"]  # 相同值不应包含在差异中
    
    def test_merge_with_defaults(self):
        """测试与默认配置合并"""
        # 默认配置
        default_config = {
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
        
        # 差异配置
        diff_config = {
            "app": {
                "name": "User App",
                "debug": True
            },
            "display": {
                "width": 1024
            }
        }
        
        # 合并配置
        merged = ConfigDiff.merge_with_defaults(diff_config, default_config)
        
        # 验证合并结果
        assert merged["app"]["name"] == "User App"  # 差异配置中的值
        assert merged["app"]["version"] == "0.1.0"  # 默认配置中的值
        assert merged["app"]["debug"] is True  # 差异配置中的值
        
        assert merged["display"]["width"] == 1024  # 差异配置中的值
        assert merged["display"]["height"] == 600  # 默认配置中的值
        
        assert merged["audio"]["enabled"] is True  # 默认配置中的值
        assert merged["audio"]["volume"] == 0.8  # 默认配置中的值
    
    def test_diff_save_load(self, mock_config_manager, setup_diff_files):
        """测试差异化保存和加载"""
        cm = mock_config_manager
        files = setup_diff_files
        
        # 设置配置路径
        cm.config_path = files["config_path"]
        cm.default_config_path = files["default_config_path"]
        
        # 启用差异化保存
        cm.set_save_diff_only(True)
        
        # 加载默认配置
        with patch.object(cm, '_load_environment_configs'):
            # 加载配置
            cm.load_default_config()
            cm.load_config()
        
        # 验证配置完整性
        assert cm.config["app"]["name"] == "User App"  # 用户配置中的值
        assert cm.config["app"]["version"] == "0.1.0"  # 默认配置中的值
        assert cm.config["app"]["debug"] is True  # 用户配置中的值
        
        assert cm.config["display"]["width"] == 1024  # 用户配置中的值
        assert cm.config["display"]["height"] == 600  # 默认配置中的值
        
        assert cm.config["audio"]["enabled"] is True  # 默认配置中的值
        assert cm.config["audio"]["volume"] == 0.8  # 默认配置中的值
        
        # 修改配置
        cm.set("audio.volume", 0.5)
        
        # 保存配置
        with patch('builtins.open', create=True):
            with patch('json.dump') as mock_dump:
                cm.save_config()
                
                # 检查保存的是差异配置而非完整配置
                saved_config = mock_dump.call_args[0][0]
                
                # 差异配置中应只包含修改过的值
                assert "app" in saved_config
                assert saved_config["app"]["name"] == "User App"
                assert saved_config["app"]["debug"] is True
                
                assert "display" in saved_config
                assert saved_config["display"]["width"] == 1024
                
                assert "audio" in saved_config
                assert saved_config["audio"]["volume"] == 0.5
                
                # 未修改的默认值不应在差异配置中
                assert "version" not in saved_config["app"]
                assert "height" not in saved_config["display"]
                assert "enabled" not in saved_config["audio"]
    
    def test_empty_diff(self):
        """测试空差异情况"""
        # 默认配置
        default_config = {
            "app": {
                "name": "Default App",
                "version": "0.1.0"
            }
        }
        
        # 用户配置与默认配置完全相同
        user_config = {
            "app": {
                "name": "Default App",
                "version": "0.1.0"
            }
        }
        
        # 获取差异
        diff = ConfigDiff.get_diff(user_config, default_config)
        
        # 差异应为None，表示没有不同的部分
        assert diff is None
    
    def test_nested_diff(self):
        """测试嵌套差异"""
        # 默认配置
        default_config = {
            "app": {
                "name": "Default App",
                "settings": {
                    "theme": "light",
                    "notifications": {
                        "enabled": True,
                        "sound": True
                    }
                }
            }
        }
        
        # 用户配置
        user_config = {
            "app": {
                "name": "Default App",  # 与默认值相同
                "settings": {
                    "theme": "dark",  # 与默认值不同
                    "notifications": {
                        "enabled": True,  # 与默认值相同
                        "sound": False  # 与默认值不同
                    }
                }
            }
        }
        
        # 获取差异
        diff = ConfigDiff.get_diff(user_config, default_config)
        
        # 验证嵌套差异
        assert "app" in diff
        assert "name" not in diff["app"]  # 相同值不应包含在差异中
        assert "settings" in diff["app"]
        assert "theme" in diff["app"]["settings"]
        assert diff["app"]["settings"]["theme"] == "dark"
        assert "notifications" in diff["app"]["settings"]
        assert "enabled" not in diff["app"]["settings"]["notifications"]  # 相同值不应包含在差异中
        assert "sound" in diff["app"]["settings"]["notifications"]
        assert diff["app"]["settings"]["notifications"]["sound"] is False
    
    def test_additional_keys(self):
        """测试额外键"""
        # 默认配置
        default_config = {
            "app": {
                "name": "Default App"
            }
        }
        
        # 用户配置包含默认配置中不存在的键
        user_config = {
            "app": {
                "name": "Default App"
            },
            "custom": {
                "setting": "value"
            }
        }
        
        # 获取差异
        diff = ConfigDiff.get_diff(user_config, default_config)
        
        # 验证差异中包含额外键
        assert "custom" in diff
        assert diff["custom"]["setting"] == "value"
    
    def test_empty_user_config(self, mock_config_manager, setup_diff_files):
        """测试空用户配置的处理"""
        cm = mock_config_manager
        files = setup_diff_files
        
        # 设置配置路径
        cm.config_path = files["config_path"]
        cm.default_config_path = files["default_config_path"]
        
        # 创建空的用户配置文件
        with open(files["config_path"], 'w') as f:
            json.dump({}, f)
        
        # 加载默认配置
        with patch.object(cm, '_load_environment_configs'):
            # 加载配置
            cm.load_default_config()
            cm.load_config()
        
        # 验证配置是否回退到默认值
        assert cm.config["app"]["name"] == "Default App"
        assert cm.config["app"]["version"] == "0.1.0"
        assert cm.config["app"]["debug"] is False
        assert cm.config["display"]["width"] == 800
        assert cm.config["display"]["height"] == 600
        assert cm.config["audio"]["enabled"] is True
        assert cm.config["audio"]["volume"] == 0.8 