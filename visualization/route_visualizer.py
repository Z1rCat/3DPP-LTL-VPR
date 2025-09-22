"""
路径可视化模块
Route Visualization Module
"""

import json
import folium
import pandas as pd
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


if __name__ == "__main__":
    test_route_visualizer()