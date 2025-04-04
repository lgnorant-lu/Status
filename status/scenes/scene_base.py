"""
---------------------------------------------------------------
File name:                  scene_base.py
Author:                     Ignorant-lu
Date created:               2025/04/03
Description:                场景基类，定义所有场景的共同接口
----------------------------------------------------------------

Changed history:            
                            2025/04/03: 初始创建;
----
"""

import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Tuple

class SceneBase(ABC):
    """场景基类，定义所有场景必须实现的接口"""
    
    def __init__(self, scene_id: str, name: str):
        """初始化场景
        
        Args:
            scene_id: 场景唯一标识符
            name: 场景显示名称
        """
        self.scene_id = scene_id
        self.name = name
        self.active = False
        self.initialized = False
        self.logger = logging.getLogger(f"Hollow-ming.Scenes.{scene_id}")
        self.data = {}  # 场景数据存储
        
        # 场景元素列表，将在子类中填充
        self.elements = {}
        
        # 场景尺寸，可在子类中覆盖
        self.size = (300, 400)  # 宽度, 高度
    
    def initialize(self) -> bool:
        """初始化场景，加载资源等
        
        Returns:
            bool: 初始化是否成功
        """
        if self.initialized:
            self.logger.debug("场景已初始化，跳过")
            return True
        
        self.logger.info(f"初始化场景: {self.name}")
        
        try:
            # 加载场景资源等操作
            # 实际实现在子类中完成
            result = self._initialize_impl()
            
            if result:
                self.initialized = True
                self.logger.info(f"场景初始化成功: {self.name}")
            else:
                self.logger.error(f"场景初始化失败: {self.name}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"场景初始化异常: {str(e)}", exc_info=True)
            return False
    
    @abstractmethod
    def _initialize_impl(self) -> bool:
        """初始化实现，子类必须实现此方法
        
        Returns:
            bool: 初始化是否成功
        """
        pass
    
    def activate(self, **kwargs) -> bool:
        """激活场景，当场景被切换为当前场景时调用
        
        Args:
            **kwargs: 激活参数
            
        Returns:
            bool: 激活是否成功
        """
        if not self.initialized and not self.initialize():
            self.logger.error(f"无法激活未初始化的场景: {self.name}")
            return False
        
        self.logger.info(f"激活场景: {self.name}")
        
        try:
            # 激活场景实现，子类可以覆盖
            result = self._activate_impl(**kwargs)
            
            if result:
                self.active = True
                self.logger.info(f"场景激活成功: {self.name}")
            else:
                self.logger.error(f"场景激活失败: {self.name}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"场景激活异常: {str(e)}", exc_info=True)
            return False
    
    def _activate_impl(self, **kwargs) -> bool:
        """激活实现，子类可以覆盖此方法
        
        Returns:
            bool: 激活是否成功
        """
        # 默认实现直接返回成功
        return True
    
    def deactivate(self) -> bool:
        """停用场景，当场景不再是当前场景时调用
        
        Returns:
            bool: 停用是否成功
        """
        if not self.active:
            self.logger.debug(f"场景已经是停用状态: {self.name}")
            return True
        
        self.logger.info(f"停用场景: {self.name}")
        
        try:
            # 停用场景实现，子类可以覆盖
            result = self._deactivate_impl()
            
            if result:
                self.active = False
                self.logger.info(f"场景停用成功: {self.name}")
            else:
                self.logger.error(f"场景停用失败: {self.name}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"场景停用异常: {str(e)}", exc_info=True)
            return False
    
    def _deactivate_impl(self) -> bool:
        """停用实现，子类可以覆盖此方法
        
        Returns:
            bool: 停用是否成功
        """
        # 默认实现直接返回成功
        return True
    
    def update(self, delta_time: float, system_data: Dict[str, Any]) -> None:
        """更新场景状态
        
        Args:
            delta_time: 自上次更新以来的时间（秒）
            system_data: 系统监控数据
        """
        if not self.active:
            return
        
        try:
            # 更新场景实现，子类必须实现
            self._update_impl(delta_time, system_data)
            
        except Exception as e:
            self.logger.error(f"场景更新异常: {str(e)}", exc_info=True)
    
    @abstractmethod
    def _update_impl(self, delta_time: float, system_data: Dict[str, Any]) -> None:
        """更新实现，子类必须实现此方法
        
        Args:
            delta_time: 自上次更新以来的时间（秒）
            system_data: 系统监控数据
        """
        pass
    
    def render(self, surface: Any) -> None:
        """渲染场景
        
        Args:
            surface: 渲染目标表面
        """
        if not self.active:
            return
        
        try:
            # 渲染场景实现，子类必须实现
            self._render_impl(surface)
            
        except Exception as e:
            self.logger.error(f"场景渲染异常: {str(e)}", exc_info=True)
    
    @abstractmethod
    def _render_impl(self, surface: Any) -> None:
        """渲染实现，子类必须实现此方法
        
        Args:
            surface: 渲染目标表面
        """
        pass
    
    def handle_input(self, event_type: str, event_data: Any) -> bool:
        """处理输入事件
        
        Args:
            event_type: 事件类型
            event_data: 事件数据
            
        Returns:
            bool: 事件是否被处理
        """
        if not self.active:
            return False
        
        try:
            # 处理输入实现，子类可以覆盖
            return self._handle_input_impl(event_type, event_data)
            
        except Exception as e:
            self.logger.error(f"场景输入处理异常: {str(e)}", exc_info=True)
            return False
    
    def _handle_input_impl(self, event_type: str, event_data: Any) -> bool:
        """输入处理实现，子类可以覆盖此方法
        
        Args:
            event_type: 事件类型
            event_data: 事件数据
            
        Returns:
            bool: 事件是否被处理
        """
        # 默认实现不处理任何事件
        return False
    
    def cleanup(self) -> bool:
        """清理场景资源
        
        Returns:
            bool: 清理是否成功
        """
        if not self.initialized:
            self.logger.debug(f"场景未初始化，无需清理: {self.name}")
            return True
        
        self.logger.info(f"清理场景: {self.name}")
        
        try:
            # 清理场景实现，子类可以覆盖
            result = self._cleanup_impl()
            
            if result:
                self.initialized = False
                self.active = False
                self.logger.info(f"场景清理成功: {self.name}")
            else:
                self.logger.error(f"场景清理失败: {self.name}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"场景清理异常: {str(e)}", exc_info=True)
            return False
    
    def _cleanup_impl(self) -> bool:
        """清理实现，子类可以覆盖此方法
        
        Returns:
            bool: 清理是否成功
        """
        # 默认实现直接返回成功
        return True
    
    def get_data(self, key: str, default: Any = None) -> Any:
        """获取场景数据
        
        Args:
            key: 数据键
            default: 默认值，如果键不存在
            
        Returns:
            数据值或默认值
        """
        return self.data.get(key, default)
    
    def set_data(self, key: str, value: Any) -> None:
        """设置场景数据
        
        Args:
            key: 数据键
            value: 数据值
        """
        self.data[key] = value
        
    def get_size(self) -> Tuple[int, int]:
        """获取场景尺寸
        
        Returns:
            (宽度, 高度)
        """
        return self.size
    
    def set_size(self, width: int, height: int) -> None:
        """设置场景尺寸
        
        Args:
            width: 宽度
            height: 高度
        """
        self.size = (width, height)
        
    def is_active(self) -> bool:
        """检查场景是否活动
        
        Returns:
            bool: 场景是否活动
        """
        return self.active
    
    def is_initialized(self) -> bool:
        """检查场景是否已初始化
        
        Returns:
            bool: 场景是否已初始化
        """
        return self.initialized 