"""
---------------------------------------------------------------
File name:                  resource_loader.py
Author:                     Ignorant-lu
Date created:               2025/04/03
Description:                资源加载器，负责加载不同类型的资源文件
----------------------------------------------------------------

Changed history:            
                            2025/04/03: 初始创建;
                            2025/04/03: 实现图像加载功能;
----
"""

import os
import json
import yaml
import logging
from typing import Dict, Any, Optional, List, Union, Tuple, BinaryIO
from enum import Enum, auto

# 第三方库导入
try:
    from PyQt6.QtGui import QImage, QPixmap, QFont
    from PyQt6.QtCore import QBuffer, QIODevice
    HAS_PYQT = True
except ImportError:
    # 定义空的类型占位符，用于类型注解
    class QImage: pass
    class QPixmap: pass
    class QFont: pass
    class QBuffer: pass
    class QIODevice: pass
    HAS_PYQT = False

class ResourceType(Enum):
    """资源类型枚举"""
    IMAGE = auto()          # 图像资源
    SOUND = auto()          # 音效资源
    MUSIC = auto()          # 音乐资源
    FONT = auto()           # 字体资源
    DATA = auto()           # 数据资源（JSON、YAML等）
    TEXT = auto()           # 文本资源
    ANIMATION = auto()      # 动画资源
    OTHER = auto()          # 其他类型资源

class ResourceLoadError(Exception):
    """资源加载错误"""
    pass

