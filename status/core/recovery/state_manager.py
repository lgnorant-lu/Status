"""
---------------------------------------------------------------
File name:                  state_manager.py
Author:                     Ignorant-lu
Date created:               2025/05/14
Description:                状态持久化管理器实现
----------------------------------------------------------------

Changed history:            
                            2025/05/14: 初始创建;
----
"""

import os
import json
import hashlib
import threading
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Callable, Tuple, TypedDict, Union

# 获取日志器
from status.core.logging import get_logger

class StateData:
    """应用状态数据类
    
    用于封装应用状态数据，包括版本、时间戳、模块数据和校验和。
    """
    
    def __init__(self, version: str = "1.0", modules: Optional[Dict[str, Dict[str, Any]]] = None):
        """初始化状态数据
        
        Args:
            version: 状态数据版本
            modules: 各模块状态数据
        """
        self.version = version
        self.timestamp = datetime.now().isoformat()
        self.modules = modules or {}
        self.checksum = ""
    
    def calculate_checksum(self) -> str:
        """计算状态数据的校验和
        
        Returns:
            校验和字符串
        """
        # 将数据转换为JSON字符串
        data_str = json.dumps({
            "version": self.version,
            "timestamp": self.timestamp,
            "modules": self.modules
        }, sort_keys=True)
        
        # 计算MD5校验和
        return hashlib.md5(data_str.encode('utf-8')).hexdigest()
    
    def update_checksum(self):
        """更新校验和"""
        self.checksum = self.calculate_checksum()
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典
        
        Returns:
            状态数据字典
        """
        # 确保校验和是最新的
        self.update_checksum()
        
        return {
            "version": self.version,
            "timestamp": self.timestamp,
            "modules": self.modules,
            "checksum": self.checksum
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'StateData':
        """从字典创建状态数据
        
        Args:
            data: 状态数据字典
        
        Returns:
            状态数据对象
        """
        state_data = cls(
            version=data.get("version", "1.0"),
            modules=data.get("modules", {})
        )
        state_data.timestamp = data.get("timestamp", datetime.now().isoformat())
        state_data.checksum = data.get("checksum", "")
        
        return state_data


class StateManager:
    """状态管理器类
    
    负责应用状态的保存、加载和管理。使用单例模式确保全局只有一个实例。
    """
    
    # 单例实例
    _instance = None
    _lock = threading.Lock()
    _initialized: bool = False
    
    def __new__(cls, *args, **kwargs):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(StateManager, cls).__new__(cls)
                cls._instance._initialized = False
            return cls._instance
    
    def __init__(self, state_dir: Optional[str] = None):
        """初始化状态管理器
        
        Args:
            state_dir: 状态文件目录
        """
        # 防止重复初始化
        if self._initialized:
            return
            
        self._initialized = True
        
        # 设置日志
        self.logger = get_logger("status.core.recovery.state_manager")
        
        # 状态文件目录
        self._state_dir = state_dir or os.path.join("data", "states")
        
        # 确保状态目录存在
        self._ensure_state_directory()
        
        # 模块回调字典 {module_name: (save_callback, load_callback)}
        self._module_callbacks: Dict[str, Tuple[Callable, Callable]] = {}
        
        # 当前加载的状态数据
        self._current_state: Optional[StateData] = None
        
        # 上次保存时间
        self._last_save_time = datetime.now()
        
        # 自动保存间隔（秒）
        self._auto_save_interval = 300  # 5分钟
        
        # 是否启用自动保存
        self._auto_save_enabled = True
        
        # 状态文件名模板
        self._state_filename_template = "state_{timestamp}.json"
        
        self.logger.info("状态管理器初始化完成")
    
    def _ensure_state_directory(self):
        """确保状态目录存在"""
        if not os.path.exists(self._state_dir):
            os.makedirs(self._state_dir, exist_ok=True)
            self.logger.debug(f"创建状态目录: {self._state_dir}")
    
    def register_module(self, module_name: str, save_callback: Callable[[], Dict[str, Any]], load_callback: Callable[[Dict[str, Any]], None]) -> bool:
        """注册模块状态处理回调
        
        Args:
            module_name: 模块名称
            save_callback: 保存状态回调函数，返回模块状态数据
            load_callback: 加载状态回调函数，接收模块状态数据
        
        Returns:
            是否注册成功
        """
        if not callable(save_callback) or not callable(load_callback):
            self.logger.error(f"注册模块 {module_name} 失败: 回调必须是可调用对象")
            return False
        
        self._module_callbacks[module_name] = (save_callback, load_callback)
        self.logger.debug(f"注册模块 {module_name} 成功")
        return True
    
    def unregister_module(self, module_name: str) -> bool:
        """取消注册模块
        
        Args:
            module_name: 模块名称
        
        Returns:
            是否取消成功
        """
        if module_name in self._module_callbacks:
            del self._module_callbacks[module_name]
            self.logger.debug(f"取消注册模块 {module_name}")
            return True
        return False
    
    def save_state(self, module_name: Optional[str] = None, force: bool = False) -> bool:
        """保存应用状态
        
        Args:
            module_name: 指定模块名称，如果为None则保存所有已注册模块
            force: 是否强制保存（即使没有变化）
        
        Returns:
            是否保存成功
        """
        try:
            # 检查是否需要保存
            now = datetime.now()
            if not force and (now - self._last_save_time).total_seconds() < self._auto_save_interval:
                self.logger.debug("跳过状态保存: 未达到自动保存间隔")
                return True
            
            # 创建新的状态数据或使用当前状态
            state_data = self._current_state or StateData()
            
            # 收集模块状态
            if module_name:
                # 只保存指定模块
                if module_name in self._module_callbacks:
                    save_callback, _ = self._module_callbacks[module_name]
                    try:
                        module_state = save_callback()
                        state_data.modules[module_name] = module_state
                        self.logger.debug(f"保存模块 {module_name} 状态")
                    except Exception as e:
                        self.logger.error(f"保存模块 {module_name} 状态失败: {e}")
                        return False
                else:
                    self.logger.warning(f"模块 {module_name} 未注册")
                    return False
            else:
                # 保存所有模块
                for module_name, (save_callback, _) in self._module_callbacks.items():
                    try:
                        module_state = save_callback()
                        state_data.modules[module_name] = module_state
                        self.logger.debug(f"保存模块 {module_name} 状态")
                    except Exception as e:
                        self.logger.error(f"保存模块 {module_name} 状态失败: {e}")
                        # 继续保存其他模块
            
            # 更新校验和
            state_data.update_checksum()
            
            # 保存状态文件
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = self._state_filename_template.format(timestamp=timestamp)
            filepath = os.path.join(self._state_dir, filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(state_data.to_dict(), f, indent=4, ensure_ascii=False)
            
            self._last_save_time = now
            self._current_state = state_data
            
            self.logger.info(f"状态保存成功: {filepath}")
            
            # 清理旧状态文件
            self._cleanup_old_states()
            
            return True
            
        except Exception as e:
            self.logger.error(f"保存状态失败: {e}")
            return False
    
    def load_state(self, version: Optional[str] = None) -> Optional[StateData]:
        """加载应用状态
        
        Args:
            version: 指定版本，如果为None则加载最新版本
        
        Returns:
            加载的状态数据，如果失败则返回None
        """
        try:
            # 获取状态文件列表
            state_files = self.get_available_versions()
            
            if not state_files:
                self.logger.warning("没有可用的状态文件")
                return None
            
            # 选择状态文件
            if version:
                # 查找指定版本
                state_file = None
                for file_info in state_files:
                    if file_info['version'] == version:
                        state_file = file_info['filepath']
                        break
                
                if not state_file:
                    self.logger.warning(f"未找到版本 {version} 的状态文件")
                    return None
            else:
                # 使用最新版本
                state_file = state_files[0]['filepath']
            
            # 读取状态文件
            with open(state_file, 'r', encoding='utf-8') as f:
                state_dict = json.load(f)
            
            # 创建状态数据对象
            state_data = StateData.from_dict(state_dict)
            
            # 验证完整性
            if not self.verify_state_integrity(state_data):
                self.logger.error(f"状态文件 {state_file} 完整性验证失败")
                return None
            
            # 应用状态到各模块
            for module_name, module_state in state_data.modules.items():
                if module_name in self._module_callbacks:
                    _, load_callback = self._module_callbacks[module_name]
                    try:
                        load_callback(module_state)
                        self.logger.debug(f"加载模块 {module_name} 状态")
                    except Exception as e:
                        self.logger.error(f"加载模块 {module_name} 状态失败: {e}")
                        # 继续加载其他模块
                else:
                    self.logger.warning(f"模块 {module_name} 未注册，跳过状态加载")
            
            self._current_state = state_data
            self.logger.info(f"状态加载成功: {state_file}")
            
            return state_data
            
        except Exception as e:
            self.logger.error(f"加载状态失败: {e}")
            return None
    
    def get_available_versions(self) -> List[Dict[str, str]]:
        """获取可用的状态版本列表
        
        Returns:
            版本信息列表，按时间戳降序排序
        """
        try:
            # 获取状态目录中的所有JSON文件
            state_files = []
            
            if not os.path.exists(self._state_dir):
                return []
            
            for filename in os.listdir(self._state_dir):
                if filename.endswith('.json') and filename.startswith('state_'):
                    filepath = os.path.join(self._state_dir, filename)
                    
                    try:
                        # 读取文件获取时间戳
                        with open(filepath, 'r', encoding='utf-8') as f:
                            state_dict = json.load(f)
                            
                        timestamp = state_dict.get('timestamp', '')
                        version = state_dict.get('version', '')
                        
                        if timestamp:
                            # 转换为日期对象以便排序
                            timestamp_dt = datetime.fromisoformat(timestamp)
                            
                            state_files.append({
                                'filepath': filepath,
                                'filename': filename,
                                'timestamp': timestamp,
                                'timestamp_dt': timestamp_dt,
                                'version': version
                            })
                    except Exception as e:
                        self.logger.warning(f"读取状态文件 {filepath} 失败: {e}")
            
            # 按时间戳降序排序
            state_files.sort(key=lambda x: x['timestamp_dt'], reverse=True)
            
            # 移除临时排序键
            for file_info in state_files:
                file_info.pop('timestamp_dt')
            
            return state_files
            
        except Exception as e:
            self.logger.error(f"获取可用版本列表失败: {e}")
            return []
    
    def verify_state_integrity(self, state_data: StateData) -> bool:
        """验证状态数据完整性
        
        Args:
            state_data: 状态数据对象
        
        Returns:
            是否完整有效
        """
        if not state_data:
            return False
        
        # 保存原始校验和
        original_checksum = state_data.checksum
        
        # 重新计算校验和
        calculated_checksum = state_data.calculate_checksum()
        
        # 比较校验和
        return original_checksum == calculated_checksum
    
    def _cleanup_old_states(self, max_files: int = 10):
        """清理旧的状态文件
        
        Args:
            max_files: 保留的最大文件数
        """
        try:
            state_files = self.get_available_versions()
            
            # 如果文件数超过最大值，删除最旧的文件
            if len(state_files) > max_files:
                for file_info in state_files[max_files:]:
                    filepath = file_info['filepath']
                    try:
                        os.remove(filepath)
                        self.logger.debug(f"删除旧状态文件: {filepath}")
                    except Exception as e:
                        self.logger.warning(f"删除旧状态文件 {filepath} 失败: {e}")
        
        except Exception as e:
            self.logger.error(f"清理旧状态文件失败: {e}")
    
    def set_auto_save_interval(self, interval_seconds: int):
        """设置自动保存间隔
        
        Args:
            interval_seconds: 间隔秒数
        """
        if interval_seconds > 0:
            self._auto_save_interval = interval_seconds
            self.logger.debug(f"设置自动保存间隔: {interval_seconds}秒")
    
    def enable_auto_save(self, enable: bool = True):
        """启用或禁用自动保存
        
        Args:
            enable: 是否启用
        """
        self._auto_save_enabled = enable
        self.logger.debug(f"{'启用' if enable else '禁用'}自动保存")
    
    def is_auto_save_enabled(self) -> bool:
        """检查是否启用自动保存
        
        Returns:
            是否启用
        """
        return self._auto_save_enabled 