"""
---------------------------------------------------------------
File name:                  test_happy_placeholder.py
Author:                     Ignorant-lu
Date created:               2025/05/15
Description:                "开心"状态占位符动画的单元测试
----------------------------------------------------------------

Changed history:            
                            2025/05/15: 初始创建;
----
"""
import unittest
import sys
from PySide6.QtWidgets import QApplication
from status.pet_assets.placeholders.happy_placeholder import create_animation
from status.animation.animation import Animation

class TestHappyPlaceholder(unittest.TestCase):
    """测试'开心'状态的占位符动画"""
    
    @classmethod
    def setUpClass(cls):
        """创建一个QApplication实例，确保Qt环境正确设置"""
        # 检查是否已存在QApplication实例，如果不存在则创建
        if not QApplication.instance():
            cls.app = QApplication(sys.argv)
    
    def test_create_animation_returns_animation_object(self):
        """测试create_animation返回Animation对象"""
        animation = create_animation()
        self.assertIsNotNone(animation)
        self.assertIsInstance(animation, Animation)

    def test_animation_has_frames(self):
        """测试动画有帧"""
        animation = create_animation()
        self.assertTrue(len(animation.frames) > 0)
        self.assertIsNotNone(animation.frames[0])
        
    def test_animation_metadata(self):
        """测试动画元数据"""
        animation = create_animation()
        self.assertTrue("placeholder" in animation.metadata)
        self.assertTrue(animation.metadata["placeholder"])
        self.assertTrue("description" in animation.metadata)
        
    def test_animation_name(self):
        """测试动画名称"""
        animation = create_animation()
        self.assertEqual(animation.name, "happy")

if __name__ == '__main__':
    unittest.main() 