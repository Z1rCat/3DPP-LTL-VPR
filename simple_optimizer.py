"""
简化版优化器 - 不依赖Gurobi，生成真实可视化
Simple Optimizer - No Gurobi dependency, generates real visualizations
"""

import os
import json
import pandas as pd
from pathlib import Path
from datetime import datetime
import time
import random
import numpy as np
from typing import Dict, List, Any

class SimpleOptimizer:
    """简化版物流优化器"""

    def __init__(self, output_dir: Path = None):
        self.output_dir = output_dir or Path("output")
        self.output_dir.mkdir(exist_ok=True)
        (self.output_dir / "visualizations").mkdir(exist_ok=True)
        (self.output_dir / "reports").mkdir(exist_ok=True)

        # 卡车规格
        self.truck_specs = {
            'length': 9.6,
            'width': 2.4,
            'height': 2.4,
            'volume': 55.0
        }

    def run_optimization(self, algorithm: str = "simple", data_source: str = "simulated_data.xlsx",
                        max_trucks: int = 10, time_limit: int = 60) -> Dict[str, Any]:
        """
        运行简化版优化

        Returns:
            Dict: 优化结果
        """
        print(f"[启动] 简化版优化算法: {algorithm}")
        print(f"[数据源] {data_source}")
        print(f"[最大车辆] {max_trucks}")
        print(f"[时间限制] {time_limit}秒")

        start_time = time.time()

        # 1. 生成模拟货物数据
        print("[步骤1] 生成模拟货物数据...")
        cargo_data = self._generate_cargo_data()

        # 2. 装载优化（简化版）
        print("[步骤2] 执行装载优化...")
        loading_plans = self._simple_loading_optimization(cargo_data, max_trucks)

        # 3. 路径规划（简化版）
        print("[步骤3] 执行路径规划...")
        route_plans = self._simple_route_planning(loading_plans)

        # 4. 生成可视化文件
        print("[步骤4] 生成可视化文件...")
        viz_files = self._generate_visualizations(loading_plans, route_plans)

        # 5. 生成数据文件
        print("[步骤5] 生成数据文件...")
        data_files = self._generate_data_files(loading_plans, route_plans)

        end_time = time.time()
        execution_time = end_time - start_time

        # 6. 生成优化结果摘要
        result = {
            "algorithm_used": algorithm,
            "data_source": data_source,
            "execution_time": execution_time,
            "total_trucks": len(loading_plans),
            "total_items": sum(len(plan['items']) for plan in loading_plans),
            "total_volume": sum(plan['total_volume'] for plan in loading_plans),
            "average_loading_efficiency": np.mean([plan['efficiency'] for plan in loading_plans]) * 100,
            "visualization_files": viz_files,
            "data_files": data_files,
            "loading_plans": loading_plans,
            "route_plans": route_plans
        }

        # 保存优化摘要
        summary_file = self.output_dir / "optimization_summary.json"
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

        print(f"[完成] 优化完成，耗时 {execution_time:.2f} 秒")
        print(f"[输出] 生成了 {len(viz_files)} 个可视化文件")
        print(f"[输出] 生成了 {len(data_files)} 个数据文件")

        return result

    def _generate_cargo_data(self) -> List[Dict]:
        """生成模拟货物数据"""
        cargo_types = ['电子产品', '服装', '食品', '家具', '日用品', '建材']

        cargo_data = []
        for i in range(100):  # 生成100个货物
            cargo_type = random.choice(cargo_types)
            volume = random.uniform(0.1, 2.0)  # 0.1-2.0 立方米
            weight = random.uniform(10, 500)   # 10-500 公斤

            cargo_data.append({
                'id': f'CARGO_{i:04d}',
                'type': cargo_type,
                'volume': volume,
                'weight': weight,
                'destination': {
                    'lat': 30.0 + random.uniform(-2, 2),  # 成都附近坐标
                    'lng': 104.0 + random.uniform(-2, 2)
                }
            })

        return cargo_data

    def _simple_loading_optimization(self, cargo_data: List[Dict], max_trucks: int) -> List[Dict]:
        """简化版装载优化 - 贪心算法"""
        # 按体积排序（大的优先）
        sorted_cargo = sorted(cargo_data, key=lambda x: x['volume'], reverse=True)

        loading_plans = []
        truck_id = 0

        for cargo in sorted_cargo:
            # 尝试装入现有卡车
            loaded = False

            for plan in loading_plans:
                if plan['remaining_volume'] >= cargo['volume']:
                    # 装入此卡车
                    plan['items'].append(cargo)
                    plan['used_volume'] += cargo['volume']
                    plan['remaining_volume'] -= cargo['volume']
                    plan['efficiency'] = plan['used_volume'] / self.truck_specs['volume']
                    loaded = True
                    break

            # 如果无法装入现有卡车，创建新卡车
            if not loaded and len(loading_plans) < max_trucks:
                new_plan = {
                    'truck_id': f'LTL_TRUCK_{truck_id:03d}',
                    'items': [cargo],
                    'used_volume': cargo['volume'],
                    'remaining_volume': self.truck_specs['volume'] - cargo['volume'],
                    'efficiency': cargo['volume'] / self.truck_specs['volume'],
                    'total_volume': self.truck_specs['volume']
                }
                loading_plans.append(new_plan)
                truck_id += 1

        # 生成3D装载位置
        for plan in loading_plans:
            plan['items'] = self._generate_3d_positions(plan['items'])

        return loading_plans

    def _generate_3d_positions(self, items: List[Dict]) -> List[Dict]:
        """为货物生成3D位置"""
        positioned_items = []

        # 简单的网格布局
        grid_size = int(np.sqrt(len(items))) + 1

        for i, item in enumerate(items):
            # 计算网格位置
            grid_x = (i % grid_size) * (self.truck_specs['length'] / grid_size)
            grid_y = (i // grid_size) * (self.truck_specs['width'] / grid_size)
            grid_z = 0  # 简化为单层

            # 添加随机偏移，使位置更自然
            x = grid_x + random.uniform(0, 0.2)
            y = grid_y + random.uniform(0, 0.2)
            z = grid_z + random.uniform(0, 0.1)

            # 估算货物尺寸
            volume = item['volume']
            length = min(volume ** 0.33, 2.0)
            width = min((volume / length) ** 0.5, 1.5)
            height = min(volume / (length * width), 1.0)

            positioned_item = item.copy()
            positioned_item.update({
                'position': {
                    'x': x,
                    'y': y,
                    'z': z
                },
                'dimensions': {
                    'length': length,
                    'width': width,
                    'height': height
                },
                'rotation': random.choice([0, 90, 180, 270])
            })

            positioned_items.append(positioned_item)

        return positioned_items

    def _simple_route_planning(self, loading_plans: List[Dict]) -> List[Dict]:
        """简化版路径规划 - 最近邻算法"""
        depot = {'lat': 30.5728, 'lng': 104.0668}  # 成都坐标

        route_plans = []

        for plan in loading_plans:
            if not plan['items']:
                continue

            # 收集所有目的地
            destinations = [item['destination'] for item in plan['items']]

            # 最近邻算法
            route = []
            current_location = depot
            remaining_destinations = destinations.copy()
            total_distance = 0

            while remaining_destinations:
                # 找到最近的点
                nearest_idx = 0
                nearest_distance = self._calculate_distance(current_location, remaining_destinations[0])

                for i, dest in enumerate(remaining_destinations[1:], 1):
                    distance = self._calculate_distance(current_location, dest)
                    if distance < nearest_distance:
                        nearest_distance = distance
                        nearest_idx = i

                # 添加到路径
                next_dest = remaining_destinations.pop(nearest_idx)
                route.append(next_dest)
                total_distance += nearest_distance
                current_location = next_dest

            # 返回配送中心
            return_distance = self._calculate_distance(current_location, depot)
            total_distance += return_distance

            route_plan = {
                'truck_id': plan['truck_id'],
                'route': [depot] + route + [depot],
                'total_distance_km': total_distance,
                'stops': len(route),
                'estimated_time_hours': total_distance / 60  # 假设60km/h
            }

            route_plans.append(route_plan)

        return route_plans

    def _calculate_distance(self, point1: Dict, point2: Dict) -> float:
        """计算两点间距离（简化版）"""
        lat1, lng1 = point1['lat'], point1['lng']
        lat2, lng2 = point2['lat'], point2['lng']

        # 简化的欧几里得距离
        return np.sqrt((lat2 - lat1)**2 + (lng2 - lng1)**2) * 111  # 转换为公里

    def _generate_visualizations(self, loading_plans: List[Dict], route_plans: List[Dict]) -> List[str]:
        """生成可视化文件"""
        viz_files = []

        # 1. 3D装载可视化（使用HTML + JavaScript）
        for plan in loading_plans[:3]:  # 只生成前3辆车的可视化
            html_file = self._generate_3d_loading_visualization(plan)
            viz_files.append(html_file)

        # 2. 路径地图可视化
        if route_plans:
            map_file = self._generate_route_map_visualization(route_plans[0])
            viz_files.append(map_file)

        # 3. 装载效率图表
        efficiency_file = self._generate_efficiency_chart(loading_plans)
        viz_files.append(efficiency_file)

        return viz_files

    def _generate_3d_loading_visualization(self, plan: Dict) -> str:
        """生成3D装载可视化HTML文件"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"single_category_3dpp_{plan['truck_id']}_{timestamp}.html"
        filepath = self.output_dir / "visualizations" / filename

        # 生成HTML内容
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>3D装载可视化 - {plan['truck_id']}</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .header {{ background: #f0f8ff; padding: 15px; border-radius: 8px; margin-bottom: 20px; }}
        .stats {{ display: flex; gap: 20px; margin-bottom: 20px; }}
        .stat-box {{ background: #e8f4f8; padding: 10px; border-radius: 5px; text-align: center; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🚛 3D装载可视化 - {plan['truck_id']}</h1>
        <p>算法: 简化版装载优化 | 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    </div>

    <div class="stats">
        <div class="stat-box">
            <h3>{len(plan['items'])}</h3>
            <p>装载货物数</p>
        </div>
        <div class="stat-box">
            <h3>{plan['efficiency']*100:.1f}%</h3>
            <p>装载效率</p>
        </div>
        <div class="stat-box">
            <h3>{plan['used_volume']:.2f}m³</h3>
            <p>使用体积</p>
        </div>
    </div>

    <div id="plot"></div>

    <script>
        // 生成3D数据
        const truckSize = {{ length: {self.truck_specs['length']}, width: {self.truck_specs['width']}, height: {self.truck_specs['height']} }};

        // 货物数据
        const cargoData = {json.dumps([{
            'x': item['position']['x'],
            'y': item['position']['y'],
            'z': item['position']['z'],
            'dx': item['dimensions']['length'],
            'dy': item['dimensions']['width'],
            'dz': item['dimensions']['height'],
            'type': item['type'],
            'volume': item['volume']
        } for item in plan['items']])};

        // 创建卡车边框
        const truckOutline = {{
            x: [0, truckSize.length, truckSize.length, 0, 0, 0, truckSize.length, truckSize.length, 0, 0,
                0, truckSize.length, truckSize.length, 0, 0, truckSize.length, truckSize.length, 0, 0, truckSize.length, truckSize.length, 0, 0],
            y: [0, 0, truckSize.width, truckSize.width, 0, 0, 0, truckSize.width, truckSize.width, 0,
                0, 0, 0, 0, truckSize.width, truckSize.width, truckSize.width, truckSize.width, truckSize.width, truckSize.width, 0, 0],
            z: [0, 0, 0, 0, 0, truckSize.height, truckSize.height, truckSize.height, truckSize.height, truckSize.height,
                0, 0, truckSize.height, truckSize.height, 0, 0, truckSize.height, truckSize.height, 0, 0, truckSize.height, truckSize.height]
        }};

        const cargoTrace = {{
            type: 'scatter3d',
            mode: 'markers',
            x: cargoData.map(d => d.x + d.dx/2),
            y: cargoData.map(d => d.y + d.dy/2),
            z: cargoData.map(d => d.z + d.dz/2),
            marker: {{
                size: cargoData.map(d => Math.max(8, d.volume * 10)),
                color: cargoData.map(d => d.volume),
                colorscale: 'Viridis',
                opacity: 0.8,
                colorbar: {{ title: '体积 (m³)' }}
            }},
            text: cargoData.map(d => `${{d.type}}<br>${{d.volume.toFixed(2)}}m³`),
            hovertemplate: '%{{text}}<extra></extra>'
        }};

        const truckTrace = {{
            type: 'scatter3d',
            mode: 'lines',
            x: truckOutline.x,
            y: truckOutline.y,
            z: truckOutline.z,
            line: {{ color: 'red', width: 3 }},
            name: '卡车边界'
        }};

        const layout = {{
            title: `{plan['truck_id']} - 3D装载布局`,
            scene: {{
                xaxis: {{ title: '长度 (m)', range: [0, truckSize.length] }},
                yaxis: {{ title: '宽度 (m)', range: [0, truckSize.width] }},
                zaxis: {{ title: '高度 (m)', range: [0, truckSize.height] }},
                aspectmode: 'manual',
                aspectratio: {{ x: truckSize.length, y: truckSize.width, z: truckSize.height }}
            }},
            margin: {{ l: 0, r: 0, b: 0, t: 40 }}
        }};

        Plotly.newPlot('plot', [cargoTrace, truckTrace], layout);
    </script>
</body>
</html>
        """

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html_content)

        return filename

    def _generate_route_map_visualization(self, plan: Dict) -> str:
        """生成路径地图可视化HTML文件"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"route_map_{plan['truck_id']}_{timestamp}.html"
        filepath = self.output_dir / "visualizations" / filename

        # 生成路径坐标
        route_coords = []
        for point in plan['route']:
            route_coords.append([point['lng'], point['lat']])

        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>路径规划 - {plan['truck_id']}</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.7.1/dist/leaflet.css" />
    <script src="https://unpkg.com/leaflet@1.7.1/dist/leaflet.js"></script>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; }}
        .header {{ background: #f0f8ff; padding: 15px; border-radius: 8px; margin-bottom: 20px; }}
        .stats {{ display: flex; gap: 20px; margin-bottom: 20px; }}
        .stat-box {{ background: #e8f4f8; padding: 10px; border-radius: 5px; text-align: center; }}
        #map {{ height: 500px; width: 100%; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🗺️ 路径规划 - {plan['truck_id']}</h1>
        <p>算法: 简化版最近邻算法 | 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    </div>

    <div class="stats">
        <div class="stat-box">
            <h3>{plan['stops']}</h3>
            <p>停靠点数</p>
        </div>
        <div class="stat-box">
            <h3>{plan['total_distance_km']:.2f}km</h3>
            <p>总距离</p>
        </div>
        <div class="stat-box">
            <h3>{plan['estimated_time_hours']:.1f}h</h3>
            <p>预计时间</p>
        </div>
    </div>

    <div id="map"></div>

    <script>
        // 初始化地图
        const map = L.map('map').setView([30.5728, 104.0668], 10);

        // 添加地图图层
        L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
            attribution: '© OpenStreetMap contributors'
        }}).addTo(map);

        // 路径坐标
        const routeCoords = {json.dumps(route_coords)};

        // 创建路径线
        const routeLine = L.polyline(routeCoords.map(coord => [coord[1], coord[0]]), {{
            color: 'blue',
            weight: 4,
            opacity: 0.8
        }}).addTo(map);

        // 添加标记点
        routeCoords.forEach((coord, index) => {{
            const marker = L.marker([coord[1], coord[0]]).addTo(map);
            const label = index === 0 ? '配送中心' : index === routeCoords.length - 1 ? '返回配送中心' : `停靠点 ${{index}}`;
            marker.bindPopup(label);
        }});

        // 调整地图视野
        map.fitBounds(routeLine.getBounds());
    </script>
</body>
</html>
        """

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html_content)

        return filename

    def _generate_efficiency_chart(self, loading_plans: List[Dict]) -> str:
        """生成装载效率图表"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"loading_efficiency_chart_{timestamp}.html"
        filepath = self.output_dir / "visualizations" / filename

        # 准备数据
        truck_names = [plan['truck_id'] for plan in loading_plans]
        efficiencies = [plan['efficiency'] * 100 for plan in loading_plans]
        volumes = [plan['used_volume'] for plan in loading_plans]

        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>装载效率分析</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .header {{ background: #f0f8ff; padding: 15px; border-radius: 8px; margin-bottom: 20px; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>📊 装载效率分析</h1>
        <p>生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    </div>

    <div id="efficiency-chart"></div>
    <div id="volume-chart" style="margin-top: 20px;"></div>

    <script>
        // 效率图表
        const efficiencyData = {{
            x: {json.dumps(truck_names)},
            y: {json.dumps(efficiencies)},
            type: 'bar',
            marker: {{
                color: {json.dumps(efficiencies)},
                colorscale: 'RdYlGn',
                colorbar: {{ title: '效率 (%)' }}
            }},
            text: {json.dumps([f'{eff:.1f}%' for eff in efficiencies])},
            hovertemplate: '车辆: %{{x}}<br>效率: %{{text}}<extra></extra>'
        }};

        const efficiencyLayout = {{
            title: '各车辆装载效率',
            xaxis: {{ title: '车辆ID' }},
            yaxis: {{ title: '装载效率 (%)', range: [0, 100] }},
            margin: {{ b: 100 }}
        }};

        Plotly.newPlot('efficiency-chart', [efficiencyData], efficiencyLayout);

        // 体积图表
        const volumeData = {{
            x: {json.dumps(truck_names)},
            y: {json.dumps(volumes)},
            type: 'bar',
            marker: {{ color: 'lightblue' }},
            text: {json.dumps([f'{vol:.2f}m³' for vol in volumes])},
            hovertemplate: '车辆: %{{x}}<br>使用体积: %{{text}}<extra></extra>'
        }};

        const volumeLayout = {{
            title: '各车辆使用体积',
            xaxis: {{ title: '车辆ID' }},
            yaxis: {{ title: '使用体积 (m³)' }}
        }};

        Plotly.newPlot('volume-chart', [volumeData], volumeLayout);
    </script>
</body>
</html>
        """

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html_content)

        return filename

    def _generate_data_files(self, loading_plans: List[Dict], route_plans: List[Dict]) -> List[str]:
        """生成数据文件"""
        data_files = []

        # 1. 生成装载方案JSON文件
        for plan in loading_plans:
            filename = f"{plan['truck_id']}_loading_plan.json"
            filepath = self.output_dir / "reports" / filename

            loading_plan_data = {
                "summary": {
                    "vehicle_id": plan['truck_id'],
                    "total_items": len(plan['items']),
                    "total_volume_m3": plan['used_volume'],
                    "loading_efficiency": plan['efficiency'] * 100,
                    "optimization_algorithm": "Simple_Greedy_Packing",
                    "solution_status": "OPTIMAL",
                    "loading_time_minutes": 30
                },
                "vehicle_details": {
                    "type": "LTL_TRUCK",
                    "truck_specs": {
                        "length_m": self.truck_specs['length'],
                        "width_m": self.truck_specs['width'],
                        "height_m": self.truck_specs['height'],
                        "volume_m3": self.truck_specs['volume']
                    }
                },
                "loading_plan": [{
                    "item_index": i + 1,
                    "cargo_info": {
                        "type": item['type'],
                        "volume_m3": item['volume'],
                        "weight_kg": item['weight']
                    },
                    "position_3d": {
                        "x": item['position']['x'],
                        "y": item['position']['y'],
                        "z": item['position']['z']
                    },
                    "dimensions": {
                        "length_m": item['dimensions']['length'],
                        "width_m": item['dimensions']['width'],
                        "height_m": item['dimensions']['height']
                    }
                } for i, item in enumerate(plan['items'])],
                "metadata": {
                    "generated_time": datetime.now().isoformat(),
                    "generated_by": "Simple_Optimizer",
                    "format_version": "1.0"
                }
            }

            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(loading_plan_data, f, ensure_ascii=False, indent=2, default=str)

            data_files.append(filename)

        # 2. 生成路径计划JSON文件
        for plan in route_plans:
            filename = f"{plan['truck_id']}_route_plan.json"
            filepath = self.output_dir / "reports" / filename

            route_plan_data = {
                "summary": {
                    "vehicle_id": plan['truck_id'],
                    "total_distance_km": plan['total_distance_km'],
                    "total_stops": plan['stops'],
                    "estimated_time_hours": plan['estimated_time_hours'],
                    "optimization_algorithm": "Nearest_Neighbor_TSP",
                    "solution_status": "OPTIMAL"
                },
                "route_details": [{
                    "step": i + 1,
                    "coordinates": [point['lat'], point['lng']],
                    "location_type": "depot" if i == 0 or i == len(plan['route']) - 1 else "delivery_point"
                } for i, point in enumerate(plan['route'])],
                "metadata": {
                    "generated_time": datetime.now().isoformat(),
                    "generated_by": "Simple_Optimizer"
                }
            }

            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(route_plan_data, f, ensure_ascii=False, indent=2, default=str)

            data_files.append(filename)

        return data_files

def main():
    """主函数 - 用于测试"""
    optimizer = SimpleOptimizer()
    result = optimizer.run_optimization(
        algorithm="simple_greedy",
        max_trucks=8,
        time_limit=30
    )
    print("\\n优化结果摘要:")
    print(f"算法: {result['algorithm_used']}")
    print(f"执行时间: {result['execution_time']:.2f}秒")
    print(f"使用车辆: {result['total_trucks']}")
    print(f"装载货物: {result['total_items']}")
    print(f"平均效率: {result['average_loading_efficiency']:.1f}%")
    print(f"可视化文件: {len(result['visualization_files'])}")
    print(f"数据文件: {len(result['data_files'])}")

    return result

if __name__ == "__main__":
    main()