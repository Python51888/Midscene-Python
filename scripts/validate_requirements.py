#!/usr/bin/env python3
"""
依赖验证脚本
验证生成的requirements.txt文件是否包含所有必要依赖
"""

import subprocess
import sys
import tempfile
import os
from pathlib import Path


def run_command(cmd, check=True, capture_output=True):
    """运行命令并返回结果"""
    try:
        result = subprocess.run(
            cmd, 
            shell=True, 
            check=check, 
            capture_output=capture_output,
            text=True
        )
        return result
    except subprocess.CalledProcessError as e:
        print(f"命令执行失败: {cmd}")
        print(f"错误输出: {e.stderr}")
        sys.exit(1)


def create_test_environment():
    """创建临时测试环境"""
    print("=== 创建临时测试环境 ===")
    
    # 创建临时目录
    temp_dir = tempfile.mkdtemp(prefix="midscene_test_")
    print(f"临时目录: {temp_dir}")
    
    # 创建虚拟环境
    venv_path = os.path.join(temp_dir, "test_env")
    print("创建虚拟环境...")
    run_command(f"python -m venv {venv_path}")
    
    # 获取虚拟环境的Python路径
    if sys.platform == "win32":
        python_path = os.path.join(venv_path, "Scripts", "python.exe")
        pip_path = os.path.join(venv_path, "Scripts", "pip.exe")
    else:
        python_path = os.path.join(venv_path, "bin", "python")
        pip_path = os.path.join(venv_path, "bin", "pip")
    
    return temp_dir, python_path, pip_path


def install_requirements(pip_path, requirements_file):
    """在测试环境中安装依赖"""
    print("=== 安装依赖包 ===")
    print(f"使用requirements文件: {requirements_file}")
    
    # 升级pip
    run_command(f'"{pip_path}" install --upgrade pip')
    
    # 安装依赖
    run_command(f'"{pip_path}" install -r "{requirements_file}"')
    print("依赖安装完成")


def validate_imports(python_path):
    """验证核心包导入"""
    print("=== 验证包导入 ===")
    
    test_imports = [
        "import midscene",
        "import pydantic",
        "import selenium",
        "import playwright",
        "import pytest",
        "import black",
        "import mkdocs",
        "import numpy",
        "import cv2",
        "import PIL",
        "import loguru",
        "import typer",
        "import httpx",
        "import aiohttp",
        "import openai",
        "import anthropic",
    ]
    
    for import_stmt in test_imports:
        try:
            print(f"测试: {import_stmt}")
            run_command(f'"{python_path}" -c "{import_stmt}"')
            print(f"✓ {import_stmt} - 成功")
        except:
            print(f"✗ {import_stmt} - 失败")
            return False
    
    return True


def validate_cli_tools(python_path):
    """验证CLI工具可用性"""
    print("=== 验证CLI工具 ===")
    
    cli_tests = [
        (f'"{python_path}" -m pytest --version', "pytest"),
        (f'"{python_path}" -m black --version', "black"),
        (f'"{python_path}" -m mkdocs --version', "mkdocs"),
    ]
    
    for cmd, tool_name in cli_tests:
        try:
            print(f"测试: {tool_name}")
            result = run_command(cmd)
            print(f"✓ {tool_name} - 可用")
        except:
            print(f"✗ {tool_name} - 不可用")
            return False
    
    return True


def cleanup(temp_dir):
    """清理临时文件"""
    print("=== 清理临时文件 ===")
    try:
        import shutil
        shutil.rmtree(temp_dir)
        print(f"已删除临时目录: {temp_dir}")
    except Exception as e:
        print(f"清理失败: {e}")


def main():
    """主函数"""
    print("=== Midscene Python 依赖验证 ===\n")
    
    # 检查requirements.txt是否存在
    requirements_file = Path("requirements.txt")
    if not requirements_file.exists():
        print("错误: requirements.txt 文件不存在")
        print("请先运行: make requirements-freeze")
        sys.exit(1)
    
    temp_dir = None
    try:
        # 创建测试环境
        temp_dir, python_path, pip_path = create_test_environment()
        
        # 安装依赖
        install_requirements(pip_path, requirements_file)
        
        # 验证导入
        if not validate_imports(python_path):
            print("\n❌ 包导入验证失败")
            sys.exit(1)
        
        # 验证CLI工具
        if not validate_cli_tools(python_path):
            print("\n❌ CLI工具验证失败")
            sys.exit(1)
        
        print("\n✅ 所有依赖验证通过!")
        print("requirements.txt 文件完整且可用")
        
    except KeyboardInterrupt:
        print("\n用户中断验证过程")
        sys.exit(1)
    except Exception as e:
        print(f"\n验证过程中出现错误: {e}")
        sys.exit(1)
    finally:
        if temp_dir:
            cleanup(temp_dir)


if __name__ == "__main__":
    main()