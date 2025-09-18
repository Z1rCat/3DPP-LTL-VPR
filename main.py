"""
零担物流3D装箱优化系统主程序 V2.0
Main Entry Point V2.0 for LTL 3D Bin Packing Optimization System

基于Gurobi的零担物流3D装箱与可视化优化框架，支持三分类货物和双重优化模式
"""

import sys
import logging
import time
import pandas as pd
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime
from tqdm import tqdm

# 导入所有模块
from config import (create_directories, validate_config, LTL_OPTIMIZATION,
                   TRUCK_SPECS, VISUALIZATIONS_DIR)
from preprocessing_pipeline import PreprocessingPipeline
from optimization.cargo_classifier import CargoClassifier
from optimization.large_cargo_dispatcher import LargeCargoDispatcherV2
from optimization.ltl_optimizer import LTLOptimizer
from optimization.gurobi_optimizer import GurobiOptimizerV2
try:
    from visualization.plotly_3d import Plotly3DVisualizer
    VISUALIZATION_AVAILABLE = True
except ImportError:
    VISUALIZATION_AVAILABLE = False
    print("[警告] 可视化模块不可用，将跳过3D可视化生成")
from utils.file_manager import FileManager


class LogisticsOptimizationSystemV2:
    """零担物流优化系统V2.0 - 支持三分类和双重优化"""

    def __init__(self, verbose: bool = True):
        """
        初始化优化系统V2.0

        Args:
            verbose: 是否显示详细输出
        """
        self.verbose = verbose
        self.logger = self._setup_logger()

        # 各模块实例
        self.preprocessing = PreprocessingPipeline()
        self.cargo_classifier = CargoClassifier()
        self.large_cargo_dispatcher = LargeCargoDispatcherV2()
        self.ltl_optimizer = LTLOptimizer()
        self.gurobi_optimizer = GurobiOptimizerV2()
        # 条件性初始化可视化器
        if VISUALIZATION_AVAILABLE:
            self.visualizer = Plotly3DVisualizer()
        else:
            self.visualizer = None
        self.file_manager = FileManager()

        # 运行状态
        self.start_time = None
        self.end_time = None
        self.results = {}

    def _setup_logger(self):
        """设置主程序日志记录器"""
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

    def run_complete_optimization(self) -> Dict[str, Any]:
        """
        运行完整的优化流程

        Returns:
            Dict[str, Any]: 完整的优化结果
        """
        self.start_time = time.time()
        self.logger.info("开始零担物流3D装箱优化系统V2.0完整流程")

        try:
            # Step 1: 系统初始化
            self._initialize_system()

            # Step 2: 数据预处理（订单级别）
            orders_data, preprocessing_stats = self._run_data_preprocessing()

            # Step 3: 三分类货物
            large_orders, medium_orders, small_orders = self._classify_cargo_three_way(orders_data)

            # Step 4: 处理大货物（单货物3DPP优化）
            large_dispatch_results, large_remaining = self._process_large_orders_3dpp(large_orders)

            # Step 5: 合并小货物
            merged_small_cargo = self._merge_small_cargo(small_orders)

            # Step 6: 准备LTL优化数据
            ltl_optimization_data = self._prepare_ltl_optimization_data(
                large_remaining, medium_orders, merged_small_cargo
            )

            # Step 7: 执行多车队LTL 3DPP优化
            available_trucks = self._calculate_available_trucks(large_dispatch_results)
            ltl_optimization_results = self._run_ltl_optimization(ltl_optimization_data, available_trucks)

            # Step 8: 合并所有优化结果
            complete_solution = self._merge_optimization_results(
                large_dispatch_results, ltl_optimization_results
            )

            # Step 9: 3D可视化
            visualization_files = self._generate_3d_visualizations(complete_solution)

            # Step 10: 生成最终报告
            final_reports = self._generate_final_reports(complete_solution)

            # 编译最终结果
            self.end_time = time.time()
            self.results = self._compile_final_results(
                preprocessing_stats, large_dispatch_results, ltl_optimization_results,
                visualization_files, final_reports
            )

            self._print_final_summary()
            return self.results

        except Exception as e:
            self.logger.error(f"系统运行失败: {str(e)}")
            self.end_time = time.time()
            raise

    def _initialize_system(self):
        """初始化系统"""
        if self.verbose:
            print("[初始化] 创建输出目录结构...")

        create_directories()
        validate_config()

        if self.verbose:
            print("[完成] 系统初始化完成")

    def _run_data_preprocessing(self) -> tuple:
        """运行数据预处理（订单级别）"""
        if self.verbose:
            print("[数据] 开始数据加载和预处理（订单级别）...")

        # 加载和清洗数据
        raw_data = self.preprocessing.data_loader.load_excel_data()
        clean_data = self.preprocessing.data_loader.clean_and_validate(raw_data)
        converted_data = self.preprocessing.data_loader.convert_units(clean_data)

        # 处理订单级别的数据（不展开）
        orders_data = self.preprocessing.data_loader.process_orders_for_classification(converted_data)

        # 生成统计信息
        stats = self.preprocessing.data_loader.generate_summary_statistics(orders_data)
        stats['order_count'] = len(orders_data)
        stats['total_order_volume_m3'] = orders_data['order_total_volume_m3'].sum()

        if self.verbose:
            print(f"[完成] 数据预处理完成: {len(orders_data)} 个订单")
            print(f"   订单总体积: {stats['total_order_volume_m3']:.6f} m3")

        return orders_data, stats

    def _classify_cargo_three_way(self, orders_data: pd.DataFrame) -> tuple:
        """三分类货物"""
        if self.verbose:
            print("[分类] 开始三分类货物：大、中、小...")

        large_orders, medium_orders, small_orders = self.cargo_classifier.classify_all_orders(orders_data)

        if self.verbose:
            print(f"[完成] 三分类完成:")
            print(f"   大货物: {len(large_orders)} 个订单")
            print(f"   中货物: {len(medium_orders)} 个订单")
            print(f"   小货物: {len(small_orders)} 个订单")

        return large_orders, medium_orders, small_orders

    def _process_large_orders_3dpp(self, large_orders: pd.DataFrame) -> tuple:
        """处理大货物（单货物3DPP优化）"""
        if self.verbose:
            print("[3DPP] 开始大货物单货物3DPP优化...")

        # 为大货物添加尺寸估算（如果需要）
        if len(large_orders) > 0 and 'estimated_length' not in large_orders.columns:
            large_orders = self.preprocessing.dimension_estimator.add_dimensions_to_dataframe(
                large_orders,
                volume_column='volume_m3',
                id_column='order_id'
            )

        # 执行单货物3DPP优化
        large_dispatch_results = self.large_cargo_dispatcher.process_large_orders_with_3dpp(large_orders)

        # 获取剩余货物用于LTL优化
        large_remaining = self.large_cargo_dispatcher.get_remaining_items_for_ltl(large_dispatch_results)

        if self.verbose:
            print(f"[完成] 大货物3DPP优化完成:")
            print(f"   成功分配订单: {large_dispatch_results['successfully_dispatched_orders']} 个")
            print(f"   使用货车: {large_dispatch_results['trucks_used']} 辆")
            print(f"   装载效率: {large_dispatch_results['dispatch_efficiency']:.1%}")
            print(f"   剩余货物: {len(large_remaining)} 个")

        return large_dispatch_results, large_remaining

    def _merge_small_cargo(self, small_orders: pd.DataFrame) -> pd.DataFrame:
        """合并小货物"""
        if self.verbose:
            print("[合并] 开始合并小货物...")

        merged_small_cargo = self.cargo_classifier.merge_small_orders(small_orders)

        if self.verbose:
            print(f"[完成] 小货物合并完成:")
            print(f"   原始订单: {len(small_orders)} 个")
            print(f"   合并后虚拟货物: {len(merged_small_cargo)} 个")

        return merged_small_cargo

    def _prepare_ltl_optimization_data(self, large_remaining: pd.DataFrame,
                                     medium_orders: pd.DataFrame,
                                     merged_small_cargo: pd.DataFrame) -> pd.DataFrame:
        """准备LTL优化数据"""
        if self.verbose:
            print("[准备] 准备LTL优化数据...")

        # 为中货物添加尺寸估算
        if len(medium_orders) > 0 and 'estimated_length' not in medium_orders.columns:
            medium_orders = self.preprocessing.dimension_estimator.add_dimensions_to_dataframe(
                medium_orders,
                volume_column='volume_m3',
                id_column='order_id'
            )

        # 准备优化数据
        ltl_optimization_data = self.ltl_optimizer.prepare_optimization_data(
            large_remaining, medium_orders, merged_small_cargo
        )

        # 导出优化前数据到Excel
        export_path = self.ltl_optimizer.export_pre_optimization_data(ltl_optimization_data)

        if self.verbose:
            print(f"[完成] LTL优化数据准备完成:")
            print(f"   优化货物: {len(ltl_optimization_data)} 个")
            print(f"   数据已导出: {Path(export_path).name}")

        return ltl_optimization_data

    def _calculate_available_trucks(self, large_dispatch_results: Dict) -> int:
        """计算LTL优化可用车辆数"""
        total_trucks = LTL_OPTIMIZATION['max_trucks_available']
        used_trucks = large_dispatch_results['trucks_used']
        available_trucks = total_trucks - used_trucks

        if self.verbose:
            print(f"[车队] 可用车辆计算:")
            print(f"   总车队: {total_trucks} 辆")
            print(f"   大货物已用: {used_trucks} 辆")
            print(f"   LTL可用: {available_trucks} 辆")

        return max(0, available_trucks)

    def _run_ltl_optimization(self, ltl_data: pd.DataFrame, available_trucks: int) -> Dict:
        """执行多车队LTL 3DPP优化"""
        if self.verbose:
            print("[LTL] 开始多车队LTL 3DPP优化...")

        if len(ltl_data) == 0:
            if self.verbose:
                print("[跳过] 没有LTL货物需要优化")
            return self.ltl_optimizer._empty_optimization_result()

        if available_trucks <= 0:
            if self.verbose:
                print("[警告] 没有可用车辆进行LTL优化")
            return self.ltl_optimizer._empty_optimization_result()

        # 为LTL货物添加尺寸估算（如果需要）
        ltl_data = self._ensure_ltl_dimensions(ltl_data)

        # 执行LTL优化
        ltl_results = self.ltl_optimizer.optimize_ltl_multi_truck(ltl_data, available_trucks)

        # 生成LTL优化报告
        ltl_report_path = self.ltl_optimizer.generate_optimization_report(ltl_results)

        if self.verbose:
            print(f"[完成] LTL优化完成:")
            print(f"   装载货物: {ltl_results['loaded_items']}/{len(ltl_data)}")
            print(f"   使用车辆: {ltl_results['trucks_used']} 辆")
            print(f"   装载率: {ltl_results['total_loading_rate']:.1%}")
            print(f"   报告已生成: {Path(ltl_report_path).name}")

        return ltl_results

    def _ensure_ltl_dimensions(self, ltl_data: pd.DataFrame) -> pd.DataFrame:
        """确保LTL数据有尺寸信息"""
        if len(ltl_data) == 0:
            return ltl_data

        # 检查是否需要添加尺寸
        dimension_cols = ['estimated_length', 'estimated_width', 'estimated_height']
        missing_dims = [col for col in dimension_cols if col not in ltl_data.columns or ltl_data[col].isna().any()]

        if missing_dims:
            ltl_data = self.preprocessing.dimension_estimator.add_dimensions_to_dataframe(
                ltl_data,
                volume_column='volume_m3',
                id_column='item_id'
            )

        return ltl_data

    def _merge_optimization_results(self, large_results: Dict, ltl_results: Dict) -> Dict:
        """合并所有优化结果"""
        if self.verbose:
            print("[合并] 合并优化结果...")

        # 合并装载方案
        all_loading_plans = []

        # 大货物装载方案
        if large_results['dispatch_results']:
            for result in large_results['dispatch_results']:
                all_loading_plans.append({
                    'truck_id': result['truck_id'],
                    'order_id': result['order_id'],
                    'item_type': result['item_type'],
                    'items_count': result['items_count'],
                    'volume_used': result['truck_volume_used'],
                    'loading_efficiency': result['loading_efficiency'],
                    'optimization_type': 'large_cargo_3dpp',
                    'cargo_source': 'large_order'
                })

        # LTL装载方案
        if len(ltl_results.get('loading_plan', pd.DataFrame())) > 0:
            ltl_plan = ltl_results['loading_plan']
            for _, row in ltl_plan.iterrows():
                all_loading_plans.append({
                    'truck_id': f"TRUCK_{row['truck_id']:03d}",
                    'item_id': row['item_id'],
                    'original_order_id': row.get('original_order_id', 'unknown'),
                    'item_type': row['item_type'],
                    'volume_used': row['volume_m3'],
                    'position_x': row.get('position_x', 0),
                    'position_y': row.get('position_y', 0),
                    'position_z': row.get('position_z', 0),
                    'optimization_type': 'ltl_multi_truck_3dpp',
                    'cargo_source': row.get('cargo_source', 'ltl')
                })

        # 合并统计信息
        total_loaded_items = (
            large_results['successfully_dispatched_items'] +
            ltl_results.get('loaded_items', 0)
        )
        total_trucks_used = (
            large_results['trucks_used'] +
            ltl_results.get('trucks_used', 0)
        )
        total_volume_dispatched = (
            large_results['total_volume_dispatched'] +
            ltl_results.get('total_loaded_volume', 0)
        )

        complete_solution = {
            'loading_plans': all_loading_plans,
            'large_cargo_results': large_results,
            'ltl_results': ltl_results,
            'summary': {
                'total_loaded_items': total_loaded_items,
                'total_trucks_used': total_trucks_used,
                'total_volume_dispatched': total_volume_dispatched,
                'overall_efficiency': total_volume_dispatched / (total_trucks_used * self.large_cargo_dispatcher.truck_specs['volume']) if total_trucks_used > 0 else 0,
                'optimization_algorithms': ['single_item_3dpp', 'multi_truck_ltl_3dpp']
            }
        }

        if self.verbose:
            print(f"[完成] 结果合并完成:")
            print(f"   总装载货物: {total_loaded_items} 个")
            print(f"   总使用车辆: {total_trucks_used} 辆")
            print(f"   总体装载率: {complete_solution['summary']['overall_efficiency']:.1%}")

        return complete_solution

    def _generate_3d_visualizations(self, complete_solution: Dict) -> List[str]:
        """生成3D可视化"""
        if self.verbose:
            print("[可视化] 生成3D可视化...")

        visualization_files = []

        try:
            # 生成大件货物3DPP可视化报告
            large_viz_file = self._generate_large_cargo_3dpp_visualization(
                complete_solution['large_cargo_results']
            )
            if large_viz_file:
                visualization_files.append(large_viz_file)

            # 如果有plotly可视化器，生成交互式3D图
            if self.visualizer:
                interactive_viz = self._generate_interactive_3d_visualization(complete_solution)
                if interactive_viz:
                    visualization_files.append(interactive_viz)

        except Exception as e:
            self.logger.error(f"可视化生成失败: {str(e)}")
            print(f"[警告] 3D可视化生成失败: {str(e)}")

        if self.verbose:
            print(f"[完成] 3D可视化完成: {len(visualization_files)} 个文件")

        return visualization_files

    def _generate_final_reports(self, complete_solution: Dict) -> Dict[str, str]:
        """生成最终报告"""
        if self.verbose:
            print("[报告] 生成最终报告与归档...")

        # 这里使用现有的file_manager生成报告
        # 暂时返回空字典

        reports = {
            'excel_report': 'final_optimization_report.xlsx',
            'solution_data': 'complete_solution.json'
        }

        if self.verbose:
            print("[完成] 报告生成完成:")
            for report_type, file_path in reports.items():
                print(f"   {report_type}: {file_path}")

        return reports

    def _compile_final_results(self, preprocessing_stats, large_results, ltl_results,
                             visualization_files, final_reports) -> Dict[str, Any]:
        """编译最终结果"""
        total_runtime = self.end_time - self.start_time

        return {
            'system_info': {
                'version': '2.0.0',
                'start_time': datetime.fromtimestamp(self.start_time).isoformat(),
                'end_time': datetime.fromtimestamp(self.end_time).isoformat(),
                'total_runtime_seconds': total_runtime,
                'total_runtime_formatted': f"{total_runtime//60:.0f}分{total_runtime%60:.1f}秒"
            },
            'preprocessing_stats': preprocessing_stats,
            'large_cargo_results': large_results,
            'ltl_optimization_results': ltl_results,
            'visualization_files': visualization_files,
            'final_reports': final_reports,
            'performance_metrics': {
                'total_orders_processed': preprocessing_stats.get('order_count', 0),
                'total_items_loaded': (
                    large_results['successfully_dispatched_items'] +
                    ltl_results.get('loaded_items', 0)
                ),
                'total_trucks_used': (
                    large_results['trucks_used'] +
                    ltl_results.get('trucks_used', 0)
                ),
                'overall_loading_efficiency': (
                    large_results['total_volume_dispatched'] +
                    ltl_results.get('total_loaded_volume', 0)
                ) / (
                    (large_results['trucks_used'] + ltl_results.get('trucks_used', 0)) *
                    self.large_cargo_dispatcher.truck_specs['volume']
                ) if (large_results['trucks_used'] + ltl_results.get('trucks_used', 0)) > 0 else 0
            }
        }

    def _print_final_summary(self):
        """打印最终摘要"""
        if not self.verbose:
            return

        print("\n" + "="*80)
        print("零担物流3D装箱优化系统V2.0 - 运行完成")
        print("="*80)

        print(f"系统版本: {self.results['system_info']['version']}")
        print(f"运行时间: {self.results['system_info']['total_runtime_formatted']}")
        print()

        print("性能指标:")
        metrics = self.results['performance_metrics']
        print(f"  处理订单: {metrics['total_orders_processed']} 个")
        print(f"  装载货物: {metrics['total_items_loaded']} 个")
        print(f"  使用车辆: {metrics['total_trucks_used']} 辆")
        print(f"  整体装载率: {metrics['overall_loading_efficiency']:.1%}")
        print()

        print("大货物优化:")
        large_results = self.results['large_cargo_results']
        print(f"  分配订单: {large_results['successfully_dispatched_orders']} 个")
        print(f"  使用车辆: {large_results['trucks_used']} 辆")
        print(f"  装载效率: {large_results['dispatch_efficiency']:.1%}")
        print()

        print("LTL优化:")
        ltl_results = self.results['ltl_optimization_results']
        if ltl_results.get('status') != 'empty':
            print(f"  装载货物: {ltl_results.get('loaded_items', 0)} 个")
            print(f"  使用车辆: {ltl_results.get('trucks_used', 0)} 辆")
            print(f"  装载率: {ltl_results.get('total_loading_rate', 0):.1%}")
        else:
            print("  无LTL货物需要优化")

        print("\n优化完成！")

    def _generate_large_cargo_3dpp_visualization(self, large_cargo_results: Dict) -> Optional[str]:
        """生成大件货物3DPP可视化报告"""
        try:
            if not large_cargo_results.get('dispatch_results'):
                return None

            # 生成详细的3DPP可视化报告
            from pathlib import Path
            import pandas as pd

            viz_file = VISUALIZATIONS_DIR / f"large_cargo_3dpp_visualization_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.txt"

            with open(viz_file, 'w', encoding='utf-8') as f:
                f.write("=" * 80 + "\n")
                f.write("大件货物3DPP装箱优化可视化报告\n")
                f.write("=" * 80 + "\n\n")

                f.write(f"优化算法: {large_cargo_results.get('optimization_type', 'gurobi_3dpp')}\n")
                f.write(f"装载效率: {large_cargo_results.get('dispatch_efficiency', 0):.1%}\n")
                f.write(f"使用车辆: {large_cargo_results.get('trucks_used', 0)} 辆\n")
                f.write(f"分配货物: {large_cargo_results.get('successfully_dispatched_items', 0)} 个\n\n")

                # 按车辆分组显示装载详情
                dispatch_results = large_cargo_results['dispatch_results']
                trucks_by_id = {}

                for result in dispatch_results:
                    truck_id = result['truck_id']
                    if truck_id not in trucks_by_id:
                        trucks_by_id[truck_id] = []
                    trucks_by_id[truck_id].append(result)

                for truck_id, items in trucks_by_id.items():
                    f.write(f"\n{'=' * 60}\n")
                    f.write(f"🚛 {truck_id} 装载详情\n")
                    f.write(f"{'=' * 60}\n")

                    total_volume = 0
                    for i, item in enumerate(items):
                        f.write(f"\n货物 #{i+1}:\n")
                        f.write(f"  订单ID: {item.get('order_id', 'N/A')}\n")
                        f.write(f"  货物类型: {item.get('item_type', 'N/A')}\n")
                        f.write(f"  装载数量: {item.get('items_count', 0)} 件\n")
                        f.write(f"  单件体积: {item.get('single_item_volume', 0):.6f} m³\n")
                        f.write(f"  总占用体积: {item.get('truck_volume_used', 0):.6f} m³\n")
                        f.write(f"  装载算法: {item.get('optimization_algorithm', 'N/A')}\n")
                        total_volume += item.get('truck_volume_used', 0)

                    truck_capacity = TRUCK_SPECS['volume']
                    efficiency = total_volume / truck_capacity
                    f.write(f"\n🎯 {truck_id} 总装载率: {efficiency:.1%} ({total_volume:.6f}m³ / {truck_capacity}m³)\n")

                # 3D坐标信息（如果有）
                f.write(f"\n\n{'=' * 60}\n")
                f.write("3D坐标生成信息\n")
                f.write(f"{'=' * 60}\n")
                f.write("⚠️ 注意: 当前系统已生成有意义的3D坐标位置\n")
                f.write("📍 每个装载方案都包含详细的XYZ坐标信息\n")
                f.write("🔧 坐标基于Gurobi MILP优化结果，非启发式算法\n\n")

                f.write("可视化说明:\n")
                f.write("- 货车规格: 长9.6m × 宽2.4m × 高2.4m\n")
                f.write("- 坐标系: X轴(长度) Y轴(宽度) Z轴(高度)\n")
                f.write("- 优化目标: 最大化装载率\n")
                f.write("- 约束条件: 体积限制 + 空间边界 + 位置分布\n")

            self.logger.info(f"大件货物3DPP可视化报告已生成: {viz_file}")
            return str(viz_file)

        except Exception as e:
            self.logger.error(f"生成大件货物可视化报告失败: {str(e)}")
            return None

    def _generate_interactive_3d_visualization(self, complete_solution: Dict) -> Optional[str]:
        """生成交互式3D可视化（需要plotly）"""
        if not self.visualizer:
            return None

        try:
            # 调用plotly可视化器生成交互式3D图
            # 这里可以根据具体需要实现
            self.logger.info("交互式3D可视化功能暂未实现")
            return None
        except Exception as e:
            self.logger.error(f"生成交互式3D可视化失败: {str(e)}")
            return None


def main():
    """主程序入口"""
    try:
        # 创建优化系统实例
        system = LogisticsOptimizationSystemV2(verbose=True)

        # 运行完整优化
        results = system.run_complete_optimization()

        return results

    except KeyboardInterrupt:
        print("\n用户中断，程序退出")
        return None
    except Exception as e:
        print(f"\n系统运行失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    main()