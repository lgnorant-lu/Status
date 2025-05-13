"""
---------------------------------------------------------------
File name:                  interaction_area.py
Author:                     Ignorant-lu
Date created:               2025/05/13
Description:                桌宠互动区域定义和管理
----------------------------------------------------------------

Changed history:            
                            2025/05/13: 初始创建;
----
"""

from typing import Dict, List, Optional, Tuple, Any
from enum import Enum, auto
import logging

from PySide6.QtCore import QRect, QPoint


class InteractionType(Enum):
    """交互类型枚举"""
    CLICK = auto()        # 单击
    DOUBLE_CLICK = auto() # 双击
    RIGHT_CLICK = auto()  # 右键点击
    DRAG = auto()         # 拖动
    HOVER = auto()        # 悬停
    PET = auto()          # 抚摸(滑动或按住拖动)


class InteractionArea:
    """互动区域定义
    
    定义桌宠身体的特定区域及不同交互对应的状态
    """
    
    def __init__(self, name: str, rect: QRect, states: Dict[InteractionType, int]):
        """初始化互动区域
        
        Args:
            name: 区域名称，如"head"、"body"、"tail"等
            rect: 区域矩形范围
            states: 不同交互类型对应的状态ID字典，如{InteractionType.CLICK: PetState.CLICKED.value}
        """
        self.name = name
        self.rect = rect
        self.states = states
        self.logger = logging.getLogger(f"Status.Interaction.Area.{name}")
        
    def contains(self, point: QPoint) -> bool:
        """检查点是否在区域内
        
        Args:
            point: 待检查的点坐标
            
        Returns:
            bool: 如果点在区域内返回True，否则返回False
        """
        return self.rect.contains(point)
    
    def get_state_id_for_interaction(self, interaction_type: InteractionType) -> Optional[int]:
        """获取指定交互类型对应的状态ID
        
        Args:
            interaction_type: 交互类型
            
        Returns:
            Optional[int]: 对应的状态ID，如果没有对应状态则返回None
        """
        return self.states.get(interaction_type)
    
    def __str__(self) -> str:
        """返回区域的字符串表示
        
        Returns:
            str: 区域字符串表示
        """
        return f"InteractionArea({self.name}, {self.rect}, states={len(self.states)} types)"


class InteractionAreaManager:
    """互动区域管理器
    
    管理所有互动区域，处理区域检测和状态映射
    """
    
    def __init__(self):
        """初始化互动区域管理器"""
        self.areas: List[InteractionArea] = []
        self.logger = logging.getLogger("Status.Interaction.AreaManager")
        
    def add_area(self, area: InteractionArea) -> None:
        """添加互动区域
        
        Args:
            area: 待添加的互动区域
        """
        self.areas.append(area)
        self.logger.debug(f"添加互动区域: {area}")
        
    def remove_area(self, name: str) -> bool:
        """移除指定名称的互动区域
        
        Args:
            name: 区域名称
            
        Returns:
            bool: 如果成功移除则返回True，如果区域不存在则返回False
        """
        for i, area in enumerate(self.areas):
            if area.name == name:
                self.areas.pop(i)
                self.logger.debug(f"移除互动区域: {name}")
                return True
        return False
    
    def get_area_at_point(self, point: QPoint) -> Optional[InteractionArea]:
        """获取指定点所在的区域
        
        如果点在多个重叠的区域内，返回列表中最后添加的（最上层）区域
        
        Args:
            point: 坐标点
            
        Returns:
            Optional[InteractionArea]: 点所在的区域，如果点不在任何区域内则返回None
        """
        # 倒序遍历，先处理后添加的区域（假设后添加的在上层）
        for area in reversed(self.areas):
            if area.contains(point):
                return area
        return None
    
    def get_state_id_for_interaction(self, point: QPoint, interaction_type: InteractionType) -> Optional[Tuple[str, int]]:
        """获取指定点和交互类型对应的区域名称和状态ID
        
        Args:
            point: 坐标点
            interaction_type: 交互类型
            
        Returns:
            Optional[Tuple[str, int]]: (区域名称, 状态ID)元组，如果没有对应区域或状态则返回None
        """
        area = self.get_area_at_point(point)
        if not area:
            return None
            
        state_id = area.get_state_id_for_interaction(interaction_type)
        if state_id is None:
            return None
            
        return (area.name, state_id)
    
    def clear(self) -> None:
        """清除所有互动区域"""
        self.areas.clear()
        self.logger.debug("清除所有互动区域")
    
    def __len__(self) -> int:
        """返回区域数量
        
        Returns:
            int: 区域数量
        """
        return len(self.areas) 