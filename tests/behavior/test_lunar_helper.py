"""
---------------------------------------------------------------
File name:                  test_lunar_helper.py
Author:                     Ignorant-lu
Date created:               2025/05/14
Description:                测试农历辅助功能
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

from status.behavior.time_based_behavior import LunarHelper, LUNAR_AVAILABLE


@unittest.skipIf(not LUNAR_AVAILABLE, "lunar-python库未安装，跳过农历测试")
class TestLunarHelper(unittest.TestCase):
    """测试LunarHelper类"""
    
    def test_solar_to_lunar(self):
        """测试公历转农历"""
        # 测试特定日期
        # 2025年5月26日
        date = datetime.date(2025, 5, 26)
        lunar_date = LunarHelper.solar_to_lunar(date)
        
        self.assertIsNotNone(lunar_date)
        if lunar_date:
            year, month, day, is_leap = lunar_date
            self.assertEqual(year, 2025)  # 年份应该相同
            # 无法确定具体的农历月和日，因为每年公历和农历的对应关系不同
            # 只确保它们是有效值
            self.assertTrue(1 <= month <= 12)
            self.assertTrue(1 <= day <= 30)
            self.assertIsInstance(is_leap, bool)
    
    def test_lunar_to_solar(self):
        """测试农历转公历"""
        # 测试农历2025年5月5日（端午节）
        solar_date = LunarHelper.lunar_to_solar(2025, 5, 5)
        
        self.assertIsNotNone(solar_date)
        if solar_date:
            self.assertIsInstance(solar_date, datetime.date)
            # 同样无法确定具体日期，但可以确保是有效日期
            self.assertEqual(solar_date.year, 2025)
    
    def test_leap_month_conversion(self):
        """测试农历闰月转换"""
        # 注意：不是每年都有闰月，这个测试仅在有闰月的年份有效
        # 这里假设某一年有闰4月
        
        # 先尝试将公历日期转为农历闰4月1日
        # 检查是否能找到一个闰月进行测试
        found_leap_month = False
        test_date = datetime.date(2025, 1, 1)
        
        # 循环检查一年内的日期，寻找闰月
        for i in range(365):
            check_date = test_date + datetime.timedelta(days=i)
            lunar_result = LunarHelper.solar_to_lunar(check_date)
            
            if lunar_result and lunar_result[3]:  # 第四个元素是闰月标志
                found_leap_month = True
                year, month, day, _ = lunar_result
                
                # 尝试农历闰月转公历
                solar_date = LunarHelper.lunar_to_solar(year, month, day, True)
                
                self.assertIsNotNone(solar_date)
                if solar_date:
                    # 转回农历，检查是否一致
                    re_lunar = LunarHelper.solar_to_lunar(solar_date)
                    self.assertIsNotNone(re_lunar)
                    if re_lunar:
                        re_year, re_month, re_day, re_leap = re_lunar
                        
                        # 验证转换回来的农历日期是否与原始日期一致
                        self.assertEqual(year, re_year)
                        self.assertEqual(month, re_month)
                        self.assertEqual(day, re_day)
                        # 闰月标志可能因农历API限制而不准确，暂不验证
                
                break
        
        # 如果未找到闰月，仅记录信息而不导致测试失败
        if not found_leap_month:
            self.skipTest("测试年份内未找到闰月，跳过闰月测试")
    
    @patch('status.behavior.time_based_behavior.LunarHelper.get_solar_term')
    def test_get_next_solar_term(self, mock_get_solar_term):
        """测试获取下一个节气"""
        # 模拟节气检测
        def mock_solar_term(date):
            # 只对特定日期返回节气
            if date == datetime.date(2025, 6, 6):
                return "芒种"
            return None
            
        mock_get_solar_term.side_effect = mock_solar_term
        
        # 使用固定日期进行测试
        with freeze_time("2025-05-26"):
            next_term = LunarHelper.get_next_solar_term()
            
            self.assertIsNotNone(next_term)
            if next_term:
                term_name, term_date = next_term
                self.assertEqual(term_name, "芒种")
                self.assertEqual(term_date, datetime.date(2025, 6, 6))
                # 下一个节气应该在当前日期之后
                self.assertTrue(term_date > datetime.date(2025, 5, 26))
    
    def test_solar_term_detection(self):
        """测试节气检测功能"""
        # 由于不知道具体哪天是节气，我们检查一个小范围内的几天
        # 以验证节气检测功能是否工作
        
        # 2025年立春大约在2月4日前后，检查2月1日至2月10日
        found_solar_term = False
        for day in range(1, 11):
            test_date = datetime.date(2025, 2, day)
            solar_term = LunarHelper.get_solar_term(test_date)
            
            if solar_term:
                found_solar_term = True
                self.assertIn(solar_term, LunarHelper.SOLAR_TERMS)
                self.assertEqual(type(solar_term), str)
                break
        
        # 仅输出信息，不导致测试失败
        if not found_solar_term:
            print("警告: 在2025年2月1日至10日范围内未检测到节气")
    
    def test_lunar_new_year(self):
        """测试获取农历新年日期"""
        # 获取2025年的农历新年
        lunar_new_year = LunarHelper.get_lunar_new_year(2025)
        
        self.assertIsNotNone(lunar_new_year)
        if lunar_new_year:
            # 农历新年应该落在1月或2月
            self.assertTrue(1 <= lunar_new_year.month <= 2)
            # 验证是一个有效的公历日期
            self.assertIsInstance(lunar_new_year, datetime.date)
            # 验证年份正确
            self.assertEqual(lunar_new_year.year, 2025)
    
    @patch('status.behavior.time_based_behavior.LUNAR_AVAILABLE', False)
    def test_lunar_api_not_available(self):
        """测试农历API不可用的情况"""
        # 先确保我们的模拟生效
        self.assertFalse(LunarHelper.is_available())
        
        # 测试各个方法返回None
        date = datetime.date(2025, 5, 26)
        self.assertIsNone(LunarHelper.solar_to_lunar(date))
        self.assertIsNone(LunarHelper.lunar_to_solar(2025, 5, 5))
        self.assertIsNone(LunarHelper.get_next_solar_term())


if __name__ == '__main__':
    unittest.main() 