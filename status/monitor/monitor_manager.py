"""
---------------------------------------------------------------
File name:                  monitor_manager.py
Author:                     Ignorant-lu
Date created:               2025/04/04
Description:                监控管理器，整合系统监控的各个组件
----------------------------------------------------------------

Changed history:            
                            2025/04/04: 初始创建;
----
"""

import logging
import threading
import time
from typing import Dict, Any, List, Optional, Callable, Union

from .data_collector import SystemDataCollector
from .data_processor import DataProcessor
from .visualization import VisualMapper
from .scene_manager import SceneManager


class MonitorManager:
    """监控管理器，整合数据采集器、处理器、可视化映射器和场景管理器"""
    
    def __init__(
        self, 
        data_collector: Optional[SystemDataCollector] = None,
        data_processor: Optional[DataProcessor] = None,
        visual_mapper: Optional[VisualMapper] = None,
        scene_manager: Optional[SceneManager] = None,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        初始化监控管理器
        
        Args:
            data_collector: 数据采集器
            data_processor: 数据处理器
            visual_mapper: 可视化映射器
            scene_manager: 场景管理器
            config: 配置字典
        """
        self.config = config or {}
        self.logger = logging.getLogger("MonitorManager")
        
        # 设置组件
        self.data_collector = data_collector or SystemDataCollector()
        self.data_processor = data_processor or DataProcessor()
        self.visual_mapper = visual_mapper or VisualMapper()
        self.scene_manager = scene_manager or SceneManager()
        
        # 线程控制
        self.running = False
        self.update_thread = None
        self.lock = threading.RLock()
        
        # 数据缓存
        self.raw_data = {}
        self.processed_data = {}
        self.visual_params = {}
        self.last_update = 0
        
        # 更新间隔
        self.update_interval = self.config.get("update_interval", 1.0)
        
        # 回调函数
        self.update_callbacks = []
        
        self.logger.info("监控管理器初始化完成")
        
    def start(self) -> bool:
        """
        启动监控
        
        Returns:
            bool: 是否成功启动
        """
        with self.lock:
            if self.running:
                self.logger.warning("监控已经在运行中")
                return False
                
            self.running = True
            self.update_thread = threading.Thread(target=self._update_loop, daemon=True)
            self.update_thread.start()
            
            self.logger.info("监控已启动")
            return True
            
    def stop(self) -> bool:
        """
        停止监控
        
        Returns:
            bool: 是否成功停止
        """
        with self.lock:
            if not self.running:
                self.logger.warning("监控未运行")
                return False
                
            self.running = False
            if self.update_thread:
                self.update_thread.join(timeout=3.0)
                self.update_thread = None
                
            self.logger.info("监控已停止")
            return True
            
    def is_running(self) -> bool:
        """
        检查监控是否正在运行
        
        Returns:
            bool: 是否正在运行
        """
        with self.lock:
            return self.running
            
    def _update_loop(self) -> None:
        """更新循环，在单独的线程中运行"""
        self.logger.info("更新循环开始")
        
        while self.running:
            try:
                # 获取当前活动场景的采集配置
                collection_config = self.scene_manager.get_scene_collection_config()
                
                # 采集数据
                raw_data = self.data_collector.collect_data(collection_config.get("metrics", []))
                
                # 获取当前活动场景的处理配置
                processing_config = self.scene_manager.get_scene_processing_config()
                
                # 处理数据
                self.data_processor.update_config(processing_config)
                processed_data = self.data_processor.process_data(raw_data)
                
                # 获取当前活动场景的视觉配置
                visual_config = self.scene_manager.get_scene_visual_config()
                
                # 映射为视觉参数
                self.visual_mapper.update_config(visual_config)
                visual_params = self.visual_mapper.map_data(processed_data)
                
                # 更新缓存
                with self.lock:
                    self.raw_data = raw_data
                    self.processed_data = processed_data
                    self.visual_params = visual_params
                    self.last_update = time.time()
                    
                # 缓存当前场景数据
                active_scene_id = self.scene_manager.get_active_scene_id()
                if active_scene_id:
                    self.scene_manager.cache_scene_data(active_scene_id, {
                        "raw": raw_data,
                        "processed": processed_data,
                        "visual": visual_params
                    })
                    
                # 调用更新回调
                self._trigger_update_callbacks()
                
                # 根据场景配置调整更新间隔
                self.update_interval = collection_config.get("interval", 1.0)
                
            except Exception as e:
                self.logger.error(f"更新循环发生错误: {e}")
                
            # 等待下一次更新
            time.sleep(self.update_interval)
            
        self.logger.info("更新循环结束")
        
    def force_update(self) -> bool:
        """
        强制立即更新数据
        
        Returns:
            bool: 是否成功更新
        """
        if not self.running:
            self.logger.warning("监控未运行，无法强制更新")
            return False
            
        try:
            # 获取当前活动场景的采集配置
            collection_config = self.scene_manager.get_scene_collection_config()
            
            # 采集数据
            raw_data = self.data_collector.collect_data(collection_config.get("metrics", []))
            
            # 获取当前活动场景的处理配置
            processing_config = self.scene_manager.get_scene_processing_config()
            
            # 处理数据
            self.data_processor.update_config(processing_config)
            processed_data = self.data_processor.process_data(raw_data)
            
            # 获取当前活动场景的视觉配置
            visual_config = self.scene_manager.get_scene_visual_config()
            
            # 映射为视觉参数
            self.visual_mapper.update_config(visual_config)
            visual_params = self.visual_mapper.map_data(processed_data)
            
            # 更新缓存
            with self.lock:
                self.raw_data = raw_data
                self.processed_data = processed_data
                self.visual_params = visual_params
                self.last_update = time.time()
                
            # 缓存当前场景数据
            active_scene_id = self.scene_manager.get_active_scene_id()
            if active_scene_id:
                self.scene_manager.cache_scene_data(active_scene_id, {
                    "raw": raw_data,
                    "processed": processed_data,
                    "visual": visual_params
                })
                
            # 调用更新回调
            self._trigger_update_callbacks()
            
            self.logger.info("强制更新完成")
            return True
            
        except Exception as e:
            self.logger.error(f"强制更新失败: {e}")
            return False
            
    def register_update_callback(self, callback: Callable[[Dict[str, Any]], None]) -> None:
        """
        注册数据更新回调函数
        
        Args:
            callback: 回调函数，接收视觉参数作为参数
        """
        if callback not in self.update_callbacks:
            self.update_callbacks.append(callback)
            self.logger.debug("注册更新回调")
            
    def unregister_update_callback(self, callback: Callable) -> bool:
        """
        注销数据更新回调函数
        
        Args:
            callback: 回调函数
            
        Returns:
            bool: 是否成功注销
        """
        if callback in self.update_callbacks:
            self.update_callbacks.remove(callback)
            self.logger.debug("注销更新回调")
            return True
        return False
        
    def _trigger_update_callbacks(self) -> None:
        """触发所有更新回调"""
        for callback in self.update_callbacks:
            try:
                callback(self.visual_params)
            except Exception as e:
                self.logger.error(f"更新回调执行失败: {e}")
                
    def get_raw_data(self) -> Dict[str, Any]:
        """
        获取最新的原始数据
        
        Returns:
            Dict: 原始数据
        """
        with self.lock:
            return self.raw_data.copy()
            
    def get_processed_data(self) -> Dict[str, Any]:
        """
        获取最新的处理后数据
        
        Returns:
            Dict: 处理后数据
        """
        with self.lock:
            return self.processed_data.copy()
            
    def get_visual_params(self) -> Dict[str, Any]:
        """
        获取最新的视觉参数
        
        Returns:
            Dict: 视觉参数
        """
        with self.lock:
            return self.visual_params.copy()
            
    def switch_scene(self, scene_id: str) -> bool:
        """
        切换到指定场景
        
        Args:
            scene_id: 场景ID
            
        Returns:
            bool: 是否成功切换
        """
        if not self.scene_manager.set_active_scene(scene_id):
            return False
            
        # 强制更新数据
        if self.running:
            self.force_update()
            
        return True
        
    def get_current_scene(self) -> Dict[str, Any]:
        """
        获取当前场景信息
        
        Returns:
            Dict: 场景信息
        """
        active_scene = self.scene_manager.get_active_scene()
        if active_scene:
            return {
                "id": self.scene_manager.get_active_scene_id(),
                "metadata": active_scene.get_metadata(),
                "collection": active_scene.get_collection_config(),
                "processing": active_scene.get_processing_config(),
                "visual": active_scene.get_visual_config()
            }
        return {"error": "No active scene"}
        
    def get_all_scenes(self) -> List[Dict[str, Any]]:
        """
        获取所有场景信息
        
        Returns:
            List[Dict]: 场景信息列表
        """
        return self.scene_manager.list_scenes()
        
    def create_scene(self, scene_id: str, config: Dict[str, Any]) -> bool:
        """
        创建新场景
        
        Args:
            scene_id: 场景ID
            config: 场景配置
            
        Returns:
            bool: 是否成功创建
        """
        try:
            self.scene_manager.create_scene(scene_id, config)
            self.logger.info(f"创建场景: {scene_id}")
            return True
        except Exception as e:
            self.logger.error(f"创建场景失败: {e}")
            return False
            
    def delete_scene(self, scene_id: str) -> bool:
        """
        删除场景
        
        Args:
            scene_id: 场景ID
            
        Returns:
            bool: 是否成功删除
        """
        return self.scene_manager.delete_scene(scene_id)
        
    def update_scene_config(self, scene_id: str, config: Dict[str, Any]) -> bool:
        """
        更新场景配置
        
        Args:
            scene_id: 场景ID
            config: 新配置
            
        Returns:
            bool: 是否成功更新
        """
        success = self.scene_manager.update_scene_config(scene_id, config)
        
        # 如果更新的是当前场景，强制更新数据
        if success and scene_id == self.scene_manager.get_active_scene_id() and self.running:
            self.force_update()
            
        return success
        
    def update_config(self, config: Dict[str, Any]) -> None:
        """
        更新监控管理器配置
        
        Args:
            config: 新配置
        """
        self.config.update(config)
        
        # 更新更新间隔
        if "update_interval" in config:
            self.update_interval = config["update_interval"]
            
        self.logger.debug(f"更新监控管理器配置: {list(config.keys())}")
        
    def check_system_alerts(self) -> List[Dict[str, Any]]:
        """
        获取系统告警信息
        
        Returns:
            List[Dict]: 告警信息列表
        """
        with self.lock:
            if not self.visual_params or 'alerts' not in self.visual_params:
                return []
                
            return self.visual_params['alerts']
            
    def get_system_summary(self) -> Dict[str, Any]:
        """
        获取系统状态摘要
        
        Returns:
            Dict: 状态摘要
        """
        with self.lock:
            if not self.visual_params or 'summary' not in self.visual_params:
                return {"status": "unknown", "load": 0, "label": "未知"}
                
            return self.visual_params['summary']
            
    def get_last_update_time(self) -> float:
        """
        获取最后更新时间
        
        Returns:
            float: 时间戳
        """
        with self.lock:
            return self.last_update 