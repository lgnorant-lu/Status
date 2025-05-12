"""
---------------------------------------------------------------
File name:                  component_base.py
Author:                     Ignorant-lu
Date created:               2025/05/18
Description:                组件基类，定义组件的基本接口和功能
----------------------------------------------------------------

Changed history:            
                            2025/05/18: 初始创建;
----
"""

import uuid
import logging
from typing import Dict, Any, Optional


class ComponentBase:
    """组件基类，所有组件的基础实现"""
    
    def __init__(self):
        """初始化组件基类"""
        self.id = uuid.uuid4()  # 组件唯一标识符
        self.enabled = True  # 组件是否启用
        self.initialized = False  # 组件是否已初始化
        self.data = {}  # 组件数据存储
        self.logger = logging.getLogger(f"{self.__class__.__name__}.{self.id}")
    
    def initialize(self) -> bool:
        """初始化组件
        
        Returns:
            bool: 初始化是否成功
        """
        if self.initialized:
            return True
            
        result = self._initialize()
        if result:
            self.initialized = True
            
        return result
    
    def _initialize(self) -> bool:
        """初始化实现，子类可覆盖
        
        Returns:
            bool: 初始化是否成功
        """
        return True
    
    def update(self, dt: float) -> None:
        """更新组件状态
        
        Args:
            dt: 时间增量（秒）
        """
        if not self.enabled or not self.initialized:
            return
            
        self._update(dt)
    
    def _update(self, dt: float) -> None:
        """更新实现，子类可覆盖
        
        Args:
            dt: 时间增量（秒）
        """
        pass
    
    def enable(self) -> None:
        """启用组件"""
        self.enabled = True
    
    def disable(self) -> None:
        """禁用组件"""
        self.enabled = False
    
    def is_enabled(self) -> bool:
        """检查组件是否启用
        
        Returns:
            bool: 组件是否启用
        """
        return self.enabled
    
    def is_initialized(self) -> bool:
        """检查组件是否已初始化
        
        Returns:
            bool: 组件是否已初始化
        """
        return self.initialized
    
    def get_data(self, key: str, default: Any = None) -> Any:
        """获取组件数据
        
        Args:
            key: 数据键
            default: 默认值
            
        Returns:
            Any: 数据值
        """
        return self.data.get(key, default)
    
    def set_data(self, key: str, value: Any) -> None:
        """设置组件数据
        
        Args:
            key: 数据键
            value: 数据值
        """
        self.data[key] = value 