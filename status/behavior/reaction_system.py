"""
---------------------------------------------------------------
File name:                  reaction_system.py
Author:                     Ignorant-lu
Date created:               2025/04/04
Description:                桌宠反应系统 - 处理用户操作与桌宠行为的映射
----------------------------------------------------------------

Changed history:            
                            2025/04/04: 初始创建;
----
"""

import logging
import time
from typing import Callable, Dict, List, Optional, Any, Union


class Reaction:
    """反应类
    
    定义特定用户操作与桌宠行为之间的映射关系
    """
    
    def __init__(self, 
                 event_type: str, 
                 conditions: Optional[Callable] = None, 
                 behavior_id: Optional[str] = None, 
                 behavior_params: Optional[Dict[str, Any]] = None, 
                 priority: int = 0):
        """初始化反应
        
        Args:
            event_type (str): 事件类型（如'click', 'drag', 'hover'等）
            conditions (callable, optional): 额外的条件判断函数，接收event和entity参数
            behavior_id (str, optional): 要执行的行为ID
            behavior_params (dict, optional): 行为参数
            priority (int, optional): 优先级，数值越高优先级越高
        """
        self.event_type = event_type
        self.conditions = conditions or (lambda event, entity: True)
        self.behavior_id = behavior_id
        self.behavior_params = behavior_params or {}
        self.priority = priority
        
    def matches(self, event_type: str, event: Any, entity: Any) -> bool:
        """检查事件是否匹配该反应
        
        Args:
            event_type (str): 事件类型
            event: 事件对象
            entity: 实体对象
            
        Returns:
            bool: 是否匹配
        """
        try:
            return event_type == self.event_type and self.conditions(event, entity)
        except Exception as e:
            logging.getLogger("Reaction").error(f"反应条件检查失败: {e}")
            return False


class ReactionSystem:
    """反应系统
    
    管理所有反应规则，处理事件并触发相应行为
    """
    
    def __init__(self, entity):
        """初始化反应系统
        
        Args:
            entity: 关联的实体对象
        """
        self.entity = entity
        self.reactions: List[Reaction] = []
        self.logger = logging.getLogger("ReactionSystem")
        self.last_events = {}  # 记录最近的事件时间戳，用于防抖
        self.debounce_time = 0.2  # 默认防抖时间（秒）
        
    def add_reaction(self, reaction: Reaction) -> None:
        """添加反应规则
        
        Args:
            reaction (Reaction): 反应规则
        """
        self.reactions.append(reaction)
        # 按优先级排序
        self.reactions.sort(key=lambda r: -r.priority)
        self.logger.debug(f"添加反应: {reaction.event_type} -> {reaction.behavior_id}")
        
    def remove_reaction(self, event_type: str, behavior_id: Optional[str] = None) -> int:
        """移除反应规则
        
        Args:
            event_type (str): 事件类型
            behavior_id (str, optional): 行为ID，如果为None则移除所有匹配事件类型的反应
            
        Returns:
            int: 移除的反应数量
        """
        original_count = len(self.reactions)
        
        if behavior_id is None:
            self.reactions = [r for r in self.reactions if r.event_type != event_type]
        else:
            self.reactions = [r for r in self.reactions if not (r.event_type == event_type and r.behavior_id == behavior_id)]
            
        removed_count = original_count - len(self.reactions)
        if removed_count > 0:
            self.logger.debug(f"移除{removed_count}个反应规则: {event_type}")
        return removed_count
        
    def handle_event(self, event_type: str, event: Any, debounce: bool = True) -> bool:
        """处理事件，触发相应反应
        
        Args:
            event_type (str): 事件类型
            event: 事件对象
            debounce (bool, optional): 是否启用防抖，默认为True
            
        Returns:
            bool: 是否有反应被触发
        """
        current_time = time.time()
        
        # 防抖处理
        if debounce and event_type in self.last_events:
            if current_time - self.last_events[event_type] < self.debounce_time:
                self.logger.debug(f"事件{event_type}被防抖过滤")
                return False
        
        self.last_events[event_type] = current_time
        self.logger.debug(f"处理事件: {event_type}")
        
        for reaction in self.reactions:
            if reaction.matches(event_type, event, self.entity):
                self.logger.debug(f"触发反应: {reaction.event_type} -> {reaction.behavior_id}")
                
                if reaction.behavior_id and hasattr(self.entity, 'behavior_manager'):
                    success = self.entity.behavior_manager.execute_behavior(
                        reaction.behavior_id, 
                        params=reaction.behavior_params
                    )
                    if success:
                        return True
        
        return False
    
    def set_debounce_time(self, seconds: float) -> None:
        """设置防抖时间
        
        Args:
            seconds (float): 防抖时间（秒）
        """
        self.debounce_time = max(0.0, seconds)
        self.logger.debug(f"设置防抖时间: {self.debounce_time}秒")
        
    def get_reactions_for_event(self, event_type: str) -> List[Reaction]:
        """获取特定事件类型的所有反应
        
        Args:
            event_type (str): 事件类型
            
        Returns:
            List[Reaction]: 反应列表
        """
        return [r for r in self.reactions if r.event_type == event_type]


