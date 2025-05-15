"""
---------------------------------------------------------------
File name:                  run_tests.py
Author:                     Ignorant-lu
Date created:               2025/04/01
Date modified:              2025/05/15
Description:                测试运行脚本，提供易用的测试命令行界面和报告功能
----------------------------------------------------------------

Changed history:            
                            2025/04/01: 初始创建;
                            2025/04/20: 添加进度条显示;
                            2025/05/15: 增强覆盖率报告和测试可视化;
                            2025/05/15: 修复模块测试文件查找问题，增强智能匹配功能;
----
"""

import argparse
import os
import sys
import time
import platform
import glob
from pathlib import Path
import subprocess
import shutil
import importlib
from typing import List, Optional, Dict, Any, Tuple
import pytest
import json
import datetime

# 将项目根目录添加到sys.path
PROJECT_ROOT = Path(__file__).parent.parent.absolute()
sys.path.insert(0, str(PROJECT_ROOT))

try:
    import graphviz
    HAS_GRAPHVIZ = True
except ImportError:
    HAS_GRAPHVIZ = False

# 定义颜色和样式常量
class Style:
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'

class Color:
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    END = '\033[0m'

def print_color(text: str, color: str, bold: bool = False, underline: bool = False) -> None:
    """打印带颜色的文本"""
    style = ""
    if bold:
        style += Style.BOLD
    if underline:
        style += Style.UNDERLINE
    print(f"{style}{color}{text}{Color.END}{Style.END}")

def print_header(text: str) -> None:
    """打印标题"""
    print("\n" + "=" * 80)
    print_color(f" {text} ", Color.BLUE, bold=True)
    print("=" * 80)

def print_section(text: str) -> None:
    """打印小节标题"""
    print("\n" + "-" * 40)
    print_color(f" {text} ", Color.CYAN)
    print("-" * 40)

# 测试类型定义
class TestType:
    UNIT = "unit"
    INTEGRATION = "integration"
    SYSTEM = "system"
    ALL = "all"

# 测试目录结构
TEST_DIRS = {
    TestType.UNIT: PROJECT_ROOT / "tests" / "unit",
    TestType.INTEGRATION: PROJECT_ROOT / "tests" / "integration",
    TestType.SYSTEM: PROJECT_ROOT / "tests" / "system",
}

# 额外的模块特定测试目录
MODULE_TEST_DIRS = [
    PROJECT_ROOT / "tests" / "pet_assets",
    PROJECT_ROOT / "tests" / "core",
    PROJECT_ROOT / "tests" / "behavior",
    PROJECT_ROOT / "tests" / "monitoring",
    PROJECT_ROOT / "tests" / "interaction",
    PROJECT_ROOT / "tests" / "renderer",
    PROJECT_ROOT / "tests" / "ui",
    PROJECT_ROOT / "tests" / "events",
    PROJECT_ROOT / "tests" / "resources",
    PROJECT_ROOT / "tests" / "plugin",
    PROJECT_ROOT / "tests" / "animation",
    PROJECT_ROOT / "tests" / "scenes",
]

# 覆盖率报告目录
COVERAGE_DIR = PROJECT_ROOT / "reports" / "coverage"
TEST_RESULTS_DIR = PROJECT_ROOT / "reports" / "test_results"
VISUALIZATION_DIR = PROJECT_ROOT / "reports" / "visualizations"

def ensure_dir_exists(path: Path) -> None:
    """确保目录存在"""
    path.mkdir(parents=True, exist_ok=True)

def check_pytest_plugins() -> List[str]:
    """检查是否安装了必要的pytest插件"""
    required_plugins = ["pytest-cov", "pytest-mock", "pytest-qt", "pytest-timeout"]
    missing_plugins = []
    
    for plugin in required_plugins:
        try:
            importlib.import_module(plugin.replace("-", "_"))
        except ImportError:
            missing_plugins.append(plugin)
    
    return missing_plugins

