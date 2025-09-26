#!/usr/bin/env python3
"""
物流优化系统 API 服务启动脚本
Logistics Optimization System API Server Startup Script
"""

import os
import sys
import subprocess
from pathlib import Path

def check_dependencies():
    """检查必要的依赖是否安装"""
    try:
        import fastapi
        import uvicorn
        import plotly
        import folium
        print("✅ 核心依赖检查通过")
        return True
    except ImportError as e:
        print(f"❌ 缺少依赖: {e}")
        print("请运行: pip install -r requirements.txt")
        return False

def check_gurobi():
    """检查Gurobi许可证"""
    try:
        import gurobipy as gp
        env = gp.Env(empty=True)
        env.start()
        print("✅ Gurobi许可证验证通过")
        return True
    except Exception as e:
        print(f"⚠️ Gurobi许可证问题: {e}")
        print("系统将以基础模式运行（某些优化功能可能不可用）")
        return False

def ensure_directories():
    """确保必要的目录存在"""
    directories = [
        "output/reports",
        "output/visualizations",
        "output/logs",
        "frontend/static/css",
        "frontend/static/js",
        "frontend/static/images"
    ]

    for dir_path in directories:
        Path(dir_path).mkdir(parents=True, exist_ok=True)

    print("✅ 目录结构检查完成")

def main():
    """主函数"""
    print("🚛 物流优化系统 V4.0 启动中...")
    print("=" * 50)

    # 检查依赖
    if not check_dependencies():
        sys.exit(1)

    # 检查Gurobi（非必需）
    check_gurobi()

    # 确保目录存在
    ensure_directories()

    # 设置环境变量
    os.environ["PYTHONPATH"] = str(Path.cwd())

    print("=" * 50)
    print("🌐 启动Web API服务...")
    print("📋 访问地址:")
    print("   - 主页: http://localhost:8000")
    print("   - API文档: http://localhost:8000/docs")
    print("   - ReDoc: http://localhost:8000/redoc")
    print("=" * 50)
    print("按 Ctrl+C 停止服务")
    print()

    try:
        # 启动API服务
        subprocess.run([
            sys.executable, "-m", "uvicorn",
            "api.app:app",
            "--host", "0.0.0.0",
            "--port", "8000",
            "--reload"
        ], check=True)

    except KeyboardInterrupt:
        print("\n👋 API服务已停止")

    except Exception as e:
        print(f"❌ 启动失败: {e}")
        print("请检查错误信息或参考技术文档")
        sys.exit(1)

if __name__ == "__main__":
    main()