class ReactionSystemEventHandler:
    """反应系统事件处理器
    
    连接交互系统和反应系统，将交互事件转发给反应系统
    """
    
    def __init__(self, reaction_system: ReactionSystem):
        """初始化事件处理器
        
        Args:
            reaction_system (ReactionSystem): 反应系统实例
        """
        self.reaction_system = reaction_system
        self.logger = logging.getLogger("ReactionSystemEventHandler")
        self.hover_start_time = None
        
    def register_handlers(self, interaction_manager) -> None:
        """注册事件处理器
        
        Args:
            interaction_manager: 交互管理器实例
        """
        # 注册点击事件处理器
        interaction_manager.register_handler('mouse_click', self.on_mouse_click)
        
        # 注册双击事件处理器
        interaction_manager.register_handler('mouse_double_click', self.on_mouse_double_click)
        
        # 注册拖拽事件处理器
        interaction_manager.register_handler('drag_start', self.on_drag_start)
        interaction_manager.register_handler('drag_end', self.on_drag_end)
        
        # 注册悬停事件处理器
        interaction_manager.register_handler('mouse_hover', self.on_mouse_hover)
        interaction_manager.register_handler('mouse_leave', self.on_mouse_leave)
        
        # 注册托盘菜单事件处理器
        interaction_manager.register_handler('tray_menu_show', self.on_tray_menu_show)
        
        self.logger.info("反应系统事件处理器已注册")
        
    def on_mouse_click(self, event) -> bool:
        """处理鼠标点击事件
        
        Args:
            event: 鼠标点击事件
            
        Returns:
            bool: 事件是否被处理
        """
        return self.reaction_system.handle_event('click', event)
    
    def on_mouse_double_click(self, event) -> bool:
        """处理鼠标双击事件
        
        Args:
            event: 鼠标双击事件
            
        Returns:
            bool: 事件是否被处理
        """
        return self.reaction_system.handle_event('double_click', event)
    
    def on_drag_start(self, event) -> bool:
        """处理拖拽开始事件
        
        Args:
            event: 拖拽开始事件
            
        Returns:
            bool: 事件是否被处理
        """
        return self.reaction_system.handle_event('drag_start', event)
    
    def on_drag_end(self, event) -> bool:
        """处理拖拽结束事件
        
        Args:
            event: 拖拽结束事件
            
        Returns:
            bool: 事件是否被处理
        """
        return self.reaction_system.handle_event('drag_end', event)
    
    def on_mouse_hover(self, event) -> bool:
        """处理鼠标悬停事件
        
        Args:
            event: 鼠标悬停事件
            
        Returns:
            bool: 事件是否被处理
        """
        current_time = time.time()
        
        if self.hover_start_time is None:
            self.hover_start_time = current_time
            
        # 计算悬停时间并添加到事件对象
        hover_duration = current_time - self.hover_start_time
        event_with_duration = {'original_event': event, 'hover_duration': hover_duration}
        
        return self.reaction_system.handle_event('hover', event_with_duration, debounce=False)
    
    def on_mouse_leave(self, event) -> bool:
        """处理鼠标离开事件
        
        Args:
            event: 鼠标离开事件
            
        Returns:
            bool: 事件是否被处理
        """
        self.hover_start_time = None
        return self.reaction_system.handle_event('leave', event)
    
    def on_tray_menu_show(self, event) -> bool:
        """处理托盘菜单显示事件
        
        Args:
            event: 托盘菜单显示事件
            
        Returns:
            bool: 事件是否被处理
        """
        return self.reaction_system.handle_event('tray_menu_show', event)


def initialize_default_reactions(reaction_system: ReactionSystem, config: Optional[Dict[str, Any]] = None) -> None:
    """初始化默认反应规则
    
    Args:
        reaction_system (ReactionSystem): 反应系统实例
        config (dict, optional): 配置信息
    """
    config = config or {}
    
    # 点击反应
    reaction_system.add_reaction(Reaction(
        event_type='click',
        behavior_id='jump',
        priority=10
    ))
    
    # 双击反应
    reaction_system.add_reaction(Reaction(
        event_type='double_click',
        behavior_id='high_jump',
        priority=20
    ))
    
    # 拖拽开始反应
    reaction_system.add_reaction(Reaction(
        event_type='drag_start',
        # 这里不需要触发行为，因为拖拽由交互系统直接处理
        priority=30
    ))
    
    # 拖拽结束反应
    reaction_system.add_reaction(Reaction(
        event_type='drag_end',
        behavior_id='fall',
        priority=30
    ))
    
    # 鼠标悬停反应
    reaction_system.add_reaction(Reaction(
        event_type='hover',
        behavior_id='wave',
        behavior_params={'duration': 1.0},
        # 条件：只有当鼠标悬停超过1秒时才触发
        conditions=lambda event, entity: event.get('hover_duration', 0) > 1.0,
        priority=5
    ))
    
    # 鼠标离开反应
    reaction_system.add_reaction(Reaction(
        event_type='leave',
        behavior_id='idle',
        priority=5
    ))
    
    # 系统托盘菜单显示反应
    reaction_system.add_reaction(Reaction(
        event_type='tray_menu_show',
        behavior_id='idle',
        behavior_params={'animation_name': 'attention'},
        priority=15
    ))
    
    reaction_system.logger.info("默认反应规则已初始化") 