def install_missing_plugins(plugins: List[str]) -> None:
    """安装缺失的插件"""
    if not plugins:
        return
    
    print_section("安装缺失的插件")
    for plugin in plugins:
        print(f"正在安装 {plugin}...")
        subprocess.run([sys.executable, "-m", "pip", "install", plugin], check=True)
    print("插件安装完成")

def find_test_files(module: str) -> List[str]:
    """
    寻找与指定模块相关的测试文件
    
    Args:
        module: 模块名称，例如 'placeholder_factory' 或 'placeholder_factory_cache'
        
    Returns:
        匹配的测试文件路径列表
    """
    test_files = []
    
    # 考虑可能的模块名称变体
    module_variants = [module]
    
    # 如果模块名称包含下划线，尝试匹配部分名称
    if '_' in module:
        # 将 'placeholder_factory_cache' 拆分为 ['placeholder', 'factory', 'cache']
        parts = module.split('_')
        # 添加主要部分，如 'placeholder_factory' 和 'factory_cache'
        if len(parts) > 1:
            module_variants.append('_'.join(parts[:-1]))  # 例如 'placeholder_factory'
            module_variants.append('_'.join(parts[1:]))   # 例如 'factory_cache'
    
    # 对于每个测试目录，尝试查找匹配的测试文件
    all_test_dirs = list(TEST_DIRS.values()) + MODULE_TEST_DIRS
    
    for test_dir in all_test_dirs:
        if not test_dir.exists():
            continue
            
        for variant in module_variants:
            # 具体匹配 test_module.py
            exact_match = test_dir / f"test_{variant}.py"
            if exact_match.exists():
                test_files.append(str(exact_match))
                
            # 前缀匹配 test_module_*.py
            prefix_pattern = str(test_dir / f"test_{variant}_*.py")
            prefix_matches = glob.glob(prefix_pattern)
            test_files.extend(prefix_matches)
            
            # 中间匹配 test_*_module_*.py
            middle_pattern = str(test_dir / f"test_*_{variant}_*.py")
            middle_matches = glob.glob(middle_pattern)
            test_files.extend(middle_matches)
            
            # 后缀匹配 test_*_module.py
            suffix_pattern = str(test_dir / f"test_*_{variant}.py")
            suffix_matches = glob.glob(suffix_pattern)
            test_files.extend(suffix_matches)
    
    # 移除重复项
    return list(set(test_files))

