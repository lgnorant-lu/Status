"""
---------------------------------------------------------------
File name:                  run_monitor_ui.py
Author:                     Ignorant-lu
Date created:               2025/04/03
Description:                运行系统监控GUI示例
----------------------------------------------------------------

Changed history:            
                            2025/04/03: 初始创建;
----
"""

import sys
import os

# 将项目根目录添加到模块搜索路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from status.ui.monitor_app import run_app

if __name__ == "__main__":
    print("启动Hollow-ming系统监控GUI...")
    sys.exit(run_app()) 