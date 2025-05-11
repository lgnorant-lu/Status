"""
---------------------------------------------------------------
File name:                  resource_pack.py
Author:                     Ignorant-lu
Date created:               2025/04/03
Description:                资源包管理，提供资源包加载和切换功能
----------------------------------------------------------------

Changed history:            
                            2025/04/03: 初始创建;
----
"""

import os
import json
import logging
import zipfile
import shutil
from typing import Dict, Any, List, Optional, Set, Tuple
from enum import Enum, auto
import threading

from status.core.config import config_manager


class ResourcePackFormat(Enum):
    """资源包格式版本"""
    V1 = 1  # 基础格式
    V2 = 2  # 支持嵌套目录和元数据
    V3 = 3  # 支持依赖和条件加载


class ResourcePackType(Enum):
    """资源包类型"""
    DIRECTORY = auto()  # 目录格式
    ZIP = auto()        # 压缩包格式
    BUILTIN = auto()    # 内置资源包


class ResourcePackError(Exception):
    """资源包错误"""
    pass


class ResourcePackLoadError(ResourcePackError):
    """资源包加载错误"""
    pass


class ResourcePackValidationError(ResourcePackError):
    """资源包验证错误"""
    pass


class ResourcePackMetadata:
    """资源包元数据"""
    
    def __init__(self, data: Dict[str, Any]):
        """初始化资源包元数据
        
        Args:
            data: 元数据字典
        """
        # 必需字段
        self.id = data.get("id", "")
        self.name = data.get("name", "")
        self.version = data.get("version", "1.0.0")
        self.description = data.get("description", "")
        self.format = ResourcePackFormat(data.get("format", 1))
        
        # 可选字段
        self.author = data.get("author", "")
        self.website = data.get("website", "")
        self.license = data.get("license", "")
        self.dependencies = data.get("dependencies", [])
        self.tags = data.get("tags", [])
        self.preview_image = data.get("preview_image", "")
        self.created_at = data.get("created_at", "")
        self.updated_at = data.get("updated_at", "")
        
        # 资源覆盖设置
        self.override_settings = data.get("override_settings", {})
        
        # 原始数据
        self.raw_data = data
    
    def validate(self) -> bool:
        """验证元数据
        
        Returns:
            bool: 验证是否通过
            
        Raises:
            ResourcePackValidationError: 验证失败时抛出
        """
        # 验证必填字段
        if not self.id:
            raise ResourcePackValidationError("资源包ID不能为空")
        
        if not self.name:
            raise ResourcePackValidationError("资源包名称不能为空")
        
        # 验证ID格式
        if not self.id.isalnum() and not all(c.isalnum() or c in "._-" for c in self.id):
            raise ResourcePackValidationError(f"资源包ID '{self.id}' 格式无效，只能包含字母、数字、点、下划线和连字符")
        
        # 验证版本格式
        try:
            parts = self.version.split(".")
            if len(parts) < 1 or len(parts) > 3:
                raise ValueError()
            
            for part in parts:
                int(part)
        except ValueError:
            raise ResourcePackValidationError(f"资源包版本 '{self.version}' 格式无效，应为 X.Y.Z 格式")
        
        return True
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典
        
        Returns:
            Dict[str, Any]: 元数据字典
        """
        return {
            "id": self.id,
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "format": self.format.value,
            "author": self.author,
            "website": self.website,
            "license": self.license,
            "dependencies": self.dependencies,
            "tags": self.tags,
            "preview_image": self.preview_image,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "override_settings": self.override_settings
        }


class ResourcePack:
    """资源包类"""
    
    def __init__(self, path: str, pack_type: ResourcePackType):
        """初始化资源包
        
        Args:
            path: 资源包路径
            pack_type: 资源包类型
        """
        self.path = path
        self.type = pack_type
        self.logger = logging.getLogger("Status.ResourcePack")
        
        # 资源包元数据
        self.metadata: Optional[ResourcePackMetadata] = None
        
        # 资源文件列表缓存
        self.files: List[str] = []
        
        # 资源文件映射（替代路径 -> 实际路径）
        self.file_mapping: Dict[str, str] = {}
        
        # 是否已加载
        self.loaded = False
        
        # 加载锁
        self._load_lock = threading.Lock()
    
    def load(self) -> bool:
        """加载资源包
        
        Returns:
            bool: 加载是否成功
            
        Raises:
            ResourcePackLoadError: 加载失败时抛出
        """
        if self.loaded:
            return True
        
        with self._load_lock:
            if self.loaded:
                return True
            
            try:
                self._load_metadata()
                # 确保 metadata 已加载
                if not self.metadata:
                    # _load_metadata 内部应该抛出异常，但作为安全检查
                    raise ResourcePackLoadError("元数据加载失败，无法继续加载资源包")
                self._scan_files()
                self.loaded = True
                self.logger.info(f"资源包 '{self.metadata.name}' (ID: {self.metadata.id}) 加载成功")
                return True
            except Exception as e:
                self.logger.error(f"加载资源包失败: {str(e)}")
                # 重新抛出异常以便上层处理
                if isinstance(e, ResourcePackError):
                    raise
                else:
                    raise ResourcePackLoadError(f"加载资源包失败: {str(e)}")
    
    def _load_metadata(self) -> None:
        """加载资源包元数据
        
        Raises:
            ResourcePackLoadError: 加载失败时抛出
        """
        metadata_path = ""
        metadata_content = None
        
        try:
            if self.type == ResourcePackType.DIRECTORY:
                metadata_path = os.path.join(self.path, "pack.json")
                
                if not os.path.exists(metadata_path):
                    raise ResourcePackLoadError(f"资源包元数据文件不存在: {metadata_path}")
                
                with open(metadata_path, "r", encoding="utf-8") as f:
                    metadata_content = json.load(f)
            
            elif self.type == ResourcePackType.ZIP:
                if not zipfile.is_zipfile(self.path):
                    raise ResourcePackLoadError(f"无效的ZIP资源包: {self.path}")
                
                with zipfile.ZipFile(self.path, "r") as zip_file:
                    if "pack.json" not in zip_file.namelist():
                        raise ResourcePackLoadError(f"ZIP资源包中缺少元数据文件: {self.path}")
                    
                    with zip_file.open("pack.json") as f:
                        metadata_content = json.loads(f.read().decode("utf-8"))
            
            elif self.type == ResourcePackType.BUILTIN:
                # 内置资源包，元数据可能是硬编码的
                if os.path.exists(os.path.join(self.path, "pack.json")):
                    with open(os.path.join(self.path, "pack.json"), "r", encoding="utf-8") as f:
                        metadata_content = json.load(f)
                else:
                    # 为内置资源包生成默认元数据
                    name = os.path.basename(self.path)
                    metadata_content = {
                        "id": f"builtin.{name}",
                        "name": f"内置资源包 ({name})",
                        "version": "1.0.0",
                        "description": "内置默认资源包",
                        "format": 1,
                        "author": "Status Team"
                    }
            
            if metadata_content is None:
                raise ResourcePackLoadError("无法加载资源包元数据")
            
            # 创建元数据对象
            self.metadata = ResourcePackMetadata(metadata_content)
            
            # 验证元数据
            self.metadata.validate()
            
        except json.JSONDecodeError as e:
            raise ResourcePackLoadError(f"资源包元数据格式错误: {str(e)}")
        except Exception as e:
            if isinstance(e, ResourcePackError):
                raise
            else:
                raise ResourcePackLoadError(f"加载资源包元数据时出错: {str(e)}")
    
    def _scan_files(self) -> None:
        """扫描资源包中的文件
        
        Raises:
            ResourcePackLoadError: 扫描失败时抛出
        """
        try:
            if self.type == ResourcePackType.DIRECTORY:
                self._scan_directory(self.path)
            
            elif self.type == ResourcePackType.ZIP:
                self._scan_zip(self.path)
            
            elif self.type == ResourcePackType.BUILTIN:
                self._scan_directory(self.path)
            
            # 确保 metadata 已加载
            if self.metadata: 
                self.logger.debug(f"资源包 '{self.metadata.id}' 包含 {len(self.files)} 个资源文件")
            else:
                self.logger.debug(f"资源包 (路径: {self.path}) 包含 {len(self.files)} 个资源文件，但元数据未加载")
        except Exception as e:
            raise ResourcePackLoadError(f"扫描资源包文件时出错: {str(e)}")
    
    def _scan_directory(self, directory: str) -> None:
        """扫描目录类型资源包
        
        Args:
            directory: 目录路径
            
        Raises:
            ResourcePackLoadError: 扫描失败时抛出
        """
        if not os.path.isdir(directory):
            raise ResourcePackLoadError(f"资源包路径不是目录: {directory}")
        
        # 遍历目录
        for root, _, files in os.walk(directory):
            # 跳过元数据和其他特殊文件
            if os.path.basename(root) in [".git", "__pycache__"]:
                continue
            
            for file in files:
                if file in ["pack.json", ".gitignore", "README.md"]:
                    continue
                
                file_path = os.path.join(root, file)
                relative_path = os.path.relpath(file_path, directory)
                
                # 转换为统一的路径格式（使用正斜杠）
                relative_path = relative_path.replace("\\", "/")
                
                self.files.append(relative_path)
                self.file_mapping[relative_path] = file_path
    
    def _scan_zip(self, zip_path: str) -> None:
        """扫描ZIP类型资源包
        
        Args:
            zip_path: ZIP文件路径
            
        Raises:
            ResourcePackLoadError: 扫描失败时抛出
        """
        if not zipfile.is_zipfile(zip_path):
            raise ResourcePackLoadError(f"无效的ZIP资源包: {zip_path}")
        
        try:
            with zipfile.ZipFile(zip_path, "r") as zip_file:
                # 过滤出资源文件（排除元数据和其他特殊文件）
                for file_info in zip_file.infolist():
                    file_path = file_info.filename
                    
                    # 跳过目录和特殊文件
                    if file_path.endswith("/") or file_path in ["pack.json", ".gitignore", "README.md"]:
                        continue
                    
                    # 跳过隐藏文件和特殊目录
                    parts = file_path.split("/")
                    if any(part.startswith(".") or part in ["__pycache__"] for part in parts):
                        continue
                    
                    self.files.append(file_path)
                    self.file_mapping[file_path] = f"zip:{zip_path}!{file_path}"
        except Exception as e:
            raise ResourcePackLoadError(f"扫描ZIP资源包时出错: {str(e)}")
    
    def get_file_path(self, relative_path: str) -> Optional[str]:
        """获取资源文件的实际路径
        
        Args:
            relative_path: 相对路径
            
        Returns:
            Optional[str]: 实际路径，如果不存在则返回None
        """
        # 统一路径格式
        relative_path = relative_path.replace("\\", "/")
        
        return self.file_mapping.get(relative_path)
    
    def has_file(self, relative_path: str) -> bool:
        """检查资源包是否包含指定文件
        
        Args:
            relative_path: 相对路径
            
        Returns:
            bool: 是否包含文件
        """
        # 统一路径格式
        relative_path = relative_path.replace("\\", "/")
        
        return relative_path in self.file_mapping
    
    def get_file_content(self, relative_path: str) -> Optional[bytes]:
        """获取资源文件内容
        
        Args:
            relative_path: 相对路径
            
        Returns:
            Optional[bytes]: 文件内容，如果不存在则返回None
            
        Raises:
            ResourcePackError: 读取失败时抛出
        """
        # 统一路径格式
        relative_path = relative_path.replace("\\", "/")
        
        # 检查文件是否存在
        if not self.has_file(relative_path):
            return None
        
        file_path = self.file_mapping[relative_path]
        
        try:
            # 处理ZIP文件中的资源
            if file_path.startswith("zip:"):
                zip_path, internal_path = file_path[4:].split("!", 1)
                
                with zipfile.ZipFile(zip_path, "r") as zip_file:
                    return zip_file.read(internal_path)
            
            # 处理普通文件
            else:
                with open(file_path, "rb") as f:
                    return f.read()
        except Exception as e:
            raise ResourcePackError(f"读取资源文件失败: {str(e)}")
    
    def get_info(self) -> Dict[str, Any]:
        """获取资源包信息
        
        Returns:
            Dict[str, Any]: 资源包信息
        """
        return {
            "id": self.metadata.id if self.metadata else "",
            "name": self.metadata.name if self.metadata else "",
            "version": self.metadata.version if self.metadata else "",
            "description": self.metadata.description if self.metadata else "",
            "author": self.metadata.author if self.metadata else "",
            "type": self.type.name,
            "path": self.path,
            "file_count": len(self.files),
            "format": self.metadata.format.value if self.metadata else 0,
            "loaded": self.loaded
        }
    
    def __str__(self) -> str:
        """获取资源包字符串表示
        
        Returns:
            str: 资源包字符串表示
        """
        if self.metadata:
            return f"ResourcePack(id={self.metadata.id}, name={self.metadata.name}, version={self.metadata.version})"
        else:
            return f"ResourcePack(path={self.path}, type={self.type.name}, loaded={self.loaded})"
    
    def __repr__(self) -> str:
        """获取资源包字符串表示
        
        Returns:
            str: 资源包字符串表示
        """
        return self.__str__()


class ResourcePackManager:
    """资源包管理器"""
    
    # 单例实例
    _instance = None
    _lock = threading.Lock()
    
    @classmethod
    def get_instance(cls) -> 'ResourcePackManager':
        """获取资源包管理器实例
        
        Returns:
            ResourcePackManager: 资源包管理器实例
        """
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        
        return cls._instance
    
    def __init__(self):
        """初始化资源包管理器"""
        # 防止直接实例化
        if ResourcePackManager._instance is not None:
            raise RuntimeError("ResourcePackManager是单例类，请使用get_instance()获取实例")
        
        self.logger = logging.getLogger("Status.ResourcePackManager")
        
        # 资源包目录
        self.builtin_dir = os.path.join(os.path.dirname(__file__), "..", "..", "resources")
        self.user_dir = os.path.expanduser(config_manager.get("resources.packs_directory", "~/.status/packs"))
        
        # 确保用户资源包目录存在
        os.makedirs(self.user_dir, exist_ok=True)
        
        # 已加载的资源包
        self.resource_packs: Dict[str, ResourcePack] = {}
        
        # 资源路径映射（资源相对路径 -> 处理后的资源包路径）
        self.resource_path_map: Dict[str, str] = {}
        
        # 激活的资源包列表，按优先级排序（高优先级在前）
        self.active_packs: List[str] = []
        
        # 是否已初始化
        self.initialized = False
        
        # 初始化锁
        self._init_lock = threading.Lock()
    
    def initialize(self) -> bool:
        """初始化资源包管理器
        
        Returns:
            bool: 初始化是否成功
        """
        if self.initialized:
            return True
        
        with self._init_lock:
            if self.initialized:
                return True
            
            self.logger.info("正在初始化资源包管理器...")
            
            try:
                # 加载内置资源包
                self._load_builtin_packs()
                
                # 加载用户资源包
                self._load_user_packs()
                
                # 设置活跃资源包
                self._setup_active_packs()
                
                # 更新资源路径映射
                self._update_resource_path_map()
                
                self.initialized = True
                self.logger.info(f"资源包管理器初始化完成，已加载 {len(self.resource_packs)} 个资源包，激活 {len(self.active_packs)} 个")
                
                return True
            except Exception as e:
                self.logger.error(f"初始化资源包管理器失败: {str(e)}")
                return False
    
    def _load_builtin_packs(self) -> None:
        """加载内置资源包"""
        if not os.path.exists(self.builtin_dir):
            self.logger.warning(f"内置资源包目录不存在: {self.builtin_dir}")
            return
        
        # 获取内置资源包目录
        builtin_packs_dir = os.path.join(self.builtin_dir, "packs")
        
        if not os.path.exists(builtin_packs_dir):
            self.logger.warning(f"内置资源包目录不存在: {builtin_packs_dir}")
            return
        
        # 遍历内置资源包目录
        for item in os.listdir(builtin_packs_dir):
            item_path = os.path.join(builtin_packs_dir, item)
            
            # 只加载目录
            if not os.path.isdir(item_path):
                continue
            
            try:
                # 创建内置资源包
                pack = ResourcePack(item_path, ResourcePackType.BUILTIN)
                
                # 加载资源包
                pack.load()
                
                # 确保 metadata 已加载
                if pack.metadata:
                    # 添加到已加载资源包列表
                    self.resource_packs[pack.metadata.id] = pack
                    self.logger.info(f"已加载内置资源包: {pack.metadata.name} (ID: {pack.metadata.id})")
                else:
                    self.logger.error(f"加载内置资源包元数据失败: {item_path}")
            except Exception as e:
                self.logger.error(f"加载内置资源包失败: {item_path}, 错误: {str(e)}")
    
    def _load_user_packs(self) -> None:
        """加载用户资源包"""
        if not os.path.exists(self.user_dir):
            self.logger.warning(f"用户资源包目录不存在: {self.user_dir}")
            return
        
        # 遍历用户资源包目录
        for item in os.listdir(self.user_dir):
            item_path = os.path.join(self.user_dir, item)
            
            try:
                # 处理目录类型资源包
                if os.path.isdir(item_path):
                    # 检查是否有元数据文件
                    if not os.path.exists(os.path.join(item_path, "pack.json")):
                        self.logger.warning(f"跳过无效的资源包目录: {item_path}")
                        continue
                    
                    # 创建目录资源包
                    pack = ResourcePack(item_path, ResourcePackType.DIRECTORY)
                
                # 处理ZIP类型资源包
                elif os.path.isfile(item_path) and item.endswith(".zip"):
                    # 创建ZIP资源包
                    pack = ResourcePack(item_path, ResourcePackType.ZIP)
                
                # 跳过其他类型文件
                else:
                    continue
                
                # 加载资源包
                pack.load()
                
                # 确保 metadata 已加载
                if not pack.metadata:
                    self.logger.error(f"加载用户资源包元数据失败: {item_path}")
                    continue
                
                # 检查是否已存在同ID资源包
                if pack.metadata.id in self.resource_packs:
                    existing_pack = self.resource_packs[pack.metadata.id]
                    if not existing_pack.metadata: # 确保 existing_pack 的 metadata 也存在
                        self.logger.warning(f"已存在的资源包 {existing_pack.path} 元数据丢失，将覆盖它")
                        self.resource_packs[pack.metadata.id] = pack
                        self.logger.info(f"用户资源包 {pack.metadata.name} 覆盖了元数据丢失的现有包")
                        continue

                    # 如果内置资源包，则用户资源包优先
                    if existing_pack.type == ResourcePackType.BUILTIN:
                        self.logger.info(f"用户资源包 {pack.metadata.name} 覆盖了内置资源包 {existing_pack.metadata.name}")
                        self.resource_packs[pack.metadata.id] = pack
                    else:
                        # 否则根据版本号决定
                        if pack.metadata.version > existing_pack.metadata.version:
                            self.logger.info(f"更新资源包: {existing_pack.metadata.name} ({existing_pack.metadata.version}) -> {pack.metadata.name} ({pack.metadata.version})")
                            self.resource_packs[pack.metadata.id] = pack
                        else:
                            self.logger.info(f"跳过加载旧版本资源包: {pack.metadata.name} ({pack.metadata.version}), 已存在: {existing_pack.metadata.version}")
                else:
                    # 添加到已加载资源包列表
                    self.resource_packs[pack.metadata.id] = pack
                    self.logger.info(f"已加载用户资源包: {pack.metadata.name} (ID: {pack.metadata.id})")
            except Exception as e:
                self.logger.error(f"加载用户资源包失败: {item_path}, 错误: {str(e)}")
    
    def _setup_active_packs(self) -> None:
        """设置活跃资源包"""
        # 清空当前活跃列表
        self.active_packs.clear()
        
        # 从配置中获取激活的资源包列表
        active_packs_from_config = config_manager.get("resources.active_packs", [])
        
        # 添加配置中指定的资源包
        for pack_id in active_packs_from_config:
            if pack_id in self.resource_packs:
                self.active_packs.append(pack_id)
                self.logger.debug(f"已激活资源包: {pack_id}")
            else:
                self.logger.warning(f"配置中的资源包不存在: {pack_id}")
        
        # 如果没有激活的资源包，使用默认资源包
        if not self.active_packs:
            # 查找一个内置默认资源包（通常是ID以builtin.default开头的）
            default_pack_id = None
            
            for pack_id, pack in self.resource_packs.items():
                if pack_id.startswith("builtin.default") or pack_id == "builtin.default":
                    default_pack_id = pack_id
                    break
            
            if default_pack_id:
                self.active_packs.append(default_pack_id)
                self.logger.info(f"使用默认资源包: {default_pack_id}")
            else:
                self.logger.warning("未找到默认资源包，资源系统可能无法正常工作")
    
    def _update_resource_path_map(self) -> None:
        """更新资源路径映射"""
        # 清空当前映射
        self.resource_path_map.clear()
        
        # 逆序遍历活跃资源包（低优先级资源包在前，被高优先级覆盖）
        for pack_id in reversed(self.active_packs):
            pack = self.resource_packs.get(pack_id)
            
            if pack is None or not pack.metadata: # 增加对 pack.metadata 的检查
                continue
            
            # 遍历资源包中的所有文件
            for file_path in pack.files:
                # 构建规范化的资源路径
                resource_path = file_path
                
                # 将资源路径映射到资源包文件路径
                actual_file_path = pack.get_file_path(file_path)
                if actual_file_path: # 确保路径不是None
                    self.resource_path_map[resource_path] = actual_file_path
        
        self.logger.debug(f"已更新资源路径映射，共 {len(self.resource_path_map)} 个资源")
    
    def reload(self) -> bool:
        """重新加载所有资源包
        
        Returns:
            bool: 重新加载是否成功
        """
        self.logger.info("正在重新加载资源包...")
        
        # 清空当前状态
        self.resource_packs.clear()
        self.active_packs.clear()
        self.resource_path_map.clear()
        self.initialized = False
        
        # 重新初始化
        return self.initialize()
    
    def add_resource_pack(self, pack_path: str) -> Optional[str]:
        """添加资源包
        
        Args:
            pack_path: 资源包路径
            
        Returns:
            Optional[str]: 成功时返回资源包ID，失败时返回None
            
        Raises:
            ResourcePackError: 加载失败时抛出
        """
        try:
            # 确保已初始化
            if not self.initialized:
                self.initialize()
            
            # 判断资源包类型
            if os.path.isdir(pack_path):
                pack_type = ResourcePackType.DIRECTORY
            elif os.path.isfile(pack_path) and pack_path.endswith(".zip"):
                pack_type = ResourcePackType.ZIP
            else:
                raise ResourcePackError(f"不支持的资源包类型: {pack_path}")
            
            # 创建资源包
            pack = ResourcePack(pack_path, pack_type)
            
            # 加载资源包
            pack.load()
 
            if not pack.metadata: # 检查 metadata 是否加载成功
                raise ResourcePackError(f"添加资源包失败: 无法加载元数据 {pack_path}")
            
            # 检查是否已存在同ID资源包
            if pack.metadata.id in self.resource_packs:
                existing_pack = self.resource_packs[pack.metadata.id]
                if not existing_pack.metadata: # 确保 existing_pack 的 metadata 也存在
                    self.logger.warning(f"已存在的资源包 {existing_pack.path} 元数据丢失，将覆盖它")
                    self.resource_packs[pack.metadata.id] = pack
                    self.logger.info(f"新资源包 {pack.metadata.name} 覆盖了元数据丢失的现有包")
                    return pack.metadata.id
                
                # 根据版本号决定是否更新
                if pack.metadata.version > existing_pack.metadata.version:
                    self.logger.info(f"更新资源包: {existing_pack.metadata.name} ({existing_pack.metadata.version}) -> {pack.metadata.name} ({pack.metadata.version})")
                    self.resource_packs[pack.metadata.id] = pack
                else:
                    self.logger.info(f"跳过加载旧版本资源包: {pack.metadata.name} ({pack.metadata.version}), 已存在: {existing_pack.metadata.version}")
                    return existing_pack.metadata.id # 返回已存在包的ID
            else:
                # 添加到已加载资源包列表
                self.resource_packs[pack.metadata.id] = pack
                self.logger.info(f"已加载资源包: {pack.metadata.name} (ID: {pack.metadata.id})")
            
            # 如果是用户资源包，复制到用户资源包目录
            if pack_type == ResourcePackType.ZIP:
                if not pack.metadata: 
                     raise ResourcePackError(f"添加资源包失败: 无法加载元数据用于确定目标路径 {pack_path}")
                target_path = os.path.join(self.user_dir, f"{pack.metadata.id}.zip")
                
                if os.path.normpath(pack_path) != os.path.normpath(target_path):
                    shutil.copy2(pack_path, target_path)
                    self.logger.info(f"已复制资源包到用户目录: {target_path}")
            
            if not pack.metadata: 
                raise ResourcePackError(f"添加资源包失败: 无法加载元数据以返回ID {pack_path}")
            return pack.metadata.id
        except Exception as e:
            self.logger.error(f"添加资源包失败: {str(e)}")
            
            # 重新抛出异常以便上层处理
            if isinstance(e, ResourcePackError):
                raise
            else:
                raise ResourcePackError(f"添加资源包失败: {str(e)}")
    
    def remove_resource_pack(self, pack_id: str) -> bool:
        """移除资源包
        
        Args:
            pack_id: 资源包ID
            
        Returns:
            bool: 移除是否成功
        """
        # 确保已初始化
        if not self.initialized:
            self.initialize()
        
        # 检查资源包是否存在
        if pack_id not in self.resource_packs:
            self.logger.warning(f"移除资源包失败: 资源包不存在 {pack_id}")
            return False
        
        # 获取资源包
        pack = self.resource_packs[pack_id]
        
        # 不允许移除内置资源包
        if pack.type == ResourcePackType.BUILTIN:
            self.logger.warning(f"不允许移除内置资源包: {pack_id}")
            return False
        
        try:
            # 从激活列表中移除
            if pack_id in self.active_packs:
                self.active_packs.remove(pack_id)
                
                # 更新配置
                config_manager.set("resources.active_packs", self.active_packs)
            
            # 从已加载资源包中移除
            del self.resource_packs[pack_id]
            
            # 如果是ZIP资源包，尝试从用户目录删除文件
            if pack.type == ResourcePackType.ZIP:
                # 资源包文件路径
                pack_file = os.path.join(self.user_dir, f"{pack_id}.zip")
                
                if os.path.exists(pack_file):
                    os.remove(pack_file)
                    self.logger.info(f"已删除资源包文件: {pack_file}")
            
            # 重新计算资源路径映射
            self._update_resource_path_map()
            
            self.logger.info(f"已移除资源包: {pack_id}")
            
            return True
        except Exception as e:
            self.logger.error(f"移除资源包失败: {pack_id}, 错误: {str(e)}")
            return False
    
    def get_resource_packs(self) -> Dict[str, Dict[str, Any]]:
        """获取所有资源包信息
        
        Returns:
            Dict[str, Dict[str, Any]]: 资源包信息字典，键为资源包ID
        """
        # 确保已初始化
        if not self.initialized:
            self.initialize()
        
        result = {}
        
        for pack_id, pack in self.resource_packs.items():
            # 获取资源包信息
            pack_info = pack.get_info()
            
            # 添加激活状态
            pack_info["active"] = pack_id in self.active_packs
            
            result[pack_id] = pack_info
        
        return result
    
    def get_resource_pack(self, pack_id: str) -> Optional[ResourcePack]:
        """获取资源包
        
        Args:
            pack_id: 资源包ID
            
        Returns:
            Optional[ResourcePack]: 资源包，如果不存在则返回None
        """
        # 确保已初始化
        if not self.initialized:
            self.initialize()
        
        return self.resource_packs.get(pack_id)
    
    def get_active_packs(self) -> List[str]:
        """获取激活的资源包ID列表
        
        Returns:
            List[str]: 激活的资源包ID列表
        """
        # 确保已初始化
        if not self.initialized:
            self.initialize()
        
        return self.active_packs.copy()
    
    def activate_pack(self, pack_id: str) -> bool:
        """激活资源包
        
        Args:
            pack_id: 资源包ID
            
        Returns:
            bool: 激活是否成功
        """
        # 确保已初始化
        if not self.initialized:
            self.initialize()
        
        # 检查资源包是否存在
        if pack_id not in self.resource_packs:
            self.logger.warning(f"激活资源包失败: 资源包不存在 {pack_id}")
            return False
        
        # 检查是否已激活
        if pack_id in self.active_packs:
            self.logger.info(f"资源包已激活: {pack_id}")
            return True
        
        try:
            # 添加到激活列表（放在最前面，表示最高优先级）
            self.active_packs.insert(0, pack_id)
            
            # 更新配置
            config_manager.set("resources.active_packs", self.active_packs)
            
            # 重新计算资源路径映射
            self._update_resource_path_map()
            
            self.logger.info(f"已激活资源包: {pack_id}")
            
            return True
        except Exception as e:
            self.logger.error(f"激活资源包失败: {pack_id}, 错误: {str(e)}")
            return False
    
    def deactivate_pack(self, pack_id: str) -> bool:
        """取消激活资源包
        
        Args:
            pack_id: 资源包ID
            
        Returns:
            bool: 取消激活是否成功
        """
        # 确保已初始化
        if not self.initialized:
            self.initialize()
        
        # 检查是否已激活
        if pack_id not in self.active_packs:
            self.logger.info(f"资源包未激活: {pack_id}")
            return True
        
        try:
            # 从激活列表中移除
            self.active_packs.remove(pack_id)
            
            # 更新配置
            config_manager.set("resources.active_packs", self.active_packs)
            
            # 重新计算资源路径映射
            self._update_resource_path_map()
            
            self.logger.info(f"已取消激活资源包: {pack_id}")
            
            return True
        except Exception as e:
            self.logger.error(f"取消激活资源包失败: {pack_id}, 错误: {str(e)}")
            return False
    
    def set_pack_priority(self, pack_id: str, priority: int) -> bool:
        """设置资源包优先级
        
        Args:
            pack_id: 资源包ID
            priority: 优先级（0表示最高优先级）
            
        Returns:
            bool: 设置是否成功
        """
        # 确保已初始化
        if not self.initialized:
            self.initialize()
        
        # 检查资源包是否存在
        if pack_id not in self.resource_packs:
            self.logger.warning(f"设置资源包优先级失败: 资源包不存在 {pack_id}")
            return False
        
        # 检查是否已激活
        if pack_id not in self.active_packs:
            self.logger.warning(f"设置资源包优先级失败: 资源包未激活 {pack_id}")
            return False
        
        try:
            # 从激活列表中移除
            self.active_packs.remove(pack_id)
            
            # 插入到指定位置
            priority = max(0, min(priority, len(self.active_packs)))
            self.active_packs.insert(priority, pack_id)
            
            # 更新配置
            config_manager.set("resources.active_packs", self.active_packs)
            
            # 重新计算资源路径映射
            self._update_resource_path_map()
            
            self.logger.info(f"已设置资源包优先级: {pack_id}, 优先级: {priority}")
            
            return True
        except Exception as e:
            self.logger.error(f"设置资源包优先级失败: {pack_id}, 错误: {str(e)}")
            return False
    
    def get_resource_path(self, resource_path: str) -> Optional[str]:
        """获取资源文件的实际路径
        
        Args:
            resource_path: 资源相对路径
            
        Returns:
            Optional[str]: 实际路径，如果不存在则返回None
        """
        # 确保已初始化
        if not self.initialized:
            self.initialize()
        
        # 统一路径格式
        resource_path = resource_path.replace("\\", "/")
        
        # 查找资源路径映射
        return self.resource_path_map.get(resource_path)
    
    def get_resource_content(self, resource_path: str) -> Optional[bytes]:
        """获取资源文件内容
        
        Args:
            resource_path: 资源相对路径
            
        Returns:
            Optional[bytes]: 文件内容，如果不存在则返回None
            
        Raises:
            ResourcePackError: 读取失败时抛出
        """
        # 确保已初始化
        if not self.initialized:
            self.initialize()
        
        # 统一路径格式
        resource_path = resource_path.replace("\\", "/")
        
        # 获取实际路径
        file_path = self.get_resource_path(resource_path)
        
        if file_path is None:
            return None
        
        try:
            # 处理ZIP文件中的资源
            if file_path.startswith("zip:"):
                zip_path, internal_path = file_path[4:].split("!", 1)
                
                with zipfile.ZipFile(zip_path, "r") as zip_file:
                    return zip_file.read(internal_path)
            
            # 处理普通文件
            else:
                with open(file_path, "rb") as f:
                    return f.read()
        except Exception as e:
            raise ResourcePackError(f"读取资源文件失败: {str(e)}")
    
    def has_resource(self, resource_path: str) -> bool:
        """检查资源是否存在
        
        Args:
            resource_path: 资源相对路径
            
        Returns:
            bool: 资源是否存在
        """
        # 确保已初始化
        if not self.initialized:
            self.initialize()
        
        # 统一路径格式
        resource_path = resource_path.replace("\\", "/")
        
        # 查找资源路径映射
        return resource_path in self.resource_path_map
    
    def list_resources(self, prefix: str = "") -> List[str]:
        """列出资源
        
        Args:
            prefix: 资源路径前缀
            
        Returns:
            List[str]: 资源路径列表
        """
        # 确保已初始化
        if not self.initialized:
            self.initialize()
        
        # 统一路径格式
        prefix = prefix.replace("\\", "/")
        
        # 筛选资源
        result = []
        
        for resource_path in self.resource_path_map.keys():
            if resource_path.startswith(prefix):
                result.append(resource_path)
        
        return result
    
    def create_resource_pack(self, pack_id: str, name: str, output_path: Optional[str] = None) -> Optional[str]:
        """创建新的资源包
        
        Args:
            pack_id: 资源包ID
            name: 资源包名称
            output_path: 输出路径，如果不指定则在用户资源包目录中创建
            
        Returns:
            Optional[str]: 成功时返回资源包路径，失败时返回None
            
        Raises:
            ResourcePackError: 创建失败时抛出
        """
        try:
            # 验证资源包ID
            if not pack_id:
                raise ResourcePackError("资源包ID不能为空")
            
            if not pack_id.isalnum() and not all(c.isalnum() or c in "._-" for c in pack_id):
                raise ResourcePackError(f"资源包ID '{pack_id}' 格式无效，只能包含字母、数字、点、下划线和连字符")
            
            # 验证资源包名称
            if not name:
                raise ResourcePackError("资源包名称不能为空")
            
            # 检查资源包ID是否已存在
            if pack_id in self.resource_packs:
                raise ResourcePackError(f"资源包ID '{pack_id}' 已存在")
            
            # 确定输出路径
            if output_path is None:
                output_path = os.path.join(self.user_dir, pack_id)
            
            # 创建资源包目录
            os.makedirs(output_path, exist_ok=True)
            
            # 创建元数据文件
            metadata = {
                "id": pack_id,
                "name": name,
                "version": "1.0.0",
                "description": f"自定义资源包 {name}",
                "format": 1,
                "author": "Status Team",
                "created_at": "",  # 可以添加当前时间
                "updated_at": ""
            }
            
            # 写入元数据文件
            with open(os.path.join(output_path, "pack.json"), "w", encoding="utf-8") as f:
                json.dump(metadata, f, ensure_ascii=False, indent=4)
            
            self.logger.info(f"已创建资源包: {name} (ID: {pack_id}), 路径: {output_path}")
            
            return output_path
        except Exception as e:
            self.logger.error(f"创建资源包失败: {str(e)}")
            
            # 重新抛出异常以便上层处理
            if isinstance(e, ResourcePackError):
                raise
            else:
                raise ResourcePackError(f"创建资源包失败: {str(e)}")
    
    def export_resource_pack(self, pack_id: str, output_path: str) -> Optional[str]:
        """导出资源包为ZIP文件
        
        Args:
            pack_id: 资源包ID
            output_path: 输出路径
            
        Returns:
            Optional[str]: 成功时返回导出的文件路径，失败时返回None
            
        Raises:
            ResourcePackError: 导出失败时抛出
        """
        try:
            # 检查资源包是否存在
            if pack_id not in self.resource_packs:
                raise ResourcePackError(f"资源包不存在: {pack_id}")
            
            # 获取资源包
            pack = self.resource_packs[pack_id]
            
            # 确保输出目录存在
            os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
            
            # 如果已经是ZIP资源包，可以直接复制
            if pack.type == ResourcePackType.ZIP:
                # 复制文件
                shutil.copy2(pack.path, output_path)
                return output_path
            
            # 创建ZIP文件
            with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zip_file:
                # 添加元数据
                if pack.metadata:
                    metadata_content = json.dumps(pack.metadata.to_dict(), ensure_ascii=False, indent=4)
                    zip_file.writestr("pack.json", metadata_content.encode("utf-8"))
                
                # 添加资源文件
                for relative_path in pack.files:
                    # 获取文件内容
                    content = pack.get_file_content(relative_path)
                    
                    if content is not None:
                        # 添加到ZIP文件
                        zip_file.writestr(relative_path, content)
            
            self.logger.info(f"已导出资源包: {pack_id}, 路径: {output_path}")
            
            return output_path
        except Exception as e:
            self.logger.error(f"导出资源包失败: {pack_id}, 错误: {str(e)}")
            
            # 重新抛出异常以便上层处理
            if isinstance(e, ResourcePackError):
                raise
            else:
                raise ResourcePackError(f"导出资源包失败: {str(e)}")


# 创建资源包管理器实例
resource_pack_manager = ResourcePackManager.get_instance()


# 导出的API
__all__ = [
    'ResourcePack',
    'ResourcePackManager',
    'ResourcePackError',
    'ResourcePackLoadError',
    'ResourcePackValidationError',
    'ResourcePackType',
    'ResourcePackFormat',
    'ResourcePackMetadata',
    'resource_pack_manager'
] 