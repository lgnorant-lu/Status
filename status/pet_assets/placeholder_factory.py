"""
---------------------------------------------------------------
File name:                  placeholder_factory.py
Author:                     Ignorant-lu
Date created:               2025/05/15
Description:                占位符工厂，负责动态加载和提供各状态的占位符动画
----------------------------------------------------------------

Changed history:            
                            2025/05/15: 初始创建;
                            2025/05/15: 添加缓存机制;
                            2025/05/15: 添加缓存统计功能;
----
"""
import importlib
import logging
from collections import OrderedDict
from status.behavior.pet_state import PetState
from status.animation.animation import Animation

logger = logging.getLogger(__name__)

class PlaceholderFactory:
    """占位符工厂，负责动态加载和提供各状态的占位符动画"""
    
    def __init__(self, cache_size_limit=5):
        """初始化占位符工厂
        
        Args:
            cache_size_limit: 缓存的最大容量，默认为5
        """
        self._animation_cache = OrderedDict()  # 使用OrderedDict实现LRU缓存
        self._cache_size_limit = cache_size_limit
        
        # 初始化缓存统计
        self._stats = {
            "total_requests": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "hit_rate": 0.0
        }
    
    def get_animation(self, state: PetState) -> Animation | None:
        """根据状态获取对应的占位符动画
        
        Args:
            state: 宠物状态
            
        Returns:
            Animation | None: 对应状态的动画对象，如果加载失败则返回None
        """
        # 更新请求统计
        self._stats["total_requests"] += 1
        
        # 检查缓存中是否已有该状态的动画
        if state in self._animation_cache:
            logger.debug(f"从缓存加载{state.name}状态的占位符动画")
            # 将最近使用的项移到末尾（OrderedDict LRU机制）
            animation = self._animation_cache.pop(state)
            self._animation_cache[state] = animation
            
            # 更新命中统计
            self._stats["cache_hits"] += 1
            self._update_hit_rate()
            
            return animation
            
        # 缓存中没有，需要加载模块
        # 更新未命中统计
        self._stats["cache_misses"] += 1
        self._update_hit_rate()
        
        module_name = state.name.lower() + "_placeholder"
        try:
            module_path = f"status.pet_assets.placeholders.{module_name}"
            logger.debug(f"尝试加载占位符模块: {module_path}")
            placeholder_module = importlib.import_module(module_path)
            if hasattr(placeholder_module, "create_animation"):
                animation_instance = placeholder_module.create_animation()
                if isinstance(animation_instance, Animation):
                    logger.debug(f"成功加载{state.name}状态的占位符动画")
                    
                    # 添加到缓存
                    self._add_to_cache(state, animation_instance)
                    
                    return animation_instance
                else:
                    logger.error(f"错误: {module_path}中的create_animation未返回Animation对象")
                    return None
            else:
                logger.error(f"错误: 在{module_path}中未找到create_animation函数")
                return None
        except ImportError:
            logger.warning(f"未能导入状态{state.name}的占位符模块{module_path}")
            return None
        except Exception as e:
            logger.error(f"加载状态{state.name}的占位符时发生意外错误: {e}")
            return None
            
    def _add_to_cache(self, state: PetState, animation: Animation) -> None:
        """将动画添加到缓存中，如果缓存已满则移除最久未使用的项
        
        Args:
            state: 宠物状态
            animation: 动画对象
        """
        # 如果缓存已达到大小限制，移除最早添加的项（OrderedDict的第一项）
        if len(self._animation_cache) >= self._cache_size_limit:
            self._animation_cache.popitem(last=False)
            
        # 添加新项到缓存
        self._animation_cache[state] = animation
        
    def clear_cache(self) -> None:
        """清空动画缓存"""
        self._animation_cache.clear()
        logger.debug("已清空动画缓存")
    
    def get_cache_info(self) -> dict:
        """获取缓存信息
        
        Returns:
            dict: 包含缓存大小、限制和缓存的状态列表的字典
        """
        return {
            "size": len(self._animation_cache),
            "limit": self._cache_size_limit,
            "states": [state.name for state in self._animation_cache.keys()]
        }
        
    def _update_hit_rate(self) -> None:
        """更新缓存命中率"""
        if self._stats["total_requests"] > 0:
            self._stats["hit_rate"] = self._stats["cache_hits"] / self._stats["total_requests"]
        else:
            self._stats["hit_rate"] = 0.0
            
    def get_cache_stats(self) -> dict:
        """获取缓存统计信息
        
        Returns:
            dict: 包含请求总数、命中次数、未命中次数和命中率的字典
        """
        return self._stats.copy()
        
    def reset_cache_stats(self) -> None:
        """重置缓存统计数据"""
        self._stats = {
            "total_requests": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "hit_rate": 0.0
        } 