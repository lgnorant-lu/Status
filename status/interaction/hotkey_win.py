"""
---------------------------------------------------------------
File name:                  hotkey_win.py
Author:                     Ignorant-lu
Date created:               2025/04/03
Description:                Windows平台的全局热键处理实现
----------------------------------------------------------------

Changed history:            
                            2025/04/03: 初始创建;
----
"""

import logging
import time
import win32con
import win32gui
import win32api
import threading

# 配置日志
logger = logging.getLogger(__name__)

# 定义修饰键常量
MOD_ALT = win32con.MOD_ALT
MOD_CONTROL = win32con.MOD_CONTROL
MOD_SHIFT = win32con.MOD_SHIFT
MOD_WIN = win32con.MOD_WIN

# 虚拟键码映射
VK_MAP = {
    'A': ord('A'), 'B': ord('B'), 'C': ord('C'), 'D': ord('D'),
    'E': ord('E'), 'F': ord('F'), 'G': ord('G'), 'H': ord('H'),
    'I': ord('I'), 'J': ord('J'), 'K': ord('K'), 'L': ord('L'),
    'M': ord('M'), 'N': ord('N'), 'O': ord('O'), 'P': ord('P'),
    'Q': ord('Q'), 'R': ord('R'), 'S': ord('S'), 'T': ord('T'),
    'U': ord('U'), 'V': ord('V'), 'W': ord('W'), 'X': ord('X'),
    'Y': ord('Y'), 'Z': ord('Z'),
    '0': ord('0'), '1': ord('1'), '2': ord('2'), '3': ord('3'),
    '4': ord('4'), '5': ord('5'), '6': ord('6'), '7': ord('7'),
    '8': ord('8'), '9': ord('9'),
    'F1': win32con.VK_F1, 'F2': win32con.VK_F2, 'F3': win32con.VK_F3,
    'F4': win32con.VK_F4, 'F5': win32con.VK_F5, 'F6': win32con.VK_F6,
    'F7': win32con.VK_F7, 'F8': win32con.VK_F8, 'F9': win32con.VK_F9,
    'F10': win32con.VK_F10, 'F11': win32con.VK_F11, 'F12': win32con.VK_F12,
    'Tab': win32con.VK_TAB, 'Space': win32con.VK_SPACE,
    'Return': win32con.VK_RETURN, 'Enter': win32con.VK_RETURN,
    'Escape': win32con.VK_ESCAPE, 'Esc': win32con.VK_ESCAPE,
    'Backspace': win32con.VK_BACK,
    'Insert': win32con.VK_INSERT, 'Delete': win32con.VK_DELETE,
    'Home': win32con.VK_HOME, 'End': win32con.VK_END,
    'PageUp': win32con.VK_PRIOR, 'PageDown': win32con.VK_NEXT,
    'Left': win32con.VK_LEFT, 'Right': win32con.VK_RIGHT,
    'Up': win32con.VK_UP, 'Down': win32con.VK_DOWN,
}


