"""
---------------------------------------------------------------
File name:                  resource_loader.py
Author:                     Ignorant-lu
Date created:               2025/04/04
Description:                资源加载工具模块
----------------------------------------------------------------

Changed history:            
                            2025/04/04: 初始创建;
----
"""

import os
import re
import json
import logging
import importlib.util
from pathlib import Path
from typing import Dict, Any, List, Optional, Union, Set, Tuple
from functools import lru_cache

# 尝试导入PySide6相关模块
try:
    from PySide6.QtGui import QImage, QPixmap, QFont, QFontDatabase # 假设 QFont 也可能在 PySide 中使用
    # from PySide6.QtMultimedia import QSoundEffect # 如果用 PySide 加载音效
    HAS_GUI = True
except ImportError:
    HAS_GUI = False

# 配置日志
logger = logging.getLogger(__name__)

def natural_sort_key(s):
    """用于文件的自然排序 (如 frame1.png, frame2.png, ..., frame10.png)"""
    return [int(c) if c.isdigit() else c.lower() for c in re.split(r'(\d+)', str(s))]

class ResourceLoader:
    """资源加载类，提供统一的资源加载接口"""
    
    def __init__(self):
        """初始化资源加载器"""
        self.logger = logging.getLogger("Status.ResourceLoader")
        self._manager = None # 资源管理器实例，如 ResourcePackManager
        
        # 缓存
        self._image_cache = {}      # 图像缓存
        self._sound_cache = {}      # 音效缓存
        self._font_cache = {}       # 字体缓存
        self._json_cache = {}       # JSON数据缓存
        self._text_cache = {}       # 文本缓存
        
        # 缓存控制
        self._max_image_cache = 100  # 最大图像缓存数量
        self._max_sound_cache = 50   # 最大音效缓存数量
        self._max_font_cache = 20    # 最大字体缓存数量
        self._max_json_cache = 50    # 最大JSON缓存数量
        self._max_text_cache = 50    # 最大文本缓存数量
        
        # 加载默认资源包管理器
        self._load_default_manager()
    
    def _load_default_manager(self):
        """尝试加载默认的资源管理器"""
        try:
            # 尝试导入资源包管理器
            from status.resources.resource_pack import ResourcePackManager
            self._manager = ResourcePackManager.get_instance()
            self.logger.info("已加载ResourcePackManager作为默认资源管理器")
        except ImportError:
            self.logger.warning("无法加载ResourcePackManager，将使用文件系统作为备选")
            self._manager = None
    
    def set_manager(self, manager):
        # 运行时切换资源管理器实例，便于测试和mock
        self._manager = manager

    @property
    def manager(self):
        return self._manager

    def has_resource(self, path):
        # 如果 manager 没有 has_resource, 或者返回 False, 尝试文件系统
        mgr = self.manager
        if mgr and hasattr(mgr, 'has_resource') and mgr.has_resource(path):
            return True
        return os.path.exists(path)

    def get_resource_content(self, path):
        # 优先尝试 manager
        mgr = self.manager
        content = None
        
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

    def clear_cache(self):
        """清空所有缓存"""
        self._image_cache.clear()
        self._sound_cache.clear()
        self._font_cache.clear()
        self._json_cache.clear()
        self._text_cache.clear()

    def reload(self):
        """重新加载资源管理器并清空缓存"""
        mgr = self.manager
        self.clear_cache()
        if mgr and hasattr(mgr, 'reload'):
            return mgr.reload()
        if mgr and hasattr(mgr, 'initialize'):
            return mgr.initialize()
        return False # 如果 manager 无相关方法
    
    def initialize(self) -> bool:
        """初始化资源加载器
        
        Returns:
            bool: 是否初始化成功
        """
        # 初始化资源包管理器
        if self.manager and hasattr(self.manager, 'initialize'):
            return self.manager.initialize()
        return True # 如果 manager 无需初始化，则认为成功
    
    def get_resource_path(self, resource_path: str) -> Optional[str]:
        """获取资源的实际文件系统路径
        
        如果资源位于资源包中，则返回资源包内的文件路径
        如果资源位于文件系统中，则返回原路径
        
        Args:
            resource_path: 资源路径
            
        Returns:
            str: 资源的实际文件系统路径，或None（如果资源不存在）
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
        resources = []
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
    
    def load_image(self, image_path: str, use_cache: bool = True) -> Optional[QImage]:
        """加载图像资源
        
        Args:
            image_path: 图像资源路径
            use_cache: 是否使用缓存
            
        Returns:
            QImage: 加载的图像对象，或None（如果加载失败）
        """
        if not HAS_GUI:
            self.logger.error("QImage未导入，无法加载图像")
            return None
        
        # 如果启用缓存且已在缓存中，直接返回
        if use_cache and image_path in self._image_cache:
            return self._image_cache[image_path]
        
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
                    # 加载成功
                    # 通常不需要 convert_alpha，QImage 会保留透明度
                    if use_cache:
                        self._image_cache[image_path] = qimage
                    return qimage
                else:
                    # 加载失败
                    self.logger.error(f"使用 QImage.loadFromData 加载图像失败: {image_path}")
                    return None
            
            except Exception as e:
                self.logger.error(f"处理图像数据时出错: {e}")
                return None
            
        # 尝试从文件路径加载
        try:
            qimage = QImage(real_path)
            
            if qimage.isNull():
                self.logger.error(f"加载图像失败: {real_path}")
                return None
                
            # 加载成功
            if use_cache:
                self._image_cache[image_path] = qimage
                
            return qimage
            
        except Exception as e:
            self.logger.error(f"加载图像时出错: {e}")
            return None
    
    def load_sound(self, sound_path: str, use_cache: bool = True) -> Optional[Any]:
        """加载音效资源
        
        Args:
            sound_path: 音效资源路径
            use_cache: 是否使用缓存
            
        Returns:
            Any: 加载的音效对象，或None（如果加载失败）
        """
        # 实际实现等待添加 QSoundEffect 或其他音效引擎
        self.logger.warning("音效加载功能尚未实现")
    
    def load_font(self, font_path: str, size: int = 16, use_cache: bool = True) -> Optional[Any]:
        """加载字体资源
        
        Args:
            font_path: 字体资源路径
            size: 字体大小
            use_cache: 是否使用缓存
            
        Returns:
            QFont: 加载的字体对象，或None（如果加载失败）
        """
        if not HAS_GUI:
            self.logger.error("QFont未导入，无法加载字体")
            return None
            
        # 缓存键包含字体路径和大小
        cache_key = f"{font_path}_{size}"
        
        # 如果启用缓存且已在缓存中，直接返回
        if use_cache and cache_key in self._font_cache:
            return self._font_cache[cache_key]
        
        # 获取资源实际路径
        real_path = self.get_resource_path(font_path)
            
        if not real_path:
            self.logger.error(f"找不到字体: {font_path}")
            return None
            
        # 尝试加载字体
        try:
            font = QFont()
            font_database = QFontDatabase()
            
            # 从文件加载字体
            font_id = font_database.addApplicationFont(real_path)
            
            if font_id != -1:
                # 获取字体族名称
                font_families = font_database.applicationFontFamilies(font_id)
                if font_families:
                    font.setFamily(font_families[0])
                    font.setPointSize(size)
            else:
                # 如果 addApplicationFont 失败，尝试使用系统字体作为后备
                font.setFamily("Arial") # 或者其他通用的后备字体
                font.setPointSize(size)
                self.logger.warning(f"无法通过 addApplicationFont 加载字体 {real_path}，使用后备字体 Arial")
            
            # 加入缓存
            if use_cache:
                self._font_cache[cache_key] = font
            
            return font
            
        except Exception as e:
            self.logger.error(f"加载字体时出错: {e}")
            return None
    
    def load_json(self, json_path: str, use_cache: bool = True) -> Optional[Dict[str, Any]]:
        """加载JSON资源
        
        Args:
            json_path: JSON资源路径
            use_cache: 是否使用缓存
            
        Returns:
            Dict[str, Any]: 解析后的JSON数据，或None（如果加载失败）
        """
        # 如果启用缓存且已在缓存中，直接返回
        if use_cache and json_path in self._json_cache:
            return self._json_cache[json_path]
        
        # 先尝试加载文本内容
        text_content = self.load_text(json_path, use_cache=False) # 重命名以避免与内置text冲突
            
        if not text_content:
            self.logger.error(f"无法加载JSON文件内容: {json_path}")
            return None
            
        # 解析JSON
        try:
            data = json.loads(text_content)
            
            # 加入缓存
            if use_cache:
                self._json_cache[json_path] = data
            
            return data
            
        except json.JSONDecodeError as e:
            self.logger.error(f"解析JSON时出错: {json_path}, {e}")
            return None
    
    def load_text(self, text_path: str, encoding: str = "utf-8", use_cache: bool = True) -> Optional[str]:
        """加载文本资源
        
        Args:
            text_path: 文本资源路径
            encoding: 文本编码
            use_cache: 是否使用缓存
            
        Returns:
            str: 加载的文本内容，或None（如果加载失败）
        """
        # 如果启用缓存且已在缓存中，直接返回
        cache_key = f"{text_path}_{encoding}"
        if use_cache and cache_key in self._text_cache:
            return self._text_cache[cache_key]
        
        # 获取资源二进制内容
        binary_content = self.get_resource_content(text_path)
            
        if not binary_content:
            self.logger.error(f"找不到文本文件: {text_path}")
            return None
            
        # 尝试解码文本
        try:
            decoded_text = binary_content.decode(encoding)
            
            # 加入缓存
            if use_cache:
                self._text_cache[cache_key] = decoded_text
            
            return decoded_text
            
        except UnicodeDecodeError as e:
            self.logger.error(f"解码文本文件时出错: {text_path}, {e}")
            return None
    
    def load_image_sequence(self, directory_path: str, use_cache: bool = True) -> Optional[List[QImage]]:
        """加载图像序列
        
        Args:
            directory_path: 包含图像序列的目录路径
            use_cache: 是否使用缓存
            
        Returns:
            List[QImage]: 图像序列，或None（如果加载失败）
        """
        if not HAS_GUI:
            self.logger.error("QImage未导入，无法加载图像序列")
            return None
            
        # 列出目录中的图像资源
        image_files = self.list_resources(directory_path, resource_type="image")
        
        if not image_files:
            self.logger.error(f"未找到图像序列: {directory_path}")
            return None
    
        # 加载并排序图像
        images = []
        for image_file in sorted(image_files, key=natural_sort_key):
            # 构建完整路径
            if directory_path.endswith("/") or directory_path.endswith("\\"):
                image_path = f"{directory_path}{image_file}"
            else:
                image_path = f"{directory_path}/{image_file}"
                
            # 加载图像
            image = self.load_image(image_path, use_cache=use_cache)
            if image:
                images.append(image)
            
        if not images:
            self.logger.error(f"图像序列加载失败: {directory_path}")
            return None
            
        self.logger.info(f"已加载图像序列，共 {len(images)} 帧，来自 {directory_path}")
        return images


# 创建资源加载器实例
# resource_loader = ResourceLoader() # 实例应由 AssetManager 创建和管理


# 导出的API
__all__ = [
    'ResourceLoader',
    # 'resource_loader'
] 