def run_tests(
    test_type: str, 
    module: Optional[str] = None, 
    generate_coverage: bool = True,
    visualize: bool = False,
    parallel: bool = False,
    verbose: bool = False,
    fail_fast: bool = False,
) -> Tuple[int, dict]:
    """
    运行指定类型的测试
    
    Args:
        test_type: 测试类型 (unit, integration, system, all)
        module: 要测试的特定模块
        generate_coverage: 是否生成覆盖率报告
        visualize: 是否生成可视化报告
        parallel: 是否并行运行测试
        verbose: 是否启用详细输出
        fail_fast: 是否在第一个测试失败时停止
        
    Returns:
        运行结果和覆盖率数据的元组
    """
    # 准备目录
    ensure_dir_exists(COVERAGE_DIR)
    ensure_dir_exists(TEST_RESULTS_DIR)
    
    # 准备pytest参数
    pytest_args = []
    
    # 设置测试目录或文件
    if module:
        # 使用增强的测试文件查找逻辑
        test_files = find_test_files(module)
        
        if not test_files:
            print_color(f"错误: 未找到与模块 '{module}' 相关的测试文件", Color.RED)
            # 提供建议
            print("建议:")
            print("1. 检查模块名称是否正确")
            print("2. 确保测试文件名遵循命名约定 (test_<module>.py)")
            print("3. 确保测试文件位于 tests 目录或其子目录中")
            return 1, {}
            
        print_color(f"找到以下与模块 '{module}' 相关的测试文件:", Color.CYAN)
        for i, file in enumerate(test_files, 1):
            print(f"  {i}. {file}")
            
        pytest_args.extend(test_files)
    else:
        # 根据测试类型选择测试目录
        if test_type == TestType.ALL:
            # 运行所有测试目录
            for test_dir in TEST_DIRS.values():
                if test_dir.exists():
                    pytest_args.append(str(test_dir))
        else:
            test_dir = TEST_DIRS.get(test_type)
            if not test_dir or not test_dir.exists():
                print_color(f"错误: 测试目录 {test_dir} 不存在", Color.RED)
                return 1, {}
                
            pytest_args.append(str(test_dir))
    
    # 添加覆盖率参数
    if generate_coverage:
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        html_report_dir = COVERAGE_DIR / f"html_{timestamp}"
        xml_report_file = COVERAGE_DIR / f"coverage_{timestamp}.xml"
        
        pytest_args.extend([
            "--cov=status",
            f"--cov-report=html:{html_report_dir}",
            f"--cov-report=xml:{xml_report_file}",
            "--cov-report=term-missing",
        ])
    
    # 添加JUnit格式测试结果报告
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    junit_report_file = TEST_RESULTS_DIR / f"junit_{timestamp}.xml"
    pytest_args.extend(["--junitxml", str(junit_report_file)])
    
    # 其他参数
    if verbose:
        pytest_args.append("-v")
    
    if fail_fast:
        pytest_args.append("-xvs")
    
    if parallel:
        # 使用auto自动决定进程数
        pytest_args.extend(["-n", "auto"])
    
    # 运行pytest
    print_header(f"运行{test_type}测试" + (f" - 模块: {module}" if module else ""))
    print(f"命令: pytest {' '.join(pytest_args)}")
    
    start_time = time.time()
    result = pytest.main(pytest_args)
    elapsed_time = time.time() - start_time
    
    # 结果处理
    if result == 0:
        print_color(f"\n测试通过! 耗时: {elapsed_time:.2f}秒", Color.GREEN, bold=True)
    else:
        print_color(f"\n测试失败! 耗时: {elapsed_time:.2f}秒", Color.RED, bold=True)
    
    # 读取覆盖率数据
    coverage_data = {}
    if generate_coverage:
        try:
            xml_path = xml_report_file
            if xml_path.exists():
                # 这里可以解析XML文件来获取详细覆盖率数据
                # 简单起见，仅返回HTML报告路径
                coverage_data = {
                    "html_report": str(html_report_dir),
                    "xml_report": str(xml_report_file),
                }
                print_color(f"覆盖率报告已生成: {html_report_dir}", Color.CYAN)
                
                # 在生成可视化报告之前打开覆盖率HTML报告
                if sys.platform.startswith('win'):
                    os.startfile(html_report_dir)
                elif sys.platform.startswith('darwin'):
                    subprocess.run(['open', html_report_dir], check=False)
                else:
                    subprocess.run(['xdg-open', html_report_dir], check=False)
        except Exception as e:
            print_color(f"读取覆盖率数据时出错: {e}", Color.RED)
    
    # 处理测试结果可视化
    if visualize and HAS_GRAPHVIZ:
        try:
            visualize_test_results(junit_report_file, module)
        except Exception as e:
            print_color(f"生成可视化报告时出错: {e}", Color.RED)
    
    return result, coverage_data