class WindowsHotkeyHandler:
    """Windows平台的全局热键处理实现类
    
    使用Windows API实现全局热键的注册和监听。
    """
    
    def __init__(self):
        """初始化Windows热键处理器
        """
        self.hotkeys = {}
        self.callback = None
        self.running = False
        self.message_window = None
        self.next_id = 1
        self.message_thread = None
        self.lock = threading.Lock()
        
        logger.info("WindowsHotkeyHandler initialized")
    
    def start(self, callback):
        """启动热键监听
        
        Args:
            callback (function): 热键触发时的回调函数
            
        Returns:
            bool: 是否成功启动
        """
        if self.running:
            logger.warning("WindowsHotkeyHandler already running")
            return True
        
        self.callback = callback
        self.running = True
        
        # 创建消息窗口线程
        self.message_thread = threading.Thread(
            target=self._message_window_thread,
            daemon=True
        )
        self.message_thread.start()
        
        # 等待消息窗口创建完成
        while self.running and not self.message_window:
            time.sleep(0.1)
        
        logger.info("WindowsHotkeyHandler started")
        return True
    
    def stop(self):
        """停止热键监听
        
        Returns:
            bool: 是否成功停止
        """
        if not self.running:
            logger.warning("WindowsHotkeyHandler not running")
            return True
        
        try:
            self.running = False
            
            # 发送消息结束消息窗口线程
            if self.message_window:
                win32gui.PostMessage(self.message_window, win32con.WM_CLOSE, 0, 0)
            
            # 等待消息窗口线程结束
            if self.message_thread and self.message_thread.is_alive():
                self.message_thread.join(timeout=1.0)
            
            logger.info("WindowsHotkeyHandler stopped")
            return True
            
        except Exception as e:
            logger.error(f"Failed to stop WindowsHotkeyHandler: {str(e)}")
            return False
    
    def poll(self):
        """轮询方法
        
        在Windows实现中这是一个空方法，因为消息处理在专用线程中。
        """
        # Windows的热键处理是基于消息的，不需要轮询
        time.sleep(0.01)
    
    def _message_window_thread(self):
        """消息窗口线程
        
        创建一个隐藏的消息窗口来接收热键消息。
        """
        try:
            # 注册窗口类
            wc = win32gui.WNDCLASS()
            wc.lpfnWndProc = self._window_proc
            wc.lpszClassName = "DesktopPetHotkeyWindow"
            wc.hInstance = win32api.GetModuleHandle(None)
            
            # 注册类
            class_atom = win32gui.RegisterClass(wc)
            
            # 创建窗口
            self.message_window = win32gui.CreateWindow(
                class_atom,
                "Desktop Pet Hotkey Window",
                0,  # 样式
                0, 0, 0, 0,  # 位置和大小
                0,  # 父窗口
                0,  # 菜单
                wc.hInstance,
                None  # 参数
            )
            
            logger.debug(f"Message window created: {self.message_window}")
            
            # 消息循环
            while self.running:
                try:
                    # 获取消息
                    msg = win32gui.GetMessage(None, 0, 0)
                    
                    # 如果是退出消息，结束循环
                    if msg[0] == 0:
                        break
                    
                    # 翻译和分发消息
                    win32gui.TranslateMessage(msg)
                    win32gui.DispatchMessage(msg)
                    
                except Exception as e:
                    logger.error(f"Error in message loop: {str(e)}")
                    break
            
            # 注销所有热键
            with self.lock:
                for hotkey_id in self.hotkeys.values():
                    try:
                        win32gui.UnregisterHotKey(self.message_window, hotkey_id)
                    except Exception as e:
                        logger.error(f"Error unregistering hotkey {hotkey_id}: {str(e)}")
            
            # 销毁窗口
            if self.message_window:
                win32gui.DestroyWindow(self.message_window)
                self.message_window = None
            
            # 注销窗口类
            win32gui.UnregisterClass(class_atom, wc.hInstance)
            
            logger.debug("Message window thread ended")
            
        except Exception as e:
            logger.error(f"Error in message window thread: {str(e)}")
            self.running = False
            self.message_window = None
    
    def _window_proc(self, hwnd, msg, wparam, lparam):
        """窗口过程函数
        
        处理窗口消息，特别是WM_HOTKEY消息。
        
        Args:
            hwnd: 窗口句柄
            msg: 消息ID
            wparam: WPARAM参数
            lparam: LPARAM参数
            
        Returns:
            int: 消息处理结果
        """
        if msg == win32con.WM_HOTKEY:
            # 热键ID
            hotkey_id = wparam
            
            # 查找对应的热键组合
            with self.lock:
                key_combination = None
                for k, v in self.hotkeys.items():
                    if v == hotkey_id:
                        key_combination = k
                        break
            
            if key_combination and self.callback:
                try:
                    # 调用回调函数
                    self.callback(key_combination)
                except Exception as e:
                    logger.error(f"Error calling hotkey callback: {str(e)}")
                    
            return 0
            
        elif msg == win32con.WM_CLOSE:
            # 结束消息循环
            win32gui.PostQuitMessage(0)
            return 0
            
        elif msg == win32con.WM_DESTROY:
            return 0
            
        # 默认窗口过程
        return win32gui.DefWindowProc(hwnd, msg, wparam, lparam)
    
    def register_hotkey(self, key_combination):
        """注册热键
        
        Args:
            key_combination (str): 热键组合字符串，例如"Ctrl+Alt+P"
            
        Returns:
            bool: 是否成功注册
        """
        if not self.message_window:
            logger.error("Message window not created, cannot register hotkey")
            return False
        
        try:
            # 解析热键组合
            modifiers, vk = self._parse_key_combination(key_combination)
            
            if vk is None:
                logger.error(f"Invalid key in combination: {key_combination}")
                return False
            
            # 分配热键ID
            with self.lock:
                if key_combination in self.hotkeys:
                    logger.warning(f"Hotkey {key_combination} already registered")
                    return True
                
                hotkey_id = self.next_id
                self.next_id += 1
            
            # 注册热键
            if win32gui.RegisterHotKey(self.message_window, hotkey_id, modifiers, vk):
                with self.lock:
                    self.hotkeys[key_combination] = hotkey_id
                logger.info(f"Registered hotkey {key_combination} with id {hotkey_id}")
                return True
            else:
                logger.error(f"Failed to register hotkey {key_combination}")
                return False
                
        except Exception as e:
            logger.error(f"Error registering hotkey {key_combination}: {str(e)}")
            return False
    
    def unregister_hotkey(self, key_combination):
        """注销热键
        
        Args:
            key_combination (str): 热键组合字符串
            
        Returns:
            bool: 是否成功注销
        """
        if not self.message_window:
            logger.error("Message window not created, cannot unregister hotkey")
            return False
        
        try:
            # 获取热键ID
            with self.lock:
                if key_combination not in self.hotkeys:
                    logger.warning(f"Hotkey {key_combination} not registered")
                    return False
                
                hotkey_id = self.hotkeys[key_combination]
            
            # 注销热键
            if win32gui.UnregisterHotKey(self.message_window, hotkey_id):
                with self.lock:
                    del self.hotkeys[key_combination]
                logger.info(f"Unregistered hotkey {key_combination} with id {hotkey_id}")
                return True
            else:
                logger.error(f"Failed to unregister hotkey {key_combination}")
                return False
                
        except Exception as e:
            logger.error(f"Error unregistering hotkey {key_combination}: {str(e)}")
            return False
    
    def _parse_key_combination(self, key_combination):
        """解析热键组合
        
        解析形如"Ctrl+Alt+P"的热键组合字符串。
        
        Args:
            key_combination (str): 热键组合字符串
            
        Returns:
            tuple: (修饰键标志, 虚拟键码)
        """
        try:
            # 分割组合键
            parts = key_combination.split('+')
            
            # 初始化修饰键标志
            modifiers = 0
            
            # 最后一个部分是主键
            main_key = parts[-1].strip()
            
            # 前面的部分是修饰键
            for modifier in parts[:-1]:
                modifier = modifier.strip().lower()
                
                if modifier == 'ctrl' or modifier == 'control':
                    modifiers |= MOD_CONTROL
                elif modifier == 'alt':
                    modifiers |= MOD_ALT
                elif modifier == 'shift':
                    modifiers |= MOD_SHIFT
                elif modifier == 'win' or modifier == 'windows':
                    modifiers |= MOD_WIN
                else:
                    logger.warning(f"Unknown modifier: {modifier}")
            
            # 获取主键的虚拟键码
            if main_key.upper() in VK_MAP:
                vk = VK_MAP[main_key.upper()]
            else:
                logger.error(f"Unknown key: {main_key}")
                return modifiers, None
            
            return modifiers, vk
            
        except Exception as e:
            logger.error(f"Error parsing key combination {key_combination}: {str(e)}")
            return 0, None 