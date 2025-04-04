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
                            2024/04/04: 更新为黑色背景，简化连接线，采用鲜明色彩区分;
                            2024/04/04: 调整为扁平星形布局，直接从核心连接所有节点;
                            2024/04/04: 完全重新设计为水平链式结构，所有节点排成一行;
----
"""

import graphviz

def create_system_architecture():
    """
    创建系统总体架构图，水平链式布局，所有节点在一行
    
    Returns:
        graphviz.Digraph: 生成的图表对象
    """
    # 创建有向图
    dot = graphviz.Digraph('系统总体架构', 
                          comment='Hollow-ming系统架构 - 水平链式布局',
                          format='png')
    
    # 设置图表属性
    dot.attr(rankdir='LR',  # 从左到右布局
             size='20,5',   # 宽矮的比例
             ratio='fill', 
             fontname='Microsoft YaHei',
             dpi='500',
             splines='curved',
             overlap='false',
             ranksep='0.2',
             nodesep='0.8',
             ordering='out')
    
    # 定义节点样式
    dot.attr('node', 
             shape='circle', 
             style='filled', 
             fontname='Microsoft YaHei', 
             fontsize='12',
             fontcolor='white',
             fixedsize='true',
             width='1.3',
             height='1.3')
    
    # 定义边样式
    dot.attr('edge', 
             color='#555555', 
             penwidth='0.8',
             arrowhead='vee',
             arrowsize='0.6')
    
    # 明亮色彩方案 - 黑色背景
    colors = {
        'bg': '#121212',            # 黑色背景
        'core': '#9c27b0',          # 紫色 - 核心
        'business': '#ff5722',      # 橙色 - 业务层
        'presentation': '#8bc34a',  # 绿色 - 表现层
        'data': '#f44336',          # 红色 - 数据层
        'tools': '#03a9f4',         # 蓝色 - 工具层
        'others': '#9e9e9e'         # 灰色 - 其他
    }
    
    # 设置图表背景
    dot.attr(bgcolor=colors['bg'])
    
    # 定义所有节点及其顺序
    nodes = [
        ('core_engine', '核心引擎', colors['core']),
        ('scene_manager', '场景管理器', colors['business']),
        ('database', '数据库', colors['data']),
        ('resource_system', '资源系统', colors['business']),
        ('visual_effects', '视觉效果', colors['presentation']),
        ('render_system', '渲染系统', colors['business']),
        ('cache', '缓存', colors['data']),
        ('ui', 'UI组件', colors['presentation']),
        ('file_system', '文件系统', colors['data']),
        ('serialization', '序列化', colors['data']),
        ('api_interface', 'API接口', colors['tools']),
        ('event_system', '事件系统', colors['tools']),
        ('config_system', '配置系统', colors['business']),
        ('plugin_system', '插件系统', colors['tools']),
        ('logging', '日志系统', colors['tools']),
        ('others', '其他模块', colors['others'])
    ]
    
    # 创建所有节点
    for node_id, label, color in nodes:
        # 核心引擎稍微大一些
        size = '1.6' if node_id == 'core_engine' else '1.3'
        dot.node(node_id, label, 
                fillcolor=color, 
                width=size, 
                height=size)
    
    # 创建隐形的边来保证节点的顺序
    for i in range(len(nodes) - 1):
        dot.edge(nodes[i][0], nodes[i+1][0], style='invis')
    
    # 创建连接线 - 上部弧线
    connections = [
        # 从核心引擎出发的连接
        ('core_engine', 'scene_manager'),
        ('core_engine', 'resource_system'),
        ('core_engine', 'render_system'),
        ('core_engine', 'ui'),
        ('core_engine', 'config_system'),
        ('core_engine', 'plugin_system'),
        ('core_engine', 'logging'),
        
        # 其他核心连接
        ('scene_manager', 'database'),
        ('resource_system', 'file_system'),
        ('render_system', 'cache'),
        ('config_system', 'serialization'),
        ('ui', 'event_system'),
        ('api_interface', 'config_system')
    ]
    
    # 添加连接
    for src, dst in connections:
        dot.edge(src, dst, constraint='false')
    
    # 添加图表说明
    dot.attr(label='Hollow-ming系统架构图 | 2024-04-04', fontsize='14', fontcolor='white')
    
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