"""
---------------------------------------------------------------
File name:                  plugin_registry.py
Author:                     Ignorant-lu
Date created:               2025/05/14
Description:                插件注册表
----------------------------------------------------------------

Changed history:            
                            2025/05/14: 初始创建;
----
"""

import logging
from typing import Dict, List, Optional, Set, Callable, Any, Type, TypeVar, Generic, Union

from status.core.types import SingletonType
from status.plugin.plugin_base import PluginBase


# 类型变量和接口定义
T = TypeVar('T')
ExtensionPoint = str  # 扩展点标识符
PluginType = str  # 插件类型标识符


class ExtensionHandler(Generic[T]):
    """扩展点处理器，负责管理特定扩展点的所有扩展"""
    
    def __init__(self, extension_point: ExtensionPoint, description: str = ""):
        """初始化扩展点处理器
        
        Args:
            extension_point: 扩展点标识符
            description: 扩展点描述
        """
        self.extension_point = extension_point
        self.description = description
        self.extensions: Dict[str, T] = {}  # 插件ID到扩展实现的映射
        self.logger = logging.getLogger(f"Status.Plugin.ExtensionHandler.{extension_point}")
    
    def register_extension(self, plugin_id: str, extension: T) -> None:
        """注册扩展实现
        
        Args:
            plugin_id: 插件ID
            extension: 扩展实现
        """
        if plugin_id in self.extensions:
            self.logger.warning(f"扩展点 '{self.extension_point}' 的扩展 '{plugin_id}' 已存在，将被覆盖")
        
        self.extensions[plugin_id] = extension
        self.logger.debug(f"注册扩展: '{plugin_id}' 到扩展点 '{self.extension_point}'")
    
    def unregister_extension(self, plugin_id: str) -> bool:
        """注销扩展实现
        
        Args:
            plugin_id: 插件ID
            
        Returns:
            bool: 是否成功注销
        """
        if plugin_id not in self.extensions:
            self.logger.warning(f"尝试注销不存在的扩展: 插件 '{plugin_id}', 扩展点 '{self.extension_point}'")
            return False
        
        del self.extensions[plugin_id]
        self.logger.debug(f"注销扩展: '{plugin_id}' 从扩展点 '{self.extension_point}'")
        return True
    
    def get_extension(self, plugin_id: str) -> Optional[T]:
        """获取特定插件的扩展实现
        
        Args:
            plugin_id: 插件ID
            
        Returns:
            Optional[T]: 扩展实现，如果不存在则返回None
        """
        return self.extensions.get(plugin_id)
    
    def get_all_extensions(self) -> Dict[str, T]:
        """获取所有扩展实现
        
        Returns:
            Dict[str, T]: 插件ID到扩展实现的映射
        """
        return self.extensions.copy()


