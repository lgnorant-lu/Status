"""
---------------------------------------------------------------
File name:                  app.py
Author:                     Ignorant-lu
Date created:               2025/04/15
Description:                应用主入口，负责启动桌宠主窗口。
----------------------------------------------------------------
Changed history:            
                            2025/04/15: 初始创建;
                            2025/04/15: 按全局规范补充头部注释;
----
"""

import sys
from PyQt6.QtWidgets import QApplication
from renderer.pyqt_renderer import KnightIdleWidget

def main():
    """应用主入口，启动桌宠Idle窗口。"""
    app = QApplication(sys.argv)
    knight = KnightIdleWidget()
    knight.move(200, 200)
    knight.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
