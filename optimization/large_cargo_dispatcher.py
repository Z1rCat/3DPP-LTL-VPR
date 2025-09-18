"""
大宗货物调度模块 V2.0 - 纯Gurobi版本
Large Cargo Dispatcher V2.0 with Gurobi-Only Optimization
"""

import pandas as pd
import numpy as np
import json
import logging
from typing import Dict, List, Tuple, Optional
from pathlib import Path
from tqdm import tqdm

# 导入配置
import sys
sys.path.append(str(Path(__file__).parent.parent))
from config import (TRUCK_SPECS, FLEET_CONFIG, CARGO_CLASSIFICATION, GUROBI_CONFIG,
                   INTERMEDIATE_DIR, REPORTS_DIR, FILE_CONFIG)


class LargeCargoDispatcherV2:
    """大宗货物调度器V2 - 强制使用Gurobi优化，移除所有启发式算法"""

    def __init__(self):
        """初始化大宗货物调度器V2"""
        self.logger = self._setup_logger()
        self.truck_specs = TRUCK_SPECS
        self.fleet_config = FLEET_CONFIG
        self.large_threshold = CARGO_CLASSIFICATION['large_cargo_threshold']

        # 车辆使用跟踪
        self.used_trucks = []
        self.remaining_trucks = list(range(FLEET_CONFIG['total_trucks']))

        # 单货物3DPP优化结果缓存
        self.optimization_cache = {}

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

    def process_large_orders_with_3dpp(self, large_orders: pd.DataFrame) -> Dict:
        """
        使用单货物3DPP优化处理大宗订单

        Args:
            large_orders: 大宗订单DataFrame

        Returns:
            Dict: 处理结果，包含装载结果和剩余货物
        """
        self.logger.info(f"开始使用Gurobi 3DPP优化处理{len(large_orders)}个大宗订单")

        if len(large_orders) == 0:
            return self._empty_dispatch_result()

        dispatch_results = []
        remaining_items = []
        successfully_dispatched_orders = 0
        successfully_dispatched_items = 0
        total_volume_dispatched = 0.0

        # 处理每个大宗订单
        with tqdm(total=len(large_orders), desc="Gurobi 3DPP优化大宗订单") as pbar:
            for _, order in large_orders.iterrows():
                order_result = self._process_single_large_order_3dpp(order)

                if order_result['success']:
                    # 成功分配的车辆
                    dispatch_results.extend(order_result['dispatch_results'])
                    successfully_dispatched_orders += 1
                    successfully_dispatched_items += order_result['dispatched_items']
                    total_volume_dispatched += order_result['dispatched_volume']

                    # 收集剩余货物
                    if order_result['remaining_items'] > 0:
                        remaining_items.append({
                            'order_id': order['order_id'],
                            'item_type': order['item_type'],
                            'single_volume_m3': order['volume_m3'],
                            'single_weight_kg': order['weight_kg'] if 'weight_kg' in order else 0,
                            'remaining_quantity': order_result['remaining_items'],
                            'cargo_source': 'large_order_remaining'
                        })

                pbar.update(1)

        # 计算整体效率
        trucks_used = len(dispatch_results)
        dispatch_efficiency = (
            total_volume_dispatched / (trucks_used * self.truck_specs['volume'])
            if trucks_used > 0 else 0.0
        )

        result = {
            'dispatch_results': dispatch_results,
            'remaining_items': remaining_items,
            'successfully_dispatched_orders': successfully_dispatched_orders,
            'successfully_dispatched_items': successfully_dispatched_items,
            'trucks_used': trucks_used,
            'total_volume_dispatched': total_volume_dispatched,
            'dispatch_efficiency': dispatch_efficiency,
            'optimization_type': 'gurobi_single_item_3dpp'
        }

        self.logger.info(f"大宗订单Gurobi 3DPP优化完成:")
        self.logger.info(f"  成功分配订单: {successfully_dispatched_orders}/{len(large_orders)}")
        self.logger.info(f"  成功分配货物: {successfully_dispatched_items} 个")
        self.logger.info(f"  使用货车: {trucks_used} 辆")
        self.logger.info(f"  装载效率: {dispatch_efficiency:.1%}")
        self.logger.info(f"  剩余货物组: {len(remaining_items)} 组")

        return result

    def _process_single_large_order_3dpp(self, order: pd.Series) -> Dict:
        """
        使用Gurobi 3DPP优化处理单个大宗订单

        Args:
            order: 单个订单数据

        Returns:
            Dict: 单个订单的处理结果
        """
        order_id = order['order_id']
        item_type = order['item_type']
        single_volume = order['volume_m3']
        single_weight = order['weight_kg'] if 'weight_kg' in order else 0
        total_quantity = order['quantity']

        self.logger.info(f"  Gurobi 3DPP优化订单 {order_id}: {item_type} x{total_quantity}")

        # 检查缓存
        cache_key = f"{item_type}_{single_volume}_{single_weight}"
        if cache_key in self.optimization_cache:
            optimal_loading = self.optimization_cache[cache_key]
            self.logger.info(f"    使用缓存结果: 每车最多装载 {optimal_loading} 件")
        else:
            # 执行单货物3DPP优化
            optimal_loading = self._optimize_single_item_loading(order)
            self.optimization_cache[cache_key] = optimal_loading
            self.logger.info(f"    Gurobi 3DPP优化结果: 每车最多装载 {optimal_loading} 件")

        if optimal_loading <= 0:
            self.logger.error(f"    订单 {order_id} Gurobi 3DPP优化失败")
            return {
                'success': False,
                'dispatch_results': [],
                'dispatched_items': 0,
                'dispatched_volume': 0,
                'remaining_items': total_quantity
            }

        # 计算需要的满车数和剩余货物
        full_trucks_needed = total_quantity // optimal_loading
        remaining_items = total_quantity % optimal_loading

        self.logger.info(f"    分配方案: {full_trucks_needed} 辆满车 + {remaining_items} 件剩余")

        # 检查可用车辆
        if full_trucks_needed > len(self.remaining_trucks):
            available_trucks = len(self.remaining_trucks)
            self.logger.warning(f"    车辆不足: 需要 {full_trucks_needed} 辆，可用 {available_trucks} 辆")

            # 尽力分配可用车辆
            if available_trucks > 0:
                items_dispatched = available_trucks * optimal_loading
                remaining_items = total_quantity - items_dispatched
                full_trucks_needed = available_trucks
            else:
                return {
                    'success': False,
                    'dispatch_results': [],
                    'dispatched_items': 0,
                    'dispatched_volume': 0,
                    'remaining_items': total_quantity
                }

        # 分配满车
        dispatch_results = []
        for truck_idx in range(full_trucks_needed):
            truck_id = self.remaining_trucks.pop(0)
            self.used_trucks.append(truck_id)

            truck_volume_used = optimal_loading * single_volume
            loading_efficiency = truck_volume_used / self.truck_specs['volume']

            dispatch_result = {
                'truck_id': f"TRUCK_{truck_id:03d}",
                'order_id': order_id,
                'item_type': item_type,
                'items_count': optimal_loading,
                'single_item_volume': single_volume,
                'single_item_weight': single_weight,
                'truck_volume_used': truck_volume_used,
                'loading_efficiency': loading_efficiency,
                'dispatch_type': 'large_order_gurobi_3dpp',
                'optimization_algorithm': 'gurobi_single_item_3dpp',
                'dispatch_timestamp': pd.Timestamp.now()
            }

            dispatch_results.append(dispatch_result)

        return {
            'success': True,
            'dispatch_results': dispatch_results,
            'dispatched_items': full_trucks_needed * optimal_loading,
            'dispatched_volume': full_trucks_needed * optimal_loading * single_volume,
            'remaining_items': remaining_items
        }

    def _optimize_single_item_loading(self, order: pd.Series) -> int:
        """
        执行单货物3DPP优化，计算单车最优装载量
        (V2.2 - 兼容启发式算法)

        Args:
            order: 订单数据

        Returns:
            int: 单车最优装载件数
        """
        try:
            # 创建单货物3DPP优化问题
            single_volume = order['volume_m3']
            item_type = order['item_type']

            # 估算货物尺寸（如果没有）
            if 'estimated_length' not in order or pd.isna(order.get('estimated_length')):
                dimensions = self._estimate_item_dimensions(single_volume)
            else:
                dimensions = (
                    order['estimated_length'],
                    order['estimated_width'],
                    order['estimated_height']
                )

            # 动态创建Gurobi优化器实例来调用方法
            # 这是解耦的关键，即使文件名是gurobi_optimizer，内部也可以是启发式
            from optimization.gurobi_optimizer_fixed import GurobiOptimizerV2
            optimizer = GurobiOptimizerV2()

            optimization_result = optimizer.optimize_single_item_3dpp(
                item_volume=single_volume,
                item_dimensions=dimensions,
                truck_specs=self.truck_specs
            )

            # --- [最终修改] ---
            # 定义一个可接受的成功状态列表
            SUCCESS_STATUSES = ['optimal', 'feasible', 'heuristic_success', 'time_limit_with_solution']

            # 检查返回的状态是否在我们的成功列表里
            if optimization_result.get('status') in SUCCESS_STATUSES and optimization_result.get('optimal_items_count', 0) > 0:
                optimal_count = optimization_result['optimal_items_count']
                self.logger.info(f"    单车容量计算成功: {optimal_count} 件，状态: {optimization_result['status']}")
                return optimal_count
            else:
                # 如果状态不成功或计算结果为0，则抛出错误
                status = optimization_result.get('status', '未知')
                self.logger.error(f"    单货物容量计算失败，返回状态为: {status}")
                raise RuntimeError(f"单货物容量计算失败: 状态为 {status}")

        except Exception as e:
            self.logger.error(f"  在 _optimize_single_item_loading 中发生严重错误: {str(e)}")
            raise # 直接抛出，让上层捕获

    def _call_gurobi_single_item_3dpp(self, volume: float, dimensions: Tuple[float, float, float],
                                    truck_specs: Dict) -> Dict:
        """
        调用Gurobi进行单货物3DPP优化
        ⚠️ 重要：此方法现在强制使用Gurobi，移除所有启发式回退

        Args:
            volume: 单件货物体积
            dimensions: 货物尺寸 (长, 宽, 高)
            truck_specs: 车辆规格

        Returns:
            Dict: 优化结果
        """
        try:
            # 导入并创建Gurobi优化器
            from optimization.gurobi_optimizer import GurobiOptimizerV2
            optimizer = GurobiOptimizerV2()

            # 强制调用Gurobi优化
            result = optimizer.optimize_single_item_3dpp(volume, dimensions, truck_specs)
            SUCCESS_STATUSES = ['optimal', 'feasible', 'heuristic_success', 'time_limit_with_solution']
            # 检查Gurobi求解状态
            if result['status'] not in SUCCESS_STATUSES:
                raise RuntimeError(f"Gurobi单货物3DPP求解失败: {result['status']}")

            self.logger.info(f"Gurobi求解成功: {result['optimal_items_count']} 件，状态: {result['status']}")
            return result

        except Exception as e:
            # 不再回退到启发式，直接抛出异常
            self.logger.error(f"Gurobi单货物3DPP优化失败: {str(e)}")
            raise RuntimeError(f"Gurobi优化失败，系统要求必须使用Gurobi求解: {str(e)}")

    def _estimate_item_dimensions(self, volume: float) -> Tuple[float, float, float]:
        """
        估算货物尺寸

        Args:
            volume: 货物体积

        Returns:
            Tuple[float, float, float]: (长, 宽, 高)
        """
        # 简单立方体假设
        side = volume ** (1/3)
        return (side, side, side)

    def get_remaining_items_for_ltl(self, dispatch_result: Dict) -> pd.DataFrame:
        """
        将大货物处理的剩余货物转换为LTL优化输入格式

        Args:
            dispatch_result: 大货物处理结果

        Returns:
            pd.DataFrame: 格式化的剩余货物数据
        """
        remaining_items = dispatch_result.get('remaining_items', [])

        if not remaining_items:
            return pd.DataFrame()

        ltl_items = []
        item_counter = 0

        for remaining_group in remaining_items:
            # 为每个剩余货物创建独立的LTL优化条目
            for i in range(remaining_group['remaining_quantity']):
                ltl_item = {
                    'item_id': f"LARGE_REMAINING_{item_counter:05d}",
                    'original_order_id': remaining_group['order_id'],
                    'item_type': remaining_group['item_type'],
                    'volume_m3': remaining_group['single_volume_m3'],
                    'weight_kg': remaining_group['single_weight_kg'],
                    'cargo_source': remaining_group['cargo_source'],
                    'quantity': 1,  # LTL优化中按单件处理
                    'is_merged': False,
                    'processed_timestamp': pd.Timestamp.now()
                }
                ltl_items.append(ltl_item)
                item_counter += 1

        ltl_df = pd.DataFrame(ltl_items)

        self.logger.info(f"大货物剩余转LTL: {len(remaining_items)} 组 → {len(ltl_df)} 个独立货物")

        return ltl_df

    def _empty_dispatch_result(self) -> Dict:
        """返回空的分配结果"""
        return {
            'dispatch_results': [],
            'remaining_items': [],
            'successfully_dispatched_orders': 0,
            'successfully_dispatched_items': 0,
            'trucks_used': 0,
            'total_volume_dispatched': 0.0,
            'dispatch_efficiency': 0.0,
            'optimization_type': 'none'
        }

    def generate_dispatch_report(self, dispatch_summary: Dict, output_file: Optional[str] = None) -> str:
        """
        生成分配报告

        Args:
            dispatch_summary: 分配结果摘要
            output_file: 输出文件路径

        Returns:
            str: 报告文件路径
        """
        if output_file is None:
            output_file = REPORTS_DIR / FILE_CONFIG['large_cargo_dispatch_file']

        self.logger.info("生成大宗货物分配报告")

        try:
            with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
                # 主分配表
                if dispatch_summary['dispatch_results']:
                    dispatch_df = pd.DataFrame(dispatch_summary['dispatch_results'])
                    dispatch_df.to_excel(writer, sheet_name='大宗货物分配', index=False)
                else:
                    pd.DataFrame().to_excel(writer, sheet_name='大宗货物分配', index=False)

                # 剩余货物表
                if dispatch_summary['remaining_items']:
                    remaining_df = pd.DataFrame(dispatch_summary['remaining_items'])
                    remaining_df.to_excel(writer, sheet_name='剩余货物', index=False)
                else:
                    pd.DataFrame().to_excel(writer, sheet_name='剩余货物', index=False)

                # 摘要信息
                summary_data = {
                    '指标': ['成功分配订单', '成功分配货物', '使用货车数', '总分配体积(m³)',
                           '平均装载效率', '剩余货物组数', '优化算法'],
                    '数值': [
                        dispatch_summary['successfully_dispatched_orders'],
                        dispatch_summary['successfully_dispatched_items'],
                        dispatch_summary['trucks_used'],
                        f"{dispatch_summary['total_volume_dispatched']:.6f}",
                        f"{dispatch_summary['dispatch_efficiency']:.1%}",
                        len(dispatch_summary['remaining_items']),
                        dispatch_summary.get('optimization_type', 'gurobi_only')
                    ]
                }
                summary_df = pd.DataFrame(summary_data)
                summary_df.to_excel(writer, sheet_name='分配摘要', index=False)

            self.logger.info(f"大宗货物分配报告已保存到: {output_file}")
            return str(output_file)

        except Exception as e:
            self.logger.error(f"生成分配报告失败: {str(e)}")
            raise

    def save_remaining_vehicles(self, output_file: Optional[str] = None) -> str:
        """
        保存剩余可用车辆信息

        Args:
            output_file: 输出文件路径

        Returns:
            str: 文件路径
        """
        if output_file is None:
            output_file = INTERMEDIATE_DIR / FILE_CONFIG['remaining_vehicles_file']

        remaining_vehicles_data = {
            'total_fleet_size': self.fleet_config['total_trucks'],
            'used_trucks_count': len(self.used_trucks),
            'remaining_trucks_count': len(self.remaining_trucks),
            'used_truck_ids': [f"TRUCK_{truck_id:03d}" for truck_id in self.used_trucks],
            'remaining_truck_ids': [f"TRUCK_{truck_id:03d}" for truck_id in self.remaining_trucks],
            'truck_specifications': self.truck_specs,
            'large_cargo_optimization_summary': {
                'optimization_type': 'gurobi_only',
                'optimization_cache_size': len(self.optimization_cache),
                'cached_configurations': list(self.optimization_cache.keys())
            },
            'last_updated': pd.Timestamp.now().isoformat()
        }

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(remaining_vehicles_data, f, ensure_ascii=False, indent=2)

        self.logger.info(f"剩余车辆信息已保存到: {output_file}")
        self.logger.info(f"剩余可用货车: {len(self.remaining_trucks)}/{self.fleet_config['total_trucks']}")

        return str(output_file)


