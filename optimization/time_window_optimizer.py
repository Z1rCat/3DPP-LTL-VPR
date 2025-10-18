"""
时间窗约束优化器 - 实现公式3-17至3-19的时间窗系统
Time Window Constraint Optimizer - Implementing Time Window System (Formulas 3-17 to 3-19)

实现完整的时间窗约束系统：
- 时间窗约束 (公式3-17)
- 时间递推关系 (公式3-18)
- 服务时间和行驶时间计算 (公式3-19)
"""

import gurobipy as gp
from gurobipy import GRB
import numpy as np
import pandas as pd
import logging
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
import math

# 导入配置
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))
from config import (TIME_WINDOW_CONFIG, ROUTING_CONFIG, DISTANCE_MATRIX)
from utils.distance_calculator import DistanceCalculator


@dataclass
class TimeWindow:
    """时间窗数据结构"""
    earliest_time: str  # E_i - 最早到达时间，格式: "HH:MM"
    latest_time: str    # F_i - 最晚到达时间，格式: "HH:MM"
    service_time: int   # s_ih - 服务时间(分钟)
    penalty_rate: float = 0.0  # 时间窗违反惩罚率(元/分钟)

    def __post_init__(self):
        """验证时间窗格式"""
        try:
            datetime.strptime(self.earliest_time, "%H:%M")
            datetime.strptime(self.latest_time, "%H:%M")
        except ValueError:
            raise ValueError("时间格式错误，应为 'HH:MM'")

    def get_earliest_minutes(self) -> int:
        """获取最早时间（从0点开始的分钟数）"""
        time_obj = datetime.strptime(self.earliest_time, "%H:%M")
        return time_obj.hour * 60 + time_obj.minute

    def get_latest_minutes(self) -> int:
        """获取最晚时间（从0点开始的分钟数）"""
        time_obj = datetime.strptime(self.latest_time, "%H:%M")
        return time_obj.hour * 60 + time_obj.minute

    def is_valid_time_window(self) -> bool:
        """检查时间窗是否有效"""
        return self.get_latest_minutes() > self.get_earliest_minutes()


@dataclass
class CustomerNode:
    """客户节点数据结构"""
    node_id: str
    order_id: str
    coordinates: Tuple[float, float]  # (latitude, longitude)
    demand: float  # 正数=取货，负数=配送
    time_window: TimeWindow
    node_type: str  # 'pickup' or 'delivery'
    priority: int = 1  # 优先级 (1=高, 2=中, 3=低)


@dataclass
class VehicleInfo:
    """车辆信息数据结构"""
    vehicle_id: str
    capacity: float  # 载重能力(kg)
    start_time: str  # T_0 - 开始工作时间
    max_working_hours: float  # 最大工作时间
    average_speed_kmh: float  # 平均速度
    depot_coordinates: Tuple[float, float]  # 车库坐标


