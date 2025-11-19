"""
实验对比引擎
Comparison Engine for analyzing experiment results
"""

import json
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import logging
import statistics

from database.db_manager import db_manager
from database.models import STANDARD_METRICS

class ComparisonEngine:
    """实验对比分析引擎"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def compare_experiments(self, experiment_ids: List[str],
                          metrics: List[str] = None) -> Dict[str, Any]:
        """
        对比多个实验的结果

        Args:
            experiment_ids: 实验ID列表
            metrics: 要对比的指标列表

        Returns:
            Dict: 对比结果
        """
        try:
            if not experiment_ids:
                return {'error': '没有指定实验ID'}

            if not metrics:
                metrics = ['loading_efficiency', 'total_distance', 'vehicle_utilization']

            # 获取实验详细数据
            experiments_data = {}
            for exp_id in experiment_ids:
                exp_detail = db_manager.get_experiment_detail(exp_id)
                if exp_detail:
                    experiments_data[exp_id] = exp_detail

            if not experiments_data:
                return {'error': '没有找到有效的实验数据'}

            # 生成对比分析
            comparison_result = {
                'experiment_count': len(experiments_data),
                'metrics': metrics,
                'comparison_data': {},
                'summary': {},
                'recommendations': [],
                'generated_at': datetime.now().isoformat()
            }

            # 对比每个指标
            for metric in metrics:
                comparison_result['comparison_data'][metric] = self._compare_metric(
                    experiments_data, metric
                )

            # 生成综合分析摘要
            comparison_result['summary'] = self._generate_comparison_summary(
                experiments_data, comparison_result['comparison_data']
            )

            # 生成优化建议
            comparison_result['recommendations'] = self._generate_recommendations(
                experiments_data, comparison_result['comparison_data']
            )

            return comparison_result

        except Exception as e:
            self.logger.error(f"实验对比失败: {str(e)}")
            return {'error': f'对比失败: {str(e)}'}

    def compare_algorithms(self, algorithm_names: List[str],
                          time_period: int = 30) -> Dict[str, Any]:
        """
        对比不同算法的性能

        Args:
            algorithm_names: 算法名称列表
            time_period: 时间范围（天）

        Returns:
            Dict: 算法对比结果
        """
        try:
            # 获取指定时间内的实验数据
            experiments = db_manager.get_experiments(limit=1000)

            # 按算法分组
            algorithm_experiments = {}
            cutoff_date = datetime.now() - timedelta(days=time_period)

            for exp in experiments:
                exp_date = datetime.fromisoformat(exp['created_at'].replace('Z', '+00:00').replace('+00:00', ''))
                if (exp['algorithm'] in algorithm_names and
                    exp['status'] == 'completed' and
                    exp_date >= cutoff_date):

                    if exp['algorithm'] not in algorithm_experiments:
                        algorithm_experiments[exp['algorithm']] = []
                    algorithm_experiments[exp['algorithm']].append(exp['experiment_id'])

            if not algorithm_experiments:
                return {'error': '指定时间范围内没有找到相关实验'}

            # 对每个算法进行分析
            algorithm_comparison = {}
            for algorithm, exp_ids in algorithm_experiments.items():
                if exp_ids:
                    # 获取该算法的平均性能
                    avg_metrics = self._calculate_average_metrics(exp_ids)
                    experiment_count = len(exp_ids)

                    algorithm_comparison[algorithm] = {
                        'experiment_count': experiment_count,
                        'average_metrics': avg_metrics,
                        'best_experiment': self._find_best_experiment(exp_ids),
                        'consistency_score': self._calculate_consistency(exp_ids)
                    }

            # 生成算法排名
            rankings = self._rank_algorithms(algorithm_comparison)

            return {
                'algorithm_comparison': algorithm_comparison,
                'rankings': rankings,
                'time_period_days': time_period,
                'generated_at': datetime.now().isoformat()
            }

        except Exception as e:
            self.logger.error(f"算法对比失败: {str(e)}")
            return {'error': f'算法对比失败: {str(e)}'}

    def analyze_trends(self, metric_name: str, category: str = None,
                      days: int = 30) -> Dict[str, Any]:
        """
        分析指标趋势

        Args:
            metric_name: 指标名称
            category: 指标类别
            days: 分析天数

        Returns:
            Dict: 趋势分析结果
        """
        try:
            # 获取趋势数据
            trend_data = db_manager.get_performance_trends(metric_name, category, days)

            if not trend_data:
                return {'error': f'没有找到指标 {metric_name} 的趋势数据'}

            # 分析趋势
            trend_analysis = self._analyze_trend_data(trend_data)

            # 计算统计信息
            values = [point['metric_value'] for point in trend_data]
            statistics_info = {
                'count': len(values),
                'mean': statistics.mean(values),
                'median': statistics.median(values),
                'std_dev': statistics.stdev(values) if len(values) > 1 else 0,
                'min': min(values),
                'max': max(values)
            }

            return {
                'metric_name': metric_name,
                'category': category,
                'time_period_days': days,
                'data_points': trend_data,
                'trend_analysis': trend_analysis,
                'statistics': statistics_info,
                'generated_at': datetime.now().isoformat()
            }

        except Exception as e:
            self.logger.error(f"趋势分析失败: {str(e)}")
            return {'error': f'趋势分析失败: {str(e)}'}

    def find_similar_experiments(self, experiment_id: str,
                                similarity_threshold: float = 0.8) -> List[Dict]:
        """
        查找相似的实验

        Args:
            experiment_id: 基准实验ID
            similarity_threshold: 相似度阈值

        Returns:
            List: 相似实验列表
        """
        try:
            base_experiment = db_manager.get_experiment_detail(experiment_id)
            if not base_experiment:
                return []

            # 获取所有完成的实验
            all_experiments = db_manager.get_experiments(limit=1000)
            completed_experiments = [exp for exp in all_experiments
                                   if exp['status'] == 'completed'
                                   and exp['experiment_id'] != experiment_id]

            similar_experiments = []

            for exp in completed_experiments:
                exp_detail = db_manager.get_experiment_detail(exp['experiment_id'])
                if exp_detail:
                    similarity_score = self._calculate_similarity(base_experiment, exp_detail)

                    if similarity_score >= similarity_threshold:
                        similar_experiments.append({
                            'experiment_id': exp['experiment_id'],
                            'name': exp['name'],
                            'similarity_score': similarity_score,
                            'algorithm': exp['algorithm'],
                            'created_at': exp['created_at']
                        })

            # 按相似度排序
            similar_experiments.sort(key=lambda x: x['similarity_score'], reverse=True)

            return similar_experiments

        except Exception as e:
            self.logger.error(f"查找相似实验失败: {str(e)}")
            return []

    def _compare_metric(self, experiments_data: Dict, metric: str) -> Dict:
        """对比单个指标"""
        metric_comparison = {
            'metric_name': metric,
            'experiments': {},
            'best_performer': None,
            'worst_performer': None,
            'improvement_opportunities': []
        }

        metric_values = {}

        # 收集每个实验的指标值
        for exp_id, exp_data in experiments_data.items():
            metric_value = None

            # 从性能指标中查找
            for metric_record in exp_data.get('metrics', []):
                if metric_record['metric_name'] == metric:
                    metric_value = metric_record['metric_value']
                    break

            # 如果没找到，尝试从车辆数据中计算
            if metric_value is None:
                metric_value = self._calculate_metric_from_vehicles(
                    exp_data.get('vehicles', []), metric
                )

            if metric_value is not None:
                metric_values[exp_id] = metric_value
                metric_comparison['experiments'][exp_id] = {
                    'value': metric_value,
                    'experiment_name': exp_data['name']
                }

        # 找出最佳和最差表现
        if metric_values:
            # 对于大多数指标，值越大越好，但距离类指标除外
            if metric in ['total_distance']:  # 距离越小越好
                best_exp = min(metric_values.items(), key=lambda x: x[1])
                worst_exp = max(metric_values.items(), key=lambda x: x[1])
            else:  # 效率类指标越大越好
                best_exp = max(metric_values.items(), key=lambda x: x[1])
                worst_exp = min(metric_values.items(), key=lambda x: x[1])

            metric_comparison['best_performer'] = {
                'experiment_id': best_exp[0],
                'value': best_exp[1]
            }
            metric_comparison['worst_performer'] = {
                'experiment_id': worst_exp[0],
                'value': worst_exp[1]
            }

        return metric_comparison

    def _generate_comparison_summary(self, experiments_data: Dict,
                                   comparison_data: Dict) -> Dict:
        """生成对比摘要"""
        summary = {
            'total_experiments': len(experiments_data),
            'algorithms_used': [],
            'date_range': {'earliest': None, 'latest': None},
            'key_findings': []
        }

        # 收集使用的算法
        algorithms = set()
        dates = []

        for exp_data in experiments_data.values():
            algorithms.add(exp_data['algorithm'])
            if exp_data['created_at']:
                dates.append(exp_data['created_at'])

        summary['algorithms_used'] = list(algorithms)

        if dates:
            dates.sort()
            summary['date_range']['earliest'] = dates[0]
            summary['date_range']['latest'] = dates[-1]

        # 生成关键发现
        for metric, metric_data in comparison_data.items():
            if metric_data.get('best_performer') and metric_data.get('worst_performer'):
                best_value = metric_data['best_performer']['value']
                worst_value = metric_data['worst_performer']['value']

                if best_value != worst_value:
                    improvement_pct = abs((best_value - worst_value) / worst_value * 100)
                    summary['key_findings'].append(
                        f"{metric}: 最佳与最差相差 {improvement_pct:.1f}%"
                    )

        return summary

    def _generate_recommendations(self, experiments_data: Dict,
                                comparison_data: Dict) -> List[str]:
        """生成优化建议"""
        recommendations = []

        try:
            # 基于对比结果生成建议
            for metric, metric_data in comparison_data.items():
                best_exp_id = metric_data.get('best_performer', {}).get('experiment_id')
                worst_exp_id = metric_data.get('worst_performer', {}).get('experiment_id')

                if best_exp_id and worst_exp_id:
                    best_exp = experiments_data[best_exp_id]
                    worst_exp = experiments_data[worst_exp_id]

                    if best_exp['algorithm'] != worst_exp['algorithm']:
                        recommendations.append(
                            f"对于 {metric}，考虑使用 {best_exp['algorithm']} "
                            f"算法替代 {worst_exp['algorithm']}"
                        )

            # 通用建议
            if len(recommendations) == 0:
                recommendations.append("所有实验表现相近，继续保持当前配置")

        except Exception as e:
            self.logger.error(f"生成建议失败: {str(e)}")

        return recommendations

    def _calculate_average_metrics(self, experiment_ids: List[str]) -> Dict:
        """计算平均指标"""
        all_metrics = {}

        for exp_id in experiment_ids:
            exp_detail = db_manager.get_experiment_detail(exp_id)
            if exp_detail:
                for metric in exp_detail.get('metrics', []):
                    metric_name = metric['metric_name']
                    metric_value = metric['metric_value']

                    if metric_name not in all_metrics:
                        all_metrics[metric_name] = []
                    all_metrics[metric_name].append(metric_value)

        # 计算平均值
        avg_metrics = {}
        for metric_name, values in all_metrics.items():
            if values:
                avg_metrics[metric_name] = {
                    'average': sum(values) / len(values),
                    'count': len(values),
                    'min': min(values),
                    'max': max(values)
                }

        return avg_metrics

    def _find_best_experiment(self, experiment_ids: List[str]) -> Optional[Dict]:
        """找到最佳实验"""
        best_experiment = None
        best_score = -1

        for exp_id in experiment_ids:
            exp_detail = db_manager.get_experiment_detail(exp_id)
            if exp_detail:
                # 简单的评分机制：装载效率权重高
                score = 0
                for metric in exp_detail.get('metrics', []):
                    if metric['metric_name'] == 'loading_efficiency':
                        score += metric['metric_value'] * 0.4
                    elif metric['metric_name'] == 'vehicle_utilization':
                        score += metric['metric_value'] * 0.3
                    elif metric['metric_name'] == 'order_fulfillment_rate':
                        score += metric['metric_value'] * 0.3

                if score > best_score:
                    best_score = score
                    best_experiment = {
                        'experiment_id': exp_id,
                        'name': exp_detail['name'],
                        'score': score
                    }

        return best_experiment

    def _calculate_consistency(self, experiment_ids: List[str]) -> float:
        """计算算法一致性得分"""
        if len(experiment_ids) < 2:
            return 1.0

        # 收集装载效率数据
        efficiencies = []
        for exp_id in experiment_ids:
            exp_detail = db_manager.get_experiment_detail(exp_id)
            if exp_detail:
                for metric in exp_detail.get('metrics', []):
                    if metric['metric_name'] == 'loading_efficiency':
                        efficiencies.append(metric['metric_value'])
                        break

        if len(efficiencies) < 2:
            return 1.0

        # 计算变异系数（标准差/均值）
        mean_efficiency = statistics.mean(efficiencies)
        std_efficiency = statistics.stdev(efficiencies)

        if mean_efficiency > 0:
            cv = std_efficiency / mean_efficiency
            consistency_score = max(0, 1 - cv)  # 变异系数越小，一致性越高
        else:
            consistency_score = 0

        return consistency_score

    def _rank_algorithms(self, algorithm_comparison: Dict) -> Dict:
        """算法排名"""
        rankings = {}

        # 按平均装载效率排名
        loading_efficiency_ranking = []
        for algorithm, data in algorithm_comparison.items():
            avg_metrics = data.get('average_metrics', {})
            loading_eff = avg_metrics.get('loading_efficiency', {}).get('average', 0)
            loading_efficiency_ranking.append((algorithm, loading_eff))

        loading_efficiency_ranking.sort(key=lambda x: x[1], reverse=True)
        rankings['loading_efficiency'] = [
            {'algorithm': alg, 'value': val} for alg, val in loading_efficiency_ranking
        ]

        # 按一致性排名
        consistency_ranking = []
        for algorithm, data in algorithm_comparison.items():
            consistency = data.get('consistency_score', 0)
            consistency_ranking.append((algorithm, consistency))

        consistency_ranking.sort(key=lambda x: x[1], reverse=True)
        rankings['consistency'] = [
            {'algorithm': alg, 'value': val} for alg, val in consistency_ranking
        ]

        return rankings

    def _analyze_trend_data(self, trend_data: List[Dict]) -> Dict:
        """分析趋势数据"""
        if len(trend_data) < 2:
            return {'trend_direction': 'insufficient_data'}

        # 计算趋势方向
        values = [point['metric_value'] for point in trend_data]

        # 简单的线性趋势分析
        first_half_avg = statistics.mean(values[:len(values)//2])
        second_half_avg = statistics.mean(values[len(values)//2:])

        trend_direction = 'stable'
        trend_strength = 0

        if second_half_avg > first_half_avg * 1.05:  # 增长超过5%
            trend_direction = 'increasing'
            trend_strength = (second_half_avg - first_half_avg) / first_half_avg
        elif second_half_avg < first_half_avg * 0.95:  # 下降超过5%
            trend_direction = 'decreasing'
            trend_strength = (first_half_avg - second_half_avg) / first_half_avg
        else:
            trend_direction = 'stable'
            trend_strength = abs(second_half_avg - first_half_avg) / first_half_avg

        return {
            'trend_direction': trend_direction,
            'trend_strength': min(trend_strength, 1.0),  # 限制在1.0以内
            'first_half_average': first_half_avg,
            'second_half_average': second_half_avg
        }

    def _calculate_similarity(self, exp1: Dict, exp2: Dict) -> float:
        """计算两个实验的相似度"""
        similarity_score = 0.0
        total_weight = 0.0

        # 算法相似度（权重0.3）
        if exp1['algorithm'] == exp2['algorithm']:
            similarity_score += 0.3
        total_weight += 0.3

        # 车辆数量相似度（权重0.2）
        vehicles1_count = len(exp1.get('vehicles', []))
        vehicles2_count = len(exp2.get('vehicles', []))

        if vehicles1_count > 0 and vehicles2_count > 0:
            vehicle_ratio = min(vehicles1_count, vehicles2_count) / max(vehicles1_count, vehicles2_count)
            similarity_score += 0.2 * vehicle_ratio
        total_weight += 0.2

        # 性能指标相似度（权重0.5）
        metrics1 = {m['metric_name']: m['metric_value'] for m in exp1.get('metrics', [])}
        metrics2 = {m['metric_name']: m['metric_value'] for m in exp2.get('metrics', [])}

        common_metrics = set(metrics1.keys()) & set(metrics2.keys())
        if common_metrics:
            metric_similarity = 0
            for metric in common_metrics:
                val1, val2 = metrics1[metric], metrics2[metric]
                if val1 > 0 and val2 > 0:
                    ratio = min(val1, val2) / max(val1, val2)
                    metric_similarity += ratio

            similarity_score += 0.5 * (metric_similarity / len(common_metrics))
        total_weight += 0.5

        return similarity_score / total_weight if total_weight > 0 else 0.0

    def _calculate_metric_from_vehicles(self, vehicles: List[Dict], metric: str) -> Optional[float]:
        """从车辆数据计算指标"""
        if not vehicles:
            return None

        if metric == 'loading_efficiency':
            efficiencies = [v.get('loading_efficiency', 0) for v in vehicles if v.get('loading_efficiency')]
            return statistics.mean(efficiencies) if efficiencies else None

        elif metric == 'total_distance':
            return sum(v.get('route_distance', 0) for v in vehicles)

        elif metric == 'vehicle_utilization':
            used_vehicles = len([v for v in vehicles if v.get('total_items', 0) > 0])
            return (used_vehicles / len(vehicles)) * 100

        return None

# 全局对比引擎实例
comparison_engine = ComparisonEngine()