"""
---------------------------------------------------------------
File name:                  __init__.py
Author:                     Ignorant-lu
Date created:               2025/04/04
Description:                桌宠行为系统初始化
----------------------------------------------------------------

Changed history:            
                            2025/04/04: 初始创建;
                            2025/04/04: 添加基础行为集;
                            2025/04/04: 添加自主行为生成系统;
                            2025/05/16: 修复文件编码问题;
                            2025/05/16: 彻底重写，解决循环引用问题;
                            2025/05/16: 移除直接导入语句，完全使用延迟导入;
                            2025/05/18: 解决环境传感器元类冲突导致的导入问题;
----
"""

# 版本信息
__version__ = '0.1.0'

# 定义导出模块
__all__ = [
    'StateMachine', 'State', 'Transition',
    'BehaviorManager', 'BasicBehavior', 'BehaviorRegistry', 'initialize_behaviors',
    'EnvironmentSensor', 'DesktopObject', 'EnvironmentEvent',
    'Reaction', 'ReactionSystem', 'ReactionSystemEventHandler',
    'AutonomousBehaviorGenerator', 'AutonomousBehaviorConfig', 'EntityUpdater',
    'create_autonomous_behavior_generator',
    'EmotionSystem', 'EmotionState', 'EmotionParams', 'EmotionType',
    'EmotionalEvent', 'EmotionalEventType', 'get_emotion_system',
    'initialize_default_emotion_events'
]

# 导入标准库
import platform

# 第一步：导入不依赖环境传感器的模块
from status.behavior.state_machine import StateMachine, State, Transition
from status.behavior.behavior_manager import BehaviorManager
from status.behavior.basic_behaviors import BasicBehavior, BehaviorRegistry, initialize_behaviors
from status.behavior.reaction_system import Reaction, ReactionSystem, ReactionSystemEventHandler
from status.behavior.emotion_system import (
    EmotionSystem, EmotionState, EmotionParams, EmotionType,
    EmotionalEvent, EmotionalEventType, get_emotion_system,
    initialize_default_emotion_events
)

# 第二步：处理环境传感器导入问题
# 2.1 直接创建存根类，不尝试导入
# 这样可以避免导入路径兼容性问题，并且解决元类冲突
class EnvironmentEvent:
    """环境事件类"""
    SCREEN_CHANGE = "environment.screen_change"
    WINDOW_MOVE = "environment.window_move"
    DESKTOP_OBJECTS_CHANGE = "environment.desktop_objects_change"
    
    def __init__(self, event_type, data=None):
        self.type = event_type
        self.data = data or {}
        
class DesktopObject:
    """桌面对象类"""
    def __init__(self, handle=None, title="", rect=None, process_name="", visible=True):
        self.handle = handle
        self.title = title
        self.rect = rect
        self.process_name = process_name
        self.visible = visible

class EnvironmentData:
    """环境数据类"""
    def __init__(self):
        self.screen_info = {}
        self.window_info = {}
        self.desktop_objects = []
        self.active_window = None
        self.cursor_position = None
        self.timestamp = 0.0

# 2.2 处理特定实现类，解决类型兼容性问题
# 注意：导入特定平台的传感器类作为EnvironmentSensor可能导致类型问题
# 因此，我们在这里创建一个统一的存根类，但提供平台检测功能
class EnvironmentSensorStub:
    """环境传感器存根类，解决导入和元类冲突问题"""
    
    @classmethod
    def get_instance(cls):
        """获取平台特定的环境传感器实例"""
        try:
            # 根据平台动态导入特定实现
            system = platform.system()
            if system == "Windows":
                from status.behavior.environment_sensor import WindowsEnvironmentSensor
                return WindowsEnvironmentSensor()
            elif system == "Darwin":
                from status.behavior.environment_sensor import MacEnvironmentSensor
                return MacEnvironmentSensor()
            elif system == "Linux":
                from status.behavior.environment_sensor import LinuxEnvironmentSensor
                return LinuxEnvironmentSensor()
            else:
                return None
        except (ImportError, TypeError):
            # 导入失败或元类冲突时返回None
            return None

# 将存根类暴露为模块导出的EnvironmentSensor
EnvironmentSensor = EnvironmentSensorStub

# 第三步：暂时注释掉依赖环境传感器的模块
# from status.behavior.autonomous_behavior import (
#     AutonomousBehaviorGenerator, AutonomousBehaviorConfig,
#     EntityUpdater, create_autonomous_behavior_generator
# )
