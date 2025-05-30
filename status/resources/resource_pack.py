"""
---------------------------------------------------------------
File name:                  resource_pack.py
Author:                     Ignorant-lu
Date created:               2025/04/03
Description:                资源包管理，提供资源包加载和切换功能
----------------------------------------------------------------

Changed history:            
                            2025/04/03: 初始创建;
                            2025/05/12: 修复类型提示;
                            2025/05/15: 添加热加载功能;
----
"""

import os
import json
import logging
import zipfile
import shutil
from typing import Dict, Any, List, Optional, Set, Tuple, cast, TypeVar, Type
from enum import Enum, auto
import threading
import time

from status.core.config import config_manager
from status.core.types import PathLike

# 尝试导入事件系统
try:
    from status.core.events import EventManager
    HAS_EVENT_SYSTEM = True
except ImportError:
    HAS_EVENT_SYSTEM = False


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
        self.id: str = data.get("id", "")
        self.name: str = data.get("name", "")
        self.version: str = data.get("version", "1.0.0")
        self.description: str = data.get("description", "")
        self.format: ResourcePackFormat = ResourcePackFormat(data.get("format", 1))
        
        # 可选字段
        self.author: str = data.get("author", "")
        self.website: str = data.get("website", "")
        self.license: str = data.get("license", "")
        self.dependencies: List[str] = data.get("dependencies", [])
        self.tags: List[str] = data.get("tags", [])
        self.preview_image: str = data.get("preview_image", "")
        self.created_at: str = data.get("created_at", "")
        self.updated_at: str = data.get("updated_at", "")
        
        # 资源覆盖设置
        self.override_settings: Dict[str, Any] = data.get("override_settings", {})
        
        # 原始数据
        self.raw_data: Dict[str, Any] = data
    
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
    
    def __init__(self, path: PathLike, pack_type: ResourcePackType):
        """初始化资源包
        
        Args:
            path: 资源包路径
            pack_type: 资源包类型
        """
        self.path: PathLike = path
        self.type: ResourcePackType = pack_type
        self.logger: logging.Logger = logging.getLogger("Status.ResourcePack")
        
        # 资源包元数据
        self.metadata: Optional[ResourcePackMetadata] = None
        
        # 资源文件列表缓存
        self.files: List[str] = []
        
        # 资源文件映射（替代路径 -> 实际路径）
        self.file_mapping: Dict[str, str] = {}
        
        # 是否已加载
        self.loaded: bool = False
        
        # 加载锁
        self._load_lock: threading.Lock = threading.Lock()
    
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
                return True # type: ignore[unreachable]
            
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
        metadata_content: Optional[Dict[str, Any]] = None
        
        try:
            if self.type == ResourcePackType.DIRECTORY:
                metadata_path = os.path.join(str(self.path), "pack.json")
                
                if not os.path.exists(metadata_path):
                    raise ResourcePackLoadError(f"资源包元数据文件不存在: {metadata_path}")
                
                with open(metadata_path, "r", encoding="utf-8") as f:
                    metadata_content = json.load(f)
            
            elif self.type == ResourcePackType.ZIP:
                if not zipfile.is_zipfile(self.path):
                    raise ResourcePackLoadError(f"无效的ZIP资源包: {self.path}")
                
                with zipfile.ZipFile(str(self.path), "r") as zip_file:
                    if "pack.json" not in zip_file.namelist():
                        raise ResourcePackLoadError(f"ZIP资源包中缺少元数据文件: {self.path}")
                    
                    with zip_file.open("pack.json") as f:
                        metadata_content = json.loads(f.read().decode("utf-8"))
            
            elif self.type == ResourcePackType.BUILTIN:
                # 内置资源包，元数据可能是硬编码的
                metadata_path = os.path.join(str(self.path), "pack.json")
                if os.path.exists(metadata_path):
                    with open(metadata_path, "r", encoding="utf-8") as f:
                        metadata_content = json.load(f)
                else:
                    # 为内置资源包生成默认元数据
                    name = os.path.basename(str(self.path))
                    metadata_content = {
                        "id": f"builtin.{name}",
                        "name": f"内置资源包 ({name})",
                        "version": "1.0.0",
                        "description": "内置默认资源包",
                        "format": 1,
                        "author": "Status-Ming",
                        "license": "MIT"
                    }
            
            if not metadata_content:
                raise ResourcePackLoadError(f"无法加载资源包元数据: {self.path}")
            
            # 创建元数据对象
            self.metadata = ResourcePackMetadata(metadata_content)
            
            # 验证元数据
            self.metadata.validate()
            
        except json.JSONDecodeError as e:
            raise ResourcePackLoadError(f"资源包元数据格式错误: {str(e)}")
        except Exception as e:
            # 重新抛出异常以便上层处理
            if isinstance(e, ResourcePackError):
                raise
            else:
                raise ResourcePackLoadError(f"加载资源包元数据失败: {str(e)}")
    
    def _scan_files(self) -> None:
        """扫描资源文件
        
        扫描资源包中的所有文件，并建立文件映射
        
        Raises:
            ResourcePackLoadError: 扫描失败时抛出
        """
        try:
            if self.type == ResourcePackType.DIRECTORY:
                self._scan_directory(str(self.path))
            elif self.type == ResourcePackType.ZIP:
                self._scan_zip(str(self.path))
            elif self.type == ResourcePackType.BUILTIN:
                self._scan_directory(str(self.path))
            
            self.logger.debug(f"资源包 '{self.metadata.id if self.metadata else 'unknown'}' 文件扫描完成，共 {len(self.files)} 个文件")
        except Exception as e:
            self.logger.error(f"扫描资源包文件失败: {str(e)}")
            # 重新抛出异常以便上层处理
            if isinstance(e, ResourcePackError):
                raise
            else:
                raise ResourcePackLoadError(f"扫描资源包文件失败: {str(e)}")
    
    def _scan_directory(self, directory: str) -> None:
        """扫描目录
        
        Args:
            directory: 目录路径
        """
        for root, _, files in os.walk(directory):
            for file in files:
                # 跳过元数据文件
                if file == "pack.json" and root == directory:
                    continue
                
                file_path = os.path.join(root, file)
                # 计算相对路径
                rel_path = os.path.relpath(file_path, directory)
                # 统一使用正斜杠
                rel_path = rel_path.replace("\\", "/")
                
                self.files.append(rel_path)
                self.file_mapping[rel_path] = file_path
    
    def _scan_zip(self, zip_path: str) -> None:
        """扫描ZIP文件
        
        Args:
            zip_path: ZIP文件路径
        """
        with zipfile.ZipFile(zip_path, "r") as zip_file:
            for file_info in zip_file.infolist():
                # 跳过目录和元数据文件
                if file_info.filename.endswith("/") or file_info.filename == "pack.json":
                    continue
                    
                # 统一使用正斜杠
                rel_path = file_info.filename.replace("\\", "/")
                    
                self.files.append(rel_path)
                # 对于ZIP文件，映射存储完整路径
                self.file_mapping[rel_path] = f"{zip_path}:{rel_path}"

    def get_file_path(self, relative_path: str) -> Optional[str]:
        """获取文件实际路径
        
        Args:
            relative_path: 相对路径
            
        Returns:
            Optional[str]: 实际路径，如果文件不存在则返回None
        """
        # 统一使用正斜杠
        relative_path = relative_path.replace("\\", "/")
        
        return self.file_mapping.get(relative_path)
    
    def has_file(self, relative_path: str) -> bool:
        """判断文件是否存在
        
        Args:
            relative_path: 相对路径
            
        Returns:
            bool: 文件是否存在
        """
        # 统一使用正斜杠
        relative_path = relative_path.replace("\\", "/")
        
        return relative_path in self.file_mapping
    
    def get_file_content(self, relative_path: str) -> Optional[bytes]:
        """获取文件内容
        
        Args:
            relative_path: 相对路径
            
        Returns:
            Optional[bytes]: 文件内容，如果文件不存在则返回None
        """
        # 统一使用正斜杠
        relative_path = relative_path.replace("\\", "/")
        
        # 获取实际文件路径
        file_path = self.file_mapping.get(relative_path)
        
        if not file_path:
            return None
        
        try:
            # 处理ZIP文件
            if self.type == ResourcePackType.ZIP:
                # ZIP文件的路径格式为 "zip_path:file_path"
                zip_path, inner_path = file_path.split(":", 1)
                
                with zipfile.ZipFile(zip_path, "r") as zip_file:
                    return zip_file.read(inner_path)
            else:
                # 直接打开文件
                with open(file_path, "rb") as f:
                    return f.read()
        except Exception as e:
            self.logger.error(f"读取文件失败: {relative_path}, 错误: {str(e)}")
            return None
    
    def get_info(self) -> Dict[str, Any]:
        """获取资源包信息
        
        Returns:
            Dict[str, Any]: 资源包信息
        """
        if not self.metadata:
            return {"id": "", "name": "未知资源包", "error": "未加载元数据"}
        
        info = self.metadata.to_dict()
        
        # 添加额外信息
        info["file_count"] = len(self.files)
        info["path"] = str(self.path)
        info["type"] = self.type.name
        
        return info
    
    def __str__(self) -> str:
        """字符串表示
        
        Returns:
            str: 字符串表示
        """
        if self.metadata:
            return f"ResourcePack(id={self.metadata.id}, name={self.metadata.name}, version={self.metadata.version})"
        else:
            return f"ResourcePack(path={self.path}, type={self.type.name}, unloaded)"
    
    def __repr__(self) -> str:
        """表示
        
        Returns:
            str: 表示
        """
        return self.__str__()


