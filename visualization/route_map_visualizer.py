"""
路径地图可视化器 - 基于真实GPS坐标的路径地图
Route Map Visualizer using Real GPS Coordinates with Folium
"""

import folium
import json
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import logging
from datetime import datetime

from .json_data_processor import JsonDataProcessor

class RouteMapVisualizer:
    """路径地图可视化器"""

    def __init__(self, output_dir: str = "A:\\MYpython\\物流\\output\\visualizations"):
        """初始化路径地图可视化器"""
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.json_processor = JsonDataProcessor()
        self.logger = self._setup_logger()

        # 成都地区中心坐标
        self.center_coords = [30.800835, 104.139111]

    def _setup_logger(self):
        """设置日志记录器"""
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.INFO)
        return logger

    def create_route_map_from_json(self, route_json_path: Path) -> Optional[str]:
        """
        基于真实GPS坐标创建路径地图

        Args:
            route_json_path: 路径计划JSON文件路径

        Returns:
            str: 生成的HTML地图文件路径
        """
        try:
            # 加载路径数据
            route_data = self.json_processor.load_route_plan(route_json_path)
            if not route_data:
                return None

            vehicle_id = route_data['summary']['vehicle_id']

            # 创建地图中心点
            center_coords = self._calculate_map_center(route_data)
            m = folium.Map(location=center_coords, zoom_start=11,
                          tiles='OpenStreetMap',
                          attr='Map data &copy; OpenStreetMap contributors')

            # 添加配送中心标记
            self._add_depot_marker(m, route_data)

            # 添加路径和停靠点
            route_coords = self._add_route_and_stops(m, route_data)

            # 绘制路径线
            if len(route_coords) > 1:
                folium.PolyLine(
                    route_coords,
                    color='red',
                    weight=4,
                    opacity=0.8,
                    popup=f'{vehicle_id} 路径'
                ).add_to(m)

            # 添加路径信息面板
            self._add_route_info_panel(m, route_data)

            # 保存HTML文件
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"route_map_{vehicle_id}_{timestamp}.html"
            filepath = self.output_dir / filename
            m.save(str(filepath))

            self.logger.info(f"路径地图已生成: {filename}")
            return str(filepath)

        except Exception as e:
            self.logger.error(f"生成路径地图失败 {route_json_path}: {str(e)}")
            return None

    def generate_all_route_maps(self) -> List[str]:
        """
        生成所有路径地图HTML文件

        Returns:
            List[str]: 生成的HTML文件路径列表
        """
        html_files = []
        json_files = self.json_processor.scan_json_files()

        self.logger.info(f"开始生成 {len(json_files['route_plans'])} 个路径地图...")

        for route_json in json_files['route_plans']:
            html_path = self.create_route_map_from_json(route_json)
            if html_path:
                html_files.append(html_path)

        self.logger.info(f"路径地图生成完成: {len(html_files)} 个HTML文件")
        return html_files

    def _calculate_map_center(self, route_data: Dict) -> List[float]:
        """
        计算地图中心点坐标

        Args:
            route_data: 路径数据

        Returns:
            List[float]: [纬度, 经度]
        """
        try:
            depot_coords = route_data['route_details']['depot_info']['coordinates']
            itinerary = route_data.get('itinerary', [])

            if not itinerary:
                return [depot_coords['lat'], depot_coords['lng']]

            # 收集所有坐标点
            all_lats = [depot_coords['lat']]
            all_lngs = [depot_coords['lng']]

            for step in itinerary:
                coords = step.get('coordinates', [])
                if len(coords) >= 2:
                    all_lats.append(coords[0])  # 纬度
                    all_lngs.append(coords[1])  # 经度

            # 计算中心点
            center_lat = sum(all_lats) / len(all_lats)
            center_lng = sum(all_lngs) / len(all_lngs)

            return [center_lat, center_lng]

        except Exception as e:
            self.logger.warning(f"计算地图中心失败，使用默认坐标: {str(e)}")
            return self.center_coords

    def _add_depot_marker(self, m: folium.Map, route_data: Dict):
        """添加配送中心标记"""
        try:
            depot_info = route_data['route_details']['depot_info']
            depot_coords = depot_info['coordinates']

            folium.Marker(
                [depot_coords['lat'], depot_coords['lng']],
                popup=f"<b>{depot_info['name']}</b><br>配送中心<br>{depot_info.get('address', '')}",
                tooltip="配送中心",
                icon=folium.Icon(color='red', icon='home', prefix='fa')
            ).add_to(m)

        except Exception as e:
            self.logger.warning(f"添加配送中心标记失败: {str(e)}")

    def _add_route_and_stops(self, m: folium.Map, route_data: Dict) -> List[List[float]]:
        """
        添加路径和停靠点标记

        Args:
            m: folium地图对象
            route_data: 路径数据

        Returns:
            List: 路径坐标列表
        """
        try:
            depot_coords = route_data['route_details']['depot_info']['coordinates']
            itinerary = route_data.get('itinerary', [])
            vehicle_id = route_data['summary']['vehicle_id']

            # 路径坐标列表，从配送中心开始
            route_coords = [[depot_coords['lat'], depot_coords['lng']]]

            for i, step in enumerate(itinerary):
                coords = step.get('coordinates', [])
                if len(coords) < 2:
                    continue

                lat, lng = coords[0], coords[1]
                route_coords.append([lat, lng])

                # 确定图标颜色和类型
                action = step.get('action', '未知')
                if action == '取货':
                    color = 'green'
                    icon = 'arrow-up'
                elif action == '送货':
                    color = 'blue'
                    icon = 'arrow-down'
                else:
                    color = 'orange'
                    icon = 'info-sign'

                # 创建详细的弹出信息
                popup_html = self._create_stop_popup_html(step, i + 1, vehicle_id)

                folium.Marker(
                    [lat, lng],
                    popup=folium.Popup(popup_html, max_width=300),
                    tooltip=f"停靠点 {i + 1}: {action}",
                    icon=folium.Icon(color=color, icon=icon, prefix='fa')
                ).add_to(m)

            # 返回配送中心
            route_coords.append([depot_coords['lat'], depot_coords['lng']])

            return route_coords

        except Exception as e:
            self.logger.warning(f"添加路径和停靠点失败: {str(e)}")
            return []

    def _create_stop_popup_html(self, step: Dict, step_num: int, vehicle_id: str) -> str:
        """创建停靠点弹出信息HTML"""
        try:
            action = step.get('action', '未知')
            order_id = step.get('order_id', '未知')
            arrival_time = step.get('estimated_arrival', '未知')
            departure_time = step.get('departure_time', '未知')
            service_time = step.get('service_time_minutes', 0)
            weight_change = step.get('weight_change_kg', 0)
            distance = step.get('distance_from_previous_km', 0)

            cargo_info = step.get('cargo_info', {})
            cargo_type = cargo_info.get('type', '未知')
            cargo_quantity = cargo_info.get('quantity', 0)

            html = f"""
            <div style="font-family: Arial, sans-serif;">
                <h4 style="margin: 0; color: #333;">停靠点 {step_num}</h4>
                <hr style="margin: 5px 0;">
                <p><b>车辆:</b> {vehicle_id}</p>
                <p><b>操作:</b> {action}</p>
                <p><b>订单:</b> {order_id}</p>
                <p><b>货物类型:</b> {cargo_type}</p>
                <p><b>货物数量:</b> {cargo_quantity}</p>
                <p><b>重量变化:</b> {weight_change:.1f} kg</p>
                <p><b>距离:</b> {distance:.1f} km</p>
                <p><b>到达时间:</b> {arrival_time}</p>
                <p><b>服务时间:</b> {service_time} 分钟</p>
                <p><b>离开时间:</b> {departure_time}</p>
            </div>
            """
            return html

        except Exception as e:
            self.logger.warning(f"创建弹出信息失败: {str(e)}")
            return f"<b>停靠点 {step_num}</b><br>{step.get('action', '未知')}"

    def _add_route_info_panel(self, m: folium.Map, route_data: Dict):
        """添加路径信息面板"""
        try:
            summary = route_data['summary']
            vehicle_id = summary['vehicle_id']
            total_distance = summary.get('total_distance_km', 0)
            total_duration = summary.get('total_duration_hours', 0)
            fuel_cost = summary.get('fuel_cost_yuan', 0)
            total_stops = summary.get('total_stops', 0)

            info_html = f"""
            <div style="
                position: fixed;
                top: 10px;
                right: 10px;
                width: 250px;
                background: white;
                border: 2px solid #ccc;
                border-radius: 5px;
                padding: 10px;
                font-family: Arial, sans-serif;
                z-index: 9999;
                box-shadow: 0 0 10px rgba(0,0,0,0.3);
            ">
                <h4 style="margin: 0; color: #333; text-align: center;">{vehicle_id} 路径信息</h4>
                <hr style="margin: 5px 0;">
                <p><b>总距离:</b> {total_distance:.1f} km</p>
                <p><b>总时间:</b> {total_duration:.1f} 小时</p>
                <p><b>燃油成本:</b> ¥{fuel_cost:.0f}</p>
                <p><b>停靠点:</b> {total_stops} 个</p>
                <p style="font-size: 10px; color: #666; margin: 5px 0 0 0;">
                    🔴 配送中心 🟢 取货点 🔵 送货点
                </p>
            </div>
            """

            # 将信息面板添加到地图
            folium.Element(info_html).add_to(m.get_root().html)

        except Exception as e:
            self.logger.warning(f"添加路径信息面板失败: {str(e)}")

    def create_combined_route_overview_map(self) -> Optional[str]:
        """
        创建所有路径的综合概览地图

        Returns:
            str: 生成的HTML文件路径
        """
        try:
            json_files = self.json_processor.scan_json_files()

            if not json_files['route_plans']:
                self.logger.warning("没有找到路径计划文件")
                return None

            # 创建概览地图
            m = folium.Map(location=self.center_coords, zoom_start=10)

            colors = ['red', 'blue', 'green', 'purple', 'orange', 'darkred',
                     'lightred', 'beige', 'darkblue', 'darkgreen', 'cadetblue',
                     'darkpurple', 'white', 'pink', 'lightblue', 'lightgreen']

            for i, route_json in enumerate(json_files['route_plans']):
                route_data = self.json_processor.load_route_plan(route_json)
                if not route_data:
                    continue

                color = colors[i % len(colors)]
                vehicle_id = route_data['summary']['vehicle_id']

                # 添加简化的路径线
                route_coords = self._get_simplified_route_coords(route_data)
                if len(route_coords) > 1:
                    folium.PolyLine(
                        route_coords,
                        color=color,
                        weight=3,
                        opacity=0.7,
                        popup=f'{vehicle_id} 路径'
                    ).add_to(m)

            # 添加图例
            self._add_overview_legend(m, json_files['route_plans'])

            # 保存文件
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"route_overview_all_vehicles_{timestamp}.html"
            filepath = self.output_dir / filename
            m.save(str(filepath))

            self.logger.info(f"综合路径概览地图已生成: {filename}")
            return str(filepath)

        except Exception as e:
            self.logger.error(f"生成综合路径概览地图失败: {str(e)}")
            return None

    def _get_simplified_route_coords(self, route_data: Dict) -> List[List[float]]:
        """获取简化的路径坐标"""
        try:
            depot_coords = route_data['route_details']['depot_info']['coordinates']
            itinerary = route_data.get('itinerary', [])

            coords = [[depot_coords['lat'], depot_coords['lng']]]

            for step in itinerary:
                step_coords = step.get('coordinates', [])
                if len(step_coords) >= 2:
                    coords.append([step_coords[0], step_coords[1]])

            coords.append([depot_coords['lat'], depot_coords['lng']])
            return coords

        except Exception as e:
            self.logger.warning(f"获取简化路径坐标失败: {str(e)}")
            return []

    def _add_overview_legend(self, m: folium.Map, route_files: List[Path]):
        """添加概览地图图例"""
        try:
            legend_html = """
            <div style="
                position: fixed;
                bottom: 50px;
                left: 50px;
                width: 200px;
                height: auto;
                background-color: white;
                border:2px solid grey;
                z-index:9999;
                font-size:14px;
                padding: 10px;
                border-radius: 5px;
            ">
                <h4>路径图例</h4>
                <p><i class="fa fa-minus" style="color:red"></i> 车辆路径</p>
                <p>总计: """ + str(len(route_files)) + """ 辆车</p>
            </div>
            """

            folium.Element(legend_html).add_to(m.get_root().html)

        except Exception as e:
            self.logger.warning(f"添加概览图例失败: {str(e)}")