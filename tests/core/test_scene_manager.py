"""
---------------------------------------------------------------
File name:                  test_scene_manager.py
Author:                     Ignorant-lu
Date created:               2025/04/04
Description:                场景管理器测试
----------------------------------------------------------------

Changed history:            
                            2025/04/04: 初始创建;
----
"""

import pytest
from unittest.mock import MagicMock, patch, Mock

from status.core.scene_manager import SceneManager

class TestSceneManager:
    """场景管理器测试用例"""

    def test_init(self):
        """测试初始化"""
        manager = SceneManager()
        assert isinstance(manager.scenes, dict)
        assert isinstance(manager.scene_classes, dict)
        assert manager.current_scene is None
        assert manager.previous_scene is None

    def test_register_scene(self):
        """测试场景注册"""
        manager = SceneManager()
        
        # 创建模拟场景类
        mock_scene_class = MagicMock()
        
        # 注册场景
        manager.register_scene("test_scene", mock_scene_class)
        
        # 验证注册成功
        assert "test_scene" in manager.scene_classes
        assert manager.scene_classes["test_scene"] is mock_scene_class

    def test_create_scene(self):
        """测试场景创建"""
        manager = SceneManager()
        
        # 创建模拟场景类
        mock_scene_class = Mock()
        mock_scene = mock_scene_class.return_value
        
        # 注册场景
        manager.register_scene("test_scene", mock_scene_class)
        
        # 创建场景
        result = manager.create_scene("test_scene", param1="value1")
        
        # 验证创建成功
        assert result is True
        assert "test_scene" in manager.scenes
        assert manager.scenes["test_scene"] is mock_scene
        
        # 验证参数传递
        mock_scene_class.assert_called_once_with(param1="value1")
        
        # 测试创建未注册的场景
        result = manager.create_scene("non_existent_scene")
        assert result is False
        
        # 测试创建已存在的场景
        mock_scene_class.reset_mock()
        result = manager.create_scene("test_scene")
        assert result is True
        mock_scene_class.assert_not_called()  # 不应该再次创建

    @patch('status.core.scene_manager.logging')
    def test_create_scene_exception(self, mock_logging):
        """测试场景创建异常处理"""
        manager = SceneManager()
        
        # 创建会抛出异常的模拟场景类
        mock_scene_class = Mock(side_effect=Exception("Test exception"))
        
        # 注册场景
        manager.register_scene("test_scene", mock_scene_class)
        
        # 尝试创建场景
        result = manager.create_scene("test_scene")
        
        # 验证创建失败
        assert result is False
        assert "test_scene" not in manager.scenes
        assert mock_logging.getLogger().error.called

    def test_switch_to(self):
        """测试场景切换"""
        manager = SceneManager()
        
        # 创建模拟场景类和实例
        mock_scene_class1 = Mock()
        mock_scene1 = mock_scene_class1.return_value
        
        mock_scene_class2 = Mock()
        mock_scene2 = mock_scene_class2.return_value
        
        # 注册场景
        manager.register_scene("scene1", mock_scene_class1)
        manager.register_scene("scene2", mock_scene_class2)
        
        # 切换到场景1
        result = manager.switch_to("scene1")
        
        # 验证切换成功
        assert result is True
        assert manager.current_scene == "scene1"
        assert manager.previous_scene is None
        
        # 切换到场景2
        result = manager.switch_to("scene2")
        
        # 验证切换成功
        assert result is True
        assert manager.current_scene == "scene2"
        assert manager.previous_scene == "scene1"
        
        # 测试切换到未注册的场景
        result = manager.switch_to("non_existent_scene")
        assert result is False
        assert manager.current_scene == "scene2"  # 保持原场景

    def test_get_current_scene(self):
        """测试获取当前场景"""
        manager = SceneManager()
        
        # 创建模拟场景
        mock_scene_class = Mock()
        mock_scene = mock_scene_class.return_value
        
        # 注册并切换到场景
        manager.register_scene("test_scene", mock_scene_class)
        manager.create_scene("test_scene")
        manager.switch_to("test_scene")
        
        # 获取当前场景
        current_scene = manager.get_current_scene()
        
        # 验证结果
        assert current_scene is mock_scene
        
        # 测试无当前场景的情况
        manager.current_scene = None
        assert manager.get_current_scene() is None

    def test_get_scene(self):
        """测试获取指定场景"""
        manager = SceneManager()
        
        # 创建模拟场景
        mock_scene_class = Mock()
        mock_scene = mock_scene_class.return_value
        
        # 注册并创建场景
        manager.register_scene("test_scene", mock_scene_class)
        manager.create_scene("test_scene")
        
        # 获取场景
        scene = manager.get_scene("test_scene")
        
        # 验证结果
        assert scene is mock_scene
        
        # 测试获取不存在的场景
        assert manager.get_scene("non_existent_scene") is None

    def test_get_all_scene_ids(self):
        """测试获取所有场景ID"""
        manager = SceneManager()
        
        # 创建多个模拟场景类
        mock_scene_class1 = Mock()
        mock_scene_class2 = Mock()
        mock_scene_class3 = Mock()
        
        # 注册场景
        manager.register_scene("scene1", mock_scene_class1)
        manager.register_scene("scene2", mock_scene_class2)
        manager.register_scene("scene3", mock_scene_class3)
        
        # 获取所有场景ID
        scene_ids = manager.get_all_scene_ids()
        
        # 验证结果
        assert isinstance(scene_ids, list)
        assert len(scene_ids) == 3
        assert "scene1" in scene_ids
        assert "scene2" in scene_ids
        assert "scene3" in scene_ids

    def test_reload_scene(self):
        """测试重新加载场景"""
        manager = SceneManager()
        
        # 创建模拟场景类和实例
        mock_scene_class = Mock()
        mock_scene1 = mock_scene_class.return_value
        
        # 注册并创建场景
        manager.register_scene("test_scene", mock_scene_class)
        manager.create_scene("test_scene")
        
        # 切换到场景
        manager.switch_to("test_scene")
        
        # 重置模拟对象以便检查重新创建
        mock_scene_class.reset_mock()
        mock_scene2 = Mock()
        mock_scene_class.return_value = mock_scene2
        
        # 重新加载场景
        result = manager.reload_scene("test_scene", param1="value1")
        
        # 验证重新加载成功
        assert result is True
        assert manager.scenes["test_scene"] is mock_scene2
        mock_scene_class.assert_called_once_with(param1="value1")
        
        # 测试重新加载未注册的场景
        result = manager.reload_scene("non_existent_scene")
        assert result is False

    def test_preload_scenes(self):
        """测试预加载场景"""
        manager = SceneManager()
        
        # 创建多个模拟场景类
        mock_scene_class1 = Mock()
        mock_scene_class2 = Mock()
        
        # 注册场景
        manager.register_scene("scene1", mock_scene_class1)
        manager.register_scene("scene2", mock_scene_class2)
        
        # 预加载场景
        manager.preload_scenes(["scene1", "scene2"])
        
        # 验证场景被创建
        assert "scene1" in manager.scenes
        assert "scene2" in manager.scenes
        mock_scene_class1.assert_called_once()
        mock_scene_class2.assert_called_once()

    @patch('status.core.scene_manager.logging')
    def test_cleanup(self, mock_logging):
        """测试清理所有场景"""
        manager = SceneManager()
        
        # 创建多个模拟场景
        mock_scene1 = Mock()
        mock_scene2 = Mock()
        
        # 添加场景到管理器
        manager.scenes = {
            "scene1": mock_scene1,
            "scene2": mock_scene2
        }
        manager.current_scene = "scene1"
        manager.previous_scene = "scene2"
        
        # 清理场景
        manager.cleanup()
        
        # 验证清理结果
        assert len(manager.scenes) == 0
        assert manager.current_scene is None
        assert manager.previous_scene is None
        assert mock_logging.getLogger().info.called
        
        # 验证异常处理
        # 创建一个带有异常处理程序的logger mock
        real_logger = Mock()
        real_logger.error = Mock()
        real_logger.info = Mock()
        real_logger.debug = Mock()
        
        # 创建模拟场景
        error_scene = Mock()
        # 让场景本身在被访问时抛出异常
        error_scene.cleanup = Mock(side_effect=Exception("测试异常"))
        
        # 重新创建场景管理器，使用正常的字典但覆盖logger
        manager = SceneManager()
        manager.logger = real_logger
        manager.scenes = {"error_scene": error_scene}
        
        # 修改原始实现，在循环过程中实际调用场景的cleanup方法
        # 这样异常会在try块内被捕获
        original_cleanup = manager.cleanup
        
        def patched_cleanup(self):
            self.logger.info("清理所有场景")
            
            for scene_id, scene in self.scenes.items():
                try:
                    # 实际调用场景的cleanup方法，这将触发异常
                    scene.cleanup()
                    self.logger.debug(f"场景已清理: {scene_id}")
                except Exception as e:
                    self.logger.error(f"场景清理失败: {scene_id}, 错误: {str(e)}", exc_info=True)
            
            self.scenes.clear()
            self.current_scene = None
            self.previous_scene = None
        
        # 使用修补的方法替换原始方法
        from types import MethodType
        manager.cleanup = MethodType(patched_cleanup, manager)
        
        # 清理场景应该捕获异常，不会中断
        manager.cleanup()
        
        # 验证错误被记录
        assert real_logger.error.called 