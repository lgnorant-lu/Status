"""
---------------------------------------------------------------
File name:                  command.py
Author:                     Ignorant-lu
Date created:               2025/04/05
Description:                交互命令系统基础类和枚举定义
----------------------------------------------------------------

Changed history:            
                            2025/04/05: 初始创建;
----
"""

import logging
import time
import uuid
from enum import Enum, auto
from typing import Dict, Any, Optional, List, Callable, Union

# 配置日志
logger = logging.getLogger(__name__)

class CommandType(Enum):
    """命令类型枚举
    
    定义了系统支持的不同类型的命令。
    """
    SYSTEM = auto()      # 系统命令，如关闭、重启应用等
    APP = auto()         # 应用程序命令，如启动特定功能
    UI = auto()          # UI相关命令，如切换视图、调整大小等
    ACTION = auto()      # 动作命令，引发桌宠特定行为
    MACRO = auto()       # 宏命令，组合多个命令的序列
    CUSTOM = auto()      # 用户自定义命令
    QUERY = auto()       # 查询命令，获取系统或应用状态
    GESTURE = auto()     # 手势命令，通过特定鼠标移动触发
    VOICE = auto()       # 语音命令（未来扩展）
    SCRIPT = auto()      # 脚本命令，执行自定义脚本
    SHORTCUT = auto()    # 快捷方式，启动外部程序或URL

class CommandStatus(Enum):
    """命令状态枚举
    
    定义了命令的可能状态。
    """
    PENDING = auto()     # 待处理
    EXECUTING = auto()   # 执行中
    SUCCEEDED = auto()   # 执行成功
    FAILED = auto()      # 执行失败
    CANCELED = auto()    # 已取消
    TIMEOUT = auto()     # 执行超时
    UNAUTHORIZED = auto() # 未授权执行
    INVALID = auto()     # 命令无效

class CommandContext:
    """命令上下文类
    
    提供命令执行时的上下文信息，如发起者、环境参数等。
    
    Args:
        source (str, optional): 命令来源. 默认为None
        params (Dict[str, Any], optional): 上下文参数. 默认为None
        session_id (str, optional): 会话ID，用于跟踪相关命令. 默认为None
    """
    
    def __init__(self, source: Optional[str] = None, 
                 params: Optional[Dict[str, Any]] = None,
                 session_id: Optional[str] = None):
        """初始化命令上下文"""
        self.source = source or "unknown"
        self.params = params or {}
        self.session_id = session_id or str(uuid.uuid4())
        self.created_at = time.time()
        
        # 用于存储命令执行过程中的临时数据
        self.data = {}
    
    def get_param(self, key: str, default: Any = None) -> Any:
        """获取参数值
        
        Args:
            key: 参数键名
            default: 默认值，当键不存在时返回
            
        Returns:
            Any: 参数值或默认值
        """
        return self.params.get(key, default)
    
    def set_data(self, key: str, value: Any) -> None:
        """设置临时数据
        
        Args:
            key: 数据键名
            value: 数据值
        """
        self.data[key] = value
    
    def get_data(self, key: str, default: Any = None) -> Any:
        """获取临时数据
        
        Args:
            key: 数据键名
            default: 默认值，当键不存在时返回
            
        Returns:
            Any: 数据值或默认值
        """
        return self.data.get(key, default)
    
    def __str__(self) -> str:
        """字符串表示
        
        Returns:
            str: 上下文的字符串表示
        """
        return f"CommandContext(source={self.source}, session_id={self.session_id}, params={self.params})"

