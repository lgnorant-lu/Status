"""
测试 PySideRenderer 是否能正常工作的简单脚本
"""

import sys
import logging

from PySide6.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget
from PySide6.QtGui import QPixmap, QPainter, QColor
from PySide6.QtCore import Qt, QTimer

# 配置日志
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(levelname)s - %(name)s - %(message)s')
logger = logging.getLogger("TestRenderer")

class TestWindow(QMainWindow):
    """测试窗口"""
    
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("PySide6 Renderer Test")
        self.resize(300, 300)
        
        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 创建布局
        layout = QVBoxLayout(central_widget)
        
        # 创建图像标签
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.image_label)
        
        # 创建测试图像
        self.create_test_image()
        
    def create_test_image(self):
        """创建测试图像"""
        pixmap = QPixmap(200, 200)
        pixmap.fill(Qt.GlobalColor.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        
        # 绘制简单图形
        painter.setBrush(QColor(255, 0, 0, 128))  # 半透明红色
        painter.drawEllipse(50, 50, 100, 100)
        
        painter.setBrush(QColor(0, 0, 255, 128))  # 半透明蓝色
        painter.drawRect(25, 25, 150, 150)
        
        painter.end()
        
        # 设置到标签
        self.image_label.setPixmap(pixmap)
        logger.info("测试图像已创建")

def main():
    """主函数"""
    app = QApplication(sys.argv)
    
    window = TestWindow()
    window.show()
    
    logger.info("测试窗口已显示")
    sys.exit(app.exec())

if __name__ == "__main__":
    main() 