"""
---------------------------------------------------------------
File name:                  config_manager.py
Author:                     Ignorant-lu
Date created:               2024/03/20
Description:                配置管理器实现
----------------------------------------------------------------

Changed history:            
                            2024/03/20: 初始创建;
                            2024/04/04: 添加ConfigEnvironment枚举;
                            2024/04/05: 添加版本控制和升级机制;
----
"""

import os
import json
import logging
import threading
import copy
import time
from typing import Dict, Any, Optional, List, Callable, Union, Set, Tuple
from enum import Enum, auto
import jsonschema
from jsonschema import validate

# 替换为正确的导入路径，临时使用模拟对象
# from status.events import EventSystem, EventType
from status.config.utils import Debounce, FileChangeMonitor, ThreadResourceController, ConfigDiff
from status.config.validators import ConfigValidationError

# 模拟事件系统类
class EventSystem:
    _instance = None
    
    @staticmethod
    def get_instance():
        if EventSystem._instance is None:
            EventSystem._instance = EventSystem()
        return EventSystem._instance
        
    def dispatch_event(self, event_type, data):
        pass

class EventType(Enum):
    CONFIG_CHANGE = auto()


# 配置变更事件类型
class ConfigChangeType(Enum):
    """配置变更类型枚举"""
    ADD = auto()      # 添加配置项
    MODIFY = auto()   # 修改配置项
    DELETE = auto()   # 删除配置项
    RELOAD = auto()   # 重新加载配置


class ConfigEnvironment(Enum):
    """配置环境类型"""
    DEVELOPMENT = "development"  # 开发环境
    TESTING = "testing"          # 测试环境
    PRODUCTION = "production"    # 生产环境


