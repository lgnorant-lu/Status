"""
---------------------------------------------------------------
File name:                  system_architecture.py
Author:                     Ignorant-lu
Date created:               2024/04/04
Description:                系统总体架构图生成脚本
----------------------------------------------------------------

Changed history:            
                            2024/04/04: 初始创建;
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
    
    # 设置图表属性
    dot.attr(rankdir='TB', 
             size='12,10', 
             ratio='fill', 
             fontname='Microsoft YaHei',
             nodesep='0.5', 
             ranksep='1.2')
    
    # 定义节点样式
    dot.attr('node', shape='box', style='filled,rounded', fontname='Microsoft YaHei', fontsize='12')
    
    # 创建子图 - 表现层
    with dot.subgraph(name='cluster_presentation') as pres:
        pres.attr(label='表现层', style='filled', color='lightblue', fontsize='16')
        pres.node('ui', 'UI组件')
        pres.node('interaction', '交互系统')
        pres.node('scene_editor', '场景编辑器')
        pres.node('visual_effects', '视觉效果')
        
        # 表现层内部连接
        pres.edge('ui', 'interaction')
        pres.edge('interaction', 'scene_editor')
        pres.edge('scene_editor', 'visual_effects')
        pres.edge('visual_effects', 'ui', constraint='false')
    
    # 创建子图 - 业务逻辑层
    with dot.subgraph(name='cluster_business') as busi:
        busi.attr(label='业务逻辑层', style='filled', color='lightgreen', fontsize='16')
        busi.node('core_engine', '核心引擎')
        busi.node('scene_manager', '场景管理器')
        busi.node('render_system', '渲染系统')
        busi.node('resource_system', '资源系统')
        busi.node('config_system', '配置系统')
        
        # 业务逻辑层内部连接
        busi.edge('core_engine', 'scene_manager')
        busi.edge('core_engine', 'render_system')
        busi.edge('core_engine', 'resource_system')
        busi.edge('core_engine', 'config_system')
        busi.edge('scene_manager', 'render_system')
        busi.edge('resource_system', 'render_system')
        busi.edge('config_system', 'scene_manager')
    
    # 创建子图 - 数据层
    with dot.subgraph(name='cluster_data') as data:
        data.attr(label='数据层', style='filled', color='lightyellow', fontsize='16')
        data.node('file_system', '文件系统')
        data.node('database', '数据库')
        data.node('cache', '缓存')
        data.node('serialization', '序列化')
        
        # 数据层内部连接
        data.edge('file_system', 'database')
        data.edge('database', 'cache')
        data.edge('cache', 'serialization')
    
    # 创建跨层连接
    dot.edge('interaction', 'core_engine')
    dot.edge('scene_editor', 'scene_manager')
    dot.edge('ui', 'config_system')
    dot.edge('visual_effects', 'render_system')
    
    dot.edge('core_engine', 'file_system')
    dot.edge('resource_system', 'file_system')
    dot.edge('scene_manager', 'database')
    dot.edge('render_system', 'cache')
    dot.edge('config_system', 'serialization')
    
    # 添加模块划分说明
    dot.attr(label='Hollow-ming系统总体架构图 | 创建日期: 2024-04-04', fontsize='14')
    
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