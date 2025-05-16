"""
---------------------------------------------------------------
File name:                  test_basic_behaviors.py
Author:                     Ignorant-lu
Date created:               2025/04/04
Description:                桌宠基础行为集单元测试
----------------------------------------------------------------

Changed history:            
                            2025/04/04: 初始创建;
                            2025/05/16: 更新测试用例;
----
"""

import sys
import os
import unittest
from unittest.mock import Mock, patch, MagicMock
import time
from PySide6.QtCore import QRect, QPoint, QPointF
import math

# Add project root to sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, project_root)

from status.behavior.basic_behaviors import (
    BasicBehavior, BehaviorRegistry, IdleBehavior, MoveBehavior,
    JumpBehavior, initialize_behaviors
)
from status.behavior.environment_sensor import EnvironmentSensor


class TestBasicBehavior(unittest.TestCase):
    """测试基础行为类"""
    
    def setUp(self):
        """测试前准备"""
        # 创建一个具体的基础行为子类用于测试
        class TestBehavior(BasicBehavior):
            def __init__(self, duration=None, loop=False):
                super().__init__(name="测试行为", duration=duration, loop=loop)
                self.started = False
                self.updated = False
                self.stopped = False
                self.completed = False
                
            def _on_start(self):
                self.started = True
                
            def _on_update(self, dt):
                self.updated = True
                return True  # 返回True表示继续行为
                
            def _on_stop(self):
                self.stopped = True
                
            def _on_complete(self):
                self.completed = True
                
        self.TestBehavior = TestBehavior
        
    def test_behavior_initialization(self):
        """测试行为初始化"""
        behavior = self.TestBehavior(duration=5.0, loop=True)
        
        self.assertEqual(behavior.name, "测试行为")
        self.assertEqual(behavior.duration, 5.0)
        self.assertTrue(behavior.loop)
        self.assertFalse(behavior.is_running)
        self.assertIsNone(behavior.start_time)
        self.assertEqual(behavior.params, {})
        
    def test_behavior_start(self):
        """测试行为启动"""
        behavior = self.TestBehavior()
        behavior.start(params={"speed": 10})
        
        self.assertTrue(behavior.is_running)
        self.assertIsNotNone(behavior.start_time)
        self.assertEqual(behavior.params, {"speed": 10})
        self.assertTrue(behavior.started)
        
    def test_behavior_update(self):
        """测试行为更新"""
        behavior = self.TestBehavior(duration=1.0)
        behavior.start()
        
        # 确保行为已正确启动
        self.assertTrue(behavior.started)
        
        # 重写_on_update方法并确保它被调用
        update_called = [False]  # 使用列表以便在lambda中修改
        original_update = behavior._on_update
        
        def mock_update(dt):
            update_called[0] = True  # 标记方法被调用
            behavior.updated = True  # 设置updated标志
            return True  # 继续行为
            
        behavior._on_update = mock_update
        
        # 更新行为，时间未到
        is_completed = behavior.update(0.5)
        
        # 验证行为
        self.assertTrue(update_called[0])  # _on_update被调用
        self.assertFalse(is_completed)  # 行为未完成
        self.assertTrue(behavior.updated)  # updated标志被设置
        self.assertTrue(behavior.is_running)  # 行为仍在运行
        
        # 模拟时间已过，设置一个过去的时间点
        behavior.start_time = time.time() - 2.0
        
        # 更新行为，时间已过
        is_completed = behavior.update(0.5)
        self.assertTrue(is_completed)  # 行为应该完成
        self.assertTrue(behavior.completed)  # completed标志应该被设置
        self.assertFalse(behavior.is_running)  # 行为应该停止运行
        
    def test_behavior_loop(self):
        """测试循环行为"""
        behavior = self.TestBehavior(duration=1.0, loop=True)
        behavior.start()
        
        # 模拟时间到达或超过 duration
        assert behavior.duration is not None # Linter fix: ensure duration is not None
        behavior.start_time = time.time() - behavior.duration 
        
        # 确保 _on_update 会被调用并且返回 True (继续)
        on_update_called_in_loop = [False]
        def mock_on_update_loop(dt):
            on_update_called_in_loop[0] = True
            return True # 指示行为应该继续
        behavior._on_update = mock_on_update_loop
        
        initial_start_time = behavior.start_time
        
        # 更新行为
        # 根据新的逻辑，循环时 update() 应该返回 False (未完成，继续新循环)
        is_still_running = not behavior.update(0.5) 
        
        self.assertTrue(on_update_called_in_loop[0]) # _on_update 应在循环时被调用
        self.assertNotEqual(behavior.start_time, initial_start_time, "Start time should be reset for loop.")
        self.assertTrue(behavior.is_running, "Behavior should still be running after loop reset.")
        self.assertTrue(is_still_running, "update() should return False for a looping behavior at duration point.")
        self.assertFalse(behavior.is_complete, "Looping behavior should not be marked as complete after one cycle.")
        
    def test_behavior_stop(self):
        """测试停止行为"""
        behavior = self.TestBehavior()
        behavior.start()
        
        self.assertTrue(behavior.is_running)
        
        behavior.stop()
        
        self.assertFalse(behavior.is_running)
        self.assertTrue(behavior.stopped)
        
        # 测试未运行的行为的更新
        is_completed = behavior.update(0.5)
        self.assertTrue(is_completed)
        self.assertFalse(behavior.is_running)