def visualize_test_results(junit_file: Path, module: Optional[str] = None) -> None:
    """
    使用Graphviz生成测试结果可视化图表
    
    Args:
        junit_file: JUnit XML测试结果文件
        module: 要可视化的特定模块
    """
    if not HAS_GRAPHVIZ:
        print_color("Graphviz未安装，无法生成可视化报告", Color.YELLOW)
        return
    
    import xml.etree.ElementTree as ET
    
    print_section("生成测试结果可视化")
    
    # 确保可视化目录存在
    ensure_dir_exists(VISUALIZATION_DIR)
    
    try:
        # 解析JUnit XML文件
        tree = ET.parse(junit_file)
        root = tree.getroot()
        
        # 创建有向图
        dot = graphviz.Digraph(
            comment='测试结果可视化',
            format='png',
            engine='dot',
            graph_attr={'rankdir': 'LR', 'bgcolor': '#ffffff'}
        )
        
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        title = f"测试结果 - {timestamp}" + (f" - 模块: {module}" if module else "")
        dot.attr(label=title, fontsize='20', labelloc='t')
        
        # 测试结果统计
        total_tests = 0
        passed_tests = 0
        failed_tests = 0
        skipped_tests = 0
        
        # 处理测试用例
        for testcase in root.findall('.//testcase'):
            classname = testcase.get('classname', '')
            testname = testcase.get('name', '')
            
            # 如果指定了模块且测试类名不包含该模块，则跳过
            if module and module not in classname:
                continue
            
            total_tests += 1
            
            # 确定测试状态
            failure = testcase.find('failure')
            error = testcase.find('error')
            skipped = testcase.find('skipped')
            
            status = 'passed'
            color = '#44bb44'  # 绿色表示通过
            
            if failure is not None or error is not None:
                status = 'failed'
                color = '#ff4444'  # 红色表示失败
                failed_tests += 1
            elif skipped is not None:
                status = 'skipped'
                color = '#bbbb44'  # 黄色表示跳过
                skipped_tests += 1
            else:
                passed_tests += 1
            
            # 添加测试用例节点
            test_id = f"{classname}.{testname}"
            label = f"{testname}\n({status})"
            dot.node(test_id, label, shape='box', style='filled', fillcolor=color)
            
            # 根据测试类名分组
            parts = classname.split('.')
            current_path = ''
            parent_node = None
            
            for i, part in enumerate(parts):
                if current_path:
                    current_path += '.'
                current_path += part
                
                # 如果不是最后一部分，添加为模块/包节点
                if i < len(parts) - 1:
                    dot.node(current_path, part, shape='folder', style='filled', fillcolor='#aaaaff')
                    
                    if parent_node:
                        dot.edge(parent_node, current_path)
                    
                    parent_node = current_path
                else:
                    # 最后一部分是测试类
                    class_node = current_path
                    dot.node(class_node, part, shape='ellipse', style='filled', fillcolor='#ddddff')
                    
                    if parent_node:
                        dot.edge(parent_node, class_node)
                    
                    # 连接测试类和测试用例
                    dot.edge(class_node, test_id)
        
        # 添加摘要节点
        summary_text = f"总计: {total_tests}\n通过: {passed_tests}\n失败: {failed_tests}\n跳过: {skipped_tests}"
        dot.node('summary', summary_text, shape='note', style='filled', fillcolor='#ffffaa')
        
        # 保存图表
        output_file = VISUALIZATION_DIR / f"test_results_{timestamp}"
        dot.render(str(output_file), cleanup=True)
        
        print_color(f"测试结果可视化已生成: {output_file}.png", Color.CYAN)
        
        # 自动打开生成的图表
        if sys.platform.startswith('win'):
            os.startfile(f"{output_file}.png")
        elif sys.platform.startswith('darwin'):
            subprocess.run(['open', f"{output_file}.png"], check=False)
        else:
            subprocess.run(['xdg-open', f"{output_file}.png"], check=False)
            
    except Exception as e:
        print_color(f"生成测试结果可视化时出错: {e}", Color.RED)

