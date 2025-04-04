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
import pygame

from .resource_pack import resource_pack_manager, ResourcePackError


class ResourceLoader:
    """资源加载器，提供简化的资源加载接口"""
    
    def __init__(self):
        """初始化资源加载器"""
        self.logger = logging.getLogger("Hollow-ming.ResourceLoader")
        
        # 资源缓存
        self._image_cache: Dict[str, pygame.Surface] = {}
        self._sound_cache: Dict[str, pygame.mixer.Sound] = {}
        self._font_cache: Dict[str, Dict[int, pygame.font.Font]] = {}
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
    
    def initialize(self) -> bool:
        """初始化资源加载器
        
        Returns:
            bool: 初始化是否成功
        """
        # 初始化资源包管理器
        return resource_pack_manager.initialize()
    
    def reload(self) -> bool:
        """重新加载所有资源
        
        Returns:
            bool: 重新加载是否成功
        """
        # 清空缓存
        self.clear_cache()
        
        # 重新加载资源包
        return resource_pack_manager.reload()
    
    def clear_cache(self) -> None:
        """清空资源缓存"""
        # 清空各类缓存
        self._image_cache.clear()
        self._sound_cache.clear()
        self._font_cache.clear()
        self._json_cache.clear()
        self._text_cache.clear()
        
        self.logger.debug("已清空资源缓存")
    
    def get_resource_path(self, resource_path: str) -> Optional[str]:
        """获取资源文件的实际路径
        
        Args:
            resource_path: 资源相对路径
            
        Returns:
            Optional[str]: 实际路径，如果不存在则返回None
        """
        return resource_pack_manager.get_resource_path(resource_path)
    
    def has_resource(self, resource_path: str) -> bool:
        """检查资源是否存在
        
        Args:
            resource_path: 资源相对路径
            
        Returns:
            bool: 资源是否存在
        """
        return resource_pack_manager.has_resource(resource_path)
    
    def get_resource_content(self, resource_path: str) -> Optional[bytes]:
        """获取资源文件内容
        
        Args:
            resource_path: 资源相对路径
            
        Returns:
            Optional[bytes]: 文件内容，如果不存在则返回None
        """
        return resource_pack_manager.get_resource_content(resource_path)
    
    def list_resources(self, prefix: str = "", resource_type: Optional[str] = None) -> List[str]:
        """列出资源
        
        Args:
            prefix: 资源路径前缀
            resource_type: 资源类型（image, sound, font, json, text）
            
        Returns:
            List[str]: 资源路径列表
        """
        resources = resource_pack_manager.list_resources(prefix)
        
        # 如果指定了资源类型，筛选对应扩展名的资源
        if resource_type and resource_type in self._registered_extensions:
            extensions = self._registered_extensions[resource_type]
            resources = [r for r in resources if any(r.lower().endswith(ext) for ext in extensions)]
        
        return resources
    
    def load_image(self, image_path: str, use_cache: bool = True) -> Optional[pygame.Surface]:
        """加载图像
        
        Args:
            image_path: 图像路径
            use_cache: 是否使用缓存
            
        Returns:
            Optional[pygame.Surface]: 图像，如果不存在则返回None
        """
        # 检查缓存
        if use_cache and image_path in self._image_cache:
            return self._image_cache[image_path]
        
        try:
            # 获取资源内容
            content = self.get_resource_content(image_path)
            
            if content is None:
                self.logger.warning(f"图像资源不存在: {image_path}")
                return None
            
            # 从内存加载图像
            image = pygame.image.load(pygame.io.BytesIO(content)).convert_alpha()
            
            # 添加到缓存
            if use_cache:
                self._image_cache[image_path] = image
            
            return image
        except Exception as e:
            self.logger.error(f"加载图像失败: {image_path}, 错误: {str(e)}")
            return None
    
    def load_sound(self, sound_path: str, use_cache: bool = True) -> Optional[pygame.mixer.Sound]:
        """加载音效
        
        Args:
            sound_path: 音效路径
            use_cache: 是否使用缓存
            
        Returns:
            Optional[pygame.mixer.Sound]: 音效，如果不存在则返回None
        """
        # 检查缓存
        if use_cache and sound_path in self._sound_cache:
            return self._sound_cache[sound_path]
        
        try:
            # 获取资源内容
            content = self.get_resource_content(sound_path)
            
            if content is None:
                self.logger.warning(f"音效资源不存在: {sound_path}")
                return None
            
            # 从内存加载音效
            sound = pygame.mixer.Sound(pygame.io.BytesIO(content))
            
            # 添加到缓存
            if use_cache:
                self._sound_cache[sound_path] = sound
            
            return sound
        except Exception as e:
            self.logger.error(f"加载音效失败: {sound_path}, 错误: {str(e)}")
            return None
    
    def load_font(self, font_path: str, size: int = 16, use_cache: bool = True) -> Optional[pygame.font.Font]:
        """加载字体
        
        Args:
            font_path: 字体路径
            size: 字体大小
            use_cache: 是否使用缓存
            
        Returns:
            Optional[pygame.font.Font]: 字体，如果不存在则返回None
        """
        # 检查缓存
        if use_cache and font_path in self._font_cache and size in self._font_cache[font_path]:
            return self._font_cache[font_path][size]
        
        try:
            # 获取资源内容
            content = self.get_resource_content(font_path)
            
            if content is None:
                self.logger.warning(f"字体资源不存在: {font_path}")
                return None
            
            # 从内存加载字体
            font_file = pygame.io.BytesIO(content)
            font = pygame.font.Font(font_file, size)
            
            # 添加到缓存
            if use_cache:
                if font_path not in self._font_cache:
                    self._font_cache[font_path] = {}
                
                self._font_cache[font_path][size] = font
            
            return font
        except Exception as e:
            self.logger.error(f"加载字体失败: {font_path}, 错误: {str(e)}")
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
    
    def load_sprite_sheet(self, image_path: str, sprite_width: int, sprite_height: int, 
                          use_cache: bool = True) -> Optional[List[pygame.Surface]]:
        """加载精灵表
        
        Args:
            image_path: 图像路径
            sprite_width: 精灵宽度
            sprite_height: 精灵高度
            use_cache: 是否使用缓存
            
        Returns:
            Optional[List[pygame.Surface]]: 精灵列表，如果不存在则返回None
        """
        try:
            # 加载原始图像
            sheet = self.load_image(image_path, use_cache)
            
            if sheet is None:
                return None
            
            # 获取尺寸
            sheet_width, sheet_height = sheet.get_size()
            
            # 计算精灵数量
            cols = sheet_width // sprite_width
            rows = sheet_height // sprite_height
            
            # 提取精灵
            sprites = []
            
            for row in range(rows):
                for col in range(cols):
                    # 计算位置
                    x = col * sprite_width
                    y = row * sprite_height
                    
                    # 提取精灵
                    sprite = sheet.subsurface((x, y, sprite_width, sprite_height))
                    sprites.append(sprite)
            
            return sprites
        except Exception as e:
            self.logger.error(f"加载精灵表失败: {image_path}, 错误: {str(e)}")
            return None
    
    def load_animation(self, base_path: str, frame_count: int, use_cache: bool = True) -> Optional[List[pygame.Surface]]:
        """加载动画
        
        Args:
            base_path: 基础路径（不含序号和扩展名）
            frame_count: 帧数
            use_cache: 是否使用缓存
            
        Returns:
            Optional[List[pygame.Surface]]: 动画帧列表，如果不存在则返回None
        """
        try:
            frames = []
            
            # 确定文件扩展名
            extensions = self._registered_extensions["image"]
            extension = None
            
            for ext in extensions:
                test_path = f"{base_path}1{ext}"
                if self.has_resource(test_path):
                    extension = ext
                    break
            
            if extension is None:
                self.logger.warning(f"找不到动画帧: {base_path}[1-{frame_count}].*")
                return None
            
            # 加载所有帧
            for i in range(1, frame_count + 1):
                frame_path = f"{base_path}{i}{extension}"
                frame = self.load_image(frame_path, use_cache)
                
                if frame is None:
                    self.logger.warning(f"动画帧不存在: {frame_path}")
                    continue
                
                frames.append(frame)
            
            if not frames:
                self.logger.warning(f"没有加载到有效的动画帧: {base_path}[1-{frame_count}]{extension}")
                return None
            
            return frames
        except Exception as e:
            self.logger.error(f"加载动画失败: {base_path}, 错误: {str(e)}")
            return None


# 创建资源加载器实例
resource_loader = ResourceLoader()


# 导出的API
__all__ = [
    'ResourceLoader',
    'resource_loader'
] 