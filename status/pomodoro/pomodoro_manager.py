"""
---------------------------------------------------------------
File name:                  pomodoro_manager.py
Author:                     Ignorant-lu
Date created:               2025/04/05
Description:                番茄钟管理器，协调番茄钟与系统集成
----------------------------------------------------------------

Changed history:            
                            2025/04/05: 初始创建;
----
"""

import logging
import threading
import time
from typing import Dict, Any, Optional, Callable, List, Union, Tuple
import os
import json
from datetime import datetime, date

from status.core.events import EventManager, Event, EventType
from status.pomodoro.pomodoro_timer import PomodoroTimer, PomodoroState, PomodoroConfig

# 配置日志记录器
logger = logging.getLogger(__name__)

class PomodoroEventType:
    """番茄钟相关的事件类型常量"""
    POMODORO_START = "pomodoro_start"           # 番茄钟开始
    POMODORO_PAUSE = "pomodoro_pause"           # 番茄钟暂停
    POMODORO_RESUME = "pomodoro_resume"         # 番茄钟恢复
    POMODORO_STOP = "pomodoro_stop"             # 番茄钟停止
    POMODORO_TICK = "pomodoro_tick"             # 番茄钟计时刻度
    POMODORO_COMPLETE = "pomodoro_complete"     # 番茄钟完成
    POMODORO_STATE_CHANGE = "pomodoro_state_change"  # 番茄钟状态变化
    POMODORO_CONFIG_CHANGE = "pomodoro_config_change"  # 番茄钟配置变化
    POMODORO_STATS_UPDATE = "pomodoro_stats_update"    # 番茄钟统计数据更新

