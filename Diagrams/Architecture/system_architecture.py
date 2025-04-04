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
----
"""

from diagrams import Diagram, Cluster, Edge
from diagrams.custom import Custom
import os

# 创建图标目录（如果不存在）
ICONS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icons")
os.makedirs(ICONS_DIR, exist_ok=True)

# 定义节点图标路径
def create_icon_path(name, color):
    """创建彩色节点圆形图标"""
    from PIL import Image, ImageDraw
    
    # 图标文件路径
    icon_path = os.path.join(ICONS_DIR, f"{name}_{color.replace('#', '')}.png")
    
    # 如果图标已存在则直接返回
    if os.path.exists(icon_path):
        return icon_path
    
    # 创建圆形图标
    size = (200, 200)
    img = Image.new('RGBA', size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # 绘制填充圆
    draw.ellipse((10, 10, 190, 190), fill=color)
    
    # 保存图标
    img.save(icon_path)
    return icon_path

def generate_diagram():
    """
    生成系统架构图 - 使用Diagrams库
    """
    # 定义颜色方案
    colors = {
        'core': '#9c27b0',          # 紫色 - 核心
        'business': '#ff5722',      # 橙色 - 业务层
        'presentation': '#8bc34a',  # 绿色 - 表现层
        'data': '#f44336',          # 红色 - 数据层
        'tools': '#03a9f4',         # 蓝色 - 工具层
        'others': '#9e9e9e'         # 灰色 - 其他
    }
    
    # 创建自定义图标
    core_icon = create_icon_path("core", colors['core'])
    business_icon = create_icon_path("business", colors['business'])
    presentation_icon = create_icon_path("presentation", colors['presentation'])
    data_icon = create_icon_path("data", colors['data'])
    tools_icon = create_icon_path("tools", colors['tools'])
    others_icon = create_icon_path("others", colors['others'])
    
    # 开始创建架构图
    with Diagram(
        "Hollow-ming系统架构图",
        filename="system_architecture",
        outformat="png",
        show=False,
        direction="TB",
        graph_attr={
            "bgcolor": "#121212",
            "fontcolor": "white",
            "fontname": "Microsoft YaHei",
            "fontsize": "20",
            "overlap": "false",
            "splines": "true",
            "dpi": "300",
            "pad": "0.5",
        }
    ):
        # 创建核心节点
        core_engine = Custom("核心引擎", core_icon)
        
        # 创建业务层节点
        scene_manager = Custom("场景管理器", business_icon)
        render_system = Custom("渲染系统", business_icon)
        resource_system = Custom("资源系统", business_icon)
        config_system = Custom("配置系统", business_icon)
        
        # 创建表现层节点
        ui = Custom("UI组件", presentation_icon)
        interaction = Custom("交互系统", presentation_icon)
        scene_editor = Custom("场景编辑器", presentation_icon)
        visual_effects = Custom("视觉效果", presentation_icon)
        
        # 创建数据层节点
        file_system = Custom("文件系统", data_icon)
        database = Custom("数据库", data_icon)
        cache = Custom("缓存", data_icon)
        serialization = Custom("序列化", data_icon)
        
        # 创建工具层节点
        plugin_system = Custom("插件系统", tools_icon)
        event_system = Custom("事件系统", tools_icon)
        logging = Custom("日志系统", tools_icon)
        api_interface = Custom("API接口", tools_icon)
        
        # 创建其他节点
        others = Custom("其他模块", others_icon)
        
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