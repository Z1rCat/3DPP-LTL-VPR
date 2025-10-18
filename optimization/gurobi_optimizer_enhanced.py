"""
Gurobi增强优化器 - 集成空间-时间约束系统
Enhanced Gurobi Optimizer with Spatial-Temporal Constraint System Integration

集成功能：
- 3D空间冲突检测 (公式3-3至3-5)
- 时间窗约束优化 (公式3-17至3-19)
- 多目标优化 (公式3-7)
- 高级约束求解配置
"""

import gurobipy as gp
from gurobipy import GRB
import pandas as pd
import numpy as np
import logging
from typing import Dict, List, Tuple, Optional, Any
from pathlib import Path
import time
from dataclasses import dataclass

# 导入现有模块
from .gurobi_optimizer import GurobiOptimizerV2
from .spatial_collision_detector import SpatialCollisionDetector, Item3D, Truck3D, RotationType
from .time_window_optimizer import TimeWindowOptimizer, CustomerNode, VehicleInfo, TimeWindow

# 导入配置
import sys
sys.path.append(str(Path(__file__).parent.parent))
from config import (
    TRUCK_SPECS, GUROBI_CONFIG, MODEL_PARAMS, SPATIAL_CONSTRAINT_CONFIG,
    TIME_WINDOW_CONFIG, MULTI_OBJECTIVE_CONFIG, ADVANCED_SOLVER_CONFIG
)


@dataclass
class EnhancedCargoItem:
    """增强的货物数据结构 - 支持空间和时间约束"""
    # 基础属性
    item_id: str
    volume_m3: float
    weight_kg: float
    estimated_length: float
    estimated_width: float
    estimated_height: float

    # 空间约束属性
    rotation_allowed: bool = True
    fragile: bool = False
    stackable: bool = True
    preferred_orientation: int = 1

    # 时间约束属性
    earliest_delivery_time: str = "08:00"
    latest_delivery_time: str = "18:00"
    service_time_minutes: int = 15
    time_window_penalty_rate: float = 0.0

    # 其他属性
    cargo_type: str = "general"
    priority: int = 1
    order_id: str = ""


@dataclass
class OptimizationResult:
    """优化结果数据结构"""
    status: str
    objective_value: float
    solve_time: float
    gap: float

    # 空间优化结果
    loading_plan: List[Dict[str, Any]]
    spatial_positions: List[Dict[str, Any]]
    volume_utilization: float
    weight_utilization: float

    # 时间优化结果
    time_schedule: List[Dict[str, Any]]
    time_window_violations: Dict[str, Any]
    total_time_penalty: float

    # 多目标优化结果
    economic_cost: float
    loading_efficiency: float
    multi_objective_score: float

    # 算法信息
    algorithm: str
    solver_config: Dict[str, Any]


