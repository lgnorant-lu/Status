"""
---------------------------------------------------------------
File name:                  launcher_types.py
Author:                     Ignorant-lu
Date created:               2025/04/05
Description:                快捷启动器数据类型定义
----------------------------------------------------------------

Changed history:            
                            2025/04/05: 初始创建;
                            2023/11/29: 增强启动参数支持，添加环境变量和启动模式支持;
----
"""

import logging
import uuid
from datetime import datetime
from enum import Enum, auto
from typing import Dict, List, Optional, Union, Any


class LaunchStatus(Enum):
    """启动状态枚举"""
    SUCCESS = auto()  # 启动成功
    NOT_FOUND = auto()  # 应用不存在
    PERMISSION_ERROR = auto()  # 权限错误
    EXECUTION_ERROR = auto()  # 执行错误
    UNKNOWN_ERROR = auto()  # 未知错误


class LaunchMode(Enum):
    """应用启动模式枚举"""
    NORMAL = auto()  # 正常模式启动
    MINIMIZED = auto()  # 最小化启动
    MAXIMIZED = auto()  # 最大化启动
    HIDDEN = auto()  # 隐藏窗口启动
    ADMIN = auto()  # 管理员权限启动


class LaunchResult:
    """应用启动结果"""
    
    def __init__(self, 
                 status: LaunchStatus, 
                 message: str = "", 
                 error: Optional[Exception] = None):
        """初始化启动结果
        
        Args:
            status: 启动状态
            message: 状态消息
            error: 错误对象(如果有)
        """
        self.status = status
        self.message = message
        self.error = error
        self.timestamp = datetime.now()
    
    @property
    def success(self) -> bool:
        """启动是否成功
        
        Returns:
            bool: 启动成功返回True，否则返回False
        """
        return self.status == LaunchStatus.SUCCESS
    
    def __str__(self) -> str:
        if self.success:
            return f"启动成功: {self.message}"
        return f"启动失败 ({self.status.name}): {self.message}"


