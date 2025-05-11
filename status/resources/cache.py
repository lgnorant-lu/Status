"""
---------------------------------------------------------------
File name:                  cache.py
Author:                     Ignorant-lu
Date created:               2025/04/03
Description:                缓存系统，实现资源缓存逻辑，优化资源访问性能
----------------------------------------------------------------

Changed history:            
                            2025/04/03: 初始创建;
                            2025/05/12: 修复类型提示;
----
"""

import time
import logging
import threading
from typing import Dict, Any, Optional, List, Tuple, Callable, cast
from enum import Enum, auto
import weakref
import gc


class CacheStrategy(Enum):
    """缓存策略枚举"""
    LRU = auto()  # 最近最少使用
    FIFO = auto() # 先进先出
    LFU = auto()  # 最少使用频率
    TTL = auto()  # 基于时间的过期


class CacheItemStatus(Enum):
    """缓存项状态枚举"""
    READY = auto()        # 就绪状态
    LOADING = auto()      # 正在加载
    ERROR = auto()        # 加载错误
    EXPIRED = auto()      # 已过期


class CacheItem:
    """缓存项，表示一个被缓存的资源"""
    
    def __init__(self, key: str, value: Any, max_age: float = 0):
        """初始化缓存项
        
        Args:
            key: 缓存键
            value: 缓存值
            max_age: 最大存活时间（秒），0表示永不过期
        """
        self.key = key
        self.value = value
        self.max_age = max_age
        self.created_at = time.time()
        self.last_accessed = time.time()
        self.access_count = 0
        self.status = CacheItemStatus.READY
        self.size = self._estimate_size(value)
    
    def _estimate_size(self, obj: Any) -> int:
        """估计对象的内存大小（字节）
        
        Args:
            obj: 要估计大小的对象
            
        Returns:
            int: 估计的内存大小（字节）
        """
        # 对于某些已知类型，使用其内部方法或属性来获取大小
        if hasattr(obj, 'nbytes'):  # 例如numpy数组
            return int(obj.nbytes)  # 确保返回int类型
        elif hasattr(obj, 'width') and hasattr(obj, 'height'):  # QImage或类似的图像对象
            # 估计图像大小：宽x高x像素深度（假设4字节RGBA）
            return int(obj.width() * obj.height() * 4)
        elif hasattr(obj, 'size'):  # PIL.Image或具有size属性的对象
            if isinstance(obj.size, tuple) and len(obj.size) >= 2:
                # 假设是PIL图像，size是(width, height)
                width, height = obj.size[0], obj.size[1]  # 只取前两个元素
                return int(width * height * 4)  # 假设4字节RGBA
        elif isinstance(obj, (bytes, bytearray)):
            return len(obj)
        elif isinstance(obj, str):
            return len(obj) * 2  # 假设UTF-16编码，每个字符2字节
        
        # 默认大小：对于复杂对象，这只是一个很粗略的估计
        return 1024  # 1KB默认大小
    
    def access(self) -> None:
        """访问缓存项，更新访问时间和计数"""
        self.last_accessed = time.time()
        self.access_count += 1
    
    def is_expired(self) -> bool:
        """检查缓存项是否已过期
        
        Returns:
            bool: 是否已过期
        """
        if self.max_age <= 0:
            return False
        
        current_time = time.time()
        return (current_time - self.created_at) > self.max_age
    
    def get_age(self) -> float:
        """获取缓存项的年龄（秒）
        
        Returns:
            float: 缓存项年龄（秒）
        """
        return time.time() - self.created_at
    
    def get_idle_time(self) -> float:
        """获取缓存项的空闲时间（上次访问后经过的时间）
        
        Returns:
            float: 空闲时间（秒）
        """
        return time.time() - self.last_accessed


