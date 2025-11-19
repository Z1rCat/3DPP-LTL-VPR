#!/usr/bin/env python3
"""
物流优化系统 API 服务启动脚本 (简化版)
Logistics Optimization System API Server Startup Script (Simple Version)
"""

import os
import sys
from pathlib import Path

def check_dependencies():
    """检查必要的依赖是否安装"""
    try:
        import fastapi
        import uvicorn
        print("Core dependencies check passed")
        return True
    except ImportError as e:
        print(f"Missing dependency: {e}")
        print("Please run: pip install -r requirements.txt")
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

    print("Directory structure check completed")

def main():
    """主函数"""
    print("Logistics Optimization System Starting...")
    print("=" * 50)

    # 检查依赖
    if not check_dependencies():
        sys.exit(1)

    # 确保目录存在
    ensure_directories()

    # 设置环境变量
    os.environ["PYTHONPATH"] = str(Path.cwd())

    print("=" * 50)
    print("Starting Web API service...")
    print("Access URLs:")
    print("   - Home: http://localhost:8001")
    print("   - Admin (真实数据监控): http://localhost:8001/admin")
    print("   - Admin Real Data: http://localhost:8001/admin-real")
    print("   - Admin V2 Direct: http://localhost:8001/admin-v2")
    print("   - Vehicle Management: http://localhost:8001/admin/vehicles")
    print("   - Smart Analytics: http://localhost:8001/admin/analytics")
    print("   - Customer: http://localhost:8001/customer")
    print("   - Driver: http://localhost:8001/driver")
    print("   - Manager: http://localhost:8001/manager")
    print("   - Real Data API: http://localhost:8001/api/real-data/optimization-summary")
    print("   - API Docs: http://localhost:8001/docs")
    print("   - Health Check: http://localhost:8001/health")
    print("=" * 50)
    print("Press Ctrl+C to stop service")
    print()

    try:
        # 启动API服务
        import uvicorn
        uvicorn.run(
            "api.app:app",
            host="0.0.0.0",
            port=8001,
            reload=True,
            app_dir=str(Path.cwd())
        )

    except KeyboardInterrupt:
        print("\nAPI service stopped")

    except Exception as e:
        print(f"Startup failed: {e}")
        print("Please check error messages or refer to technical documentation")
        sys.exit(1)

if __name__ == "__main__":
    main()