def generate_coverage_visualization() -> None:
    """
    使用Graphviz生成覆盖率可视化图表
    """
    if not HAS_GRAPHVIZ:
        print_color("Graphviz未安装，无法生成覆盖率可视化", Color.YELLOW)
        return
    
    print_section("生成覆盖率可视化")
    
    # 确保可视化目录存在
    ensure_dir_exists(VISUALIZATION_DIR)
    
    try:
        # 查找最新的覆盖率XML文件
        xml_files = list(COVERAGE_DIR.glob("coverage_*.xml"))
        if not xml_files:
            print_color("未找到覆盖率XML文件", Color.YELLOW)
            return
        
        latest_xml = max(xml_files, key=lambda f: f.stat().st_mtime)
        
        # 解析XML文件
        import xml.etree.ElementTree as ET
        tree = ET.parse(latest_xml)
        root = tree.getroot()
        
        # 创建有向图
        dot = graphviz.Digraph(
            comment='覆盖率可视化',
            format='png',
            engine='dot',
            graph_attr={'rankdir': 'TB', 'bgcolor': '#ffffff'}
        )
        
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        dot.attr(label=f"覆盖率报告 - {timestamp}", fontsize='20', labelloc='t')
        
        # 处理覆盖率数据
        packages = {}
        
        for package in root.findall('.//package'):
            package_name = package.get('name', '')
            
            # 跳过测试目录
            if 'tests' in package_name:
                continue
            
            # 计算包的平均覆盖率
            total_lines = 0
            covered_lines = 0
            
            for class_node in package.findall('./class'):
                class_lines = int(class_node.get('line-rate', '0')) * 100
                class_covered = int(class_node.get('line-rate', '0')) * 100
                
                total_lines += class_lines
                covered_lines += class_covered
            
            if total_lines > 0:
                coverage_rate = (covered_lines / total_lines) * 100
            else:
                coverage_rate = 0
            
            # 确定颜色（基于覆盖率）
            if coverage_rate >= 80:
                color = '#44bb44'  # 绿色
            elif coverage_rate >= 60:
                color = '#bbbb44'  # 黄色
            else:
                color = '#ff4444'  # 红色
            
            # 添加包节点
            parts = package_name.split('.')
            current_path = ''
            parent_node = None
            
            for i, part in enumerate(parts):
                if current_path:
                    current_path += '.'
                current_path += part
                
                if current_path not in packages:
                    packages[current_path] = {
                        'name': part,
                        'parent': parent_node,
                        'is_leaf': i == len(parts) - 1,
                        'coverage': coverage_rate if i == len(parts) - 1 else 0
                    }
                    
                parent_node = current_path
        
        # 添加节点和边
        for path, info in packages.items():
            label = f"{info['name']}\n" + (f"覆盖率: {info['coverage']:.1f}%" if info['is_leaf'] else "")
            
            # 确定颜色
            if info['is_leaf']:
                if info['coverage'] >= 80:
                    color = '#44bb44'  # 绿色
                elif info['coverage'] >= 60:
                    color = '#bbbb44'  # 黄色
                else:
                    color = '#ff4444'  # 红色
            else:
                color = '#aaaaff'  # 蓝色（模块）
            
            # 添加节点
            dot.node(path, label, shape='box', style='filled', fillcolor=color)
            
            # 添加边
            if info['parent']:
                dot.edge(info['parent'], path)
        
        # 保存图表
        output_file = VISUALIZATION_DIR / f"coverage_{timestamp}"
        dot.render(str(output_file), cleanup=True)
        
        print_color(f"覆盖率可视化已生成: {output_file}.png", Color.CYAN)
        
        # 自动打开生成的图表
        if sys.platform.startswith('win'):
            os.startfile(f"{output_file}.png")
        elif sys.platform.startswith('darwin'):
            subprocess.run(['open', f"{output_file}.png"], check=False)
        else:
            subprocess.run(['xdg-open', f"{output_file}.png"], check=False)
            
    except Exception as e:
        print_color(f"生成覆盖率可视化时出错: {e}", Color.RED)

