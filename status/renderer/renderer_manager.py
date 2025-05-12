"""
---------------------------------------------------------------
File name:                  renderer_manager.py
Author:                     Ignorant-lu
Date created:               2025/04/03
Description:                渲染器管理器，管理多个渲染器实例
----------------------------------------------------------------

Changed history:            
                            2025/04/03: 初始创建;
                            2025/05/15: 添加类型注解;
----
"""

import logging
from typing import Dict, Optional, List, Any, Type, cast, Union
from enum import Enum, auto

from status.renderer.renderer_base import RendererBase, RenderLayer
from status.renderer.pyside_renderer import PySideRenderer

# 创建RendererType枚举类
class RendererType(str, Enum):
    """渲染器类型枚举"""
    PYSIDE = "pyside"  # PySide渲染器
    PYGAME = "pygame"  # Pygame渲染器
    OPENGL = "opengl"  # OpenGL渲染器
    MOCK = "mock"      # 模拟渲染器（用于测试）

# 设置日志记录器
logger = logging.getLogger(__name__)

class RendererManager:
    """渲染器管理器，负责管理多个渲染器实例"""
    
    _instance = None
    _initialized: bool = False
    
    @classmethod
    def get_instance(cls) -> 'RendererManager':
        """获取单例实例"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def __new__(cls, *args, **kwargs) -> 'RendererManager':
        """创建单例实例"""
        if cls._instance is None:
            cls._instance = super(RendererManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self) -> None:
        """初始化渲染器管理器"""
        # 单例模式只初始化一次
        if self._initialized:
            return
            
        self.logger = logging.getLogger(__name__)
        self.logger.info("初始化渲染器管理器")
        
        # 渲染器字典，存储不同类型的渲染器实例
        self.renderers: Dict[str, RendererBase] = {}
        
        # 默认渲染器
        self.default_renderer: Optional[RendererBase] = None
        
        self._initialized = True
    
    def register_renderer(self, name: Union[str, RendererType], renderer: Type[RendererBase]) -> bool:
        """注册渲染器
        
        Args:
            name: 渲染器名称或类型
            renderer: 渲染器类
            
        Returns:
            bool: 是否注册成功
        """
        # 转换枚举值为字符串
        renderer_name = name.value if isinstance(name, RendererType) else name
        
        if renderer_name in self.renderers:
            self.logger.warning(f"渲染器 '{renderer_name}' 已存在，将被覆盖")
        
        # 实例化渲染器类
        renderer_instance = renderer()
        self.renderers[renderer_name] = renderer_instance
        
        # 如果还没有默认渲染器，将此渲染器设为默认
        if self.default_renderer is None:
            self.default_renderer = renderer_instance
            self.logger.info(f"将 '{renderer_name}' 设为默认渲染器")
            
        self.logger.info(f"已注册渲染器: {renderer_name}")
        return True
    
    def unregister_renderer(self, name: str) -> bool:
        """注销渲染器
        
        Args:
            name: 渲染器名称
            
        Returns:
            bool: 是否注销成功
        """
        if name not in self.renderers:
            self.logger.warning(f"渲染器 '{name}' 不存在")
            return False
            
        renderer = self.renderers.pop(name)
        
        # 如果是默认渲染器，需要重新选择默认渲染器
        if renderer is self.default_renderer:
            if self.renderers:
                # 选择第一个可用的渲染器作为默认
                first_key = next(iter(self.renderers))
                self.default_renderer = self.renderers[first_key]
                self.logger.info(f"默认渲染器已更改为 '{first_key}'")
            else:
                self.default_renderer = None
                self.logger.warning("已移除所有渲染器，没有默认渲染器")
                
        self.logger.info(f"已注销渲染器: {name}")
        return True
    
    def get_renderer(self, name: str) -> Optional[RendererBase]:
        """获取渲染器
        
        Args:
            name: 渲染器名称
            
        Returns:
            可选的渲染器实例
        """
        return self.renderers.get(name)
    
    def get_default_renderer(self) -> Optional[RendererBase]:
        """获取默认渲染器
        
        Returns:
            可选的默认渲染器实例
        """
        return self.default_renderer
    
    def set_default_renderer(self, name: str) -> bool:
        """设置默认渲染器
        
        Args:
            name: 渲染器名称
            
        Returns:
            bool: 是否设置成功
        """
        if name not in self.renderers:
            self.logger.warning(f"渲染器 '{name}' 不存在，无法设为默认")
            return False
            
        self.default_renderer = self.renderers[name]
        self.logger.info(f"已将 '{name}' 设为默认渲染器")
        return True
    
    def get_all_renderers(self) -> Dict[str, RendererBase]:
        """获取所有渲染器
        
        Returns:
            渲染器字典
        """
        return self.renderers.copy() 