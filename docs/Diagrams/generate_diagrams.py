"""
---------------------------------------------------------------
File name:                  generate_diagrams.py
Author:                     Ignorant-lu
Date created:               2023/04/04
Description:                图表生成工具，用于生成项目架构和模块关系图表
----------------------------------------------------------------

Changed history:            
                            2023/04/04: 初始创建;
----
"""

import os
import sys
import graphviz
from pathlib import Path

def ensure_dir(directory):
    """确保目录存在，如不存在则创建

    Args:
        directory (str): 目录路径
    """
    Path(directory).mkdir(parents=True, exist_ok=True)

def generate_system_architecture():
    """生成系统架构图

    Returns:
        str: 生成的图表文件路径
    """
    dot = graphviz.Digraph('system_architecture', comment='系统架构图', 
                          format='png', engine='dot')
    
    # 设置图表属性
    dot.attr(rankdir='TB', size='8,5', ratio='fill', fontname='SimSun')
    dot.attr('node', shape='box', style='filled', color='lightblue', 
            fontname='SimSun', fontsize='12')
    dot.attr('edge', fontname='SimSun', fontsize='10')
    
    # 添加节点
    dot.node('config', '配置系统')
    dot.node('renderer', '渲染系统')
    dot.node('resource', '资源系统')
    dot.node('scene', '场景系统')
    dot.node('interaction', '交互系统')
    dot.node('plugin', '插件系统')
    
    # 添加边
    dot.edge('config', 'renderer', label='配置参数')
    dot.edge('config', 'resource', label='资源路径')
    dot.edge('resource', 'renderer', label='加载资源')
    dot.edge('scene', 'renderer', label='渲染场景')
    dot.edge('interaction', 'scene', label='场景交互')
    dot.edge('plugin', 'config', label='扩展配置')
    dot.edge('plugin', 'renderer', label='扩展渲染')
    dot.edge('plugin', 'resource', label='扩展资源')
    
    # 保存图表
    output_dir = 'docs/Diagrams/Architecture'
    ensure_dir(output_dir)
    return dot.render(os.path.join(output_dir, 'system_architecture'))

def generate_module_dependencies():
    """生成模块依赖关系图

    Returns:
        str: 生成的图表文件路径
    """
    dot = graphviz.Digraph('module_dependencies', comment='模块依赖关系图', 
                          format='png', engine='dot')
    
    # 设置图表属性
    dot.attr(rankdir='LR', size='8,5', ratio='fill', fontname='SimSun')
    dot.attr('node', shape='ellipse', style='filled', color='lightgreen', 
            fontname='SimSun', fontsize='12')
    dot.attr('edge', fontname='SimSun', fontsize='10')
    
    # 添加节点（核心模块）
    with dot.subgraph(name='cluster_core') as c:
        c.attr(label='核心模块', style='filled', color='lightgrey')
        c.node('core_config', '核心配置')
        c.node('core_renderer', '核心渲染器')
        c.node('core_resource', '核心资源管理')
        c.node('core_scene', '核心场景')
    
    # 添加节点（扩展模块）
    with dot.subgraph(name='cluster_extensions') as c:
        c.attr(label='扩展模块', style='filled', color='lightpink')
        c.node('ext_interaction', '交互扩展')
        c.node('ext_plugin', '插件系统')
        c.node('ext_effects', '特效系统')
    
    # 添加边
    dot.edge('core_config', 'core_renderer')
    dot.edge('core_config', 'core_resource')
    dot.edge('core_resource', 'core_renderer')
    dot.edge('core_scene', 'core_renderer')
    dot.edge('ext_interaction', 'core_scene')
    dot.edge('ext_plugin', 'core_config')
    dot.edge('ext_plugin', 'core_renderer')
    dot.edge('ext_plugin', 'core_resource')
    dot.edge('ext_effects', 'core_renderer')
    
    # 保存图表
    output_dir = 'docs/Diagrams/Modules'
    ensure_dir(output_dir)
    return dot.render(os.path.join(output_dir, 'module_dependencies'))

