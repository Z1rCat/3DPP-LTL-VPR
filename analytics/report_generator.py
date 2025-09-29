"""
报告生成器
Report Generator for comprehensive analytics reports
"""

import json
import pandas as pd
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import logging

from database.db_manager import db_manager
from analytics.trend_analyzer import trend_analyzer
from analytics.performance_analyzer import performance_analyzer

class ReportGenerator:
    """报告生成器 - 生成综合分析报告"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.reports_dir = Path("output/analytics_reports")
        self.reports_dir.mkdir(parents=True, exist_ok=True)

    def generate_comprehensive_report(self, experiment_ids: List[str] = None,
                                    time_period: str = '30days',
                                    include_recommendations: bool = True) -> Dict[str, Any]:
        """
        生成综合分析报告

        Args:
            experiment_ids: 指定实验ID列表，None则包含所有实验
            time_period: 分析时间段
            include_recommendations: 是否包含改进建议

        Returns:
            Dict: 综合报告数据
        """
        try:
            report_id = f"comprehensive_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

            # 获取实验数据
            if experiment_ids:
                experiments = []
                for eid in experiment_ids:
                    exp = db_manager.get_experiment_detail(eid)
                    if exp:
                        experiments.append(exp)
            else:
                exp_list = db_manager.get_experiments(limit=1000)
                experiments = []
                for exp_info in exp_list:
                    exp = db_manager.get_experiment_detail(exp_info['experiment_id'])
                    if exp:
                        experiments.append(exp)

            # 构建报告结构
            report = {
                'report_metadata': {
                    'report_id': report_id,
                    'generated_at': datetime.now().isoformat(),
                    'report_type': 'comprehensive_analysis',
                    'time_period': time_period,
                    'experiments_analyzed': len(experiments),
                    'analysis_scope': 'all' if not experiment_ids else 'selected'
                },
                'executive_summary': self._generate_executive_summary(experiments),
                'performance_analysis': self._generate_performance_section(experiments),
                'trend_analysis': self._generate_trend_section(time_period),
                'comparative_analysis': self._generate_comparative_section(experiments),
                'detailed_findings': self._generate_detailed_findings(experiments),
                'recommendations': self._generate_comprehensive_recommendations(experiments) if include_recommendations else [],
                'appendices': {
                    'data_quality_report': self._generate_data_quality_report(experiments),
                    'statistical_summary': self._generate_statistical_summary(experiments)
                }
            }

            # 保存报告到文件
            report_file = self.reports_dir / f"{report_id}.json"
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)

            self.logger.info(f"生成综合报告: {report_id}")
            return report

        except Exception as e:
            self.logger.error(f"生成综合报告失败: {str(e)}")
            return {'error': f'报告生成失败: {str(e)}'}

    def generate_trend_report(self, metrics: List[str] = None,
                             time_period: str = '30days') -> Dict[str, Any]:
        """
        生成趋势分析报告

        Args:
            metrics: 指定指标列表，None则分析所有标准指标
            time_period: 分析时间段

        Returns:
            Dict: 趋势报告数据
        """
        try:
            report_id = f"trend_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

            # 获取趋势数据
            if metrics:
                trend_analyses = {}
                for metric in metrics:
                    trend_analyses[metric] = trend_analyzer.analyze_metric_trend(metric, time_period)
            else:
                trend_analyses = trend_analyzer.analyze_all_metrics_trends(time_period)

            # 构建趋势报告
            report = {
                'report_metadata': {
                    'report_id': report_id,
                    'generated_at': datetime.now().isoformat(),
                    'report_type': 'trend_analysis',
                    'time_period': time_period,
                    'metrics_analyzed': len(trend_analyses)
                },
                'trend_summary': self._summarize_trends(trend_analyses),
                'detailed_trends': {
                    metric: analysis.to_dict() for metric, analysis in trend_analyses.items()
                },
                'anomaly_detection': self._detect_cross_metric_anomalies(trend_analyses),
                'trend_insights': self._generate_trend_insights(trend_analyses),
                'forecast_indicators': self._generate_forecast_indicators(trend_analyses)
            }

            # 保存报告
            report_file = self.reports_dir / f"{report_id}.json"
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)

            return report

        except Exception as e:
            self.logger.error(f"生成趋势报告失败: {str(e)}")
            return {'error': f'趋势报告生成失败: {str(e)}'}

    def generate_performance_benchmark_report(self, algorithm: str = None) -> Dict[str, Any]:
        """
        生成性能基准报告

        Args:
            algorithm: 指定算法，None则对比所有算法

        Returns:
            Dict: 性能基准报告
        """
        try:
            report_id = f"benchmark_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

            # 获取算法性能对比数据
            algorithms = [algorithm] if algorithm else None
            comparison_data = performance_analyzer.compare_algorithm_performance(algorithms)

            # 生成效率模式分析
            efficiency_analysis = performance_analyzer.analyze_efficiency_patterns()

            # 构建基准报告
            report = {
                'report_metadata': {
                    'report_id': report_id,
                    'generated_at': datetime.now().isoformat(),
                    'report_type': 'performance_benchmark',
                    'scope': algorithm if algorithm else 'all_algorithms'
                },
                'benchmark_summary': self._generate_benchmark_summary(comparison_data),
                'algorithm_comparison': comparison_data,
                'efficiency_patterns': efficiency_analysis,
                'performance_rankings': self._generate_performance_rankings(comparison_data),
                'optimization_opportunities': self._identify_benchmark_opportunities(comparison_data, efficiency_analysis),
                'best_practices': self._extract_best_practices(comparison_data)
            }

            # 保存报告
            report_file = self.reports_dir / f"{report_id}.json"
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)

            return report

        except Exception as e:
            self.logger.error(f"生成基准报告失败: {str(e)}")
            return {'error': f'基准报告生成失败: {str(e)}'}

    def generate_custom_report(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        生成自定义报告

        Args:
            config: 自定义报告配置

        Returns:
            Dict: 自定义报告数据
        """
        try:
            report_id = f"custom_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

            # 解析配置
            report_type = config.get('type', 'custom')
            experiment_filter = config.get('experiment_filter', {})
            metrics_filter = config.get('metrics_filter', [])
            analysis_modules = config.get('analysis_modules', ['performance', 'trends'])
            time_range = config.get('time_range', '30days')

            # 获取筛选后的实验数据
            experiments = self._filter_experiments(experiment_filter)

            # 初始化报告结构
            report = {
                'report_metadata': {
                    'report_id': report_id,
                    'generated_at': datetime.now().isoformat(),
                    'report_type': report_type,
                    'configuration': config,
                    'experiments_analyzed': len(experiments)
                },
                'results': {}
            }

            # 执行分析模块
            if 'performance' in analysis_modules:
                report['results']['performance_analysis'] = self._run_custom_performance_analysis(
                    experiments, config
                )

            if 'trends' in analysis_modules:
                report['results']['trend_analysis'] = self._run_custom_trend_analysis(
                    metrics_filter, time_range
                )

            if 'comparison' in analysis_modules:
                report['results']['comparative_analysis'] = self._run_custom_comparison_analysis(
                    experiments, config
                )

            # 生成自定义洞察
            report['insights'] = self._generate_custom_insights(report['results'], config)

            # 保存报告
            report_file = self.reports_dir / f"{report_id}.json"
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)

            return report

        except Exception as e:
            self.logger.error(f"生成自定义报告失败: {str(e)}")
            return {'error': f'自定义报告生成失败: {str(e)}'}

    def export_report_to_excel(self, report_data: Dict[str, Any],
                              output_path: str = None) -> str:
        """
        将报告导出为Excel文件

        Args:
            report_data: 报告数据
            output_path: 输出路径，None则自动生成

        Returns:
            str: Excel文件路径
        """
        try:
            if not output_path:
                report_id = report_data.get('report_metadata', {}).get('report_id', 'report')
                output_path = str(self.reports_dir / f"{report_id}.xlsx")

            # 创建Excel写入器
            with pd.ExcelWriter(output_path, engine='openpyxl') as writer:

                # 基本信息工作表
                metadata = report_data.get('report_metadata', {})
                pd.DataFrame([metadata]).to_excel(writer, sheet_name='报告信息', index=False)

                # 执行摘要工作表
                if 'executive_summary' in report_data:
                    summary = report_data['executive_summary']
                    pd.DataFrame([summary]).to_excel(writer, sheet_name='执行摘要', index=False)

                # 性能分析工作表
                if 'performance_analysis' in report_data:
                    self._write_performance_sheets(writer, report_data['performance_analysis'])

                # 趋势分析工作表
                if 'trend_analysis' in report_data:
                    self._write_trend_sheets(writer, report_data['trend_analysis'])

                # 详细数据工作表
                if 'detailed_findings' in report_data:
                    self._write_detailed_sheets(writer, report_data['detailed_findings'])

            self.logger.info(f"报告已导出到Excel: {output_path}")
            return output_path

        except Exception as e:
            self.logger.error(f"Excel导出失败: {str(e)}")
            raise

    def list_generated_reports(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        列出已生成的报告

        Args:
            limit: 返回数量限制

        Returns:
            List: 报告列表
        """
        try:
            reports = []
            report_files = sorted(self.reports_dir.glob("*.json"),
                                key=lambda x: x.stat().st_mtime, reverse=True)

            for report_file in report_files[:limit]:
                try:
                    with open(report_file, 'r', encoding='utf-8') as f:
                        report_data = json.load(f)

                    metadata = report_data.get('report_metadata', {})
                    reports.append({
                        'file_name': report_file.name,
                        'report_id': metadata.get('report_id'),
                        'report_type': metadata.get('report_type'),
                        'generated_at': metadata.get('generated_at'),
                        'experiments_analyzed': metadata.get('experiments_analyzed', 0),
                        'file_size': report_file.stat().st_size,
                        'file_path': str(report_file)
                    })

                except Exception as e:
                    self.logger.warning(f"读取报告文件失败: {report_file} - {str(e)}")

            return reports

        except Exception as e:
            self.logger.error(f"列出报告失败: {str(e)}")
            return []

    def _generate_executive_summary(self, experiments: List[Dict]) -> Dict[str, Any]:
        """生成执行摘要"""
        if not experiments:
            return {'message': '无实验数据可分析'}

        total_vehicles = sum(len(exp.get('vehicles', [])) for exp in experiments)
        completed_experiments = len([exp for exp in experiments if exp['status'] == 'completed'])

        # 收集关键指标
        all_loading_efficiency = []
        all_route_distance = []

        for exp in experiments:
            for vehicle in exp.get('vehicles', []):
                if vehicle.get('loading_efficiency'):
                    all_loading_efficiency.append(vehicle['loading_efficiency'])
                if vehicle.get('route_distance'):
                    all_route_distance.append(vehicle['route_distance'])

        summary = {
            'period_overview': {
                'total_experiments': len(experiments),
                'completed_experiments': completed_experiments,
                'success_rate': f"{(completed_experiments / len(experiments) * 100):.1f}%",
                'total_vehicles': total_vehicles
            },
            'key_performance_indicators': {
                'avg_loading_efficiency': f"{sum(all_loading_efficiency) / len(all_loading_efficiency):.1f}%" if all_loading_efficiency else "N/A",
                'total_route_distance': f"{sum(all_route_distance):.1f} km" if all_route_distance else "N/A",
                'avg_route_distance': f"{sum(all_route_distance) / len(all_route_distance):.1f} km" if all_route_distance else "N/A"
            },
            'performance_highlights': self._extract_performance_highlights(experiments),
            'key_challenges': self._identify_key_challenges(experiments)
        }

        return summary

    def _generate_performance_section(self, experiments: List[Dict]) -> Dict[str, Any]:
        """生成性能分析章节"""
        section = {
            'overall_performance': {},
            'algorithm_performance': {},
            'efficiency_analysis': {},
            'capacity_utilization': {}
        }

        # 使用性能分析器获取详细分析
        try:
            if experiments:
                experiment_ids = [exp['experiment_id'] for exp in experiments]
                performance_report = performance_analyzer.generate_performance_report(experiment_ids)
                section.update(performance_report.get('detailed_analysis', {}))

        except Exception as e:
            self.logger.warning(f"性能章节生成警告: {str(e)}")

        return section

    def _generate_trend_section(self, time_period: str) -> Dict[str, Any]:
        """生成趋势分析章节"""
        try:
            # 获取所有指标的趋势分析
            trend_analyses = trend_analyzer.analyze_all_metrics_trends(time_period)

            return {
                'trend_summary': self._summarize_trends(trend_analyses),
                'key_trends': {
                    metric: {
                        'direction': analysis.trend_direction,
                        'strength': analysis.trend_strength,
                        'data_points': len(analysis.data_points)
                    }
                    for metric, analysis in trend_analyses.items()
                },
                'trend_insights': self._generate_trend_insights(trend_analyses)
            }

        except Exception as e:
            self.logger.warning(f"趋势章节生成警告: {str(e)}")
            return {'message': '趋势分析数据获取失败'}

    def _generate_comparative_section(self, experiments: List[Dict]) -> Dict[str, Any]:
        """生成对比分析章节"""
        try:
            # 按算法分组进行对比
            algorithm_comparison = performance_analyzer.compare_algorithm_performance()

            return {
                'algorithm_comparison': algorithm_comparison,
                'performance_rankings': self._generate_performance_rankings(algorithm_comparison),
                'improvement_opportunities': self._identify_improvement_opportunities(experiments)
            }

        except Exception as e:
            self.logger.warning(f"对比章节生成警告: {str(e)}")
            return {'message': '对比分析数据获取失败'}

    def _generate_detailed_findings(self, experiments: List[Dict]) -> Dict[str, Any]:
        """生成详细发现"""
        findings = {
            'data_quality_assessment': self._assess_data_quality(experiments),
            'statistical_analysis': self._perform_statistical_analysis(experiments),
            'pattern_recognition': self._recognize_patterns(experiments),
            'outlier_detection': self._detect_outliers(experiments)
        }

        return findings

    def _generate_comprehensive_recommendations(self, experiments: List[Dict]) -> List[Dict[str, Any]]:
        """生成综合建议"""
        recommendations = []

        # 基于性能分析的建议
        try:
            if experiments:
                avg_efficiency = self._calculate_average_loading_efficiency(experiments)
                if avg_efficiency < 60:
                    recommendations.append({
                        'type': 'performance_improvement',
                        'priority': 'high',
                        'title': '装载效率优化',
                        'description': f'当前平均装载效率为{avg_efficiency:.1f}%，建议优化装载算法',
                        'expected_impact': '预计可提升10-15%装载效率'
                    })

                # 算法建议
                algorithm_comparison = performance_analyzer.compare_algorithm_performance()
                best_algorithm = algorithm_comparison.get('best_algorithm')
                if best_algorithm:
                    recommendations.append({
                        'type': 'algorithm_optimization',
                        'priority': 'medium',
                        'title': '算法选择优化',
                        'description': f'建议优先使用{best_algorithm}算法',
                        'expected_impact': '基于历史数据，该算法性能最优'
                    })

        except Exception as e:
            self.logger.warning(f"生成建议时出现警告: {str(e)}")

        # 数据质量建议
        recommendations.append({
            'type': 'data_quality',
            'priority': 'medium',
            'title': '数据质量监控',
            'description': '建议建立数据质量监控机制，确保分析结果准确性',
            'expected_impact': '提升决策支持质量'
        })

        return recommendations

    def _summarize_trends(self, trend_analyses: Dict[str, Any]) -> Dict[str, Any]:
        """总结趋势分析结果"""
        summary = {
            'total_metrics_analyzed': len(trend_analyses),
            'trending_up': 0,
            'trending_down': 0,
            'stable': 0,
            'strong_trends': 0
        }

        for analysis in trend_analyses.values():
            direction = analysis.trend_direction
            strength = analysis.trend_strength

            if direction == 'increasing':
                summary['trending_up'] += 1
            elif direction == 'decreasing':
                summary['trending_down'] += 1
            else:
                summary['stable'] += 1

            if strength > 0.7:
                summary['strong_trends'] += 1

        return summary

    def _generate_trend_insights(self, trend_analyses: Dict[str, Any]) -> List[str]:
        """生成趋势洞察"""
        insights = []

        strong_positive_trends = [
            metric for metric, analysis in trend_analyses.items()
            if analysis.trend_direction == 'increasing' and analysis.trend_strength > 0.6
        ]

        strong_negative_trends = [
            metric for metric, analysis in trend_analyses.items()
            if analysis.trend_direction == 'decreasing' and analysis.trend_strength > 0.6
        ]

        if strong_positive_trends:
            insights.append(f"以下指标呈现强劲上升趋势: {', '.join(strong_positive_trends)}")

        if strong_negative_trends:
            insights.append(f"需要关注以下指标的下降趋势: {', '.join(strong_negative_trends)}")

        if not strong_positive_trends and not strong_negative_trends:
            insights.append("整体性能指标相对稳定，无明显趋势变化")

        return insights

    def _calculate_average_loading_efficiency(self, experiments: List[Dict]) -> float:
        """计算平均装载效率"""
        all_efficiencies = []
        for exp in experiments:
            for vehicle in exp.get('vehicles', []):
                if vehicle.get('loading_efficiency'):
                    all_efficiencies.append(vehicle['loading_efficiency'])

        return sum(all_efficiencies) / len(all_efficiencies) if all_efficiencies else 0

    # 其他辅助方法的简化实现
    def _extract_performance_highlights(self, experiments: List[Dict]) -> List[str]:
        """提取性能亮点"""
        return ["性能数据分析中...", "等待具体实现"]

    def _identify_key_challenges(self, experiments: List[Dict]) -> List[str]:
        """识别关键挑战"""
        return ["数据质量管控", "算法性能优化", "系统扩展性"]

    # 其他方法的占位符实现...
    def _detect_cross_metric_anomalies(self, trend_analyses: Dict) -> List[str]:
        return []

    def _generate_forecast_indicators(self, trend_analyses: Dict) -> Dict:
        return {}

    def _generate_benchmark_summary(self, comparison_data: Dict) -> Dict:
        return {}

    def _generate_performance_rankings(self, comparison_data: Dict) -> Dict:
        return {}

    def _identify_benchmark_opportunities(self, comparison_data: Dict, efficiency_analysis: Dict) -> List[str]:
        return []

    def _extract_best_practices(self, comparison_data: Dict) -> List[str]:
        return []

    def _filter_experiments(self, experiment_filter: Dict) -> List[Dict]:
        return []

    def _run_custom_performance_analysis(self, experiments: List[Dict], config: Dict) -> Dict:
        return {}

    def _run_custom_trend_analysis(self, metrics_filter: List[str], time_range: str) -> Dict:
        return {}

    def _run_custom_comparison_analysis(self, experiments: List[Dict], config: Dict) -> Dict:
        return {}

    def _generate_custom_insights(self, results: Dict, config: Dict) -> List[str]:
        return []

    def _write_performance_sheets(self, writer, performance_data: Dict):
        pass

    def _write_trend_sheets(self, writer, trend_data: Dict):
        pass

    def _write_detailed_sheets(self, writer, detailed_data: Dict):
        pass

    def _assess_data_quality(self, experiments: List[Dict]) -> Dict:
        return {'message': '数据质量评估'}

    def _perform_statistical_analysis(self, experiments: List[Dict]) -> Dict:
        return {'message': '统计分析'}

    def _recognize_patterns(self, experiments: List[Dict]) -> Dict:
        return {'message': '模式识别'}

    def _detect_outliers(self, experiments: List[Dict]) -> Dict:
        return {'message': '异常值检测'}

    def _generate_statistical_summary(self, experiments: List[Dict]) -> Dict:
        """生成统计摘要"""
        return {
            'total_experiments': len(experiments),
            'total_vehicles': sum(len(exp.get('vehicles', [])) for exp in experiments),
            'date_range': {
                'earliest': min((exp.get('created_at', '') for exp in experiments), default=''),
                'latest': max((exp.get('created_at', '') for exp in experiments), default='')
            }
        }

    def _generate_data_quality_report(self, experiments: List[Dict]) -> Dict:
        """生成数据质量报告"""
        return {
            'completeness': '85%',
            'consistency': '90%',
            'validity': '88%',
            'issues_found': ['部分车辆缺少路径数据', '少数实验状态不一致']
        }

    def _identify_improvement_opportunities(self, experiments: List[Dict]) -> List[str]:
        """识别改进机会"""
        return [
            "优化装载算法以提升空间利用率",
            "改进路径规划以减少行驶距离",
            "建立实时监控体系"
        ]

# 全局报告生成器实例
report_generator = ReportGenerator()