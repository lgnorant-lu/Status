"""
---------------------------------------------------------------
File name:                  cache.py
Author:                     Ignorant-lu
Date created:               2023/04/03
Description:                资源缓存系统，管理已加载的资源
----------------------------------------------------------------

Changed history:            
                            2023/04/03: 初始创建;
                            2025/04/03: 添加获取所有键和缓存统计信息的方法;
----
"""

import logging
import time
from typing import Dict, Any, Optional, List, Set, Tuple, Callable
import weakref

class CacheEntry:
    """缓存条目类，表示一个被缓存的资源项"""
    
    def __init__(self, key: str, value: Any, lifetime: Optional[float] = None):
        """初始化缓存条目
        
        Args:
            key: 缓存键
            value: 缓存的资源
            lifetime: 生命期（秒），None表示永久缓存
        """
        self.key = key
        self.value = value
        self.lifetime = lifetime
        self.created_time = time.time()
        self.last_access_time = self.created_time
        self.access_count = 0
    
    def access(self) -> Any:
        """访问缓存项，更新访问统计
        
        Returns:
            缓存的资源
        """
        self.last_access_time = time.time()
        self.access_count += 1
        return self.value
    
    def is_expired(self) -> bool:
        """检查缓存项是否已过期
        
        Returns:
            bool: 是否已过期
        """
        if self.lifetime is None:
            return False
        
        current_time = time.time()
        return (current_time - self.created_time) > self.lifetime
    
    def time_to_expiry(self) -> Optional[float]:
        """获取到期剩余时间
        
        Returns:
            剩余秒数，如果永久缓存则返回None
        """
        if self.lifetime is None:
            return None
        
        current_time = time.time()
        elapsed = current_time - self.created_time
        remaining = self.lifetime - elapsed
        
        return max(0.0, remaining)

class CacheFull(Exception):
    """缓存已满异常"""
    pass

