"""
---------------------------------------------------------------
File name:                  launcher_example.py
Author:                     Ignorant-lu
Date created:               2023/11/28
Description:                快捷启动器示例应用
----------------------------------------------------------------

Changed history:
                           2023/11/28: 初始创建
                            2023/11/29: 添加导入/导出功能支持;
                            2025/04/05: 修复路径和UI初始化问题;
----
"""

import sys
import os
import logging
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
import traceback

# 导入启动器相关组件
from status.launcher import LauncherManager, LauncherUI, LaunchedApplication, LauncherGroup

# 设置日志
logger = logging.getLogger(__name__)

def add_example_applications(manager):
    """添加示例应用到启动器"""
    # 创建常用工具分组
    common_tools = LauncherGroup(
        name="常用工具",
        description="常用的应用程序工具"
    )
    
    # 创建系统工具分组
    system_tools = LauncherGroup(
        name="系统工具",
        description="系统管理工具"
    )
    
    # 创建收藏夹分组
    favorites_group = LauncherGroup(
        name="收藏夹",
        description="收藏的应用程序"
    )
    
    # 添加分组
    manager.add_group(common_tools)
    manager.add_group(system_tools)
    manager.add_group(favorites_group)
    
    # 设置收藏夹分组ID
    manager.config["favorite_group_id"] = favorites_group.id
    
    # 添加应用
    notepad = LaunchedApplication(
        name="记事本",
        path="C:\\Windows\\System32\\notepad.exe",
        description="Windows记事本程序"
    )
    
    calculator = LaunchedApplication(
        name="计算器",
        path="C:\\Windows\\System32\\calc.exe",
        description="Windows计算器"
    )
    
    # 移除画图程序，因为不同Windows版本路径可能不同
    # 添加更通用的应用
    wordpad = LaunchedApplication(
        name="写字板",
        path="C:\\Program Files\\Windows NT\\Accessories\\wordpad.exe", 
        description="Windows写字板程序"
    )
    
    cmd = LaunchedApplication(
        name="命令提示符",
        path="C:\\Windows\\System32\\cmd.exe",
        description="Windows命令提示符"
    )
    
    explorer = LaunchedApplication(
        name="文件资源管理器",
        path="C:\\Windows\\explorer.exe",
        description="Windows文件资源管理器"
    )
    
    # 将应用添加到启动器
    manager.add_application(notepad)
    manager.add_application(calculator)
    manager.add_application(wordpad)  # 替换paint为wordpad
    manager.add_application(cmd)
    manager.add_application(explorer)
    
    # 将应用添加到分组
    manager.add_to_group(notepad.id, common_tools.id)
    manager.add_to_group(calculator.id, common_tools.id)
    manager.add_to_group(wordpad.id, common_tools.id)  # 更新为wordpad
    
    manager.add_to_group(cmd.id, system_tools.id)
    manager.add_to_group(explorer.id, system_tools.id)
    
    # 设置收藏
    manager.toggle_favorite(notepad.id)
    manager.toggle_favorite(explorer.id)
    
    logger.info("已添加示例应用")
    
    return manager

def add_demo_features(manager):
    """添加演示功能
    
    Args:
        manager: 启动器管理器
    """
    # 添加示例应用
    add_example_applications(manager)
    
    # 创建示例导出
    try:
        # 导出所有应用到示例文件
        all_apps_path = os.path.join(os.path.dirname(__file__), "all_apps_export.json")
        manager.export_applications(all_apps_path)
        print(f"已导出所有应用到: {all_apps_path}")
        
        # 导出"常用工具"分组
        common_group = None
        for group in manager.groups.values():
            if group.name == "常用工具":
                common_group = group
                break
                
        if common_group:
            common_group_path = os.path.join(os.path.dirname(__file__), "common_tools_export.json")
            manager.export_group(common_group.id, common_group_path)
            print(f"已导出'常用工具'分组到: {common_group_path}")
    except Exception as e:
        print(f"导出示例文件时出错: {str(e)}")

def show_launcher():
    """显示启动器界面"""
    # 创建启动器管理器
    manager = LauncherManager()
    
    # 获取配置管理器
    from status.core.config import ConfigManager
    config_manager = ConfigManager.get_instance()
    manager.config_manager = config_manager
    
    # 模拟事件管理器
    from unittest.mock import MagicMock
    event_manager = MagicMock()
    manager.event_manager = event_manager
    
    # 初始化管理器
    manager.initialize()
    
    # 添加示例
    add_example_applications(manager)
    
    # 添加演示功能
    add_demo_features(manager)
    
    # 创建并显示UI，注意传递launcher_manager作为参数而不是parent参数
    app = QApplication(sys.argv)
    ui = LauncherUI(launcher_manager=manager)
    ui.show()
    
    # 运行应用
    return app.exec()

def main():
    """主函数"""
    try:
        # 设置日志
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # 显示启动器
        exit_code = show_launcher()
        sys.exit(exit_code)
        
    except Exception as e:
        print(f"错误: {str(e)}")
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main() 