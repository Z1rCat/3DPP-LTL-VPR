#!/usr/bin/env python3
"""
智能物流3D装箱优化系统演示启动脚本
Logistics Optimization System Demo Startup Script
"""

import os
import sys
import webbrowser
import time
import threading
from pathlib import Path

def start_server():
    """启动FastAPI服务器"""
    import uvicorn
    from api.app import app

    print("🚀 启动智能物流优化系统服务器...")
    print("📡 服务器地址: http://localhost:8000")
    print("🎯 演示页面: http://localhost:8000/demo")
    print("👤 管理员页面: http://localhost:8000/admin")
    print("🚚 司机端页面: http://localhost:8000/driver")
    print("👥 管理层页面: http://localhost:8000/manager")
    print("📦 客户端页面: http://localhost:8000/customer")
    print("🔧 API文档: http://localhost:8000/docs")
    print("\n按 Ctrl+C 停止服务器")
    print("-" * 50)

    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)

def open_browser():
    """延迟打开浏览器"""
    time.sleep(3)
    try:
        webbrowser.open("http://localhost:8000/demo")
        print("🌐 已在浏览器中打开演示页面")
    except Exception as e:
        print(f"⚠️  无法自动打开浏览器: {e}")

def main():
    """主函数"""
    print("=" * 60)
    print("🎯 智能物流3D装箱优化系统")
    print("📊 Smart Logistics 3D Bin Packing Optimization System")
    print("=" * 60)

    # 检查当前目录
    if not Path("api/app.py").exists():
        print("❌ 错误: 请在项目根目录运行此脚本")
        sys.exit(1)

    # 在后台线程中打开浏览器
    browser_thread = threading.Thread(target=open_browser, daemon=True)
    browser_thread.start()

    # 启动服务器
    try:
        start_server()
    except KeyboardInterrupt:
        print("\n👋 服务器已停止")
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()