class GurobiOptimizerEnhanced:
    """Gurobi增强优化器 - 集成空间-时间约束"""

    def __init__(self):
        """初始化增强优化器"""
        self.logger = self._setup_logger()

        # 初始化各模块
        self.base_optimizer = GurobiOptimizerV2()
        self.spatial_detector = SpatialCollisionDetector()
        self.time_optimizer = TimeWindowOptimizer()

        # 加载配置
        self.spatial_config = SPATIAL_CONSTRAINT_CONFIG
        self.time_config = TIME_WINDOW_CONFIG
        self.multi_objective_config = MULTI_OBJECTIVE_CONFIG
        self.solver_config = ADVANCED_SOLVER_CONFIG

        self.logger.info("Gurobi增强优化器初始化完成")

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

    def optimize_with_constraints(self, items: List[EnhancedCargoItem],
                                truck_specs: Dict, max_items: int = 100,
                                enable_spatial: bool = True,
                                enable_time_windows: bool = False) -> OptimizationResult:
        """
        使用增强约束系统进行优化

        Args:
            items: 增强货物列表
            truck_specs: 车辆规格
            max_items: 最大货物数量
            enable_spatial: 是否启用空间约束
            enable_time_windows: 是否启用时间窗约束

        Returns:
            OptimizationResult: 优化结果
        """
        self.logger.info(f"开始增强约束优化: {len(items)} 个货物，空间约束={enable_spatial}，时间窗={enable_time_windows}")

        start_time = time.time()
        model = None

        try:
            # 创建Gurobi模型
            model = self._create_enhanced_model()

            # 数据准备
            truck = self._create_truck3d(truck_specs)
            item3d_list = self._convert_to_item3d(items)

            # 添加约束系统
            variables = {}

            if enable_spatial:
                self.logger.info("添加3D空间约束系统")
                spatial_vars = self.spatial_detector.add_spatial_constraints(
                    model, item3d_list, truck, max_items
                )
                variables.update(spatial_vars)

            if enable_time_windows:
                self.logger.info("添加时间窗约束系统")
                customer_nodes = self._convert_to_customer_nodes(items)
                vehicle_info = self._create_vehicle_info(truck_specs)

                # 创建简化的距离矩阵
                coordinates = [vehicle_info.depot_coordinates] + [node.coordinates for node in customer_nodes]
                distance_matrix = self._create_distance_matrix(coordinates)

                time_vars = self.time_optimizer.add_time_window_constraints(
                    model, customer_nodes, vehicle_info, distance_matrix, len(items) + 1
                )
                variables.update(time_vars)

            # 设置目标函数
            self._set_enhanced_objective(model, variables, items, truck_specs, enable_spatial, enable_time_windows)

            # 求解
            self.logger.info("开始增强约束求解...")
            model.optimize()

            solve_time = time.time() - start_time
            self.logger.info(f"增强约束求解完成，耗时: {solve_time:.2f}秒，状态: {model.Status}")

            # 处理结果
            result = self._process_enhanced_result(
                model, variables, items, truck_specs, max_items,
                enable_spatial, enable_time_windows, solve_time
            )

            return result

        except Exception as e:
            self.logger.error(f"增强约束优化异常: {str(e)}")
            raise RuntimeError(f"增强约束优化失败: {str(e)}")

        finally:
            if model is not None:
                model.dispose()

    def _create_enhanced_model(self) -> gp.Model:
        """创建增强的Gurobi模型"""
        model = gp.Model("EnhancedConstraints3DPP")

        # 应用高级求解器配置
        model.setParam('OutputFlag', 1 if GUROBI_CONFIG['log_to_console'] else 0)
        model.setParam('TimeLimit', self.solver_config['max_solve_time_minutes'] * 60)
        model.setParam('Threads', self.solver_config['parallel_threads'])
        model.setParam('MIPFocus', self.solver_config['mip_focus'])
        model.setParam('Heuristics', self.solver_config['heuristic_focus'])
        # 注释掉不支持的参数
        # model.setParam('CutsAggressive', self.solver_config['cuts_aggressiveness'])
        # model.setParam('PresolveAggressive', self.solver_config['presolve_aggressiveness'])
        model.setParam('NumericFocus', self.solver_config['numeric_focus'])

        self.logger.info(f"Gurobi参数配置: {self.solver_config}")
        return model

    def _create_truck3d(self, truck_specs: Dict) -> Truck3D:
        """创建3D车厢对象"""
        return Truck3D(
            length=truck_specs['length'],
            width=truck_specs['width'],
            height=truck_specs['height'],
            volume=truck_specs['volume'],
            max_weight=truck_specs['max_weight']
        )

    def _convert_to_item3d(self, items: List[EnhancedCargoItem]) -> List[Item3D]:
        """将增强货物转换为3D货物对象"""
        item3d_list = []
        for item in items:
            item3d = Item3D(
                item_id=item.item_id,
                length=item.estimated_length,
                width=item.estimated_width,
                height=item.estimated_height,
                volume=item.volume_m3,
                weight=item.weight_kg,
                rotation_allowed=item.rotation_allowed,
                fragile=item.fragile,
                stackable=item.stackable
            )
            item3d_list.append(item3d)
        return item3d_list

    def _convert_to_customer_nodes(self, items: List[EnhancedCargoItem]) -> List[CustomerNode]:
        """将增强货物转换为客户节点（用于时间窗优化）"""
        nodes = []
        for item in items:
            # 这里简化处理，实际应该从订单数据中提取真实坐标
            # 使用默认坐标作为示例
            coordinates = (30.650 + 0.01 * len(nodes), 104.100 + 0.01 * len(nodes))

            time_window = TimeWindow(
                earliest_time=item.earliest_delivery_time,
                latest_time=item.latest_delivery_time,
                service_time=item.service_time_minutes,
                penalty_rate=item.time_window_penalty_rate
            )

            node = CustomerNode(
                node_id=f"node_{item.item_id}",
                order_id=item.order_id or item.item_id,
                coordinates=coordinates,
                demand=item.weight_kg,  # 简化：使用重量作为需求
                time_window=time_window,
                node_type="delivery",  # 简化处理
                priority=item.priority
            )
            nodes.append(node)
        return nodes

    def _create_vehicle_info(self, truck_specs: Dict) -> VehicleInfo:
        """创建车辆信息对象"""
        return VehicleInfo(
            vehicle_id="enhanced_truck_001",
            capacity=truck_specs['max_weight'],
            start_time=f"{self.time_config['start_time_hour']:02d}:00",
            max_working_hours=10,  # 固定10小时工作时间
            average_speed_kmh=self.time_config['average_speed_kmh'],
            depot_coordinates=(30.800835, 104.139111)  # A网点坐标
        )

    def _create_distance_matrix(self, coordinates: List[Tuple[float, float]]) -> np.ndarray:
        """创建简化的距离矩阵"""
        from utils.distance_calculator import DistanceCalculator

        calculator = DistanceCalculator()
        return calculator.build_distance_matrix(coordinates)

    def _set_enhanced_objective(self, model: gp.Model, variables: Dict,
                              items: List[EnhancedCargoItem], truck_specs: Dict,
                              enable_spatial: bool, enable_time_windows: bool):
        """设置增强的目标函数"""

        if self.multi_objective_config['enable_multi_objective']:
            # 多目标优化 (公式3-7)
            self._set_multi_objective_function(model, variables, items, truck_specs)
        else:
            # 单目标优化：最大化装载率
            if enable_spatial and 'x' in variables:
                x = variables['x']
                total_volume = gp.quicksum(
                    x[i] * items[i].volume_m3 for i in range(min(len(items), len(x)))
                )
                model.setObjective(total_volume, GRB.MAXIMIZE)
            else:
                # 降级为简单的装载数量最大化
                model.setObjective(0, GRB.MAXIMIZE)  # 占位符

    def _set_multi_objective_function(self, model: gp.Model, variables: Dict,
                                    items: List[EnhancedCargoItem], truck_specs: Dict):
        """
        设置多目标优化函数 (公式3-7)

        min z = 0.6 * (c_total / c_max) + 0.4 * (1 - α)
        """
        self.logger.info("设置多目标优化函数")

        economic_weight = self.multi_objective_config['economic_weight']
        loading_weight = self.multi_objective_config['loading_rate_weight']

        # 计算经济效益部分
        economic_cost = self._calculate_economic_cost(variables, items, truck_specs)
        max_cost = self._calculate_max_cost(truck_specs)
        economic_objective = economic_cost / max_cost if max_cost > 0 else 0

        # 计算装载率部分
        loading_rate = self._calculate_loading_rate(variables, items, truck_specs)
        loading_objective = 1 - loading_rate

        # 多目标组合
        multi_objective = economic_weight * economic_objective + loading_weight * loading_objective

        if self.multi_objective_config['optimization_method'] == 'weighted_sum':
            model.setObjective(multi_objective, GRB.MINIMIZE)
        else:
            # Pareto优化方法 (简化处理)
            model.setObjective(multi_objective, GRB.MINIMIZE)

    def _calculate_economic_cost(self, variables: Dict, items: List[EnhancedCargoItem],
                               truck_specs: Dict) -> gp.tuplelist:
        """计算经济成本 (公式3-8, 3-9)"""
        # 简化实现：使用固定成本 + 燃油成本
        if 'x' in variables:
            x = variables['x']

            # 固定成本
            fixed_cost = self.multi_objective_config['fixed_cost_per_vehicle']

            # 燃油成本 (简化计算)
            fuel_cost_per_ton_km = self.multi_objective_config['fuel_cost_per_ton_km']
            empty_weight = self.multi_objective_config['empty_vehicle_weight_tons']

            total_weight = gp.quicksum(
                x[i] * items[i].weight_kg / 1000 for i in range(min(len(items), len(x)))
            )

            # 简化的距离成本（假设平均距离100km）
            avg_distance = 100  # km
            fuel_cost = fuel_cost_per_ton_km * (empty_weight + total_weight) * avg_distance

            total_cost = fixed_cost + fuel_cost
            return total_cost

        return 0

    def _calculate_max_cost(self, truck_specs: Dict) -> float:
        """计算最大成本 (公式3-8)"""
        fixed_cost = self.multi_objective_config['fixed_cost_per_vehicle']
        fuel_cost_per_ton_km = self.multi_objective_config['fuel_cost_per_ton_km']
        empty_weight = self.multi_objective_config['empty_vehicle_weight_tons']
        max_payload = truck_specs['max_weight'] / 1000  # 转换为吨

        # 假设最大距离200km
        max_distance = 200
        max_fuel_cost = fuel_cost_per_ton_km * (empty_weight + max_payload) * max_distance

        return fixed_cost + max_fuel_cost

    def _calculate_loading_rate(self, variables: Dict, items: List[EnhancedCargoItem],
                              truck_specs: Dict) -> gp.tuplelist:
        """计算装载率"""
        if 'x' in variables:
            x = variables['x']
            total_loaded_volume = gp.quicksum(
                x[i] * items[i].volume_m3 for i in range(min(len(items), len(x)))
            )
            loading_rate = total_loaded_volume / truck_specs['volume']
            return loading_rate

        return 0

    def _process_enhanced_result(self, model: gp.Model, variables: Dict,
                               items: List[EnhancedCargoItem], truck_specs: Dict,
                               max_items: int, enable_spatial: bool, enable_time_windows: bool,
                               solve_time: float) -> OptimizationResult:
        """处理增强优化结果"""

        # 基础结果信息
        status = self._get_status_string(model.Status)
        objective_value = model.ObjVal if hasattr(model, 'ObjVal') else 0.0
        gap = model.MIPGap if hasattr(model, 'MIPGap') else 0.0

        # 空间优化结果
        loading_plan = []
        spatial_positions = []
        volume_utilization = 0.0
        weight_utilization = 0.0

        if enable_spatial and 'x' in variables:
            # 提取空间位置信息
            item3d_list = self._convert_to_item3d(items)
            truck = self._create_truck3d(truck_specs)

            spatial_positions = self.spatial_detector.get_solution_positions(
                variables, item3d_list, max_items
            )

            # 验证空间约束
            validation = self.spatial_detector.validate_solution(spatial_positions, truck)
            volume_utilization = validation['statistics']['volume_utilization']
            weight_utilization = validation['statistics']['weight_utilization']

            # 生成装载计划
            for pos in spatial_positions:
                loading_plan.append({
                    'item_id': pos['item_id'],
                    'truck_id': 0,  # 单车优化
                    'position_x': pos['position']['x'],
                    'position_y': pos['position']['y'],
                    'position_z': pos['position']['z'],
                    'orientation': pos['rotation'],
                    'dimensions': pos['dimensions']
                })

        # 时间优化结果
        time_schedule = []
        time_window_violations = {}
        total_time_penalty = 0.0

        if enable_time_windows:
            # 提取时间安排信息
            customer_nodes = self._convert_to_customer_nodes(items)

            # 这里需要路径信息，简化处理
            route_vars = {}
            time_schedule = self.time_optimizer.get_solution_schedule(
                variables, route_vars, customer_nodes, len(items) + 1
            )

            # 验证时间窗
            time_window_violations = self.time_optimizer.validate_time_windows(time_schedule)
            total_time_penalty = time_window_violations['total_penalty']

        # 多目标优化结果
        economic_cost = 0.0
        loading_efficiency = volume_utilization / 100.0  # 转换为小数
        multi_objective_score = (
            self.multi_objective_config['economic_weight'] * economic_cost +
            self.multi_objective_config['loading_rate_weight'] * (1 - loading_efficiency)
        )

        # 构造结果对象
        result = OptimizationResult(
            status=status,
            objective_value=objective_value,
            solve_time=solve_time,
            gap=gap,
            loading_plan=loading_plan,
            spatial_positions=spatial_positions,
            volume_utilization=volume_utilization,
            weight_utilization=weight_utilization,
            time_schedule=time_schedule,
            time_window_violations=time_window_violations,
            total_time_penalty=total_time_penalty,
            economic_cost=economic_cost,
            loading_efficiency=loading_efficiency,
            multi_objective_score=multi_objective_score,
            algorithm="gurobi_enhanced_spatial_temporal",
            solver_config=self.solver_config.copy()
        )

        self.logger.info(f"增强优化结果: {status}, 装载率={volume_utilization:.1f}%, 时间惩罚={total_time_penalty:.2f}元")
        return result

    def _get_status_string(self, status: int) -> str:
        """获取状态字符串"""
        status_map = {
            GRB.OPTIMAL: 'optimal',
            GRB.INFEASIBLE: 'infeasible',
            GRB.UNBOUNDED: 'unbounded',
            GRB.TIME_LIMIT: 'time_limit',
            GRB.INTERRUPTED: 'interrupted',
            GRB.NUMERIC: 'numeric_error'
        }
        return status_map.get(status, f'unknown_{status}')


