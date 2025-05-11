"""
---------------------------------------------------------------
File name:                  resource_loader.py
Author:                     Ignorant-lu
Date created:               2025/04/03
Description:                资源加载器，提供简化的资源加载接口
----------------------------------------------------------------

Changed history:            
                            2025/04/03: 初始创建;
----
"""

import os
import json
import logging
from typing import Dict, Any, List, Optional, Union, Tuple, Set
from pathlib import Path
# 移除 pygame 的直接导入，如果其他地方不再需要
# import pygame
import io
import re

# 导入 PyQt 相关
from PyQt6.QtGui import QImage, QPixmap, QFont # 假设 QFont 也可能在 PyQt 中使用
# from PyQt6.QtMultimedia import QSoundEffect # 如果用 PyQt 加载音效

from .resource_pack import resource_pack_manager, ResourcePackError


def natural_sort_key(s):
    """为字符串生成自然排序键。例如：'frame_10.png' > 'frame_9.png'"""
    return [int(text) if text.isdigit() else text.lower()
            for text in re.split(r'(\d+)', s)]

class ResourceLoader:
    """资源加载器，提供简化的资源加载接口"""
    
    def __init__(self):
        """初始化资源加载器"""
        self.logger = logging.getLogger("Hollow-ming.ResourceLoader")
        
        # 资源缓存
        self._image_cache: Dict[str, QImage] = {}
        # self._sound_cache: Dict[str, QSoundEffect] = {} # <-- 如果用 PyQt 音效
        self._sound_cache: Dict[str, Any] = {} # 暂时保留 Any
        # self._font_cache: Dict[str, Dict[int, QFont]] = {} # <-- 如果用 PyQt 字体
        self._font_cache: Dict[str, Dict[int, Any]] = {} # 暂时保留 Any
        self._json_cache: Dict[str, Any] = {}
        self._text_cache: Dict[str, str] = {}
        
        # 已注册的资源类型与扩展名
        self._registered_extensions = {
            "image": [".png", ".jpg", ".jpeg", ".bmp", ".gif"],
            "sound": [".wav", ".ogg", ".mp3"],
            "font": [".ttf", ".otf"],
            "json": [".json"],
            "text": [".txt", ".md", ".csv"]
        }
        
        # 资源管理器实例
        self._manager = resource_pack_manager
    
    def set_manager(self, manager):
        # 运行时切换资源管理器实例，便于测试和mock
        self._manager = manager

    @property
    def manager(self):
        return getattr(self, '_manager', resource_pack_manager)

    def has_resource(self, path):
        # 如果 manager 没有 has_resource, 或者返回 False, 尝试文件系统
        if not hasattr(self.manager, 'has_resource') or not self.manager.has_resource(path):
            return Path(path).is_file()
        return True

    def get_resource_content(self, path):
        # 优先尝试 manager
        content = None
        if hasattr(self.manager, 'get_resource_content'):
             content = self.manager.get_resource_content(path)
        # 如果 manager 未提供，尝试文件系统
        if content is None:
            try:
                fs_path = Path(path).resolve()
                if fs_path.is_file():
                    with open(fs_path, 'rb') as f:
                        content = f.read()
                    if content:
                         self.logger.debug(f"通过文件系统获取内容: {path}")
                    else:
                         self.logger.warning(f"文件系统文件为空: {path}")
                         content = None # 确保空文件也返回 None
                else:
                    # logger 在 load_* 方法中处理路径无效
                    content = None
            except Exception as e:
                self.logger.error(f"从文件系统读取内容失败: {path}, 错误: {e}")
                content = None
        return content

    def clear_cache(self):
        self._image_cache.clear()
        self._sound_cache.clear()
        self._font_cache.clear()
        self._json_cache.clear()
        self._text_cache.clear()

    def reload(self):
        self.clear_cache()
        mgr = self.manager
        if hasattr(mgr, 'reload'):
            return mgr.reload()
        if hasattr(mgr, 'initialize'):
        return mgr.initialize()
        return False # 如果 manager 无相关方法
    
    def initialize(self) -> bool:
        """初始化资源加载器
        
        Returns:
            bool: 初始化是否成功
        """
        # 初始化资源包管理器
        if hasattr(self.manager, 'initialize'):
        return self.manager.initialize()
        return True # 如果 manager 无需初始化，则认为成功
    
    def get_resource_path(self, resource_path: str) -> Optional[str]:
        """获取资源文件的实际路径
        
        Args:
            resource_path: 资源相对路径
            
        Returns:
            Optional[str]: 实际路径，如果不存在则返回None
        """
        path = None
        if hasattr(self.manager, 'get_resource_path'):
            path = self.manager.get_resource_path(resource_path)
        if path is None:
            # 尝试文件系统
            fs_path = Path(resource_path).resolve()
            if fs_path.is_file():
                return str(fs_path)
        return path
    
    def list_resources(self, prefix: str = "", resource_type: Optional[str] = None) -> List[str]:
        """列出资源
        
        Args:
            prefix: 资源路径前缀
            resource_type: 资源类型（image, sound, font, json, text）
            
        Returns:
            List[str]: 资源路径列表
        """
        # 优先尝试从 ResourcePackManager 获取资源列表
        resources = []
        if hasattr(self.manager, 'list_resources'):
        resources = self.manager.list_resources(prefix)
        
        # 如果 ResourcePackManager 没有返回任何资源，尝试从文件系统扫描
        if not resources:
            self.logger.debug(f"ResourcePackManager未找到 '{prefix}' 下的资源，尝试扫描文件系统...")
            
            # -- 直接使用 prefix 作为相对路径进行扫描 --
            # 假设 prefix 是相对于当前工作目录 (CWD) 的路径
            try:
                scan_path = Path(prefix).resolve() # 获取绝对路径以确保目录存在性检查可靠
                self.logger.debug(f"尝试扫描绝对路径: '{scan_path}'")
                
                if scan_path.is_dir():
                    self.logger.debug(f"正在扫描目录: {scan_path}")
                    fs_resources = []
                    for item in scan_path.iterdir():
                        if item.is_file():
                            # 使用传入的 prefix 的原始形式（相对路径）来表示资源
                            # 路径拼接：prefix + 文件名
                            try:
                                relative_file_path = Path(prefix) / item.name
                                # 统一路径分隔符
                                resource_path = str(relative_file_path).replace("\\", "/")
                                fs_resources.append(resource_path)
                            except Exception as e_rel: # 改为通用 Exception
                                self.logger.warning(f"处理文件路径 '{item}' 时出错: {e_rel}")
                    
                    if fs_resources:
                        self.logger.info(f"在文件系统 '{scan_path}' 中找到 {len(fs_resources)} 个文件。")
                        resources = fs_resources # 使用文件系统找到的资源列表
                    else:
                        self.logger.debug(f"文件系统扫描未在 '{scan_path}' 找到任何文件。")
                else:
                     self.logger.debug(f"文件系统路径 '{scan_path}' ('{prefix}') 不是一个有效目录。") # 添加原始 prefix

            except Exception as e:
                self.logger.error(f"扫描文件系统目录 '{prefix}' 时出错: {e}")

        # -- 文件系统扫描结束 --

        # 如果指定了资源类型，筛选对应扩展名的资源
        if resource_type and resource_type in self._registered_extensions:
            extensions = self._registered_extensions[resource_type]
            filtered_resources = [r for r in resources if any(r.lower().endswith(ext) for ext in extensions)]
            return filtered_resources # 返回筛选后的列表
        
        return resources # 返回原始列表（可能来自manager或文件系统）
    
    def load_image(self, image_path: str, use_cache: bool = True) -> Optional[QImage]:
        """加载图像为 QImage 对象。
        
        Args:
            image_path: 图像路径
            use_cache: 是否使用缓存
            
        Returns:
            Optional[QImage]: QImage 对象，如果不存在或加载失败则返回None
        """
        # 检查缓存
        if use_cache and image_path in self._image_cache:
            return self._image_cache[image_path]
        
        try:
            # 获取资源内容 (已包含文件系统回退)
            content = self.get_resource_content(image_path)
            
            # 如果最终没有获取到内容，则资源不存在
            if content is None:
                self.logger.warning(f"图像资源不存在或无法读取: {image_path}")
                return None
            
            # --- 使用 PyQt 加载图像 ---
            qimage = QImage()
            # loadFromData 可以根据内容自动判断格式 (PNG, JPG etc.)
            if qimage.loadFromData(content):
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
            self.logger.error(f"加载图像时发生意外错误: {image_path}, 错误: {str(e)}")
            return None
    
    def load_sound(self, sound_path: str, use_cache: bool = True) -> Optional[Any]:
        """加载音效 (当前仍使用 Pygame)
        
        Args:
            sound_path: 音效路径
            use_cache: 是否使用缓存
            
        Returns:
            Optional[Any]: 音效，如果不存在则返回None
        """
        # 检查缓存
        if use_cache and sound_path in self._sound_cache:
            return self._sound_cache[sound_path]
        try:
            import pygame # 延迟导入
            pygame.mixer.init() # 确保 mixer 初始化
            content = self.get_resource_content(sound_path)
            if content is None: return None
            sound = pygame.mixer.Sound(io.BytesIO(content))
            if use_cache: self._sound_cache[sound_path] = sound
            return sound
        except Exception as e:
            self.logger.error(f"加载音效(pygame)失败: {sound_path}, {e}")
            return None
    
    def load_font(self, font_path: str, size: int = 16, use_cache: bool = True) -> Optional[Any]:
        """加载字体 (当前仍使用 Pygame)"""
        # 检查缓存 - 使用 font_path 作为主键，size 作为次级键
        if use_cache and font_path in self._font_cache and size in self._font_cache[font_path]:
            return self._font_cache[font_path][size]
        
        # cache_key = (font_path, size) # 不再使用元组键
        # if use_cache and cache_key in self._font_cache: # 旧的错误检查方式
        #    return self._font_cache[cache_key]
        try:
            import pygame # 延迟导入
            pygame.font.init() # 确保 font 初始化
            content = self.get_resource_content(font_path)
            if content is None: return None
            font_file = io.BytesIO(content)
            font = pygame.font.Font(font_file, size)
            
            # 写入缓存 - 遵循 Dict[str, Dict[int, Any]] 结构
            if use_cache:
                if font_path not in self._font_cache:
                    self._font_cache[font_path] = {}
                self._font_cache[font_path][size] = font # 正确写入嵌套字典
                
            # if use_cache: self._font_cache[cache_key] = font # 旧的错误写入方式
            return font
        except Exception as e:
            self.logger.error(f"加载字体(pygame)失败: {font_path} size {size}, {e}")
            return None
    
    def load_json(self, json_path: str, use_cache: bool = True) -> Optional[Dict[str, Any]]:
        """加载JSON
        
        Args:
            json_path: JSON路径
            use_cache: 是否使用缓存
            
        Returns:
            Optional[Dict[str, Any]]: JSON数据，如果不存在则返回None
        """
        # 检查缓存
        if use_cache and json_path in self._json_cache:
            return self._json_cache[json_path]
        
        try:
            # 获取资源内容
            content = self.get_resource_content(json_path)
            
            if content is None:
                self.logger.warning(f"JSON资源不存在: {json_path}")
                return None
            
            # 解析JSON
            data = json.loads(content.decode("utf-8"))
            
            # 添加到缓存
            if use_cache:
                self._json_cache[json_path] = data
            
            return data
        except Exception as e:
            self.logger.error(f"加载JSON失败: {json_path}, 错误: {str(e)}")
            return None
    
    def load_text(self, text_path: str, encoding: str = "utf-8", use_cache: bool = True) -> Optional[str]:
        """加载文本
        
        Args:
            text_path: 文本路径
            encoding: 文本编码
            use_cache: 是否使用缓存
            
        Returns:
            Optional[str]: 文本内容，如果不存在则返回None
        """
        # 检查缓存
        if use_cache and text_path in self._text_cache:
            return self._text_cache[text_path]
        
        try:
            # 获取资源内容
            content = self.get_resource_content(text_path)
            
            if content is None:
                self.logger.warning(f"文本资源不存在: {text_path}")
                return None
            
            # 解码文本
            text = content.decode(encoding)
            
            # 添加到缓存
            if use_cache:
                self._text_cache[text_path] = text
            
            return text
        except Exception as e:
            self.logger.error(f"加载文本失败: {text_path}, 错误: {str(e)}")
            return None
    
    def load_image_sequence(self, directory_path: str, use_cache: bool = True) -> Optional[List[QImage]]:
        """加载指定目录下的所有图像文件作为一个动画序列 (QImage 列表)。
        
        Args:
            directory_path (str): 包含图像序列的目录路径 (相对于资源根目录)。
            use_cache (bool, optional): 是否使用或填充图像缓存. Defaults to True.
            
        Returns:
            Optional[List[QImage]]: 加载的 QImage 列表，按自然顺序排序。
                                        如果目录不存在或加载失败，返回 None。
        """
        self.logger.info(f"尝试加载 QImage 序列: {directory_path}")
        try:
            image_paths = self.list_resources(prefix=directory_path, resource_type='image')
            if not image_paths:
                self.logger.warning(f"在目录 '{directory_path}' 中未找到图像文件。")
                return None
            
            # 按自然顺序排序文件名
            image_paths.sort(key=natural_sort_key)
            
            frames: List[QImage] = []
            for img_path in image_paths:
                # 调用修改后的 load_image，它返回 QImage
                frame = self.load_image(img_path, use_cache=use_cache)
                if frame and not frame.isNull(): # 检查 QImage 是否有效
                    frames.append(frame)
                else:
                    # 如果单个帧加载失败，中止
                    self.logger.error(f"加载序列 '{directory_path}' 中的帧 '{img_path}' 失败，序列加载中止。")
                return None
            
            if frames:
                self.logger.info(f"成功加载 QImage 序列: {directory_path}, 共 {len(frames)} 帧")
                return frames
            else:
                self.logger.warning(f"加载 QImage 序列 '{directory_path}' 失败，未成功加载任何帧。")
                return None
            
        except Exception as e:
            self.logger.exception(f"加载 QImage 序列 '{directory_path}' 时发生意外错误: {e}")
            return None


# 创建资源加载器实例
# resource_loader = ResourceLoader() # 实例应由 AssetManager 创建和管理


# 导出的API
__all__ = [
    'ResourceLoader',
    # 'resource_loader'
] 