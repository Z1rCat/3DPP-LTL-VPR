"""
单车取送货路径优化求解器
VRPPD (Vehicle Routing Problem with Pickup and Delivery) Solver
"""

import json
import logging
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Any
from datetime import datetime, timedelta
from pathlib import Path
import time
import random

try:
    from ortools.constraint_solver import routing_enums_pb2
    from ortools.constraint_solver import pywrapcp
    ORTOOLS_AVAILABLE = True
except ImportError:
    ORTOOLS_AVAILABLE = False
    print("[警告] Google OR-Tools 不可用，路径优化功能将被禁用")

import sys
sys.path.append(str(Path(__file__).parent.parent))

from utils.distance_calculator import DistanceCalculator


class VRPPDSolver:
    """VRPPD求解器 - 支持动态燃油成本的取送货路径优化"""

    def __init__(self):
        """初始化VRPPD求解器"""
        self.logger = self._setup_logger()

        # 加载配置参数
        self._load_config()

        # 初始化距离计算器
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

    def _load_config(self):
        """加载配置参数"""
        try:
            from config import ROUTING_CONFIG, ORTOOLS_CONFIG, TRUCK_SPECS
            self.routing_config = ROUTING_CONFIG
            self.ortools_config = ORTOOLS_CONFIG
            self.truck_specs = TRUCK_SPECS
        except ImportError:
            # 使用默认配置
            self.routing_config = {
                'fuel_cost_per_ton_km': 0.16,
                'empty_vehicle_weight': 8.5,
                'depot_coordinates': [104.139111, 30.800835],
                'max_route_time_hours': 12,
                'average_speed_kmh': 40,
                'max_payload_capacity': 15.0
            }
            self.ortools_config = {
                'first_solution_strategy': 'PATH_CHEAPEST_ARC',
                'local_search_metaheuristic': 'GUIDED_LOCAL_SEARCH',
                'time_limit_seconds': 300,
                'log_search': True
            }
            self.truck_specs = {
                'length': 9.6,
                'width': 2.4,
                'height': 2.4,
                'volume': 55.296,
                'max_weight': 18000
            }

    def prepare_routing_data_for_truck(self, truck_id: str, dispatch_plan: Dict,
                                     mapping: Dict, orders_df: pd.DataFrame) -> Dict:
        """
        为指定车辆准备路径优化数据

        Args:
            truck_id: 车辆ID
            dispatch_plan: 完整调度计划
            mapping: ID映射关系
            orders_df: 原始订单数据

        Returns:
            Dict: 路径优化数据
        """
        self.logger.info(f"为车辆 {truck_id} 准备路径优化数据")

        try:
            # 1. 提取该车装载的item_id列表
            truck_data = dispatch_plan['dispatch_plan'].get(truck_id)
            if not truck_data:
                raise ValueError(f"未找到车辆 {truck_id} 的调度数据")

            loaded_items = self._extract_loaded_items(truck_data)

            # 2. 通过mapping映射到原始order_id
            order_ids = self._map_items_to_orders(loaded_items, mapping)

            # 3. 从orders_df提取客户信息
            customer_data = self._extract_customer_data(order_ids, orders_df)

            # 4. 分离取货点和配送点，构建节点列表
            nodes_data = self._build_nodes_data(customer_data)

            # 5. 计算距离矩阵
            distance_matrix = self._calculate_distance_matrix(nodes_data['coordinates'])

            # 6. 构建需求数组
            demands = self._build_demands_array(nodes_data['demands'])

            # 7. 计算初始装载重量
            initial_load = self._calculate_initial_load(nodes_data['delivery_demands'])

            routing_data = {
                'truck_id': truck_id,
                'nodes_data': nodes_data,
                'distance_matrix': distance_matrix,
                'demands': demands,
                'initial_load': initial_load,
                'depot_index': 0,
                'num_nodes': len(nodes_data['coordinates']),
                'vehicle_capacity': self.routing_config['max_payload_capacity'] * 1000  # 转换为kg
            }

            self.logger.info(f"车辆 {truck_id} 路径数据准备完成: {routing_data['num_nodes']} 个节点")
            return routing_data

        except Exception as e:
            self.logger.error(f"准备车辆 {truck_id} 路径数据失败: {str(e)}")
            raise

    def _extract_loaded_items(self, truck_data: Dict) -> List[str]:
        """提取车辆装载的物品ID列表"""
        loaded_items = []

        if truck_data['type'] == 'FULL_TRUCK':
            # 大宗货物车辆
            loaded_items.append(truck_data['source_order'])
        elif truck_data['type'] == 'LTL_TRUCK':
            # LTL车辆
            for item in truck_data['loaded_items']:
                loaded_items.append(item['item_id'])

        return loaded_items

    def _map_items_to_orders(self, loaded_items: List[str], mapping: Dict) -> List[str]:
        """将item_id映射到原始order_id"""
        order_ids = []

        for item_id in loaded_items:
            if item_id in mapping:
                mapped_orders = mapping[item_id]
                if isinstance(mapped_orders, list):
                    order_ids.extend(mapped_orders)
                else:
                    order_ids.append(mapped_orders)
            else:
                # 直接使用item_id作为order_id
                order_ids.append(item_id)

        return list(set(order_ids))  # 去重

    def _extract_customer_data(self, order_ids: List[str], orders_df: pd.DataFrame) -> pd.DataFrame:
        """从原始订单数据中提取客户信息"""
        # 打印调试信息
        self.logger.info(f"可用的列名: {orders_df.columns.tolist()}")
        self.logger.info(f"查找订单ID: {order_ids}")

        # 筛选相关订单
        relevant_orders = orders_df[orders_df['order_id'].isin(order_ids)].copy()

        if relevant_orders.empty:
            raise ValueError("未找到相关的客户订单数据")

        # 定义列名映射关系
        column_mapping = {
            'longitude': ['longitude', '经度'],
            'latitude': ['latitude', '纬度'],
            'weight_kg': ['weight_kg', '重量 (kg)', '重量', 'weight'],
            'order_type': ['订单类型', 'order_type', '类型', 'pickup_delivery']
        }

        # 执行列名映射
        mapped_columns = []
        for target_col, possible_cols in column_mapping.items():
            if target_col not in relevant_orders.columns:
                for col in possible_cols:
                    if col in relevant_orders.columns:
                        relevant_orders[target_col] = relevant_orders[col]
                        mapped_columns.append(f"{col} -> {target_col}")
                        self.logger.info(f"映射列名: {col} -> {target_col}")
                        break
        
        if mapped_columns:
            self.logger.info(f"执行的列名映射: {mapped_columns}")

        # 检查必需的列
        required_columns = ['order_id', 'longitude', 'latitude', 'weight_kg', 'order_type']
        missing_columns = [col for col in required_columns if col not in relevant_orders.columns]

        if missing_columns:
            self.logger.error(f"缺失必需的列: {missing_columns}")
            self.logger.error(f"当前可用的列: {relevant_orders.columns.tolist()}")
            # 再次尝试映射，以防第一次映射失败
            self.logger.info("尝试重新映射列名...")
            for target_col in missing_columns:
                if target_col in column_mapping:
                    for col in column_mapping[target_col]:
                        if col in relevant_orders.columns:
                            relevant_orders[target_col] = relevant_orders[col]
                            self.logger.info(f"重新映射列名: {col} -> {target_col}")
                            break
            
            # 再次检查
            final_missing = [col for col in required_columns if col not in relevant_orders.columns]
            if final_missing:
                raise ValueError(f"缺失必需的列: {final_missing}")

        return relevant_orders

    def _build_nodes_data(self, customer_data: pd.DataFrame) -> Dict:
        """构建节点数据（Depot + 客户点）"""
        # Depot节点（A网点）
        depot_coord = self.routing_config['depot_coordinates']
        # depot_coordinates 是 [经度, 纬度] 格式，需要转换为 (纬度, 经度)
        coordinates = [(depot_coord[1], depot_coord[0])]
        node_types = ['depot']
        order_ids = ['DEPOT']
        demands = [0.0]  # Depot需求为0

        # 客户节点
        delivery_demands = 0.0
        for _, row in customer_data.iterrows():
            # 确保坐标顺序为 (latitude, longitude)
            coordinates.append((row['latitude'], row['longitude']))
            order_ids.append(row['order_id'])

            # 根据订单类型确定需求量，使用订单总重量而不是单件重量
            order_type = row['order_type']
            # 优先使用订单总重量，如果没有则使用单件重量
            order_weight = row.get('order_total_weight_kg', row['weight_kg'])
            
            if order_type == '配送需求':
                demand = -order_weight  # 配送为负需求
                delivery_demands += order_weight  # 累计配送重量
                node_types.append('delivery')
            elif order_type == '取货需求':
                demand = order_weight   # 取货为正需求
                node_types.append('pickup')
            else:
                # 处理其他可能的订单类型，默认按配送处理
                self.logger.warning(f"未知订单类型: {order_type}，按配送需求处理")
                demand = -order_weight
                delivery_demands += order_weight
                node_types.append('delivery')

            demands.append(demand)

        return {
            'coordinates': coordinates,
            'node_types': node_types,
            'order_ids': order_ids,
            'demands': demands,
            'delivery_demands': delivery_demands
        }

    def _calculate_distance_matrix(self, coordinates: List[Tuple[float, float]]) -> np.ndarray:
        """计算距离矩阵"""
        return self.distance_calculator.build_distance_matrix(coordinates)

    def _build_demands_array(self, demands: List[float]) -> List[int]:
        """构建需求数组（转换为kg整数）"""
        return [int(round(demand)) for demand in demands]

    def _calculate_initial_load(self, delivery_demands: float) -> int:
        """计算初始装载重量（车辆从Depot出发时的载重）"""
        return int(delivery_demands)  # 所有配送货物的总重量

    def solve_route(self, routing_data: Dict) -> Dict:
        """
        求解VRPPD模型（增强版）

        Args:
            routing_data: 路径优化数据

        Returns:
            Dict: 路径优化结果
        """
        truck_id = routing_data['truck_id']
        self.logger.info(f"开始求解车辆 {truck_id} 的路径优化问题")

        # 首先验证输入数据
        validation_result = self._validate_routing_data(routing_data)
        if not validation_result['valid']:
            self.logger.error(f"数据验证失败: {validation_result['errors']}")
            return self._empty_route_solution(truck_id)

        # 尝试OR-Tools求解
        if ORTOOLS_AVAILABLE:
            try:
                result = self._solve_with_ortools(routing_data)
                if result and result.get('summary', {}).get('total_stops', 0) > 0:
                    self.logger.info(f"OR-Tools求解成功 - 车辆 {truck_id}")
                    return result
                else:
                    self.logger.warning(f"OR-Tools求解无解 - 车辆 {truck_id}，尝试启发式方法")
            except Exception as e:
                self.logger.error(f"OR-Tools求解失败 - 车辆 {truck_id}: {str(e)}，尝试启发式方法")
        else:
            self.logger.warning(f"OR-Tools不可用 - 车辆 {truck_id}，使用启发式方法")

        # 使用启发式算法作为fallback
        try:
            result = self._solve_with_heuristic(routing_data)
            self.logger.info(f"启发式算法求解完成 - 车辆 {truck_id}")
            return result
        except Exception as e:
            self.logger.error(f"启发式算法求解失败 - 车辆 {truck_id}: {str(e)}")
            return self._empty_route_solution(truck_id)

    def _validate_routing_data(self, routing_data: Dict) -> Dict:
        """验证路径优化数据的完整性"""
        errors = []

        # 检查必需字段
        required_fields = ['truck_id', 'nodes_data', 'distance_matrix', 'demands',
                          'initial_load', 'depot_index', 'num_nodes', 'vehicle_capacity']
        for field in required_fields:
            if field not in routing_data:
                errors.append(f"缺少必需字段: {field}")

        if errors:
            return {'valid': False, 'errors': errors}

        # 检查数据一致性
        num_nodes = routing_data['num_nodes']
        distance_matrix = routing_data['distance_matrix']
        demands = routing_data['demands']

        if distance_matrix.shape != (num_nodes, num_nodes):
            errors.append(f"距离矩阵维度不匹配: {distance_matrix.shape} vs ({num_nodes}, {num_nodes})")

        if len(demands) != num_nodes:
            errors.append(f"需求数组长度不匹配: {len(demands)} vs {num_nodes}")

        # 检查容量约束
        total_delivery_demand = sum(abs(d) for d in demands if d < 0)
        if total_delivery_demand > routing_data['vehicle_capacity']:
            errors.append(f"总配送需求超过车辆容量: {total_delivery_demand} > {routing_data['vehicle_capacity']}")

        return {'valid': len(errors) == 0, 'errors': errors}

    def _solve_with_ortools(self, routing_data: Dict) -> Dict:
        """使用OR-Tools求解VRPPD"""
        truck_id = routing_data['truck_id']
        start_time = time.time()

        try:
            # 1. 创建路径管理器和模型
            manager = pywrapcp.RoutingIndexManager(
                routing_data['num_nodes'],  # 节点数量
                1,  # 车辆数量（单车问题）
                routing_data['depot_index']   # Depot索引
            )
            routing = pywrapcp.RoutingModel(manager)

            # 2. 注册距离回调函数
            distance_callback_index = self._register_distance_callback(manager, routing, routing_data)

            # 3. 创建并注册动态燃油成本回调函数
            fuel_cost_callback_index = self._register_fuel_cost_callback(manager, routing, routing_data)

            # 4. 设置弧成本评估器（使用燃油成本）
            routing.SetArcCostEvaluatorOfAllVehicles(fuel_cost_callback_index)

            # 5. 添加载重维度约束
            self._add_capacity_dimension(manager, routing, routing_data)

            # 6. 添加时间窗口约束（可选）
            self._add_time_dimension(manager, routing, routing_data)

            # 7. 设置搜索参数
            search_parameters = self._create_enhanced_search_parameters(routing_data)

            # 8. 求解
            self.logger.info(f"开始OR-Tools求解... (节点数: {routing_data['num_nodes']})")
            solution = routing.SolveWithParameters(search_parameters)

            solve_time = time.time() - start_time

            # 9. 解析结果
            if solution:
                result = self._parse_solution(manager, routing, solution, routing_data)
                result['solver_info'] = {
                    'method': 'OR-Tools',
                    'solve_time_seconds': round(solve_time, 2),
                    'status': self._get_solution_status(solution.status())
                }
                self.logger.info(f"OR-Tools求解完成 - 车辆 {truck_id} (耗时: {solve_time:.2f}秒)")
                return result
            else:
                self.logger.warning(f"OR-Tools无解 - 车辆 {truck_id}")
                return None

        except Exception as e:
            self.logger.error(f"OR-Tools求解异常 - 车辆 {truck_id}: {str(e)}")
            raise

    def _solve_with_heuristic(self, routing_data: Dict) -> Dict:
        """使用启发式算法求解VRPPD"""
        truck_id = routing_data['truck_id']
        self.logger.info(f"使用启发式算法求解 - 车辆 {truck_id}")
        start_time = time.time()

        # 使用改进的最近邻算法
        result = self._nearest_neighbor_vrppd(routing_data)

        # 尝试局部优化
        optimized_result = self._local_search_optimization(result, routing_data)

        solve_time = time.time() - start_time
        optimized_result['solver_info'] = {
            'method': 'Heuristic_NearestNeighbor_2Opt',
            'solve_time_seconds': round(solve_time, 2),
            'status': 'HEURISTIC_SOLUTION'
        }

        self.logger.info(f"启发式算法求解完成 - 车辆 {truck_id} (耗时: {solve_time:.2f}秒)")
        return optimized_result

    def _register_distance_callback(self, manager, routing, routing_data) -> int:
        """注册距离回调函数"""
        distance_matrix = routing_data['distance_matrix']

        def distance_callback(from_index, to_index):
            from_node = manager.IndexToNode(from_index)
            to_node = manager.IndexToNode(to_index)
            return int(distance_matrix[from_node][to_node] * 1000)  # 转换为米

        return routing.RegisterTransitCallback(distance_callback)

    def _register_fuel_cost_callback(self, manager, routing, routing_data) -> int:
        """注册动态燃油成本回调函数"""
        distance_matrix = routing_data['distance_matrix']
        demands = routing_data['demands']
        fuel_coefficient = self.routing_config['fuel_cost_per_ton_km']
        empty_weight = self.routing_config['empty_vehicle_weight'] * 1000  # 转换为kg
        initial_load = routing_data['initial_load']

        def fuel_cost_callback(from_index, to_index):
            from_node = manager.IndexToNode(from_index)
            to_node = manager.IndexToNode(to_index)

            # 计算距离（km）
            distance_km = distance_matrix[from_node][to_node]

            # 改进的载重估算：基于路径进展动态估算载重
            if from_node == 0:  # 从Depot出发
                current_load = initial_load
            else:
                # 简化估算：基于已服务节点的需求变化
                current_load = initial_load + demands[from_node]

            # 计算总重量（空车 + 当前载重）
            total_weight_kg = empty_weight + current_load
            total_weight_ton = total_weight_kg / 1000.0

            # 计算燃油成本（元 * 100，OR-Tools使用整数）
            fuel_cost = fuel_coefficient * total_weight_ton * distance_km * 100

            return int(fuel_cost)

        return routing.RegisterTransitCallback(fuel_cost_callback)

    def _add_capacity_dimension(self, manager, routing, routing_data):
        """添加载重维度约束"""
        demands = routing_data['demands']
        capacity = routing_data['vehicle_capacity']
        initial_load = routing_data['initial_load']

        def demand_callback(from_index):
            from_node = manager.IndexToNode(from_index)
            return int(demands[from_node])  # 确保返回整数

        demand_callback_index = routing.RegisterUnaryTransitCallback(demand_callback)

        # 添加载重维度
        routing.AddDimensionWithVehicleCapacity(
            demand_callback_index,
            0,  # 无松弛变量
            [int(capacity)],  # 确保车辆容量为整数
            True,  # 从零开始累计
            'Capacity'
        )

        # 设置初始载重
        capacity_dimension = routing.GetDimensionOrDie('Capacity')
        capacity_dimension.SetCumulVarSoftLowerBound(
            manager.NodeToIndex(0), int(initial_load), 1000000
        )

    def _create_enhanced_search_parameters(self, routing_data: Dict):
        """创建增强的搜索参数"""
        search_parameters = pywrapcp.DefaultRoutingSearchParameters()

        # 根据问题规模调整策略
        num_nodes = routing_data['num_nodes']

        if num_nodes <= 10:
            # 小规模问题：使用精确策略
            search_parameters.first_solution_strategy = (
                routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
            )
            search_parameters.local_search_metaheuristic = (
                routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
            )
            time_limit = 60
        elif num_nodes <= 50:
            # 中等规模问题：平衡策略
            search_parameters.first_solution_strategy = (
                routing_enums_pb2.FirstSolutionStrategy.AUTOMATIC
            )
            search_parameters.local_search_metaheuristic = (
                routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
            )
            time_limit = 180
        else:
            # 大规模问题：快速策略
            search_parameters.first_solution_strategy = (
                routing_enums_pb2.FirstSolutionStrategy.PARALLEL_CHEAPEST_INSERTION
            )
            search_parameters.local_search_metaheuristic = (
                routing_enums_pb2.LocalSearchMetaheuristic.TABU_SEARCH
            )
            time_limit = 300

        # 设置时间限制
        search_parameters.time_limit.seconds = self.ortools_config.get('time_limit_seconds', time_limit)

        # 设置日志
        search_parameters.log_search = self.ortools_config.get('log_search', False)

        # 设置解的质量限制
        search_parameters.solution_limit = 10000

        return search_parameters

    def _add_time_dimension(self, manager, routing, routing_data):
        """添加时间维度约束"""
        try:
            distance_matrix = routing_data['distance_matrix']
            avg_speed = self.routing_config['average_speed_kmh']

            def time_callback(from_index, to_index):
                from_node = manager.IndexToNode(from_index)
                to_node = manager.IndexToNode(to_index)
                travel_time_hours = distance_matrix[from_node][to_node] / avg_speed
                return int(travel_time_hours * 3600)  # 转换为秒

            time_callback_index = routing.RegisterTransitCallback(time_callback)

            # 添加时间维度
            max_time = int(self.routing_config['max_route_time_hours'] * 3600)  # 最大工作时间
            routing.AddDimension(
                time_callback_index,
                max_time,  # 松弛时间
                max_time,  # 最大累计时间
                False,     # 不强制从零开始
                'Time'
            )

            self.logger.debug("时间维度约束添加成功")

        except Exception as e:
            self.logger.warning(f"添加时间维度约束失败: {str(e)}")

    def _get_solution_status(self, status_code: int) -> str:
        """获取解的状态描述"""
        status_map = {
            0: 'ROUTING_NOT_SOLVED',
            1: 'ROUTING_SUCCESS',
            2: 'ROUTING_PARTIAL_SUCCESS_LOCAL_OPTIMUM_NOT_REACHED',
            3: 'ROUTING_PARTIAL_SUCCESS_LOCAL_OPTIMUM_REACHED',
            4: 'ROUTING_INVALID',
            5: 'ROUTING_INFEASIBLE'
        }
        return status_map.get(status_code, f'UNKNOWN_STATUS_{status_code}')

    def _parse_solution(self, manager, routing, solution, routing_data) -> Dict:
        """解析求解结果为标准JSON格式"""
        truck_id = routing_data['truck_id']
        nodes_data = routing_data['nodes_data']
        distance_matrix = routing_data['distance_matrix']

        # 提取路径
        route = []
        index = routing.Start(0)
        total_distance = 0
        total_duration = 0
        current_time = datetime.now().replace(hour=8, minute=0, second=0, microsecond=0)

        while not routing.IsEnd(index):
            node_index = manager.IndexToNode(index)

            if node_index > 0:  # 跳过Depot起点
                coordinates = nodes_data['coordinates'][node_index]
                order_id = nodes_data['order_ids'][node_index]
                node_type = nodes_data['node_types'][node_index]
                demand = nodes_data['demands'][node_index]

                # 计算到前一个节点的距离
                prev_index = routing.Start(0) if len(route) == 0 else manager.NodeToIndex(route[-1]['node_index'])
                prev_node = manager.IndexToNode(prev_index)
                segment_distance = distance_matrix[prev_node][node_index]
                total_distance += segment_distance

                # 估算到达时间
                travel_time_hours = segment_distance / self.routing_config['average_speed_kmh']
                current_time += timedelta(hours=travel_time_hours)

                # 服务时间
                service_time_minutes = 15 if node_type == 'delivery' else 10

                route.append({
                    'step': len(route) + 1,
                    'action': '送货' if node_type == 'delivery' else '取货',
                    'order_id': order_id,
                    'coordinates': list(coordinates),
                    'weight_change_kg': demand,
                    'distance_from_previous_km': round(segment_distance, 2),
                    'estimated_arrival': current_time.strftime('%H:%M'),
                    'service_time_minutes': service_time_minutes,
                    'node_index': node_index
                })

                # 更新时间
                current_time += timedelta(minutes=service_time_minutes)
                total_duration += travel_time_hours + (service_time_minutes / 60.0)

            previous_index = index
            index = solution.Value(routing.NextVar(index))

        # 返回Depot
        if route:
            last_node = route[-1]['node_index']
            return_distance = distance_matrix[last_node][0]
            total_distance += return_distance

            return_travel_time = return_distance / self.routing_config['average_speed_kmh']
            current_time += timedelta(hours=return_travel_time)
            total_duration += return_travel_time

        # 计算详细的成本和统计信息
        avg_weight_ton = self.routing_config['empty_vehicle_weight'] + (routing_data['initial_load'] / 2000.0)
        fuel_cost = self.routing_config['fuel_cost_per_ton_km'] * avg_weight_ton * total_distance

        # 计算累计载重变化
        cumulative_load = routing_data['initial_load']
        for stop in route:
            cumulative_load += stop['weight_change_kg']
            stop['cumulative_load_kg'] = cumulative_load

        # 添加地址信息（可扩展）
        for stop in route:
            stop['address'] = f"坐标({stop['coordinates'][0]:.4f}, {stop['coordinates'][1]:.4f})"
            stop['departure_time'] = (datetime.strptime(stop['estimated_arrival'], '%H:%M') +
                                    timedelta(minutes=stop['service_time_minutes'])).strftime('%H:%M')

        # 计算OR-Tools优化质量指标
        solution_status = "OPTIMAL" if solution.status() == 1 else "FEASIBLE"

        return {
            'summary': {
                'vehicle_id': truck_id,
                'total_distance_km': round(total_distance, 2),
                'total_duration_hours': round(total_duration, 2),
                'fuel_cost_yuan': round(fuel_cost, 2),
                'total_stops': len(route),
                'pickup_stops': len([r for r in route if r['action'] == '取货']),
                'delivery_stops': len([r for r in route if r['action'] == '送货']),
                'optimization_algorithm': 'VRPPD_OR_Tools',
                'solution_status': solution_status,
                'completion_time': current_time.strftime('%H:%M'),
                'start_time': '08:00',
                'working_hours': round(total_duration, 2),
                'average_speed_kmh': round(total_distance / total_duration, 2) if total_duration > 0 else 0,
                'initial_load_kg': routing_data['initial_load'],
                'final_load_kg': cumulative_load,
                'load_efficiency': round(routing_data['initial_load'] / routing_data['vehicle_capacity'] * 100, 2)
            },
            'route_details': {
                'depot_info': {
                    'name': 'A网点（成都至重庆专线）',
                    'coordinates': {
                        'lat': self.routing_config['depot_coordinates'][1],
                        'lng': self.routing_config['depot_coordinates'][0]
                    },
                    'address': f"({self.routing_config['depot_coordinates'][1]:.6f}, {self.routing_config['depot_coordinates'][0]:.6f})"
                },
                'vehicle_info': {
                    'type': '9.6米厢式货车',
                    'capacity_kg': routing_data['vehicle_capacity'],
                    'empty_weight_kg': self.routing_config['empty_vehicle_weight'] * 1000,
                    'fuel_coefficient': self.routing_config['fuel_cost_per_ton_km']
                },
                'optimization_info': {
                    'solver': 'Google OR-Tools',
                    'strategy': 'PATH_CHEAPEST_ARC + GUIDED_LOCAL_SEARCH',
                    'time_limit_seconds': self.ortools_config.get('time_limit_seconds', 300),
                    'solution_quality': solution_status
                }
            },
            'itinerary': route,
            'performance_metrics': {
                'total_service_time_minutes': sum(stop['service_time_minutes'] for stop in route),
                'total_travel_time_hours': round(total_duration - sum(stop['service_time_minutes'] for stop in route) / 60.0, 2),
                'longest_segment_km': max([stop['distance_from_previous_km'] for stop in route]) if route else 0,
                'average_segment_km': round(total_distance / len(route), 2) if route else 0,
                'service_efficiency': round(sum(stop['service_time_minutes'] for stop in route) / (total_duration * 60) * 100, 2) if total_duration > 0 else 0
            }
        }

    def _nearest_neighbor_vrppd(self, routing_data: Dict) -> Dict:
        """使用最近邻算法求解VRPPD"""
        truck_id = routing_data['truck_id']
        nodes_data = routing_data['nodes_data']
        distance_matrix = routing_data['distance_matrix']
        demands = routing_data['demands']
        vehicle_capacity = routing_data['vehicle_capacity']
        initial_load = routing_data['initial_load']

        # 初始化
        unvisited = set(range(1, routing_data['num_nodes']))  # 除了depot的所有节点
        current_node = 0  # 从 depot 开始
        route = []
        current_load = initial_load
        total_distance = 0.0

        while unvisited:
            # 在可行的节点中找最近的
            feasible_nodes = []
            for node in unvisited:
                new_load = current_load + demands[node]
                if 0 <= new_load <= vehicle_capacity:
                    feasible_nodes.append(node)

            if not feasible_nodes:
                # 无可行节点，强制结束
                self.logger.warning(f"无法找到可行的下一个节点，当前负载: {current_load}")
                break

            # 选择最近的可行节点
            next_node = min(feasible_nodes, key=lambda n: distance_matrix[current_node][n])

            # 更新状态
            distance = distance_matrix[current_node][next_node]
            total_distance += distance
            current_load += demands[next_node]

            # 添加到路径
            coordinates = nodes_data['coordinates'][next_node]
            order_id = nodes_data['order_ids'][next_node]
            node_type = nodes_data['node_types'][next_node]

            route.append({
                'step': len(route) + 1,
                'action': '送货' if node_type == 'delivery' else '取货',
                'order_id': order_id,
                'coordinates': list(coordinates),
                'weight_change_kg': demands[next_node],
                'distance_from_previous_km': round(distance, 2),
                'cumulative_load_kg': current_load,
                'node_index': next_node
            })

            unvisited.remove(next_node)
            current_node = next_node

        # 返回 depot
        if route:
            return_distance = distance_matrix[current_node][0]
            total_distance += return_distance

        # 计算时间和成本
        total_duration = total_distance / self.routing_config['average_speed_kmh']
        avg_weight_ton = self.routing_config['empty_vehicle_weight'] + (initial_load / 2000.0)
        fuel_cost = self.routing_config['fuel_cost_per_ton_km'] * avg_weight_ton * total_distance

        # 添加时间信息
        current_time = datetime.now().replace(hour=8, minute=0, second=0, microsecond=0)
        for stop in route:
            travel_time_hours = stop['distance_from_previous_km'] / self.routing_config['average_speed_kmh']
            current_time += timedelta(hours=travel_time_hours)
            stop['estimated_arrival'] = current_time.strftime('%H:%M')
            stop['service_time_minutes'] = 15 if stop['action'] == '送货' else 10
            current_time += timedelta(minutes=stop['service_time_minutes'])
            stop['departure_time'] = current_time.strftime('%H:%M')
            stop['address'] = f"坐标({stop['coordinates'][0]:.4f}, {stop['coordinates'][1]:.4f})"

        result = {
            'summary': {
                'vehicle_id': truck_id,
                'total_distance_km': round(total_distance, 2),
                'total_duration_hours': round(total_duration, 2),
                'fuel_cost_yuan': round(fuel_cost, 2),
                'total_stops': len(route),
                'pickup_stops': len([r for r in route if r['action'] == '取货']),
                'delivery_stops': len([r for r in route if r['action'] == '送货']),
                'optimization_algorithm': 'Heuristic_NearestNeighbor',
                'solution_status': 'HEURISTIC_FEASIBLE',
                'completion_time': current_time.strftime('%H:%M'),
                'start_time': '08:00',
                'working_hours': round(total_duration, 2),
                'initial_load_kg': initial_load,
                'final_load_kg': current_load,
                'load_efficiency': round(initial_load / vehicle_capacity * 100, 2)
            },
            'route_details': {
                'depot_info': {
                    'name': 'A网点（成都至重庆专线）',
                    'coordinates': {
                        'lat': self.routing_config['depot_coordinates'][1],
                        'lng': self.routing_config['depot_coordinates'][0]
                    }
                },
                'vehicle_info': {
                    'type': '9.6米箱式货车',
                    'capacity_kg': vehicle_capacity,
                    'empty_weight_kg': self.routing_config['empty_vehicle_weight'] * 1000
                }
            },
            'itinerary': route,
            'performance_metrics': {
                'total_service_time_minutes': sum(stop.get('service_time_minutes', 0) for stop in route),
                'service_efficiency': round(len(route) / total_duration * 100, 2) if total_duration > 0 else 0
            },
            'solver_info': {
                'method': 'Heuristic_NearestNeighbor',
                'solve_time_seconds': 0.0,
                'status': 'HEURISTIC_FEASIBLE'
            }
        }
        
        return result

    def _local_search_optimization(self, solution: Dict, routing_data: Dict) -> Dict:
        """使用局部搜索优化路径（简化的2-opt）"""
        if not solution.get('itinerary') or len(solution['itinerary']) < 3:
            return solution

        route = solution['itinerary']
        distance_matrix = routing_data['distance_matrix']
        improved = True
        max_iterations = 10
        iteration = 0

        while improved and iteration < max_iterations:
            improved = False
            iteration += 1

            # 简化的2-opt：尝试交换相邻的两个节点
            for i in range(len(route) - 1):
                for j in range(i + 1, min(i + 3, len(route))):
                    # 检查交换后的可行性
                    new_route = route[:]
                    new_route[i], new_route[j] = new_route[j], new_route[i]

                    # 重新计算距离
                    old_distance = self._calculate_route_distance(route, distance_matrix)
                    new_distance = self._calculate_route_distance(new_route, distance_matrix)

                    if new_distance < old_distance:
                        route = new_route
                        improved = True
                        self.logger.debug(f"局部优化改进: {old_distance:.2f} -> {new_distance:.2f} km")
                        break

                if improved:
                    break

        # 更新解
        if iteration > 1:
            solution = self._recalculate_solution_metrics(solution, route, routing_data)
            solution['solver_info']['local_search_iterations'] = iteration - 1

        return solution

    def _calculate_route_distance(self, route: List[Dict], distance_matrix: np.ndarray) -> float:
        """计算路径的总距离"""
        if not route:
            return 0.0

        total_distance = distance_matrix[0][route[0]['node_index']]  # depot to first
        for i in range(len(route) - 1):
            total_distance += distance_matrix[route[i]['node_index']][route[i + 1]['node_index']]
        total_distance += distance_matrix[route[-1]['node_index']][0]  # last to depot

        return total_distance

    def _recalculate_solution_metrics(self, solution: Dict, route: List[Dict], routing_data: Dict) -> Dict:
        """重新计算解的指标"""
        distance_matrix = routing_data['distance_matrix']
        total_distance = self._calculate_route_distance(route, distance_matrix)
        total_duration = total_distance / self.routing_config['average_speed_kmh']

        # 重新计算时间和步骤序号
        current_time = datetime.now().replace(hour=8, minute=0, second=0, microsecond=0)
        cumulative_load = routing_data['initial_load']

        # 更新路径中的所有信息，确保顺序正确
        for i, stop in enumerate(route):
            # 更新步骤序号
            stop['step'] = i + 1
            
            # 计算距离
            if i == 0:
                stop['distance_from_previous_km'] = round(distance_matrix[0][stop['node_index']], 2)
            else:
                prev_node = route[i - 1]['node_index']
                stop['distance_from_previous_km'] = round(distance_matrix[prev_node][stop['node_index']], 2)
            
            # 计算到达时间
            travel_time_hours = stop['distance_from_previous_km'] / self.routing_config['average_speed_kmh']
            current_time += timedelta(hours=travel_time_hours)
            stop['estimated_arrival'] = current_time.strftime('%H:%M')
            
            # 更新累计载重
            cumulative_load += stop['weight_change_kg']
            stop['cumulative_load_kg'] = cumulative_load
            
            # 服务时间
            service_time_minutes = stop.get('service_time_minutes', 15 if stop['action'] == '送货' else 10)
            stop['service_time_minutes'] = service_time_minutes
            current_time += timedelta(minutes=service_time_minutes)
            stop['departure_time'] = current_time.strftime('%H:%M')
            
            # 更新地址信息
            stop['address'] = f"坐标({stop['coordinates'][0]:.4f}, {stop['coordinates'][1]:.4f})"

        # 重新计算燃油成本
        avg_weight_ton = self.routing_config['empty_vehicle_weight'] + (routing_data['initial_load'] / 2000.0)
        fuel_cost = self.routing_config['fuel_cost_per_ton_km'] * avg_weight_ton * total_distance

        # 更新总结信息
        solution['summary']['total_distance_km'] = round(total_distance, 2)
        solution['summary']['total_duration_hours'] = round(total_duration, 2)
        solution['summary']['fuel_cost_yuan'] = round(fuel_cost, 2)
        solution['summary']['completion_time'] = current_time.strftime('%H:%M')
        solution['summary']['working_hours'] = round(total_duration, 2)
        solution['summary']['final_load_kg'] = cumulative_load
        solution['itinerary'] = route

        return solution

    def _empty_route_solution(self, truck_id: str) -> Dict:
        """返回空的路径解"""
        return {
            'summary': {
                'vehicle_id': truck_id,
                'total_distance_km': 0.0,
                'total_duration_hours': 0.0,
                'fuel_cost_yuan': 0.0,
                'total_stops': 0,
                'pickup_stops': 0,
                'delivery_stops': 0,
                'optimization_algorithm': 'VRPPD_OR_Tools',
                'status': 'no_solution'
            },
            'route_details': {
                'start_location': {
                    'lat': self.routing_config['depot_coordinates'][1],
                    'lng': self.routing_config['depot_coordinates'][0]
                },
                'end_location': {
                    'lat': self.routing_config['depot_coordinates'][1],
                    'lng': self.routing_config['depot_coordinates'][0]
                }
            },
            'itinerary': [],
            'solver_info': {
                'method': 'FAILED',
                'status': 'NO_SOLUTION'
            }
        }


