"""
---------------------------------------------------------------
File name:                  resource_pack.py
Author:                     Ignorant-lu
Date created:               2025/04/15
Description:                资源包相关核心模块（最小实现，供测试用）
----------------------------------------------------------------
Changed history:            
                            2025/04/15: 初始创建，最小实现以通过pytest测试;
----
"""

import os
import zipfile
import json
from enum import Enum

class ResourcePackError(Exception):
    pass
class ResourcePackLoadError(ResourcePackError):
    pass
class ResourcePackValidationError(ResourcePackError):
    pass

class ResourcePackType(Enum):
    DIRECTORY = 1
    ZIP = 2

class ResourcePackFormat(Enum):
    V1 = 1

class ResourcePackMetadata:
    def __init__(self, meta):
        self.id = meta.get("id")
        self.name = meta.get("name")
        self.version = meta.get("version")
        self.format = ResourcePackFormat(meta.get("format", 1)) if meta.get("format") else None
    def validate(self):
        if not self.id or not self.name or not self.version or not self.format:
            raise ResourcePackValidationError()
        return True

class ResourcePack:
    def __init__(self, path, pack_type):
        self.path = path
        self.pack_type = pack_type
        self.metadata = None
        self._files = None
        self.name = None
    def load(self):
        # 加载并校验元数据
        if self.pack_type == ResourcePackType.DIRECTORY:
            meta_path = os.path.join(self.path, "pack.json")
            if not os.path.exists(meta_path):
                raise ResourcePackLoadError()
            with open(meta_path, "r", encoding="utf-8") as f:
                meta = json.load(f)
            self.metadata = ResourcePackMetadata(meta)
            self.metadata.validate()
            self.name = self.metadata.name
            # 收集所有文件
            self._files = {}
            for root, _, files in os.walk(self.path):
                for file in files:
                    relpath = os.path.relpath(os.path.join(root, file), self.path)
                    with open(os.path.join(root, file), "rb") as fobj:
                        self._files[relpath.replace("\\", "/")] = fobj.read()
        elif self.pack_type == ResourcePackType.ZIP:
            if not zipfile.is_zipfile(self.path):
                raise ResourcePackLoadError()
            self._files = {}
            with zipfile.ZipFile(self.path, "r") as z:
                if "pack.json" not in z.namelist():
                    raise ResourcePackLoadError()
                meta = json.loads(z.read("pack.json").decode("utf-8"))
                self.metadata = ResourcePackMetadata(meta)
                self.metadata.validate()
                self.name = self.metadata.name
                for name in z.namelist():
                    self._files[name] = z.read(name)
        else:
            raise ResourcePackLoadError()
        return True
    def has_file(self, name):
        return self._files and name in self._files
    def get_file_path(self, name):
        if self.pack_type == ResourcePackType.DIRECTORY and self.has_file(name):
            return os.path.join(self.path, name)
        return None
    def get_file_content(self, name):
        if not self.has_file(name):
            raise ResourcePackLoadError()
        return self._files[name]

class ResourcePackManager:
    _instance = None
    def __init__(self):
        self.resource_packs = {}
        self.builtin_dir = None
        self.user_dir = None
    @classmethod
    def get_instance(cls):
        if not cls._instance:
            cls._instance = ResourcePackManager()
        return cls._instance
    def initialize(self):
        # 自动扫描builtin_dir和user_dir下的资源包
        self.resource_packs = {}
        for base_dir in [self.builtin_dir, self.user_dir]:
            if base_dir and os.path.exists(base_dir):
                for root, dirs, files in os.walk(base_dir):
                    if "pack.json" in files:
                        try:
                            pack = ResourcePack(root, ResourcePackType.DIRECTORY)
                            pack.load()
                            self.resource_packs[pack.metadata.id] = pack
                        except Exception:
                            continue
        return True
    def add_resource_pack(self, path):
        pack = ResourcePack(path, ResourcePackType.DIRECTORY)
        pack.load()
        pack_id = pack.metadata.id
        self.resource_packs[pack_id] = pack
        return pack_id
    def get_resource_packs(self):
        # 返回dict，value为dict，包含name字段，兼容测试断言
        return {pid: {"name": pack.name} for pid, pack in self.resource_packs.items()}
    def remove_resource_pack(self, pack_id):
        if pack_id in self.resource_packs:
            self.resource_packs.pop(pack_id)
            return True
        return False
    def has_resource(self, name):
        for pack in self.resource_packs.values():
            if hasattr(pack, 'has_file') and pack.has_file(name):
                return True
        return False
    def get_resource_content(self, name):
        for pack in self.resource_packs.values():
            if hasattr(pack, 'has_file') and pack.has_file(name):
                return pack.get_file_content(name)
        raise ResourcePackLoadError()

resource_pack_manager = ResourcePackManager.get_instance()
