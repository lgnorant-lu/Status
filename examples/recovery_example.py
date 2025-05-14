"""
---------------------------------------------------------------
File name:                  recovery_example.py
Author:                     Ignorant-lu
Date created:               2025/05/14
Description:                错误恢复机制示例
----------------------------------------------------------------

Changed history:            
                            2025/05/14: 初始创建;
----
"""

import os
import sys
import time
import random
import shutil
from datetime import datetime
from typing import Dict, Any, Optional

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# 导入日志系统
from status.core.logging import get_logger

# 首先定义一个简单的setup_logging函数
def setup_logging():
    """设置日志系统"""
    # 在正式项目中，这个函数应该从status.core.logging中导入
    # 这里简单实现，确保示例可运行
    pass

# 初始化目录和清理旧的崩溃日志文件
def setup_example_environment():
    """准备示例环境，确保目录存在并清理旧日志"""
    # 创建必要的目录
    for path in ["data/recovery", "data/states", "logs"]:
        os.makedirs(path, exist_ok=True)
    
    # 清理旧的崩溃日志文件
    crash_log_path = os.path.join("data", "recovery", "crash_log.json")
    recovery_status_path = os.path.join("data", "recovery", "recovery_status.json")
    
    # 删除旧的崩溃日志文件，防止格式不一致问题
    for path in [crash_log_path, recovery_status_path]:
        if os.path.exists(path):
            os.remove(path)
            print(f"清理旧文件: {path}")

# 导入恢复系统
from status.core.recovery import (
    state_manager, recovery_manager, exception_handler,
    StateManager, RecoveryManager, RecoveryMode, ExceptionHandler, ErrorLevel
)

# 设置日志
setup_logging()
logger = get_logger("examples.recovery_example")

