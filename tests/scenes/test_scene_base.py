"""
---------------------------------------------------------------
File name:                  test_scene_base.py
Author:                     Ignorant-lu
Date created:               2023/04/03
Description:                场景基类测试
----------------------------------------------------------------

Changed history:            
                            2023/04/03: 初始创建;
----
"""

import pytest
from unittest.mock import patch, MagicMock

from status.scenes.scene_base import SceneBase

class TestSceneBase:
    """场景基类测试用例"""

    def test_init(self):
        """测试初始化"""
        # 创建一个SceneBase的具体子类
        class ConcreteScene(SceneBase):
            def _initialize_impl(self):
                return True
            
            def _update_impl(self, delta_time, system_data):
                pass
            
            def _render_impl(self, surface):
                pass
            
            def _handle_input_impl(self, event_type, event_data):
                return False
            
            def _cleanup_impl(self):
                return True
        
        # 测试基本初始化
        scene = ConcreteScene(scene_id="test_scene", name="Test Scene")
        
        assert scene.scene_id == "test_scene"
        assert scene.name == "Test Scene"
        assert not scene.active
        assert not scene.initialized
        assert hasattr(scene, 'logger')
        assert isinstance(scene.data, dict)
        assert isinstance(scene.elements, dict)
        assert hasattr(scene, 'size')

    @patch('status.scenes.scene_base.logging')
    def test_initialize(self, mock_logging):
        """测试场景初始化"""
        # 创建一个SceneBase的具体子类，跟踪init_scene调用
        class ConcreteScene(SceneBase):
            def __init__(self, **kwargs):
                super().__init__(**kwargs)
                self.init_scene_called = False
            
            def _initialize_impl(self):
                self.init_scene_called = True
                return True
            
            def _update_impl(self, delta_time, system_data):
                pass
            
            def _render_impl(self, surface):
                pass
            
            def _handle_input_impl(self, event_type, event_data):
                return False
            
            def _cleanup_impl(self):
                return True
        
        # 创建场景并初始化
        scene = ConcreteScene(scene_id="test_scene", name="Test Scene")
        scene.initialize()
        
        # 验证初始化状态
        assert scene.initialized
        assert scene.init_scene_called
        assert mock_logging.getLogger().info.called
        
        # 测试重复初始化
        scene.init_scene_called = False
        scene.initialize()
        assert not scene.init_scene_called  # 不应再次调用init_scene
        
        # 测试初始化异常处理
        scene = ConcreteScene(scene_id="error_scene", name="Error Scene")
        scene._initialize_impl = MagicMock(side_effect=Exception("Test exception"))
        
        scene.initialize()
        assert not scene.initialized
        assert mock_logging.getLogger().error.called

    @patch('status.scenes.scene_base.logging')
    def test_activate_deactivate(self, mock_logging):
        """测试场景激活和停用"""
        # 创建一个SceneBase的具体子类
        class ConcreteScene(SceneBase):
            def _initialize_impl(self):
                return True
            
            def _update_impl(self, delta_time, system_data):
                pass
            
            def _render_impl(self, surface):
                pass
            
            def _handle_input_impl(self, event_type, event_data):
                return False
            
            def _cleanup_impl(self):
                return True
        
        # 创建场景并初始化
        scene = ConcreteScene(scene_id="test_scene", name="Test Scene")
        scene.initialize()
        
        # 测试激活
        scene.activate()
        assert scene.active
        assert mock_logging.getLogger().info.called
        
        # 测试停用
        scene.deactivate()
        assert not scene.active
        assert mock_logging.getLogger().info.called
        
        # 测试激活未初始化的场景
        scene = ConcreteScene(scene_id="uninit_scene", name="Uninitialized Scene")
        # 使用MagicMock覆盖initialize方法，使其总是返回False
        scene.initialize = MagicMock(return_value=False)
        scene.activate()
        assert not scene.active  # 不应激活未初始化的场景
        assert mock_logging.getLogger().error.called

    @patch('status.scenes.scene_base.logging')
    def test_update(self, mock_logging):
        """测试场景更新"""
        # 创建一个SceneBase的具体子类，实现update方法
        class ConcreteScene(SceneBase):
            def __init__(self, **kwargs):
                super().__init__(**kwargs)
                self.update_called = False
                self.update_dt = None
            
            def _initialize_impl(self):
                return True
            
            def _update_impl(self, delta_time, system_data):
                self.update_called = True
                self.update_dt = delta_time
            
            def _render_impl(self, surface):
                pass
            
            def _handle_input_impl(self, event_type, event_data):
                return False
            
            def _cleanup_impl(self):
                return True
        
        # 创建场景并初始化
        scene = ConcreteScene(scene_id="test_scene", name="Test Scene")
        scene.initialize()
        scene.activate()
        
        # 测试更新
        dt = 0.1
        scene.update(dt, {})
        
        # 验证更新状态
        assert scene.update_called
        assert scene.update_dt == dt
        
        # 测试非活动场景
        scene.update_called = False
        scene.deactivate()
        scene.update(dt, {})
        assert not scene.update_called  # 非活动场景不应该更新
        
        # 测试更新异常处理
        scene.activate()
        scene._update_impl = MagicMock(side_effect=Exception("Test exception"))
        scene.update(dt, {})
        assert mock_logging.getLogger().error.called

    @patch('status.scenes.scene_base.logging')
    def test_render(self, mock_logging):
        """测试场景渲染"""
        # 创建一个SceneBase的具体子类，实现render方法
        class ConcreteScene(SceneBase):
            def __init__(self, **kwargs):
                super().__init__(**kwargs)
                self.render_called = False
            
            def _initialize_impl(self):
                return True
            
            def _update_impl(self, delta_time, system_data):
                pass
            
            def _render_impl(self, surface):
                self.render_called = True
            
            def _handle_input_impl(self, event_type, event_data):
                return False
            
            def _cleanup_impl(self):
                return True
        
        # 创建场景并初始化
        scene = ConcreteScene(scene_id="test_scene", name="Test Scene")
        scene.initialize()
        scene.activate()
        
        # 测试渲染
        scene.render(None)
        
        # 验证渲染状态
        assert scene.render_called
        
        # 测试非活动场景
        scene.render_called = False
        scene.deactivate()
        scene.render(None)
        assert not scene.render_called  # 非活动场景不应该渲染
        
        # 测试渲染异常处理
        scene.activate()
        scene._render_impl = MagicMock(side_effect=Exception("Test exception"))
        scene.render(None)
        assert mock_logging.getLogger().error.called

    @patch('status.scenes.scene_base.logging')
    def test_handle_input(self, mock_logging):
        """测试场景输入处理"""
        # 创建一个SceneBase的具体子类，实现handle_input方法
        class ConcreteScene(SceneBase):
            def __init__(self, **kwargs):
                super().__init__(**kwargs)
                self.handle_input_called = False
                self.handled_event = None
            
            def _initialize_impl(self):
                return True
            
            def _update_impl(self, delta_time, system_data):
                pass
            
            def _render_impl(self, surface):
                pass
            
            def _handle_input_impl(self, event_type, event_data):
                self.handle_input_called = True
                self.handled_event = event_data
                return True
            
            def _cleanup_impl(self):
                return True
        
        # 创建场景并初始化
        scene = ConcreteScene(scene_id="test_scene", name="Test Scene")
        scene.initialize()
        scene.activate()
        
        # 测试输入处理
        test_event = {"type": "click", "position": (100, 100)}
        result = scene.handle_input("click", test_event)
        
        # 验证输入处理状态
        assert scene.handle_input_called
        assert scene.handled_event == test_event
        assert result  # 处理成功应返回True
        
        # 测试非活动场景
        scene.handle_input_called = False
        scene.deactivate()
        result = scene.handle_input("click", test_event)
        assert not scene.handle_input_called  # 非活动场景不应该处理输入
        assert not result  # 未处理应返回False
        
        # 测试输入处理异常处理
        scene.activate()
        scene._handle_input_impl = MagicMock(side_effect=Exception("Test exception"))
        scene.handle_input("click", test_event)
        assert mock_logging.getLogger().error.called

    def test_set_get_data(self):
        """测试场景数据存取"""
        # 创建一个SceneBase的具体子类
        class ConcreteScene(SceneBase):
            def _initialize_impl(self):
                return True
            
            def _update_impl(self, delta_time, system_data):
                pass
            
            def _render_impl(self, surface):
                pass
            
            def _handle_input_impl(self, event_type, event_data):
                return False
            
            def _cleanup_impl(self):
                return True
        
        # 创建场景
        scene = ConcreteScene(scene_id="test_scene", name="Test Scene")
        
        # 测试设置和获取数据
        assert scene.get_data("test_key") is None
        assert scene.get_data("test_key", "default") == "default"
        
        scene.set_data("test_key", "test_value")
        assert scene.get_data("test_key") == "test_value"
        
        # 测试覆盖数据
        scene.set_data("test_key", "new_value")
        assert scene.get_data("test_key") == "new_value"
        
        # 测试不同类型的数据
        scene.set_data("int_key", 123)
        scene.set_data("list_key", [1, 2, 3])
        scene.set_data("dict_key", {"a": 1, "b": 2})
        
        assert scene.get_data("int_key") == 123
        assert scene.get_data("list_key") == [1, 2, 3]
        assert scene.get_data("dict_key") == {"a": 1, "b": 2}

    @patch('status.scenes.scene_base.logging')
    def test_cleanup(self, mock_logging):
        """测试场景清理"""
        # 创建一个SceneBase的具体子类，跟踪cleanup调用
        class ConcreteScene(SceneBase):
            def __init__(self, **kwargs):
                super().__init__(**kwargs)
                self.cleanup_called = False
            
            def _initialize_impl(self):
                return True
            
            def _update_impl(self, delta_time, system_data):
                pass
            
            def _render_impl(self, surface):
                pass
            
            def _handle_input_impl(self, event_type, event_data):
                return False
            
            def _cleanup_impl(self):
                self.cleanup_called = True
                return True
        
        # 创建场景并初始化
        scene = ConcreteScene(scene_id="test_scene", name="Test Scene")
        scene.initialize()
        
        # 测试清理
        scene.cleanup()
        
        # 验证清理状态
        assert scene.cleanup_called
        assert not scene.initialized
        assert mock_logging.getLogger().info.called
        
        # 测试重复清理
        scene.cleanup_called = False
        scene.cleanup()
        assert not scene.cleanup_called  # 不应再次调用cleanup
        
        # 测试清理异常处理
        scene = ConcreteScene(scene_id="error_scene", name="Error Scene")
        scene.initialize()
        scene._cleanup_impl = MagicMock(side_effect=Exception("Test exception"))
        scene.cleanup()
        assert mock_logging.getLogger().error.called

    @patch('status.scenes.scene_base.logging')
    def test_resize(self, mock_logging):
        """测试场景大小调整"""
        # 创建一个SceneBase的具体子类，实现on_resize方法
        class ConcreteScene(SceneBase):
            def _initialize_impl(self):
                return True
            
            def _update_impl(self, delta_time, system_data):
                pass
            
            def _render_impl(self, surface):
                pass
            
            def _handle_input_impl(self, event_type, event_data):
                return False
            
            def _cleanup_impl(self):
                return True
            
            def on_resize(self, new_size):
                self.size = new_size
        
        # 创建场景
        scene = ConcreteScene(scene_id="test_scene", name="Test Scene")
        
        # 测试默认大小
        assert scene.get_size() == (300, 400)
        
        # 测试设置大小
        scene.set_size(800, 600)
        assert scene.get_size() == (800, 600)
        
        # 测试on_resize方法
        scene.on_resize((1024, 768))
        assert scene.get_size() == (1024, 768) 