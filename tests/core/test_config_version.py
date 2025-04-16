"""
---------------------------------------------------------------
File name:                  test_config_version.py
Author:                     Ignorant-lu
Date created:               2025/04/04
Description:                配置版本控制与升级机制测试
----------------------------------------------------------------

Changed history:            
                            2025/04/04: 初始创建;
----
"""

import os
import json
import shutil
import tempfile
import pytest
from unittest.mock import patch, MagicMock, call
from contextlib import contextmanager

from status.config import ConfigurationManager, ConfigChangeType, ConfigValidationError
import sys

# 添加测试目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestConfigVersion:
    """配置版本控制测试"""

    @pytest.fixture
    def setup_version_files(self):
        """准备版本测试配置文件"""
        # 创建临时目录
        temp_dir = tempfile.mkdtemp()
        
        # 创建配置文件
        old_config = {
            "version": "1.0.0",
            "app": {
                "name": "Test App",
                "display": {
                    "width": 800,
                    "height": 600
                }
            },
            "logging": {
                "level": "info"
            }
        }
        
        # 新默认配置（更高版本）
        new_default_config = {
            "version": "1.1.0",
            "app": {
                "name": "Test App",
                "display": {
                    "width": 800,
                    "height": 600,
                    "scaling": 1.0   # 新增字段
                }
            },
            "logging": {
                "level": "info",
                "format": "standard"  # 新增字段
            }
        }
        
        # 写入配置文件
        config_path = os.path.join(temp_dir, "config.json")
        default_config_path = os.path.join(temp_dir, "default_config.json")
        
        with open(config_path, 'w') as f:
            json.dump(old_config, f, indent=4)
            
        with open(default_config_path, 'w') as f:
            json.dump(new_default_config, f, indent=4)
            
        yield temp_dir, config_path, default_config_path
        
        # 清理
        shutil.rmtree(temp_dir)
        
    @pytest.fixture
    def mock_config_manager(self):
        """创建配置管理器实例"""
        # 重置单例实例
        ConfigurationManager._instance = None
        
        # 创建实例
        config_manager = ConfigurationManager()
        
        # 禁用日志避免测试输出过多
        config_manager.logger.disabled = True
        
        yield config_manager
        
        # 重置单例实例
        ConfigurationManager._instance = None
        
    def test_detect_version_mismatch(self, setup_version_files, mock_config_manager):
        """测试检测版本不匹配"""
        temp_dir, config_path, default_config_path = setup_version_files
        
        # 设置配置路径
        mock_config_manager.config_path = config_path
        mock_config_manager.default_config_path = default_config_path
        
        # 加载默认配置
        with open(default_config_path, 'r') as f:
            default_config = json.load(f)
        mock_config_manager.default_config = default_config
        
        # 测试版本检查方法
        with patch.object(mock_config_manager, '_upgrade_config') as mock_upgrade:
            mock_config_manager.load_config()
            
            # 检查是否调用了升级方法
            mock_upgrade.assert_called_once()
            
            # 获取传递给升级方法的参数
            args, _ = mock_upgrade.call_args
            user_config = args[0]
            
            # 验证版本正确
            assert user_config["version"] == "1.0.0"
            
    def test_version_upgrade_callback(self, setup_version_files, mock_config_manager):
        """测试版本升级回调"""
        temp_dir, config_path, default_config_path = setup_version_files
        
        # 设置配置路径
        mock_config_manager.config_path = config_path
        mock_config_manager.default_config_path = default_config_path
        
        # 加载默认配置
        with open(default_config_path, 'r') as f:
            default_config = json.load(f)
        mock_config_manager.default_config = default_config
        
        # 用于测试的升级函数
        def upgrade_to_1_1_0(old_config, old_version, new_version):
            """从1.0.0升级到1.1.0的测试升级函数"""
            assert old_version == "1.0.0"
            assert new_version == "1.1.0"
            
            # 升级配置
            new_config = old_config.copy()
            
            # 添加新字段
            if "app" in new_config and "display" in new_config["app"]:
                new_config["app"]["display"]["scaling"] = 1.0
                
            if "logging" in new_config:
                new_config["logging"]["format"] = "standard"
                
            # 更新版本
            new_config["version"] = new_version
            
            return new_config
            
        # 注册升级处理器
        mock_config_manager.register_version_upgrade("1.0.0", "1.1.0", upgrade_to_1_1_0)
        
        # 执行配置加载和升级
        mock_config_manager.load_config()
        
        # 验证配置已更新
        config = mock_config_manager.config
        assert config["version"] == "1.1.0"
        assert config["app"]["display"]["scaling"] == 1.0
        assert config["logging"]["format"] == "standard"
        
    def test_sequential_version_upgrade(self, setup_version_files, mock_config_manager):
        """测试连续版本升级"""
        temp_dir, config_path, default_config_path = setup_version_files
        
        # 修改默认配置为更高版本
        with open(default_config_path, 'r') as f:
            default_config = json.load(f)
        
        default_config["version"] = "1.2.0"  # 从1.0.0需要升级到1.2.0
        default_config["app"]["theme"] = "dark"  # 新增字段
        
        with open(default_config_path, 'w') as f:
            json.dump(default_config, f, indent=4)
            
        # 设置配置路径
        mock_config_manager.config_path = config_path
        mock_config_manager.default_config_path = default_config_path
        mock_config_manager.default_config = default_config
        
        # 第一步升级函数 1.0.0 -> 1.1.0
        def upgrade_to_1_1_0(old_config, old_version, new_version):
            new_config = old_config.copy()
            if "app" in new_config and "display" in new_config["app"]:
                new_config["app"]["display"]["scaling"] = 1.0
            if "logging" in new_config:
                new_config["logging"]["format"] = "standard"
            new_config["version"] = new_version
            return new_config
            
        # 第二步升级函数 1.1.0 -> 1.2.0
        def upgrade_to_1_2_0(old_config, old_version, new_version):
            new_config = old_config.copy()
            if "app" in new_config:
                new_config["app"]["theme"] = "dark"
            new_config["version"] = new_version
            return new_config
            
        # 注册两个升级处理器
        mock_config_manager.register_version_upgrade("1.0.0", "1.1.0", upgrade_to_1_1_0)
        mock_config_manager.register_version_upgrade("1.1.0", "1.2.0", upgrade_to_1_2_0)
        
        # 执行配置加载和升级
        mock_config_manager.load_config()
        
        # 验证配置已连续升级到1.2.0
        config = mock_config_manager.config
        assert config["version"] == "1.2.0"
        assert config["app"]["display"]["scaling"] == 1.0
        assert config["logging"]["format"] == "standard"
        assert config["app"]["theme"] == "dark"
        
    def test_no_upgrade_needed(self, setup_version_files, mock_config_manager):
        """测试无需升级的情况"""
        temp_dir, config_path, default_config_path = setup_version_files
        
        # 修改用户配置使版本匹配默认配置
        with open(config_path, 'r') as f:
            user_config = json.load(f)
        
        with open(default_config_path, 'r') as f:
            default_config = json.load(f)
        
        # 设置相同版本
        user_config["version"] = default_config["version"]
        
        with open(config_path, 'w') as f:
            json.dump(user_config, f, indent=4)
            
        # 设置配置路径
        mock_config_manager.config_path = config_path
        mock_config_manager.default_config_path = default_config_path
        mock_config_manager.default_config = default_config
        
        # 创建升级方法的Mock
        with patch.object(mock_config_manager, '_upgrade_config') as mock_upgrade:
            # 加载配置
            mock_config_manager.load_config()
            
            # 验证没有调用升级方法
            mock_upgrade.assert_not_called()
            
    def test_missing_version_field(self, setup_version_files, mock_config_manager):
        """测试配置缺少版本字段的情况"""
        temp_dir, config_path, default_config_path = setup_version_files
        
        # 修改用户配置移除版本字段
        with open(config_path, 'r') as f:
            user_config = json.load(f)
        
        # 删除版本字段
        del user_config["version"]
        
        with open(config_path, 'w') as f:
            json.dump(user_config, f, indent=4)
            
        # 设置配置路径
        mock_config_manager.config_path = config_path
        mock_config_manager.default_config_path = default_config_path
        
        # 加载默认配置
        with open(default_config_path, 'r') as f:
            default_config = json.load(f)
        mock_config_manager.default_config = default_config
        
        # 加载配置（应该自动添加版本）
        mock_config_manager.load_config()
        
        # 检查加载后的配置是否包含版本
        loaded_config = mock_config_manager.config
        assert "version" in loaded_config
        assert loaded_config["version"] == default_config["version"]
        
    def test_invalid_version_format(self, setup_version_files, mock_config_manager):
        """测试无效版本格式"""
        temp_dir, config_path, default_config_path = setup_version_files
        
        # 修改用户配置为无效版本格式
        with open(config_path, 'r') as f:
            user_config = json.load(f)
            
        user_config["version"] = "invalid.version"
        
        with open(config_path, 'w') as f:
            json.dump(user_config, f, indent=4)
            
        # 设置配置路径
        mock_config_manager.config_path = config_path
        mock_config_manager.default_config_path = default_config_path
        
        # 加载默认配置
        with open(default_config_path, 'r') as f:
            default_config = json.load(f)
        mock_config_manager.default_config = default_config
        
        # 应该捕获版本比较异常并回退到默认配置
        mock_config_manager.load_config()
        
        # 检查是否回退到默认配置
        config = mock_config_manager.config
        assert config["version"] == default_config["version"]
        
    def test_prevent_downgrade(self, setup_version_files, mock_config_manager):
        """测试防止配置降级"""
        temp_dir, config_path, default_config_path = setup_version_files
        
        # 修改用户配置为更高版本
        with open(config_path, 'r') as f:
            user_config = json.load(f)
            
        user_config["version"] = "2.0.0"  # 高于默认配置的1.1.0
        
        with open(config_path, 'w') as f:
            json.dump(user_config, f, indent=4)
            
        # 设置配置路径
        mock_config_manager.config_path = config_path
        mock_config_manager.default_config_path = default_config_path
        
        # 加载默认配置
        with open(default_config_path, 'r') as f:
            default_config = json.load(f)
        mock_config_manager.default_config = default_config
        
        # 加载配置
        mock_config_manager.load_config()
        
        # 检查警告日志（由于测试中禁用了日志，只能检查配置未被降级）
        config = mock_config_manager.config
        assert config["version"] == "2.0.0"  # 确保版本未被降级
        
    def test_custom_upgrade_handler(self, setup_version_files, mock_config_manager):
        """测试自定义升级处理器"""
        temp_dir, config_path, default_config_path = setup_version_files
        
        # 设置配置路径
        mock_config_manager.config_path = config_path
        mock_config_manager.default_config_path = default_config_path
        
        # 加载默认配置
        with open(default_config_path, 'r') as f:
            default_config = json.load(f)
        mock_config_manager.default_config = default_config
        
        # 自定义升级处理器
        mock_handler = MagicMock(return_value={
            "version": "1.1.0",
            "app": {
                "name": "Custom App",  # 定制化值
                "display": {
                    "width": 1024,     # 定制化值
                    "height": 768,     # 定制化值
                    "scaling": 1.0
                }
            },
            "logging": {
                "level": "debug",     # 定制化值
                "format": "standard"
            }
        })
        
        # 注册处理器
        mock_config_manager.register_version_upgrade("1.0.0", "1.1.0", mock_handler)
        
        # 加载配置
        mock_config_manager.load_config()
        
        # 验证升级处理器被调用
        mock_handler.assert_called_once()
        args, _ = mock_handler.call_args
        assert args[1] == "1.0.0"  # 旧版本
        assert args[2] == "1.1.0"  # 新版本
        
        # 验证配置被自定义处理器修改
        config = mock_config_manager.config
        assert config["version"] == "1.1.0"
        assert config["app"]["name"] == "Custom App"
        assert config["app"]["display"]["width"] == 1024
        assert config["logging"]["level"] == "debug" 