class PomodoroManager:
    """番茄钟管理器
    
    协调番茄钟计时器与系统其他组件的交互，
    处理事件分发、通知、数据记录等功能。
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """初始化番茄钟管理器
        
        Args:
            config: 配置参数
        """
        # 基础配置
        self.config = config or {}
        
        # 创建番茄钟计时器
        timer_config = self.config.get('timer', {})
        self.timer = PomodoroTimer(timer_config)
        
        # 获取事件管理器
        self.event_manager = EventManager.get_instance()
        
        # 统计数据
        self.stats = {
            'today': {
                'focus_sessions': 0,        # 今日专注次数
                'focus_minutes': 0,         # 今日专注分钟数
                'completed_pomodoros': 0,   # 今日完成的番茄数
            },
            'total': {
                'focus_sessions': 0,        # 总专注次数
                'focus_minutes': 0,         # 总专注分钟数
                'completed_pomodoros': 0,   # 总计完成的番茄数
                'streak_days': 0,           # 连续使用天数
            },
            'history': {},                  # 历史数据，按日期存储
            'last_active_date': None,       # 最后活动日期
        }
        
        # 任务相关
        self.current_task = self.config.get('current_task', '')
        self.task_history = []
        
        # 加载统计数据
        self._load_stats()
        
        # 注册计时器回调
        self._register_timer_callbacks()
        
        # 最后活动时间
        self.last_active_time = time.time()
        
        # 自动保存统计数据的计时器
        self.auto_save_interval = self.config.get('auto_save_interval', 300)  # 默认5分钟
        self._auto_save_thread = None
        self._stop_auto_save = threading.Event()
        
        # 启动自动保存线程
        self._start_auto_save()
        
        logger.info("番茄钟管理器已初始化")
    
    def _register_timer_callbacks(self):
        """注册计时器回调函数"""
        # 注册刻度回调
        self.timer.register_tick_callback(self._on_timer_tick)
        
        # 注册状态变化回调
        self.timer.register_state_change_callback(self._on_timer_state_change)
        
        # 注册完成回调
        self.timer.register_complete_callback(self._on_timer_complete)
        
        logger.debug("已注册计时器回调函数")
    
    def _on_timer_tick(self, state_info: Dict[str, Any]):
        """计时器刻度回调
        
        Args:
            state_info: 状态信息字典
        """
        # 更新最后活动时间
        self.last_active_time = time.time()
        
        # 发布刻度事件
        self.event_manager.dispatch_event(
            EventType.APPLICATION_STATE,
            self,
            {"type": PomodoroEventType.POMODORO_TICK, "state_info": state_info}
        )
    
    def _on_timer_state_change(self, old_state: PomodoroState, new_state: PomodoroState):
        """计时器状态变化回调
        
        Args:
            old_state: 旧状态
            new_state: 新状态
        """
        # 处理状态转换
        if old_state == PomodoroState.FOCUS and new_state != PomodoroState.PAUSED:
            # 专注结束（非暂停）
            if self.timer.elapsed_time > 0:
                self._update_focus_stats(self.timer.elapsed_time)
        
        # 发布状态变化事件
        self.event_manager.dispatch_event(
            EventType.APPLICATION_STATE,
            self,
            {
                "type": PomodoroEventType.POMODORO_STATE_CHANGE,
                "old_state": old_state,
                "new_state": new_state
            }
        )
        
        logger.info(f"番茄钟状态变化: {old_state.name} -> {new_state.name}")
    
    def _on_timer_complete(self, completed_state: PomodoroState):
        """计时器完成回调
        
        Args:
            completed_state: 完成的状态
        """
        # 处理完成事件
        if completed_state == PomodoroState.FOCUS:
            # 专注完成，增加完成番茄数
            self.stats['today']['completed_pomodoros'] += 1
            self.stats['total']['completed_pomodoros'] += 1
            
            # 记录任务历史（如果有）
            if self.current_task:
                self.task_history.append({
                    'task': self.current_task,
                    'timestamp': datetime.now().isoformat(),
                    'duration': self.timer.total_time
                })
        
        # 发布完成事件
        self.event_manager.dispatch_event(
            EventType.APPLICATION_STATE,
            self,
            {
                "type": PomodoroEventType.POMODORO_COMPLETE,
                "state": completed_state,
                "stats": self.get_today_stats()
            }
        )
        
        # 保存统计数据
        self._save_stats()
        
        logger.info(f"番茄钟完成: {completed_state.name}")
    
    def _update_focus_stats(self, elapsed_seconds: int):
        """更新专注统计数据
        
        Args:
            elapsed_seconds: 专注时长(秒)
        """
        # 检查当前日期
        self._check_new_day()
        
        # 转换为分钟
        elapsed_minutes = elapsed_seconds / 60
        
        # 更新统计数据
        self.stats['today']['focus_sessions'] += 1
        self.stats['today']['focus_minutes'] += elapsed_minutes
        self.stats['total']['focus_sessions'] += 1
        self.stats['total']['focus_minutes'] += elapsed_minutes
        
        # 添加到历史记录
        today = date.today().isoformat()
        if today not in self.stats['history']:
            self.stats['history'][today] = {
                'focus_sessions': 0,
                'focus_minutes': 0,
                'completed_pomodoros': 0
            }
        
        self.stats['history'][today]['focus_sessions'] += 1
        self.stats['history'][today]['focus_minutes'] += elapsed_minutes
        
        # 发布统计更新事件
        self.event_manager.dispatch_event(
            EventType.APPLICATION_STATE,
            self,
            {
                "type": PomodoroEventType.POMODORO_STATS_UPDATE,
                "stats": self.get_today_stats()
            }
        )
    
    def _check_new_day(self):
        """检查是否为新的一天，更新统计数据"""
        today = date.today()
        today_str = today.isoformat()
        
        # 检查最后活动日期
        if self.stats['last_active_date'] is not None:
            last_date = date.fromisoformat(self.stats['last_active_date'])
            
            if today > last_date:
                # 新的一天，更新统计数据
                self.stats['today'] = {
                    'focus_sessions': 0,
                    'focus_minutes': 0,
                    'completed_pomodoros': 0
                }
                
                # 更新连续天数
                if (today - last_date).days == 1:
                    # 连续使用
                    self.stats['total']['streak_days'] += 1
                else:
                    # 中断连续使用
                    self.stats['total']['streak_days'] = 1
        else:
            # 首次使用
            self.stats['total']['streak_days'] = 1
        
        # 更新最后活动日期
        self.stats['last_active_date'] = today_str
        
        # 确保历史记录中有今天的条目
        if today_str not in self.stats['history']:
            self.stats['history'][today_str] = {
                'focus_sessions': 0,
                'focus_minutes': 0,
                'completed_pomodoros': 0
            }
    
    def start_focus(self) -> bool:
        """开始专注工作
        
        Returns:
            bool: 是否成功开始
        """
        result = self.timer.start_focus()
        
        if result:
            # 发布开始事件
            self.event_manager.dispatch_event(
                EventType.APPLICATION_STATE,
                self,
                {
                    "type": PomodoroEventType.POMODORO_START,
                    "state": PomodoroState.FOCUS,
                    "duration": self.timer.total_time
                }
            )
            
            # 更新最后活动时间
            self.last_active_time = time.time()
        
        return result
    
    def start_short_break(self) -> bool:
        """开始短休息
        
        Returns:
            bool: 是否成功开始
        """
        result = self.timer.start_short_break()
        
        if result:
            # 发布开始事件
            self.event_manager.dispatch_event(
                EventType.APPLICATION_STATE,
                self,
                {
                    "type": PomodoroEventType.POMODORO_START,
                    "state": PomodoroState.SHORT_BREAK,
                    "duration": self.timer.total_time
                }
            )
            
            # 更新最后活动时间
            self.last_active_time = time.time()
        
        return result
    
    def start_long_break(self) -> bool:
        """开始长休息
        
        Returns:
            bool: 是否成功开始
        """
        result = self.timer.start_long_break()
        
        if result:
            # 发布开始事件
            self.event_manager.dispatch_event(
                EventType.APPLICATION_STATE,
                self,
                {
                    "type": PomodoroEventType.POMODORO_START,
                    "state": PomodoroState.LONG_BREAK,
                    "duration": self.timer.total_time
                }
            )
            
            # 更新最后活动时间
            self.last_active_time = time.time()
        
        return result
    
    def pause(self) -> bool:
        """暂停计时器
        
        Returns:
            bool: 是否成功暂停
        """
        result = self.timer.pause()
        
        if result:
            # 发布暂停事件
            self.event_manager.dispatch_event(
                EventType.APPLICATION_STATE,
                self,
                {
                    "type": PomodoroEventType.POMODORO_PAUSE,
                    "state_info": self.timer.get_state_info()
                }
            )
            
            # 更新最后活动时间
            self.last_active_time = time.time()
        
        return result
    
    def resume(self) -> bool:
        """恢复计时器
        
        Returns:
            bool: 是否成功恢复
        """
        result = self.timer.resume()
        
        if result:
            # 发布恢复事件
            self.event_manager.dispatch_event(
                EventType.APPLICATION_STATE,
                self,
                {
                    "type": PomodoroEventType.POMODORO_RESUME,
                    "state_info": self.timer.get_state_info()
                }
            )
            
            # 更新最后活动时间
            self.last_active_time = time.time()
        
        return result
    
    def stop(self) -> bool:
        """停止计时器
        
        Returns:
            bool: 是否成功停止
        """
        # 如果是专注状态，更新统计数据
        if self.timer.state == PomodoroState.FOCUS and self.timer.elapsed_time > 0:
            self._update_focus_stats(self.timer.elapsed_time)
        
        result = self.timer.stop()
        
        if result:
            # 发布停止事件
            self.event_manager.dispatch_event(
                EventType.APPLICATION_STATE,
                self,
                {
                    "type": PomodoroEventType.POMODORO_STOP,
                    "state_info": self.timer.get_state_info()
                }
            )
            
            # 更新最后活动时间
            self.last_active_time = time.time()
            
            # 保存统计数据
            self._save_stats()
        
        return result
    
    def reset(self) -> bool:
        """重置计时器
        
        Returns:
            bool: 是否成功重置
        """
        result = self.timer.reset()
        
        if result:
            # 更新最后活动时间
            self.last_active_time = time.time()
        
        return result
    
    def next_state(self) -> bool:
        """切换到下一个状态
        
        Returns:
            bool: 是否成功切换
        """
        result = self.timer.next_state()
        
        if result:
            # 更新最后活动时间
            self.last_active_time = time.time()
        
        return result
    
    def set_current_task(self, task: str) -> None:
        """设置当前任务
        
        Args:
            task: 任务描述
        """
        self.current_task = task
        
        # 更新配置
        self.config['current_task'] = task
        
        logger.info(f"已设置当前任务: {task}")
    
    def get_current_task(self) -> str:
        """获取当前任务
        
        Returns:
            str: 当前任务
        """
        return self.current_task
    
    def get_task_history(self) -> List[Dict[str, Any]]:
        """获取任务历史
        
        Returns:
            List[Dict[str, Any]]: 任务历史列表
        """
        return self.task_history.copy()
    
    def clear_task_history(self) -> None:
        """清空任务历史"""
        self.task_history.clear()
        logger.info("已清空任务历史")
    
    def get_state_info(self) -> Dict[str, Any]:
        """获取当前状态信息
        
        Returns:
            Dict[str, Any]: 状态信息字典
        """
        return self.timer.get_state_info()
    
    def get_today_stats(self) -> Dict[str, Any]:
        """获取今日统计数据
        
        Returns:
            Dict[str, Any]: 今日统计数据
        """
        # 检查当前日期
        self._check_new_day()
        
        return {
            'today': self.stats['today'],
            'streak_days': self.stats['total']['streak_days'],
            'total': self.stats['total']
        }
    
    def get_history_stats(self, days: int = 7) -> Dict[str, Dict[str, Any]]:
        """获取历史统计数据
        
        Args:
            days: 获取最近多少天的数据
            
        Returns:
            Dict[str, Dict[str, Any]]: 历史统计数据
        """
        # 获取最近几天的日期
        today = date.today()
        result = {}
        
        for i in range(days):
            day = today - date(days=i)
            day_str = day.isoformat()
            
            if day_str in self.stats['history']:
                result[day_str] = self.stats['history'][day_str]
            else:
                result[day_str] = {
                    'focus_sessions': 0,
                    'focus_minutes': 0,
                    'completed_pomodoros': 0
                }
        
        return result
    
    def update_config(self, new_config: Dict[str, Any]) -> bool:
        """更新配置
        
        Args:
            new_config: 新的配置参数
            
        Returns:
            bool: 是否成功更新
        """
        try:
            # 更新管理器配置
            for key, value in new_config.items():
                if key != 'timer':  # 计时器配置单独处理
                    self.config[key] = value
            
            # 更新自动保存间隔
            if 'auto_save_interval' in new_config:
                self.auto_save_interval = new_config['auto_save_interval']
            
            # 更新计时器配置
            if 'timer' in new_config:
                timer_config = new_config['timer']
                result = self.timer.update_config(timer_config)
                if not result:
                    logger.warning("更新计时器配置失败")
                    return False
            
            # 发布配置变化事件
            self.event_manager.dispatch_event(
                EventType.CONFIG_CHANGE,
                self,
                {
                    "type": PomodoroEventType.POMODORO_CONFIG_CHANGE,
                    "config": self.config
                }
            )
            
            logger.info("番茄钟配置已更新")
            return True
            
        except Exception as e:
            logger.error(f"更新配置失败: {str(e)}")
            return False
    
    def get_config(self) -> Dict[str, Any]:
        """获取当前配置
        
        Returns:
            Dict[str, Any]: 当前配置
        """
        return self.config.copy()
    
    def _get_stats_file_path(self) -> str:
        """获取统计数据文件路径
        
        Returns:
            str: 文件路径
        """
        # 从配置中获取保存路径，默认为data目录
        data_dir = self.config.get('data_dir', 'data')
        
        # 确保目录存在
        os.makedirs(data_dir, exist_ok=True)
        
        return os.path.join(data_dir, 'pomodoro_stats.json')
    
    def _load_stats(self) -> None:
        """加载统计数据"""
        try:
            file_path = self._get_stats_file_path()
            
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    saved_stats = json.load(f)
                
                # 更新统计数据
                self.stats.update(saved_stats)
                
                # 检查当前日期
                self._check_new_day()
                
                logger.info("已加载番茄钟统计数据")
            
        except Exception as e:
            logger.error(f"加载统计数据失败: {str(e)}")
    
    def _save_stats(self) -> None:
        """保存统计数据"""
        try:
            file_path = self._get_stats_file_path()
            
            # 确保目录存在
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(self.stats, f, ensure_ascii=False, indent=2)
            
            logger.debug("已保存番茄钟统计数据")
            
        except Exception as e:
            logger.error(f"保存统计数据失败: {str(e)}")
    
    def _start_auto_save(self) -> None:
        """启动自动保存线程"""
        if self._auto_save_thread is not None and self._auto_save_thread.is_alive():
            return
        
        # 重置停止事件
        self._stop_auto_save.clear()
        
        # 创建并启动线程
        self._auto_save_thread = threading.Thread(target=self._auto_save_loop, daemon=True)
        self._auto_save_thread.start()
        
        logger.debug("已启动自动保存线程")
    
    def _auto_save_loop(self) -> None:
        """自动保存循环"""
        try:
            while not self._stop_auto_save.is_set():
                # 等待指定时间
                self._stop_auto_save.wait(self.auto_save_interval)
                
                if not self._stop_auto_save.is_set():
                    # 保存统计数据
                    self._save_stats()
                    
        except Exception as e:
            logger.error(f"自动保存线程异常: {str(e)}")
    
    def _stop_auto_save(self) -> None:
        """停止自动保存线程"""
        # 设置停止事件
        self._stop_auto_save.set()
        
        # 等待线程结束
        if self._auto_save_thread and self._auto_save_thread.is_alive():
            self._auto_save_thread.join(timeout=2.0)
        
        logger.debug("已停止自动保存线程")
    
    def get_last_active_time(self) -> float:
        """获取最后活动时间
        
        Returns:
            float: 最后活动时间的时间戳
        """
        return self.last_active_time
    
    def shutdown(self) -> None:
        """关闭番茄钟管理器"""
        logger.info("正在关闭番茄钟管理器...")
        
        # 停止计时器
        if self.timer.is_active():
            self.stop()
        
        # 停止自动保存线程
        self._stop_auto_save()
        
        # 保存统计数据
        self._save_stats()
        
        logger.info("番茄钟管理器已关闭") 