class TestBehaviorRegistry(unittest.TestCase):
    """测试行为注册表"""
    
    def setUp(self):
        """测试前准备"""
        # 清除单例实例
        BehaviorRegistry._instance = None
        
        # 创建一个测试行为类
        class TestBehavior(BasicBehavior):
            def __init__(self, name="测试", duration=None, loop=False, param1=None, param2=None):
                super().__init__(name=name, duration=duration, loop=loop)
                self.param1 = param1
                self.param2 = param2
                
        self.TestBehavior = TestBehavior
        
    def test_registry_singleton(self):
        """测试注册表单例模式"""
        registry1 = BehaviorRegistry.get_instance()
        registry2 = BehaviorRegistry.get_instance()
        
        self.assertIs(registry1, registry2)
        
    def test_register_behavior(self):
        """测试注册行为"""
        registry = BehaviorRegistry.get_instance()
        
        # 注册行为
        registry.register('test', self.TestBehavior, param1="默认值")
        
        # 验证行为是否已注册
        self.assertIn('test', registry.behaviors)
        
        # 验证注册的行为类和默认参数
        behavior_class, default_params = registry.behaviors['test']
        self.assertEqual(behavior_class, self.TestBehavior)
        self.assertEqual(default_params, {'param1': '默认值'})
        
    def test_create_behavior(self):
        """测试创建行为实例"""
        registry = BehaviorRegistry.get_instance()
        
        # 注册行为
        registry.register('test', self.TestBehavior, param1="默认值")
        
        # 创建行为实例，不覆盖默认参数
        behavior1 = registry.create('test')
        assert isinstance(behavior1, self.TestBehavior) # Linter fix: assert type
        self.assertIsInstance(behavior1, self.TestBehavior)
        self.assertEqual(behavior1.param1, "默认值")
        
        # 创建行为实例，覆盖默认参数
        behavior2 = registry.create('test', param1="新值", param2="参数2")
        assert isinstance(behavior2, self.TestBehavior) # Linter fix: assert type
        self.assertIsInstance(behavior2, self.TestBehavior)
        self.assertEqual(behavior2.param1, "新值")
        self.assertEqual(behavior2.param2, "参数2")
        
    def test_create_behavior_with_params(self):
        """测试创建带参数的行为"""
        registry = BehaviorRegistry.get_instance()
        
        # 注册带默认参数的行为
        registry.register('test', self.TestBehavior, param1="默认值")
        
        # 创建行为实例，使用默认参数
        behavior1 = registry.create('test')
        assert isinstance(behavior1, self.TestBehavior) # Linter fix: assert type
        self.assertIsInstance(behavior1, self.TestBehavior)
        self.assertEqual(behavior1.param1, "默认值") # type: ignore[attr-defined]
        
        # 创建行为实例，覆盖默认参数
        behavior2 = registry.create('test', param1="新值", param2="参数2")
        assert isinstance(behavior2, self.TestBehavior) # Linter fix: assert type
        self.assertIsInstance(behavior2, self.TestBehavior)
        self.assertEqual(behavior2.param1, "新值") # type: ignore[attr-defined]
        self.assertEqual(behavior2.param2, "参数2") # type: ignore[attr-defined]
        
    def test_create_nonexistent_behavior(self):
        """测试创建不存在的行为"""
        registry = BehaviorRegistry.get_instance()
        
        with self.assertRaises(ValueError):
            registry.create('不存在的行为')
            
    def test_unregister_behavior(self):
        """测试注销行为"""
        registry = BehaviorRegistry.get_instance()
        behavior_id = "test_unregister"
        
        # 注册行为
        registry.register(behavior_id, self.TestBehavior)
        self.assertIn(behavior_id, registry.behaviors)
        
        # 注销行为
        registry.unregister(behavior_id)
        self.assertNotIn(behavior_id, registry.behaviors)
        
        # 尝试创建已注销的行为，应失败
        with self.assertRaises(ValueError):
            registry.create(behavior_id)
            
        # 尝试注销不存在的行为，应失败 (KeyError)
        with self.assertRaises(KeyError):
            registry.unregister("does_not_exist")

    def test_initialize_behaviors(self):
        """测试行为初始化函数"""
        registry = BehaviorRegistry.get_instance()
        # 清理一下，以防其他测试影响
        registry.behaviors.clear() 

        initialize_behaviors() # 调用初始化函数

        # 验证核心行为是否已注册
        self.assertIn("idle", registry.behaviors)
        self.assertIn("move", registry.behaviors)
        self.assertIn("jump", registry.behaviors)
        
        # 可以进一步验证注册的类是否正确
        idle_class, _ = registry.behaviors["idle"]
        move_class, _ = registry.behaviors["move"]
        jump_class, _ = registry.behaviors["jump"]
        
        self.assertIs(idle_class, IdleBehavior)
        self.assertIs(move_class, MoveBehavior)
        self.assertIs(jump_class, JumpBehavior)
        
        # 测试创建这些行为是否不会出错
        try:
            registry.create("idle")
            registry.create("move")
            registry.create("jump")
        except Exception as e:
            self.fail(f"initialize_behaviors registered a behavior that failed to create: {e}")

    def test_register_and_create_concrete_behaviors(self):
        """测试注册和创建具体行为子类"""
        registry = BehaviorRegistry.get_instance()
        
        # 注册移动行为
        registry.register('move_right', MoveBehavior, direction=(1, 0), speed=50)
        # 注册跳跃行为
        registry.register('high_jump', JumpBehavior, height=100, duration=0.5)
        
        # 创建移动行为
        move = registry.create('move_right')
        self.assertIsInstance(move, MoveBehavior)
        self.assertEqual(move.direction, (1, 0)) # type: ignore[attr-defined]
        
        # 创建跳跃行为
        jump = registry.create('high_jump')
        self.assertIsInstance(jump, JumpBehavior)
        self.assertEqual(jump.height, 100) # type: ignore[attr-defined]


