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
----
"""

import logging
import sys
import time
from typing import Optional, Dict, Any, List, Tuple

import os
import random

from PySide6.QtWidgets import QApplication, QMainWindow, QSystemTrayIcon, QMenu, QColorDialog
from PySide6.QtGui import QIcon, QPixmap, QColor, QPainter, QPen, QBrush, QAction, QImage, QMouseEvent
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

from status.behavior.pet_state import PetState
from status.behavior.pet_state_machine import PetStateMachine
from status.behavior.system_state_adapter import SystemStateAdapter

from status.monitoring.system_monitor import publish_stats

from status.interaction.interaction_handler import InteractionHandler
from status.behavior.interaction_tracker import InteractionTracker

from status.behavior.time_based_behavior import TimeBasedBehaviorSystem
from status.behavior.time_state_bridge import TimeStateBridge

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
        self._update_timer.setInterval(1000)  # 修改此处，原为16ms
        self._update_timer.timeout.connect(self.update)
    
    def create_main_window(self):
        """创建主窗口"""
        # 创建主窗口
        self.main_window = MainPetWindow()
        
        # 设置窗口标题
        self.main_window.setWindowTitle("Status Pet")
        
        # 创建并设置一个占位符图像
        placeholder_image = self._create_placeholder_image()
        if placeholder_image:
            self.main_window.set_image(placeholder_image)
        
        logger.info(f"MainPetWindow created. Initial size: {self.main_window.size()}")

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
        """处理显示/隐藏统计面板的请求。"""
        if not self.stats_panel or not self.main_window:
            logger.warning("StatsPanel 或主窗口不存在，无法切换统计面板可见性。")
            return

        if show:
            # 不再需要手动计算位置，面板会自动跟随主窗口
            # 只需要在主窗口当前位置显示面板
            if self.main_window.isVisible():
                # 获取当前主窗口位置和大小
                pet_pos = self.main_window.pos()
                pet_size = self.main_window.size()
                
                logger.info(f"展示统计面板 - 主窗口当前位置: {pet_pos}, 大小: {pet_size}")
                
                # 主动调用更新位置方法
                self.stats_panel.parent_window_pos = pet_pos
                self.stats_panel.parent_window_size = pet_size
                self.stats_panel.update_position(pet_pos, pet_size)
                
                # 显示面板，使用show_panel方法
                panel_pos = QPoint(pet_pos.x() + pet_size.width() + 10, pet_pos.y())
                self.stats_panel.show_panel(panel_pos)
                
                # 确保面板可见
                if not self.stats_panel.isVisible():
                    logger.warning("StatsPanel.isVisible() 仍然是 False，尝试直接调用 show()")
                    self.stats_panel.show()
                    self.stats_panel.raise_()
                    self.stats_panel.activateWindow()
                
                logger.info(f"显示统计面板于 {pet_pos}，面板实际位置: {self.stats_panel.pos()}")
                logger.info(f"统计面板可见状态: {self.stats_panel.isVisible()}, 几何属性: {self.stats_panel.geometry()}")
            else:
                logger.warning("主窗口不可见，无法显示统计面板。")
        else:
            self.stats_panel.hide_panel()
            logger.info("隐藏统计面板")
            
        # 确保托盘菜单项的文本状态同步 (这一步已由 SystemTrayManager 内部处理)
        # if self.system_tray and hasattr(self.system_tray, 'toggle_stats_action'):
        #     self.system_tray.toggle_stats_action.setChecked(show)

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
    
    def _create_placeholder_image(self, width=64, height=64) -> Optional[QImage]:
        """创建一个占位符图像
        
        Args:
            width: 图像宽度
            height: 图像高度
            
        Returns:
            QImage: 创建的图像，如果失败则为None
        """
        try:
            logger.info("Creating placeholder image for pet")

            # 创建一个QImage
            image = QImage(width, height, QImage.Format.Format_ARGB32)
            image.fill(QColor(0, 0, 0, 0))  # 透明背景
            
            # 添加绘制代码，使图像可见
            painter = QPainter(image)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            
            # 绘制猫咪轮廓
            painter.setPen(QPen(QColor(70, 70, 70), 2))
            painter.setBrush(QBrush(QColor(200, 200, 200, 220)))
            
            # 绘制头部（圆形）
            painter.drawEllipse(10, 10, 44, 44)
            
            # 绘制耳朵
            painter.setBrush(QBrush(QColor(180, 180, 180, 220)))
            # 左耳
            painter.drawPolygon([
                QPoint(15, 15),
                QPoint(25, 5),
                QPoint(30, 15)
            ])
            # 右耳
            painter.drawPolygon([
                QPoint(49, 15),
                QPoint(39, 5),
                QPoint(34, 15)
            ])
            
            # 绘制眼睛
            painter.setPen(QPen(QColor(30, 30, 30), 1))
            painter.setBrush(QBrush(QColor(30, 30, 30)))
            # 左眼
            painter.drawEllipse(20, 25, 8, 8)
            # 右眼
            painter.drawEllipse(36, 25, 8, 8)
            
            # 绘制鼻子
            painter.setBrush(QBrush(QColor(255, 150, 150)))
            painter.drawEllipse(29, 35, 6, 4)

            # 绘制嘴
            painter.setPen(QPen(QColor(70, 70, 70), 1))
            painter.drawLine(32, 39, 32, 42)
            painter.drawLine(32, 42, 28, 45)
            painter.drawLine(32, 42, 36, 45)
            
            painter.end()
            
            logger.info(f"Created placeholder image: {width}x{height}")
            return image
        except Exception as e:
            logger.error(f"Failed to create placeholder image: {str(e)}")
            return None
    
    def _create_busy_placeholder_image(self, width=64, height=64) -> Optional[QImage]:
        """创建一个代表'忙碌'状态的占位符图像
        
        Args:
            width: 图像宽度
            height: 图像高度
            
        Returns:
            QImage: 创建的图像，如果失败则为None
        """
        try:
            logger.debug("Creating busy placeholder image for pet") # Use debug level

            # 创建一个QImage
            image = QImage(width, height, QImage.Format.Format_ARGB32)
            image.fill(QColor(0, 0, 0, 0))  # 透明背景
            
            # 添加绘制代码，使图像可见
            painter = QPainter(image)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            
            # 绘制猫咪轮廓 (与idle相同)
            painter.setPen(QPen(QColor(70, 70, 70), 2))
            painter.setBrush(QBrush(QColor(200, 200, 200, 220)))
            painter.drawEllipse(10, 10, 44, 44) # Head
            painter.setBrush(QBrush(QColor(180, 180, 180, 220)))
            painter.drawPolygon([QPoint(15, 15), QPoint(25, 5), QPoint(30, 15)]) # Left Ear
            painter.drawPolygon([QPoint(49, 15), QPoint(39, 5), QPoint(34, 15)]) # Right Ear
            
            # --- 修改眼睛 ---
            painter.setPen(QPen(QColor(30, 30, 30), 1))
            painter.setBrush(QBrush(QColor(30, 30, 30)))
            # 左眼 (更窄)
            painter.drawEllipse(20, 28, 8, 4) # y=28, height=4
            # 右眼 (更窄)
            painter.drawEllipse(36, 28, 8, 4) # y=28, height=4
            # --- 结束修改 ---
            
            # 绘制鼻子 (与idle相同)
            painter.setBrush(QBrush(QColor(255, 150, 150)))
            painter.drawEllipse(29, 35, 6, 4)

            # 绘制嘴 (与idle相同)
            painter.setPen(QPen(QColor(70, 70, 70), 1))
            painter.drawLine(32, 39, 32, 42)
            painter.drawLine(32, 42, 28, 45)
            painter.drawLine(32, 42, 36, 45)
            
            painter.end()
            
            logger.debug(f"Created busy placeholder image: {width}x{height}") # Use debug level
            return image
        except Exception as e:
            logger.error(f"Failed to create busy placeholder image: {str(e)}")
            return None
    
    def _create_memory_warning_placeholder_image(self, width=64, height=64) -> Optional[QImage]:
        """创建一个代表'内存警告'状态的占位符图像"""
        try:
            logger.debug("Creating memory warning placeholder image for pet")

            image = QImage(width, height, QImage.Format.Format_ARGB32)
            image.fill(QColor(0, 0, 0, 0))  # 透明背景
            
            painter = QPainter(image)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            
            # --- 修改主体颜色为橙红色 --- 
            painter.setPen(QPen(QColor(150, 50, 0), 2)) # 深橙色边框
            painter.setBrush(QBrush(QColor(255, 100, 0, 220))) # 橙红色填充
            # --- 结束修改 --- 
            
            painter.drawEllipse(10, 10, 44, 44) # Head
            
            # 耳朵颜色也调整
            painter.setBrush(QBrush(QColor(220, 80, 0, 220)))
            painter.drawPolygon([QPoint(15, 15), QPoint(25, 5), QPoint(30, 15)]) # Left Ear
            painter.drawPolygon([QPoint(49, 15), QPoint(39, 5), QPoint(34, 15)]) # Right Ear
            
            # 眼睛 (可以夸张一点，比如用X表示或者瞪大的眼睛)
            painter.setPen(QPen(QColor(50, 0, 0), 1))
            painter.setBrush(QBrush(QColor(50, 0, 0)))
            # 左眼 (瞪大)
            painter.drawEllipse(18, 23, 12, 12) 
            # 右眼 (瞪大)
            painter.drawEllipse(34, 23, 12, 12)
            # 眼白部分可以稍微亮一点
            painter.setBrush(QBrush(QColor(255, 200, 200)))
            painter.drawEllipse(21, 26, 6, 6)
            painter.drawEllipse(37, 26, 6, 6)
            
            # 鼻子 (与idle相同)
            painter.setBrush(QBrush(QColor(255, 150, 150)))
            painter.drawEllipse(29, 35, 6, 4)

            # 嘴 (张开表示惊讶/警告)
            painter.setPen(QPen(QColor(70, 70, 70), 1))
            painter.setBrush(QBrush(QColor(70,70,70)))
            painter.drawEllipse(28, 40, 8, 8) # 张开的嘴
            
            painter.end()
            
            logger.debug(f"Created memory warning placeholder image: {width}x{height}")
            return image
        except Exception as e:
            logger.error(f"Failed to create memory warning placeholder image: {str(e)}")
            return None

    def create_character_sprite(self):
        """创建角色精灵/动画"""
        try:
            # 创建待机动画
            self.idle_animation = Animation()
            idle_image = self._create_placeholder_image()
            if idle_image:
                self.idle_animation.add_frame(idle_image)
                self.idle_animation.set_loop(True)
                
            # 创建忙碌动画
            self.busy_animation = Animation()
            busy_image = self._create_busy_placeholder_image()
            if busy_image:
                self.busy_animation.add_frame(busy_image)
                self.busy_animation.set_loop(True)
                
            # 创建内存警告动画
            self.memory_warning_animation = Animation()
            memory_warning_image = self._create_memory_warning_placeholder_image()
            if memory_warning_image:
                self.memory_warning_animation.add_frame(memory_warning_image)
                self.memory_warning_animation.set_loop(True)
            
            # 创建早晨动画
            self.morning_animation = Animation()
            morning_image = self._create_morning_placeholder_image()
            if morning_image:
                self.morning_animation.add_frame(morning_image)
                self.morning_animation.set_loop(True)
                
            # 创建中午动画
            self.noon_animation = Animation()
            noon_image = self._create_noon_placeholder_image()
            if noon_image:
                self.noon_animation.add_frame(noon_image)
                self.noon_animation.set_loop(True)
                
            # 创建下午动画（新增）
            self.afternoon_animation = Animation()
            # 目前复用中午图像，可以在未来创建专用的下午图像
            afternoon_image = self._create_noon_placeholder_image(color_adjust=True)
            if afternoon_image:
                self.afternoon_animation.add_frame(afternoon_image)
                self.afternoon_animation.set_loop(True)
                
            # 创建晚上动画（新增）
            self.evening_animation = Animation()
            # 创建较暗的傍晚效果
            evening_image = self._create_night_placeholder_image(make_darker=False)
            if evening_image:
                self.evening_animation.add_frame(evening_image)
                self.evening_animation.set_loop(True)
                
            # 创建深夜动画
            self.night_animation = Animation()
            night_image = self._create_night_placeholder_image()
            if night_image:
                self.night_animation.add_frame(night_image)
                self.night_animation.set_loop(True)
                
            # 设置初始动画为待机
            self.current_animation = self.idle_animation
            if self.current_animation:
                self.current_animation.play()
                
            logger.info("Character animations created successfully")
        except Exception as e:
            logger.error(f"Failed to create character animations: {e}")

    def _create_morning_placeholder_image(self, width=64, height=64) -> Optional[QImage]:
        """创建一个代表'早晨'状态的占位符图像"""
        try:
            logger.debug("Creating morning placeholder image for pet")

            image = QImage(width, height, QImage.Format.Format_ARGB32)
            image.fill(QColor(0, 0, 0, 0))  # 透明背景
            
            painter = QPainter(image)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            
            # 基础形状与普通状态相同
            painter.setPen(QPen(QColor(70, 70, 70), 2))
            # 使用暖色调（黄色和橙色）来表示早晨的阳光
            painter.setBrush(QBrush(QColor(255, 230, 180, 220)))
            
            # 绘制头部（圆形）
            painter.drawEllipse(10, 10, 44, 44)
            
            # 绘制耳朵
            painter.setBrush(QBrush(QColor(255, 210, 160, 220)))
            # 左耳
            painter.drawPolygon([QPoint(15, 15), QPoint(25, 5), QPoint(30, 15)])
            # 右耳
            painter.drawPolygon([QPoint(49, 15), QPoint(39, 5), QPoint(34, 15)])
            
            # 绘制眼睛（睁开的明亮眼睛）
            painter.setPen(QPen(QColor(30, 30, 30), 1))
            painter.setBrush(QBrush(QColor(30, 30, 30)))
            painter.drawEllipse(20, 25, 8, 8)  # 左眼
            painter.drawEllipse(36, 25, 8, 8)  # 右眼
            
            # 添加一点点高光表示阳光
            painter.setBrush(QBrush(QColor(255, 255, 255, 180)))
            painter.setPen(QPen(QColor(255, 255, 255, 0)))
            painter.drawEllipse(22, 27, 3, 3)  # 左眼高光
            painter.drawEllipse(38, 27, 3, 3)  # 右眼高光
            
            # 绘制鼻子
            painter.setPen(QPen(QColor(70, 70, 70), 1))
            painter.setBrush(QBrush(QColor(255, 150, 150)))
            painter.drawEllipse(29, 35, 6, 4)
            
            # 绘制微笑的嘴
            painter.setPen(QPen(QColor(70, 70, 70), 1))
            painter.drawArc(QRect(25, 38, 14, 10), 0, -180 * 16)  # 微笑的弧线
            
            # 绘制阳光光芒（额外装饰）
            painter.setPen(QPen(QColor(255, 200, 0, 100), 1))
            for i in range(8):
                angle = i * 45
                rad = angle * 3.14159 / 180
                x1 = width / 2 + (width / 2 - 5) * math.cos(rad)
                y1 = height / 2 + (height / 2 - 5) * math.sin(rad)
                x2 = width / 2 + (width / 2 + 5) * math.cos(rad)
                y2 = height / 2 + (height / 2 + 5) * math.sin(rad)
                painter.drawLine(int(x1), int(y1), int(x2), int(y2))
            
            painter.end()
            
            logger.debug(f"Created morning placeholder image: {width}x{height}")
            return image
        except Exception as e:
            logger.error(f"Failed to create morning placeholder image: {str(e)}")
            return None
            
    def _create_noon_placeholder_image(self, width=64, height=64, color_adjust=False) -> Optional[QImage]:
        """创建一个代表'中午'/'下午'状态的占位符图像
        
        Args:
            width: 图像宽度
            height: 图像高度
            color_adjust: 是否调整颜色（用于区分中午和下午）
        """
        try:
            # 创建透明图像
            image = QImage(width, height, QImage.Format.Format_ARGB32)
            image.fill(Qt.GlobalColor.transparent)
            
            # 创建画布
            painter = QPainter(image)
            
            # 启用抗锯齿
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            
            # 绘制太阳
            if color_adjust:
                # 下午的太阳颜色偏橙
                sun_color = QColor(255, 180, 80)  # 橙色
            else:
                # 中午的太阳颜色偏黄
                sun_color = QColor(255, 220, 0)  # 亮黄色
            
            painter.setBrush(QBrush(sun_color))
            painter.setPen(Qt.PenStyle.NoPen)
            
            # 太阳位置，根据是中午还是下午调整
            if color_adjust:
                # 下午的太阳偏右下
                sun_x, sun_y = 48, 15  # 右边45度位置
            else:
                # 中午的太阳在顶部中央
                sun_x, sun_y = 32, 10  # 顶部中央
                
            painter.drawEllipse(sun_x, sun_y, 12, 12)
            
            # 绘制身体
            painter.setBrush(QBrush(QColor(200, 200, 200)))
            painter.setPen(QPen(QColor(70, 70, 70), 1))
            painter.drawEllipse(20, 25, 24, 20)
            
            # 绘制头部
            painter.drawEllipse(32, 18, 16, 16)
            
            # 绘制耳朵
            painter.drawEllipse(34, 10, 8, 8)
            painter.drawEllipse(42, 12, 8, 8)
            
            # 绘制眼睛
            if color_adjust:
                # 下午状态 - 半睁眼
                painter.setBrush(QBrush(QColor(70, 70, 70)))
                painter.drawEllipse(35, 20, 3, 2)
                painter.drawEllipse(42, 21, 3, 2)
            else:
                # 中午状态 - 眯眼（炎热）
                painter.setBrush(QBrush(QColor(70, 70, 70)))
                painter.drawEllipse(35, 21, 3, 1)
                painter.drawEllipse(42, 22, 3, 1)
            
            # 绘制嘴巴 - 因炎热伸出舌头
            painter.setBrush(QBrush(QColor(255, 150, 150)))
            painter.drawEllipse(38, 26, 4, 2)
            
            # 额外的效果
            if color_adjust:
                # 下午 - 添加一些小云和阴影
                painter.setBrush(QBrush(QColor(255, 255, 255, 180)))
                painter.drawEllipse(10, 15, 12, 8)
                painter.drawEllipse(15, 12, 10, 7)
            else:
                # 中午 - 添加热气线条
                painter.setPen(QPen(QColor(255, 200, 100, 150), 1, Qt.PenStyle.DashLine))
                painter.drawLine(28, 18, 26, 10)
                painter.drawLine(46, 20, 48, 12)
            
            painter.end()

            logger.debug(f"Created noon/afternoon placeholder image: {width}x{height}, color_adjust={color_adjust}")
            return image
        except Exception as e:
            logger.error(f"Failed to create noon/afternoon placeholder image: {str(e)}")
            return None
            
    def _create_night_placeholder_image(self, width=64, height=64, make_darker=True) -> Optional[QImage]:
        """创建一个代表'晚上'/'夜晚'状态的占位符图像
        
        Args:
            width: 图像宽度
            height: 图像高度
            make_darker: 是否使颜色更暗（区分晚上和深夜）
        """
        try:
            # 创建透明图像
            image = QImage(width, height, QImage.Format.Format_ARGB32)
            image.fill(Qt.GlobalColor.transparent)
            
            # 创建画布
            painter = QPainter(image)
            
            # 启用抗锯齿
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            
            # 绘制月亮/星星背景
            if make_darker:
                # 深夜 - 深蓝色背景与月亮
                bg_color = QColor(20, 20, 60, 80)  # 深蓝色半透明背景
                moon_color = QColor(230, 230, 255)  # 亮白月亮
            else:
                # 晚上 - 淡蓝色背景与日落
                bg_color = QColor(40, 50, 100, 50)  # 淡蓝色半透明背景
                moon_color = QColor(255, 200, 100)  # 橙黄色月亮/太阳
            
            # 添加背景色
            painter.fillRect(0, 0, width, height, bg_color)
            
            # 绘制月亮/落日
            painter.setBrush(QBrush(moon_color))
            painter.setPen(Qt.PenStyle.NoPen)
            
            if make_darker:
                # 深夜 - 月亮在右上角
                painter.drawEllipse(46, 8, 10, 10)
                
                # 添加几颗星星
                painter.setBrush(QBrush(QColor(255, 255, 255, 200)))
                painter.drawEllipse(10, 12, 2, 2)
                painter.drawEllipse(22, 8, 2, 2)
                painter.drawEllipse(35, 6, 2, 2)
                painter.drawEllipse(15, 20, 1, 1)
            else:
                # 晚上 - 落日在左下角
                painter.drawEllipse(8, 20, 12, 12)
                
                # 添加一些云彩
                painter.setBrush(QBrush(QColor(150, 120, 200, 100)))
                painter.drawEllipse(30, 15, 10, 6)
                painter.drawEllipse(25, 12, 12, 8)

            # 绘制身体
            gray_level = 150 if make_darker else 180
            painter.setBrush(QBrush(QColor(gray_level, gray_level, gray_level)))
            painter.setPen(QPen(QColor(70, 70, 70), 1))
            painter.drawEllipse(20, 25, 24, 20)
            
            # 绘制头部
            painter.drawEllipse(32, 18, 16, 16)
            
            # 绘制耳朵
            painter.drawEllipse(34, 10, 8, 8)
            painter.drawEllipse(42, 12, 8, 8)
            
            # 绘制眼睛
            if make_darker:
                # 深夜状态 - 闭眼
                painter.setPen(QPen(QColor(70, 70, 70), 1))
                painter.drawLine(35, 22, 38, 22)
                painter.drawLine(41, 23, 44, 23)
            else:
                # 晚上状态 - 半睁眼
                painter.setBrush(QBrush(QColor(70, 70, 70)))
                painter.drawEllipse(35, 21, 3, 2)
                painter.drawEllipse(42, 22, 3, 2)
            
            # 绘制鼻子
            painter.setBrush(QBrush(QColor(255, 150, 150)))
            painter.drawEllipse(29, 35, 6, 4)
            
            # 绘制闭口打哈欠的嘴
            painter.setPen(QPen(QColor(70, 70, 70), 1))
            painter.drawLine(28, 42, 36, 42)  # 简单的嘴线
            
            # 添加小泡泡表示睡意（Z字）
            painter.setPen(QPen(QColor(200, 200, 255, 200), 1))
            painter.drawText(QPoint(48, 15), "z")
            
            painter.end()
            
            logger.debug(f"Created night/evening placeholder image: {width}x{height}, make_darker={make_darker}")
            return image
        except Exception as e:
            logger.error(f"Failed to create night/evening placeholder image: {str(e)}")
            return None

    def update(self):
        """主更新循环"""
        # 导入所需的时间枚举
        from status.behavior.time_based_behavior import TimePeriod
        
        logger.debug("---- UPDATE METHOD CALLED ----") # 添加 DEBUG 日志
        # 如果窗口不可见，无需进行全部更新
        if self.main_window and not self.main_window.isVisible():
            # 只需最小程度的更新以保持应用响应
            self._last_update_time = time.perf_counter()
            return

        current_time = time.perf_counter()
        dt = current_time - self._last_update_time
        # 防止 dt 过大或过小导致的问题
        dt = max(0.001, min(dt, 0.1))
        self._last_update_time = current_time

        # 1. 获取系统状态 (通过发布事件)
        publish_stats(include_details=True) # 始终发送详细系统信息

        # 获取当前状态，用于检测状态变化
        # 只有在状态机存在时才获取状态
        previous_state = self.state_machine.get_state() if self.state_machine else PetState.IDLE 
        current_state = self.state_machine.get_state() if self.state_machine else PetState.IDLE
        
        # 检测状态是否变化
        state_changed = previous_state != current_state

        # 3. 根据状态更新动画
        if state_changed:
            new_animation = None
            # 检查是否是时间相关状态
            if current_state in [PetState.MORNING, PetState.NOON, PetState.AFTERNOON, PetState.EVENING, PetState.NIGHT]:
                # 尝试从时间动画管理器获取对应的动画
                if hasattr(self, 'time_animation_manager') and self.time_animation_manager:
                    # 将PetState映射回TimePeriod
                    time_period = None
                    if current_state == PetState.MORNING:
                        time_period = TimePeriod.MORNING
                    elif current_state == PetState.NOON:
                        time_period = TimePeriod.NOON
                    elif current_state == PetState.AFTERNOON:
                        time_period = TimePeriod.AFTERNOON
                    elif current_state == PetState.EVENING:
                        time_period = TimePeriod.EVENING
                    elif current_state == PetState.NIGHT:
                        time_period = TimePeriod.NIGHT
                    
                    if time_period:
                        time_animation = self.time_animation_manager.get_animation_for_time_period(time_period)
                        if time_animation:
                            new_animation = time_animation
                            logger.info(f"时间状态 {current_state.name} 使用时间动画: {time_period.name}")
            
            # 如果没有从时间动画管理器获取到动画，使用直接引用的动画
            if new_animation is None:    
                if current_state == PetState.IDLE or current_state == PetState.SYSTEM_IDLE:
                new_animation = self.idle_animation
                elif current_state in [PetState.BUSY, PetState.VERY_BUSY, PetState.CPU_CRITICAL, 
                                    PetState.DISK_BUSY, PetState.NETWORK_BUSY, PetState.GPU_BUSY]:
                new_animation = self.busy_animation
                elif current_state in [PetState.MEMORY_WARNING, PetState.MEMORY_CRITICAL]:
                new_animation = self.memory_warning_animation
                # 用户交互状态
                elif current_state in [PetState.CLICKED, PetState.HEAD_CLICKED, PetState.BODY_CLICKED, 
                                    PetState.TAIL_CLICKED, PetState.PETTED, PetState.HEAD_PETTED, 
                                    PetState.BODY_PETTED, PetState.TAIL_PETTED, PetState.DRAGGED,
                                    PetState.HAPPY, PetState.ANGRY]:
                    # 对于MVP阶段，我们可以使用idle动画表示交互，后续可以添加专门的交互动画
                    new_animation = self.idle_animation  # 可以根据需要替换为专门的交互动画
                # 时间相关状态
                elif current_state == PetState.MORNING:
                    new_animation = self.morning_animation if hasattr(self, 'morning_animation') else self.idle_animation
                elif current_state == PetState.NOON:
                    new_animation = self.noon_animation if hasattr(self, 'noon_animation') else self.idle_animation
                elif current_state == PetState.AFTERNOON:
                    # 下午可以复用中午动画，或者创建专门的下午动画
                    new_animation = self.noon_animation if hasattr(self, 'noon_animation') else self.idle_animation
                elif current_state == PetState.EVENING:
                    # 傍晚可以复用中午或夜晚动画，或者创建专门的傍晚动画
                    new_animation = self.noon_animation if hasattr(self, 'noon_animation') else self.idle_animation
                elif current_state == PetState.NIGHT:
                    new_animation = self.night_animation if hasattr(self, 'night_animation') else self.idle_animation
                # 特殊日期状态
                elif current_state in [PetState.BIRTHDAY, PetState.NEW_YEAR, PetState.VALENTINE]:
                    # 尝试从时间动画管理器获取特殊日期动画
                    if hasattr(self, 'time_animation_manager') and self.time_animation_manager:
                        date_name = None
                        if current_state == PetState.BIRTHDAY:
                            date_name = "生日"
                        elif current_state == PetState.NEW_YEAR:
                            date_name = "新年"
                        elif current_state == PetState.VALENTINE:
                            date_name = "情人节"
                        
                        if date_name:
                            special_animation = self.time_animation_manager.get_animation_for_special_date(date_name)
                            if special_animation:
                                new_animation = special_animation
                                logger.info(f"特殊日期状态 {current_state.name} 使用特殊日期动画: {date_name}")
                    
                    # 如果找不到特殊日期动画，使用默认动画
                    if new_animation is None:
                        new_animation = self.idle_animation
            # 可以添加更多状态的动画切换
            
            if new_animation and self.current_animation != new_animation:
                previous_state_name = previous_state.name if previous_state else "Unknown"
                logger.debug(f"状态变化: {previous_state_name} -> {current_state.name}. 切换动画 -> {new_animation}") 
                if self.current_animation and self.current_animation.is_playing:
                    self.current_animation.stop()
                self.current_animation = new_animation
                self.current_animation.play()

        # 4. 更新动画 - 只需调用 update() 让动画自己处理帧切换和循环
        if self.current_animation and self.current_animation.is_playing:
            self.current_animation.update(dt)

        # 5. 更新窗口显示的图像
        if self.main_window and self.current_animation and self.current_animation.is_playing:
            current_frame = self.current_animation.get_current_frame() # 获取 QImage
            if current_frame:
                 self.main_window.set_image(current_frame)
        
        # 更新托盘可见性状态
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
        
        # 创建角色精灵/动画
        self.create_character_sprite()
        
        # 创建状态机
        self.state_machine = PetStateMachine()
        
        # 创建系统状态适配器
        self.system_state_adapter = SystemStateAdapter(self.state_machine)
        # 初始化系统状态适配器
        self.system_state_adapter._initialize()
        logger.info("系统状态适配器已初始化")
        
        # 创建交互状态适配器
        self.interaction_state_adapter = InteractionStateAdapter(self.state_machine)
        # 初始化交互状态适配器
        self.interaction_state_adapter._initialize()
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
        self.time_state_bridge._initialize()
        logger.info("时间状态桥接器已初始化")
        
        # 创建交互处理器
        self.interaction_handler = InteractionHandler(parent_window=self.main_window)
        # 初始化交互处理器
        self.interaction_handler._initialize()
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
        logger.info("启动更新定时器，间隔: 1000ms (1fps)") # 修改日志消息
        self._update_timer.start()
    
    def connect_interaction_handler(self):
        """将窗口的鼠标事件连接到交互处理器"""
        if not self.main_window or not hasattr(self, 'interaction_handler') or not self.interaction_handler:
            logger.warning("主窗口或交互处理器未初始化，无法连接事件")
            return

        # 添加对interaction_handler方法的显式检查
        if not hasattr(self.interaction_handler, 'handle_mouse_event'):
            logger.warning("交互处理器没有handle_mouse_event方法，无法连接事件")
            return
            
        try:
            # 使用类型断言
            handler = self.interaction_handler
            assert isinstance(handler, InteractionHandler), "交互处理器类型错误"
            
            # 获取信号引用
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
            
            logger.info("已连接窗口鼠标事件到交互处理器")
        except (AttributeError, TypeError, AssertionError) as e:
            logger.error(f"连接鼠标事件失败: {e}")
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
        from PySide6.QtGui import QMouseEvent
        
        # 创建简单的QMouseEvent用于传递给交互处理器
        return QMouseEvent(
            QEvent.Type.MouseButtonPress,  # 事件类型，实际由handle_mouse_event的event_type参数决定
            QPointF(pos),                  # 位置
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