def generate_data_flow():
    """生成数据流图

    Returns:
        str: 生成的图表文件路径
    """
    dot = graphviz.Digraph('data_flow', comment='数据流图', 
                          format='png', engine='dot')
    
    # 设置图表属性
    dot.attr(rankdir='TB', size='8,5', ratio='fill', fontname='SimSun')
    dot.attr('node', fontname='SimSun', fontsize='12')
    
    # 添加节点
    dot.node('input', '用户输入', shape='ellipse', style='filled', color='lightblue')
    dot.node('config', '配置解析', shape='box', style='filled', color='lightgreen')
    dot.node('resource', '资源加载', shape='box', style='filled', color='lightgreen')
    dot.node('processing', '数据处理', shape='box', style='filled', color='lightgreen')
    dot.node('rendering', '渲染处理', shape='box', style='filled', color='lightgreen')
    dot.node('output', '屏幕输出', shape='ellipse', style='filled', color='lightblue')
    
    # 添加边
    dot.edge('input', 'config', label='配置参数')
    dot.edge('config', 'resource', label='资源请求')
    dot.edge('resource', 'processing', label='原始数据')
    dot.edge('processing', 'rendering', label='处理后数据')
    dot.edge('rendering', 'output', label='渲染结果')
    
    # 保存图表
    output_dir = 'docs/Diagrams/Flowcharts'
    ensure_dir(output_dir)
    return dot.render(os.path.join(output_dir, 'data_flow'))

def generate_class_diagram():
    """生成类图

    Returns:
        str: 生成的图表文件路径
    """
    dot = graphviz.Digraph('class_diagram', comment='类图', 
                          format='png', engine='dot')
    
    # 设置图表属性
    dot.attr(rankdir='TB', size='8,5', ratio='fill', fontname='SimSun')
    dot.attr('node', shape='record', style='filled', color='lightblue', 
            fontname='SimSun', fontsize='12')
    dot.attr('edge', fontname='SimSun', fontsize='10')
    
    # 添加类节点
    dot.node('ConfigManager', '{ConfigManager|+ config_data : dict\\l+ file_path : str\\l|+ load() : bool\\l+ save() : bool\\l+ get_value(key) : any\\l+ set_value(key, value) : void\\l}')
    
    dot.node('ResourceManager', '{ResourceManager|+ resources : dict\\l|+ load_resource(path) : Resource\\l+ get_resource(id) : Resource\\l+ unload_resource(id) : bool\\l}')
    
    dot.node('Renderer', '{Renderer|+ width : int\\l+ height : int\\l|+ init() : bool\\l+ render_scene(scene) : void\\l+ cleanup() : void\\l}')
    
    dot.node('Scene', '{Scene|+ objects : list\\l+ camera : Camera\\l|+ add_object(obj) : void\\l+ remove_object(obj) : void\\l+ update() : void\\l}')
    
    # 添加关系边
    dot.edge('Scene', 'Renderer', label='使用')
    dot.edge('ResourceManager', 'Renderer', label='供应资源')
    dot.edge('ConfigManager', 'ResourceManager', label='配置')
    dot.edge('ConfigManager', 'Renderer', label='配置')
    
    # 保存图表
    output_dir = 'docs/Diagrams/DataModels'
    ensure_dir(output_dir)
    return dot.render(os.path.join(output_dir, 'class_diagram'))

def main():
    """主函数，生成所有图表"""
    print("正在生成系统架构图...")
    system_arch_path = generate_system_architecture()
    print(f"系统架构图已生成：{system_arch_path}")
    
    print("正在生成模块依赖关系图...")
    module_dep_path = generate_module_dependencies()
    print(f"模块依赖关系图已生成：{module_dep_path}")
    
    print("正在生成数据流图...")
    data_flow_path = generate_data_flow()
    print(f"数据流图已生成：{data_flow_path}")
    
    print("正在生成类图...")
    class_diagram_path = generate_class_diagram()
    print(f"类图已生成：{class_diagram_path}")
    
    print("所有图表生成完成！")

if __name__ == "__main__":
    main() 