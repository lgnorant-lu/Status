"""
---------------------------------------------------------------
File name:                  resource_loader.py
Author:                     Ignorant-lu
Date created:               2025/04/04
Description:                资源加载工具模块
----------------------------------------------------------------

Changed history:            
                            2025/04/04: 初始创建;
                            2025/05/12: 修复类型提示;
                            2025/05/15: 添加热加载事件响应支持;
----
"""

import os
import re
import json
import logging
import importlib.util
import time
from pathlib import Path
from typing import Dict, Any, List, Optional, Union, Set, Tuple, TypeVar, Callable, cast, Type, Protocol, overload, runtime_checkable, TYPE_CHECKING
from functools import lru_cache
from collections import OrderedDict
import zlib # 添加zlib导入用于压缩

# 全局标志
HAS_GUI = False

# 尝试导入事件系统
try:
    from status.core.events import EventManager
    HAS_EVENT_SYSTEM = True
except ImportError:
    HAS_EVENT_SYSTEM = False

# PySide6类型定义
if TYPE_CHECKING:
    # 类型检查时导入
    from PySide6.QtGui import QImage, QFont, QFontDatabase, QPixmap
else:
    # 运行时尝试导入
    try:
        from PySide6.QtGui import QImage, QPixmap, QFont, QFontDatabase
        HAS_GUI = True
    except ImportError:
        HAS_GUI = False
        # 为类型检查器定义占位类
        class QImage:
            def loadFromData(self, data: bytes) -> bool: ...
            def isNull(self) -> bool: ...
        class QFont:
            def setPointSize(self, size: int) -> None: ...
        class QFontDatabase:
            @staticmethod
            def addApplicationFontFromData(data: bytes) -> int: ...
            @staticmethod
            def applicationFontFamilies(font_id: int) -> List[str]: ...
            @staticmethod
            def addApplicationFont(file_path: str) -> int: ...

# 导入核心类型
from status.core.types import PathLike
from status.resources import ResourceType # 添加导入

# 配置日志
logger = logging.getLogger(__name__)

def natural_sort_key(s: str) -> List[Union[int, str]]:
    """用于文件的自然排序 (如 frame1.png, frame2.png, ..., frame10.png)"""
    return [int(c) if c.isdigit() else c.lower() for c in re.split(r'(\d+)', str(s))]

# 用于类型标注的声明
T = TypeVar('T')

# 资源管理器接口
@runtime_checkable
class ResourceManager(Protocol):
    """资源管理器接口，供ResourceLoader使用"""
    def has_resource(self, path: str) -> bool: ...
    def get_resource_content(self, path: str) -> Optional[bytes]: ...
    def get_resource_path(self, path: str) -> Optional[str]: ...
    def list_resources(self, prefix: str = "") -> List[str]: ...
    def reload(self) -> bool: ...
    def initialize(self) -> bool: ...

class LRUCache:
    """LRU缓存实现，用于ResourceLoader缓存管理
    
    使用OrderedDict实现LRU缓存，支持自动清理最近最少使用的缓存项
    """
    
    def __init__(self, capacity: int = 100):
        """初始化LRU缓存
        
        Args:
            capacity: 缓存容量, 默认为100
        """
        self.capacity = capacity
        self.cache = OrderedDict() #恢复 OrderedDict
        self.access_times = {}  # 记录每个键的最后访问时间
        
    def get(self, key):
        """获取缓存项
        
        Args:
            key: 缓存项的键
            
        Returns:
            缓存项的值，如果不存在则返回None
        """
        if key not in self.cache:
            return None
        
        # 移动到末尾（最近使用）
        value = self.cache.pop(key)
        self.cache[key] = value
        
        # 更新访问时间
        self.access_times[key] = time.time()
        
        return value

    def put(self, key, value):
        """添加缓存项
        
        Args:
            key: 缓存项的键
            value: 缓存项的值
        """
        # 如果已存在，先移除
        if key in self.cache:
            self.cache.pop(key)
        
        # 如果已达到容量上限，移除最早使用的项
        if len(self.cache) >= self.capacity:
            oldest_key, _ = self.cache.popitem(last=False)
            if oldest_key in self.access_times:
                del self.access_times[oldest_key]
        
        # 添加新项
        self.cache[key] = value
        self.access_times[key] = time.time()
    
    def remove(self, key):
        """移除缓存项
        
        Args:
            key: 缓存项的键
            
        Returns:
            bool: 是否成功移除
        """
        if key in self.cache:
            self.cache.pop(key)
            if key in self.access_times:
                del self.access_times[key]
            return True
        return False

    def clear(self):
        """清空缓存"""
        self.cache.clear()
        self.access_times.clear()
    
    def clean_old_entries(self, max_age_seconds: int = 3600):
        """清理过期的缓存项
        
        Args:
            max_age_seconds: 最大缓存时间(秒)，默认为3600秒(1小时)
            
        Returns:
            int: 清理的项数
        """
        now = time.time()
        keys_to_remove = []
        
        # 找出需要清理的键
        # 在迭代时复制 access_times.items() 以允许在循环中删除
        for key, access_time in list(self.access_times.items()):
            if now - access_time > max_age_seconds:
                keys_to_remove.append(key)
        
        # 清理缓存
        for key_to_remove in keys_to_remove:
            self.remove(key_to_remove)
            
        return len(keys_to_remove)
    
    def __len__(self):
        """获取缓存项数量"""
        return len(self.cache)
    
    def __contains__(self, key):
        """检查键是否在缓存中"""
        return key in self.cache


