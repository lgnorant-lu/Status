"""
---------------------------------------------------------------
File name:                  utils.py
Author:                     Ignorant-lu
Date created:               2025/04/04
Description:                配置系统工具类
----------------------------------------------------------------

Changed history:            
                            2025/04/04: 初始创建;
----
"""

import time
import threading
from functools import wraps

class Debounce:
    """防抖动工具类"""
    
    def __init__(self, wait_time):
        """初始化防抖动工具
        
        Args:
            wait_time: 等待时间（秒）
        """
        self.wait_time = wait_time
        self.last_call_time = 0
        self.timer = None
        self.lock = threading.Lock()
        
    def __call__(self, func):
        """装饰器方法
        
        Args:
            func: 要装饰的函数
            
        Returns:
            function: 包装后的函数
        """
        @wraps(func)
        def wrapped(*args, **kwargs):
            current_time = time.time()
            
            with self.lock:
                # 取消等待中的定时器
                if self.timer:
                    self.timer.cancel()
                    self.timer = None
                
                # 如果距离上次执行已经超过等待时间，则立即执行
                elapsed = current_time - self.last_call_time
                if elapsed >= self.wait_time:
                    self.last_call_time = current_time
                    return func(*args, **kwargs)
                
                # 否则，设置一个定时器在等待时间后执行
                def delayed_call():
                    with self.lock:
                        self.last_call_time = time.time()
                    return func(*args, **kwargs)
                
                self.timer = threading.Timer(self.wait_time - elapsed, delayed_call)
                self.timer.daemon = True
                self.timer.start()
                
                # 返回None表示函数稍后将被调用
                return None
                
        return wrapped

class FileChangeMonitor:
    """文件变更监视器"""
    
    def __init__(self, file_path, check_interval=1.0, callback=None):
        """初始化监视器
        
        Args:
            file_path: 要监视的文件路径
            check_interval: 检查间隔（秒）
            callback: 文件变更时的回调函数
        """
        self.file_path = file_path
        self.check_interval = check_interval
        self.callback = callback
        self.last_modified = 0
        self.running = False
        self.thread = None
        self.lock = threading.Lock()
    
    def start(self):
        """开始监视"""
        with self.lock:
            if self.running:
                return
                
            self.running = True
            
            # 获取初始修改时间
            try:
                self.last_modified = self._get_mtime()
            except:
                pass
                
            # 启动监视线程
            self.thread = threading.Thread(target=self._monitor_thread)
            self.thread.daemon = True
            self.thread.start()
    
    def stop(self):
        """停止监视"""
        with self.lock:
            if not self.running:
                return
                
            self.running = False
            
            if self.thread:
                self.thread.join(timeout=1.0)
                self.thread = None
    
    def _monitor_thread(self):
        """监视线程函数"""
        while self.running:
            try:
                mtime = self._get_mtime()
                
                # 检测是否有变更
                if mtime > self.last_modified:
                    self.last_modified = mtime
                    
                    # 调用回调函数
                    if self.callback:
                        self.callback()
            except Exception as e:
                # 忽略文件操作错误
                pass
                
            # 休眠一段时间
            time.sleep(self.check_interval)
    
    def _get_mtime(self):
        """获取文件修改时间"""
        import os
        return os.path.getmtime(self.file_path) if os.path.exists(self.file_path) else 0

class ThreadResourceController:
    """线程资源控制器"""
    
    def __init__(self, max_cpu_percent=10, check_interval=5.0):
        """初始化控制器
        
        Args:
            max_cpu_percent: 最大CPU使用率
            check_interval: 检查间隔（秒）
        """
        self.max_cpu_percent = max_cpu_percent
        self.check_interval = check_interval
        self.last_check_time = 0
        self.lock = threading.Lock()
        
    def adjust_interval(self, current_interval):
        """根据系统负载调整间隔
        
        Args:
            current_interval: 当前间隔
            
        Returns:
            float: 调整后的间隔
        """
        try:
            # 避免频繁检查
            current_time = time.time()
            if current_time - self.last_check_time < self.check_interval:
                return current_interval
                
            self.last_check_time = current_time
            
            # 获取当前CPU使用率
            cpu_percent = self._get_cpu_percent()
            
            with self.lock:
                # 根据CPU使用率调整间隔
                if cpu_percent > self.max_cpu_percent:
                    # 增加间隔减少资源消耗
                    return min(current_interval * 1.5, 10.0)
                elif cpu_percent < self.max_cpu_percent / 2:
                    # 减少间隔提高响应性
                    return max(current_interval / 1.2, 0.5)
                    
                return current_interval
        except:
            # 发生错误时保持当前间隔
            return current_interval
    
    def _get_cpu_percent(self):
        """获取CPU使用率"""
        try:
            import psutil
            return psutil.cpu_percent(interval=0.1)
        except ImportError:
            # 如果psutil不可用，返回默认值
            return 0 

class ConfigDiff:
    """配置差异工具类"""
    
    @staticmethod
    def get_diff(user_config, default_config):
        """获取用户配置与默认配置的差异部分
        
        Args:
            user_config: 用户配置
            default_config: 默认配置
            
        Returns:
            dict: 只包含与默认值不同的配置项
        """
        if not isinstance(user_config, dict) or not isinstance(default_config, dict):
            # 如果不是字典类型，直接比较值是否相等
            return user_config if user_config != default_config else None
            
        result = {}
        
        # 遍历用户配置
        for key, value in user_config.items():
            # 如果键不在默认配置中，保留该键
            if key not in default_config:
                result[key] = value
                continue
                
            # 递归比较嵌套字典
            if isinstance(value, dict) and isinstance(default_config[key], dict):
                diff = ConfigDiff.get_diff(value, default_config[key])
                if diff:
                    result[key] = diff
            # 比较其他类型的值
            elif value != default_config[key]:
                result[key] = value
                
        return result if result else None
    
    @staticmethod
    def merge_with_defaults(diff_config, default_config):
        """将差异配置与默认配置合并
        
        Args:
            diff_config: 差异配置
            default_config: 默认配置
            
        Returns:
            dict: 完整的配置
        """
        if not isinstance(diff_config, dict) or not isinstance(default_config, dict):
            return diff_config if diff_config is not None else default_config
            
        result = default_config.copy()
        
        # 遍历差异配置
        for key, value in diff_config.items():
            # 如果键在默认配置中且都是字典，递归合并
            if key in result and isinstance(value, dict) and isinstance(result[key], dict):
                result[key] = ConfigDiff.merge_with_defaults(value, result[key])
            # 否则直接使用差异配置的值
            else:
                result[key] = value
                
        return result 