T = TypeVar('T')


class ResourcePackManager:
    """资源包管理器"""
    
    # 单例实例
    _instance: Optional['ResourcePackManager'] = None
    _lock: threading.Lock = threading.Lock()
    
    @classmethod
    def get_instance(cls) -> 'ResourcePackManager':
        """获取单例实例
        
        Returns:
            ResourcePackManager: 单例实例
        """
        with cls._lock:
            if cls._instance is None:
                cls._instance = cls()
            
        return cls._instance
    
    def __init__(self):
        """初始化资源包管理器"""
        # 日志记录器
        self.logger: logging.Logger = logging.getLogger("Status.ResourcePackManager")
        
        # 资源包目录
        self.base_dir: str = ""  # 资源包基础目录
        self.user_dir: str = ""  # 用户资源包目录
        self.builtin_dir: str = ""  # 内置资源包目录
        
        # 资源包列表
        self.resource_packs: Dict[str, ResourcePack] = {}  # 所有已加载的资源包，键为pack_id
        
        # 激活的资源包列表（有序，优先级高的在前）
        self.active_packs: List[str] = []  # 激活的资源包ID列表
        
        # 资源路径映射，用于快速查找资源
        self.resource_path_map: Dict[str, str] = {}  # 资源相对路径 -> 资源包ID
        
        # 初始化状态
        self.initialized: bool = False
        
        # 热加载相关属性
        self._monitoring: bool = False  # 是否正在监控文件变化
        self._monitor_thread: Optional[threading.Thread] = None  # 监控线程
        self._monitor_interval: float = 5.0  # 监控间隔（秒）
        self._last_check_time: float = 0.0  # 上次检查时间
        self._directory_state: Dict[str, Any] = {}  # 目录状态缓存
        self._stop_event: threading.Event = threading.Event()  # 用于停止监控线程的事件
        
        self._instance_init_lock = threading.Lock() # Add instance-level lock

        # 事件系统集成
        self._event_system = None
        if HAS_EVENT_SYSTEM:
            try:
                self._event_system = EventManager.get_instance()
            except Exception as e:
                self.logger.warning(f"无法获取事件管理器实例: {e}")
    
    def initialize(self) -> bool:
        """初始化资源包管理器
        
        Returns:
            bool: 初始化是否成功
        """
        if self.initialized:
            return True
        
        with self._instance_init_lock: # Use instance-level lock
            if self.initialized:
                return True # type: ignore[unreachable]
            
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
                        # 根据版本号决定是否更新
                        if pack.metadata and existing_pack.metadata and pack.metadata.version > existing_pack.metadata.version:
                            self.logger.info(f"更新资源包: {existing_pack.metadata.name} ({existing_pack.metadata.version}) -> {pack.metadata.name} ({pack.metadata.version})")
                            self.resource_packs[pack.metadata.id] = pack
                        else:
                            self.logger.info(f"跳过加载旧版本资源包: {pack.metadata.name if pack.metadata else 'unknown'} ({pack.metadata.version if pack.metadata else 'unknown'}), 已存在: {existing_pack.metadata.version if existing_pack.metadata else 'unknown'}")
                            # 跳过当前包的处理
                            continue
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
            pack_path: 资源包路径（ZIP文件或目录）
            
        Returns:
            Optional[str]: 资源包ID，如果添加失败则返回None
            
        Raises:
            ResourcePackError: 添加资源包失败时抛出
        """
        # 确保已初始化
        if not self.initialized:
            self.initialize()
            
        # 检查路径是否存在
        if not os.path.exists(pack_path):
            self.logger.error(f"添加资源包失败: 路径不存在 {pack_path}")
            return None
        
        try:
            # 判断资源包类型
            pack_type: ResourcePackType
            if os.path.isdir(pack_path):
                pack_type = ResourcePackType.DIRECTORY
            elif zipfile.is_zipfile(pack_path):
                pack_type = ResourcePackType.ZIP
            else:
                self.logger.error(f"添加资源包失败: 无法识别的资源包类型 {pack_path}")
                return None
            
            # 创建资源包
            pack = ResourcePack(pack_path, pack_type)
            
            # 加载资源包
            pack.load()
 
            # 检查资源包是否加载成功
            if not pack.metadata:
                self.logger.error(f"添加资源包失败: 无法加载元数据 {pack_path}")
                return None
            
            # 检查是否已存在同ID资源包
            if pack.metadata.id in self.resource_packs:
                existing_pack = self.resource_packs[pack.metadata.id]
                
                # 判断是否为同一资源包
                if os.path.samefile(str(existing_pack.path), pack_path):
                    self.logger.info(f"资源包已存在，无需重复加载: {pack.metadata.id}")
                    return pack.metadata.id
                
                # 根据版本号决定是否更新
                if pack.metadata and existing_pack.metadata and pack.metadata.version > existing_pack.metadata.version:
                    self.logger.info(f"更新资源包: {existing_pack.metadata.name} ({existing_pack.metadata.version}) -> {pack.metadata.name} ({pack.metadata.version})")
                    self.resource_packs[pack.metadata.id] = pack
                else:
                    self.logger.info(f"跳过加载旧版本资源包: {pack.metadata.name if pack.metadata else 'unknown'} ({pack.metadata.version if pack.metadata else 'unknown'}), 已存在: {existing_pack.metadata.version if existing_pack.metadata else 'unknown'}")
                    # 返回已存在包的ID，确保返回类型为 Optional[str]
                    if existing_pack.metadata:
                        return existing_pack.metadata.id
                    return None
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
            
            # pack.metadata 此时必定不为 None
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
    
    def get_resource_path(self, path: str) -> Optional[str]:
        """获取资源文件实际路径
        
        Args:
            path: 资源相对路径
            
        Returns:
            Optional[str]: 资源文件实际路径，如果资源不存在则返回None
        """
        # 确保已初始化
        if not self.initialized:
            self.initialize()
        
        # 统一使用正斜杠
        path = path.replace("\\", "/")
        
        return self.resource_path_map.get(path)
    
    def get_resource_content(self, path: str) -> Optional[bytes]:
        """获取资源文件内容
        
        Args:
            path: 资源相对路径
            
        Returns:
            Optional[bytes]: 文件内容，如果不存在则返回None
            
        Raises:
            ResourcePackError: 读取失败时抛出
        """
        # 确保已初始化
        if not self.initialized:
            self.initialize()
        
        # 统一路径格式
        path = path.replace("\\", "/")
        
        # 获取实际路径
        file_path = self.get_resource_path(path)
        
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
    
    def has_resource(self, path: str) -> bool:
        """检查资源是否存在
        
        Args:
            path: 资源相对路径
            
        Returns:
            bool: 资源是否存在
        """
        # 确保已初始化
        if not self.initialized:
            self.initialize()
        
        # 统一路径格式
        path = path.replace("\\", "/")
        
        # 查找资源路径映射
        return path in self.resource_path_map
    
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
    
    def start_monitoring(self) -> bool:
        """开始监控资源包目录变化
        
        Returns:
            bool: 是否成功启动监控
        """
        # 如果已经在监控中，则直接返回
        if self._monitoring:
            self.logger.debug("资源包监控已经在运行")
            return True
        
        # 确保已初始化
        if not self.initialized:
            self.initialize()
        
        # 标记为正在监控
        self._monitoring = True
        
        # 记录当前时间
        self._last_check_time = time.time()
        
        # 获取初始目录状态
        self._directory_state = self._get_directory_state()
        
        # 重置停止事件
        self._stop_event.clear()
        
        # 创建并启动监控线程
        self._monitor_thread = threading.Thread(
            target=self._monitor_worker,
            name="ResourcePackMonitor",
            daemon=True  # 守护线程，主线程退出时自动结束
        )
        self._monitor_thread.start()
        
        self.logger.info(f"已启动资源包目录监控，监控间隔: {self._monitor_interval}秒")
        return True
    
    def stop_monitoring(self) -> bool:
        """停止监控资源包目录变化
        
        Returns:
            bool: 是否成功停止监控
        """
        # 如果没有在监控中，则直接返回
        if not self._monitoring:
            self.logger.debug("资源包监控未运行")
            return True
        
        # 标记为不再监控
        self._monitoring = False
        
        # 设置停止事件，通知监控线程退出
        self._stop_event.set()
        
        # 等待监控线程结束
        if self._monitor_thread and self._monitor_thread.is_alive():
            self._monitor_thread.join(timeout=2.0)  # 最多等待2秒
            
            # 如果线程仍在运行，记录警告
            if self._monitor_thread.is_alive():
                self.logger.warning("资源包监控线程未能在2秒内正常退出")
        
        self._monitor_thread = None
        self.logger.info("已停止资源包目录监控")
        return True
    
    def set_monitor_interval(self, interval: float) -> None:
        """设置监控间隔
        
        Args:
            interval: 监控间隔（秒）
        """
        if interval < 0.5:
            interval = 0.5  # 最小0.5秒
        
        self._monitor_interval = interval
        self.logger.info(f"已设置资源包目录监控间隔为 {interval} 秒")
    
    def _monitor_worker(self) -> None:
        """监控工作线程，定期检查目录变化"""
        self.logger.debug("资源包监控线程已启动")
        
        try:
            while self._monitoring and not self._stop_event.is_set():
                # 检查目录变化
                self._check_directory_changes()
                
                # 等待指定的间隔时间，同时检查停止事件
                # 每0.5秒检查一次停止事件，以便及时响应停止请求
                for _ in range(int(self._monitor_interval * 2)):
                    if self._stop_event.is_set():
                        break
                    time.sleep(0.5)
        except Exception as e:
            self.logger.error(f"资源包监控线程发生异常: {str(e)}")
        finally:
            self.logger.debug("资源包监控线程已退出")
    
    def _get_directory_state(self) -> Dict[str, Any]:
        """获取当前资源包目录状态
        
        Returns:
            Dict[str, Any]: 目录状态
        """
        state = {}
        
        # 检查用户目录
        if os.path.exists(self.user_dir):
            user_state = {
                "mtime": os.path.getmtime(self.user_dir),
                "files": {}
            }
            
            # 获取所有文件的修改时间
            for file in os.listdir(self.user_dir):
                file_path = os.path.join(self.user_dir, file)
                if os.path.isfile(file_path):
                    user_state["files"][file_path] = os.path.getmtime(file_path)
            
            state[self.user_dir] = user_state
        
        # 检查已加载的目录类型资源包
        for pack_id, pack in self.resource_packs.items():
            if pack.type == ResourcePackType.DIRECTORY:
                dir_path = str(pack.path)
                if os.path.exists(dir_path) and os.path.isdir(dir_path):
                    dir_state = {
                        "mtime": os.path.getmtime(dir_path),
                        "files": {}
                    }
                    
                    # 递归获取所有文件的修改时间
                    for root, _, files in os.walk(dir_path):
                        for file in files:
                            file_path = os.path.join(root, file)
                            dir_state["files"][file_path] = os.path.getmtime(file_path)
                    
                    state[dir_path] = dir_state
        
        return state
    
    def _check_directory_changes(self) -> None:
        """检查目录变化，必要时重新加载资源包"""
        current_time = time.time()
        
        # 获取当前目录状态
        current_state = self._get_directory_state()
        
        # 检查用户目录是否有新文件
        user_dir = self.user_dir
        if os.path.exists(user_dir):
            # 获取上次检查时的用户目录状态
            prev_user_state = self._directory_state.get(user_dir, {"mtime": 0, "files": {}})
            
            # 获取当前用户目录状态
            curr_user_state = current_state.get(user_dir, {"mtime": 0, "files": {}})
            
            # 检查是否有新文件
            prev_files = set(prev_user_state.get("files", {}).keys())
            curr_files = set(curr_user_state.get("files", {}).keys())
            
            # 新增的文件
            new_files = curr_files - prev_files
            
            # 处理新文件
            for file_path in new_files:
                if zipfile.is_zipfile(file_path):
                    self.logger.info(f"发现新资源包: {file_path}")
                    try:
                        # 添加资源包
                        pack_id = self.add_resource_pack(file_path)
                        if pack_id:
                            self.logger.info(f"已自动加载新资源包: {pack_id}")
                            
                            # 触发事件
                            if self._event_system and hasattr(self._event_system, 'publish'):
                                self._event_system.publish("resource_pack.added", {
                                    "pack_id": pack_id,
                                    "path": file_path
                                })
                    except Exception as e:
                        self.logger.error(f"自动加载资源包失败: {file_path}, 错误: {str(e)}")
        
        # 检查目录类型资源包是否有变化
        for pack_id, pack in list(self.resource_packs.items()):
            if pack.type == ResourcePackType.DIRECTORY:
                dir_path = str(pack.path)
                if not os.path.exists(dir_path) or not os.path.isdir(dir_path):
                    # 目录已被删除
                    self.logger.warning(f"资源包目录已被删除: {dir_path}")
                    continue
                
                # 获取上次检查时的目录状态
                prev_dir_state = self._directory_state.get(dir_path, {"mtime": 0, "files": {}})
                
                # 获取当前目录状态
                curr_dir_state = current_state.get(dir_path, {"mtime": 0, "files": {}})
                
                # 检查文件是否有变化
                prev_files = prev_dir_state.get("files", {})
                curr_files = curr_dir_state.get("files", {})
                
                # 检查修改的文件
                changed = False
                for file_path, curr_mtime in curr_files.items():
                    prev_mtime = prev_files.get(file_path, 0)
                    if curr_mtime > prev_mtime:
                        # 文件已修改
                        changed = True
                        self.logger.debug(f"资源包文件已修改: {file_path}")
                
                if changed:
                    self.logger.info(f"检测到资源包变更: {pack_id}")
                    try:
                        # 热重载资源包
                        if self.hot_reload_pack(pack_id):
                            self.logger.info(f"已自动重新加载资源包: {pack_id}")
                    except Exception as e:
                        self.logger.error(f"自动重新加载资源包失败: {pack_id}, 错误: {str(e)}")
        
        # 更新目录状态
        self._directory_state = current_state
        self._last_check_time = current_time
    
    def hot_reload_pack(self, pack_id: str) -> bool:
        """热重载指定的资源包
        
        Args:
            pack_id: 资源包ID
            
        Returns:
            bool: 重载是否成功
        """
        # 检查资源包是否存在
        if pack_id not in self.resource_packs:
            self.logger.warning(f"热重载资源包失败: 资源包不存在 {pack_id}")
            return False
        
        # 获取资源包
        pack = self.resource_packs[pack_id]
        
        # 清空资源文件列表缓存
        pack.files = []
        pack.file_mapping = {}
        
        # 标记为未加载
        pack.loaded = False
        
        # 重新加载资源包
        try:
            # 调用资源包的load方法
            if not pack.load():
                self.logger.error(f"热重载资源包失败: 无法加载资源包 {pack_id}")
                return False
            
            # 更新资源路径映射
            self._update_resource_path_map()
            
            self.logger.info(f"已热重载资源包: {pack_id}")
            
            # 触发事件
            if self._event_system and hasattr(self._event_system, 'publish'):
                self._event_system.publish("resource_pack.reloaded", {
                    "pack_id": pack_id
                })
            
            return True
        except Exception as e:
            self.logger.error(f"热重载资源包失败: {pack_id}, 错误: {str(e)}")
            return False


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