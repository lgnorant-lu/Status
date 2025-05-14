"""
---------------------------------------------------------------
File name:                  main.py
Author:                     Ignorant-lu
Date created:               2025/05/13
Description:                Status - 一个跟随系统状态变化的桌宠应用，主程序入口
----------------------------------------------------------------

Changed history:            
                            2025/05/13: 初始创建;
                            2025/05/13: 添加初步的文件结构和功能框架;
                            2025/05/13: 添加系统托盘和主窗口实现;
                            2025/05/13: 添加简单的动画系统;
                            2025/05/13: 增加系统状态监控功能;
                            2025/05/13: 实现基础交互功能;
                            2025/05/14: 添加时间行为系统;
                            2025/05/15: 添加占位符工厂;
----
"""

import logging
import sys
import time
from typing import Optional, Dict, Any, List, Tuple

import os
import random

from PySide6.QtWidgets import QApplication, QMainWindow, QSystemTrayIcon, QMenu, QColorDialog
from PySide6.QtGui import QIcon, QPixmap, QColor, QPainter, QPen, QBrush, QAction, QImage, QMouseEvent, QFont, QPainterPath, QCursor, QRadialGradient
from PySide6.QtCore import Qt, QTimer, QRect, QPoint, QSize, Signal, QObject

# 设置日志格式
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(name)s - %(message)s'
)

# 创建一个专用的日志记录器
logger = logging.getLogger("StatusApp")

# 导入本地模块
from status.ui.main_pet_window import MainPetWindow
from status.ui.system_tray import SystemTrayManager
from status.ui.stats_panel import StatsPanel

from status.animation.animation import Animation
from status.core.event_system import Event, EventType

from status.behavior.pet_state import PetState
from status.behavior.pet_state_machine import PetStateMachine
from status.behavior.system_state_adapter import SystemStateAdapter

from status.monitoring.system_monitor import publish_stats

from status.interaction.interaction_handler import InteractionHandler
from status.behavior.interaction_tracker import InteractionTracker

from status.behavior.time_based_behavior import TimeBasedBehaviorSystem, TimePeriod
from status.behavior.time_state_bridge import TimeStateBridge

from status.pet_assets.placeholder_factory import PlaceholderFactory

# 全局实例，允许其他模块访问
instance = None

# 未来可能需要的模块
import math