class TimeWindowOptimizer:
    """时间窗约束优化器"""

    def __init__(self):
        """初始化时间窗优化器"""
        self.logger = self._setup_logger()
        self.config = TIME_WINDOW_CONFIG
        self.routing_config = ROUTING_CONFIG
        self.distance_calculator = DistanceCalculator()

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

    def add_time_window_constraints(self, model: gp.Model, nodes: List[CustomerNode],
                                  vehicle: VehicleInfo, distance_matrix: np.ndarray,
                                  max_nodes: int) -> Dict[str, Any]:
        """
        为Gurobi模型添加完整的时间窗约束系统

        Args:
            model: Gurobi模型
            nodes: 客户节点列表
            vehicle: 车辆信息
            distance_matrix: 距离矩阵
            max_nodes: 最大节点数

        Returns:
            Dict[str, Any]: 时间相关变量和约束
        """
        self.logger.info(f"添加时间窗约束系统，节点数量: {len(nodes)}, 最大容量: {max_nodes}")

        # 1. 创建时间相关决策变量
        time_vars = self._create_time_variables(model, nodes, max_nodes)

        # 2. 时间窗约束 (公式3-17)
        self._add_time_window_constraints(model, time_vars, nodes, max_nodes)

        # 3. 时间递推关系 (公式3-18)
        self._add_time_progression_constraints(model, time_vars, nodes, vehicle, distance_matrix, max_nodes)

        # 4. 服务时间和行驶时间计算 (公式3-19)
        self._add_travel_time_constraints(model, time_vars, nodes, vehicle, distance_matrix, max_nodes)

        # 5. 工作时间约束
        self._add_working_time_constraints(model, time_vars, vehicle, max_nodes)

        self.logger.info("时间窗约束系统添加完成")
        return time_vars

    def _create_time_variables(self, model: gp.Model, nodes: List[CustomerNode],
                            max_nodes: int) -> Dict[str, Any]:
        """创建时间相关决策变量"""
        self.logger.info("创建时间决策变量")

        # T_ih - 车辆到达节点i的实际时间
        arrival_time = model.addVars(max_nodes, vtype=GRB.CONTINUOUS, name="T_arrival")

        # s_ih - 服务时间
        service_time = model.addVars(max_nodes, vtype=GRB.CONTINUOUS, name="s_service")

        # t_ijh - 行驶时间
        travel_time = model.addVars(max_nodes, max_nodes, vtype=GRB.CONTINUOUS, name="t_travel")

        # 时间窗违反惩罚变量
        early_penalty = model.addVars(max_nodes, vtype=GRB.CONTINUOUS, name="early_penalty")
        late_penalty = model.addVars(max_nodes, vtype=GRB.CONTINUOUS, name="late_penalty")

        # 等待时间变量
        waiting_time = model.addVars(max_nodes, vtype=GRB.CONTINUOUS, name="waiting_time")

        return {
            'arrival_time': arrival_time,
            'service_time': service_time,
            'travel_time': travel_time,
            'early_penalty': early_penalty,
            'late_penalty': late_penalty,
            'waiting_time': waiting_time
        }

    def _add_time_window_constraints(self, model: gp.Model, time_vars: Dict,
                                   nodes: List[CustomerNode], max_nodes: int):
        """
        添加时间窗约束 (公式3-17)

        公式3-17: E_i ≤ T_ih ≤ F_i
        """
        self.logger.info("添加时间窗约束 (公式3-17)")

        arrival_time = time_vars['arrival_time']
        early_penalty = time_vars['early_penalty']
        late_penalty = time_vars['late_penalty']

        start_time_minutes = self.config['start_time_hour'] * 60

        for i in range(max_nodes):
            if i == 0:
                # Depot节点，设置为开始时间
                model.addConstr(
                    arrival_time[i] == start_time_minutes,
                    name=f"depot_start_time_{i}"
                )
                model.addConstr(early_penalty[i] == 0, name=f"depot_early_penalty_{i}")
                model.addConstr(late_penalty[i] == 0, name=f"depot_late_penalty_{i}")
            elif i < len(nodes) + 1:  # +1 因为包含Depot
                node_idx = i - 1  # 去掉Depot
                node = nodes[node_idx]

                # 最早时间约束
                earliest_minutes = node.time_window.get_earliest_minutes()
                if self.config['soft_time_windows']:
                    # 软时间窗：允许早到但有惩罚
                    model.addConstr(
                        arrival_time[i] + early_penalty[i] >= earliest_minutes,
                        name=f"earliest_time_soft_{i}"
                    )
                    model.addConstr(early_penalty[i] >= 0, name=f"early_penalty_nonneg_{i}")
                else:
                    # 硬时间窗：不允许早到
                    model.addConstr(
                        arrival_time[i] >= earliest_minutes,
                        name=f"earliest_time_hard_{i}"
                    )
                    model.addConstr(early_penalty[i] == 0, name=f"early_penalty_zero_{i}")

                # 最晚时间约束
                latest_minutes = node.time_window.get_latest_minutes()
                if self.config['soft_time_windows']:
                    # 软时间窗：允许晚到但有惩罚
                    model.addConstr(
                        arrival_time[i] <= latest_minutes + late_penalty[i],
                        name=f"latest_time_soft_{i}"
                    )
                    model.addConstr(late_penalty[i] >= 0, name=f"late_penalty_nonneg_{i}")
                else:
                    # 硬时间窗：不允许晚到
                    model.addConstr(
                        arrival_time[i] <= latest_minutes,
                        name=f"latest_time_hard_{i}"
                    )
                    model.addConstr(late_penalty[i] == 0, name=f"late_penalty_zero_{i}")

            else:
                # 虚拟节点
                model.addConstr(arrival_time[i] == 0, name=f"dummy_arrival_{i}")
                model.addConstr(early_penalty[i] == 0, name=f"dummy_early_{i}")
                model.addConstr(late_penalty[i] == 0, name=f"dummy_late_{i}")

    def _add_time_progression_constraints(self, model: gp.Model, time_vars: Dict,
                                        nodes: List[CustomerNode], vehicle: VehicleInfo,
                                        distance_matrix: np.ndarray, max_nodes: int):
        """
        添加时间递推关系 (公式3-18)

        公式3-18: T_jh = T_ih + s_ih + t_ijh * q_ijh
        """
        self.logger.info("添加时间递推关系 (公式3-18)")

        arrival_time = time_vars['arrival_time']
        service_time = time_vars['service_time']
        travel_time = time_vars['travel_time']
        waiting_time = time_vars['waiting_time']

        # 创建路径决策变量（这里简化处理，实际应与路径规划模块集成）
        # q_ijh - 车辆是否从i到j
        route_edge = model.addVars(max_nodes, max_nodes, vtype=GRB.BINARY, name="q_route")

        # 路径约束：每个节点最多进入和离开一次
        for i in range(1, max_nodes):  # 跳过Depot
            model.addConstr(
                gp.quicksum(route_edge[j, i] for j in range(max_nodes) if j != i) <= 1,
                name=f"enter_node_{i}"
            )
            model.addConstr(
                gp.quicksum(route_edge[i, j] for j in range(max_nodes) if j != i) <= 1,
                name=f"leave_node_{i}"
            )

        # 时间递推约束
        for i in range(max_nodes):
            for j in range(max_nodes):
                if i != j:
                    # 如果从i到j，则到达j的时间 = 离开i的时间 + 行驶时间
                    leave_time_i = arrival_time[i] + service_time[i] + waiting_time[i]

                    model.addConstr(
                        arrival_time[j] >= leave_time_i + travel_time[i, j] - 1000 * (1 - route_edge[i, j]),
                        name=f"time_progression_{i}_{j}"
                    )

        # Depot特殊处理
        model.addConstr(
            gp.quicksum(route_edge[0, j] for j in range(1, max_nodes)) <= 1,
            name="depot_departure"
        )
        model.addConstr(
            gp.quicksum(route_edge[j, 0] for j in range(1, max_nodes)) <= 1,
            name="depot_return"
        )

        return {'route_edge': route_edge}

    def _add_travel_time_constraints(self, model: gp.Model, time_vars: Dict,
                                   nodes: List[CustomerNode], vehicle: VehicleInfo,
                                   distance_matrix: np.ndarray, max_nodes: int):
        """
        添加服务时间和行驶时间计算 (公式3-19)

        公式3-19:
        t_ijh = d_ij / v_h  (行驶时间)
        s_ih = n_hi * 1     (服务时间，每件货物1分钟)
        """
        self.logger.info("添加服务时间和行驶时间计算 (公式3-19)")

        service_time = time_vars['service_time']
        travel_time = time_vars['travel_time']

        # 行驶时间计算
        for i in range(max_nodes):
            for j in range(max_nodes):
                if i != j:
                    # t_ijh = d_ij / v_h
                    distance_km = distance_matrix[i][j] if i < len(distance_matrix) and j < len(distance_matrix[i]) else 0
                    travel_time_minutes = (distance_km / vehicle.average_speed_kmh) * 60  # 转换为分钟

                    model.addConstr(
                        travel_time[i, j] == travel_time_minutes,
                        name=f"travel_time_calc_{i}_{j}"
                    )

        # 服务时间计算
        for i in range(max_nodes):
            if i == 0:
                # Depot服务时间为0
                model.addConstr(service_time[i] == 0, name=f"depot_service_{i}")
            elif i < len(nodes) + 1:
                node_idx = i - 1
                node = nodes[node_idx]

                # s_ih = n_hi * 1 (每件货物1分钟)
                # 这里简化处理，假设每个节点服务1件货物
                # 实际应用中应根据货物数量计算
                base_service_time = self.config['service_time_per_item']

                model.addConstr(
                    service_time[i] == node.time_window.service_time,
                    name=f"service_time_calc_{i}"
                )
            else:
                # 虚拟节点
                model.addConstr(service_time[i] == 0, name=f"dummy_service_{i}")

    def _add_working_time_constraints(self, model: gp.Model, time_vars: Dict,
                                     vehicle: VehicleInfo, max_nodes: int):
        """添加工作时间约束"""
        self.logger.info("添加工作时间约束")

        arrival_time = time_vars['arrival_time']
        service_time = time_vars['service_time']
        waiting_time = time_vars['waiting_time']

        # 总工作时间不能超过最大限制
        max_working_minutes = vehicle.max_working_hours * 60

        # 计算总工作时间（从离开Depot到返回Depot）
        total_working_time = 0

        # 这里简化处理，实际需要更复杂的路径时间计算
        for i in range(1, max_nodes):
            total_working_time += service_time[i] + waiting_time[i]

        model.addConstr(
            total_working_time <= max_working_minutes,
            name="max_working_time"
        )

    def calculate_time_window_cost(self, time_vars: Dict, nodes: List[CustomerNode],
                                 max_nodes: int) -> float:
        """
        计算时间窗违反的总成本

        Args:
            time_vars: 时间变量字典
            nodes: 客户节点列表
            max_nodes: 最大节点数

        Returns:
            float: 时间窗总成本
        """
        early_penalty = time_vars['early_penalty']
        late_penalty = time_vars['late_penalty']

        total_cost = 0.0

        for i in range(1, min(len(nodes) + 1, max_nodes)):
            node_idx = i - 1
            node = nodes[node_idx]

            early_cost = early_penalty[i].X * self.config['early_delivery_penalty']
            late_cost = late_penalty[i].X * self.config['late_delivery_penalty']

            total_cost += early_cost + late_cost

        return total_cost

    def get_solution_schedule(self, time_vars: Dict, route_vars: Dict,
                            nodes: List[CustomerNode], max_nodes: int) -> List[Dict[str, Any]]:
        """
        从求解结果中提取时间安排

        Args:
            time_vars: 时间变量字典
            route_vars: 路径变量字典
            nodes: 客户节点列表
            max_nodes: 最大节点数

        Returns:
            List[Dict]: 时间安排列表
        """
        schedule = []
        arrival_time = time_vars['arrival_time']
        service_time = time_vars['service_time']
        waiting_time = time_vars['waiting_time']
        early_penalty = time_vars['early_penalty']
        late_penalty = time_vars['late_penalty']

        # 构建路径
        route_edges = route_vars.get('route_edge', {})
        current_node = 0  # 从Depot开始
        visited = set()
        step = 1

        while current_node not in visited and step < max_nodes:
            visited.add(current_node)

            if current_node > 0:  # 跳过Depot
                node_idx = current_node - 1
                if node_idx < len(nodes):
                    node = nodes[node_idx]

                    arrival_minutes = arrival_time[current_node].X
                    service_minutes = service_time[current_node].X
                    waiting_minutes = waiting_time[current_node].X
                    early_minutes = early_penalty[current_node].X
                    late_minutes = late_penalty[current_node].X

                    schedule_entry = {
                        'step': step,
                        'node_id': node.node_id,
                        'order_id': node.order_id,
                        'node_type': node.node_type,
                        'coordinates': node.coordinates,
                        'demand': node.demand,
                        'time_window': {
                            'earliest': node.time_window.earliest_time,
                            'latest': node.time_window.latest_time
                        },
                        'schedule': {
                            'arrival_time': self._minutes_to_time(arrival_minutes),
                            'service_time': int(service_minutes),
                            'waiting_time': int(waiting_minutes),
                            'departure_time': self._minutes_to_time(arrival_minutes + service_minutes + waiting_minutes)
                        },
                        'violations': {
                            'early_arrival': int(early_minutes),
                            'late_arrival': int(late_minutes),
                            'early_penalty': early_minutes * self.config['early_delivery_penalty'],
                            'late_penalty': late_minutes * self.config['late_delivery_penalty']
                        }
                    }
                    schedule.append(schedule_entry)

            # 找下一个节点
            next_node = None
            if route_edges:
                for j in range(max_nodes):
                    if current_node != j and route_edges[current_node, j].X > 0.5:
                        next_node = j
                        break

            if next_node is None:
                break
            else:
                current_node = next_node
                step += 1

        self.logger.info(f"提取了 {len(schedule)} 个节点的时间安排")
        return schedule

    def _minutes_to_time(self, minutes: float) -> str:
        """将分钟数转换为时间字符串"""
        hours = int(minutes // 60)
        mins = int(minutes % 60)
        return f"{hours:02d}:{mins:02d}"

    def validate_time_windows(self, schedule: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        验证时间窗约束的满足情况

        Args:
            schedule: 时间安排列表

        Returns:
            Dict: 验证结果
        """
        validation_result = {
            'valid': True,
            'violations': [],
            'statistics': {},
            'total_penalty': 0.0
        }

        total_early_violations = 0
        total_late_violations = 0
        total_early_penalty = 0.0
        total_late_penalty = 0.0

        for entry in schedule:
            violations = entry['violations']
            time_window = entry['time_window']
            schedule_time = entry['schedule']['arrival_time']

            # 检查早到
            if violations['early_arrival'] > 0:
                total_early_violations += 1
                total_early_penalty += violations['early_penalty']
                validation_result['violations'].append({
                    'node_id': entry['node_id'],
                    'type': 'early_arrival',
                    'scheduled_time': schedule_time,
                    'earliest_time': time_window['earliest'],
                    'violation_minutes': violations['early_arrival'],
                    'penalty': violations['early_penalty']
                })

            # 检查晚到
            if violations['late_arrival'] > 0:
                total_late_violations += 1
                total_late_penalty += violations['late_penalty']
                validation_result['violations'].append({
                    'node_id': entry['node_id'],
                    'type': 'late_arrival',
                    'scheduled_time': schedule_time,
                    'latest_time': time_window['latest'],
                    'violation_minutes': violations['late_arrival'],
                    'penalty': violations['late_penalty']
                })

        # 统计信息
        validation_result['statistics'] = {
            'total_nodes': len(schedule),
            'early_violations': total_early_violations,
            'late_violations': total_late_violations,
            'total_violations': total_early_violations + total_late_violations,
            'on_time_rate': round((len(schedule) - total_early_violations - total_late_violations) / len(schedule) * 100, 2) if schedule else 0
        }

        validation_result['total_penalty'] = total_early_penalty + total_late_penalty

        if validation_result['total_violations'] > 0:
            self.logger.warning(f"时间窗验证发现 {validation_result['total_violations']} 个违规")
        else:
            self.logger.info("时间窗验证通过")

        return validation_result


def test_time_window_optimizer():
    """测试时间窗约束优化器"""
    print("=== 时间窗约束优化器测试 ===")

    # 创建测试客户节点
    nodes = [
        CustomerNode(
            node_id="node_001",
            order_id="order_001",
            coordinates=(30.650, 104.100),
            demand=-500,  # 配送500kg
            time_window=TimeWindow("08:00", "12:00", 15),
            node_type="delivery"
        ),
        CustomerNode(
            node_id="node_002",
            order_id="order_002",
            coordinates=(30.700, 104.200),
            demand=300,   # 取货300kg
            time_window=TimeWindow("09:00", "14:00", 10),
            node_type="pickup"
        ),
        CustomerNode(
            node_id="node_003",
            order_id="order_003",
            coordinates=(30.750, 104.050),
            demand=-200,  # 配送200kg
            time_window=TimeWindow("10:00", "16:00", 20),
            node_type="delivery"
        )
    ]

    # 创建车辆信息
    vehicle = VehicleInfo(
        vehicle_id="truck_001",
        capacity=15000,  # 15吨
        start_time="06:00",  # T_0 = 6点
        max_working_hours=10,
        average_speed_kmh=40,
        depot_coordinates=(30.800835, 104.139111)
    )

    # 计算距离矩阵
    coordinates = [vehicle.depot_coordinates] + [node.coordinates for node in nodes]
    distance_calculator = DistanceCalculator()
    distance_matrix = distance_calculator.build_distance_matrix(coordinates)

    # 创建时间窗优化器
    optimizer = TimeWindowOptimizer()

    # 创建测试模型
    model = gp.Model("TestTimeWindows")
    model.setParam('OutputFlag', 0)

    # 添加时间窗约束
    time_vars = optimizer.add_time_window_constraints(
        model, nodes, vehicle, distance_matrix, max_nodes=len(nodes) + 1
    )

    # 设置目标函数：最小化时间窗惩罚
    total_penalty = gp.quicksum(
        time_vars['early_penalty'][i] * optimizer.config['early_delivery_penalty'] +
        time_vars['late_penalty'][i] * optimizer.config['late_delivery_penalty']
        for i in range(1, len(nodes) + 1)
    )
    model.setObjective(total_penalty, GRB.MINIMIZE)

    # 求解
    model.optimize()

    if model.status == GRB.OPTIMAL:
        print(f"求解成功! 目标值: {model.ObjVal}")

        # 提取时间安排
        route_vars = {}  # 这里简化处理
        schedule = optimizer.get_solution_schedule(time_vars, route_vars, nodes, len(nodes) + 1)

        # 验证时间窗
        validation = optimizer.validate_time_windows(schedule)

        print(f"服务节点数量: {len(schedule)}")
        print(f"准时到达率: {validation['statistics']['on_time_rate']:.2f}%")
        print(f"总惩罚成本: {validation['total_penalty']:.2f}元")

        for entry in schedule:
            print(f"节点 {entry['node_id']} ({entry['node_type']}): "
                  f"到达 {entry['schedule']['arrival_time']}, "
                  f"时间窗 {entry['time_window']['earliest']}-{entry['time_window']['latest']}")

        if validation['total_violations'] == 0:
            print("✅ 时间窗约束验证通过")
        else:
            print("⚠️ 时间窗约束有违规:")
            for violation in validation['violations']:
                print(f"  - {violation}")

    else:
        print(f"❌ 求解失败，状态: {model.status}")


if __name__ == "__main__":
    test_time_window_optimizer()