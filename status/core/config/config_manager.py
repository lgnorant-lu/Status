"""
---------------------------------------------------------------
File name:                  config_manager.py
Author:                     Ignorant-lu
Date created:               2025/04/05
Description:                配置管理器实现
----------------------------------------------------------------

Changed history:            
                            2025/04/05: 初始创建;
----
"""

import os
import json
import logging
from typing import Any, Dict, List, Optional, Union, Callable

from status.core.config.config_types import DEFAULT_CONFIG, DEFAULT_CONFIG_FILE, ConfigEventType

# 获取日志记录器
logger = logging.getLogger(__name__)


class ConfigManager:
    """配置管理器类"""
    
    _instance = None
    
    @classmethod
    def get_instance(cls):
        """获取单例实例"""
        if cls._instance is None:
            cls._instance = ConfigManager()
        return cls._instance
    
    def __init__(self):
        """初始化配置管理器"""
        self.config = {}
        self.event_listeners = []
        self.load_default_config()
    
    def load_default_config(self):
        """加载默认配置"""
        self.config = DEFAULT_CONFIG.copy()
        logger.debug("已加载默认配置")
    
    def load_config(self, config_file: Optional[str] = None) -> bool:
        """从文件加载配置
        
        Args:
            config_file: 配置文件路径，如果为None则使用默认路径
            
        Returns:
            bool: 是否成功加载配置
        """
        if config_file is None:
            config_file = DEFAULT_CONFIG_FILE
        
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                loaded_config = json.load(f)
                # 使用递归更新，保留默认配置中存在但加载的配置中不存在的项
                self._update_config_recursive(self.config, loaded_config)
                logger.info(f"已从 {config_file} 加载配置")
                self._notify_listeners(ConfigEventType.CONFIG_LOADED, None, None)
                return True
        except FileNotFoundError:
            logger.warning(f"配置文件不存在: {config_file}")
            return False
        except json.JSONDecodeError:
            logger.warning(f"配置文件格式错误: {config_file}")
            return False
        except Exception as e:
            logger.error(f"加载配置文件时出错: {str(e)}")
            return False
    
    def save_config(self, config_file: Optional[str] = None) -> bool:
        """保存配置到文件
        
        Args:
            config_file: 配置文件路径，如果为None则使用默认路径
            
        Returns:
            bool: 是否成功保存配置
        """
        if config_file is None:
            config_file = DEFAULT_CONFIG_FILE
        
        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(config_file), exist_ok=True)
            
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
                logger.info(f"已保存配置到 {config_file}")
                self._notify_listeners(ConfigEventType.CONFIG_SAVED, None, None)
                return True
        except Exception as e:
            logger.error(f"保存配置文件时出错: {str(e)}")
            return False
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取配置项
        
        支持使用点号访问嵌套配置，例如 "launcher.grid_columns"
        
        Args:
            key: 配置项键名
            default: 如果配置项不存在，返回的默认值
            
        Returns:
            Any: 配置项的值，如果不存在则返回默认值
        """
        if "." in key:
            # 处理嵌套配置
            parts = key.split(".")
            current = self.config
            
            for part in parts:
                if isinstance(current, dict) and part in current:
                    current = current[part]
                else:
                    return default
            
            return current
        else:
            # 处理简单配置
            return self.config.get(key, default)
    
    def set(self, key: str, value: Any) -> bool:
        """设置配置项
        
        支持使用点号设置嵌套配置，例如 "launcher.grid_columns"
        
        Args:
            key: 配置项键名
            value: 配置项的新值
            
        Returns:
            bool: 是否成功设置配置项
        """
        try:
            if "." in key:
                # 处理嵌套配置
                parts = key.split(".")
                current = self.config
                last_part = parts[-1]
                old_value = None
                
                # 导航到最后一级的父级
                for part in parts[:-1]:
                    if part not in current:
                        current[part] = {}
                    current = current[part]
                
                # 获取旧值（如果存在）
                if last_part in current:
                    old_value = current[last_part]
                
                # 设置新值
                current[last_part] = value
                
                # 如果值发生变化，触发事件
                if old_value != value:
                    self._notify_listeners(key, old_value, value)
            else:
                # 处理简单配置
                old_value = self.config.get(key)
                self.config[key] = value
                
                # 如果值发生变化，触发事件
                if old_value != value:
                    self._notify_listeners(key, old_value, value)
            
            return True
        except Exception as e:
            logger.error(f"设置配置项时出错: {str(e)}")
            return False
    
    def _update_config_recursive(self, target: Dict, source: Dict) -> None:
        """递归更新配置字典
        
        将source中的内容更新到target中，保留target中已有但source中不存在的项
        
        Args:
            target: 目标字典
            source: 源字典
        """
        for key, value in source.items():
            if key in target and isinstance(target[key], dict) and isinstance(value, dict):
                # 如果两边都是字典，递归更新
                self._update_config_recursive(target[key], value)
            else:
                # 否则直接覆盖
                target[key] = value
    
    def add_listener(self, listener: Callable) -> None:
        """添加配置更改监听器
        
        Args:
            listener: 监听器函数，接收三个参数(key, old_value, new_value)
        """
        if listener not in self.event_listeners:
            self.event_listeners.append(listener)
    
    def remove_listener(self, listener: Callable) -> None:
        """移除配置更改监听器
        
        Args:
            listener: 要移除的监听器函数
        """
        if listener in self.event_listeners:
            self.event_listeners.remove(listener)
    
    def _notify_listeners(self, key: str, old_value: Any, new_value: Any) -> None:
        """通知所有监听器配置已更改
        
        Args:
            key: 更改的配置项键名
            old_value: 旧值
            new_value: 新值
        """
        for listener in self.event_listeners:
            try:
                listener(key, old_value, new_value)
            except Exception as e:
                logger.error(f"通知配置监听器时出错: {str(e)}")
    
    def reset_to_defaults(self) -> None:
        """重置所有配置到默认值"""
        self.config = DEFAULT_CONFIG.copy()
        logger.info("已重置所有配置到默认值")
        self._notify_listeners(ConfigEventType.CONFIG_LOADED, None, None) 