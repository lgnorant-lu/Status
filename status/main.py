"""
---------------------------------------------------------------
File name:                  main.py
Author:                     Ignorant-lu
Date created:               2025/04/16
Description:                Status-Ming 主应用入口
----------------------------------------------------------------

Changed history:            
                            2025/04/16: 初始创建;
                            2025/05/13: 实现系统托盘功能;
                            2025/05/13: 优化UI性能，添加平滑拖动;
----
"""

import sys
import time
import logging
from typing import Optional

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QImage, QPixmap, QColor, QPainter, QPen, QBrush
from PySide6.QtCore import QTimer, QPoint, Qt

from status.ui.main_pet_window import MainPetWindow
from status.ui.system_tray import SystemTrayManager
from status.animation.animation import Animation
from status.monitoring.system_monitor import get_cpu_usage, get_memory_usage
from status.behavior.pet_state_machine import PetStateMachine
from status.behavior.pet_state import PetState
# 我们将在initialize方法中导入Application类，以避免循环导入问题

# 配置日志
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(name)s - %(message)s')
logger = logging.getLogger("StatusApp")

class StatusPet:
    """Status Pet 应用主类"""
    
    def __init__(self):
        """初始化应用"""
        logger.info("Initializing Status Pet...")
        
        # 创建应用实例
        self.app = QApplication(sys.argv)

        # 创建主窗口
        self.main_window: Optional[MainPetWindow] = None
        
        # 创建系统托盘
        self.system_tray: Optional[SystemTrayManager] = None
        
        # 动画
        self.animation_manager = None  # 动画管理器
        self.idle_animation: Optional[Animation] = None  # 待机动画
        self.busy_animation: Optional[Animation] = None  # 忙碌动画
        self.current_animation: Optional[Animation] = None # 当前播放的动画
        self.memory_warning_animation: Optional[Animation] = None # 内存警告动画
        
        # 状态机
        self.state_machine: Optional[PetStateMachine] = None
        
        # 更新相关
        self._last_update_time = time.perf_counter()
        self._update_timer = QTimer()
        self._update_timer.setInterval(16)  # 约60fps
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
        
        # 设置菜单
        self.system_tray.setup_menu(
            show_hide_callback=self.toggle_window_visibility,
            exit_callback=self.exit_app,
            drag_mode_callback=self.set_drag_mode,
            toggle_interaction_callback=self.toggle_pet_interaction
        )
        
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
    
    def exit_app(self):
        """退出应用"""
        logger.info("用户请求退出应用程序")
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
        """创建角色精灵(即桌宠角色)
        
        这里是一个极简的实现，实际上应该使用资源管理器加载资源
        为 IDLE 和 BUSY 状态创建简单的 2 帧动画
        """
        # --- 创建 IDLE 动画 ---
        idle_frame_1 = self._create_placeholder_image() # 标准眼睛
        idle_frame_2 = self._create_placeholder_image() # 创建第二个idle帧，稍作修改
        if idle_frame_1 and idle_frame_2:
             # 稍微修改第二帧的眼睛，让它看起来像眨眼或呼吸
            painter = QPainter(idle_frame_2)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            painter.setPen(QPen(QColor(0,0,0,0))) # 透明画笔
            painter.setBrush(QBrush(QColor(200, 200, 200, 220))) # 用背景色覆盖旧眼睛
            painter.drawEllipse(20, 25, 8, 8) # 覆盖左眼
            painter.drawEllipse(36, 25, 8, 8) # 覆盖右眼
            painter.setPen(QPen(QColor(30, 30, 30), 1))
            painter.setBrush(QBrush(QColor(30, 30, 30)))
            painter.drawEllipse(20, 26, 8, 6) # 左眼稍微小一点
            painter.drawEllipse(36, 26, 8, 6) # 右眼稍微小一点
            painter.end()
            
            self.idle_animation = Animation()
            self.idle_animation.add_frame(idle_frame_1, 800)  # 标准帧，持续800ms
            self.idle_animation.add_frame(idle_frame_2, 200)  # 小眼帧，持续200ms
            self.idle_animation.set_loop(True)
            logger.info("Created IDLE animation with 2 frames.")
        else:
            logger.error("Failed to create frames for IDLE animation.")

        # --- 创建 BUSY 动画 ---
        busy_frame_1 = self._create_busy_placeholder_image() # 眯眼
        busy_frame_2 = self._create_busy_placeholder_image() # 创建第二个busy帧，稍作修改
        if busy_frame_1 and busy_frame_2:
            # 修改第二帧为完全闭眼
            painter = QPainter(busy_frame_2)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            painter.setPen(QPen(QColor(0,0,0,0))) # 透明画笔
            painter.setBrush(QBrush(QColor(200, 200, 200, 220))) # 用背景色覆盖旧眼睛
            painter.drawEllipse(20, 28, 8, 4) # 覆盖左眼
            painter.drawEllipse(36, 28, 8, 4) # 覆盖右眼
            painter.setPen(QPen(QColor(30, 30, 30), 1))
            # 画两条横线表示闭眼
            painter.drawLine(21, 29, 27, 29) # 左眼线
            painter.drawLine(37, 29, 43, 29) # 右眼线
            painter.end()

            self.busy_animation = Animation()
            self.busy_animation.add_frame(busy_frame_1, 300) # 眯眼帧，持续300ms
            self.busy_animation.add_frame(busy_frame_2, 150) # 闭眼帧，持续150ms
            self.busy_animation.set_loop(True)
            logger.info("Created BUSY animation with 2 frames.")
        else:
            logger.error("Failed to create frames for BUSY animation.")

        # --- 创建 MEMORY_WARNING 动画 ---
        mem_warn_frame_1 = self._create_memory_warning_placeholder_image()
        # 可以简单地使用单帧动画，或者创建第二帧让它闪烁
        if mem_warn_frame_1:
            self.memory_warning_animation = Animation()
            self.memory_warning_animation.add_frame(mem_warn_frame_1, 500) # 持续500ms
            # 如果需要闪烁效果，可以再添加一个透明或略微变化的帧
            # mem_warn_frame_2 = self._create_memory_warning_placeholder_image() 
            # # ... (对 frame_2 做微小修改) ...
            # self.memory_warning_animation.add_frame(mem_warn_frame_2, 300)
            self.memory_warning_animation.set_loop(True)
            logger.info("Created MEMORY_WARNING animation.")
        else:
            logger.error("Failed to create frames for MEMORY_WARNING animation.")

        # 设置初始动画
        if self.idle_animation:
            self.current_animation = self.idle_animation
            logger.info(f"Initial animation set to IDLE animation: {self.current_animation}")
        else:
            logger.warning("Idle animation not created, cannot set initial animation.")

    def update(self):
        """主更新循环"""
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

        # 1. 处理输入 (后续添加)
        # self.handle_input(dt)

        # 2. 获取系统状态
        cpu_usage = get_cpu_usage()
        memory_usage = get_memory_usage() # 获取内存使用率

        # 3. 更新行为/状态机
        state_changed = False
        previous_state = self.state_machine.get_state() if self.state_machine else None
        if self.state_machine:
            state_changed = self.state_machine.update(cpu_usage, memory_usage) # 传递内存使用率
            # 可以在状态改变时触发其他逻辑，例如切换动画
            current_state = self.state_machine.get_state()
            logger.debug(f"当前状态: {current_state.name} (CPU: {cpu_usage:.1f}%, Mem: {memory_usage:.1f}%)")
            
            # --- 动画切换逻辑 ---
            if state_changed:
                new_animation = None
                if current_state == PetState.IDLE:
                    new_animation = self.idle_animation
                elif current_state == PetState.BUSY:
                    new_animation = self.busy_animation
                elif current_state == PetState.MEMORY_WARNING: # 新增处理
                    new_animation = self.memory_warning_animation
                # 可以添加更多状态的动画切换
                
                if new_animation and self.current_animation != new_animation:
                    previous_state_name = previous_state.name if previous_state else "Unknown"
                    logger.debug(f"状态变化: {previous_state_name} -> {current_state.name}. 切换动画 -> {new_animation}") 
                    if self.current_animation and self.current_animation.is_playing:
                        self.current_animation.stop()
                    self.current_animation = new_animation
                    self.current_animation.play()
            # --- 结束动画切换逻辑 ---

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
        # logger.critical("%%%% INITIALIZE METHOD CALLED %%%%") # 移除诊断日志
        # 在这里导入Application，避免循环导入问题
        from status.core.app import Application
        
        # 初始化核心系统
        self.core_app = Application()
        self.core_app.initialize()
        
        # 跳过获取资源管理器、渲染器等组件
        # 因为目前Application尚未实现get_renderer_manager方法
        # self.animation_manager = self.core_app.get_renderer_manager()
        
        # 创建主窗口
        self.create_main_window()

        # 创建系统托盘
        self.create_system_tray()
        
        # 创建状态机
        self.state_machine = PetStateMachine()
        
        # 创建角色精灵
        self.create_character_sprite()
        
        # 显示窗口
        if self.main_window:
            self.main_window.show()
            logger.info("MainPetWindow shown.")
        
        # 更新系统托盘菜单项状态
        if self.system_tray and self.main_window:
            self.system_tray.set_window_visibility(self.main_window.isVisible())
    
    def run(self):
        """运行应用"""
        # 初始化
        self.initialize()
        
        # 进入事件循环
        return self.app.exec()

def main():
    """主函数"""
    pet_app = StatusPet()
    exit_code = pet_app.run()
    sys.exit(exit_code)

if __name__ == "__main__":
    main()