class TestIdleBehavior(unittest.TestCase):
    """测试闲置行为"""
    
    def test_idle_behavior(self):
        """测试闲置行为基本功能"""
        behavior = IdleBehavior(animation_name="测试动画")
        
        self.assertEqual(behavior.name, "闲置")
        self.assertEqual(behavior.animation_name, "测试动画")
        self.assertTrue(behavior.loop)
        
        # 启动行为
        behavior.start()
        self.assertTrue(behavior.is_running)
        
        # 更新行为
        is_completed = behavior.update(0.1)
        self.assertFalse(is_completed)

    def test_idle_behavior_infinite_duration(self):
        """测试无固定时长的Idle行为 (应永不自行完成)"""
        idle_behavior_infinite = IdleBehavior() # duration is None by default
        self.assertIsNone(idle_behavior_infinite.duration)

        idle_behavior_infinite.start()
        self.assertTrue(idle_behavior_infinite.is_running)

        # 多次更新，行为应始终未完成
        for _ in range(10):
            is_completed = idle_behavior_infinite.update(0.1)
            self.assertFalse(is_completed, "Idle behavior with no duration should not complete on its own.")
            self.assertTrue(idle_behavior_infinite.is_running)
        
        # 验证手动停止
        idle_behavior_infinite.stop()
        self.assertFalse(idle_behavior_infinite.is_running)
        self.assertTrue(idle_behavior_infinite.is_interrupted)


