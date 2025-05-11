"""
测试PySide6渲染器的简单脚本
"""

import sys
import os
import logging
from typing import Optional

# 配置日志
logging.basicConfig(level=logging.DEBUG,
                   format='%(asctime)s - %(levelname)s - %(name)s - %(message)s')
logger = logging.getLogger("TestRenderer")

try:
    from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QLabel
    from PySide6.QtGui import QPixmap, QPainter, QColor
    from PySide6.QtCore import Qt, QTimer, QObject, Signal
    
    # 先添加当前目录到路径
    # sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))) # 在tests目录下，这个可能需要调整
    #  向上两级目录，即项目根目录
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    sys.path.insert(0, project_root)

    # 导入渲染器基础类
    from status.renderer.renderer_base import Color, Rect, RendererBase, BlendMode, TextAlign
    
    # 导入PySide渲染器
    from status.renderer.pyside_renderer import PySideRenderer
    
except ImportError as e:
    logger.critical(f"导入错误: {e}")
    sys.exit(1)

class TestWindow(QMainWindow):
    """测试窗口"""
    
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("PySide6 Renderer Test")
        self.resize(400, 400)
        
        # 创建中央部件
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        # 创建布局
        self.main_layout = QVBoxLayout(self.central_widget)
        
        # 创建标签
        self.label = QLabel()
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.main_layout.addWidget(self.label)
        
        # 初始化渲染器
        self.renderer = PySideRenderer()
        self.init_renderer()
        
        # 创建定时器
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_render)
        self.timer.start(30)  # 约33FPS
        
    def init_renderer(self):
        """初始化渲染器"""
        try:
            # 初始化渲染器
            result = self.renderer.initialize(300, 300)
            if result:
                logger.info("渲染器初始化成功")
            else:
                logger.error("渲染器初始化失败")
        except Exception as e:
            logger.error(f"初始化渲染器时出错: {e}")
    
    def update_render(self):
        """更新渲染"""
        if not self.renderer:
            return
        
        try:
            # 开始渲染
            self.renderer.begin_frame()
            
            # 清除画面
            self.renderer.clear()
            
            # 绘制一些图形
            self.draw_test_shapes()
            
            # 结束渲染
            self.renderer.end_frame()
            
            # 获取渲染结果
            pixmap = self.renderer.get_pixmap()
            if pixmap:
                self.label.setPixmap(pixmap)
            
        except Exception as e:
            logger.error(f"渲染时出错: {e}")
    
    def draw_test_shapes(self):
        """绘制测试图形"""
        # 绘制矩形
        rect = Rect(50, 50, 100, 100)
        color = Color(255, 0, 0, 150)  # 半透明红色
        self.renderer.draw_rect(rect, color, 2.0, filled=True)
        
        # 绘制圆形
        color = Color(0, 0, 255, 150)  # 半透明蓝色
        self.renderer.draw_circle(200, 100, 40, color, 2.0, filled=True)
        
        # 绘制线条
        color = Color(0, 255, 0, 255)  # 绿色
        self.renderer.draw_line(30, 180, 270, 180, color, 3.0)
        
        # 绘制文本
        color = Color(255, 255, 255, 255)  # 白色
        self.renderer.draw_text("PySide6 Renderer Test", 50, 30, color, "Arial", 16, TextAlign.LEFT)
        
        # 绘制点
        color = Color(255, 255, 0, 255)  # 黄色
        for i in range(10):
            x = 50 + i * 20
            y = 220
            self.renderer.draw_point(x, y, color, 5.0)

def main():
    """主函数"""
    app = QApplication(sys.argv)
    
    window = TestWindow()
    window.show()
    
    logger.info("测试窗口已显示")
    sys.exit(app.exec())

if __name__ == "__main__":
    main() 