def print_welcome_message():
    """打印欢迎信息"""
    print_header("Status-Ming 测试运行器")
    print(f"项目根目录: {PROJECT_ROOT}")
    print(f"Python版本: {platform.python_version()}")
    print(f"系统: {platform.system()} {platform.release()}")
    print(f"日期时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    print_color("TDD模式已启用: 先编写测试，再实现功能", Color.GREEN, bold=True)
    print()

def main():
    """主函数，处理命令行参数并执行测试"""
    parser = argparse.ArgumentParser(description="Status-Ming项目测试运行器")
    
    # 测试类型选项
    parser.add_argument(
        "--type", "-t",
        choices=[TestType.UNIT, TestType.INTEGRATION, TestType.SYSTEM, TestType.ALL],
        default=TestType.ALL,
        help="运行的测试类型 (默认: all)"
    )
    
    # 模块选项
    parser.add_argument(
        "--module", "-m",
        help="要测试的特定模块 (例如: placeholder_factory)"
    )
    
    # 覆盖率选项
    parser.add_argument(
        "--coverage", "-c",
        action="store_true",
        help="生成覆盖率报告"
    )
    
    # 可视化选项
    parser.add_argument(
        "--visualize", "-v",
        action="store_true",
        help="生成测试结果可视化图表"
    )
    
    # 并行选项
    parser.add_argument(
        "--parallel", "-p",
        action="store_true",
        help="并行运行测试"
    )
    
    # 详细输出选项
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="启用详细输出"
    )
    
    # 快速失败选项
    parser.add_argument(
        "--fail-fast", "-f",
        action="store_true",
        help="在第一个测试失败时停止"
    )
    
    # 仅生成覆盖率可视化
    parser.add_argument(
        "--cov-viz",
        action="store_true",
        help="仅生成覆盖率可视化图表"
    )
    
    # TDD模式选项
    parser.add_argument(
        "--tdd",
        action="store_true",
        help="使用TDD模式，验证测试是否先失败"
    )
    
    # 添加新的搜索选项
    parser.add_argument(
        "--search", "-s",
        help="搜索包含指定关键字的测试文件，不执行测试"
    )
    
    # 添加执行指定测试文件的选项
    parser.add_argument(
        "--file",
        help="执行指定的测试文件 (相对于tests目录的路径)"
    )
    
    # 在测试目录搜索模式
    parser.add_argument(
        "--show-modules",
        action="store_true",
        help="显示可测试的模块列表"
    )
    
    args = parser.parse_args()
    
    # 打印欢迎信息
    print_welcome_message()
    
    # 检查必要的pytest插件
    missing_plugins = check_pytest_plugins()
    if missing_plugins:
        print_color(f"缺少必要的pytest插件: {', '.join(missing_plugins)}", Color.YELLOW)
        install_missing_plugins(missing_plugins)
    
    # 处理搜索请求
    if args.search:
        search_tests(args.search)
        return 0
        
    # 处理显示模块列表请求
    if args.show_modules:
        show_available_modules()
        return 0
    
    # 处理仅生成覆盖率可视化的情况
    if args.cov_viz:
        generate_coverage_visualization()
        return 0
        
    # 处理指定文件执行
    if args.file:
        test_file = PROJECT_ROOT / "tests" / args.file
        if not test_file.exists():
            print_color(f"错误: 测试文件 {test_file} 不存在", Color.RED)
            return 1
            
        print_header(f"运行指定测试文件: {args.file}")
        
        pytest_args = [str(test_file)]
        if args.verbose:
            pytest_args.append("-v")
        if args.fail_fast:
            pytest_args.append("-xvs")
            
        return pytest.main(pytest_args)
    
    # TDD模式处理
    if args.tdd:
        print_section("TDD模式 - 测试预期失败")
        
        # 第一步：运行测试，预期失败
        result, _ = run_tests(
            args.type,
            args.module,
            generate_coverage=False,
            visualize=False,
            parallel=False,
            verbose=args.verbose,
            fail_fast=True
        )
        
        if result == 0:
            print_color("警告: 在TDD模式下，测试应该先失败，但现在已经通过。", Color.YELLOW, bold=True)
            print("您可能已经实现了功能，或者测试没有正确验证功能。")
            
            response = input("是否继续运行完整测试套件? (y/n): ").lower()
            if response != 'y':
                return 1
            
            print_color("\n继续TDD流程 - 验证实现", Color.GREEN)
        else:
            print_color("测试预期失败，符合TDD模式。请实现功能使测试通过。", Color.GREEN, bold=True)
            print_color("TDD流程提示:", Color.CYAN)
            print("1. 检查测试失败的原因，了解需要实现的功能")
            print("2. 实现最小化代码使测试通过")
            print("3. 运行相同的测试命令（不带--tdd参数）验证测试是否通过")
            print("4. 重构代码保持测试通过")
            return 0
    
    # 运行测试
    result, coverage_data = run_tests(
        args.type,
        args.module,
        generate_coverage=args.coverage,
        visualize=args.visualize,
        parallel=args.parallel,
        verbose=args.verbose,
        fail_fast=args.fail_fast
    )
    
    # 生成覆盖率可视化
    if args.coverage and args.visualize and HAS_GRAPHVIZ:
        generate_coverage_visualization()
    
    return result