class SampleApp:
    """示例应用"""
    
    def __init__(self):
        """初始化示例应用"""
        self.logger = get_logger("examples.recovery_example.SampleApp")
        self.config: Dict[str, Any] = {}
        self.user_data: Dict[str, Any] = {}
        self.running = False
        
        # 初始化状态
        self._init_state()
        
        # 检查是否需要恢复
        self._check_recovery()
    
    def _init_state(self):
        """初始化状态管理"""
        # 注册模块状态
        state_manager.register_module(
            "sample_app",
            self._save_state,
            self._load_state
        )
        
        # 注册启动钩子
        recovery_manager.register_startup_hook(
            10,  # 优先级
            self._startup_hook
        )
        
        # 安装全局异常处理器
        exception_handler.install_global_handler()
        
        # 注册特定异常处理
        exception_handler.register_exception_handler(
            KeyError,
            self._handle_key_error
        )
        
        self.logger.info("初始化状态管理完成")
    
    def _check_recovery(self):
        """检查是否需要恢复"""
        if recovery_manager.detect_abnormal_exit():
            self.logger.warning("检测到非正常退出，开始恢复...")
            recovery_manager.start_recovery_process()
        else:
            self.logger.info("正常启动")
    
    def _save_state(self) -> Dict[str, Any]:
        """保存应用状态"""
        return {
            "config": self.config,
            "user_data": self.user_data,
            "timestamp": datetime.now().isoformat()
        }
    
    def _load_state(self, state_data: Dict[str, Any]) -> None:
        """加载应用状态"""
        if not state_data:
            self.logger.warning("没有可用的状态数据")
            return
        
        self.config = state_data.get("config", {})
        self.user_data = state_data.get("user_data", {})
        
        self.logger.info(f"状态加载成功，时间戳: {state_data.get('timestamp', 'unknown')}")
    
    def _startup_hook(self, mode: RecoveryMode) -> None:
        """启动钩子"""
        self.logger.info(f"应用启动，模式: {mode.value}")
        
        # 根据恢复模式执行不同操作
        if mode == RecoveryMode.NORMAL:
            self.logger.info("正常模式启动，加载所有功能")
        elif mode == RecoveryMode.SAFE:
            self.logger.info("安全模式启动，仅加载核心功能")
            # 简化配置
            self.config = {k: v for k, v in self.config.items() 
                          if k in ("core", "essential")}
        else:
            self.logger.info("最小模式启动，仅加载UI")
            self.config = {"ui": self.config.get("ui", {})}
    
    def _handle_key_error(self, exc_value: Exception, error_level: ErrorLevel, details: str) -> bool:
        """处理键错误"""
        self.logger.warning(f"处理键错误: {exc_value}, 级别: {error_level.value}")
        key = str(exc_value)
        
        # 尝试恢复缺失的键
        if key.startswith("config."):
            # 提取配置键
            config_key = key.split(".", 1)[1]
            self.config[config_key] = {}
            self.logger.info(f"已恢复配置键: {config_key}")
            return True
        
        elif key.startswith("user_data."):
            # 提取用户数据键
            data_key = key.split(".", 1)[1]
            self.user_data[data_key] = {}
            self.logger.info(f"已恢复用户数据键: {data_key}")
            return True
        
        return False  # 无法处理
    
    def start(self):
        """启动应用"""
        self.running = True
        self.logger.info("应用启动")
        
        # 设置初始配置
        if not self.config:
            self.config = {
                "core": {
                    "version": "1.0",
                    "debug": False
                },
                "ui": {
                    "theme": "default",
                    "color_scheme": "light"
                },
                "data": {
                    "storage_path": "./data",
                    "max_cache_size": 1024
                }
            }
        
        # 保存初始状态
        state_manager.save_state(force=True)
        
        # 运行主循环
        try:
            count = 0
            while self.running and count < 10:
                count += 1
                self._process_cycle(count)
                time.sleep(0.5)
            
            self.logger.info("应用正常退出")
            
        except KeyboardInterrupt:
            self.logger.info("用户中断")
            self.stop()
    
    def _process_cycle(self, cycle: int):
        """处理一个周期"""
        self.logger.info(f"处理周期: {cycle}")
        
        # 添加一些用户数据
        self.user_data[f"item_{cycle}"] = {
            "timestamp": datetime.now().isoformat(),
            "value": random.randint(1, 100)
        }
        
        # 每3个周期保存一次状态
        if cycle % 3 == 0:
            self.logger.info(f"保存周期: {cycle}")
            state_manager.save_state()
        
        # 在第5个周期模拟一个错误
        if cycle == 5:
            error_type = random.choice([
                "key_error", "value_error", "index_error", "attribute_error"
            ])
            
            self.logger.warning(f"模拟错误: {error_type}")
            
            if error_type == "key_error":
                # 使用注册的异常处理器处理
                try:
                    value = self.config["nonexistent_key"]
                except KeyError as e:
                    exception_handler.handle_exception(
                        type(e), e, e.__traceback__)
            
            elif error_type == "value_error":
                # 触发ValueError
                int("not_a_number")
            
            elif error_type == "index_error":
                # 触发IndexError
                empty_list = []
                item = empty_list[10]
            
            else:
                # 触发AttributeError
                obj = "string"
                # 故意调用不存在的方法
                try:
                    # 类型检查器会标记这里有错误，但这是故意的，用于演示异常处理
                    getattr(obj, "nonexistent_method")()  # type: ignore
                except AttributeError as e:
                    exception_handler.handle_exception(
                        type(e), e, e.__traceback__)
    
    def stop(self):
        """停止应用"""
        self.running = False
        
        # 保存最终状态
        state_manager.save_state(force=True)
        
        self.logger.info("应用已停止")


def demonstrate_recovery_features():
    """演示恢复机制功能"""
    logger = get_logger("examples.recovery_example.demo")
    
    # 设置测试环境
    setup_example_environment()
    
    logger.info("=== 恢复机制功能演示 ===")
    
    # 演示状态管理
    logger.info("\n--- 状态管理演示 ---")
    
    # 创建一个测试状态
    test_state = {
        "version": "1.0",
        "data": {
            "name": "测试状态",
            "value": 42,
            "items": ["a", "b", "c"]
        }
    }
    
    # 注册模块状态
    state_manager.register_module(
        "test",
        lambda: test_state,
        lambda state: None
    )
    
    # 保存状态
    state_manager.save_state()
    
    # 加载状态
    state_data = state_manager.load_state()
    
    # 显示状态数据
    if state_data:
        logger.info(f"状态数据: {state_data.to_dict()}")
    
    # 演示恢复模式
    logger.info("\n--- 恢复模式演示 ---")
    
    for mode in RecoveryMode:
        logger.info(f"恢复模式: {mode.name} ({mode.value})")
    
    # 演示错误级别
    logger.info("\n--- 错误级别演示 ---")
    
    for level in ErrorLevel:
        logger.info(f"错误级别: {level.name} ({level.value})")
    
    # 启动示例应用
    logger.info("\n--- 启动示例应用 ---")
    
    app = SampleApp()
    app.start()


if __name__ == "__main__":
    demonstrate_recovery_features() 