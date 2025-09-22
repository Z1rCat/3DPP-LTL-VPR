"""
零担优化器模块
LTL (Less Than Truckload) Optimizer Module for Multi-Truck Mixed Cargo 3D Bin Packing
"""

import pandas as pd
import numpy as np
import logging
from typing import Dict, List, Tuple, Optional
from pathlib import Path
from tqdm import tqdm

# 导入配置
import sys
sys.path.append(str(Path(__file__).parent.parent))
from config import (TRUCK_SPECS, LTL_OPTIMIZATION, GUROBI_CONFIG,
                   INTERMEDIATE_DIR, REPORTS_DIR, FILE_CONFIG)


class LTLOptimizer:
    """零担优化器 - 多车队混合货物3D装箱优化"""

    def __init__(self):
        """初始化零担优化器"""
        self.logger = self._setup_logger()
        self.truck_specs = TRUCK_SPECS
        self.max_trucks = LTL_OPTIMIZATION['max_trucks_available']
        self.objective = LTL_OPTIMIZATION['objective']

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

    def prepare_optimization_data(self, large_remaining: pd.DataFrame,
                                medium_orders: pd.DataFrame,
                                merged_small: pd.DataFrame) -> pd.DataFrame:
        """
        准备最终优化数据

        Args:
            large_remaining: 大货物剩余货物
            medium_orders: 中货物订单
            merged_small: 合并后的小货物

        Returns:
            pd.DataFrame: 统一格式的优化数据
        """
        self.logger.info("准备LTL优化数据")

        optimization_items = []
        item_counter = 0

        # 处理大货物剩余
        if len(large_remaining) > 0:
            self.logger.info(f"  处理大货物剩余: {len(large_remaining)} 个")
            for _, item in large_remaining.iterrows():
                opt_item = self._format_optimization_item(item, item_counter, 'large_remaining')
                optimization_items.append(opt_item)
                item_counter += 1

        # 处理中货物（展开为单件）
        if len(medium_orders) > 0:
            self.logger.info(f"  处理中货物订单: {len(medium_orders)} 个")
            for _, order in medium_orders.iterrows():
                # 中货物按件数展开
                for i in range(order['quantity']):
                    opt_item = {
                        'item_id': f"LTL_{item_counter:05d}",
                        'original_order_id': order['order_id'],
                        'item_type': order['item_type'],
                        'volume_m3': order['volume_m3'],
                        'weight_kg': order['weight_kg'] if 'weight_kg' in order else 0,
                        'estimated_length': order.get('estimated_length', self._estimate_dimension(order['volume_m3'])[0]),
                        'estimated_width': order.get('estimated_width', self._estimate_dimension(order['volume_m3'])[1]),
                        'estimated_height': order.get('estimated_height', self._estimate_dimension(order['volume_m3'])[2]),
                        'cargo_source': 'medium_order',
                        'is_merged': False,
                        'original_quantity': 1,
                        'density': order['weight_kg'] / order['volume_m3'] if 'weight_kg' in order and order['volume_m3'] > 0 else 1000
                    }
                    optimization_items.append(opt_item)
                    item_counter += 1

        # 处理合并后的小货物
        if len(merged_small) > 0:
            self.logger.info(f"  处理合并小货物: {len(merged_small)} 个")
            for _, merged in merged_small.iterrows():
                opt_item = self._format_optimization_item(merged, item_counter, 'small_merged')
                optimization_items.append(opt_item)
                item_counter += 1

        # 转换为DataFrame
        optimization_df = pd.DataFrame(optimization_items)

        if len(optimization_df) > 0:
            # 添加优化所需的额外字段
            optimization_df['loaded'] = False
            optimization_df['truck_assignment'] = -1
            optimization_df['position_x'] = 0.0
            optimization_df['position_y'] = 0.0
            optimization_df['position_z'] = 0.0
            optimization_df['orientation'] = 0

            # 按体积降序排列（大件优先策略）
            optimization_df = optimization_df.sort_values('volume_m3', ascending=False).reset_index(drop=True)

        self.logger.info(f"LTL优化数据准备完成: {len(optimization_df)} 个货物项目")
        self.logger.info(f"  总体积: {optimization_df['volume_m3'].sum():.6f} m³")
        self.logger.info(f"  货物来源分布: {optimization_df['cargo_source'].value_counts().to_dict()}")

        return optimization_df

    def _format_optimization_item(self, item: pd.Series, item_id: int, source: str) -> Dict:
        """格式化优化项目"""
        return {
            'item_id': f"LTL_{item_id:05d}",
            'original_order_id': item.get('original_order_id', item.get('order_id', 'unknown')),
            'item_type': item['item_type'],
            'volume_m3': item['volume_m3'],
            'weight_kg': item.get('weight_kg', 0),
            'estimated_length': item.get('estimated_length', self._estimate_dimension(item['volume_m3'])[0]),
            'estimated_width': item.get('estimated_width', self._estimate_dimension(item['volume_m3'])[1]),
            'estimated_height': item.get('estimated_height', self._estimate_dimension(item['volume_m3'])[2]),
            'cargo_source': source,
            'is_merged': item.get('is_merged', False),
            'original_quantity': item.get('original_quantity', 1),
            'density': item.get('density', 1000)
        }

    def _estimate_dimension(self, volume: float) -> Tuple[float, float, float]:
        """估算尺寸"""
        side = volume ** (1/3)
        return (side, side, side)

    def export_pre_optimization_data(self, optimization_data: pd.DataFrame) -> str:
        """
        导出优化前数据到Excel确认

        Args:
            optimization_data: 优化数据

        Returns:
            str: 输出文件路径
        """
        output_file = REPORTS_DIR / FILE_CONFIG['ltl_optimization_input_file']

        self.logger.info("导出LTL优化前数据到Excel")

        try:
            with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
                # 货物清单
                optimization_data.to_excel(writer, sheet_name='货物清单', index=False)

                # 车队信息
                vehicle_info = {
                    '指标': ['总车队数量', '可用车辆数', '单车长度(m)', '单车宽度(m)',
                           '单车高度(m)', '单车体积(m³)', '最大载重(kg)'],
                    '数值': [
                        self.max_trucks,
                        self.max_trucks,  # 这里应该是扣除大货物后的剩余数量
                        self.truck_specs['length'],
                        self.truck_specs['width'],
                        self.truck_specs['height'],
                        self.truck_specs['volume'],
                        self.truck_specs.get('max_weight', 0)
                    ]
                }
                vehicle_df = pd.DataFrame(vehicle_info)
                vehicle_df.to_excel(writer, sheet_name='车队信息', index=False)

                # 分类统计
                source_stats = optimization_data.groupby('cargo_source').agg({
                    'item_id': 'count',
                    'volume_m3': ['sum', 'mean'],
                    'weight_kg': ['sum', 'mean']
                }).round(6)

                source_stats.columns = ['货物数量', '总体积(m³)', '平均体积(m³)', '总重量(kg)', '平均重量(kg)']
                source_stats.to_excel(writer, sheet_name='分类统计')

                # 货物类型统计
                type_stats = optimization_data.groupby('item_type').agg({
                    'item_id': 'count',
                    'volume_m3': ['sum', 'mean']
                }).round(6)
                type_stats.columns = ['货物数量', '总体积(m³)', '平均体积(m³)']
                type_stats.to_excel(writer, sheet_name='货物类型统计')

            self.logger.info(f"LTL优化前数据已导出: {output_file}")
            return str(output_file)

        except Exception as e:
            self.logger.error(f"导出优化前数据失败: {str(e)}")
            raise

    def optimize_ltl_multi_truck(self, optimization_data: pd.DataFrame, available_trucks: int) -> Dict:
        """
        执行多车队LTL 3DPP优化

        Args:
            optimization_data: 优化数据
            available_trucks: 可用车辆数

        Returns:
            Dict: 优化结果
        """
        self.logger.info(f"开始多车队LTL 3DPP优化: {len(optimization_data)} 个货物，{available_trucks} 辆可用车")

        if len(optimization_data) == 0:
            return self._empty_optimization_result()

        if available_trucks <= 0:
            self.logger.error("没有可用车辆进行LTL优化")
            return self._empty_optimization_result()

        try:
            # 调用Gurobi多车队3DPP优化
            optimization_result = self._call_gurobi_multi_truck_3dpp(optimization_data, available_trucks)

            if optimization_result['status'] == 'optimal' or optimization_result['status'] == 'feasible':
                # 处理优化结果
                processed_result = self._process_optimization_result(optimization_result, optimization_data)

                self.logger.info(f"LTL优化完成:")
                self.logger.info(f"  装载货物: {processed_result['loaded_items']}/{len(optimization_data)}")
                self.logger.info(f"  使用车辆: {processed_result['trucks_used']}/{available_trucks}")
                self.logger.info(f"  总装载率: {processed_result['total_loading_rate']:.1%}")
                self.logger.info(f"  未装载货物: {processed_result['unloaded_items']} 个")

                return processed_result

            else:
                # 不再回退，直接抛出异常
                raise RuntimeError(f"Gurobi LTL优化失败: {optimization_result['status']}")

        except Exception as e:
            self.logger.error(f"LTL优化异常: {str(e)}")
            # 完全移除启发式回退
            raise RuntimeError(f"Gurobi LTL优化失败，系统要求必须使用Gurobi求解: {str(e)}")

    def _call_gurobi_multi_truck_3dpp(self, optimization_data: pd.DataFrame, available_trucks: int) -> Dict:
        """
        调用Gurobi进行多车队3DPP优化
        ⚠️ 强制使用Gurobi，移除所有启发式回退

        Args:
            optimization_data: 优化数据
            available_trucks: 可用车辆数

        Returns:
            Dict: Gurobi优化结果
        """
        self.logger.info("强制调用Gurobi多车队3DPP优化器")

        try:
            # 导入并创建Gurobi优化器V2
            from optimization.gurobi_optimizer import GurobiOptimizerV2
            optimizer = GurobiOptimizerV2()

            # 强制调用Gurobi多车队3DPP优化
            result = optimizer.optimize_multi_truck_3dpp(optimization_data, available_trucks, self.truck_specs)

            # 检查Gurobi求解状态
            if result['status'] not in ['optimal', 'feasible']:
                raise RuntimeError(f"Gurobi多车队3DPP求解失败: {result['status']}")

            self.logger.info(f"Gurobi多车队求解成功: {result['loaded_items']} 件装载，状态: {result['status']}")
            return result

        except Exception as e:
            # 不再回退到启发式，直接抛出异常
            self.logger.error(f"Gurobi多车队3DPP优化失败: {str(e)}")
            raise RuntimeError(f"Gurobi优化失败，系统要求必须使用Gurobi求解: {str(e)}")

    # ⚠️ 移除启发式算法 - 系统强制使用Gurobi优化
    # 原_simulate_gurobi_optimization方法已删除，防止启发式回退

    def _process_optimization_result(self, optimization_result: Dict, optimization_data: pd.DataFrame) -> Dict:
        """
        处理优化结果

        Args:
            optimization_result: Gurobi优化结果
            optimization_data: 原始优化数据

        Returns:
            Dict: 处理后的结果
        """
        loaded_items = optimization_result['loaded_items']
        unloaded_items = optimization_result['unloaded_items']
        trucks_used = optimization_result['trucks_used']

        # 创建装载方案DataFrame - 修复构造错误
        if loaded_items:
            # 🔧 确保loaded_items是列表格式，修复DataFrame构造错误
            if isinstance(loaded_items, list) and len(loaded_items) > 0:
                loading_plan = pd.DataFrame(loaded_items)
            elif isinstance(loaded_items, int):
                # 如果loaded_items是数字，说明需要从loading_plan获取数据
                loading_plan = pd.DataFrame(optimization_result.get('loading_plan', []))
            else:
                loading_plan = pd.DataFrame()
            # 合并原始数据信息
            loading_plan = loading_plan.merge(
                optimization_data[['item_id', 'original_order_id', 'item_type', 'volume_m3', 'weight_kg', 'cargo_source']],
                on='item_id',
                how='left'
            )
        else:
            loading_plan = pd.DataFrame()

        # 创建未装载货物DataFrame - 修复isin()错误
        if unloaded_items:
            # 🔧 确保unloaded_items是列表格式，修复isin()错误
            if isinstance(unloaded_items, int):
                # 如果是数字，表示未装载的数量，需要计算哪些未装载
                loaded_item_ids = set()
                if 'loading_plan' in optimization_result and optimization_result['loading_plan']:
                    loaded_item_ids = {item['item_id'] for item in optimization_result['loading_plan']}
                unloaded_df = optimization_data[~optimization_data['item_id'].isin(loaded_item_ids)].copy()
            elif isinstance(unloaded_items, list):
                unloaded_df = optimization_data[optimization_data['item_id'].isin(unloaded_items)].copy()
            else:
                unloaded_df = pd.DataFrame()
        else:
            unloaded_df = pd.DataFrame()

        # 计算统计信息
        total_items = len(optimization_data)

        # 🔧 修复loaded_items类型检查错误
        if isinstance(loaded_items, int):
            loaded_count = loaded_items
            # 从loading_plan获取装载的item_ids来计算体积
            if 'loading_plan' in optimization_result and optimization_result['loading_plan']:
                loaded_item_ids = {item['item_id'] for item in optimization_result['loading_plan']}
                loaded_volume = optimization_data[optimization_data['item_id'].isin(loaded_item_ids)]['volume_m3'].sum()
            else:
                loaded_volume = 0
        elif isinstance(loaded_items, list):
            loaded_count = len(loaded_items)
            loaded_volume = optimization_data[optimization_data['item_id'].isin([item['item_id'] for item in loaded_items])]['volume_m3'].sum() if loaded_items else 0
        else:
            loaded_count = 0
            loaded_volume = 0

        total_volume = optimization_data['volume_m3'].sum()

        # 🔧 修复unloaded_items类型检查错误
        if isinstance(unloaded_items, int):
            unloaded_count = unloaded_items
        elif isinstance(unloaded_items, list):
            unloaded_count = len(unloaded_items)
        else:
            unloaded_count = 0

        return {
            'status': 'success',
            'loading_plan': loading_plan,
            'unloaded_items_df': unloaded_df,
            'loaded_items': loaded_count,
            'unloaded_items': unloaded_count,
            'trucks_used': trucks_used,
            'total_loading_rate': optimization_result['total_loading_rate'],
            'volume_utilization': loaded_volume / total_volume if total_volume > 0 else 0,
            'truck_details': optimization_result.get('truck_details', []),
            'optimization_algorithm': optimization_result.get('algorithm', 'unknown'),
            'optimization_time': optimization_result.get('solve_time', 0),
            'objective_value': optimization_result.get('objective_value', 0)
        }

    # ⚠️ 移除启发式回退 - 系统强制使用Gurobi优化
    # 原_fallback_heuristic_optimization方法已删除，防止启发式回退

    def _empty_optimization_result(self) -> Dict:
        """返回空的优化结果"""
        return {
            'status': 'empty',
            'loading_plan': pd.DataFrame(),
            'unloaded_items_df': pd.DataFrame(),
            'loaded_items': 0,
            'unloaded_items': 0,
            'trucks_used': 0,
            'total_loading_rate': 0.0,
            'volume_utilization': 0.0,
            'truck_details': [],
            'optimization_algorithm': 'none',
            'optimization_time': 0,
            'objective_value': 0
        }

    def generate_optimization_report(self, optimization_result: Dict, output_file: Optional[str] = None) -> str:
        """
        生成优化报告

        Args:
            optimization_result: 优化结果
            output_file: 输出文件路径

        Returns:
            str: 报告文件路径
        """
        if output_file is None:
            output_file = REPORTS_DIR / "ltl_optimization_results.xlsx"

        self.logger.info("生成LTL优化报告")

        try:
            with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
                # 装载方案
                if len(optimization_result['loading_plan']) > 0:
                    optimization_result['loading_plan'].to_excel(writer, sheet_name='装载方案', index=False)
                else:
                    pd.DataFrame().to_excel(writer, sheet_name='装载方案', index=False)

                # 未装载货物
                if len(optimization_result['unloaded_items_df']) > 0:
                    optimization_result['unloaded_items_df'].to_excel(writer, sheet_name='未装载货物', index=False)
                else:
                    pd.DataFrame().to_excel(writer, sheet_name='未装载货物', index=False)

                # 车辆利用情况
                if optimization_result['truck_details']:
                    truck_summary = []
                    for truck in optimization_result['truck_details']:
                        truck_summary.append({
                            '车辆ID': f"TRUCK_{truck['truck_id']:03d}",
                            '装载体积(m³)': truck['used_volume'],
                            '装载率': truck['used_volume'] / self.truck_specs['volume'],
                            '装载货物数': len(truck['items'])
                        })
                    truck_df = pd.DataFrame(truck_summary)
                    truck_df.to_excel(writer, sheet_name='车辆利用情况', index=False)

                # 优化摘要
                summary_data = {
                    '指标': ['总货物数', '装载货物数', '未装载货物数', '使用车辆数',
                           '总装载率', '体积利用率', '优化算法', '求解时间(秒)'],
                    '数值': [
                        optimization_result['loaded_items'] + optimization_result['unloaded_items'],
                        optimization_result['loaded_items'],
                        optimization_result['unloaded_items'],
                        optimization_result['trucks_used'],
                        f"{optimization_result['total_loading_rate']:.1%}",
                        f"{optimization_result['volume_utilization']:.1%}",
                        optimization_result['optimization_algorithm'],
                        optimization_result['optimization_time']
                    ]
                }
                summary_df = pd.DataFrame(summary_data)
                summary_df.to_excel(writer, sheet_name='优化摘要', index=False)

            self.logger.info(f"LTL优化报告已保存到: {output_file}")
            return str(output_file)

        except Exception as e:
            self.logger.error(f"生成优化报告失败: {str(e)}")
            raise

    def generate_full_dispatch_plan(self, large_results: Dict, ltl_results: Dict,
                                   run_id: str = None) -> str:
        """
        生成完整调度计划JSON文件

        Args:
            large_results: 大货物调度结果
            ltl_results: LTL优化结果
            run_id: 运行ID

        Returns:
            str: 输出文件路径
        """
        import json
        from datetime import datetime

        if run_id is None:
            run_id = f"run_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        self.logger.info("生成完整调度计划JSON文件")

        try:
            dispatch_plan = {}

            # 处理大货物调度结果
            if large_results.get('dispatch_results'):
                for i, result in enumerate(large_results['dispatch_results']):
                    truck_id = f"LARGE_TRUCK_{i:02d}"
                    dispatch_plan[truck_id] = {
                        'type': 'FULL_TRUCK',
                        'source_order': result.get('order_id', f'LARGE_ORDER_{i}'),
                        'item_type': result.get('item_type', 'unknown'),
                        'quantity_per_truck': result.get('items_count', 0),
                        'total_weight_kg': result.get('truck_volume_used', 0) * 1000,  # 估算重量
                        'loading_efficiency': result.get('loading_efficiency', 0)
                    }

            # 处理LTL优化结果
            if ltl_results.get('loading_plan') is not None and len(ltl_results['loading_plan']) > 0:
                # 按truck_id分组
                ltl_plan = ltl_results['loading_plan']
                trucks_dict = {}

                for _, row in ltl_plan.iterrows():
                    truck_id = f"LTL_TRUCK_{row['truck_id']:02d}"
                    if truck_id not in trucks_dict:
                        trucks_dict[truck_id] = []

                    trucks_dict[truck_id].append({
                        'item_id': row['item_id'],
                        'weight_kg': row.get('weight_kg', 0),
                        'volume_m3': row['volume_m3']
                    })

                # 添加到调度计划
                for truck_id, items in trucks_dict.items():
                    total_weight = sum(item['weight_kg'] for item in items)
                    dispatch_plan[truck_id] = {
                        'type': 'LTL_TRUCK',
                        'loaded_items': items,
                        'total_weight_kg': total_weight,
                        'item_count': len(items)
                    }

            # 构建完整数据结构
            full_dispatch_data = {
                'run_id': run_id,
                'generated_time': datetime.now().isoformat(),
                'dispatch_plan': dispatch_plan,
                'summary': {
                    'total_trucks': len(dispatch_plan),
                    'large_trucks': len([t for t in dispatch_plan.values() if t['type'] == 'FULL_TRUCK']),
                    'ltl_trucks': len([t for t in dispatch_plan.values() if t['type'] == 'LTL_TRUCK']),
                    'large_cargo_efficiency': large_results.get('dispatch_efficiency', 0),
                    'ltl_loading_rate': ltl_results.get('total_loading_rate', 0)
                }
            }

            # 保存文件
            output_file = INTERMEDIATE_DIR / FILE_CONFIG['full_dispatch_plan_file']
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(full_dispatch_data, f, ensure_ascii=False, indent=2)

            self.logger.info(f"完整调度计划已保存到: {output_file}")
            return str(output_file)

        except Exception as e:
            self.logger.error(f"生成完整调度计划失败: {str(e)}")
            raise

    def generate_id_mapping(self, merge_mapping: Dict, large_results: Dict,
                           ltl_results: Dict) -> str:
        """
        生成ID映射关系JSON文件

        Args:
            merge_mapping: 小货物合并映射关系
            large_results: 大货物调度结果
            ltl_results: LTL优化结果

        Returns:
            str: 输出文件路径
        """
        import json
        from datetime import datetime

        self.logger.info("生成ID映射关系JSON文件")

        try:
            id_to_orders_mapping = {}

            # 处理小货物合并映射
            if merge_mapping:
                for merged_id, order_list in merge_mapping.items():
                    id_to_orders_mapping[merged_id] = order_list

            # 处理大货物映射
            if large_results.get('dispatch_results'):
                for result in large_results['dispatch_results']:
                    order_id = result.get('order_id')
                    if order_id:
                        # 大货物直接映射
                        id_to_orders_mapping[order_id] = [order_id]

            # 处理LTL优化结果中的映射
            if ltl_results.get('loading_plan') is not None and len(ltl_results['loading_plan']) > 0:
                ltl_plan = ltl_results['loading_plan']
                for _, row in ltl_plan.iterrows():
                    item_id = row['item_id']
                    original_order_id = row.get('original_order_id', item_id)

                    if item_id not in id_to_orders_mapping:
                        # 如果是单个订单，直接映射
                        id_to_orders_mapping[item_id] = [original_order_id]

            # 保存映射文件
            output_file = INTERMEDIATE_DIR / FILE_CONFIG['id_to_orders_mapping_file']
            mapping_data = {
                'generated_time': datetime.now().isoformat(),
                'mapping_count': len(id_to_orders_mapping),
                'id_to_orders_mapping': id_to_orders_mapping
            }

            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(mapping_data, f, ensure_ascii=False, indent=2)

            self.logger.info(f"ID映射关系已保存到: {output_file}")
            self.logger.info(f"映射关系数量: {len(id_to_orders_mapping)}")

            return str(output_file)

        except Exception as e:
            self.logger.error(f"生成ID映射关系失败: {str(e)}")
            raise

    def get_merge_mapping_from_classifier(self, cargo_classifier) -> Dict:
        """
        从货物分类器获取合并映射关系

        Args:
            cargo_classifier: 货物分类器实例

        Returns:
            Dict: 合并映射关系
        """
        try:
            # 尝试从分类器获取合并映射
            if hasattr(cargo_classifier, 'merge_mapping'):
                return cargo_classifier.merge_mapping
            elif hasattr(cargo_classifier, 'get_merge_mapping'):
                return cargo_classifier.get_merge_mapping()
            else:
                self.logger.warning("无法从货物分类器获取合并映射关系，返回空字典")
                return {}

        except Exception as e:
            self.logger.error(f"获取合并映射关系失败: {str(e)}")
            return {}


