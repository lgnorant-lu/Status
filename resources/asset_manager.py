"""
---------------------------------------------------------------
File name:                  asset_manager.py
Author:                     Ignorant-lu
Date created:               2025/04/15
Description:                动画资源加载与缓存管理模块。
----------------------------------------------------------------
Changed history:            
                            2025/04/15: 初始创建;
                            2025/04/15: 按全局规范补充头部与方法注释;
----
"""

import os
from PyQt6.QtGui import QPixmap

class AssetManager:
    """动画资源加载与缓存管理器。

    支持Idle动画帧的多路径查找与QPixmap缓存。
    """
    def __init__(self, base_dir=None):
        """初始化资源管理器。

        Args:
            base_dir (str|None): 资源根目录，默认自动推断
        """
        self.base_dir = base_dir or os.path.dirname(os.path.dirname(__file__))
        self.cache = {}

    def load_idle_frame(self, idx):
        """加载指定编号的Idle动画帧图片。

        Args:
            idx (int): 帧编号（1起始）
        Returns:
            QPixmap|None: 成功则为QPixmap，否则为None
        """
        path1 = os.path.join(self.base_dir, f'frame_{idx:02d}.png')
        path2 = os.path.join(self.base_dir, 'assets', 'sprites', 'idle', f'frame_{idx:02d}.png')
        path = path1 if os.path.exists(path1) else path2
        if path in self.cache:
            return self.cache[path]
        if os.path.exists(path):
            pix = QPixmap(path)
            self.cache[path] = pix
            return pix
        return None

    def load_idle_frames(self, count=8):
        """批量加载Idle动画帧。

        Args:
            count (int): 帧总数
        Returns:
            list[QPixmap]: 动画帧列表
        """
        return [self.load_idle_frame(i+1) or QPixmap(64,64) for i in range(count)]
