"""
---------------------------------------------------------------
File name:                  monitor_app.py
Author:                     Ignorant-lu
Date created:               2025/04/03
Description:                系统监控GUI应用启动器
----------------------------------------------------------------

Changed history:            
                            2025/04/03: 初始创建;
----
"""

import sys
import logging
import argparse
from typing import List, Optional

try:
    from PyQt6.QtWidgets import QApplication
    from PyQt6.QtCore import Qt
    HAS_PYQT = True
except ImportError:
    HAS_PYQT = False

from status.ui.monitor_ui import MonitorUIWindow


def setup_logging(level: int = logging.INFO) -> logging.Logger:
    """设置日志系统
    
    Args:
        level: 日志级别
        
    Returns:
        日志记录器实例
    """
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler("monitor.log"),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger("Hollow-ming.MonitorApp")


def parse_args(args: Optional[List[str]] = None) -> argparse.Namespace:
    """解析命令行参数
    
    Args:
        args: 命令行参数，默认使用sys.argv
        
    Returns:
        解析后的参数对象
    """
    parser = argparse.ArgumentParser(description="Hollow-ming 系统监控应用")
    parser.add_argument(
        "-d", "--debug",
        action="store_true",
        help="启用调试模式"
    )
    parser.add_argument(
        "-i", "--interval",
        type=float,
        default=1.0,
        help="监控数据更新间隔（秒）"
    )
    return parser.parse_args(args)


def run_app() -> int:
    """运行应用程序
    
    Returns:
        退出代码
    """
    # 解析命令行参数
    args = parse_args()
    
    # 设置日志级别
    log_level = logging.DEBUG if args.debug else logging.INFO
    logger = setup_logging(log_level)
    
    if not HAS_PYQT:
        logger.error("PyQt6未安装，无法启动GUI应用")
        print("错误: PyQt6未安装，请先安装PyQt6")
        return 1
    
    logger.info("启动Hollow-ming系统监控应用")
    
    try:
        # 创建应用
        app = QApplication(sys.argv)
        app.setApplicationName("Hollow-ming 系统监控")
        
        # 设置样式
        app.setStyle("Fusion")
        
        # 创建主窗口
        window = MonitorUIWindow()
        window.show()
        
        # 执行应用
        return app.exec()
    except Exception as e:
        logger.error(f"应用运行失败: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(run_app()) 