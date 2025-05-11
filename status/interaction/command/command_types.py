"""
---------------------------------------------------------------
File name:                  command_types.py
Author:                     Ignorant-lu
Date created:               2025/04/05
Description:                命令系统的核心数据类型和命令模型定义
----------------------------------------------------------------

Changed history:            
                            2025/04/05: 初始创建;
----
"""

import enum
import logging
from typing import Callable, Dict, List, Any, Optional, Union, Set, Tuple
from dataclasses import dataclass, field

# 配置日志
logger = logging.getLogger(__name__)

class CommandType(enum.Enum):
    """命令类型枚举"""
    SYSTEM = "system"       # 系统命令，如帮助、历史记录等
    ACTION = "action"       # 动作命令，执行特定操作
    QUERY = "query"         # 查询命令，获取信息
    CONFIG = "config"       # 配置命令，更改设置
    CUSTOM = "custom"       # 自定义命令

class CommandStatus(enum.Enum):
    """命令执行状态枚举"""
    SUCCESS = "success"           # 命令执行成功
    FAILED = "failed"             # 命令执行失败
    NOT_FOUND = "not_found"       # 命令未找到
    INVALID_PARAMS = "invalid_params"  # 参数无效
    NOT_EXECUTED = "not_executed"  # 命令未执行
    PERMISSION_DENIED = "permission_denied"  # 权限不足
    CANCELED = "canceled"         # 命令已取消

@dataclass
class CommandContext:
    """命令上下文，包含命令执行的环境信息和参数"""
    command_name: str
    params: Dict[str, Any] = field(default_factory=dict)
    raw_text: Optional[str] = None
    source: Optional[str] = None  # 命令来源：text, hotkey, gesture, etc.
    user_id: Optional[str] = None
    result: Any = None
    status: CommandStatus = CommandStatus.NOT_EXECUTED
    error_message: Optional[str] = None
    
    def set_result(self, result: Any, status: CommandStatus = CommandStatus.SUCCESS):
        """设置命令执行结果"""
        self.result = result
        self.status = status
        return self
    
    def set_error(self, error_message: str, status: CommandStatus = CommandStatus.FAILED):
        """设置命令执行错误"""
        self.error_message = error_message
        self.status = status
        return self
    
    def succeeded(self) -> bool:
        """检查命令是否执行成功"""
        return self.status == CommandStatus.SUCCESS
    
    def failed(self) -> bool:
        """检查命令是否执行失败"""
        return self.status != CommandStatus.SUCCESS

