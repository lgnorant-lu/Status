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
----
"""

import graphviz

def create_system_architecture():
    """
    创建系统总体架构图，展示三层架构和主要模块
    
    Returns:
        graphviz.Digraph: 生成的图表对象
    """
    # 创建有向图
    dot = graphviz.Digraph('系统总体架构', 
                          comment='Hollow-ming系统三层架构和主要模块',
                          format='png')
    
    # 设置图表属性 - 提高DPI以增加清晰度
    dot.attr(rankdir='TB', 
             size='12,10', 
             ratio='fill', 
             fontname='Microsoft YaHei',
             nodesep='0.7', 
             ranksep='1.5',
             dpi='300')
    
    # 定义节点样式 - 改为圆角和圆形
    dot.attr('node', shape='ellipse', style='filled', fontname='Microsoft YaHei', fontsize='13')
    
    # 定义边样式 - 使用曲线
    dot.attr('edge', style='curved', penwidth='1.2')
    
    # 卡其色和绿色系配色方案
    colors = {
        'presentation': '#d5c59f',  # 暖卡其色
        'business': '#8fbfa4',      # 薄荷绿
        'data': '#c2d5a7',          # 浅黄绿
        'border': '#5e7c5e',        # 深绿边框
        'edge': '#6b7a59',          # 橄榄绿连接线
        'bg': '#f7f3e9'             # 米色背景
    }
    
    # 设置图表背景
    dot.attr(bgcolor=colors['bg'])
    
    # 创建子图 - 表现层
    with dot.subgraph(name='cluster_presentation') as pres:
        pres.attr(label='表现层', style='filled,rounded', color=colors['border'], fillcolor=colors['presentation'], 
                 fontsize='16', fontcolor='#333333', penwidth='2.0')
        pres.node('ui', 'UI组件', shape='circle', fillcolor='#e6d7b8', color=colors['border'], penwidth='1.5')
        pres.node('interaction', '交互系统', shape='circle', fillcolor='#e6d7b8', color=colors['border'], penwidth='1.5')
        pres.node('scene_editor', '场景编辑器', shape='circle', fillcolor='#e6d7b8', color=colors['border'], penwidth='1.5')
        pres.node('visual_effects', '视觉效果', shape='circle', fillcolor='#e6d7b8', color=colors['border'], penwidth='1.5')
        
        # 表现层内部连接
        pres.edge('ui', 'interaction', color=colors['edge'])
        pres.edge('interaction', 'scene_editor', color=colors['edge'])
        pres.edge('scene_editor', 'visual_effects', color=colors['edge'])
        pres.edge('visual_effects', 'ui', constraint='false', color=colors['edge'])
    
    # 创建子图 - 业务逻辑层
    with dot.subgraph(name='cluster_business') as busi:
        busi.attr(label='业务逻辑层', style='filled,rounded', color=colors['border'], fillcolor=colors['business'], 
                 fontsize='16', fontcolor='#333333', penwidth='2.0')
        busi.node('core_engine', '核心引擎', shape='circle', fillcolor='#add8c0', color=colors['border'], penwidth='1.5')
        busi.node('scene_manager', '场景管理器', shape='circle', fillcolor='#add8c0', color=colors['border'], penwidth='1.5')
        busi.node('render_system', '渲染系统', shape='circle', fillcolor='#add8c0', color=colors['border'], penwidth='1.5')
        busi.node('resource_system', '资源系统', shape='circle', fillcolor='#add8c0', color=colors['border'], penwidth='1.5')
        busi.node('config_system', '配置系统', shape='circle', fillcolor='#add8c0', color=colors['border'], penwidth='1.5')
        
        # 业务逻辑层内部连接
        busi.edge('core_engine', 'scene_manager', color=colors['edge'])
        busi.edge('core_engine', 'render_system', color=colors['edge'])
        busi.edge('core_engine', 'resource_system', color=colors['edge'])
        busi.edge('core_engine', 'config_system', color=colors['edge'])
        busi.edge('scene_manager', 'render_system', color=colors['edge'])
        busi.edge('resource_system', 'render_system', color=colors['edge'])
        busi.edge('config_system', 'scene_manager', color=colors['edge'])
    
    # 创建子图 - 数据层
    with dot.subgraph(name='cluster_data') as data:
        data.attr(label='数据层', style='filled,rounded', color=colors['border'], fillcolor=colors['data'], 
                 fontsize='16', fontcolor='#333333', penwidth='2.0')
        data.node('file_system', '文件系统', shape='circle', fillcolor='#dae8c3', color=colors['border'], penwidth='1.5')
        data.node('database', '数据库', shape='circle', fillcolor='#dae8c3', color=colors['border'], penwidth='1.5')
        data.node('cache', '缓存', shape='circle', fillcolor='#dae8c3', color=colors['border'], penwidth='1.5')
        data.node('serialization', '序列化', shape='circle', fillcolor='#dae8c3', color=colors['border'], penwidth='1.5')
        
        # 数据层内部连接
        data.edge('file_system', 'database', color=colors['edge'])
        data.edge('database', 'cache', color=colors['edge'])
        data.edge('cache', 'serialization', color=colors['edge'])
    
    # 创建跨层连接
    dot.edge('interaction', 'core_engine', color=colors['edge'])
    dot.edge('scene_editor', 'scene_manager', color=colors['edge'])
    dot.edge('ui', 'config_system', color=colors['edge'])
    dot.edge('visual_effects', 'render_system', color=colors['edge'])
    
    dot.edge('core_engine', 'file_system', color=colors['edge'])
    dot.edge('resource_system', 'file_system', color=colors['edge'])
    dot.edge('scene_manager', 'database', color=colors['edge'])
    dot.edge('render_system', 'cache', color=colors['edge'])
    dot.edge('config_system', 'serialization', color=colors['edge'])
    
    # 添加模块划分说明
    dot.attr(label='Hollow-ming系统总体架构图 | 创建日期: 2024-04-04', fontsize='14', fontcolor='#333333')
    
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