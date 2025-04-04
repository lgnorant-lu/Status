"""
---------------------------------------------------------------
File name:                  system_architecture.py
Author:                     Ignorant-lu
Date created:               2023/04/04
Description:                系统架构图生成脚本
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
    output_dir = '.'
    ensure_dir(output_dir)
    return dot.render(os.path.join(output_dir, 'system_architecture'))

if __name__ == "__main__":
    print("正在生成系统架构图...")
    system_arch_path = generate_system_architecture()
    print(f"系统架构图已生成：{system_arch_path}") 