class Command:
    """命令类，代表一个可执行的命令"""
    
    def __init__(self, 
                 name: str, 
                 callback: Callable[[CommandContext], CommandContext],
                 description: str = "",
                 type: CommandType = CommandType.ACTION,
                 aliases: List[str] = None,
                 group: str = "default",
                 parameters: Dict[str, Dict[str, Any]] = None,
                 enabled: bool = True,
                 permission_level: int = 0):
        """
        初始化命令对象
        
        Args:
            name: 命令名称，用于唯一标识命令
            callback: 命令执行函数，接收命令上下文作为参数，返回更新后的上下文
            description: 命令描述，用于帮助信息
            type: 命令类型
            aliases: 命令别名列表
            group: 命令所属分组
            parameters: 命令参数定义，格式为{param_name: {type: type, required: bool, default: value, description: str}}
            enabled: 命令是否启用
            permission_level: 执行命令所需的权限级别
        """
        self.name = name
        self.callback = callback
        self.description = description
        self.type = type
        self.aliases = aliases or []
        self.group = group
        self.parameters = parameters or {}
        self.enabled = enabled
        self.permission_level = permission_level
        
        # 验证参数定义
        self._validate_parameters()
        
        logger.debug(f"命令已创建: {self.name} (类型: {self.type.value}, 组: {self.group})")
    
    def _validate_parameters(self):
        """验证参数定义的有效性"""
        for param_name, param_def in self.parameters.items():
            # 确保每个参数定义至少包含类型
            if 'type' not in param_def:
                param_def['type'] = str
            
            # 设置默认值
            if 'required' not in param_def:
                param_def['required'] = False
            
            # 如果参数不是必需的，确保有默认值
            if not param_def['required'] and 'default' not in param_def:
                # 根据类型设置合适的默认值
                if param_def['type'] == bool:
                    param_def['default'] = False
                elif param_def['type'] == int:
                    param_def['default'] = 0
                elif param_def['type'] == float:
                    param_def['default'] = 0.0
                elif param_def['type'] == list:
                    param_def['default'] = []
                elif param_def['type'] == dict:
                    param_def['default'] = {}
                else:
                    param_def['default'] = None
    
    def execute(self, context: CommandContext) -> CommandContext:
        """
        执行命令
        
        Args:
            context: 命令上下文，包含执行所需的参数和环境信息
            
        Returns:
            更新后的命令上下文，包含执行结果
        """
        if not self.enabled:
            return context.set_error(
                f"命令 '{self.name}' 已禁用",
                CommandStatus.PERMISSION_DENIED
            )
        
        # 验证必需参数
        for param_name, param_def in self.parameters.items():
            if param_def.get('required', False) and param_name not in context.params:
                return context.set_error(
                    f"缺少必需参数: {param_name}",
                    CommandStatus.INVALID_PARAMS
                )
        
        # 应用默认参数
        for param_name, param_def in self.parameters.items():
            if param_name not in context.params and 'default' in param_def:
                context.params[param_name] = param_def['default']
        
        try:
            # 执行命令回调
            result_context = self.callback(context)
            if result_context is None:
                # 如果回调没有返回上下文，则使用当前上下文
                logger.warning(f"命令 '{self.name}' 的回调未返回上下文，使用原始上下文")
                return context.set_result(None)
            return result_context
        except Exception as e:
            logger.exception(f"执行命令 '{self.name}' 时出错")
            return context.set_error(str(e))
    
    def get_usage(self) -> str:
        """
        获取命令用法说明
        
        Returns:
            命令用法字符串
        """
        usage = f"{self.name}"
        
        # 添加参数
        param_parts = []
        for param_name, param_def in self.parameters.items():
            is_required = param_def.get('required', False)
            has_default = 'default' in param_def
            param_desc = f"{param_name}"
            
            if has_default:
                param_desc += f"={param_def['default']}"
                
            if is_required:
                param_parts.append(f"<{param_desc}>")
            else:
                param_parts.append(f"[{param_desc}]")
        
        if param_parts:
            usage += " " + " ".join(param_parts)
            
        return usage
    
    def get_help(self) -> str:
        """
        获取命令帮助信息
        
        Returns:
            命令帮助字符串
        """
        help_text = [
            f"命令: {self.name}",
            f"描述: {self.description or '无描述'}",
            f"类型: {self.type.value}",
            f"用法: {self.get_usage()}"
        ]
        
        if self.aliases:
            help_text.append(f"别名: {', '.join(self.aliases)}")
            
        if self.parameters:
            help_text.append("\n参数:")
            for param_name, param_def in self.parameters.items():
                param_type = param_def.get('type', str).__name__
                required = "必需" if param_def.get('required', False) else "可选"
                default = f", 默认值: {param_def.get('default')}" if 'default' in param_def else ""
                description = f" - {param_def.get('description', '无描述')}" if 'description' in param_def else ""
                
                help_text.append(f"  {param_name} ({param_type}, {required}{default}){description}")
        
        return "\n".join(help_text)

