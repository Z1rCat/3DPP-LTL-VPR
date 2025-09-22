"""
测试基于JSON文件的装载可视化
Test JSON-based Loading Visualization with Real Data
"""

import sys
import json
from pathlib import Path

# 添加项目路径
sys.path.append(str(Path(__file__).parent))

from visualization.real_data_loader import RealDataLoader
from visualization.plotly_3d import Plotly3DVisualizer
from config import VISUALIZATIONS_DIR

def test_json_loading_visualization():
    """测试JSON装载可视化"""
    print("=== 测试基于JSON文件的装载可视化 ===")

    try:
        # 1. 加载真实数据
        print("[1] 加载装载方案JSON数据...")
        data_loader = RealDataLoader()

        # 获取统计信息
        stats = data_loader.get_statistics()
        print(f"   数据统计: {stats}")

        # 获取装载可视化数据
        loading_data = data_loader.get_loading_visualization_data()
        truck_assignments = loading_data.get('truck_assignments', {})

        if not truck_assignments:
            print("[错误] 没有找到装载方案数据")
            return

        print(f"   成功加载 {len(truck_assignments)} 个车辆的装载数据")
        print(f"   车辆类型: {loading_data['summary']['vehicle_types']}")
        print(f"   货物类型: {loading_data['summary']['cargo_types']}")
        print(f"   总货物数: {loading_data['summary']['total_items']}")

        # 2. 初始化可视化器
        print("[2] 初始化Plotly3D可视化器...")
        visualizer = Plotly3DVisualizer()

        # 3. 生成3D装载可视化
        print("[3] 生成3D装载可视化...")

        # 为每个车辆生成可视化
        visualization_files = []
        for truck_id, truck_data in truck_assignments.items():
            print(f"   处理车辆: {truck_id}")
            print(f"     - 装载货物数: {len(truck_data.get('loaded_items', []))}")
            print(f"     - 装载效率: {truck_data.get('loading_efficiency', 0):.1f}%")
            print(f"     - 货物类型: {truck_data.get('cargo_types', [])}")

            try:
                # 使用单车辆可视化方法
                truck_items = truck_data.get('loaded_items', [])
                if truck_items:
                    fig = visualizer.create_truck_visualization(
                        truck_id,
                        truck_items
                    )

                    # 更新标题
                    fig.update_layout(title=f"JSON装载可视化 - {truck_id} (真实数据)")

                    if fig:
                        # 保存HTML文件
                        html_file = VISUALIZATIONS_DIR / f"json_loading_{truck_id}_3d_visualization.html"
                        fig.write_html(str(html_file))
                        visualization_files.append(str(html_file))
                        print(f"     OK 生成可视化文件: {html_file}")
                    else:
                        print(f"     FAIL 可视化生成失败: {truck_id}")
                else:
                    print(f"     SKIP 无装载货物: {truck_id}")

            except Exception as e:
                print(f"     ERROR 生成可视化时出错: {str(e)}")

        # 4. 生成综合统计图表
        try:
            print("[4] 生成装载效率统计...")

            # 创建一个简单的统计图
            import plotly.graph_objects as go

            truck_names = []
            loading_efficiencies = []
            total_items = []

            for truck_id, truck_data in truck_assignments.items():
                truck_names.append(truck_id)
                loading_efficiencies.append(truck_data.get('loading_efficiency', 0))
                total_items.append(len(truck_data.get('loaded_items', [])))

            # 创建装载效率柱状图
            fig = go.Figure()
            fig.add_trace(go.Bar(
                x=truck_names,
                y=loading_efficiencies,
                name='装载效率 (%)',
                text=[f"{eff:.1f}%" for eff in loading_efficiencies],
                textposition='auto'
            ))

            fig.update_layout(
                title='车辆装载效率统计 (基于JSON真实数据)',
                xaxis_title='车辆ID',
                yaxis_title='装载效率 (%)',
                yaxis=dict(range=[0, 100])
            )

            html_file = VISUALIZATIONS_DIR / "json_loading_efficiency_stats.html"
            fig.write_html(str(html_file))
            visualization_files.append(str(html_file))
            print(f"   OK 装载效率统计图: {html_file}")

        except Exception as e:
            print(f"   ERROR 统计图生成失败: {str(e)}")

        # 5. 结果汇总
        print(f"\n[完成] 生成了 {len(visualization_files)} 个可视化HTML文件:")
        for file_path in visualization_files:
            print(f"   - {file_path}")

        print(f"\n可视化文件保存在: {VISUALIZATIONS_DIR}")
        print("请在浏览器中打开HTML文件查看3D装载可视化结果")

    except Exception as e:
        print(f"[错误] 测试过程中出现异常: {str(e)}")
        import traceback
        traceback.print_exc()

def display_sample_data():
    """显示JSON数据样本"""
    print("\n=== JSON数据样本 ===")

    try:
        data_loader = RealDataLoader()
        loading_plans = data_loader.load_loading_plans()

        if loading_plans:
            # 显示第一个车辆的数据结构
            first_vehicle = list(loading_plans.keys())[0]
            first_data = loading_plans[first_vehicle]

            print(f"车辆 {first_vehicle} 的数据结构:")
            print(f"- 摘要: {json.dumps(first_data.get('summary', {}), indent=2, ensure_ascii=False)}")

            loading_plan = first_data.get('loading_plan', [])
            if loading_plan:
                print(f"- 装载计划样本 (第1个货物):")
                print(f"  {json.dumps(loading_plan[0], indent=2, ensure_ascii=False)}")

    except Exception as e:
        print(f"显示样本数据失败: {str(e)}")

if __name__ == "__main__":
    # 显示样本数据
    display_sample_data()

    # 测试可视化
    test_json_loading_visualization()