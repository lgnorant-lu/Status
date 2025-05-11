"""
---------------------------------------------------------------
File name:                  factory.py
Author:                     Ignorant-lu
Date created:               2025/04/04
Description:                监控系统工厂，提供创建监控系统的便捷方法
----------------------------------------------------------------

Changed history:            
                            2025/04/04: 初始创建;
----
"""

import logging
from typing import Dict, Any, Optional

from .data_collector import SystemDataCollector
from .data_processor import DataProcessor
from .visualization import VisualMapper
from .scene_manager import SceneManager
from .monitor_manager import MonitorManager


def create_monitor_system(config: Optional[Dict[str, Any]] = None) -> MonitorManager:
    """
    创建一个完整的监控系统
    
    Args:
        config: 监控系统配置
        
    Returns:
        MonitorManager: 监控管理器实例
    """
    logger = logging.getLogger("MonitorFactory")
    config = config or {}
    
    # 创建数据采集器
    logger.info("创建数据采集器")
    data_collector = SystemDataCollector(config.get("data_collector", {}))
    
    # 创建数据处理器
    logger.info("创建数据处理器")
    data_processor = DataProcessor(config.get("data_processor", {}))
    
    # 创建可视化映射器
    logger.info("创建可视化映射器")
    visual_mapper = VisualMapper(config.get("visual_mapper", {}))
    
    # 创建场景管理器
    logger.info("创建场景管理器")
    scene_manager = SceneManager(config.get("scene_manager", {}))
    
    # 如果配置中要求创建默认场景，则创建
    if config.get("create_default_scenes", True):
        logger.info("创建默认场景")
        scene_manager.create_default_scenes()
        
    # 创建监控管理器
    logger.info("创建监控管理器")
    monitor_manager = MonitorManager(
        data_collector=data_collector,
        data_processor=data_processor,
        visual_mapper=visual_mapper,
        scene_manager=scene_manager,
        config=config.get("monitor_manager", {})
    )
    
    # 如果配置中要求自动启动，则启动监控
    if config.get("auto_start", False):
        logger.info("自动启动监控")
        monitor_manager.start()
        
    return monitor_manager
    
    
def create_custom_monitor_system(
    data_collector: Optional[SystemDataCollector] = None,
    data_processor: Optional[DataProcessor] = None,
    visual_mapper: Optional[VisualMapper] = None,
    scene_manager: Optional[SceneManager] = None,
    config: Optional[Dict[str, Any]] = None,
    auto_start: bool = False
) -> MonitorManager:
    """
    创建一个自定义组件的监控系统
    
    Args:
        data_collector: 自定义的数据采集器
        data_processor: 自定义的数据处理器
        visual_mapper: 自定义的可视化映射器
        scene_manager: 自定义的场景管理器
        config: 监控系统配置
        auto_start: 是否自动启动
        
    Returns:
        MonitorManager: 监控管理器实例
    """
    logger = logging.getLogger("MonitorFactory")
    config = config or {}
    
    # 创建监控管理器
    logger.info("创建自定义监控系统")
    monitor_manager = MonitorManager(
        data_collector=data_collector,
        data_processor=data_processor,
        visual_mapper=visual_mapper,
        scene_manager=scene_manager,
        config=config
    )
    
    # 如果要求自动启动，则启动监控
    if auto_start:
        logger.info("自动启动监控")
        monitor_manager.start()
        
    return monitor_manager
    
    
