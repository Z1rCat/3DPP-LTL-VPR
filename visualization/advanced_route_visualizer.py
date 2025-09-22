"""
高级路径可视化模块 - 专业的VRP路径优化结果可视化
Advanced Route Visualization Module - Professional VRP Route Optimization Visualization
"""

import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
import json
import time
from typing import Dict, List, Tuple, Optional, Any
from pathlib import Path
import logging
from datetime import datetime

# 导入配置
import sys
sys.path.append(str(Path(__file__).parent.parent))

# 导入真实数据加载器
from visualization.real_data_loader import RealDataLoader

# 尝试导入配置，如果失败则使用默认配置
try:
    from config import VISUALIZATIONS_DIR
except ImportError:
    VISUALIZATIONS_DIR = Path(__file__).parent.parent / "output" / "visualizations"


class AdvancedRouteVisualizer:
    """高级路径可视化器 - 专业的地图路径可视化"""

    def __init__(self):
        """初始化可视化器"""
        self.logger = self._setup_logger()
        self.real_data_loader = RealDataLoader()

        # 配送中心坐标 (成都A网点)
        self.depot_coordinates = [30.800835, 104.139111]

        # 专业配色方案
        self.route_colors = [
            '#FF6B6B',  # 珊瑚红
            '#4ECDC4',  # 青蓝色
            '#45B7D1',  # 天蓝色
            '#96CEB4',  # 薄荷绿
            '#FFEAA7',  # 香槟黄
            '#DDA0DD',  # 紫罗兰
            '#98D8C8',  # 海绿色
            '#F7DC6F',  # 柠檬黄
            '#BB8FCE',  # 淡紫色
            '#85C1E9',  # 浅蓝色
            '#F8C471',  # 橙黄色
            '#82E0AA'   # 浅绿色
        ]

        # 图标配置
        self.marker_config = {
            'depot': {
                'size': 25,
                'color': '#FF0000',
                'symbol': 'star'
            },
            'pickup': {
                'size': 15,
                'color': '#00AA00',
                'symbol': 'triangle-up'
            },
            'delivery': {
                'size': 15,
                'color': '#0066CC',
                'symbol': 'triangle-down'
            }
        }

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

    def create_professional_vrp_visualization(self, route_solutions: Dict) -> go.Figure:
        """
        创建专业的VRP路径优化可视化

        Args:
            route_solutions: 路径解决方案字典

        Returns:
            go.Figure: 专业的路径可视化图形
        """
        self.logger.info("创建专业VRP路径优化可视化")

        # 创建图形
        fig = go.Figure()

        # 处理路径数据 - 优先使用真实数据
        if not route_solutions:
            try:
                real_route_data = self.real_data_loader.get_route_optimization_data()
                if real_route_data and real_route_data.get('route_solutions'):
                    route_solutions = real_route_data['route_solutions']
                    self.depot_coordinates = real_route_data.get('depot_location', self.depot_coordinates)
                    self.logger.info(f"成功加载真实路径数据: {len(route_solutions)} 个车辆路径")
                else:
                    route_solutions = self._generate_sample_route_solutions()
                    self.logger.info("使用示例路径数据")
            except Exception as e:
                self.logger.warning(f"加载真实路径数据失败: {e}，使用示例数据")
                route_solutions = self._generate_sample_route_solutions()

        # 收集所有坐标点用于地图中心计算
        all_lats = [self.depot_coordinates[0]]
        all_lons = [self.depot_coordinates[1]]

        # 添加配送中心
        fig.add_trace(go.Scattermapbox(
            lat=[self.depot_coordinates[0]],
            lon=[self.depot_coordinates[1]],
            mode='markers',
            marker=self.marker_config['depot'],
            name='🏢 A网点配送中心',
            text=[self._create_depot_info_text(route_solutions)],
            hovertemplate='<b>A网点配送中心</b><br>' +
                         '%{text}<extra></extra>',
            showlegend=True
        ))

        # 处理每个车辆的路径
        route_stats = []
        for route_idx, (vehicle_id, route_data) in enumerate(route_solutions.items()):
            color = self.route_colors[route_idx % len(self.route_colors)]

            # 处理路径序列
            route_sequence = route_data.get('route_sequence', [])
            if not route_sequence:
                continue

            # 收集路径坐标
            route_lats = [self.depot_coordinates[0]]
            route_lons = [self.depot_coordinates[1]]

            pickup_points = []
            delivery_points = []

            for stop in route_sequence:
                lat, lon = stop['latitude'], stop['longitude']
                all_lats.append(lat)
                all_lons.append(lon)
                route_lats.append(lat)
                route_lons.append(lon)

                if stop['type'] == 'pickup':
                    pickup_points.append(stop)
                else:
                    delivery_points.append(stop)

            # 返回配送中心
            route_lats.append(self.depot_coordinates[0])
            route_lons.append(self.depot_coordinates[1])

            # 添加路径线
            fig.add_trace(go.Scattermapbox(
                lat=route_lats,
                lon=route_lons,
                mode='lines',
                line=dict(width=4, color=color),
                name=f'🚛 {vehicle_id}',
                hoverinfo='skip',
                showlegend=True
            ))

            # 添加取货点
            if pickup_points:
                pickup_lats = [p['latitude'] for p in pickup_points]
                pickup_lons = [p['longitude'] for p in pickup_points]
                pickup_texts = [self._create_stop_info_text(p, vehicle_id) for p in pickup_points]

                fig.add_trace(go.Scattermapbox(
                    lat=pickup_lats,
                    lon=pickup_lons,
                    mode='markers',
                    marker=dict(
                        size=self.marker_config['pickup']['size'],
                        color=color,
                        symbol=self.marker_config['pickup']['symbol']
                    ),
                    name=f'📦 {vehicle_id} 取货',
                    text=pickup_texts,
                    hovertemplate='<b>取货点</b><br>%{text}<extra></extra>',
                    showlegend=False
                ))

            # 添加送货点
            if delivery_points:
                delivery_lats = [p['latitude'] for p in delivery_points]
                delivery_lons = [p['longitude'] for p in delivery_points]
                delivery_texts = [self._create_stop_info_text(p, vehicle_id) for p in delivery_points]

                fig.add_trace(go.Scattermapbox(
                    lat=delivery_lats,
                    lon=delivery_lons,
                    mode='markers',
                    marker=dict(
                        size=self.marker_config['delivery']['size'],
                        color=color,
                        symbol=self.marker_config['delivery']['symbol']
                    ),
                    name=f'🚚 {vehicle_id} 送货',
                    text=delivery_texts,
                    hovertemplate='<b>送货点</b><br>%{text}<extra></extra>',
                    showlegend=False
                ))

            # 收集路径统计
            summary = route_data.get('summary', {})
            route_stats.append({
                'vehicle_id': vehicle_id,
                'distance': summary.get('total_distance_km', 0),
                'time': summary.get('total_duration_hours', 0),
                'cost': summary.get('fuel_cost_yuan', 0),
                'stops': len(route_sequence),
                'color': color
            })

        # 计算总体统计
        total_distance = sum(stat['distance'] for stat in route_stats)
        total_cost = sum(stat['cost'] for stat in route_stats)
        total_time = max(stat['time'] for stat in route_stats) if route_stats else 0
        total_vehicles = len(route_stats)

        # 设置地图布局
        center_lat = sum(all_lats) / len(all_lats) if all_lats else self.depot_coordinates[0]
        center_lon = sum(all_lons) / len(all_lons) if all_lons else self.depot_coordinates[1]

        fig.update_layout(
            title={
                'text': f'🗺️ 路径优化方案总览<br>'
                       f'车辆数: {total_vehicles} 辆 | 总里程: {total_distance:.1f} km | '
                       f'预计耗时: {total_time:.1f} 小时 | 预估成本: {total_cost:.2f} 元',
                'x': 0.5,
                'font': {'size': 16, 'color': '#2E86AB', 'family': 'Arial Black'}
            },
            mapbox=dict(
                style='carto-positron',
                center=dict(lat=center_lat, lon=center_lon),
                zoom=10,
                bearing=0,
                pitch=0
            ),
            width=1500,
            height=1000,
            legend=dict(
                orientation="v",
                yanchor="top",
                y=1,
                xanchor="left",
                x=0.01,
                bgcolor='rgba(255,255,255,0.9)',
                bordercolor='rgba(0,0,0,0.3)',
                borderwidth=1,
                font=dict(size=11)
            ),
            margin=dict(l=0, r=0, t=80, b=0),
            annotations=[
                dict(
                    x=0.99, y=0.02,
                    xref='paper', yref='paper',
                    text=f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                    showarrow=False,
                    font=dict(size=10, color='gray'),
                    bgcolor='rgba(255,255,255,0.7)',
                    bordercolor='rgba(0,0,0,0.1)',
                    borderwidth=1
                )
            ]
        )

        return fig

    def create_single_vehicle_detailed_view(self, vehicle_id: str, route_data: Dict) -> go.Figure:
        """
        创建单车辆详细路径视图

        Args:
            vehicle_id: 车辆ID
            route_data: 路径数据

        Returns:
            go.Figure: 单车辆详细视图
        """
        self.logger.info(f"创建单车辆详细视图: {vehicle_id}")

        fig = go.Figure()

        # 处理路径数据
        route_sequence = route_data.get('route_sequence', [])
        if not route_sequence:
            route_sequence = self._generate_sample_single_route()

        # 收集坐标
        route_lats = [self.depot_coordinates[0]]
        route_lons = [self.depot_coordinates[1]]

        # 添加配送中心
        fig.add_trace(go.Scattermapbox(
            lat=[self.depot_coordinates[0]],
            lon=[self.depot_coordinates[1]],
            mode='markers+text',
            marker=self.marker_config['depot'],
            text=['START'],
            textposition='bottom center',
            name='配送中心',
            hovertemplate='<b>A网点配送中心</b><br>' +
                         '起始点和终点<extra></extra>'
        ))

        # 处理每个停靠点
        for i, stop in enumerate(route_sequence):
            lat, lon = stop['latitude'], stop['longitude']
            route_lats.append(lat)
            route_lons.append(lon)

            # 确定标记样式
            if stop['type'] == 'pickup':
                marker_config = self.marker_config['pickup'].copy()
                action_text = '取货'
                icon = '▲'
            else:
                marker_config = self.marker_config['delivery'].copy()
                action_text = '送货'
                icon = '▼'

            # 添加停靠点标记
            fig.add_trace(go.Scattermapbox(
                lat=[lat],
                lon=[lon],
                mode='markers+text',
                marker=marker_config,
                text=[f'{i+1}'],
                textposition='middle center',
                textfont=dict(size=10, color='white'),
                name=f'{action_text}点 {i+1}',
                hovertemplate=f'<b>{action_text}点 {i+1}</b><br>' +
                             f'订单: {stop["order_id"]}<br>' +
                             f'坐标: ({lat:.6f}, {lon:.6f})<br>' +
                             f'重量: {stop["weight_kg"]:.1f}kg<br>' +
                             f'到达时间: {stop.get("arrival_time", "N/A")}<br>' +
                             f'行驶距离: {stop.get("travel_distance_km", 0):.2f}km<extra></extra>'
            ))

        # 返回配送中心
        route_lats.append(self.depot_coordinates[0])
        route_lons.append(self.depot_coordinates[1])

        # 添加路径线
        fig.add_trace(go.Scattermapbox(
            lat=route_lats,
            lon=route_lons,
            mode='lines',
            line=dict(width=5, color='#FF6B6B'),
            name='行驶路径',
            hoverinfo='skip'
        ))

        # 添加方向箭头（简化版）
        self._add_direction_arrows(fig, route_lats, route_lons)

        # 计算路径统计
        summary = route_data.get('summary', {})
        vehicle_info = route_data.get('vehicle_info', {})

        total_distance = summary.get('total_distance_km', 0)
        total_time = summary.get('total_duration_hours', 0)
        fuel_cost = summary.get('fuel_cost_yuan', 0)
        total_orders = len(route_sequence)

        # 设置布局
        center_lat = sum(route_lats) / len(route_lats)
        center_lon = sum(route_lons) / len(route_lons)

        fig.update_layout(
            title={
                'text': f'🚛 {vehicle_id} 详细路径方案<br>'
                       f'总里程: {total_distance:.1f} km | 预计耗时: {total_time:.1f} 小时 | '
                       f'燃料成本: ¥{fuel_cost:.2f} | 订单数: {total_orders}',
                'x': 0.5,
                'font': {'size': 16, 'color': '#FF6B6B', 'family': 'Arial Black'}
            },
            mapbox=dict(
                style='carto-positron',
                center=dict(lat=center_lat, lon=center_lon),
                zoom=11,
                bearing=0,
                pitch=0
            ),
            width=1200,
            height=800,
            legend=dict(
                orientation="v",
                yanchor="top",
                y=1,
                xanchor="left",
                x=0.01,
                bgcolor='rgba(255,255,255,0.9)',
                bordercolor='rgba(0,0,0,0.3)',
                borderwidth=1
            ),
            annotations=[
                # 车辆信息面板
                dict(
                    x=0.99, y=0.98,
                    xref='paper', yref='paper',
                    text=f"<b>车辆信息</b><br>"
                         f"类型: {vehicle_info.get('type', 'N/A')}<br>"
                         f"载重: {vehicle_info.get('payload_kg', 0):.0f}kg<br>"
                         f"油耗: {vehicle_info.get('fuel_consumption', 0):.1f}L/100km",
                    showarrow=False,
                    font=dict(size=11),
                    bgcolor='rgba(255,255,255,0.9)',
                    bordercolor='rgba(0,0,0,0.2)',
                    borderwidth=1,
                    align='left'
                )
            ]
        )

        return fig

    def create_route_comparison_dashboard(self, route_solutions: Dict) -> go.Figure:
        """
        创建路径对比仪表板

        Args:
            route_solutions: 路径解决方案字典

        Returns:
            go.Figure: 路径对比仪表板
        """
        self.logger.info("创建路径对比仪表板")

        if not route_solutions:
            try:
                real_route_data = self.real_data_loader.get_route_optimization_data()
                if real_route_data and real_route_data.get('route_solutions'):
                    route_solutions = real_route_data['route_solutions']
                    self.logger.info(f"成功加载真实路径数据用于对比分析: {len(route_solutions)} 个车辆")
                else:
                    route_solutions = self._generate_sample_route_solutions()
                    self.logger.info("使用示例路径数据进行对比分析")
            except Exception as e:
                self.logger.warning(f"加载真实路径数据失败: {e}，使用示例数据")
                route_solutions = self._generate_sample_route_solutions()

        # 准备数据
        vehicle_data = []
        for vehicle_id, route_data in route_solutions.items():
            summary = route_data.get('summary', {})
            route_sequence = route_data.get('route_sequence', [])

            # 统计取货和送货点
            pickup_count = sum(1 for stop in route_sequence if stop['type'] == 'pickup')
            delivery_count = sum(1 for stop in route_sequence if stop['type'] == 'delivery')

            vehicle_data.append({
                'vehicle_id': vehicle_id,
                'distance': summary.get('total_distance_km', 0),
                'time': summary.get('total_duration_hours', 0),
                'cost': summary.get('fuel_cost_yuan', 0),
                'orders': len(route_sequence),
                'pickup_count': pickup_count,
                'delivery_count': delivery_count,
                'efficiency': summary.get('route_efficiency', np.random.uniform(70, 95))
            })

        df = pd.DataFrame(vehicle_data)

        # 创建子图
        fig = make_subplots(
            rows=2, cols=3,
            subplot_titles=(
                '📏 行驶距离对比', '⏱️ 耗时分析', '💰 成本分析',
                '📦 订单分布', '⚡ 路径效率', '📊 综合指标雷达图'
            ),
            specs=[
                [{"type": "bar"}, {"type": "bar"}, {"type": "bar"}],
                [{"type": "bar"}, {"type": "bar"}, {"type": "scatterpolar"}]
            ]
        )

        colors = self.route_colors[:len(df)]

        # 1. 行驶距离对比
        fig.add_trace(
            go.Bar(x=df['vehicle_id'], y=df['distance'],
                   marker_color=colors, name='距离(km)',
                   text=df['distance'].round(1), textposition='auto'),
            row=1, col=1
        )

        # 2. 耗时分析
        fig.add_trace(
            go.Bar(x=df['vehicle_id'], y=df['time'],
                   marker_color=colors, name='时间(h)',
                   text=df['time'].round(1), textposition='auto'),
            row=1, col=2
        )

        # 3. 成本分析
        fig.add_trace(
            go.Bar(x=df['vehicle_id'], y=df['cost'],
                   marker_color=colors, name='成本(元)',
                   text=df['cost'].round(0), textposition='auto'),
            row=1, col=3
        )

        # 4. 订单分布
        fig.add_trace(
            go.Bar(x=df['vehicle_id'], y=df['pickup_count'],
                   marker_color='lightgreen', name='取货',
                   text=df['pickup_count'], textposition='auto'),
            row=2, col=1
        )
        fig.add_trace(
            go.Bar(x=df['vehicle_id'], y=df['delivery_count'],
                   marker_color='lightblue', name='送货',
                   text=df['delivery_count'], textposition='auto'),
            row=2, col=1
        )

        # 5. 路径效率
        fig.add_trace(
            go.Bar(x=df['vehicle_id'], y=df['efficiency'],
                   marker_color=colors, name='效率(%)',
                   text=df['efficiency'].round(1), textposition='auto'),
            row=2, col=2
        )

        # 6. 综合指标雷达图
        avg_metrics = {
            '距离效率': (100 - df['distance'].mean() / df['distance'].max() * 100),
            '时间效率': (100 - df['time'].mean() / df['time'].max() * 100),
            '成本效率': (100 - df['cost'].mean() / df['cost'].max() * 100),
            '订单效率': (df['orders'].mean() / df['orders'].max() * 100),
            '路径效率': df['efficiency'].mean()
        }

        fig.add_trace(
            go.Scatterpolar(
                r=list(avg_metrics.values()),
                theta=list(avg_metrics.keys()),
                fill='toself',
                name='综合效率',
                line_color='rgb(255,99,132)'
            ),
            row=2, col=3
        )

        # 更新布局
        fig.update_layout(
            title={
                'text': '📊 车辆路径对比分析仪表板',
                'x': 0.5,
                'font': {'size': 20, 'color': '#2E86AB'}
            },
            height=800,
            showlegend=False,
            # 添加总体统计注释
            annotations=[
                dict(
                    x=0.5, y=0.02,
                    xref='paper', yref='paper',
                    text=f"总计: {len(df)}辆车 | 总距离: {df['distance'].sum():.1f}km | "
                         f"平均效率: {df['efficiency'].mean():.1f}% | "
                         f"总成本: ¥{df['cost'].sum():.0f}",
                    showarrow=False,
                    font=dict(size=12, color='#2E86AB'),
                    bgcolor='rgba(255,255,255,0.8)',
                    bordercolor='rgba(0,0,0,0.2)',
                    borderwidth=1
                )
            ]
        )

        # 更新子图标题
        fig.update_xaxes(title_text="车辆ID", row=1, col=1)
        fig.update_xaxes(title_text="车辆ID", row=1, col=2)
        fig.update_xaxes(title_text="车辆ID", row=1, col=3)
        fig.update_xaxes(title_text="车辆ID", row=2, col=1)
        fig.update_xaxes(title_text="车辆ID", row=2, col=2)

        fig.update_yaxes(title_text="距离 (km)", row=1, col=1)
        fig.update_yaxes(title_text="时间 (小时)", row=1, col=2)
        fig.update_yaxes(title_text="成本 (元)", row=1, col=3)
        fig.update_yaxes(title_text="订单数量", row=2, col=1)
        fig.update_yaxes(title_text="效率 (%)", row=2, col=2)

        return fig

    def _create_depot_info_text(self, route_solutions: Dict) -> str:
        """创建配送中心信息文本"""
        total_vehicles = len(route_solutions)
        total_routes = sum(1 for route in route_solutions.values()
                          if route.get('route_sequence'))

        return (f"调度车辆: {total_vehicles}辆<br>"
               f"有效路径: {total_routes}条<br>"
               f"坐标: {self.depot_coordinates}")

    def _create_stop_info_text(self, stop: Dict, vehicle_id: str) -> str:
        """创建停靠点信息文本"""
        return (f"车辆: {vehicle_id}<br>"
               f"订单: {stop['order_id']}<br>"
               f"重量: {stop['weight_kg']:.1f}kg<br>"
               f"坐标: ({stop['latitude']:.4f}, {stop['longitude']:.4f})")

    def _add_direction_arrows(self, fig: go.Figure, lats: List[float], lons: List[float]):
        """添加方向箭头（简化版）"""
        # 在关键点添加方向指示
        for i in range(1, len(lats)-1, 2):  # 每隔一个点添加箭头
            if i < len(lats) - 1:
                # 计算方向
                dlat = lats[i+1] - lats[i]
                dlon = lons[i+1] - lons[i]

                # 简单的箭头标记
                fig.add_trace(go.Scattermapbox(
                    lat=[lats[i]],
                    lon=[lons[i]],
                    mode='markers',
                    marker=dict(
                        size=8,
                        color='red',
                        symbol='triangle-up',
                        angle=np.arctan2(dlat, dlon) * 180 / np.pi
                    ),
                    showlegend=False,
                    hoverinfo='skip'
                ))

    def _generate_sample_route_solutions(self) -> Dict:
        """生成示例路径解决方案"""
        np.random.seed(42)

        solutions = {}
        vehicle_ids = ['LARGE_TRUCK_00', 'LARGE_TRUCK_01', 'LTL_TRUCK_01']

        for vehicle_id in vehicle_ids:
            route_sequence = self._generate_sample_single_route()

            # 计算统计信息
            total_distance = sum(
                np.random.uniform(5, 15) for _ in range(len(route_sequence))
            )
            total_time = total_distance / 45  # 假设平均速度45km/h
            fuel_cost = total_distance * 0.8  # 假设每公里0.8元

            solutions[vehicle_id] = {
                'vehicle_id': vehicle_id,
                'route_sequence': route_sequence,
                'summary': {
                    'total_distance_km': total_distance,
                    'total_duration_hours': total_time,
                    'fuel_cost_yuan': fuel_cost,
                    'total_orders': len(route_sequence),
                    'route_efficiency': np.random.uniform(70, 95)
                },
                'vehicle_info': {
                    'type': 'LARGE' if 'LARGE' in vehicle_id else 'LTL',
                    'payload_kg': 18000 if 'LARGE' in vehicle_id else 8000,
                    'fuel_consumption': 25 if 'LARGE' in vehicle_id else 12
                }
            }

        return solutions

    def _generate_sample_single_route(self) -> List[Dict]:
        """生成单条路径示例数据"""
        np.random.seed(42)

        # 成都市区坐标范围
        lat_range = (30.65, 30.85)
        lon_range = (104.05, 104.25)

        route_sequence = []
        order_ids = ['ORDER_001', 'ORDER_002', 'ORDER_003', 'ORDER_004', 'ORDER_005']
        types = ['pickup', 'delivery', 'pickup', 'delivery', 'delivery']

        for i, (order_id, stop_type) in enumerate(zip(order_ids, types)):
            lat = np.random.uniform(*lat_range)
            lon = np.random.uniform(*lon_range)
            weight = np.random.uniform(500, 3000)

            route_sequence.append({
                'order_id': order_id,
                'type': stop_type,
                'latitude': lat,
                'longitude': lon,
                'weight_kg': weight,
                'arrival_time': f'{8 + i * 2}:00',
                'travel_distance_km': np.random.uniform(3, 12),
                'service_time_minutes': 30
            })

        return route_sequence

    def save_route_visualization(self, fig: go.Figure, filename: str,
                                output_dir: Optional[Path] = None) -> str:
        """
        保存路径可视化文件

        Args:
            fig: Plotly图形对象
            filename: 文件名
            output_dir: 输出目录

        Returns:
            str: 保存的文件路径
        """
        if output_dir is None:
            output_dir = VISUALIZATIONS_DIR

        output_dir.mkdir(parents=True, exist_ok=True)

        # 添加时间戳
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        filename_with_timestamp = f"{filename}_{timestamp}"

        # 保存HTML文件
        html_file = output_dir / f"{filename_with_timestamp}.html"
        fig.write_html(
            str(html_file),
            include_plotlyjs=True,
            config={
                'displayModeBar': True,
                'displaylogo': False,
                'modeBarButtonsToRemove': ['select2d', 'lasso2d'],
                'toImageButtonOptions': {
                    'format': 'png',
                    'filename': filename,
                    'height': 800,
                    'width': 1200,
                    'scale': 2
                }
            }
        )

        self.logger.info(f"路径可视化已保存: {html_file}")
        return str(html_file)

    def create_all_route_visualizations(self, route_solutions: Optional[Dict] = None) -> List[str]:
        """
        创建所有路径可视化

        Args:
            route_solutions: 路径解决方案数据

        Returns:
            List[str]: 生成的文件路径列表
        """
        self.logger.info("开始创建所有路径可视化")

        generated_files = []

        try:
            # 如果没有提供数据，尝试从真实数据加载器获取
            if not route_solutions:
                try:
                    real_route_data = self.real_data_loader.get_route_optimization_data()
                    if real_route_data and real_route_data.get('route_solutions'):
                        route_solutions = real_route_data['route_solutions']
                        self.depot_coordinates = real_route_data.get('depot_location', self.depot_coordinates)
                        self.logger.info(f"使用真实路径数据创建可视化: {len(route_solutions)} 个车辆")
                    else:
                        self.logger.info("真实数据不可用，将使用示例数据")
                except Exception as e:
                    self.logger.warning(f"加载真实数据失败: {e}，将使用示例数据")

            # 1. 专业VRP总览
            vrp_fig = self.create_professional_vrp_visualization(route_solutions)
            file_path = self.save_route_visualization(vrp_fig, 'professional_vrp_overview')
            generated_files.append(file_path)

            # 2. 路径对比仪表板
            dashboard_fig = self.create_route_comparison_dashboard(route_solutions)
            file_path = self.save_route_visualization(dashboard_fig, 'route_comparison_dashboard')
            generated_files.append(file_path)

            # 3. 单车辆详细视图
            if route_solutions:
                for vehicle_id, route_data in route_solutions.items():
                    single_fig = self.create_single_vehicle_detailed_view(vehicle_id, route_data)
                    file_path = self.save_route_visualization(single_fig, f'single_vehicle_detailed')
                    generated_files.append(file_path)
            else:
                # 生成示例单车辆视图
                sample_route = self._generate_sample_single_route()
                single_fig = self.create_single_vehicle_detailed_view('SAMPLE_TRUCK', {'route_sequence': sample_route})
                file_path = self.save_route_visualization(single_fig, 'single_vehicle_detailed')
                generated_files.append(file_path)

            self.logger.info(f"路径可视化完成，共生成 {len(generated_files)} 个文件")

        except Exception as e:
            self.logger.error(f"创建路径可视化失败: {e}")

        return generated_files


def main():
    """测试高级路径可视化模块"""
    print("=== 高级路径可视化模块测试 ===")

    visualizer = AdvancedRouteVisualizer()

    # 创建所有路径可视化
    generated_files = visualizer.create_all_route_visualizations()

    print(f"\n路径可视化生成完成!")
    print(f"生成了 {len(generated_files)} 个可视化文件:")
    for file_path in generated_files:
        print(f"  {file_path}")

    print(f"\n请在浏览器中打开HTML文件查看路径可视化效果")


if __name__ == "__main__":
    main()