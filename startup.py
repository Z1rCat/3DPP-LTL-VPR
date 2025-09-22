"""
零担物流优化系统启动脚本
Logistics Optimization System Startup Script

支持命令行模式和Web API服务器模式
"""

import argparse
import sys
import os
from pathlib import Path
import logging

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from config import (API_CONFIG, create_all_directories, validate_extended_config)


def setup_logging(verbose: bool = False):
    """设置日志配置"""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('output/logs/system.log', encoding='utf-8')
        ]
    )


def start_api_server(host: str = None, port: int = None, debug: bool = None):
    """启动Web API服务器"""
    try:
        # 导入API模块
        from api import create_app

        # 使用参数或配置文件中的默认值
        server_host = host or API_CONFIG['host']
        server_port = port or API_CONFIG['port']
        server_debug = debug if debug is not None else API_CONFIG['debug']

        print("=" * 60)
        print("零担物流优化系统 Web API 服务器")
        print("=" * 60)
        print(f"服务器地址: http://{server_host}:{server_port}")
        print(f"调试模式: {'开启' if server_debug else '关闭'}")
        print(f"API文档: http://{server_host}:{server_port}/api/health")
        print("=" * 60)
        print("按 Ctrl+C 停止服务器")
        print("=" * 60)

        # 创建并启动Flask应用
        app = create_app()
        app.run(
            host=server_host,
            port=server_port,
            debug=server_debug,
            threaded=True
        )

    except ImportError as e:
        print(f"错误: 无法导入API模块: {e}")
        print("请确保已安装Flask和相关依赖:")
        print("pip install flask flask-cors")
        sys.exit(1)
    except Exception as e:
        print(f"启动API服务器失败: {e}")
        sys.exit(1)


def start_cli_mode(verbose: bool = False):
    """启动命令行模式"""
    try:
        from main import main as run_optimization

        print("=" * 60)
        print("零担物流优化系统 - 命令行模式")
        print("=" * 60)

        # 运行优化
        result = run_optimization()

        if result:
            print("\n" + "=" * 60)
            print("优化完成!")
            print("=" * 60)
            return 0
        else:
            print("\n" + "=" * 60)
            print("优化失败!")
            print("=" * 60)
            return 1

    except Exception as e:
        print(f"命令行模式执行失败: {e}")
        if verbose:
            import traceback
            traceback.print_exc()
        return 1


def start_interactive_mode():
    """启动交互式模式"""
    from frontend_interface import frontend_interface

    print("=" * 60)
    print("零担物流优化系统 - 交互式模式")
    print("=" * 60)

    def progress_callback(progress_info):
        print(f"进度: {progress_info['progress']:3d}% - {progress_info['step']}")

    print("正在提交优化任务...")
    task_id = frontend_interface.submit_optimization_task(
        progress_callback=progress_callback
    )

    print(f"任务ID: {task_id}")
    print("正在执行优化...")

    # 等待任务完成
    import time
    while True:
        status = frontend_interface.get_task_status(task_id)

        if status['status'] == 'completed':
            print("\n优化完成!")
            summary = frontend_interface.get_result_summary(task_id)
            if summary:
                print("\n结果摘要:")
                opt_summary = summary['optimization_summary']
                print(f"  使用车辆: {opt_summary['total_trucks_used']} 辆")
                print(f"  装载货物: {opt_summary['total_items_loaded']} 个")
                print(f"  装载效率: {opt_summary['overall_loading_efficiency']:.1f}%")
                print(f"  运行时间: {opt_summary['runtime']}")
            break

        elif status['status'] == 'failed':
            print(f"\n优化失败: {status.get('error', '未知错误')}")
            break

        time.sleep(2)


