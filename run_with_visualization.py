"""
使用虚拟环境Python启动主程序的脚本
确保可视化功能正常工作
"""

import os
import sys
import subprocess
from pathlib import Path

def main():
    """启动主程序，使用虚拟环境的Python"""

    # 虚拟环境Python路径
    venv_python = Path("A:/MYpython/MCM/mcm/python.exe")

    # 检查虚拟环境是否存在
    if not venv_python.exists():
        print(f"[错误] 虚拟环境Python不存在: {venv_python}")
        print("请确保虚拟环境路径正确")
        return

    # 当前项目路径
    project_dir = Path(__file__).parent
    main_script = project_dir / "main.py"

    if not main_script.exists():
        print(f"[错误] 主程序不存在: {main_script}")
        return

    print("="*60)
    print("零担物流3D装箱优化系统V3.0 - 高级可视化版本")
    print("="*60)
    print(f"[信息] 使用虚拟环境Python: {venv_python}")
    print(f"[信息] 项目目录: {project_dir}")
    print(f"[信息] 可视化功能: 已启用 (Plotly + Folium + Matplotlib)")
    print("[信息] 将生成高清PNG图片和交互式HTML文件")
    print("-"*60)

    try:
        # 切换到项目目录
        os.chdir(project_dir)

        # 使用虚拟环境Python运行主程序
        cmd = [str(venv_python), str(main_script)]
        print(f"[启动] {' '.join(cmd)}")
        print("-"*60)

        # 运行主程序
        result = subprocess.run(cmd, capture_output=False, text=True)

        if result.returncode == 0:
            print("-"*60)
            print("[成功] 程序运行完成!")
            print("[提示] 请查看 output/visualizations/ 目录中的PNG图片文件")
        else:
            print(f"[错误] 程序运行失败，返回码: {result.returncode}")

    except Exception as e:
        print(f"[错误] 启动失败: {e}")

if __name__ == "__main__":
    main()