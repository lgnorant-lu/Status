"""
---------------------------------------------------------------
File name:                  command_manager.py
Author:                     Ignorant-lu
Date created:               2025/04/05
Description:                命令管理器模块，负责协调命令注册、解析和执行
----------------------------------------------------------------

Changed history:            
                            2025/04/05: 初始创建;
----
"""

import logging
from typing import Dict, List, Optional, Any, Set, Tuple, Callable, Union
from datetime import datetime
import threading

from status.interaction.command.command_types import (
    Command, 
    CommandType, 
    CommandStatus, 
    CommandContext,
    CommandRegistry
)
from status.interaction.command.command_parser import CommandParser
from status.event.event_manager import EventManager
from status.interaction.interaction_event import InteractionEvent, InteractionEventType

# 配置日志
logger = logging.getLogger(__name__)

class CommandManager:
    """
    命令管理器，负责协调命令注册、解析和执行
    
    使用单例模式确保全局只有一个命令管理器实例。
    """
    
    _instance = None
    _lock = threading.Lock()
    
    @classmethod
    def get_instance(cls) -> 'CommandManager':
        """
        获取命令管理器的单例实例
        
        Returns:
            命令管理器实例
        """
        with cls._lock:
            if cls._instance is None:
                logger.debug("创建命令管理器实例")
                cls._instance = CommandManager()
            return cls._instance
    
    def __init__(self):
        """初始化命令管理器"""
        if CommandManager._instance is not None:
            raise RuntimeError("CommandManager是单例模式，请使用get_instance()获取实例")
        
        # 命令注册中心
        self.registry = CommandRegistry()
        
        # 命令解析器
        self.parser = CommandParser()
        
        # 命令历史记录
        self.history: List[CommandContext] = []
        
        # 命令别名映射
        self.aliases: Dict[str, str] = {}
        
        # 命令组
        self.command_groups: Dict[str, List[str]] = {}
        
        # 事件管理器引用
        self.event_manager = None
        
        # 管理器状态
        self.enabled = True
        
        # 初始化标志
        self._initialized = False
        
        logger.debug("命令管理器已初始化")
    
    def initialize(self) -> bool:
        """
        初始化命令管理器
        
        注册系统命令、设置事件监听器等
        
        Returns:
            初始化是否成功
        """
        if self._initialized:
            logger.warning("命令管理器已经初始化")
            return False
        
        try:
            # 获取事件管理器引用
            from status.event.event_manager import EventManager
            self.event_manager = EventManager.get_instance()
            
            # 注册事件监听器
            self.event_manager.add_listener(
                InteractionEventType.COMMAND,
                self._handle_command_event
            )
            
            self.event_manager.add_listener(
                InteractionEventType.MENU_COMMAND,
                self._handle_menu_command_event
            )
            
            self.event_manager.add_listener(
                InteractionEventType.TRAY_MENU_COMMAND,
                self._handle_tray_menu_command_event
            )
            
            # 注册系统命令
            self._register_system_commands()
            
            self._initialized = True
            logger.info("命令管理器初始化成功")
            return True
            
        except Exception as e:
            logger.error(f"命令管理器初始化失败: {str(e)}")
            return False
    
    def _register_system_commands(self):
        """注册系统命令"""
        # 帮助命令
        self.register_command(
            Command(
                name="help",
                callback=self._help_command,
                description="显示帮助信息",
                type=CommandType.SYSTEM,
                parameters={
                    "command": {
                        "type": str,
                        "required": False,
                        "description": "要查看帮助的命令名"
                    }
                }
            )
        )
        
        # 命令列表命令
        self.register_command(
            Command(
                name="commands",
                callback=self._commands_command,
                description="显示所有可用命令",
                type=CommandType.SYSTEM,
                parameters={
                    "group": {
                        "type": str,
                        "required": False,
                        "description": "筛选特定组的命令"
                    }
                }
            )
        )
        
        # 命令历史命令
        self.register_command(
            Command(
                name="history",
                callback=self._history_command,
                description="显示命令历史记录",
                type=CommandType.SYSTEM,
                parameters={
                    "count": {
                        "type": int,
                        "required": False,
                        "default": 10,
                        "description": "要显示的历史记录数量"
                    }
                }
            )
        )
        
        # 别名命令
        self.register_command(
            Command(
                name="alias",
                callback=self._alias_command,
                description="管理命令别名",
                type=CommandType.SYSTEM,
                parameters={
                    "action": {
                        "type": str,
                        "required": False,
                        "default": "list",
                        "description": "操作类型：add, remove, list"
                    },
                    "name": {
                        "type": str,
                        "required": False,
                        "description": "别名名称"
                    },
                    "command": {
                        "type": str,
                        "required": False,
                        "description": "对应的命令"
                    }
                }
            )
        )
    
    def register_command(self, command: Command) -> bool:
        """
        注册命令
        
        Args:
            command: 要注册的命令对象
            
        Returns:
            注册是否成功
        """
        return self.registry.register(command)
    
    def unregister_command(self, command_name: str) -> bool:
        """
        注销命令
        
        Args:
            command_name: 要注销的命令名
            
        Returns:
            注销是否成功
        """
        return self.registry.unregister(command_name)
    
    def execute_command(self, command_text: str, source: str = "text") -> CommandContext:
        """
        执行命令文本
        
        Args:
            command_text: 命令文本
            source: 命令来源
            
        Returns:
            命令执行上下文
        """
        if not self.enabled:
            logger.warning("命令管理器已禁用，无法执行命令")
            context = CommandContext(command_name="")
            return context.set_error("命令管理器已禁用", CommandStatus.PERMISSION_DENIED)
        
        # 解析命令
        context = self.parser.create_context(command_text, source)
        
        if not context:
            logger.warning(f"无法解析命令: {command_text}")
            context = CommandContext(command_name="")
            return context.set_error(f"无法解析命令: {command_text}", CommandStatus.NOT_FOUND)
        
        # 查找命令
        command = self.registry.get_command(context.command_name)
        
        if not command:
            logger.warning(f"命令未找到: {context.command_name}")
            return context.set_error(f"命令未找到: {context.command_name}", CommandStatus.NOT_FOUND)
        
        # 执行命令
        logger.debug(f"执行命令: {context.command_name}")
        result_context = command.execute(context)
        
        # 添加到历史记录
        self.add_to_history(result_context)
        
        return result_context
    
    def add_to_history(self, context: CommandContext):
        """
        添加命令上下文到历史记录
        
        Args:
            context: 命令上下文
        """
        # 存储历史时间
        context.timestamp = datetime.now()
        
        # 添加到历史记录
        self.history.append(context)
        
        # 限制历史记录大小
        max_history = 100
        if len(self.history) > max_history:
            self.history = self.history[-max_history:]
    
    def get_history(self, count: int = None) -> List[CommandContext]:
        """
        获取命令历史记录
        
        Args:
            count: 要获取的记录数量，默认为全部
            
        Returns:
            命令历史记录列表
        """
        if count is None:
            return self.history.copy()
        return self.history[-count:]
    
    def clear_history(self):
        """清空命令历史记录"""
        self.history.clear()
        logger.debug("命令历史记录已清空")
    
    def add_alias(self, alias: str, command_name: str) -> bool:
        """
        添加命令别名
        
        Args:
            alias: 别名
            command_name: 对应的命令名
            
        Returns:
            添加是否成功
        """
        # 检查命令是否存在
        command = self.registry.get_command(command_name)
        if not command:
            logger.warning(f"无法为不存在的命令 '{command_name}' 添加别名")
            return False
        
        return self.registry.add_alias(command_name, alias)
    
    def remove_alias(self, alias: str) -> bool:
        """
        移除命令别名
        
        Args:
            alias: 要移除的别名
            
        Returns:
            移除是否成功
        """
        return self.registry.remove_alias(alias)
    
    def get_aliases(self) -> Dict[str, str]:
        """
        获取所有命令别名
        
        Returns:
            别名字典，格式为 {别名: 命令名}
        """
        return {alias: self.registry._aliases[alias] for alias in self.registry._aliases}
    
    def set_command_prefix(self, prefix: str):
        """
        设置命令前缀
        
        Args:
            prefix: 新的命令前缀
        """
        self.parser.set_command_prefix(prefix)
    
    def set_comment_prefix(self, prefix: str):
        """
        设置注释前缀
        
        Args:
            prefix: 新的注释前缀
        """
        self.parser.set_comment_prefix(prefix)
    
    def enable(self):
        """启用命令管理器"""
        if not self.enabled:
            self.enabled = True
            logger.info("命令管理器已启用")
    
    def disable(self):
        """禁用命令管理器"""
        if self.enabled:
            self.enabled = False
            logger.info("命令管理器已禁用")
    
    def shutdown(self):
        """关闭命令管理器"""
        logger.info("正在关闭命令管理器")
        
        # 取消事件监听
        if self.event_manager:
            self.event_manager.remove_listener(InteractionEventType.COMMAND, self._handle_command_event)
            self.event_manager.remove_listener(InteractionEventType.MENU_COMMAND, self._handle_menu_command_event)
            self.event_manager.remove_listener(InteractionEventType.TRAY_MENU_COMMAND, self._handle_tray_menu_command_event)
        
        # 清空历史记录
        self.clear_history()
        
        # 清空命令注册表
        self.registry.clear()
        
        # 禁用管理器
        self.enabled = False
        
        # 重置初始化标志
        self._initialized = False
        
        logger.info("命令管理器已关闭")
    
    def _handle_command_event(self, event: InteractionEvent):
        """
        处理命令事件
        
        Args:
            event: 交互事件
        """
        if not event.data or not isinstance(event.data, dict):
            logger.warning("命令事件没有有效数据")
            return
        
        command_text = event.data.get("command")
        if not command_text:
            logger.warning("命令事件中没有命令文本")
            return
        
        source = event.data.get("source", "event")
        context = self.execute_command(command_text, source)
        
        # 发送命令结果事件
        if self.event_manager:
            result_event = InteractionEvent(
                type=InteractionEventType.COMMAND_RESULT,
                data={
                    "command": command_text,
                    "result": context.result,
                    "status": context.status.value,
                    "error": context.error_message
                }
            )
            self.event_manager.emit(result_event)
    
    def _handle_menu_command_event(self, event: InteractionEvent):
        """
        处理菜单命令事件
        
        Args:
            event: 交互事件
        """
        if not event.data or not isinstance(event.data, dict):
            logger.warning("菜单命令事件没有有效数据")
            return
        
        command_name = event.data.get("command")
        if not command_name:
            logger.warning("菜单命令事件中没有命令名")
            return
        
        # 查找命令
        command = self.registry.get_command(command_name)
        
        if not command:
            logger.warning(f"菜单命令未找到: {command_name}")
            return
        
        # 创建命令上下文
        context = CommandContext(
            command_name=command_name,
            params=event.data.get("params", {}),
            source="menu"
        )
        
        # 执行命令
        result_context = command.execute(context)
        
        # 添加到历史记录
        self.add_to_history(result_context)
        
        # 发送命令结果事件
        if self.event_manager:
            result_event = InteractionEvent(
                type=InteractionEventType.COMMAND_RESULT,
                data={
                    "command": command_name,
                    "result": result_context.result,
                    "status": result_context.status.value,
                    "error": result_context.error_message
                }
            )
            self.event_manager.emit(result_event)
    
    def _handle_tray_menu_command_event(self, event: InteractionEvent):
        """
        处理托盘菜单命令事件
        
        Args:
            event: 交互事件
        """
        # 托盘菜单命令处理与普通菜单命令类似
        self._handle_menu_command_event(event)
    
    # 系统命令回调函数
    def _help_command(self, context: CommandContext) -> CommandContext:
        """
        帮助命令回调
        
        Args:
            context: 命令上下文
            
        Returns:
            更新后的命令上下文
        """
        command_name = context.params.get("command")
        
        if command_name:
            # 显示特定命令的帮助
            command = self.registry.get_command(command_name)
            
            if not command:
                return context.set_error(f"命令 '{command_name}' 不存在", CommandStatus.NOT_FOUND)
            
            help_text = command.get_help()
            return context.set_result(help_text)
        else:
            # 显示一般帮助
            help_text = [
                "可用命令组:",
                "--------------"
            ]
            
            for group in self.registry.get_command_groups():
                commands = self.registry.get_group_commands(group)
                if commands:
                    help_text.append(f"{group} ({len(commands)}个命令)")
            
            help_text.extend([
                "",
                "使用 help <命令名> 查看特定命令的帮助",
                "使用 commands [组名] 查看命令列表"
            ])
            
            return context.set_result("\n".join(help_text))
    
    def _commands_command(self, context: CommandContext) -> CommandContext:
        """
        命令列表命令回调
        
        Args:
            context: 命令上下文
            
        Returns:
            更新后的命令上下文
        """
        group = context.params.get("group")
        
        if group:
            # 显示特定组的命令
            commands = self.registry.get_group_commands(group)
            
            if not commands:
                return context.set_error(f"命令组 '{group}' 不存在或没有命令", CommandStatus.NOT_FOUND)
            
            command_list = [f"{group} 组命令:"]
            for cmd in commands:
                command_list.append(f"  {cmd.name}: {cmd.description}")
            
            return context.set_result("\n".join(command_list))
        else:
            # 显示所有命令
            command_list = ["所有可用命令:"]
            
            for group in self.registry.get_command_groups():
                commands = self.registry.get_group_commands(group)
                if commands:
                    command_list.append(f"\n{group}:")
                    for cmd in commands:
                        command_list.append(f"  {cmd.name}: {cmd.description}")
            
            return context.set_result("\n".join(command_list))
    
    def _history_command(self, context: CommandContext) -> CommandContext:
        """
        命令历史命令回调
        
        Args:
            context: 命令上下文
            
        Returns:
            更新后的命令上下文
        """
        count = int(context.params.get("count", 10))
        
        history = self.get_history(count)
        
        if not history:
            return context.set_result("命令历史记录为空")
        
        history_text = ["最近的命令:"]
        for i, cmd_context in enumerate(reversed(history), 1):
            status = "成功" if cmd_context.succeeded() else f"失败: {cmd_context.error_message}"
            timestamp = getattr(cmd_context, 'timestamp', None)
            time_str = timestamp.strftime('%Y-%m-%d %H:%M:%S') if timestamp else 'N/A'
            history_text.append(f"{i}. [{time_str}] {cmd_context.command_name} - {status}")
        
        return context.set_result("\n".join(history_text))
    
    def _alias_command(self, context: CommandContext) -> CommandContext:
        """
        别名命令回调
        
        Args:
            context: 命令上下文
            
        Returns:
            更新后的命令上下文
        """
        action = context.params.get("action", "list").lower()
        
        if action == "list":
            # 列出所有别名
            aliases = self.get_aliases()
            
            if not aliases:
                return context.set_result("没有定义的命令别名")
            
            alias_text = ["命令别名:"]
            for alias, command in aliases.items():
                alias_text.append(f"  {alias} -> {command}")
            
            return context.set_result("\n".join(alias_text))
            
        elif action == "add":
            # 添加别名
            alias = context.params.get("name")
            command = context.params.get("command")
            
            if not alias or not command:
                return context.set_error("添加别名需要指定 name 和 command 参数", CommandStatus.INVALID_PARAMS)
            
            success = self.add_alias(alias, command)
            
            if success:
                return context.set_result(f"别名 '{alias}' 已添加，指向命令 '{command}'")
            else:
                return context.set_error(f"无法添加别名 '{alias}'", CommandStatus.FAILED)
                
        elif action == "remove":
            # 移除别名
            alias = context.params.get("name")
            
            if not alias:
                return context.set_error("移除别名需要指定 name 参数", CommandStatus.INVALID_PARAMS)
            
            success = self.remove_alias(alias)
            
            if success:
                return context.set_result(f"别名 '{alias}' 已移除")
            else:
                return context.set_error(f"无法移除别名 '{alias}'", CommandStatus.FAILED)
                
        else:
            return context.set_error(f"未知的操作: {action}", CommandStatus.INVALID_PARAMS) 