class LaunchedApplication:
    """可启动的应用程序"""
    
    def __init__(self, 
                 name: str, 
                 path: str, 
                 icon_path: Optional[str] = None, 
                 arguments: Optional[List[str]] = None, 
                 description: Optional[str] = None, 
                 tags: Optional[List[str]] = None,
                 working_directory: Optional[str] = None,
                 environment_variables: Optional[Dict[str, str]] = None,
                 launch_mode: LaunchMode = LaunchMode.NORMAL):
        """初始化应用程序
        
        Args:
            name: 应用名称
            path: 应用路径
            icon_path: 图标路径
            arguments: 启动参数
            description: 描述
            tags: 标签
            working_directory: 工作目录
            environment_variables: 环境变量
            launch_mode: 启动模式
        """
        self.id = str(uuid.uuid4())  # 自动生成唯一ID
        self.name = name
        self.path = path
        self.icon_path = icon_path
        self.arguments = arguments or []
        self.description = description
        self.tags = tags or []
        self.working_directory = working_directory
        self.environment_variables = environment_variables or {}
        self.launch_mode = launch_mode
        
        # 使用统计
        self.last_used = None  # 最近使用时间
        self.use_count = 0  # 使用次数
        self.favorite = False  # 是否为收藏
        
        # 日志记录器
        self.logger = logging.getLogger(__name__)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典
        
        Returns:
            Dict: 属性字典
        """
        return {
            "id": self.id,
            "name": self.name,
            "path": self.path,
            "icon_path": self.icon_path,
            "arguments": self.arguments,
            "description": self.description,
            "tags": self.tags,
            "working_directory": self.working_directory,
            "environment_variables": self.environment_variables,
            "launch_mode": self.launch_mode.name if self.launch_mode else LaunchMode.NORMAL.name,
            "last_used": self.last_used.isoformat() if self.last_used else None,
            "use_count": self.use_count,
            "favorite": self.favorite
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'LaunchedApplication':
        """从字典创建应用程序对象
        
        Args:
            data: 属性字典
            
        Returns:
            LaunchedApplication: 应用程序对象
        """
        # 处理启动模式
        launch_mode_str = data.get("launch_mode", LaunchMode.NORMAL.name)
        try:
            launch_mode = LaunchMode[launch_mode_str]
        except (KeyError, TypeError):
            launch_mode = LaunchMode.NORMAL
        
        app = cls(
            name=data.get("name", ""),
            path=data.get("path", ""),
            icon_path=data.get("icon_path"),
            arguments=data.get("arguments", []),
            description=data.get("description"),
            tags=data.get("tags", []),
            working_directory=data.get("working_directory"),
            environment_variables=data.get("environment_variables", {}),
            launch_mode=launch_mode
        )
        
        # 设置ID和统计信息
        app.id = data.get("id", app.id)
        app.use_count = data.get("use_count", 0)
        app.favorite = data.get("favorite", False)
        
        # 处理日期时间
        last_used = data.get("last_used")
        if last_used:
            try:
                app.last_used = datetime.fromisoformat(last_used)
            except (ValueError, TypeError):
                app.last_used = None
        
        return app
    
    def increase_usage_count(self) -> None:
        """增加使用次数并更新最近使用时间"""
        self.use_count += 1
        self.last_used = datetime.now()
        
    def toggle_favorite(self) -> bool:
        """切换收藏状态
        
        Returns:
            bool: 切换后的收藏状态
        """
        self.favorite = not self.favorite
        return self.favorite
    
    def get_command_args(self) -> List[str]:
        """获取启动命令行参数
        
        Returns:
            List[str]: 命令行参数列表
        """
        command = [self.path]
        
        # 添加参数
        if self.arguments:
            command.extend(self.arguments)
            
        return command
    
    def get_launch_flags(self) -> Dict[str, Any]:
        """获取启动标志
        
        根据启动模式返回适当的启动标志
        
        Returns:
            Dict[str, Any]: 启动标志字典
        """
        flags = {}
        
        if self.launch_mode == LaunchMode.MINIMIZED:
            flags["creationflags"] = 0x08000000  # SW_SHOWMINIMIZED
        elif self.launch_mode == LaunchMode.MAXIMIZED:
            flags["creationflags"] = 0x01000000  # SW_MAXIMIZE
        elif self.launch_mode == LaunchMode.HIDDEN:
            flags["creationflags"] = 0x08000000  # SW_HIDE
        elif self.launch_mode == LaunchMode.ADMIN:
            # 使用runas命令
            flags["need_admin"] = True
            
        return flags
    
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, LaunchedApplication):
            return False
        return self.id == other.id
    
    def __hash__(self) -> int:
        return hash(self.id)


class LauncherGroup:
    """应用程序分组"""
    
    def __init__(self, 
                 name: str, 
                 icon: Optional[str] = None, 
                 description: Optional[str] = None):
        """初始化分组
        
        Args:
            name: 组名
            icon: 组图标
            description: 描述
        """
        self.id = str(uuid.uuid4())  # 自动生成唯一ID
        self.name = name
        self.icon = icon
        self.description = description
        self.applications: List[str] = []  # 应用ID列表
    
    def add_application(self, app_id: str) -> bool:
        """添加应用到分组
        
        Args:
            app_id: 应用ID
            
        Returns:
            bool: 是否成功添加
        """
        if app_id not in self.applications:
            self.applications.append(app_id)
            return True
        return False
    
    def remove_application(self, app_id: str) -> bool:
        """从分组中移除应用
        
        Args:
            app_id: 应用ID
            
        Returns:
            bool: 是否成功移除
        """
        if app_id in self.applications:
            self.applications.remove(app_id)
            return True
        return False
    
    def contains_application(self, app_id: str) -> bool:
        """检查分组是否包含应用
        
        Args:
            app_id: 应用ID
            
        Returns:
            bool: 是否包含应用
        """
        return app_id in self.applications
    
    def has_application(self, app_id: str) -> bool:
        """检查分组是否包含应用（contains_application的别名）
        
        Args:
            app_id: 应用ID
            
        Returns:
            bool: 是否包含应用
        """
        return self.contains_application(app_id)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典
        
        Returns:
            Dict: 属性字典
        """
        return {
            "id": self.id,
            "name": self.name,
            "icon": self.icon,
            "description": self.description,
            "applications": self.applications
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'LauncherGroup':
        """从字典创建分组对象
        
        Args:
            data: 属性字典
            
        Returns:
            LauncherGroup: 分组对象
        """
        group = cls(
            name=data.get("name", ""),
            icon=data.get("icon"),
            description=data.get("description")
        )
        
        # 设置ID和应用列表
        group.id = data.get("id", group.id)
        group.applications = data.get("applications", [])
        
        return group
    
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, LauncherGroup):
            return False
        return self.id == other.id
    
    def __hash__(self) -> int:
        return hash(self.id) 