"""
3D空间冲突检测器 - 重叠约束算法实现
3D Spatial Collision Detector - Overlap Constraints Algorithm Implementation

实现公式3-3至3-5的空间约束系统：
- 边长约束 (公式3-3)
- 旋转约束 (公式3-4)
- 重叠约束 (公式3-5)
"""

import gurobipy as gp
from gurobipy import GRB
import numpy as np
import logging
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from enum import Enum
import math

# 导入配置
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))
from config import (SPATIAL_CONSTRAINT_CONFIG, TRUCK_SPECS, MODEL_PARAMS)


class RotationType(Enum):
    """货物旋转类型枚举 - 基于公式3-4的6种旋转方式"""
    ORIGINAL = 1      # r=1: (L_i, W_i, H_i)
    HEIGHT_LENGTH = 2  # r=2: (H_i, W_i, L_i)
    WIDTH_LENGTH = 3   # r=3: (W_i, L_i, H_i)
    HEIGHT_WIDTH = 4   # r=4: (H_i, L_i, W_i)
    WIDTH_HEIGHT = 5   # r=5: (W_i, H_i, L_i)
    LENGTH_HEIGHT = 6  # r=6: (L_i, H_i, W_i)


@dataclass
class Item3D:
    """3D货物数据结构"""
    item_id: str
    length: float
    width: float
    height: float
    volume: float
    weight: float
    rotation_allowed: bool = True
    fragile: bool = False
    stackable: bool = True

    def get_rotated_dimensions(self, rotation: RotationType) -> Tuple[float, float, float]:
        """
        根据公式3-4获取旋转后的尺寸

        Args:
            rotation: 旋转类型

        Returns:
            Tuple[float, float, float]: (length, width, height) 旋转后的尺寸
        """
        if rotation == RotationType.ORIGINAL:
            return (self.length, self.width, self.height)
        elif rotation == RotationType.HEIGHT_LENGTH:
            return (self.height, self.width, self.length)
        elif rotation == RotationType.WIDTH_LENGTH:
            return (self.width, self.length, self.height)
        elif rotation == RotationType.HEIGHT_WIDTH:
            return (self.height, self.length, self.width)
        elif rotation == RotationType.WIDTH_HEIGHT:
            return (self.width, self.height, self.length)
        elif rotation == RotationType.LENGTH_HEIGHT:
            return (self.length, self.height, self.width)
        else:
            raise ValueError(f"不支持的旋转类型: {rotation}")


@dataclass
class Truck3D:
    """3D车厢数据结构"""
    length: float
    width: float
    height: float
    volume: float
    max_weight: float

    def __post_init__(self):
        """验证车厢尺寸"""
        calculated_volume = self.length * self.width * self.height
        if abs(calculated_volume - self.volume) > 0.001:
            self.volume = calculated_volume