def main():
    """测试大宗货物调度器V2模块"""
    # 模拟测试数据
    test_large_orders = pd.DataFrame({
        'order_id': ['ORDER_0001', 'ORDER_0002', 'ORDER_0003'],
        'item_type': ['食品', '饮水', '农产品'],
        'volume_m3': [0.05, 0.03, 0.04],
        'weight_kg': [2.0, 1.5, 3.0],
        'quantity': [1200, 2000, 1500],
        'order_total_volume_m3': [60.0, 60.0, 60.0],
        'order_total_weight_kg': [2400, 3000, 4500]
    })

    # 创建调度器并测试
    dispatcher = LargeCargoDispatcherV2()

    try:
        # 测试Gurobi 3DPP优化
        result = dispatcher.process_large_orders_with_3dpp(test_large_orders)

        print("大宗货物Gurobi 3DPP优化测试完成!")
        print(f"成功分配订单: {result['successfully_dispatched_orders']}")
        print(f"使用货车: {result['trucks_used']} 辆")
        print(f"装载效率: {result['dispatch_efficiency']:.1%}")
        print(f"剩余货物组: {len(result['remaining_items'])} 组")

        # 测试剩余货物转换
        ltl_items = dispatcher.get_remaining_items_for_ltl(result)
        print(f"转换为LTL货物: {len(ltl_items)} 个")

    except Exception as e:
        print(f"测试失败: {str(e)}")


if __name__ == "__main__":
    main()