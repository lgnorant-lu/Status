"""
---------------------------------------------------------------
File name:                  logging_example.py
Author:                     Ignorant-lu
Date created:               2025/05/14
Description:                日志系统使用示例
----------------------------------------------------------------

Changed history:            
                            2025/05/14: 初始创建;
----
"""

import os
import sys

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# 导入日志模块
from status.core.logging import log, get_logger

def basic_logging_example():
    """基本日志记录示例"""
    print("\n=== 基本日志记录示例 ===")
    
    # 使用全局日志器
    log.debug("这是一条调试日志")
    log.info("这是一条信息日志")
    log.warning("这是一条警告日志")
    log.error("这是一条错误日志")
    log.critical("这是一条严重错误日志")

def module_logging_example():
    """模块日志记录示例"""
    print("\n=== 模块日志记录示例 ===")
    
    # 创建模块级日志器
    module_log = get_logger("example.module")
    
    module_log.debug("模块调试信息")
    module_log.info("模块信息")
    module_log.warning("模块警告")

def exception_logging_example():
    """异常日志记录示例"""
    print("\n=== 异常日志记录示例 ===")
    
    # 创建异常日志器
    exception_log = get_logger("example.exception")
    
    try:
        # 故意触发异常
        result = 1 / 0
    except Exception as e:
        # 记录异常
        exception_log.error(f"发生异常: {e}", exc_info=True)
        
        # 不带堆栈跟踪记录
        exception_log.warning(f"发生异常(不带堆栈): {e}")

def performance_logging_example():
    """性能日志记录示例"""
    print("\n=== 性能日志记录示例 ===")
    
    # 创建性能日志器
    perf_log = get_logger("example.performance")
    
    import time
    
    # 记录函数执行时间
    def log_execution_time(func):
        def wrapper(*args, **kwargs):
            start_time = time.time()
            result = func(*args, **kwargs)
            end_time = time.time()
            perf_log.debug(f"函数 {func.__name__} 执行时间: {end_time - start_time:.6f} 秒")
            return result
        return wrapper
    
    @log_execution_time
    def slow_function():
        """模拟耗时操作"""
        time.sleep(0.5)
        return "操作完成"
    
    # 调用函数
    slow_function()
    slow_function()

def extra_data_logging_example():
    """附加数据日志记录示例"""
    print("\n=== 附加数据日志记录示例 ===")
    
    # 创建数据日志器
    data_log = get_logger("example.data")
    
    # 创建一个上下文管理器，用于临时添加额外数据
    class LogContext:
        def __init__(self, logger, **kwargs):
            self.logger = logger
            self.extra = kwargs
        
        def __enter__(self):
            return self
        
        def __exit__(self, exc_type, exc_val, exc_tb):
            pass
        
        def debug(self, msg, *args, **kwargs):
            kwargs["extra"] = self.extra
            self.logger.debug(msg, *args, **kwargs)
        
        def info(self, msg, *args, **kwargs):
            kwargs["extra"] = self.extra
            self.logger.info(msg, *args, **kwargs)
        
        def warning(self, msg, *args, **kwargs):
            kwargs["extra"] = self.extra
            self.logger.warning(msg, *args, **kwargs)
        
        def error(self, msg, *args, **kwargs):
            kwargs["extra"] = self.extra
            self.logger.error(msg, *args, **kwargs)
        
        def critical(self, msg, *args, **kwargs):
            kwargs["extra"] = self.extra
            self.logger.critical(msg, *args, **kwargs)
    
    # 使用上下文记录日志
    with LogContext(data_log, user_id="123", session_id="abc-456") as ctx_log:
        ctx_log.info("用户登录")
        ctx_log.debug("用户查询数据")
        
        # 模拟出错
        ctx_log.error("查询失败")


def main():
    """主函数"""
    print("日志系统使用示例")
    
    # 运行各个示例
    basic_logging_example()
    module_logging_example()
    exception_logging_example()
    performance_logging_example()
    extra_data_logging_example()
    
    print("\n示例完成。查看logs目录下的日志文件以获取更多信息。")


if __name__ == "__main__":
    # 确保目录存在
    os.makedirs("logs", exist_ok=True)
    
    # 运行示例
    main() 