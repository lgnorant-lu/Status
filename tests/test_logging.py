"""
---------------------------------------------------------------
File name:                  test_logging.py
Author:                     Ignorant-lu
Date created:               2025/05/14
Description:                日志系统测试模块
----------------------------------------------------------------

Changed history:            
                            2025/05/14: 初始创建;
----
"""

import os
import sys
import unittest
import logging
import tempfile
import json
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# 导入日志模块
from status.core.logging import LogManager, get_logger, log


class TestLogging(unittest.TestCase):
    """日志系统测试类"""
    
    def setUp(self):
        """测试前的设置"""
        # 创建临时配置文件
        self.temp_dir = tempfile.TemporaryDirectory()
        self.config_path = os.path.join(self.temp_dir.name, "logging.json")
        
        # 创建临时日志目录
        self.log_dir = os.path.join(self.temp_dir.name, "logs")
        os.makedirs(self.log_dir, exist_ok=True)
        
        # 临时配置
        self.config = {
            "version": 1,
            "root": {
                "level": "info",
                "handlers": ["test_console", "test_file"]
            },
            "formatters": {
                "test_formatter": {
                    "format": "TEST: %(message)s"
                }
            },
            "handlers": {
                "test_console": {
                    "class": "logging.StreamHandler",
                    "level": "info",
                    "formatter": "test_formatter"
                },
                "test_file": {
                    "class": "logging.handlers.RotatingFileHandler",
                    "level": "debug",
                    "formatter": "test_formatter",
                    "filename": os.path.join(self.log_dir, "test.log"),
                    "maxBytes": 1024,
                    "backupCount": 3,
                    "encoding": "utf-8"
                }
            },
            "loggers": {
                "test_logger": {
                    "level": "debug",
                    "handlers": ["test_file"],
                    "propagate": False
                }
            }
        }
        
        # 保存配置
        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=4)
    
    def tearDown(self):
        """测试后的清理"""
        # 清理临时目录
        self.temp_dir.cleanup()
    
    def test_log_manager_singleton(self):
        """测试日志管理器单例模式"""
        # 创建两个实例
        manager1 = LogManager(self.config_path)
        manager2 = LogManager(self.config_path)
        
        # 验证是同一个实例
        self.assertIs(manager1, manager2)
    
    def test_get_logger(self):
        """测试获取日志器"""
        # 使用不同名称获取日志器
        logger1 = get_logger("test1")
        logger2 = get_logger("test1")  # 相同名称
        logger3 = get_logger("test2")  # 不同名称
        
        # 验证相同名称返回相同实例，不同名称返回不同实例
        self.assertIs(logger1, logger2)
        self.assertIsNot(logger1, logger3)
        
        # 验证类型
        self.assertIsInstance(logger1, logging.Logger)
    
    def test_log_levels(self):
        """测试日志级别"""
        # 创建临时日志文件
        log_file = os.path.join(self.log_dir, "level_test.log")
        
        # 创建临时配置
        level_config = {
            "version": 1,
            "root": {
                "level": "warning",  # 只记录warning及以上级别
                "handlers": ["level_file"]
            },
            "formatters": {
                "simple": {
                    "format": "%(levelname)s: %(message)s"
                }
            },
            "handlers": {
                "level_file": {
                    "class": "logging.FileHandler",
                    "level": "warning",
                    "formatter": "simple",
                    "filename": log_file,
                    "encoding": "utf-8"
                }
            }
        }
        
        # 保存配置
        level_config_path = os.path.join(self.temp_dir.name, "level_config.json")
        with open(level_config_path, 'w', encoding='utf-8') as f:
            json.dump(level_config, f, indent=4)
        
        # 创建日志管理器
        manager = LogManager(level_config_path)
        test_logger = manager.get_logger("level_test")
        
        # 记录不同级别的日志
        test_logger.debug("Debug message")    # 不应该记录
        test_logger.info("Info message")      # 不应该记录
        test_logger.warning("Warning message")  # 应该记录
        test_logger.error("Error message")      # 应该记录
        test_logger.critical("Critical message")  # 应该记录
        
        # 读取日志文件
        with open(log_file, 'r', encoding='utf-8') as f:
            log_content = f.read()
        
        # 验证日志内容
        self.assertNotIn("Debug message", log_content)
        self.assertNotIn("Info message", log_content)
        self.assertIn("Warning message", log_content)
        self.assertIn("Error message", log_content)
        self.assertIn("Critical message", log_content)
    
    def test_memory_records(self):
        """测试内存记录功能"""
        # 创建临时配置
        memory_config = {
            "version": 1,
            "root": {
                "level": "debug",
                "handlers": ["memory_handler"]
            },
            "handlers": {
                "memory_handler": {
                    "class": "memory",
                    "level": "debug",
                    "capacity": 5  # 只保留最近5条记录
                }
            }
        }
        
        # 保存配置
        memory_config_path = os.path.join(self.temp_dir.name, "memory_config.json")
        with open(memory_config_path, 'w', encoding='utf-8') as f:
            json.dump(memory_config, f, indent=4)
        
        # 创建日志管理器
        manager = LogManager(memory_config_path)
        memory_logger = manager.get_logger("memory_test")
        
        # 记录6条日志
        for i in range(6):
            memory_logger.debug(f"Memory test message {i}")
        
        # 获取内存记录
        records = manager.get_memory_records()
        
        # 验证只保留了最近5条记录
        self.assertEqual(len(records), 5)
        
        # 验证记录内容（第一条应该被丢弃）
        for i, record in enumerate(records):
            self.assertEqual(record["message"], f"Memory test message {i+1}")
    
    def test_file_rotation(self):
        """测试文件轮转功能"""
        # 创建临时日志文件
        rotation_log_file = os.path.join(self.log_dir, "rotation.log")
        
        # 创建临时配置
        rotation_config = {
            "version": 1,
            "root": {
                "level": "debug",
                "handlers": ["rotation_file"]
            },
            "formatters": {
                "simple": {
                    "format": "%(message)s"
                }
            },
            "handlers": {
                "rotation_file": {
                    "class": "logging.handlers.RotatingFileHandler",
                    "level": "debug",
                    "formatter": "simple",
                    "filename": rotation_log_file,
                    "maxBytes": 100,  # 非常小的文件大小，便于测试轮转
                    "backupCount": 3,
                    "encoding": "utf-8"
                }
            }
        }
        
        # 保存配置
        rotation_config_path = os.path.join(self.temp_dir.name, "rotation_config.json")
        with open(rotation_config_path, 'w', encoding='utf-8') as f:
            json.dump(rotation_config, f, indent=4)
        
        # 创建日志管理器
        manager = LogManager(rotation_config_path)
        rotation_logger = manager.get_logger("rotation_test")
        
        # 记录多条日志，触发文件轮转
        long_message = "X" * 50  # 50个字符的消息
        for _ in range(10):  # 写入10条，应该足以触发轮转
            rotation_logger.debug(long_message)
        
        # 验证是否生成了备份文件
        self.assertTrue(os.path.exists(rotation_log_file))
        self.assertTrue(os.path.exists(f"{rotation_log_file}.1") or
                       os.path.exists(f"{rotation_log_file}.1.gz"))
    
    def test_exception_logging(self):
        """测试异常记录功能"""
        # 创建临时日志文件
        exception_log_file = os.path.join(self.log_dir, "exception.log")
        
        # 创建临时配置
        exception_config = {
            "version": 1,
            "root": {
                "level": "debug",
                "handlers": ["exception_file"]
            },
            "formatters": {
                "simple": {
                    "format": "%(message)s"
                }
            },
            "handlers": {
                "exception_file": {
                    "class": "logging.FileHandler",
                    "level": "debug",
                    "formatter": "simple",
                    "filename": exception_log_file,
                    "encoding": "utf-8"
                }
            }
        }
        
        # 保存配置
        exception_config_path = os.path.join(self.temp_dir.name, "exception_config.json")
        with open(exception_config_path, 'w', encoding='utf-8') as f:
            json.dump(exception_config, f, indent=4)
        
        # 创建日志管理器
        manager = LogManager(exception_config_path)
        exception_logger = manager.get_logger("exception_test")
        
        # 记录带异常的日志
        try:
            # 故意触发异常
            1 / 0
        except Exception as e:
            exception_logger.error("发生除零错误", exc_info=True)
        
        # 读取日志文件
        with open(exception_log_file, 'r', encoding='utf-8') as f:
            log_content = f.read()
        
        # 验证日志内容包含异常信息
        self.assertIn("发生除零错误", log_content)
        self.assertIn("ZeroDivisionError", log_content)
        self.assertIn("1 / 0", log_content)


if __name__ == "__main__":
    unittest.main() 