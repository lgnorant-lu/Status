"""
---------------------------------------------------------------
File name:                  __init__.py
Author:                     Ignorant-lu
Date created:               2025/04/03
Description:                资源管理模块，提供资源包和加载功能
----------------------------------------------------------------

Changed history:            
                            2025/04/03: 初始创建;
----
"""

from .resource_pack import (
    ResourcePack, ResourcePackManager, ResourcePackError,
    ResourcePackLoadError, ResourcePackValidationError,
    ResourcePackType, ResourcePackFormat, ResourcePackMetadata,
    resource_pack_manager
)

from .resource_loader import ResourceLoader, resource_loader


# 导出的API
__all__ = [
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
    'resource_loader'
]