"""
性能分析器
Performance Analyzer for detailed experiment performance analysis
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import logging

from database.db_manager import db_manager
from database.models import STANDARD_METRICS, MetricCategory

class PerformanceAnalyzer:
    """性能分析器 - 深度分析实验性能数据"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def analyze_experiment_performance(self, experiment_id: str) -> Dict[str, Any]:
        """
        全面分析单个实验的性能

        Args:
            experiment_id: 实验ID

        Returns:
            Dict: 性能分析结果
        """
        try:
            # 获取实验详细信息
            exp_detail = db_manager.get_experiment_detail(experiment_id)
            if not exp_detail:
                return {'error': f'实验 {experiment_id} 不存在'}

            analysis = {
                'experiment_info': {
                    'id': experiment_id,
                    'name': exp_detail['name'],
                    'algorithm': exp_detail['algorithm'],
                    'status': exp_detail['status'],
                    'created_at': exp_detail['created_at']
                },
                'vehicle_analysis': self._analyze_vehicle_performance(exp_detail['vehicles']),
                'metrics_analysis': self._analyze_metrics_performance(exp_detail['metrics']),
                'overall_score': 0,
                'recommendations': []
            }

            # 计算综合评分
            analysis['overall_score'] = self._calculate_overall_score(analysis)

            # 生成改进建议
            analysis['recommendations'] = self._generate_recommendations(analysis)

            return analysis

        except Exception as e:
            self.logger.error(f"实验性能分析失败: {str(e)}")
            return {'error': f'分析失败: {str(e)}'}

    def compare_algorithm_performance(self, algorithms: List[str] = None,
                                    time_period: int = 30) -> Dict[str, Any]:
        """
        对比不同算法的性能表现

        Args:
            algorithms: 算法列表，None则对比所有算法
            time_period: 时间段（天）

        Returns:
            Dict: 算法性能对比结果
        """
        try:
            # 获取实验数据
            experiments = db_manager.get_experiments(limit=1000)

            # 按算法分组
            algorithm_groups = {}
            for exp in experiments:
                if algorithms is None or exp['algorithm'] in algorithms:
                    alg = exp['algorithm']
                    if alg not in algorithm_groups:
                        algorithm_groups[alg] = []
                    algorithm_groups[alg].append(exp)

            comparison = {
                'algorithms': list(algorithm_groups.keys()),
                'comparison_data': {},
                'summary': {},
                'best_algorithm': None
            }

            # 分析每个算法
            for algorithm, exps in algorithm_groups.items():
                alg_analysis = self._analyze_algorithm_group(exps)
                comparison['comparison_data'][algorithm] = alg_analysis

            # 确定最佳算法
            comparison['best_algorithm'] = self._determine_best_algorithm(
                comparison['comparison_data']
            )

            # 生成对比摘要
            comparison['summary'] = self._generate_comparison_summary(
                comparison['comparison_data']
            )

            return comparison

        except Exception as e:
            self.logger.error(f"算法性能对比失败: {str(e)}")
            return {'error': f'对比失败: {str(e)}'}

    def analyze_efficiency_patterns(self, category: str = None) -> Dict[str, Any]:
        """
        分析效率模式和规律

        Args:
            category: 指标类别筛选

        Returns:
            Dict: 效率模式分析结果
        """
        try:
            # 获取所有实验的车辆数据
            experiments = db_manager.get_experiments(limit=1000)
            all_vehicles = []

            for exp in experiments:
                exp_detail = db_manager.get_experiment_detail(exp['experiment_id'])
                if exp_detail and exp_detail['vehicles']:
                    for vehicle in exp_detail['vehicles']:
                        vehicle['experiment_name'] = exp['name']
                        vehicle['experiment_algorithm'] = exp['algorithm']
                        all_vehicles.append(vehicle)

            if not all_vehicles:
                return {'error': '没有足够的车辆数据进行分析'}

            # 创建DataFrame进行分析
            df = pd.DataFrame(all_vehicles)

            analysis = {
                'total_vehicles_analyzed': len(all_vehicles),
                'efficiency_distribution': self._analyze_efficiency_distribution(df),
                'capacity_utilization': self._analyze_capacity_utilization(df),
                'vehicle_type_performance': self._analyze_vehicle_type_performance(df),
                'loading_patterns': self._identify_loading_patterns(df),
                'optimization_opportunities': []
            }

            # 识别优化机会
            analysis['optimization_opportunities'] = self._identify_optimization_opportunities(df)

            return analysis

        except Exception as e:
            self.logger.error(f"效率模式分析失败: {str(e)}")
            return {'error': f'分析失败: {str(e)}'}

    def generate_performance_report(self, experiment_ids: List[str] = None,
                                  include_visualizations: bool = True) -> Dict[str, Any]:
        """
        生成综合性能报告

        Args:
            experiment_ids: 实验ID列表，None则包含所有实验
            include_visualizations: 是否包含可视化数据

        Returns:
            Dict: 综合性能报告
        """
        try:
            if experiment_ids:
                experiments = [db_manager.get_experiment_detail(eid) for eid in experiment_ids]
                experiments = [exp for exp in experiments if exp]  # 过滤None
            else:
                exp_list = db_manager.get_experiments(limit=1000)
                experiments = [db_manager.get_experiment_detail(exp['experiment_id'])
                             for exp in exp_list]
                experiments = [exp for exp in experiments if exp]

            report = {
                'report_metadata': {
                    'generated_at': datetime.now().isoformat(),
                    'total_experiments': len(experiments),
                    'analysis_period': '全部历史数据'
                },
                'executive_summary': {},
                'detailed_analysis': {
                    'loading_performance': {},
                    'routing_performance': {},
                    'overall_performance': {}
                },
                'trends_and_patterns': {},
                'recommendations': []
            }

            # 执行摘要
            report['executive_summary'] = self._generate_executive_summary(experiments)

            # 详细分析
            report['detailed_analysis'] = self._generate_detailed_analysis(experiments)

            # 趋势和模式
            report['trends_and_patterns'] = self._analyze_trends_and_patterns(experiments)

            # 总体建议
            report['recommendations'] = self._generate_overall_recommendations(experiments)

            return report

        except Exception as e:
            self.logger.error(f"性能报告生成失败: {str(e)}")
            return {'error': f'报告生成失败: {str(e)}'}

    def _analyze_vehicle_performance(self, vehicles: List[Dict]) -> Dict[str, Any]:
        """分析车辆性能数据"""
        if not vehicles:
            return {'message': '无车辆数据'}

        df = pd.DataFrame(vehicles)

        analysis = {
            'total_vehicles': len(vehicles),
            'loading_efficiency': {
                'average': df['loading_efficiency'].mean() if 'loading_efficiency' in df else 0,
                'median': df['loading_efficiency'].median() if 'loading_efficiency' in df else 0,
                'std': df['loading_efficiency'].std() if 'loading_efficiency' in df else 0,
                'min': df['loading_efficiency'].min() if 'loading_efficiency' in df else 0,
                'max': df['loading_efficiency'].max() if 'loading_efficiency' in df else 0
            },
            'capacity_utilization': {
                'volume_utilization': (df['actual_volume'] / df['capacity_volume']).mean()
                                    if 'actual_volume' in df and 'capacity_volume' in df else 0,
                'weight_utilization': (df['actual_weight'] / df['capacity_weight']).mean()
                                    if 'actual_weight' in df and 'capacity_weight' in df else 0
            },
            'routing_performance': {
                'average_distance': df['route_distance'].mean() if 'route_distance' in df else 0,
                'average_duration': df['route_duration'].mean() if 'route_duration' in df else 0,
                'total_distance': df['route_distance'].sum() if 'route_distance' in df else 0
            }
        }

        return analysis

    def _analyze_metrics_performance(self, metrics: List[Dict]) -> Dict[str, Any]:
        """分析性能指标数据"""
        if not metrics:
            return {'message': '无性能指标数据'}

        metrics_by_category = {}
        for metric in metrics:
            category = metric.get('category', 'overall')
            if category not in metrics_by_category:
                metrics_by_category[category] = []
            metrics_by_category[category].append(metric)

        analysis = {}
        for category, cat_metrics in metrics_by_category.items():
            analysis[category] = {}
            for metric in cat_metrics:
                analysis[category][metric['metric_name']] = {
                    'value': metric['metric_value'],
                    'unit': metric.get('metric_unit', ''),
                    'calculated_at': metric.get('calculated_at', '')
                }

        return analysis

    def _calculate_overall_score(self, analysis: Dict) -> float:
        """计算综合评分"""
        try:
            score_components = []

            # 装载效率评分 (0-40分)
            vehicle_analysis = analysis.get('vehicle_analysis', {})
            loading_eff = vehicle_analysis.get('loading_efficiency', {}).get('average', 0)
            if loading_eff > 0:
                loading_score = min(loading_eff * 0.4, 40)  # 最高40分
                score_components.append(loading_score)

            # 容量利用率评分 (0-30分)
            capacity_util = vehicle_analysis.get('capacity_utilization', {})
            vol_util = capacity_util.get('volume_utilization', 0)
            weight_util = capacity_util.get('weight_utilization', 0)
            if vol_util > 0 or weight_util > 0:
                capacity_score = min((vol_util + weight_util) / 2 * 30, 30)
                score_components.append(capacity_score)

            # 路径效率评分 (0-30分)
            route_perf = vehicle_analysis.get('routing_performance', {})
            avg_distance = route_perf.get('average_distance', 0)
            if avg_distance > 0:
                # 简化评分：距离越短评分越高（需要基准值调整）
                route_score = max(30 - (avg_distance / 100), 0)
                score_components.append(route_score)

            return sum(score_components) if score_components else 0

        except Exception:
            return 0

    def _generate_recommendations(self, analysis: Dict) -> List[str]:
        """生成改进建议"""
        recommendations = []

        try:
            vehicle_analysis = analysis.get('vehicle_analysis', {})

            # 装载效率建议
            loading_eff = vehicle_analysis.get('loading_efficiency', {}).get('average', 0)
            if loading_eff < 60:
                recommendations.append("装载效率偏低，建议优化装载算法或调整货物分配策略")

            # 容量利用率建议
            capacity_util = vehicle_analysis.get('capacity_utilization', {})
            vol_util = capacity_util.get('volume_utilization', 0)
            weight_util = capacity_util.get('weight_utilization', 0)

            if vol_util < 0.8:
                recommendations.append("体积利用率有提升空间，考虑优化货物排列方式")

            if weight_util < 0.8:
                recommendations.append("重量利用率有提升空间，考虑调整货物重量分配")

            # 路径优化建议
            route_perf = vehicle_analysis.get('routing_performance', {})
            if route_perf.get('average_distance', 0) > 200:
                recommendations.append("平均路径距离较长，建议优化路径规划算法")

        except Exception:
            recommendations.append("数据分析异常，建议检查数据质量")

        return recommendations if recommendations else ["当前性能表现良好，继续保持"]

    def _analyze_algorithm_group(self, experiments: List[Dict]) -> Dict[str, Any]:
        """分析算法组的性能数据"""
        if not experiments:
            return {}

        # 收集所有性能指标
        all_metrics = {}
        experiment_count = len(experiments)

        for exp in experiments:
            exp_detail = db_manager.get_experiment_detail(exp['experiment_id'])
            if exp_detail and exp_detail['metrics']:
                for metric in exp_detail['metrics']:
                    metric_name = metric['metric_name']
                    if metric_name not in all_metrics:
                        all_metrics[metric_name] = []
                    all_metrics[metric_name].append(metric['metric_value'])

        # 计算统计值
        statistics = {}
        for metric_name, values in all_metrics.items():
            if values:
                statistics[metric_name] = {
                    'mean': np.mean(values),
                    'median': np.median(values),
                    'std': np.std(values),
                    'min': min(values),
                    'max': max(values),
                    'count': len(values)
                }

        return {
            'experiment_count': experiment_count,
            'performance_statistics': statistics,
            'success_rate': len([exp for exp in experiments if exp['status'] == 'completed']) / experiment_count if experiment_count > 0 else 0
        }

    def _determine_best_algorithm(self, comparison_data: Dict) -> Optional[str]:
        """确定最佳算法"""
        if not comparison_data:
            return None

        scores = {}
        for algorithm, data in comparison_data.items():
            score = 0
            stats = data.get('performance_statistics', {})

            # 基于多个指标计算综合得分
            loading_eff = stats.get('loading_efficiency', {}).get('mean', 0)
            score += loading_eff * 0.4

            vehicle_util = stats.get('vehicle_utilization', {}).get('mean', 0)
            score += vehicle_util * 0.3

            success_rate = data.get('success_rate', 0)
            score += success_rate * 100 * 0.3

            scores[algorithm] = score

        return max(scores.items(), key=lambda x: x[1])[0] if scores else None

    def _generate_comparison_summary(self, comparison_data: Dict) -> Dict[str, Any]:
        """生成对比摘要"""
        if not comparison_data:
            return {}

        total_experiments = sum(data.get('experiment_count', 0) for data in comparison_data.values())

        return {
            'total_algorithms_compared': len(comparison_data),
            'total_experiments_analyzed': total_experiments,
            'summary_by_algorithm': {
                alg: {
                    'experiments': data.get('experiment_count', 0),
                    'success_rate': f"{data.get('success_rate', 0)*100:.1f}%",
                    'avg_loading_efficiency': data.get('performance_statistics', {}).get('loading_efficiency', {}).get('mean', 0)
                }
                for alg, data in comparison_data.items()
            }
        }

    def _analyze_efficiency_distribution(self, df: pd.DataFrame) -> Dict[str, Any]:
        """分析效率分布"""
        if 'loading_efficiency' not in df.columns:
            return {'message': '缺少装载效率数据'}

        efficiency_data = df['loading_efficiency'].dropna()
        if efficiency_data.empty:
            return {'message': '无有效装载效率数据'}

        return {
            'mean': efficiency_data.mean(),
            'median': efficiency_data.median(),
            'std': efficiency_data.std(),
            'quartiles': {
                'q1': efficiency_data.quantile(0.25),
                'q2': efficiency_data.quantile(0.5),
                'q3': efficiency_data.quantile(0.75)
            },
            'distribution_bins': self._create_efficiency_bins(efficiency_data)
        }

    def _analyze_capacity_utilization(self, df: pd.DataFrame) -> Dict[str, Any]:
        """分析容量利用率"""
        analysis = {}

        if 'actual_volume' in df.columns and 'capacity_volume' in df.columns:
            vol_util = (df['actual_volume'] / df['capacity_volume']).dropna()
            analysis['volume_utilization'] = {
                'mean': vol_util.mean(),
                'median': vol_util.median(),
                'std': vol_util.std()
            }

        if 'actual_weight' in df.columns and 'capacity_weight' in df.columns:
            weight_util = (df['actual_weight'] / df['capacity_weight']).dropna()
            analysis['weight_utilization'] = {
                'mean': weight_util.mean(),
                'median': weight_util.median(),
                'std': weight_util.std()
            }

        return analysis

    def _analyze_vehicle_type_performance(self, df: pd.DataFrame) -> Dict[str, Any]:
        """分析不同车辆类型的性能"""
        if 'vehicle_type' not in df.columns:
            return {'message': '缺少车辆类型数据'}

        type_analysis = {}
        for vehicle_type in df['vehicle_type'].unique():
            type_df = df[df['vehicle_type'] == vehicle_type]

            type_analysis[vehicle_type] = {
                'count': len(type_df),
                'avg_loading_efficiency': type_df['loading_efficiency'].mean() if 'loading_efficiency' in type_df else 0,
                'avg_capacity_volume': type_df['capacity_volume'].mean() if 'capacity_volume' in type_df else 0,
                'avg_route_distance': type_df['route_distance'].mean() if 'route_distance' in type_df else 0
            }

        return type_analysis

    def _identify_loading_patterns(self, df: pd.DataFrame) -> Dict[str, Any]:
        """识别装载模式"""
        patterns = {
            'high_efficiency_vehicles': len(df[df['loading_efficiency'] > 80]) if 'loading_efficiency' in df else 0,
            'medium_efficiency_vehicles': len(df[(df['loading_efficiency'] >= 60) & (df['loading_efficiency'] <= 80)]) if 'loading_efficiency' in df else 0,
            'low_efficiency_vehicles': len(df[df['loading_efficiency'] < 60]) if 'loading_efficiency' in df else 0,
            'underutilized_vehicles': len(df[(df['actual_volume'] / df['capacity_volume'] < 0.5) |
                                          (df['actual_weight'] / df['capacity_weight'] < 0.5)]) if all(col in df for col in ['actual_volume', 'capacity_volume', 'actual_weight', 'capacity_weight']) else 0
        }

        return patterns

    def _identify_optimization_opportunities(self, df: pd.DataFrame) -> List[str]:
        """识别优化机会"""
        opportunities = []

        # 装载效率优化
        if 'loading_efficiency' in df.columns:
            low_eff_count = len(df[df['loading_efficiency'] < 60])
            if low_eff_count > 0:
                opportunities.append(f"有{low_eff_count}辆车装载效率低于60%，建议优化装载策略")

        # 容量利用优化
        if all(col in df for col in ['actual_volume', 'capacity_volume']):
            underutilized_vol = len(df[df['actual_volume'] / df['capacity_volume'] < 0.7])
            if underutilized_vol > 0:
                opportunities.append(f"有{underutilized_vol}辆车体积利用率低于70%，考虑调整货物分配")

        # 路径优化
        if 'route_distance' in df.columns:
            high_distance_count = len(df[df['route_distance'] > df['route_distance'].quantile(0.8)])
            if high_distance_count > 0:
                opportunities.append(f"有{high_distance_count}辆车路径距离较长，建议优化路径规划")

        return opportunities if opportunities else ["当前运营效率良好"]

    def _create_efficiency_bins(self, efficiency_data: pd.Series) -> List[Dict]:
        """创建效率分布区间"""
        bins = [0, 40, 60, 80, 100]
        labels = ['低效率(0-40%)', '中低效率(40-60%)', '中等效率(60-80%)', '高效率(80-100%)']

        hist, _ = np.histogram(efficiency_data, bins=bins)

        return [
            {'range': labels[i], 'count': int(hist[i]), 'percentage': (hist[i] / len(efficiency_data)) * 100}
            for i in range(len(labels))
        ]

    def _generate_executive_summary(self, experiments: List[Dict]) -> Dict[str, Any]:
        """生成执行摘要"""
        total_vehicles = sum(len(exp.get('vehicles', [])) for exp in experiments)
        completed_experiments = len([exp for exp in experiments if exp['status'] == 'completed'])

        return {
            'total_experiments': len(experiments),
            'completed_experiments': completed_experiments,
            'success_rate': f"{(completed_experiments / len(experiments) * 100):.1f}%" if experiments else "0%",
            'total_vehicles_analyzed': total_vehicles,
            'analysis_period': f"{min(exp['created_at'] for exp in experiments)} 至 {max(exp['created_at'] for exp in experiments)}" if experiments else "无数据"
        }

    def _generate_detailed_analysis(self, experiments: List[Dict]) -> Dict[str, Any]:
        """生成详细分析"""
        # 这里可以进一步细化，目前返回基本结构
        return {
            'loading_performance': {'message': '装载性能分析'},
            'routing_performance': {'message': '路径性能分析'},
            'overall_performance': {'message': '综合性能分析'}
        }

    def _analyze_trends_and_patterns(self, experiments: List[Dict]) -> Dict[str, Any]:
        """分析趋势和模式"""
        return {
            'temporal_trends': {'message': '时间趋势分析'},
            'algorithm_patterns': {'message': '算法模式分析'},
            'efficiency_patterns': {'message': '效率模式分析'}
        }

    def _generate_overall_recommendations(self, experiments: List[Dict]) -> List[str]:
        """生成总体建议"""
        return [
            "基于历史数据分析，建议持续监控装载效率指标",
            "考虑在装载效率低于60%时采用更优算法",
            "建议定期进行路径优化评估"
        ]

# 全局性能分析器实例
performance_analyzer = PerformanceAnalyzer()