def test_vrppd_solver():
    """测试VRPPD求解器"""
    if not ORTOOLS_AVAILABLE:
        print("OR-Tools 不可用，跳过测试")
        return

    print("=== VRPPD求解器测试 ===")

    # 创建求解器实例
    solver = VRPPDSolver()

    # 模拟测试数据
    test_routing_data = {
        'truck_id': 'TEST_TRUCK_001',
        'nodes_data': {
            'coordinates': [
                (30.800835, 104.139111),  # Depot
                (30.650, 104.100),        # 配送点1
                (30.700, 104.200),        # 取货点1
                (30.750, 104.050)         # 配送点2
            ],
            'node_types': ['depot', 'delivery', 'pickup', 'delivery'],
            'order_ids': ['DEPOT', 'ORDER_001', 'ORDER_002', 'ORDER_003'],
            'demands': [0, -500, 300, -200],  # kg
            'delivery_demands': 700  # 总配送重量
        },
        'distance_matrix': np.array([
            [0, 25.5, 15.2, 20.1],
            [25.5, 0, 30.8, 18.7],
            [15.2, 30.8, 0, 25.3],
            [20.1, 18.7, 25.3, 0]
        ]),
        'demands': [0, -500, 300, -200],
        'initial_load': 700,
        'depot_index': 0,
        'num_nodes': 4,
        'vehicle_capacity': 15000  # 15吨
    }

    # 求解路径
    result = solver.solve_route(test_routing_data)

    print(f"求解结果:")
    print(f"车辆ID: {result['summary']['vehicle_id']}")
    print(f"总距离: {result['summary']['total_distance_km']} km")
    print(f"总时间: {result['summary']['total_duration_hours']:.2f} 小时")
    print(f"燃油成本: {result['summary']['fuel_cost_yuan']:.2f} 元")
    print(f"停靠点数: {result['summary']['total_stops']}")

    print("\n行程安排:")
    for stop in result['itinerary']:
        print(f"  步骤{stop['step']}: {stop['action']} - {stop['order_id']} "
              f"({stop['coordinates'][0]:.3f}, {stop['coordinates'][1]:.3f}) "
              f"重量变化: {stop['weight_change_kg']}kg")


if __name__ == "__main__":
    test_vrppd_solver()
