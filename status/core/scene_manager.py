"""
---------------------------------------------------------------
File name:                  scene_manager.py
Author:                     Ignorant-lu
Date created:               2023/04/03
Description:                场景管理器，负责场景的创建、切换和管理
----------------------------------------------------------------

Changed history:            
                            2023/04/03: 初始创建;
----
"""

import logging
from typing import Dict, Optional, Type, List, Any

# 将在实际实现时导入
# from status.scenes.scene_base import SceneBase

class SceneManager:
    """场景管理器，负责场景的创建、切换和管理"""
    
    def __init__(self):
        """初始化场景管理器"""
        self.logger = logging.getLogger("Hollow-ming.Core.SceneManager")
        self.scenes = {}  # 场景实例字典
        self.scene_classes = {}  # 场景类字典
        self.current_scene = None  # 当前活动场景
        self.previous_scene = None  # 前一个场景
        
    def register_scene(self, scene_id: str, scene_class: Type) -> None:
        """注册场景类
        
        Args:
            scene_id: 场景ID
            scene_class: 场景类
        """
        self.scene_classes[scene_id] = scene_class
        self.logger.debug(f"场景类已注册: {scene_id}")
    
    def create_scene(self, scene_id: str, **kwargs) -> bool:
        """创建场景实例
        
        Args:
            scene_id: 场景ID
            **kwargs: 传递给场景构造函数的参数
            
        Returns:
            bool: 创建是否成功
        """
        if scene_id not in self.scene_classes:
            self.logger.error(f"场景ID未注册: {scene_id}")
            return False
        
        if scene_id in self.scenes:
            self.logger.debug(f"场景已存在，跳过创建: {scene_id}")
            return True
        
        try:
            scene_class = self.scene_classes[scene_id]
            self.scenes[scene_id] = scene_class(**kwargs)
            self.logger.info(f"场景创建成功: {scene_id}")
            return True
        except Exception as e:
            self.logger.error(f"场景创建失败: {scene_id}, 错误: {str(e)}", exc_info=True)
            return False
    
    def switch_to(self, scene_id: str, **kwargs) -> bool:
        """切换到指定场景
        
        Args:
            scene_id: 场景ID
            **kwargs: 传递给场景的参数
            
        Returns:
            bool: 切换是否成功
        """
        if scene_id not in self.scene_classes:
            self.logger.error(f"场景ID未注册: {scene_id}")
            return False
        
        if scene_id not in self.scenes and not self.create_scene(scene_id, **kwargs):
            self.logger.error(f"无法切换到场景: {scene_id}, 创建失败")
            return False
        
        scene = self.scenes[scene_id]
        
        # 暂停当前场景
        if self.current_scene:
            self.logger.debug(f"暂停场景: {self.current_scene}")
            # 实际实现时会调用场景的暂停方法
            # self.scenes[self.current_scene].pause()
            self.previous_scene = self.current_scene
        
        # 激活新场景
        self.current_scene = scene_id
        self.logger.info(f"切换到场景: {scene_id}")
        
        # 实际实现时会调用场景的恢复方法
        # scene.resume(**kwargs)
        
        return True
    
    def get_current_scene(self) -> Optional[Any]:
        """获取当前场景实例
        
        Returns:
            当前场景实例或None
        """
        if not self.current_scene:
            return None
        return self.scenes.get(self.current_scene)
    
    def get_scene(self, scene_id: str) -> Optional[Any]:
        """获取指定场景实例
        
        Args:
            scene_id: 场景ID
            
        Returns:
            场景实例或None
        """
        return self.scenes.get(scene_id)
    
    def get_all_scene_ids(self) -> List[str]:
        """获取所有已注册的场景ID
        
        Returns:
            场景ID列表
        """
        return list(self.scene_classes.keys())
    
    def reload_scene(self, scene_id: str, **kwargs) -> bool:
        """重新加载场景
        
        Args:
            scene_id: 场景ID
            **kwargs: 传递给场景的参数
            
        Returns:
            bool: 重新加载是否成功
        """
        if scene_id not in self.scene_classes:
            self.logger.error(f"场景ID未注册: {scene_id}")
            return False
        
        # 如果场景存在，先删除
        if scene_id in self.scenes:
            # 实际实现时会调用场景的清理方法
            # self.scenes[scene_id].cleanup()
            del self.scenes[scene_id]
            self.logger.debug(f"场景已删除: {scene_id}")
        
        # 创建新场景
        if not self.create_scene(scene_id, **kwargs):
            self.logger.error(f"重新加载场景失败: {scene_id}")
            return False
        
        # 如果重新加载的是当前场景，需要重新激活
        if self.current_scene == scene_id:
            # 实际实现时会调用场景的恢复方法
            # self.scenes[scene_id].resume(**kwargs)
            self.logger.debug(f"重新激活场景: {scene_id}")
        
        self.logger.info(f"场景重新加载成功: {scene_id}")
        return True
    
    def preload_scenes(self, scene_ids: List[str]) -> None:
        """预加载场景
        
        Args:
            scene_ids: 要预加载的场景ID列表
        """
        for scene_id in scene_ids:
            if scene_id not in self.scenes:
                self.logger.debug(f"预加载场景: {scene_id}")
                self.create_scene(scene_id)
    
    def cleanup(self) -> None:
        """清理所有场景资源"""
        self.logger.info("清理所有场景")
        
        for scene_id, scene in self.scenes.items():
            try:
                # 实际实现时会调用场景的清理方法
                # scene.cleanup()
                self.logger.debug(f"场景已清理: {scene_id}")
            except Exception as e:
                self.logger.error(f"场景清理失败: {scene_id}, 错误: {str(e)}", exc_info=True)
        
        self.scenes.clear()
        self.current_scene = None
        self.previous_scene = None 