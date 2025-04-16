"""
---------------------------------------------------------------
File name:                  test_resource_system.py
Author:                     Ignorant-lu
Date created:               2025/04/03
Description:                资源管理系统测试模块
----------------------------------------------------------------
Changed history:            
                            2025/04/03: 初始创建;
                            2025/04/04: 移动到正确的测试目录;
                            2025/04/15: 规范为pytest风格，移除unittest入口;
----
"""

import os
import tempfile
import shutil
import zipfile
import json
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

# 导入待测试模块（按实际结构调整）
from status.resources.resource_pack import (
    ResourcePack, ResourcePackManager, resource_pack_manager,
    ResourcePackError, ResourcePackLoadError, ResourcePackValidationError,
    ResourcePackType, ResourcePackFormat, ResourcePackMetadata
)
from status.resources.resource_loader import ResourceLoader, resource_loader

@pytest.fixture
def temp_dir():
    """创建临时目录（自动清理）"""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)

@pytest.fixture
def temp_pack_dir(temp_dir):
    """创建临时资源包目录（自动清理）"""
    pack_dir = os.path.join(temp_dir, "test_pack")
    os.makedirs(pack_dir)
    metadata = {
        "id": "test_pack",
        "name": "Test Pack",
        "description": "A test resource pack",
        "version": "1.0.0",
        "format": 1,
        "author": "Test Author"
    }
    with open(os.path.join(pack_dir, "pack.json"), "w", encoding="utf-8") as f:
        json.dump(metadata, f)
    os.makedirs(os.path.join(pack_dir, "textures"))
    os.makedirs(os.path.join(pack_dir, "sounds"))
    with open(os.path.join(pack_dir, "textures", "test.txt"), "w", encoding="utf-8") as f:
        f.write("Hello, world!")
    return pack_dir

@pytest.fixture
def temp_zip_pack(temp_dir):
    """创建临时ZIP资源包（自动清理）"""
    zip_path = os.path.join(temp_dir, "test_pack.zip")
    with zipfile.ZipFile(zip_path, "w") as zip_file:
        # 添加元数据
        zip_file.writestr("pack.json", json.dumps({
            "id": "test_pack",
            "name": "Test Pack",
            "description": "A test resource pack",
            "version": "1.0.0",
            "format": 1,
            "author": "Test Author"
        }))
        # 添加测试文件
        zip_file.writestr("textures/test.txt", "Hello from ZIP!")
    return zip_path

@pytest.fixture
def resource_pack(temp_pack_dir):
    """创建资源包对象"""
    return ResourcePack(temp_pack_dir, ResourcePackType.DIRECTORY)

@pytest.fixture
def zip_resource_pack(temp_zip_pack):
    """创建ZIP资源包对象"""
    return ResourcePack(temp_zip_pack, ResourcePackType.ZIP)

@pytest.fixture(scope="function")
def resource_loader():
    """创建资源加载器对象（每个用例独立实例）"""
    from status.resources.resource_loader import ResourceLoader
    return ResourceLoader()

def test_resource_pack_load(resource_pack):
    """测试资源包加载"""
    result = resource_pack.load()
    assert result
    assert resource_pack.metadata.id == "test_pack"
    assert resource_pack.metadata.name == "Test Pack"
    assert resource_pack.metadata.version == "1.0.0"
    assert resource_pack.metadata.format == ResourcePackFormat.V1

def test_resource_pack_file_access(resource_pack):
    """测试资源包文件访问"""
    resource_pack.load()
    assert resource_pack.has_file("textures/test.txt")
    assert not resource_pack.has_file("non_existent.txt")
    file_path = resource_pack.get_file_path("textures/test.txt")
    assert file_path is not None
    assert os.path.exists(file_path)
    content = resource_pack.get_file_content("textures/test.txt")
    assert content.decode("utf-8") == "Hello, world!"

def test_zip_resource_pack(zip_resource_pack):
    """测试ZIP格式资源包"""
    result = zip_resource_pack.load()
    assert result
    assert zip_resource_pack.metadata.id == "test_pack"
    assert zip_resource_pack.has_file("textures/test.txt")
    content = zip_resource_pack.get_file_content("textures/test.txt")
    assert content.decode("utf-8") == "Hello from ZIP!"

def test_invalid_resource_pack(temp_dir):
    """测试无效的资源包"""
    invalid_dir = os.path.join(temp_dir, "invalid_pack")
    os.makedirs(invalid_dir)
    pack = ResourcePack(invalid_dir, ResourcePackType.DIRECTORY)
    with pytest.raises(ResourcePackLoadError):
        pack.load()

def test_metadata_validation():
    """测试元数据验证"""
    invalid_metadata = {
        "name": "Invalid Pack",
        "description": "Missing required fields"
    }
    metadata_obj = ResourcePackMetadata(invalid_metadata)
    with pytest.raises(ResourcePackValidationError):
        metadata_obj.validate()

    valid_metadata = {
        "id": "valid_pack",
        "name": "Valid Pack",
        "version": "1.0.0",
        "format": 1
    }
    metadata_obj = ResourcePackMetadata(valid_metadata)
    assert metadata_obj.validate()

@pytest.fixture
def resource_pack_manager(temp_dir):
    """创建资源包管理器对象"""
    manager = ResourcePackManager.get_instance()
    manager.builtin_dir = os.path.join(temp_dir, "builtin")
    manager.user_dir = os.path.join(temp_dir, "user")
    return manager

