"""
---------------------------------------------------------------
File name:                  plugin_manager.py
Author:                     Ignorant-lu
Date created:               2025/05/14
Description:                插件管理器
----------------------------------------------------------------

Changed history:            
                            2025/05/14: 初始创建;
----
"""

import os
import sys
import logging
import importlib
import importlib.util
from typing import Dict, List, Optional, Set, Any, Tuple
import traceback

from status.core.types import ConfigDict, SingletonType
from status.plugin.plugin_base import PluginBase


class PluginError(Exception):
    """插件相关错误的基类"""
    pass


class PluginNotFoundError(PluginError):
    """插件未找到错误"""
    pass


class PluginLoadError(PluginError):
    """插件加载错误"""
    pass


class DependencyError(PluginError):
    """插件依赖错误"""
    pass


class PluginManager(metaclass=SingletonType):
    """插件管理器，负责管理插件的发现、加载、启用和卸载
    
    采用单例模式确保全局只有一个插件管理器实例
    """
    
    def __init__(self):
        """初始化插件管理器"""
        self.plugins: Dict[str, PluginBase] = {}  # 所有已注册的插件
        self.enabled_plugins: Set[str] = set()  # 已启用的插件ID集合
        self.plugin_paths: List[str] = []  # 插件搜索路径
        self.logger = logging.getLogger("Status.Plugin.PluginManager")
        
        # 插件配置信息
        self.plugin_configs: Dict[str, ConfigDict] = {}
        
        # 默认插件目录
        default_plugin_dir = os.path.join(os.path.dirname(__file__), "..", "..", "plugins")
        if os.path.exists(default_plugin_dir):
            self.add_plugin_path(default_plugin_dir)
    
    def add_plugin_path(self, path: str) -> None:
        """添加插件搜索路径
        
        Args:
            path: 插件目录路径
        """
        if path not in self.plugin_paths and os.path.exists(path):
            self.plugin_paths.append(path)
            self.logger.info(f"添加插件路径: {path}")
        else:
            self.logger.warning(f"插件路径已存在或不存在: {path}")
    
    def discover_plugins(self) -> List[str]:
        """发现所有插件目录中的插件
        
        Returns:
            List[str]: 发现的插件ID列表
        """
        discovered_plugins = []
        
        for plugin_dir in self.plugin_paths:
            if not os.path.exists(plugin_dir):
                continue
                
            # 遍历插件目录
            for item in os.listdir(plugin_dir):
                plugin_path = os.path.join(plugin_dir, item)
                
                # 检查是否是目录
                if os.path.isdir(plugin_path):
                    # 检查是否包含__init__.py文件
                    init_file = os.path.join(plugin_path, "__init__.py")
                    if os.path.isfile(init_file):
                        # 尝试加载插件
                        try:
                            plugin_id = item  # 使用目录名作为插件ID
                            if self._load_plugin_module(plugin_path, plugin_id):
                                discovered_plugins.append(plugin_id)
                        except Exception as e:
                            self.logger.error(f"发现插件时出错 '{item}': {str(e)}")
                            traceback.print_exc()
        
        return discovered_plugins
    
    def _load_plugin_module(self, plugin_path: str, plugin_id: str) -> bool:
        """加载插件模块
        
        Args:
            plugin_path: 插件目录路径
            plugin_id: 插件ID
            
        Returns:
            bool: 加载是否成功
        """
        try:
            # 确保插件目录在Python路径中
            if plugin_path not in sys.path:
                sys.path.insert(0, os.path.dirname(plugin_path))
            
            # 导入插件模块
            module_name = os.path.basename(plugin_path)
            spec = importlib.util.spec_from_file_location(
                module_name, 
                os.path.join(plugin_path, "__init__.py")
            )
            
            if spec is None or spec.loader is None:
                self.logger.error(f"无法加载插件 '{plugin_id}': 规范或加载器为空")
                return False
                
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # 检查模块是否有create_plugin函数
            if not hasattr(module, "create_plugin"):
                self.logger.error(f"插件 '{plugin_id}' 没有create_plugin函数")
                return False
            
            # 创建插件实例
            plugin_instance = module.create_plugin()
            
            # 验证插件实例是否是PluginBase的子类
            if not isinstance(plugin_instance, PluginBase):
                self.logger.error(f"插件 '{plugin_id}' 不是PluginBase的子类")
                return False
            
            # 注册插件
            self.register_plugin(plugin_instance)
            return True
            
        except Exception as e:
            self.logger.error(f"加载插件模块 '{plugin_id}' 时出错: {str(e)}")
            traceback.print_exc()
            return False
    
    def register_plugin(self, plugin: PluginBase) -> None:
        """注册插件
        
        Args:
            plugin: 插件实例
        """
        if plugin.plugin_id in self.plugins:
            self.logger.warning(f"插件 '{plugin.plugin_id}' 已注册，将被覆盖")
        
        self.plugins[plugin.plugin_id] = plugin
        self.logger.info(f"注册插件: {plugin.name} (ID: {plugin.plugin_id}, 版本: {plugin.version})")
        
        # 如果有配置，设置给插件
        if plugin.plugin_id in self.plugin_configs:
            plugin.set_config(self.plugin_configs[plugin.plugin_id])
    
    def unregister_plugin(self, plugin_id: str) -> bool:
        """注销插件
        
        Args:
            plugin_id: 插件ID
            
        Returns:
            bool: 注销是否成功
        """
        if plugin_id not in self.plugins:
            self.logger.warning(f"尝试注销不存在的插件: {plugin_id}")
            return False
        
        # 如果插件已启用，先禁用它
        if plugin_id in self.enabled_plugins:
            self.disable_plugin(plugin_id)
        
        # 如果插件已加载，先卸载它
        plugin = self.plugins[plugin_id]
        if plugin.is_loaded:
            plugin.unload()
        
        # 从注册表中移除
        del self.plugins[plugin_id]
        self.logger.info(f"注销插件: {plugin_id}")
        return True
    
    def load_plugin(self, plugin_id: str) -> bool:
        """加载插件
        
        Args:
            plugin_id: 插件ID
            
        Returns:
            bool: 加载是否成功
        
        Raises:
            PluginNotFoundError: 插件未找到
            PluginLoadError: 插件加载失败
            DependencyError: 插件依赖错误
        """
        if plugin_id not in self.plugins:
            raise PluginNotFoundError(f"插件未找到: {plugin_id}")
        
        plugin = self.plugins[plugin_id]
        
        # 如果已经加载，直接返回成功
        if plugin.is_loaded:
            return True
        
        # 检查并加载依赖
        for dep_id in plugin.get_dependencies():
            if dep_id not in self.plugins:
                raise DependencyError(f"插件 '{plugin_id}' 依赖的插件 '{dep_id}' 未找到")
            
            dep_plugin = self.plugins[dep_id]
            if not dep_plugin.is_loaded:
                if not self.load_plugin(dep_id):
                    raise DependencyError(f"无法加载插件 '{plugin_id}' 的依赖 '{dep_id}'")
        
        # 加载插件
        try:
            if not plugin.load():
                raise PluginLoadError(f"插件 '{plugin_id}' 加载失败")
            
            plugin.is_loaded = True
            self.logger.info(f"加载插件: {plugin_id}")
            return True
        except Exception as e:
            self.logger.error(f"加载插件 '{plugin_id}' 时出错: {str(e)}")
            traceback.print_exc()
            raise PluginLoadError(f"加载插件 '{plugin_id}' 时出错: {str(e)}")
    
    def enable_plugin(self, plugin_id: str) -> bool:
        """启用插件
        
        Args:
            plugin_id: 插件ID
            
        Returns:
            bool: 启用是否成功
            
        Raises:
            PluginNotFoundError: 插件未找到
            PluginLoadError: 插件未加载
            DependencyError: 依赖的插件未启用
        """
        if plugin_id not in self.plugins:
            raise PluginNotFoundError(f"插件未找到: {plugin_id}")
        
        plugin = self.plugins[plugin_id]
        
        # 如果已经启用，直接返回成功
        if plugin.is_enabled:
            return True
        
        # 确保插件已加载
        if not plugin.is_loaded:
            if not self.load_plugin(plugin_id):
                raise PluginLoadError(f"插件 '{plugin_id}' 未加载")
        
        # 检查并启用依赖
        for dep_id in plugin.get_dependencies():
            dep_plugin = self.plugins.get(dep_id)
            
            if dep_plugin is None:
                raise DependencyError(f"插件 '{plugin_id}' 依赖的插件 '{dep_id}' 未找到")
            
            if not dep_plugin.is_enabled:
                if not self.enable_plugin(dep_id):
                    raise DependencyError(f"无法启用插件 '{plugin_id}' 的依赖 '{dep_id}'")
        
        # 启用插件
        try:
            if not plugin.enable():
                raise PluginError(f"插件 '{plugin_id}' 启用失败")
            
            plugin.is_enabled = True
            self.enabled_plugins.add(plugin_id)
            self.logger.info(f"启用插件: {plugin_id}")
            return True
        except Exception as e:
            self.logger.error(f"启用插件 '{plugin_id}' 时出错: {str(e)}")
            traceback.print_exc()
            raise PluginError(f"启用插件 '{plugin_id}' 时出错: {str(e)}")
    
    def disable_plugin(self, plugin_id: str) -> bool:
        """禁用插件
        
        Args:
            plugin_id: 插件ID
            
        Returns:
            bool: 禁用是否成功
        """
        if plugin_id not in self.plugins:
            self.logger.warning(f"尝试禁用不存在的插件: {plugin_id}")
            return False
        
        plugin = self.plugins[plugin_id]
        
        # 如果已经禁用，直接返回成功
        if not plugin.is_enabled:
            return True
        
        # 检查是否有其他插件依赖此插件
        dependent_plugins = self._find_dependent_plugins(plugin_id)
        if dependent_plugins:
            dependent_names = [self.plugins[p].name for p in dependent_plugins]
            raise DependencyError(f"插件 '{plugin.name}' 无法禁用，因为以下插件依赖它: {', '.join(dependent_names)}")
        
        # 禁用插件
        try:
            if not plugin.disable():
                self.logger.warning(f"插件 '{plugin_id}' 返回禁用失败")
                return False
            
            plugin.is_enabled = False
            self.enabled_plugins.remove(plugin_id)
            self.logger.info(f"禁用插件: {plugin_id}")
            return True
        except Exception as e:
            self.logger.error(f"禁用插件 '{plugin_id}' 时出错: {str(e)}")
            traceback.print_exc()
            return False
    
    def unload_plugin(self, plugin_id: str) -> bool:
        """卸载插件
        
        Args:
            plugin_id: 插件ID
            
        Returns:
            bool: 卸载是否成功
        """
        if plugin_id not in self.plugins:
            self.logger.warning(f"尝试卸载不存在的插件: {plugin_id}")
            return False
        
        plugin = self.plugins[plugin_id]
        
        # 如果已经卸载，直接返回成功
        if not plugin.is_loaded:
            return True
        
        # 如果插件已启用，先禁用它
        if plugin.is_enabled:
            if not self.disable_plugin(plugin_id):
                return False
        
        # 检查是否有其他已加载的插件依赖此插件
        dependent_plugins = self._find_dependent_plugins(plugin_id, check_loaded=True)
        if dependent_plugins:
            dependent_names = [self.plugins[p].name for p in dependent_plugins]
            raise DependencyError(f"插件 '{plugin.name}' 无法卸载，因为以下插件依赖它: {', '.join(dependent_names)}")
        
        # 卸载插件
        try:
            if not plugin.unload():
                self.logger.warning(f"插件 '{plugin_id}' 返回卸载失败")
                return False
            
            plugin.is_loaded = False
            self.logger.info(f"卸载插件: {plugin_id}")
            return True
        except Exception as e:
            self.logger.error(f"卸载插件 '{plugin_id}' 时出错: {str(e)}")
            traceback.print_exc()
            return False
    
    def get_plugin(self, plugin_id: str) -> Optional[PluginBase]:
        """获取指定ID的插件实例
        
        Args:
            plugin_id: 插件ID
            
        Returns:
            Optional[PluginBase]: 插件实例，如果不存在则返回None
        """
        return self.plugins.get(plugin_id)
    
    def get_all_plugins(self) -> Dict[str, PluginBase]:
        """获取所有已注册的插件
        
        Returns:
            Dict[str, PluginBase]: 插件ID到插件实例的映射
        """
        return self.plugins.copy()
    
    def get_enabled_plugins(self) -> Dict[str, PluginBase]:
        """获取所有已启用的插件
        
        Returns:
            Dict[str, PluginBase]: 插件ID到插件实例的映射
        """
        return {plugin_id: self.plugins[plugin_id] for plugin_id in self.enabled_plugins}
    
    def _find_dependent_plugins(self, plugin_id: str, check_loaded: bool = False) -> List[str]:
        """查找依赖指定插件的所有其他插件
        
        Args:
            plugin_id: 插件ID
            check_loaded: 是否只检查已加载的插件
            
        Returns:
            List[str]: 依赖此插件的插件ID列表
        """
        dependent_plugins = []
        
        for pid, plugin in self.plugins.items():
            if pid == plugin_id:
                continue
                
            if check_loaded and not plugin.is_loaded:
                continue
                
            if plugin_id in plugin.get_dependencies():
                dependent_plugins.append(pid)
        
        return dependent_plugins
    
    def set_plugin_config(self, plugin_id: str, config: ConfigDict) -> None:
        """设置插件配置
        
        Args:
            plugin_id: 插件ID
            config: 配置字典
        """
        self.plugin_configs[plugin_id] = config
        
        # 如果插件已注册，也设置给插件实例
        if plugin_id in self.plugins:
            self.plugins[plugin_id].set_config(config)
    
    def get_plugin_config(self, plugin_id: str) -> Optional[ConfigDict]:
        """获取插件配置
        
        Args:
            plugin_id: 插件ID
            
        Returns:
            Optional[ConfigDict]: 插件配置，如果不存在则返回None
        """
        if plugin_id in self.plugins:
            return self.plugins[plugin_id].get_config()
        return self.plugin_configs.get(plugin_id)
    
    def enable_all_plugins(self) -> Tuple[List[str], List[Tuple[str, str]]]:
        """启用所有已注册的插件
        
        Returns:
            Tuple[List[str], List[Tuple[str, str]]]: 成功启用的插件ID列表和失败的插件ID与错误信息
        """
        success = []
        failures = []
        
        for plugin_id in self.plugins.keys():
            try:
                if self.enable_plugin(plugin_id):
                    success.append(plugin_id)
            except Exception as e:
                failures.append((plugin_id, str(e)))
        
        return success, failures 