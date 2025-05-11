"""
---------------------------------------------------------------
File name:                  behavior_manager.py
Author:                     Ignorant-lu
Date created:               2025/04/04
Description:                桌宠行为管理器
----------------------------------------------------------------

Changed history:            
                            2025/04/04: 初始创建;
                            2025/04/04: 添加行为系统集成;
                            2025/05/16: 修复文件编码问题;
                            2025/05/16: 移除循环引用问题;
----
"""

import logging


class BehaviorManager:
    """行为管理器
    
    管理桌宠的行为执行和状态
    """
    
    def __init__(self, entity=None):
        """初始化行为管理器
        
        Args:
            entity: 关联的实体对象
        """
        self.entity = entity
        self.current_behavior = None
        self.behavior_history = []
        self.logger = logging.getLogger("BehaviorManager")
        
        # 确保行为注册表已初始化
        self._initialize_behaviors()
        
    def _initialize_behaviors(self):
        """初始化行为注册表"""
        try:
            # 延迟导入，避免循环引用
            from status.behavior.basic_behaviors import initialize_behaviors
            initialize_behaviors()
            self.logger.info("行为注册表初始化完成")
        except Exception as e:
            self.logger.error(f"行为注册表初始化失败: {e}")
        
    def execute_behavior(self, behavior_id, params=None):
        """执行指定ID的行为
        
        Args:
            behavior_id (str): 行为唯一标识符
            params (dict, optional): 行为参数
            
        Returns:
            bool: 行为是否成功执行
        """
        self.logger.debug(f"执行行为: {behavior_id} 参数: {params}")
        
        if self.current_behavior:
            self.logger.debug(f"停止当前行为: {self.current_behavior.name}")
            self.current_behavior.stop()
            
        try:
            # 延迟导入，避免循环引用
            from status.behavior.basic_behaviors import BehaviorRegistry
            registry = BehaviorRegistry.get_instance()
            self.current_behavior = registry.create(behavior_id, **(params or {}))
            
            # 确保params不为None
            behavior_params = params or {}
            self.current_behavior.start(behavior_params)
            
            # 记录行为历史
            self.behavior_history.append({
                'behavior_id': behavior_id,
                'params': params
            })
            if len(self.behavior_history) > 20:  # 限制历史记录长度
                self.behavior_history.pop(0)
                
            return True
        except ValueError as e:
            self.logger.error(f"执行行为失败: {e}")
            return False
        except Exception as e:
            self.logger.error(f"执行行为时发生未知错误: {e}")
            return False
            
    def update(self, dt):
        """更新当前行为
        
        Args:
            dt (float): 时间增量（秒）
        """
        if self.current_behavior and self.current_behavior.is_running:
            try:
                is_completed = self.current_behavior.update(dt)
                if is_completed:
                    self.logger.debug(f"行为完成: {self.current_behavior.name}")
                    self.current_behavior = None
            except Exception as e:
                self.logger.error(f"更新行为时发生错误: {e}")
                self.current_behavior = None
                
    def stop_current_behavior(self):
        """停止当前行为"""
        if self.current_behavior:
            self.logger.debug(f"手动停止行为: {self.current_behavior.name}")
            self.current_behavior.stop()
            self.current_behavior = None
            return True
        return False
        
    def get_current_behavior(self):
        """获取当前正在执行的行为
        
        Returns:
            dict or None: 包含当前行为信息的字典，如果没有行为则返回None
        """
        if not self.current_behavior:
            return None
            
        return {
            'name': self.current_behavior.name,
            'running': self.current_behavior.is_running,
            'duration': self.current_behavior.duration,
            'loop': self.current_behavior.loop,
            'params': self.current_behavior.params
        }
        
    def get_available_behaviors(self):
        """获取所有可用的行为ID列表
        
        Returns:
            list: 行为ID列表
        """
        # 延迟导入，避免循环引用
        from status.behavior.basic_behaviors import BehaviorRegistry
        registry = BehaviorRegistry.get_instance()
        return list(registry.behaviors.keys()) 