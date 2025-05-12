"""
---------------------------------------------------------------
File name:                  types.py
Author:                     Ignorant-lu
Date created:               2025/05/12
Description:                通用类型定义模块
----------------------------------------------------------------

Changed history:            
                            2025/05/12: 初始创建;
----
"""

from typing import Dict, List, Any, Optional, Union, Tuple, Callable, TypeVar, Generic, Protocol, Set
from pathlib import Path
import os

# 通用类型别名
PathLike = Union[str, os.PathLike, Path]
JSON = Dict[str, Any]  # JSON 对象
JSONLike = Union[Dict[str, Any], List[Any], str, int, float, bool, None]  # JSON 值
Numeric = Union[int, float]

# 事件相关类型
EventType = str
EventData = Dict[str, Any]
EventHandler = Callable[[EventType, EventData], None]
EventPredicate = Callable[[EventType, EventData], bool]

# 资源相关类型
ResourceID = str
ResourcePath = str
ResourceContent = bytes
ResourceMetadata = Dict[str, Any]

# 配置相关类型
ConfigKey = str
ConfigValue = Union[str, int, float, bool, List[Any], Dict[str, Any], None]
ConfigDict = Dict[str, ConfigValue]

# 行为系统类型
StateID = str
BehaviorID = str
BehaviorParams = Dict[str, Any]
BehaviorPredicate = Callable[[], bool]

# 通用回调类型
T = TypeVar('T')
R = TypeVar('R')
Callback = Callable[[], None]
CallbackWithArg = Callable[[T], None]
CallbackWithReturn = Callable[[], R]
CallbackWithArgAndReturn = Callable[[T], R]

# 几何类型
Position = Tuple[float, float]
Size = Tuple[float, float]
Rectangle = Tuple[float, float, float, float]  # x, y, width, height
Color = Tuple[int, int, int, int]  # RGBA

# 状态类型
class Initializable(Protocol):
    """可初始化对象协议"""
    def initialize(self) -> bool:
        """初始化对象
        
        Returns:
            bool: 是否初始化成功
        """
        ...

class Disposable(Protocol):
    """可释放资源对象协议"""
    def shutdown(self) -> bool:
        """释放对象资源
        
        Returns:
            bool: 是否释放成功
        """
        ...

class SingletonType(type):
    """单例元类，用于创建单例类"""
    _instances: Dict[type, Any] = {}
    
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(SingletonType, cls).__call__(*args, **kwargs)
        return cls._instances[cls] 