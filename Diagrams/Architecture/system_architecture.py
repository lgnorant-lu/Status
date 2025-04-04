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
----
"""

import graphviz

def create_system_architecture():
    """
    创建系统总体架构图，以核心引擎为中心的辐射状结构，黑色背景
    
    Returns:
        graphviz.Digraph: 生成的图表对象
    """
    # 创建有向图
    dot = graphviz.Digraph('系统总体架构', 
                          comment='Hollow-ming系统架构 - 黑色背景简洁风格',
                          format='png')
    
    # 设置图表属性
    dot.attr(rankdir='TB', 
             size='16,16', 
             ratio='fill', 
             fontname='Microsoft YaHei',
             dpi='400',
             splines='true',
             overlap='false', 
             ranksep='2.5',
             nodesep='1.0')
    
    # 定义节点样式
    dot.attr('node', 
             shape='circle', 
             style='filled', 
             fontname='Microsoft YaHei', 
             fontsize='14',
             fontcolor='white')
    
    # 定义边样式
    dot.attr('edge', 
             color='#777777', 
             penwidth='1.0',
             dir='forward',
             arrowhead='normal',
             arrowsize='0.7')
    
    # 明亮色彩方案 - 黑色背景
    colors = {
        'bg': '#121212',            # 黑色背景
        'core': '#9c27b0',          # 紫色 - 核心
        'main_meals': '#ff5722',    # 橙色 - 主餐
        'snacks': '#8bc34a',        # 绿色 - 零食
        'drinking': '#03a9f4',      # 蓝色 - 饮品
        'medication': '#f44336',    # 红色 - 药物
        'others': '#9e9e9e',        # 灰色 - 其他
        'edge': '#555555'           # 暗灰 - 连接线
    }
    
    # 设置图表背景
    dot.attr(bgcolor=colors['bg'])
    
    # ===== 核心节点 =====
    dot.node('core_engine', '核心引擎', 
             fillcolor=colors['core'], 
             fixedsize='true', 
             width='1.8', 
             height='1.8',
             fontsize='16')
    
    # ===== 业务逻辑层节点 =====
    business_nodes = [
        ('scene_manager', '场景管理器', colors['main_meals']),
        ('render_system', '渲染系统', colors['main_meals']),
        ('resource_system', '资源系统', colors['main_meals']),
        ('config_system', '配置系统', colors['main_meals'])
    ]
    
    for id, label, color in business_nodes:
        dot.node(id, label,
                fillcolor=color,
                fixedsize='true',
                width='1.5',
                height='1.5')
        dot.edge('core_engine', id)
    
    # ===== 表现层节点 =====
    presentation_nodes = [
        ('ui', 'UI组件', 'config_system', colors['snacks']),
        ('interaction', '交互系统', 'core_engine', colors['snacks']),
        ('scene_editor', '场景编辑器', 'scene_manager', colors['snacks']),
        ('visual_effects', '视觉效果', 'render_system', colors['snacks'])
    ]
    
    for id, label, connect_to, color in presentation_nodes:
        dot.node(id, label,
                fillcolor=color,
                fixedsize='true',
                width='1.3',
                height='1.3')
        dot.edge(connect_to, id)
    
    # ===== 数据层节点 =====
    data_nodes = [
        ('file_system', '文件系统', 'resource_system', colors['medication']),
        ('database', '数据库', 'scene_manager', colors['medication']),
        ('cache', '缓存', 'render_system', colors['medication']),
        ('serialization', '序列化', 'config_system', colors['medication'])
    ]
    
    for id, label, connect_to, color in data_nodes:
        dot.node(id, label,
                fillcolor=color,
                fixedsize='true',
                width='1.3',
                height='1.3')
        dot.edge(connect_to, id)
    
    # ===== 工具/接口节点 =====
    tools_nodes = [
        ('plugin_system', '插件系统', 'core_engine', colors['drinking']),
        ('event_system', '事件系统', 'interaction', colors['drinking']),
        ('logging', '日志系统', 'core_engine', colors['drinking']),
        ('api_interface', 'API接口', 'config_system', colors['drinking'])
    ]
    
    for id, label, connect_to, color in tools_nodes:
        dot.node(id, label,
                fillcolor=color,
                fixedsize='true',
                width='1.3',
                height='1.3')
        dot.edge(connect_to, id)
    
    # ===== 其他节点 =====
    dot.node('others', '其他模块', 
             fillcolor=colors['others'],
             fixedsize='true',
             width='1.3',
             height='1.3')
    dot.edge('core_engine', 'others')
    
    # 添加图表说明
    dot.attr(label='Hollow-ming系统架构图 | 2024-04-04', fontsize='16', fontcolor='white')
    
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