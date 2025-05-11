"""
---------------------------------------------------------------
File name:                  renderer_manager.py
Author:                     Ignorant-lu
Date created:               2025/04/03
Description:                渲染器管理器，用于注册和管理不同类型的渲染器
----------------------------------------------------------------

Changed history:            
                            2025/04/03: 初始创建;
                            2025/04/17: 从PyQt迁移到PySide，更新RendererType;
----
"""

import logging
import enum
from typing import Dict, Type, Optional, Callable, Any, cast

from status.renderer.renderer_base import RendererBase

# 设置日志记录器
logger = logging.getLogger(__name__)

class RendererType(enum.Enum):
    """渲染器类型枚举"""
    NONE = 0        # 无渲染器
    PYSIDE = 1      # PySide渲染器
    PYGAME = 2      # Pygame渲染器
    OPENGL = 3      # OpenGL渲染器
    CUSTOM = 99     # 自定义渲染器

class SingletonMeta(type):
    """单例元类，确保RendererManager只有一个实例"""
    _instances = {}
    
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(SingletonMeta, cls).__call__(*args, **kwargs)
        return cls._instances[cls]

class RendererManager(metaclass=SingletonMeta):
    """渲染器管理器，用于注册和管理不同类型的渲染器"""
    
    def __init__(self):
        """初始化渲染器管理器"""
        self.renderers: Dict[RendererType, Type[RendererBase]] = {}
        self.current_type: RendererType = RendererType.NONE
        self.current_renderer: Optional[RendererBase] = None
        
        logger.info("渲染器管理器已创建")
    
    @classmethod
    def get_instance(cls) -> 'RendererManager':
        """获取RendererManager的唯一实例"""
        return cls()
    
    def register_renderer(self, renderer_type: RendererType, renderer_class: Type[RendererBase]) -> bool:
        """注册一个渲染器
        
        Args:
            renderer_type: 渲染器类型
            renderer_class: 渲染器类
            
        Returns:
            bool: 注册是否成功
        """
        if renderer_type in self.renderers:
            logger.warning(f"渲染器类型 {renderer_type} 已经注册")
            return False
        
        self.renderers[renderer_type] = renderer_class
        logger.info(f"渲染器类型 {renderer_type} 已注册")
        return True
    
    def create_renderer(self, renderer_type: RendererType, *args, **kwargs) -> Optional[RendererBase]:
        """创建一个渲染器实例
        
        Args:
            renderer_type: 渲染器类型
            *args: 传递给渲染器构造函数的位置参数
            **kwargs: 传递给渲染器构造函数的关键字参数
            
        Returns:
            Optional[RendererBase]: 渲染器实例，如果创建失败则为None
        """
        if renderer_type not in self.renderers:
            logger.error(f"渲染器类型 {renderer_type} 未注册")
            return None
        
        try:
            renderer_class = self.renderers[renderer_type]
            renderer = renderer_class()
            logger.info(f"已创建 {renderer_type} 类型的渲染器实例")
            
            self.current_type = renderer_type
            self.current_renderer = renderer
            
            return renderer
        except Exception as e:
            logger.error(f"创建渲染器实例失败: {e}")
            return None
    
    def get_renderer(self, renderer_type: RendererType) -> Optional[Type[RendererBase]]:
        """获取指定类型的渲染器类
        
        Args:
            renderer_type: 渲染器类型
            
        Returns:
            Optional[Type[RendererBase]]: 渲染器类，如果不存在则为None
        """
        return self.renderers.get(renderer_type)
    
    def get_current_renderer(self) -> Optional[RendererBase]:
        """获取当前渲染器实例
        
        Returns:
            Optional[RendererBase]: 当前渲染器实例，如果不存在则为None
        """
        return self.current_renderer
    
    def get_current_type(self) -> RendererType:
        """获取当前渲染器类型
        
        Returns:
            RendererType: 当前渲染器类型
        """
        return self.current_type 