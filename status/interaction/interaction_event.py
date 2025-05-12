"""
---------------------------------------------------------------
File name:                  interaction_event.py
Author:                     Ignorant-lu
Date created:               2025/04/03
Description:                桌宠交互事件定义
----------------------------------------------------------------

Changed history:            
                            2025/04/03: 初始创建;
----
"""

import time
from enum import Enum, auto
from status.core.event_system import Event, EventType  # 直接从event_system导入正确的Event和EventType类

class InteractionEventType(Enum):
    """交互事件类型枚举"""
    # 鼠标事件
    MOUSE_CLICK = auto()         # 鼠标单击
    MOUSE_DOUBLE_CLICK = auto()  # 鼠标双击
    MOUSE_RIGHT_CLICK = auto()   # 鼠标右键点击
    MOUSE_MOVE = auto()          # 鼠标移动
    MOUSE_HOVER = auto()         # 鼠标悬停
    MOUSE_ENTER = auto()         # 鼠标进入区域
    MOUSE_LEAVE = auto()         # 鼠标离开区域
    MOUSE_PRESS = auto()         # 鼠标按下
    MOUSE_RELEASE = auto()       # 鼠标释放
    MOUSE_DOWN = auto()          # ADDED - 鼠标按下 (兼容或别名)
    MOUSE_UP = auto()            # ADDED - 鼠标释放 (兼容或别名)
    MOUSE_WHEEL = auto()         # ADDED - 鼠标滚轮
    
    # 拖拽事件
    MOUSE_DRAG_START = auto()    # 开始拖拽(旧名称，保留向后兼容)
    MOUSE_DRAG = auto()          # 拖拽过程中(旧名称，保留向后兼容)
    MOUSE_DRAG_END = auto()      # 结束拖拽(旧名称，保留向后兼容)
    DRAG_START = auto()          # 开始拖拽
    DRAG_MOVE = auto()           # 拖拽移动
    DRAG_END = auto()            # 结束拖拽
    
    # 菜单事件
    MENU_SHOW = auto()           # 显示菜单
    MENU_HIDE = auto()           # 隐藏菜单
    MENU_COMMAND = auto()        # 菜单命令执行
    
    # 托盘事件
    TRAY_ICON_ACTIVATED = auto() # 托盘图标被激活
    TRAY_MENU_COMMAND = auto()   # 托盘菜单命令执行
    
    # 热键事件
    HOTKEY_TRIGGERED = auto()    # 热键被触发
    
    # 键盘事件 (新增)
    KEY_DOWN = auto()            # ADDED - 按键按下
    KEY_UP = auto()              # ADDED - 按键释放
    KEY_PRESS = auto()           # ADDED - 按键按下并释放 (字符输入)
    
    # 触发器事件
    TIMER_TRIGGER = auto()       # 定时器触发
    SYSTEM_EVENT = auto()        # 系统事件触发
    IDLE_TRIGGER = auto()        # 空闲触发
    
    # 状态事件
    PET_STATE_CHANGE = auto()    # 桌宠状态改变
    PET_MOOD_CHANGE = auto()     # 桌宠心情改变
    PET_ACTION_START = auto()    # 桌宠动作开始
    PET_ACTION_END = auto()      # 桌宠动作结束


class InteractionEvent(Event):
    """交互事件类
    
    扩展自基础事件类，添加了交互相关的属性
    
    Args:
        event_type (InteractionEventType): 交互事件类型
        data (dict, optional): 事件数据，包含事件的详细信息
        source (str, optional): 事件源，标识事件从哪里发出
    """
    
    def __init__(self, event_type, data=None, source="interaction"):
        """初始化交互事件
        
        Args:
            event_type (InteractionEventType): 交互事件类型
            data (dict, optional): 事件数据. 默认为None
            source (str, optional): 事件源. 默认为"interaction"
        """
        # 使用 EventType.USER_INTERACTION 作为事件类型
        super().__init__(EventType.USER_INTERACTION, source, data or {})
        self.interaction_type = event_type
        self.event_type = event_type  # 别名，为了保持API一致性
        self.timestamp = time.time()
        
    def __str__(self):
        """返回事件的字符串表示
        
        Returns:
            str: 事件的字符串表示
        """
        return f"InteractionEvent({self.interaction_type.name}, source={self.sender}, data={self.data}, timestamp={self.timestamp})"
    
    @classmethod
    def create_mouse_event(cls, event_type, x, y, button=None):
        """创建鼠标事件
        
        Args:
            event_type (InteractionEventType): 鼠标事件类型
            x (int): 鼠标x坐标
            y (int): 鼠标y坐标
            button (str, optional): 鼠标按钮. 默认为None
            
        Returns:
            InteractionEvent: 鼠标交互事件
        """
        data = {
            "x": x,
            "y": y
        }
        if button:
            data["button"] = button
        return cls(event_type, data)
    
    @classmethod
    def create_menu_event(cls, event_type, menu_id, action_id=None):
        """创建菜单事件
        
        Args:
            event_type (InteractionEventType): 菜单事件类型
            menu_id (str): 菜单ID
            action_id (str, optional): 动作ID. 默认为None
            
        Returns:
            InteractionEvent: 菜单交互事件
        """
        data = {
            "menu_id": menu_id
        }
        if action_id:
            data["action_id"] = action_id
        return cls(event_type, data)
    
    @classmethod
    def create_tray_event(cls, event_type, reason=None, action_id=None):
        """创建托盘事件
        
        Args:
            event_type (InteractionEventType): 托盘事件类型
            reason (str, optional): 激活原因. 默认为None
            action_id (str, optional): 动作ID. 默认为None
            
        Returns:
            InteractionEvent: 托盘交互事件
        """
        data = {}
        if reason:
            data["reason"] = reason
        if action_id:
            data["action_id"] = action_id
        return cls(event_type, data)
    
    @classmethod
    def create_hotkey_event(cls, key_combination):
        """创建热键事件
        
        Args:
            key_combination (str): 按键组合
            
        Returns:
            InteractionEvent: 热键交互事件
        """
        data = {
            "key_combination": key_combination
        }
        return cls(InteractionEventType.HOTKEY_TRIGGERED, data)
    
    @classmethod
    def create_timer_event(cls, timer_id, data=None):
        """创建定时器事件
        
        Args:
            timer_id (str): 定时器ID
            data (dict, optional): 额外数据. 默认为None
            
        Returns:
            InteractionEvent: 定时器交互事件
        """
        event_data = {
            "timer_id": timer_id
        }
        if data:
            event_data.update(data)
        return cls(InteractionEventType.TIMER_TRIGGER, event_data)
    
    @classmethod
    def create_pet_state_event(cls, state_type, old_state, new_state):
        """创建桌宠状态事件
        
        Args:
            state_type (str): 状态类型
            old_state (any): 旧状态
            new_state (any): 新状态
            
        Returns:
            InteractionEvent: 桌宠状态交互事件
        """
        data = {
            "state_type": state_type,
            "old_state": old_state,
            "new_state": new_state
        }
        return cls(InteractionEventType.PET_STATE_CHANGE, data)