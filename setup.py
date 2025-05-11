"""
---------------------------------------------------------------
File name:                  setup.py
Author:                     Ignorant-lu
Date created:               2025/04/04
Description:                项目安装配置文件
----------------------------------------------------------------

Changed history:            
                            2025/04/04: 初始创建;
----
"""

from setuptools import setup, find_packages
import os

# 读取README.md作为长描述
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

# 读取requirements.txt作为依赖列表
with open("requirements.txt", "r", encoding="utf-8") as f:
    requirements = f.read().splitlines()
    # 移除注释行
    requirements = [r for r in requirements if not r.startswith('#') and r.strip()]

setup(
    name="status-pet",
    version="0.1.0",
    author="lgnorant-lu",
    author_email="lgnorantlu@gmail.com",
    description="桌面交互式宠物应用",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/lgnorant-lu/status",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Operating System :: Microsoft :: Windows",
        "Operating System :: POSIX :: Linux",
        "Operating System :: MacOS :: MacOS X",
    ],
    python_requires=">=3.8",
    install_requires=[
        "PySide6>=6.4.0",
        "psutil>=5.9.0",
        "py-cpuinfo>=8.0.0",
        "Pillow>=9.2.0",
        "pyyaml>=6.0",
        "pypiwin32",
        # 其他依赖
    ],
    include_package_data=True,
    package_data={
        "status": ["assets/**/*"],
    },
    entry_points={
        "console_scripts": [
            "status-pet=status.main:main",
        ],
    },
) 