class MockPetEntity:
    """一个简单的模拟宠物实体类，用于测试行为。"""
    def __init__(self, x: float, y: float, width: int, height: int): # x, y are float for QPointF
        self._x = x
        self._y = y
        self._width = width # Kept for conceptual size, though not directly used by MoveBehavior
        self._height = height # Kept for conceptual size
        # Mock any methods that behaviors might call on the entity
        self.play_animation = MagicMock() # Renamed from set_animation for consistency with code
        # get_screen_rect is on EnvironmentSensor, not entity usually
        # self.get_screen_rect = MagicMock(return_value=QRect(0,0,1920,1080)) 

    def get_position(self) -> QPointF:
        return QPointF(self._x, self._y)

    def set_position(self, x: float, y: float) -> None:
        self._x = x
        self._y = y


@patch('status.behavior.environment_sensor.EnvironmentSensor.get_instance')
class TestMoveBehavior(unittest.TestCase):
    """测试移动行为"""
    
    def setUp(self):
        """测试前准备"""
        self.mock_env_sensor = MagicMock(spec=EnvironmentSensor)
        # 模拟 get_primary_screen 方法
        primary_screen_mock_info = {
            'geometry': QRect(0, 0, 1920, 1080), # QRect for geometry
            'width': 1920,
            'height': 1080,
            'x': 0,
            'y': 0,
            'name': 'Mock Primary Screen',
            'scale_factor': 1.0,
            'primary': True
        }
        self.mock_env_sensor.get_primary_screen.return_value = primary_screen_mock_info
        # mock_get_instance will be passed to each test method by @patch

    def test_move_behavior_initialization(self, mock_get_instance):
        mock_get_instance.return_value = self.mock_env_sensor
        behavior = MoveBehavior(target_x=100, target_y=100, speed=50)
        self.assertEqual(behavior.target_x, 100)
        self.assertEqual(behavior.target_y, 100)
        self.assertEqual(behavior.speed, 50)

    def test_move_behavior_start(self, mock_get_instance):
        mock_get_instance.return_value = self.mock_env_sensor
        behavior = MoveBehavior(target_x=100, target_y=100)
        entity = MockPetEntity(0.0, 0.0, 10, 10)
        behavior.set_entity(entity)
        behavior.start()
        
        self.assertTrue(behavior.is_running)
        self.assertIsNotNone(behavior.current_position)
        if behavior.current_position: # Check if current_position is not None
            self.assertEqual(behavior.current_position.x(), 0) # Use .x() for QPointF
            self.assertEqual(behavior.current_position.y(), 0) # Use .y() for QPointF
        
        self.assertIsNotNone(behavior.target_position)
        if behavior.target_position:
            # For non-random move to target_x/y, target_position is set directly
            if not behavior.random_direction:
                self.assertEqual(behavior.target_position.x(), 100) # Use .x()
                self.assertEqual(behavior.target_position.y(), 100) # Use .y()

    def test_move_behavior_update_reaches_target(self, mock_get_instance):
        mock_get_instance.return_value = self.mock_env_sensor
        behavior = MoveBehavior(target_x=10.0, target_y=0.0, speed=100.0)
        entity = MockPetEntity(0.0, 0.0, 10, 10) # Start at (0,0)
        behavior.set_entity(entity)
        behavior.start()

        self.assertTrue(behavior.is_running)

        is_completed = behavior.update(0.05) # Move 5px to (5,0)
        self.assertFalse(is_completed, "Behavior should not be complete yet")
        self.assertTrue(behavior.is_running)
        self.assertAlmostEqual(entity.get_position().x(), 5.0, places=1)
        self.assertAlmostEqual(entity.get_position().y(), 0.0, places=1)

        is_completed = behavior.update(0.05) # Move 5px to (10,0) - target
        self.assertTrue(is_completed, "Behavior should be complete as target is reached")
        self.assertFalse(behavior.is_running)
        self.assertTrue(behavior.is_complete)
        self.assertAlmostEqual(entity.get_position().x(), 10.0, places=1)
        self.assertAlmostEqual(entity.get_position().y(), 0.0, places=1)

    def test_move_behavior_update_continues_moving(self, mock_get_instance):
        mock_get_instance.return_value = self.mock_env_sensor
        behavior = MoveBehavior(target_x=100.0, target_y=0.0, speed=50.0)
        entity = MockPetEntity(0.0, 0.0, 10, 10)
        behavior.set_entity(entity)
        behavior.start()

        is_completed = behavior.update(0.1) # Move 5px to (5,0)
        self.assertFalse(is_completed, "Behavior should not be complete, target not reached")
        self.assertTrue(behavior.is_running)
        self.assertFalse(behavior.is_complete)
        self.assertAlmostEqual(entity.get_position().x(), 5.0, places=1)

        is_completed = behavior.update(0.2) # Move 10px to (15,0)
        self.assertFalse(is_completed, "Behavior should still not be complete")
        self.assertTrue(behavior.is_running)
        self.assertAlmostEqual(entity.get_position().x(), 15.0, places=1)

    def test_random_direction(self, mock_get_instance):
        mock_get_instance.return_value = self.mock_env_sensor
        behavior = MoveBehavior(random_direction=True, speed=50)
        entity = MockPetEntity(100.0, 100.0, 10, 10) # Initial position
        behavior.set_entity(entity)
        behavior.start()
        
        self.assertTrue(behavior.random_direction)
        self.assertIsNotNone(behavior.target_position)
        current_pos = entity.get_position()
        if behavior.target_position and current_pos: # Check if target_position and current_pos are not None
            # Target should be different from current position
            self.assertTrue(behavior.target_position.x() != current_pos.x() or behavior.target_position.y() != current_pos.y())
            # Target should be within screen bounds (mocked as 0,0 to 1920,1080)
            screen_rect_dict = self.mock_env_sensor.get_primary_screen.return_value
            screen_rect = screen_rect_dict['geometry'] # Get QRect from dict
            self.assertTrue(screen_rect.contains(QPoint(int(behavior.target_position.x()), int(behavior.target_position.y()))))


