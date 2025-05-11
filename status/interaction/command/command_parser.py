"""
---------------------------------------------------------------
File name:                  command_parser.py
Author:                     Ignorant-lu
Date created:               2025/04/05
Description:                命令解析器模块，负责解析用户输入的命令文本
----------------------------------------------------------------

Changed history:            
                            2025/04/05: 初始创建;
----
"""

import re
import logging
from typing import Dict, Tuple, Any, Optional, List, Set, Union
from status.interaction.command.command_types import CommandContext

# 配置日志
logger = logging.getLogger(__name__)

class CommandParser:
    """命令解析器，负责解析用户输入的命令文本"""
    
    DEFAULT_COMMAND_PREFIX = "/"
    DEFAULT_COMMENT_PREFIX = "#"
    
    def __init__(self, 
                 command_prefix: str = DEFAULT_COMMAND_PREFIX, 
                 comment_prefix: str = DEFAULT_COMMENT_PREFIX):
        """
        初始化命令解析器
        
        Args:
            command_prefix: 命令前缀，默认为"/"
            comment_prefix: 注释前缀，默认为"#"
        """
        self.command_prefix = command_prefix
        self.comment_prefix = comment_prefix
        logger.debug(f"命令解析器已初始化 (命令前缀: '{command_prefix}', 注释前缀: '{comment_prefix}')")
    
    def is_command(self, text: str) -> bool:
        """
        检查文本是否为命令
        
        Args:
            text: 要检查的文本
            
        Returns:
            是否为命令
        """
        if not text or not isinstance(text, str):
            return False
        
        # 去除前导空格
        text = text.lstrip()
        
        # 检查是否以命令前缀开头
        if not text.startswith(self.command_prefix):
            return False
        
        # 检查是否是注释
        if text.startswith(self.comment_prefix):
            return False
        
        # 检查是否仅包含命令前缀
        if len(text) <= len(self.command_prefix):
            return False
        
        return True
    
    def parse_command(self, text: str) -> Tuple[Optional[str], Dict[str, str]]:
        """
        解析命令文本，提取命令名和参数
        
        Args:
            text: 命令文本
            
        Returns:
            (命令名, 参数字典)，如果不是命令则返回(None, {})
        """
        if not self.is_command(text):
            return None, {}
        
        # 去除前导空格和命令前缀
        text = text.lstrip()[len(self.command_prefix):]
        
        # 分割命令和参数
        parts = text.split(maxsplit=1)
        command_name = parts[0].lower() if parts else ""
        
        # 如果没有参数
        if len(parts) < 2:
            return command_name, {}
        
        # 解析参数
        params_text = parts[1]
        return command_name, self._parse_params(params_text)
    
    def _parse_params(self, params_text: str) -> Dict[str, str]:
        """
        解析参数文本
        
        Args:
            params_text: 参数部分文本
            
        Returns:
            参数字典
        """
        params = {}
        
        # 正则表达式匹配参数
        # 支持以下格式:
        # 1. --param value 或 -p value
        # 2. --param=value 或 -p=value
        # 3. 位置参数(不带--或-)
        
        # 匹配带名称的参数（--param value 或 -p value 或 --param=value 或 -p=value）
        named_params_pattern = r'(?:--([a-zA-Z0-9_-]+)|-([a-zA-Z]))\s*(?:=\s*|\s+)?(\'([^\']*)\')?(\"([^\"]*)\")?([^\s\'\"]+)?'
        named_matches = re.finditer(named_params_pattern, params_text)
        
        # 收集已处理的文本范围
        processed_ranges = []
        
        # 处理命名参数
        for match in named_matches:
            start, end = match.span()
            processed_ranges.append((start, end))
            
            # 参数名（长格式或短格式）
            param_name = match.group(1) or match.group(2)
            
            # 参数值（引号或无引号）
            param_value = match.group(4) or match.group(6) or match.group(7) or "true"
            
            params[param_name] = param_value
        
        # 处理位置参数
        pos_param_index = 0
        
        # 创建一个标记已处理位置的列表
        pos_mask = [False] * len(params_text)
        for start, end in processed_ranges:
            for i in range(start, end):
                if i < len(pos_mask):
                    pos_mask[i] = True
        
        # 匹配未处理的位置参数
        pos_param_pattern = r'(\'([^\']*)\'|\"([^\"]*)\"|[^\s\'\"]+)'
        pos_matches = re.finditer(pos_param_pattern, params_text)
        
        for match in pos_matches:
            start, end = match.span()
            
            # 检查这个匹配是否已经被处理
            if all(not pos_mask[i] for i in range(start, end) if i < len(pos_mask)):
                # 参数值（引号或无引号）
                param_value = match.group(2) or match.group(3) or match.group(1)
                params[str(pos_param_index)] = param_value
                pos_param_index += 1
                
                # 标记为已处理
                for i in range(start, end):
                    if i < len(pos_mask):
                        pos_mask[i] = True
        
        return params
    
    def convert_param_value(self, value: str, expected_type: Any) -> Any:
        """
        根据期望类型转换参数值
        
        Args:
            value: 参数值（字符串）
            expected_type: 期望的类型
            
        Returns:
            转换后的参数值
        """
        if value is None:
            return None
        
        try:
            # 布尔类型
            if expected_type == bool:
                lower_value = value.lower()
                if lower_value in ('true', 'yes', 'y', '1', 'on'):
                    return True
                if lower_value in ('false', 'no', 'n', '0', 'off'):
                    return False
                return bool(value)
            
            # 整数类型
            if expected_type == int:
                return int(value)
            
            # 浮点类型
            if expected_type == float:
                return float(value)
            
            # 列表类型
            if expected_type == list:
                if not value:
                    return []
                return [item.strip() for item in value.split(',')]
            
            # 字符串类型（默认）
            return value
        except (ValueError, TypeError) as e:
            logger.warning(f"参数值转换失败: {value} -> {expected_type.__name__}，错误: {str(e)}")
            return value
    
    def create_context(self, text: str, source: str = "text") -> Optional[CommandContext]:
        """
        从命令文本创建命令上下文
        
        Args:
            text: 命令文本
            source: 命令来源，默认为"text"
            
        Returns:
            命令上下文，如果不是有效命令则返回None
        """
        command_name, params = self.parse_command(text)
        
        if not command_name:
            return None
        
        context = CommandContext(
            command_name=command_name,
            params=params,
            raw_text=text,
            source=source
        )
        
        return context
    
    def set_command_prefix(self, prefix: str):
        """
        设置命令前缀
        
        Args:
            prefix: 新的命令前缀
        """
        if prefix and isinstance(prefix, str):
            old_prefix = self.command_prefix
            self.command_prefix = prefix
            logger.debug(f"命令前缀已更改: '{old_prefix}' -> '{prefix}'")
    
    def set_comment_prefix(self, prefix: str):
        """
        设置注释前缀
        
        Args:
            prefix: 新的注释前缀
        """
        if prefix and isinstance(prefix, str):
            old_prefix = self.comment_prefix
            self.comment_prefix = prefix
            logger.debug(f"注释前缀已更改: '{old_prefix}' -> '{prefix}'")
    
    def get_command_usage(self, command_name: str, parameters: Dict[str, Dict[str, Any]]) -> str:
        """
        获取命令用法说明
        
        Args:
            command_name: 命令名
            parameters: 命令参数定义
            
        Returns:
            命令用法字符串
        """
        usage = f"{self.command_prefix}{command_name}"
        
        # 添加参数
        param_parts = []
        for param_name, param_def in parameters.items():
            is_required = param_def.get('required', False)
            has_default = 'default' in param_def
            param_desc = f"--{param_name}"
            
            if has_default:
                param_desc += f"={param_def['default']}"
                
            if is_required:
                param_parts.append(f"<{param_desc}>")
            else:
                param_parts.append(f"[{param_desc}]")
        
        if param_parts:
            usage += " " + " ".join(param_parts)
            
        return usage
    
    def get_command_help(self, command_name: str, description: str, parameters: Dict[str, Dict[str, Any]]) -> str:
        """
        获取命令帮助信息
        
        Args:
            command_name: 命令名
            description: 命令描述
            parameters: 命令参数定义
            
        Returns:
            命令帮助字符串
        """
        help_text = [
            f"命令: {self.command_prefix}{command_name}",
            f"描述: {description or '无描述'}",
            f"用法: {self.get_command_usage(command_name, parameters)}"
        ]
        
        if parameters:
            help_text.append("\n参数:")
            for param_name, param_def in parameters.items():
                param_type = param_def.get('type', str).__name__
                required = "必需" if param_def.get('required', False) else "可选"
                default = f", 默认值: {param_def.get('default')}" if 'default' in param_def else ""
                description = f" - {param_def.get('description', '无描述')}" if 'description' in param_def else ""
                
                help_text.append(f"  --{param_name} ({param_type}, {required}{default}){description}")
        
        return "\n".join(help_text) 