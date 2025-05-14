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

# 全局标志
HAS_GUI = False

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
        self.cache = OrderedDict()
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
        for key, access_time in self.access_times.items():
            if now - access_time > max_age_seconds:
                keys_to_remove.append(key)
        
        # 清理缓存
        for key in keys_to_remove:
            self.remove(key)
            
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
        self._sound_cache = LRUCache(50)         # 音效缓存
        self._font_cache = LRUCache(20)  # 字体缓存
        self._json_cache = LRUCache(50)    # JSON数据缓存
        self._text_cache = LRUCache(50)          # 文本缓存
        
        # 缓存控制
        self._cache_enabled = True  # 是否启用缓存
        self._cache_max_age = 3600  # 缓存项的最大生命周期（秒）
        
        # 加载默认资源包管理器
        self._load_default_manager()
        
        # 上次缓存清理时间
        self._last_cache_clean_time = time.time()
        # 缓存清理间隔（秒）
        self._cache_clean_interval = 600  # 10分钟
    
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
        """清空所有缓存"""
        self._image_cache.clear()
        self._sound_cache.clear()
        self._font_cache.clear()
        self._json_cache.clear()
        self._text_cache.clear()
        self.logger.info("所有资源缓存已清空")

    def _check_clean_cache(self) -> None:
        """检查是否需要清理缓存，并在必要时执行清理"""
        now = time.time()
        # 如果距离上次清理时间超过设定的间隔，清理缓存
        if now - self._last_cache_clean_time > self._cache_clean_interval:
            self._clean_old_cache_entries()
            self._last_cache_clean_time = now

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
        """重新加载资源管理器并清空缓存
        
        Returns:
            bool: 是否重新加载成功
        """
        mgr = self.manager
        self.clear_cache()
        
        if mgr and hasattr(mgr, 'reload'):
            try:
                return bool(mgr.reload())
            except Exception:
                return False
                
        if mgr and hasattr(mgr, 'initialize'):
            try:
                return bool(mgr.initialize())
            except Exception:
                return False
                
        return False # 如果 manager 无相关方法
    
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
    
    def load_resource(self, path: str, resource_type: Optional[ResourceType] = None, use_cache: bool = True, **kwargs: Any) -> Any:
        """通用资源加载方法。

        Args:
            path: 资源路径。
            resource_type: 显式指定的资源类型。如果为None，则尝试从路径推断。
            use_cache: 是否使用缓存。
            **kwargs: 传递给特定加载方法的额外参数。
        
        Returns:
            加载的资源，如果加载失败则为 None。
        """
        r_type = resource_type if resource_type is not None else self._get_resource_type(path)

        if r_type == ResourceType.IMAGE:
            return self.load_image(path, use_cache=use_cache, **kwargs)
        elif r_type == ResourceType.AUDIO:
            return self.load_sound(path, use_cache=use_cache)
        elif r_type == ResourceType.JSON:
            return self.load_json(path, use_cache=use_cache, encoding=kwargs.get('encoding', 'utf-8'))
        elif r_type == ResourceType.TEXT:
            return self.load_text(path, use_cache=use_cache, encoding=kwargs.get('encoding', 'utf-8'))
        elif r_type == ResourceType.FONT:
            return self.load_font(path, size=kwargs.get('size', 16), use_cache=use_cache)
        # ANIMATION, CONFIG, ARCHIVE 等会通过 _get_resource_type 映射为 OTHER (或其他已定义类型)
        # 因此这里不需要单独处理它们，它们会进入下面的 else 分支
        else: # ResourceType.OTHER 或 r_type 为 None (如果 _get_resource_type 返回 None)
            self.logger.warning(f"load_resource: 无法加载未知或不支持的资源类型 ({r_type}) for path: {path}")
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

# 创建资源加载器实例
# resource_loader = ResourceLoader() # 实例应由 AssetManager 创建和管理


# 导出的API
__all__ = [
    'ResourceLoader',
    # 'resource_loader'
] 