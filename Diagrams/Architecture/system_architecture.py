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
                            2024/04/04: 优化模块显示，添加图标，采用浅蓝色分层背景;
                            2024/04/04: 修复图标初始化错误;
                            2024/04/04: 为每个节点添加专有图标，提高节点区分度;
----
"""

from diagrams import Diagram, Cluster, Edge, Node
from diagrams.onprem.compute import Server
from diagrams.onprem.database import PostgreSQL, MySQL, Cassandra
from diagrams.onprem.network import Nginx
from diagrams.onprem.client import Users
from diagrams.onprem.workflow import Airflow
from diagrams.onprem.queue import Kafka
from diagrams.onprem.analytics import Spark
from diagrams.onprem.monitoring import Grafana
from diagrams.programming.framework import React, Flutter, Spring
from diagrams.programming.language import Python, Go, Java
from diagrams.aws.storage import SimpleStorageServiceS3 as S3
from diagrams.aws.compute import Lambda
from diagrams.generic.storage import Storage
from diagrams.generic.compute import Rack
from diagrams.generic.database import SQL
from diagrams.generic.os import Windows, IOS
from diagrams.generic.network import Firewall, VPN, Router
from diagrams.generic.place import Datacenter

# 创建带图标的节点类
class IconNode(Node):
    """带图标的节点"""
    
    def __init__(self, label, icon, color):
        """
        初始化节点
        
        Args:
            label: 节点标签
            icon: 图标类
            color: 填充颜色
        """
        # 使用图标类创建节点
        self.node = icon(label)
        
        # 设置节点样式属性
        self.node._attrs["style"] = "filled,rounded"
        self.node._attrs["fillcolor"] = color
        self.node._attrs["fontcolor"] = "#FFFFFF"
        self.node._attrs["fontsize"] = "13"
        self.node._attrs["fontname"] = "Microsoft YaHei"
        self.node._attrs["margin"] = "0.2"
        self.node._attrs["penwidth"] = "1.5"
        self.node._attrs["color"] = self._adjust_color(color, -40)
    
    def _adjust_color(self, hex_color, amount):
        """
        调整颜色亮度
        
        Args:
            hex_color: 十六进制颜色值
            amount: 调整量，正值变亮，负值变暗
        
        Returns:
            str: 调整后的十六进制颜色值
        """
        h = hex_color.lstrip('#')
        rgb = tuple(int(h[i:i+2], 16) for i in (0, 2, 4))
        rgb = tuple(max(0, min(255, c + amount)) for c in rgb)
        return '#{:02x}{:02x}{:02x}'.format(*rgb)

def generate_diagram():
    """生成系统架构图"""
    
    # 颜色方案
    colors = {
        'core': '#7e57c2',          # 紫色 - 核心层
        'business': '#ff7043',      # 橙色 - 业务层
        'presentation': '#42a5f5',  # 蓝色 - 表现层
        'tool': '#26a69a',          # 青色 - 工具层
        'data': '#ef5350',          # 红色 - 数据层
        'module': '#78909c',        # 灰色 - 其他模块
        'datacenter': '#333333',    # 深灰色 - 数据中心
        'cluster_bg': '#e3f2fd',    # 浅蓝色 - 分组背景
    }
    
    # 开始创建架构图
    with Diagram(
        "Hollow-ming系统架构图",
        filename="system_architecture",
        outformat="png",
        show=False,
        direction="TB",
        graph_attr={
            "bgcolor": "#f5f5f5",       # 浅灰色背景
            "fontcolor": "#333333",
            "fontname": "Microsoft YaHei",
            "fontsize": "20",
            "ranksep": "1.2",
            "nodesep": "0.9",
            "pad": "0.7",
            "splines": "polyline",      # 使用折线连接
            "concentrate": "true",
        },
        node_attr={
            "fontname": "Microsoft YaHei",
        },
        edge_attr={
            "color": "#90a4ae",
            "penwidth": "1.2",
            "arrowsize": "0.7",
        }
    ):
        # 创建核心节点
        core_engine = Lambda("核心引擎")
        core_engine._attrs["style"] = "filled,rounded"
        core_engine._attrs["fillcolor"] = colors['core']
        core_engine._attrs["fontcolor"] = "#FFFFFF"
        
        # 创建数据中心节点
        datacenter = Datacenter("数据中心")
        datacenter._attrs["fillcolor"] = colors['datacenter']
        datacenter._attrs["fontcolor"] = "#FFFFFF" 
        datacenter._attrs["style"] = "filled"

        # ==== 业务层 ====
        with Cluster("业务层", graph_attr={
            "bgcolor": colors['cluster_bg'],
            "style": "filled,rounded",
            "color": colors['business'],
            "fontcolor": colors['business'],
            "fontsize": "16",
            "margin": "30",
            "penwidth": "2.0",
            "label_loc": "t", # 顶部放置标签
        }):
            config_system = Windows("配置系统")
            config_system._attrs["style"] = "filled,rounded"
            config_system._attrs["fillcolor"] = colors['business']
            config_system._attrs["fontcolor"] = "#FFFFFF"
            
            render_system = Spring("渲染系统")
            render_system._attrs["style"] = "filled,rounded"
            render_system._attrs["fillcolor"] = colors['business']
            render_system._attrs["fontcolor"] = "#FFFFFF"
            
            resource_system = S3("资源系统")
            resource_system._attrs["style"] = "filled,rounded"
            resource_system._attrs["fillcolor"] = colors['business']
            resource_system._attrs["fontcolor"] = "#FFFFFF"
            
            scene_system = Airflow("场景系统")
            scene_system._attrs["style"] = "filled,rounded"
            scene_system._attrs["fillcolor"] = colors['business']
            scene_system._attrs["fontcolor"] = "#FFFFFF"
        
        # ==== 表现层 ====
        with Cluster("表现层", graph_attr={
            "bgcolor": colors['cluster_bg'],
            "style": "filled,rounded",
            "color": colors['presentation'],
            "fontcolor": colors['presentation'],
            "fontsize": "16",
            "margin": "30",
            "penwidth": "2.0",
            "label_loc": "t",
        }):
            ui_system = React("UI系统")
            ui_system._attrs["style"] = "filled,rounded"
            ui_system._attrs["fillcolor"] = colors['presentation']
            ui_system._attrs["fontcolor"] = "#FFFFFF"
            
            interaction_system = Flutter("交互系统")
            interaction_system._attrs["style"] = "filled,rounded"
            interaction_system._attrs["fillcolor"] = colors['presentation']
            interaction_system._attrs["fontcolor"] = "#FFFFFF"
            
            scene_editor = Nginx("场景编辑器")
            scene_editor._attrs["style"] = "filled,rounded"
            scene_editor._attrs["fillcolor"] = colors['presentation']
            scene_editor._attrs["fontcolor"] = "#FFFFFF"
            
            visual_system = Grafana("视觉系统")
            visual_system._attrs["style"] = "filled,rounded"
            visual_system._attrs["fillcolor"] = colors['presentation']
            visual_system._attrs["fontcolor"] = "#FFFFFF"
        
        # ==== 数据层 ====
        with Cluster("数据层", graph_attr={
            "bgcolor": colors['cluster_bg'],
            "style": "filled,rounded",
            "color": colors['data'],
            "fontcolor": colors['data'],
            "fontsize": "16",
            "margin": "30",
            "penwidth": "2.0",
            "label_loc": "t",
        }):
            file_system = Storage("文件系统")
            file_system._attrs["style"] = "filled,rounded"
            file_system._attrs["fillcolor"] = colors['data']
            file_system._attrs["fontcolor"] = "#FFFFFF"
            
            database = MySQL("数据库")
            database._attrs["style"] = "filled,rounded"
            database._attrs["fillcolor"] = colors['data']
            database._attrs["fontcolor"] = "#FFFFFF"
            
            cache = Cassandra("缓存")
            cache._attrs["style"] = "filled,rounded"
            cache._attrs["fillcolor"] = colors['data']
            cache._attrs["fontcolor"] = "#FFFFFF"
            
            serialization = PostgreSQL("序列化")
            serialization._attrs["style"] = "filled,rounded"
            serialization._attrs["fillcolor"] = colors['data']
            serialization._attrs["fontcolor"] = "#FFFFFF"
        
        # ==== 工具层 ====
        with Cluster("工具层", graph_attr={
            "bgcolor": colors['cluster_bg'],
            "style": "filled,rounded",
            "color": colors['tool'],
            "fontcolor": colors['tool'],
            "fontsize": "16",
            "margin": "30",
            "penwidth": "2.0",
            "label_loc": "t",
        }):
            plugin_system = Python("插件系统")
            plugin_system._attrs["style"] = "filled,rounded"
            plugin_system._attrs["fillcolor"] = colors['tool']
            plugin_system._attrs["fontcolor"] = "#FFFFFF"
            
            event_system = Kafka("事件系统")
            event_system._attrs["style"] = "filled,rounded"
            event_system._attrs["fillcolor"] = colors['tool']
            event_system._attrs["fontcolor"] = "#FFFFFF"
            
            log_system = Spark("日志系统")
            log_system._attrs["style"] = "filled,rounded"
            log_system._attrs["fillcolor"] = colors['tool']
            log_system._attrs["fontcolor"] = "#FFFFFF"
            
            api_system = Firewall("API系统")
            api_system._attrs["style"] = "filled,rounded"
            api_system._attrs["fillcolor"] = colors['tool']
            api_system._attrs["fontcolor"] = "#FFFFFF"
        
        # 其他模块
        with Cluster("", graph_attr={"style": "invis"}):
            others = Rack("其他模块")
            others._attrs["style"] = "filled,rounded"
            others._attrs["fillcolor"] = colors['module']
            others._attrs["fontcolor"] = "#FFFFFF"
        
        # ===== 创建连接 =====
        # 核心引擎和数据中心
        core_engine - datacenter
        
        # 核心引擎连接到各层
        core_engine >> scene_system
        core_engine >> render_system
        core_engine >> resource_system
        core_engine >> config_system
        core_engine >> others
        
        # 业务层连接到表现层
        scene_system >> scene_editor
        render_system >> visual_system
        config_system >> ui_system
        
        # 核心连接交互系统
        core_engine >> interaction_system
        
        # 业务层连接到数据层
        scene_system >> database
        render_system >> cache
        resource_system >> file_system
        config_system >> serialization
        
        # 核心连接到工具层
        core_engine >> plugin_system
        core_engine >> log_system
        
        # 交互系统连接事件系统
        interaction_system >> event_system
        
        # 配置系统连接API系统
        config_system >> api_system
        
        # 添加表现层内部连接（用虚线）
        ui_system >> Edge(style="dashed") >> interaction_system
        interaction_system >> Edge(style="dashed") >> scene_editor
        scene_editor >> Edge(style="dashed") >> visual_system
        visual_system >> Edge(style="dashed") >> ui_system
        
        # 数据中心与数据层连接
        datacenter >> database
        datacenter >> cache
        datacenter >> file_system

if __name__ == '__main__':
    generate_diagram() 