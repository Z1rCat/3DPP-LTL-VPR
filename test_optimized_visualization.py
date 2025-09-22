"""
测试优化后的可视化性能
Test Optimized Visualization Performance
"""

import sys
import time
from pathlib import Path

# 添加项目路径
sys.path.append(str(Path(__file__).parent))

from visualization.real_data_loader import RealDataLoader
from visualization.plotly_3d import Plotly3DVisualizer

def test_optimized_visualizations():
    """测试优化后的可视化性能"""
    print("=== 测试优化后的可视化性能 ===")

    try:
        # 1. 加载数据
        print("[1] 加载装载数据...")
        data_loader = RealDataLoader()
        loading_data = data_loader.get_loading_visualization_data()
        truck_assignments = loading_data.get('truck_assignments', {})

        if not truck_assignments:
            print("[错误] 没有找到装载数据")
            return

        # 转换数据格式以适配可视化函数
        solution_data = {}
        for truck_id, truck_data in truck_assignments.items():
            solution_data[truck_id] = truck_data.get('loaded_items', [])

        print(f"   总车辆数: {len(solution_data)}")
        for truck_id, items in solution_data.items():
            print(f"   {truck_id}: {len(items)} 个货物")

        # 2. 初始化可视化器
        print("[2] 初始化可视化器...")
        visualizer = Plotly3DVisualizer()

        # 3. 测试多品类3DPP可视化
        print("[3] 测试多品类3DPP可视化...")
        start_time = time.time()

        try:
            figures = visualizer.create_multi_category_3dpp_visualization({
                'truck_assignments': solution_data
            })
            end_time = time.time()

            print(f"   OK 多品类可视化完成: {len(figures)} 个图形, 耗时: {end_time-start_time:.2f}秒")

        except Exception as e:
            print(f"   ERROR 多品类可视化失败: {str(e)}")

        # 4. 测试装载密度热力图
        print("[4] 测试装载密度热力图...")
        start_time = time.time()

        try:
            fig = visualizer.create_loading_density_heatmap({
                'truck_assignments': solution_data
            })
            end_time = time.time()

            print(f"   OK 密度热力图完成, 耗时: {end_time-start_time:.2f}秒")

        except Exception as e:
            print(f"   ERROR 密度热力图失败: {str(e)}")

        # 5. 测试3D装载效率分析
        print("[5] 测试3D装载效率分析...")
        start_time = time.time()

        try:
            fig = visualizer.create_3d_loading_efficiency_analysis({
                'truck_assignments': solution_data
            })
            end_time = time.time()

            print(f"   OK 效率分析完成, 耗时: {end_time-start_time:.2f}秒")

        except Exception as e:
            print(f"   ERROR 效率分析失败: {str(e)}")

        print("\n[完成] 所有可视化测试完成")

    except Exception as e:
        print(f"[错误] 测试过程中出现异常: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_optimized_visualizations()