"""
测试可视化功能的完整脚本
"""

import sys
from pathlib import Path

# 确保可以导入项目模块
sys.path.append(str(Path(__file__).parent))

try:
    from visualization.plotly_3d import Plotly3DVisualizer
    import plotly.graph_objects as go
    print("[OK] 所有可视化库导入成功")

    # 创建测试数据
    test_solution = {
        'truck_assignments': {
            'LARGE_TRUCK_00': [
                {
                    'item_id': 'item_001',
                    'item_type': '大型货物',
                    'volume': 15.0,
                    'weight': 100.0,
                    'position': [0.5, 0.5, 0.5],
                    'dimensions': [1.0, 1.0, 1.0],
                    'category': 'large',
                    'order_id': 'ORDER_001',
                    'destination': '北京',
                    'orientation': 'LWH'
                },
                {
                    'item_id': 'item_002',
                    'item_type': '中型货物',
                    'volume': 8.0,
                    'weight': 60.0,
                    'position': [2.0, 0.5, 0.5],
                    'dimensions': [0.8, 0.8, 0.8],
                    'category': 'medium',
                    'order_id': 'ORDER_002',
                    'destination': '上海',
                    'orientation': 'LWH'
                },
                {
                    'item_id': 'item_003',
                    'item_type': '小型货物',
                    'volume': 2.0,
                    'weight': 20.0,
                    'position': [3.5, 0.5, 0.5],
                    'dimensions': [0.4, 0.4, 0.4],
                    'category': 'small',
                    'order_id': 'ORDER_003',
                    'destination': '广州',
                    'orientation': 'LWH'
                }
            ],
            'LTL_TRUCK_01': [
                {
                    'item_id': 'item_004',
                    'item_type': '中型货物',
                    'volume': 12.0,
                    'weight': 80.0,
                    'position': [1.0, 1.0, 0.5],
                    'dimensions': [0.9, 0.9, 0.9],
                    'category': 'medium',
                    'order_id': 'ORDER_004',
                    'destination': '深圳',
                    'orientation': 'LWH'
                },
                {
                    'item_id': 'item_005',
                    'item_type': '小型货物',
                    'volume': 5.0,
                    'weight': 30.0,
                    'position': [2.5, 1.0, 0.5],
                    'dimensions': [0.6, 0.6, 0.6],
                    'category': 'small',
                    'order_id': 'ORDER_005',
                    'destination': '天津',
                    'orientation': 'LWH'
                }
            ]
        }
    }

    # 初始化可视化器
    visualizer = Plotly3DVisualizer()
    print("[OK] Plotly3DVisualizer初始化成功")

    # 测试1: 单品类3DPP可视化
    print("\n[测试1] 单品类3DPP可视化...")
    figures1 = visualizer.create_enhanced_single_category_3dpp_visualization(test_solution)
    if figures1:
        for i, fig in enumerate(figures1):
            filename = f"test_single_category_{i+1}"
            saved_path = visualizer.save_enhanced_visualization(fig, filename)
            print(f"   ✓ 已保存: {saved_path}")
    else:
        print("   [警告] 没有生成图形")

    # 测试2: 多品类3DPP可视化
    print("\n[测试2] 多品类3DPP可视化...")
    figures2 = visualizer.create_multi_category_3dpp_visualization(test_solution)
    if figures2:
        for i, fig in enumerate(figures2):
            filename = f"test_multi_category_{i+1}"
            saved_path = visualizer.save_enhanced_visualization(fig, filename)
            print(f"   ✓ 已保存: {saved_path}")
    else:
        print("   [警告] 没有生成图形")

    # 测试3: 装载密度热力图
    print("\n[测试3] 装载密度热力图...")
    fig3 = visualizer.create_loading_density_heatmap(test_solution)
    if fig3:
        filename = "test_loading_density"
        saved_path = visualizer.save_enhanced_visualization(fig3, filename)
        print(f"   ✓ 已保存: {saved_path}")
    else:
        print("   [警告] 没有生成图形")

    # 测试4: 3D装载效率分析
    print("\n[测试4] 3D装载效率分析...")
    fig4 = visualizer.create_3d_loading_efficiency_analysis(test_solution)
    if fig4:
        filename = "test_3d_efficiency"
        saved_path = visualizer.save_enhanced_visualization(fig4, filename)
        print(f"   ✓ 已保存: {saved_path}")
    else:
        print("   [警告] 没有生成图形")

    # 测试5: 交互式3D可视化
    print("\n[测试5] 交互式3D可视化...")
    figures5 = visualizer.create_interactive_3d_visualization(test_solution)
    if figures5:
        for i, fig in enumerate(figures5):
            filename = f"test_interactive_3d_{i+1}"
            saved_path = visualizer.save_enhanced_visualization(fig, filename)
            print(f"   ✓ 已保存: {saved_path}")
    else:
        print("   [警告] 没有生成图形")

    # 检查生成的文件
    print("\n[文件检查] 检查生成的可视化文件...")
    viz_dir = Path("output/visualizations")
    if viz_dir.exists():
        files = list(viz_dir.glob("test_*.png")) + list(viz_dir.glob("test_*.html"))
        if files:
            print(f"   ✓ 找到 {len(files)} 个可视化文件:")
            for file in sorted(files):
                file_size = file.stat().st_size / 1024  # KB
                print(f"     - {file.name} ({file_size:.1f} KB)")
        else:
            print("   [警告] 没有找到测试可视化文件")
    else:
        print("   [错误] 可视化目录不存在")

    print("\n[SUCCESS] 可视化功能测试完成!")

except Exception as e:
    print(f"[ERROR] 测试失败: {e}")
    import traceback
    traceback.print_exc()