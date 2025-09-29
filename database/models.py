"""
数据模型定义
Database Models and Data Structures
"""

from dataclasses import dataclass
from typing import Dict, List, Any, Optional
from datetime import datetime
from enum import Enum

class ExperimentStatus(str, Enum):
    """实验状态枚举"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class VehicleType(str, Enum):
    """车辆类型枚举"""
    LARGE_TRUCK = "LARGE_TRUCK"
    LTL_TRUCK = "LTL_TRUCK"

class MetricCategory(str, Enum):
    """指标类别枚举"""
    LOADING = "loading"
    ROUTING = "routing"
    OVERALL = "overall"

@dataclass
class Experiment:
    """实验数据模型"""
    experiment_id: str
    name: str
    description: Optional[str] = None
    algorithm: str = "integrated"
    parameters: Optional[Dict[str, Any]] = None
    status: ExperimentStatus = ExperimentStatus.PENDING
    created_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_by: str = "system"
    total_orders: Optional[int] = None
    total_vehicles: Optional[int] = None
    data_path: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'experiment_id': self.experiment_id,
            'name': self.name,
            'description': self.description,
            'algorithm': self.algorithm,
            'parameters': self.parameters,
            'status': self.status.value,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'created_by': self.created_by,
            'total_orders': self.total_orders,
            'total_vehicles': self.total_vehicles,
            'data_path': self.data_path
        }

@dataclass
class Vehicle:
    """车辆数据模型"""
    experiment_id: str
    vehicle_id: str
    vehicle_type: VehicleType
    capacity_volume: float
    capacity_weight: float
    loading_efficiency: Optional[float] = None
    total_items: Optional[int] = None
    actual_volume: Optional[float] = None
    actual_weight: Optional[float] = None
    route_distance: Optional[float] = None
    route_duration: Optional[float] = None
    created_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'experiment_id': self.experiment_id,
            'vehicle_id': self.vehicle_id,
            'vehicle_type': self.vehicle_type.value,
            'capacity_volume': self.capacity_volume,
            'capacity_weight': self.capacity_weight,
            'loading_efficiency': self.loading_efficiency,
            'total_items': self.total_items,
            'actual_volume': self.actual_volume,
            'actual_weight': self.actual_weight,
            'route_distance': self.route_distance,
            'route_duration': self.route_duration,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

@dataclass
class PerformanceMetric:
    """性能指标数据模型"""
    experiment_id: str
    metric_name: str
    metric_value: float
    metric_unit: Optional[str] = None
    category: MetricCategory = MetricCategory.OVERALL
    calculated_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'experiment_id': self.experiment_id,
            'metric_name': self.metric_name,
            'metric_value': self.metric_value,
            'metric_unit': self.metric_unit,
            'category': self.category.value,
            'calculated_at': self.calculated_at.isoformat() if self.calculated_at else None
        }

@dataclass
class OptimizationRun:
    """优化运行记录数据模型"""
    experiment_id: str
    run_type: str  # 'loading', 'routing', 'integrated'
    algorithm: str
    status: str = "running"
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    execution_time_seconds: Optional[float] = None
    success_rate: Optional[float] = None
    error_message: Optional[str] = None
    result_summary: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'experiment_id': self.experiment_id,
            'run_type': self.run_type,
            'algorithm': self.algorithm,
            'status': self.status,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'execution_time_seconds': self.execution_time_seconds,
            'success_rate': self.success_rate,
            'error_message': self.error_message,
            'result_summary': self.result_summary
        }

@dataclass
class ExperimentComparison:
    """实验对比数据模型"""
    experiments: List[str]
    metrics: List[str]
    comparison_data: Dict[str, Dict[str, Any]]
    generated_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'experiments': self.experiments,
            'metrics': self.metrics,
            'comparison_data': self.comparison_data,
            'generated_at': self.generated_at.isoformat() if self.generated_at else None
        }

@dataclass
class TrendAnalysis:
    """趋势分析数据模型"""
    metric_name: str
    category: str
    time_period: str  # '7days', '30days', '90days'
    data_points: List[Dict[str, Any]]
    trend_direction: str  # 'increasing', 'decreasing', 'stable'
    trend_strength: float  # 0-1
    analysis_summary: Optional[str] = None
    generated_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'metric_name': self.metric_name,
            'category': self.category,
            'time_period': self.time_period,
            'data_points': self.data_points,
            'trend_direction': self.trend_direction,
            'trend_strength': self.trend_strength,
            'analysis_summary': self.analysis_summary,
            'generated_at': self.generated_at.isoformat() if self.generated_at else None
        }

# 常用的性能指标定义
STANDARD_METRICS = {
    'loading_efficiency': {
        'name': '装载效率',
        'unit': '%',
        'category': MetricCategory.LOADING,
        'description': '车辆空间利用率'
    },
    'total_distance': {
        'name': '总行驶距离',
        'unit': 'km',
        'category': MetricCategory.ROUTING,
        'description': '所有车辆的总行驶距离'
    },
    'avg_route_duration': {
        'name': '平均路径时长',
        'unit': 'hours',
        'category': MetricCategory.ROUTING,
        'description': '平均每辆车的行驶时间'
    },
    'vehicle_utilization': {
        'name': '车辆利用率',
        'unit': '%',
        'category': MetricCategory.OVERALL,
        'description': '实际使用车辆数/总可用车辆数'
    },
    'cost_efficiency': {
        'name': '成本效率',
        'unit': 'yuan/km',
        'category': MetricCategory.OVERALL,
        'description': '单位距离运输成本'
    },
    'order_fulfillment_rate': {
        'name': '订单完成率',
        'unit': '%',
        'category': MetricCategory.OVERALL,
        'description': '成功处理的订单比例'
    },
    'optimization_time': {
        'name': '优化计算时间',
        'unit': 'seconds',
        'category': MetricCategory.OVERALL,
        'description': '算法执行时间'
    }
}

# 常用的算法参数配置
ALGORITHM_CONFIGS = {
    'gurobi_3dpp': {
        'name': 'Gurobi 3D装载优化',
        'parameters': {
            'time_limit': 300,
            'mip_gap': 0.01,
            'enable_rotation': True,
            'collision_detection': True
        }
    },
    'ltl_optimizer': {
        'name': 'LTL拼装优化',
        'parameters': {
            'max_items_per_truck': 1000,
            'weight_threshold': 18000,
            'volume_threshold': 55.296
        }
    },
    'integrated': {
        'name': '集成优化',
        'parameters': {
            'loading_algorithm': 'gurobi_3dpp',
            'routing_algorithm': 'vrp_basic',
            'enable_visualization': True,
            'sample_ratio': 0.3
        }
    }
}