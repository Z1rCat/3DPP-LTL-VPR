"""
路径可视化模块
Route Visualization Module
"""

import json
import folium
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import logging
from datetime import datetime


class RouteVisualizer:
    """路径可视化器"""

    def __init__(self, output_dir: str = "output/visualizations"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.logger = self._setup_logger()

        # 配色方案
        self.colors = [
            '#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7',
            '#DDA0DD', '#98D8C8', '#F7DC6F', '#BB8FCE', '#85C1E9',
            '#F8C471', '#82E0AA', '#F1948A', '#85C1E9', '#F4D03F'
        ]

        # 图标样式
        self.depot_icon = folium.Icon(color='red', icon='home', prefix='fa')
        self.pickup_icon = folium.Icon(color='green', icon='arrow-up', prefix='fa')
        self.delivery_icon = folium.Icon(color='blue', icon='arrow-down', prefix='fa')

    def _setup_logger(self):
        """设置日志记录器"""
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.INFO)
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        return logger

    def visualize_single_route(self, route_data: Dict, save_path: Optional[str] = None) -> str:
        """可视化单条路径"""
        try:
            vehicle_id = route_data.get('vehicle_id', 'Unknown')

            if not route_data.get('route_sequence'):
                self.logger.warning(f"车辆 {vehicle_id} 没有路径序列")
                return None

            # 创建地图
            center_lat, center_lon = self._calculate_route_center(route_data)
            m = folium.Map(
                location=[center_lat, center_lon],
                zoom_start=10,
                tiles='OpenStreetMap'
            )

            # 添加图例
            self._add_legend(m)

            # 添加配送中心
            depot_coords = route_data.get('depot_coordinates', [104.139111, 30.800835])
            folium.Marker(
                depot_coords,
                popup=f"配送中心 A网点<br>坐标: {depot_coords}",
                tooltip="配送中心",
                icon=self.depot_icon
            ).add_to(m)

            # 添加路径点和连线
            route_coordinates = [depot_coords]  # 从配送中心开始

            for i, stop in enumerate(route_data['route_sequence']):
                coords = [stop['latitude'], stop['longitude']]
                route_coordinates.append(coords)

                # 确定图标类型
                icon = self.pickup_icon if stop['type'] == 'pickup' else self.delivery_icon

                # 添加标记
                popup_text = f"""
                <b>站点 {i+1}: {stop['type'].upper()}</b><br>
                订单ID: {stop['order_id']}<br>
                坐标: ({stop['latitude']:.6f}, {stop['longitude']:.6f})<br>
                重量: {stop['weight_kg']}kg<br>
                到达时间: {stop.get('arrival_time', 'N/A')}<br>
                行驶距离: {stop.get('travel_distance_km', 0):.2f}km
                """

                folium.Marker(
                    coords,
                    popup=popup_text,
                    tooltip=f"{stop['type'].upper()} - 订单{stop['order_id']}",
                    icon=icon
                ).add_to(m)

            # 返回配送中心
            route_coordinates.append(depot_coords)

            # 绘制路径线
            folium.PolyLine(
                route_coordinates,
                color='red',
                weight=3,
                opacity=0.8,
                popup=f"车辆 {vehicle_id} 路径"
            ).add_to(m)

            # 添加路径信息面板
            self._add_route_info_panel(m, route_data)

            # 保存地图
            if not save_path:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                save_path = self.output_dir / f"route_{vehicle_id}_{timestamp}.html"

            m.save(str(save_path))
            self.logger.info(f"路径可视化已保存: {save_path}")

            return str(save_path)

        except Exception as e:
            self.logger.error(f"单条路径可视化失败: {e}")
            return None

    def visualize_all_routes(self, routes_data: List[Dict], save_path: Optional[str] = None) -> str:
        """可视化所有路径总览"""
        try:
            if not routes_data:
                self.logger.warning("没有路径数据需要可视化")
                return None

            # 计算地图中心
            center_lat, center_lon = self._calculate_all_routes_center(routes_data)
            m = folium.Map(
                location=[center_lat, center_lon],
                zoom_start=9,
                tiles='OpenStreetMap'
            )

            # 添加图例
            self._add_legend(m)

            # 添加配送中心
            depot_coords = [104.139111, 30.800835]
            folium.Marker(
                depot_coords,
                popup="配送中心 A网点",
                tooltip="配送中心",
                icon=self.depot_icon
            ).add_to(m)

            # 为每个路径使用不同颜色
            for route_idx, route_data in enumerate(routes_data):
                if not route_data.get('route_sequence'):
                    continue

                vehicle_id = route_data.get('vehicle_id', f'Vehicle_{route_idx}')
                color = self.colors[route_idx % len(self.colors)]

                # 构建路径坐标
                route_coordinates = [depot_coords]

                for stop in route_data['route_sequence']:
                    coords = [stop['latitude'], stop['longitude']]
                    route_coordinates.append(coords)

                    # 添加简化的标记
                    icon_color = 'green' if stop['type'] == 'pickup' else 'blue'
                    folium.CircleMarker(
                        coords,
                        radius=3,
                        popup=f"车辆{vehicle_id} - {stop['type']} - 订单{stop['order_id']}",
                        color=color,
                        fill=True,
                        fillColor=color
                    ).add_to(m)

                route_coordinates.append(depot_coords)

                # 绘制路径线
                folium.PolyLine(
                    route_coordinates,
                    color=color,
                    weight=2,
                    opacity=0.7,
                    popup=f"车辆 {vehicle_id}"
                ).add_to(m)

            # 添加总览信息面板
            self._add_overview_info_panel(m, routes_data)

            # 保存地图
            if not save_path:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                save_path = self.output_dir / f"routes_overview_{timestamp}.html"

            m.save(str(save_path))
            self.logger.info(f"路径总览可视化已保存: {save_path}")

            return str(save_path)

        except Exception as e:
            self.logger.error(f"总览路径可视化失败: {e}")
            return None

    def visualize_from_json_files(self, json_dir: str = "output/reports") -> Dict[str, str]:
        """从JSON文件批量生成可视化"""
        results = {}
        json_path = Path(json_dir)

        try:
            # 查找所有路径计划JSON文件
            route_files = list(json_path.glob("*_route_plan.json"))

            if not route_files:
                self.logger.warning(f"在 {json_dir} 中没有找到路径计划文件")
                return results

            all_routes = []

            # 处理每个路径文件
            for route_file in route_files:
                try:
                    with open(route_file, 'r', encoding='utf-8') as f:
                        route_data = json.load(f)

                    # 单独可视化每条路径
                    single_path = self.visualize_single_route(route_data)
                    if single_path:
                        results[route_file.stem] = single_path

                    # 收集用于总览
                    all_routes.append(route_data)

                except Exception as e:
                    self.logger.error(f"处理文件 {route_file} 失败: {e}")

            # 生成总览可视化
            if all_routes:
                overview_path = self.visualize_all_routes(all_routes)
                if overview_path:
                    results['overview'] = overview_path

            self.logger.info(f"批量可视化完成，生成了 {len(results)} 个可视化文件")
            return results

        except Exception as e:
            self.logger.error(f"批量可视化失败: {e}")
            return results

    def _calculate_route_center(self, route_data: Dict) -> Tuple[float, float]:
        """计算单条路径的地图中心"""
        if not route_data.get('route_sequence'):
            return 104.139111, 30.800835  # 默认配送中心坐标

        lats = [stop['latitude'] for stop in route_data['route_sequence']]
        lons = [stop['longitude'] for stop in route_data['route_sequence']]

        # 包含配送中心
        lats.append(30.800835)
        lons.append(104.139111)

        return sum(lats) / len(lats), sum(lons) / len(lons)

    def _calculate_all_routes_center(self, routes_data: List[Dict]) -> Tuple[float, float]:
        """计算所有路径的地图中心"""
        all_lats, all_lons = [], []

        for route_data in routes_data:
            if route_data.get('route_sequence'):
                all_lats.extend([stop['latitude'] for stop in route_data['route_sequence']])
                all_lons.extend([stop['longitude'] for stop in route_data['route_sequence']])

        if not all_lats:
            return 104.139111, 30.800835

        # 包含配送中心
        all_lats.append(30.800835)
        all_lons.append(104.139111)

        return sum(all_lats) / len(all_lats), sum(all_lons) / len(all_lons)

    def _add_legend(self, map_obj):
        """添加图例"""
        legend_html = '''
        <div style="position: fixed;
                    bottom: 50px; left: 50px; width: 150px; height: 90px;
                    border:2px solid grey; z-index:9999; font-size:14px;
                    background-color:white; opacity: 0.9;
                    ">
        <p style="margin: 5px;"><b>图例</b></p>
        <p style="margin: 5px;"><i class="fa fa-home" style="color:red"></i> 配送中心</p>
        <p style="margin: 5px;"><i class="fa fa-arrow-up" style="color:green"></i> 取货点</p>
        <p style="margin: 5px;"><i class="fa fa-arrow-down" style="color:blue"></i> 送货点</p>
        </div>
        '''
        map_obj.get_root().html.add_child(folium.Element(legend_html))

    def _add_route_info_panel(self, map_obj, route_data: Dict):
        """添加路径信息面板"""
        vehicle_info = route_data.get('vehicle_info', {})
        summary = route_data.get('summary', {})

        info_html = f'''
        <div style="position: fixed;
                    top: 10px; right: 10px; width: 250px;
                    border:2px solid grey; z-index:9999; font-size:12px;
                    background-color:white; opacity: 0.95; padding: 10px;
                    ">
        <h4>车辆信息</h4>
        <p><b>车辆ID:</b> {route_data.get('vehicle_id', 'N/A')}</p>
        <p><b>车辆类型:</b> {vehicle_info.get('type', 'N/A')}</p>
        <p><b>载重:</b> {vehicle_info.get('payload_kg', 0):.1f}kg</p>
        <p><b>总距离:</b> {summary.get('total_distance_km', 0):.2f}km</p>
        <p><b>总时间:</b> {summary.get('total_time_hours', 0):.2f}小时</p>
        <p><b>燃料成本:</b> ¥{summary.get('fuel_cost', 0):.2f}</p>
        <p><b>订单数量:</b> {summary.get('total_orders', 0)}</p>
        </div>
        '''
        map_obj.get_root().html.add_child(folium.Element(info_html))

    def _add_overview_info_panel(self, map_obj, routes_data: List[Dict]):
        """添加总览信息面板"""
        total_vehicles = len(routes_data)
        total_distance = sum(route.get('summary', {}).get('total_distance_km', 0) for route in routes_data)
        total_orders = sum(route.get('summary', {}).get('total_orders', 0) for route in routes_data)
        total_cost = sum(route.get('summary', {}).get('fuel_cost', 0) for route in routes_data)

        info_html = f'''
        <div style="position: fixed;
                    top: 10px; right: 10px; width: 200px;
                    border:2px solid grey; z-index:9999; font-size:12px;
                    background-color:white; opacity: 0.95; padding: 10px;
                    ">
        <h4>路径总览</h4>
        <p><b>车辆总数:</b> {total_vehicles}</p>
        <p><b>总距离:</b> {total_distance:.2f}km</p>
        <p><b>总订单:</b> {total_orders}</p>
        <p><b>总成本:</b> ¥{total_cost:.2f}</p>
        </div>
        '''
        map_obj.get_root().html.add_child(folium.Element(info_html))


