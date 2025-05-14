"""
---------------------------------------------------------------
File name:                  exception_handler.py
Author:                     Ignorant-lu
Date created:               2025/05/14
Description:                异常处理器实现
----------------------------------------------------------------

Changed history:            
                            2025/05/14: 初始创建;
----
"""

import os
import sys
import enum
import threading
import traceback
from datetime import datetime
from typing import Dict, List, Any, Optional, Callable, Tuple, Type, Union, cast

# 获取日志器
from status.core.logging import get_logger

# 导入恢复管理器
from status.core.recovery.recovery_manager import RecoveryManager


class ErrorLevel(enum.Enum):
    """错误级别枚举"""
    
    FATAL = "fatal"        # 致命错误，无法继续运行
    SEVERE = "severe"      # 严重错误，可能影响功能
    MODERATE = "moderate"  # 中度错误，局部功能受影响
    MINOR = "minor"        # 轻微错误，几乎不影响使用


class ExceptionHandler:
    """异常处理器类
    
    全局异常处理器，负责捕获和处理未处理的异常。使用单例模式确保全局只有一个实例。
    """
    
    # 单例实例
    _instance = None
    _lock = threading.Lock()
    _initialized: bool = False
    
    # 标准异常类型与错误级别映射
    _DEFAULT_ERROR_LEVELS = {
        SystemExit: ErrorLevel.FATAL,
        KeyboardInterrupt: ErrorLevel.FATAL,
        SystemError: ErrorLevel.FATAL,
        MemoryError: ErrorLevel.SEVERE,
        ImportError: ErrorLevel.SEVERE,
        IOError: ErrorLevel.SEVERE,
        OSError: ErrorLevel.SEVERE,
        ValueError: ErrorLevel.MODERATE,
        TypeError: ErrorLevel.MODERATE,
        KeyError: ErrorLevel.MODERATE,
        IndexError: ErrorLevel.MODERATE,
        AttributeError: ErrorLevel.MODERATE,
        NameError: ErrorLevel.MODERATE,
        RuntimeError: ErrorLevel.MODERATE,
        Exception: ErrorLevel.MODERATE,  # 默认
    }
    
    def __new__(cls, *args, **kwargs):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(ExceptionHandler, cls).__new__(cls)
                cls._instance._initialized = False
            return cls._instance
    
    def __init__(self):
        """初始化异常处理器"""
        # 防止重复初始化
        if self._initialized:
            return
            
        self._initialized = True
        
        # 设置日志
        self.logger = get_logger("status.core.recovery.exception_handler")
        
        # 恢复管理器实例
        self._recovery_manager = RecoveryManager()
        
        # 异常类型到错误级别的映射
        self._error_levels = self._DEFAULT_ERROR_LEVELS.copy()
        
        # 异常类型到处理函数的映射
        self._exception_handlers: Dict[Type[Exception], Callable[[Exception, ErrorLevel, str], bool]] = {}
        
        # 是否已经安装全局处理器
        self._installed = False
        
        # 是否在开发模式下
        self._dev_mode = os.environ.get("STATUS_DEV_MODE", "0") == "1"
        
        # 记录原始的sys.excepthook
        self._original_excepthook = sys.excepthook
        
        # 错误对话框的回调函数（UI层注册）
        self._error_dialog_callback: Optional[Callable[[str, str, str], None]] = None
        
        self.logger.info("异常处理器初始化完成")
    
    def install_global_handler(self) -> None:
        """安装全局异常处理器"""
        if self._installed:
            self.logger.debug("全局异常处理器已安装")
            return
        
        # 安装全局处理器
        sys.excepthook = self._global_exception_handler
        
        # 设置为已安装
        self._installed = True
        
        self.logger.info("全局异常处理器安装成功")
    
    def uninstall_global_handler(self) -> None:
        """卸载全局异常处理器"""
        if not self._installed:
            return
        
        # 恢复原始处理器
        sys.excepthook = self._original_excepthook
        
        # 设置为未安装
        self._installed = False
        
        self.logger.info("全局异常处理器已卸载")
    
    def _global_exception_handler(self, exc_type: Type[BaseException], exc_value: BaseException, exc_traceback) -> None:
        """全局异常处理函数
        
        Args:
            exc_type: 异常类型
            exc_value: 异常值
            exc_traceback: 异常堆栈
        """
        try:
            # 处理异常
            self.handle_exception(exc_type, exc_value, exc_traceback)
        except Exception as e:
            # 处理异常的过程中出现异常
            self.logger.critical(f"异常处理器出现异常: {e}")
            # 使用原始处理器
            self._original_excepthook(exc_type, exc_value, exc_traceback)
    
    def handle_exception(self, exc_type: Type[BaseException], exc_value: BaseException, exc_traceback) -> bool:
        """处理异常
        
        Args:
            exc_type: 异常类型
            exc_value: 异常值
            exc_traceback: 异常堆栈
            
        Returns:
            是否处理成功
        """
        try:
            # 记录异常到日志
            self.log_exception(exc_type, exc_value, exc_traceback)
            
            # 获取错误级别
            error_level = self._get_error_level(exc_type)
            
            # 获取异常详细信息
            error_details = self._format_exception(exc_type, exc_value, exc_traceback)
            
            # 检查是否有特定的处理函数
            if issubclass(exc_type, Exception):
                exc_value_as_exception = cast(Exception, exc_value)  # 类型转换确保类型安全
                if exc_type in self._exception_handlers:
                    handler = self._exception_handlers[exc_type]
                    try:
                        result = handler(exc_value_as_exception, error_level, error_details)
                        return bool(result)
                    except Exception as e:
                        self.logger.error(f"执行异常处理函数失败: {e}")
            
            # 尝试自动恢复
            recovered = self.attempt_recovery(exc_type, exc_value)
            
            # 显示错误对话框
            message = str(exc_value) or exc_type.__name__
            self.show_error_dialog(message, error_details, error_level)
            
            # 创建崩溃报告
            self._create_crash_report(exc_type, exc_value, exc_traceback)
            
            return recovered
        
        except Exception as e:
            self.logger.critical(f"处理异常时出错: {e}")
            return False
    
    def log_exception(self, exc_type: Type[BaseException], exc_value: BaseException, exc_traceback) -> None:
        """记录异常到日志
        
        Args:
            exc_type: 异常类型
            exc_value: 异常值
            exc_traceback: 异常堆栈
        """
        # 格式化异常信息
        tb_str = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
        
        # 获取错误级别
        error_level = self._get_error_level(exc_type)
        
        # 根据错误级别记录到不同日志级别
        if error_level == ErrorLevel.FATAL:
            self.logger.critical(f"致命错误: {exc_value}\n{tb_str}")
        elif error_level == ErrorLevel.SEVERE:
            self.logger.error(f"严重错误: {exc_value}\n{tb_str}")
        elif error_level == ErrorLevel.MODERATE:
            self.logger.error(f"错误: {exc_value}\n{tb_str}")
        else:  # MINOR
            self.logger.warning(f"警告: {exc_value}\n{tb_str}")
    
    def _get_error_level(self, exc_type: Type[BaseException]) -> ErrorLevel:
        """获取异常的错误级别
        
        Args:
            exc_type: 异常类型
            
        Returns:
            错误级别
        """
        # 直接匹配
        if exc_type in self._error_levels:
            return self._error_levels[exc_type]
        
        # 查找最接近的父类
        for base_exc, level in self._error_levels.items():
            if issubclass(exc_type, base_exc):
                return level
        
        # 默认为中度错误
        return ErrorLevel.MODERATE
    
    def _format_exception(self, exc_type: Type[BaseException], exc_value: BaseException, exc_traceback) -> str:
        """格式化异常信息
        
        Args:
            exc_type: 异常类型
            exc_value: 异常值
            exc_traceback: 异常堆栈
            
        Returns:
            格式化后的异常信息
        """
        # 在开发模式下显示完整堆栈
        if self._dev_mode:
            return "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
        
        # 在生产模式下显示简化信息
        lines = traceback.format_exception(exc_type, exc_value, exc_traceback)
        
        # 如果堆栈太长，只保留前5行和后5行
        if len(lines) > 12:  # 头部信息+前5行+后5行+省略信息
            return "".join(lines[:6] + ["...\n(省略中间 {} 行)\n...\n".format(len(lines) - 11)] + lines[-5:])
        
        return "".join(lines)
    
    def attempt_recovery(self, exc_type: Type[BaseException], exc_value: BaseException) -> bool:
        """尝试自动恢复
        
        Args:
            exc_type: 异常类型
            exc_value: 异常值
            
        Returns:
            是否恢复成功
        """
        # 获取错误级别
        error_level = self._get_error_level(exc_type)
        
        # 致命错误无法恢复
        if error_level == ErrorLevel.FATAL:
            self.logger.critical("致命错误无法恢复")
            return False
        
        # 尝试恢复措施
        try:
            # 保存当前状态
            from status.core.recovery.state_manager import StateManager
            state_manager = StateManager()
            state_manager.save_state(force=True)
            
            # 根据错误级别采取不同措施
            if error_level == ErrorLevel.SEVERE:
                # 严重错误，建议重启应用
                self.logger.error("严重错误，建议用户重启应用")
                return False
                
            elif error_level == ErrorLevel.MODERATE:
                # 中度错误，尝试部分恢复
                self.logger.warning("中度错误，尝试部分恢复")
                return True
                
            else:  # MINOR
                # 轻微错误，可以继续
                self.logger.info("轻微错误，可以继续")
                return True
                
        except Exception as e:
            self.logger.error(f"尝试恢复失败: {e}")
            return False
    
    def show_error_dialog(self, message: str, details: str, level: ErrorLevel = ErrorLevel.MODERATE) -> None:
        """显示错误对话框
        
        Args:
            message: 错误消息
            details: 详细信息
            level: 错误级别
        """
        # 如果UI层注册了回调函数，则使用回调函数显示对话框
        if self._error_dialog_callback is not None:
            try:
                self._error_dialog_callback(message, details, level.value)
                return
            except Exception as e:
                self.logger.error(f"调用错误对话框回调函数失败: {e}")
        
        # 如果没有回调或回调失败，使用标准输出
        if level == ErrorLevel.FATAL:
            print(f"\n[致命错误] {message}")
        elif level == ErrorLevel.SEVERE:
            print(f"\n[严重错误] {message}")
        elif level == ErrorLevel.MODERATE:
            print(f"\n[错误] {message}")
        else:  # MINOR
            print(f"\n[警告] {message}")
        
        if self._dev_mode:
            print(f"\n详细信息:\n{details}")
    
    def register_error_dialog_callback(self, callback: Callable[[str, str, str], None]) -> None:
        """注册错误对话框回调函数
        
        Args:
            callback: 回调函数，接收消息、详情和错误级别
        """
        if not callable(callback):
            self.logger.error("注册错误对话框回调函数失败: 回调必须是可调用对象")
            return
        
        self._error_dialog_callback = callback
        self.logger.debug("错误对话框回调函数注册成功")
    
    def register_exception_handler(self, exc_type: Type[Exception], handler: Callable[[Exception, ErrorLevel, str], bool]) -> None:
        """注册异常处理函数
        
        Args:
            exc_type: 异常类型
            handler: 处理函数，接收异常值、错误级别和详细信息
        """
        if not callable(handler):
            self.logger.error(f"注册异常处理函数失败: 处理函数必须是可调用对象")
            return
        
        self._exception_handlers[exc_type] = handler
        self.logger.debug(f"异常处理函数注册成功: {exc_type.__name__}")
    
    def set_error_level(self, exc_type: Type[Exception], level: ErrorLevel) -> None:
        """设置异常的错误级别
        
        Args:
            exc_type: 异常类型
            level: 错误级别
        """
        self._error_levels[exc_type] = level
        self.logger.debug(f"设置异常 {exc_type.__name__} 的错误级别为 {level.value}")
    
    def set_dev_mode(self, enabled: bool = True) -> None:
        """设置开发模式
        
        Args:
            enabled: 是否启用开发模式
        """
        self._dev_mode = enabled
        self.logger.debug(f"{'启用' if enabled else '禁用'}开发模式")
    
    def is_dev_mode(self) -> bool:
        """检查是否处于开发模式
        
        Returns:
            是否处于开发模式
        """
        return self._dev_mode
    
    def _create_crash_report(self, exc_type: Type[BaseException], exc_value: BaseException, exc_traceback) -> str:
        """创建崩溃报告
        
        Args:
            exc_type: 异常类型
            exc_value: 异常值
            exc_traceback: 异常堆栈
            
        Returns:
            崩溃报告文件路径
        """
        try:
            # 格式化异常信息
            tb_str = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
            
            # 准备错误信息
            error_info = {
                "type": exc_type.__name__,
                "message": str(exc_value),
                "traceback": tb_str,
                "module": getattr(exc_value, "__module__", "unknown"),
                "time": datetime.now().isoformat()
            }
            
            # 使用恢复管理器创建崩溃报告
            report_path = self._recovery_manager.create_crash_report(error_info)
            
            self.logger.info(f"崩溃报告创建成功: {report_path}")
            return report_path
            
        except Exception as e:
            self.logger.error(f"创建崩溃报告失败: {e}")
            return "" 