def test_system():
    """测试系统功能"""
    print("=" * 60)
    print("零担物流优化系统 - 系统测试")
    print("=" * 60)

    try:
        # 测试配置
        print("1. 测试配置...")
        validate_extended_config()
        print("   [OK] 配置验证通过")

        # 测试目录创建
        print("2. 测试目录创建...")
        create_all_directories()
        print("   [OK] 目录创建成功")

        # 测试主模块导入
        print("3. 测试主模块...")
        from main import LogisticsOptimizationSystemV2
        system = LogisticsOptimizationSystemV2(verbose=False)
        print("   [OK] 主系统初始化成功")

        # 测试API模块
        print("4. 测试API模块...")
        try:
            from api import create_app
            app = create_app()
            print("   [OK] API模块加载成功")
        except ImportError:
            print("   [WARNING] API模块不可用 (需要安装Flask)")

        # 测试前端接口
        print("5. 测试前端接口...")
        from frontend_interface import frontend_interface
        status = frontend_interface.get_system_status()
        print(f"   [OK] 前端接口正常 (最大并发: {status['system_resources']['max_concurrent_tasks']})")

        print("\n" + "=" * 60)
        print("系统测试通过! !")
        print("=" * 60)
        return 0

    except Exception as e:
        print(f"\n[ERROR] 系统测试失败: {e}")
        import traceback
        traceback.print_exc()
        return 1


def show_status():
    """显示系统状态"""
    print("=" * 60)
    print("零担物流优化系统 - 状态信息")
    print("=" * 60)

    try:
        # 显示基本信息
        print("基本信息:")
        print(f"  项目路径: {project_root}")
        print(f"  Python版本: {sys.version}")

        # 显示配置信息
        print("\n配置信息:")
        print(f"  API端口: {API_CONFIG['port']}")
        print(f"  最大并发任务: {API_CONFIG['max_concurrent_tasks']}")
        print(f"  调试模式: {API_CONFIG['debug']}")

        # 检查关键文件
        print("\n关键文件检查:")
        key_files = [
            'main.py', 'config.py', 'api.py',
            'frontend_interface.py', 'generate_full_truck_routes.py',
            'export_route_results.py'
        ]

        for file_name in key_files:
            file_path = project_root / file_name
            status = "[OK]" if file_path.exists() else "[MISSING]"
            print(f"  {status} {file_name}")

        # 检查输出目录
        print("\n输出目录检查:")
        from config import OUTPUT_DIR, INTERMEDIATE_DIR, REPORTS_DIR, VISUALIZATIONS_DIR
        dirs = [
            ('output', OUTPUT_DIR),
            ('intermediate', INTERMEDIATE_DIR),
            ('reports', REPORTS_DIR),
            ('visualizations', VISUALIZATIONS_DIR)
        ]

        for name, path in dirs:
            status = "[OK]" if path.exists() else "[MISSING]"
            print(f"  {status} {name}: {path}")

        # 检查数据文件
        print("\n数据文件检查:")
        from config import DATA_FILE
        status = "[OK]" if DATA_FILE.exists() else "[MISSING]"
        print(f"  {status} 数据文件: {DATA_FILE.name}")

        print("\n" + "=" * 60)

    except Exception as e:
        print(f"获取状态信息失败: {e}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="零担物流3D装箱优化系统",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  python startup.py                    # 命令行模式
  python startup.py --mode api         # API服务器模式
  python startup.py --mode interactive # 交互式模式
  python startup.py --mode test        # 系统测试
  python startup.py --mode status      # 查看状态

API模式选项:
  python startup.py --mode api --host 127.0.0.1 --port 8080 --debug
        """
    )

    parser.add_argument(
        '--mode',
        choices=['cli', 'api', 'interactive', 'test', 'status'],
        default='cli',
        help='运行模式 (默认: cli)'
    )

    parser.add_argument(
        '--host',
        type=str,
        help='API服务器主机地址 (仅API模式)'
    )

    parser.add_argument(
        '--port',
        type=int,
        help='API服务器端口号 (仅API模式)'
    )

    parser.add_argument(
        '--debug',
        action='store_true',
        help='启用调试模式 (仅API模式)'
    )

    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='详细输出'
    )

    args = parser.parse_args()

    # 设置日志
    setup_logging(args.verbose)

    # 确保输出目录存在
    try:
        create_all_directories()
    except Exception as e:
        print(f"创建输出目录失败: {e}")
        return 1

    # 根据模式执行相应操作
    if args.mode == 'cli':
        return start_cli_mode(args.verbose)

    elif args.mode == 'api':
        return start_api_server(args.host, args.port, args.debug)

    elif args.mode == 'interactive':
        start_interactive_mode()
        return 0

    elif args.mode == 'test':
        return test_system()

    elif args.mode == 'status':
        show_status()
        return 0

    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n用户中断，程序退出")
        sys.exit(0)
    except Exception as e:
        print(f"程序运行失败: {e}")
        sys.exit(1)