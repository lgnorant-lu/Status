"""
---------------------------------------------------------------
File name:                  scene_manager.py
Author:                     Ignorant-lu
Date created:               2025/04/04
Description:                场景管理器，管理不同的系统监控场景
----------------------------------------------------------------

Changed history:            
                            2025/04/04: 初始创建;
----
"""

import logging
import time
from typing import Dict, Any, List, Optional, Union, Tuple


class Scene:
    """监控场景类，定义不同监控数据的采集和显示需求"""
    
    def __init__(self, scene_id: str, config: Optional[Dict[str, Any]] = None):
        """
        初始化场景
        
        Args:
            scene_id: 场景唯一ID
            config: 场景配置
        """
        self.scene_id = scene_id
        self.config = config or {}
        self.logger = logging.getLogger(f"Scene.{scene_id}")
        
        # 默认采集配置
        self.collection_config = self.config.get("collection", {
            "data_range": "all",  # 采集所有数据
            "metrics": ["cpu", "memory", "disk", "network", "system"],  # 采集的指标
            "interval": 1.0,  # 采集间隔（秒）
            "advanced": False  # 是否采集高级指标
        })
        
        # 默认处理配置
        self.processing_config = self.config.get("processing", {
            "enable_trends": True,  # 启用趋势分析
            "enable_predictions": False,  # 启用预测
            "smoothing_window": 3  # 平滑窗口大小
        })
        
        # 默认视觉配置
        self.visual_config = self.config.get("visual", {
            "style": "default",  # 视觉风格
            "animations": True,  # 是否启用动画
            "indicators": ["cpu", "memory", "disk", "network"]  # 显示的指标
        })
        
        # 场景元数据
        self.metadata = self.config.get("metadata", {
            "name": scene_id,  # 场景名称
            "description": "",  # 场景描述
            "icon": "chart-bar",  # 场景图标
            "priority": 0  # 场景优先级
        })
        
        # 缓存数据
        self.cached_data = None
        self.last_update = 0
        
        self.logger.info(f"初始化场景 '{scene_id}'")
        
    def update_config(self, config: Dict[str, Any]) -> None:
        """
        更新场景配置
        
        Args:
            config: 新配置
        """
        self.config.update(config)
        
        # 更新具体配置项
        if "collection" in config:
            self.collection_config.update(config["collection"])
            
        if "processing" in config:
            self.processing_config.update(config["processing"])
            
        if "visual" in config:
            self.visual_config.update(config["visual"])
            
        if "metadata" in config:
            self.metadata.update(config["metadata"])
            
        self.logger.debug(f"更新场景 '{self.scene_id}' 配置")
        
    def get_collection_config(self) -> Dict[str, Any]:
        """
        获取数据采集配置
        
        Returns:
            Dict: 采集配置
        """
        return self.collection_config.copy()
        
    def get_processing_config(self) -> Dict[str, Any]:
        """
        获取数据处理配置
        
        Returns:
            Dict: 处理配置
        """
        return self.processing_config.copy()
        
    def get_visual_config(self) -> Dict[str, Any]:
        """
        获取视觉配置
        
        Returns:
            Dict: 视觉配置
        """
        return self.visual_config.copy()
        
    def get_metadata(self) -> Dict[str, Any]:
        """
        获取场景元数据
        
        Returns:
            Dict: 元数据
        """
        return self.metadata.copy()
        
    def cache_data(self, data: Dict[str, Any]) -> None:
        """
        缓存数据
        
        Args:
            data: 要缓存的数据
        """
        self.cached_data = data
        self.last_update = time.time()
        
    def get_cached_data(self) -> Optional[Dict[str, Any]]:
        """
        获取缓存数据
        
        Returns:
            Optional[Dict]: 缓存的数据或None
        """
        return self.cached_data
        
    def is_cache_valid(self, max_age: float = 5.0) -> bool:
        """
        检查缓存是否有效
        
        Args:
            max_age: 最大有效期（秒）
            
        Returns:
            bool: 缓存是否有效
        """
        if self.cached_data is None:
            return False
            
        return (time.time() - self.last_update) <= max_age
        
    def to_dict(self) -> Dict[str, Any]:
        """
        转换为字典表示
        
        Returns:
            Dict: 场景的字典表示
        """
        return {
            "id": self.scene_id,
            "metadata": self.metadata,
            "collection": self.collection_config,
            "processing": self.processing_config,
            "visual": self.visual_config,
            "last_update": self.last_update
        }
        
        
