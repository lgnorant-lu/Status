"""
---------------------------------------------------------------
File name:                  __init__.py
Author:                     Ignorant-lu
Date created:               2025/05/14
Description:                测试包
----------------------------------------------------------------

Changed history:            
                            2025/05/14: 初始创建;
----
"""

import sys
import os

# 添加项目根目录到Python路径，以便测试可以导入status包
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))) 