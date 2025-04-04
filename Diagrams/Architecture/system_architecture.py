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
----
"""

import graphviz

def create_system_architecture():
    """
    创建系统总体架构图，扁平星形布局，黑色背景
    
    Returns:
        graphviz.Digraph: 生成的图表对象
    """
    # 创建有向图
    dot = graphviz.Digraph('系统总体架构', 
                          comment='Hollow-ming系统架构 - 扁平星形布局',
                          format='png')
    
    # 设置图表属性
    dot.attr(rankdir='TB', 
             size='16,16', 
             ratio='fill', 
             fontname='Microsoft YaHei',
             dpi='500',
             splines='true',
             overlap='false',
             sep='0.5',
             pack='true')
    
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
    
    # ===== 核心节点 =====
    dot.node('core_engine', '核心引擎', 
             fillcolor=colors['core'], 
             fixedsize='true', 
             width='1.8', 
             height='1.8',
             fontsize='16')
    
    # ===== 所有节点定义 =====
    nodes = {
        # 业务层节点
        'scene_manager': {'label': '场景管理器', 'color': colors['business'], 'size': 1.5},
        'render_system': {'label': '渲染系统', 'color': colors['business'], 'size': 1.5},
        'resource_system': {'label': '资源系统', 'color': colors['business'], 'size': 1.5},
        'config_system': {'label': '配置系统', 'color': colors['business'], 'size': 1.5},
        
        # 表现层节点
        'ui': {'label': 'UI组件', 'color': colors['presentation'], 'size': 1.3},
        'interaction': {'label': '交互系统', 'color': colors['presentation'], 'size': 1.3},
        'scene_editor': {'label': '场景编辑器', 'color': colors['presentation'], 'size': 1.3},
        'visual_effects': {'label': '视觉效果', 'color': colors['presentation'], 'size': 1.3},
        
        # 数据层节点
        'file_system': {'label': '文件系统', 'color': colors['data'], 'size': 1.3},
        'database': {'label': '数据库', 'color': colors['data'], 'size': 1.3},
        'cache': {'label': '缓存', 'color': colors['data'], 'size': 1.3},
        'serialization': {'label': '序列化', 'color': colors['data'], 'size': 1.3},
        
        # 工具/接口节点
        'plugin_system': {'label': '插件系统', 'color': colors['tools'], 'size': 1.3},
        'event_system': {'label': '事件系统', 'color': colors['tools'], 'size': 1.3},
        'logging': {'label': '日志系统', 'color': colors['tools'], 'size': 1.3},
        'api_interface': {'label': 'API接口', 'color': colors['tools'], 'size': 1.3},
        
        # 其他节点
        'others': {'label': '其他模块', 'color': colors['others'], 'size': 1.3}
    }
    
    # 创建所有节点
    for node_id, props in nodes.items():
        dot.node(node_id, props['label'],
                fillcolor=props['color'],
                fixedsize='true',
                width=str(props['size']),
                height=str(props['size']))
    
    # ===== 节点之间的次要连接 =====
    secondary_connections = [
        # 表现层连接到业务层
        ('ui', 'config_system'),
        ('interaction', 'core_engine'),
        ('scene_editor', 'scene_manager'),
        ('visual_effects', 'render_system'),
        
        # 业务层连接到数据层
        ('resource_system', 'file_system'),
        ('scene_manager', 'database'),
        ('render_system', 'cache'),
        ('config_system', 'serialization'),
        
        # 工具层连接
        ('event_system', 'interaction'),
        ('api_interface', 'config_system'),
        
        # 表现层节点间连接
        ('ui', 'interaction'),
        ('interaction', 'scene_editor'),
        ('scene_editor', 'visual_effects'),
        ('visual_effects', 'ui')
    ]
    
    # 创建所有核心连接 (从核心引擎到各主要节点)
    primary_nodes = [
        'scene_manager', 'render_system', 'resource_system', 'config_system',  # 业务层
        'interaction', 'plugin_system', 'logging', 'others'  # 直接连接核心的节点
    ]
    
    # 添加主要连接
    for node in primary_nodes:
        dot.edge('core_engine', node, constraint='false')
    
    # 添加次要连接
    for src, dst in secondary_connections:
        dot.edge(src, dst, constraint='false', style='dashed')
    
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