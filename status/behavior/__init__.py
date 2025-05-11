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
----
"""

# 版本信息
__version__ = '0.1.0'

# 定义导出模块，但不在这里导入，避免循环引用问题
# 使用lazy import模式，由需要的模块直接导入具体文件
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

# 不再直接导入模块，完全依赖延迟导入
# 从environment_sensor模块导入的内容已经被移除
