"""
---------------------------------------------------------------
File name:                  scene_manager.py
Author:                     Ignorant-lu
Date created:               2025/04/03
Description:                场景管理器，管理场景切换和转场效果
----------------------------------------------------------------

Changed history:            
                            2025/04/03: 初始创建;
----
"""

import logging
from typing import Dict, Any, Optional, List

from status.scenes.scene_base import SceneBase
from status.scenes.scene_transition import TransitionManager, SceneTransition, TransitionState
from status.renderer.renderer_base import RendererBase
from status.core.event_system import EventSystem, EventType, Event

class SceneManager:
    """场景管理器，负责管理场景切换和转场效果"""
    
    # 单例模式
    _instance = None
    
    @classmethod
    def get_instance(cls):
        """获取单例实例"""
        if cls._instance is None:
            cls._instance = SceneManager()
        return cls._instance
    
    def __init__(self):
        """初始化场景管理器"""
        if SceneManager._instance is not None:
            raise RuntimeError("SceneManager is a singleton, use get_instance() instead")
        
        self.logger = logging.getLogger("Status.SceneManager")
        self.scenes = {}  # 场景字典
        self.current_scene = None  # 当前场景
        self.next_scene = None  # 下一个场景
        self.transition = None  # 当前转场效果
        self.transition_manager = TransitionManager.get_instance()
        self.scene_params = {}  # 场景参数
        
        # 注册事件系统
        self.event_system = EventSystem.get_instance()
    
    def register_scene(self, scene: SceneBase) -> None:
        """注册场景
        
        Args:
            scene: 要注册的场景
        """
        if scene.scene_id in self.scenes:
            self.logger.warning(f"场景已存在，将被覆盖: {scene.scene_id}")
            
        self.scenes[scene.scene_id] = scene
        self.logger.info(f"注册场景: {scene.scene_id} - {scene.name}")
    
    def unregister_scene(self, scene_id: str) -> bool:
        """注销场景
        
        Args:
            scene_id: 场景ID
            
        Returns:
            bool: 是否成功注销
        """
        if scene_id not in self.scenes:
            self.logger.warning(f"场景不存在，无法注销: {scene_id}")
            return False
            
        # 不能注销当前场景或下一个场景
        if (self.current_scene and self.current_scene.scene_id == scene_id) or \
           (self.next_scene and self.next_scene.scene_id == scene_id):
            self.logger.error(f"无法注销当前活动场景: {scene_id}")
            return False
            
        # 获取场景并清理资源
        scene = self.scenes[scene_id]
        if scene.is_initialized():
            scene.cleanup()
            
        # 从字典中移除
        del self.scenes[scene_id]
        self.logger.info(f"注销场景: {scene_id}")
        
        return True
    
    def get_scene(self, scene_id: str) -> Optional[SceneBase]:
        """获取场景
        
        Args:
            scene_id: 场景ID
            
        Returns:
            Optional[SceneBase]: 场景对象，如果不存在则返回None
        """
        return self.scenes.get(scene_id)
    
    def get_scenes(self) -> List[SceneBase]:
        """获取所有场景
        
        Returns:
            List[SceneBase]: 场景列表
        """
        return list(self.scenes.values())
    
    def get_current_scene(self) -> Optional[SceneBase]:
        """获取当前场景
        
        Returns:
            Optional[SceneBase]: 当前场景，如果没有则返回None
        """
        return self.current_scene
    
    def switch_to(self, scene_id: str, transition: Optional[str] = None, 
                 transition_params: Dict[str, Any] = None, 
                 scene_params: Dict[str, Any] = None) -> bool:
        """切换到指定场景
        
        Args:
            scene_id: 目标场景ID
            transition: 转场效果名称
            transition_params: 转场效果参数
            scene_params: 传递给目标场景的参数
            
        Returns:
            bool: 切换是否成功
        """
        # 检查场景是否存在
        if scene_id not in self.scenes:
            self.logger.error(f"场景不存在: {scene_id}")
            return False
        
        # 如果是当前场景，不做切换
        if self.current_scene and self.current_scene.scene_id == scene_id:
            self.logger.info(f"已经是当前场景: {scene_id}")
            return True
        
        # 获取目标场景
        target_scene = self.scenes[scene_id]
        
        # 初始化目标场景（如果尚未初始化）
        if not target_scene.is_initialized():
            self.logger.info(f"初始化场景: {scene_id}")
            if not target_scene.initialize():
                self.logger.error(f"初始化场景失败: {scene_id}")
                return False
        
        # 如果当前已经有正在进行的转场，直接完成它
        if self.transition and self.transition.state != TransitionState.COMPLETED:
            self.logger.info("完成当前转场效果")
            self._complete_transition()
        
        # 创建新的转场效果
        transition_params = transition_params or {}
        if transition:
            self.logger.info(f"使用转场效果: {transition}")
            self.transition = self.transition_manager.get_transition(transition, **transition_params)
        else:
            self.logger.info("使用默认转场效果")
            self.transition = self.transition_manager.get_transition(**transition_params)
        
        # 设置下一个场景
        self.next_scene = target_scene
        
        # 开始转场动画
        self.transition.start_transition(True)  # 进入动画
        
        # 如果没有当前场景，直接完成转场
        if not self.current_scene:
            self._complete_transition()
            
        # 初始化场景参数
        self.scene_params = scene_params or {}
            
        return True
    
    def _complete_transition(self) -> None:
        """完成当前转场"""
        # 释放当前场景
        if self.current_scene:
            self.logger.info(f"停用当前场景: {self.current_scene.scene_id}")
            self.current_scene.deactivate()
            
            # 发送场景切换事件
            self.event_system.dispatch_event(EventType.SCENE_CHANGE, {
                "old_scene_id": self.current_scene.scene_id,
                "new_scene_id": self.next_scene.scene_id if self.next_scene else None
            })
        
        # 激活下一个场景
        if self.next_scene:
            self.logger.info(f"激活场景: {self.next_scene.scene_id}")
            if self.next_scene.activate(**self.scene_params):
                self.current_scene = self.next_scene
                self.next_scene = None
            else:
                self.logger.error(f"激活场景失败: {self.next_scene.scene_id}")
                # 如果激活失败，回退到之前的场景
                if self.current_scene:
                    self.logger.info(f"恢复之前的场景: {self.current_scene.scene_id}")
                    self.current_scene.activate()
        
        # 重置转场
        self.transition = None
    
    def update(self, delta_time: float, system_data: Dict[str, Any] = None) -> None:
        """更新场景管理器
        
        Args:
            delta_time: 时间增量
            system_data: 系统数据
        """
        # 更新转场动画
        if self.transition and self.transition.state != TransitionState.COMPLETED:
            if self.transition.update(delta_time):
                self._complete_transition()
        
        # 更新当前场景
        if self.current_scene and self.current_scene.is_active():
            self.current_scene.update(delta_time, system_data or {})
    
    def render(self, renderer: RendererBase) -> None:
        """渲染当前场景和转场效果
        
        Args:
            renderer: 渲染器
        """
        # 如果有转场动画且未完成，渲染转场
        if self.transition and self.transition.state != TransitionState.COMPLETED:
            self.transition.render(renderer, self.current_scene, self.next_scene)
        # 否则直接渲染当前场景
        elif self.current_scene and self.current_scene.is_active():
            self.current_scene.render(renderer)
    
    def handle_input(self, event_type: str, event_data: Any) -> bool:
        """处理输入事件
        
        Args:
            event_type: 事件类型
            event_data: 事件数据
            
        Returns:
            bool: 事件是否被处理
        """
        # 如果有转场动画且未完成，不处理输入
        if self.transition and self.transition.state != TransitionState.COMPLETED:
            return False
        
        # 否则将事件传递给当前场景
        if self.current_scene and self.current_scene.is_active():
            return self.current_scene.handle_input(event_type, event_data)
        
        return False
    
    def cleanup(self) -> None:
        """清理场景管理器资源"""
        # 停用当前场景
        if self.current_scene:
            self.current_scene.deactivate()
            
        # 清理所有场景资源
        for scene_id, scene in self.scenes.items():
            if scene.is_initialized():
                self.logger.info(f"清理场景资源: {scene_id}")
                scene.cleanup()
                
        # 清空场景字典
        self.scenes.clear()
        self.current_scene = None
        self.next_scene = None
        self.transition = None 