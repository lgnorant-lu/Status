"""
---------------------------------------------------------------
File name:                  log_manager.py
Author:                     Ignorant-lu
Date created:               2025/05/14
Description:                日志管理器实现
----------------------------------------------------------------

Changed history:            
                            2025/05/14: 初始创建;
----
"""

import os
import json
import logging
import logging.handlers
from datetime import datetime
from typing import Dict, Optional, List, Any, Union
import threading

class LogManager:
    """日志管理器类，负责创建、配置和管理日志器

    该类使用单例模式，确保整个应用中只有一个日志管理实例。
    支持多级别日志记录、文件轮转和格式化输出。
    """
    
    # 单例实例
    _instance = None
    _lock = threading.Lock()
    _initialized: bool = False
    
    # 日志级别映射
    _LEVEL_MAP = {
        'debug': logging.DEBUG,
        'info': logging.INFO,
        'warning': logging.WARNING,
        'error': logging.ERROR,
        'critical': logging.CRITICAL
    }
    
    def __new__(cls, *args, **kwargs):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(LogManager, cls).__new__(cls)
                cls._instance._initialized = False
            return cls._instance
    
    def __init__(self, config_path: Optional[str] = None):
        """初始化日志管理器

        Args:
            config_path: 日志配置文件路径，如果为None则使用默认配置
        """
        # 防止重复初始化
        if self._initialized:
            return
            
        self._initialized = True
        self._loggers: Dict[str, logging.Logger] = {}
        self._memory_handler = None
        self._memory_records: List[Dict[str, Any]] = []
        self._memory_capacity = 100  # 默认内存中保留100条日志
        
        # 加载配置
        self._config = self._load_config(config_path)
        
        # 创建日志目录
        self._ensure_log_directory()
        
        # 创建根日志器
        self._setup_root_logger()
        
        # 记录日志系统启动信息
        root_logger = self.get_logger("root")
        root_logger.info("日志系统初始化完成")
    
    def _load_config(self, config_path: Optional[str]) -> Dict[str, Any]:
        """加载日志配置

        Args:
            config_path: 配置文件路径

        Returns:
            配置字典
        """
        default_config = {
            "version": 1,
            "root": {
                "level": "info",
                "handlers": ["console", "file", "memory"]
            },
            "formatters": {
                "standard": {
                    "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
                    "datefmt": "%Y-%m-%d %H:%M:%S"
                },
                "simple": {
                    "format": "%(levelname)s: %(message)s"
                }
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "level": "info",
                    "formatter": "simple"
                },
                "file": {
                    "class": "logging.handlers.RotatingFileHandler",
                    "level": "debug",
                    "formatter": "standard",
                    "filename": "status.log",
                    "maxBytes": 10485760,  # 10MB
                    "backupCount": 5,
                    "encoding": "utf-8"
                },
                "memory": {
                    "class": "memory",
                    "level": "error",
                    "capacity": 100
                }
            },
            "loggers": {}
        }
        
        if config_path and os.path.exists(config_path):
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    # 合并配置
                    return self._merge_configs(default_config, config)
            except Exception as e:
                print(f"加载日志配置失败: {e}，使用默认配置")
        
        return default_config
    
    def _merge_configs(self, default_config: Dict[str, Any], user_config: Dict[str, Any]) -> Dict[str, Any]:
        """合并默认配置和用户配置

        Args:
            default_config: 默认配置
            user_config: 用户配置

        Returns:
            合并后的配置
        """
        # 这里实现简单的合并，实际可能需要更复杂的深度合并
        result = default_config.copy()
        
        for key, value in user_config.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key].update(value)
            else:
                result[key] = value
                
        return result
    
    def _ensure_log_directory(self):
        """确保日志目录存在"""
        log_dir = "logs"
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
    
    def _setup_root_logger(self):
        """设置根日志器配置"""
        # 配置根日志器
        root_config = self._config["root"]
        root_logger = logging.getLogger()
        root_logger.setLevel(self._get_level(root_config.get("level", "info")))
        
        # 清除已有处理器
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
        
        # 添加处理器
        for handler_name in root_config.get("handlers", []):
            if handler_name in self._config["handlers"]:
                handler_config = self._config["handlers"][handler_name]
                handler = self._create_handler(handler_name, handler_config)
                if handler:
                    root_logger.addHandler(handler)
    
    def _create_handler(self, name: str, config: Dict[str, Any]) -> Optional[logging.Handler]:
        """创建日志处理器

        Args:
            name: 处理器名称
            config: 处理器配置

        Returns:
            日志处理器实例
        """
        handler_class = config.get("class", "")
        level = self._get_level(config.get("level", "info"))
        formatter_name = config.get("formatter", "standard")
        
        handler = None
        
        # 控制台处理器
        if handler_class == "logging.StreamHandler":
            handler = logging.StreamHandler()
        
        # 文件处理器
        elif handler_class == "logging.handlers.RotatingFileHandler":
            filename = os.path.join("logs", config.get("filename", "status.log"))
            max_bytes = config.get("maxBytes", 10485760)  # 默认10MB
            backup_count = config.get("backupCount", 5)
            encoding = config.get("encoding", "utf-8")
            
            handler = logging.handlers.RotatingFileHandler(
                filename=filename,
                maxBytes=max_bytes,
                backupCount=backup_count,
                encoding=encoding
            )
        
        # 内存处理器（自定义）
        elif handler_class == "memory":
            capacity = config.get("capacity", 100)
            self._memory_capacity = capacity
            
            # 创建内存处理器，稍后添加到内存记录列表中
            class MemoryHandler(logging.Handler):
                def __init__(self, manager):
                    super().__init__()
                    self.manager = manager
                
                def emit(self, record):
                    self.manager._add_memory_record(record)
            
            handler = MemoryHandler(self)
            self._memory_handler = handler
        
        # 设置处理器级别和格式化器
        if handler:
            handler.setLevel(level)
            
            if formatter_name in self._config["formatters"]:
                formatter_config = self._config["formatters"][formatter_name]
                fmt = formatter_config.get("format", "%(message)s")
                datefmt = formatter_config.get("datefmt", None)
                formatter = logging.Formatter(fmt=fmt, datefmt=datefmt)
                handler.setFormatter(formatter)
        
        return handler
    
    def _get_level(self, level_name: str) -> int:
        """获取日志级别

        Args:
            level_name: 级别名称

        Returns:
            日志级别值
        """
        level_name = level_name.lower()
        return self._LEVEL_MAP.get(level_name, logging.INFO)
    
    def _add_memory_record(self, record: logging.LogRecord):
        """添加日志记录到内存

        Args:
            record: 日志记录
        """
        # 格式化记录
        formatted_record = {
            "time": datetime.fromtimestamp(record.created).strftime("%Y-%m-%d %H:%M:%S"),
            "level": record.levelname,
            "name": record.name,
            "message": record.getMessage(),
            "file": record.pathname,
            "line": record.lineno,
            "function": record.funcName
        }
        
        # 添加异常信息（如果有）
        if record.exc_info:
            formatted_record["exception"] = self._format_exception(record.exc_info)
        
        # 添加记录到内存列表
        self._memory_records.append(formatted_record)
        
        # 限制内存记录数量
        if len(self._memory_records) > self._memory_capacity:
            self._memory_records.pop(0)
    
    def _format_exception(self, exc_info) -> str:
        """格式化异常信息

        Args:
            exc_info: 异常信息

        Returns:
            格式化后的异常字符串
        """
        import traceback
        return "".join(traceback.format_exception(*exc_info))
    
    def get_logger(self, name: str) -> logging.Logger:
        """获取指定名称的日志器

        Args:
            name: 日志器名称

        Returns:
            日志器实例
        """
        if name in self._loggers:
            return self._loggers[name]
        
        logger = logging.getLogger(name)
        
        # 检查配置中是否有特定的日志器配置
        if name in self._config.get("loggers", {}):
            logger_config = self._config["loggers"][name]
            level = logger_config.get("level", None)
            if level:
                logger.setLevel(self._get_level(level))
            
            # 如果配置了propagate为False，则不继承父日志器的处理器
            propagate = logger_config.get("propagate", True)
            logger.propagate = propagate
            
            # 如果配置了特定的处理器，则添加
            handlers = logger_config.get("handlers", [])
            if handlers:
                # 清除已有处理器
                for handler in logger.handlers[:]:
                    logger.removeHandler(handler)
                
                # 添加处理器
                for handler_name in handlers:
                    if handler_name in self._config["handlers"]:
                        handler_config = self._config["handlers"][handler_name]
                        handler = self._create_handler(handler_name, handler_config)
                        if handler:
                            logger.addHandler(handler)
        
        self._loggers[name] = logger
        return logger
    
    def get_memory_records(self) -> List[Dict[str, Any]]:
        """获取内存中的日志记录

        Returns:
            内存中的日志记录列表
        """
        return self._memory_records.copy()
    
    def save_config(self, config_path: str) -> bool:
        """保存当前配置到文件

        Args:
            config_path: 配置文件路径

        Returns:
            是否保存成功
        """
        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(config_path), exist_ok=True)
            
            # 保存配置
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(self._config, f, indent=4, ensure_ascii=False)
            
            return True
        except Exception as e:
            print(f"保存日志配置失败: {e}")
            return False


# 单例获取函数
_log_manager = None
_manager_lock = threading.Lock()

def get_logger(name: str = "root") -> logging.Logger:
    """获取日志器实例
    
    这是一个便捷函数，用于获取日志器实例。
    首次调用时会初始化LogManager。

    Args:
        name: 日志器名称

    Returns:
        日志器实例
    """
    global _log_manager
    
    if _log_manager is None:
        with _manager_lock:
            if _log_manager is None:
                # 尝试查找配置文件
                config_paths = [
                    "status/config/logging.json",
                    "config/logging.json",
                ]
                
                config_path = None
                for path in config_paths:
                    if os.path.exists(path):
                        config_path = path
                        break
                
                _log_manager = LogManager(config_path)
    
    return _log_manager.get_logger(name) 