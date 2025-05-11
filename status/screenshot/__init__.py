"""
---------------------------------------------------------------
File name:                  __init__.py
Author:                     Ignorant-lu
Date created:               2025/04/05
Description:                截图模块，提供快速屏幕截图功能
----------------------------------------------------------------

Changed history:            
                            2025/04/05: 初始创建;
----
"""

# 从模块中导入类和函数
from status.screenshot.screenshot_service import ScreenshotService, ScreenshotFormat, ScreenshotError
from status.screenshot.screenshot_manager import ScreenshotManager, ScreenshotEventType
from status.screenshot.factory import create_screenshot_system, create_custom_screenshot_system

# 定义公开的API
__all__ = [
    'ScreenshotService',
    'ScreenshotManager',
    'ScreenshotFormat',
    'ScreenshotError',
    'ScreenshotEventType',
    'create_screenshot_system',
    'create_custom_screenshot_system'
] 