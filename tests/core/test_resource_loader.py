"""
---------------------------------------------------------------
File name:                  test_resource_loader.py
Author:                     Ignorant-lu
Date created:               2025/04/04
Description:                资源加载器测试
----------------------------------------------------------------

Changed history:            
                            2025/04/04: 初始创建;
----
"""

import os
import pytest
from unittest.mock import patch, mock_open

from status.core.resource_loader import ResourceLoader, ResourceType, ResourceLoadError

class TestResourceLoader:
    """资源加载器测试用例"""

    def test_init(self):
        """测试初始化"""
        loader = ResourceLoader()
        assert loader.base_path == ""
        
        loader = ResourceLoader("/test/path")
        assert loader.base_path == "/test/path"
        
        # 验证支持的扩展名已正确初始化
        assert ResourceType.IMAGE in loader.supported_extensions
        assert ResourceType.TEXT in loader.supported_extensions
        assert '.png' in loader.supported_extensions[ResourceType.IMAGE]
        assert '.txt' in loader.supported_extensions[ResourceType.TEXT]

    def test_set_base_path(self):
        """测试设置基础路径"""
        loader = ResourceLoader()
        loader.set_base_path("/new/path")
        assert loader.base_path == "/new/path"

    def test_get_resource_type(self):
        """测试根据文件扩展名确定资源类型"""
        loader = ResourceLoader()
        
        # 测试图像类型
        assert loader.get_resource_type("test.png") == ResourceType.IMAGE
        assert loader.get_resource_type("test.jpg") == ResourceType.IMAGE
        assert loader.get_resource_type("test.jpeg") == ResourceType.IMAGE
        
        # 测试音效类型
        assert loader.get_resource_type("test.wav") == ResourceType.SOUND
        assert loader.get_resource_type("test.ogg") == ResourceType.SOUND
        
        # 测试数据类型
        assert loader.get_resource_type("test.json") == ResourceType.DATA
        assert loader.get_resource_type("test.yaml") == ResourceType.DATA
        
        # 测试未知类型
        assert loader.get_resource_type("test.unknown") == ResourceType.OTHER

    @patch('os.path.exists')
    def test_load_file_not_exists(self, mock_exists):
        """测试加载不存在的文件"""
        mock_exists.return_value = False
        
        loader = ResourceLoader()
        
        with pytest.raises(ResourceLoadError) as excinfo:
            loader.load("non_existent.png")
        
        assert "资源文件不存在" in str(excinfo.value)

    @patch('os.path.exists')
    @patch('status.core.resource_loader.ResourceLoader._load_image')
    def test_load_image(self, mock_load_image, mock_exists):
        """测试加载图像资源"""
        mock_exists.return_value = True
        mock_load_image.return_value = {"path": "test.png", "type": "image", "loaded": True}
        
        loader = ResourceLoader()
        result = loader.load("test.png")
        
        assert result["path"] == "test.png"
        assert result["type"] == "image"
        assert result["loaded"] is True
        mock_load_image.assert_called_once()

    @patch('os.path.exists')
    @patch('status.core.resource_loader.ResourceLoader._load_sound')
    def test_load_sound(self, mock_load_sound, mock_exists):
        """测试加载音效资源"""
        mock_exists.return_value = True
        mock_load_sound.return_value = {"path": "test.wav", "type": "sound", "loaded": True}
        
        loader = ResourceLoader()
        result = loader.load("test.wav")
        
        assert result["path"] == "test.wav"
        assert result["type"] == "sound"
        assert result["loaded"] is True
        mock_load_sound.assert_called_once()

    @patch('os.path.exists')
    @patch('status.core.resource_loader.ResourceLoader._load_data')
    def test_load_data(self, mock_load_data, mock_exists):
        """测试加载数据资源"""
        mock_exists.return_value = True
        mock_load_data.return_value = {"test_key": "test_value"}
        
        loader = ResourceLoader()
        result = loader.load("test.json")
        
        assert "test_key" in result
        assert result["test_key"] == "test_value"
        mock_load_data.assert_called_once()

    @patch('os.path.exists')
    @patch('status.core.resource_loader.ResourceLoader._load_text')
    def test_load_text(self, mock_load_text, mock_exists):
        """测试加载文本资源"""
        mock_exists.return_value = True
        mock_load_text.return_value = "Test content"
        
        loader = ResourceLoader()
        result = loader.load("test.txt")
        
        assert result == "Test content"
        mock_load_text.assert_called_once()

    @patch('os.path.exists')
    @patch('builtins.open', new_callable=mock_open, read_data='{"test_key": "test_value"}')
    def test_load_data_json(self, mock_file, mock_exists):
        """测试加载JSON数据文件"""
        mock_exists.return_value = True
        
        loader = ResourceLoader()
        result = loader.load("test.json", ResourceType.DATA)
        
        assert "test_key" in result
        assert result["test_key"] == "test_value"

    @patch('os.path.exists')
    @patch('builtins.open', new_callable=mock_open, read_data='test_content')
    def test_load_text_file(self, mock_file, mock_exists):
        """测试加载文本文件"""
        mock_exists.return_value = True
        
        loader = ResourceLoader()
        result = loader.load("test.txt", ResourceType.TEXT)
        
        assert result == "test_content"

    @patch('os.path.exists')
    @patch('status.core.resource_loader.ResourceLoader._load_binary')
    def test_load_binary(self, mock_load_binary, mock_exists):
        """测试加载二进制资源"""
        mock_exists.return_value = True
        mock_load_binary.return_value = b"binary_data"
        
        loader = ResourceLoader()
        result = loader.load("test.bin", ResourceType.OTHER)
        
        assert result == b"binary_data"
        mock_load_binary.assert_called_once()

    @patch('os.path.exists')
    def test_load_exception(self, mock_exists):
        """测试加载异常处理"""
        mock_exists.return_value = True
        
        loader = ResourceLoader()
        # 替换_load_data方法以抛出异常
        loader._loaders[ResourceType.DATA] = lambda path, **kwargs: exec('raise Exception("Test exception")')
        
        with pytest.raises(ResourceLoadError) as excinfo:
            loader.load("test.json", ResourceType.DATA)
        
        assert "加载资源失败" in str(excinfo.value)

    def test_get_supported_extensions(self):
        """测试获取支持的文件扩展名"""
        loader = ResourceLoader()
        extensions = loader.get_supported_extensions()
        
        assert ResourceType.IMAGE in extensions
        assert ResourceType.SOUND in extensions
        assert ResourceType.DATA in extensions
        assert ResourceType.TEXT in extensions
        
        assert '.png' in extensions[ResourceType.IMAGE]
        assert '.wav' in extensions[ResourceType.SOUND]
        assert '.json' in extensions[ResourceType.DATA]
        assert '.txt' in extensions[ResourceType.TEXT]

    @patch('os.path.exists')
    @patch('os.path.isdir')
    @patch('os.walk')
    def test_scan_directory(self, mock_walk, mock_isdir, mock_exists):
        """测试扫描目录"""
        mock_exists.return_value = True
        mock_isdir.return_value = True
        
        # 模拟os.walk返回的数据结构
        # (dirpath, dirnames, filenames)
        mock_walk.return_value = [
            ('/test', ['subdir'], ['image.png', 'sound.wav', 'data.json']),
            ('/test/subdir', [], ['text.txt', 'other.bin'])
        ]
        
        loader = ResourceLoader('/test')
        result = loader.scan_directory('.')
        
        # 验证结果包含文件并按类型分类
        assert 'image.png' in result[ResourceType.IMAGE]
        assert 'sound.wav' in result[ResourceType.SOUND]
        assert 'data.json' in result[ResourceType.DATA]
        # 检查是否包含text.txt文件，需要处理路径分隔符
        assert any('text.txt' in path for path in result[ResourceType.TEXT])
        # 检查是否包含other.bin文件，需要处理路径分隔符
        assert any('other.bin' in path for path in result[ResourceType.OTHER])

    @patch('os.path.exists')
    @patch('os.path.isdir')
    def test_scan_directory_not_exists(self, mock_isdir, mock_exists):
        """测试扫描不存在的目录"""
        mock_exists.return_value = False
        mock_isdir.return_value = False
        
        loader = ResourceLoader()
        
        with pytest.raises(ResourceLoadError) as excinfo:
            loader.scan_directory('non_existent')
        
        assert "目录不存在" in str(excinfo.value) 