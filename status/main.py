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
from PySide6.QtCore import QTimer, QPoint

from status.ui.main_pet_window import MainPetWindow
from status.ui.system_tray import SystemTrayManager
from status.animation.animation import Animation
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
            drag_mode_callback=self.set_drag_mode
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
    
    def create_character_sprite(self):
        """创建角色精灵(即桌宠角色)
        
        这里是一个极简的实现，实际上应该使用资源管理器加载资源
        """
        # 创建一个简单的动画用于测试
        placeholder_image = self._create_placeholder_image()
        if placeholder_image:
            # 创建一个Animation对象
            self.idle_animation = Animation()
            self.idle_animation.add_frame(placeholder_image, 500)  # 添加一帧，持续500ms
            
            # 设置动画为循环播放
            self.idle_animation.set_loop(True)
            
            logger.info(f"Character sprite logic instance created with initial size {placeholder_image.width()}x{placeholder_image.height()}.")

    def update(self):
        """主更新循环"""
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

        # 2. 更新动画
        if self.animation_manager:
            self.animation_manager.update(dt)

        # 3. 更新行为/状态机 (后续添加)
        # self.behavior_manager.update(dt)

        # 4. 更新窗口显示的图像
        if self.main_window and self.idle_animation and self.idle_animation.is_playing:
            current_frame = self.idle_animation.get_current_frame() # 获取 QImage
            if current_frame:
                 self.main_window.set_image(current_frame)
    
    def initialize(self):
        """初始化应用"""
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
        
        # 创建角色精灵
        self.create_character_sprite()
        
        # 显示窗口
        if self.main_window:
            self.main_window.show()
            logger.info("MainPetWindow shown.")
        
        # 更新系统托盘菜单项状态
        if self.system_tray and self.main_window:
            self.system_tray.set_window_visibility(self.main_window.isVisible())
        
        # 启动待机动画
        if self.idle_animation:
            self.idle_animation.play()
            logger.info("Idle animation started.")
        
        # 启动更新循环
        self._update_timer.start()
        logger.info("Update loop started.")
        
        logger.info("Status Pet initialized successfully. Starting event loop...")
    
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