class ResourceLoader:
    """资源加载器，负责加载不同类型的资源文件"""
    
    def __init__(self, base_path: str = ""):
        """初始化资源加载器
        
        Args:
            base_path: 资源基础路径
        """
        self.logger = logging.getLogger("Hollow-ming.Core.ResourceLoader")
        self.base_path = base_path
        self.supported_extensions = {
            ResourceType.IMAGE: ['.png', '.jpg', '.jpeg', '.bmp', '.gif'],
            ResourceType.SOUND: ['.wav', '.ogg', '.mp3'],
            ResourceType.MUSIC: ['.mp3', '.ogg', '.wav'],
            ResourceType.FONT: ['.ttf', '.otf'],
            ResourceType.DATA: ['.json', '.yaml', '.yml'],
            ResourceType.TEXT: ['.txt', '.md'],
            ResourceType.ANIMATION: ['.json', '.sprite']
        }
        self._loaders = {
            ResourceType.IMAGE: self._load_image,
            ResourceType.SOUND: self._load_sound,
            ResourceType.MUSIC: self._load_music,
            ResourceType.FONT: self._load_font,
            ResourceType.DATA: self._load_data,
            ResourceType.TEXT: self._load_text,
            ResourceType.ANIMATION: self._load_animation,
            ResourceType.OTHER: self._load_binary
        }
        self.logger.info("资源加载器初始化完成")
    
    def set_base_path(self, base_path: str) -> None:
        """设置资源基础路径
        
        Args:
            base_path: 资源基础路径
        """
        self.base_path = base_path
        self.logger.debug(f"设置资源基础路径: {base_path}")
    
    def get_resource_type(self, file_path: str) -> ResourceType:
        """根据文件扩展名确定资源类型
        
        Args:
            file_path: 文件路径
            
        Returns:
            ResourceType: 资源类型
        """
        _, ext = os.path.splitext(file_path.lower())
        
        for res_type, extensions in self.supported_extensions.items():
            if ext in extensions:
                return res_type
                
        return ResourceType.OTHER
    
    def get_supported_extensions(self) -> Dict[ResourceType, List[str]]:
        """获取支持的文件扩展名
        
        Returns:
            Dict[ResourceType, List[str]]: 资源类型及其支持的扩展名字典
        """
        return self.supported_extensions
    
    def scan_directory(self, directory: str, recursive: bool = True) -> Dict[ResourceType, List[str]]:
        """扫描目录中的资源文件
        
        Args:
            directory: 要扫描的目录
            recursive: 是否递归扫描子目录
            
        Returns:
            Dict[ResourceType, List[str]]: 按资源类型分组的文件路径
            
        Raises:
            ResourceLoadError: 目录不存在或无法访问时抛出
        """
        full_path = os.path.join(self.base_path, directory)
        
        if not os.path.exists(full_path):
            error_msg = f"目录不存在: {full_path}"
            self.logger.error(error_msg)
            raise ResourceLoadError(error_msg)
        
        if not os.path.isdir(full_path):
            error_msg = f"路径不是目录: {full_path}"
            self.logger.error(error_msg)
            raise ResourceLoadError(error_msg)
        
        result = {res_type: [] for res_type in ResourceType}
        
        try:
            if recursive:
                for root, _, files in os.walk(full_path):
                    for file in files:
                        file_path = os.path.join(root, file)
                        rel_path = os.path.relpath(file_path, self.base_path)
                        res_type = self.get_resource_type(file)
                        result[res_type].append(rel_path)
            else:
                for item in os.listdir(full_path):
                    item_path = os.path.join(full_path, item)
                    if os.path.isfile(item_path):
                        rel_path = os.path.relpath(item_path, self.base_path)
                        res_type = self.get_resource_type(item)
                        result[res_type].append(rel_path)
        except Exception as e:
            error_msg = f"扫描目录失败: {full_path}, 错误: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            raise ResourceLoadError(error_msg) from e
        
        return result
    
    def load(self, path: str, res_type: Optional[ResourceType] = None, **kwargs) -> Any:
        """加载资源
        
        Args:
            path: 资源路径
            res_type: 资源类型，如果为None则自动根据扩展名判断
            **kwargs: 传递给具体加载函数的额外参数
            
        Returns:
            加载的资源对象
            
        Raises:
            ResourceLoadError: 资源加载失败时抛出
        """
        # 组合完整路径
        full_path = os.path.join(self.base_path, path)
        
        # 检查文件是否存在
        if not os.path.exists(full_path):
            error_msg = f"资源文件不存在: {full_path}"
            self.logger.error(error_msg)
            raise ResourceLoadError(error_msg)
        
        # 确定资源类型
        if res_type is None:
            res_type = self.get_resource_type(path)
        
        self.logger.debug(f"加载资源: {path}, 类型: {res_type.name}")
        
        try:
            # 调用对应的加载函数
            return self._loaders[res_type](full_path, **kwargs)
        except Exception as e:
            error_msg = f"加载资源失败: {path}, 错误: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            raise ResourceLoadError(error_msg) from e
    
    def _load_image(self, path: str, **kwargs) -> Union[QImage, Dict]:
        """加载图像资源
        
        使用PyQt6加载图像，如果PyQt6不可用则返回占位数据
        
        Args:
            path: 图像文件路径
            **kwargs: 额外参数
                as_pixmap (bool): 是否返回QPixmap而不是QImage
                scale_width (int): 缩放到指定宽度
                scale_height (int): 缩放到指定高度
            
        Returns:
            QImage: 图像对象，如果PyQt6不可用则返回占位字典
        """
        if not HAS_PYQT:
            self.logger.warning(f"PyQt6未安装，无法加载图像: {path}")
            return {"path": path, "type": "image", "loaded": False, "error": "PyQt6未安装"}
        
        try:
            # 加载图像
            image = QImage(path)
            
            if image.isNull():
                raise ResourceLoadError(f"无法加载图像: {path}")
            
            # 缩放处理
            scale_width = kwargs.get('scale_width')
            scale_height = kwargs.get('scale_height')
            
            if scale_width and scale_height:
                image = image.scaled(scale_width, scale_height)
            elif scale_width:
                # 保持宽高比
                ratio = image.height() / image.width()
                image = image.scaled(scale_width, int(scale_width * ratio))
            elif scale_height:
                # 保持宽高比
                ratio = image.width() / image.height()
                image = image.scaled(int(scale_height * ratio), scale_height)
            
            # 是否返回QPixmap
            if kwargs.get('as_pixmap', False):
                return QPixmap.fromImage(image)
            
            return image
        except Exception as e:
            self.logger.error(f"加载图像失败: {path}", exc_info=True)
            raise ResourceLoadError(f"加载图像失败: {path}, 错误: {str(e)}") from e
    
    def _load_sound(self, path: str, **kwargs) -> Any:
        """加载音效资源
        
        暂时返回占位数据，将在音频库实现后更新
        
        Args:
            path: 音效文件路径
            **kwargs: 额外参数
            
        Returns:
            音效对象（或占位数据）
        """
        self.logger.info(f"音效加载将在实际实现中完成: {path}")
        return {"path": path, "type": "sound", "loaded": True}
    
    def _load_music(self, path: str, **kwargs) -> Any:
        """加载音乐资源
        
        暂时返回占位数据，将在音频库实现后更新
        
        Args:
            path: 音乐文件路径
            **kwargs: 额外参数
            
        Returns:
            音乐对象（或占位数据）
        """
        self.logger.info(f"音乐加载将在实际实现中完成: {path}")
        return {"path": path, "type": "music", "loaded": True}
    
    def _load_font(self, path: str, size: int = 12, **kwargs) -> Union[QFont, Dict]:
        """加载字体资源
        
        使用PyQt6加载字体，如果PyQt6不可用则返回占位数据
        
        Args:
            path: 字体文件路径
            size: 字体大小
            **kwargs: 额外参数
            
        Returns:
            QFont: 字体对象，如果PyQt6不可用则返回占位字典
        """
        if not HAS_PYQT:
            self.logger.warning(f"PyQt6未安装，无法加载字体: {path}")
            return {"path": path, "type": "font", "size": size, "loaded": False, "error": "PyQt6未安装"}
        
        try:
            font = QFont()
            font_loaded = font.family() != ""
            
            if not font_loaded:
                font_id = QFont.addApplicationFont(path)
                if font_id == -1:
                    self.logger.warning(f"字体加载失败: {path}")
                    return {"path": path, "type": "font", "size": size, "loaded": False, "error": "字体加载失败"}
                
                font_families = QFont.applicationFontFamilies(font_id)
                if not font_families:
                    self.logger.warning(f"无法获取字体族: {path}")
                    return {"path": path, "type": "font", "size": size, "loaded": False, "error": "无法获取字体族"}
                
                font = QFont(font_families[0])
            
            font.setPointSize(size)
            
            # 应用额外参数
            if kwargs.get('bold', False):
                font.setBold(True)
            if kwargs.get('italic', False):
                font.setItalic(True)
            if kwargs.get('underline', False):
                font.setUnderline(True)
            
            return font
        except Exception as e:
            self.logger.error(f"加载字体失败: {path}", exc_info=True)
            return {"path": path, "type": "font", "size": size, "loaded": False, "error": str(e)}
    
    def _load_data(self, path: str, **kwargs) -> Dict[str, Any]:
        """加载数据资源（JSON或YAML）
        
        Args:
            path: 数据文件路径
            **kwargs: 额外参数
            
        Returns:
            Dict: 解析后的数据
        """
        _, ext = os.path.splitext(path.lower())
        
        with open(path, 'r', encoding='utf-8') as f:
            if ext in ['.json']:
                return json.load(f)
            elif ext in ['.yaml', '.yml']:
                return yaml.safe_load(f)
            else:
                error_msg = f"不支持的数据文件格式: {ext}"
                self.logger.error(error_msg)
                raise ResourceLoadError(error_msg)
    
    def _load_text(self, path: str, **kwargs) -> str:
        """加载文本资源
        
        Args:
            path: 文本文件路径
            **kwargs: 额外参数
                encoding: 文件编码，默认为utf-8
            
        Returns:
            str: 文本内容
        """
        encoding = kwargs.get('encoding', 'utf-8')
        
        with open(path, 'r', encoding=encoding) as f:
            return f.read()
    
    def _load_animation(self, path: str, **kwargs) -> Dict[str, Any]:
        """加载动画资源
        
        暂时返回占位数据，将在动画系统实现后更新
        
        Args:
            path: 动画文件路径
            **kwargs: 额外参数
            
        Returns:
            Dict: 动画数据（或占位数据）
        """
        self.logger.info(f"动画加载将在实际实现中完成: {path}")
        return {"path": path, "type": "animation", "loaded": True}
    
    def _load_binary(self, path: str, **kwargs) -> bytes:
        """加载二进制资源
        
        Args:
            path: 二进制文件路径
            **kwargs: 额外参数
            
        Returns:
            bytes: 二进制数据
        """
        with open(path, 'rb') as f:
            return f.read() 