class Cache:
    """缓存系统，负责管理各类资源的缓存"""
    
    def __init__(self, 
                 strategy: CacheStrategy = CacheStrategy.LRU,
                 max_size: int = 100 * 1024 * 1024,  # 默认100MB
                 max_items: int = 1000,
                 default_ttl: float = 300,  # 默认5分钟
                 cleanup_interval: float = 60):  # 默认1分钟清理一次
        """初始化缓存系统
        
        Args:
            strategy: 缓存策略
            max_size: 最大缓存大小（字节）
            max_items: 最大缓存项数量
            default_ttl: 默认生存时间（秒）
            cleanup_interval: 清理间隔（秒）
        """
        self.strategy = strategy
        self.max_size = max_size
        self.max_items = max_items
        self.default_ttl = default_ttl
        self.cleanup_interval = cleanup_interval
        
        self._cache: Dict[str, CacheItem] = {}
        self._current_size = 0
        self._lock = threading.RLock()
        self._loading_locks: Dict[str, threading.Lock] = {}
        self._logger = logging.getLogger("Cache")
        
        # 将核心方法定义为可调用的实例变量，并用内部实现初始化
        self.get: Callable[..., Any] = self._default_get_impl
        self.put: Callable[..., None] = self._default_put_impl
        self.clear: Callable[..., int] = self._default_clear_impl
        self.remove_method: Callable[[str], bool] = self._default_remove_impl # Renamed to avoid conflict with list.remove
        
        # 启动自动清理任务
        self._cleanup_timer: Optional[threading.Timer] = None
        self._start_cleanup_task()
    
    def _start_cleanup_task(self) -> None:
        """启动自动清理任务"""
        if self.cleanup_interval > 0:
            def cleanup_task():
                self.cleanup()
                # 重新调度自身
                if self._cleanup_timer is None:
                    self._cleanup_timer = threading.Timer(self.cleanup_interval, cleanup_task)
                    self._cleanup_timer.daemon = True
                    self._cleanup_timer.start()
                else:
                    self._cleanup_timer = threading.Timer(self.cleanup_interval, cleanup_task)
                    self._cleanup_timer.daemon = True
                    self._cleanup_timer.start()
            
            self._cleanup_timer = threading.Timer(self.cleanup_interval, cleanup_task)
            self._cleanup_timer.daemon = True
            self._cleanup_timer.start()
            # 无需到达此处
            return
    
    def _stop_cleanup_task(self) -> None:
        """停止自动清理任务"""
        if self._cleanup_timer is not None:
            self._cleanup_timer.cancel()
            self._cleanup_timer = None
    
    def __del__(self) -> None:
        """析构函数，确保清理任务被停止"""
        self._stop_cleanup_task()
    
    def _default_get_impl(self, key: str, default: Any = None, loader: Optional[Callable[[], Any]] = None, 
            ttl: Optional[float] = None) -> Any:
        """获取缓存项的默认实现"""
        with self._lock:
            # 检查缓存项是否存在
            item = self._cache.get(key)
            
            # 如果存在且未过期，更新访问信息并返回
            if item is not None and item.status == CacheItemStatus.READY and not item.is_expired():
                item.access()
                return item.value
            
            # 如果存在但已过期，将其从缓存中移除
            if item is not None and (item.is_expired() or item.status == CacheItemStatus.EXPIRED):
                self._remove_item(key)
                item = None
            
            # 如果存在但处于加载状态，等待加载完成
            if item is not None and item.status == CacheItemStatus.LOADING:
                loading_lock = self._loading_locks.get(key)
                if loading_lock is not None:
                    self._lock.release()
                    try:
                        loading_lock.acquire()
                        loading_lock.release()
                        self._lock.acquire()
                        item = self._cache.get(key)
                        if item is not None and item.status == CacheItemStatus.READY:
                            item.access()
                            return item.value
                    except Exception as e:
                        self._logger.error(f"等待加载缓存项时发生错误: {str(e)}")
                        if not hasattr(self._lock, '_is_owned') or not getattr(self._lock, '_is_owned', lambda: False)(): self._lock.acquire()
            
            if item is None and loader is not None:
                loading_lock = threading.Lock()
                loading_lock.acquire()
                self._loading_locks[key] = loading_lock
                temp_item = CacheItem(key, None, ttl or self.default_ttl)
                temp_item.status = CacheItemStatus.LOADING
                self._cache[key] = temp_item
                self._lock.release()
                try:
                    value = loader()
                    self._lock.acquire()
                    new_item_obj = CacheItem(key, value, ttl or self.default_ttl)
                    self._add_item(key, new_item_obj)
                    item = new_item_obj
                except Exception as e:
                    self._logger.error(f"加载缓存项时发生错误: {str(e)}")
                    if not hasattr(self._lock, '_is_owned') or not getattr(self._lock, '_is_owned', lambda: False)(): self._lock.acquire()
                    temp_item.status = CacheItemStatus.ERROR
                finally:
                    loading_lock.release()
                    self._loading_locks.pop(key, None)
                if item is not None and item.status == CacheItemStatus.READY:
                    return item.value
            return default
    
    def _default_put_impl(self, key: str, value: Any, ttl: Optional[float] = None) -> None:
        """添加或更新缓存项的默认实现"""
        with self._lock:
            item = CacheItem(key, value, ttl or self.default_ttl)
            self._add_item(key, item)
    
    def _add_item(self, key: str, item: CacheItem) -> None:
        """添加缓存项到缓存
        
        Args:
            key: 缓存键
            item: 缓存项
        """
        # 如果键已存在，先移除旧的缓存项
        if key in self._cache:
            self._remove_item(key)
        
        # 检查是否需要腾出空间
        self._ensure_capacity(item.size)
        
        # 添加缓存项
        self._cache[key] = item
        self._current_size += item.size
    
    def _remove_item(self, key: str) -> None:
        """从缓存中移除一个项
        
        Args:
            key: 缓存键
        """
        item_popped = self._cache.pop(key, None)
        if item_popped is not None:
            self._current_size -= item_popped.size
    
    def _ensure_capacity(self, required_size: int) -> None:
        """确保缓存有足够的空间
        
        Args:
            required_size: 需要的空间大小
        """
        # 如果缓存项数量超过限制或空间不足，根据策略移除缓存项
        while (len(self._cache) >= self.max_items or 
               self._current_size + required_size > self.max_size) and self._cache:
            self._evict()
    
    def _evict(self) -> None:
        """根据策略逐出缓存项"""
        if not self._cache:
            return
        
        # 首先移除已过期的项
        expired_keys = [k for k, v in self._cache.items() if v.is_expired()]
        if expired_keys:
            for key_to_evict_expired in expired_keys[:1]:  # 每次只移除一项，避免一次性移除太多
                self._remove_item(key_to_evict_expired)
            return
        
        # 根据策略选择要逐出的项
        if self.strategy == CacheStrategy.LRU:
            # 最近最少使用：移除最久未访问的项
            key_to_evict = min(self._cache.items(), key=lambda x: x[1].last_accessed)[0]
        elif self.strategy == CacheStrategy.FIFO:
            # 先进先出：移除最早创建的项
            key_to_evict = min(self._cache.items(), key=lambda x: x[1].created_at)[0]
        elif self.strategy == CacheStrategy.LFU:
            # 最少使用频率：移除访问次数最少的项
            key_to_evict = min(self._cache.items(), key=lambda x: x[1].access_count)[0]
        else:  # 默认LRU
            key_to_evict = min(self._cache.items(), key=lambda x: x[1].last_accessed)[0]
        
        # 移除选中的项
        self._remove_item(key_to_evict)
    
    def _default_remove_impl(self, key: str) -> bool:
        """从缓存中移除一个项的默认实现"""
        with self._lock:
            if key in self._cache:
                self._remove_item(key)
                return True
            return False
    
    def _default_clear_impl(self) -> int:
        """清空缓存并返回移除数量的默认实现"""
        with self._lock:
            cleared_count = len(self._cache)
            self._cache.clear()
            self._current_size = 0
            self._logger.info(f"缓存已清空，移除了 {cleared_count} 个条目")
            return cleared_count
    
    def cleanup(self) -> int:
        """清理过期的缓存项
        
        Returns:
            int: 清理的项数量
        """
        with self._lock:
            expired_keys = [k for k, v in self._cache.items() if v.is_expired()]
            for key in expired_keys:
                self._remove_item(key)
            return len(expired_keys)
    
    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        with self._lock:
            return {
                "items_count": len(self._cache),
                "max_items": self.max_items,
                "current_size": self._current_size,
                "max_size": self.max_size,
                "usage_percent": (self._current_size / self.max_size * 100) if self.max_size > 0 else 0,
                "strategy": self.strategy.name,
                "expired_items": sum(1 for v in self._cache.values() if v.is_expired()),
                "loading_items": sum(1 for v in self._cache.values() if v.status == CacheItemStatus.LOADING),
                "error_items": sum(1 for v in self._cache.values() if v.status == CacheItemStatus.ERROR)
            }
    
    def set_strategy(self, strategy: CacheStrategy) -> None:
        """设置缓存策略
        
        Args:
            strategy: 新的缓存策略
        """
        with self._lock:
            self.strategy = strategy
    
    def set_max_size(self, max_size: int) -> None:
        """设置最大缓存大小
        
        Args:
            max_size: 最大缓存大小（字节）
        """
        with self._lock:
            self.max_size = max_size
            # 确保遵守新的大小限制
            while self._current_size > self.max_size and self._cache:
                self._evict()
    
    def set_max_items(self, max_items: int) -> None:
        """设置最大缓存项数量
        
        Args:
            max_items: 最大缓存项数量
        """
        with self._lock:
            self.max_items = max_items
            # 确保遵守新的数量限制
            while len(self._cache) > self.max_items and self._cache:
                self._evict()
    
    def keys(self) -> List[str]:
        """获取所有缓存键
        
        Returns:
            List[str]: 缓存键列表
        """
        with self._lock:
            return list(self._cache.keys())
    
    def contains(self, key: str) -> bool:
        """检查缓存是否包含指定键
        
        Args:
            key: 缓存键
            
        Returns:
            bool: 是否包含
        """
        with self._lock:
            return key in self._cache
    
    def get_item_info(self, key: str) -> Optional[Dict[str, Any]]:
        """获取缓存项信息
        
        Args:
            key: 缓存键
            
        Returns:
            Optional[Dict[str, Any]]: 缓存项信息，如果不存在则返回None
        """
        with self._lock:
            item = self._cache.get(key)
            if item is None:
                return None
            
            return {
                "key": item.key,
                "size": item.size,
                "created_at": item.created_at,
                "last_accessed": item.last_accessed,
                "access_count": item.access_count,
                "status": item.status.name,
                "age": item.get_age(),
                "idle_time": item.get_idle_time(),
                "is_expired": item.is_expired(),
                "max_age": item.max_age
            }


# 创建一个全局默认缓存实例
default_cache = Cache() 