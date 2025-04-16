"""
---------------------------------------------------------------
File name:                  __init__.py
Author:                     Ignorant-lu
Date created:               2025/04/03
Description:                资源管理模块，提供资源包和加载功能
----------------------------------------------------------------

Changed history:            
                            2025/04/03: 初始创建;
                            2025/04/05: 添加ResourceType枚举;
                            2025/04/05: 添加ResourceError和ImageFormat;
----
"""

from enum import Enum, auto

class ResourceType(Enum):
    """资源类型枚举"""
    IMAGE = "image"
    SOUND = "sound"
    FONT = "font"
    JSON = "json"
    TEXT = "text"
    SPRITE_SHEET = "sprite_sheet"
    ANIMATION = "animation"
    AUDIO = "audio"  # 音频类型，与SOUND兼容
    OTHER = "other"  # 其他类型

class ImageFormat(Enum):
    """图像格式枚举"""
    PNG = "png"
    JPG = "jpg"
    BMP = "bmp"
    GIF = "gif"
    WEBP = "webp"
    AUTO = "auto"  # 自动检测

class ResourceError(Exception):
    """资源操作异常基类"""
    def __init__(self, message: str):
        self.message = message
        super().__init__(message)

from .resource_pack import (
    ResourcePack, ResourcePackManager, ResourcePackError,
    ResourcePackLoadError, ResourcePackValidationError,
    ResourcePackType, ResourcePackFormat, ResourcePackMetadata,
    resource_pack_manager
)

# 只导入类，不导入实例
from .resource_loader import ResourceLoader

# --- 缓存相关 --- (假设 cache.py 只定义类)
from .cache import Cache, CacheStrategy, CacheItemStatus


# 导出的API
__all__ = [
    # 资源类型
    'ResourceType',
    'ImageFormat',
    'ResourceError',
    
    # 资源包相关
    'ResourcePack',
    'ResourcePackManager',
    'ResourcePackError',
    'ResourcePackLoadError',
    'ResourcePackValidationError',
    'ResourcePackType',
    'ResourcePackFormat',
    'ResourcePackMetadata',
    'resource_pack_manager',
    
    # 资源加载器相关
    'ResourceLoader',
    
    # 缓存相关
    'Cache',
    'CacheStrategy',
    'CacheItemStatus'
]