class SceneManager:
    """场景管理器，管理多个监控场景"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化场景管理器
        
        Args:
            config: 管理器配置
        """
        self.config = config or {}
        self.logger = logging.getLogger("SceneManager")
        self.scenes = {}
        self.active_scene_id = None
        
        # 如果配置中提供了默认场景，创建它们
        default_scenes = self.config.get("default_scenes", [])
        for scene_config in default_scenes:
            scene_id = scene_config.get("id")
            if scene_id:
                self.create_scene(scene_id, scene_config)
                
        # 设置默认活动场景
        default_active = self.config.get("default_active")
        if default_active and default_active in self.scenes:
            self.active_scene_id = default_active
        elif self.scenes:
            # 如果没有指定默认活动场景，使用第一个创建的场景
            self.active_scene_id = next(iter(self.scenes))
            
        self.logger.info(f"场景管理器初始化完成，加载了 {len(self.scenes)} 个场景")
        if self.active_scene_id:
            self.logger.info(f"活动场景: '{self.active_scene_id}'")
            
    def create_scene(self, scene_id: str, config: Optional[Dict[str, Any]] = None) -> Scene:
        """
        创建新场景
        
        Args:
            scene_id: 场景ID
            config: 场景配置
            
        Returns:
            Scene: 创建的场景对象
        """
        if scene_id in self.scenes:
            self.logger.warning(f"场景 '{scene_id}' 已存在，将被覆盖")
            
        scene = Scene(scene_id, config)
        self.scenes[scene_id] = scene
        
        # 如果这是第一个场景，设置为活动场景
        if not self.active_scene_id:
            self.active_scene_id = scene_id
            
        self.logger.info(f"创建场景 '{scene_id}'")
        return scene
        
    def get_scene(self, scene_id: str) -> Optional[Scene]:
        """
        获取指定ID的场景
        
        Args:
            scene_id: 场景ID
            
        Returns:
            Optional[Scene]: 场景对象或None
        """
        if scene_id not in self.scenes:
            self.logger.warning(f"场景 '{scene_id}' 不存在")
            return None
            
        return self.scenes[scene_id]
        
    def delete_scene(self, scene_id: str) -> bool:
        """
        删除场景
        
        Args:
            scene_id: 要删除的场景ID
            
        Returns:
            bool: 是否成功删除
        """
        if scene_id not in self.scenes:
            self.logger.warning(f"尝试删除不存在的场景 '{scene_id}'")
            return False
            
        # 如果删除的是当前活动场景，切换到另一个场景
        if scene_id == self.active_scene_id:
            # 找到另一个场景
            other_scenes = [s for s in self.scenes.keys() if s != scene_id]
            if other_scenes:
                self.active_scene_id = other_scenes[0]
            else:
                self.active_scene_id = None
                
        del self.scenes[scene_id]
        self.logger.info(f"删除场景 '{scene_id}'")
        return True
        
    def set_active_scene(self, scene_id: str) -> bool:
        """
        设置活动场景
        
        Args:
            scene_id: 要激活的场景ID
            
        Returns:
            bool: 是否成功设置
        """
        if scene_id not in self.scenes:
            self.logger.warning(f"尝试激活不存在的场景 '{scene_id}'")
            return False
            
        self.active_scene_id = scene_id
        self.logger.info(f"设置活动场景: '{scene_id}'")
        return True
        
    def get_active_scene(self) -> Optional[Scene]:
        """
        获取当前活动场景
        
        Returns:
            Optional[Scene]: 活动场景或None
        """
        if not self.active_scene_id:
            return None
            
        return self.scenes.get(self.active_scene_id)
        
    def get_active_scene_id(self) -> Optional[str]:
        """
        获取当前活动场景ID
        
        Returns:
            Optional[str]: 活动场景ID或None
        """
        return self.active_scene_id
        
    def list_scenes(self) -> List[Dict[str, Any]]:
        """
        列出所有场景
        
        Returns:
            List[Dict]: 场景列表，包含基本信息
        """
        return [
            {
                "id": scene_id,
                "name": scene.metadata.get("name", scene_id),
                "description": scene.metadata.get("description", ""),
                "icon": scene.metadata.get("icon", "chart-bar"),
                "priority": scene.metadata.get("priority", 0),
                "is_active": scene_id == self.active_scene_id
            }
            for scene_id, scene in self.scenes.items()
        ]
        
    def get_scene_collection_config(self, scene_id: Optional[str] = None) -> Dict[str, Any]:
        """
        获取指定场景的数据采集配置
        
        Args:
            scene_id: 场景ID，如果为None则使用当前活动场景
            
        Returns:
            Dict: 采集配置
        """
        if scene_id is None:
            scene_id = self.active_scene_id
            
        if not scene_id or scene_id not in self.scenes:
            # 返回默认配置
            return {
                "data_range": "all",
                "metrics": ["cpu", "memory", "disk", "network", "system"],
                "interval": 1.0,
                "advanced": False
            }
            
        return self.scenes[scene_id].get_collection_config()
        
    def get_scene_processing_config(self, scene_id: Optional[str] = None) -> Dict[str, Any]:
        """
        获取指定场景的数据处理配置
        
        Args:
            scene_id: 场景ID，如果为None则使用当前活动场景
            
        Returns:
            Dict: 处理配置
        """
        if scene_id is None:
            scene_id = self.active_scene_id
            
        if not scene_id or scene_id not in self.scenes:
            # 返回默认配置
            return {
                "enable_trends": True,
                "enable_predictions": False,
                "smoothing_window": 3
            }
            
        return self.scenes[scene_id].get_processing_config()
        
    def get_scene_visual_config(self, scene_id: Optional[str] = None) -> Dict[str, Any]:
        """
        获取指定场景的视觉配置
        
        Args:
            scene_id: 场景ID，如果为None则使用当前活动场景
            
        Returns:
            Dict: 视觉配置
        """
        if scene_id is None:
            scene_id = self.active_scene_id
            
        if not scene_id or scene_id not in self.scenes:
            # 返回默认配置
            return {
                "style": "default",
                "animations": True,
                "indicators": ["cpu", "memory", "disk", "network"]
            }
            
        return self.scenes[scene_id].get_visual_config()
        
    def update_scene_config(self, scene_id: str, config: Dict[str, Any]) -> bool:
        """
        更新场景配置
        
        Args:
            scene_id: 场景ID
            config: 新配置
            
        Returns:
            bool: 是否成功更新
        """
        if scene_id not in self.scenes:
            self.logger.warning(f"尝试更新不存在的场景 '{scene_id}' 的配置")
            return False
            
        self.scenes[scene_id].update_config(config)
        return True
        
    def cache_scene_data(self, scene_id: str, data: Dict[str, Any]) -> bool:
        """
        缓存场景数据
        
        Args:
            scene_id: 场景ID
            data: 要缓存的数据
            
        Returns:
            bool: 是否成功缓存
        """
        if scene_id not in self.scenes:
            self.logger.warning(f"尝试为不存在的场景 '{scene_id}' 缓存数据")
            return False
            
        self.scenes[scene_id].cache_data(data)
        return True
        
    def get_scene_data(self, scene_id: Optional[str] = None, max_age: float = 5.0) -> Optional[Dict[str, Any]]:
        """
        获取场景数据
        
        Args:
            scene_id: 场景ID，如果为None则使用当前活动场景
            max_age: 缓存最大有效期（秒）
            
        Returns:
            Optional[Dict]: 场景数据或None
        """
        if scene_id is None:
            scene_id = self.active_scene_id
            
        if not scene_id or scene_id not in self.scenes:
            return None
            
        scene = self.scenes[scene_id]
        if not scene.is_cache_valid(max_age):
            return None
            
        return scene.get_cached_data()
        
    def optimize_collection(self) -> Dict[str, Any]:
        """
        根据所有场景的需求，优化数据采集配置
        
        Returns:
            Dict: 优化后的采集配置
        """
        # 默认基础配置
        optimized = {
            "data_range": "minimal",
            "metrics": [],
            "interval": 5.0,  # 默认较长间隔
            "advanced": False
        }
        
        # 遍历所有场景，优化数据采集需求
        scene_metrics = set()
        min_interval = float('inf')
        need_advanced = False
        
        for scene in self.scenes.values():
            config = scene.get_collection_config()
            
            # 收集所有需要的指标
            scene_metrics.update(config.get("metrics", []))
            
            # 取最小的采集间隔
            interval = config.get("interval", 5.0)
            min_interval = min(min_interval, interval)
            
            # 检查是否需要高级指标
            if config.get("advanced", False):
                need_advanced = True
                
            # 如果有场景需要全部数据范围，则设为"all"
            if config.get("data_range", "minimal") == "all":
                optimized["data_range"] = "all"
                
        # 更新优化后的配置
        optimized["metrics"] = list(scene_metrics)
        optimized["interval"] = min_interval if min_interval != float('inf') else 1.0
        optimized["advanced"] = need_advanced
        
        return optimized
        
    def create_default_scenes(self) -> None:
        """创建默认场景集"""
        # 1. 概览场景
        overview_config = {
            "metadata": {
                "name": "系统概览",
                "description": "显示系统主要指标的概览",
                "icon": "chart-bar",
                "priority": 100
            },
            "collection": {
                "data_range": "minimal",
                "metrics": ["cpu", "memory", "disk", "network", "system"],
                "interval": 2.0,
                "advanced": False
            },
            "processing": {
                "enable_trends": True,
                "enable_predictions": False,
                "smoothing_window": 3
            },
            "visual": {
                "style": "default",
                "animations": True,
                "indicators": ["cpu", "memory", "disk", "network"]
            }
        }
        self.create_scene("overview", overview_config)
        
        # 2. CPU详情场景
        cpu_config = {
            "metadata": {
                "name": "CPU详情",
                "description": "详细的CPU使用情况和性能监控",
                "icon": "cpu",
                "priority": 90
            },
            "collection": {
                "data_range": "all",
                "metrics": ["cpu", "system"],
                "interval": 1.0,
                "advanced": True
            },
            "processing": {
                "enable_trends": True,
                "enable_predictions": True,
                "smoothing_window": 3
            },
            "visual": {
                "style": "technical",
                "animations": True,
                "indicators": ["cpu"]
            }
        }
        self.create_scene("cpu", cpu_config)
        
        # 3. 内存详情场景
        memory_config = {
            "metadata": {
                "name": "内存详情",
                "description": "详细的内存使用情况监控",
                "icon": "memory",
                "priority": 80
            },
            "collection": {
                "data_range": "all",
                "metrics": ["memory", "system"],
                "interval": 1.0,
                "advanced": True
            },
            "processing": {
                "enable_trends": True,
                "enable_predictions": False,
                "smoothing_window": 3
            },
            "visual": {
                "style": "technical",
                "animations": True,
                "indicators": ["memory"]
            }
        }
        self.create_scene("memory", memory_config)
        
        # 4. 磁盘详情场景
        disk_config = {
            "metadata": {
                "name": "磁盘详情",
                "description": "详细的磁盘使用情况和I/O监控",
                "icon": "hdd",
                "priority": 70
            },
            "collection": {
                "data_range": "all",
                "metrics": ["disk", "system"],
                "interval": 2.0,
                "advanced": True
            },
            "processing": {
                "enable_trends": True,
                "enable_predictions": False,
                "smoothing_window": 3
            },
            "visual": {
                "style": "technical",
                "animations": True,
                "indicators": ["disk"]
            }
        }
        self.create_scene("disk", disk_config)
        
        # 5. 网络详情场景
        network_config = {
            "metadata": {
                "name": "网络详情",
                "description": "详细的网络流量和连接监控",
                "icon": "network-wired",
                "priority": 60
            },
            "collection": {
                "data_range": "all",
                "metrics": ["network", "system"],
                "interval": 1.0,
                "advanced": True
            },
            "processing": {
                "enable_trends": True,
                "enable_predictions": False,
                "smoothing_window": 3
            },
            "visual": {
                "style": "technical",
                "animations": True,
                "indicators": ["network"]
            }
        }
        self.create_scene("network", network_config)
        
        # 设置默认活动场景
        self.active_scene_id = "overview"
        self.logger.info("创建默认场景集，当前活动场景: 'overview'")
        
    def serialize(self) -> Dict[str, Any]:
        """
        序列化所有场景配置
        
        Returns:
            Dict: 序列化的场景配置
        """
        return {
            "active_scene_id": self.active_scene_id,
            "scenes": {scene_id: scene.to_dict() for scene_id, scene in self.scenes.items()}
        }
        
    def deserialize(self, data: Dict[str, Any]) -> None:
        """
        从序列化数据恢复场景配置
        
        Args:
            data: 序列化的场景配置
        """
        # 清除现有场景
        self.scenes = {}
        
        # 恢复场景
        for scene_id, scene_data in data.get("scenes", {}).items():
            self.create_scene(scene_id, scene_data)
            
        # 恢复活动场景
        active_id = data.get("active_scene_id")
        if active_id and active_id in self.scenes:
            self.active_scene_id = active_id
        elif self.scenes:
            self.active_scene_id = next(iter(self.scenes))
        else:
            self.active_scene_id = None
            
        self.logger.info(f"从序列化数据恢复 {len(self.scenes)} 个场景") 