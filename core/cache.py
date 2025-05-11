"""
---------------------------------------------------------------
File name:                  cache.py
Author:                     Ignorant-lu
Date created:               2025/04/15
Description:                核心缓存系统模块（最小实现，供测试用）
----------------------------------------------------------------
Changed history:            
                            2025/04/15: 初始创建，最小实现以通过pytest测试;
----
"""

import time
import threading

class CacheFull(Exception):
    """缓存已满异常"""
    pass

class CacheEntry:
    """缓存条目"""
    def __init__(self, key, value, lifetime=None):
        self.key = key
        self.value = value
        self.lifetime = lifetime
        self.access_count = 0
        self.last_access_time = time.time()

    def access(self):
        self.access_count += 1
        self.last_access_time = time.time()
        return self.value

    def is_expired(self):
        if self.lifetime is None:
            return False
        return (time.time() - self.last_access_time) >= self.lifetime

    def time_to_expiry(self):
        if self.lifetime is None:
            return None
        remaining = self.lifetime - (time.time() - self.last_access_time)
        return max(0.0, remaining)

class Cache:
    """缓存系统"""
    def __init__(self, max_size=1000):
        self.max_size = max_size
        self.entries = {}
        self.auto_cleanup_enabled = True
        self.stats = {"hits": 0, "misses": 0}
        self.lock = threading.Lock()

    def set(self, key, value, lifetime=None):
        with self.lock:
            if len(self.entries) >= self.max_size:
                raise CacheFull()
            self.entries[key] = CacheEntry(key, value, lifetime)

    def get(self, key, default=None):
        with self.lock:
            entry = self.entries.get(key)
            if entry and not entry.is_expired():
                self.stats["hits"] += 1
                return entry.access()
            self.stats["misses"] += 1
            return default