@patch('status.behavior.environment_sensor.EnvironmentSensor.get_instance')
class TestJumpBehavior(unittest.TestCase):
    """测试跳跃行为"""
    
    def setUp(self):
        """测试前准备"""
        # EnvironmentSensor mock is set up by @patch, but JumpBehavior doesn't use it directly anymore.
        # We still need the mock_get_instance parameter in test methods due to the class decorator.
        self.mock_entity = MockPetEntity(x=100.0, y=200.0, width=10, height=10)
        
    def test_jump_initialization_and_start(self, mock_get_instance): # mock_get_instance is from @patch
        """测试跳跃行为的初始化和启动"""
        jump_height = 60.0
        jump_duration = 0.8
        behavior = JumpBehavior(height=jump_height, duration=jump_duration)
        
        self.assertEqual(behavior.name, "跳跃")
        self.assertEqual(behavior.height, jump_height)
        self.assertEqual(behavior.duration, jump_duration)
        self.assertFalse(behavior.is_running)
        
        behavior.set_entity(self.mock_entity)
        behavior.start()
        
        self.assertTrue(behavior.is_running)
        self.assertEqual(behavior.original_y, 200.0) # Initial Y position of mock_entity
        self.mock_entity.play_animation.assert_called_once_with('jump', loop=False)

    def test_jump_update_trajectory_and_completion(self, mock_get_instance):
        """测试跳跃轨迹和完成逻辑"""
        jump_height = 100.0
        jump_duration = 1.0 # Makes progress calculation easier: elapsed_time == progress
        behavior = JumpBehavior(height=jump_height, duration=jump_duration)
        behavior.set_entity(self.mock_entity)
        initial_x = self.mock_entity.get_position().x()
        initial_y = self.mock_entity.get_position().y()
        
        behavior.start()
        self.assertTrue(behavior.is_running)

        # Test at quarter point (going up)
        # elapsed_time will be 0.25 after this update
        is_completed = behavior.update(0.25) 
        self.assertFalse(is_completed, "Jump should not be complete at 1/4 time")
        expected_y_offset_quarter = jump_height * math.sin(0.25 * math.pi) # sin(pi/4) = sqrt(2)/2 ~= 0.707
        self.assertAlmostEqual(self.mock_entity.get_position().y(), initial_y - expected_y_offset_quarter, places=5)
        self.assertEqual(self.mock_entity.get_position().x(), initial_x) # X should not change

        # Test at half point (peak of jump)
        # elapsed_time will be 0.25 + 0.25 = 0.5 after this update
        is_completed = behavior.update(0.25) 
        self.assertFalse(is_completed, "Jump should not be complete at 1/2 time (peak)")
        self.assertAlmostEqual(self.mock_entity.get_position().y(), initial_y - jump_height, places=5) # At peak
        
        # Test at three-quarters point (going down)
        # elapsed_time will be 0.5 + 0.25 = 0.75 after this update
        is_completed = behavior.update(0.25) 
        self.assertFalse(is_completed, "Jump should not be complete at 3/4 time")
        expected_y_offset_three_quarters = jump_height * math.sin(0.75 * math.pi) # sin(3pi/4) = sqrt(2)/2 ~= 0.707
        self.assertAlmostEqual(self.mock_entity.get_position().y(), initial_y - expected_y_offset_three_quarters, places=5)

        # Test at full duration (completion)
        # elapsed_time will be 0.75 + 0.25 = 1.0 after this update
        # BehaviorBase.update will call _on_update, which returns False (arc complete). Then BehaviorBase.update itself returns True (duration met).
        is_completed_by_base = behavior.update(0.25) 
        self.assertTrue(is_completed_by_base, "Jump should be complete at full duration")
        self.assertFalse(behavior.is_running)
        self.assertTrue(behavior.is_complete)
        # _on_complete should have reset the position to original_y
        self.assertAlmostEqual(self.mock_entity.get_position().y(), initial_y, places=5)

    def test_jump_zero_duration(self, mock_get_instance):
        """测试零秒持续时间的跳跃 (应立即完成)"""
        behavior = JumpBehavior(height=50.0, duration=0.0)
        behavior.set_entity(self.mock_entity)
        initial_y = self.mock_entity.get_position().y()

        behavior.start()
        self.assertTrue(behavior.is_running) # Starts running

        # First update should complete it
        is_completed = behavior.update(0.01) # dt doesn't matter much here
        self.assertTrue(is_completed, "Jump with 0 duration should complete on first update")
        self.assertFalse(behavior.is_running)
        self.assertTrue(behavior.is_complete)
        self.assertAlmostEqual(self.mock_entity.get_position().y(), initial_y, places=5) # Should be back to original Y