def search_tests(keyword: str) -> None:
    """
    搜索包含指定关键字的测试文件
    
    Args:
        keyword: 搜索关键字
    """
    print_header(f"搜索包含关键字 '{keyword}' 的测试文件")
    
    # 获取所有测试目录
    all_test_dirs = list(TEST_DIRS.values()) + MODULE_TEST_DIRS
    
    # 搜索匹配的测试文件
    matches = []
    for test_dir in all_test_dirs:
        if not test_dir.exists():
            continue
            
        pattern = str(test_dir / f"**/*{keyword}*.py")
        files = glob.glob(pattern, recursive=True)
        matches.extend(files)
    
    if not matches:
        print_color(f"未找到包含关键字 '{keyword}' 的测试文件", Color.YELLOW)
        return
        
    print_color(f"找到 {len(matches)} 个匹配的测试文件:", Color.CYAN)
    for i, file in enumerate(matches, 1):
        rel_path = Path(file).relative_to(PROJECT_ROOT)
        print(f"  {i}. {rel_path}")
        
def show_available_modules() -> None:
    """显示所有可测试的模块列表"""
    print_header("可测试的模块列表")
    
    # 获取所有测试目录
    all_test_dirs = list(TEST_DIRS.values()) + MODULE_TEST_DIRS
    
    # 搜索所有测试文件
    test_files = []
    for test_dir in all_test_dirs:
        if not test_dir.exists():
            continue
            
        pattern = str(test_dir / "test_*.py")
        files = glob.glob(pattern)
        test_files.extend(files)
    
    # 提取模块名称
    modules = set()
    for file in test_files:
        filename = Path(file).name
        # 从test_module.py或test_module_*.py中提取模块名
        if filename.startswith("test_"):
            # 移除test_前缀
            module_part = filename[5:]
            # 移除.py后缀
            if module_part.endswith(".py"):
                module_part = module_part[:-3]
            
            # 处理带下划线的模块名
            parts = module_part.split("_")
            if len(parts) > 0:
                modules.add(parts[0])  # 添加第一部分作为主模块
                if len(parts) > 1:
                    modules.add("_".join(parts[:2]))  # 添加前两部分
                modules.add(module_part)  # 添加完整模块名
    
    # 输出模块列表
    if not modules:
        print_color("未找到可测试的模块", Color.YELLOW)
        return
        
    print_color(f"找到 {len(modules)} 个可测试的模块:", Color.CYAN)
    for i, module in enumerate(sorted(modules), 1):
        print(f"  {i}. {module}")
    
    print("\n使用示例:")
    print("  python run_tests.py --module <模块名> --type unit")
    print("  python run_tests.py -m placeholder_factory -t unit")

if __name__ == "__main__":
    sys.exit(main()) 