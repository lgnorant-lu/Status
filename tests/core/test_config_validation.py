"""
---------------------------------------------------------------
File name:                  test_config_validation.py
Author:                     Ignorant-lu
Date created:               2025/04/04
Description:                配置验证功能测试
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

from status.config import ConfigurationManager, ConfigChangeType, ConfigValidationError, config_manager

class TestConfigValidation:
    """配置验证功能测试用例"""
    
    @pytest.fixture
    def setup_validation_files(self):
        """准备测试配置和模式文件"""
        # 创建临时文件夹
        temp_dir = tempfile.TemporaryDirectory()
        
        # 创建临时配置文件路径
        config_path = os.path.join(temp_dir.name, "config.json")
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
        
        # 测试配置模式
        test_schema = {
            "type": "object",
            "required": ["app"],
            "properties": {
                "app": {
                    "type": "object",
                    "required": ["name", "version"],
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
                }
            }
        }
        
        # 写入测试文件
        with open(config_path, 'w') as f:
            json.dump(test_config, f)
            
        with open(schema_path, 'w') as f:
            json.dump(test_schema, f)
        
        # 返回文件路径和临时目录
        yield {
            "temp_dir": temp_dir,
            "config_path": config_path,
            "schema_path": schema_path,
            "test_config": test_config,
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
        
        # 禁用日志记录以防止测试输出过多
        instance.logger = Mock()
        
        # 返回实例
        yield instance
        
        # 恢复原始单例
        ConfigurationManager._instance = original_instance
    
    def test_load_schema(self, mock_config_manager, setup_validation_files):
        """测试加载JSON Schema模式"""
        cm = mock_config_manager
        files = setup_validation_files
        
        # 设置模式路径
        cm.schema_path = files["schema_path"]
        
        # 模拟加载方法
        with patch.object(cm, 'load_default_config', return_value=True):
            with patch.object(cm, 'load_config', return_value=True):
                cm.initialize(schema_path=files["schema_path"])
                
        # 验证模式加载
        assert cm.schema is not None
        assert "type" in cm.schema
        assert "properties" in cm.schema
        assert "app" in cm.schema["properties"]
    
    def test_validate_config(self, mock_config_manager, setup_validation_files):
        """测试配置验证功能"""
        cm = mock_config_manager
        files = setup_validation_files
        
        # 设置模式和配置
        cm.schema = files["test_schema"]
        cm.config = files["test_config"]
        
        # 验证有效配置
        assert cm.validate_config() is True
        
        # 验证无效配置
        invalid_config = {
            "app": {
                "name": "Test App",
                # 缺少 version 字段
                "debug": True
            }
        }
        
        with pytest.raises(ConfigValidationError):
            cm.validate_config(invalid_config)
    
    def test_validate_on_set(self, mock_config_manager, setup_validation_files):
        """测试设置配置项时的验证"""
        cm = mock_config_manager
        files = setup_validation_files
        
        # 设置模式和配置
        cm.schema = files["test_schema"]
        cm.config = files["test_config"].copy()
        
        # 模拟保存方法
        with patch.object(cm, 'save_config', return_value=True):
            # 有效设置
            assert cm.set("display.width", 1024) is True
            assert cm.config["display"]["width"] == 1024
            
            # 无效设置
            with pytest.raises(ConfigValidationError):
                cm.set("display.width", 100)  # 小于最小值320
    
    def test_validation_with_custom_schema(self, mock_config_manager):
        """测试使用自定义模式验证"""
        cm = mock_config_manager
        
        # 自定义简单模式
        custom_schema = {
            "type": "object",
            "properties": {
                "test": {
                    "type": "number",
                    "minimum": 0,
                    "maximum": 100
                }
            }
        }
        
        # 设置模式
        cm.set_schema(custom_schema)
        
        # 初始化配置
        cm.config = {"test": 50}
        
        # 验证配置
        assert cm.validate_config() is True
        
        # 无效配置
        cm.config = {"test": 200}  # 超过最大值
        with pytest.raises(ConfigValidationError):
            cm.validate_config()
            
        # 类型错误
        cm.config = {"test": "string"}  # 类型错误
        with pytest.raises(ConfigValidationError):
            cm.validate_config()
    
    def test_validation_on_load(self, mock_config_manager, setup_validation_files):
        """测试加载配置时的验证"""
        cm = mock_config_manager
        files = setup_validation_files
        
        # 设置路径
        cm.config_path = files["config_path"]
        cm.schema_path = files["schema_path"]
        
        # 创建无效配置
        invalid_config = {
            "app": {
                "name": 123,  # 应该是字符串
                "version": "0.1.0"
            }
        }
        
        # 写入无效配置
        with open(files["config_path"], 'w') as f:
            json.dump(invalid_config, f)
        
        # 设置模式
        cm.schema = files["test_schema"]
        
        # 加载默认配置
        with patch.object(cm, 'load_default_config', return_value=True):
            # 加载配置，应返回False表示验证失败
            assert cm.load_config() is False
            
        # 验证回退到默认配置
        assert cm.config != invalid_config 