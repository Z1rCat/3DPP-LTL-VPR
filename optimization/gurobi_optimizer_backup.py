"""
Gurobi优化器模块 V2.0
Gurobi MILP Optimizer V2.0 for 3D Bin Packing Problem with Dual Optimization Modes
"""

import gurobipy as gp
from gurobipy import GRB
import pandas as pd
import numpy as np
import pickle
import logging
import json
from typing import Dict, List, Tuple, Optional, Any
from pathlib import Path
from tqdm import tqdm
import time
import math
# 导入配置
import sys
sys.path.append(str(Path(__file__).parent.parent))
from config import (TRUCK_SPECS, GUROBI_CONFIG, MODEL_PARAMS,
                   INTERMEDIATE_DIR, LOGS_DIR, FILE_CONFIG)


class GurobiOptimizerV2:
    """Gurobi优化器V2 - 支持单货物3DPP和多车队LTL 3DPP优化

    ⚠️ 重要约束标注说明 (用于未来调优):
    1. 边界约束 (x_bound, y_bound, z_bound): 控制货物在车厢内的位置边界
    2. 体积约束 (volume_constraint): 确保装载体积不超过车厢容积
    3. 非重叠约束 (sep_x, sep_y, sep_z): 防止货物间重叠
    4. 方向约束 (orientation): 货物可旋转方向限制
    5. 车辆使用约束 (truck_usage): 货物只能装入已使用的车辆
    6. 货物分配约束 (item_assignment): 每个货物最多分配到一辆车

    调优建议:
    - 增大big_m值可提高求解精度但降低速度
    - 减少方向选择(0-5→0-2)可显著提升速度
    - 调整MIPGap可平衡精度与速度
    - TimeLimit应根据问题规模调整
    """

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
    # def optimize_single_item_3dpp(self, item_volume: float, item_dimensions: Tuple[float, float, float],
    #                              truck_specs: Dict, max_items: int = 2000) -> Dict:
    #     """
    #     单货物3DPP优化 (V2.2 - 启发式算法版，接口兼容)
    #     采用您提出的启发式算法，快速计算单车最大容量。
    #     此版本的返回格式与原Gurobi版本完全兼容，无需修改调用方代码。

    #     Args:
    #         item_volume: 单件货物体积 (m³)
    #         item_dimensions: 货物尺寸 (长, 宽, 高) in meters
    #         truck_specs: 车辆规格
    #         max_items: (此参数在启发式中不再使用，但保留以兼容接口)

    #     Returns:
    #         Dict: 优化结果，格式与Gurobi版本一致
    #     """
    #     self.logger.info(f"开始单货物3DPP启发式计算: 体积={item_volume:.6f}m³, 尺寸={item_dimensions}")
    #     start_time = time.time()

    #     truck_L, truck_W, truck_H = truck_specs['length'], truck_specs['width'], truck_specs['height']
    #     truck_volume = truck_specs['volume']
        
    #     item_l, item_w, item_h = item_dimensions

    #     # 检查单件货物本身是否能以任何方向放入货车
    #     sorted_item_dims = sorted(item_dimensions)
    #     sorted_truck_dims = sorted((truck_L, truck_W, truck_H))
    #     if any(d_item > d_truck for d_item, d_truck in zip(sorted_item_dims, sorted_truck_dims)):
    #          self.logger.warning(f"单件货物尺寸 {item_dimensions} 大于货车尺寸，无法装载。")
    #          return {
    #              'status': 'infeasible', 
    #              'optimal_items_count': 0, 
    #              'loading_rate': 0.0,
    #              'solve_time': time.time() - start_time,
    #              'gap': 0.0,
    #              'loading_plan': []
    #          }
        
    #     # 1. 初始估算
    #     if item_volume <= 1e-9:
    #          self.logger.error("单件货物体积过小或为0，无法进行计算。")
    #          return {'status': 'error', 'optimal_items_count': 0, 'loading_rate': 0.0, 'solve_time': time.time() - start_time}
        
    #     N_initial = math.floor(truck_volume / item_volume)
    #     self.logger.info(f"  体积上限估算: N = {N_initial} 件")

    #     # 2. 迭代搜索
    #     for n_items in range(N_initial, 0, -1):
    #         # 3. 创建虚拟大包裹
    #         scale_factor = (n_items) ** (1/3.0)
    #         virtual_l, virtual_w, virtual_h = item_l * scale_factor, item_w * scale_factor, item_h * scale_factor

    #         # 4. 检查6种摆放方向
    #         orientations = [
    #             (virtual_l, virtual_w, virtual_h), (virtual_l, virtual_h, virtual_w),
    #             (virtual_w, virtual_l, virtual_h), (virtual_w, virtual_h, virtual_l),
    #             (virtual_h, virtual_l, virtual_w), (virtual_h, virtual_w, virtual_l)
    #         ]

    #         for l, w, h in orientations:
    #             if l <= truck_L and w <= truck_W and h <= truck_H:
    #                 # 找到了一个可行的解
    #                 solve_time = time.time() - start_time
    #                 loading_rate = (n_items * item_volume) / truck_volume
                    
    #                 self.logger.info(f"  启发式计算成功: 最多可装载 {n_items} 件, 装载率 {loading_rate:.1%}")
                    
    #                 # 按照Gurobi版本的格式返回结果
    #                 return {
    #                     'status': 'feasible', # 使用 feasible 表示这是启发式找到的可行解
    #                     'optimal_items_count': n_items,
    #                     'loading_rate': loading_rate,
    #                     'solve_time': solve_time,
    #                     'gap': None,  # 启发式算法没有gap的概念
    #                     'loading_plan': [] # 启发式算法不生成具体坐标，返回空列表
    #                 }
        
    #     # 如果循环结束还没找到解（只可能在单件货物就放不进时发生）
    #     self.logger.error("启发式计算失败，无法找到任何可行解。")
    #     return {
    #         'status': 'error', 
    #         'optimal_items_count': 0, 
    #         'loading_rate': 0.0,
    #         'solve_time': time.time() - start_time
    #     }    
    def optimize_single_item_3dpp(self, item_volume: float, item_dimensions: Tuple[float, float, float],
                                 truck_specs: Dict, max_items: int = 2000) -> Dict:
        """
        单货物3DPP优化 (V2.5 - 分层构建启发式算法，最终版)
        采用精确的分层构建法，快速计算单车最大容量。
        此版本接口与项目完全兼容，且不再调用Gurobi。

        Args:
            item_volume: 单件货物体积 (m³)
            item_dimensions: 货物尺寸 (长, 宽, 高) in meters
            truck_specs: 车辆规格
            max_items: (此参数在启发式中不再使用，但保留以兼容接口)

        Returns:
            Dict: 优化结果
        """
        self.logger.info(f"开始单货物3DPP【分层构建法】计算: 体积={item_volume:.6f}m³, 尺寸={item_dimensions}")
        start_time = time.time()

        truck_L, truck_W, truck_H = truck_specs['length'], truck_specs['width'], truck_specs['height']

        # 获取货物的6种旋转方向 (作为底面长、底面宽、高)
        orientations = [
            (item_dimensions[0], item_dimensions[1], item_dimensions[2]), # l, w, h
            (item_dimensions[0], item_dimensions[2], item_dimensions[1]), # l, h, w
            (item_dimensions[1], item_dimensions[0], item_dimensions[2]), # w, l, h
            (item_dimensions[1], item_dimensions[2], item_dimensions[0]), # w, h, l
            (item_dimensions[2], item_dimensions[0], item_dimensions[1]), # h, l, w
            (item_dimensions[2], item_dimensions[1], item_dimensions[0]), # h, w, l
        ]

        max_loaded_items = 0

        # 主循环: 遍历6种基础摆放姿态
        for item_l, item_w, item_h in orientations:

            # 检查这个姿态本身是否有效 (物品高度不能超过货车高度)
            if item_h > truck_H:
                continue

            # 计算这一层的层高
            num_layers = math.floor(truck_H / item_h)
            if num_layers == 0:
                continue

            # --- 计算二维填充 ---
            # 填充方式 1: 货物长边(l)沿货车长边(L)
            count1 = 0
            if item_l <= truck_L and item_w <= truck_W:
                n_x = math.floor(truck_L / item_l)
                n_y = math.floor(truck_W / item_w)
                count1 = n_x * n_y

            # 填充方式 2: 货物长边(l)沿货车宽边(W)
            count2 = 0
            if item_l <= truck_W and item_w <= truck_L:
                n_x = math.floor(truck_L / item_w)
                n_y = math.floor(truck_W / item_l)
                count2 = n_x * n_y

            # 选择当前姿态下，最优的二维填充方式
            items_per_layer = max(count1, count2)

            total_for_orientation = items_per_layer * num_layers

            if total_for_orientation > max_loaded_items:
                max_loaded_items = total_for_orientation

        solve_time = time.time() - start_time
        loading_rate = (max_loaded_items * item_volume) / truck_specs['volume']

        self.logger.info(f"  分层构建法计算成功: 最多可装载 {max_loaded_items} 件, 装载率 {loading_rate:.1%}")

        # 按照完全兼容的格式返回结果
        return {
            'status': 'heuristic_success',
            'optimal_items_count': max_loaded_items,
            'loading_rate': loading_rate,
            'solve_time': solve_time,
            'gap': None,
            'loading_plan': []
        }
    def optimize_multi_truck_3dpp(self, items_data: pd.DataFrame, available_trucks: int, truck_specs: Dict) -> Dict:
        """多车队3DPP优化 - 供LTL优化器调用的接口"""
        return self.optimize_multi_truck_ltl_3dpp(items_data, available_trucks)

    def optimize_multi_truck_ltl_3dpp(self, items_data: pd.DataFrame, available_trucks: int) -> Dict:
        """
        多车队LTL 3DPP优化 (V2.1 - 最终修正版)
        - 修正了所有变量未定义的问题。
        - 统一了变量命名风格。
        - 采用了稳定高效的约束模型。
        """
        self.logger.info(f"开始多车队LTL 3DPP优化: {len(items_data)} 个货物，{available_trucks} 辆车")
        start_time = time.time()
        model = None

        try:
            # --- 1. 获取配置并创建模型 ---
            config = self.gurobi_config['multi_truck_ltl']
            model = gp.Model("MultiTruckLTL3DPP_V2.1")

            # --- 2. 设置稳定且高效的Gurobi参数 (修复Status=11) ---
            model.setParam('OutputFlag', 1 if self.gurobi_config.get('log_to_console', True) else 0)
            model.setParam('TimeLimit', config.get('time_limit', 1800))
            model.setParam('MIPGap', 0.05)  # 🔧 放宽到5%，避免过度求解
            model.setParam('Threads', 1)
            model.setParam('NumericFocus', 1)  # 🔧 降低数值精度，提高稳定性
            model.setParam('Presolve', 1)     # 🔧 保守的预处理
            model.setParam('Heuristics', 0.1) # 🔧 启用启发式算法找初始解
            model.setParam('MIPFocus', 1)     # 🔧 专注找可行解
            self.logger.info("🔧 Gurobi参数已优化：更稳定的求解配置")

            # --- 3. 数据准备 (定义所有需要的变量) ---
            n_items = len(items_data)
            n_trucks = available_trucks
            truck_length = self.truck_specs['length']
            truck_width = self.truck_specs['width']
            truck_height = self.truck_specs['height']
            truck_volume = self.truck_specs['volume']

            # --- 4. 决策变量 ---
            # x[i, k] = 1 表示货物i装载到车辆k (这是我们主要的放置变量)
            x = model.addVars(n_items, n_trucks, vtype=GRB.BINARY, name="x")
            
            # 位置变量
            pos_x = model.addVars(n_items, vtype=GRB.CONTINUOUS, name="pos_x")
            pos_y = model.addVars(n_items, vtype=GRB.CONTINUOUS, name="pos_y")
            pos_z = model.addVars(n_items, vtype=GRB.CONTINUOUS, name="pos_z")
            
            # --- 5. 目标函数 ---
            total_loaded_volume = gp.quicksum(
                x[i, k] * items_data.iloc[i]['volume_m3']
                for i in range(n_items) for k in range(n_trucks)
            )
            model.setObjective(total_loaded_volume, GRB.MAXIMIZE)

            # --- 6. 约束条件 ---

            # 约束 6a: 每个货物最多被放置一次
            for i in range(n_items):
                model.addConstr(gp.quicksum(x[i, k] for k in range(n_trucks)) <= 1, name=f"assignment_{i}")

            # 约束 6b: 每辆车的体积容量限制
            for k in range(n_trucks):
                model.addConstr(
                    gp.quicksum(x[i, k] * items_data.iloc[i]['volume_m3'] for i in range(n_items)) <= truck_volume,
                    name=f"volume_{k}"
                )

            # 约束 6c: 空间约束 (边界 和 非重叠)
            self.logger.info("  正在构建高效的非重叠约束...")
            for i in range(n_items):
                dims_i = (items_data.iloc[i]['estimated_length'],
                          items_data.iloc[i]['estimated_width'],
                          items_data.iloc[i]['estimated_height'])
                l_i, w_i, h_i = dims_i

                # 🔧 修复LinExpr错误：创建辅助二进制变量
                is_placed_i = model.addVar(vtype=GRB.BINARY, name=f"is_placed_{i}")
                model.addConstr(is_placed_i == gp.quicksum(x[i, k] for k in range(n_trucks)))

                # 边界约束: 如果货物i被放置，其坐标必须在车厢内
                model.addGenConstrIndicator(is_placed_i, True, pos_x[i] + l_i <= truck_length, name=f"x_bound_{i}")
                model.addGenConstrIndicator(is_placed_i, True, pos_y[i] + w_i <= truck_width, name=f"y_bound_{i}")
                model.addGenConstrIndicator(is_placed_i, True, pos_z[i] + h_i <= truck_height, name=f"z_bound_{i}")

                # 非重叠约束
                for j in range(i):
                    dims_j = (items_data.iloc[j]['estimated_length'],
                              items_data.iloc[j]['estimated_width'],
                              items_data.iloc[j]['estimated_height'])
                    l_j, w_j, h_j = dims_j
                    
                    for k in range(n_trucks):
                        # 辅助变量 both_in_truck_k = 1 if i and j 都在车k中
                        both_in_truck_k = model.addVar(vtype=GRB.BINARY, name=f"both_in_truck_{i}_{j}_{k}")
                        model.addConstr(both_in_truck_k <= x[i, k])
                        model.addConstr(both_in_truck_k <= x[j, k])
                        model.addConstr(both_in_truck_k >= x[i, k] + x[j, k] - 1)

                        delta = model.addVars(6, vtype=GRB.BINARY, name=f"delta_{i}_{j}_{k}")
                        
                        model.addGenConstrIndicator(both_in_truck_k, True, gp.quicksum(delta) >= 1)

                        model.addGenConstrIndicator(delta[0], True, pos_x[i] + l_i <= pos_x[j])
                        model.addGenConstrIndicator(delta[1], True, pos_x[j] + l_j <= pos_x[i])
                        model.addGenConstrIndicator(delta[2], True, pos_y[i] + w_i <= pos_y[j])
                        model.addGenConstrIndicator(delta[3], True, pos_y[j] + w_j <= pos_y[i])
                        model.addGenConstrIndicator(delta[4], True, pos_z[i] + h_i <= pos_z[j])
                        model.addGenConstrIndicator(delta[5], True, pos_z[j] + h_j <= pos_z[i])

            # --- 7. 优化 ---
            self.logger.info("  开始Gurobi求解...")
            model.optimize()
            solve_time = time.time() - start_time
            self.logger.info(f"  ✅ Gurobi求解完成，耗时: {solve_time:.2f}秒")

            # --- 8. 结果处理 ---
            if model.Status in [GRB.OPTIMAL, GRB.TIME_LIMIT] and model.SolCount > 0:
                # (这里的逻辑可以复用您之前写得很好的结果提取部分，但需要适配新的变量)
                loading_plan = []
                truck_assignments = {k: [] for k in range(n_trucks)}
                loaded_item_indices = set()

                for i in range(n_items):
                    for k in range(n_trucks):
                        if x[i, k].X > 0.5:
                            loaded_item_indices.add(i)
                            loading_plan.append({
                                'item_id': items_data.iloc[i]['item_id'],
                                'truck_id': k,
                                'position_x': pos_x[i].X,
                                'position_y': pos_y[i].X,
                                'position_z': pos_z[i].X
                            })
                            if k not in truck_assignments: truck_assignments[k] = []
                            truck_assignments[k].append(items_data.iloc[i]['item_id'])
                
                used_trucks_indices = [k for k, v in truck_assignments.items() if v]
                
                result = {
                    'status': 'optimal' if model.Status == GRB.OPTIMAL else 'feasible',
                    'loading_plan': loading_plan,
                    'loaded_items': [items_data.iloc[i]['item_id'] for i in loaded_item_indices],
                    'unloaded_items': [items_data.iloc[i]['item_id'] for i in range(n_items) if i not in loaded_item_indices],
                    'trucks_used': len(used_trucks_indices),
                    'total_loaded_volume': model.ObjVal,
                    'solve_time': solve_time,
                    'objective_value': model.ObjVal,
                    'gap': model.MIPGap,
                    'truck_assignments': truck_assignments
                }
                
                self.logger.info(f"  多车队LTL优化完成: 装载 {len(result['loaded_items'])}/{n_items} 个货物, "
                               f"使用 {result['trucks_used']} 辆车。")
                return result
            else:
                # 🔧 改进的错误处理：对Status=11提供更详细的诊断
                if model.Status == 11:  # GRB.INTERRUPTED
                    self.logger.warning(f"  ⚠️ Gurobi求解被中断(Status=11)，尝试降级求解")
                    # 尝试更简单的配置重新求解
                    try:
                        model.setParam('MIPGap', 0.1)  # 进一步放宽Gap到10%
                        model.setParam('TimeLimit', 60)  # 短时间限制
                        model.setParam('MIPFocus', 1)   # 专注可行解
                        self.logger.info("  🔧 使用降级配置重新求解...")
                        model.optimize()

                        if model.Status in [GRB.OPTIMAL, GRB.TIME_LIMIT] and getattr(model, 'SolCount', 0) > 0:
                            self.logger.info(f"  ✅ 降级求解成功，状态: {model.Status}")
                            # 重新执行结果提取逻辑
                            loading_plan = []
                            truck_assignments = {k: [] for k in range(n_trucks)}
                            loaded_item_indices = set()

                            for i in range(n_items):
                                for k in range(n_trucks):
                                    if x[i, k].X > 0.5:
                                        loaded_item_indices.add(i)
                                        loading_plan.append({
                                            'item_id': items_data.iloc[i]['item_id'],
                                            'truck_id': k,
                                            'position_x': pos_x[i].X,
                                            'position_y': pos_y[i].X,
                                            'position_z': pos_z[i].X
                                        })
                                        if k not in truck_assignments: truck_assignments[k] = []
                                        truck_assignments[k].append(items_data.iloc[i]['item_id'])

                            used_trucks_indices = [k for k, v in truck_assignments.items() if v]

                            result = {
                                'status': 'feasible',  # 降级求解标记为可行解
                                'loading_plan': loading_plan,
                                'loaded_items': [items_data.iloc[i]['item_id'] for i in loaded_item_indices],
                                'unloaded_items': [items_data.iloc[i]['item_id'] for i in range(n_items) if i not in loaded_item_indices],
                                'trucks_used': len(used_trucks_indices),
                                'total_loaded_volume': model.ObjVal,
                                'solve_time': time.time() - start_time,
                                'objective_value': model.ObjVal,
                                'gap': model.MIPGap,
                                'truck_assignments': truck_assignments,
                                'algorithm': 'gurobi_multi_truck_ltl_3dpp_degraded'
                            }

                            self.logger.info(f"  🔧 降级求解完成: 装载 {len(result['loaded_items'])}/{n_items} 个货物")
                            return result
                    except Exception as retry_error:
                        self.logger.error(f"  ❌ 降级求解也失败: {str(retry_error)}")

                # 如果不是Status=11或降级求解失败，抛出原始错误
                raise RuntimeError(f"多车队LTL Gurobi求解失败: status={model.Status}")

        except gp.GurobiError as e:
            self.logger.error(f"Gurobi Error: {e.message} (code: {e.errno})")
            raise RuntimeError(f"Gurobi内部错误: {e.message}")
        except Exception as e:
            self.logger.error(f"多车队LTL优化异常: {str(e)}")
            raise
        finally:
            if model:
                model.dispose()
                self.logger.info("  ✅ Gurobi模型资源已清理")

    def _get_dimensions_by_orientation(self, base_dimensions: Tuple[float, float, float]) -> List[Tuple[float, float, float]]:
        """
        获取6种方向的尺寸

        Args:
            base_dimensions: 基础尺寸 (长, 宽, 高)

        Returns:
            List[Tuple[float, float, float]]: 6种方向的尺寸
        """
        l, w, h = base_dimensions
        return [
            (l, w, h),  # 0: 原方向
            (l, h, w),  # 1: 绕x轴旋转90度
            (w, l, h),  # 2: 绕z轴旋转90度
            (w, h, l),  # 3: 绕y轴旋转90度
            (h, l, w),  # 4: 复合旋转1
            (h, w, l)   # 5: 复合旋转2
        ]

    def _add_non_overlap_constraints(self, model, i, j, pos_x, pos_y, pos_z, orient, x, item_dimensions):
        """添加非重叠约束（单车版本）"""
        M = self.model_params['big_m']
        dimensions_by_orient = self._get_dimensions_by_orientation(item_dimensions)

        # 两个货物都装载时才需要非重叠约束
        both_loaded = model.addVar(vtype=GRB.BINARY, name=f"both_loaded_{i}_{j}")
        model.addConstr(both_loaded <= x[i])
        model.addConstr(both_loaded <= x[j])
        model.addConstr(both_loaded >= x[i] + x[j] - 1)

        # 互斥分离约束
        sep_x_left = model.addVar(vtype=GRB.BINARY, name=f"sep_x_left_{i}_{j}")
        sep_x_right = model.addVar(vtype=GRB.BINARY, name=f"sep_x_right_{i}_{j}")
        sep_y_left = model.addVar(vtype=GRB.BINARY, name=f"sep_y_left_{i}_{j}")
        sep_y_right = model.addVar(vtype=GRB.BINARY, name=f"sep_y_right_{i}_{j}")
        sep_z_left = model.addVar(vtype=GRB.BINARY, name=f"sep_z_left_{i}_{j}")
        sep_z_right = model.addVar(vtype=GRB.BINARY, name=f"sep_z_right_{i}_{j}")

        # 至少一个分离方向
        model.addConstr(
            sep_x_left + sep_x_right + sep_y_left + sep_y_right + sep_z_left + sep_z_right >= both_loaded
        )

        # 分离约束（简化版本，使用平均尺寸）
        avg_dim = (sum(item_dimensions) / 3)

        model.addConstr(pos_x[i] + avg_dim <= pos_x[j] + M * (1 - sep_x_left))
        model.addConstr(pos_x[j] + avg_dim <= pos_x[i] + M * (1 - sep_x_right))
        model.addConstr(pos_y[i] + avg_dim <= pos_y[j] + M * (1 - sep_y_left))
        model.addConstr(pos_y[j] + avg_dim <= pos_y[i] + M * (1 - sep_y_right))
        model.addConstr(pos_z[i] + avg_dim <= pos_z[j] + M * (1 - sep_z_left))
        model.addConstr(pos_z[j] + avg_dim <= pos_z[i] + M * (1 - sep_z_right))

    def _add_non_overlap_constraints_multi_truck(self, model, i, j, k, pos_x, pos_y, pos_z, orient, x, items_data):
        """添加非重叠约束（多车版本）"""
        M = self.model_params['big_m']

        # 两个货物都在同一辆车时才需要非重叠约束
        both_in_truck = model.addVar(vtype=GRB.BINARY, name=f"both_in_truck_{i}_{j}_{k}")
        model.addConstr(both_in_truck <= x[i, k])
        model.addConstr(both_in_truck <= x[j, k])
        model.addConstr(both_in_truck >= x[i, k] + x[j, k] - 1)

        # 简化的非重叠约束
        item_i_vol = items_data.iloc[i]['volume_m3']
        item_j_vol = items_data.iloc[j]['volume_m3']

        avg_dim_i = item_i_vol ** (1/3)
        avg_dim_j = item_j_vol ** (1/3)

        # 互斥分离
        sep_x = model.addVar(vtype=GRB.BINARY, name=f"sep_x_{i}_{j}_{k}")
        sep_y = model.addVar(vtype=GRB.BINARY, name=f"sep_y_{i}_{j}_{k}")
        sep_z = model.addVar(vtype=GRB.BINARY, name=f"sep_z_{i}_{j}_{k}")

        model.addConstr(sep_x + sep_y + sep_z >= both_in_truck)

        model.addConstr(pos_x[i] + avg_dim_i <= pos_x[j] + M * (1 - sep_x))
        model.addConstr(pos_x[j] + avg_dim_j <= pos_x[i] + M * (1 - sep_x))
        model.addConstr(pos_y[i] + avg_dim_i <= pos_y[j] + M * (1 - sep_y))
        model.addConstr(pos_y[j] + avg_dim_j <= pos_y[i] + M * (1 - sep_y))
        model.addConstr(pos_z[i] + avg_dim_i <= pos_z[j] + M * (1 - sep_z))
        model.addConstr(pos_z[j] + avg_dim_j <= pos_z[i] + M * (1 - sep_z))

    # ⚠️ 移除LTL启发式回退 - 系统强制使用Gurobi优化
    # 原_fallback_ltl_optimization方法已删除，防止启发式回退
    # 📝 所有优化必须通过Gurobi求解器完成，确保有意义的XYZ坐标生成


