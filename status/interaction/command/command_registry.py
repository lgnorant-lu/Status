"""
---------------------------------------------------------------
File name:                  command_registry.py
Author:                     Ignorant-lu
Date created:               2025/04/05
Description:                命令注册表，用于管理和查找命令
----------------------------------------------------------------

Changed history:            
                            2025/04/05: 初始创建;
----
"""

import logging
from typing import Dict, List, Optional, Callable, Any, Set, Tuple, Union

from status.interaction.command.command import Command, CommandType

# 配置日志
logger = logging.getLogger(__name__)

class CommandRegistry:
    """命令注册表
    
    用于注册、查找和管理交互命令。
    
    Attributes:
        commands (Dict[str, Command]): 通过名称索引的命令字典
        commands_by_id (Dict[str, Command]): 通过ID索引的命令字典
        commands_by_type (Dict[CommandType, List[Command]]): 通过类型索引的命令列表字典
    """
    
    def __init__(self):
        """初始化命令注册表"""
        self.commands = {}  # 通过名称索引
        self.commands_by_id = {}  # 通过ID索引
        self.commands_by_type = {cmd_type: [] for cmd_type in CommandType}  # 通过类型索引
        self.aliases = {}  # 命令别名字典
        self.tags = {}  # 命令标签索引
        
        logger.info("CommandRegistry initialized")
    
    def register(self, command: Command) -> bool:
        """注册命令
        
        Args:
            command: 要注册的命令
            
        Returns:
            bool: 是否成功注册
        """
        # 检查命令名称是否已存在
        if command.name in self.commands:
            logger.warning(f"Command with name '{command.name}' already exists")
            return False
        
        # 检查命令ID是否已存在
        if command.id in self.commands_by_id:
            logger.warning(f"Command with ID '{command.id}' already exists")
            return False
        
        # 注册命令
        self.commands[command.name] = command
        self.commands_by_id[command.id] = command
        self.commands_by_type[command.command_type].append(command)
        
        logger.info(f"Registered command '{command.name}' with ID '{command.id}'")
        return True
    
    def unregister(self, name_or_id: str) -> bool:
        """取消注册命令
        
        Args:
            name_or_id: 命令名称或ID
            
        Returns:
            bool: 是否成功取消注册
        """
        command = self.get(name_or_id)
        if not command:
            logger.warning(f"Command with name or ID '{name_or_id}' not found")
            return False
        
        # 从各个索引中移除命令
        if command.name in self.commands:
            del self.commands[command.name]
        
        if command.id in self.commands_by_id:
            del self.commands_by_id[command.id]
        
        if command.command_type in self.commands_by_type:
            self.commands_by_type[command.command_type].remove(command)
        
        # 移除别名
        for alias, target in list(self.aliases.items()):
            if target == command.name:
                del self.aliases[alias]
        
        # 移除标签
        for tag, cmd_list in list(self.tags.items()):
            if command in cmd_list:
                cmd_list.remove(command)
                if not cmd_list:  # 如果标签下没有命令了，移除标签
                    del self.tags[tag]
        
        logger.info(f"Unregistered command '{command.name}' with ID '{command.id}'")
        return True
    
    def get(self, name_or_id: str) -> Optional[Command]:
        """获取命令
        
        Args:
            name_or_id: 命令名称或ID
            
        Returns:
            Optional[Command]: 找到的命令或None
        """
        # 先尝试通过名称查找
        if name_or_id in self.commands:
            return self.commands[name_or_id]
        
        # 再尝试通过ID查找
        if name_or_id in self.commands_by_id:
            return self.commands_by_id[name_or_id]
        
        # 最后尝试通过别名查找
        if name_or_id in self.aliases:
            target_name = self.aliases[name_or_id]
            return self.commands.get(target_name)
        
        return None
    
    def get_by_type(self, command_type: CommandType) -> List[Command]:
        """获取指定类型的所有命令
        
        Args:
            command_type: 命令类型
            
        Returns:
            List[Command]: 命令列表
        """
        return self.commands_by_type.get(command_type, []).copy()
    
    def get_all(self) -> List[Command]:
        """获取所有命令
        
        Returns:
            List[Command]: 所有命令的列表
        """
        return list(self.commands.values())
    
    def create_alias(self, alias: str, target_name: str) -> bool:
        """创建命令别名
        
        Args:
            alias: 别名
            target_name: 目标命令名称
            
        Returns:
            bool: 是否成功创建
        """
        # 检查目标命令是否存在
        if target_name not in self.commands:
            logger.warning(f"Target command '{target_name}' not found")
            return False
        
        # 检查别名是否已存在
        if alias in self.aliases:
            logger.warning(f"Alias '{alias}' already exists")
            return False
        
        # 创建别名
        self.aliases[alias] = target_name
        logger.info(f"Created alias '{alias}' for command '{target_name}'")
        return True
    
    def remove_alias(self, alias: str) -> bool:
        """移除命令别名
        
        Args:
            alias: 要移除的别名
            
        Returns:
            bool: 是否成功移除
        """
        if alias not in self.aliases:
            logger.warning(f"Alias '{alias}' not found")
            return False
        
        target = self.aliases[alias]
        del self.aliases[alias]
        logger.info(f"Removed alias '{alias}' for command '{target}'")
        return True
    
    def tag_command(self, command_name_or_id: str, tag: str) -> bool:
        """为命令添加标签
        
        Args:
            command_name_or_id: 命令名称或ID
            tag: 标签
            
        Returns:
            bool: 是否成功添加
        """
        command = self.get(command_name_or_id)
        if not command:
            logger.warning(f"Command '{command_name_or_id}' not found")
            return False
        
        # 初始化标签列表（如果不存在）
        if tag not in self.tags:
            self.tags[tag] = []
        
        # 添加命令到标签列表
        if command not in self.tags[tag]:
            self.tags[tag].append(command)
            logger.info(f"Tagged command '{command.name}' with '{tag}'")
            return True
        
        return False
    
    def untag_command(self, command_name_or_id: str, tag: str) -> bool:
        """移除命令的标签
        
        Args:
            command_name_or_id: 命令名称或ID
            tag: 标签
            
        Returns:
            bool: 是否成功移除
        """
        command = self.get(command_name_or_id)
        if not command:
            logger.warning(f"Command '{command_name_or_id}' not found")
            return False
        
        if tag not in self.tags:
            logger.warning(f"Tag '{tag}' not found")
            return False
        
        if command in self.tags[tag]:
            self.tags[tag].remove(command)
            logger.info(f"Untagged command '{command.name}' from '{tag}'")
            
            # 如果标签下没有命令了，移除标签
            if not self.tags[tag]:
                del self.tags[tag]
            
            return True
        
        return False
    
    def get_by_tag(self, tag: str) -> List[Command]:
        """获取具有指定标签的所有命令
        
        Args:
            tag: 标签
            
        Returns:
            List[Command]: 命令列表
        """
        return self.tags.get(tag, []).copy()
    
    def get_tagged_commands(self) -> Dict[str, List[Command]]:
        """获取所有带标签的命令
        
        Returns:
            Dict[str, List[Command]]: 标签和命令列表的字典
        """
        return {tag: cmds.copy() for tag, cmds in self.tags.items()}
    
    def search(self, query: str) -> List[Command]:
        """搜索命令
        
        通过名称、描述、标签等搜索命令。
        
        Args:
            query: 搜索关键词
            
        Returns:
            List[Command]: 匹配的命令列表
        """
        query = query.lower()
        results = []
        
        for command in self.commands.values():
            # 搜索名称和描述
            if query in command.name.lower() or query in command.description.lower():
                results.append(command)
                continue
            
            # 搜索标签
            for tag, commands in self.tags.items():
                if query in tag.lower() and command in commands:
                    results.append(command)
                    break
        
        return results
    
    def has_command(self, name_or_id: str) -> bool:
        """检查是否存在指定名称或ID的命令
        
        Args:
            name_or_id: 命令名称或ID
            
        Returns:
            bool: 命令是否存在
        """
        return self.get(name_or_id) is not None
    
    def count(self) -> int:
        """获取命令总数
        
        Returns:
            int: 命令总数
        """
        return len(self.commands)
    
    def count_by_type(self, command_type: CommandType) -> int:
        """获取指定类型的命令数量
        
        Args:
            command_type: 命令类型
            
        Returns:
            int: 命令数量
        """
        return len(self.commands_by_type.get(command_type, []))
    
    def clear(self) -> None:
        """清空注册表
        
        移除所有命令、别名和标签。
        """
        self.commands.clear()
        self.commands_by_id.clear()
        self.commands_by_type = {cmd_type: [] for cmd_type in CommandType}
        self.aliases.clear()
        self.tags.clear()
        logger.info("Command registry cleared") 