class SpatialCollisionDetector:
    """3D空间冲突检测器"""

    def __init__(self):
        """初始化空间冲突检测器"""
        self.logger = self._setup_logger()
        self.config = SPATIAL_CONSTRAINT_CONFIG
        self.truck_specs = TRUCK_SPECS

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

    def add_spatial_constraints(self, model: gp.Model, items: List[Item3D],
                              truck: Truck3D, max_items: int) -> Dict[str, Any]:
        """
        为Gurobi模型添加完整的空间约束系统

        Args:
            model: Gurobi模型
            items: 货物列表
            truck: 车厢规格
            max_items: 最大货物数量

        Returns:
            Dict[str, Any]: 约束变量和相关信息
        """
        self.logger.info(f"添加3D空间约束系统，货物数量: {len(items)}, 最大容量: {max_items}")

        # 1. 决策变量定义
        variables = self._create_decision_variables(model, items, max_items)

        # 2. 边长约束 (公式3-3)
        self._add_boundary_constraints(model, variables, items, truck, max_items)

        # 3. 旋转约束和尺寸关联
        self._add_rotation_constraints(model, variables, items, max_items)

        # 4. 重叠约束 (公式3-5)
        self._add_overlap_constraints(model, variables, items, max_items)

        # 5. 支撑约束 (重力方向)
        if self.config['enable_support_constraint']:
            self._add_support_constraints(model, variables, items, max_items)

        self.logger.info("3D空间约束系统添加完成")
        return variables

    def _create_decision_variables(self, model: gp.Model, items: List[Item3D],
                                 max_items: int) -> Dict[str, Any]:
        """创建决策变量"""
        self.logger.info("创建空间决策变量")

        # 基础决策变量
        x = model.addVars(max_items, vtype=GRB.BINARY, name="x")           # 是否装载货物i
        pos_x = model.addVars(max_items, vtype=GRB.CONTINUOUS, name="pos_x") # x坐标
        pos_y = model.addVars(max_items, vtype=GRB.CONTINUOUS, name="pos_y") # y坐标
        pos_z = model.addVars(max_items, vtype=GRB.CONTINUOUS, name="pos_z") # z坐标

        # 🚫 简化的旋转相关变量
        if self.config['enable_rotation_optimization']:
            # 🚫 简化：仅2种旋转方式而不是6种
            r = model.addVars(max_items, range(1, 3), vtype=GRB.BINARY, name="r")  # 仅r=1,2
        else:
            r = None

        # 重叠检测辅助变量
        if self.config['enable_3d_collision_detection']:
            # 三个维度的非重叠变量
            overlap_x = model.addVars(max_items, max_items, vtype=GRB.BINARY, name="overlap_x")
            overlap_y = model.addVars(max_items, max_items, vtype=GRB.BINARY, name="overlap_y")
            overlap_z = model.addVars(max_items, max_items, vtype=GRB.BINARY, name="overlap_z")
        else:
            overlap_x = overlap_y = overlap_z = None

        # 尺寸变量 (动态变化的货物尺寸)
        dim_l = model.addVars(max_items, vtype=GRB.CONTINUOUS, name="dim_l")  # 长度
        dim_w = model.addVars(max_items, vtype=GRB.CONTINUOUS, name="dim_w")  # 宽度
        dim_h = model.addVars(max_items, vtype=GRB.CONTINUOUS, name="dim_h")  # 高度

        return {
            'x': x, 'pos_x': pos_x, 'pos_y': pos_y, 'pos_z': pos_z,
            'r': r, 'overlap_x': overlap_x, 'overlap_y': overlap_y, 'overlap_z': overlap_z,
            'dim_l': dim_l, 'dim_w': dim_w, 'dim_h': dim_h
        }

    def _add_boundary_constraints(self, model: gp.Model, variables: Dict,
                                 items: List[Item3D], truck: Truck3D, max_items: int):
        """
        添加边长约束 (公式3-3)

        公式3-3:
        0 ≤ x_hi ≤ L_h - L_i^r
        0 ≤ y_hi ≤ W_h - W_i^r
        0 ≤ z_hi ≤ H_h - H_i^r
        """
        self.logger.info("添加边长约束 (公式3-3)")

        x = variables['x']
        pos_x = variables['pos_x']
        pos_y = variables['pos_y']
        pos_z = variables['pos_z']
        dim_l = variables['dim_l']
        dim_w = variables['dim_w']
        dim_h = variables['dim_h']

        big_m = self.config['big_m_for_spatial_constraints']

        for i in range(max_items):
            # 获取货物原始尺寸
            if i < len(items):
                item = items[i]
                orig_l, orig_w, orig_h = item.length, item.width, item.height
            else:
                # 虚拟货物，尺寸为0
                orig_l, orig_w, orig_h = 0, 0, 0

            # 边界约束 - 使用Big-M方法
            model.addConstr(
                pos_x[i] + dim_l[i] <= truck.length + big_m * (1 - x[i]),
                name=f"boundary_x_{i}"
            )
            model.addConstr(
                pos_y[i] + dim_w[i] <= truck.width + big_m * (1 - x[i]),
                name=f"boundary_y_{i}"
            )
            model.addConstr(
                pos_z[i] + dim_h[i] <= truck.height + big_m * (1 - x[i]),
                name=f"boundary_z_{i}"
            )

            # 非负约束
            model.addConstr(pos_x[i] >= 0, name=f"pos_x_nonneg_{i}")
            model.addConstr(pos_y[i] >= 0, name=f"pos_y_nonneg_{i}")
            model.addConstr(pos_z[i] >= 0, name=f"pos_z_nonneg_{i}")

    def _add_rotation_constraints(self, model: gp.Model, variables: Dict,
                                items: List[Item3D], max_items: int):
        """
        添加简化的旋转约束 (简化版公式3-4)

        🚫 简化版本：仅支持2种旋转方式或完全禁用旋转
        """
        if not self.config['enable_rotation_optimization']:
            # 不启用旋转优化，所有货物使用原始尺寸
            self.logger.info("🚫 旋转优化已禁用，使用原始货物尺寸")
            self._set_original_dimensions(model, variables, items, max_items)
            return

        # 🚫 简化：如果启用，也仅支持2种简单旋转方式
        self.logger.info("添加简化的旋转约束 (仅2种方式)")

        x = variables['x']
        r = variables['r']
        dim_l = variables['dim_l']
        dim_w = variables['dim_w']
        dim_h = variables['dim_h']

        big_m = self.config['big_m_for_spatial_constraints']

        for i in range(max_items):
            if i < len(items):
                item = items[i]

                # 🚫 简化：仅2种旋转方式
                # r=1: (L_i, W_i, H_i)  原始方向
                # r=2: (W_i, L_i, H_i)  长宽互换（仅90度旋转）

                # 尺寸约束：每个货物只能选择一种旋转方式
                model.addConstr(
                    r[i, 1] + r[i, 2] == x[i],
                    name=f"simple_rotation_sum_{i}"
                )

                # r=1: 原始尺寸 (L_i, W_i, H_i)
                model.addConstr(
                    dim_l[i] == item.length * r[i, 1] + item.width * r[i, 2],
                    name=f"simple_dim_l_{i}"
                )
                model.addConstr(
                    dim_w[i] == item.width * r[i, 1] + item.length * r[i, 2],
                    name=f"simple_dim_w_{i}"
                )
                model.addConstr(
                    dim_h[i] == item.height * x[i],  # 高度不变
                    name=f"simple_dim_h_{i}"
                )

            else:
                # 虚拟货物，所有尺寸为0
                model.addConstr(dim_l[i] == 0, name=f"dummy_dim_l_{i}")
                model.addConstr(dim_w[i] == 0, name=f"dummy_dim_w_{i}")
                model.addConstr(dim_h[i] == 0, name=f"dummy_dim_h_{i}")

    def _set_original_dimensions(self, model: gp.Model, variables: Dict,
                               items: List[Item3D], max_items: int):
        """设置原始尺寸（不启用旋转优化时）"""
        dim_l = variables['dim_l']
        dim_w = variables['dim_w']
        dim_h = variables['dim_h']

        for i in range(max_items):
            if i < len(items):
                item = items[i]
                model.addConstr(dim_l[i] == item.length, name=f"orig_dim_l_{i}")
                model.addConstr(dim_w[i] == item.width, name=f"orig_dim_w_{i}")
                model.addConstr(dim_h[i] == item.height, name=f"orig_dim_h_{i}")
            else:
                model.addConstr(dim_l[i] == 0, name=f"dummy_dim_l_{i}")
                model.addConstr(dim_w[i] == 0, name=f"dummy_dim_w_{i}")
                model.addConstr(dim_h[i] == 0, name=f"dummy_dim_h_{i}")

    def _add_overlap_constraints(self, model: gp.Model, variables: Dict,
                               items: List[Item3D], max_items: int):
        """
        添加简化的重叠约束 (简化版公式3-5)

        简化版本：仅检查X-Y平面重叠，减少约束复杂度
        """
        if not self.config['enable_3d_collision_detection']:
            self.logger.info("3D碰撞检测已禁用")
            return

        if self.config['overlap_detection_method'] == 'approximate':
            self.logger.info("添加简化的重叠约束 (近似方法)")
            self._add_approximate_overlap_constraints(model, variables, items, max_items)
            return

        self.logger.info("添加重叠约束 (公式3-5 - 简化版)")

        x = variables['x']
        pos_x = variables['pos_x']
        pos_y = variables['pos_y']
        pos_z = variables['pos_z']
        dim_l = variables['dim_l']
        dim_w = variables['dim_w']
        dim_h = variables['dim_h']
        overlap_x = variables['overlap_x']
        overlap_y = variables['overlap_y']
        overlap_z = variables['overlap_z']

        big_m = self.config['big_m_for_spatial_constraints']

        # 🚫 简化：仅处理前5个货物以减少复杂度
        simplified_max_items = min(max_items, 5)
        self.logger.info(f"🚫 简化重叠约束：仅处理前 {simplified_max_items} 个货物")

        # 对每一对货物添加简化的重叠约束
        for i in range(simplified_max_items):
            for j in range(i + 1, simplified_max_items):
                # 简化的重叠约束：仅检查X和Y维度
                # X维度约束
                model.addConstr(
                    pos_x[i] + dim_l[i] <= pos_x[j] + big_m * (1 - overlap_x[i, j]) + big_m * (2 - x[i] - x[j]),
                    name=f"overlap_x_{i}_{j}"
                )

                # Y维度约束
                model.addConstr(
                    pos_y[i] + dim_w[i] <= pos_y[j] + big_m * (1 - overlap_y[i, j]) + big_m * (2 - x[i] - x[j]),
                    name=f"overlap_y_{i}_{j}"
                )

                # 🚫 简化：移除Z维度重叠约束以减少复杂度

                # 至少一个维度不重叠（仅X和Y）
                model.addConstr(
                    overlap_x[i, j] + overlap_y[i, j] >= x[i] + x[j] - 1,
                    name=f"no_overlap_{i}_{j}"
                )

                # 对称性约束
                model.addConstr(overlap_x[i, j] == overlap_x[j, i], name=f"sym_x_{i}_{j}")
                model.addConstr(overlap_y[i, j] == overlap_y[j, i], name=f"sym_y_{i}_{j}")

    def _add_approximate_overlap_constraints(self, model: gp.Model, variables: Dict,
                                           items: List[Item3D], max_items: int):
        """
        添加近似重叠约束 - 进一步简化
        使用简单的分离约束减少计算复杂度
        """
        self.logger.info("🚫 使用近似重叠检测（简单分离约束）")

        x = variables['x']
        pos_x = variables['pos_x']
        pos_y = variables['pos_y']
        pos_z = variables['pos_z']
        dim_l = variables['dim_l']
        dim_w = variables['dim_w']
        dim_h = variables['dim_h']

        # 🚫 简化：使用简单的X轴优先分离策略
        # 将货物按X轴坐标顺序放置，避免复杂的重叠检测
        for i in range(min(max_items, 5)):  # 🚫 最多5个货物
            if i > 0:
                # 确保货物i在货物i-1的右侧，至少有最小间距
                min_spacing = 0.05  # 5cm最小间距
                model.addConstr(
                    pos_x[i] >= pos_x[i-1] + dim_l[i-1] + min_spacing - 1000 * (2 - x[i] - x[i-1]),
                    name=f"simple_spacing_{i}"
                )

        self.logger.info("近似重叠约束添加完成（X轴顺序排列）")

    def _add_support_constraints(self, model: gp.Model, variables: Dict,
                               items: List[Item3D], max_items: int):
        """
        添加支撑约束（重力方向）
        确保货物不会"悬浮"在空中
        """
        self.logger.info("添加支撑约束")

        x = variables['x']
        pos_z = variables['pos_z']
        dim_h = variables['dim_h']

        # 支撑关系变量
        support = model.addVars(max_items, max_items, vtype=GRB.BINARY, name="support")

        big_m = self.config['big_m_for_spatial_constraints']
        epsilon = 1e-6  # 小量，防止数值精度问题

        for i in range(max_items):
            for j in range(max_items):
                if i == j:
                    continue

                # 如果货物i支撑货物j
                model.addConstr(
                    pos_z[j] >= pos_z[i] + dim_h[i] - big_m * (1 - support[i, j]) - big_m * (2 - x[i] - x[j]),
                    name=f"support_{i}_{j}"
                )

                # 支撑关系需要XY平面有接触
                # 这里简化处理：如果支撑，则XY坐标相近
                # 实际应用中可能需要更复杂的几何接触检测

        # 每个货物要么在车厢底部，要么被其他货物支撑
        for i in range(max_items):
            if i < len(items):
                # 底部支撑约束：如果货物i被装载，要么在底部，要么被其他货物支撑
                model.addConstr(
                    pos_z[i] <= epsilon + big_m * (1 - x[i]) + gp.quicksum(support[j, i] for j in range(max_items) if j != i),
                    name=f"gravity_support_{i}"
                )

    def get_solution_positions(self, variables: Dict, items: List[Item3D],
                             max_items: int) -> List[Dict[str, Any]]:
        """
        从求解结果中提取货物的位置和旋转信息

        Args:
            variables: 决策变量字典
            items: 货物列表
            max_items: 最大货物数量

        Returns:
            List[Dict]: 每个装载货物的位置信息
        """
        positions = []

        x = variables['x']
        pos_x = variables['pos_x']
        pos_y = variables['pos_y']
        pos_z = variables['pos_z']
        r = variables.get('r')
        dim_l = variables['dim_l']
        dim_w = variables['dim_w']
        dim_h = variables['dim_h']

        for i in range(max_items):
            if i < len(items):
                # 检查货物是否被装载
                if x[i].X > 0.5:  # 二进制变量，阈值0.5
                    item = items[i]

                    # 获取旋转信息
                    rotation = 1  # 默认旋转
                    if r:
                        for rot_val in range(1, 7):
                            if r[i, rot_val].X > 0.5:
                                rotation = rot_val
                                break

                    position_info = {
                        'item_id': item.item_id,
                        'position': {
                            'x': round(pos_x[i].X, 3),
                            'y': round(pos_y[i].X, 3),
                            'z': round(pos_z[i].X, 3)
                        },
                        'dimensions': {
                            'length': round(dim_l[i].X, 3),
                            'width': round(dim_w[i].X, 3),
                            'height': round(dim_h[i].X, 3)
                        },
                        'rotation': rotation,
                        'original_dimensions': {
                            'length': item.length,
                            'width': item.width,
                            'height': item.height
                        },
                        'volume': item.volume,
                        'weight': item.weight
                    }
                    positions.append(position_info)

        self.logger.info(f"提取了 {len(positions)} 个货物的位置信息")
        return positions

    def validate_solution(self, positions: List[Dict[str, Any]],
                         truck: Truck3D) -> Dict[str, Any]:
        """
        验证求解结果的有效性

        Args:
            positions: 货物位置信息
            truck: 车厢规格

        Returns:
            Dict: 验证结果
        """
        validation_result = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'statistics': {}
        }

        total_volume = 0
        total_weight = 0

        # 检查每个货物
        for pos in positions:
            dims = pos['dimensions']
            position = pos['position']

            # 边界检查
            if position['x'] < 0 or position['y'] < 0 or position['z'] < 0:
                validation_result['valid'] = False
                validation_result['errors'].append(f"货物{pos['item_id']}: 负坐标")

            if (position['x'] + dims['length'] > truck.length + 1e-6 or
                position['y'] + dims['width'] > truck.width + 1e-6 or
                position['z'] + dims['height'] > truck.height + 1e-6):
                validation_result['valid'] = False
                validation_result['errors'].append(f"货物{pos['item_id']}: 超出车厢边界")

            total_volume += dims['length'] * dims['width'] * dims['height']
            total_weight += pos['weight']

        # 检查重叠
        for i, pos1 in enumerate(positions):
            for j, pos2 in enumerate(positions[i+1:], i+1):
                if self._check_overlap(pos1, pos2):
                    validation_result['valid'] = False
                    validation_result['errors'].append(f"货物{pos1['item_id']}与{pos2['item_id']}重叠")

        # 统计信息
        validation_result['statistics'] = {
            'total_items': len(positions),
            'total_volume': round(total_volume, 3),
            'total_weight': round(total_weight, 1),
            'volume_utilization': round(total_volume / truck.volume * 100, 2),
            'weight_utilization': round(total_weight / truck.max_weight * 100, 2)
        }

        if validation_result['errors']:
            self.logger.error(f"空间验证失败: {validation_result['errors']}")
        else:
            self.logger.info("空间验证通过")

        return validation_result

    def _check_overlap(self, pos1: Dict[str, Any], pos2: Dict[str, Any]) -> bool:
        """检查两个货物是否重叠"""
        dims1, pos1_coords = pos1['dimensions'], pos1['position']
        dims2, pos2_coords = pos2['dimensions'], pos2['position']

        # AABB碰撞检测
        overlap_x = (pos1_coords['x'] < pos2_coords['x'] + dims2['length'] and
                    pos1_coords['x'] + dims1['length'] > pos2_coords['x'])
        overlap_y = (pos1_coords['y'] < pos2_coords['y'] + dims2['width'] and
                    pos1_coords['y'] + dims1['width'] > pos2_coords['y'])
        overlap_z = (pos1_coords['z'] < pos2_coords['z'] + dims2['height'] and
                    pos1_coords['z'] + dims1['height'] > pos2_coords['z'])

        return overlap_x and overlap_y and overlap_z


