"""
---------------------------------------------------------------
File name:                  resource_system_example.py
Author:                     Ignorant-lu
Date created:               2025/04/03
Description:                资源管理系统使用示例
----------------------------------------------------------------

Changed history:            
                            2025/04/03: 初始创建;
                            2025/04/04: 移动到正确的示例目录;
----
"""

import os
import sys
import pygame
import tempfile
import shutil
import json
import zipfile
from pathlib import Path

# 添加项目根目录到路径以便导入模块
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

# 导入资源包管理模块
from status.resources.resource_pack import (
    ResourcePack, ResourcePackManager, resource_pack_manager,
    ResourcePackError, ResourcePackLoadError, ResourcePackValidationError,
    ResourcePackType, ResourcePackFormat, ResourcePackMetadata
)
from status.resources.resource_loader import ResourceLoader, resource_loader


def setup_demo_resource_packs():
    """创建演示用的资源包"""
    print("正在创建演示资源包...")
    
    # 创建临时目录
    temp_dir = tempfile.mkdtemp()
    print(f"临时目录创建在: {temp_dir}")
    
    # 创建默认资源包
    default_dir = os.path.join(temp_dir, "builtin", "default")
    os.makedirs(default_dir)
    
    # 创建默认资源包的元数据
    default_metadata = {
        "id": "default",
        "name": "默认资源包",
        "description": "系统默认资源包示例",
        "version": "1.0.0",
        "format_version": 2,
        "author": "系统"
    }
    
    with open(os.path.join(default_dir, "pack.json"), "w", encoding="utf-8") as f:
        json.dump(default_metadata, f, ensure_ascii=False, indent=4)
    
    # 创建资源目录
    textures_dir = os.path.join(default_dir, "textures")
    sounds_dir = os.path.join(default_dir, "sounds")
    data_dir = os.path.join(default_dir, "data")
    
    os.makedirs(textures_dir)
    os.makedirs(sounds_dir)
    os.makedirs(data_dir)
    
    # 创建一些测试资源
    with open(os.path.join(textures_dir, "test.txt"), "w", encoding="utf-8") as f:
        f.write("这是默认资源包中的测试文本文件")
    
    with open(os.path.join(data_dir, "config.json"), "w", encoding="utf-8") as f:
        json.dump({"key": "value", "is_default": True}, f, ensure_ascii=False, indent=4)
    
    # 创建自定义资源包
    custom_dir = os.path.join(temp_dir, "user", "custom")
    os.makedirs(custom_dir)
    
    # 创建自定义资源包的元数据
    custom_metadata = {
        "id": "custom",
        "name": "自定义资源包",
        "description": "用户自定义资源包示例",
        "version": "1.0.0",
        "format_version": 2,
        "author": "用户"
    }
    
    with open(os.path.join(custom_dir, "pack.json"), "w", encoding="utf-8") as f:
        json.dump(custom_metadata, f, ensure_ascii=False, indent=4)
    
    # 创建资源目录
    textures_dir = os.path.join(custom_dir, "textures")
    data_dir = os.path.join(custom_dir, "data")
    
    os.makedirs(textures_dir)
    os.makedirs(data_dir)
    
    # 创建覆盖默认资源的文件
    with open(os.path.join(textures_dir, "test.txt"), "w", encoding="utf-8") as f:
        f.write("这是自定义资源包中的测试文本文件，覆盖了默认资源包")
    
    with open(os.path.join(data_dir, "config.json"), "w", encoding="utf-8") as f:
        json.dump({"key": "custom_value", "is_custom": True}, f, ensure_ascii=False, indent=4)
    
    # 创建ZIP格式的资源包
    zip_dir = os.path.join(temp_dir, "user")
    zip_path = os.path.join(zip_dir, "zip_pack.zip")
    
    with zipfile.ZipFile(zip_path, "w") as zip_file:
        # 添加元数据
        zip_metadata = {
            "id": "zip_pack",
            "name": "ZIP资源包",
            "description": "ZIP格式的资源包示例",
            "version": "1.0.0",
            "format_version": 2,
            "author": "ZIP用户"
        }
        
        zip_file.writestr("pack.json", json.dumps(zip_metadata, ensure_ascii=False, indent=4))
        
        # 添加资源
        zip_file.writestr("textures/zip_test.txt", "这是ZIP资源包中的测试文本文件")
        zip_file.writestr("data/zip_config.json", json.dumps({"is_zip": True}, ensure_ascii=False, indent=4))
    
    return temp_dir


