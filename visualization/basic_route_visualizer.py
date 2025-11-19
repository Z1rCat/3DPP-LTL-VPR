"""
基础路径可视化器 - 使用matplotlib实现
提供路径优化结果的2D可视化功能
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional, Any
import time

class BasicRouteVisualizer:
    """基础路径可视化器 - matplotlib实现"""

    def __init__(self):
        """初始化基础路径可视化器"""
        self.output_dir = Path("output/visualizations")
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # 设置matplotlib中文字体
        plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei']
        plt.rcParams['axes.unicode_minus'] = False

    def create_enhanced_route_optimization_visualization(self, truck_id: str, route_data: Dict) -> Optional[str]:
        """生成增强版路径优化可视化"""
        try:
            route_points = route_data.get('route_points', [])
            if not route_points:
                return None

            fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 10))

            # 1. 路径轨迹图
            self._plot_route_trajectory(ax1, route_points, f"{truck_id} - 路径轨迹")

            # 2. 距离分析
            self._plot_distance_analysis(ax2, route_points, f"{truck_id} - 距离分析")

            # 3. 时间分析
            self._plot_time_analysis(ax3, route_data, f"{truck_id} - 时间分析")

            # 4. 效率统计
            self._plot_efficiency_stats(ax4, route_data, f"{truck_id} - 效率统计")

            plt.suptitle(f"路径优化分析 - {truck_id}", fontsize=16)
            plt.tight_layout()

            # 保存图片
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filename = f"route_optimization_{truck_id}_{timestamp}.png"
            filepath = self.output_dir / filename
            plt.savefig(filepath, dpi=300, bbox_inches='tight')
            plt.close()

            return str(filepath)

        except Exception as e:
            print(f"[错误] 路径可视化生成失败: {e}")
            return None

    def create_route_efficiency_heatmap(self, route_solutions: Dict) -> Optional[str]:
        """生成路径效率热力图"""
        try:
            # 计算每辆车的效率数据
            efficiency_data = []
            for truck_id, route_data in route_solutions.items():
                if not route_data:
                    continue

                total_distance = route_data.get('total_distance', 0)
                total_time = route_data.get('total_time', 0)
                cargo_count = len(route_data.get('cargo_list', []))

                efficiency_data.append({
                    'truck_id': truck_id,
                    'distance': total_distance,
                    'time': total_time,
                    'cargo_count': cargo_count,
                    'efficiency': cargo_count / total_distance if total_distance > 0 else 0
                })

            if not efficiency_data:
                return None

            df = pd.DataFrame(efficiency_data)

            fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 10))

            # 距离热力图
            ax1.bar(df['truck_id'], df['distance'], color='lightblue', alpha=0.7)
            ax1.set_title('车辆行驶距离')
            ax1.set_ylabel('距离 (km)')
            ax1.tick_params(axis='x', rotation=45)

            # 时间分布
            ax2.bar(df['truck_id'], df['time'], color='lightgreen', alpha=0.7)
            ax2.set_title('车辆运行时间')
            ax2.set_ylabel('时间 (小时)')
            ax2.tick_params(axis='x', rotation=45)

            # 货物数量
            ax3.bar(df['truck_id'], df['cargo_count'], color='orange', alpha=0.7)
            ax3.set_title('载货数量')
            ax3.set_ylabel('货物件数')
            ax3.tick_params(axis='x', rotation=45)

            # 效率散点图
            colors = plt.cm.viridis(df['efficiency'])
            ax4.scatter(df['distance'], df['efficiency'], c=colors, s=df['cargo_count']*10, alpha=0.7)
            ax4.set_xlabel('行驶距离 (km)')
            ax4.set_ylabel('运输效率')
            ax4.set_title('距离-效率关系')

            plt.suptitle('路径效率热力图分析', fontsize=16)
            plt.tight_layout()

            # 保存图片
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filename = f"route_efficiency_heatmap_{timestamp}.png"
            filepath = self.output_dir / filename
            plt.savefig(filepath, dpi=300, bbox_inches='tight')
            plt.close()

            return str(filepath)

        except Exception as e:
            print(f"[错误] 路径效率热力图生成失败: {e}")
            return None

    def create_vehicle_performance_dashboard(self, route_solutions: Dict) -> Optional[str]:
        """生成车辆性能仪表盘"""
        try:
            # 收集性能数据
            performance_data = []
            for truck_id, route_data in route_solutions.items():
                if not route_data:
                    continue

                performance_data.append({
                    'truck_id': truck_id,
                    'distance': route_data.get('total_distance', 0),
                    'time': route_data.get('total_time', 0),
                    'stops': len(route_data.get('route_points', [])),
                    'cargo': len(route_data.get('cargo_list', [])),
                    'fuel_cost': route_data.get('fuel_cost', 0)
                })

            if not performance_data:
                return None

            df = pd.DataFrame(performance_data)

            fig = plt.figure(figsize=(16, 12))

            # 综合性能雷达图
            ax1 = fig.add_subplot(331, polar=True)
            self._create_radar_chart(ax1, df, '综合性能评估')

            # 距离分布
            ax2 = fig.add_subplot(332)
            ax2.pie(df['distance'], labels=df['truck_id'], autopct='%1.1f%%')
            ax2.set_title('距离分布')

            # 时间对比
            ax3 = fig.add_subplot(333)
            ax3.barh(df['truck_id'], df['time'], color='skyblue')
            ax3.set_title('运行时间对比')
            ax3.set_xlabel('时间 (小时)')

            # 停靠点数量
            ax4 = fig.add_subplot(334)
            ax4.bar(df['truck_id'], df['stops'], color='lightcoral')
            ax4.set_title('停靠点数量')
            ax4.set_ylabel('停靠次数')
            ax4.tick_params(axis='x', rotation=45)

            # 载货量
            ax5 = fig.add_subplot(335)
            ax5.bar(df['truck_id'], df['cargo'], color='lightgreen')
            ax5.set_title('载货量')
            ax5.set_ylabel('货物件数')
            ax5.tick_params(axis='x', rotation=45)

            # 燃油成本
            ax6 = fig.add_subplot(336)
            ax6.plot(df['truck_id'], df['fuel_cost'], 'o-', color='orange')
            ax6.set_title('燃油成本')
            ax6.set_ylabel('成本 (元)')
            ax6.tick_params(axis='x', rotation=45)

            # 效率散点矩阵
            ax7 = fig.add_subplot(337)
            ax7.scatter(df['distance'], df['time'], s=df['cargo']*5, alpha=0.6)
            ax7.set_xlabel('距离 (km)')
            ax7.set_ylabel('时间 (小时)')
            ax7.set_title('距离-时间关系')

            # 综合评分
            ax8 = fig.add_subplot(338)
            scores = self._calculate_performance_scores(df)
            ax8.bar(df['truck_id'], scores, color='gold')
            ax8.set_title('综合评分')
            ax8.set_ylabel('评分')
            ax8.tick_params(axis='x', rotation=45)

            # 关键指标汇总
            ax9 = fig.add_subplot(339)
            ax9.axis('off')
            summary_text = self._generate_summary_text(df)
            ax9.text(0.1, 0.9, summary_text, transform=ax9.transAxes, fontsize=10,
                    verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

            plt.suptitle('车辆性能仪表盘', fontsize=16)
            plt.tight_layout()

            # 保存图片
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filename = f"vehicle_performance_dashboard_{timestamp}.png"
            filepath = self.output_dir / filename
            plt.savefig(filepath, dpi=300, bbox_inches='tight')
            plt.close()

            return str(filepath)

        except Exception as e:
            print(f"[错误] 车辆性能仪表盘生成失败: {e}")
            return None

    def create_comprehensive_route_analysis(self, route_solutions: Dict) -> Optional[str]:
        """生成综合路径分析"""
        try:
            # 创建综合分析图
            fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 10))

            # 1. 路径网络图
            self._plot_route_network(ax1, route_solutions, '路径网络分析')

            # 2. 成本效益分析
            self._plot_cost_benefit_analysis(ax2, route_solutions, '成本效益分析')

            # 3. 时间分布分析
            self._plot_time_distribution(ax3, route_solutions, '时间分布分析')

            # 4. 优化建议
            self._plot_optimization_suggestions(ax4, route_solutions, '优化建议')

            plt.suptitle('综合路径分析报告', fontsize=16)
            plt.tight_layout()

            # 保存图片
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filename = f"comprehensive_route_analysis_{timestamp}.png"
            filepath = self.output_dir / filename
            plt.savefig(filepath, dpi=300, bbox_inches='tight')
            plt.close()

            return str(filepath)

        except Exception as e:
            print(f"[错误] 综合路径分析生成失败: {e}")
            return None

    def save_visualization(self, fig, filename: str) -> str:
        """保存可视化图片"""
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        full_filename = f"{filename}_{timestamp}.png"
        filepath = self.output_dir / full_filename

        if hasattr(fig, 'savefig'):
            fig.savefig(filepath, dpi=300, bbox_inches='tight')
        else:
            plt.savefig(filepath, dpi=300, bbox_inches='tight')

        return str(filepath)

    # 辅助方法
    def _plot_route_trajectory(self, ax, route_points: List, title: str):
        """绘制路径轨迹"""
        if not route_points:
            ax.text(0.5, 0.5, '无路径数据', ha='center', va='center', transform=ax.transAxes)
            ax.set_title(title)
            return

        # 模拟坐标数据（实际应用中需要真实的GPS坐标）
        x_coords = [i for i in range(len(route_points))]
        y_coords = [hash(str(point)) % 100 for point in route_points]

        ax.plot(x_coords, y_coords, 'o-', linewidth=2, markersize=6)
        ax.set_xlabel('路径点序号')
        ax.set_ylabel('位置(模拟)')
        ax.set_title(title)
        ax.grid(True, alpha=0.3)

    def _plot_distance_analysis(self, ax, route_points: List, title: str):
        """绘制距离分析"""
        if len(route_points) < 2:
            ax.text(0.5, 0.5, '路径点不足', ha='center', va='center', transform=ax.transAxes)
            ax.set_title(title)
            return

        # 模拟距离数据
        distances = [np.random.uniform(5, 50) for _ in range(len(route_points)-1)]
        cumulative_distances = np.cumsum([0] + distances)

        ax.plot(range(len(cumulative_distances)), cumulative_distances, 'b-', linewidth=2, label='累计距离')
        ax.bar(range(1, len(distances)+1), distances, alpha=0.6, label='段距离')
        ax.set_xlabel('路段')
        ax.set_ylabel('距离 (km)')
        ax.set_title(title)
        ax.legend()
        ax.grid(True, alpha=0.3)

    def _plot_time_analysis(self, ax, route_data: Dict, title: str):
        """绘制时间分析"""
        total_time = route_data.get('total_time', 8)
        stops = len(route_data.get('route_points', []))

        # 模拟时间分配
        driving_time = total_time * 0.7
        loading_time = total_time * 0.2
        waiting_time = total_time * 0.1

        labels = ['行驶时间', '装卸时间', '等待时间']
        sizes = [driving_time, loading_time, waiting_time]
        colors = ['lightblue', 'orange', 'lightcoral']

        ax.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90)
        ax.set_title(title)

    def _plot_efficiency_stats(self, ax, route_data: Dict, title: str):
        """绘制效率统计"""
        distance = route_data.get('total_distance', 100)
        time = route_data.get('total_time', 8)
        cargo_count = len(route_data.get('cargo_list', []))

        stats = ['距离\n(km)', '时间\n(小时)', '货物\n(件数)', '速度\n(km/h)']
        values = [distance, time, cargo_count, distance/time if time > 0 else 0]

        bars = ax.bar(stats, values, color=['blue', 'green', 'orange', 'red'], alpha=0.7)
        ax.set_title(title)
        ax.set_ylabel('数值')

        # 添加数值标签
        for bar, value in zip(bars, values):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{value:.1f}', ha='center', va='bottom')

    def _create_radar_chart(self, ax, df: pd.DataFrame, title: str):
        """创建雷达图"""
        if df.empty:
            return

        # 标准化数据
        metrics = ['distance', 'time', 'stops', 'cargo']
        angles = np.linspace(0, 2*np.pi, len(metrics), endpoint=False)

        for i, row in df.head(3).iterrows():  # 最多显示3辆车
            values = [row[metric] / df[metric].max() if df[metric].max() > 0 else 0 for metric in metrics]
            values += values[:1]  # 闭合
            angles_plot = np.concatenate((angles, [angles[0]]))
            ax.plot(angles_plot, values, 'o-', linewidth=2, label=row['truck_id'])

        ax.set_thetagrids(angles * 180/np.pi, metrics)
        ax.set_title(title)
        ax.legend()

    def _calculate_performance_scores(self, df: pd.DataFrame) -> List[float]:
        """计算性能评分"""
        scores = []
        for _, row in df.iterrows():
            # 简化的评分算法
            distance_score = 100 - (row['distance'] / df['distance'].max() * 50) if df['distance'].max() > 0 else 50
            time_score = 100 - (row['time'] / df['time'].max() * 30) if df['time'].max() > 0 else 50
            cargo_score = (row['cargo'] / df['cargo'].max() * 50) if df['cargo'].max() > 0 else 0

            total_score = distance_score + time_score + cargo_score
            scores.append(total_score)

        return scores

    def _generate_summary_text(self, df: pd.DataFrame) -> str:
        """生成汇总文本"""
        total_distance = df['distance'].sum()
        total_time = df['time'].sum()
        total_cargo = df['cargo'].sum()
        avg_distance = df['distance'].mean()

        return f"""运输概览:
总距离: {total_distance:.1f} km
总时间: {total_time:.1f} 小时
总货物: {total_cargo} 件
平均距离: {avg_distance:.1f} km
车辆数量: {len(df)} 辆
平均速度: {total_distance/total_time:.1f} km/h"""

    def _plot_route_network(self, ax, route_solutions: Dict, title: str):
        """绘制路径网络"""
        # 简化的网络图
        truck_count = len(route_solutions)
        if truck_count == 0:
            ax.text(0.5, 0.5, '无路径数据', ha='center', va='center', transform=ax.transAxes)
            ax.set_title(title)
            return

        # 创建简化的网络视图
        x = np.random.rand(truck_count)
        y = np.random.rand(truck_count)
        ax.scatter(x, y, s=100, alpha=0.7)

        for i, truck_id in enumerate(route_solutions.keys()):
            ax.annotate(truck_id, (x[i], y[i]), xytext=(5, 5), textcoords='offset points')

        ax.set_title(title)
        ax.set_xlabel('地理位置 X (模拟)')
        ax.set_ylabel('地理位置 Y (模拟)')

    def _plot_cost_benefit_analysis(self, ax, route_solutions: Dict, title: str):
        """绘制成本效益分析"""
        costs = []
        benefits = []
        truck_ids = []

        for truck_id, route_data in route_solutions.items():
            distance = route_data.get('total_distance', 0)
            cargo_count = len(route_data.get('cargo_list', []))

            cost = distance * 2  # 假设每公里2元
            benefit = cargo_count * 50  # 假设每件货物50元收益

            costs.append(cost)
            benefits.append(benefit)
            truck_ids.append(truck_id)

        if costs and benefits:
            ax.scatter(costs, benefits, alpha=0.7, s=100)
            for i, truck_id in enumerate(truck_ids):
                ax.annotate(truck_id, (costs[i], benefits[i]), xytext=(5, 5), textcoords='offset points')

            ax.set_xlabel('成本 (元)')
            ax.set_ylabel('收益 (元)')
            ax.plot([min(costs), max(costs)], [min(costs), max(costs)], 'r--', alpha=0.5, label='盈亏平衡线')
            ax.legend()

        ax.set_title(title)

    def _plot_time_distribution(self, ax, route_solutions: Dict, title: str):
        """绘制时间分布"""
        times = [route_data.get('total_time', 0) for route_data in route_solutions.values()]

        if times:
            ax.hist(times, bins=5, alpha=0.7, color='skyblue', edgecolor='black')
            ax.set_xlabel('运行时间 (小时)')
            ax.set_ylabel('车辆数量')
            ax.axvline(np.mean(times), color='red', linestyle='--', label=f'平均时间: {np.mean(times):.1f}h')
            ax.legend()

        ax.set_title(title)

    def _plot_optimization_suggestions(self, ax, route_solutions: Dict, title: str):
        """绘制优化建议"""
        ax.axis('off')

        suggestions = [
            "• 合并短距离路径以提高效率",
            "• 优化装载顺序减少配送时间",
            "• 考虑交通高峰期调整发车时间",
            "• 增加GPS跟踪提高调度准确性",
            "• 定期维护车辆保持最佳性能"
        ]

        suggestion_text = "优化建议:\n\n" + "\n".join(suggestions)
        ax.text(0.1, 0.9, suggestion_text, transform=ax.transAxes, fontsize=11,
               verticalalignment='top', bbox=dict(boxstyle='round', facecolor='lightgreen', alpha=0.7))

        ax.set_title(title)