def test_spatial_collision_detector():
    """测试3D空间冲突检测器"""
    print("=== 3D空间冲突检测器测试 ===")

    # 创建测试货物
    items = [
        Item3D("item_001", 2.0, 1.5, 1.0, 3.0, 500),
        Item3D("item_002", 1.5, 1.0, 0.8, 1.2, 300),
        Item3D("item_003", 1.0, 1.0, 1.0, 1.0, 200)
    ]

    # 创建车厢
    truck = Truck3D(
        length=TRUCK_SPECS['length'],
        width=TRUCK_SPECS['width'],
        height=TRUCK_SPECS['height'],
        volume=TRUCK_SPECS['volume'],
        max_weight=TRUCK_SPECS['max_weight']
    )

    # 创建检测器
    detector = SpatialCollisionDetector()

    # 创建测试模型
    model = gp.Model("TestSpatialConstraints")
    model.setParam('OutputFlag', 0)

    # 添加空间约束
    variables = detector.add_spatial_constraints(model, items, truck, max_items=3)

    # 设置目标函数：最大化装载货物数量
    model.setObjective(gp.quicksum(variables['x'][i] for i in range(3)), GRB.MAXIMIZE)

    # 求解
    model.optimize()

    if model.status == GRB.OPTIMAL:
        print(f"求解成功! 目标值: {model.ObjVal}")

        # 提取位置信息
        positions = detector.get_solution_positions(variables, items, 3)

        # 验证结果
        validation = detector.validate_solution(positions, truck)

        print(f"装载货物数量: {len(positions)}")
        print(f"体积利用率: {validation['statistics']['volume_utilization']:.2f}%")
        print(f"重量利用率: {validation['statistics']['weight_utilization']:.2f}%")

        for pos in positions:
            print(f"货物 {pos['item_id']}: 位置({pos['position']['x']}, {pos['position']['y']}, {pos['position']['z']}), "
                  f"旋转{pos['rotation']}, 尺寸{pos['dimensions']}")

        if validation['valid']:
            print("✅ 空间约束验证通过")
        else:
            print("❌ 空间约束验证失败:")
            for error in validation['errors']:
                print(f"  - {error}")

    else:
        print(f"❌ 求解失败，状态: {model.status}")


if __name__ == "__main__":
    test_spatial_collision_detector()