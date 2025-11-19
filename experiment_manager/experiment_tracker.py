"""
实验跟踪器
Experiment Tracker for managing optimization experiments
"""

import json
import shutil
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
import logging

from database.db_manager import db_manager
from database.models import (
    Experiment, Vehicle, PerformanceMetric, OptimizationRun,
    ExperimentStatus, VehicleType, MetricCategory, STANDARD_METRICS
)

class ExperimentTracker:
    """实验跟踪器 - 管理优化实验的生命周期"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.output_dir = Path("output")
        self.detailed_data_dir = Path("database/detailed_data")
        self.detailed_data_dir.mkdir(parents=True, exist_ok=True)

    def start_experiment(self, name: str, description: str = None,
                        algorithm: str = "integrated", parameters: Dict = None,
                        created_by: str = "user") -> str:
        """
        启动新实验

        Args:
            name: 实验名称
            description: 实验描述
            algorithm: 使用的算法
            parameters: 算法参数
            created_by: 创建者

        Returns:
            experiment_id: 实验ID
        """
        try:
            # 创建实验记录
            experiment_id = db_manager.create_experiment(
                name=name,
                description=description,
                algorithm=algorithm,
                parameters=parameters,
                created_by=created_by
            )

            # 创建实验数据目录
            exp_data_dir = self.detailed_data_dir / experiment_id
            exp_data_dir.mkdir(exist_ok=True)

            # 保存实验配置
            config_file = exp_data_dir / "config.json"
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'experiment_id': experiment_id,
                    'name': name,
                    'description': description,
                    'algorithm': algorithm,
                    'parameters': parameters or {},
                    'created_by': created_by,
                    'created_at': datetime.now().isoformat()
                }, f, ensure_ascii=False, indent=2)

            self.logger.info(f"启动实验: {experiment_id} - {name}")
            return experiment_id

        except Exception as e:
            self.logger.error(f"启动实验失败: {str(e)}")
            raise

    def complete_experiment(self, experiment_id: str, results_data: Dict = None):
        """
        完成实验并保存结果

        Args:
            experiment_id: 实验ID
            results_data: 结果数据
        """
        try:
            # 收集和分析结果数据
            if not results_data:
                results_data = self._collect_results_from_output()

            # 更新实验状态
            db_manager.update_experiment_status(
                experiment_id=experiment_id,
                status='completed',
                total_orders=results_data.get('total_orders'),
                total_vehicles=results_data.get('total_vehicles'),
                data_path=str(self.detailed_data_dir / experiment_id)
            )

            # 保存车辆数据
            if 'vehicles' in results_data:
                for vehicle_data in results_data['vehicles']:
                    db_manager.add_vehicle_data(experiment_id, vehicle_data)

            # 计算和保存性能指标
            metrics = self._calculate_performance_metrics(results_data)
            for metric in metrics:
                db_manager.add_performance_metric(
                    experiment_id=experiment_id,
                    metric_name=metric['name'],
                    metric_value=metric['value'],
                    metric_unit=metric['unit'],
                    category=metric['category']
                )

            # 归档详细数据
            self._archive_detailed_data(experiment_id, results_data)

            self.logger.info(f"完成实验: {experiment_id}")

        except Exception as e:
            self.logger.error(f"完成实验失败: {str(e)}")
            # 标记实验为失败状态
            db_manager.update_experiment_status(experiment_id, 'failed')
            raise

    def fail_experiment(self, experiment_id: str, error_message: str):
        """标记实验为失败状态"""
        try:
            db_manager.update_experiment_status(experiment_id, 'failed')

            # 记录错误信息
            exp_data_dir = self.detailed_data_dir / experiment_id
            error_file = exp_data_dir / "error.json"
            with open(error_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'error_message': error_message,
                    'failed_at': datetime.now().isoformat()
                }, f, ensure_ascii=False, indent=2)

            self.logger.error(f"实验失败: {experiment_id} - {error_message}")

        except Exception as e:
            self.logger.error(f"标记实验失败状态时出错: {str(e)}")

    def get_experiment_summary(self, experiment_id: str) -> Optional[Dict]:
        """获取实验摘要"""
        try:
            return db_manager.get_experiment_detail(experiment_id)
        except Exception as e:
            self.logger.error(f"获取实验摘要失败: {str(e)}")
            return None

    def list_experiments(self, limit: int = 50, offset: int = 0,
                        created_by: str = None) -> List[Dict]:
        """列出实验"""
        try:
            return db_manager.get_experiments(limit, offset, created_by)
        except Exception as e:
            self.logger.error(f"列出实验失败: {str(e)}")
            return []

    def delete_experiment(self, experiment_id: str, remove_data: bool = True) -> bool:
        """
        删除实验

        Args:
            experiment_id: 实验ID
            remove_data: 是否删除详细数据文件

        Returns:
            bool: 是否删除成功
        """
        try:
            # 删除数据库记录
            success = db_manager.delete_experiment(experiment_id)

            # 删除详细数据目录
            if remove_data and success:
                exp_data_dir = self.detailed_data_dir / experiment_id
                if exp_data_dir.exists():
                    shutil.rmtree(exp_data_dir)

            self.logger.info(f"删除实验: {experiment_id}")
            return success

        except Exception as e:
            self.logger.error(f"删除实验失败: {str(e)}")
            return False

    def _collect_results_from_output(self) -> Dict:
        """从output目录收集结果数据"""
        results = {
            'vehicles': [],
            'total_orders': 0,
            'total_vehicles': 0
        }

        try:
            reports_dir = self.output_dir / "reports"
            if not reports_dir.exists():
                return results

            # 收集装载计划数据
            loading_files = list(reports_dir.glob("*_loading_plan.json"))
            for loading_file in loading_files:
                try:
                    with open(loading_file, 'r', encoding='utf-8') as f:
                        loading_data = json.load(f)

                    vehicle_info = self._extract_vehicle_info(loading_data, loading_file.name)
                    if vehicle_info:
                        results['vehicles'].append(vehicle_info)

                except Exception as e:
                    self.logger.warning(f"处理装载文件失败: {loading_file} - {str(e)}")

            # 收集路径计划数据并合并
            route_files = list(reports_dir.glob("*_route_plan.json"))
            for route_file in route_files:
                try:
                    with open(route_file, 'r', encoding='utf-8') as f:
                        route_data = json.load(f)

                    route_info = self._extract_route_info(route_data)
                    if route_info:
                        # 找到对应的车辆并合并路径信息
                        vehicle_id = route_info['vehicle_id']
                        for vehicle in results['vehicles']:
                            if vehicle['vehicle_id'] == vehicle_id:
                                vehicle.update(route_info)
                                break

                except Exception as e:
                    self.logger.warning(f"处理路径文件失败: {route_file} - {str(e)}")

            results['total_vehicles'] = len(results['vehicles'])
            results['total_orders'] = sum(v.get('total_items', 0) for v in results['vehicles'])

        except Exception as e:
            self.logger.error(f"收集结果数据失败: {str(e)}")

        return results

    def _extract_vehicle_info(self, loading_data: Dict, filename: str) -> Optional[Dict]:
        """从装载数据中提取车辆信息"""
        try:
            summary = loading_data.get('summary', {})
            vehicle_details = loading_data.get('vehicle_details', {})
            truck_specs = vehicle_details.get('truck_specs', {})

            vehicle_id = summary.get('vehicle_id', filename.replace('_loading_plan.json', ''))

            return {
                'vehicle_id': vehicle_id,
                'vehicle_type': vehicle_details.get('type', 'LARGE_TRUCK'),
                'capacity_volume': truck_specs.get('volume_m3', 55.296),
                'capacity_weight': truck_specs.get('capacity_kg', 18000),
                'loading_efficiency': summary.get('loading_efficiency', 0),
                'total_items': summary.get('total_items', 0),
                'actual_volume': summary.get('total_volume_m3', 0),
                'actual_weight': summary.get('total_weight_kg', 0)
            }

        except Exception as e:
            self.logger.warning(f"提取车辆信息失败: {filename} - {str(e)}")
            return None

    def _extract_route_info(self, route_data: Dict) -> Optional[Dict]:
        """从路径数据中提取路径信息"""
        try:
            summary = route_data.get('summary', {})

            return {
                'vehicle_id': summary.get('vehicle_id'),
                'route_distance': summary.get('total_distance_km', 0),
                'route_duration': summary.get('estimated_duration_hours', 0)
            }

        except Exception as e:
            self.logger.warning(f"提取路径信息失败: {str(e)}")
            return None

    def _calculate_performance_metrics(self, results_data: Dict) -> List[Dict]:
        """计算性能指标"""
        metrics = []

        try:
            vehicles = results_data.get('vehicles', [])
            if not vehicles:
                return metrics

            # 平均装载效率
            efficiencies = [v.get('loading_efficiency', 0) for v in vehicles if v.get('loading_efficiency')]
            if efficiencies:
                metrics.append({
                    'name': 'loading_efficiency',
                    'value': sum(efficiencies) / len(efficiencies),
                    'unit': '%',
                    'category': 'loading'
                })

            # 总行驶距离
            total_distance = sum(v.get('route_distance', 0) for v in vehicles)
            metrics.append({
                'name': 'total_distance',
                'value': total_distance,
                'unit': 'km',
                'category': 'routing'
            })

            # 平均路径时长
            durations = [v.get('route_duration', 0) for v in vehicles if v.get('route_duration')]
            if durations:
                metrics.append({
                    'name': 'avg_route_duration',
                    'value': sum(durations) / len(durations),
                    'unit': 'hours',
                    'category': 'routing'
                })

            # 车辆利用率
            used_vehicles = len([v for v in vehicles if v.get('total_items', 0) > 0])
            if len(vehicles) > 0:
                metrics.append({
                    'name': 'vehicle_utilization',
                    'value': (used_vehicles / len(vehicles)) * 100,
                    'unit': '%',
                    'category': 'overall'
                })

            # 订单完成率（假设所有订单都完成了）
            total_orders = results_data.get('total_orders', 0)
            if total_orders > 0:
                metrics.append({
                    'name': 'order_fulfillment_rate',
                    'value': 100.0,  # 简化假设
                    'unit': '%',
                    'category': 'overall'
                })

        except Exception as e:
            self.logger.error(f"计算性能指标失败: {str(e)}")

        return metrics

    def _archive_detailed_data(self, experiment_id: str, results_data: Dict):
        """归档详细数据"""
        try:
            exp_data_dir = self.detailed_data_dir / experiment_id

            # 保存结果摘要
            summary_file = exp_data_dir / "summary.json"
            with open(summary_file, 'w', encoding='utf-8') as f:
                json.dump(results_data, f, ensure_ascii=False, indent=2)

            # 复制详细的JSON文件
            reports_dir = self.output_dir / "reports"
            if reports_dir.exists():
                detailed_dir = exp_data_dir / "reports"
                detailed_dir.mkdir(exist_ok=True)

                for json_file in reports_dir.glob("*.json"):
                    shutil.copy2(json_file, detailed_dir / json_file.name)

            # 复制可视化文件（可选）
            viz_dir = self.output_dir / "visualizations"
            if viz_dir.exists():
                viz_archive_dir = exp_data_dir / "visualizations"
                viz_archive_dir.mkdir(exist_ok=True)

                # 只保存关键的可视化文件，避免占用过多空间
                key_viz_files = [
                    "loading_density_heatmap*.html",
                    "loading_efficiency_dashboard*.html",
                    "3d_efficiency_analysis*.html"
                ]

                for pattern in key_viz_files:
                    for viz_file in viz_dir.glob(pattern):
                        shutil.copy2(viz_file, viz_archive_dir / viz_file.name)

        except Exception as e:
            self.logger.error(f"归档详细数据失败: {str(e)}")

# 全局实验跟踪器实例
experiment_tracker = ExperimentTracker()