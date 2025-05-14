"""
---------------------------------------------------------------
File name:                  plugin_base.py
Author:                     Ignorant-lu
Date created:               2025/05/14
Description:                插件系统的抽象基类
----------------------------------------------------------------

Changed history:            
                            2025/05/14: 初始创建;
----
"""

import abc
import logging
from typing import Dict, Any, Optional, List, Set

from status.core.types import ConfigDict


class PluginBase(abc.ABC):
    """插件抽象基类，定义所有插件必须实现的接口和生命周期方法"""
    
    def __init__(self, plugin_id: str, name: str, version: str, description: str = ""):
        """初始化插件基本信息
        
        Args:
            plugin_id: 插件唯一标识符
            name: 插件名称
            version: 插件版本
            description: 插件描述
        """
        self.plugin_id = plugin_id
        self.name = name
        self.version = version
        self.description = description
        self.is_enabled = False
        self.is_loaded = False
        self.dependencies: Set[str] = set()  # 依赖的其他插件ID
        self.config: ConfigDict = {}  # 插件配置
        self.logger = logging.getLogger(f"Status.Plugin.{self.plugin_id}")
    
    @abc.abstractmethod
    def load(self) -> bool:
        """加载插件资源和初始化，但不激活功能
        
        插件在被发现后首先调用此方法进行加载准备。
        此阶段应加载资源、初始化内部状态，但不应激活功能或影响系统。
        
        Returns:
            bool: 加载是否成功
        """
        pass
    
    @abc.abstractmethod
    def enable(self) -> bool:
        """启用插件功能
        
        在此方法中应注册事件监听器、添加UI元素、注册命令等，
        使插件功能对用户可用。
        
        Returns:
            bool: 启用是否成功
        """
        pass
    
    @abc.abstractmethod
    def disable(self) -> bool:
        """禁用插件功能
        
        在此方法中应注销事件监听器、移除UI元素、注销命令等，
        使插件功能对用户不可用，但不释放资源。
        
        Returns:
            bool: 禁用是否成功
        """
        pass
    
    @abc.abstractmethod
    def unload(self) -> bool:
        """卸载插件并释放资源
        
        在此方法中应释放所有资源，如关闭文件、断开连接等。
        此方法在应用程序关闭或用户手动卸载插件时调用。
        
        Returns:
            bool: 卸载是否成功
        """
        pass
    
    def get_metadata(self) -> Dict[str, Any]:
        """获取插件元数据
        
        Returns:
            Dict[str, Any]: 包含插件信息的字典
        """
        return {
            "id": self.plugin_id,
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "is_enabled": self.is_enabled,
            "is_loaded": self.is_loaded,
            "dependencies": list(self.dependencies)
        }
    
    def set_config(self, config: ConfigDict) -> None:
        """设置插件配置
        
        Args:
            config: 配置字典
        """
        self.config = config
    
    def get_config(self) -> ConfigDict:
        """获取插件配置
        
        Returns:
            ConfigDict: 当前插件配置
        """
        return self.config
    
    def add_dependency(self, plugin_id: str) -> None:
        """添加插件依赖
        
        Args:
            plugin_id: 依赖的插件ID
        """
        self.dependencies.add(plugin_id)
    
    def remove_dependency(self, plugin_id: str) -> None:
        """移除插件依赖
        
        Args:
            plugin_id: 要移除的依赖插件ID
        """
        if plugin_id in self.dependencies:
            self.dependencies.remove(plugin_id)
    
    def get_dependencies(self) -> List[str]:
        """获取所有依赖的插件ID列表
        
        Returns:
            List[str]: 依赖插件ID列表
        """
        return list(self.dependencies) 