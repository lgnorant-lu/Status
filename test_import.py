"""
简单的测试脚本，用于验证导入
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath('.'))
print("Python路径已添加")

# 测试导入mocks
print("测试导入mocks")
from tests.mocks import *
print("mocks导入成功")

# 测试导入environment_sensor
print("测试导入environment_sensor")
from status.behavior.environment_sensor import EnvironmentSensor, EnvironmentEvent, DesktopObject
print("environment_sensor导入成功")

# 测试导入basic_behaviors
print("测试导入basic_behaviors")
try:
    from status.behavior.basic_behaviors import BasicBehavior, BehaviorRegistry, initialize_behaviors
    print("basic_behaviors导入成功")
except Exception as e:
    print(f"basic_behaviors导入失败: {e}")

# 测试导入behavior_manager
print("测试导入behavior_manager")
try:
    from status.behavior.behavior_manager import BehaviorManager
    print("behavior_manager导入成功")
except Exception as e:
    print(f"behavior_manager导入失败: {e}")

print("测试完成") 