class Cache:
    """资源缓存系统，提供资源的缓存管理功能"""
    
    def __init__(self, max_size: int = 1000):
        """初始化缓存系统
        
        Args:
            max_size: 最大缓存项数量，0表示无限制
        """
        self.logger = logging.getLogger("Hollow-ming.Core.Cache")
        self.max_size = max_size
        self.entries: Dict[str, CacheEntry] = {}
        self.auto_cleanup_enabled = True
        self.stats = {
            "hits": 0,
            "misses": 0,
            "evictions": 0,
            "expirations": 0,
            "total_items_cached": 0
        }
        self.logger.info("缓存系统初始化完成")
    
    def set(self, key: str, value: Any, lifetime: Optional[float] = None) -> bool:
        """设置缓存项
        
        Args:
            key: 缓存键
            value: 缓存值
            lifetime: 生命期（秒），None表示永久缓存
            
        Returns:
            bool: 设置是否成功
            
        Raises:
            CacheFull: 如果缓存已满且无法腾出空间
        """
        # 如果键已存在，直接更新
        if key in self.entries:
            self.entries[key] = CacheEntry(key, value, lifetime)
            self.logger.debug(f"更新缓存项: {key}")
            return True
        
        # 如果缓存已满，尝试清理过期项
        if self.max_size > 0 and len(self.entries) >= self.max_size:
            if self.auto_cleanup_enabled:
                self.cleanup_expired()
            
            # 如果仍然满，尝试驱逐最不常用的项
            if len(self.entries) >= self.max_size:
                if not self._evict_one():
                    self.logger.error("缓存已满，无法添加新项")
                    raise CacheFull("缓存已满，无法添加新项")
        
        # 添加新缓存项
        self.entries[key] = CacheEntry(key, value, lifetime)
        self.stats["total_items_cached"] += 1
        self.logger.debug(f"添加缓存项: {key}")
        return True
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取缓存项
        
        Args:
            key: 缓存键
            default: 如果键不存在或已过期，返回的默认值
            
        Returns:
            缓存值或默认值
        """
        if key not in self.entries:
            self.stats["misses"] += 1
            self.logger.debug(f"缓存未命中: {key}")
            return default
        
        entry = self.entries[key]
        
        # 检查是否过期
        if entry.is_expired():
            self.stats["expirations"] += 1
            del self.entries[key]
            self.logger.debug(f"缓存项已过期: {key}")
            return default
        
        # 增加访问计数并返回值
        self.stats["hits"] += 1
        self.logger.debug(f"缓存命中: {key}")
        return entry.access()
    
    def has(self, key: str) -> bool:
        """检查缓存中是否存在非过期的键
        
        Args:
            key: 缓存键
            
        Returns:
            bool: 是否存在且未过期
        """
        if key not in self.entries:
            return False
        
        entry = self.entries[key]
        if entry.is_expired():
            # 删除过期项
            del self.entries[key]
            self.stats["expirations"] += 1
            self.logger.debug(f"检查时删除过期项: {key}")
            return False
        
        return True
    
    def delete(self, key: str) -> bool:
        """从缓存中删除项
        
        Args:
            key: 要删除的缓存键
            
        Returns:
            bool: 是否成功删除（键存在且被删除）
        """
        if key in self.entries:
            del self.entries[key]
            self.logger.debug(f"从缓存中删除项: {key}")
            return True
        
        return False
    
    def cleanup_expired(self) -> int:
        """清理所有过期的缓存项
        
        Returns:
            int: 清理的项数量
        """
        # 收集过期的键
        expired_keys = [key for key, entry in self.entries.items() if entry.is_expired()]
        
        # 删除过期项
        for key in expired_keys:
            del self.entries[key]
            self.stats["expirations"] += 1
        
        count = len(expired_keys)
        if count > 0:
            self.logger.info(f"清理了 {count} 个过期缓存项")
        
        return count
    
    def _evict_one(self) -> bool:
        """驱逐一个缓存项，基于最少使用策略
        
        Returns:
            bool: 是否成功驱逐
        """
        if not self.entries:
            return False
        
        # 找出访问次数最少的项
        least_used_key = min(self.entries.items(), key=lambda x: x[1].access_count)[0]
        
        # 删除该项
        del self.entries[least_used_key]
        self.stats["evictions"] += 1
        self.logger.debug(f"驱逐缓存项: {least_used_key}")
        
        return True
    
    def clear(self) -> int:
        """清空缓存
        
        Returns:
            int: 清除的项数量
        """
        count = len(self.entries)
        self.entries.clear()
        self.logger.info(f"清空缓存，删除了 {count} 个项")
        return count
    
    def size(self) -> int:
        """获取当前缓存项数量
        
        Returns:
            int: 缓存项数量
        """
        return len(self.entries)
    
    def get_stats(self) -> Dict[str, int]:
        """获取缓存统计信息
        
        Returns:
            Dict[str, int]: 统计信息字典
        """
        stats = self.stats.copy()
        stats["current_size"] = len(self.entries)
        stats["max_size"] = self.max_size
        return stats
    
    def get_keys(self) -> List[str]:
        """获取所有缓存键
        
        Returns:
            List[str]: 缓存键列表
        """
        return list(self.entries.keys())
    
    def get_lifetime(self, key: str) -> Optional[float]:
        """获取缓存项的剩余生命期
        
        Args:
            key: 缓存键
            
        Returns:
            Optional[float]: 剩余生命期（秒），None表示永久缓存或键不存在
        """
        if key not in self.entries:
            return None
        
        return self.entries[key].time_to_expiry()
    
    def set_auto_cleanup(self, enabled: bool) -> None:
        """设置是否自动清理过期项
        
        Args:
            enabled: 是否启用自动清理
        """
        self.auto_cleanup_enabled = enabled
        self.logger.debug(f"自动清理设置为: {enabled}")
    
    def update_max_size(self, max_size: int) -> None:
        """更新最大缓存大小
        
        Args:
            max_size: 新的最大大小，0表示无限制
        """
        self.max_size = max_size
        self.logger.debug(f"最大缓存大小更新为: {max_size}")
        
        # 如果新大小小于当前大小，需要驱逐项
        if 0 < max_size < len(self.entries):
            to_evict = len(self.entries) - max_size
            self._evict_multiple(to_evict)
    
    def _evict_multiple(self, count: int) -> int:
        """驱逐多个缓存项
        
        Args:
            count: 要驱逐的项数量
            
        Returns:
            int: 实际驱逐的项数量
        """
        if count <= 0 or not self.entries:
            return 0
        
        # 按访问次数排序
        sorted_entries = sorted(self.entries.items(), key=lambda x: x[1].access_count)
        
        # 取出需要驱逐的键
        to_evict = [key for key, _ in sorted_entries[:count]]
        
        # 删除这些键
        for key in to_evict:
            del self.entries[key]
            self.stats["evictions"] += 1
        
        evict_count = len(to_evict)
        self.logger.info(f"驱逐了 {evict_count} 个缓存项")
        
        return evict_count
    
    def get_all_keys(self) -> Set[str]:
        """获取所有缓存键
        
        Returns:
            Set[str]: 所有缓存键的集合
        """
        return set(self.entries.keys())
    
    def get_expired_keys(self) -> List[str]:
        """获取所有已过期的缓存键
        
        Returns:
            List[str]: 已过期的缓存键列表
        """
        expired_keys = []
        current_time = time.time()
        
        for key, entry in self.entries.items():
            if entry.lifetime is not None and (current_time - entry.created_time) > entry.lifetime:
                expired_keys.append(key)
        
        return expired_keys
    
    def get_entry_info(self, key: str) -> Optional[Dict[str, Any]]:
        """获取缓存项信息
        
        Args:
            key: 缓存键
            
        Returns:
            Dict或None: 缓存项信息，不存在则返回None
        """
        if key not in self.entries:
            return None
        
        entry = self.entries[key]
        current_time = time.time()
        
        return {
            "key": key,
            "lifetime": entry.lifetime,
            "created_time": entry.created_time,
            "last_access_time": entry.last_access_time,
            "access_count": entry.access_count,
            "age": current_time - entry.created_time,
            "time_since_last_access": current_time - entry.last_access_time,
            "is_expired": entry.is_expired(),
            "time_to_expiry": entry.time_to_expiry()
        } 