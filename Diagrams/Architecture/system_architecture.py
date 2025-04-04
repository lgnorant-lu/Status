"""
---------------------------------------------------------------
File name:                  system_architecture.py
Author:                     Ignorant-lu
Date created:               2024/04/04
Description:                系统总体架构图生成脚本 - 使用Diagrams库
----------------------------------------------------------------

Changed history:            
                            2024/04/04: 初始创建;
                            2024/04/04: 更新风格为圆角和圆形，使用卡其色调和绿色系;
                            2024/04/04: 更新为中心辐射型结构，核心引擎为中心;
                            2024/04/04: 更新为黑色背景，简化连接线，采用鲜明色彩区分;
                            2024/04/04: 调整为扁平星形布局，直接从核心连接所有节点;
                            2024/04/04: 优化为环树状结构，中心向四周辐射展开;
                            2024/04/04: 使用Diagrams库重写，采用更现代的图表风格;
                            2024/04/04: 简化实现，使用内置节点类型;
----
"""

from diagrams import Diagram, Cluster, Edge
from diagrams.onprem.compute import Server
from diagrams.onprem.database import PostgreSQL
from diagrams.onprem.network import Nginx
from diagrams.onprem.client import Users
from diagrams.programming.framework import React
from diagrams.programming.language import Python
from diagrams.generic.storage import Storage
from diagrams.generic.compute import Rack

def generate_diagram():
    """
    生成系统架构图 - 使用Diagrams库内置节点
    """
    
    # 开始创建架构图
    with Diagram(
        "Hollow-ming系统架构图",
        filename="system_architecture",
        outformat="png",
        show=False,
        direction="LR",
        graph_attr={
            "bgcolor": "#121212",
            "fontcolor": "white",
            "fontname": "Microsoft YaHei",
            "fontsize": "20",
            "overlap": "false",
            "splines": "curved",
            "nodesep": "0.75",
            "ranksep": "0.75",
            "pad": "0.5",
        },
        node_attr={
            "fontcolor": "white",
            "fontname": "Microsoft YaHei",
            "fontsize": "14",
        },
        edge_attr={
            "color": "#606060",
            "arrowsize": "0.5",
        }
    ):
        # 创建核心节点
        core_engine = Server("核心引擎")
        
        # 创建业务层节点
        scene_manager = Server("场景管理器")
        render_system = Server("渲染系统")
        resource_system = Server("资源系统")
        config_system = Server("配置系统")
        
        # 创建表现层节点
        ui = React("UI组件")
        interaction = React("交互系统")
        scene_editor = React("场景编辑器")
        visual_effects = React("视觉效果")
        
        # 创建数据层节点
        file_system = Storage("文件系统")
        database = PostgreSQL("数据库")
        cache = Rack("缓存")
        serialization = Python("序列化")
        
        # 创建工具层和其他节点
        plugin_system = Python("插件系统")
        event_system = Python("事件系统")
        logging = Python("日志系统")
        api_interface = Nginx("API接口")
        others = Users("其他模块")
        
        # 连接核心节点到业务层
        core_engine >> scene_manager
        core_engine >> render_system
        core_engine >> resource_system
        core_engine >> config_system
        
        # 连接核心节点到工具层
        core_engine >> plugin_system
        core_engine >> logging
        core_engine >> others
        
        # 连接业务层到表现层
        config_system >> ui
        core_engine >> interaction
        scene_manager >> scene_editor
        render_system >> visual_effects
        
        # 连接业务层到数据层
        resource_system >> file_system
        scene_manager >> database
        render_system >> cache
        config_system >> serialization
        
        # 连接工具层到其他节点
        interaction >> event_system
        config_system >> api_interface
        
        # 添加表现层内部连接（用虚线）
        ui >> Edge(style="dashed") >> interaction
        interaction >> Edge(style="dashed") >> scene_editor
        scene_editor >> Edge(style="dashed") >> visual_effects
        visual_effects >> Edge(style="dashed") >> ui

if __name__ == '__main__':
    generate_diagram() 