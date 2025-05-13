"""
---------------------------------------------------------------
File name:                  test_special_dates.py
Author:                     Ignorant-lu
Date created:               2025/05/14
Description:                测试特殊日期功能
----------------------------------------------------------------

Changed history:            
                            2025/05/14: 初始创建;
                            2025/05/14: 添加节气检测和边界情况测试;
----
"""

import unittest
from unittest.mock import patch, MagicMock
import datetime
from freezegun import freeze_time

from status.behavior.time_based_behavior import (
    TimeBasedBehaviorSystem, 
    SpecialDate, 
    LunarHelper,
    TimePeriod,
    LUNAR_AVAILABLE
)
from status.core.event_system import EventSystem, EventType


class TestSpecialDates(unittest.TestCase):
    """测试特殊日期功能"""
    
    def setUp(self):
        """设置测试环境"""
        # 模拟事件系统
        self.patcher = patch('status.core.event_system.EventSystem')
        self.mock_event_system = self.patcher.start()
        self.mock_event_system_instance = MagicMock()
        self.mock_event_system.get_instance.return_value = self.mock_event_system_instance
        
        # 创建时间行为系统实例
        self.time_system = TimeBasedBehaviorSystem(check_interval=5)
        
        # 手动设置事件系统
        self.time_system.event_system = self.mock_event_system_instance
        
        # 创建更好的信号模拟
        mock_signals = MagicMock()
        mock_signals.time_period_changed.emit = MagicMock()
        mock_signals.special_date_triggered.emit = MagicMock()
        
        # 设置模拟信号
        self.time_system.signals = mock_signals
    
    def tearDown(self):
        """清理测试环境"""
        self.patcher.stop()
    
    def test_solar_special_date(self):
        """测试公历特殊日期"""
        # 清除已触发特殊日期
        self.time_system.reset_triggered_dates()
        
        # 添加测试用公历特殊日期（设为今天）
        today = datetime.date.today()
        test_special_date = SpecialDate.create_solar_festival(
            name="测试公历日期",
            month=today.month,
            day=today.day,
            description="测试公历描述"
        )
        self.time_system.add_special_date(test_special_date)
        
        # 检查特殊日期
        self.time_system._check_special_dates()
        
        # 验证特殊日期事件被触发
        self.time_system.signals.special_date_triggered.emit.assert_called_once()
        args, _ = self.time_system.signals.special_date_triggered.emit.call_args
        self.assertEqual(args[0], "测试公历日期")
        self.assertEqual(args[1], "测试公历描述")
    
    @unittest.skipIf(not LUNAR_AVAILABLE, "lunar-python库未安装，跳过农历测试")
    def test_lunar_special_date(self):
        """测试农历特殊日期"""
        # 清除已触发特殊日期
        self.time_system.reset_triggered_dates()
        
        # 获取今天的农历日期
        today = datetime.date.today()
        lunar_date = LunarHelper.solar_to_lunar(today)
        
        if not lunar_date:
            self.skipTest("获取农历日期失败")
            return
            
        lunar_year, lunar_month, lunar_day, is_leap = lunar_date
        
        # 添加测试用农历特殊日期（设为今天）
        test_special_date = SpecialDate.create_lunar_festival(
            name="测试农历日期",
            month=lunar_month,
            day=lunar_day,
            description="测试农历描述",
            lunar_leap_month=is_leap
        )
        self.time_system.add_special_date(test_special_date)
        
        # 检查特殊日期
        self.time_system._check_special_dates()
        
        # 验证特殊日期事件被触发
        self.time_system.signals.special_date_triggered.emit.assert_called_once()
        args, _ = self.time_system.signals.special_date_triggered.emit.call_args
        self.assertEqual(args[0], "测试农历日期")
        self.assertEqual(args[1], "测试农历描述")
    
    def test_special_date_types(self):
        """测试不同类型的特殊日期"""
        # 创建各种类型的特殊日期
        solar_festival = SpecialDate.create_solar_festival("元旦", 1, 1, "新年快乐")
        lunar_festival = SpecialDate.create_lunar_festival("春节", 1, 1, "春节快乐")
        solar_term = SpecialDate.create_solar_term("立春", 2, 4, "春天开始")
        
        # 验证类型信息
        self.assertEqual(solar_festival.date_type, SpecialDate.Type.SOLAR_FESTIVAL)
        self.assertEqual(lunar_festival.date_type, SpecialDate.Type.LUNAR_FESTIVAL)
        self.assertEqual(solar_term.date_type, SpecialDate.Type.SOLAR_TERM)
        
        # 验证是否农历标志
        self.assertFalse(solar_festival.is_lunar)
        self.assertTrue(lunar_festival.is_lunar)
        self.assertFalse(solar_term.is_lunar)
        
        # 验证字符串表示
        self.assertIn("公历节日", str(solar_festival))
        self.assertIn("农历节日", str(lunar_festival))
        self.assertIn("节气", str(solar_term))
    
    def test_initialize_special_dates(self):
        """测试特殊日期列表初始化"""
        # 初始化特殊日期
        self.time_system._initialize_special_dates()
        
        # 验证是否有特殊日期被添加
        self.assertTrue(len(self.time_system.special_dates) > 0)
        
        # 验证是否包含所有类型的特殊日期
        has_solar_festival = False
        has_lunar_festival = False
        
        for date in self.time_system.special_dates:
            if date.is_lunar:
                has_lunar_festival = True
            else:
                has_solar_festival = True
            
            if has_solar_festival and has_lunar_festival:
                break
                
        self.assertTrue(has_solar_festival, "缺少公历节日")
        self.assertTrue(has_lunar_festival, "缺少农历节日")
    
    def test_trigger_days_before(self):
        """测试提前触发特殊日期功能"""
        # 清除已触发特殊日期
        self.time_system.reset_triggered_dates()
        
        # 创建一个设置为明天的特殊日期，但设置提前1天触发
        today = datetime.date.today()
        tomorrow = today + datetime.timedelta(days=1)
        
        test_special_date = SpecialDate.create_solar_festival(
            name="提前触发测试",
            month=tomorrow.month,
            day=tomorrow.day,
            description="测试提前触发",
            trigger_days_before=1  # 提前1天触发
        )
        
        self.time_system.add_special_date(test_special_date)
        
        # 检查特殊日期
        self.time_system._check_special_dates()
        
        # 验证特殊日期事件被触发（虽然实际日期是明天，但因为设置了提前1天触发）
        self.time_system.signals.special_date_triggered.emit.assert_called_once()
        args, _ = self.time_system.signals.special_date_triggered.emit.call_args
        self.assertEqual(args[0], "提前触发测试")
        self.assertEqual(args[1], "测试提前触发")
    
    def test_custom_date_type(self):
        """测试自定义日期类型"""
        # 创建一个自定义类型的特殊日期
        custom_date = SpecialDate(
            name="自定义纪念日",
            month=6,
            day=10,
            description="测试自定义日期类型",
            is_lunar=False,
            date_type=SpecialDate.Type.CUSTOM
        )
        
        # 验证类型信息
        self.assertEqual(custom_date.date_type, SpecialDate.Type.CUSTOM)
        self.assertFalse(custom_date.is_lunar)
        
        # 验证字符串表示
        self.assertIn("自定义日期", str(custom_date))
        self.assertIn("公历", str(custom_date))
        self.assertIn("6月10日", str(custom_date))
    
    @unittest.skipIf(not LUNAR_AVAILABLE, "lunar-python库未安装，跳过农历测试")
    def test_lunar_leap_month(self):
        """测试农历闰月特殊日期
        
        注意：此测试依赖于当前年份是否有闰月，可能需要调整
        """
        # 尝试寻找今年的闰月
        # 从正月初一开始检查全年
        lunar_new_year = LunarHelper.get_lunar_new_year(datetime.date.today().year)
        
        if not lunar_new_year:
            self.skipTest("获取农历新年失败")
            return
            
        found_leap_month = False
        check_date = lunar_new_year
        
        # 检查一年内的日期，寻找闰月
        for i in range(365):
            date_to_check = check_date + datetime.timedelta(days=i)
            lunar_info = LunarHelper.solar_to_lunar(date_to_check)
            
            if lunar_info and lunar_info[3]:  # 第四个元素是闰月标志
                found_leap_month = True
                lunar_year, lunar_month, lunar_day, is_leap = lunar_info
                
                # 创建一个闰月特殊日期
                test_leap_date = SpecialDate.create_lunar_festival(
                    name="测试闰月日期",
                    month=lunar_month,
                    day=lunar_day,
                    description="测试闰月特殊日期",
                    lunar_leap_month=True
                )
                
                # 验证闰月标志
                self.assertTrue(test_leap_date.lunar_leap_month)
                self.assertTrue(test_leap_date.is_lunar)
                
                # 验证字符串表示包含闰月信息
                self.assertIn("闰月", str(test_leap_date))
                break
                
        if not found_leap_month:
            self.skipTest("当前年份没有闰月，跳过闰月测试")
    
    def test_upcoming_special_dates(self):
        """测试获取即将到来的特殊日期功能"""
        # 添加一些测试特殊日期
        today = datetime.date.today()
        
        # 添加5天后的特殊日期
        future_date = today + datetime.timedelta(days=5)
        future_special_date = SpecialDate.create_solar_festival(
            name="未来特殊日期",
            month=future_date.month,
            day=future_date.day,
            description="5天后的特殊日期"
        )
        self.time_system.add_special_date(future_special_date)
        
        # 添加25天后的特殊日期
        far_future_date = today + datetime.timedelta(days=25)
        far_future_special_date = SpecialDate.create_solar_festival(
            name="较远未来特殊日期",
            month=far_future_date.month,
            day=far_future_date.day,
            description="25天后的特殊日期"
        )
        self.time_system.add_special_date(far_future_special_date)
        
        # 添加365天后的特殊日期 (超出30天范围)
        very_far_future_date = today + datetime.timedelta(days=365)
        very_far_future_special_date = SpecialDate.create_solar_festival(
            name="很远未来特殊日期",
            month=very_far_future_date.month,
            day=very_far_future_date.day,
            description="365天后的特殊日期"
        )
        self.time_system.add_special_date(very_far_future_special_date)
        
        # 获取未来30天内的特殊日期
        upcoming_dates = self.time_system.get_upcoming_special_dates(days=30)
        
        # 验证结果
        self.assertTrue(len(upcoming_dates) >= 2)  # 至少包含我们添加的两个30天内的日期
        
        # 验证返回的数据格式和内容
        for special_date, date in upcoming_dates:
            # 验证是SpecialDate对象
            self.assertIsInstance(special_date, SpecialDate)
            # 验证是datetime.date对象 
            self.assertIsInstance(date, datetime.date)
            # 验证日期在未来30天内
            self.assertTrue(today <= date <= today + datetime.timedelta(days=30))
            
        # 验证日期排序
        for i in range(1, len(upcoming_dates)):
            self.assertTrue(upcoming_dates[i-1][1] <= upcoming_dates[i][1])
    
    @unittest.skipIf(not LUNAR_AVAILABLE, "lunar-python库未安装，跳过农历测试")
    def test_solar_term_dates(self):
        """测试节气特殊日期检测"""
        # 清除已触发特殊日期
        self.time_system.reset_triggered_dates()
        
        # 获取未来的某个节气
        next_term = LunarHelper.get_next_solar_term()
        
        if not next_term:
            self.skipTest("无法获取下一个节气")
            return
            
        term_name, term_date = next_term
        
        # 创建这个节气的特殊日期
        test_term_date = SpecialDate.create_solar_term(
            name=term_name,
            month=term_date.month,
            day=term_date.day,
            description=f"{term_name}节气测试"
        )
        
        self.time_system.add_special_date(test_term_date)
        
        # 冻结时间到节气当天
        with freeze_time(term_date.isoformat()):
            # 检查特殊日期
            self.time_system._check_special_dates()
            
            # 验证特殊日期事件被触发
            self.time_system.signals.special_date_triggered.emit.assert_called_once()
            args, _ = self.time_system.signals.special_date_triggered.emit.call_args
            self.assertEqual(args[0], term_name)
            self.assertEqual(args[1], f"{term_name}节气测试")


if __name__ == '__main__':
    unittest.main() 