def test_enhanced_optimizer():
    """测试增强优化器"""
    print("=== Gurobi增强优化器测试 ===")

    # 创建测试货物
    items = [
        EnhancedCargoItem(
            item_id="item_001",
            volume_m3=2.0,
            weight_kg=500,
            estimated_length=2.0,
            estimated_width=1.0,
            estimated_height=1.0,
            earliest_delivery_time="08:00",
            latest_delivery_time="12:00",
            service_time_minutes=15
        ),
        EnhancedCargoItem(
            item_id="item_002",
            volume_m3=1.5,
            weight_kg=300,
            estimated_length=1.5,
            estimated_width=1.0,
            estimated_height=1.0,
            earliest_delivery_time="09:00",
            latest_delivery_time="14:00",
            service_time_minutes=10
        ),
        EnhancedCargoItem(
            item_id="item_003",
            volume_m3=1.0,
            weight_kg=200,
            estimated_length=1.0,
            estimated_width=1.0,
            estimated_height=1.0,
            earliest_delivery_time="10:00",
            latest_delivery_time="16:00",
            service_time_minutes=20
        )
    ]

    # 创建优化器
    optimizer = GurobiOptimizerEnhanced()

    try:
        # 进行优化
        result = optimizer.optimize_with_constraints(
            items=items,
            truck_specs=TRUCK_SPECS,
            max_items=3,
            enable_spatial=True,
            enable_time_windows=True
        )

        print(f"✅ 优化成功!")
        print(f"状态: {result.status}")
        print(f"求解时间: {result.solve_time:.2f}秒")
        print(f"体积利用率: {result.volume_utilization:.2f}%")
        print(f"重量利用率: {result.weight_utilization:.2f}%")
        print(f"时间惩罚: {result.total_time_penalty:.2f}元")
        print(f"多目标得分: {result.multi_objective_score:.4f}")

        print(f"\n空间位置信息:")
        for pos in result.spatial_positions:
            print(f"  货物 {pos['item_id']}: 位置({pos['position']['x']}, {pos['position']['y']}, {pos['position']['z']}), "
                  f"旋转{pos['rotation']}")

        if result.time_schedule:
            print(f"\n时间安排信息:")
            for entry in result.time_schedule:
                print(f"  节点 {entry['node_id']}: 到达 {entry['schedule']['arrival_time']}, "
                      f"时间窗 {entry['time_window']['earliest']}-{entry['time_window']['latest']}")

        if result.time_window_violations['total_violations'] > 0:
            print(f"\n⚠️ 时间窗违规: {result.time_window_violations['total_violations']} 个")
        else:
            print(f"\n✅ 所有时间窗约束都满足")

    except Exception as e:
        print(f"❌ 优化失败: {str(e)}")


if __name__ == "__main__":
    test_enhanced_optimizer()