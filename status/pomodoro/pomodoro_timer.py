"""
---------------------------------------------------------------
File name:                  pomodoro_timer.py
Author:                     Ignorant-lu
Date created:               2025/04/05
Description:                番茄钟定时器，提供番茄工作法的计时功能
----------------------------------------------------------------

Changed history:            
                            2025/04/05: 初始创建;
----
"""

import threading
import time
import logging
from typing import Dict, Any, Optional, Callable, List, Union
from enum import Enum, auto
from dataclasses import dataclass

# 配置日志记录器
logger = logging.getLogger(__name__)

class PomodoroState(Enum):
    """番茄钟状态枚举"""
    IDLE = auto()        # 空闲状态
    FOCUS = auto()       # 专注工作
    SHORT_BREAK = auto() # 短休息
    LONG_BREAK = auto()  # 长休息
    PAUSED = auto()      # 暂停

@dataclass
class PomodoroConfig:
    """番茄钟配置类"""
    focus_duration: int = 25 * 60     # 专注时长(秒)，默认25分钟
    short_break_duration: int = 5 * 60  # 短休息时长(秒)，默认5分钟
    long_break_duration: int = 15 * 60  # 长休息时长(秒)，默认15分钟
    cycles_before_long_break: int = 4  # 长休息前的工作周期数，默认4
    auto_start_breaks: bool = True     # 是否自动开始休息
    auto_start_focus: bool = False     # 是否自动开始专注
    tick_interval: float = 1.0         # 计时器刷新间隔(秒)

