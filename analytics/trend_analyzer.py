"""
趋势分析器
Trend Analyzer for performance metrics over time
"""

import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from scipy import stats
import logging

from database.db_manager import db_manager
from database.models import TrendAnalysis, MetricCategory, STANDARD_METRICS

class TrendAnalyzer:
    """趋势分析器 - 分析性能指标的时间序列趋势"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def analyze_metric_trend(self, metric_name: str, time_period: str = '30days',
                            category: str = None) -> TrendAnalysis:
        """
        分析指定指标的趋势

        Args:
            metric_name: 指标名称
            time_period: 时间段 ('7days', '30days', '90days')
            category: 指标类别筛选

        Returns:
            TrendAnalysis: 趋势分析结果
        """
        try:
            days = self._parse_time_period(time_period)

            # 获取趋势数据
            trend_data = db_manager.get_performance_trends(
                metric_name=metric_name,
                category=category,
                days=days
            )

            if not trend_data:
                return self._create_empty_trend_analysis(metric_name, category, time_period)

            # 处理数据点
            data_points = []
            values = []
            timestamps = []

            for point in trend_data:
                data_points.append({
                    'experiment_id': point['experiment_id'],
                    'name': point['name'],
                    'timestamp': point['created_at'],
                    'value': point['metric_value'],
                    'unit': point['metric_unit']
                })
                values.append(point['metric_value'])
                timestamps.append(datetime.fromisoformat(point['created_at'].replace('Z', '+00:00')))

            # 趋势分析
            trend_direction, trend_strength = self._calculate_trend(values, timestamps)
            analysis_summary = self._generate_trend_summary(
                metric_name, values, trend_direction, trend_strength
            )

            return TrendAnalysis(
                metric_name=metric_name,
                category=category or 'all',
                time_period=time_period,
                data_points=data_points,
                trend_direction=trend_direction,
                trend_strength=trend_strength,
                analysis_summary=analysis_summary,
                generated_at=datetime.now()
            )

        except Exception as e:
            self.logger.error(f"趋势分析失败: {str(e)}")
            return self._create_empty_trend_analysis(metric_name, category, time_period)

    def analyze_all_metrics_trends(self, time_period: str = '30days') -> Dict[str, TrendAnalysis]:
        """分析所有标准指标的趋势"""
        results = {}

        for metric_name in STANDARD_METRICS.keys():
            try:
                trend_analysis = self.analyze_metric_trend(metric_name, time_period)
                if trend_analysis.data_points:  # 只保存有数据的分析
                    results[metric_name] = trend_analysis
            except Exception as e:
                self.logger.warning(f"分析指标 {metric_name} 趋势失败: {str(e)}")

        return results

    def compare_metric_periods(self, metric_name: str,
                              periods: List[str] = None) -> Dict[str, TrendAnalysis]:
        """对比不同时间段的指标趋势"""
        if not periods:
            periods = ['7days', '30days', '90days']

        comparisons = {}

        for period in periods:
            try:
                analysis = self.analyze_metric_trend(metric_name, period)
                comparisons[period] = analysis
            except Exception as e:
                self.logger.warning(f"对比时间段 {period} 失败: {str(e)}")

        return comparisons

    def detect_anomalies(self, metric_name: str, time_period: str = '30days',
                        threshold_factor: float = 2.0) -> List[Dict]:
        """检测指标异常值"""
        try:
            trend_data = db_manager.get_performance_trends(
                metric_name=metric_name,
                days=self._parse_time_period(time_period)
            )

            if len(trend_data) < 3:
                return []

            values = [point['metric_value'] for point in trend_data]
            mean_val = np.mean(values)
            std_val = np.std(values)

            anomalies = []
            for i, point in enumerate(trend_data):
                z_score = abs((point['metric_value'] - mean_val) / std_val) if std_val > 0 else 0

                if z_score > threshold_factor:
                    anomalies.append({
                        'experiment_id': point['experiment_id'],
                        'name': point['name'],
                        'value': point['metric_value'],
                        'z_score': z_score,
                        'timestamp': point['created_at'],
                        'deviation_type': 'high' if point['metric_value'] > mean_val else 'low'
                    })

            return sorted(anomalies, key=lambda x: x['z_score'], reverse=True)

        except Exception as e:
            self.logger.error(f"异常检测失败: {str(e)}")
            return []

    def calculate_improvement_rate(self, metric_name: str, time_period: str = '30days') -> Dict:
        """计算指标改进率"""
        try:
            trend_data = db_manager.get_performance_trends(
                metric_name=metric_name,
                days=self._parse_time_period(time_period)
            )

            if len(trend_data) < 2:
                return {'improvement_rate': 0, 'confidence': 'low', 'data_points': len(trend_data)}

            # 按时间排序
            trend_data.sort(key=lambda x: x['created_at'])

            # 计算改进率
            first_half = trend_data[:len(trend_data)//2]
            second_half = trend_data[len(trend_data)//2:]

            first_avg = np.mean([p['metric_value'] for p in first_half])
            second_avg = np.mean([p['metric_value'] for p in second_half])

            improvement_rate = ((second_avg - first_avg) / first_avg) * 100 if first_avg != 0 else 0

            # 置信度评估
            confidence = 'high' if len(trend_data) >= 10 else 'medium' if len(trend_data) >= 5 else 'low'

            return {
                'improvement_rate': improvement_rate,
                'first_period_avg': first_avg,
                'second_period_avg': second_avg,
                'confidence': confidence,
                'data_points': len(trend_data)
            }

        except Exception as e:
            self.logger.error(f"改进率计算失败: {str(e)}")
            return {'improvement_rate': 0, 'confidence': 'error', 'data_points': 0}

    def _parse_time_period(self, time_period: str) -> int:
        """解析时间段字符串为天数"""
        period_map = {
            '7days': 7,
            '30days': 30,
            '90days': 90,
            '1year': 365
        }
        return period_map.get(time_period, 30)

    def _calculate_trend(self, values: List[float], timestamps: List[datetime]) -> Tuple[str, float]:
        """计算趋势方向和强度"""
        if len(values) < 2:
            return 'stable', 0.0

        try:
            # 将时间戳转换为数值
            time_numeric = [(ts - timestamps[0]).total_seconds() for ts in timestamps]

            # 计算线性回归
            slope, intercept, r_value, p_value, std_err = stats.linregress(time_numeric, values)

            # 确定趋势方向
            if abs(slope) < 0.001:  # 阈值可调整
                direction = 'stable'
            elif slope > 0:
                direction = 'increasing'
            else:
                direction = 'decreasing'

            # 趋势强度 (基于R²值)
            strength = abs(r_value) if not np.isnan(r_value) else 0.0

            return direction, strength

        except Exception as e:
            self.logger.warning(f"趋势计算失败: {str(e)}")
            return 'stable', 0.0

    def _generate_trend_summary(self, metric_name: str, values: List[float],
                               direction: str, strength: float) -> str:
        """生成趋势分析摘要"""
        metric_info = STANDARD_METRICS.get(metric_name, {})
        metric_display_name = metric_info.get('name', metric_name)

        if not values:
            return f"{metric_display_name}暂无足够数据进行趋势分析"

        avg_value = np.mean(values)
        min_value = min(values)
        max_value = max(values)

        strength_desc = '强烈' if strength > 0.7 else '中等' if strength > 0.4 else '微弱'

        if direction == 'increasing':
            trend_desc = f"呈{strength_desc}上升趋势"
        elif direction == 'decreasing':
            trend_desc = f"呈{strength_desc}下降趋势"
        else:
            trend_desc = "保持相对稳定"

        return f"{metric_display_name}{trend_desc}，平均值为{avg_value:.2f}，范围在{min_value:.2f}到{max_value:.2f}之间"

    def _create_empty_trend_analysis(self, metric_name: str, category: str,
                                   time_period: str) -> TrendAnalysis:
        """创建空的趋势分析结果"""
        return TrendAnalysis(
            metric_name=metric_name,
            category=category or 'all',
            time_period=time_period,
            data_points=[],
            trend_direction='stable',
            trend_strength=0.0,
            analysis_summary=f"指标 {metric_name} 在指定时间段内暂无数据",
            generated_at=datetime.now()
        )

# 全局趋势分析器实例
trend_analyzer = TrendAnalyzer()