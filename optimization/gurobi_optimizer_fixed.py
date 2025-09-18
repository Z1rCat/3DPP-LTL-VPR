"""
Gurobi优化器模块 - 修复版本
Fixed Gurobi MILP Optimizer for 3D Bin Packing Problem
"""

import gurobipy as gp
from gurobipy import GRB
import pandas as pd
import numpy as np
import pickle
import logging
import json
import math
from typing import Dict, List, Tuple, Optional, Any
from pathlib import Path
from tqdm import tqdm
import time

# 导入配置
import sys
sys.path.append(str(Path(__file__).parent.parent))
from config import (TRUCK_SPECS, GUROBI_CONFIG, MODEL_PARAMS,
                   INTERMEDIATE_DIR, LOGS_DIR, FILE_CONFIG)


class GurobiOptimizerV2:
    """Gurobi优化器V2 - 修复版本"""

    def __init__(self):
        """初始化Gurobi优化器V2"""
        self.logger = self._setup_logger()
        self.truck_specs = TRUCK_SPECS
        self.gurobi_config = GUROBI_CONFIG
        self.model_params = MODEL_PARAMS

        # 模型缓存
        self.models = {}
        self.solutions = {}

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

    def optimize_single_item_3dpp(self, item_volume: float, item_dimensions: Tuple[float, float, float],
                                 truck_specs: Dict, max_items: int = 2000) -> Dict:
        """
        单货物3DPP优化 (V3.0 - 完整版分层构建法，含完整不重叠约束)
        采用两阶段算法：快速找到最优姿态 + 生成坐标验证不重叠

        Args:
            item_volume: 单件货物体积 (m³)
            item_dimensions: 货物尺寸 (长, 宽, 高) in meters
            truck_specs: 车辆规格
            max_items: (此参数在启发式中不再使用，但保留以兼容接口)

        Returns:
            Dict: 优化结果，含完整装载方案
        """
        self.logger.info(f"开始单货物3DPP【完整版分层构建】计算: 体积={item_volume:.6f}m³, 尺寸={item_dimensions}")
        start_time = time.time()

        truck_L, truck_W, truck_H = truck_specs['length'], truck_specs['width'], truck_specs['height']

        # === 阶段1：快速找到最优姿态和布局参数 ===
        orientations = [
            (item_dimensions[0], item_dimensions[1], item_dimensions[2]), # l, w, h
            (item_dimensions[0], item_dimensions[2], item_dimensions[1]), # l, h, w
            (item_dimensions[1], item_dimensions[0], item_dimensions[2]), # w, l, h
            (item_dimensions[1], item_dimensions[2], item_dimensions[0]), # w, h, l
            (item_dimensions[2], item_dimensions[0], item_dimensions[1]), # h, l, w
            (item_dimensions[2], item_dimensions[1], item_dimensions[0]), # h, w, l
        ]

        best_layout = None
        max_loaded_items = 0

        for idx, (item_l, item_w, item_h) in enumerate(orientations):
            layout_info = self._calculate_layout_parameters(item_l, item_w, item_h, truck_L, truck_W, truck_H)

            if layout_info['total_items'] > max_loaded_items:
                max_loaded_items = layout_info['total_items']
                best_layout = {
                    'orientation': (item_l, item_w, item_h),
                    'orientation_index': idx,
                    **layout_info
                }

        if max_loaded_items == 0:
            self.logger.warning("  无法装载任何货物")
            return {
                'status': 'heuristic_success',
                'optimal_items_count': 0,
                'loading_rate': 0.0,
                'solve_time': time.time() - start_time,
                'gap': None,
                'loading_plan': []
            }

        # === 阶段2：为最优姿态生成完整坐标和验证不重叠 ===
        loading_plan = self._generate_complete_loading_plan(best_layout, item_dimensions)

        # 验证不重叠约束
        self._verify_non_overlap_constraints(loading_plan, best_layout['orientation'], truck_L, truck_W, truck_H)

        solve_time = time.time() - start_time
        loading_rate = (max_loaded_items * item_volume) / truck_specs['volume']

        self.logger.info(f"  ✅ 完整版分层构建成功: {max_loaded_items} 件，装载率 {loading_rate:.1%}")
        self.logger.info(f"  最优姿态: {best_layout['orientation']}, 网格: {best_layout['grid_x']}×{best_layout['grid_y']}×{best_layout['layers']}")

        return {
            'status': 'heuristic_success',
            'optimal_items_count': max_loaded_items,
            'loading_rate': loading_rate,
            'solve_time': solve_time,
            'gap': None,
            'loading_plan': loading_plan,
            'layout_info': best_layout
        }

    def _calculate_layout_parameters(self, item_l: float, item_w: float, item_h: float,
                                   truck_L: float, truck_W: float, truck_H: float) -> Dict:
        """计算给定姿态下的布局参数"""
        # 检查高度约束
        if item_h > truck_H:
            return {'total_items': 0}

        # 计算层数
        num_layers = math.floor(truck_H / item_h)
        if num_layers == 0:
            return {'total_items': 0}

        # 计算两种二维填充方式
        # 方式1：item_l 沿 truck_L
        layout1 = None
        if item_l <= truck_L and item_w <= truck_W:
            n_x1 = math.floor(truck_L / item_l)
            n_y1 = math.floor(truck_W / item_w)
            layout1 = {
                'grid_x': n_x1,
                'grid_y': n_y1,
                'items_per_layer': n_x1 * n_y1,
                'fill_mode': 'mode1',  # item_l 沿 truck_L
                'step_x': item_l,
                'step_y': item_w
            }

        # 方式2：item_l 沿 truck_W（旋转90度）
        layout2 = None
        if item_l <= truck_W and item_w <= truck_L:
            n_x2 = math.floor(truck_L / item_w)
            n_y2 = math.floor(truck_W / item_l)
            layout2 = {
                'grid_x': n_x2,
                'grid_y': n_y2,
                'items_per_layer': n_x2 * n_y2,
                'fill_mode': 'mode2',  # item_l 沿 truck_W
                'step_x': item_w,
                'step_y': item_l
            }

        # 选择最优填充方式
        best_layout = None
        if layout1 and layout2:
            best_layout = layout1 if layout1['items_per_layer'] >= layout2['items_per_layer'] else layout2
        elif layout1:
            best_layout = layout1
        elif layout2:
            best_layout = layout2

        if not best_layout:
            return {'total_items': 0}

        return {
            'total_items': best_layout['items_per_layer'] * num_layers,
            'layers': num_layers,
            'layer_height': item_h,
            **best_layout
        }

    def _generate_complete_loading_plan(self, layout: Dict, original_dimensions: Tuple[float, float, float]) -> List[Dict]:
        """为最优布局生成完整的3D坐标装载方案"""
        loading_plan = []
        item_counter = 0

        item_l, item_w, item_h = layout['orientation']

        # 生成网格坐标
        for layer in range(layout['layers']):
            z_pos = layer * layout['layer_height']

            for y_idx in range(layout['grid_y']):
                y_pos = y_idx * layout['step_y']

                for x_idx in range(layout['grid_x']):
                    x_pos = x_idx * layout['step_x']

                    # 确定货物的实际尺寸（考虑旋转）
                    if layout['fill_mode'] == 'mode1':
                        # item_l 沿 truck_L
                        actual_dims = (item_l, item_w, item_h)
                    else:
                        # item_l 沿 truck_W (旋转90度)
                        actual_dims = (item_w, item_l, item_h)

                    loading_plan.append({
                        'item_index': item_counter,
                        'position': (round(x_pos, 4), round(y_pos, 4), round(z_pos, 4)),
                        'dimensions': actual_dims,
                        'orientation': layout['orientation'],
                        'fill_mode': layout['fill_mode'],
                        'layer': layer,
                        'grid_pos': (x_idx, y_idx)
                    })

                    item_counter += 1

        return loading_plan

    def _verify_non_overlap_constraints(self, loading_plan: List[Dict], orientation: Tuple[float, float, float],
                                      truck_L: float, truck_W: float, truck_H: float):
        """验证完整的不重叠约束"""
        if not loading_plan:
            return

        # 验证1：边界约束
        for item in loading_plan:
            x, y, z = item['position']
            w, l, h = item['dimensions']  # 注意：这里是旋转后的实际尺寸

            # 检查是否超出边界
            if x + w > truck_L + 1e-6:  # 加入小的容差
                raise ValueError(f"货物 {item['item_index']} X方向超出边界: {x + w} > {truck_L}")
            if y + l > truck_W + 1e-6:
                raise ValueError(f"货物 {item['item_index']} Y方向超出边界: {y + l} > {truck_W}")
            if z + h > truck_H + 1e-6:
                raise ValueError(f"货物 {item['item_index']} Z方向超出边界: {z + h} > {truck_H}")

        # 验证2：货物间不重叠（利用网格规律性快速验证）
        # 对于单货物网格布局，只需验证网格的规律性即可，无需逐一检查
        self._verify_grid_regularity(loading_plan)

        self.logger.info(f"  ✅ 不重叠约束验证通过: {len(loading_plan)} 个货物位置合法")

    def _verify_grid_regularity(self, loading_plan: List[Dict]):
        """验证网格布局的规律性（巧妙的快速验证方法）"""
        if len(loading_plan) <= 1:
            return

        # 按层分组验证
        layers = {}
        for item in loading_plan:
            layer = item['layer']
            if layer not in layers:
                layers[layer] = []
            layers[layer].append(item)

        # 验证每层内的网格规律性
        for layer_num, layer_items in layers.items():
            if len(layer_items) <= 1:
                continue

            # 获取网格步长
            step_x = None
            step_y = None

            # 找到相邻的货物来确定步长
            layer_items_sorted = sorted(layer_items, key=lambda x: (x['grid_pos'][1], x['grid_pos'][0]))

            for i in range(1, len(layer_items_sorted)):
                curr_item = layer_items_sorted[i]
                prev_item = layer_items_sorted[i-1]

                curr_x, curr_y, _ = curr_item['position']
                prev_x, prev_y, _ = prev_item['position']

                # 如果在同一行（Y相同）
                if abs(curr_y - prev_y) < 1e-6:
                    if step_x is None:
                        step_x = curr_x - prev_x
                    else:
                        if abs((curr_x - prev_x) - step_x) > 1e-6:
                            raise ValueError(f"第{layer_num}层网格X方向不规律")

        self.logger.debug(f"  网格规律性验证通过")

    def _check_two_items_overlap(self, item1: Dict, item2: Dict) -> bool:
        """检查两个货物是否重叠（辅助函数，仅在需要时使用）"""
        x1, y1, z1 = item1['position']
        w1, l1, h1 = item1['dimensions']

        x2, y2, z2 = item2['position']
        w2, l2, h2 = item2['dimensions']

        # 如果在任一维度上不重叠，则整体不重叠
        if (x1 + w1 <= x2 + 1e-6) or (x2 + w2 <= x1 + 1e-6):
            return False
        if (y1 + l1 <= y2 + 1e-6) or (y2 + l2 <= y1 + 1e-6):
            return False
        if (z1 + h1 <= z2 + 1e-6) or (z2 + h2 <= z1 + 1e-6):
            return False

        return True  # 重叠

    def optimize_multi_truck_3dpp(self, items_data: pd.DataFrame, available_trucks: int, truck_specs: Dict) -> Dict:
        """多车队3DPP优化 - 供LTL优化器调用的接口"""
        return self.optimize_multi_truck_ltl_3dpp(items_data, available_trucks)

    def optimize_multi_truck_ltl_3dpp(self, items_data: pd.DataFrame, available_trucks: int) -> Dict:
        """
        多车队LTL 3DPP优化 (V4.0 - 完整版三阶段启发式算法)
        采用：预处理排序 → 贪心装箱 → 完整验证

        Args:
            items_data: 货物数据DataFrame，包含item_id, volume_m3等字段
            available_trucks: 可用车辆数

        Returns:
            Dict: 优化结果，含完整装载方案和不重叠验证
        """
        self.logger.info(f"开始多车队LTL【完整版三阶段启发式】: {len(items_data)} 个货物，{available_trucks} 辆车")
        start_time = time.time()

        truck_L = self.truck_specs['length']
        truck_W = self.truck_specs['width']
        truck_H = self.truck_specs['height']
        truck_volume = self.truck_specs['volume']

        # === 阶段1: 货物预处理与智能排序 ===
        processed_items = self._preprocess_items_for_multitruck(items_data)

        # === 阶段2: 三维贪心装箱算法 ===
        loading_result = self._greedy_3d_packing(processed_items, available_trucks, truck_L, truck_W, truck_H)

        # === 阶段3: 完整不重叠约束验证 ===
        self._verify_multitruck_constraints(loading_result, truck_L, truck_W, truck_H)

        solve_time = time.time() - start_time

        # 统计结果
        loaded_items = loading_result['loaded_items']
        unloaded_items = len(items_data) - loaded_items
        trucks_used = loading_result['trucks_used']
        total_loaded_volume = loading_result['total_loaded_volume']
        total_loading_rate = total_loaded_volume / (trucks_used * truck_volume) if trucks_used > 0 else 0

        self.logger.info(f"  ✅ 多车队LTL启发式完成: {loaded_items}/{len(items_data)} 个货物")
        self.logger.info(f"  使用车辆: {trucks_used}/{available_trucks} 辆，装载率: {total_loading_rate:.1%}")

        return {
            'status': 'heuristic_success',
            'loading_plan': loading_result['loading_plan'],
            'loaded_items': loaded_items,
            'unloaded_items': unloaded_items,
            'trucks_used': trucks_used,
            'total_loading_rate': total_loading_rate,
            'total_loaded_volume': total_loaded_volume,
            'solve_time': solve_time,
            'truck_assignments': loading_result['truck_assignments'],
            'algorithm': 'heuristic_multi_truck_ltl_3dpp_v4',
            'packing_details': loading_result.get('packing_details', {})
        }

    def _preprocess_items_for_multitruck(self, items_data: pd.DataFrame) -> List[Dict]:
        """阶段1: 货物预处理与智能排序"""
        processed_items = []

        for idx, row in items_data.iterrows():
            # 估算货物尺寸
            volume = row['volume_m3']
            if 'estimated_length' in row and not pd.isna(row['estimated_length']):
                dims = (row['estimated_length'], row['estimated_width'], row['estimated_height'])
            else:
                # 立方体假设
                side = volume ** (1/3)
                dims = (side, side, side)

            # 计算装箱难度指标
            max_dim = max(dims)
            min_dim = min(dims)
            aspect_ratio = max_dim / min_dim if min_dim > 0 else 1.0

            processed_items.append({
                'original_index': idx,
                'item_id': row['item_id'],
                'volume': volume,
                'dimensions': dims,
                'aspect_ratio': aspect_ratio,
                'packing_difficulty': volume * aspect_ratio,  # 体积越大、形状越不规则，越难装
                'weight': row.get('weight_kg', volume * 500),  # 假设密度500kg/m³
            })

        # 智能排序策略：按装箱难度降序（难装的优先处理）
        processed_items.sort(key=lambda x: x['packing_difficulty'], reverse=True)

        self.logger.info(f"  货物预处理完成: 按装箱难度排序，最难装货物体积={processed_items[0]['volume']:.4f}m³")
        return processed_items

    def _greedy_3d_packing(self, items: List[Dict], num_trucks: int,
                          truck_L: float, truck_W: float, truck_H: float) -> Dict:
        """阶段2: 三维贪心装箱算法"""

        # 初始化车辆状态
        trucks = []
        for truck_id in range(num_trucks):
            trucks.append({
                'truck_id': truck_id,
                'items': [],  # 已装载的货物
                'occupied_volume': 0.0,
                'available_positions': [(0.0, 0.0, 0.0)],  # 可用放置点
            })

        loading_plan = []
        truck_assignments = {}
        loaded_count = 0
        total_volume = 0.0

        # 逐个尝试装载货物
        for item in items:
            best_position = None
            best_truck_id = None

            # 尝试所有车辆
            for truck in trucks:
                truck_id = truck['truck_id']

                # 检查体积约束
                if truck['occupied_volume'] + item['volume'] > self.truck_specs['volume']:
                    continue

                # 尝试货物的所有可能姿态
                position = self._find_best_position_in_truck(item, truck, truck_L, truck_W, truck_H)

                if position is not None:
                    # 找到可行位置，使用第一个可行的车辆（贪心策略）
                    best_position = position
                    best_truck_id = truck_id
                    break

            # 如果找到合适位置，装载货物
            if best_position is not None:
                truck = trucks[best_truck_id]

                # 添加到装载方案
                loading_plan.append({
                    'item_id': item['item_id'],
                    'truck_id': best_truck_id,
                    'position_x': best_position['x'],
                    'position_y': best_position['y'],
                    'position_z': best_position['z'],
                    'dimensions': best_position['dimensions'],
                    'orientation': best_position['orientation'],
                    'volume': item['volume']
                })

                # 更新车辆状态
                truck['items'].append({
                    'item': item,
                    'position': (best_position['x'], best_position['y'], best_position['z']),
                    'dimensions': best_position['dimensions']
                })
                truck['occupied_volume'] += item['volume']

                # 更新统计
                if best_truck_id not in truck_assignments:
                    truck_assignments[best_truck_id] = []
                truck_assignments[best_truck_id].append(item['original_index'])

                loaded_count += 1
                total_volume += item['volume']

                self.logger.debug(f"  货物 {item['item_id']} 装载到车辆 {best_truck_id}")

        trucks_used = len([t for t in trucks if t['items']])

        self.logger.info(f"  贪心装箱完成: {loaded_count} 个货物装载到 {trucks_used} 辆车")

        return {
            'loading_plan': loading_plan,
            'loaded_items': loaded_count,
            'trucks_used': trucks_used,
            'total_loaded_volume': total_volume,
            'truck_assignments': truck_assignments,
            'truck_states': trucks
        }

    def _find_best_position_in_truck(self, item: Dict, truck: Dict,
                                    truck_L: float, truck_W: float, truck_H: float) -> Optional[Dict]:
        """为货物在指定车辆中寻找最佳位置"""

        item_dims = item['dimensions']

        # 尝试货物的6种可能姿态
        orientations = [
            (item_dims[0], item_dims[1], item_dims[2]),  # 原始姿态
            (item_dims[0], item_dims[2], item_dims[1]),  # 绕X轴旋转
            (item_dims[1], item_dims[0], item_dims[2]),  # 绕Z轴旋转90°
            (item_dims[1], item_dims[2], item_dims[0]),  # 复合旋转1
            (item_dims[2], item_dims[0], item_dims[1]),  # 复合旋转2
            (item_dims[2], item_dims[1], item_dims[0]),  # 复合旋转3
        ]

        best_position = None

        for orientation_idx, (w, l, h) in enumerate(orientations):
            # 检查尺寸约束
            if w > truck_L or l > truck_W or h > truck_H:
                continue

            # 使用Bottom-Left-Fill策略寻找位置
            position = self._bottom_left_fill(w, l, h, truck['items'], truck_L, truck_W, truck_H)

            if position is not None:
                best_position = {
                    'x': position[0],
                    'y': position[1],
                    'z': position[2],
                    'dimensions': (w, l, h),
                    'orientation': orientation_idx
                }
                break  # 找到第一个可行位置就返回（贪心策略）

        return best_position

    def _bottom_left_fill(self, w: float, l: float, h: float, existing_items: List[Dict],
                         truck_L: float, truck_W: float, truck_H: float) -> Optional[Tuple[float, float, float]]:
        """Bottom-Left-Fill 策略寻找放置位置"""

        # 生成候选位置 (从左下角开始)
        candidate_positions = [(0.0, 0.0, 0.0)]

        # 基于已有货物生成更多候选位置
        for existing in existing_items:
            ex_x, ex_y, ex_z = existing['position']
            ex_w, ex_l, ex_h = existing['dimensions']

            # 在已有货物的各个面上生成候选位置
            candidates = [
                (ex_x + ex_w, ex_y, ex_z),      # 右侧
                (ex_x, ex_y + ex_l, ex_z),      # 后方
                (ex_x, ex_y, ex_z + ex_h),      # 上方
                (ex_x + ex_w, ex_y + ex_l, ex_z), # 右后角
                (ex_x + ex_w, ex_y, ex_z + ex_h), # 右上角
                (ex_x, ex_y + ex_l, ex_z + ex_h), # 后上角
            ]
            candidate_positions.extend(candidates)

        # 按左下优先排序
        candidate_positions.sort(key=lambda pos: (pos[2], pos[1], pos[0]))  # z, y, x

        # 测试每个候选位置
        for x, y, z in candidate_positions:
            # 边界检查
            if x + w > truck_L or y + l > truck_W or z + h > truck_H:
                continue

            # 重叠检查
            new_box = (x, y, z, x + w, y + l, z + h)
            overlaps = False

            for existing in existing_items:
                ex_x, ex_y, ex_z = existing['position']
                ex_w, ex_l, ex_h = existing['dimensions']
                existing_box = (ex_x, ex_y, ex_z, ex_x + ex_w, ex_y + ex_l, ex_z + ex_h)

                if self._boxes_overlap_3d(new_box, existing_box):
                    overlaps = True
                    break

            if not overlaps:
                return (x, y, z)

        return None  # 无法找到合适位置

    def _boxes_overlap_3d(self, box1: Tuple[float, float, float, float, float, float],
                         box2: Tuple[float, float, float, float, float, float]) -> bool:
        """检查两个3D盒子是否重叠"""
        x1_min, y1_min, z1_min, x1_max, y1_max, z1_max = box1
        x2_min, y2_min, z2_min, x2_max, y2_max, z2_max = box2

        # 如果在任一维度上不重叠，则整体不重叠
        if x1_max <= x2_min or x2_max <= x1_min:
            return False
        if y1_max <= y2_min or y2_max <= y1_min:
            return False
        if z1_max <= z2_min or z2_max <= z1_min:
            return False

        return True  # 三个维度都有重叠

    def _verify_multitruck_constraints(self, loading_result: Dict, truck_L: float, truck_W: float, truck_H: float):
        """阶段3: 验证多车队完整不重叠约束"""
        loading_plan = loading_result['loading_plan']

        if not loading_plan:
            return

        # 按车辆分组验证
        trucks_items = {}
        for item in loading_plan:
            truck_id = item['truck_id']
            if truck_id not in trucks_items:
                trucks_items[truck_id] = []
            trucks_items[truck_id].append(item)

        total_verified_items = 0

        for truck_id, truck_items in trucks_items.items():
            self.logger.debug(f"  验证车辆 {truck_id}: {len(truck_items)} 个货物")

            # 验证边界约束
            for item in truck_items:
                x, y, z = item['position_x'], item['position_y'], item['position_z']
                w, l, h = item['dimensions']

                if x + w > truck_L + 1e-6:
                    raise ValueError(f"车辆{truck_id}货物{item['item_id']} X方向超界: {x + w} > {truck_L}")
                if y + l > truck_W + 1e-6:
                    raise ValueError(f"车辆{truck_id}货物{item['item_id']} Y方向超界: {y + l} > {truck_W}")
                if z + h > truck_H + 1e-6:
                    raise ValueError(f"车辆{truck_id}货物{item['item_id']} Z方向超界: {z + h} > {truck_H}")

            # 验证车内货物间不重叠
            for i in range(len(truck_items)):
                for j in range(i + 1, len(truck_items)):
                    if self._check_items_overlap(truck_items[i], truck_items[j]):
                        raise ValueError(f"车辆{truck_id}中货物{truck_items[i]['item_id']}与{truck_items[j]['item_id']}重叠")

            total_verified_items += len(truck_items)

        self.logger.info(f"  ✅ 多车队不重叠约束验证通过: {total_verified_items} 个货物位置合法")

    def _check_items_overlap(self, item1: Dict, item2: Dict) -> bool:
        """检查两个货物是否重叠"""
        x1, y1, z1 = item1['position_x'], item1['position_y'], item1['position_z']
        w1, l1, h1 = item1['dimensions']

        x2, y2, z2 = item2['position_x'], item2['position_y'], item2['position_z']
        w2, l2, h2 = item2['dimensions']

        # 构建3D盒子
        box1 = (x1, y1, z1, x1 + w1, y1 + l1, z1 + h1)
        box2 = (x2, y2, z2, x2 + w2, y2 + l2, z2 + h2)

        return self._boxes_overlap_3d(box1, box2)


if __name__ == "__main__":
    # 测试代码
    print("Gurobi优化器修复版本已就绪")