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
                            2024/04/04: 优化为环树状结构，中心向四周辐射展开;
----
"""

import graphviz

def create_system_architecture():
    """
    创建系统总体架构图，中心辐射式环树状布局，黑色背景
    
    Returns:
        graphviz.Digraph: 生成的图表对象
    """
    # 创建有向图
    dot = graphviz.Digraph('系统总体架构', 
                          comment='Hollow-ming系统架构 - 环树状辐射布局',
                          format='png')
    
    # 设置图表属性
    dot.attr(
        size='16,16', 
        ratio='fill', 
        fontname='Microsoft YaHei',
        dpi='500',
        rankdir='TB',
        concentrate='true',  # 合并边
        splines='true',      # 使用曲线
        overlap='false'      # 避免重叠
    )
    
    # 定义节点样式
    dot.attr('node', 
             shape='circle', 
             style='filled', 
             fontname='Microsoft YaHei', 
             fontsize='14',
             fontcolor='white')
    
    # 定义边样式 - 灰色箭头
    dot.attr('edge', 
             color='#777777', 
             penwidth='1.0',
             arrowhead='normal',
             arrowsize='0.7')
    
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
    
    # 创建不可见中心点，用于布局定位
    with dot.subgraph() as c:
        c.attr(rank='source')
        # ===== 核心节点 =====
        c.node('core_engine', '核心引擎', 
               fillcolor=colors['core'], 
               fixedsize='true', 
               width='1.8', 
               height='1.8',
               fontsize='16')
    
    # 创建第一层环 - 业务层
    with dot.subgraph() as c:
        c.attr(rank='same')
        business_nodes = [
            ('scene_manager', '场景管理器'),
            ('render_system', '渲染系统'),
            ('resource_system', '资源系统'),
            ('config_system', '配置系统')
        ]
        
        for i, (node_id, label) in enumerate(business_nodes):
            c.node(node_id, label,
                 fillcolor=colors['business'],
                 fixedsize='true',
                 width='1.5',
                 height='1.5')
        
        # 创建环形连接
        c.edge('scene_manager', 'render_system', style='invis')
        c.edge('render_system', 'resource_system', style='invis')
        c.edge('resource_system', 'config_system', style='invis')
        c.edge('config_system', 'scene_manager', style='invis')
    
    # 从核心到第一层的连接
    for node_id, _ in business_nodes:
        dot.edge('core_engine', node_id)
    
    # 创建第二层环 - 表现层和工具层
    with dot.subgraph() as c:
        c.attr(rank='same')
        outer_nodes = [
            # 表现层节点
            ('ui', 'UI组件', colors['presentation'], 'config_system'),
            ('interaction', '交互系统', colors['presentation'], 'core_engine'),
            ('scene_editor', '场景编辑器', colors['presentation'], 'scene_manager'),
            ('visual_effects', '视觉效果', colors['presentation'], 'render_system'),
            
            # 工具层节点
            ('plugin_system', '插件系统', colors['tools'], 'core_engine'),
            ('event_system', '事件系统', colors['tools'], 'interaction'),
            ('logging', '日志系统', colors['tools'], 'core_engine'),
            ('api_interface', 'API接口', colors['tools'], 'config_system')
        ]
        
        for i, (node_id, label, color, connect_to) in enumerate(outer_nodes):
            c.node(node_id, label,
                 fillcolor=color,
                 fixedsize='true',
                 width='1.3',
                 height='1.3')
        
        # 创建半环形布局助手（不可见连接）
        c.edge('ui', 'interaction', style='invis')
        c.edge('interaction', 'scene_editor', style='invis')
        c.edge('scene_editor', 'visual_effects', style='invis')
        c.edge('visual_effects', 'plugin_system', style='invis')
        c.edge('plugin_system', 'event_system', style='invis')
        c.edge('event_system', 'logging', style='invis')
        c.edge('logging', 'api_interface', style='invis')
        c.edge('api_interface', 'ui', style='invis')
    
    # 从第一层到第二层的连接
    for node_id, _, _, connect_to in outer_nodes:
        dot.edge(connect_to, node_id)
    
    # 创建第三层环 - 数据层和其他
    with dot.subgraph() as c:
        c.attr(rank='same')
        data_nodes = [
            ('file_system', '文件系统', 'resource_system'),
            ('database', '数据库', 'scene_manager'),
            ('cache', '缓存', 'render_system'),
            ('serialization', '序列化', 'config_system'),
            ('others', '其他模块', 'core_engine')
        ]
        
        for i, (node_id, label, connect_to) in enumerate(data_nodes):
            color = colors['others'] if node_id == 'others' else colors['data']
            c.node(node_id, label,
                 fillcolor=color,
                 fixedsize='true',
                 width='1.3',
                 height='1.3')
        
        # 创建环形布局助手（不可见连接）
        c.edge('file_system', 'database', style='invis')
        c.edge('database', 'cache', style='invis')
        c.edge('cache', 'serialization', style='invis')
        c.edge('serialization', 'others', style='invis')
        c.edge('others', 'file_system', style='invis')
    
    # 从业务层到数据层的连接
    for node_id, _, connect_to in data_nodes:
        dot.edge(connect_to, node_id)
    
    # 添加一些表现层节点间的次要连接
    additional_connections = [
        ('ui', 'interaction'),
        ('interaction', 'scene_editor'),
        ('scene_editor', 'visual_effects'),
        ('visual_effects', 'ui')
    ]
    
    # 添加次要连接为虚线
    for src, dst in additional_connections:
        dot.edge(src, dst, style='dashed', constraint='false')
    
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