class ConfigurationManager:
    """配置管理器，负责管理应用程序配置"""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls, *args, **kwargs):
        """实现单例模式"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(ConfigurationManager, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        """初始化配置管理器"""
        if hasattr(self, 'initialized'):
            return
            
        self.logger = logging.getLogger("Hollow-ming.Config")
        
        # 配置存储
        self.config: Dict[str, Any] = {}
        
        # 默认配置
        self.default_config: Dict[str, Any] = {}
        
        # 默认配置锁定状态
        self.default_config_locked: bool = True
        
        # 配置模式（用于验证）
        self.schema: Dict[str, Any] = {}
        
        # 当前环境
        self.environment = ConfigEnvironment.DEVELOPMENT
        
        # 环境特定配置文件名模板
        self.env_config_template = "config.{}.json"
        
        # 配置文件路径
        self.config_path = "config.json"
        
        # 默认配置文件路径
        self.default_config_path = "default_config.json"
        
        # 配置模式文件路径
        self.schema_path = "config_schema.json"
        
        # 环境特定配置
        self.env_configs: Dict[ConfigEnvironment, Dict[str, Any]] = {}
        
        # 配置文件监视时间戳
        self.config_file_timestamp = 0
        
        # 配置变更回调
        self.change_callbacks: Dict[str, List[Callable[[str, Any, Any, ConfigChangeType], None]]] = {}
        
        # 文件自动重载标志
        self.auto_reload = False
        
        # 文件监视间隔（秒）
        self.reload_interval = 5
        
        # 文件监视线程
        self.reload_thread = None
        self.reload_thread_stop = False
        
        # 受保护的配置项（不会被用户设置覆盖）
        self.protected_keys: Set[str] = set()
        
        # 差异化保存标志
        self.save_diff_only = True
        
        # 版本升级处理器
        self.version_upgrade_handlers: Dict[str, Dict[str, Callable[[Dict[str, Any], str, str], Dict[str, Any]]]] = {}
        
        # 标记为已初始化
        self.initialized = True
    
    def initialize(self, config_path: Optional[str] = None, 
                  schema_path: Optional[str] = None,
                  default_config_path: Optional[str] = None,
                  auto_reload: bool = False,
                  reload_interval: float = 5,
                  save_diff_only: bool = True,
                  lock_default_config: bool = True,
                  environment: Optional[ConfigEnvironment] = None,
                  env_config_template: Optional[str] = None) -> bool:
        """初始化配置管理器
        
        Args:
            config_path: 配置文件路径
            schema_path: 配置模式文件路径
            default_config_path: 默认配置文件路径
            auto_reload: 是否自动重载文件
            reload_interval: 文件监视间隔（秒）
            save_diff_only: 是否只保存与默认值不同的配置
            lock_default_config: 是否锁定默认配置防止修改
            environment: 当前环境
            env_config_template: 环境特定配置文件名模板
            
        Returns:
            bool: 初始化是否成功
        """
        if config_path:
            self.config_path = config_path
            
        if schema_path:
            self.schema_path = schema_path
            
        if default_config_path:
            self.default_config_path = default_config_path
            
        if environment:
            self.environment = environment
            
        if env_config_template:
            self.env_config_template = env_config_template
            
        self.auto_reload = auto_reload
        self.reload_interval = reload_interval
        self.save_diff_only = save_diff_only
        self.default_config_locked = lock_default_config
        
        success = True
        
        # 先加载默认配置
        if not self.load_default_config():
            self.logger.warning("默认配置加载失败，将使用内建默认值")
            self._set_builtin_defaults()
            success = False
        
        # 加载配置模式
        if os.path.exists(self.schema_path):
            try:
                with open(self.schema_path, 'r', encoding='utf-8') as f:
                    self.schema = json.load(f)
                self.logger.info(f"配置模式已从 {self.schema_path} 加载")
            except Exception as e:
                self.logger.error(f"加载配置模式失败: {str(e)}")
                success = False
        
        # 加载环境特定配置
        self._load_environment_configs()
        
        # 加载用户配置
        if not self.load_config():
            self.logger.warning("用户配置加载失败，将使用默认配置")
            # 使用默认配置的复制
            self.config = copy.deepcopy(self.default_config)
            success = False
        
        # 启动配置文件监视（如果启用）
        if self.auto_reload:
            self._start_file_monitoring()
        
        return success
    
    def load_default_config(self) -> bool:
        """加载默认配置
        
        Returns:
            bool: 加载是否成功
        """
        # 临时解锁默认配置以便加载
        was_locked = self.default_config_locked
        self.default_config_locked = False
        
        try:
            if os.path.exists(self.default_config_path):
                try:
                    with open(self.default_config_path, 'r', encoding='utf-8') as f:
                        self.default_config = json.load(f)
                    self.logger.info(f"默认配置已从 {self.default_config_path} 加载")
                    return True
                except Exception as e:
                    self.logger.error(f"加载默认配置失败: {str(e)}")
                    self._set_builtin_defaults()
                    return False
            else:
                self._set_builtin_defaults()
                self.logger.info("默认配置文件不存在，使用内建默认值")
                return True
        finally:
            # 恢复锁定状态
            self.default_config_locked = was_locked
    
    def _set_builtin_defaults(self) -> None:
        """设置内建默认配置"""
        # 临时解锁默认配置以便设置
        was_locked = self.default_config_locked
        self.default_config_locked = False
        
        try:
            self.default_config = {
                "app": {
                    "name": "Hollow-ming",
                    "version": "0.1.0",
                    "language": "zh_CN",
                    "theme": "default",
                    "debug": False,
                    "first_run": True
                },
                "window": {
                    "width": 800,
                    "height": 600,
                    "fullscreen": False,
                    "always_on_top": False,
                    "frameless": False,
                    "opacity": 1.0
                },
                "graphics": {
                    "fps_limit": 60,
                    "vsync": True,
                    "effects_level": "medium",
                    "animation_speed": 1.0
                },
                "audio": {
                    "enabled": True,
                    "master_volume": 0.7,
                    "music_volume": 0.5,
                    "effects_volume": 0.8,
                    "ambient_volume": 0.6
                },
                "resources": {
                    "theme_pack": "default",
                    "preload_enabled": True,
                    "cache_size_mb": 200
                },
                "controls": {
                    "mouse_sensitivity": 1.0,
                    "double_click_time": 0.5
                }
            }
        finally:
            # 恢复锁定状态
            self.default_config_locked = was_locked
    
    def _load_environment_configs(self) -> None:
        """加载所有环境配置"""
        # 清空现有环境配置
        self.env_configs.clear()
        
        # 加载每个环境的配置
        for env in ConfigEnvironment:
            env_file = self.env_config_template.format(env.value)
            
            if os.path.exists(env_file):
                try:
                    with open(env_file, 'r', encoding='utf-8') as f:
                        env_config = json.load(f)
                        
                    # 验证配置（如果有模式）
                    if self.schema:
                        try:
                            validate(instance=env_config, schema=self.schema)
                        except jsonschema.exceptions.ValidationError as e:
                            self.logger.error(f"环境配置 {env.name} 验证失败: {str(e)}")
                            continue
                    
                    # 保存环境配置
                    self.env_configs[env] = env_config
                    self.logger.info(f"已加载环境配置: {env.name}")
                except Exception as e:
                    self.logger.error(f"加载环境配置 {env.name} 失败: {str(e)}")

    def load_config(self) -> bool:
        """从配置文件加载配置
        
        Returns:
            bool: 加载是否成功
        """
        if not os.path.exists(self.config_path):
            self.logger.warning(f"配置文件 {self.config_path} 不存在，将使用默认配置")
            # 保存默认配置到文件
            if self.save_config():
                self.logger.info(f"默认配置已保存到 {self.config_path}")
            
            # 使用默认配置
            self.config = copy.deepcopy(self.default_config)
            return True
        
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                user_config = json.load(f)
            
            # 更新文件时间戳
            self.config_file_timestamp = os.path.getmtime(self.config_path)
            
            # 如果用户配置为空且启用了差异化保存，表示没有自定义设置
            if not user_config and self.save_diff_only:
                self.logger.info(f"配置文件 {self.config_path} 为空，使用默认配置")
                self.config = copy.deepcopy(self.default_config)
                return True
            
            # 检查版本是否需要升级
            user_version = user_config.get("version")
            default_version = self.default_config.get("version")
            
            # 如果需要升级配置
            if user_version and default_version and self._check_version(user_version, default_version):
                # 执行配置升级
                user_config = self._upgrade_config(user_config)
                
                # 保存升级后的配置
                with open(self.config_path, 'w', encoding='utf-8') as f:
                    json.dump(user_config, f, indent=4, ensure_ascii=False)
                
                self.logger.info(f"配置已从版本 {user_version} 升级到 {default_version}")
            
            # 合并配置
            base_config = copy.deepcopy(self.default_config)
            
            # 1. 合并当前环境配置
            env_config = self.get_environment_config()
            if env_config:
                base_config = self._merge_configs(base_config, env_config)
                self.logger.debug(f"已合并环境配置: {self.environment.name}")
            
            # 2. 合并用户配置
            if self.save_diff_only:
                # 如果启用了差异化保存，用户配置只包含与默认值不同的部分
                merged_config = ConfigDiff.merge_with_defaults(user_config, base_config)
            else:
                # 否则正常合并
                merged_config = self._merge_configs(base_config, user_config)
            
            # 验证配置（如果有模式）
            if self.schema:
                try:
                    jsonschema.validate(instance=merged_config, schema=self.schema)
                except jsonschema.exceptions.ValidationError as e:
                    self.logger.error(f"配置验证失败: {str(e)}")
                    # 回退到默认配置
                    self.config = copy.deepcopy(self.default_config)
                    return False
            
            # 使用合并后的配置
            self.config = merged_config
            self.logger.info(f"配置已从 {self.config_path} 加载并与默认值合并")
            return True
            
        except Exception as e:
            self.logger.error(f"加载配置失败: {str(e)}")
            # 回退到默认配置
            self.config = copy.deepcopy(self.default_config)
            return False
    
    def reload_config(self) -> bool:
        """重新加载配置文件
        
        Returns:
            bool: 重新加载是否成功
        """
        self.logger.info("重新加载配置文件")
        
        # 保存当前配置
        old_config = copy.deepcopy(self.config)
        
        # 重新加载配置
        if not self.load_config():
            return False
        
        # 触发变更事件
        self._trigger_change_event("", self.config, old_config, ConfigChangeType.RELOAD)
        
        # 触发全局事件
        try:
            event_system = EventSystem.get_instance()
            event_system.dispatch_event(EventType.CONFIG_CHANGE, {
                "type": ConfigChangeType.RELOAD.name,
                "old_value": old_config,
                "new_value": self.config
            })
        except Exception as e:
            self.logger.error(f"触发全局配置变更事件时发生错误: {str(e)}")
        
        return True
    
    def save_config(self) -> bool:
        """保存配置到文件
        
        Returns:
            bool: 保存是否成功
        """
        try:
            # 创建目录（如果不存在）
            os.makedirs(os.path.dirname(os.path.abspath(self.config_path)), exist_ok=True)
            
            # 确定要保存的配置
            config_to_save = self.config
            
            # 如果启用差异化保存，只保存与默认值不同的部分
            if self.save_diff_only:
                diff_config = ConfigDiff.get_diff(self.config, self.default_config)
                if diff_config:
                    config_to_save = diff_config
                else:
                    # 如果没有差异，保存一个空对象
                    config_to_save = {}
                    self.logger.debug("没有发现与默认配置的差异，将保存空配置")
            
            # 保存配置
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(config_to_save, f, indent=4, ensure_ascii=False)
            
            # 更新文件时间戳
            self.config_file_timestamp = os.path.getmtime(self.config_path)
            
            self.logger.info(f"配置已保存到 {self.config_path}")
            return True
        except Exception as e:
            self.logger.error(f"保存配置失败: {str(e)}")
            return False
    
    def _merge_configs(self, base_config: Dict[str, Any], override_config: Dict[str, Any]) -> Dict[str, Any]:
        """合并配置
        
        Args:
            base_config: 基础配置
            override_config: 覆盖配置
            
        Returns:
            Dict[str, Any]: 合并后的配置
        """
        result = copy.deepcopy(base_config)
        
        # 递归合并字典
        for key, value in override_config.items():
            # 检查受保护的键
            if key in self.protected_keys:
                continue
                
            # 如果值是字典且基础配置中对应的键也是字典，则递归合并
            if isinstance(value, dict) and isinstance(result.get(key), dict):
                # 检查嵌套路径是否受保护
                nested_protected = False
                for protected_key in self.protected_keys:
                    if '.' in protected_key and protected_key.startswith(f"{key}."):
                        nested_protected = True
                        break
                    
                if nested_protected:
                    # 对于嵌套受保护的路径，递归处理，但不直接赋值整个字典
                    result[key] = self._merge_configs_with_protection(result[key], value)
                else:
                    # 否则正常递归合并
                    result[key] = self._merge_configs(result[key], value)
            else:
                # 检查点号分隔的受保护键
                protected = False
                for protected_key in self.protected_keys:
                    if '.' in protected_key:
                        parts = protected_key.split('.')
                        current_key = parts[0]
                        
                        # 如果当前键是受保护路径的开始部分
                        if current_key == key:
                            # 如果路径长度为1或者匹配完整路径
                            if len(parts) == 1 or '.'.join(parts) == f"{key}":
                                protected = True
                                break
                        
                if not protected:
                    # 如果不受保护，则覆盖或添加新值
                    result[key] = value
        
        return result

    def _merge_configs_with_protection(self, base_config: Dict[str, Any], override_config: Dict[str, Any]) -> Dict[str, Any]:
        """合并配置时处理受保护的嵌套路径
        
        Args:
            base_config: 基础配置
            override_config: 覆盖配置
            
        Returns:
            Dict[str, Any]: 合并后的配置
        """
        result = copy.deepcopy(base_config)
        
        for key, value in override_config.items():
            # 检查当前键是否受保护
            if key in self.protected_keys:
                continue
                
            # 如果是嵌套字典，递归处理
            if isinstance(value, dict) and isinstance(result.get(key), dict):
                result[key] = self._merge_configs_with_protection(
                    result[key],
                    value
                )
            else:
                # 检查此路径是否受保护（针对点号分隔的保护键）
                path_protected = False
                for protected_key in self.protected_keys:
                    if '.' in protected_key:
                        if protected_key.endswith(f".{key}"):
                            path_protected = True
                            break
                    
                if not path_protected:
                    result[key] = value
                
        return result
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取配置项
        
        Args:
            key: 配置项键，支持点号分隔的路径（例如 'app.name'）
            default: 默认值，如果键不存在则返回
            
        Returns:
            Any: 配置项值或默认值
        """
        # 处理点号分隔的路径
        if '.' in key:
            parts = key.split('.')
            current = self.config
            
            for part in parts:
                if isinstance(current, dict) and part in current:
                    current = current[part]
                else:
                    return default
            
            return current
        else:
            return self.config.get(key, default)
    
    def set(self, key: str, value: Any, save: bool = True, validate: bool = True) -> bool:
        """设置配置项
        
        Args:
            key: 配置项键，支持点号分隔的路径
            value: 配置项值
            save: 是否立即保存到文件
            validate: 是否验证新配置
            
        Returns:
            bool: 设置是否成功
        """
        # 保存当前值（用于变更事件）
        old_value = self.get(key)
        
        # 如果值没有变化，直接返回成功
        if old_value == value:
            return True
        
        # 确定变更类型
        change_type = ConfigChangeType.MODIFY
        if old_value is None:
            change_type = ConfigChangeType.ADD
        
        # 处理点号分隔的路径
        if '.' in key:
            parts = key.split('.')
            current = self.config
            
            # 导航到最后一个父节点
            for part in parts[:-1]:
                if part not in current:
                    current[part] = {}
                    
                if not isinstance(current[part], dict):
                    # 如果路径中的某个部分不是字典，则无法设置
                    self.logger.error(f"无法设置配置项 {key}: 路径中的 {part} 不是字典")
                    return False
                    
                current = current[part]
            
            # 设置值
            current[parts[-1]] = value
        else:
            self.config[key] = value
        
        # 验证新配置
        if validate and self.schema:
            try:
                jsonschema.validate(instance=self.config, schema=self.schema)
            except jsonschema.exceptions.ValidationError as e:
                # 回滚修改
                if '.' in key:
                    parts = key.split('.')
                    current = self.config
                    for part in parts[:-1]:
                        current = current[part]
                    
                    if old_value is None:
                        del current[parts[-1]]
                    else:
                        current[parts[-1]] = old_value
                else:
                    if old_value is None:
                        del self.config[key]
                    else:
                        self.config[key] = old_value
                
                self.logger.error(f"配置验证失败: {str(e)}")
                raise ConfigValidationError(f"配置验证失败: {str(e)}")
        
        # 触发变更事件
        self._trigger_change_event(key, value, old_value, change_type)
        
        # 保存配置
        if save:
            return self.save_config()
            
        return True
    
    def delete(self, key: str, save: bool = True) -> bool:
        """删除配置项
        
        Args:
            key: 配置项键，支持点号分隔的路径
            save: 是否立即保存到文件
            
        Returns:
            bool: 删除是否成功
        """
        # 空键无法删除
        if not key:
            self.logger.error("无法删除空键")
            return False
        
        # 保存当前值（用于变更事件）
        old_value = self.get(key)
        
        # 如果键不存在，直接返回成功
        if old_value is None:
            return True
        
        # 处理点号分隔的路径
        if '.' in key:
            parts = key.split('.')
            current = self.config
            
            # 导航到最后一个父节点
            for part in parts[:-1]:
                if part not in current or not isinstance(current[part], dict):
                    # 如果路径不存在，则无法删除
                    return False
                current = current[part]
            
            # 删除键
            if parts[-1] in current:
                del current[parts[-1]]
            else:
                return False
        else:
            if key in self.config:
                del self.config[key]
            else:
                return False
        
        # 触发变更事件
        self._trigger_change_event(key, None, old_value, ConfigChangeType.DELETE)
        
        # 保存配置
        if save:
            return self.save_config()
            
        return True
    
    def reset(self, key: Optional[str] = None, save: bool = True) -> bool:
        """重置配置项到默认值
        
        Args:
            key: 配置项键，支持点号分隔的路径，None表示重置所有配置
            save: 是否立即保存到文件
            
        Returns:
            bool: 重置是否成功
        """
        if key is None:
            # 重置所有配置
            old_config = copy.deepcopy(self.config)
            self.config = copy.deepcopy(self.default_config)
            
            # 触发变更事件
            self._trigger_change_event("", self.config, old_config, ConfigChangeType.RELOAD)
        else:
            # 获取默认值
            default_value = self._get_from_default(key)
            if default_value is not None:
                # 设置为默认值
                return self.set(key, default_value, save)
            else:
                # 如果默认值不存在，则删除该键
                return self.delete(key, save)
        
        # 保存配置
        if save:
            return self.save_config()
            
        return True
    
    def _get_from_default(self, key: str) -> Any:
        """从默认配置获取值
        
        Args:
            key: 配置项键，支持点号分隔的路径
            
        Returns:
            Any: 默认配置值或None
        """
        # 处理点号分隔的路径
        if '.' in key:
            parts = key.split('.')
            current = self.default_config
            
            for part in parts:
                if isinstance(current, dict) and part in current:
                    current = current[part]
                else:
                    return None
            
            return current
        else:
            return self.default_config.get(key)
    
    def register_change_callback(self, callback: Callable[[str, Any, Any, ConfigChangeType], None], 
                                key: str = "") -> None:
        """注册配置变更回调
        
        Args:
            callback: 回调函数，参数为 (key, new_value, old_value, change_type)
            key: 要监听的配置项键，空字符串表示监听所有变更
        """
        if key not in self.change_callbacks:
            self.change_callbacks[key] = []
            
        self.change_callbacks[key].append(callback)
    
    def unregister_change_callback(self, callback: Callable[[str, Any, Any, ConfigChangeType], None], 
                                  key: str = "") -> bool:
        """注销配置变更回调
        
        Args:
            callback: 回调函数
            key: 配置项键
            
        Returns:
            bool: 注销是否成功
        """
        if key in self.change_callbacks and callback in self.change_callbacks[key]:
            self.change_callbacks[key].remove(callback)
            return True
        return False
    
    def _trigger_change_event(self, key: str, new_value: Any, old_value: Any, 
                            change_type: ConfigChangeType) -> None:
        """触发配置变更事件
        
        Args:
            key: 配置项键
            new_value: 新值
            old_value: 旧值
            change_type: 变更类型
        """
        # 触发特定键的回调
        if key in self.change_callbacks:
            for callback in self.change_callbacks[key]:
                try:
                    callback(key, new_value, old_value, change_type)
                except Exception as e:
                    self.logger.error(f"执行配置变更回调时发生错误: {str(e)}")
        
        # 触发全局回调
        if "" in self.change_callbacks:
            for callback in self.change_callbacks[""]:
                try:
                    callback(key, new_value, old_value, change_type)
                except Exception as e:
                    self.logger.error(f"执行配置变更回调时发生错误: {str(e)}")
    
    def set_schema(self, schema: Dict[str, Any]) -> None:
        """设置配置模式
        
        Args:
            schema: JSON Schema模式
        """
        self.schema = schema
    
    def _start_file_monitoring(self) -> None:
        """启动配置文件监视"""
        if self.reload_thread is not None:
            return
            
        self.reload_thread_stop = False
        
        # 创建资源控制器
        resource_controller = ThreadResourceController(max_cpu_percent=5)
        
        # 使用防抖动装饰器，避免频繁重载
        @Debounce(wait_time=0.5)
        def reload_config_debounced():
            self.logger.info("检测到配置文件变更，正在重新加载")
            return self.reload_config()
        
        def monitor_thread():
            current_interval = self.reload_interval
            
            while not self.reload_thread_stop:
                try:
                    if os.path.exists(self.config_path):
                        # 检查文件是否被修改
                        current_timestamp = os.path.getmtime(self.config_path)
                        if current_timestamp > self.config_file_timestamp:
                            reload_config_debounced()
                except Exception as e:
                    self.logger.error(f"监视配置文件时发生错误: {str(e)}")
                
                # 根据系统负载调整间隔
                current_interval = resource_controller.adjust_interval(current_interval)
                
                # 休眠一段时间
                time.sleep(current_interval)
        
        self.reload_thread = threading.Thread(target=monitor_thread)
        self.reload_thread.daemon = True
        self.reload_thread.start()
        self.logger.debug(f"配置文件监视已启动，间隔为 {self.reload_interval} 秒")
    
    def _stop_file_monitoring(self) -> None:
        """停止配置文件监视"""
        if self.reload_thread is None:
            return
            
        self.reload_thread_stop = True
        self.reload_thread.join(timeout=1.0)
        self.reload_thread = None
        self.logger.debug("配置文件监视已停止")
    
    def set_auto_reload(self, enabled: bool, interval: Optional[float] = None) -> None:
        """设置自动重载
        
        Args:
            enabled: 是否启用自动重载
            interval: 监视间隔（秒）
        """
        if interval is not None:
            # 限制间隔范围，避免太频繁的检查
            self.reload_interval = max(0.5, min(interval, 60.0))
            
        if enabled == self.auto_reload:
            # 只更新间隔
            self.logger.debug(f"更新配置文件监视间隔为 {self.reload_interval} 秒")
            return
            
        self.auto_reload = enabled
        
        if enabled:
            self.logger.info(f"启用配置文件自动重载，监视间隔为 {self.reload_interval} 秒")
            self._start_file_monitoring()
        else:
            self.logger.info("禁用配置文件自动重载")
            self._stop_file_monitoring()
    
    def protect_key(self, key: str) -> None:
        """保护配置项，防止用户覆盖
        
        Args:
            key: 配置项键
        """
        self.protected_keys.add(key)
    
    def unprotect_key(self, key: str) -> None:
        """取消保护配置项
        
        Args:
            key: 配置项键
        """
        if key in self.protected_keys:
            self.protected_keys.remove(key)
    
    def validate_config(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """验证配置
        
        Args:
            config: 要验证的配置，None表示验证当前配置
            
        Returns:
            bool: 验证是否通过
            
        Raises:
            ConfigValidationError: 配置验证失败时抛出
        """
        if config is None:
            config = self.config
            
        if not self.schema:
            # 没有模式，无法验证
            return True
            
        try:
            jsonschema.validate(instance=config, schema=self.schema)
            return True
        except jsonschema.exceptions.ValidationError as e:
            self.logger.error(f"配置验证失败: {str(e)}")
            raise ConfigValidationError(f"配置验证失败: {str(e)}")
    
    def export_config(self, path: Optional[str] = None) -> bool:
        """导出配置到文件
        
        Args:
            path: 导出路径，None表示使用默认路径
            
        Returns:
            bool: 导出是否成功
        """
        export_path = path or f"{self.config_path}.export"
        
        try:
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=4, ensure_ascii=False)
                
            self.logger.info(f"配置已导出到 {export_path}")
            return True
        except Exception as e:
            self.logger.error(f"导出配置失败: {str(e)}")
            return False
    
    def import_config(self, path: str, validate: bool = True, save: bool = True) -> bool:
        """从文件导入配置
        
        Args:
            path: 导入路径
            validate: 是否验证导入的配置
            save: 是否保存到默认配置文件
            
        Returns:
            bool: 导入是否成功
            
        Raises:
            ConfigValidationError: 配置验证失败时抛出
        """
        if not os.path.exists(path):
            self.logger.error(f"导入配置失败: 文件 {path} 不存在")
            return False
            
        try:
            with open(path, 'r', encoding='utf-8') as f:
                imported_config = json.load(f)
                
            # 保存旧配置
            old_config = copy.deepcopy(self.config)
            
            # 验证新配置
            if validate and self.schema:
                # 在应用前验证
                try:
                    jsonschema.validate(instance=imported_config, schema=self.schema)
                except jsonschema.exceptions.ValidationError as e:
                    self.logger.error(f"导入的配置验证失败: {str(e)}")
                    raise ConfigValidationError(f"导入的配置验证失败: {str(e)}")
            
            # 合并默认配置和导入配置
            self.config = self._merge_configs(copy.deepcopy(self.default_config), imported_config)
            
            # 触发变更事件
            self._trigger_change_event("", self.config, old_config, ConfigChangeType.RELOAD)
            
            # 保存到文件
            if save:
                return self.save_config()
                
            return True
        except Exception as e:
            if not isinstance(e, ConfigValidationError):
                self.logger.error(f"导入配置失败: {str(e)}")
            return False

    def set_save_diff_only(self, enabled: bool) -> None:
        """设置是否只保存与默认值不同的配置
        
        Args:
            enabled: 是否启用差异化保存
        """
        if self.save_diff_only != enabled:
            self.save_diff_only = enabled
            self.logger.info(f"{'启用' if enabled else '禁用'}配置差异化保存")

    def lock_default_config(self) -> None:
        """锁定默认配置，防止修改"""
        if not self.default_config_locked:
            self.default_config_locked = True
            self.logger.info("默认配置已锁定，防止修改")

    def unlock_default_config(self) -> None:
        """解锁默认配置，允许修改"""
        if self.default_config_locked:
            self.default_config_locked = False
            self.logger.warning("默认配置已解锁，允许修改（不推荐）")

    def set_default_config(self, key: str, value: Any) -> bool:
        """设置默认配置项
        
        Args:
            key: 配置项键，支持点号分隔的路径
            value: 配置项值
            
        Returns:
            bool: 设置是否成功
        """
        if self.default_config_locked:
            self.logger.error("默认配置已锁定，无法修改")
            return False
        
        # 处理点号分隔的路径
        if '.' in key:
            parts = key.split('.')
            current = self.default_config
            
            # 导航到最后一个父节点
            for part in parts[:-1]:
                if part not in current:
                    current[part] = {}
                    
                if not isinstance(current[part], dict):
                    self.logger.error(f"无法设置默认配置项 {key}: 路径中的 {part} 不是字典")
                    return False
                    
                current = current[part]
            
            # 设置值
            current[parts[-1]] = value
        else:
            self.default_config[key] = value
        
        self.logger.info(f"已设置默认配置项: {key} = {value}")
        return True

    def get_environment_config(self, environment: Optional[ConfigEnvironment] = None) -> Dict[str, Any]:
        """获取指定环境的配置
        
        Args:
            environment: 环境，None表示当前环境
            
        Returns:
            Dict[str, Any]: 环境配置
        """
        env = environment or self.environment
        
        return self.env_configs.get(env, {})

    def set_environment(self, environment: ConfigEnvironment) -> bool:
        """设置当前环境并加载对应配置
        
        Args:
            environment: 配置环境
            
        Returns:
            bool: 设置是否成功
        """
        if self.environment == environment:
            return True
            
        old_environment = self.environment
        self.environment = environment
        
        # 保存当前配置
        old_config = copy.deepcopy(self.config)
        
        # 重新加载配置
        if not self.reload_config():
            # 如果加载失败，恢复原环境
            self.environment = old_environment
            self.logger.error(f"切换到环境 {environment.name} 失败，恢复到 {old_environment.name}")
            return False
            
        self.logger.info(f"已切换环境: {old_environment.name} -> {environment.name}")
        return True

    def _compare_versions(self, version1: str, version2: str) -> int:
        """比较两个版本号
        
        Args:
            version1: 第一个版本号
            version2: 第二个版本号
            
        Returns:
            int: 如果version1 > version2返回1，如果version1 < version2返回-1，如果相等返回0
            
        Raises:
            ValueError: 版本号格式无效时抛出
        """
        if not version1 or not version2:
            raise ValueError("版本号不能为空")
        
        try:
            v1_parts = list(map(int, version1.split('.')))
            v2_parts = list(map(int, version2.split('.')))
        except ValueError:
            raise ValueError(f"无效的版本号格式: {version1} 或 {version2}")
        
        # 确保两个版本号有相同的部分数
        while len(v1_parts) < len(v2_parts):
            v1_parts.append(0)
        while len(v2_parts) < len(v1_parts):
            v2_parts.append(0)
        
        # 比较各部分
        for i in range(len(v1_parts)):
            if v1_parts[i] > v2_parts[i]:
                return 1
            elif v1_parts[i] < v2_parts[i]:
                return -1
        
        # 版本号相等
        return 0

    def _check_version(self, user_version: Optional[str], default_version: str) -> bool:
        """检查配置版本是否需要升级
        
        Args:
            user_version: 用户配置版本号，None表示无版本信息
            default_version: 默认配置版本号
            
        Returns:
            bool: 如果需要升级则返回True，否则返回False
            
        Raises:
            ValueError: 版本号格式无效时抛出
        """
        # 如果用户配置没有版本号，认为需要升级
        if user_version is None:
            return True
        
        # 比较版本号
        comparison = self._compare_versions(user_version, default_version)
        
        # 如果用户版本低于默认版本，需要升级
        if comparison < 0:
            self.logger.info(f"检测到配置版本不匹配：用户版本 {user_version}，默认版本 {default_version}")
            return True
        # 如果用户版本高于默认版本，发出警告但不升级
        elif comparison > 0:
            self.logger.warning(f"用户配置版本 {user_version} 高于默认版本 {default_version}，可能导致兼容性问题")
            return False
        # 版本相同，不需要升级
        else:
            return False

    def _find_upgrade_path(self, from_version: str, to_version: str) -> List[Tuple[str, str, Callable]]:
        """查找从一个版本升级到另一个版本的路径
        
        Args:
            from_version: 起始版本
            to_version: 目标版本
            
        Returns:
            List[Tuple[str, str, Callable]]: 升级路径，每一步包含起始版本、目标版本和处理函数
        """
        # 找出所有可能的升级路径
        path = []
        current_version = from_version
        
        while self._compare_versions(current_version, to_version) < 0:
            found_next_step = False
            
            # 查找注册的直接升级处理器
            if current_version in self.version_upgrade_handlers:
                handlers = self.version_upgrade_handlers[current_version]
                
                # 直接检查是否存在从当前版本到目标版本的处理器
                if to_version in handlers:
                    handler = handlers[to_version]
                    path.append((current_version, to_version, handler))
                    current_version = to_version
                    found_next_step = True
                    break
                
                # 找到一个可行的下一步
                for next_version, handler in handlers.items():
                    if self._compare_versions(next_version, to_version) <= 0:
                        path.append((current_version, next_version, handler))
                        current_version = next_version
                        found_next_step = True
                        break
            
            if not found_next_step:
                # 如果找不到升级路径，创建默认的升级处理器
                self.logger.warning(f"找不到从版本 {current_version} 到 {to_version} 的升级路径，将使用默认合并")
                def default_handler(old_config, old_ver, new_ver):
                    # 使用合并策略创建一个带有新版本号的配置
                    new_config = copy.deepcopy(old_config)
                    new_config["version"] = new_ver
                    return self._merge_configs(new_config, self.default_config)
                    
                path.append((current_version, to_version, default_handler))
                current_version = to_version
        
        return path

    def _upgrade_config(self, user_config: Dict[str, Any]) -> Dict[str, Any]:
        """升级用户配置到最新版本
        
        Args:
            user_config: 用户配置
            
        Returns:
            Dict[str, Any]: 升级后的配置
            
        Raises:
            ValueError: 配置版本高于默认版本时抛出
        """
        # 获取配置版本
        user_version = user_config.get("version")
        default_version = self.default_config.get("version")
        
        # 如果用户配置没有版本信息，添加默认版本并返回合并后的配置
        if not user_version:
            self.logger.warning("用户配置缺少版本信息，将添加默认版本")
            user_config["version"] = default_version
            return self._merge_configs(self.default_config, user_config)
        
        # 如果用户版本高于默认版本，防止降级
        if self._compare_versions(user_version, default_version) > 0:
            raise ValueError(f"无法将配置从高版本 {user_version} 降级到 {default_version}")
        
        # 如果版本已经匹配，无需升级
        if user_version == default_version:
            return user_config
        
        # 查找升级路径
        upgrade_path = self._find_upgrade_path(user_version, default_version)
        
        # 依次执行升级
        current_config = copy.deepcopy(user_config)
        
        for from_ver, to_ver, handler in upgrade_path:
            self.logger.info(f"升级配置：{from_ver} -> {to_ver}")
            current_config = handler(current_config, from_ver, to_ver)
            
            # 确保版本号已更新
            current_config["version"] = to_ver
        
        return current_config

    def register_version_upgrade(self, from_version: str, to_version: str, 
                              handler: Callable[[Dict[str, Any], str, str], Dict[str, Any]]) -> None:
        """注册版本升级处理函数
        
        Args:
            from_version: 起始版本
            to_version: 目标版本
            handler: 升级处理函数，参数为(old_config, old_version, new_version)
        """
        # 确保版本格式有效
        try:
            self._compare_versions(from_version, to_version)
        except ValueError as e:
            self.logger.error(f"无法注册版本升级处理程序: {str(e)}")
            return
        
        # 初始化处理器字典（如果不存在）
        if from_version not in self.version_upgrade_handlers:
            self.version_upgrade_handlers[from_version] = {}
        
        # 注册处理器
        self.version_upgrade_handlers[from_version][to_version] = handler
        self.logger.info(f"已注册版本升级处理程序: {from_version} -> {to_version}")


# 创建全局单例实例
config_manager = ConfigurationManager() 