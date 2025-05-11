"""
---------------------------------------------------------------
File name:                  screenshot_service.py
Author:                     Ignorant-lu
Date created:               2025/04/05
Description:                截图服务，提供屏幕截图捕获功能
----------------------------------------------------------------

Changed history:            
                            2025/04/05: 初始创建;
----
"""

import os
import logging
import time
from datetime import datetime
from typing import Dict, Any, Optional, Callable, Tuple, List, Union
from enum import Enum, auto
import pyautogui
import tempfile
from PIL import Image, ImageGrab

# 配置日志记录器
logger = logging.getLogger(__name__)

class ScreenshotFormat(Enum):
    """截图文件格式"""
    PNG = "png"
    JPG = "jpg"
    BMP = "bmp"

class ScreenshotError(Exception):
    """截图过程中的错误"""
    pass

class ScreenshotService:
    """截图服务类
    
    负责实际执行屏幕截图功能，包括全屏和区域截图，
    以及截图的保存和处理。
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """初始化截图服务
        
        Args:
            config: 配置参数，包括保存路径、文件格式等
        """
        self.config = config or {}
        
        # 默认保存路径
        self.save_dir = self.config.get('save_dir', os.path.join(os.path.expanduser('~'), 'Pictures', 'Screenshots'))
        
        # 确保保存目录存在
        os.makedirs(self.save_dir, exist_ok=True)
        
        # 默认文件格式
        self.format = ScreenshotFormat(self.config.get('format', 'png'))
        
        # 是否包含鼠标光标
        self.include_cursor = self.config.get('include_cursor', False)
        
        # 默认文件名格式
        self.filename_pattern = self.config.get('filename_pattern', 'screenshot_%Y%m%d_%H%M%S')
        
        # 截图计数器
        self.counter = 0
        
        # 上次截图的文件路径
        self.last_screenshot_path = None
        
        # 回调函数
        self.on_screenshot_taken = None
        self.on_error = None
        
        logger.info("截图服务已初始化")
    
    def take_full_screenshot(self) -> Optional[str]:
        """获取全屏截图
        
        Returns:
            str: 保存的截图文件路径，失败时返回None
        """
        try:
            # 生成文件名
            filename = self._generate_filename()
            filepath = os.path.join(self.save_dir, filename)
            
            # 捕获屏幕
            if self.include_cursor:
                # 使用pyautogui包含鼠标光标
                screenshot = pyautogui.screenshot()
            else:
                # 使用PIL不包含鼠标光标
                screenshot = ImageGrab.grab()
                
            # 保存截图
            screenshot.save(filepath, format=self.format.value.upper())
            
            logger.info(f"全屏截图已保存至: {filepath}")
            self.last_screenshot_path = filepath
            
            # 调用回调函数
            if self.on_screenshot_taken:
                self.on_screenshot_taken(filepath)
                
            return filepath
            
        except Exception as e:
            logger.error(f"全屏截图失败: {str(e)}")
            
            if self.on_error:
                self.on_error(str(e))
                
            raise ScreenshotError(f"全屏截图失败: {str(e)}")
    
    def take_region_screenshot(self, region: Tuple[int, int, int, int]) -> Optional[str]:
        """获取区域截图
        
        Args:
            region: 区域坐标和大小 (x, y, width, height)
            
        Returns:
            str: 保存的截图文件路径，失败时返回None
        """
        try:
            # 生成文件名
            filename = self._generate_filename()
            filepath = os.path.join(self.save_dir, filename)
            
            # 捕获指定区域
            if self.include_cursor:
                # 使用pyautogui包含鼠标光标，然后裁剪
                full_screenshot = pyautogui.screenshot()
                region_screenshot = full_screenshot.crop(
                    (region[0], region[1], region[0] + region[2], region[1] + region[3])
                )
            else:
                # 使用PIL不包含鼠标光标
                region_screenshot = ImageGrab.grab(
                    bbox=(region[0], region[1], region[0] + region[2], region[1] + region[3])
                )
                
            # 保存截图
            region_screenshot.save(filepath, format=self.format.value.upper())
            
            logger.info(f"区域截图已保存至: {filepath}")
            self.last_screenshot_path = filepath
            
            # 调用回调函数
            if self.on_screenshot_taken:
                self.on_screenshot_taken(filepath)
                
            return filepath
            
        except Exception as e:
            logger.error(f"区域截图失败: {str(e)}")
            
            if self.on_error:
                self.on_error(str(e))
                
            raise ScreenshotError(f"区域截图失败: {str(e)}")
    
    def take_window_screenshot(self, window_title: str = None) -> Optional[str]:
        """获取窗口截图
        
        Args:
            window_title: 窗口标题，为None时捕获活动窗口
            
        Returns:
            str: 保存的截图文件路径，失败时返回None
        """
        try:
            # 在Windows平台上，使用pyautogui获取窗口截图
            import platform
            if platform.system() != 'Windows':
                logger.warning("窗口截图仅支持Windows平台")
                return self.take_full_screenshot()
            
            # 导入win32gui模块
            import win32gui
            import win32con
            
            # 找到目标窗口句柄
            if window_title:
                hwnd = win32gui.FindWindow(None, window_title)
                if hwnd == 0:
                    logger.warning(f"未找到标题为 '{window_title}' 的窗口")
                    return None
            else:
                # 获取活动窗口
                hwnd = win32gui.GetForegroundWindow()
            
            # 获取窗口位置和大小
            rect = win32gui.GetWindowRect(hwnd)
            x, y, x2, y2 = rect
            width = x2 - x
            height = y2 - y
            
            # 生成文件名
            filename = self._generate_filename()
            filepath = os.path.join(self.save_dir, filename)
            
            # 捕获窗口区域
            window_screenshot = ImageGrab.grab(bbox=(x, y, x2, y2))
            
            # 保存截图
            window_screenshot.save(filepath, format=self.format.value.upper())
            
            logger.info(f"窗口截图已保存至: {filepath}")
            self.last_screenshot_path = filepath
            
            # 调用回调函数
            if self.on_screenshot_taken:
                self.on_screenshot_taken(filepath)
                
            return filepath
            
        except Exception as e:
            logger.error(f"窗口截图失败: {str(e)}")
            
            if self.on_error:
                self.on_error(str(e))
                
            raise ScreenshotError(f"窗口截图失败: {str(e)}")
    
    def get_screen_size(self) -> Tuple[int, int]:
        """获取屏幕分辨率
        
        Returns:
            Tuple[int, int]: 屏幕宽度和高度
        """
        return pyautogui.size()
    
    def get_mouse_position(self) -> Tuple[int, int]:
        """获取鼠标位置
        
        Returns:
            Tuple[int, int]: 鼠标当前的x和y坐标
        """
        return pyautogui.position()
    
    def set_save_directory(self, directory: str) -> bool:
        """设置截图保存目录
        
        Args:
            directory: 新的保存目录路径
            
        Returns:
            bool: 是否成功设置
        """
        try:
            # 确保目录存在
            os.makedirs(directory, exist_ok=True)
            
            # 更新保存目录
            self.save_dir = directory
            
            logger.info(f"截图保存目录已更新: {directory}")
            return True
            
        except Exception as e:
            logger.error(f"设置保存目录失败: {str(e)}")
            
            if self.on_error:
                self.on_error(str(e))
                
            return False
    
    def set_format(self, format_str: str) -> bool:
        """设置截图格式
        
        Args:
            format_str: 格式字符串("png", "jpg", "bmp")
            
        Returns:
            bool: 是否成功设置
        """
        try:
            self.format = ScreenshotFormat(format_str.lower())
            logger.info(f"截图格式已更新: {self.format.value}")
            return True
            
        except ValueError:
            logger.error(f"无效的格式: {format_str}")
            
            if self.on_error:
                self.on_error(f"无效的格式: {format_str}")
                
            return False
    
    def set_filename_pattern(self, pattern: str) -> None:
        """设置文件名模式
        
        Args:
            pattern: 文件名模式，使用strftime格式
        """
        self.filename_pattern = pattern
        logger.info(f"文件名模式已更新: {pattern}")
    
    def open_save_directory(self) -> bool:
        """打开保存目录
        
        Returns:
            bool: 是否成功打开
        """
        try:
            import platform
            import subprocess
            
            system = platform.system()
            
            if system == 'Windows':
                os.startfile(self.save_dir)
            elif system == 'Darwin':  # macOS
                subprocess.run(['open', self.save_dir])
            else:  # Linux
                subprocess.run(['xdg-open', self.save_dir])
                
            logger.info(f"已打开保存目录: {self.save_dir}")
            return True
            
        except Exception as e:
            logger.error(f"打开保存目录失败: {str(e)}")
            
            if self.on_error:
                self.on_error(str(e))
                
            return False
    
    def register_screenshot_callback(self, callback: Callable[[str], None]) -> None:
        """注册截图完成回调函数
        
        Args:
            callback: 回调函数，接收截图文件路径作为参数
        """
        self.on_screenshot_taken = callback
        logger.debug("已注册截图完成回调函数")
    
    def register_error_callback(self, callback: Callable[[str], None]) -> None:
        """注册错误回调函数
        
        Args:
            callback: 回调函数，接收错误消息作为参数
        """
        self.on_error = callback
        logger.debug("已注册错误回调函数")
    
    def get_last_screenshot(self) -> Optional[str]:
        """获取最后一次截图的文件路径
        
        Returns:
            str: 最后一次截图的文件路径，如果没有则返回None
        """
        return self.last_screenshot_path
    
    def copy_to_clipboard(self, filepath: Optional[str] = None) -> bool:
        """将截图复制到剪贴板
        
        Args:
            filepath: 截图文件路径，为None时使用最后一次的截图
            
        Returns:
            bool: 是否成功复制
        """
        try:
            # 使用最后一次截图的路径
            if filepath is None:
                filepath = self.last_screenshot_path
                
            if not filepath or not os.path.exists(filepath):
                logger.warning("没有可用的截图文件")
                return False
                
            # 读取图像
            image = Image.open(filepath)
            
            # 复制到剪贴板
            import platform
            system = platform.system()
            
            if system == 'Windows':
                import win32clipboard
                from io import BytesIO
                
                # 将图像转换为BMP格式（Windows剪贴板所需）
                output = BytesIO()
                image.convert('RGB').save(output, 'BMP')
                data = output.getvalue()[14:]  # 去除BMP文件头
                output.close()
                
                # 复制到剪贴板
                win32clipboard.OpenClipboard()
                win32clipboard.EmptyClipboard()
                win32clipboard.SetClipboardData(win32clipboard.CF_DIB, data)
                win32clipboard.CloseClipboard()
                
            elif system == 'Darwin':  # macOS
                import subprocess
                
                # 将图像保存到临时文件
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
                temp_file.close()
                image.save(temp_file.name)
                
                # 使用osascript复制到剪贴板
                subprocess.run(['osascript', '-e', 
                              f'set the clipboard to (read (POSIX file "{temp_file.name}") as TIFF picture)'])
                
                # 删除临时文件
                os.unlink(temp_file.name)
                
            else:  # Linux
                import subprocess
                
                # 保存为临时文件
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
                temp_file.close()
                image.save(temp_file.name)
                
                # 使用xclip复制到剪贴板
                subprocess.run(['xclip', '-selection', 'clipboard', '-t', 'image/png', '-i', temp_file.name])
                
                # 删除临时文件
                os.unlink(temp_file.name)
            
            logger.info("截图已复制到剪贴板")
            return True
            
        except Exception as e:
            logger.error(f"复制到剪贴板失败: {str(e)}")
            
            if self.on_error:
                self.on_error(str(e))
                
            return False
    
    def _generate_filename(self) -> str:
        """生成截图文件名
        
        Returns:
            str: 生成的文件名
        """
        # 生成时间戳
        timestamp = datetime.now().strftime(self.filename_pattern)
        
        # 增加计数器
        self.counter += 1
        
        # 返回文件名
        return f"{timestamp}_{self.counter}.{self.format.value}" 