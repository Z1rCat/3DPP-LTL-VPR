"""
基础可视化器 - 使用matplotlib作为fallback
当plotly不可用时提供基础的2D/3D可视化功能
"""

import matplotlib.pyplot as plt
import matplotlib.patches as patches
from mpl_toolkits.mplot3d import Axes3D
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional, Any
import time
import seaborn as sns

class BasicVisualizer:
    """基础可视化器 - matplotlib实现"""

    def __init__(self):
        """初始化基础可视化器"""
        self.output_dir = Path("output/visualizations")
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # 设置matplotlib中文字体
        plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei']
        plt.rcParams['axes.unicode_minus'] = False

        # 设置默认样式
        plt.style.use('default')

    def create_enhanced_single_category_3dpp_visualization(self, solution_data: Dict) -> List[str]:
        """生成单品类3DPP装载可视化"""
        visualization_files = []

        try:
            truck_assignments = solution_data.get('truck_assignments', {})

            for truck_id, truck_data in truck_assignments.items():
                if not truck_data or 'items' not in truck_data:
                    continue

                fig = plt.figure(figsize=(15, 10))

                # 创建3D子图
                ax1 = fig.add_subplot(221, projection='3d')
                self._plot_3d_loading(ax1, truck_data, f"{truck_id} - 3D装载视图")

                # 创建装载统计
                ax2 = fig.add_subplot(222)
                self._plot_loading_stats(ax2, truck_data, f"{truck_id} - 装载统计")

                # 创建空间利用分析
                ax3 = fig.add_subplot(223)
                self._plot_space_utilization(ax3, truck_data, f"{truck_id} - 空间利用率")

                # 创建货物分布
                ax4 = fig.add_subplot(224)
                self._plot_cargo_distribution(ax4, truck_data, f"{truck_id} - 货物分布")

                plt.tight_layout()

                # 保存图片
                timestamp = time.strftime("%Y%m%d_%H%M%S")
                filename = f"single_category_3dpp_{truck_id}_{timestamp}.png"
                filepath = self.output_dir / filename
                plt.savefig(filepath, dpi=300, bbox_inches='tight')
                plt.close()

                visualization_files.append(str(filepath))

        except Exception as e:
            print(f"[错误] 单品类3DPP可视化生成失败: {e}")

        return visualization_files

    def create_multi_category_3dpp_visualization(self, solution_data: Dict) -> List[str]:
        """生成多品类3DPP装载可视化"""
        visualization_files = []

        try:
            truck_assignments = solution_data.get('truck_assignments', {})

            # 创建综合多车辆视图
            fig = plt.figure(figsize=(20, 12))

            trucks_to_plot = list(truck_assignments.keys())[:6]  # 最多显示6辆车

            for i, truck_id in enumerate(trucks_to_plot):
                truck_data = truck_assignments[truck_id]
                if not truck_data or 'items' not in truck_data:
                    continue

                ax = fig.add_subplot(2, 3, i+1, projection='3d')
                self._plot_3d_loading_multicolor(ax, truck_data, f"{truck_id}")

            plt.suptitle("多品类3DPP装载可视化 - 混合装载方案", fontsize=16)
            plt.tight_layout()

            # 保存图片
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filename = f"multi_category_3dpp_{timestamp}.png"
            filepath = self.output_dir / filename
            plt.savefig(filepath, dpi=300, bbox_inches='tight')
            plt.close()

            visualization_files.append(str(filepath))

        except Exception as e:
            print(f"[错误] 多品类3DPP可视化生成失败: {e}")

        return visualization_files

    def create_loading_density_heatmap(self, solution_data: Dict) -> Optional[str]:
        """生成装载密度热力图"""
        try:
            truck_assignments = solution_data.get('truck_assignments', {})

            # 计算每辆车的装载密度数据
            density_data = []
            for truck_id, truck_data in truck_assignments.items():
                if not truck_data or 'items' not in truck_data:
                    continue

                total_volume = truck_data.get('truck_volume', 100)
                used_volume = sum(item.get('volume', 0) for item in truck_data.get('items', []))
                density = used_volume / total_volume if total_volume > 0 else 0

                density_data.append({
                    'truck_id': truck_id,
                    'density': density,
                    'used_volume': used_volume,
                    'total_volume': total_volume,
                    'item_count': len(truck_data.get('items', []))
                })

            if not density_data:
                return None

            df = pd.DataFrame(density_data)

            # 创建热力图
            fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 10))

            # 密度条形图
            ax1.bar(df['truck_id'], df['density'], color='skyblue', alpha=0.7)
            ax1.set_title('车辆装载密度分布')
            ax1.set_ylabel('装载密度')
            ax1.tick_params(axis='x', rotation=45)

            # 体积对比
            ax2.bar(df['truck_id'], df['used_volume'], alpha=0.7, label='已用体积')
            ax2.bar(df['truck_id'], df['total_volume'], alpha=0.3, label='总体积')
            ax2.set_title('体积使用情况')
            ax2.set_ylabel('体积 (m³)')
            ax2.legend()
            ax2.tick_params(axis='x', rotation=45)

            # 货物数量分布
            ax3.pie(df['item_count'], labels=df['truck_id'], autopct='%1.1f%%')
            ax3.set_title('货物数量分布')

            # 密度散点图
            colors = plt.cm.viridis(df['density'])
            ax4.scatter(df['item_count'], df['density'], c=colors, s=100, alpha=0.7)
            ax4.set_xlabel('货物数量')
            ax4.set_ylabel('装载密度')
            ax4.set_title('密度 vs 货物数量')

            plt.tight_layout()

            # 保存图片
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filename = f"loading_density_heatmap_{timestamp}.png"
            filepath = self.output_dir / filename
            plt.savefig(filepath, dpi=300, bbox_inches='tight')
            plt.close()

            return str(filepath)

        except Exception as e:
            print(f"[错误] 装载密度热力图生成失败: {e}")
            return None

    def create_3d_loading_efficiency_analysis(self, solution_data: Dict) -> Optional[str]:
        """生成3D装载效率分析"""
        try:
            truck_assignments = solution_data.get('truck_assignments', {})

            # 计算效率指标
            efficiency_data = []
            for truck_id, truck_data in truck_assignments.items():
                if not truck_data or 'items' not in truck_data:
                    continue

                items = truck_data.get('items', [])
                total_volume = truck_data.get('truck_volume', 100)
                used_volume = sum(item.get('volume', 0) for item in items)

                efficiency_data.append({
                    'truck_id': truck_id,
                    'volume_efficiency': used_volume / total_volume if total_volume > 0 else 0,
                    'item_count': len(items),
                    'avg_item_volume': used_volume / len(items) if items else 0,
                    'total_weight': sum(item.get('weight', 0) for item in items)
                })

            if not efficiency_data:
                return None

            df = pd.DataFrame(efficiency_data)

            # 创建3D效率分析图
            fig = plt.figure(figsize=(15, 10))

            # 3D散点图
            ax1 = fig.add_subplot(221, projection='3d')
            ax1.scatter(df['item_count'], df['volume_efficiency'], df['avg_item_volume'],
                       c=df['total_weight'], cmap='viridis', s=100)
            ax1.set_xlabel('货物数量')
            ax1.set_ylabel('体积效率')
            ax1.set_zlabel('平均货物体积')
            ax1.set_title('3D效率分析')

            # 效率对比
            ax2 = fig.add_subplot(222)
            ax2.barh(df['truck_id'], df['volume_efficiency'], color='lightcoral')
            ax2.set_title('车辆体积效率对比')
            ax2.set_xlabel('体积效率')

            # 重量-体积关系
            ax3 = fig.add_subplot(223)
            ax3.scatter(df['total_weight'], df['volume_efficiency'], s=df['item_count']*10, alpha=0.6)
            ax3.set_xlabel('总重量 (kg)')
            ax3.set_ylabel('体积效率')
            ax3.set_title('重量-效率关系')

            # 综合评分雷达图（简化版）
            ax4 = fig.add_subplot(224, polar=True)
            for i, row in df.iterrows():
                values = [row['volume_efficiency'],
                         row['item_count']/df['item_count'].max(),
                         row['avg_item_volume']/df['avg_item_volume'].max()]
                angles = np.linspace(0, 2*np.pi, len(values), endpoint=False)
                values += values[:1]  # 闭合
                angles = np.concatenate((angles, [angles[0]]))
                ax4.plot(angles, values, 'o-', linewidth=2, label=row['truck_id'])
            ax4.set_title('综合效率雷达图')
            ax4.legend()

            plt.tight_layout()

            # 保存图片
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filename = f"3d_loading_efficiency_{timestamp}.png"
            filepath = self.output_dir / filename
            plt.savefig(filepath, dpi=300, bbox_inches='tight')
            plt.close()

            return str(filepath)

        except Exception as e:
            print(f"[错误] 3D效率分析生成失败: {e}")
            return None

    def save_enhanced_visualization(self, fig, filename: str) -> str:
        """保存增强版可视化图片"""
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        full_filename = f"{filename}_{timestamp}.png"
        filepath = self.output_dir / full_filename

        if hasattr(fig, 'savefig'):
            fig.savefig(filepath, dpi=300, bbox_inches='tight')
        else:
            plt.savefig(filepath, dpi=300, bbox_inches='tight')

        return str(filepath)

    def _plot_3d_loading(self, ax, truck_data: Dict, title: str):
        """绘制3D装载视图"""
        items = truck_data.get('items', [])
        truck_dimensions = truck_data.get('truck_dimensions', [6, 2.4, 2.6])

        # 绘制货车轮廓
        ax.plot([0, truck_dimensions[0]], [0, 0], [0, 0], 'k-', linewidth=2)
        ax.plot([0, 0], [0, truck_dimensions[1]], [0, 0], 'k-', linewidth=2)
        ax.plot([0, 0], [0, 0], [0, truck_dimensions[2]], 'k-', linewidth=2)

        # 绘制货物
        colors = plt.cm.tab10(np.linspace(0, 1, len(items)))
        for i, item in enumerate(items):
            if 'position' in item and 'dimensions' in item:
                pos = item['position']
                dims = item['dimensions']
                color = colors[i % len(colors)]

                # 简化的立方体表示
                ax.scatter([pos[0]], [pos[1]], [pos[2]], c=[color], s=50, alpha=0.7)

        ax.set_xlabel('长度 (m)')
        ax.set_ylabel('宽度 (m)')
        ax.set_zlabel('高度 (m)')
        ax.set_title(title)

    def _plot_3d_loading_multicolor(self, ax, truck_data: Dict, title: str):
        """绘制多色3D装载视图"""
        items = truck_data.get('items', [])

        # 按货物类型分色
        large_items = [item for item in items if item.get('category') == 'large']
        medium_items = [item for item in items if item.get('category') == 'medium']
        small_items = [item for item in items if item.get('category') == 'small']

        # 绘制不同类型的货物
        if large_items:
            ax.scatter([0.5], [0.5], [0.5], c='red', s=100, alpha=0.7, label='大货物')
        if medium_items:
            ax.scatter([1.5], [0.5], [0.5], c='blue', s=60, alpha=0.7, label='中货物')
        if small_items:
            ax.scatter([2.5], [0.5], [0.5], c='green', s=30, alpha=0.7, label='小货物')

        ax.set_title(title)
        ax.legend()

    def _plot_loading_stats(self, ax, truck_data: Dict, title: str):
        """绘制装载统计"""
        items = truck_data.get('items', [])

        categories = ['大货物', '中货物', '小货物']
        counts = [
            len([item for item in items if item.get('category') == 'large']),
            len([item for item in items if item.get('category') == 'medium']),
            len([item for item in items if item.get('category') == 'small'])
        ]

        ax.bar(categories, counts, color=['red', 'blue', 'green'], alpha=0.7)
        ax.set_title(title)
        ax.set_ylabel('货物数量')

    def _plot_space_utilization(self, ax, truck_data: Dict, title: str):
        """绘制空间利用率"""
        total_volume = truck_data.get('truck_volume', 100)
        used_volume = sum(item.get('volume', 0) for item in truck_data.get('items', []))
        utilization = used_volume / total_volume if total_volume > 0 else 0

        labels = ['已使用', '剩余']
        sizes = [utilization, 1 - utilization]
        colors = ['lightcoral', 'lightgray']

        ax.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90)
        ax.set_title(title)

    def _plot_cargo_distribution(self, ax, truck_data: Dict, title: str):
        """绘制货物分布"""
        items = truck_data.get('items', [])

        if not items:
            ax.text(0.5, 0.5, '无货物数据', ha='center', va='center', transform=ax.transAxes)
            ax.set_title(title)
            return

        # 简化的2D投影
        x_positions = [item.get('position', [0, 0, 0])[0] for item in items if 'position' in item]
        y_positions = [item.get('position', [0, 0, 0])[1] for item in items if 'position' in item]

        if x_positions and y_positions:
            ax.scatter(x_positions, y_positions, alpha=0.6)
            ax.set_xlabel('X位置 (m)')
            ax.set_ylabel('Y位置 (m)')
        else:
            ax.text(0.5, 0.5, '无位置数据', ha='center', va='center', transform=ax.transAxes)

        ax.set_title(title)