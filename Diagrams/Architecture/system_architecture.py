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
                            2024/04/04: 调整结构与样式，参考样图，底色改为#BFFDCC;
----
"""

from diagrams import Diagram, Cluster, Edge, Node
from diagrams.onprem.compute import Server
from diagrams.onprem.database import PostgreSQL
from diagrams.onprem.network import Nginx
from diagrams.onprem.client import Users
from diagrams.programming.framework import React
from diagrams.programming.language import Python
from diagrams.generic.storage import Storage
from diagrams.generic.compute import Rack

# 创建自定义节点类 - 分配不同颜色
class ColorNode(Node):
    def __init__(self, label, color):
        super().__init__(label)
        self._attrs["fillcolor"] = color
        self._attrs["style"] = "filled"
        self._attrs["fontcolor"] = "white"
        self._attrs["shape"] = "circle"
        self._attrs["width"] = "1.2"
        self._attrs["height"] = "1.2"
        self._attrs["fixedsize"] = "true"

def generate_diagram():
    """
    生成系统架构图 - 使用中心辐射型结构
    """
    # 颜色方案 - 参考样图
    colors = {
        'core': '#9c27b0',          # 紫色 - 核心
        'main_meals': '#ff5722',    # 橙色 - 主餐类
        'snacks': '#8bc34a',        # 绿色 - 零食类
        'drinking': '#03a9f4',      # 蓝色 - 饮品类
        'medication': '#f44336',    # 红色 - 药物类
        'others': '#9e9e9e',        # 灰色 - 其他
    }
    
    # 开始创建架构图
    with Diagram(
        "Hollow-ming系统架构图",
        filename="system_architecture",
        outformat="png",
        show=False,
        direction="TB",  # 改为自上而下的布局
        graph_attr={
            "bgcolor": "#BFFDCC",
            "fontcolor": "#333333",
            "fontname": "Microsoft YaHei",
            "fontsize": "20",
            "overlap": "false",
            "splines": "true",  # 使用样条线
            "sep": "+20",
            "nodesep": "0.8",
            "ranksep": "1.0", 
            "concentrate": "true", # 合并边
        },
        node_attr={
            "fontcolor": "white",
            "fontname": "Microsoft YaHei",
            "fontsize": "14",
        },
        edge_attr={
            "color": "#666666",
            "arrowsize": "0.6",
        }
    ):
        # 创建核心节点
        core_engine = ColorNode("核心引擎", colors['core'])
        
        # ===== 创建主要分类节点 =====
        # 业务层节点 - 对应参考图中的橙色节点
        with Cluster("", graph_attr={"style": "invis"}):
            scene_system = ColorNode("场景系统", colors['main_meals'])
            render_system = ColorNode("渲染系统", colors['main_meals'])
            resource_system = ColorNode("资源系统", colors['main_meals'])
            config_system = ColorNode("配置系统", colors['main_meals'])
        
        # 表现层节点 - 对应参考图中的绿色节点
        with Cluster("", graph_attr={"style": "invis"}):
            ui_system = ColorNode("UI系统", colors['snacks'])
            interaction_system = ColorNode("交互系统", colors['snacks'])
            scene_editor = ColorNode("场景编辑器", colors['snacks'])
            visual_system = ColorNode("视觉系统", colors['snacks'])
        
        # 工具层节点 - 对应参考图中的蓝色节点
        with Cluster("", graph_attr={"style": "invis"}):
            plugin_system = ColorNode("插件系统", colors['drinking'])
            event_system = ColorNode("事件系统", colors['drinking'])
            log_system = ColorNode("日志系统", colors['drinking'])
            api_system = ColorNode("API系统", colors['drinking'])
        
        # 数据层节点 - 对应参考图中的红色节点
        with Cluster("", graph_attr={"style": "invis"}):
            file_system = ColorNode("文件系统", colors['medication'])
            database = ColorNode("数据库", colors['medication'])
            cache = ColorNode("缓存", colors['medication'])
            serialization = ColorNode("序列化", colors['medication'])
        
        # 其他节点
        others = ColorNode("其他模块", colors['others'])
        
        # ===== 创建连接 =====
        # 从核心节点连接到主要分类
        core_engine >> scene_system
        core_engine >> render_system
        core_engine >> resource_system
        core_engine >> config_system
        core_engine >> others
        
        # 业务层连接到表现层
        scene_system >> scene_editor
        render_system >> visual_system
        config_system >> ui_system
        core_engine >> interaction_system
        
        # 业务层连接到数据层
        scene_system >> database
        render_system >> cache
        resource_system >> file_system
        config_system >> serialization
        
        # 核心连接到工具层
        core_engine >> plugin_system
        core_engine >> log_system
        interaction_system >> event_system
        config_system >> api_system
        
        # 添加表现层内部连接（用虚线）
        ui_system >> Edge(style="dashed") >> interaction_system
        interaction_system >> Edge(style="dashed") >> scene_editor
        scene_editor >> Edge(style="dashed") >> visual_system
        visual_system >> Edge(style="dashed") >> ui_system

if __name__ == '__main__':
    generate_diagram() 