class PomodoroTimer:
    """番茄钟定时器类
    
    实现番茄工作法的计时功能，包括专注工作、短休息和长休息，
    支持自定义时长、暂停恢复、重置等功能。
    """
    
    def __init__(self, config: Optional[Union[Dict[str, Any], PomodoroConfig]] = None):
        """初始化番茄钟定时器
        
        Args:
            config: 配置参数，可以是PomodoroConfig对象或字典
        """
        # 配置初始化
        if isinstance(config, PomodoroConfig):
            self.config = config
        elif isinstance(config, dict):
            # 从字典创建配置
            self.config = PomodoroConfig(
                focus_duration=config.get('focus_duration', 25 * 60),
                short_break_duration=config.get('short_break_duration', 5 * 60),
                long_break_duration=config.get('long_break_duration', 15 * 60),
                cycles_before_long_break=config.get('cycles_before_long_break', 4),
                auto_start_breaks=config.get('auto_start_breaks', True),
                auto_start_focus=config.get('auto_start_focus', False),
                tick_interval=config.get('tick_interval', 1.0)
            )
        else:
            # 使用默认配置
            self.config = PomodoroConfig()
        
        # 状态初始化
        self.state = PomodoroState.IDLE
        self.remaining_time = 0
        self.elapsed_time = 0
        self.total_time = 0
        self.completed_cycles = 0
        self.is_running = False
        
        # 线程相关
        self._timer_thread = None
        self._stop_event = threading.Event()
        
        # 回调函数
        self._on_tick = None
        self._on_state_change = None
        self._on_complete = None
        
        logger.info("番茄钟定时器已初始化")
    
    def start_focus(self) -> bool:
        """开始专注工作
        
        进入专注工作状态，开始倒计时。
        
        Returns:
            bool: 是否成功开始
        """
        if self.is_running:
            logger.warning("番茄钟已经在运行中")
            return False
        
        # 设置状态和时间
        self._change_state(PomodoroState.FOCUS)
        self.total_time = self.config.focus_duration
        self.remaining_time = self.total_time
        self.elapsed_time = 0
        
        # 启动计时器
        return self._start_timer()
    
    def start_short_break(self) -> bool:
        """开始短休息
        
        进入短休息状态，开始倒计时。
        
        Returns:
            bool: 是否成功开始
        """
        if self.is_running:
            logger.warning("番茄钟已经在运行中")
            return False
        
        # 设置状态和时间
        self._change_state(PomodoroState.SHORT_BREAK)
        self.total_time = self.config.short_break_duration
        self.remaining_time = self.total_time
        self.elapsed_time = 0
        
        # 启动计时器
        return self._start_timer()
    
    def start_long_break(self) -> bool:
        """开始长休息
        
        进入长休息状态，开始倒计时。
        
        Returns:
            bool: 是否成功开始
        """
        if self.is_running:
            logger.warning("番茄钟已经在运行中")
            return False
        
        # 设置状态和时间
        self._change_state(PomodoroState.LONG_BREAK)
        self.total_time = self.config.long_break_duration
        self.remaining_time = self.total_time
        self.elapsed_time = 0
        
        # 启动计时器
        return self._start_timer()
    
    def pause(self) -> bool:
        """暂停计时器
        
        暂停当前计时，可以稍后恢复。
        
        Returns:
            bool: 是否成功暂停
        """
        if not self.is_running:
            logger.warning("番茄钟未在运行中")
            return False
        
        # 记录当前状态
        self._prev_state = self.state
        
        # 设置为暂停状态
        self._change_state(PomodoroState.PAUSED)
        
        # 停止计时器
        self._stop_timer()
        
        logger.info("番茄钟已暂停")
        return True
    
    def resume(self) -> bool:
        """恢复计时器
        
        从暂停状态恢复计时。
        
        Returns:
            bool: 是否成功恢复
        """
        if self.state != PomodoroState.PAUSED:
            logger.warning("番茄钟不处于暂停状态")
            return False
        
        # 恢复之前的状态
        if hasattr(self, '_prev_state'):
            self._change_state(self._prev_state)
        else:
            self._change_state(PomodoroState.FOCUS)
        
        # 启动计时器
        return self._start_timer()
    
    def stop(self) -> bool:
        """停止计时器
        
        停止当前计时，重置状态。
        
        Returns:
            bool: 是否成功停止
        """
        # 停止计时器
        self._stop_timer()
        
        # 重置状态
        self._change_state(PomodoroState.IDLE)
        self.remaining_time = 0
        self.elapsed_time = 0
        self.total_time = 0
        
        logger.info("番茄钟已停止")
        return True
    
    def reset(self) -> bool:
        """重置计时器
        
        重置计时器状态和计数。
        
        Returns:
            bool: 是否成功重置
        """
        # 停止计时器
        self._stop_timer()
        
        # 重置状态和计数
        self._change_state(PomodoroState.IDLE)
        self.remaining_time = 0
        self.elapsed_time = 0
        self.total_time = 0
        self.completed_cycles = 0
        
        logger.info("番茄钟已重置")
        return True
    
    def is_active(self) -> bool:
        """检查计时器是否活动
        
        Returns:
            bool: 是否处于活动状态(运行中或暂停)
        """
        return self.is_running or self.state == PomodoroState.PAUSED
    
    def get_progress(self) -> float:
        """获取当前进度
        
        Returns:
            float: 当前进度(0.0-1.0)
        """
        if self.total_time == 0:
            return 0.0
        
        return self.elapsed_time / self.total_time
    
    def get_state_info(self) -> Dict[str, Any]:
        """获取当前状态信息
        
        Returns:
            Dict[str, Any]: 状态信息字典
        """
        return {
            'state': self.state,
            'elapsed_time': self.elapsed_time,
            'remaining_time': self.remaining_time,
            'total_time': self.total_time,
            'completed_cycles': self.completed_cycles,
            'is_running': self.is_running,
            'progress': self.get_progress()
        }
    
    def register_tick_callback(self, callback: Callable[[Dict[str, Any]], None]) -> None:
        """注册计时刻度回调
        
        Args:
            callback: 回调函数，接收状态信息字典作为参数
        """
        self._on_tick = callback
        logger.debug("已注册计时刻度回调")
    
    def register_state_change_callback(self, callback: Callable[[PomodoroState, PomodoroState], None]) -> None:
        """注册状态变化回调
        
        Args:
            callback: 回调函数，接收旧状态和新状态作为参数
        """
        self._on_state_change = callback
        logger.debug("已注册状态变化回调")
    
    def register_complete_callback(self, callback: Callable[[PomodoroState], None]) -> None:
        """注册完成回调
        
        Args:
            callback: 回调函数，接收完成的状态作为参数
        """
        self._on_complete = callback
        logger.debug("已注册完成回调")
    
    def update_config(self, config: Union[Dict[str, Any], PomodoroConfig]) -> bool:
        """更新配置
        
        Args:
            config: 新的配置参数
            
        Returns:
            bool: 是否成功更新
        """
        try:
            if isinstance(config, PomodoroConfig):
                self.config = config
            elif isinstance(config, dict):
                # 只更新提供的配置项
                if 'focus_duration' in config:
                    self.config.focus_duration = config['focus_duration']
                if 'short_break_duration' in config:
                    self.config.short_break_duration = config['short_break_duration']
                if 'long_break_duration' in config:
                    self.config.long_break_duration = config['long_break_duration']
                if 'cycles_before_long_break' in config:
                    self.config.cycles_before_long_break = config['cycles_before_long_break']
                if 'auto_start_breaks' in config:
                    self.config.auto_start_breaks = config['auto_start_breaks']
                if 'auto_start_focus' in config:
                    self.config.auto_start_focus = config['auto_start_focus']
                if 'tick_interval' in config:
                    self.config.tick_interval = config['tick_interval']
            
            logger.info("番茄钟配置已更新")
            return True
            
        except Exception as e:
            logger.error(f"更新配置失败: {str(e)}")
            return False
    
    def next_state(self) -> bool:
        """切换到下一个状态
        
        根据当前状态自动切换到下一个状态。
        
        Returns:
            bool: 是否成功切换
        """
        # 停止当前计时
        if self.is_running:
            self._stop_timer()
        
        # 根据当前状态决定下一个状态
        if self.state == PomodoroState.FOCUS:
            # 专注完成，增加完成周期数
            self.completed_cycles += 1
            
            # 判断是否需要长休息
            if self.completed_cycles % self.config.cycles_before_long_break == 0:
                return self.start_long_break() if self.config.auto_start_breaks else self._prepare_long_break()
            else:
                return self.start_short_break() if self.config.auto_start_breaks else self._prepare_short_break()
                
        elif self.state == PomodoroState.SHORT_BREAK or self.state == PomodoroState.LONG_BREAK:
            # 休息完成，开始下一个专注
            return self.start_focus() if self.config.auto_start_focus else self._prepare_focus()
            
        elif self.state == PomodoroState.IDLE or self.state == PomodoroState.PAUSED:
            # 空闲或暂停状态，开始专注
            return self.start_focus()
        
        return False
    
    def _prepare_focus(self) -> bool:
        """准备进入专注状态但不启动计时器
        
        Returns:
            bool: 是否成功准备
        """
        self._change_state(PomodoroState.IDLE)
        self.total_time = self.config.focus_duration
        self.remaining_time = self.total_time
        self.elapsed_time = 0
        return True
    
    def _prepare_short_break(self) -> bool:
        """准备进入短休息状态但不启动计时器
        
        Returns:
            bool: 是否成功准备
        """
        self._change_state(PomodoroState.IDLE)
        self.total_time = self.config.short_break_duration
        self.remaining_time = self.total_time
        self.elapsed_time = 0
        return True
    
    def _prepare_long_break(self) -> bool:
        """准备进入长休息状态但不启动计时器
        
        Returns:
            bool: 是否成功准备
        """
        self._change_state(PomodoroState.IDLE)
        self.total_time = self.config.long_break_duration
        self.remaining_time = self.total_time
        self.elapsed_time = 0
        return True
    
    def _start_timer(self) -> bool:
        """启动计时器线程
        
        Returns:
            bool: 是否成功启动
        """
        if self.is_running:
            return False
        
        # 重置停止事件
        self._stop_event.clear()
        
        # 创建并启动线程
        self._timer_thread = threading.Thread(target=self._timer_loop, daemon=True)
        self._timer_thread.start()
        
        self.is_running = True
        logger.info(f"番茄钟计时器已启动，状态: {self.state.name}")
        return True
    
    def _stop_timer(self) -> None:
        """停止计时器线程"""
        if not self.is_running:
            return
        
        # 设置停止事件
        self._stop_event.set()
        
        # 等待线程结束
        if self._timer_thread and self._timer_thread.is_alive():
            self._timer_thread.join(timeout=2.0)
        
        self.is_running = False
        logger.info("番茄钟计时器已停止")
    
    def _timer_loop(self) -> None:
        """计时器线程循环"""
        try:
            last_tick_time = time.time()
            
            while not self._stop_event.is_set() and self.remaining_time > 0:
                # 计算时间差
                current_time = time.time()
                elapsed = current_time - last_tick_time
                
                # 更新计时
                if elapsed >= self.config.tick_interval:
                    # 更新时间
                    time_delta = int(elapsed)
                    self.remaining_time = max(0, self.remaining_time - time_delta)
                    self.elapsed_time = min(self.total_time, self.elapsed_time + time_delta)
                    
                    # 触发刻度回调
                    if self._on_tick:
                        self._on_tick(self.get_state_info())
                    
                    # 重置计时
                    last_tick_time = current_time
                
                # 暂停线程，减少CPU使用
                self._stop_event.wait(min(0.1, self.config.tick_interval / 2))
            
            # 计时结束
            if not self._stop_event.is_set():
                # 正常结束，触发完成回调
                if self._on_complete:
                    self._on_complete(self.state)
                
                # 自动切换到下一个状态
                self.next_state()
                
        except Exception as e:
            logger.error(f"计时器线程异常: {str(e)}")
            self.is_running = False
    
    def _change_state(self, new_state: PomodoroState) -> None:
        """改变番茄钟状态
        
        Args:
            new_state: 新状态
        """
        old_state = self.state
        self.state = new_state
        
        # 触发状态变化回调
        if self._on_state_change and old_state != new_state:
            self._on_state_change(old_state, new_state)
            
        logger.debug(f"番茄钟状态变化: {old_state.name} -> {new_state.name}") 