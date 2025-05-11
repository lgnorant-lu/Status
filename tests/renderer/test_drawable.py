"""
---------------------------------------------------------------
File name:                  test_drawable.py
Author:                     Ignorant-lu
Date created:               2025/04/04
Description:                测试可绘制对象和变换
----------------------------------------------------------------

Changed history:            
                            2025/04/04: 初始创建;
----
"""

import unittest
from unittest.mock import MagicMock
import math

from status.renderer.drawable import Transform, Drawable
from status.renderer.renderer_base import RenderLayer, Rect


class TestTransform(unittest.TestCase):
    """测试变换类"""
    
    def setUp(self):
        """测试准备"""
        self.transform = Transform(x=100, y=100, rotation=45, scale_x=2.0, scale_y=1.5)
        
    def test_init(self):
        """测试初始化"""
        self.assertEqual(self.transform.x, 100)
        self.assertEqual(self.transform.y, 100)
        self.assertEqual(self.transform.rotation, 45)
        self.assertEqual(self.transform.scale_x, 2.0)
        self.assertEqual(self.transform.scale_y, 1.5)
        self.assertEqual(self.transform.origin_x, 0.0)
        self.assertEqual(self.transform.origin_y, 0.0)
        
    def test_position(self):
        """测试位置属性"""
        # 获取位置
        self.assertEqual(self.transform.position, (100, 100))
        
        # 设置位置
        self.transform.position = (200, 300)
        self.assertEqual(self.transform.x, 200)
        self.assertEqual(self.transform.y, 300)
        
        # set_position 方法
        self.transform.set_position(400, 500)
        self.assertEqual(self.transform.position, (400, 500))
        
    def test_translate(self):
        """测试平移"""
        self.transform.translate(50, 100)
        self.assertEqual(self.transform.position, (150, 200))
        
    def test_rotation(self):
        """测试旋转"""
        # 设置旋转
        self.transform.set_rotation(90)
        self.assertEqual(self.transform.rotation, 90)
        
        # 增加旋转
        self.transform.rotate(45)
        self.assertEqual(self.transform.rotation, 135)
        
    def test_scale(self):
        """测试缩放"""
        # 设置X和Y缩放
        self.transform.set_scale(3.0, 4.0)
        self.assertEqual(self.transform.scale_x, 3.0)
        self.assertEqual(self.transform.scale_y, 4.0)
        
        # 只设置X缩放（Y使用相同值）
        self.transform.set_scale(2.5)
        self.assertEqual(self.transform.scale_x, 2.5)
        self.assertEqual(self.transform.scale_y, 2.5)
        
    def test_origin(self):
        """测试原点设置"""
        self.transform.set_origin(10, 20)
        self.assertEqual(self.transform.origin_x, 10)
        self.assertEqual(self.transform.origin_y, 20)
        
    def test_apply_to_point(self):
        """测试点变换"""
        # 重置变换为简单情况
        transform = Transform(x=10, y=20, rotation=90, scale_x=2.0, scale_y=2.0)
        transform.set_origin(0, 0)
        
        # 应用变换到点(10, 0)
        # 旋转90度后，点应该在(0, 10)
        # 缩放2倍后，点应该在(0, 20)
        # 加上变换位置(10, 20)后，最终点应该在(10, 40)
        result = transform.apply_to_point(10, 0)
        self.assertAlmostEqual(result[0], 10, delta=0.001)
        self.assertAlmostEqual(result[1], 40, delta=0.001)
        
    def test_combine(self):
        """测试变换组合"""
        # 创建两个简单变换
        t1 = Transform(x=10, y=20, rotation=45, scale_x=2.0, scale_y=2.0)
        t2 = Transform(x=5, y=10, rotation=45, scale_x=1.5, scale_y=1.5)
        
        # 组合变换
        combined = t1.combine(t2)
        
        # 验证结果
        self.assertEqual(combined.x, 10 + 5 * 2.0)  # t1.x + t2.x * t1.scale_x
        self.assertEqual(combined.y, 20 + 10 * 2.0)  # t1.y + t2.y * t1.scale_y
        self.assertEqual(combined.rotation, 90)  # t1.rotation + t2.rotation
        self.assertEqual(combined.scale_x, 3.0)  # t1.scale_x * t2.scale_x
        self.assertEqual(combined.scale_y, 3.0)  # t1.scale_y * t2.scale_y