def test_manager_initialization(resource_pack_manager, temp_dir):
    """测试管理器初始化"""
    builtin_dir = os.path.join(temp_dir, "builtin")
    os.makedirs(builtin_dir)
    builtin_packs_dir = os.path.join(builtin_dir, "packs")
    os.makedirs(builtin_packs_dir)
    builtin_pack_dir = os.path.join(builtin_packs_dir, "default")
    os.makedirs(builtin_pack_dir)
    with open(os.path.join(builtin_pack_dir, "pack.json"), "w", encoding="utf-8") as f:
        json.dump({
            "id": "default",
            "name": "Default Pack",
            "description": "Default built-in resource pack",
            "version": "1.0.0",
            "format": 1,
            "author": "System"
        }, f)
    user_dir = os.path.join(temp_dir, "user")
    os.makedirs(user_dir)
    user_pack_dir = os.path.join(user_dir, "user_pack")
    os.makedirs(user_pack_dir)
    with open(os.path.join(user_pack_dir, "pack.json"), "w", encoding="utf-8") as f:
        json.dump({
            "id": "user_pack",
            "name": "User Pack",
            "description": "Custom user resource pack",
            "version": "1.0.0",
            "format": 1,
            "author": "User"
        }, f)
    result = resource_pack_manager.initialize()
    assert result
    assert "user_pack" in resource_pack_manager.resource_packs

def test_resource_access(resource_loader):
    """测试资源访问（mock manager注入）"""
    from unittest.mock import MagicMock
    mock_manager = MagicMock()
    mock_manager.has_resource.return_value = True
    mock_manager.get_resource_content.return_value = b"Test resource content"
    resource_loader.set_manager(mock_manager)
    assert resource_loader.has_resource("textures/test.txt")
    content = resource_loader.get_resource_content("textures/test.txt")
    assert content == b"Test resource content"

def test_resource_pack_management(resource_pack_manager, temp_dir):
    """测试资源包管理功能"""
    new_pack_dir = os.path.join(temp_dir, "new_pack")
    os.makedirs(new_pack_dir)
    with open(os.path.join(new_pack_dir, "pack.json"), "w", encoding="utf-8") as f:
        json.dump({
            "id": "new_pack",
            "name": "New Pack",
            "description": "New resource pack",
            "version": "1.0.0",
            "format": 1,
            "author": "Test"
        }, f)
    pack_id = resource_pack_manager.add_resource_pack(new_pack_dir)
    assert pack_id == "new_pack"
    assert "new_pack" in resource_pack_manager.resource_packs
    packs = resource_pack_manager.get_resource_packs()
    assert "new_pack" in packs
    assert packs["new_pack"]["name"] == "New Pack"
    result = resource_pack_manager.remove_resource_pack("new_pack")
    assert result
    assert "new_pack" not in resource_pack_manager.resource_packs

def test_resource_loader_initialization(resource_loader):
    """测试资源加载器初始化"""
    from unittest.mock import MagicMock
    mock_manager = MagicMock()
    mock_manager.initialize.return_value = True
    resource_loader.set_manager(mock_manager)
    result = resource_loader.initialize()
    assert result
    mock_manager.initialize.assert_called_once()

def test_image_loading(resource_loader):
    """测试图像加载（mock manager+mock pygame.image.load）"""
    from unittest.mock import MagicMock, patch
    mock_manager = MagicMock()
    mock_manager.has_resource.return_value = True
    mock_manager.get_resource_content.return_value = b"fake image data"
    resource_loader.set_manager(mock_manager)
    mock_surface = MagicMock(name="FakeSurface")
    with patch("pygame.image.load", return_value=mock_surface):
        result = resource_loader.load_image("textures/test.png")
        assert result is mock_surface.convert_alpha.return_value
        assert "textures/test.png" in resource_loader._image_cache

def test_json_loading(resource_loader):
    """测试JSON加载"""
    from unittest.mock import MagicMock
    mock_manager = MagicMock()
    json_data = {"key": "value"}
    mock_manager.get_resource_content.return_value = json.dumps(json_data).encode("utf-8")
    resource_loader.set_manager(mock_manager)
    data = resource_loader.load_json("data/test.json")
    assert data == json_data
    mock_manager.get_resource_content.assert_called_with("data/test.json")
    assert "data/test.json" in resource_loader._json_cache

def test_text_loading(resource_loader):
    """测试文本加载"""
    from unittest.mock import MagicMock
    mock_manager = MagicMock()
    text_content = "Hello, world!"
    mock_manager.get_resource_content.return_value = text_content.encode("utf-8")
    resource_loader.set_manager(mock_manager)
    text = resource_loader.load_text("texts/test.txt")
    assert text == text_content
    mock_manager.get_resource_content.assert_called_with("texts/test.txt")
    assert "texts/test.txt" in resource_loader._text_cache

def test_cache_management(resource_loader):
    """测试缓存管理"""
    from unittest.mock import MagicMock
    mock_manager = MagicMock()
    mock_manager.get_resource_content.return_value = b"test data"
    resource_loader.set_manager(mock_manager)
    resource_loader.load_text("test.txt")
    assert "test.txt" in resource_loader._text_cache
    resource_loader.clear_cache()
    assert "test.txt" not in resource_loader._text_cache
    assert len(resource_loader._image_cache) == 0
    assert len(resource_loader._sound_cache) == 0
    assert len(resource_loader._font_cache) == 0
    assert len(resource_loader._json_cache) == 0
    assert len(resource_loader._text_cache) == 0

def test_reload(resource_loader):
    """测试重新加载（mock manager注入）"""
    from unittest.mock import MagicMock
    mock_manager = MagicMock()
    mock_manager.reload.return_value = True
    resource_loader.set_manager(mock_manager)
    resource_loader._text_cache["test.txt"] = "cached text"
    result = resource_loader.reload()
    assert result
    mock_manager.reload.assert_called_once()
    assert len(resource_loader._text_cache) == 0