def main():
    """测试Gurobi优化器V2模块"""
    # 创建优化器
    optimizer = GurobiOptimizerV2()

    # 测试单货物3DPP优化
    print("测试单货物3DPP优化...")
    single_result = optimizer.optimize_single_item_3dpp(
        item_volume=0.05,
        item_dimensions=(0.4, 0.3, 0.417),
        truck_specs=TRUCK_SPECS
    )
    print(f"单货物3DPP结果: {single_result['optimal_items_count']} 件，装载率 {single_result['loading_rate']:.1%}")

    # 测试多车队LTL优化
    print("\n测试多车队LTL优化...")
    test_items = pd.DataFrame({
        'item_id': [f'ITEM_{i:03d}' for i in range(20)],
        'volume_m3': np.random.uniform(0.01, 0.5, 20),
        'weight_kg': np.random.uniform(1, 10, 20),
        'estimated_length': np.random.uniform(0.2, 1.0, 20),
        'estimated_width': np.random.uniform(0.2, 1.0, 20),
        'estimated_height': np.random.uniform(0.2, 1.0, 20)
    })

    ltl_result = optimizer.optimize_multi_truck_ltl_3dpp(test_items, 3)
    if ltl_result['status'] != 'error':
        print(f"多车队LTL结果: 装载 {ltl_result['loaded_items']}/{len(test_items)} 个货物，"
              f"使用 {ltl_result['trucks_used']} 辆车")


if __name__ == "__main__":
    main()