class CommandRegistry:
    """
    命令注册中心，管理命令的注册和查找
    """
    
    def __init__(self):
        """初始化命令注册中心"""
        self._commands: Dict[str, Command] = {}
        self._aliases: Dict[str, str] = {}
        self._groups: Dict[str, Set[str]] = {}
        logger.debug("命令注册中心已初始化")
    
    def register(self, command: Command) -> bool:
        """
        注册命令
        
        Args:
            command: 要注册的命令对象
            
        Returns:
            注册是否成功
        """
        # 检查命令名是否已存在
        if command.name in self._commands:
            logger.warning(f"命令名 '{command.name}' 已存在，注册失败")
            return False
        
        # 检查别名是否已存在
        for alias in command.aliases:
            if alias in self._aliases or alias in self._commands:
                logger.warning(f"命令别名 '{alias}' 已存在，将被忽略")
                command.aliases.remove(alias)
        
        # 注册命令
        self._commands[command.name] = command
        
        # 注册别名
        for alias in command.aliases:
            self._aliases[alias] = command.name
        
        # 添加到分组
        if command.group not in self._groups:
            self._groups[command.group] = set()
        self._groups[command.group].add(command.name)
        
        logger.debug(f"命令 '{command.name}' 已注册 (组: {command.group})")
        return True
    
    def unregister(self, command_name: str) -> bool:
        """
        注销命令
        
        Args:
            command_name: 要注销的命令名
            
        Returns:
            注销是否成功
        """
        # 检查命令是否存在
        if command_name not in self._commands:
            logger.warning(f"命令 '{command_name}' 不存在，无法注销")
            return False
        
        command = self._commands[command_name]
        
        # 删除别名
        for alias in command.aliases:
            if alias in self._aliases and self._aliases[alias] == command_name:
                del self._aliases[alias]
        
        # 从分组中移除
        if command.group in self._groups and command_name in self._groups[command.group]:
            self._groups[command.group].remove(command_name)
            if not self._groups[command.group]:
                del self._groups[command.group]
        
        # 删除命令
        del self._commands[command_name]
        
        logger.debug(f"命令 '{command_name}' 已注销")
        return True
    
    def get_command(self, command_name_or_alias: str) -> Optional[Command]:
        """
        获取命令对象
        
        Args:
            command_name_or_alias: 命令名或别名
            
        Returns:
            命令对象，如果未找到则返回None
        """
        # 先检查是否为命令名
        if command_name_or_alias in self._commands:
            return self._commands[command_name_or_alias]
        
        # 再检查是否为别名
        if command_name_or_alias in self._aliases:
            command_name = self._aliases[command_name_or_alias]
            return self._commands[command_name]
        
        return None
    
    def get_group_commands(self, group_name: str) -> List[Command]:
        """
        获取指定分组中的所有命令
        
        Args:
            group_name: 分组名称
            
        Returns:
            命令对象列表
        """
        if group_name not in self._groups:
            return []
        
        return [self._commands[name] for name in self._groups[group_name] if name in self._commands]
    
    def get_all_commands(self) -> List[Command]:
        """
        获取所有命令
        
        Returns:
            所有命令对象的列表
        """
        return list(self._commands.values())
    
    def get_command_groups(self) -> List[str]:
        """
        获取所有命令分组名称
        
        Returns:
            分组名称列表
        """
        return list(self._groups.keys())
    
    def add_alias(self, command_name: str, alias: str) -> bool:
        """
        为命令添加别名
        
        Args:
            command_name: 命令名
            alias: 要添加的别名
            
        Returns:
            添加是否成功
        """
        # 检查命令是否存在
        if command_name not in self._commands:
            logger.warning(f"命令 '{command_name}' 不存在，无法添加别名")
            return False
        
        # 检查别名是否已存在
        if alias in self._aliases or alias in self._commands:
            logger.warning(f"别名 '{alias}' 已存在，无法添加")
            return False
        
        # 添加别名
        self._aliases[alias] = command_name
        self._commands[command_name].aliases.append(alias)
        
        logger.debug(f"为命令 '{command_name}' 添加别名 '{alias}'")
        return True
    
    def remove_alias(self, alias: str) -> bool:
        """
        移除命令别名
        
        Args:
            alias: 要移除的别名
            
        Returns:
            移除是否成功
        """
        # 检查别名是否存在
        if alias not in self._aliases:
            logger.warning(f"别名 '{alias}' 不存在，无法移除")
            return False
        
        # 获取命令名
        command_name = self._aliases[alias]
        
        # 从命令的别名列表中移除
        if command_name in self._commands and alias in self._commands[command_name].aliases:
            self._commands[command_name].aliases.remove(alias)
        
        # 移除别名
        del self._aliases[alias]
        
        logger.debug(f"别名 '{alias}' 已移除")
        return True
    
    def clear(self):
        """清空所有注册的命令"""
        self._commands.clear()
        self._aliases.clear()
        self._groups.clear()
        logger.debug("命令注册中心已清空")
    
    @property
    def command_count(self) -> int:
        """获取注册的命令数量"""
        return len(self._commands)
    
    @property
    def alias_count(self) -> int:
        """获取注册的别名数量"""
        return len(self._aliases)
    
    @property
    def group_count(self) -> int:
        """获取命令分组数量"""
        return len(self._groups) 