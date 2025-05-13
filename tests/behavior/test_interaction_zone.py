"""
---------------------------------------------------------------
File name:                  test_interaction_zone.py
Author:                     Ignorant-lu
Date created:               2025/05/13
Description:                InteractionZone单元测试
----------------------------------------------------------------

Changed history:            
                            2025/05/13: 初始创建;
----
"""

import unittest
from unittest.mock import patch, MagicMock
import math

from status.interaction.interaction_zones import (
    InteractionZone, InteractionZoneManager, 
    ZoneShape, InteractionType, Point
)


class TestInteractionZone(unittest.TestCase):
    """InteractionZone单元测试"""
    
    def setUp(self):
        """初始化测试环境"""
        # 模拟事件系统
        with patch('status.core.event_system.EventSystem') as mock_event_system:
            mock_instance = MagicMock()
            mock_event_system.get_instance.return_value = mock_instance

            # 创建测试区域
            self.circle_zone = InteractionZone(
                "test_circle",
                ZoneShape.CIRCLE,
                {"center": (100, 100), "radius": 50}
            )
            
            self.rect_zone = InteractionZone(
                "test_rect",
                ZoneShape.RECTANGLE,
                {"top_left": (200, 200), "width": 100, "height": 50}
            )
            
            self.polygon_zone = InteractionZone(
                "test_polygon",
                ZoneShape.POLYGON,
                {"points": [(300, 300), (350, 300), (350, 350), (300, 350)]}
            )
            
            self.zone_manager = InteractionZoneManager()
            
            # 设置模拟对象
            self.mock_event_system = mock_instance
            
            # 手动设置每个区域的事件系统
            self.circle_zone.event_system = self.mock_event_system
            self.rect_zone.event_system = self.mock_event_system
            self.polygon_zone.event_system = self.mock_event_system
    
    def test_circle_zone_creation(self):
        """测试圆形区域创建"""
        self.assertEqual(self.circle_zone.zone_id, "test_circle")
        self.assertEqual(self.circle_zone.shape, ZoneShape.CIRCLE)
        self.assertEqual(self.circle_zone.params["center"], (100, 100))
        self.assertEqual(self.circle_zone.params["radius"], 50)
        self.assertTrue(self.circle_zone.enabled)
        self.assertFalse(self.circle_zone.active)
    
    def test_rect_zone_creation(self):
        """测试矩形区域创建"""
        self.assertEqual(self.rect_zone.zone_id, "test_rect")
        self.assertEqual(self.rect_zone.shape, ZoneShape.RECTANGLE)
        self.assertEqual(self.rect_zone.params["top_left"], (200, 200))
        self.assertEqual(self.rect_zone.params["width"], 100)
        self.assertEqual(self.rect_zone.params["height"], 50)
    
    def test_polygon_zone_creation(self):
        """测试多边形区域创建"""
        self.assertEqual(self.polygon_zone.zone_id, "test_polygon")
        self.assertEqual(self.polygon_zone.shape, ZoneShape.POLYGON)
        self.assertEqual(len(self.polygon_zone.params["points"]), 4)
        self.assertEqual(self.polygon_zone.params["points"][0], (300, 300))
    
    def test_point_in_circle_zone(self):
        """测试点在圆形区域内的检测"""
        # 圆心点
        self.assertTrue(self.circle_zone.contains_point((100, 100)))
        
        # 圆内的点
        self.assertTrue(self.circle_zone.contains_point((120, 120)))
        
        # 圆边缘的点 (近似)
        edge_point = (100 + 50 * math.cos(math.pi/4), 100 + 50 * math.sin(math.pi/4))
        self.assertTrue(self.circle_zone.contains_point(edge_point))
        
        # 圆外的点
        self.assertFalse(self.circle_zone.contains_point((200, 200)))
        
        # 禁用区域后点在区域内也返回False
        self.circle_zone.disable()
        self.assertFalse(self.circle_zone.contains_point((100, 100)))
    
    def test_point_in_rect_zone(self):
        """测试点在矩形区域内的检测"""
        # 矩形角点
        self.assertTrue(self.rect_zone.contains_point((200, 200)))
        
        # 矩形内的点
        self.assertTrue(self.rect_zone.contains_point((250, 225)))
        
        # 矩形边缘的点
        self.assertTrue(self.rect_zone.contains_point((300, 200)))
        
        # 矩形外的点
        self.assertFalse(self.rect_zone.contains_point((350, 350)))
    
    def test_point_in_polygon_zone(self):
        """测试点在多边形区域内的检测"""
        # 多边形内的点
        self.assertTrue(self.polygon_zone.contains_point((325, 325)))
        
        # 多边形顶点
        self.assertTrue(self.polygon_zone.contains_point((300, 300)))
        
        # 多边形边上的点
        self.assertTrue(self.polygon_zone.contains_point((325, 300)))
        
        # 多边形外的点
        self.assertFalse(self.polygon_zone.contains_point((400, 400)))
    
    def test_zone_activation(self):
        """测试区域激活"""
        # 初始状态为未激活
        self.assertFalse(self.circle_zone.active)
        
        # 激活区域
        result = self.circle_zone.activate()
        self.assertTrue(result)
        self.assertTrue(self.circle_zone.active)
        
        # 应该发布了区域激活事件
        self.mock_event_system.dispatch_event.assert_called_once()
        
        # 再次激活不应该有变化
        self.mock_event_system.dispatch_event.reset_mock()
        result = self.circle_zone.activate()
        self.assertFalse(result)
        self.mock_event_system.dispatch_event.assert_not_called()
    
    def test_zone_deactivation(self):
        """测试区域停用"""
        # 先激活
        self.circle_zone.activate()
        self.assertTrue(self.circle_zone.active)
        
        # 重置mock
        self.mock_event_system.dispatch_event.reset_mock()
        
        # 停用区域
        result = self.circle_zone.deactivate()
        self.assertTrue(result)
        self.assertFalse(self.circle_zone.active)
        
        # 应该发布了区域停用事件
        self.mock_event_system.dispatch_event.assert_called_once()
        
        # 再次停用不应该有变化
        self.mock_event_system.dispatch_event.reset_mock()
        result = self.circle_zone.deactivate()
        self.assertFalse(result)
        self.mock_event_system.dispatch_event.assert_not_called()
    
    def test_zone_overlap(self):
        """测试区域重叠"""
        # 添加区域到管理器
        self.zone_manager.add_zone(self.circle_zone)
        self.zone_manager.add_zone(self.rect_zone)
        
        # 测试重叠点 (两个区域都不包含)
        no_zone_point = (0, 0)
        zones = self.zone_manager.get_zones_at_point(no_zone_point)
        self.assertEqual(len(zones), 0)
        
        # 测试重叠点 (只有圆形区域包含)
        circle_only_point = (100, 100)
        zones = self.zone_manager.get_zones_at_point(circle_only_point)
        self.assertEqual(len(zones), 1)
        self.assertEqual(zones[0].zone_id, "test_circle")
        
        # 创建一个与矩形重叠的新圆形区域
        overlap_circle = InteractionZone(
            "overlap_circle", 
            ZoneShape.CIRCLE, 
            {"center": (250, 225), "radius": 30}
        )
        self.zone_manager.add_zone(overlap_circle)
        
        # 测试重叠点 (矩形和新圆形都包含)
        overlap_point = (250, 225)
        zones = self.zone_manager.get_zones_at_point(overlap_point)
        self.assertEqual(len(zones), 2)
        zone_ids = [zone.zone_id for zone in zones]
        self.assertIn("test_rect", zone_ids)
        self.assertIn("overlap_circle", zone_ids)
    
    def test_zone_events(self):
        """测试区域事件处理"""
        # 创建测试区域
        test_zone = InteractionZone(
            "test_events",
            ZoneShape.CIRCLE,
            {"center": (150, 150), "radius": 40},
            {InteractionType.CLICK, InteractionType.HOVER}
        )
        
        # 手动设置模拟事件系统
        test_zone.event_system = self.mock_event_system

        # 验证支持的交互类型
        self.assertIn(InteractionType.CLICK, test_zone.supported_interactions)
        self.assertIn(InteractionType.HOVER, test_zone.supported_interactions)

        # 重置mock
        self.mock_event_system.dispatch_event.reset_mock()

        # 处理支持的交互类型
        result = test_zone.handle_interaction(InteractionType.CLICK, {"x": 150, "y": 150})
        self.assertTrue(result)

        # 验证事件被派发
        self.mock_event_system.dispatch_event.assert_called_once()
        
        # 重置mock
        self.mock_event_system.dispatch_event.reset_mock()
        
        # 处理不支持的交互类型
        result = test_zone.handle_interaction(InteractionType.DRAG, {"x": 150, "y": 150})
        self.assertFalse(result)
        
        # 不应该发布交互事件
        self.mock_event_system.dispatch_event.assert_not_called()
        
        # 测试交互回调
        callback_called = False
        
        def test_callback(data):
            nonlocal callback_called
            callback_called = True
            self.assertEqual(data.get("x"), 150)
            self.assertEqual(data.get("y"), 150)
        
        # 注册回调
        test_zone.register_interaction_callback(InteractionType.CLICK, test_callback)
        
        # 处理交互
        test_zone.handle_interaction(InteractionType.CLICK, {"x": 150, "y": 150})
        
        # 回调应该被调用
        self.assertTrue(callback_called)
    
    def test_zone_manager_functions(self):
        """测试区域管理器功能"""
        # 添加区域到管理器
        self.zone_manager.add_zone(self.circle_zone)
        self.zone_manager.add_zone(self.rect_zone)
        
        # 测试获取区域
        zone = self.zone_manager.get_zone("test_circle")
        self.assertEqual(zone, self.circle_zone)
        
        # 测试获取不存在的区域
        zone = self.zone_manager.get_zone("non_existent")
        self.assertIsNone(zone)
        
        # 测试激活包含点的区域
        activated = self.zone_manager.activate_zones_at_point((100, 100))
        self.assertEqual(len(activated), 1)
        self.assertEqual(activated[0], "test_circle")
        self.assertTrue(self.circle_zone.active)
        
        # 测试停用所有区域
        deactivated = self.zone_manager.deactivate_all_zones()
        self.assertEqual(len(deactivated), 1)
        self.assertEqual(deactivated[0], "test_circle")
        self.assertFalse(self.circle_zone.active)
        
        # 测试处理交互
        handled = self.zone_manager.handle_interaction((100, 100), InteractionType.CLICK)
        self.assertEqual(len(handled), 1)
        self.assertEqual(handled[0], "test_circle")
        
        # 测试移除区域
        result = self.zone_manager.remove_zone("test_circle")
        self.assertTrue(result)
        self.assertIsNone(self.zone_manager.get_zone("test_circle"))
        
        # 测试清空所有区域
        self.zone_manager.clear()
        self.assertEqual(len(self.zone_manager.zones), 0)
    
    def test_convenience_creation_methods(self):
        """测试便利创建方法"""
        # 创建圆形区域
        circle = self.zone_manager.create_circle_zone(
            "convenience_circle", 
            (50, 50), 
            20
        )
        self.assertEqual(circle.shape, ZoneShape.CIRCLE)
        self.assertEqual(circle.params["center"], (50, 50))
        self.assertEqual(circle.params["radius"], 20)
        
        # 创建矩形区域
        rect = self.zone_manager.create_rectangle_zone(
            "convenience_rect", 
            (100, 100), 
            50, 
            30
        )
        self.assertEqual(rect.shape, ZoneShape.RECTANGLE)
        self.assertEqual(rect.params["top_left"], (100, 100))
        self.assertEqual(rect.params["width"], 50)
        self.assertEqual(rect.params["height"], 30)
        
        # 创建多边形区域
        polygon = self.zone_manager.create_polygon_zone(
            "convenience_polygon", 
            [(150, 150), (200, 150), (175, 200)]
        )
        self.assertEqual(polygon.shape, ZoneShape.POLYGON)
        self.assertEqual(len(polygon.params["points"]), 3)
        
        # 验证已添加到管理器
        self.assertEqual(len(self.zone_manager.zones), 3)
        self.assertIn("convenience_circle", self.zone_manager.zones)
        self.assertIn("convenience_rect", self.zone_manager.zones)
        self.assertIn("convenience_polygon", self.zone_manager.zones)
    
    def test_invalid_parameters(self):
        """测试无效参数处理"""
        # 圆形区域缺少 radius
        with self.assertRaises(ValueError):
            InteractionZone("invalid_circle", ZoneShape.CIRCLE, {"center": (100, 100)})
        
        # 矩形区域缺少 width
        with self.assertRaises(ValueError):
            InteractionZone("invalid_rect", ZoneShape.RECTANGLE, 
                          {"top_left": (200, 200), "height": 50})
        
        # 多边形区域点数不足
        with self.assertRaises(ValueError):
            InteractionZone("invalid_polygon", ZoneShape.POLYGON, 
                          {"points": [(300, 300), (350, 300)]})


if __name__ == '__main__':
    unittest.main() 