@patch('status.behavior.environment_sensor.EnvironmentSensor.get_instance')
class TestBehaviorIntegration(unittest.TestCase):
    """测试行为系统集成"""
    
    def setUp(self):
        """测试前准备"""
        # 清除单例实例
        BehaviorRegistry._instance = None
        
        # 初始化行为注册表
        initialize_behaviors()
        
        # 模拟环境感知器
        self.mock_env_sensor = Mock(spec=EnvironmentSensor)
        self.mock_env_sensor.get_window_position.return_value = QRect(100, 100, 50, 50)
        self.mock_env_sensor.get_screen_boundaries.return_value = {
            'x': 0, 'y': 0, 'width': 1920, 'height': 1080
        }
        
    def test_behavior_creation_from_registry(self, mock_get_instance):
        """测试从注册表创建行为"""
        mock_get_instance.return_value = self.mock_env_sensor
        
        registry = BehaviorRegistry.get_instance()
        
        # 创建闲置行为
        idle = registry.create('idle')
        self.assertIsInstance(idle, IdleBehavior)
        
        # 创建移动行为
        move = registry.create('move_right')
        assert isinstance(move, MoveBehavior) # Linter fix
        self.assertIsInstance(move, MoveBehavior)
        self.assertEqual(move.direction, (1, 0))
        
        # 创建跳跃行为
        jump = registry.create('high_jump')
        assert isinstance(jump, JumpBehavior) # Linter fix
        self.assertIsInstance(jump, JumpBehavior)
        self.assertEqual(jump.height, 100)
        
    def test_behavior_execution_sequence(self, mock_get_instance):
        """测试行为执行序列"""
        mock_get_instance.return_value = self.mock_env_sensor
        
        registry = BehaviorRegistry.get_instance()
        
        # 创建行为序列
        idle = registry.create('idle', duration=1.0, loop=False)
        move = registry.create('move_right')
        jump = registry.create('jump')
        
        # 执行闲置行为
        idle.start()
        self.assertTrue(idle.is_running)
        
        # 模拟时间经过，行为完成
        idle.start_time = time.time() - 2.0
        is_completed = idle.update(0.1)
        self.assertTrue(is_completed)
        self.assertFalse(idle.is_running)
        
        # 执行移动行为
        move.start()
        self.assertTrue(move.is_running)
        
        # 停止移动行为，执行跳跃行为
        move.stop()
        self.assertFalse(move.is_running)
        
        jump.start()
        self.assertTrue(jump.is_running)


if __name__ == '__main__':
    unittest.main() 