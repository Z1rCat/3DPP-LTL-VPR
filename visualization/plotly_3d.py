"""
3D可视化模块
3D Visualization Module using Plotly for Bin Packing Results
"""

import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
import pickle
import json
import time
from typing import Dict, List, Tuple, Optional, Any
from pathlib import Path
import logging

# 导入配置
import sys
sys.path.append(str(Path(__file__).parent.parent))
from config import (TRUCK_SPECS, VISUALIZATION_CONFIG, VISUALIZATIONS_DIR,
                   INTERMEDIATE_DIR, FILE_CONFIG, CARGO_CLASSIFICATION)


class Plotly3DVisualizer:
    """3D装箱结果可视化器"""

    def __init__(self):
        """初始化可视化器"""
        self.logger = self._setup_logger()
        self.truck_specs = TRUCK_SPECS
        self.viz_config = VISUALIZATION_CONFIG

        # 颜色配置
        self.colors = self.viz_config['colors_palette'] * 10  # 重复以确保有足够颜色

        # 货物分类颜色配置
        self.cargo_type_colors = {
            'large': '#FF4444',    # 红色 - 大货物
            'medium': '#44AA44',   # 绿色 - 中货物
            'small': '#4444FF'     # 蓝色 - 小货物
        }

        # 载入货物分类阈值
        self.classification_thresholds = CARGO_CLASSIFICATION

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

    def load_solution(self, solution_file: Optional[str] = None) -> Dict:
        """
        加载求解结果

        Args:
            solution_file: 求解结果文件路径

        Returns:
            Dict: 求解结果数据
        """
        if solution_file is None:
            solution_file = INTERMEDIATE_DIR / FILE_CONFIG['gurobi_solution_file']

        with open(solution_file, 'rb') as f:
            solution = pickle.load(f)

        self.logger.info(f"已加载求解结果: {len(solution['loaded_items'])} 个装载货物")
        return solution

    def create_truck_box(self, truck_id: str, opacity: float = 0.1) -> go.Mesh3d:
        """
        创建货车边界框

        Args:
            truck_id: 货车ID
            opacity: 透明度

        Returns:
            go.Mesh3d: 货车边界框对象
        """
        L, W, H = self.truck_specs['length'], self.truck_specs['width'], self.truck_specs['height']

        # 定义立方体的8个顶点
        vertices = np.array([
            [0, 0, 0], [L, 0, 0], [L, W, 0], [0, W, 0],  # 底面
            [0, 0, H], [L, 0, H], [L, W, H], [0, W, H]   # 顶面
        ])

        # 定义立方体的12个面（每个面用2个三角形表示）
        faces = np.array([
            # 底面 (z=0)
            [0, 1, 2], [0, 2, 3],
            # 顶面 (z=H)
            [4, 6, 5], [4, 7, 6],
            # 前面 (y=0)
            [0, 4, 5], [0, 5, 1],
            # 后面 (y=W)
            [2, 6, 7], [2, 7, 3],
            # 左面 (x=0)
            [0, 3, 7], [0, 7, 4],
            # 右面 (x=L)
            [1, 5, 6], [1, 6, 2]
        ])

        truck_box = go.Mesh3d(
            x=vertices[:, 0],
            y=vertices[:, 1],
            z=vertices[:, 2],
            i=faces[:, 0],
            j=faces[:, 1],
            k=faces[:, 2],
            opacity=opacity,
            color=self.viz_config['truck_color'],
            name=f'{truck_id} 边界',
            showlegend=True
        )

        return truck_box

    def get_cargo_category(self, volume: float) -> str:
        """
        根据体积判断货物类别

        Args:
            volume: 货物体积 (m³)

        Returns:
            str: 货物类别 ('large', 'medium', 'small')
        """
        if volume > self.classification_thresholds['large_cargo_threshold']:
            return 'large'
        elif volume >= self.classification_thresholds['medium_cargo_threshold']:
            return 'medium'
        else:
            return 'small'

    def create_package_box(self, item: Dict, color_idx: int, use_category_color: bool = False) -> go.Mesh3d:
        """
        创建货物包装盒

        Args:
            item: 货物信息字典
            color_idx: 颜色索引

        Returns:
            go.Mesh3d: 货物盒子对象
        """
        x, y, z = item['position']
        L, W, H = item['dimensions']

        # 定义货物立方体的8个顶点
        vertices = np.array([
            [x, y, z], [x+L, y, z], [x+L, y+W, z], [x, y+W, z],         # 底面
            [x, y, z+H], [x+L, y, z+H], [x+L, y+W, z+H], [x, y+W, z+H] # 顶面
        ])

        # 立方体面定义
        faces = np.array([
            [0, 1, 2], [0, 2, 3],  # 底面
            [4, 6, 5], [4, 7, 6],  # 顶面
            [0, 4, 5], [0, 5, 1],  # 前面
            [2, 6, 7], [2, 7, 3],  # 后面
            [0, 3, 7], [0, 7, 4],  # 左面
            [1, 5, 6], [1, 6, 2]   # 右面
        ])

        # 判断货物类别
        cargo_category = self.get_cargo_category(item['volume'])

        # 选择颜色
        if use_category_color:
            box_color = self.cargo_type_colors[cargo_category]
        else:
            box_color = self.colors[color_idx % len(self.colors)]

        # 准备悬停信息
        hover_text = (
            f"货物ID: {item['item_id']}<br>"
            f"类型: {item['item_type']}<br>"
            f"类别: {cargo_category.upper()} ({self._get_category_desc(cargo_category)})<br>"
            f"尺寸: {L:.3f}×{W:.3f}×{H:.3f}m<br>"
            f"体积: {item['volume']:.6f}m³<br>"
            f"重量: {item['weight']:.2f}kg<br>"
            f"位置: ({x:.3f}, {y:.3f}, {z:.3f})<br>"
            f"方向: {item['orientation']}"
        )

        package_box = go.Mesh3d(
            x=vertices[:, 0],
            y=vertices[:, 1],
            z=vertices[:, 2],
            i=faces[:, 0],
            j=faces[:, 1],
            k=faces[:, 2],
            opacity=self.viz_config['package_opacity'],
            color=box_color,
            name=f"{item['item_id']} ({cargo_category.upper()})",
            text=hover_text,
            hovertemplate='%{text}<extra></extra>',
            showlegend=True
        )

        return package_box

    def _get_category_desc(self, category: str) -> str:
        """
        获取货物类别描述

        Args:
            category: 货物类别

        Returns:
            str: 类别描述
        """
        if category == 'large':
            return f'>={self.classification_thresholds["large_cargo_threshold"]}m³'
        elif category == 'medium':
            return f'{self.classification_thresholds["medium_cargo_threshold"]}-{self.classification_thresholds["large_cargo_threshold"]}m³'
        else:
            return f'<{self.classification_thresholds["medium_cargo_threshold"]}m³'

    def create_truck_visualization(self, truck_id: str, truck_items: List[Dict],
                                  highlight_large_cargo: bool = True) -> go.Figure:
        """
        创建单个货车的3D装载可视化

        Args:
            truck_id: 货车ID
            truck_items: 该货车装载的货物列表

        Returns:
            go.Figure: Plotly 3D图形对象
        """
        self.logger.info(f"创建货车 {truck_id} 的3D可视化 ({len(truck_items)} 个货物)")

        # 性能限制：最大显示500个货物，否则采样30%
        MAX_ITEMS_SINGLE_TRUCK = 500
        SAMPLE_RATIO = 0.3

        if len(truck_items) > MAX_ITEMS_SINGLE_TRUCK:
            sample_size = min(MAX_ITEMS_SINGLE_TRUCK, int(len(truck_items) * SAMPLE_RATIO))
            truck_items = truck_items[:sample_size]
            self.logger.warning(f"车辆 {truck_id} 货物过多，采样显示 {len(truck_items)} 个货物")

        # 创建图形
        fig = go.Figure()

        # 添加货车边界框
        truck_box = self.create_truck_box(truck_id, self.viz_config['truck_opacity'])
        fig.add_trace(truck_box)

        # 统计货物类别
        cargo_stats = {'large': 0, 'medium': 0, 'small': 0}
        for item in truck_items:
            category = self.get_cargo_category(item['volume'])
            cargo_stats[category] += 1

        # 添加货物盒子
        for idx, item in enumerate(truck_items):
            package_box = self.create_package_box(item, idx, use_category_color=highlight_large_cargo)
            fig.add_trace(package_box)

        # 计算装载统计
        total_volume = sum(item['volume'] for item in truck_items)
        truck_volume = self.truck_specs['volume']
        loading_efficiency = total_volume / truck_volume * 100

        # 准备标题信息
        cargo_summary = f"大货: {cargo_stats['large']} | 中货: {cargo_stats['medium']} | 小货: {cargo_stats['small']}"

        # 设置布局
        fig.update_layout(
            title={
                'text': f'🚛 {truck_id} 装载方案<br>'
                       f'总货物: {len(truck_items)} 件 ({cargo_summary})<br>'
                       f'装载体积: {total_volume:.3f}m³ | 装载率: {loading_efficiency:.1f}%',
                'x': 0.5,
                'font': {'size': 16}
            },
            scene=dict(
                xaxis=dict(title='长度 (m)', range=[0, self.truck_specs['length']]),
                yaxis=dict(title='宽度 (m)', range=[0, self.truck_specs['width']]),
                zaxis=dict(title='高度 (m)', range=[0, self.truck_specs['height']]),
                aspectmode='manual',
                aspectratio=dict(
                    x=self.truck_specs['length'],
                    y=self.truck_specs['width'],
                    z=self.truck_specs['height']
                ),
                camera=dict(
                    eye=dict(x=1.5, y=1.5, z=1.5),
                    up=dict(x=0, y=0, z=1)
                )
            ),
            width=1200,
            height=800,
            legend=dict(
                orientation="v",
                yanchor="top",
                y=1,
                xanchor="left",
                x=1.02
            )
        )

        return fig

    def create_large_cargo_3dpp_visualization(self, solution: Dict) -> List[go.Figure]:
        """
        专门为大货物3DPP创建可视化

        Args:
            solution: 求解结果

        Returns:
            List[go.Figure]: 大货物专用可视化图形列表
        """
        self.logger.info("创建大货物3DPP专用可视化")

        truck_assignments = solution['truck_assignments']
        large_cargo_figures = []

        # 性能限制：最大处理20辆车，每车最大100个大货物
        MAX_TRUCKS_LARGE_CARGO = 20
        MAX_LARGE_ITEMS_PER_TRUCK = 100
        SAMPLE_RATIO = 0.3

        truck_items = list(truck_assignments.items())
        if len(truck_items) > MAX_TRUCKS_LARGE_CARGO:
            sample_size = min(MAX_TRUCKS_LARGE_CARGO, int(len(truck_items) * SAMPLE_RATIO))
            truck_items = truck_items[:sample_size]
            self.logger.warning(f"大货物可视化采样显示 {len(truck_items)} 辆车")

        for truck_id, items in truck_items:
            # 筛选出大货物
            large_items = [item for item in items
                          if self.get_cargo_category(item['volume']) == 'large']

            if not large_items:
                continue

            # 性能限制：限制每车大货物数量
            if len(large_items) > MAX_LARGE_ITEMS_PER_TRUCK:
                sample_size = min(MAX_LARGE_ITEMS_PER_TRUCK, int(len(large_items) * SAMPLE_RATIO))
                large_items = large_items[:sample_size]
                self.logger.warning(f"车辆 {truck_id} 大货物过多，采样显示 {len(large_items)} 个")

            # 创建大货物专用可视化
            fig = self.create_truck_visualization(
                truck_id,
                large_items,
                highlight_large_cargo=True
            )

            # 更新标题突出大货物
            total_large_volume = sum(item['volume'] for item in large_items)
            fig.update_layout(
                title={
                    'text': f'🚛 {truck_id} - 大货物3DPP装载方案<br>'
                           f'大货物数量: {len(large_items)} 件<br>'
                           f'大货物体积: {total_large_volume:.3f}m³',
                    'x': 0.5,
                    'font': {'size': 18, 'color': '#FF4444'}
                }
            )

            large_cargo_figures.append(fig)

        return large_cargo_figures

    def save_truck_visualization(self, fig: go.Figure, truck_id: str, output_dir: Optional[Path] = None) -> str:
        """
        保存货车可视化为HTML文件

        Args:
            fig: Plotly图形对象
            truck_id: 货车ID
            output_dir: 输出目录

        Returns:
            str: 保存的文件路径
        """
        if output_dir is None:
            output_dir = VISUALIZATIONS_DIR

        output_dir.mkdir(parents=True, exist_ok=True)

        output_file = output_dir / f"{truck_id}_visualization.html"

        fig.write_html(
            str(output_file),
            include_plotlyjs=True,
            config={
                'displayModeBar': True,
                'displaylogo': False,
                'modeBarButtonsToRemove': [
                    'pan2d', 'select2d', 'lasso2d', 'autoScale2d', 'hoverClosestCartesian'
                ]
            }
        )

        self.logger.info(f"货车 {truck_id} 可视化已保存到: {output_file}")
        return str(output_file)

    def create_fleet_summary_visualization(self, solution: Dict) -> go.Figure:
        """
        创建车队装载摘要可视化

        Args:
            solution: 完整求解结果

        Returns:
            go.Figure: 车队摘要图形对象
        """
        self.logger.info("创建车队装载摘要可视化")

        truck_assignments = solution['truck_assignments']

        if not truck_assignments:
            # 创建空图表
            fig = go.Figure()
            fig.add_annotation(
                text="没有装载的货物",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False,
                font=dict(size=20)
            )
            return fig

        # 性能限制：最大处理50辆车，否则采样30%
        MAX_TRUCKS_FLEET_SUMMARY = 50
        SAMPLE_RATIO = 0.3

        truck_items = list(truck_assignments.items())
        if len(truck_items) > MAX_TRUCKS_FLEET_SUMMARY:
            sample_size = min(MAX_TRUCKS_FLEET_SUMMARY, int(len(truck_items) * SAMPLE_RATIO))
            truck_items = truck_items[:sample_size]
            self.logger.warning(f"车队过大，采样显示 {len(truck_items)} 辆车的摘要")

        # 准备数据
        truck_data = []
        for truck_id, items in truck_items:
            total_volume = sum(item['volume'] for item in items)
            total_weight = sum(item['weight'] for item in items)
            loading_efficiency = total_volume / self.truck_specs['volume'] * 100

            truck_data.append({
                'truck_id': truck_id,
                'item_count': len(items),
                'total_volume': total_volume,
                'total_weight': total_weight,
                'loading_efficiency': loading_efficiency
            })

        df = pd.DataFrame(truck_data)

        # 创建子图
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=('装载货物数量', '装载体积分布', '装载效率', '重量分布'),
            specs=[[{"type": "bar"}, {"type": "bar"}],
                   [{"type": "bar"}, {"type": "bar"}]]
        )

        # 1. 货物数量条形图
        fig.add_trace(
            go.Bar(x=df['truck_id'], y=df['item_count'], name='货物数量',
                   marker_color='lightblue'),
            row=1, col=1
        )

        # 2. 体积分布条形图
        fig.add_trace(
            go.Bar(x=df['truck_id'], y=df['total_volume'], name='装载体积(m³)',
                   marker_color='lightgreen'),
            row=1, col=2
        )

        # 3. 装载效率条形图
        fig.add_trace(
            go.Bar(x=df['truck_id'], y=df['loading_efficiency'], name='装载效率(%)',
                   marker_color='orange'),
            row=2, col=1
        )

        # 4. 重量分布条形图
        fig.add_trace(
            go.Bar(x=df['truck_id'], y=df['total_weight'], name='装载重量(kg)',
                   marker_color='salmon'),
            row=2, col=2
        )

        # 更新布局
        fig.update_layout(
            title={
                'text': f'车队装载摘要 - 共使用 {len(truck_assignments)} 辆货车',
                'x': 0.5,
                'font': {'size': 18}
            },
            height=800,
            showlegend=False
        )

        # 更新轴标签
        fig.update_xaxes(title_text="货车ID", row=1, col=1)
        fig.update_xaxes(title_text="货车ID", row=1, col=2)
        fig.update_xaxes(title_text="货车ID", row=2, col=1)
        fig.update_xaxes(title_text="货车ID", row=2, col=2)

        fig.update_yaxes(title_text="数量", row=1, col=1)
        fig.update_yaxes(title_text="体积 (m³)", row=1, col=2)
        fig.update_yaxes(title_text="效率 (%)", row=2, col=1)
        fig.update_yaxes(title_text="重量 (kg)", row=2, col=2)

        return fig

    def batch_visualize_all_trucks(self, solution: Dict, focus_large_cargo: bool = True) -> List[str]:
        """
        批量生成所有货车的可视化文件

        Args:
            solution: 完整求解结果

        Returns:
            List[str]: 生成的HTML文件路径列表
        """
        self.logger.info("开始批量生成所有货车的可视化文件")

        truck_assignments = solution['truck_assignments']
        generated_files = []

        # 生成单个货车可视化
        for truck_id, items in truck_assignments.items():
            try:
                # 检查是否需要简化显示
                if len(items) > self.viz_config['max_packages_full_render']:
                    self.logger.warning(f"货车 {truck_id} 有 {len(items)} 个包裹，"
                                      f"超过阈值 {self.viz_config['max_packages_full_render']}，"
                                      f"将进行简化显示")
                    # 可以在这里实现简化逻辑，比如只显示较大的包裹

                fig = self.create_truck_visualization(truck_id, items)
                file_path = self.save_truck_visualization(fig, truck_id)
                generated_files.append(file_path)

            except Exception as e:
                self.logger.error(f"生成货车 {truck_id} 可视化时出错: {str(e)}")

        # 生成车队摘要
        try:
            summary_fig = self.create_fleet_summary_visualization(solution)
            summary_path = VISUALIZATIONS_DIR / "fleet_summary.html"
            summary_fig.write_html(str(summary_path))
            generated_files.append(str(summary_path))
            self.logger.info(f"车队摘要已保存到: {summary_path}")

        except Exception as e:
            self.logger.error(f"生成车队摘要时出错: {str(e)}")

        # 生成大货物专用可视化
        if focus_large_cargo:
            try:
                large_cargo_figs = self.create_large_cargo_3dpp_visualization(solution)
                for idx, fig in enumerate(large_cargo_figs):
                    large_cargo_path = VISUALIZATIONS_DIR / f"large_cargo_3dpp_{idx+1}.html"
                    fig.write_html(str(large_cargo_path))
                    generated_files.append(str(large_cargo_path))
                    self.logger.info(f"大货物3DPP可视化已保存到: {large_cargo_path}")

            except Exception as e:
                self.logger.error(f"生成大货物3DPP可视化时出错: {str(e)}")

        # 生成增强的货物类别分析
        try:
            category_fig = self.create_cargo_category_analysis_enhanced(solution)
            category_path = VISUALIZATIONS_DIR / "cargo_category_analysis_enhanced.html"
            category_fig.write_html(str(category_path))
            generated_files.append(str(category_path))
            self.logger.info(f"增强货物类别分析已保存到: {category_path}")

        except Exception as e:
            self.logger.error(f"生成增强货物类别分析时出错: {str(e)}")

        self.logger.info(f"批量可视化完成，生成了 {len(generated_files)} 个文件")
        return generated_files

    def create_cargo_type_analysis(self, solution: Dict) -> go.Figure:
        """
        创建货物类型分析图

        Args:
            solution: 求解结果

        Returns:
            go.Figure: 货物类型分析图
        """
        loaded_items = solution['loaded_items']

        # 统计货物类型
        type_stats = {}
        for item in loaded_items:
            item_type = item['item_type']
            if item_type not in type_stats:
                type_stats[item_type] = {'count': 0, 'volume': 0, 'weight': 0}

            type_stats[item_type]['count'] += 1
            type_stats[item_type]['volume'] += item['volume']
            type_stats[item_type]['weight'] += item['weight']

        # 创建饼图
        labels = list(type_stats.keys())
        values = [stats['count'] for stats in type_stats.values()]
        volumes = [stats['volume'] for stats in type_stats.values()]

        fig = go.Figure(data=[
            go.Pie(
                labels=labels,
                values=values,
                hole=0.3,
                textinfo='label+percent+value',
                hovertemplate='<b>%{label}</b><br>数量: %{value}<br>占比: %{percent}<br>总体积: %{customdata:.6f}m³<extra></extra>',
                customdata=volumes
            )
        ])

        fig.update_layout(
            title={
                'text': '装载货物类型分布',
                'x': 0.5,
                'font': {'size': 16}
            }
        )

        return fig

    def create_cargo_category_analysis_enhanced(self, solution: Dict) -> go.Figure:
        """
        创建增强的货物类别分析图表

        Args:
            solution: 求解结果

        Returns:
            go.Figure: 增强的货物类别分析图
        """
        loaded_items = solution['loaded_items']
        truck_assignments = solution['truck_assignments']

        # 性能限制：最大处理30辆车，每车最大500个货物
        MAX_TRUCKS_CATEGORY_ANALYSIS = 30
        MAX_ITEMS_PER_TRUCK_ANALYSIS = 500
        SAMPLE_RATIO = 0.3

        truck_items = list(truck_assignments.items())
        if len(truck_items) > MAX_TRUCKS_CATEGORY_ANALYSIS:
            sample_size = min(MAX_TRUCKS_CATEGORY_ANALYSIS, int(len(truck_items) * SAMPLE_RATIO))
            truck_items = truck_items[:sample_size]
            self.logger.warning(f"类别分析采样显示 {len(truck_items)} 辆车")

        # 统计各类别货物信息
        category_stats = {
            'large': {'count': 0, 'volume': 0, 'weight': 0, 'trucks': set()},
            'medium': {'count': 0, 'volume': 0, 'weight': 0, 'trucks': set()},
            'small': {'count': 0, 'volume': 0, 'weight': 0, 'trucks': set()}
        }

        # 按车辆统计（采样后的数据）
        for truck_id, items in truck_items:
            # 性能限制：每车最大分析货物数
            if len(items) > MAX_ITEMS_PER_TRUCK_ANALYSIS:
                sample_size = min(MAX_ITEMS_PER_TRUCK_ANALYSIS, int(len(items) * SAMPLE_RATIO))
                items = items[:sample_size]

            for item in items:
                category = self.get_cargo_category(item['volume'])
                category_stats[category]['count'] += 1
                category_stats[category]['volume'] += item['volume']
                category_stats[category]['weight'] += item['weight']
                category_stats[category]['trucks'].add(truck_id)

        # 创建子图
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=(
                '货物类别数量分布',
                '货物类别体积分布',
                '货物类别重量分布',
                '各类别使用车辆数'
            ),
            specs=[[{"type": "bar"}, {"type": "bar"}],
                   [{"type": "bar"}, {"type": "bar"}]]
        )

        categories = ['large', 'medium', 'small']
        category_labels = ['大货物', '中货物', '小货物']
        colors = [self.cargo_type_colors[cat] for cat in categories]

        # 1. 数量分布
        counts = [category_stats[cat]['count'] for cat in categories]
        fig.add_trace(
            go.Bar(x=category_labels, y=counts, name='货物数量',
                   marker_color=colors, text=counts, textposition='auto'),
            row=1, col=1
        )

        # 2. 体积分布
        volumes = [category_stats[cat]['volume'] for cat in categories]
        fig.add_trace(
            go.Bar(x=category_labels, y=volumes, name='总体积(m³)',
                   marker_color=colors, text=[f'{v:.2f}' for v in volumes],
                   textposition='auto'),
            row=1, col=2
        )

        # 3. 重量分布
        weights = [category_stats[cat]['weight'] for cat in categories]
        fig.add_trace(
            go.Bar(x=category_labels, y=weights, name='总重量(kg)',
                   marker_color=colors, text=[f'{w:.1f}' for w in weights],
                   textposition='auto'),
            row=2, col=1
        )

        # 4. 使用车辆数
        truck_counts = [len(category_stats[cat]['trucks']) for cat in categories]
        fig.add_trace(
            go.Bar(x=category_labels, y=truck_counts, name='使用车辆数',
                   marker_color=colors, text=truck_counts, textposition='auto'),
            row=2, col=2
        )

        # 更新布局
        fig.update_layout(
            title={
                'text': '🚛 货物类别装载分析报告',
                'x': 0.5,
                'font': {'size': 20}
            },
            height=800,
            showlegend=False
        )

        return fig

    def create_enhanced_single_category_3dpp_visualization(self, solution: Dict) -> List[go.Figure]:
        """
        增强版单品类3DPP装载可视化
        专门展示大货物的详细3D装载方案，包括空间利用率分析

        Args:
            solution: 求解结果

        Returns:
            List[go.Figure]: 增强的单品类可视化图形列表
        """
        self.logger.info("创建增强版单品类3DPP装载可视化")

        truck_assignments = solution.get('truck_assignments', {})
        enhanced_figures = []

        for truck_id, items in truck_assignments.items():
            # 筛选出大货物
            large_items = [item for item in items
                          if self.get_cargo_category(item['volume']) == 'large']

            if not large_items:
                continue

            # 创建增强的3D可视化
            fig = go.Figure()

            # 添加货车边界框（透明）
            truck_box = self.create_truck_box(truck_id, opacity=0.05)
            fig.add_trace(truck_box)

            # 添加大货物盒子（高亮显示）
            for idx, item in enumerate(large_items):
                package_box = self.create_package_box(item, idx, use_category_color=True)
                # 增强大货物的可视化效果
                package_box.update(opacity=0.9, showlegend=True)
                fig.add_trace(package_box)

            # 添加空间利用率网格
            self._add_space_utilization_grid(fig, large_items)

            # 计算详细统计
            total_large_volume = sum(item['volume'] for item in large_items)
            truck_volume = self.truck_specs['volume']
            utilization_rate = total_large_volume / truck_volume * 100

            # 计算空间分布
            space_distribution = self._calculate_space_distribution(large_items)

            # 设置增强布局
            fig.update_layout(
                title={
                    'text': f'📦 {truck_id} - 单品类3DPP装载可视化<br>'
                           f'大货物装载：{len(large_items)} 件 | '
                           f'空间利用率：{utilization_rate:.1f}%<br>'
                           f'X轴占用：{space_distribution["x_usage"]:.1f}% | '
                           f'Y轴占用：{space_distribution["y_usage"]:.1f}% | '
                           f'Z轴占用：{space_distribution["z_usage"]:.1f}%',
                    'x': 0.5,
                    'font': {'size': 16, 'color': '#FF4444'}
                },
                scene=dict(
                    xaxis=dict(
                        title='长度 (m)',
                        range=[0, self.truck_specs['length']],
                        showgrid=True,
                        gridwidth=2,
                        gridcolor='rgba(255,255,255,0.3)'
                    ),
                    yaxis=dict(
                        title='宽度 (m)',
                        range=[0, self.truck_specs['width']],
                        showgrid=True,
                        gridwidth=2,
                        gridcolor='rgba(255,255,255,0.3)'
                    ),
                    zaxis=dict(
                        title='高度 (m)',
                        range=[0, self.truck_specs['height']],
                        showgrid=True,
                        gridwidth=2,
                        gridcolor='rgba(255,255,255,0.3)'
                    ),
                    aspectmode='manual',
                    aspectratio=dict(
                        x=self.truck_specs['length'],
                        y=self.truck_specs['width'],
                        z=self.truck_specs['height']
                    ),
                    camera=dict(
                        eye=dict(x=1.8, y=1.8, z=1.2),
                        up=dict(x=0, y=0, z=1)
                    ),
                    bgcolor='rgba(240,240,240,0.1)'
                ),
                width=1400,
                height=900,
                legend=dict(
                    orientation="v",
                    yanchor="top",
                    y=1,
                    xanchor="left",
                    x=1.02,
                    bgcolor='rgba(255,255,255,0.8)',
                    bordercolor='rgba(0,0,0,0.2)',
                    borderwidth=1
                )
            )

            enhanced_figures.append(fig)

        return enhanced_figures

    def create_multi_category_3dpp_visualization(self, solution: Dict) -> List[go.Figure]:
        """
        多品类3DPP装载可视化
        同时展示大、中、小货物的混合装载方案，按类别颜色编码

        Args:
            solution: 求解结果

        Returns:
            List[go.Figure]: 多品类可视化图形列表
        """
        self.logger.info("创建多品类3DPP装载可视化")

        truck_assignments = solution.get('truck_assignments', {})
        multi_category_figures = []

        for truck_id, items in truck_assignments.items():
            if not items:
                continue

            # 性能优化：跳过货物数量过多的车辆，避免渲染卡死
            MAX_ITEMS_FOR_MULTI_CATEGORY = 500
            if len(items) > MAX_ITEMS_FOR_MULTI_CATEGORY:
                self.logger.warning(f"跳过车辆 {truck_id}：货物数量过多 ({len(items)} > {MAX_ITEMS_FOR_MULTI_CATEGORY})")
                continue

            # 按类别分组货物
            categorized_items = {
                'large': [],
                'medium': [],
                'small': []
            }

            for item in items:
                category = self.get_cargo_category(item['volume'])
                categorized_items[category].append(item)

            # 只处理有多个类别货物的车辆
            active_categories = sum(1 for cat_items in categorized_items.values() if cat_items)
            if active_categories < 2:
                continue

            # 创建多品类可视化
            fig = go.Figure()

            # 添加货车边界框
            truck_box = self.create_truck_box(truck_id, opacity=0.08)
            fig.add_trace(truck_box)

            # 按层次添加不同类别的货物
            layer_info = []
            for category, cat_items in categorized_items.items():
                if not cat_items:
                    continue

                # 计算该类别的统计信息
                cat_volume = sum(item['volume'] for item in cat_items)
                cat_weight = sum(item.get('weight', 0) for item in cat_items)

                layer_info.append({
                    'category': category,
                    'count': len(cat_items),
                    'volume': cat_volume,
                    'weight': cat_weight
                })

                # 添加该类别的货物盒子 - 性能优化：限制每个类别的显示数量
                MAX_ITEMS_PER_CATEGORY = 50
                display_items = cat_items[:MAX_ITEMS_PER_CATEGORY] if len(cat_items) > MAX_ITEMS_PER_CATEGORY else cat_items

                if len(cat_items) > MAX_ITEMS_PER_CATEGORY:
                    self.logger.info(f"车辆 {truck_id} {category}类货物采样显示: {len(display_items)}/{len(cat_items)}")

                for idx, item in enumerate(display_items):
                    package_box = self.create_package_box(item, idx, use_category_color=True)
                    # 根据类别调整透明度
                    opacity_map = {'large': 0.9, 'medium': 0.7, 'small': 0.6}
                    package_box.update(
                        opacity=opacity_map[category],
                        showlegend=True,
                        name=f"{category.upper()} - {item['item_id']}"
                    )
                    fig.add_trace(package_box)

            # 添加类别分层线条
            self._add_category_separation_lines(fig, categorized_items)

            # 计算总体统计
            total_volume = sum(item['volume'] for item in items)
            truck_volume = self.truck_specs['volume']
            utilization_rate = total_volume / truck_volume * 100

            # 生成类别摘要文本
            category_summary = " | ".join([
                f"{info['category'].upper()}: {info['count']}件({info['volume']:.2f}m³)"
                for info in layer_info
            ])

            # 设置多品类布局
            fig.update_layout(
                title={
                    'text': f'🎨 {truck_id} - 多品类3DPP装载可视化<br>'
                           f'混合装载：{len(items)} 件 ({active_categories}类别) | '
                           f'总利用率：{utilization_rate:.1f}%<br>'
                           f'{category_summary}',
                    'x': 0.5,
                    'font': {'size': 16, 'color': '#2E86AB'}
                },
                scene=dict(
                    xaxis=dict(
                        title='长度 (m)',
                        range=[0, self.truck_specs['length']],
                        showgrid=True,
                        gridwidth=1,
                        gridcolor='rgba(200,200,200,0.4)'
                    ),
                    yaxis=dict(
                        title='宽度 (m)',
                        range=[0, self.truck_specs['width']],
                        showgrid=True,
                        gridwidth=1,
                        gridcolor='rgba(200,200,200,0.4)'
                    ),
                    zaxis=dict(
                        title='高度 (m)',
                        range=[0, self.truck_specs['height']],
                        showgrid=True,
                        gridwidth=1,
                        gridcolor='rgba(200,200,200,0.4)'
                    ),
                    aspectmode='manual',
                    aspectratio=dict(
                        x=self.truck_specs['length'],
                        y=self.truck_specs['width'],
                        z=self.truck_specs['height']
                    ),
                    camera=dict(
                        eye=dict(x=2.0, y=2.0, z=1.5),
                        up=dict(x=0, y=0, z=1)
                    ),
                    bgcolor='rgba(230,240,250,0.1)'
                ),
                width=1500,
                height=1000,
                legend=dict(
                    orientation="v",
                    yanchor="top",
                    y=1,
                    xanchor="left",
                    x=1.02,
                    bgcolor='rgba(255,255,255,0.9)',
                    bordercolor='rgba(0,0,0,0.3)',
                    borderwidth=1
                )
            )

            multi_category_figures.append(fig)

        return multi_category_figures

    def create_loading_density_heatmap(self, solution: Dict) -> go.Figure:
        """
        创建装载密度热力图
        展示货车空间利用的密度分布

        Args:
            solution: 求解结果

        Returns:
            go.Figure: 装载密度热力图
        """
        self.logger.info("创建装载密度热力图")

        truck_assignments = solution.get('truck_assignments', {})

        # 创建空间网格 - 大幅降低分辨率以提高性能
        L, W, H = self.truck_specs['length'], self.truck_specs['width'], self.truck_specs['height']
        grid_resolution = 8  # 网格分辨率降低到8 (8^3=512个网格点)

        # 性能检查：如果货物数量太大，直接返回简化图表
        total_items_count = sum(len(items) for items in truck_assignments.values())
        MAX_ITEMS_FOR_FAST_DENSITY = 500

        if total_items_count > MAX_ITEMS_FOR_FAST_DENSITY:
            self.logger.warning(f"货物数量过多({total_items_count})，返回简化密度图表")
            # 返回简化的密度可视化
            return self._create_simplified_density_chart(truck_assignments)

        x_grid = np.linspace(0, L, grid_resolution)
        y_grid = np.linspace(0, W, grid_resolution)
        z_grid = np.linspace(0, H, grid_resolution)

        # 初始化密度矩阵
        density_matrix = np.zeros((grid_resolution, grid_resolution, grid_resolution))

        # 计算每个网格点的装载密度 - 进一步减少处理数量
        MAX_ITEMS_FOR_DENSITY_ANALYSIS = 300
        if total_items_count > MAX_ITEMS_FOR_DENSITY_ANALYSIS:
            self.logger.info(f"密度分析采样：{MAX_ITEMS_FOR_DENSITY_ANALYSIS}/{total_items_count} 个货物")
            # 计算采样比例
            sample_ratio = MAX_ITEMS_FOR_DENSITY_ANALYSIS / total_items_count
        else:
            sample_ratio = 1.0

        processed_items = 0
        import time
        start_time = time.time()
        TIMEOUT_SECONDS = 5  # 5秒超时

        for truck_id, items in truck_assignments.items():
            # 检查超时
            if time.time() - start_time > TIMEOUT_SECONDS:
                self.logger.warning(f"密度分析超时({TIMEOUT_SECONDS}秒)，已处理{processed_items}个货物")
                break

            # 根据采样比例确定处理的货物数量
            items_to_process = int(len(items) * sample_ratio) if sample_ratio < 1.0 else len(items)
            sampled_items = items[:items_to_process]

            for item in sampled_items:
                processed_items += 1
                if processed_items > MAX_ITEMS_FOR_DENSITY_ANALYSIS:
                    break

                # 超时检查（每50个货物检查一次）
                if processed_items % 50 == 0 and time.time() - start_time > TIMEOUT_SECONDS:
                    self.logger.warning(f"密度分析超时，已处理{processed_items}个货物")
                    break

                try:
                    x, y, z = item['position']
                    l, w, h = item['dimensions']

                    # 简化网格计算 - 只计算中心点
                    center_x = int((x + l/2) / L * grid_resolution)
                    center_y = int((y + w/2) / W * grid_resolution)
                    center_z = int((z + h/2) / H * grid_resolution)

                    # 边界检查
                    if (0 <= center_x < grid_resolution and
                        0 <= center_y < grid_resolution and
                        0 <= center_z < grid_resolution):
                        density_matrix[center_x, center_y, center_z] += item['volume']

                except (IndexError, KeyError, TypeError) as e:
                    # 跳过有问题的货物数据
                    continue

            # 如果已经达到最大处理数量或超时，退出外层循环
            if processed_items > MAX_ITEMS_FOR_DENSITY_ANALYSIS or time.time() - start_time > TIMEOUT_SECONDS:
                break

        # 创建3D热力图
        fig = go.Figure()

        # 添加体积热力图
        x_mesh, y_mesh, z_mesh = np.meshgrid(x_grid, y_grid, z_grid, indexing='ij')

        # 只显示非零密度的点
        non_zero_mask = density_matrix > 0

        if np.any(non_zero_mask):
            fig.add_trace(go.Scatter3d(
                x=x_mesh[non_zero_mask],
                y=y_mesh[non_zero_mask],
                z=z_mesh[non_zero_mask],
                mode='markers',
                marker=dict(
                    size=8,
                    color=density_matrix[non_zero_mask],
                    colorscale='Viridis',
                    showscale=True,
                    colorbar=dict(
                        title="装载密度<br>(m³)",
                        x=1.02
                    )
                ),
                name='装载密度',
                hovertemplate='位置: (%{x:.1f}, %{y:.1f}, %{z:.1f})<br>' +
                             '密度: %{marker.color:.3f}m³<extra></extra>'
            ))

        # 添加货车边界框
        truck_box = self.create_truck_box("DENSITY_MAP", opacity=0.1)
        fig.add_trace(truck_box)

        # 设置布局
        fig.update_layout(
            title={
                'text': '🔥 装载密度热力图<br>显示货车空间利用分布',
                'x': 0.5,
                'font': {'size': 18}
            },
            scene=dict(
                xaxis=dict(title='长度 (m)', range=[0, L]),
                yaxis=dict(title='宽度 (m)', range=[0, W]),
                zaxis=dict(title='高度 (m)', range=[0, H]),
                aspectmode='manual',
                aspectratio=dict(x=L, y=W, z=H),
                camera=dict(
                    eye=dict(x=1.5, y=1.5, z=1.5)
                )
            ),
            width=1200,
            height=800
        )

        return fig

    def _create_simplified_density_chart(self, truck_assignments: Dict) -> go.Figure:
        """创建简化的密度可视化图表（当数据量过大时使用）"""
        fig = go.Figure()

        # 快速统计基本信息，不遍历所有项目
        truck_count = len(truck_assignments)
        total_items = sum(len(items) for items in truck_assignments.values())

        # 创建纯文本提示，不进行复杂计算
        fig.add_annotation(
            text=f"📊 数据量过大，已跳过密度分析<br><br>"
                 f"🚛 总车辆数: {truck_count}<br>"
                 f"📦 总货物数: {total_items}<br><br>"
                 f"💡 提示：可在config.py中调整可视化性能设置<br>"
                 f"   - 修改 VISUALIZATION_PERFORMANCE['sample_ratio']<br>"
                 f"   - 修改 VISUALIZATION_PERFORMANCE['max_items_per_visualization']<br>"
                 f"   - 设置 VISUALIZATION_PERFORMANCE['density_analysis_enabled'] = True",
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            showarrow=False,
            font=dict(size=16),
            align="center",
            bordercolor="orange",
            borderwidth=2,
            bgcolor="rgba(255,248,220,0.8)"
        )

        fig.update_layout(
            title="密度分析已跳过 - 性能保护",
            xaxis=dict(visible=False),
            yaxis=dict(visible=False),
            showlegend=False,
            width=800,
            height=500,
            paper_bgcolor="rgba(240,240,240,0.1)"
        )

        return fig

    def create_3d_loading_efficiency_analysis(self, solution: Dict) -> go.Figure:
        """
        创建3D装载效率分析图
        展示不同车辆的装载效率对比

        Args:
            solution: 求解结果

        Returns:
            go.Figure: 3D装载效率分析图
        """
        self.logger.info("创建3D装载效率分析图")

        truck_assignments = solution.get('truck_assignments', {})

        if not truck_assignments:
            # 返回空图表
            fig = go.Figure()
            fig.add_annotation(
                text="没有装载数据可分析",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False,
                font=dict(size=20)
            )
            return fig

        # 性能限制：最大处理40辆车，每车最大300个货物
        MAX_TRUCKS_EFFICIENCY_ANALYSIS = 40
        MAX_ITEMS_PER_TRUCK_EFFICIENCY = 300
        SAMPLE_RATIO = 0.3

        truck_items = list(truck_assignments.items())
        if len(truck_items) > MAX_TRUCKS_EFFICIENCY_ANALYSIS:
            sample_size = min(MAX_TRUCKS_EFFICIENCY_ANALYSIS, int(len(truck_items) * SAMPLE_RATIO))
            truck_items = truck_items[:sample_size]
            self.logger.warning(f"效率分析采样显示 {len(truck_items)} 辆车")

        # 准备数据
        truck_data = []
        truck_volume = self.truck_specs['volume']

        for truck_id, items in truck_items:
            if not items:
                continue

            # 性能限制：每车最大分析货物数
            if len(items) > MAX_ITEMS_PER_TRUCK_EFFICIENCY:
                sample_size = min(MAX_ITEMS_PER_TRUCK_EFFICIENCY, int(len(items) * SAMPLE_RATIO))
                items = items[:sample_size]

            total_volume = sum(item['volume'] for item in items)
            total_weight = sum(item.get('weight', 0) for item in items)
            item_count = len(items)

            # 按类别统计
            category_stats = {'large': 0, 'medium': 0, 'small': 0}
            for item in items:
                category = self.get_cargo_category(item['volume'])
                category_stats[category] += 1

            efficiency = total_volume / truck_volume * 100
            density = total_weight / total_volume if total_volume > 0 else 0

            truck_data.append({
                'truck_id': truck_id,
                'efficiency': efficiency,
                'density': density,
                'item_count': item_count,
                'total_volume': total_volume,
                'large_count': category_stats['large'],
                'medium_count': category_stats['medium'],
                'small_count': category_stats['small']
            })

        # 创建3D散点图
        fig = go.Figure()

        # 准备颜色映射（基于货物类别组合）
        colors = []
        hover_texts = []

        for data in truck_data:
            # 根据主要货物类别确定颜色
            if data['large_count'] > 0:
                color = '#FF4444'  # 红色 - 包含大货物
                category_type = "大货物主导"
            elif data['medium_count'] > 0:
                color = '#44AA44'  # 绿色 - 包含中货物
                category_type = "中货物主导"
            else:
                color = '#4444FF'  # 蓝色 - 小货物
                category_type = "小货物主导"

            colors.append(color)

            hover_text = (
                f"车辆: {data['truck_id']}<br>"
                f"装载效率: {data['efficiency']:.1f}%<br>"
                f"装载密度: {data['density']:.1f}kg/m³<br>"
                f"货物数量: {data['item_count']}件<br>"
                f"类别: {category_type}<br>"
                f"大货物: {data['large_count']}件<br>"
                f"中货物: {data['medium_count']}件<br>"
                f"小货物: {data['small_count']}件"
            )
            hover_texts.append(hover_text)

        # 添加3D散点
        fig.add_trace(go.Scatter3d(
            x=[data['efficiency'] for data in truck_data],
            y=[data['density'] for data in truck_data],
            z=[data['item_count'] for data in truck_data],
            mode='markers+text',
            marker=dict(
                size=15,
                color=colors,
                line=dict(width=2, color='white'),
                opacity=0.8
            ),
            text=[data['truck_id'] for data in truck_data],
            textposition='top center',
            hovertemplate='%{customdata}<extra></extra>',
            customdata=hover_texts,
            name='车辆装载效率'
        ))

        # 添加效率基准线
        max_efficiency = max([data['efficiency'] for data in truck_data]) if truck_data else 100
        max_density = max([data['density'] for data in truck_data]) if truck_data else 1000
        max_items = max([data['item_count'] for data in truck_data]) if truck_data else 50

        # 设置布局
        fig.update_layout(
            title={
                'text': '📊 3D装载效率分析<br>效率 × 密度 × 数量 多维对比',
                'x': 0.5,
                'font': {'size': 18}
            },
            scene=dict(
                xaxis=dict(
                    title='装载效率 (%)',
                    range=[0, min(100, max_efficiency + 10)]
                ),
                yaxis=dict(
                    title='装载密度 (kg/m³)',
                    range=[0, max_density + 100]
                ),
                zaxis=dict(
                    title='货物数量 (件)',
                    range=[0, max_items + 5]
                ),
                camera=dict(
                    eye=dict(x=1.8, y=1.8, z=1.5)
                )
            ),
            width=1200,
            height=800,
            annotations=[
                dict(
                    text=f"分析车辆数: {len(truck_data)}<br>"
                         f"平均效率: {np.mean([d['efficiency'] for d in truck_data]):.1f}%<br>"
                         f"平均密度: {np.mean([d['density'] for d in truck_data]):.1f}kg/m³",
                    x=0.02, y=0.98,
                    xref='paper', yref='paper',
                    showarrow=False,
                    bgcolor='rgba(255,255,255,0.8)',
                    bordercolor='rgba(0,0,0,0.2)',
                    borderwidth=1
                )
            ]
        )

        return fig

    def _add_space_utilization_grid(self, fig: go.Figure, items: List[Dict]):
        """添加空间利用率网格线"""
        L, W, H = self.truck_specs['length'], self.truck_specs['width'], self.truck_specs['height']

        # 添加网格线
        grid_lines_x = [0, L/4, L/2, 3*L/4, L]
        grid_lines_y = [0, W/4, W/2, 3*W/4, W]
        grid_lines_z = [0, H/4, H/2, 3*H/4, H]

        # X方向网格
        for x in grid_lines_x:
            fig.add_trace(go.Scatter3d(
                x=[x, x], y=[0, W], z=[0, 0],
                mode='lines',
                line=dict(color='rgba(150,150,150,0.3)', width=1),
                showlegend=False,
                hoverinfo='skip'
            ))

    def _calculate_space_distribution(self, items: List[Dict]) -> Dict[str, float]:
        """计算空间分布统计"""
        if not items:
            return {'x_usage': 0, 'y_usage': 0, 'z_usage': 0}

        L, W, H = self.truck_specs['length'], self.truck_specs['width'], self.truck_specs['height']

        # 计算各轴的占用范围
        x_positions = [item['position'][0] + item['dimensions'][0] for item in items]
        y_positions = [item['position'][1] + item['dimensions'][1] for item in items]
        z_positions = [item['position'][2] + item['dimensions'][2] for item in items]

        return {
            'x_usage': max(x_positions) / L * 100 if x_positions else 0,
            'y_usage': max(y_positions) / W * 100 if y_positions else 0,
            'z_usage': max(z_positions) / H * 100 if z_positions else 0
        }

    def _add_category_separation_lines(self, fig: go.Figure, categorized_items: Dict):
        """添加类别分隔线"""
        # 这里可以添加可视化分隔线来区分不同类别的货物区域
        # 基于货物的位置添加分隔线
        pass

    def save_enhanced_visualization(self, fig: go.Figure, filename: str,
                                  output_dir: Optional[Path] = None) -> str:
        """
        保存增强可视化为PNG和HTML文件

        Args:
            fig: Plotly图形对象
            filename: 文件名
            output_dir: 输出目录

        Returns:
            str: 保存的PNG文件路径
        """
        if output_dir is None:
            output_dir = VISUALIZATIONS_DIR

        output_dir.mkdir(parents=True, exist_ok=True)

        # 添加时间戳
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        filename_with_timestamp = f"{filename}_{timestamp}"

        # 保存PNG图片
        png_file = output_dir / f"{filename_with_timestamp}.png"
        try:
            fig.write_image(
                str(png_file),
                format='png',
                width=1200,
                height=800,
                scale=2
            )
            self.logger.info(f"PNG图片已保存: {png_file}")
        except Exception as e:
            self.logger.error(f"保存PNG失败: {e}")
            # 如果PNG保存失败，尝试保存HTML作为backup
            png_file = output_dir / f"{filename_with_timestamp}.html"
            fig.write_html(
                str(png_file),
                include_plotlyjs=True,
                config={
                    'displayModeBar': True,
                    'displaylogo': False,
                    'toImageButtonOptions': {
                        'format': 'png',
                        'filename': filename,
                        'height': 800,
                        'width': 1200,
                        'scale': 2
                    },
                    'modeBarButtonsToRemove': [
                        'select2d', 'lasso2d'
                    ]
                }
            )
            self.logger.info(f"HTML文件已保存: {png_file}")

        return str(png_file)

    def create_interactive_3d_visualization(self, solution: Dict) -> List[go.Figure]:
        """
        创建交互式3D可视化

        Args:
            solution: 求解结果

        Returns:
            List[go.Figure]: 交互式3D可视化图形列表
        """
        self.logger.info("创建交互式3D可视化")

        truck_assignments = solution.get('truck_assignments', {})
        interactive_figures = []

        # 为每辆车创建交互式3D可视化
        for truck_id, items in truck_assignments.items():
            if not items:
                continue

            fig = go.Figure()

            # 添加货车轮廓
            self._add_truck_frame(fig)

            # 按货物类别添加不同颜色的3D方块
            large_items = [item for item in items if self.get_cargo_category(item.get('volume', 0)) == 'large']
            medium_items = [item for item in items if self.get_cargo_category(item.get('volume', 0)) == 'medium']
            small_items = [item for item in items if self.get_cargo_category(item.get('volume', 0)) == 'small']

            # 大货物 - 红色
            for i, item in enumerate(large_items):
                self._add_3d_box(fig, item, f"大货物_{i+1}", 'red')

            # 中货物 - 蓝色
            for i, item in enumerate(medium_items):
                self._add_3d_box(fig, item, f"中货物_{i+1}", 'blue')

            # 小货物 - 绿色
            for i, item in enumerate(small_items):
                self._add_3d_box(fig, item, f"小货物_{i+1}", 'green')

            # 设置布局
            fig.update_layout(
                title=f"交互式3D装载可视化 - {truck_id}",
                scene=dict(
                    xaxis=dict(title='长度 (m)', range=[0, self.truck_specs['length']]),
                    yaxis=dict(title='宽度 (m)', range=[0, self.truck_specs['width']]),
                    zaxis=dict(title='高度 (m)', range=[0, self.truck_specs['height']]),
                    aspectmode='manual',
                    aspectratio=dict(
                        x=self.truck_specs['length'],
                        y=self.truck_specs['width'],
                        z=self.truck_specs['height']
                    ),
                    camera=dict(
                        eye=dict(x=1.5, y=1.5, z=1.5),
                        up=dict(x=0, y=0, z=1)
                    )
                ),
                width=1200,
                height=800,
                showlegend=True
            )

            interactive_figures.append(fig)

        return interactive_figures

    def _add_3d_box(self, fig: go.Figure, item: Dict, name: str, color: str):
        """添加3D方块到图形中"""
        # 如果没有位置信息，使用默认位置
        if 'position' not in item or 'dimensions' not in item:
            position = [0, 0, 0]
            dimensions = [0.5, 0.5, 0.5]
        else:
            position = item['position']
            dimensions = item['dimensions']

        x, y, z = position
        dx, dy, dz = dimensions

        # 创建3D方块的8个顶点
        vertices = [
            [x, y, z], [x+dx, y, z], [x+dx, y+dy, z], [x, y+dy, z],  # 底面
            [x, y, z+dz], [x+dx, y, z+dz], [x+dx, y+dy, z+dz], [x, y+dy, z+dz]  # 顶面
        ]

        # 定义6个面的顶点索引
        faces = [
            [0, 1, 2, 3],  # 底面
            [4, 5, 6, 7],  # 顶面
            [0, 1, 5, 4],  # 前面
            [2, 3, 7, 6],  # 后面
            [0, 3, 7, 4],  # 左面
            [1, 2, 6, 5]   # 右面
        ]

        # 为每个面创建mesh3d
        for face in faces:
            face_vertices = [vertices[i] for i in face]
            xs, ys, zs = zip(*face_vertices)

            fig.add_trace(go.Mesh3d(
                x=xs,
                y=ys,
                z=zs,
                i=[0, 0],
                j=[1, 2],
                k=[2, 3],
                opacity=0.7,
                color=color,
                name=name,
                showlegend=(face == faces[0])  # 只在第一个面显示图例
            ))


def main():
    """测试3D可视化模块"""
    visualizer = Plotly3DVisualizer()

    try:
        # 加载求解结果
        solution = visualizer.load_solution()

        if not solution['truck_assignments']:
            print("没有装载结果可以可视化")
            return

        # 批量生成可视化
        generated_files = visualizer.batch_visualize_all_trucks(solution)

        print(f"3D可视化完成!")
        print(f"生成了 {len(generated_files)} 个可视化文件:")
        for file_path in generated_files:
            print(f"  {file_path}")

        # 创建货物类型分析
        type_fig = visualizer.create_cargo_type_analysis(solution)
        type_path = VISUALIZATIONS_DIR / "cargo_type_analysis.html"
        type_fig.write_html(str(type_path))
        print(f"\n货物类型分析已保存到: {type_path}")

        print(f"\n可以在浏览器中打开这些HTML文件查看3D装载方案")

    except Exception as e:
        print(f"可视化测试失败: {str(e)}")


if __name__ == "__main__":
    main()