def create_minimal_monitor_system(config: Optional[Dict[str, Any]] = None) -> MonitorManager:
    """
    创建一个最小化的监控系统（资源占用较少）
    
    Args:
        config: 监控系统配置
        
    Returns:
        MonitorManager: 监控管理器实例
    """
    logger = logging.getLogger("MonitorFactory")
    config = config or {}
    
    # 配置最小化数据采集器
    collector_config = {
        "advanced_metrics": False,
        "io_stats": False,
        "network_stats": False,
        "process_stats": False,
        "collection_interval": 5.0,  # 较长的采集间隔
        "threshold_values": {
            "cpu": {
                "warning": 80,
                "critical": 95
            },
            "memory": {
                "warning": 80,
                "critical": 90
            },
            "disk": {
                "warning": 85,
                "critical": 95
            }
        }
    }
    
    # 合并用户配置
    if "data_collector" in config:
        for key, value in config["data_collector"].items():
            collector_config[key] = value
            
    # 创建数据采集器
    logger.info("创建最小化数据采集器")
    data_collector = SystemDataCollector(collector_config)
    
    # 配置最小化数据处理器
    processor_config = {
        "enable_trends": False,
        "enable_predictions": False,
        "smoothing_window": 2,
        "max_history_size": 20
    }
    
    # 合并用户配置
    if "data_processor" in config:
        for key, value in config["data_processor"].items():
            processor_config[key] = value
            
    # 创建数据处理器
    logger.info("创建最小化数据处理器")
    data_processor = DataProcessor(processor_config)
    
    # 配置最小化可视化映射器
    visual_config = {
        "animations": {
            "normal": {
                "speed": 0.8,
                "scale": 0.9,
                "effects": []
            },
            "warning": {
                "speed": 1.0,
                "scale": 1.0,
                "effects": []
            },
            "danger": {
                "speed": 1.2,
                "scale": 1.1,
                "effects": ["pulse"]
            }
        }
    }
    
    # 合并用户配置
    if "visual_mapper" in config:
        for key, value in config["visual_mapper"].items():
            visual_config[key] = value
            
    # 创建可视化映射器
    logger.info("创建最小化可视化映射器")
    visual_mapper = VisualMapper(visual_config)
    
    # 配置最小化场景管理器
    scene_config = {}
    
    # 合并用户配置
    if "scene_manager" in config:
        for key, value in config["scene_manager"].items():
            scene_config[key] = value
            
    # 创建场景管理器
    logger.info("创建最小化场景管理器")
    scene_manager = SceneManager(scene_config)
    
    # 创建最小的默认场景
    logger.info("创建最小化默认场景")
    minimal_scene_config = {
        "metadata": {
            "name": "系统状态",
            "description": "简要系统状态监控",
            "icon": "chart-bar",
            "priority": 100
        },
        "collection": {
            "data_range": "minimal",
            "metrics": ["cpu", "memory", "disk"],
            "interval": 5.0,
            "advanced": False
        },
        "processing": {
            "enable_trends": False,
            "enable_predictions": False,
            "smoothing_window": 2
        },
        "visual": {
            "style": "minimal",
            "animations": False,
            "indicators": ["cpu", "memory", "disk"]
        }
    }
    scene_manager.create_scene("minimal", minimal_scene_config)
    scene_manager.set_active_scene("minimal")
    
    # 创建监控管理器
    monitor_config = {
        "update_interval": 5.0  # 较长的更新间隔
    }
    
    # 合并用户配置
    if "monitor_manager" in config:
        for key, value in config["monitor_manager"].items():
            monitor_config[key] = value
            
    logger.info("创建最小化监控管理器")
    monitor_manager = MonitorManager(
        data_collector=data_collector,
        data_processor=data_processor,
        visual_mapper=visual_mapper,
        scene_manager=scene_manager,
        config=monitor_config
    )
    
    # 如果配置中要求自动启动，则启动监控
    if config.get("auto_start", False):
        logger.info("自动启动监控")
        monitor_manager.start()
        
    return monitor_manager
    
    
def create_debug_monitor_system(config: Optional[Dict[str, Any]] = None) -> MonitorManager:
    """
    创建一个调试用的监控系统（详细日志输出）
    
    Args:
        config: 监控系统配置
        
    Returns:
        MonitorManager: 监控管理器实例
    """
    logger = logging.getLogger("MonitorFactory")
    logger.setLevel(logging.DEBUG)
    
    # 配置日志处理器
    for handler in logger.handlers:
        handler.setLevel(logging.DEBUG)
        
    # 设置模块日志级别
    logging.getLogger("SystemDataCollector").setLevel(logging.DEBUG)
    logging.getLogger("DataProcessor").setLevel(logging.DEBUG)
    logging.getLogger("VisualMapper").setLevel(logging.DEBUG)
    logging.getLogger("SceneManager").setLevel(logging.DEBUG)
    logging.getLogger("MonitorManager").setLevel(logging.DEBUG)
    
    logger.debug("创建调试模式监控系统")
    
    # 创建基本监控系统
    monitor_manager = create_monitor_system(config)
    
    # 添加数据回调，用于输出调试信息
    def debug_callback(visual_params):
        logger.debug(f"系统状态: {visual_params.get('summary', {}).get('status', 'unknown')}")
        alerts = visual_params.get('alerts', [])
        if alerts:
            logger.debug(f"系统告警: {len(alerts)} 条")
            for alert in alerts:
                logger.debug(f"  - [{alert.get('level', 'unknown')}] {alert.get('message', '')}")
                
    monitor_manager.register_update_callback(debug_callback)
    
    logger.debug("调试监控系统创建完成")
    return monitor_manager 