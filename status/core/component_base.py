"""
---------------------------------------------------------------
File name:                  component_base.py
Author:                     Ignorant-lu
Date created:               2025/05/13
Description:                定义组件基类，提供组件生命周期管理和基本接口
----------------------------------------------------------------

Changed history:            
                            2025/05/13: 初始创建;
----
"""

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, List, Set


class ComponentBase(ABC):
    """组件基类
    
    提供组件生命周期管理（初始化、更新、关闭）和基本接口
    所有功能模块应该继承此类
    """
    
    def __init__(self):
        """初始化组件基类"""
        self.logger = logging.getLogger(f"Status.Core.{self.__class__.__name__}")
        self.is_initialized = False
        self.is_active = False
        self.name = self.__class__.__name__
        self.logger.debug(f"组件创建: {self.name}")
        
        # 组件配置
        self.config: Dict[str, Any] = {}
        
        # 依赖组件列表
        self.dependencies: List[ComponentBase] = []
        
        # 启动组件
        self.activate()
    
    def activate(self) -> bool:
        """激活组件
        
        执行初始化并开始组件工作
        
        Returns:
            bool: 是否成功激活
        """
        if self.is_active:
            self.logger.warning(f"{self.name} 已处于活动状态")
            return True
            
        # 初始化组件
        if not self.is_initialized:
            try:
                self.is_initialized = self._initialize()
                if not self.is_initialized:
                    self.logger.error(f"{self.name} 初始化失败")
                    return False
            except Exception as e:
                self.logger.error(f"{self.name} 初始化异常: {e}", exc_info=True)
                return False
                
        self.is_active = True
        self.logger.info(f"{self.name} 已激活")
        return True
    
    def deactivate(self) -> bool:
        """停用组件
        
        停止组件工作但不关闭（可重新激活）
        
        Returns:
            bool: 是否成功停用
        """
        if not self.is_active:
            self.logger.warning(f"{self.name} 已处于非活动状态")
            return True
            
        self.is_active = False
        self.logger.info(f"{self.name} 已停用")
        return True
    
    def update(self, delta_time: float) -> None:
        """更新组件状态
        
        需要定期调用以更新组件内部状态
        
        Args:
            delta_time: 自上次更新以来的时间增量（秒）
        """
        if not self.is_active:
            return
            
        try:
            self._update(delta_time)
        except Exception as e:
            self.logger.error(f"{self.name} 更新异常: {e}", exc_info=True)
    
    def shutdown(self) -> bool:
        """关闭组件
        
        执行清理工作并释放资源
        
        Returns:
            bool: 是否成功关闭
        """
        if not self.is_initialized:
            self.logger.warning(f"{self.name} 尚未初始化")
            return True
            
        self.is_active = False
        
        try:
            result = self._shutdown()
            self.is_initialized = False
            self.logger.info(f"{self.name} 已关闭")
            return result
        except Exception as e:
            self.logger.error(f"{self.name} 关闭异常: {e}", exc_info=True)
            return False
    
    def set_config(self, config: Dict[str, Any]) -> None:
        """设置组件配置
        
        Args:
            config: 配置字典
        """
        self.config.update(config)
        self.logger.debug(f"{self.name} 配置已更新")
    
    def get_config(self, key: str, default: Any = None) -> Any:
        """获取配置项
        
        Args:
            key: 配置键
            default: 默认值（如果键不存在）
            
        Returns:
            Any: 配置值
        """
        return self.config.get(key, default)
    
    def add_dependency(self, component: 'ComponentBase') -> None:
        """添加依赖组件
        
        Args:
            component: 依赖的组件
        """
        if component not in self.dependencies:
            self.dependencies.append(component)
            self.logger.debug(f"{self.name} 添加依赖: {component.name}")
    
    def get_dependencies(self) -> List['ComponentBase']:
        """获取依赖组件列表
        
        Returns:
            List[ComponentBase]: 依赖组件列表
        """
        return self.dependencies.copy()
    
    # 子类应实现的方法
    
    def _initialize(self) -> bool:
        """初始化组件
        
        执行组件的初始化工作，子类应重写此方法
        
        Returns:
            bool: 是否成功初始化
        """
        return True
    
    def _update(self, delta_time: float) -> None:
        """更新组件状态
        
        执行组件的更新工作，子类应重写此方法
        
        Args:
            delta_time: 自上次更新以来的时间增量（秒）
        """
        pass
    
    def _shutdown(self) -> bool:
        """关闭组件
        
        执行组件的清理工作，子类应重写此方法
        
        Returns:
            bool: 是否成功关闭
        """
        return True 