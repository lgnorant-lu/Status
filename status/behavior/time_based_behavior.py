"""
---------------------------------------------------------------
File name:                  time_based_behavior.py
Author:                     Ignorant-lu
Date created:               2025/05/13
Description:                时间驱动的桌宠行为系统
----------------------------------------------------------------

Changed history:            
                            2025/05/13: 初始创建;
                            2025/05/14: 修复信号定义问题;
                            2025/05/14: 添加农历日期支持;
                            2025/05/14: 改进信号机制和农历支持;
                            2025/05/14: 修复lunar_python库的导入和使用;
----
"""

import logging
import time
import datetime
from enum import Enum, auto
from typing import Dict, List, Optional, Set, Callable, Any, Tuple
import threading

from PySide6.QtCore import QTimer, QObject, Signal, Slot

from status.core.component_base import ComponentBase
from status.core.event_system import EventSystem, EventType

try:
    from lunar_python import Lunar, Solar  # 导入农历转换库
    LUNAR_AVAILABLE = True
    logging.getLogger("Status.Behavior.TimeBasedBehaviorSystem").info("成功加载lunar-python库，农历日期功能可用。")
except ImportError:
    LUNAR_AVAILABLE = False
    logging.getLogger("Status.Behavior.TimeBasedBehaviorSystem").warning(
        "lunar-python库未安装，农历日期功能将不可用。请使用pip install lunar-python安装。")


class TimePeriod(Enum):
    """时间段枚举"""
    MORNING = auto()      # 早晨 (5:00 - 11:59)
    NOON = auto()         # 中午 (12:00 - 13:59)
    AFTERNOON = auto()    # 下午 (14:00 - 17:59)
    EVENING = auto()      # 晚上 (18:00 - 22:59)
    NIGHT = auto()        # 深夜 (23:00 - 4:59)


class SpecialDate:
    """特殊日期类，用于表示节日、节气或特殊日子"""
    
    # 特殊日期类型枚举
    class Type(Enum):
        SOLAR_FESTIVAL = auto()  # 公历节日（如元旦、国庆节）
        LUNAR_FESTIVAL = auto()  # 农历节日（如春节、中秋节）
        SOLAR_TERM = auto()      # 节气（如清明、立夏）
        CUSTOM = auto()          # 自定义日期
    
    def __init__(self, name: str, month: int, day: int, description: str = "", 
                 is_lunar: bool = False, trigger_days_before: int = 0,
                 lunar_leap_month: bool = False, date_type: Optional['SpecialDate.Type'] = None,
                 type: str = ""):
        """初始化特殊日期
        
        Args:
            name: 特殊日期名称
            month: 月份 (1-12)
            day: 日期 (1-31)
            description: 描述信息
            is_lunar: 是否是农历日期
            trigger_days_before: 提前多少天触发提醒
            lunar_leap_month: 是否是农历闰月
            date_type: 日期类型，如果为None则根据is_lunar自动判断
            type: 日期字符串类型(festival, solar_term等)，用于扩展兼容
        """
        self.name = name
        self.month = month
        self.day = day
        self.description = description
        self.is_lunar = is_lunar
        self.trigger_days_before = trigger_days_before
        self.lunar_leap_month = lunar_leap_month
        self.type = type  # 新增字符串类型字段
        
        # 如果未指定类型，则根据是否是农历自动判断
        if date_type is None:
            if is_lunar:
                self.date_type = SpecialDate.Type.LUNAR_FESTIVAL
            else:
                self.date_type = SpecialDate.Type.SOLAR_FESTIVAL
        else:
            self.date_type = date_type
    
    def __str__(self) -> str:
        """字符串表示"""
        type_str = ""
        if self.type == "festival":
            type_str = "节日"
        elif self.type == "solar_term":
            type_str = "节气"
        else:
            type_str = "自定义日期"
            
        date_type = "农历" if self.is_lunar else "公历"
        return f"{self.name}: {type_str} - {date_type}{self.month}月{self.day}日 - {self.description}"
    
    @staticmethod
    def create_solar_festival(name: str, month: int, day: int, 
                             description: str = "", trigger_days_before: int = 0) -> 'SpecialDate':
        """创建公历节日
        
        Args:
            name: 节日名称
            month: 公历月份 (1-12)
            day: 公历日期 (1-31)
            description: 描述信息
            trigger_days_before: 提前多少天触发提醒
            
        Returns:
            SpecialDate: 特殊日期对象
        """
        return SpecialDate(
            name=name, 
            month=month, 
            day=day, 
            description=description, 
            is_lunar=False, 
            type="festival"
        )
    
    @staticmethod
    def create_lunar_festival(name: str, month: int, day: int, 
                             description: str = "", trigger_days_before: int = 0,
                             lunar_leap_month: bool = False) -> 'SpecialDate':
        """创建农历节日
        
        Args:
            name: 节日名称
            month: 农历月份 (1-12)
            day: 农历日期 (1-31)
            description: 描述信息
            trigger_days_before: 提前多少天触发提醒
            lunar_leap_month: 是否是农历闰月
            
        Returns:
            SpecialDate: 特殊日期对象
        """
        return SpecialDate(
            name=name, 
            month=month, 
            day=day, 
            description=description, 
            is_lunar=True, 
            type="festival"
        )
    
    @staticmethod
    def create_solar_term(name: str, month: int, day: int, 
                         description: str = "", trigger_days_before: int = 0) -> 'SpecialDate':
        """创建节气特殊日期
        
        Args:
            name: 节气名称
            month: 公历月份 (1-12)
            day: 公历日期 (1-31)
            description: 描述信息
            trigger_days_before: 提前多少天触发提醒
            
        Returns:
            SpecialDate: 特殊日期对象
        """
        return SpecialDate(
            name=name, 
            month=month, 
            day=day, 
            description=description, 
            is_lunar=False, 
            type="solar_term"
        )