class TestDrawable(unittest.TestCase):
    """测试可绘制对象"""
    
    def setUp(self):
        """测试准备"""
        self.drawable = Drawable(x=100, y=200, width=300, height=400, layer=RenderLayer.MIDDLE, priority=5, visible=True)
        
    def test_init(self):
        """测试初始化"""
        self.assertEqual(self.drawable.x, 100)
        self.assertEqual(self.drawable.y, 200)
        self.assertEqual(self.drawable.width, 300)
        self.assertEqual(self.drawable.height, 400)
        self.assertEqual(self.drawable.scale_x, 1.0)
        self.assertEqual(self.drawable.scale_y, 1.0)
        self.assertEqual(self.drawable.rotation, 0.0)
        self.assertEqual(self.drawable.layer, RenderLayer.MIDDLE)
        self.assertEqual(self.drawable.priority, 5)
        self.assertTrue(self.drawable.visible)
        self.assertEqual(self.drawable.opacity, 1.0)
        self.assertIsNone(self.drawable.parent)
        self.assertEqual(len(self.drawable.children), 0)
        self.assertEqual(len(self.drawable.tags), 0)
        self.assertEqual(len(self.drawable.data), 0)
        
    def test_properties(self):
        """测试基本属性"""
        # 位置
        self.assertEqual(self.drawable.position, (100, 200))
        self.drawable.position = (300, 400)
        self.assertEqual(self.drawable.x, 300)
        self.assertEqual(self.drawable.y, 400)
        
        # 尺寸
        self.assertEqual(self.drawable.size, (300, 400))
        self.drawable.size = (500, 600)
        self.assertEqual(self.drawable.width, 500)
        self.assertEqual(self.drawable.height, 600)
        
        # 中心点
        self.assertEqual(self.drawable.center, (300 + 500/2, 400 + 600/2))
        
        # 矩形
        self.assertEqual(self.drawable.rect, Rect(300, 400, 500, 600))
        
    def test_parent_child(self):
        """测试父子关系"""
        # 创建父子对象
        parent = Drawable(x=10, y=20)
        child = Drawable(x=30, y=40)
        
        # 添加子对象
        parent.add_child(child)
        
        # 验证关系
        self.assertIs(child.parent, parent)
        self.assertIn(child, parent.children)
        
        # 测试世界坐标
        self.assertEqual(child.world_position, (10 + 30, 20 + 40))
        
        # 移除子对象
        result = parent.remove_child(child)
        self.assertTrue(result)
        self.assertIsNone(child.parent)
        self.assertNotIn(child, parent.children)
        
        # 尝试移除不存在的子对象
        other_child = Drawable()
        result = parent.remove_child(other_child)
        self.assertFalse(result)
        
    def test_transforms(self):
        """测试变换操作"""
        # 重新设置位置，确保测试状态一致
        self.drawable.position = (100, 200)
        
        # 设置原点
        self.drawable.set_origin(50, 60)
        self.assertEqual(self.drawable.origin_x, 50)
        self.assertEqual(self.drawable.origin_y, 60)
        
        # 设置中心原点
        self.drawable.set_center_origin()
        self.assertEqual(self.drawable.origin_x, self.drawable.width / 2)
        self.assertEqual(self.drawable.origin_y, self.drawable.height / 2)
        
        # 移动
        self.drawable.move(10, 20)
        # 移动(10, 20)后应该是(110, 220)
        self.assertEqual(self.drawable.position, (110, 220))
        
        # 旋转
        self.drawable.rotate(45)
        self.assertEqual(self.drawable.rotation, 45)
        
        self.drawable.set_rotation(90)
        self.assertEqual(self.drawable.rotation, 90)
        
        # 缩放
        self.drawable.set_scale(2.0, 3.0)
        self.assertEqual(self.drawable.scale_x, 2.0)
        self.assertEqual(self.drawable.scale_y, 3.0)
        
    def test_visibility(self):
        """测试可见性和不透明度"""
        # 设置不透明度
        self.drawable.set_opacity(0.5)
        self.assertEqual(self.drawable.opacity, 0.5)
        
        # 设置可见性
        self.drawable.set_visible(False)
        self.assertFalse(self.drawable.visible)
        
    def test_tags(self):
        """测试标签"""
        # 添加标签
        self.drawable.add_tag("test")
        self.drawable.add_tag("drawable")
        
        # 检查标签
        self.assertTrue(self.drawable.has_tag("test"))
        self.assertTrue(self.drawable.has_tag("drawable"))
        self.assertFalse(self.drawable.has_tag("missing"))
        
        # 移除标签
        self.drawable.remove_tag("test")
        self.assertFalse(self.drawable.has_tag("test"))
        self.assertTrue(self.drawable.has_tag("drawable"))
        
    def test_data(self):
        """测试自定义数据"""
        # 设置数据
        self.drawable.set_data("key1", "value1")
        self.drawable.set_data("key2", 123)
        
        # 获取数据
        self.assertEqual(self.drawable.get_data("key1"), "value1")
        self.assertEqual(self.drawable.get_data("key2"), 123)
        self.assertIsNone(self.drawable.get_data("missing"))
        self.assertEqual(self.drawable.get_data("missing", "default"), "default")
        
    def test_contains_point(self):
        """测试点包含检测"""
        # 重置对象位置和尺寸
        drawable = Drawable(x=100, y=100, width=100, height=100)
        
        # 测试包含点
        self.assertTrue(drawable.contains_point(150, 150))  # 中心点
        self.assertTrue(drawable.contains_point(100, 100))  # 左上角
        self.assertTrue(drawable.contains_point(199, 199))  # 右下角内部
        
        # 测试不包含点
        self.assertFalse(drawable.contains_point(50, 150))  # 左侧
        self.assertFalse(drawable.contains_point(150, 50))  # 上方
        self.assertFalse(drawable.contains_point(250, 150))  # 右侧
        self.assertFalse(drawable.contains_point(150, 250))  # 下方
        
    def test_draw(self):
        """测试绘制"""
        mock_renderer = MagicMock()
        self.drawable.draw(mock_renderer)
        # 基类的draw方法只是一个存根，不做任何事情
        # 所以这里只是验证调用不会抛出异常
        
    def test_update(self):
        """测试更新"""
        self.drawable.update(0.1)
        # 基类的update方法只是一个存根，不做任何事情
        # 所以这里只是验证调用不会抛出异常


if __name__ == "__main__":
    unittest.main() 