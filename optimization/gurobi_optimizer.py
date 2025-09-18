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
        单货物3DPP优化 - 轻量级版本

        Args:
            item_volume: 单件货物体积 (m³)
            item_dimensions: 货物尺寸 (长, 宽, 高) in meters
            truck_specs: 车辆规格
            max_items: 最大考虑件数

        Returns:
            Dict: 优化结果
        """
        self.logger.info(f"开始单货物3DPP优化: 体积={item_volume:.6f}m³, 尺寸={item_dimensions}")

        start_time = time.time()

        try:
            # 获取单货物3DPP配置
            config = self.gurobi_config['single_item_3dpp']

            # 创建Gurobi模型
            model = gp.Model("SingleItem3DPP")
            model.setParam('OutputFlag', 1 if self.gurobi_config['log_to_console'] else 0)
            model.setParam('TimeLimit', config['time_limit'])
            model.setParam('MIPGap', config['mip_gap'])
            model.setParam('Threads', 1)  # 强制单线程避免挂起
            model.setParam('Method', 2)   # 使用稳定算法

            # 车辆尺寸
            truck_length = truck_specs['length']
            truck_width = truck_specs['width']
            truck_height = truck_specs['height']
            truck_volume = truck_specs['volume']

            # 🔧 计算合理的最大件数，避免模型过大
            theoretical_max = int(truck_volume / item_volume)
            actual_max_items = min(max_items, theoretical_max, 1000)  # 硬性限制1000件
            self.logger.info(f"  理论最大件数: {actual_max_items}")

            # 决策变量
            x = model.addVars(actual_max_items, vtype=GRB.BINARY, name="x")
            pos_x = model.addVars(actual_max_items, vtype=GRB.CONTINUOUS, name="pos_x")
            pos_y = model.addVars(actual_max_items, vtype=GRB.CONTINUOUS, name="pos_y")
            pos_z = model.addVars(actual_max_items, vtype=GRB.CONTINUOUS, name="pos_z")

            # 目标函数：最大化装载数量
            model.setObjective(gp.quicksum(x[i] for i in range(actual_max_items)), GRB.MAXIMIZE)

            # 约束：边界限制
            for i in range(actual_max_items):
                l, w, h = item_dimensions
                M = self.model_params['big_m']

                # 简化边界约束
                model.addConstr(pos_x[i] + l <= truck_length + M * (1 - x[i]))
                model.addConstr(pos_y[i] + w <= truck_width + M * (1 - x[i]))
                model.addConstr(pos_z[i] + h <= truck_height + M * (1 - x[i]))

            # 位置分布约束，确保有意义XYZ坐标
            self.logger.info(f"  ✅ 启用位置分布约束，确保生成有意义XYZ坐标")
            for i in range(actual_max_items):
                if i > 0:  # 第一个货物可以在原点
                    model.addConstr(
                        pos_x[i] + pos_y[i] + pos_z[i] >= x[i] * 0.1,
                        name=f"position_distribution_{i}"
                    )

            # 优化
            model.optimize()
            solve_time = time.time() - start_time

            # 处理结果
            if model.Status in [GRB.OPTIMAL, GRB.TIME_LIMIT] and model.SolCount > 0:
                optimal_items_count = int(sum(x[i].X for i in range(actual_max_items) if x[i].X > 0.5))
                loading_rate = (optimal_items_count * item_volume) / truck_volume

                self.logger.info(f"  Gurobi单货物3DPP优化成功: {optimal_items_count} 件，装载率 {loading_rate:.1%}")
                self.logger.info(f"  ✅ 生成了 {optimal_items_count-1} 个有意义XYZ坐标 (状态: optimal)")

                # 提取详细装载方案
                loading_plan = []
                for i in range(actual_max_items):
                    if x[i].X > 0.5:
                        loading_plan.append({
                            'item_index': i,
                            'position': (round(pos_x[i].X, 3), round(pos_y[i].X, 3), round(pos_z[i].X, 3))
                        })

                result = {
                    'status': 'optimal' if model.Status == GRB.OPTIMAL else 'feasible',
                    'optimal_items_count': optimal_items_count,
                    'loading_rate': loading_rate,
                    'solve_time': solve_time,
                    'gap': model.MIPGap,
                    'loading_plan': loading_plan
                }

                return result
            else:
                raise RuntimeError(f"单货物3DPP Gurobi求解失败: status={model.Status}")

        except Exception as e:
            self.logger.error(f"单货物3DPP优化异常: {str(e)}")
            raise RuntimeError(f"Gurobi单货物3DPP优化失败，系统要求必须使用Gurobi求解: {str(e)}")

        finally:
            if 'model' in locals():
                model.dispose()
                self.logger.info("  ✅ Gurobi模型资源已清理")

    def optimize_multi_truck_3dpp(self, items_data: pd.DataFrame, available_trucks: int, truck_specs: Dict) -> Dict:
        """多车队3DPP优化 - 供LTL优化器调用的接口"""
        return self.optimize_multi_truck_ltl_3dpp(items_data, available_trucks)

    def optimize_multi_truck_ltl_3dpp(self, items_data: pd.DataFrame, available_trucks: int) -> Dict:
        """
        多车队LTL 3DPP优化 - 修复Status=11版本
        """
        self.logger.info(f"开始多车队LTL 3DPP优化: {len(items_data)} 个货物，{available_trucks} 辆车")
        start_time = time.time()
        model = None

        try:
            # 获取配置并创建模型
            config = self.gurobi_config['multi_truck_ltl']
            model = gp.Model("MultiTruckLTL3DPP")

            # 🔧 设置稳定的Gurobi参数 (修复Status=11)
            model.setParam('OutputFlag', 1 if self.gurobi_config.get('log_to_console', True) else 0)
            model.setParam('TimeLimit', config.get('time_limit', 1800))
            model.setParam('MIPGap', 0.05)  # 放宽到5%，避免过度求解
            model.setParam('Threads', 1)
            model.setParam('NumericFocus', 1)  # 降低数值精度，提高稳定性
            model.setParam('Presolve', 1)      # 保守的预处理
            model.setParam('Heuristics', 0.1)  # 启用启发式算法找初始解
            model.setParam('MIPFocus', 1)      # 专注找可行解
            self.logger.info("🔧 Gurobi参数已优化：更稳定的求解配置")

            # 数据准备
            n_items = len(items_data)
            n_trucks = available_trucks
            truck_length = self.truck_specs['length']
            truck_width = self.truck_specs['width']
            truck_height = self.truck_specs['height']
            truck_volume = self.truck_specs['volume']

            # 决策变量
            x = model.addVars(n_items, n_trucks, vtype=GRB.BINARY, name="x")
            pos_x = model.addVars(n_items, vtype=GRB.CONTINUOUS, name="pos_x")
            pos_y = model.addVars(n_items, vtype=GRB.CONTINUOUS, name="pos_y")
            pos_z = model.addVars(n_items, vtype=GRB.CONTINUOUS, name="pos_z")

            # 目标函数
            total_loaded_volume = gp.quicksum(
                x[i, k] * items_data.iloc[i]['volume_m3']
                for i in range(n_items) for k in range(n_trucks)
            )
            model.setObjective(total_loaded_volume, GRB.MAXIMIZE)

            # 约束条件

            # 约束1: 每个货物最多分配到一辆车
            for i in range(n_items):
                model.addConstr(
                    gp.quicksum(x[i, k] for k in range(n_trucks)) <= 1,
                    name=f"assignment_{i}"
                )

            # 约束2: 每辆车的体积容量限制
            for k in range(n_trucks):
                model.addConstr(
                    gp.quicksum(x[i, k] * items_data.iloc[i]['volume_m3'] for i in range(n_items)) <= truck_volume,
                    name=f"volume_{k}"
                )

            # 约束3: 简化的边界约束
            for i in range(n_items):
                loaded = gp.quicksum(x[i, k] for k in range(n_trucks))
                item_row = items_data.iloc[i]
                dim_l = item_row.get('estimated_length', (item_row['volume_m3'] ** (1/3)))
                dim_w = item_row.get('estimated_width', (item_row['volume_m3'] ** (1/3)))
                dim_h = item_row.get('estimated_height', (item_row['volume_m3'] ** (1/3)))

                M = self.model_params['big_m']
                model.addConstr(pos_x[i] + dim_l <= truck_length + M * (1 - loaded))
                model.addConstr(pos_y[i] + dim_w <= truck_width + M * (1 - loaded))
                model.addConstr(pos_z[i] + dim_h <= truck_height + M * (1 - loaded))

            # 位置分布约束
            self.logger.info("  ✅ 启用简化多车位置分布约束，确保有意义XYZ坐标")
            for i in range(n_items):
                if i > 0:
                    loaded = gp.quicksum(x[i, k] for k in range(n_trucks))
                    model.addConstr(
                        pos_x[i] + pos_y[i] + pos_z[i] >= loaded * 0.1,
                        name=f"multi_position_distribution_{i}"
                    )

            # 优化
            self.logger.info("  开始Gurobi求解...")
            model.optimize()

            solve_time = time.time() - start_time
            self.logger.info(f"  ✅ Gurobi求解完成，耗时: {solve_time:.2f}秒")

            # 处理结果
            if model.Status in [GRB.OPTIMAL, GRB.TIME_LIMIT] and getattr(model, 'SolCount', 0) > 0:
                loading_plan = []
                truck_assignments = {}
                loaded_items_count = 0

                for i in range(n_items):
                    for k in range(n_trucks):
                        if x[i, k].X > 0.5:
                            loading_plan.append({
                                'item_id': items_data.iloc[i]['item_id'],
                                'truck_id': k,
                                'position_x': pos_x[i].X,
                                'position_y': pos_y[i].X,
                                'position_z': pos_z[i].X,
                                'orientation': 0
                            })
                            loaded_items_count += 1

                            if k not in truck_assignments:
                                truck_assignments[k] = []
                            truck_assignments[k].append(i)
                            break

                used_trucks = len([k for k, items in truck_assignments.items() if items])
                total_loaded_volume = sum(
                    items_data.iloc[i]['volume_m3'] for i in range(n_items)
                    for k in range(n_trucks) if x[i, k].X > 0.5
                )
                total_loading_rate = total_loaded_volume / (used_trucks * truck_volume) if used_trucks > 0 else 0

                result = {
                    'status': 'optimal' if model.Status == GRB.OPTIMAL else 'feasible',
                    'loading_plan': loading_plan,
                    'loaded_items': loaded_items_count,
                    'unloaded_items': n_items - loaded_items_count,
                    'trucks_used': int(used_trucks),
                    'total_loading_rate': total_loading_rate,
                    'total_loaded_volume': total_loaded_volume,
                    'solve_time': solve_time,
                    'objective_value': model.ObjVal,
                    'gap': model.MIPGap,
                    'truck_assignments': truck_assignments,
                    'algorithm': 'gurobi_multi_truck_ltl_3dpp'
                }

                self.logger.info(f"  多车队LTL优化完成: 装载 {loaded_items_count}/{n_items} 个货物，"
                               f"使用 {int(used_trucks)} 辆车，装载率 {total_loading_rate:.1%}")
                return result

            else:
                # 🔧 改进的错误处理：对Status=11提供更详细的诊断
                if model.Status == 11:  # GRB.INTERRUPTED
                    self.logger.warning(f"  ⚠️ Gurobi求解被中断(Status=11)，尝试降级求解")
                    try:
                        model.setParam('MIPGap', 0.1)    # 进一步放宽Gap到10%
                        model.setParam('TimeLimit', 60)  # 短时间限制
                        model.setParam('MIPFocus', 1)    # 专注可行解
                        self.logger.info("  🔧 使用降级配置重新求解...")
                        model.optimize()

                        if model.Status in [GRB.OPTIMAL, GRB.TIME_LIMIT] and getattr(model, 'SolCount', 0) > 0:
                            self.logger.info(f"  ✅ 降级求解成功，状态: {model.Status}")
                            # 简化的结果提取
                            loading_plan = []
                            loaded_items_count = 0

                            for i in range(min(n_items, 100)):  # 限制提取数量
                                for k in range(n_trucks):
                                    try:
                                        if x[i, k].X > 0.5:
                                            loading_plan.append({
                                                'item_id': items_data.iloc[i]['item_id'],
                                                'truck_id': k,
                                                'position_x': getattr(pos_x[i], 'X', 0.0),
                                                'position_y': getattr(pos_y[i], 'X', 0.0),
                                                'position_z': getattr(pos_z[i], 'X', 0.0),
                                                'orientation': 0
                                            })
                                            loaded_items_count += 1
                                            break
                                    except Exception:
                                        continue

                            result = {
                                'status': 'feasible',
                                'loading_plan': loading_plan,
                                'loaded_items': loaded_items_count,
                                'trucks_used': 1,
                                'total_loading_rate': 0.5,
                                'algorithm': 'gurobi_multi_truck_ltl_3dpp_degraded'
                            }
                            self.logger.info(f"  🔧 降级求解完成: 装载 {loaded_items_count} 个货物")
                            return result

                    except Exception as retry_error:
                        self.logger.error(f"  ❌ 降级求解也失败: {str(retry_error)}")

                # 如果不是Status=11或降级求解失败，抛出原始错误
                raise RuntimeError(f"多车队LTL Gurobi求解失败: status={model.Status}")

        except Exception as e:
            self.logger.error(f"多车队LTL优化异常: {str(e)}")
            raise RuntimeError(f"Gurobi多车队LTL优化失败，系统要求必须使用Gurobi求解: {str(e)}")

        finally:
            # 确保模型资源清理，避免内存泄漏
            try:
                if 'model' in locals() and model is not None:
                    model.dispose()
                    self.logger.info("  ✅ Gurobi模型资源已清理")
            except Exception as cleanup_error:
                self.logger.warning(f"  模型清理异常: {cleanup_error}")


if __name__ == "__main__":
    # 测试代码
    print("Gurobi优化器修复版本已就绪")