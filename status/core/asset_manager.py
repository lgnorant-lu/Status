"""
---------------------------------------------------------------
File name:                  asset_manager.py
Author:                     Ignorant-lu
Date created:               2023/04/03
Description:                资产管理器，整合资源加载和缓存功能
----------------------------------------------------------------

Changed history:            
                            2023/04/03: 初始创建;
                            2025/04/03: 实现与资源加载器和缓存系统的集成;
----
"""

import os
import logging
from typing import Dict, Any, Optional, List, Union, Tuple

# 导入资源加载器和缓存系统
from status.core.resource_loader import ResourceLoader, ResourceType, ResourceLoadError
from status.core.cache import Cache, CacheFull

class AssetManager:
    """资产管理器，整合资源加载和缓存功能，提供统一的资源访问接口"""
    
    _instance = None  # 单例实例
    
    def __new__(cls, *args, **kwargs):
        """实现单例模式"""
        if cls._instance is None:
            cls._instance = super(AssetManager, cls).__new__(cls)
        return cls._instance
    
    def __init__(self, base_path: str = "", cache_size: int = 1000):
        """初始化资产管理器
        
        Args:
            base_path: 资源基础路径
            cache_size: 缓存大小
        """
        # 只在首次创建时初始化
        if not hasattr(self, 'initialized'):
            self.logger = logging.getLogger("Hollow-ming.Core.AssetManager")
            
            self.resource_loader = ResourceLoader(base_path)
            self.cache = Cache(cache_size)
            
            self.base_path = base_path
            self.default_lifetimes = {
                ResourceType.IMAGE: None,  # 永久缓存
                ResourceType.SOUND: 300,   # 5分钟
                ResourceType.MUSIC: 600,   # 10分钟
                ResourceType.FONT: None,   # 永久缓存
                ResourceType.DATA: 3600,   # 1小时
                ResourceType.TEXT: 1800,   # 30分钟
                ResourceType.ANIMATION: None,  # 永久缓存
                ResourceType.OTHER: 300     # 5分钟
            }
            
            self.preloaded_groups = {}
            self.initialized = True
            self.logger.info("资产管理器初始化完成")
    
    def set_base_path(self, base_path: str) -> None:
        """设置资源基础路径
        
        Args:
            base_path: 资源基础路径
        """
        self.base_path = base_path
        self.resource_loader.set_base_path(base_path)
        self.logger.debug(f"设置资源基础路径: {base_path}")
    
    def get(self, path: str, resource_type=None, reload: bool = False, **kwargs) -> Any:
        """获取资源，优先从缓存获取，如果不存在则加载
        
        Args:
            path: 资源路径
            resource_type: 资源类型（可选）
            reload: 是否强制重新加载
            **kwargs: 传递给加载器的额外参数
            
        Returns:
            加载的资源
            
        Raises:
            ResourceLoadError: 资源加载失败时抛出
        """
        # 组合缓存键
        cache_key = f"{resource_type.name if resource_type else 'AUTO'}:{path}"
        
        # 如果不强制重新加载，尝试从缓存获取
        if not reload:
            cached = self.cache.get(cache_key)
            if cached is not None:
                self.logger.debug(f"从缓存获取资源: {path}")
                return cached
        
        # 从加载器加载资源
        self.logger.debug(f"加载资源: {path}")
        resource = self.resource_loader.load(path, resource_type, **kwargs)
        
        # 添加到缓存
        if resource_type:
            lifetime = self.default_lifetimes.get(resource_type)
        else:
            detected_type = self.resource_loader.get_resource_type(path)
            lifetime = self.default_lifetimes.get(detected_type)
        
        try:
            self.cache.set(cache_key, resource, lifetime)
        except CacheFull:
            self.logger.warning(f"缓存已满，资源 {path} 将不会被缓存")
        
        return resource
    
    def preload(self, paths: List[str], **kwargs) -> int:
        """预加载多个资源
        
        Args:
            paths: 资源路径列表
            **kwargs: 传递给加载器的额外参数
            
        Returns:
            int: 成功加载的资源数量
        """
        success_count = 0
        
        for path in paths:
            try:
                self.get(path, **kwargs)
                success_count += 1
            except Exception as e:
                self.logger.error(f"预加载资源失败: {path}, 错误: {str(e)}")
        
        self.logger.info(f"预加载完成: {success_count}/{len(paths)} 个资源成功")
        return success_count
    
    def preload_group(self, group_name: str, paths: List[str], **kwargs) -> bool:
        """预加载资源组
        
        Args:
            group_name: 组名称
            paths: 资源路径列表
            **kwargs: 传递给加载器的额外参数
            
        Returns:
            bool: 是否所有资源都加载成功
        """
        self.logger.info(f"预加载资源组: {group_name}, {len(paths)} 个资源")
        
        success_count = self.preload(paths, **kwargs)
        all_success = success_count == len(paths)
        
        # 记录组信息
        self.preloaded_groups[group_name] = {
            "paths": paths,
            "success_count": success_count,
            "all_success": all_success
        }
        
        return all_success
    
    def unload_group(self, group_name: str) -> bool:
        """卸载资源组
        
        Args:
            group_name: 组名称
            
        Returns:
            bool: 卸载是否成功
        """
        if group_name not in self.preloaded_groups:
            self.logger.warning(f"尝试卸载不存在的资源组: {group_name}")
            return False
        
        group_info = self.preloaded_groups[group_name]
        
        # 从缓存中删除组中的资源
        for path in group_info["paths"]:
            # 尝试不同的资源类型前缀
            for res_type in ResourceType:
                cache_key = f"{res_type.name}:{path}"
                self.cache.delete(cache_key)
            
            # 尝试自动检测类型的前缀
            cache_key = f"AUTO:{path}"
            self.cache.delete(cache_key)
        
        # 删除组信息
        del self.preloaded_groups[group_name]
        
        self.logger.info(f"资源组已卸载: {group_name}")
        return True
    
    def get_preloaded_groups(self) -> List[str]:
        """获取所有预加载的资源组名称
        
        Returns:
            List[str]: 组名称列表
        """
        return list(self.preloaded_groups.keys())
    
    def clear_cache(self, resource_type: Optional[ResourceType] = None) -> int:
        """清除缓存
        
        Args:
            resource_type: 要清除的资源类型，None表示清除所有类型
            
        Returns:
            int: 清除的资源数量
        """
        self.logger.info(f"清除缓存, 类型: {resource_type.name if resource_type else '所有'}")
        
        if resource_type is None:
            # 清除所有缓存
            count = len(self.cache.get_all_keys())
            self.cache.clear()
            return count
        
        # 清除特定类型的缓存
        count = 0
        for key in list(self.cache.get_all_keys()):
            if key.startswith(f"{resource_type.name}:"):
                self.cache.delete(key)
                count += 1
        
        return count
    
    def get_image(self, path: str, **kwargs) -> Any:
        """获取图像资源
        
        Args:
            path: 图像路径
            **kwargs: 额外参数，参见ResourceLoader._load_image
            
        Returns:
            图像对象
        """
        return self.get(path, ResourceType.IMAGE, **kwargs)
    
    def get_sound(self, path: str, **kwargs) -> Any:
        """获取音效资源
        
        Args:
            path: 音效路径
            **kwargs: 额外参数
            
        Returns:
            音效对象
        """
        return self.get(path, ResourceType.SOUND, **kwargs)
    
    def get_music(self, path: str, **kwargs) -> Any:
        """获取音乐资源
        
        Args:
            path: 音乐路径
            **kwargs: 额外参数
            
        Returns:
            音乐对象
        """
        return self.get(path, ResourceType.MUSIC, **kwargs)
    
    def get_font(self, path: str, size: int = 12, **kwargs) -> Any:
        """获取字体资源
        
        Args:
            path: 字体路径
            size: 字体大小
            **kwargs: 额外参数
            
        Returns:
            字体对象
        """
        kwargs['size'] = size
        return self.get(path, ResourceType.FONT, **kwargs)
    
    def get_data(self, path: str, **kwargs) -> Dict[str, Any]:
        """获取数据资源（JSON或YAML）
        
        Args:
            path: 数据文件路径
            **kwargs: 额外参数
            
        Returns:
            解析后的数据
        """
        return self.get(path, ResourceType.DATA, **kwargs)
    
    def get_text(self, path: str, **kwargs) -> str:
        """获取文本资源
        
        Args:
            path: 文本文件路径
            **kwargs: 额外参数
            
        Returns:
            文本内容
        """
        return self.get(path, ResourceType.TEXT, **kwargs)
    
    def get_animation(self, path: str, **kwargs) -> Any:
        """获取动画资源
        
        Args:
            path: 动画路径
            **kwargs: 额外参数
            
        Returns:
            动画对象
        """
        return self.get(path, ResourceType.ANIMATION, **kwargs)
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息
        
        Returns:
            Dict: 缓存统计信息
        """
        return self.cache.get_stats()
    
    def scan_resources(self, directory: str, recursive: bool = True) -> Dict[ResourceType, List[str]]:
        """扫描目录中的资源
        
        Args:
            directory: 要扫描的目录
            recursive: 是否递归扫描子目录
            
        Returns:
            Dict[ResourceType, List[str]]: 按资源类型分组的文件路径
        """
        return self.resource_loader.scan_directory(directory, recursive) 