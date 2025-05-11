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
----
"""

# 版本信息
__version__ = '0.1.0'

# 导出状态机模块
from status.behavior.state_machine import StateMachine, State, Transition

# 导出行为管理器模块
from status.behavior.behavior_manager import BehaviorManager

# 导出基础行为模块
from status.behavior.basic_behaviors import BasicBehavior, BehaviorRegistry, initialize_behaviors

# 导出决策系统模块
from status.behavior.decision_maker import (
    Decision,
    DecisionRule,
    DecisionMaker
)

# 导出环境感知模块
from status.behavior.environment_sensor import EnvironmentSensor, DesktopObject, EnvironmentEvent

# 导出反应系统模块
from status.behavior.reaction_system import Reaction, ReactionSystem, ReactionSystemEventHandler

# 导出自主行为生成系统模块
from status.behavior.autonomous_behavior import (
    AutonomousBehaviorGenerator,
    AutonomousBehaviorConfig,
    EntityUpdater,
    create_autonomous_behavior_generator
)

# 导出情绪系统模块
from status.behavior.emotion_system import (
    EmotionSystem,
    EmotionState,
    EmotionParams,
    EmotionType,
    EmotionalEvent,
    EmotionalEventType,
    get_emotion_system,
    initialize_default_emotion_events
)

# 导出下级模块
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
