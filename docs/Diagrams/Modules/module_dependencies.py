"""
---------------------------------------------------------------
File name:                  module_dependencies.py
Author:                     Ignorant-lu
Date created:               2023/04/04
Description:                模块依赖关系图生成脚本
----------------------------------------------------------------

Changed history:            
                            2023/04/04: 初始创建;
----
"""

import os
import graphviz
from pathlib import Path

def ensure_dir(directory):
    """确保目录存在，如不存在则创建

    Args:
        directory (str): 目录路径
    """
    Path(directory).mkdir(parents=True, exist_ok=True)

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
    output_dir = '.'
    ensure_dir(output_dir)
    return dot.render(os.path.join(output_dir, 'module_dependencies'))

if __name__ == "__main__":
    print("正在生成模块依赖关系图...")
    module_dep_path = generate_module_dependencies()
    print(f"模块依赖关系图已生成：{module_dep_path}") 