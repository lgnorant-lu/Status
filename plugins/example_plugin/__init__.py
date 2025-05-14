"""
---------------------------------------------------------------
File name:                  __init__.py
Author:                     Ignorant-lu
Date created:               2025/05/14
Description:                示例插件入口
----------------------------------------------------------------

Changed history:            
                            2025/05/14: 初始创建;
----
"""

import logging
from status.plugin.plugin_base import PluginBase


class ExamplePlugin(PluginBase):
    """示例插件，用于演示插件系统"""
    
    def __init__(self):
        """初始化示例插件"""
        super().__init__(
            plugin_id="example_plugin",
            name="示例插件",
            version="1.0.0",
            description="用于演示插件系统的示例插件"
        )
        self.logger.info("示例插件初始化")
    
    def load(self) -> bool:
        """加载插件资源和初始化，但不激活功能
        
        Returns:
            bool: 加载是否成功
        """
        self.logger.info("示例插件加载")
        return True
    
    def enable(self) -> bool:
        """启用插件功能
        
        Returns:
            bool: 启用是否成功
        """
        self.logger.info("示例插件启用")
        return True
    
    def disable(self) -> bool:
        """禁用插件功能
        
        Returns:
            bool: 禁用是否成功
        """
        self.logger.info("示例插件禁用")
        return True
    
    def unload(self) -> bool:
        """卸载插件并释放资源
        
        Returns:
            bool: 卸载是否成功
        """
        self.logger.info("示例插件卸载")
        return True


def create_plugin() -> PluginBase:
    """创建插件实例
    
    此函数是插件系统的入口点，必须返回一个PluginBase的子类实例
    
    Returns:
        PluginBase: 插件实例
    """
    return ExamplePlugin() 