class PluginRegistry(metaclass=SingletonType):
    """插件注册表，负责管理插件类型和扩展点
    
    采用单例模式确保全局只有一个插件注册表实例
    """
    
    def __init__(self):
        """初始化插件注册表"""
        self.plugin_types: Dict[PluginType, List[str]] = {}  # 插件类型到插件ID列表的映射
        self.extension_handlers: Dict[ExtensionPoint, ExtensionHandler] = {}  # 扩展点到处理器的映射
        self.plugin_extensions: Dict[str, Set[ExtensionPoint]] = {}  # 插件ID到其注册的扩展点集合的映射
        self.logger = logging.getLogger("Status.Plugin.PluginRegistry")
    
    def register_plugin_type(self, plugin_id: str, plugin_type: PluginType) -> None:
        """注册插件类型
        
        Args:
            plugin_id: 插件ID
            plugin_type: 插件类型
        """
        if plugin_type not in self.plugin_types:
            self.plugin_types[plugin_type] = []
        
        if plugin_id not in self.plugin_types[plugin_type]:
            self.plugin_types[plugin_type].append(plugin_id)
            self.logger.debug(f"注册插件类型: 插件 '{plugin_id}' 到类型 '{plugin_type}'")
    
    def unregister_plugin_type(self, plugin_id: str, plugin_type: PluginType) -> bool:
        """注销插件类型
        
        Args:
            plugin_id: 插件ID
            plugin_type: 插件类型
            
        Returns:
            bool: 是否成功注销
        """
        if plugin_type not in self.plugin_types or plugin_id not in self.plugin_types[plugin_type]:
            self.logger.warning(f"尝试注销不存在的插件类型: 插件 '{plugin_id}', 类型 '{plugin_type}'")
            return False
        
        self.plugin_types[plugin_type].remove(plugin_id)
        self.logger.debug(f"注销插件类型: 插件 '{plugin_id}' 从类型 '{plugin_type}'")
        
        # 如果类型下没有插件了，清理类型
        if not self.plugin_types[plugin_type]:
            del self.plugin_types[plugin_type]
        
        return True
    
    def get_plugins_by_type(self, plugin_type: PluginType) -> List[str]:
        """获取特定类型的所有插件ID
        
        Args:
            plugin_type: 插件类型
            
        Returns:
            List[str]: 插件ID列表
        """
        return self.plugin_types.get(plugin_type, []).copy()
    
    def get_plugin_types(self, plugin_id: str) -> List[PluginType]:
        """获取插件的所有类型
        
        Args:
            plugin_id: 插件ID
            
        Returns:
            List[PluginType]: 插件类型列表
        """
        return [t for t, plugins in self.plugin_types.items() if plugin_id in plugins]
    
    def register_extension_point(self, extension_point: ExtensionPoint, description: str = "") -> ExtensionHandler:
        """注册扩展点
        
        Args:
            extension_point: 扩展点标识符
            description: 扩展点描述
            
        Returns:
            ExtensionHandler: 扩展点处理器
        """
        if extension_point in self.extension_handlers:
            self.logger.warning(f"扩展点 '{extension_point}' 已存在，将使用现有处理器")
            return self.extension_handlers[extension_point]
        
        handler = ExtensionHandler(extension_point, description)
        self.extension_handlers[extension_point] = handler
        self.logger.info(f"注册扩展点: '{extension_point}' - {description}")
        return handler
    
    def unregister_extension_point(self, extension_point: ExtensionPoint) -> bool:
        """注销扩展点
        
        Args:
            extension_point: 扩展点标识符
            
        Returns:
            bool: 是否成功注销
        """
        if extension_point not in self.extension_handlers:
            self.logger.warning(f"尝试注销不存在的扩展点: '{extension_point}'")
            return False
        
        handler = self.extension_handlers[extension_point]
        
        # 检查是否有插件还在使用该扩展点
        if handler.extensions:
            self.logger.warning(f"无法注销扩展点 '{extension_point}'，因为还有插件注册了扩展: {list(handler.extensions.keys())}")
            return False
        
        del self.extension_handlers[extension_point]
        self.logger.info(f"注销扩展点: '{extension_point}'")
        
        return True
    
    def get_extension_handler(self, extension_point: ExtensionPoint) -> Optional[ExtensionHandler]:
        """获取扩展点处理器
        
        Args:
            extension_point: 扩展点标识符
            
        Returns:
            Optional[ExtensionHandler]: 扩展点处理器，如果不存在则返回None
        """
        return self.extension_handlers.get(extension_point)
    
    def register_extension(self, plugin_id: str, extension_point: ExtensionPoint, extension: Any) -> bool:
        """注册扩展实现
        
        Args:
            plugin_id: 插件ID
            extension_point: 扩展点标识符
            extension: 扩展实现
            
        Returns:
            bool: 是否成功注册
        """
        handler = self.get_extension_handler(extension_point)
        if handler is None:
            self.logger.warning(f"尝试向不存在的扩展点 '{extension_point}' 注册扩展")
            return False
        
        handler.register_extension(plugin_id, extension)
        
        # 记录插件注册的扩展点
        if plugin_id not in self.plugin_extensions:
            self.plugin_extensions[plugin_id] = set()
        self.plugin_extensions[plugin_id].add(extension_point)
        
        return True
    
    def unregister_extension(self, plugin_id: str, extension_point: ExtensionPoint) -> bool:
        """注销扩展实现
        
        Args:
            plugin_id: 插件ID
            extension_point: 扩展点标识符
            
        Returns:
            bool: 是否成功注销
        """
        handler = self.get_extension_handler(extension_point)
        if handler is None:
            self.logger.warning(f"尝试从不存在的扩展点 '{extension_point}' 注销扩展")
            return False
        
        result = handler.unregister_extension(plugin_id)
        
        # 更新插件扩展点记录
        if result and plugin_id in self.plugin_extensions:
            self.plugin_extensions[plugin_id].discard(extension_point)
            if not self.plugin_extensions[plugin_id]:
                del self.plugin_extensions[plugin_id]
        
        return result
    
    def unregister_all_plugin_extensions(self, plugin_id: str) -> None:
        """注销插件的所有扩展实现
        
        Args:
            plugin_id: 插件ID
        """
        if plugin_id not in self.plugin_extensions:
            return
        
        # 复制一份以避免迭代过程中修改集合
        extension_points = list(self.plugin_extensions[plugin_id])
        for extension_point in extension_points:
            self.unregister_extension(plugin_id, extension_point)
        
        # 注销所有插件类型
        for plugin_type in list(self.plugin_types.keys()):
            if plugin_id in self.plugin_types[plugin_type]:
                self.unregister_plugin_type(plugin_id, plugin_type)
    
    def get_all_extension_points(self) -> Dict[ExtensionPoint, str]:
        """获取所有已注册的扩展点及其描述
        
        Returns:
            Dict[ExtensionPoint, str]: 扩展点到描述的映射
        """
        return {ep: handler.description for ep, handler in self.extension_handlers.items()}
    
    def get_plugin_extension_points(self, plugin_id: str) -> Set[ExtensionPoint]:
        """获取插件注册的所有扩展点
        
        Args:
            plugin_id: 插件ID
            
        Returns:
            Set[ExtensionPoint]: 扩展点集合
        """
        return self.plugin_extensions.get(plugin_id, set()).copy()