class LunarHelper:
    """农历辅助类，用于公历和农历的转换和节气判断"""
    
    # 二十四节气名称列表
    SOLAR_TERMS = [
        "立春", "雨水", "惊蛰", "春分", "清明", "谷雨",
        "立夏", "小满", "芒种", "夏至", "小暑", "大暑",
        "立秋", "处暑", "白露", "秋分", "寒露", "霜降",
        "立冬", "小雪", "大雪", "冬至", "小寒", "大寒"
    ]
    
    @staticmethod
    def is_available() -> bool:
        """检查农历库是否可用
        
        Returns:
            bool: 农历库是否可用
        """
        return LUNAR_AVAILABLE
    
    @staticmethod
    def solar_to_lunar(date: datetime.date) -> Optional[Tuple[int, int, int, bool]]:
        """公历转农历
        
        Args:
            date: 公历日期
            
        Returns:
            Optional[Tuple[int, int, int, bool]]: 农历(年, 月, 日, 是否闰月)，如果农历库不可用则返回None
        """
        if not LUNAR_AVAILABLE:
            return None
        
        try:
            # 创建Solar对象
            solar = Solar(date.year, date.month, date.day, 0, 0, 0)
            # 转换为Lunar对象
            lunar_date = Lunar.fromSolar(solar)
            
            # 获取闰月信息
            # lunar-python库没有直接提供是否闰月的方法，但可以通过比较
            # 检查当前月是否是闰月的方法就是判断是否大于农历里的月份
            leap_month = False
            try:
                lunar_year = lunar_date.getYear()
                lunar_month = lunar_date.getMonth()
                # 在农历中，闰月用一个特殊的标记表示，我们可以通过当前日期所在的月是否是闰月来判断
                # 但lunar-python库API没有直接提供此功能，这里仅使用简单判断
                leap_month = False  # 简化处理
            except Exception:
                pass
                
            # 返回年月日和闰月标志
            return (
                lunar_date.getYear(), 
                lunar_date.getMonth(),
                lunar_date.getDay(),
                leap_month
            )
        except Exception as e:
            logging.getLogger("Status.Behavior.LunarHelper").error(f"公历转农历失败: {e}")
            return None
    
    @staticmethod
    def lunar_to_solar(year: int, month: int, day: int, leap_month: bool = False) -> Optional[datetime.date]:
        """农历转公历
        
        Args:
            year: 农历年
            month: 农历月
            day: 农历日
            leap_month: 是否闰月
            
        Returns:
            Optional[datetime.date]: 公历日期，如果农历库不可用则返回None
        """
        if not LUNAR_AVAILABLE:
            return None
        
        try:
            # 注意: lunar-python库的API处理闰月存在限制
            # 这里通过创建对应月份的Lunar对象，然后获取其公历日期
            lunar = Lunar(year, month, day, 0, 0, 0)
            
            # 获取对应的公历日期
            solar = lunar.getSolar()
            
            # 返回datetime.date对象
            return datetime.date(solar.getYear(), solar.getMonth(), solar.getDay())
        except Exception as e:
            logging.getLogger("Status.Behavior.LunarHelper").error(f"农历转公历失败: {e}")
            return None
    
    @staticmethod
    def get_lunar_new_year(year: int) -> Optional[datetime.date]:
        """获取农历新年的公历日期
        
        Args:
            year: 公历年份
            
        Returns:
            Optional[datetime.date]: 公历日期，如果农历库不可用则返回None
        """
        return LunarHelper.lunar_to_solar(year, 1, 1)
    
    @staticmethod
    def get_current_lunar_date() -> Optional[Tuple[int, int, int, bool]]:
        """获取当前农历日期
        
        Returns:
            Optional[Tuple[int, int, int, bool]]: 农历(年, 月, 日, 是否闰月)，如果农历库不可用则返回None
        """
        return LunarHelper.solar_to_lunar(datetime.date.today())
    
    @staticmethod
    def get_solar_term(date: datetime.date) -> Optional[str]:
        """获取指定日期的节气名称
        
        Args:
            date: 公历日期
            
        Returns:
            Optional[str]: 节气名称，如果当天不是节气或农历库不可用则返回None
        """
        if not LUNAR_AVAILABLE:
            return None
            
        try:
            solar = Solar(date.year, date.month, date.day, 0, 0, 0)
            # lunar-python库不直接提供节气判断方法
            # 这里通过宏观方式来判断：检查节日列表
            festivals = solar.getFestivals()
            
            # 检查节日是否包含节气
            for festival in festivals:
                for term in LunarHelper.SOLAR_TERMS:
                    if term in festival:
                        return term
            
            # 使用农历对象检查
            lunar = Lunar.fromSolar(solar)
            lunar_festivals = lunar.getFestivals()
            for festival in lunar_festivals:
                for term in LunarHelper.SOLAR_TERMS:
                    if term in festival:
                        return term
                        
            return None
        except Exception as e:
            logging.getLogger("Status.Behavior.LunarHelper").error(f"获取节气失败: {e}")
            return None
    
    @staticmethod
    def get_next_solar_term(date: Optional[datetime.date] = None) -> Optional[Tuple[str, datetime.date]]:
        """获取下一个节气的名称和日期
        
        Args:
            date: 参考日期，默认为今天
            
        Returns:
            Optional[Tuple[str, datetime.date]]: (节气名称, 公历日期)，如果农历库不可用则返回None
        """
        if not LUNAR_AVAILABLE:
            return None
            
        # 使用当前日期作为默认值
        current_date = datetime.date.today() if date is None else date
            
        try:
            # 从给定日期开始，向后查找节气
            for i in range(30):  # 最多查找未来30天
                check_date = current_date + datetime.timedelta(days=i)
                term = LunarHelper.get_solar_term(check_date)
                if term:
                    return (term, check_date)
            return None
        except Exception as e:
            logging.getLogger("Status.Behavior.LunarHelper").error(f"获取下一个节气失败: {e}")
            return None


