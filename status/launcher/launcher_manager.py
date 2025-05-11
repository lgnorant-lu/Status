"""
---------------------------------------------------------------
File name:                  launcher_manager.py
Author:                     Ignorant-lu
Date created:               2025/04/05
Description:                快捷启动器管理器，负责管理应用程序和启动服务
----------------------------------------------------------------

Changed history:            
                            2025/04/05: 初始创建;
----
"""

import logging
import os
import subprocess
import threading
import json
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any, Set, Union, Callable

from status.launcher.launcher_types import (
    LaunchedApplication, 
    LauncherGroup,
    LaunchResult,
    LaunchStatus,
    LaunchMode
)

# 获取日志记录器
logger = logging.getLogger(__name__)


class LauncherManager:
    """快捷启动器管理器，采用单例模式"""
    
    _instance = None
    _lock = threading.Lock()
    
    @classmethod
    def get_instance(cls) -> 'LauncherManager':
        """获取单例实例
        
        Returns:
            LauncherManager: 启动器管理器实例
        """
        with cls._lock:
            if cls._instance is None:
                logger.debug("创建LauncherManager实例")
                cls._instance = LauncherManager()
            return cls._instance
    
    def __init__(self):
        """初始化启动器管理器"""
        if LauncherManager._instance is not None:
            raise RuntimeError("LauncherManager是单例，请使用get_instance()获取实例")
            
        # 应用程序集合，以ID为键
        self.applications: Dict[str, LaunchedApplication] = {}
        
        # 分组集合，以ID为键
        self.groups: Dict[str, LauncherGroup] = {}
        
        # 配置管理器引用
        self.config_manager = None
        
        # 事件管理器引用
        self.event_manager = None
        
        # 搜索索引
        self._search_index: Dict[str, Set[str]] = {}  # 关键词 -> 应用ID集合
        
        # 初始化标记
        self._initialized = False
        
        # 启动器配置
        self.config = {
            "auto_load_system_apps": True,  # 是否自动加载系统应用
            "max_recent_apps": 10,  # 最近使用的应用数量上限
            "default_app_icon": None,  # 默认应用图标
            "default_group_icon": None,  # 默认分组图标
            "favorite_group_id": None  # 收藏分组ID
        }
        
        logger.debug("LauncherManager已创建")
    
    def initialize(self) -> bool:
        """初始化启动器管理器
        
        Returns:
            bool: 初始化是否成功
        """
        if self._initialized:
            logger.warning("LauncherManager已经初始化")
            return True
        
        try:
            # 获取配置管理器引用
            from status.core.config import ConfigManager
            self.config_manager = ConfigManager.get_instance()
            
            # 获取事件管理器引用
            from status.core.events import EventManager
            self.event_manager = EventManager.get_instance()
            
            # 加载配置
            self._load_configuration()
            
            # 如果没有收藏分组，创建一个
            if not self.config["favorite_group_id"] or self.config["favorite_group_id"] not in self.groups:
                favorite_group = LauncherGroup("收藏", description="收藏的应用程序")
                self.add_group(favorite_group)
                self.config["favorite_group_id"] = favorite_group.id
                
            # 如果设置为自动加载系统应用，则加载系统应用
            if self.config["auto_load_system_apps"]:
                self._load_system_applications()
            
            # 重建搜索索引
            self._rebuild_search_index()
            
            self._initialized = True
            logger.info("LauncherManager初始化成功")
            return True
            
        except Exception as e:
            logger.error(f"LauncherManager初始化失败: {str(e)}")
            return False
    
    def add_application(self, application: LaunchedApplication) -> bool:
        """添加应用程序
        
        Args:
            application: 要添加的应用程序
            
        Returns:
            bool: 添加是否成功
        """
        if application.id in self.applications:
            logger.warning(f"应用程序ID '{application.id}' 已存在")
            return False
        
        # 检查路径是否存在
        if not os.path.exists(application.path):
            logger.warning(f"应用程序路径 '{application.path}' 不存在")
            return False
        
        # 添加应用程序
        self.applications[application.id] = application
        
        # 更新搜索索引
        self._update_search_index_for_app(application)
        
        # 如果应用是收藏的，添加到收藏分组
        if application.favorite and self.config["favorite_group_id"]:
            favorite_group = self.groups.get(self.config["favorite_group_id"])
            if favorite_group:
                favorite_group.add_application(application.id)
        
        logger.info(f"添加应用程序: {application.name} ({application.id})")
        return True
    
    def remove_application(self, app_id: str) -> bool:
        """移除应用程序
        
        Args:
            app_id: 要移除的应用程序ID
            
        Returns:
            bool: 移除是否成功
        """
        if app_id not in self.applications:
            logger.warning(f"找不到ID为 '{app_id}' 的应用程序")
            return False
        
        # 从所有分组中移除该应用
        for group in self.groups.values():
            group.remove_application(app_id)
        
        # 从搜索索引中移除
        self._remove_from_search_index(app_id)
        
        # 移除应用程序
        application = self.applications.pop(app_id)
        
        logger.info(f"移除应用程序: {application.name} ({app_id})")
        return True
    
    def get_application(self, app_id: str) -> Optional[LaunchedApplication]:
        """获取应用程序
        
        Args:
            app_id: 应用程序ID
            
        Returns:
            Optional[LaunchedApplication]: 应用程序对象或None
        """
        return self.applications.get(app_id)
    
    def get_all_applications(self) -> List[LaunchedApplication]:
        """获取所有应用程序
        
        Returns:
            List[LaunchedApplication]: 应用程序列表
        """
        return list(self.applications.values())
    
    def get_applications_by_group(self, group_id: str) -> List[LaunchedApplication]:
        """获取指定分组的所有应用程序
        
        Args:
            group_id: 分组ID
            
        Returns:
            List[LaunchedApplication]: 应用程序列表
        """
        if group_id not in self.groups:
            logger.warning(f"找不到ID为 '{group_id}' 的分组")
            return []
        
        group = self.groups[group_id]
        return [self.applications[app_id] for app_id in group.applications 
                if app_id in self.applications]
    
    def get_recent_applications(self, count: int = None) -> List[LaunchedApplication]:
        """获取最近使用的应用程序
        
        Args:
            count: 返回数量，默认为配置中的max_recent_apps
            
        Returns:
            List[LaunchedApplication]: 应用程序列表，按最近使用时间排序
        """
        if count is None:
            count = self.config["max_recent_apps"]
        
        # 筛选有使用记录的应用
        used_apps = [app for app in self.applications.values() if app.last_used is not None]
        
        # 按最近使用时间排序
        used_apps.sort(key=lambda app: app.last_used, reverse=True)
        
        return used_apps[:count]
    
    def get_favorite_applications(self) -> List[LaunchedApplication]:
        """获取收藏的应用程序
        
        Returns:
            List[LaunchedApplication]: 收藏的应用程序列表
        """
        favorite_group_id = self.config["favorite_group_id"]
        if not favorite_group_id or favorite_group_id not in self.groups:
            return []
        
        return self.get_applications_by_group(favorite_group_id)
    
    def launch_application(self, app_id: str) -> LaunchResult:
        """启动应用程序
        
        Args:
            app_id: 应用程序ID
            
        Returns:
            LaunchResult: 启动结果
        """
        # 检查应用是否存在
        application = self.get_application(app_id)
        if not application:
            message = f"找不到ID为 '{app_id}' 的应用程序"
            logger.warning(message)
            return LaunchResult(LaunchStatus.NOT_FOUND, message)
        
        # 检查应用路径是否存在
        if not os.path.exists(application.path):
            message = f"应用程序路径 '{application.path}' 不存在"
            logger.warning(message)
            return LaunchResult(LaunchStatus.NOT_FOUND, message)
        
        try:
            # 获取命令参数
            cmd = application.get_command_args()
            
            # 获取启动标志
            launch_flags = application.get_launch_flags()
            need_admin = launch_flags.pop("need_admin", False)
            
            # 如果需要管理员权限，使用特殊处理
            if need_admin:
                # 构建通过runas命令启动
                admin_cmd = ['runas', '/user:Administrator', f'"{" ".join(cmd)}"']
                cmd = admin_cmd
            
            # 准备环境变量
            env = os.environ.copy()
            if application.environment_variables:
                env.update(application.environment_variables)
            
            # 启动应用程序
            process = subprocess.Popen(
                cmd,
                cwd=application.working_directory,
                shell=True,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                env=env,
                **launch_flags
            )
            
            # 更新使用统计
            application.increase_usage_count()
            
            # 返回成功结果
            message = f"成功启动应用程序 '{application.name}'"
            logger.info(message)
            return LaunchResult(LaunchStatus.SUCCESS, message)
            
        except PermissionError as e:
            message = f"启动应用程序 '{application.name}' 权限不足"
            logger.error(f"{message}: {str(e)}")
            return LaunchResult(LaunchStatus.PERMISSION_ERROR, message, e)
            
        except Exception as e:
            message = f"启动应用程序 '{application.name}' 失败"
            logger.error(f"{message}: {str(e)}")
            return LaunchResult(LaunchStatus.UNKNOWN_ERROR, message, e)
    
    def add_group(self, group: LauncherGroup) -> bool:
        """添加分组
        
        Args:
            group: 要添加的分组
            
        Returns:
            bool: 添加是否成功
        """
        if group.id in self.groups:
            logger.warning(f"分组ID '{group.id}' 已存在")
            return False
        
        self.groups[group.id] = group
        logger.info(f"添加分组: {group.name} ({group.id})")
        return True
    
    def remove_group(self, group_id: str) -> bool:
        """移除分组
        
        Args:
            group_id: 要移除的分组ID
            
        Returns:
            bool: 移除是否成功
        """
        if group_id not in self.groups:
            logger.warning(f"找不到ID为 '{group_id}' 的分组")
            return False
        
        # 不允许移除收藏分组
        if group_id == self.config["favorite_group_id"]:
            logger.warning("不能移除收藏分组")
            return False
        
        # 移除分组
        group = self.groups.pop(group_id)
        
        logger.info(f"移除分组: {group.name} ({group_id})")
        return True
    
    def get_group(self, group_id: str) -> Optional[LauncherGroup]:
        """获取分组
        
        Args:
            group_id: 分组ID
            
        Returns:
            Optional[LauncherGroup]: 分组对象或None
        """
        return self.groups.get(group_id)
    
    def get_all_groups(self) -> List[LauncherGroup]:
        """获取所有分组
        
        Returns:
            List[LauncherGroup]: 分组列表
        """
        return list(self.groups.values())
    
    def add_to_group(self, app_id: str, group_id: str) -> bool:
        """将应用添加到分组
        
        Args:
            app_id: 应用程序ID
            group_id: 分组ID
            
        Returns:
            bool: 添加是否成功
        """
        # 检查应用是否存在
        if app_id not in self.applications:
            logger.warning(f"找不到ID为 '{app_id}' 的应用程序")
            return False
        
        # 检查分组是否存在
        if group_id not in self.groups:
            logger.warning(f"找不到ID为 '{group_id}' 的分组")
            return False
        
        # 添加到分组
        group = self.groups[group_id]
        success = group.add_application(app_id)
        
        if success:
            logger.info(f"将应用 '{app_id}' 添加到分组 '{group_id}'")
        
        return success
    
    def remove_from_group(self, app_id: str, group_id: str) -> bool:
        """从分组中移除应用
        
        Args:
            app_id: 应用程序ID
            group_id: 分组ID
            
        Returns:
            bool: 移除是否成功
        """
        # 检查分组是否存在
        if group_id not in self.groups:
            logger.warning(f"找不到ID为 '{group_id}' 的分组")
            return False
        
        # 从分组中移除
        group = self.groups[group_id]
        success = group.remove_application(app_id)
        
        if success:
            logger.info(f"从分组 '{group_id}' 中移除应用 '{app_id}'")
        
        return success
    
    def toggle_favorite(self, app_id: str) -> bool:
        """切换应用的收藏状态
        
        Args:
            app_id: 应用程序ID
            
        Returns:
            bool: 切换后的收藏状态
        """
        # 检查应用是否存在
        application = self.get_application(app_id)
        if not application:
            logger.warning(f"找不到ID为 '{app_id}' 的应用程序")
            return False
        
        # 获取收藏分组
        favorite_group_id = self.config["favorite_group_id"]
        if not favorite_group_id or favorite_group_id not in self.groups:
            logger.warning("收藏分组不存在")
            return False
        
        favorite_group = self.groups[favorite_group_id]
        
        # 切换收藏状态
        new_state = application.toggle_favorite()
        
        # 更新分组
        if new_state:
            favorite_group.add_application(app_id)
            logger.info(f"将应用 '{application.name}' 添加到收藏")
        else:
            favorite_group.remove_application(app_id)
            logger.info(f"将应用 '{application.name}' 从收藏中移除")
        
        return new_state
    
    def search_applications(self, query: str) -> List[LaunchedApplication]:
        """搜索应用程序
        
        Args:
            query: 搜索关键词
            
        Returns:
            List[LaunchedApplication]: 匹配的应用程序列表
        """
        if not query:
            return []
        
        # 分割关键词
        keywords = [kw.lower() for kw in query.split() if kw]
        if not keywords:
            return []
        
        # 匹配的应用ID集合
        matched_app_ids = set()
        
        # 对每个关键词查找匹配的应用ID
        for keyword in keywords:
            # 直接匹配
            for term, app_ids in self._search_index.items():
                if keyword in term:
                    matched_app_ids.update(app_ids)
        
        # 转换为应用对象列表
        results = [self.applications[app_id] for app_id in matched_app_ids 
                   if app_id in self.applications]
        
        # 按名称排序
        results.sort(key=lambda app: app.name)
        
        return results
    
    def save_configuration(self) -> bool:
        """保存配置
        
        Returns:
            bool: 保存是否成功
        """
        if not self.config_manager:
            logger.error("配置管理器未初始化")
            return False
        
        try:
            # 准备要保存的数据
            launcher_data = {
                "config": self.config,
                "applications": [app.to_dict() for app in self.applications.values()],
                "groups": [group.to_dict() for group in self.groups.values()]
            }
            
            # 保存到配置
            self.config_manager.set("launcher", launcher_data)
            self.config_manager.save_config()
            
            logger.info("启动器配置已保存")
            return True
            
        except Exception as e:
            logger.error(f"保存启动器配置失败: {str(e)}")
            return False
    
    def export_applications(self, file_path: str, app_ids: List[str] = None) -> bool:
        """导出应用程序列表到文件
        
        Args:
            file_path: 导出文件路径
            app_ids: 要导出的应用ID列表，如果为None则导出所有应用
            
        Returns:
            bool: 导出是否成功
        """
        try:
            # 确定要导出的应用
            apps_to_export = []
            if app_ids is None:
                # 导出所有应用
                apps_to_export = list(self.applications.values())
            else:
                # 导出指定的应用
                for app_id in app_ids:
                    app = self.get_application(app_id)
                    if app:
                        apps_to_export.append(app)
            
            # 准备导出数据
            export_data = {
                "applications": [app.to_dict() for app in apps_to_export],
                "format_version": "1.0",  # 导出格式版本
                "export_time": datetime.now().isoformat()
            }
            
            # 写入文件
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"成功导出 {len(apps_to_export)} 个应用程序到 {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"导出应用程序失败: {str(e)}")
            return False
    
    def import_applications(self, file_path: str) -> Tuple[int, int, List[str]]:
        """从文件导入应用程序列表
        
        Args:
            file_path: 导入文件路径
            
        Returns:
            Tuple[int, int, List[str]]: 导入成功数量，失败数量，错误消息列表
        """
        try:
            # 读取文件
            with open(file_path, 'r', encoding='utf-8') as f:
                import_data = json.load(f)
            
            # 验证导入数据格式
            if not isinstance(import_data, dict) or "applications" not in import_data:
                logger.error("导入文件格式错误")
                return 0, 0, ["导入文件格式错误"]
            
            # 导入应用
            success_count = 0
            fail_count = 0
            error_messages = []
            
            for app_data in import_data["applications"]:
                try:
                    # 创建应用对象
                    app = LaunchedApplication.from_dict(app_data)
                    
                    # 检查应用路径是否存在
                    if not os.path.exists(app.path):
                        error_msg = f"应用 '{app.name}' 导入失败: 路径 '{app.path}' 不存在"
                        logger.warning(error_msg)
                        error_messages.append(error_msg)
                        fail_count += 1
                        continue
                    
                    # 检查应用ID是否已存在
                    existing_app = self.get_application(app.id)
                    if existing_app:
                        # 更新现有应用
                        self.applications[app.id] = app
                        logger.info(f"更新应用程序: {app.name} ({app.id})")
                    else:
                        # 添加新应用
                        self.applications[app.id] = app
                        logger.info(f"添加应用程序: {app.name} ({app.id})")
                    
                    # 更新搜索索引
                    self._update_search_index_for_app(app)
                    
                    # 如果应用是收藏的，添加到收藏分组
                    if app.favorite and self.config["favorite_group_id"]:
                        favorite_group = self.groups.get(self.config["favorite_group_id"])
                        if favorite_group:
                            favorite_group.add_application(app.id)
                    
                    success_count += 1
                    
                except Exception as e:
                    error_msg = f"应用导入失败: {str(e)}"
                    logger.error(error_msg)
                    error_messages.append(error_msg)
                    fail_count += 1
            
            logger.info(f"导入完成: {success_count} 个成功, {fail_count} 个失败")
            return success_count, fail_count, error_messages
            
        except Exception as e:
            logger.error(f"导入应用程序失败: {str(e)}")
            return 0, 0, [f"导入文件失败: {str(e)}"]
    
    def export_group(self, group_id: str, file_path: str) -> bool:
        """导出分组到文件
        
        Args:
            group_id: 分组ID
            file_path: 导出文件路径
            
        Returns:
            bool: 导出是否成功
        """
        try:
            # 获取分组
            group = self.get_group(group_id)
            if not group:
                logger.error(f"找不到ID为 '{group_id}' 的分组")
                return False
            
            # 获取分组中的应用
            apps = []
            for app_id in group.applications:
                app = self.get_application(app_id)
                if app:
                    apps.append(app)
            
            # 准备导出数据
            export_data = {
                "group": group.to_dict(),
                "applications": [app.to_dict() for app in apps],
                "format_version": "1.0",
                "export_time": datetime.now().isoformat()
            }
            
            # 写入文件
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"成功导出分组 '{group.name}' 及其 {len(apps)} 个应用程序到 {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"导出分组失败: {str(e)}")
            return False
    
    def import_group(self, file_path: str) -> Tuple[bool, str, int, int]:
        """从文件导入分组
        
        Args:
            file_path: 导入文件路径
            
        Returns:
            Tuple[bool, str, int, int]: 是否成功, 分组ID, 成功导入应用数, 失败数
        """
        try:
            # 读取文件
            with open(file_path, 'r', encoding='utf-8') as f:
                import_data = json.load(f)
            
            # 验证导入数据格式
            if not isinstance(import_data, dict) or "group" not in import_data or "applications" not in import_data:
                logger.error("导入文件格式错误")
                return False, "", 0, 0
            
            # 导入分组
            group_data = import_data["group"]
            group = LauncherGroup.from_dict(group_data)
            
            # 重置分组的应用列表
            group.applications = []
            
            # 检查分组ID是否已存在
            existing_group = self.get_group(group.id)
            if existing_group:
                # 更新现有分组
                self.groups[group.id] = group
                logger.info(f"更新分组: {group.name} ({group.id})")
            else:
                # 添加新分组
                self.groups[group.id] = group
                logger.info(f"添加分组: {group.name} ({group.id})")
            
            # 导入应用
            success_count = 0
            fail_count = 0
            
            for app_data in import_data["applications"]:
                try:
                    # 创建应用对象
                    app = LaunchedApplication.from_dict(app_data)
                    
                    # 检查应用路径是否存在
                    if not os.path.exists(app.path):
                        logger.warning(f"应用 '{app.name}' 导入失败: 路径 '{app.path}' 不存在")
                        fail_count += 1
                        continue
                    
                    # 检查应用ID是否已存在
                    existing_app = self.get_application(app.id)
                    if existing_app:
                        # 更新现有应用
                        self.applications[app.id] = app
                        logger.info(f"更新应用程序: {app.name} ({app.id})")
                    else:
                        # 添加新应用
                        self.applications[app.id] = app
                        logger.info(f"添加应用程序: {app.name} ({app.id})")
                    
                    # 更新搜索索引
                    self._update_search_index_for_app(app)
                    
                    # 添加应用到分组
                    group.add_application(app.id)
                    
                    success_count += 1
                    
                except Exception as e:
                    logger.error(f"应用导入失败: {str(e)}")
                    fail_count += 1
            
            logger.info(f"分组导入完成: {success_count} 个应用成功, {fail_count} 个失败")
            return True, group.id, success_count, fail_count
            
        except Exception as e:
            logger.error(f"导入分组失败: {str(e)}")
            return False, "", 0, 0
    
    def _load_configuration(self) -> bool:
        """加载配置
        
        Returns:
            bool: 加载是否成功
        """
        if not self.config_manager:
            logger.error("配置管理器未初始化")
            return False
        
        try:
            # 从配置中加载数据
            launcher_data = self.config_manager.get("launcher", {})
            
            # 加载配置
            if "config" in launcher_data:
                # 更新配置，保留默认值
                for key, value in launcher_data["config"].items():
                    if key in self.config:
                        self.config[key] = value
            
            # 加载应用程序
            for app_data in launcher_data.get("applications", []):
                try:
                    app = LaunchedApplication.from_dict(app_data)
                    self.applications[app.id] = app
                except Exception as e:
                    logger.error(f"加载应用程序失败: {str(e)}")
            
            # 加载分组
            for group_data in launcher_data.get("groups", []):
                try:
                    group = LauncherGroup.from_dict(group_data)
                    self.groups[group.id] = group
                except Exception as e:
                    logger.error(f"加载分组失败: {str(e)}")
            
            logger.info("启动器配置已加载")
            return True
            
        except Exception as e:
            logger.error(f"加载启动器配置失败: {str(e)}")
            return False
    
    def _load_system_applications(self) -> None:
        """加载系统应用程序
        
        此函数是平台相关的，目前仅支持Windows
        """
        import winreg
        
        try:
            # 创建系统应用分组
            system_group = LauncherGroup("系统应用", description="系统自带应用程序")
            self.add_group(system_group)
            
            # 读取所有已安装的应用
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, 
                               r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths") as key:
                # 获取子键数量
                subkey_count = winreg.QueryInfoKey(key)[0]
                
                # 遍历子键
                for i in range(subkey_count):
                    try:
                        app_name = winreg.EnumKey(key, i)
                        
                        # 打开应用子键
                        with winreg.OpenKey(key, app_name) as app_key:
                            # 获取默认值（应用路径）
                            app_path = winreg.QueryValue(app_key, None)
                            
                            # 创建应用对象
                            app = LaunchedApplication(
                                name=os.path.splitext(app_name)[0],  # 去除扩展名
                                path=app_path,
                                description="系统应用"
                            )
                            
                            # 添加应用并加入系统分组
                            if self.add_application(app):
                                system_group.add_application(app.id)
                    
                    except Exception as e:
                        logger.error(f"加载系统应用失败: {str(e)}")
                        continue
            
            logger.info(f"成功加载 {len(system_group.applications)} 个系统应用")
            
        except Exception as e:
            logger.error(f"加载系统应用失败: {str(e)}")
    
    def _update_search_index_for_app(self, application: LaunchedApplication) -> None:
        """更新应用的搜索索引
        
        Args:
            application: 要索引的应用
        """
        # 移除旧索引（如果存在）
        self._remove_from_search_index(application.id)
        
        # 添加新索引
        terms = set()
        
        # 添加名称（分词）
        for term in application.name.lower().split():
            if term:
                terms.add(term)
        
        # 添加描述（分词）
        if application.description:
            for term in application.description.lower().split():
                if term:
                    terms.add(term)
        
        # 添加标签
        for tag in application.tags:
            if tag:
                terms.add(tag.lower())
        
        # 更新索引
        for term in terms:
            if term not in self._search_index:
                self._search_index[term] = set()
            self._search_index[term].add(application.id)
    
    def _remove_from_search_index(self, app_id: str) -> None:
        """从搜索索引中移除应用
        
        Args:
            app_id: 要移除的应用ID
        """
        for term, app_ids in list(self._search_index.items()):
            if app_id in app_ids:
                app_ids.remove(app_id)
                
                # 如果没有应用与该关键词关联，移除该关键词
                if not app_ids:
                    del self._search_index[term]
    
    def _rebuild_search_index(self) -> None:
        """重建整个搜索索引"""
        # 清空索引
        self._search_index.clear()
        
        # 为每个应用重新建立索引
        for application in self.applications.values():
            self._update_search_index_for_app(application)
        
        logger.debug(f"搜索索引已重建，包含 {len(self._search_index)} 个索引项")
    
    def shutdown(self) -> None:
        """关闭启动器管理器"""
        if not self._initialized:
            return
        
        # 保存配置
        self.save_configuration()
        
        # 重置状态
        self._initialized = False
        
        logger.info("LauncherManager已关闭") 