def demo_resource_pack_manager(temp_dir):
    """演示资源包管理器的使用"""
    print("\n===== 资源包管理器演示 =====")
    
    # 创建资源包管理器
    manager = ResourcePackManager()
    
    # 设置目录路径
    manager.builtin_dir = os.path.join(temp_dir, "builtin")
    manager.user_dir = os.path.join(temp_dir, "user")
    
    # 初始化管理器
    print("正在初始化资源包管理器...")
    result = manager.initialize()
    print(f"初始化结果: {result}")
    
    # 获取所有已加载的资源包
    packs = manager.get_resource_packs()
    print(f"\n已加载的资源包数量: {len(packs)}")
    
    for pack_id, pack_info in packs.items():
        print(f"- {pack_id}: {pack_info['name']} (v{pack_info['version']})")
    
    # 激活资源包
    print("\n正在激活资源包...")
    manager.activate_pack("default")
    manager.activate_pack("custom")
    manager.activate_pack("zip_pack")
    
    active_packs = manager.get_active_packs()
    print(f"已激活的资源包: {active_packs}")
    
    # 测试资源访问
    print("\n测试资源访问:")
    test_path = "textures/test.txt"
    
    if manager.has_resource(test_path):
        content = manager.get_resource_content(test_path)
        print(f"资源 '{test_path}' 内容: {content.decode('utf-8')}")
    else:
        print(f"资源 '{test_path}' 不存在")
    
    # 测试ZIP资源访问
    zip_test_path = "textures/zip_test.txt"
    
    if manager.has_resource(zip_test_path):
        content = manager.get_resource_content(zip_test_path)
        print(f"资源 '{zip_test_path}' 内容: {content.decode('utf-8')}")
    else:
        print(f"资源 '{zip_test_path}' 不存在")
    
    # 测试资源优先级
    print("\n测试资源优先级:")
    print("当前优先级顺序下的资源内容:")
    content = manager.get_resource_content(test_path)
    print(f"资源 '{test_path}' 内容: {content.decode('utf-8')}")
    
    # 调整优先级
    print("\n调整优先级...")
    manager.set_pack_priority("default", 2)  # 提高默认资源包的优先级
    manager.set_pack_priority("custom", 1)   # 降低自定义资源包的优先级
    
    print("调整后的优先级顺序下的资源内容:")
    content = manager.get_resource_content(test_path)
    print(f"资源 '{test_path}' 内容: {content.decode('utf-8')}")
    
    # 取消激活资源包
    print("\n取消激活资源包 'custom'...")
    manager.deactivate_pack("custom")
    
    active_packs = manager.get_active_packs()
    print(f"已激活的资源包: {active_packs}")
    
    # 列出所有资源
    print("\n列出所有可用资源:")
    resources = manager.list_resources("")
    for resource in resources[:10]:  # 只显示前10个资源
        print(f"- {resource}")
    
    if len(resources) > 10:
        print(f"... 以及其他 {len(resources) - 10} 个资源")


def demo_resource_loader(temp_dir):
    """演示资源加载器的使用"""
    print("\n===== 资源加载器演示 =====")
    
    # 创建资源加载器
    loader = ResourceLoader()
    
    # 修改资源包管理器的目录路径
    resource_pack_manager.builtin_dir = os.path.join(temp_dir, "builtin")
    resource_pack_manager.user_dir = os.path.join(temp_dir, "user")
    
    # 初始化加载器
    print("正在初始化资源加载器...")
    result = loader.initialize()
    print(f"初始化结果: {result}")
    
    # 测试文本加载
    print("\n测试文本加载:")
    try:
        text = loader.load_text("textures/test.txt")
        print(f"加载的文本内容: {text}")
    except Exception as e:
        print(f"加载文本失败: {e}")
    
    # 测试JSON加载
    print("\n测试JSON加载:")
    try:
        data = loader.load_json("data/config.json")
        print(f"加载的JSON数据: {data}")
    except Exception as e:
        print(f"加载JSON失败: {e}")
    
    # 测试重新加载
    print("\n测试重新加载资源:")
    result = loader.reload()
    print(f"重新加载结果: {result}")
    
    # 测试缓存
    print("\n测试资源缓存:")
    print("首次加载资源...")
    start_time = pygame.time.get_ticks()
    loader.load_text("textures/test.txt")
    end_time = pygame.time.get_ticks()
    print(f"首次加载耗时: {end_time - start_time}ms")
    
    print("再次加载资源（使用缓存）...")
    start_time = pygame.time.get_ticks()
    loader.load_text("textures/test.txt")
    end_time = pygame.time.get_ticks()
    print(f"再次加载耗时: {end_time - start_time}ms")
    
    # 清除缓存
    print("\n清除缓存...")
    loader.clear_cache()
    
    print("清除缓存后加载资源...")
    start_time = pygame.time.get_ticks()
    loader.load_text("textures/test.txt")
    end_time = pygame.time.get_ticks()
    print(f"清除缓存后加载耗时: {end_time - start_time}ms")


def main():
    """主函数"""
    # 初始化Pygame
    pygame.init()
    
    print("===== 资源管理系统演示 =====")
    
    # 创建演示资源包
    temp_dir = setup_demo_resource_packs()
    
    try:
        # 演示资源包管理器
        demo_resource_pack_manager(temp_dir)
        
        # 演示资源加载器
        demo_resource_loader(temp_dir)
        
    except Exception as e:
        print(f"演示过程中发生错误: {e}")
    
    finally:
        # 清理临时目录
        print(f"\n正在清理临时目录: {temp_dir}")
        shutil.rmtree(temp_dir)
    
    print("\n演示完成!")
    pygame.quit()


if __name__ == "__main__":
    main() 