def main():
    """测试LTL优化器模块"""
    # 模拟测试数据
    test_large_remaining = pd.DataFrame({
        'item_id': ['LARGE_REM_001', 'LARGE_REM_002'],
        'item_type': ['食品', '饮水'],
        'volume_m3': [0.05, 0.03],
        'weight_kg': [2.0, 1.5],
        'cargo_source': ['large_remaining', 'large_remaining']
    })

    test_medium_orders = pd.DataFrame({
        'order_id': ['ORDER_MED_001', 'ORDER_MED_002'],
        'item_type': ['农产品', '日用品'],
        'volume_m3': [0.2, 0.15],
        'weight_kg': [5.0, 3.0],
        'quantity': [50, 80]
    })

    test_merged_small = pd.DataFrame({
        'item_id': ['MERGED_001'],
        'item_type': ['mixed_small'],
        'volume_m3': [8.5],
        'weight_kg': [150],
        'is_merged': [True],
        'estimated_length': [2.0],
        'estimated_width': [2.0],
        'estimated_height': [2.125]
    })

    # 创建优化器并测试
    optimizer = LTLOptimizer()

    try:
        # 准备优化数据
        optimization_data = optimizer.prepare_optimization_data(
            test_large_remaining, test_medium_orders, test_merged_small
        )

        print(f"优化数据准备完成: {len(optimization_data)} 个货物")

        # 导出优化前数据
        export_path = optimizer.export_pre_optimization_data(optimization_data)
        print(f"优化前数据已导出: {export_path}")

        # 执行优化
        result = optimizer.optimize_ltl_multi_truck(optimization_data, 16)
        print(f"LTL优化完成:")
        print(f"  装载货物: {result['loaded_items']}")
        print(f"  使用车辆: {result['trucks_used']}")
        print(f"  装载率: {result['total_loading_rate']:.1%}")

    except Exception as e:
        print(f"测试失败: {str(e)}")


if __name__ == "__main__":
    main()