class StatusPet:
    """Status Pet 应用主类"""
    
    def __init__(self):
        """初始化应用"""
        logger.info("Initializing Status Pet...")
        
        # 设置全局实例，确保在初始化早期就可获取
        global instance
        instance = self
        
        # 创建应用实例
        self.app = QApplication(sys.argv)

        # 创建主窗口
        self.main_window: Optional[MainPetWindow] = None
        
        # 创建系统托盘
        self.system_tray: Optional[SystemTrayManager] = None
        
        # 统计面板 (新增)
        self.stats_panel: Optional[StatsPanel] = None
        
        # 动画
        self.animation_manager = None  # 动画管理器
        self.idle_animation: Optional[Animation] = None  # 待机动画
        self.busy_animation: Optional[Animation] = None  # 忙碌动画
        self.current_animation: Optional[Animation] = None # 当前播放的动画
        self.memory_warning_animation: Optional[Animation] = None # 内存警告动画
        
        # 新增交互动画属性
        self.clicked_animation: Optional[Animation] = None
        self.dragged_animation: Optional[Animation] = None
        self.petted_animation: Optional[Animation] = None
        
        # 状态到动画的映射
        self.state_to_animation_map: Dict[PetState, Optional[Animation]] = {}
        
        # 占位符工厂 - 用于动态加载状态占位符
        self.placeholder_factory = None
        
        # 时间动画管理器
        self.time_animation_manager = None  # 时间相关动画管理器
        
        # 时间行为系统
        self.time_behavior_system = None  # 时间行为系统
        
        # 状态机
        self.state_machine: Optional[PetStateMachine] = None
        
        # 状态适配器
        self.system_state_adapter = None  # 系统状态适配器
        self.interaction_state_adapter = None  # 交互状态适配器
        self.time_state_bridge = None  # 时间状态桥接器
        
        # 交互处理器
        self.interaction_handler: Optional[InteractionHandler] = None  # 交互处理器
        
        # 更新相关
        self._last_update_time = time.perf_counter()
        self._update_timer = QTimer()
        self._update_timer.setInterval(1000)  # 修改此处，原为33ms (约30fps)
        self._update_timer.timeout.connect(self.update)
    
    def create_main_window(self):
        """创建主窗口"""
        # 创建主窗口
        self.main_window = MainPetWindow()
        
        # 设置窗口标题
        self.main_window.setWindowTitle("Status Pet")
        
        # 移除对 self._create_placeholder_image() 的调用
        # 初始图像将由 create_character_sprite 设置
        # if placeholder_image:
        #     self.main_window.set_image(placeholder_image)
        
        logger.info(f"MainPetWindow创建完成。初始大小: {self.main_window.size()}")

        return self.main_window
    
    def create_system_tray(self):
        """创建系统托盘"""
        # 创建系统托盘管理器
        self.system_tray = SystemTrayManager(self.app)
        
        # 设置菜单回调
        self.system_tray.setup_menu(
            show_hide_callback=self.toggle_window_visibility,
            exit_callback=self.exit_app,
            drag_mode_callback=self.set_drag_mode,
            toggle_interaction_callback=self.toggle_pet_interaction
            # toggle_stats_panel_visibility_requested 连接将在下面处理
        )
        
        # 连接 SystemTrayManager 的新信号
        if self.system_tray:
            self.system_tray.toggle_stats_panel_visibility_requested.connect(self._handle_toggle_stats_panel)
            
        logger.info("系统托盘初始化完成")
    
    def toggle_window_visibility(self):
        """切换窗口可见性"""
        if not self.main_window:
            return
        
        if self.main_window.isVisible():
            self.main_window.hide()
        else:
            self.main_window.show()
        
        # 更新托盘菜单项文本
        if self.system_tray:
            self.system_tray.set_window_visibility(self.main_window.isVisible())
    
    def set_drag_mode(self, mode):
        """设置拖动模式
        
        Args:
            mode: 拖动模式 - "smart", "precise", "smooth"
        """
        if self.main_window:
            self.main_window.set_drag_mode(mode)
            logger.info(f"拖动模式已设置为: {mode}")
            
            # 根据不同模式显示不同的提示消息
            messages = {
                "smart": "智能拖动模式：根据拖动速度自动调整平滑度",
                "precise": "精确拖动模式：精确跟随鼠标位置",
                "smooth": "平滑拖动模式：最大程度平滑拖动效果"
            }
            
            if mode in messages and self.system_tray:
                self.system_tray.show_message("拖动模式已更改", messages[mode])
    
    def toggle_pet_interaction(self):
        """切换桌宠窗口的鼠标交互状态"""
        if not self.main_window:
            logger.warning("尝试切换交互状态，但主窗口不存在")
            return

        try:
            current_flags = self.main_window.windowFlags()
            is_transparent = current_flags & Qt.WindowType.WindowTransparentForInput
            
            new_flags: Qt.WindowType = current_flags
            message = ""
            
            if is_transparent:
                # 当前是穿透状态 -> 改为可交互
                new_flags = current_flags & ~Qt.WindowType.WindowTransparentForInput
                logger.info("桌宠交互已启用 (鼠标可点击)")
                message = "交互已启用 (可拖动)"
            else:
                # 当前是可交互状态 -> 改为穿透
                new_flags = current_flags | Qt.WindowType.WindowTransparentForInput
                logger.info("桌宠交互已禁用 (鼠标穿透)")
                message = "交互已禁用 (鼠标穿透)"
            
            # 检查新旧标志是否相同，避免不必要的调用
            if new_flags != current_flags:
                self.main_window.setWindowFlags(new_flags)
                # 必须重新显示窗口以使标志生效
                self.main_window.show()
                logger.debug(f"Window flags set to: {new_flags}")
            else:
                logger.debug("Window flags already set correctly, no change needed.")

            # 显示托盘消息 (如果托盘存在)
            if self.system_tray:
                self.system_tray.show_message("桌宠交互状态", message)
                
        except Exception as e:
            logger.error(f"切换窗口交互状态时出错: {e}", exc_info=True)
    
    def _handle_toggle_stats_panel(self, show: bool):
        """处理切换统计面板的显示状态"""
        if self.stats_panel:
            if show:
                logger.debug("显示统计面板")
                # 更新面板位置并显示
                if self.main_window:
                    self.stats_panel.update_position(self.main_window.pos(), self.main_window.size())
                    self.stats_panel.show()
                # 发布一次最新的统计数据以填充面板
                publish_stats(include_details=True) 
            else:
                logger.debug("隐藏统计面板")
                self.stats_panel.hide()
        else:
            logger.warning("统计面板未初始化，无法切换显示状态。")

    def exit_app(self):
        """退出应用"""
        logger.info("用户请求退出应用程序")
        
        # 关闭时间状态桥接器
        if hasattr(self, 'time_state_bridge') and self.time_state_bridge:
            self.time_state_bridge._shutdown()
            logger.debug("时间状态桥接器已关闭")
        
        # 关闭时间行为系统
        if hasattr(self, 'time_behavior_system') and self.time_behavior_system:
            self.time_behavior_system._shutdown()
            logger.debug("时间行为系统已关闭")
        
        # 关闭交互状态适配器
        if hasattr(self, 'interaction_state_adapter') and self.interaction_state_adapter:
            self.interaction_state_adapter._shutdown()
            logger.debug("交互状态适配器已关闭")
        
        # 关闭系统状态适配器
        if hasattr(self, 'system_state_adapter') and self.system_state_adapter:
            self.system_state_adapter._shutdown()
            logger.debug("系统状态适配器已关闭")
        
        # 关闭交互处理器
        if hasattr(self, 'interaction_handler') and self.interaction_handler:
            self.interaction_handler._shutdown()
            logger.debug("交互处理器已关闭")
        
        self.app.quit()

    def create_character_sprite(self):
        """创建角色精灵和各种状态的动画"""
        logger.info("使用PlaceholderFactory创建角色精灵和各种状态的动画...")

        # 在方法开始时定义 fallback_image
        fallback_image = QImage(64, 64, QImage.Format.Format_ARGB32)
        fallback_image.fill(QColor(0,0,0,0)) # 使用 QColor(0,0,0,0) 表示透明
        _painter = QPainter(fallback_image)
        _painter.setPen(QPen(Qt.GlobalColor.red)) # Qt.GlobalColor.red 是可以的
        _painter.drawText(QRect(0,0,64,64), Qt.AlignmentFlag.AlignCenter, "Anim ERR")
        _painter.end()

        if not self.placeholder_factory:
            logger.error("PlaceholderFactory未初始化。无法创建角色精灵。")
            if self.main_window: # 如果工厂失败，也尝试设置回退图像
                self.main_window.set_image(fallback_image)
            return

        # 使用 PlaceholderFactory 获取各种状态的动画
        self.idle_animation = self.placeholder_factory.get_animation(PetState.IDLE)
        self.busy_animation = self.placeholder_factory.get_animation(PetState.BUSY)
        self.memory_warning_animation = self.placeholder_factory.get_animation(PetState.MEMORY_WARNING)
        self.error_animation = self.placeholder_factory.get_animation(PetState.SYSTEM_ERROR) # 已更正为 SYSTEM_ERROR

        # 获取交互动画
        self.clicked_animation = self.placeholder_factory.get_animation(PetState.CLICKED)
        self.dragged_animation = self.placeholder_factory.get_animation(PetState.DRAGGED)
        self.petted_animation = self.placeholder_factory.get_animation(PetState.PETTED)
        self.hover_animation = self.placeholder_factory.get_animation(PetState.HOVER)

        # 获取时间相关的动画
        self.morning_animation = self.placeholder_factory.get_animation(PetState.MORNING)
        self.noon_animation = self.placeholder_factory.get_animation(PetState.NOON)
        self.afternoon_animation = self.placeholder_factory.get_animation(PetState.AFTERNOON)
        self.evening_animation = self.placeholder_factory.get_animation(PetState.EVENING)
        self.night_animation = self.placeholder_factory.get_animation(PetState.NIGHT)
        
        animations_to_check = {
            "idle": self.idle_animation,
            "busy": self.busy_animation,
            "memory_warning": self.memory_warning_animation,
            "error": self.error_animation, # Corresponds to SYSTEM_ERROR
            "clicked": self.clicked_animation,
            "dragged": self.dragged_animation,
            "petted": self.petted_animation,
            "hover": self.hover_animation,
            "morning": self.morning_animation,
            "noon": self.noon_animation,
            "afternoon": self.afternoon_animation,
            "evening": self.evening_animation,
            "night": self.night_animation,
        }

        all_loaded = True
        for name, anim in animations_to_check.items():
            if anim is None:
                logger.error(f"从PlaceholderFactory加载'{name}'动画失败。")
                all_loaded = False
            else:
                logger.info(f"成功从PlaceholderFactory加载'{name}'动画: {anim.name}, 帧数: {len(anim.frames)}")

        if not all_loaded:
            logger.error("一个或多个动画加载失败。应用程序可能无法按预期运行。")

        # 确定初始图像
        initial_image_to_set = fallback_image # 默认为 fallback

        if self.idle_animation:
            self.current_animation = self.idle_animation
            logger.info(f"默认当前动画设置为: {self.current_animation.name}")
            current_idle_frame = self.current_animation.current_frame()
            if current_idle_frame:
                initial_image_to_set = current_idle_frame
            else:
                logger.error("Idle动画已加载但无法获取当前帧，将使用fallback图像。")
                self.current_animation = Animation(name="fallback_idle_no_frame", frames=[fallback_image], fps=1)
        else:
            logger.error("Idle动画加载失败。宠物将不会有动画，将使用fallback图像。")
            self.current_animation = Animation(name="fallback_idle_failed_load", frames=[fallback_image], fps=1)
        
        # 统一设置图像
        if self.main_window:
            self.main_window.set_image(initial_image_to_set)
        else:
            logger.warning("Main window 不存在，无法设置初始图像。")

        logger.info("角色精灵和动画创建/加载过程完成。")

    def _initialize_state_to_animation_map(self):
        """初始化状态到对应动画的映射表"""
        self.state_to_animation_map = {
            # 系统状态
            PetState.IDLE: self.idle_animation,
            PetState.LIGHT_LOAD: self.idle_animation, # 示例：轻载也用idle
            PetState.MODERATE_LOAD: self.busy_animation,
            PetState.HEAVY_LOAD: self.busy_animation,
            PetState.VERY_HEAVY_LOAD: self.busy_animation, # 也可以是更忙碌的动画
            PetState.CPU_CRITICAL: self.busy_animation, # 也可以是特定危急动画
            PetState.MEMORY_WARNING: self.memory_warning_animation,
            PetState.MEMORY_CRITICAL: self.memory_warning_animation, # 可以是更严重的警告动画
            # 其他系统资源状态可以映射到busy或idle，或专门动画
            PetState.GPU_BUSY: self.busy_animation,
            PetState.GPU_VERY_BUSY: self.busy_animation,
            PetState.DISK_BUSY: self.busy_animation,
            PetState.DISK_VERY_BUSY: self.busy_animation,
            PetState.NETWORK_BUSY: self.busy_animation,
            PetState.NETWORK_VERY_BUSY: self.busy_animation,
            PetState.SYSTEM_IDLE: self.idle_animation,

            # 时间状态
            PetState.MORNING: self.morning_animation,
            PetState.NOON: self.noon_animation,
            PetState.AFTERNOON: self.afternoon_animation,
            PetState.EVENING: self.evening_animation,
            PetState.NIGHT: self.night_animation,

            # 特殊日期状态 (可以映射到时间动画或专门的节日动画)
            PetState.BIRTHDAY: self.morning_animation, # 示例
            PetState.NEW_YEAR: self.noon_animation,    # 示例
            PetState.VALENTINE: self.evening_animation, # 示例

            # 交互状态
            PetState.CLICKED: self.clicked_animation,
            PetState.DRAGGED: self.dragged_animation,
            PetState.PETTED: self.petted_animation,
            PetState.HOVER: self.hover_animation,  # 新增HOVER状态映射
            PetState.HAPPY: self.petted_animation, # 示例：开心时用petted动画
            PetState.SAD: self.idle_animation,   # 示例：悲伤时用idle
            PetState.ANGRY: self.busy_animation, # 示例：生气时用busy
            PetState.PLAY: self.idle_animation,  # 示例：玩耍用idle，未来应有专门play动画
            
            # 以下状态已在 PetState 中注释掉，因此在此处也注释掉
            # PetState.HEAD_CLICKED: self.clicked_animation, 
            # PetState.BODY_CLICKED: self.clicked_animation,
            # PetState.TAIL_CLICKED: self.clicked_animation,
            # PetState.HEAD_PETTED: self.petted_animation,
            # PetState.BODY_PETTED: self.petted_animation,
            # PetState.TAIL_PETTED: self.petted_animation,
        }
        
        # 使用PlaceholderFactory加载哪些还没有专门定义的状态占位符
        # 例如，如果有HAPPY状态的占位符文件，它将被加载
        if self.placeholder_factory:
            for state in PetState:
                if state not in self.state_to_animation_map:
                    anim = self.placeholder_factory.get_animation(state)
                    if anim:
                        logger.debug(f"从PlaceholderFactory加载{state.name}状态的占位符动画")
                        self.state_to_animation_map[state] = anim
        
        logger.debug("状态到动画的映射表已初始化")

    def update(self):
        """应用主更新循环，由QTimer调用"""
        current_time = time.perf_counter()
        dt = current_time - self._last_update_time
        self._last_update_time = current_time

        # 1. 状态机驱动的更新 (如果未来有需要，例如连续状态更新)
        # if self.state_machine:
        #     self.state_machine.tick(dt)

        # 2. 处理动画播放
        if self.current_animation:
            self.current_animation.update(dt) # Animation.update 控制帧切换
            
            # 如果是一次性交互动画播放完毕，则切换到背景状态对应的动画
            if not self.current_animation.is_looping and \
               not self.current_animation.is_playing and \
               (self.current_animation == self.clicked_animation or self.current_animation == self.petted_animation):
                logger.debug(f"一次性动画 {self.current_animation.name} 在update中检测到播放完毕。切换到背景动画。")
                
                current_actual_state = PetState.IDLE # 默认回到IDLE
                if self.state_machine: # 检查state_machine是否存在
                    current_actual_state = self.state_machine.get_state() 
                else:
                    logger.warning("Update: 状态机不可用，默认回到IDLE动画。")
                
                background_animation = self.state_to_animation_map.get(current_actual_state, self.idle_animation)
                
                if background_animation and background_animation != self.current_animation:
                    logger.info(f"一次性动画结束，切换到背景动画: {background_animation.name} (基于状态: {current_actual_state.name})")
                    # self.current_animation.stop() # 旧动画已经is_playing=False了，不需要stop
                    self.current_animation = background_animation
                    self.current_animation.reset()
                    self.current_animation.play()
                elif not self.current_animation.is_playing: 
                    # 如果没有找到特定的背景动画，或者目标就是当前（已停止的）动画，则确保idle动画播放
                    logger.debug(f"未找到特定背景动画或目标是当前已停止动画 {self.current_animation.name}。确保idle动画播放。")
                    if self.idle_animation and self.current_animation != self.idle_animation:
                        self.current_animation = self.idle_animation
                        self.current_animation.reset()
                        self.current_animation.play()
                    elif self.idle_animation and not self.idle_animation.is_playing: # 如果当前就是idle但没播放
                        self.idle_animation.reset()
                        self.idle_animation.play()

            # 3. 更新主窗口图像
            if self.main_window and self.current_animation: # 再次检查 self.current_animation 是否有效
                current_frame_image = self.current_animation.current_frame() # 使用正确的方法名
                if current_frame_image and not current_frame_image.isNull():
                    self.main_window.set_image(current_frame_image)
                # else:
                    # logger.warning(f"当前动画 {self.current_animation.name} 的当前帧图像无效。") # 暂时注释掉，新的逻辑会覆盖

            # 如果没有当前动画或当前帧无效，尝试设置idle
            needs_fallback = False
            fallback_reason = ""

            if not self.current_animation:
                needs_fallback = True
                fallback_reason = "self.current_animation is None"
            elif self.current_animation.current_frame() is None:
                needs_fallback = True
                fallback_reason = f"Animation '{self.current_animation.name}' current_frame() is None"
            elif self.current_animation.current_frame().isNull():
                needs_fallback = True
                fallback_reason = f"Animation '{self.current_animation.name}' current_frame().isNull() is True"

            if needs_fallback:
                if self.main_window and self.idle_animation:
                    # 只有当真实需要切换到idle时才记录这个warning，避免日志刷屏
                    if self.current_animation != self.idle_animation or not self.idle_animation.is_playing:
                        logger.warning(f"动画回退 ({fallback_reason})，切换到idle动画。")
                    self.current_animation = self.idle_animation
                    if not self.current_animation.is_playing: # 确保idle动画在播放
                        self.current_animation.reset()
                        self.current_animation.play()
                    
                    current_frame_image = self.current_animation.current_frame()
                    if current_frame_image and not current_frame_image.isNull():
                        self.main_window.set_image(current_frame_image)
                    else:
                        logger.error("CRITICAL: 回退到Idle动画后，其第一帧也无效！无法显示宠物。") 
                else:
                    logger.error(f"CRITICAL: 动画回退 ({fallback_reason})，且无法回退到idle动画 (main_window or idle_animation is None)。无法显示宠物。")

        # 4. 更新统计面板 (如果可见且有数据)
        if self.stats_panel and self.main_window and self.stats_panel.isVisible():
            # 发布最新的系统统计数据
            publish_stats(include_details=True)  
            
            # 更新统计面板位置，使用存储的位置比较来检测移动
            pet_pos = self.main_window.pos()
            pet_size = self.main_window.size()
            
            # 存储主窗口位置，用于检测窗口是否移动
            if not hasattr(self, '_last_window_pos') or not hasattr(self, '_last_window_size'):
                self._last_window_pos = pet_pos
                self._last_window_size = pet_size
                self.stats_panel.update_position(pet_pos, pet_size)
                logger.debug(f"初始化统计面板位置: {pet_pos}，大小: {pet_size}")
            elif self._last_window_pos != pet_pos or self._last_window_size != pet_size:
                self._last_window_pos = pet_pos
                self._last_window_size = pet_size
                self.stats_panel.update_position(pet_pos, pet_size)
                logger.debug(f"已更新统计面板位置，主窗口移动到: {pet_pos}，大小: {pet_size}")

        # 更新托盘可见性状态 (这个逻辑似乎不属于高频update，可以移到实际切换可见性的地方)
        if self.system_tray and self.main_window:
            self.system_tray.set_window_visibility(self.main_window.isVisible())
    
    def initialize(self):
        """初始化应用"""
        # 在这里导入Application，避免循环导入问题
        from status.core.app import Application
        from status.ui.stats_panel import StatsPanel # 导入 StatsPanel
        from status.behavior.system_state_adapter import SystemStateAdapter # 导入系统状态适配器
        from status.behavior.interaction_state_adapter import InteractionStateAdapter # 导入交互状态适配器
        from status.behavior.time_based_behavior import TimeBasedBehaviorSystem # 导入时间行为系统
        from status.behavior.time_state_bridge import TimeStateBridge # 导入时间状态桥接器
        
        logger.info("Initializing application components...")
        
        # 创建主窗口
        self.create_main_window()
        
        # 创建系统托盘
        self.create_system_tray()
        
        # 创建 StatsPanel 实例 (但不显示)
        self.stats_panel = StatsPanel()
        
        # 初始化占位符工厂 (移到 create_character_sprite 之前)
        self.placeholder_factory = PlaceholderFactory()
        logger.info("占位符工厂已初始化")

        # 创建角色精灵/动画 (现在 PlaceholderFactory 已初始化)
        self.create_character_sprite()
        
        # 初始化状态到动画的映射表 (在动画加载后进行)
        self._initialize_state_to_animation_map()
        
        # 创建状态机
        self.state_machine = PetStateMachine()
        
        # 注册状态变化事件监听
        if self.state_machine and self.state_machine.event_system:
            self.state_machine.event_system.register_handler(EventType.STATE_CHANGED, self._handle_state_change)
            logger.info("已注册状态变化事件监听器")
        else:
            logger.warning("状态机或其事件系统未初始化，无法注册状态变化监听器")
        
        # 创建系统状态适配器
        self.system_state_adapter = SystemStateAdapter(self.state_machine)
        # 初始化系统状态适配器
        self.system_state_adapter.activate()
        logger.info("系统状态适配器已初始化")
        
        # 创建交互状态适配器
        self.interaction_state_adapter = InteractionStateAdapter(self.state_machine)
        # 初始化交互状态适配器
        self.interaction_state_adapter.activate()
        logger.info("交互状态适配器已初始化")
        
        # 创建时间行为系统（每分钟检查一次时间变化）
        self.time_behavior_system = TimeBasedBehaviorSystem(check_interval=60)
        # 初始化时间行为系统 (不要直接调用_initialize方法，使用activate方法)
        self.time_behavior_system.activate()
        logger.info("时间行为系统已激活")
        
        # 创建时间动画管理器
        from status.animation.time_animation_manager import TimeAnimationManager
        self.time_animation_manager = TimeAnimationManager()
        
        # 将已创建的时间动画添加到管理器中
        from status.behavior.time_based_behavior import TimePeriod
        if hasattr(self, 'morning_animation') and self.morning_animation:
            self.time_animation_manager.time_period_animations[TimePeriod.MORNING] = self.morning_animation
        
        if hasattr(self, 'noon_animation') and self.noon_animation:
            self.time_animation_manager.time_period_animations[TimePeriod.NOON] = self.noon_animation
        
        if hasattr(self, 'afternoon_animation') and self.afternoon_animation:
            self.time_animation_manager.time_period_animations[TimePeriod.AFTERNOON] = self.afternoon_animation
        
        if hasattr(self, 'evening_animation') and self.evening_animation:
            self.time_animation_manager.time_period_animations[TimePeriod.EVENING] = self.evening_animation
        
        if hasattr(self, 'night_animation') and self.night_animation:
            self.time_animation_manager.time_period_animations[TimePeriod.NIGHT] = self.night_animation
            
        # 添加特殊日期动画 - 可以使用现有的动画作为临时替代
        # 生日使用morning动画作为临时动画
        if hasattr(self, 'morning_animation') and self.morning_animation:
            self.time_animation_manager.special_date_animations["birthday"] = self.morning_animation
        
        # 新年使用noon动画作为临时动画（比较明亮）
        if hasattr(self, 'noon_animation') and self.noon_animation:
            self.time_animation_manager.special_date_animations["new_year"] = self.noon_animation
            
        # 情人节使用evening动画作为临时动画
        if hasattr(self, 'evening_animation') and self.evening_animation:
            self.time_animation_manager.special_date_animations["valentine"] = self.evening_animation
        
        logger.info("时间动画管理器已初始化")
        
        # 连接时间行为系统信号到时间动画管理器
        if hasattr(self.time_behavior_system, 'signals') and self.time_behavior_system.signals:
            self.time_behavior_system.signals.time_period_changed.connect(
                self.time_animation_manager.on_time_period_changed)
            self.time_behavior_system.signals.special_date_triggered.connect(
                self.time_animation_manager.on_special_date_triggered)
            logger.info("时间行为系统信号已连接到时间动画管理器")
            
            # 获取当前时间段，记录日志
            current_period = self.time_behavior_system.get_current_period()
            logger.info(f"当前时间段: {current_period.name}")
            
            # 检查接下来的特殊日期
            upcoming_dates = self.time_behavior_system.get_upcoming_special_dates(days=30)
            if upcoming_dates:
                dates_info = ", ".join([f"{date[0].name} ({date[1].strftime('%Y-%m-%d')})" for date in upcoming_dates[:3]])
                logger.info(f"未来30天内的特殊日期(前3个): {dates_info}")
                
        # 创建时间状态桥接器
        self.time_state_bridge = TimeStateBridge(
            pet_state_machine=self.state_machine,
            time_system=self.time_behavior_system
        )
        # 初始化时间状态桥接器
        self.time_state_bridge.activate()
        logger.info("时间状态桥接器已初始化")
        
        # 创建交互处理器
        self.interaction_handler = InteractionHandler(parent_window=self.main_window)
        # 初始化交互处理器
        self.interaction_handler.activate()
        logger.info("交互处理器已初始化")
        
        # 连接窗口事件到交互处理器
        self.connect_interaction_handler()
        
        # 显示窗口
        if self.main_window:
            self.main_window.show()
            logger.info("MainPetWindow shown.")
        
        # 更新系统托盘菜单项状态
        if self.system_tray and self.main_window:
            self.system_tray.set_window_visibility(self.main_window.isVisible())
            
        # 启动更新定时器 (之前未启动)
        logger.info("启动更新定时器，间隔: 1000ms (约10fps)") # 修改日志消息
        self._update_timer.start()
    
    def _handle_state_change(self, event: Event):
        """处理状态机状态变化事件，切换动画"""
        if not hasattr(event, 'data') or not isinstance(event.data, dict):
            logger.warning("_handle_state_change: 事件数据无效")
            return

        current_state_value = event.data.get('current_state')
        if current_state_value is None:
            logger.warning("_handle_state_change: 事件数据中缺少 current_state")
            return
        
        try:
            current_pet_state = PetState(current_state_value)
        except ValueError:
            logger.warning(f"_handle_state_change: 无效的状态值 {current_state_value}")
            return

        logger.debug(f"状态变化处理: 新状态 {current_pet_state.name}")

        # 检查当前动画是否是一次性交互动画且已播放完毕
        # 这个检查主要用于避免在一次性动画刚播完时，如果状态没变，又被这个事件处理器重新触发播放
        if self.current_animation and \
           not self.current_animation.is_looping and \
           not self.current_animation.is_playing and \
           (self.current_animation == self.clicked_animation or self.current_animation == self.petted_animation):
            
            target_animation_for_new_state = self.state_to_animation_map.get(current_pet_state)
            if target_animation_for_new_state == self.current_animation:
                 logger.debug(f"新状态 {current_pet_state.name} 的目标动画与刚播放完毕的一次性动画相同，不重新触发。交由update逻辑处理后续。")
                 return 

        # 尝试获取目标动画，如果映射表中没有，尝试使用占位符工厂动态加载
        target_animation = self.state_to_animation_map.get(current_pet_state)
        if not target_animation and self.placeholder_factory:
            # 尝试动态加载该状态的占位符动画
            anim = self.placeholder_factory.get_animation(current_pet_state)
            if anim:
                logger.info(f"动态加载了{current_pet_state.name}状态的占位符动画")
                self.state_to_animation_map[current_pet_state] = anim
                target_animation = anim

        if target_animation and target_animation != self.current_animation:
            logger.info(f"切换动画: 从 {self.current_animation.name if self.current_animation else 'None'} 到 {target_animation.name}")
            if self.current_animation:
                self.current_animation.stop() # 停止并重置旧动画
            
            self.current_animation = target_animation
            self.current_animation.reset() # 确保从第一帧开始
            self.current_animation.play()
        elif not target_animation:
            logger.warning(f"状态 {current_pet_state.name} 没有配置对应的动画，将使用idle动画。")
            if self.current_animation != self.idle_animation and self.idle_animation:
                if self.current_animation:
                    self.current_animation.stop()
                self.current_animation = self.idle_animation
                self.current_animation.reset()
                self.current_animation.play()
    
    def connect_interaction_handler(self):
        """将窗口的鼠标事件连接到交互处理器"""
        if not self.main_window or not hasattr(self, 'interaction_handler') or not self.interaction_handler:
            logger.warning("主窗口或交互处理器未初始化，无法连接事件")
            return

        if not hasattr(self.interaction_handler, 'handle_mouse_event'):
            logger.warning("交互处理器没有handle_mouse_event方法，无法连接事件")
            return
            
        try:
            handler = self.interaction_handler
            # assert isinstance(handler, InteractionHandler), "交互处理器类型错误" # InteractionHandler可能未导入
            
            self.main_window.clicked.connect(
                lambda pos: handler.handle_mouse_event(
                    self._create_mouse_event(pos, Qt.MouseButton.LeftButton), 'press'))
            
            self.main_window.double_clicked.connect(
                lambda pos: handler.handle_mouse_event(
                    self._create_mouse_event(pos, Qt.MouseButton.LeftButton), 'doubleclick'))
            
            self.main_window.dragged.connect(
                lambda pos: handler.handle_mouse_event(
                    self._create_mouse_event(pos, Qt.MouseButton.LeftButton), 'move'))
            
            self.main_window.dropped.connect(
                lambda pos: handler.handle_mouse_event(
                    self._create_mouse_event(pos, Qt.MouseButton.LeftButton), 'release'))
            
            # 连接鼠标移动事件，用于hover交互
            self.main_window.mouse_moved.connect(
                lambda pos: handler.handle_mouse_event(
                    self._create_mouse_event(pos, Qt.MouseButton.NoButton), 'move'))
            
            logger.info("已连接窗口鼠标事件到交互处理器，包括hover交互")
        except Exception as e: # 更通用的异常捕获
            logger.error(f"连接鼠标事件失败: {e}", exc_info=True)
            return

    def _create_mouse_event(self, pos, button_type):
        """创建鼠标事件对象用于传递给交互处理器
        
        Args:
            pos: 鼠标位置（QPoint）
            button_type: 按钮类型
            
        Returns:
            QMouseEvent: 创建的鼠标事件
        """
        from PySide6.QtCore import QPointF, Qt, QEvent
        from PySide6.QtGui import QMouseEvent, QCursor
        
        # 获取全局光标位置
        global_pos = QCursor.pos()
        local_pos = QPointF(pos)
        
        # 使用非弃用的构造函数创建QMouseEvent
        return QMouseEvent(
            QEvent.Type.MouseButtonPress,  # 事件类型，实际由handle_mouse_event的event_type参数决定
            local_pos,                     # 本地位置
            local_pos,                     # 场景位置（使用相同的本地位置）
            global_pos,                    # 全局位置
            button_type,                   # 按钮类型
            button_type,                   # 按钮状态
            Qt.KeyboardModifier.NoModifier # 键盘修饰符
        )
    
    def run(self):
        """运行应用"""
        try:
            # 初始化
            self.initialize()
        
            # 在启动应用前检查时间行为系统是否正常
            if hasattr(self, 'time_behavior_system') and self.time_behavior_system:
                logger.info("时间行为系统集成测试通过，准备进入事件循环")
            
            # 进入事件循环
            return self.app.exec()
        except Exception as e:
            logger.error(f"应用程序运行时发生错误: {e}", exc_info=True)
            return 1

def main():
    """程序入口函数"""
    # 启动应用
    app = StatusPet()
    
    # 将应用实例保存到全局变量
    global instance
    instance = app
    
    # 运行应用
    return app.run()

if __name__ == "__main__":
    sys.exit(main())