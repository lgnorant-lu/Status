"""
---------------------------------------------------------------
File name:                  simple_qt_test.py
Author:                     Ignorant-lu
Date created:               2025/04/05
Description:                简单的PyQt6测试程序
----------------------------------------------------------------

Changed history:            
                            2025/04/05: 初始创建;
----
"""

import sys
import os
import traceback

# 确保可以导入上层包
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))

print("开始执行PyQt6测试程序")

# 尝试导入PyQt6
try:
    print("尝试导入PyQt6...")
    from PyQt6.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget
    from PyQt6.QtCore import Qt
    
    print("PyQt6成功导入")
    
    class SimpleWindow(QMainWindow):
        def __init__(self):
            print("初始化SimpleWindow...")
            super().__init__()
            
            # 设置窗口标题和大小
            self.setWindowTitle("PyQt6测试")
            self.resize(300, 200)
            
            # 创建中央部件
            central_widget = QWidget()
            self.setCentralWidget(central_widget)
            
            # 创建布局
            layout = QVBoxLayout(central_widget)
            
            # 添加标签
            label = QLabel("PyQt6测试成功！")
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(label)
            print("SimpleWindow初始化完成")
    
    def main():
        print("进入main函数")
        try:
            print("创建QApplication...")
            app = QApplication(sys.argv)
            print("创建SimpleWindow...")
            window = SimpleWindow()
            print("显示窗口...")
            window.show()
            print("启动应用程序事件循环...")
            return app.exec()
        except Exception as e:
            print(f"执行过程中发生错误: {e}")
            traceback.print_exc()
            return 1
    
    if __name__ == "__main__":
        print("程序开始执行...")
        try:
            exit_code = main()
            print(f"程序退出，退出码: {exit_code}")
            sys.exit(exit_code)
        except Exception as e:
            print(f"主程序发生错误: {e}")
            traceback.print_exc()
            sys.exit(1)
        
except ImportError as e:
    print(f"导入PyQt6失败: {e}")
    print("请确保已安装PyQt6库: pip install PyQt6")
except Exception as e:
    print(f"发生未知错误: {e}")
    traceback.print_exc() 