class Command:
    """命令基类
    
    表示一个可执行的命令，可以由用户输入、手势、热键等触发。
    
    Args:
        name (str): 命令名称，唯一标识
        command_type (CommandType): 命令类型
        description (str, optional): 命令描述. 默认为""
        parameters (Dict[str, Any], optional): 命令参数. 默认为None
        handler (Optional[Callable], optional): 命令处理函数. 默认为None
        enabled (bool, optional): 命令是否启用. 默认为True
    """
    
    def __init__(self, name: str, 
                 command_type: CommandType,
                 description: str = "",
                 parameters: Optional[Dict[str, Any]] = None,
                 handler: Optional[Callable] = None,
                 enabled: bool = True):
        """初始化命令"""
        self.id = str(uuid.uuid4())  # 唯一ID
        self.name = name             # 命令名称
        self.command_type = command_type  # 命令类型
        self.description = description or ""  # 命令描述
        self.parameters = parameters or {}  # 命令参数
        self.handler = handler       # 命令处理函数
        self.enabled = enabled       # 是否启用
        self.created_at = time.time()  # 创建时间
        self.last_executed = None    # 最后执行时间
        self.execution_count = 0     # 执行次数
        
        # 命令性能统计
        self.stats = {
            'avg_execution_time': 0.0,
            'total_execution_time': 0.0,
            'success_count': 0,
            'failure_count': 0
        }
    
    def execute(self, context: CommandContext) -> CommandStatus:
        """执行命令
        
        Args:
            context: 命令执行上下文
            
        Returns:
            CommandStatus: 命令执行状态
        """
        if not self.enabled:
            logger.warning(f"Command '{self.name}' is disabled, cannot execute")
            return CommandStatus.INVALID
        
        if not self.handler:
            logger.error(f"Command '{self.name}' has no handler defined")
            return CommandStatus.INVALID
        
        self.last_executed = time.time()
        self.execution_count += 1
        
        start_time = time.time()
        try:
            logger.info(f"Executing command '{self.name}' ({self.id})")
            result = self.handler(context)
            execution_time = time.time() - start_time
            
            # 更新统计信息
            self._update_stats(execution_time, True)
            
            # 处理返回值
            if isinstance(result, CommandStatus):
                return result
            elif isinstance(result, bool):
                return CommandStatus.SUCCEEDED if result else CommandStatus.FAILED
            else:
                return CommandStatus.SUCCEEDED
                
        except Exception as e:
            execution_time = time.time() - start_time
            self._update_stats(execution_time, False)
            logger.error(f"Error executing command '{self.name}': {str(e)}")
            return CommandStatus.FAILED
    
    def _update_stats(self, execution_time: float, success: bool) -> None:
        """更新命令执行统计信息
        
        Args:
            execution_time: 执行时间（秒）
            success: 是否成功执行
        """
        self.stats['total_execution_time'] += execution_time
        
        if success:
            self.stats['success_count'] += 1
        else:
            self.stats['failure_count'] += 1
        
        # 重新计算平均执行时间
        total_executions = self.stats['success_count'] + self.stats['failure_count']
        if total_executions > 0:
            self.stats['avg_execution_time'] = self.stats['total_execution_time'] / total_executions
    
    def get_usage(self) -> str:
        """获取命令使用说明
        
        Returns:
            str: 命令使用说明
        """
        usage = f"{self.name}"
        if self.parameters:
            params_str = " ".join([f"<{param}>" for param in self.parameters.keys()])
            usage += f" {params_str}"
        return usage
    
    def get_help(self) -> str:
        """获取命令帮助信息
        
        Returns:
            str: 命令帮助信息
        """
        help_text = f"{self.name}: {self.description}\n"
        help_text += f"Usage: {self.get_usage()}\n"
        
        if self.parameters:
            help_text += "Parameters:\n"
            for name, info in self.parameters.items():
                help_text += f"  {name}: {info.get('description', '')}\n"
        
        return help_text
    
    def enable(self) -> None:
        """启用命令"""
        self.enabled = True
        logger.debug(f"Command '{self.name}' enabled")
    
    def disable(self) -> None:
        """禁用命令"""
        self.enabled = False
        logger.debug(f"Command '{self.name}' disabled")
    
    def __str__(self) -> str:
        """字符串表示
        
        Returns:
            str: 命令的字符串表示
        """
        return f"Command({self.name}, type={self.command_type.name}, enabled={self.enabled})" 