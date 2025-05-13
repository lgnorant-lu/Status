"""
---------------------------------------------------------------
File name:                  interaction_tracker.py
Author:                     Ignorant-lu
Date created:               2025/05/13
Description:                跟踪用户交互频率和模式
----------------------------------------------------------------

Changed history:            
                            2025/05/13: 初始创建;
----
"""

import time
import logging
from typing import Dict, List, Tuple, Optional, Any
import math
from dataclasses import dataclass

from status.interaction.interaction_area import InteractionType


@dataclass
class InteractionRecord:
    """交互记录"""
    timestamp: float  # 交互时间戳
    count: int = 1    # 交互计数
    
    def update(self) -> None:
        """更新记录
        
        更新时间戳并增加计数
        """
        self.timestamp = time.time()
        self.count += 1


class InteractionTracker:
    """追踪用户互动频率和模式
    
    记录用户与桌宠的互动历史，计算频率并提供强度估计
    """
    
    def __init__(self, decay_rate: float = 0.1, decay_interval: float = 3600, max_intensity: float = 5.0):
        """初始化交互跟踪器
        
        Args:
            decay_rate: 计数衰减率，决定了计数衰减的速度，默认为0.1
            decay_interval: 衰减间隔（秒），默认为1小时
            max_intensity: 最大强度值，默认为5.0
        """
        # 区域交互记录: {区域名称: {交互类型: 记录}}
        self.interaction_records: Dict[str, Dict[InteractionType, InteractionRecord]] = {}
        
        self.decay_rate = decay_rate
        self.decay_interval = decay_interval
        self.max_intensity = max_intensity
        self.logger = logging.getLogger("Status.Interaction.Tracker")
        
        # 上次衰减时间
        self.last_decay_time = time.time()
    
    def record_interaction(self, area_name: str, interaction_type: InteractionType) -> None:
        """记录交互
        
        记录用户与特定区域的特定类型交互
        
        Args:
            area_name: 区域名称
            interaction_type: 交互类型
        """
        # 检查并应用衰减
        self._apply_decay_if_needed()
        
        # 初始化区域记录（如果不存在）
        if area_name not in self.interaction_records:
            self.interaction_records[area_name] = {}
        
        area_records = self.interaction_records[area_name]
        
        # 更新或创建记录
        if interaction_type in area_records:
            area_records[interaction_type].update()
        else:
            area_records[interaction_type] = InteractionRecord(time.time())
            
        self.logger.debug(f"记录交互: {area_name} - {interaction_type.name}, " +
                         f"计数: {area_records[interaction_type].count}")
    
    def get_interaction_count(self, area_name: str, interaction_type: Optional[InteractionType] = None) -> int:
        """获取区域的交互计数
        
        Args:
            area_name: 区域名称
            interaction_type: 交互类型，如果为None则返回所有类型的总计数
            
        Returns:
            int: 交互计数
        """
        if area_name not in self.interaction_records:
            return 0
            
        area_records = self.interaction_records[area_name]
        
        if interaction_type is None:
            # 返回所有类型的总计数
            return sum(record.count for record in area_records.values())
        elif interaction_type in area_records:
            return area_records[interaction_type].count
        else:
            return 0
    
    def get_interaction_intensity(self, area_name: str, interaction_type: Optional[InteractionType] = None) -> float:
        """获取交互强度
        
        基于交互计数计算强度值，强度值在0到max_intensity之间
        
        Args:
            area_name: 区域名称
            interaction_type: 交互类型，如果为None则基于所有类型的总计数计算
            
        Returns:
            float: 交互强度，范围为[0, max_intensity]
        """
        count = self.get_interaction_count(area_name, interaction_type)
        
        # 使用对数函数计算强度，避免线性增长过快
        # 公式: min(max_intensity, log(1 + count) / log(10) * max_intensity)
        if count <= 0:
            return 0.0
            
        intensity = math.log(1 + count) / math.log(10) * self.max_intensity
        return min(intensity, self.max_intensity)
    
    def _apply_decay_if_needed(self) -> None:
        """根据需要应用衰减
        
        检查距离上次衰减的时间间隔，如果超过decay_interval则应用衰减
        """
        current_time = time.time()
        elapsed = current_time - self.last_decay_time
        
        if elapsed < self.decay_interval:
            return
            
        # 计算需要应用的衰减次数
        decay_times = int(elapsed / self.decay_interval)
        
        if decay_times > 0:
            self._apply_decay(decay_times)
            self.last_decay_time = current_time
    
    def _apply_decay(self, times: int = 1) -> None:
        """应用衰减到所有交互记录
        
        Args:
            times: 衰减次数，默认为1
        """
        decay_factor = (1.0 - self.decay_rate) ** times
        
        for area_name, area_records in self.interaction_records.items():
            for interaction_type, record in list(area_records.items()):
                # 更新计数，应用衰减
                new_count = int(record.count * decay_factor)
                
                if new_count > 0:
                    record.count = new_count
                else:
                    # 如果计数为0，移除记录
                    del area_records[interaction_type]
            
            # 如果区域没有任何记录，移除区域
            if not area_records:
                del self.interaction_records[area_name]
                
        self.logger.debug(f"应用衰减: {times}次, 因子: {decay_factor}")
    
    def clear(self) -> None:
        """清除所有交互记录"""
        self.interaction_records.clear()
        self.last_decay_time = time.time()
        self.logger.debug("清除所有交互记录")
        
    def get_favorite_area(self) -> Optional[str]:
        """获取用户最喜欢的交互区域
        
        Returns:
            Optional[str]: 交互总次数最多的区域名称，如果没有交互记录则返回None
        """
        if not self.interaction_records:
            return None
            
        # 计算每个区域的总交互次数
        area_counts = {area_name: sum(record.count for record in area_records.values())
                      for area_name, area_records in self.interaction_records.items()}
        
        # 返回总次数最多的区域
        if not area_counts:
            return None
            
        return max(area_counts.items(), key=lambda item: item[1])[0]
    
    def get_favorite_interaction(self, area_name: Optional[str] = None) -> Optional[InteractionType]:
        """获取用户最喜欢的交互类型
        
        Args:
            area_name: 区域名称，如果为None则考虑所有区域
            
        Returns:
            Optional[InteractionType]: 交互次数最多的类型，如果没有交互记录则返回None
        """
        if not self.interaction_records:
            return None
            
        if area_name is not None:
            # 指定区域的最喜欢交互
            if area_name not in self.interaction_records:
                return None
                
            area_records = self.interaction_records[area_name]
            if not area_records:
                return None
                
            return max(area_records.items(), key=lambda item: item[1].count)[0]
        else:
            # 所有区域的总计
            type_counts = {}
            
            for area_records in self.interaction_records.values():
                for interaction_type, record in area_records.items():
                    if interaction_type in type_counts:
                        type_counts[interaction_type] += record.count
                    else:
                        type_counts[interaction_type] = record.count
            
            if not type_counts:
                return None
                
            return max(type_counts.items(), key=lambda item: item[1])[0] 