class ResourceLoader:
    """资源加载类，提供统一的资源加载接口"""
    
    def __init__(self) -> None:
        """初始化资源加载器"""
        self.logger: logging.Logger = logging.getLogger("Status.ResourceLoader")
        self._manager: Optional[ResourceManager] = None # 资源管理器实例，如 ResourcePackManager
        self.base_path: Optional[str] = None # 资源的基础路径
        
        # 使用LRUCache替换原来的字典缓存
        self._image_cache = LRUCache(100)       # 图像缓存
        self._sound_cache = LRUCache(50)        # 音频缓存
        self._font_cache = LRUCache(20)         # 字体缓存
        self._json_cache = LRUCache(100)        # JSON缓存
        self._text_cache = LRUCache(100)        # 文本缓存
        self._general_cache = LRUCache(100)     # 通用资源缓存
        
        # 缓存控制
        self._cache_enabled = True                # 是否启用缓存
        self._cache_max_age = 3600                # 缓存最大存活时间(秒)
        self._cache_clean_interval = 600          # 缓存清理间隔(秒)
        self._last_cache_clean = time.time()      # 上次缓存清理时间
        
        # 资源加载统计
        self._load_stats = {
            "total_loads": 0,        # 总加载次数
            "cache_hits": 0,         # 缓存命中次数
            "cache_misses": 0,       # 缓存未命中次数
            "by_type": {},           # 按类型统计
            "errors": 0              # 错误次数
        }
        
        # 事件系统集成
        self._event_system = None
        if HAS_EVENT_SYSTEM:
            try:
                self._event_system = EventManager.get_instance()
                # 注册事件处理器
                self._register_event_handlers()
            except Exception as e:
                self.logger.warning(f"无法获取事件管理器实例: {e}")
        
        # 加载默认资源包管理器
        self._load_default_manager()
    
    # +++ 新增压缩/解压缩辅助方法 +++
    def _compress_data(self, data: bytes, algorithm: str = 'zlib') -> bytes:
        """压缩给定的字节数据。

        Args:
            data: 要压缩的原始字节数据。
            algorithm: 使用的压缩算法。目前仅支持 'zlib'。

        Returns:
            压缩后的字节数据。

        Raises:
            ValueError: 如果指定的算法不受支持。
        """
        if algorithm == 'zlib':
            return zlib.compress(data)
        # elif algorithm == 'gzip':
        #     return gzip.compress(data) # 示例：如果将来支持gzip
        else:
            self.logger.error(f"Unsupported compression algorithm: {algorithm}")
            raise ValueError(f"Unsupported compression algorithm: {algorithm}")

    def _decompress_data(self, data: bytes, algorithm: str = 'zlib') -> bytes:
        """解压缩给定的字节数据。

        Args:
            data: 要解压缩的压缩字节数据。
            algorithm: 使用的解压缩算法。目前仅支持 'zlib'。

        Returns:
            解压缩后的原始字节数据。

        Raises:
            ValueError: 如果指定的算法不受支持。
            zlib.error: 如果解压缩失败 (例如，数据损坏或格式不正确)。
        """
        if algorithm == 'zlib':
            try:
                return zlib.decompress(data)
            except zlib.error as e:
                self.logger.error(f"Zlib decompression failed: {e}")
                raise # 重新抛出原始的zlib错误，以便调用者可以捕获它
        # elif algorithm == 'gzip':
        #     try:
        #         return gzip.decompress(data)
        #     except gzip.BadGzipFile as e:
        #         self.logger.error(f"Gzip decompression failed: {e}")
        #         raise
        else:
            self.logger.error(f"Unsupported decompression algorithm: {algorithm}")
            raise ValueError(f"Unsupported decompression algorithm: {algorithm}")
    # --- 结束新增方法 ---

    def _get_resource_type(self, path: str) -> Optional[ResourceType]:
        """根据文件路径推断资源类型。"""
        ext = os.path.splitext(path)[1].lower()
        if ext in (".png", ".jpg", ".jpeg", ".bmp", ".gif", ".svg", ".webp"):
            return ResourceType.IMAGE
        elif ext in (".wav", ".mp3", ".ogg", ".flac"):
            return ResourceType.AUDIO
        elif ext == ".json":
            return ResourceType.JSON
        elif ext in (".txt", ".md", ".csv", ".xml", ".html", ".css", ".js"):
            return ResourceType.TEXT
        elif ext in (".ttf", ".otf"):
            return ResourceType.FONT
        # 将之前未定义的特定类型归为 OTHER
        elif ext in (".zip", ".pet_anim", ".pet_config"):
            self.logger.debug(f"路径 '{path}' 的扩展名 {ext} 归类为 OTHER")
            return ResourceType.OTHER
        else:
            self.logger.debug(f"无法从路径 '{path}' 推断主要资源类型，扩展名: {ext}，归类为 OTHER")
            return ResourceType.OTHER
    
    def _load_default_manager(self) -> None:
        """尝试加载默认的资源管理器"""
        try:
            # 尝试导入资源包管理器
            from status.resources.resource_pack import ResourcePackManager
            pack_manager = ResourcePackManager.get_instance()
            # 使用 isinstance 检查确保兼容 ResourceManager 协议
            if hasattr(pack_manager, 'has_resource') and hasattr(pack_manager, 'get_resource_content'):
                self._manager = pack_manager
                self.logger.info("已加载ResourcePackManager作为默认资源管理器")
            else:
                self.logger.warning("ResourcePackManager不符合ResourceManager接口要求")
        except ImportError:
            self.logger.warning("无法加载ResourcePackManager，将使用文件系统作为备选")
            self._manager = None
    
    def set_manager(self, manager: Optional[ResourceManager]) -> None:
        """运行时切换资源管理器实例，便于测试和mock
        
        Args:
            manager: 资源管理器实例
        """
        self._manager = manager

    @property
    def manager(self) -> Optional[ResourceManager]:
        """获取当前资源管理器
        
        Returns:
            Optional[ResourceManager]: 当前资源管理器
        """
        return self._manager

    def has_resource(self, path: str) -> bool:
        """检查资源是否存在
        
        Args:
            path: 资源路径
            
        Returns:
            bool: 资源是否存在
        """
        # 如果 manager 没有 has_resource, 或者返回 False, 尝试文件系统
        mgr = self.manager
        if mgr and hasattr(mgr, 'has_resource') and mgr.has_resource(path):
            return True
        return os.path.exists(path)

    def get_resource_content(self, path: str) -> Optional[bytes]:
        """获取资源内容
        
        Args:
            path: 资源路径
            
        Returns:
            Optional[bytes]: 资源内容，如果资源不存在则返回None
        """
        # 优先尝试 manager
        mgr = self.manager
        content: Optional[bytes] = None
        
        if mgr and hasattr(mgr, 'get_resource_content'):
            content = mgr.get_resource_content(path)
        
        if content is None and os.path.exists(path):
            # 直接从文件系统加载
            try:
                with open(path, 'rb') as f:
                    content = f.read()
            except Exception as e:
                self.logger.error(f"从文件系统加载资源'{path}'失败: {e}")
        
        return content

    def clear_cache(self) -> None:
        """清除所有缓存"""
        self.logger.debug("清除所有资源缓存")
        
        # 清除各类型缓存
        self._image_cache.clear()
        self._sound_cache.clear()
        self._font_cache.clear()
        self._json_cache.clear()
        self._text_cache.clear()
        self._general_cache.clear()

    def _check_clean_cache(self) -> None:
        """检查是否需要清理缓存，并在必要时执行清理"""
        now = time.time()
        # 如果距离上次清理时间超过设定的间隔，清理缓存
        if now - self._last_cache_clean > self._cache_clean_interval:
            self._clean_old_cache_entries()
            self._last_cache_clean = now

    def _clean_old_cache_entries(self) -> None:
        """清理过期的缓存项"""
        # 清理各个缓存
        image_count = self._image_cache.clean_old_entries(self._cache_max_age)
        sound_count = self._sound_cache.clean_old_entries(self._cache_max_age)
        font_count = self._font_cache.clean_old_entries(self._cache_max_age)
        json_count = self._json_cache.clean_old_entries(self._cache_max_age)
        text_count = self._text_cache.clean_old_entries(self._cache_max_age)
        
        total_count = image_count + sound_count + font_count + json_count + text_count
        if total_count > 0:
            self.logger.info(f"自动清理了 {total_count} 个过期缓存项 (图像: {image_count}, 音效: {sound_count}, 字体: {font_count}, JSON: {json_count}, 文本: {text_count})")

    def set_cache_params(self, enabled: bool = True, max_age: int = 3600, 
                        clean_interval: int = 600) -> None:
        """设置缓存参数
        
        Args:
            enabled: 是否启用缓存
            max_age: 缓存项的最大生命周期（秒）
            clean_interval: 缓存清理间隔（秒）
        """
        self._cache_enabled = enabled
        self._cache_max_age = max_age
        self._cache_clean_interval = clean_interval
        self.logger.debug(f"更新缓存参数: 启用={enabled}, 最大生命周期={max_age}秒, 清理间隔={clean_interval}秒")

    def get_cache_stats(self) -> Dict[str, int]:
        """获取缓存统计信息
        
        Returns:
            Dict[str, int]: 包含各类缓存数量的字典
        """
        return {
            'image_cache': len(self._image_cache),
            'sound_cache': len(self._sound_cache),
            'font_cache': len(self._font_cache),
            'json_cache': len(self._json_cache),
            'text_cache': len(self._text_cache),
            'total': len(self._image_cache) + len(self._sound_cache) + len(self._font_cache) + len(self._json_cache) + len(self._text_cache)
        }

    def reload(self) -> bool:
        """重新加载资源管理器
        
        Returns:
            bool: 重载是否成功
        """
        self.logger.info("重新加载资源管理器")
        
        # 清除所有缓存
        self.clear_cache()
        
        # 如果有资源管理器，调用其reload方法
        if self._manager:
            try:
                # 重新加载资源管理器
                if hasattr(self._manager, "reload") and callable(getattr(self._manager, "reload")):
                    return self._manager.reload()
                return True
            except Exception as e:
                self.logger.error(f"重新加载资源管理器失败: {e}")
                return False
        
        return True
    
    def initialize(self) -> bool:
        """初始化资源加载器
        
        Returns:
            bool: 是否初始化成功
        """
        # 初始化资源包管理器
        if self.manager and hasattr(self.manager, 'initialize'):
            try:
                return bool(self.manager.initialize())
            except Exception:
                return False
        return True # 如果 manager 无需初始化，则认为成功
    
    def get_resource_path(self, resource_path: str) -> Optional[str]:
        """获取资源的实际文件系统路径
        
        如果资源位于资源包中，则返回资源包内的文件路径
        如果资源位于文件系统中，则返回原路径
        
        Args:
            resource_path: 资源路径
            
        Returns:
            Optional[str]: 资源的实际文件系统路径，或None（如果资源不存在）
        """
        mgr = self.manager
        
        # 先尝试使用资源包管理器解析路径
        if mgr and hasattr(mgr, 'get_resource_path'):
            path = mgr.get_resource_path(resource_path)
            if path and os.path.exists(path):
                return path
                
        # 再尝试直接作为文件系统路径
        if os.path.exists(resource_path):
            return resource_path
            
        return None
    
    def list_resources(self, prefix: str = "", resource_type: Optional[str] = None) -> List[str]:
        """列出指定前缀和类型的资源
        
        Args:
            prefix: 资源路径前缀
            resource_type: 资源类型（如 "image", "sound" 等）
            
        Returns:
            List[str]: 符合条件的资源路径列表
        """
        resources: List[str] = []
        if self.manager and hasattr(self.manager, 'list_resources'):
            resources = self.manager.list_resources(prefix)
        
        # 如果 ResourcePackManager 没有返回任何资源，尝试从文件系统扫描
        if not resources:
            # 尝试作为文件系统路径扫描
            try:
                path = Path(prefix) if prefix else Path(".")
                if path.exists() and path.is_dir():
                    resources = [str(p.relative_to(path)) for p in path.glob("**/*") if p.is_file()]
                    
                    # 按资源类型过滤
                    if resource_type:
                        if resource_type == "image":
                            extensions = {".png", ".jpg", ".jpeg", ".gif", ".bmp"}
                        elif resource_type == "sound":
                            extensions = {".wav", ".mp3", ".ogg"}
                        elif resource_type == "font":
                            extensions = {".ttf", ".otf"}
                        elif resource_type == "json":
                            extensions = {".json"}
                        elif resource_type == "text":
                            extensions = {".txt", ".md", ".cfg", ".ini"}
                        else:
                            extensions = set()
                            
                        if extensions:
                            resources = [r for r in resources if Path(r).suffix.lower() in extensions]
            except Exception as e:
                self.logger.error(f"扫描资源目录'{prefix}'失败: {e}")
        
        return sorted(resources, key=natural_sort_key)
    
    def load_resource(self, path: str, resource_type: Optional[ResourceType] = None, use_cache: bool = True, 
                      compressed: bool = False, compression_type: str = 'zlib', 
                      **kwargs: Any) -> Any:
        """加载指定路径的资源，支持多种资源类型和缓存。

        Args:
            path: 资源路径，相对于基础路径或资源包内部路径。
            resource_type: 资源类型 (ResourceType枚举)。如果为None，则尝试从文件扩展名推断。
            use_cache: 是否使用缓存。默认为True。
            compressed: 资源是否已压缩。默认为False。如果为True，将尝试使用指定的compression_type解压缩。
            compression_type: 使用的压缩算法。默认为 'zlib'。
            **kwargs: 特定资源类型加载时可能需要的额外参数 (例如字体大小)。

        Returns:
            加载的资源对象，如果加载失败则返回None。
        """
        self._check_clean_cache() # 定期清理旧缓存
        self._load_stats["total_loads"] += 1
        
        if resource_type is None:
            resource_type = self._get_resource_type(path)
        
        if resource_type is None:
            self.logger.warning(f"无法确定资源类型: {path}")
            self._load_stats["errors"] += 1
            return None

        self.logger.debug(f"准备加载资源: {path}, 类型: {resource_type}, 缓存: {use_cache}, 压缩: {compressed}")

        # 生成缓存键，考虑压缩状态以避免混淆
        # 如果我们总是缓存解压后的数据，那么压缩状态可能不需要成为主键的一部分，
        # 但在获取原始数据时它是重要的。
        # 暂时让缓存键与之前保持一致，因为我们目标是缓存解压后的版本。
        cache_key = f"{path}#{resource_type.value}"
        if kwargs:
            # 将kwargs中的项排序后加入key，保证顺序一致性
            sorted_kwargs = "&".join(f"{k}={v}" for k, v in sorted(kwargs.items()))
            cache_key = f"{cache_key}#{sorted_kwargs}"

        specific_cache: Optional[LRUCache] = None
        if resource_type == ResourceType.IMAGE: specific_cache = self._image_cache
        elif resource_type == ResourceType.AUDIO: specific_cache = self._sound_cache
        elif resource_type == ResourceType.FONT: specific_cache = self._font_cache
        elif resource_type == ResourceType.JSON: specific_cache = self._json_cache
        elif resource_type == ResourceType.TEXT: specific_cache = self._text_cache
        else: specific_cache = self._general_cache

        if use_cache and self._cache_enabled and specific_cache and cache_key in specific_cache:
            self.logger.debug(f"缓存命中: {cache_key}")
            self._load_stats["cache_hits"] += 1
            return specific_cache.get(cache_key)
        else:
            self.logger.debug(f"缓存未命中或不使用缓存: {cache_key}")
            self._load_stats["cache_misses"] += 1

        content_bytes: Optional[bytes] = None
        if self._manager:
            content_bytes = self._manager.get_resource_content(path)
        else:
            # 如果没有资源管理器，尝试直接从文件系统加载（如果适用）
            # 这部分逻辑可以根据需要扩展，但通常 ResourceLoader 依赖于一个 Manager
            # self.logger.warning("没有配置资源管理器，尝试直接文件系统加载 (如果路径是绝对的)")
            # if os.path.isabs(path) and os.path.exists(path):
            #     try:
            #         with open(path, 'rb') as f:
            #             content_bytes = f.read()
            #     except Exception as e:
            #         self.logger.error(f"直接文件加载失败 '{path}': {e}")
            self.logger.warning("没有配置资源管理器，无法加载资源。")
            
        if content_bytes is None:
            self.logger.warning(f"无法获取资源内容: {path}")
            self._load_stats["errors"] += 1
            return None
        
        # --- 处理解压缩 ---
        if compressed:
            self.logger.debug(f"资源 '{path}' 标记为已压缩，尝试使用 '{compression_type}' 解压缩...")
            try:
                decompressed_bytes = self._decompress_data(content_bytes, algorithm=compression_type)
                self.logger.info(f"资源 '{path}' 解压缩成功，原始大小: {len(content_bytes)}, 解压后大小: {len(decompressed_bytes)}")
                content_bytes = decompressed_bytes # 后续处理使用解压后的数据
            except ValueError as ve:
                self.logger.error(f"解压缩算法 '{compression_type}' 不支持或错误: {ve} for resource {path}")
                self._load_stats["errors"] += 1
                return None # 或者根据策略决定是否尝试作为未压缩数据加载
            except Exception as e: # 例如 zlib.error
                self.logger.error(f"解压缩资源 '{path}' 失败 (算法: {compression_type}): {e}")
                self._load_stats["errors"] += 1
                # 根据测试用例，如果标记为压缩但解压失败（如数据损坏或实际未压缩），应抛出原始错误
                raise e 
        # --- 结束解压缩处理 ---

        # 根据资源类型处理内容
        loaded_resource: Any = None
        try:
            if resource_type == ResourceType.IMAGE:
                loaded_resource = self._parse_image_data(content_bytes, path, **kwargs)
            elif resource_type == ResourceType.AUDIO:
                loaded_resource = self._parse_sound_data(content_bytes, path, **kwargs) # 假设有此方法
            elif resource_type == ResourceType.FONT:
                loaded_resource = self._parse_font_data(content_bytes, path, **kwargs)
            elif resource_type == ResourceType.JSON:
                encoding = kwargs.get('encoding', 'utf-8')
                loaded_resource = json.loads(content_bytes.decode(encoding))
            elif resource_type == ResourceType.TEXT:
                encoding = kwargs.get('encoding', 'utf-8')
                loaded_resource = content_bytes.decode(encoding)
            elif resource_type == ResourceType.BINARY:
                loaded_resource = content_bytes # 二进制数据直接返回bytes
            else:
                self.logger.warning(f"不支持的资源类型进行特定解析: {resource_type} for {path}. 返回原始字节.")
                loaded_resource = content_bytes 
        except Exception as e:
            self.logger.error(f"解析资源内容失败 '{path}' (类型: {resource_type}): {e}")
            self._load_stats["errors"] += 1
            return None

        if loaded_resource is not None and use_cache and self._cache_enabled and specific_cache:
            self.logger.debug(f"缓存资源: {cache_key}")
            specific_cache.put(cache_key, loaded_resource)
            
        # 更新按类型统计
        type_stats = self._load_stats["by_type"].get(resource_type.value, {"loads": 0, "errors": 0})
        type_stats["loads"] += 1
        if loaded_resource is None:
            type_stats["errors"] += 1
        self._load_stats["by_type"][resource_type.value] = type_stats
        
        return loaded_resource

    def save_resource_content(self, file_path: str, data: bytes, compress: bool = False, compression_type: str = 'zlib', overwrite: bool = True) -> bool:
        """保存资源内容到指定路径，支持压缩。

        Args:
            file_path: 要保存到的完整文件路径。
            data: 要保存的原始字节数据。
            compress: 是否在保存前压缩数据。默认为False。
            compression_type: 如果compress为True，使用的压缩算法。默认为'zlib'。
            overwrite: 如果文件已存在，是否覆盖。默认为True。

        Returns:
            bool: 保存是否成功。
        """
        self.logger.info(f"准备保存资源到 '{file_path}', 压缩: {compress} ({compression_type if compress else '无'}), 覆盖: {overwrite}")
        
        if not overwrite and os.path.exists(file_path):
            self.logger.warning(f"文件 '{file_path}' 已存在且不允许覆盖。保存操作中止。")
            return False

        try:
            # 确保目录存在
            directory = os.path.dirname(file_path)
            if directory and not os.path.exists(directory):
                os.makedirs(directory, exist_ok=True)
                self.logger.info(f"已创建目录: {directory}")

            data_to_write = data
            if compress:
                self.logger.debug(f"对资源 '{file_path}' 进行压缩 (算法: {compression_type})...")
                try:
                    compressed_data = self._compress_data(data, algorithm=compression_type)
                    self.logger.info(f"资源 '{file_path}' 压缩完成，原始大小: {len(data)}, 压缩后大小: {len(compressed_data)}")
                    data_to_write = compressed_data
                except ValueError as ve: # 不支持的算法
                    self.logger.error(f"压缩算法 '{compression_type}' 不支持或错误: {ve} for resource {file_path}. 将保存原始数据。")
                except Exception as e:
                    self.logger.error(f"压缩资源 '{file_path}' 失败 (算法: {compression_type}): {e}. 将保存原始数据。")
            
            with open(file_path, 'wb') as f:
                f.write(data_to_write)
            
            self.logger.info(f"资源已成功保存到: {file_path}")
            return True
        except IOError as ioe:
            self.logger.error(f"写入文件时发生IO错误 '{file_path}': {ioe}")
            return False
        except Exception as e:
            self.logger.error(f"保存资源 '{file_path}' 时发生未知错误: {e}")
            return False

    def _parse_image_data(self, data: bytes, path: str, **kwargs: Any) -> Optional[Any]:
        """解析图像资源
        
        Args:
            data: 图像数据
            path: 图像路径
            **kwargs: 其他参数
        
        Returns:
            Optional[Any]: 解析后的图像对象，或None（如果解析失败）
        """
        if not HAS_GUI:
            self.logger.error("QImage未导入，无法加载图像")
            return None
        
        # 检查是否需要清理缓存
        self._check_clean_cache()
        
        # 如果启用缓存且已在缓存中，直接返回
        if self._cache_enabled:
            cached_image = self._image_cache.get(path)
            if cached_image is not None:
                return cached_image
        
        # 获取资源实际路径
        real_path = self.get_resource_path(path)
        
        # 如果获取不到实际路径，尝试直接从内容加载
        if not real_path:
            content = self.get_resource_content(path)
            if not content:
                self.logger.error(f"找不到图像: {path}")
                return None
                
            # 从二进制数据加载QImage
            try:
                qimage = QImage()
                success = qimage.loadFromData(data)
                
                if success:
                    # 确保图像有正确的格式（保持透明度）
                    if qimage.hasAlphaChannel():
                        # 确保保留Alpha通道
                        qimage = qimage.convertToFormat(QImage.Format.Format_ARGB32)
                    
                    # 加载成功
                    if self._cache_enabled:
                        self._image_cache.put(path, qimage)
                    return qimage
                else:
                    # 加载失败
                    self.logger.error(f"使用 QImage.loadFromData 加载图像失败: {path}")
                    return None
            
            except Exception as e:
                self.logger.error(f"加载图像失败: {path}, 错误: {e}")
                return None
            
        # 直接从文件路径加载
        try:
            qimage = QImage(real_path)
            
            if qimage.isNull():
                self.logger.error(f"QImage加载图像失败: {path}")
                return None
            
            # 确保图像有正确的格式（保持透明度）
            if qimage.hasAlphaChannel():
                # 确保保留Alpha通道
                qimage = qimage.convertToFormat(QImage.Format.Format_ARGB32)
                
            if self._cache_enabled:
                self._image_cache.put(path, qimage)
                
            return qimage
            
        except Exception as e:
            self.logger.error(f"加载图像失败: {path}, 错误: {e}")
            return None
    
    def _parse_sound_data(self, data: bytes, path: str, **kwargs: Any) -> Optional[Any]:
        """解析音效资源
        
        Args:
            data: 音效数据
            path: 音效路径
            **kwargs: 其他参数
        
        Returns:
            Optional[Any]: 解析后的音效对象，或None（如果解析失败）
        """
        # 此方法还未实现或者需要根据实际使用的音效库来实现
        # TODO: 实现音效加载功能，如使用 pygame.mixer 或 PySide6.QtMultimedia 等
        self.logger.warning("load_sound方法未实现")
        return None
    
    def _parse_font_data(self, data: bytes, path: str, **kwargs: Any) -> Optional[Any]:
        """解析字体资源
        
        Args:
            data: 字体数据
            path: 字体路径
            **kwargs: 其他参数
        
        Returns:
            Optional[Any]: 解析后的字体对象，或None（如果解析失败）
        """
        if not HAS_GUI:
            self.logger.error("QFont未导入，无法加载字体")
            return None
            
        # 缓存键
        cache_key = f"{path}_{kwargs.get('size', 16)}"
        
        # 如果启用缓存且已在缓存中，直接返回
        if self._cache_enabled:
            cached_font = self._font_cache.get(cache_key)
            if cached_font is not None:
                return cached_font
        
        # 获取资源实际路径
        real_path = self.get_resource_path(path)
            
        # 如果获取不到实际路径，尝试直接从内容加载
        if not real_path:
            content = self.get_resource_content(path)
            if not content:
                self.logger.error(f"找不到字体: {path}")
                return None
            
            # 从二进制数据加载QFont
            try:
                # 使用QFontDatabase从内存加载字体
                if TYPE_CHECKING:
                    from PySide6.QtGui import QFontDatabase
                font_id = QFontDatabase.addApplicationFontFromData(content)
                if font_id == -1:
                    self.logger.error(f"从内存加载字体失败: {path}")
                    return None
                    
                # 获取字体族
                families = QFontDatabase.applicationFontFamilies(font_id)
                if not families:
                    self.logger.error(f"无法获取字体族: {path}")
                    return None
                    
                font = QFont(families[0])
                font.setPointSize(kwargs.get('size', 16))
                
                if self._cache_enabled:
                    self._font_cache.put(cache_key, font)
                    
                return font
            
            except Exception as e:
                self.logger.error(f"加载字体失败: {path}, 错误: {e}")
                return None
        
        # 直接从文件路径加载
        try:
            # 使用QFontDatabase加载字体文件
            if TYPE_CHECKING:
                from PySide6.QtGui import QFontDatabase
            font_id = QFontDatabase.addApplicationFont(real_path)
            if font_id == -1:
                self.logger.error(f"加载字体失败: {path}")
                return None
                
            # 获取字体族
            families = QFontDatabase.applicationFontFamilies(font_id)
            if not families:
                self.logger.error(f"无法获取字体族: {path}")
                return None
                
            font = QFont(families[0])
            font.setPointSize(kwargs.get('size', 16))
            
            if self._cache_enabled:
                self._font_cache.put(cache_key, font)
        
            return font
        
        except Exception as e:
            self.logger.error(f"加载字体失败: {path}, 错误: {e}")
            return None
    
    def load_image(self, image_path: str, use_cache: bool = True) -> Optional[Any]:
        """加载图像资源
        
        Args:
            image_path: 图像资源路径
            use_cache: 是否使用缓存
            
        Returns:
            Optional[Any]: 加载的图像对象，或None（如果加载失败）
        """
        if not HAS_GUI:
            self.logger.error("QImage未导入，无法加载图像")
            return None
        
        # 检查是否需要清理缓存
        self._check_clean_cache()
        
        # 如果启用缓存且已在缓存中，直接返回
        if use_cache and self._cache_enabled:
            cached_image = self._image_cache.get(image_path)
            if cached_image is not None:
                return cached_image
        
        # 获取资源实际路径
        real_path = self.get_resource_path(image_path)
        
        # 如果获取不到实际路径，尝试直接从内容加载
        if not real_path:
            content = self.get_resource_content(image_path)
            if not content:
                self.logger.error(f"找不到图像: {image_path}")
                return None
                
            # 从二进制数据加载QImage
            try:
                qimage = QImage()
                success = qimage.loadFromData(content)
                
                if success:
                    # 确保图像有正确的格式（保持透明度）
                    if qimage.hasAlphaChannel():
                        # 确保保留Alpha通道
                        qimage = qimage.convertToFormat(QImage.Format.Format_ARGB32)
                    
                    # 加载成功
                    if use_cache and self._cache_enabled:
                        self._image_cache.put(image_path, qimage)
                    return qimage
                else:
                    # 加载失败
                    self.logger.error(f"使用 QImage.loadFromData 加载图像失败: {image_path}")
                    return None
            
            except Exception as e:
                self.logger.error(f"加载图像失败: {image_path}, 错误: {e}")
                return None
            
        # 直接从文件路径加载
        try:
            qimage = QImage(real_path)
            
            if qimage.isNull():
                self.logger.error(f"QImage加载图像失败: {image_path}")
                return None
            
            # 确保图像有正确的格式（保持透明度）
            if qimage.hasAlphaChannel():
                # 确保保留Alpha通道
                qimage = qimage.convertToFormat(QImage.Format.Format_ARGB32)
                
            if use_cache and self._cache_enabled:
                self._image_cache.put(image_path, qimage)
                
            return qimage
            
        except Exception as e:
            self.logger.error(f"加载图像失败: {image_path}, 错误: {e}")
            return None
    
    def load_sound(self, sound_path: str, use_cache: bool = True) -> Optional[Any]:
        """加载音效资源
        
        Args:
            sound_path: 音效资源路径
            use_cache: 是否使用缓存
            
        Returns:
            Optional[Any]: 加载的音效对象，或None（如果加载失败）
        """
        # 此方法还未实现或者需要根据实际使用的音效库来实现
        # TODO: 实现音效加载功能，如使用 pygame.mixer 或 PySide6.QtMultimedia 等
        self.logger.warning("load_sound方法未实现")
        return None
    
    def load_font(self, font_path: str, size: int = 16, use_cache: bool = True) -> Optional[Any]:
        """加载字体资源
        
        Args:
            font_path: 字体资源路径
            size: 字体大小
            use_cache: 是否使用缓存
            
        Returns:
            Optional[Any]: 加载的字体对象，或None（如果加载失败）
        """
        if not HAS_GUI:
            self.logger.error("QFont未导入，无法加载字体")
            return None
            
        # 缓存键
        cache_key = f"{font_path}_{size}"
        
        # 如果启用缓存且已在缓存中，直接返回
        if use_cache and self._cache_enabled:
            cached_font = self._font_cache.get(cache_key)
            if cached_font is not None:
                return cached_font
        
        # 获取资源实际路径
        real_path = self.get_resource_path(font_path)
            
        # 如果获取不到实际路径，尝试直接从内容加载
        if not real_path:
            content = self.get_resource_content(font_path)
            if not content:
                self.logger.error(f"找不到字体: {font_path}")
                return None
            
            # 从二进制数据加载QFont
            try:
                # 使用QFontDatabase从内存加载字体
                if TYPE_CHECKING:
                    from PySide6.QtGui import QFontDatabase
                font_id = QFontDatabase.addApplicationFontFromData(content)
                if font_id == -1:
                    self.logger.error(f"从内存加载字体失败: {font_path}")
                    return None
                    
                # 获取字体族
                families = QFontDatabase.applicationFontFamilies(font_id)
                if not families:
                    self.logger.error(f"无法获取字体族: {font_path}")
                    return None
                    
                font = QFont(families[0])
                font.setPointSize(size)
                
                if use_cache and self._cache_enabled:
                    self._font_cache.put(cache_key, font)
                    
                return font
            
            except Exception as e:
                self.logger.error(f"加载字体失败: {font_path}, 错误: {e}")
                return None
        
        # 直接从文件路径加载
        try:
            # 使用QFontDatabase加载字体文件
            if TYPE_CHECKING:
                from PySide6.QtGui import QFontDatabase
            font_id = QFontDatabase.addApplicationFont(real_path)
            if font_id == -1:
                self.logger.error(f"加载字体失败: {font_path}")
                return None
                
            # 获取字体族
            families = QFontDatabase.applicationFontFamilies(font_id)
            if not families:
                self.logger.error(f"无法获取字体族: {font_path}")
                return None
                
            font = QFont(families[0])
            font.setPointSize(size)
            
            if use_cache and self._cache_enabled:
                self._font_cache.put(cache_key, font)
        
            return font
        
        except Exception as e:
            self.logger.error(f"加载字体失败: {font_path}, 错误: {e}")
            return None
    
    def load_json(self, json_path: str, use_cache: bool = True, encoding: str = "utf-8") -> Optional[Dict[str, Any]]:
        """加载JSON资源
        
        Args:
            json_path: JSON资源路径
            use_cache: 是否使用缓存
            encoding: 文件编码
            
        Returns:
            Optional[Dict[str, Any]]: 加载的JSON数据，或None（如果加载失败）
        """
        # 检查是否需要清理缓存
        self._check_clean_cache()
        
        # 缓存键
        cache_key = f"{json_path}_{encoding}" # 缓存键应考虑编码
        
        # 如果启用缓存且已在缓存中，直接返回
        if use_cache and self._cache_enabled:
            cached_json = self._json_cache.get(cache_key)
            if cached_json is not None:
                return cached_json
        
        # 获取资源内容
        content = self.get_resource_content(json_path)
        if not content:
            self.logger.error(f"找不到JSON文件: {json_path}")
            return None
            
        # 解析JSON数据
        try:
            json_data = json.loads(content.decode(encoding))
            
            if use_cache and self._cache_enabled:
                self._json_cache.put(cache_key, json_data)
            
            return json_data
            
        except json.JSONDecodeError as e:
            self.logger.error(f"JSON解析失败: {json_path}, 错误: {e}")
            return None
        except Exception as e:
            self.logger.error(f"加载JSON失败: {json_path}, 错误: {e}")
            return None
    
    def load_text(self, text_path: str, encoding: str = "utf-8", use_cache: bool = True) -> Optional[str]:
        """加载文本资源
        
        Args:
            text_path: 文本资源路径
            encoding: 文本编码
            use_cache: 是否使用缓存
            
        Returns:
            Optional[str]: 加载的文本内容，或None（如果加载失败）
        """
        # 检查是否需要清理缓存
        self._check_clean_cache()
        
        # 缓存键（包含编码信息）
        cache_key = f"{text_path}_{encoding}"
        
        # 如果启用缓存且已在缓存中，直接返回
        if use_cache and self._cache_enabled:
            cached_text = self._text_cache.get(cache_key)
            if cached_text is not None:
                return cached_text
        
        # 获取资源内容
        content = self.get_resource_content(text_path)
        if not content:
            self.logger.error(f"找不到文本文件: {text_path}")
            return None
            
        # 解码文本
        try:
            text = content.decode(encoding)
            
            if use_cache and self._cache_enabled:
                self._text_cache.put(cache_key, text)
        
            return text
        
        except UnicodeDecodeError as e:
            self.logger.error(f"文本解码失败: {text_path}, 编码: {encoding}, 错误: {e}")
            return None
        except Exception as e:
            self.logger.error(f"加载文本失败: {text_path}, 错误: {e}")
            return None
    
    def load_image_sequence(self, directory_path: str, use_cache: bool = True) -> Optional[List[Any]]:
        """加载图像序列
        
        加载目录中所有图像，按自然排序排序（如: frame1.png, frame2.png, ..., frame10.png）
        
        Args:
            directory_path: 图像序列目录路径
            use_cache: 是否使用缓存
            
        Returns:
            Optional[List[Any]]: 加载的图像序列，或None（如果加载失败）
        """
        # 列出目录中的所有图像
        image_files = self.list_resources(directory_path, resource_type="image")
        
        if not image_files:
            self.logger.error(f"目录中没有图像: {directory_path}")
            return None
    
        # 加载每个图像
        images: List[Any] = []
        for image_file in image_files:
            full_path = os.path.join(directory_path, image_file) if not image_file.startswith(directory_path) else image_file
            image = self.load_image(full_path, use_cache)
            
            if image:
                images.append(image)
            
        if not images:
            self.logger.error(f"没有成功加载任何图像: {directory_path}")
            return None
            
        return images

    def get_resource_info(self, path: str) -> Optional[Dict[str, Any]]:
        """获取资源的基本信息。

        Args:
            path: 资源路径。

        Returns:
            一个包含资源信息的字典 (例如，大小，类型，修改时间)，如果资源不存在则为 None。
            信息字典可能包含: 'path', 'type', 'size_bytes', 'last_modified', 'full_path'。
        """
        actual_path = self.get_resource_path(path) # 尝试通过管理器获取实际路径
        if not actual_path:
            # 如果管理器未返回路径，但路径本身可能就是个直接的文件系统路径
            if os.path.exists(path):
                actual_path = path
            else:
                self.logger.debug(f"get_resource_info: 资源不存在于任何已知位置: {path}")
                return None

        if not os.path.exists(actual_path):
            self.logger.debug(f"get_resource_info: 实际路径不存在: {actual_path} (原始路径: {path})")
            return None

        try:
            resource_type = self._get_resource_type(actual_path)
            size_bytes = os.path.getsize(actual_path)
            last_modified = os.path.getmtime(actual_path)
            
            info: Dict[str, Any] = {
                'path': path, # 原始请求路径
                'full_path': actual_path, # 实际文件系统路径
                'type': resource_type.value if resource_type else "unknown", # 使用枚举值
                'size_bytes': size_bytes,
                'last_modified': last_modified
            }
            return info
        except Exception as e:
            self.logger.error(f"获取资源 '{path}' (实际: '{actual_path}') 信息失败: {e}")
            return None

    def _register_event_handlers(self) -> None:
        """注册事件处理函数"""
        if not self._event_system:
            return
            
        try:
            # 注册资源包重载事件处理函数
            if self._event_system and hasattr(self._event_system, 'subscribe'):
                self._event_system.subscribe("resource_pack.reloaded", self.handle_resource_pack_reloaded)
                self._event_system.subscribe("resource_pack.added", self.handle_resource_pack_added)
                self._event_system.subscribe("resource_pack.removed", self.handle_resource_pack_removed)
            
            self.logger.debug("已注册资源包事件处理器")
        except Exception as e:
            self.logger.error(f"注册事件处理函数失败: {e}")
    
    def handle_resource_pack_reloaded(self, event_data: Dict[str, Any]) -> None:
        """处理资源包重载事件
        
        Args:
            event_data: 事件数据，包含pack_id字段
        """
        if not event_data or "pack_id" not in event_data:
            return
            
        pack_id = event_data["pack_id"]
        self.logger.info(f"接收到资源包重载事件: {pack_id}")
        
        # 清除所有缓存，确保使用最新的资源
        self.clear_cache()
    
    def handle_resource_pack_added(self, event_data: Dict[str, Any]) -> None:
        """处理资源包添加事件
        
        Args:
            event_data: 事件数据，包含pack_id字段
        """
        if not event_data or "pack_id" not in event_data:
            return
            
        pack_id = event_data["pack_id"]
        self.logger.info(f"接收到资源包添加事件: {pack_id}")
        
        # 对于新添加的资源包，不需要清除缓存，因为还没有相关缓存
    
    def handle_resource_pack_removed(self, event_data: Dict[str, Any]) -> None:
        """处理资源包移除事件
        
        Args:
            event_data: 事件数据，包含pack_id字段
        """
        if not event_data or "pack_id" not in event_data:
            return
            
        pack_id = event_data["pack_id"]
        self.logger.info(f"接收到资源包移除事件: {pack_id}")
        
        # 清除所有缓存，因为可能有使用被移除资源包的资源
        self.clear_cache()

# 创建资源加载器实例
# resource_loader = ResourceLoader() # 实例应由 AssetManager 创建和管理


# 导出的API
__all__ = [
    'ResourceLoader',
    # 'resource_loader'
] 