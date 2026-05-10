#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
脚本工具箱启动器
用于激活虚拟环境并启动工具箱应用
"""

import os
import sys
import subprocess
import platform
from pathlib import Path


def main():
    # 获取当前脚本所在目录
    current_dir = Path(__file__).parent
    
    # 根据操作系统确定虚拟环境路径
    if platform.system() == "Windows":
        venv_path = current_dir / "venv" / "Scripts" / "python.exe"
    else:
        venv_path = current_dir / "venv" / "bin" / "python"
    
    # 检查虚拟环境是否存在
    if not venv_path.exists():
        print(f"错误: 虚拟环境未找到! 请先运行: python -m venv venv")
        print(f"期望路径: {venv_path}")
        input("按任意键退出...")
        return
    
    # 检查依赖是否已安装
    main_py = current_dir / "main.py"
    if not main_py.exists():
        print(f"错误: 主程序文件不存在! 请检查路径: {main_py}")
        input("按任意键退出...")
        return
    
    print("启动脚本工具箱...")
    print(f"使用Python解释器: {venv_path}")
    print(f"启动主程序: {main_py}")
    
    try:
        # 使用虚拟环境中的Python运行主程序
        result = subprocess.run([
            str(venv_path),
            str(main_py)
        ], cwd=current_dir)
        
        if result.returncode != 0:
            print(f"程序运行出错，退出码: {result.returncode}")
            input("按任意键退出...")
        else:
            print("程序正常退出")
    
    except FileNotFoundError:
        print("错误: 找不到Python解释器或主程序文件")
        input("按任意键退出...")
    except Exception as e:
        print(f"运行时发生错误: {e}")
        input("按任意键退出...")


if __name__ == "__main__":
    main()