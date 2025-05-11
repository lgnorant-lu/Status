"""
测试 PySideRenderer 类是否能正常工作的脚本
"""

import sys
import logging
import os
from typing import Optional, List, Tuple

# 添加当前目录到系统路径
# sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))) # 在tests目录下，这个可能需要调整
#  向上两级目录，即项目根目录
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, project_root)


# 配置日志
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(levelname)s - %(name)s - %(message)s')
logger = logging.getLogger("TestPySideRenderer")

try:
    from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QLabel
    from PySide6.QtGui import QPainter, QColor
    from PySide6.QtCore import Qt, QTimer
    
    # 导入自定义的渲染器类
    from status.renderer.renderer_base import Color, Rect
    from status.renderer.pyside_renderer import PySideRenderer
except ImportError as e:
    logger.critical(f"导入错误: {e}")
    sys.exit(1)

class TestWindow(QMainWindow):
    """测试窗口"""
    
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("PySideRenderer Test")
        self.resize(400, 400)
        
        # 创建中央部件
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        # 创建布局
        self.main_layout = QVBoxLayout(self.central_widget)
        
        # 创建标签用于显示图像
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.main_layout.addWidget(self.image_label)
        
        # 创建渲染器
        self.renderer = None
        self.create_renderer()
        
        # 设置定时器来更新渲染
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_render)
        self.timer.start(16)  # 约60FPS
        
        logger.info("测试窗口已初始化")
    
    def create_renderer(self):
        """创建渲染器"""
        try:
            logger.info("正在创建PySideRenderer...")
            self.renderer = PySideRenderer()
            logger.info("PySideRenderer已创建")
            
            # 初始化渲染器
            width, height = 300, 300
            result = self.renderer.initialize(width, height)
            
            if result:
                logger.info(f"渲染器初始化成功 ({width}x{height})")
            else:
                logger.error("渲染器初始化失败")
                return False
            
            return True
        except Exception as e:
            logger.error(f"创建渲染器时发生错误: {e}")
            return False
    
    def update_render(self):
        """更新渲染"""
        if not self.renderer:
            return
        
        # 开始渲染
        self.renderer.begin_frame()
        
        # 清除为透明
        self.renderer.clear()
        
        # 绘制一些基本图形
        # 1. 绘制一个矩形
        rect = Rect(50, 50, 100, 100)
        color = Color(255, 0, 0, 150)  # 半透明红色
        self.renderer.draw_rect(rect, color, 2.0, True)
        
        # 2. 绘制一个圆
        color = Color(0, 0, 255, 150)  # 半透明蓝色
        self.renderer.draw_circle(200, 100, 50, color, 2.0, True)
        
        # 3. 绘制一条线
        color = Color(0, 255, 0, 255)  # 绿色
        self.renderer.draw_line(50, 200, 250, 250, color, 3.0)
        
        # 4. 绘制多边形
        color = Color(255, 255, 0, 150)  # 半透明黄色
        points: List[Tuple[float, float]] = [(150.0, 150.0), (200.0, 200.0), (150.0, 250.0), (100.0, 200.0)]
        self.renderer.draw_polygon(points, color, 2.0, True)
        
        # 5. 绘制文本
        color = Color(255, 255, 255, 255)  # 白色
        self.renderer.draw_text("PySideRenderer Test", 100, 30, color, "Arial", 16)
        
        # 结束渲染
        self.renderer.end_frame()
        
        # 获取渲染结果并显示
        pixmap = self.renderer.get_pixmap()
        if pixmap:
            self.image_label.setPixmap(pixmap)
    
    def closeEvent(self, event):
        """窗口关闭事件"""
        # 停止定时器
        self.timer.stop()
        
        # 关闭渲染器
        if self.renderer:
            self.renderer.shutdown()
        
        logger.info("窗口关闭，资源已清理")
        super().closeEvent(event)

def main():
    """主函数"""
    app = QApplication(sys.argv)
    
    window = TestWindow()
    window.show()
    
    logger.info("测试窗口已显示")
    sys.exit(app.exec())

if __name__ == "__main__":
    main() 