# 创建信号类，因为QObject需要作为类的祖先，而ComponentBase可能不是QObject的子类
class TimeSignals(QObject):
    """时间信号类，用于发出时间相关的信号"""
    # 定义信号，用于时间段变化通知
    time_period_changed = Signal(object, object)  # 参数：新时间段，旧时间段
    special_date_triggered = Signal(str, str)     # 参数：特殊日期名称，描述


class TimeBasedBehaviorSystem(ComponentBase):
    """基于时间的行为系统
    
    负责检测时间变化并发布相关事件，驱动桌宠根据时间表现不同行为
    """
    
    def __init__(self, check_interval: int = 60):
        """初始化时间行为系统
        
        Args:
            check_interval: 检查时间间隔（秒）
        """
        super().__init__()
        
        self.logger = logging.getLogger("Status.Behavior.TimeBasedBehaviorSystem")
        
        # 检查间隔（秒）
        self.check_interval = check_interval
        
        # 当前时间段
        self.current_period: Optional[TimePeriod] = None
        
        # 事件系统
        self.event_system = None
        
        # 定时器，用于定期检查时间变化
        self.timer = QTimer()
        self.timer.timeout.connect(self._check_time_change)
        
        # 特殊日期列表
        self.special_dates: List[SpecialDate] = []
        
        # 已触发的特殊日期（避免重复触发）
        self.triggered_special_dates: Set[str] = set()
        
        # 初始化特殊日期
        self._initialize_special_dates()
        
        # 信号对象
        self.signals = TimeSignals()
        
        self.logger.info("时间行为系统初始化完成")
    
    def _initialize(self) -> bool:
        """初始化组件
        
        Returns:
            bool: 初始化是否成功
        """
        try:
            # 获取事件系统实例
            self.event_system = EventSystem.get_instance()
            
            # 检测当前时间段
            self.current_period = self.get_current_period()
            self.logger.info(f"初始时间段: {self.current_period.name}")
            
            # 启动定时器，定期检查时间变化
            self.timer.start(self.check_interval * 1000)  # 转换为毫秒
            
            # 发布初始化完成事件
            self._publish_time_event(self.current_period)
            
            return True
        except Exception as e:
            self.logger.error(f"时间行为系统初始化失败: {e}")
            return False
    
    def _shutdown(self) -> bool:
        """关闭组件
        
        Returns:
            bool: 关闭是否成功
        """
        try:
            # 停止定时器
            if self.timer.isActive():
                self.timer.stop()
            
            # 断开信号连接
            try:
                self.timer.timeout.disconnect(self._check_time_change)
            except RuntimeError:
                # 忽略未连接的信号错误
                pass
            
            return True
        except Exception as e:
            self.logger.error(f"关闭时间行为系统失败: {e}")
            return False
    
    def get_current_period(self) -> TimePeriod:
        """获取当前时间段
        
        Returns:
            TimePeriod: 当前时间段
        """
        now = datetime.datetime.now()
        hour = now.hour
        
        if 5 <= hour < 12:
            return TimePeriod.MORNING
        elif 12 <= hour < 14:
            return TimePeriod.NOON
        elif 14 <= hour < 18:
            return TimePeriod.AFTERNOON
        elif 18 <= hour < 23:
            return TimePeriod.EVENING
        else:  # 23, 0, 1, 2, 3, 4
            return TimePeriod.NIGHT
    
    def _check_time_change(self) -> None:
        """检查时间变化，定时器调用"""
        try:
            # 检查时间段是否变化
            new_period = self.get_current_period()
            if new_period != self.current_period:
                old_period = self.current_period
                self.current_period = new_period
                
                # 发布时间段变化事件（通过Qt信号）
                if hasattr(self, 'signals') and self.signals is not None:
                    self.signals.time_period_changed.emit(new_period, old_period)
                
                # 通过事件系统发布
                self._publish_time_event(new_period)
                
                self.logger.info(f"时间段变化: {old_period.name if old_period else 'None'} -> {new_period.name}")
            
            # 检查是否有特殊日期
            self._check_special_dates()
        except Exception as e:
            self.logger.error(f"检查时间变化时出错: {e}")
    
    def _publish_time_event(self, period: TimePeriod) -> None:
        """发布时间事件到事件系统
        
        Args:
            period: 当前时间段
        """
        if self.event_system:
            event_data = {
                'period': period.name,
                'timestamp': time.time(),
                'datetime': datetime.datetime.now().isoformat()
            }
            
            self.event_system.dispatch_event(
                EventType.TIME_PERIOD_CHANGED,
                sender=self,
                data=event_data
            )
    
    def _initialize_special_dates(self) -> None:
        """初始化特殊日期列表"""
        # 清空现有特殊日期
        self.special_dates = []
        
        # 添加公历节日
        self._add_solar_festivals()
        
        # 添加农历节日
        self._add_lunar_festivals()
        
        # 添加节气（通常使用公历表示）
        self._add_solar_terms()
        
        # 添加自定义日期
        self._add_custom_dates()
        
        self.logger.debug(f"已初始化 {len(self.special_dates)} 个特殊日期")
    
    def _add_solar_festivals(self) -> None:
        """添加公历节日"""
        solar_festivals = [
            # 诞辰
            SpecialDate.create_solar_festival("Birth of Status-Ming!", 5, 19, "Status-Ming 诞辰", trigger_days_before=1),

            # 法定节假日
            SpecialDate.create_solar_festival("元旦", 1, 1, "新的一年开始了", trigger_days_before=1),
            SpecialDate.create_solar_festival("劳动节", 5, 1, "劳动人民的节日"),
            SpecialDate.create_solar_festival("国庆节", 10, 1, "祖国生日", trigger_days_before=1),
            
            # 其他重要节日
            SpecialDate.create_solar_festival("妇女节", 3, 8, "国际妇女节"),
            SpecialDate.create_solar_festival("植树节", 3, 12, "植树造林的日子"),
            SpecialDate.create_solar_festival("青年节", 5, 4, "五四青年节"),
            SpecialDate.create_solar_festival("儿童节", 6, 1, "六一儿童节"),
            SpecialDate.create_solar_festival("建军节", 8, 1, "中国人民解放军建军节"),
            SpecialDate.create_solar_festival("教师节", 9, 10, "尊师重教"),
            
            # 西方节日
            SpecialDate.create_solar_festival("情人节", 2, 14, "浪漫的日子"),
            SpecialDate.create_solar_festival("愚人节", 4, 1, "开玩笑的日子"),
            SpecialDate.create_solar_festival("万圣节", 10, 31, "不给糖就捣蛋"),
            SpecialDate.create_solar_festival("平安夜", 12, 24, "圣诞前夜"),
            SpecialDate.create_solar_festival("圣诞节", 12, 25, "圣诞快乐"),
            
            # 特殊纪念日
            SpecialDate.create_solar_festival("世界地球日", 4, 22, "保护地球环境"),
            SpecialDate.create_solar_festival("防灾减灾日", 5, 12, "提高防灾意识"),
            SpecialDate.create_solar_festival("国家公祭日", 12, 13, "勿忘国耻"),
            
            # 程序员相关
            SpecialDate.create_solar_festival("程序员节", 10, 24, "1024程序员节")
        ]
        
        self.special_dates.extend(solar_festivals)
    
    def _add_lunar_festivals(self) -> None:
        """添加农历节日"""
        lunar_festivals = [
            # 主要传统节日
            SpecialDate.create_lunar_festival("春节", 1, 1, "农历新年", trigger_days_before=1),
            SpecialDate.create_lunar_festival("元宵节", 1, 15, "正月十五闹元宵"),
            SpecialDate.create_lunar_festival("龙抬头", 2, 2, "二月二龙抬头"),
            SpecialDate.create_lunar_festival("端午节", 5, 5, "吃粽子的日子"),
            SpecialDate.create_lunar_festival("七夕节", 7, 7, "牛郎织女相会的日子"),
            SpecialDate.create_lunar_festival("中元节", 7, 15, "鬼节"),
            SpecialDate.create_lunar_festival("中秋节", 8, 15, "团圆的日子"),
            SpecialDate.create_lunar_festival("重阳节", 9, 9, "敬老节"),
            SpecialDate.create_lunar_festival("腊八节", 12, 8, "腊八粥"),
            SpecialDate.create_lunar_festival("小年", 12, 23, "祭灶节"),
            SpecialDate.create_lunar_festival("除夕", 12, 30, "年三十", trigger_days_before=1),
            
            # 其他传统节日
            SpecialDate.create_lunar_festival("上巳节", 3, 3, "古代的春游节"),
            SpecialDate.create_lunar_festival("寒食节", 4, 3, "传统扫墓节"),
            SpecialDate.create_lunar_festival("尾牙", 12, 16, "祭祀土地神")
        ]
        
        self.special_dates.extend(lunar_festivals)
    
    def _add_solar_terms(self) -> None:
        """添加二十四节气
        
        注意：节气的准确日期每年略有不同，这里只是示例固定日期
        实际应用时应当动态获取当年的节气日期
        """
        # 由于节气日期每年不同，这里不预设固定日期
        # 实际工作中会在运行时动态计算获取
        
        # 如果支持农历库，尝试获取当年的节气日期
        if LUNAR_AVAILABLE:
            today = datetime.date.today()
            
            # 获取当年所有节气（注意：由于Lunar库API限制，这里采用查找方式）
            next_term = LunarHelper.get_next_solar_term()
            if next_term:
                # 添加下一个节气
                term_name, term_date = next_term
                self.special_dates.append(
                    SpecialDate.create_solar_term(
                        term_name, 
                        term_date.month, 
                        term_date.day, 
                        f"{term_name}时节已到", 
                        trigger_days_before=1
                    )
                )
    
    def _add_custom_dates(self) -> None:
        """添加自定义特殊日期"""
        # 这里留空，可在实例化后通过add_special_date方法添加自定义日期
        pass
    
    def _check_special_dates(self) -> None:
        """检查是否有特殊日期"""
        today = datetime.date.today()
        
        # 检查所有特殊日期
        for special_date in self.special_dates:
            try:
                # 根据是否是农历日期采用不同的检测方法
                if special_date.is_lunar:
                    if not LUNAR_AVAILABLE:
                        continue  # 农历库不可用，跳过农历日期
                    
                    self._check_lunar_date(special_date, today)
                else:
                    self._check_solar_date(special_date, today)
            except Exception as e:
                self.logger.error(f"检查特殊日期 {special_date.name} 时出错: {e}")
    
    def _check_solar_date(self, special_date: SpecialDate, today: datetime.date) -> None:
        """检查公历特殊日期
        
        Args:
            special_date: 特殊日期对象
            today: 今天的日期
        """
        # 检查是当天还是提前几天
        for days_before in range(special_date.trigger_days_before + 1):
            check_date = today + datetime.timedelta(days=days_before)
            
            # 检查月份和日期是否匹配
            if check_date.month == special_date.month and check_date.day == special_date.day:
                # 生成唯一ID避免重复触发
                trigger_id = f"{special_date.name}_{today.year}"
                
                # 确保今天没有触发过
                if trigger_id not in self.triggered_special_dates:
                    self._trigger_special_date(special_date, days_before)
                    break  # 一个特殊日期只触发一次
    
    def _check_lunar_date(self, special_date: SpecialDate, today: datetime.date) -> None:
        """检查农历特殊日期
        
        Args:
            special_date: 特殊日期对象
            today: 今天的日期
        """
        if not LUNAR_AVAILABLE:
            return
        
        # 获取今天的农历日期
        lunar_today = LunarHelper.solar_to_lunar(today)
        if not lunar_today:
            return
        
        # 生成唯一ID避免重复触发
        trigger_id = f"{special_date.name}_{today.year}"
        
        # 确保今天没有触发过
        if trigger_id in self.triggered_special_dates:
            return
        
        # 检查今天是否是特殊日期
        lunar_year, lunar_month, lunar_day, is_leap_month = lunar_today
        
        # 如果是特殊日期且闰月设置匹配
        if (lunar_month == special_date.month and 
            lunar_day == special_date.day and 
            is_leap_month == special_date.lunar_leap_month):
            self._trigger_special_date(special_date, 0)
            return
        
        # 检查提前几天的情况
        if special_date.trigger_days_before > 0:
            for days_before in range(1, special_date.trigger_days_before + 1):
                # 计算提前几天的日期
                check_date = today + datetime.timedelta(days=days_before)
                lunar_check = LunarHelper.solar_to_lunar(check_date)
                
                if not lunar_check:
                    continue
                
                check_year, check_month, check_day, check_leap = lunar_check
                
                if (check_month == special_date.month and 
                    check_day == special_date.day and 
                    check_leap == special_date.lunar_leap_month):
                    self._trigger_special_date(special_date, days_before)
                    break  # 一个特殊日期只触发一次
    
    def _trigger_special_date(self, special_date: SpecialDate, days_before: int) -> None:
        """触发特殊日期事件
        
        Args:
            special_date: 特殊日期对象
            days_before: 提前几天
        """
        # 发送特殊日期信号
        if hasattr(self, 'signals') and self.signals is not None:
            self.signals.special_date_triggered.emit(special_date.name, special_date.description)
        
        # 通过事件系统发布
        if self.event_system:
            event_data = {
                'name': special_date.name,
                'description': special_date.description,
                'days_before': days_before,
                'timestamp': time.time(),
                'is_lunar': special_date.is_lunar
            }
            
            self.event_system.dispatch_event(
                EventType.SPECIAL_DATE,
                sender=self,
                data=event_data
            )
        
        # 记录已触发，避免重复
        today = datetime.date.today()
        trigger_id = f"{special_date.name}_{today.year}"
        self.triggered_special_dates.add(trigger_id)
        
        # 日志记录
        date_type = "农历" if special_date.is_lunar else "公历"
        self.logger.info(f"触发特殊日期: {special_date.name} ({date_type}) - {special_date.description}"
                            f" (提前 {days_before} 天)")
    
    def reset_triggered_dates(self) -> None:
        """重置已触发的特殊日期列表，用于测试或日期变更时"""
        self.triggered_special_dates.clear()
        self.logger.debug("已重置触发过的特殊日期列表")
    
    def add_special_date(self, special_date: SpecialDate) -> None:
        """添加自定义特殊日期
        
        Args:
            special_date: 特殊日期对象
        """
        self.special_dates.append(special_date)
        date_type = "农历" if special_date.is_lunar else "公历"
        self.logger.debug(f"已添加特殊日期: {special_date.name} ({date_type} {special_date.month}/{special_date.day})")
    
    def get_special_dates(self) -> List[SpecialDate]:
        """获取所有特殊日期
        
        Returns:
            List[SpecialDate]: 特殊日期列表
        """
        return self.special_dates.copy()
    
    def get_upcoming_special_dates(self, days: int = 30) -> List[Tuple[SpecialDate, datetime.date]]:
        """获取即将到来的特殊日期
        
        Args:
            days: 未来多少天内的特殊日期
            
        Returns:
            List[Tuple[SpecialDate, datetime.date]]: 特殊日期和对应的公历日期列表
        """
        result = []
        today = datetime.date.today()
        end_date = today + datetime.timedelta(days=days)
        
        # 遍历特殊日期
        for special_date in self.special_dates:
            if special_date.is_lunar and not LUNAR_AVAILABLE:
                continue  # 农历库不可用，跳过农历日期
            
            try:
                # 根据是否是农历日期采用不同的方法获取今年的公历日期
                if special_date.is_lunar:
                    # 获取今年的农历节日对应的公历日期
                    solar_date = LunarHelper.lunar_to_solar(
                        today.year, special_date.month, special_date.day, special_date.lunar_leap_month)
                    
                    # 如果日期已过或农历转换失败，尝试明年的日期
                    if not solar_date or solar_date < today:
                        solar_date = LunarHelper.lunar_to_solar(
                            today.year + 1, special_date.month, special_date.day, special_date.lunar_leap_month)
                else:
                    # 公历日期直接计算
                    try:
                        solar_date = datetime.date(today.year, special_date.month, special_date.day)
                        # 如果日期已过，使用明年的日期
                        if solar_date < today:
                            solar_date = datetime.date(today.year + 1, special_date.month, special_date.day)
                    except ValueError:
                        # 处理无效日期（如2月29日在非闰年）
                        self.logger.warning(f"特殊日期 {special_date.name} 日期无效: {special_date.month}/{special_date.day}")
                        continue
                
                # 检查日期是否在范围内
                if solar_date and today <= solar_date <= end_date:
                    result.append((special_date, solar_date))
            except Exception as e:
                self.logger.error(f"计算特殊日期 {special_date.name} 的公历日期时出错: {e}")
        
        # 按日期排序
        result.sort(key=lambda x: x[1])
        return result
    
    def get_current_special_dates(self) -> List[SpecialDate]:
        """获取当前日期的特殊日期列表
        
        Returns:
            List[SpecialDate]: 当前日期的特殊日期列表
        """
        result = []
        today = datetime.date.today()
        
        # 遍历所有特殊日期
        for special_date in self.special_dates:
            try:
                # 公历日期直接比较
                if not special_date.is_lunar:
                    if today.month == special_date.month and today.day == special_date.day:
                        result.append(special_date)
                # 农历日期需要转换
                elif LUNAR_AVAILABLE:
                    lunar_today = LunarHelper.solar_to_lunar(today)
                    if lunar_today:
                        lunar_year, lunar_month, lunar_day, is_leap_month = lunar_today
                        if (lunar_month == special_date.month and 
                            lunar_day == special_date.day and 
                            is_leap_month == special_date.lunar_leap_month):
                            result.append(special_date)
            except Exception as e:
                self.logger.error(f"检查当前特殊日期 {special_date.name} 时出错: {e}")
                
        return result