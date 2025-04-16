"""
---------------------------------------------------------------
File name:                  main.py
Author:                     Ignorant-lu
Date created:               2025/04/16
Description:                Hollow Knight 桌宠主程序入口
----------------------------------------------------------------

Changed history:
                            2025/04/16: 初始创建，实现基本窗口和Idle动画渲染;
----
"""

import sys
import logging
import time

# 尝试导入 PyQt6，如果失败则记录错误并退出
try:
    from PyQt6.QtWidgets import QApplication
    from PyQt6.QtCore import QTimer
except ImportError as e:
    logging.basicConfig(level=logging.CRITICAL)
    logging.critical(f"无法导入 PyQt6 模块: {e}. 请确保已安装 PyQt6。")
    sys.exit(1)

# 导入核心模块 (假设都在status目录下且路径已配置或使用相对导入)
# 使用 try-except 包裹，以便更好地定位导入错误
try:
    from status.core.app import Application # 假设存在这个核心应用类
    from status.resources.asset_manager import AssetManager
    from status.renderer.sprite import Sprite
    from status.renderer.animation import FrameAnimation, AnimationManager
    from status.ui.main_pet_window import MainPetWindow # <-- 导入主窗口类
    # from status.behavior.state_machine import StateMachine # 暂时不用状态机
except ImportError as e:
     # 如果这里报错，说明其他文件可能有问题或路径错误
    logging.basicConfig(level=logging.CRITICAL)
    logging.critical(f"导入项目模块时出错: {e}. 检查模块是否存在以及 Python 路径设置。")
    sys.exit(1)
except SyntaxError as e:
     # 如果这里捕获到 SyntaxError，特别是 null byte 错误，说明被导入的文件有问题
    logging.basicConfig(level=logging.CRITICAL)
    logging.critical(f"导入项目模块时遇到语法错误 (可能文件损坏): {e}. 检查文件 {e.filename} 的内容。")
    sys.exit(1)


# 配置日志
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(levelname)s - %(name)s - %(message)s')
logger = logging.getLogger("HollowMingApp")

# --- 配置 --- (稍后移到 config.py)
WINDOW_WIDTH = 150
WINDOW_HEIGHT = 150
KNIGHT_IDLE_PATH = "assets/images/characters/knight/idle" # 小骑士Idle动画资源路径
KNIGHT_IDLE_FPS = 10 # Idle动画帧率

class HollowMingPet(Application):
    """桌宠主应用程序类"""
    def __init__(self):
        super().__init__()
        self.asset_manager = AssetManager.get_instance()
        self.animation_manager = AnimationManager() # 管理所有动画
        self.main_window = None # <-- 添加主窗口实例变量
        self.knight_sprite = None
        self.idle_animation = None
        self._last_update_time = time.perf_counter()

    def initialize(self):
        """初始化应用程序"""
        logger.info("Initializing Hollow Ming Pet...")
        super().initialize() # 调用父类初始化 (如果需要)

        # 初始化资源管理器 (指定资源根目录)
        # 假设脚本是从项目根目录运行的
        self.asset_manager.initialize(base_path=".")
        logger.info(f"AssetManager initialized with base path: {self.asset_manager.get_base_path()}")

        # 加载小骑士 Idle 动画帧
        logger.info(f"Loading knight idle animation from: {KNIGHT_IDLE_PATH}")
        idle_frames = self.asset_manager.load_image_sequence(KNIGHT_IDLE_PATH)

        if not idle_frames:
            logger.error("Failed to load knight idle frames. Exiting.")
            sys.exit(1) # 加载失败则退出

        logger.info(f"Loaded {len(idle_frames)} idle frames.")

        # 创建 Idle 动画实例
        self.idle_animation = FrameAnimation(frames=idle_frames, fps=KNIGHT_IDLE_FPS, loop=True, auto_start=False)
        self.animation_manager.add(self.idle_animation) # 添加到管理器

        # 创建主窗口
        self.main_window = MainPetWindow()
        logger.info(f"MainPetWindow created. Initial size: {self.main_window.size()}")

        # 创建 Sprite 实例
        if idle_frames:
            frame_width = idle_frames[0].width()
            frame_height = idle_frames[0].height()
            initial_x = (WINDOW_WIDTH - frame_width) // 2 # 初始位置可能由窗口自己管理
            initial_y = (WINDOW_HEIGHT - frame_height) // 2
            # 创建 Sprite，但不一定需要立即设置 image，因为 MainPetWindow 会处理
            self.knight_sprite = Sprite(x=initial_x, y=initial_y, width=frame_width, height=frame_height)
            logger.info(f"Knight sprite logic instance created with initial size {frame_width}x{frame_height}.")
            # 让窗口适应第一帧大小 (重要，否则窗口初始大小可能不对)
            self.main_window.set_image(idle_frames[0]) 
            logger.info(f"MainPetWindow initial image set, size should be adjusted.")

        else:
            logger.warning("No idle frames loaded, cannot create sprite properly.")
            self.knight_sprite = Sprite(x=50, y=50)

        # 显示窗口
        self.main_window.show()
        logger.info("MainPetWindow shown.")

        # 启动 Idle 动画
        if self.idle_animation:
             self.idle_animation.play()
             logger.info("Idle animation started.")

        # 启动主更新循环
        self.start_update_loop()
        logger.info("Update loop started.")

    def start_update_loop(self):
        """启动主更新定时器"""
        self.update_timer = QTimer()
        # 设置一个较快的更新频率，例如 60 FPS (大约 16ms)
        self.update_timer.setInterval(16)
        self.update_timer.timeout.connect(self.update)
        self.update_timer.start()

    def update(self):
        """主更新循环"""
        current_time = time.perf_counter()
        dt = current_time - self._last_update_time
        # 防止 dt 过大或过小导致的问题
        dt = max(0.001, min(dt, 0.1))
        self._last_update_time = current_time

        # 1. 处理输入 (后续添加)
        # self.handle_input(dt)

        # 2. 更新动画
        self.animation_manager.update(dt)

        # 3. 更新行为/状态机 (后续添加)
        # self.behavior_manager.update(dt)

        # 4. 更新窗口显示的图像
        if self.main_window and self.idle_animation and self.idle_animation.is_playing():
            current_frame = self.idle_animation.get_current_frame() # 获取 QImage
            if current_frame:
                 # 直接让 MainPetWindow 更新它的图像，它内部会调用 update() 触发重绘
                 self.main_window.set_image(current_frame)
                 # logger.debug(f"Updating window image to frame index: {self.idle_animation.current_frame_index}")

def main():
    """应用程序主入口"""
    # 在创建 QApplication 之前设置高 DPI 缩放策略 (可选, 但推荐)
    # QApplication.setAttribute(Qt.ApplicationAttribute.AA_EnableHighDpiScaling, True)
    # QApplication.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps, True)

    app = QApplication(sys.argv)

    # 确保日志在 QApplication 创建后能正常工作
    global logger
    logger = logging.getLogger("HollowMingApp") # 重新获取 logger 实例


    pet_app = HollowMingPet()
    try:
        pet_app.initialize()
        # pet_app.run() # Application 基类可能需要一个 run 方法来启动 PyQt 事件循环
        logger.info("Hollow Ming Pet initialized successfully. Starting event loop...")
        sys.exit(app.exec()) # 直接启动 PyQt 事件循环
    except Exception as e:
        logger.exception(f"Application failed to initialize or run: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()