def test_route_visualizer():
    """测试路径可视化功能"""
    print("=== 路径可视化测试 ===")

    visualizer = RouteVisualizer()

    # 测试从JSON文件生成可视化
    results = visualizer.visualize_from_json_files()

    if results:
        print(f"成功生成 {len(results)} 个可视化文件:")
        for name, path in results.items():
            print(f"  {name}: {path}")
    else:
        print("没有生成可视化文件")

    return True


    def create_enhanced_route_optimization_visualization(self, route_solutions: Dict) -> str:
        """
        创建增强版路径优化结果可视化
        展示详细的路径优化分析和对比

        Args:
            route_solutions: 路径解决方案字典

        Returns:
            str: 保存的可视化文件路径
        """
        try:
            if not route_solutions:
                self.logger.warning("没有路径数据需要可视化")
                return None

            # 计算地图中心
            all_coordinates = []
            depot_coord = [104.139111, 30.800835]  # A网点坐标
            all_coordinates.append(depot_coord)

            # 收集所有停靠点坐标
            for route_data in route_solutions.values():
                if route_data.get('route_sequence'):
                    for stop in route_data['route_sequence']:
                        all_coordinates.append([stop['longitude'], stop['latitude']])

            if not all_coordinates:
                return None

            # 计算地图中心点
            center_lat = sum(coord[1] for coord in all_coordinates) / len(all_coordinates)
            center_lng = sum(coord[0] for coord in all_coordinates) / len(all_coordinates)

            # 创建地图
            m = folium.Map(
                location=[center_lat, center_lng],
                zoom_start=10,
                tiles='OpenStreetMap'
            )

            # 添加增强图例
            self._add_enhanced_legend(m)

            # 添加配送中心标记
            folium.Marker(
                [depot_coord[1], depot_coord[0]],
                popup=self._create_depot_popup(route_solutions),
                tooltip="A网点配送中心",
                icon=folium.Icon(color='red', icon='home', prefix='fa')
            ).add_to(m)

            # 为每个路径使用不同颜色并添加详细信息
            route_stats = []
            for route_idx, (vehicle_id, route_data) in enumerate(route_solutions.items()):
                if not route_data.get('route_sequence'):
                    continue

                color = self.colors[route_idx % len(self.colors)]
                route_info = self._process_enhanced_route(route_data, color, m)
                route_stats.append(route_info)

            # 添加路径统计面板
            self._add_route_statistics_panel(m, route_stats)

            # 添加路径对比分析
            self._add_route_comparison_charts(m, route_stats)

            # 保存增强版可视化
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            save_path = self.output_dir / f"enhanced_route_optimization_{timestamp}.html"

            m.save(str(save_path))
            self.logger.info(f"增强版路径优化可视化已保存: {save_path}")

            return str(save_path)

        except Exception as e:
            self.logger.error(f"增强版路径可视化失败: {e}")
            return None

    def create_route_efficiency_heatmap(self, route_solutions: Dict) -> str:
        """
        创建路径效率热力图
        展示不同区域的配送效率

        Args:
            route_solutions: 路径解决方案字典

        Returns:
            str: 保存的热力图文件路径
        """
        try:
            # 收集所有停靠点数据
            stop_data = []
            for vehicle_id, route_data in route_solutions.items():
                if not route_data.get('route_sequence'):
                    continue

                for stop in route_data['route_sequence']:
                    stop_data.append({
                        'lat': stop['latitude'],
                        'lng': stop['longitude'],
                        'weight': stop.get('weight_kg', 1),
                        'service_time': stop.get('service_time_minutes', 30),
                        'vehicle_id': vehicle_id,
                        'type': stop['type']
                    })

            if not stop_data:
                return None

            # 计算地图中心
            center_lat = sum(stop['lat'] for stop in stop_data) / len(stop_data)
            center_lng = sum(stop['lng'] for stop in stop_data) / len(stop_data)

            # 创建热力图
            m = folium.Map(
                location=[center_lat, center_lng],
                zoom_start=11,
                tiles='OpenStreetMap'
            )

            # 准备热力图数据（基于服务时间和货物重量）
            heat_data = []
            for stop in stop_data:
                # 计算热力值（服务时间 × 货物重量）
                heat_value = stop['service_time'] * stop['weight'] / 100.0
                heat_data.append([stop['lat'], stop['lng'], heat_value])

            # 添加热力图层
            from folium.plugins import HeatMap
            HeatMap(
                heat_data,
                min_opacity=0.2,
                max_zoom=18,
                radius=15,
                blur=10,
                gradient={
                    0.0: 'blue',
                    0.3: 'cyan',
                    0.5: 'lime',
                    0.7: 'yellow',
                    1.0: 'red'
                }
            ).add_to(m)

            # 添加配送中心
            depot_coord = [104.139111, 30.800835]
            folium.Marker(
                [depot_coord[1], depot_coord[0]],
                popup="A网点配送中心",
                icon=folium.Icon(color='red', icon='home', prefix='fa')
            ).add_to(m)

            # 添加热力图说明
            self._add_heatmap_legend(m)

            # 保存热力图
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            save_path = self.output_dir / f"route_efficiency_heatmap_{timestamp}.html"

            m.save(str(save_path))
            self.logger.info(f"路径效率热力图已保存: {save_path}")

            return str(save_path)

        except Exception as e:
            self.logger.error(f"创建路径效率热力图失败: {e}")
            return None

    def create_vehicle_performance_dashboard(self, route_solutions: Dict) -> str:
        """
        创建车辆性能仪表板
        展示各车辆的关键性能指标

        Args:
            route_solutions: 路径解决方案字典

        Returns:
            str: 保存的仪表板文件路径
        """
        try:
            # 分析车辆性能数据
            vehicle_metrics = []
            for vehicle_id, route_data in route_solutions.items():
                summary = route_data.get('summary', {})

                metrics = {
                    'vehicle_id': vehicle_id,
                    'total_distance': summary.get('total_distance_km', 0),
                    'total_time': summary.get('total_duration_hours', 0),
                    'fuel_cost': summary.get('fuel_cost_yuan', 0),
                    'stops_count': summary.get('total_stops', 0),
                    'pickup_stops': summary.get('pickup_stops', 0),
                    'delivery_stops': summary.get('delivery_stops', 0),
                    'load_efficiency': summary.get('load_efficiency', 0),
                    'avg_speed': summary.get('total_distance_km', 0) / summary.get('total_duration_hours', 1) if summary.get('total_duration_hours', 0) > 0 else 0
                }
                vehicle_metrics.append(metrics)

            if not vehicle_metrics:
                return None

            # 计算地图中心
            depot_coord = [104.139111, 30.800835]
            m = folium.Map(
                location=[depot_coord[1], depot_coord[0]],
                zoom_start=10,
                tiles='OpenStreetMap'
            )

            # 添加配送中心
            folium.Marker(
                [depot_coord[1], depot_coord[0]],
                popup="A网点配送中心",
                icon=folium.Icon(color='red', icon='home', prefix='fa')
            ).add_to(m)

            # 添加车辆性能圆圈标记
            for i, metrics in enumerate(vehicle_metrics):
                # 根据效率确定圆圈大小和颜色
                efficiency = metrics['load_efficiency']
                radius = max(100, efficiency * 10)  # 基于效率的半径

                if efficiency >= 80:
                    color = 'green'
                elif efficiency >= 60:
                    color = 'yellow'
                else:
                    color = 'red'

                # 在配送中心周围分布车辆标记
                angle = (2 * 3.14159 * i) / len(vehicle_metrics)
                offset_lat = 0.01 * (i % 3 + 1) * np.cos(angle)
                offset_lng = 0.01 * (i % 3 + 1) * np.sin(angle)

                folium.CircleMarker(
                    [depot_coord[1] + offset_lat, depot_coord[0] + offset_lng],
                    radius=max(8, efficiency / 10),
                    popup=self._create_vehicle_performance_popup(metrics),
                    tooltip=f"{metrics['vehicle_id']}: {efficiency:.1f}%效率",
                    color='black',
                    fillColor=color,
                    fillOpacity=0.7
                ).add_to(m)

            # 添加性能仪表板面板
            self._add_performance_dashboard_panel(m, vehicle_metrics)

            # 保存仪表板
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            save_path = self.output_dir / f"vehicle_performance_dashboard_{timestamp}.html"

            m.save(str(save_path))
            self.logger.info(f"车辆性能仪表板已保存: {save_path}")

            return str(save_path)

        except Exception as e:
            self.logger.error(f"创建车辆性能仪表板失败: {e}")
            return None

    def create_comprehensive_route_analysis(self, route_solutions: Dict) -> List[str]:
        """
        创建综合路径分析报告
        生成多个不同角度的路径分析可视化

        Args:
            route_solutions: 路径解决方案字典

        Returns:
            List[str]: 生成的所有可视化文件路径列表
        """
        generated_files = []

        try:
            # 1. 增强版路径优化可视化
            enhanced_route_file = self.create_enhanced_route_optimization_visualization(route_solutions)
            if enhanced_route_file:
                generated_files.append(enhanced_route_file)

            # 2. 路径效率热力图
            heatmap_file = self.create_route_efficiency_heatmap(route_solutions)
            if heatmap_file:
                generated_files.append(heatmap_file)

            # 3. 车辆性能仪表板
            dashboard_file = self.create_vehicle_performance_dashboard(route_solutions)
            if dashboard_file:
                generated_files.append(dashboard_file)

            # 4. 原有的总览可视化
            overview_file = self.visualize_all_routes(list(route_solutions.values()))
            if overview_file:
                generated_files.append(overview_file)

            self.logger.info(f"综合路径分析完成，生成 {len(generated_files)} 个可视化文件")

        except Exception as e:
            self.logger.error(f"综合路径分析失败: {e}")

        return generated_files

    def _create_depot_popup(self, route_solutions: Dict) -> str:
        """创建配送中心弹出窗口"""
        total_routes = len(route_solutions)
        total_distance = sum(route.get('summary', {}).get('total_distance_km', 0) for route in route_solutions.values())
        total_cost = sum(route.get('summary', {}).get('fuel_cost_yuan', 0) for route in route_solutions.values())
        total_stops = sum(route.get('summary', {}).get('total_stops', 0) for route in route_solutions.values())

        return f"""
        <div style="width: 300px;">
        <h4 style="margin-bottom: 10px;">🏢 A网点配送中心</h4>
        <hr>
        <b>运营统计：</b><br>
        📊 调度车辆：{total_routes} 辆<br>
        📏 总行驶距离：{total_distance:.1f} km<br>
        💰 总燃油成本：¥{total_cost:.2f}<br>
        📍 总停靠点：{total_stops} 个<br>
        <hr>
        <small>点击地图上的路径查看详细信息</small>
        </div>
        """

    def _process_enhanced_route(self, route_data: Dict, color: str, map_obj) -> Dict:
        """处理增强版路径数据"""
        vehicle_id = route_data.get('vehicle_id', 'Unknown')
        summary = route_data.get('summary', {})
        route_sequence = route_data.get('route_sequence', [])

        # 构建路径坐标
        depot_coord = [104.139111, 30.800835]
        route_coordinates = [[depot_coord[1], depot_coord[0]]]  # 从配送中心开始

        for stop in route_sequence:
            coords = [stop['latitude'], stop['longitude']]
            route_coordinates.append(coords)

            # 添加增强的停靠点标记
            icon_color = 'green' if stop['type'] == 'pickup' else 'blue'
            popup_content = self._create_enhanced_stop_popup(stop, vehicle_id)

            folium.CircleMarker(
                coords,
                radius=6,
                popup=popup_content,
                tooltip=f"{vehicle_id} - {stop['type']}",
                color='white',
                fillColor=color,
                fillOpacity=0.8,
                weight=2
            ).add_to(map_obj)

        # 返回配送中心
        route_coordinates.append([depot_coord[1], depot_coord[0]])

        # 绘制增强的路径线
        folium.PolyLine(
            route_coordinates,
            color=color,
            weight=4,
            opacity=0.8,
            popup=self._create_route_popup(route_data)
        ).add_to(map_obj)

        return {
            'vehicle_id': vehicle_id,
            'distance': summary.get('total_distance_km', 0),
            'time': summary.get('total_duration_hours', 0),
            'cost': summary.get('fuel_cost_yuan', 0),
            'stops': len(route_sequence),
            'efficiency': summary.get('load_efficiency', 0),
            'color': color
        }

    def _create_enhanced_stop_popup(self, stop: Dict, vehicle_id: str) -> str:
        """创建增强的停靠点弹出窗口"""
        return f"""
        <div style="width: 250px;">
        <h5 style="color: #2E86AB; margin-bottom: 8px;">
            {'📦 取货点' if stop['type'] == 'pickup' else '🚚 送货点'}
        </h5>
        <table style="width: 100%; font-size: 12px;">
        <tr><td><b>车辆ID:</b></td><td>{vehicle_id}</td></tr>
        <tr><td><b>订单ID:</b></td><td>{stop['order_id']}</td></tr>
        <tr><td><b>坐标:</b></td><td>({stop['latitude']:.4f}, {stop['longitude']:.4f})</td></tr>
        <tr><td><b>货物重量:</b></td><td>{stop['weight_kg']:.1f} kg</td></tr>
        <tr><td><b>到达时间:</b></td><td>{stop.get('arrival_time', 'N/A')}</td></tr>
        <tr><td><b>行驶距离:</b></td><td>{stop.get('travel_distance_km', 0):.2f} km</td></tr>
        </table>
        </div>
        """

    def _create_route_popup(self, route_data: Dict) -> str:
        """创建路径弹出窗口"""
        summary = route_data.get('summary', {})
        vehicle_id = route_data.get('vehicle_id', 'Unknown')

        return f"""
        <div style="width: 280px;">
        <h5 style="color: #FF6B6B; margin-bottom: 8px;">🚛 {vehicle_id} 路径信息</h5>
        <table style="width: 100%; font-size: 12px;">
        <tr><td><b>总距离:</b></td><td>{summary.get('total_distance_km', 0):.1f} km</td></tr>
        <tr><td><b>总时间:</b></td><td>{summary.get('total_duration_hours', 0):.1f} 小时</td></tr>
        <tr><td><b>燃油成本:</b></td><td>¥{summary.get('fuel_cost_yuan', 0):.2f}</td></tr>
        <tr><td><b>停靠点数:</b></td><td>{summary.get('total_stops', 0)} 个</td></tr>
        <tr><td><b>取货点:</b></td><td>{summary.get('pickup_stops', 0)} 个</td></tr>
        <tr><td><b>送货点:</b></td><td>{summary.get('delivery_stops', 0)} 个</td></tr>
        <tr><td><b>装载效率:</b></td><td>{summary.get('load_efficiency', 0):.1f}%</td></tr>
        </table>
        </div>
        """

    def _create_vehicle_performance_popup(self, metrics: Dict) -> str:
        """创建车辆性能弹出窗口"""
        return f"""
        <div style="width: 260px;">
        <h5 style="color: #4ECDC4; margin-bottom: 8px;">📊 {metrics['vehicle_id']} 性能指标</h5>
        <table style="width: 100%; font-size: 12px;">
        <tr><td><b>总距离:</b></td><td>{metrics['total_distance']:.1f} km</td></tr>
        <tr><td><b>总时间:</b></td><td>{metrics['total_time']:.1f} 小时</td></tr>
        <tr><td><b>平均速度:</b></td><td>{metrics['avg_speed']:.1f} km/h</td></tr>
        <tr><td><b>燃油成本:</b></td><td>¥{metrics['fuel_cost']:.2f}</td></tr>
        <tr><td><b>停靠点数:</b></td><td>{metrics['stops_count']} 个</td></tr>
        <tr><td><b>装载效率:</b></td><td>{metrics['load_efficiency']:.1f}%</td></tr>
        </table>
        </div>
        """

    def _add_enhanced_legend(self, map_obj):
        """添加增强图例"""
        legend_html = '''
        <div style="position: fixed;
                    bottom: 50px; left: 50px; width: 200px; height: 140px;
                    border:2px solid grey; z-index:9999; font-size:12px;
                    background-color:white; opacity: 0.9; padding: 10px;
                    ">
        <h4 style="margin: 0 0 10px 0; color: #333;">📍 图例说明</h4>
        <p style="margin: 3px 0;"><i class="fa fa-home" style="color:red"></i> 配送中心</p>
        <p style="margin: 3px 0;"><span style="color:green">●</span> 取货点</p>
        <p style="margin: 3px 0;"><span style="color:blue">●</span> 送货点</p>
        <p style="margin: 3px 0;"><span style="color:#FF6B6B">━━</span> 车辆路径</p>
        <hr style="margin: 8px 0;">
        <p style="margin: 3px 0; font-size: 10px;">点击标记查看详细信息</p>
        </div>
        '''
        map_obj.get_root().html.add_child(folium.Element(legend_html))

    def _add_route_statistics_panel(self, map_obj, route_stats: List[Dict]):
        """添加路径统计面板"""
        if not route_stats:
            return

        total_distance = sum(stat['distance'] for stat in route_stats)
        total_cost = sum(stat['cost'] for stat in route_stats)
        avg_efficiency = sum(stat['efficiency'] for stat in route_stats) / len(route_stats)
        total_stops = sum(stat['stops'] for stat in route_stats)

        stats_html = f'''
        <div style="position: fixed;
                    top: 10px; right: 10px; width: 280px;
                    border:2px solid grey; z-index:9999; font-size:12px;
                    background-color:white; opacity: 0.95; padding: 10px;
                    ">
        <h4 style="margin: 0 0 10px 0; color: #2E86AB;">📊 路径优化统计</h4>
        <table style="width: 100%; font-size: 11px;">
        <tr><td><b>调度车辆:</b></td><td>{len(route_stats)} 辆</td></tr>
        <tr><td><b>总行驶距离:</b></td><td>{total_distance:.1f} km</td></tr>
        <tr><td><b>总燃油成本:</b></td><td>¥{total_cost:.2f}</td></tr>
        <tr><td><b>总停靠点:</b></td><td>{total_stops} 个</td></tr>
        <tr><td><b>平均装载率:</b></td><td>{avg_efficiency:.1f}%</td></tr>
        <tr><td><b>平均距离:</b></td><td>{total_distance/len(route_stats):.1f} km/车</td></tr>
        </table>
        </div>
        '''
        map_obj.get_root().html.add_child(folium.Element(stats_html))

    def _add_route_comparison_charts(self, map_obj, route_stats: List[Dict]):
        """添加路径对比图表"""
        # 这里可以添加更复杂的图表，目前先保持简单
        pass

    def _add_heatmap_legend(self, map_obj):
        """添加热力图图例"""
        legend_html = '''
        <div style="position: fixed;
                    bottom: 50px; right: 50px; width: 180px; height: 120px;
                    border:2px solid grey; z-index:9999; font-size:12px;
                    background-color:white; opacity: 0.9; padding: 10px;
                    ">
        <h4 style="margin: 0 0 10px 0; color: #333;">🔥 热力图说明</h4>
        <div style="font-size: 11px;">
        <p style="margin: 3px 0;"><span style="color:blue;">蓝色</span> - 低负荷区域</p>
        <p style="margin: 3px 0;"><span style="color:yellow;">黄色</span> - 中等负荷</p>
        <p style="margin: 3px 0;"><span style="color:red;">红色</span> - 高负荷区域</p>
        <hr style="margin: 8px 0;">
        <p style="margin: 3px 0; font-size: 10px;">基于服务时间×货物重量</p>
        </div>
        </div>
        '''
        map_obj.get_root().html.add_child(folium.Element(legend_html))

    def _add_performance_dashboard_panel(self, map_obj, vehicle_metrics: List[Dict]):
        """添加性能仪表板面板"""
        if not vehicle_metrics:
            return

        # 计算汇总统计
        total_vehicles = len(vehicle_metrics)
        best_efficiency = max(metric['load_efficiency'] for metric in vehicle_metrics)
        worst_efficiency = min(metric['load_efficiency'] for metric in vehicle_metrics)
        avg_distance = sum(metric['total_distance'] for metric in vehicle_metrics) / total_vehicles

        dashboard_html = f'''
        <div style="position: fixed;
                    top: 10px; left: 10px; width: 250px;
                    border:2px solid grey; z-index:9999; font-size:12px;
                    background-color:white; opacity: 0.95; padding: 10px;
                    ">
        <h4 style="margin: 0 0 10px 0; color: #4ECDC4;">🚛 车辆性能仪表板</h4>
        <table style="width: 100%; font-size: 11px;">
        <tr><td><b>车辆总数:</b></td><td>{total_vehicles} 辆</td></tr>
        <tr><td><b>最高效率:</b></td><td>{best_efficiency:.1f}%</td></tr>
        <tr><td><b>最低效率:</b></td><td>{worst_efficiency:.1f}%</td></tr>
        <tr><td><b>平均距离:</b></td><td>{avg_distance:.1f} km</td></tr>
        </table>
        <hr style="margin: 8px 0;">
        <div style="font-size: 10px;">
        <p style="margin: 2px 0;"><span style="color:green;">●</span> 高效率 (≥80%)</p>
        <p style="margin: 2px 0;"><span style="color:orange;">●</span> 中等效率 (60-79%)</p>
        <p style="margin: 2px 0;"><span style="color:red;">●</span> 低效率 (<60%)</p>
        </div>
        </div>
        '''
        map_obj.get_root().html.add_child(folium.Element(dashboard_html))


if __name__ == "__main__":
    test_route_visualizer()