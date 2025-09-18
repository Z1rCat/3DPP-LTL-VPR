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

        for truck_id, items in truck_assignments.items():
            # 筛选出大货物
            large_items = [item for item in items
                          if self.get_cargo_category(item['volume']) == 'large']

            if not large_items:
                continue

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

        # 准备数据
        truck_data = []
        for truck_id, items in truck_assignments.items():
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

        # 统计各类别货物信息
        category_stats = {
            'large': {'count': 0, 'volume': 0, 'weight': 0, 'trucks': set()},
            'medium': {'count': 0, 'volume': 0, 'weight': 0, 'trucks': set()},
            'small': {'count': 0, 'volume': 0, 'weight': 0, 'trucks': set()}
        }

        # 按车辆统计
        for truck_id, items in truck_assignments.items():
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