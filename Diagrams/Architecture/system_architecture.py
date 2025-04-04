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
                            2024/04/04: 更新为方形节点带图标，使用更舒适的淡绿色背景;
                            2024/04/04: 修复导入错误，使用本地可用的图标;
                            2024/04/04: 修复节点初始化参数错误;
----
"""

from diagrams import Diagram, Cluster, Edge, Node
from diagrams.onprem.compute import Server
from diagrams.onprem.database import PostgreSQL, MySQL
from diagrams.onprem.network import Nginx
from diagrams.onprem.client import Users
from diagrams.onprem.workflow import Airflow
from diagrams.programming.framework import React
from diagrams.programming.language import Python
from diagrams.generic.storage import Storage
from diagrams.generic.compute import Rack
from diagrams.generic.database import SQL
from diagrams.generic.os import Windows
from diagrams.generic.network import Firewall
from diagrams.generic.place import Datacenter

# 创建自定义节点类 - 方形节点带颜色
class ColorNode(Node):
    def __init__(self, label, color):
        super().__init__(label)
        self._attrs["fillcolor"] = color
        self._attrs["style"] = "filled"
        self._attrs["fontcolor"] = "#FFFFFF"
        self._attrs["shape"] = "rect"
        self._attrs["fontsize"] = "14"
        self._attrs["width"] = "1.8"
        self._attrs["height"] = "1.5"
        self._attrs["margin"] = "0.3"
        self._attrs["penwidth"] = "2.0"
        self._attrs["color"] = self._darken_color(color, 20)  # 边框颜色略深

    def _darken_color(self, hex_color, percent):
        """将颜色加深指定百分比"""
        h = hex_color.lstrip('#')
        rgb = tuple(int(h[i:i+2], 16) for i in (0, 2, 4))
        rgb = tuple(max(0, int(c * (100 - percent) / 100)) for c in rgb)
        return '#{:02x}{:02x}{:02x}'.format(*rgb)

def generate_diagram():
    """
    生成系统架构图 - 使用分层结构
    """
    # 颜色方案 - 更柔和的色彩
    colors = {
        'core': '#6200ea',          # 深紫色 - 核心
        'main_meals': '#e65100',    # 深橙色 - 业务层
        'snacks': '#2e7d32',        # 深绿色 - 表现层
        'drinking': '#0277bd',      # 深蓝色 - 工具层
        'medication': '#c62828',    # 深红色 - 数据层
        'others': '#455a64',        # 深灰蓝色 - 其他
    }
    
    # 开始创建架构图
    with Diagram(
        "Hollow-ming系统架构图",
        filename="system_architecture",
        outformat="png",
        show=False,
        direction="TB",  # 自上而下的布局
        graph_attr={
            "bgcolor": "#e8f5e9",   # 更柔和的淡绿色背景
            "fontcolor": "#263238",
            "fontname": "Microsoft YaHei",
            "fontsize": "22",
            "overlap": "false",
            "splines": "ortho",      # 正交连线
            "nodesep": "0.8",
            "ranksep": "1.0",
            "pad": "0.5", 
            "concentrate": "true",   # 合并边
        },
        node_attr={
            "fontname": "Microsoft YaHei",
        },
        edge_attr={
            "color": "#78909c",      # 更柔和的连线颜色
            "penwidth": "1.5",
            "arrowsize": "0.8",
        }
    ):
        # 创建核心节点与各种系统节点
        core_engine = ColorNode("核心引擎", colors['core'])
        
        # 使用不同的图标类型作为节点
        datacenter = Datacenter("数据中心")
        
        # 创建分层结构
        with Cluster("业务层", graph_attr={"fontcolor": colors['main_meals'], "style": "dotted", "color": colors['main_meals'], "fontsize": "16"}):
            scene_system = ColorNode("场景系统", colors['main_meals'])
            render_system = ColorNode("渲染系统", colors['main_meals'])
            resource_system = ColorNode("资源系统", colors['main_meals'])
            config_system = ColorNode("配置系统", colors['main_meals'])
        
        with Cluster("表现层", graph_attr={"fontcolor": colors['snacks'], "style": "dotted", "color": colors['snacks'], "fontsize": "16"}):
            ui_system = ColorNode("UI系统", colors['snacks'])
            interaction_system = ColorNode("交互系统", colors['snacks'])
            scene_editor = ColorNode("场景编辑器", colors['snacks'])
            visual_system = ColorNode("视觉系统", colors['snacks'])
        
        with Cluster("工具层", graph_attr={"fontcolor": colors['drinking'], "style": "dotted", "color": colors['drinking'], "fontsize": "16"}):
            plugin_system = ColorNode("插件系统", colors['drinking'])
            event_system = ColorNode("事件系统", colors['drinking'])
            log_system = ColorNode("日志系统", colors['drinking'])
            api_system = ColorNode("API系统", colors['drinking'])
        
        with Cluster("数据层", graph_attr={"fontcolor": colors['medication'], "style": "dotted", "color": colors['medication'], "fontsize": "16"}):
            file_system = ColorNode("文件系统", colors['medication'])
            database = ColorNode("数据库", colors['medication'])
            cache = ColorNode("缓存", colors['medication'])
            serialization = ColorNode("序列化", colors['medication'])
        
        # 其他节点
        others = ColorNode("其他模块", colors['others'])
        
        # ===== 创建连接 =====
        # 从核心节点连接到各层
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