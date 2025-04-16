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
    name="hollow-ming",
    version="0.1.0",
    author="Ignorant-lu",
    author_email="example@example.com",
    description="空洞骑士主题系统监控桌宠应用",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Ignorant-lu/hollow-ming",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Development Status :: 3 - Alpha",
        "Intended Audience :: End Users/Desktop",
        "Topic :: System :: Monitoring",
        "Topic :: Desktop Environment"
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    include_package_data=True,
    package_data={
        "status": ["assets/**/*"],
    },
    entry_points={
        "console_scripts": [
            "hollow-ming=status.main:main",
        ],
    },
) 