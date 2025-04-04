"""
---------------------------------------------------------------
File name:                  system_architecture.py
Author:                     Ignorant-lu
Date created:               2024/04/04
Description:                系统总体架构图生成脚本
----------------------------------------------------------------

Changed history:            
                            2024/04/04: 初始创建;
                            2024/04/04: 更新风格为圆角和圆形，使用卡其色调和绿色系;
                            2024/04/04: 更新为中心辐射型结构，核心引擎为中心;
----
"""

import graphviz

def create_system_architecture():
    """
    创建系统总体架构图，以核心引擎为中心的辐射状结构
    
    Returns:
        graphviz.Digraph: 生成的图表对象
    """
    # 创建有向图
    dot = graphviz.Digraph('系统总体架构', 
                          comment='Hollow-ming系统架构 - 中心辐射型结构',
                          format='png')
    
    # 设置图表属性 - 提高DPI以增加清晰度
    dot.attr(rankdir='TB', 
             size='12,12', 
             ratio='fill', 
             fontname='Microsoft YaHei',
             dpi='300',
             splines='true',  # 使用样条曲线连接
             overlap='false',  # 避免节点重叠
             sep='+25')  # 增加间隔
    
    # 定义节点样式 - 改为圆角和圆形
    dot.attr('node', shape='circle', style='filled', fontname='Microsoft YaHei', fontsize='14')
    
    # 定义边样式 - 使用曲线
    dot.attr('edge', style='curved', penwidth='1.3')
    
    # 卡其色和绿色系配色方案
    colors = {
        'presentation': '#d5c59f',  # 暖卡其色
        'business': '#8fbfa4',      # 薄荷绿
        'data': '#c2d5a7',          # 浅黄绿
        'border': '#5e7c5e',        # 深绿边框
        'core': '#4a7c59',          # 核心深绿
        'edge': '#6b7a59',          # 橄榄绿连接线
        'pres_edge': '#b3a278',     # 表现层连接线
        'business_edge': '#78a38d', # 业务层连接线
        'data_edge': '#a3b78c',     # 数据层连接线
        'bg': '#f7f3e9'             # 米色背景
    }
    
    # 设置图表背景
    dot.attr(bgcolor=colors['bg'])
    
    # 创建中心节点 - 核心引擎
    dot.node('core_engine', '核心引擎', 
             shape='circle', 
             fixedsize='true', 
             width='2.0', 
             height='2.0',
             fillcolor=colors['core'], 
             fontcolor='white', 
             color=colors['border'], 
             penwidth='2.0', 
             fontsize='16')
    
    # ===== 业务逻辑层节点 =====
    # 业务逻辑层节点 - 与核心引擎直接相连
    business_nodes = [
        ('scene_manager', '场景管理器'),
        ('render_system', '渲染系统'),
        ('resource_system', '资源系统'),
        ('config_system', '配置系统')
    ]
    
    for i, (id, label) in enumerate(business_nodes):
        dot.node(id, label, 
                shape='circle', 
                fillcolor=colors['business'], 
                color=colors['border'], 
                penwidth='1.5',
                fontsize='14',
                fixedsize='true',
                width='1.7',
                height='1.7')
        # 从核心连接到业务节点
        dot.edge('core_engine', id, color=colors['business_edge'], constraint='false')
    
    # ===== 表现层节点 =====
    presentation_nodes = [
        ('ui', 'UI组件', 'config_system'),
        ('interaction', '交互系统', 'core_engine'),
        ('scene_editor', '场景编辑器', 'scene_manager'),
        ('visual_effects', '视觉效果', 'render_system')
    ]
    
    for i, (id, label, connect_to) in enumerate(presentation_nodes):
        dot.node(id, label, 
                shape='circle', 
                fillcolor=colors['presentation'], 
                color=colors['border'], 
                penwidth='1.5',
                fontsize='14',
                fixedsize='true',
                width='1.5',
                height='1.5')
        # 从业务节点连接到表现层节点
        dot.edge(id, connect_to, color=colors['pres_edge'], constraint='false')
    
    # 表现层节点之间的连接
    dot.edge('ui', 'interaction', color=colors['pres_edge'], constraint='false')
    dot.edge('interaction', 'scene_editor', color=colors['pres_edge'], constraint='false')
    dot.edge('scene_editor', 'visual_effects', color=colors['pres_edge'], constraint='false')
    dot.edge('visual_effects', 'ui', color=colors['pres_edge'], constraint='false')
    
    # ===== 数据层节点 =====
    data_nodes = [
        ('file_system', '文件系统', 'resource_system'),
        ('database', '数据库', 'scene_manager'),
        ('cache', '缓存', 'render_system'),
        ('serialization', '序列化', 'config_system')
    ]
    
    for i, (id, label, connect_to) in enumerate(data_nodes):
        dot.node(id, label, 
                shape='circle', 
                fillcolor=colors['data'], 
                color=colors['border'], 
                penwidth='1.5',
                fontsize='14',
                fixedsize='true',
                width='1.5',
                height='1.5')
        # 从业务节点连接到数据层节点
        dot.edge(connect_to, id, color=colors['data_edge'], constraint='false')
    
    # 数据层节点之间的连接
    dot.edge('file_system', 'database', color=colors['data_edge'], constraint='false', style='dashed')
    dot.edge('database', 'cache', color=colors['data_edge'], constraint='false', style='dashed')
    dot.edge('cache', 'serialization', color=colors['data_edge'], constraint='false', style='dashed')
    dot.edge('serialization', 'file_system', color=colors['data_edge'], constraint='false', style='dashed')
    
    # 添加图表说明及图例
    dot.attr(label='Hollow-ming系统总体架构图 - 中心辐射型 | 创建日期: 2024-04-04', fontsize='16', fontcolor='#333333')
    
    # 创建图例子图
    with dot.subgraph(name='cluster_legend') as legend:
        legend.attr(label='图例', style='filled', fillcolor='white', color=colors['border'], fontcolor='#333333')
        legend.node('l_core', '核心组件', shape='circle', style='filled', fillcolor=colors['core'], fontcolor='white')
        legend.node('l_business', '业务层组件', shape='circle', style='filled', fillcolor=colors['business'])
        legend.node('l_presentation', '表现层组件', shape='circle', style='filled', fillcolor=colors['presentation'])
        legend.node('l_data', '数据层组件', shape='circle', style='filled', fillcolor=colors['data'])
        
        # 隐藏图例中的连接线，但保持排列
        legend.edge('l_core', 'l_business', style='invis')
        legend.edge('l_business', 'l_presentation', style='invis')
        legend.edge('l_presentation', 'l_data', style='invis')
    
    return dot

def generate_diagram():
    """
    生成架构图并保存到文件
    """
    dot = create_system_architecture()
    
    # 渲染并保存图表，cleanup=True表示删除中间文件
    dot.render('system_architecture', directory='Diagrams/Architecture', cleanup=True)
    print("系统架构图已生成: Diagrams/Architecture/system_architecture.png")

if __name__ == '__main__':
    generate_diagram() 