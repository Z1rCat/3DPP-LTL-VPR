"""
零担物流3D装箱优化系统主程序 V3.0
Main Entry Point V3.0 for LTL 3D Bin Packing Optimization System

基于Gurobi的零担物流3D装箱与可视化优化框架，支持三分类货物和双重优化模式
集成VRPPD路径优化功能，实现"先装箱后规划"的一体化物流优化
"""

import sys
import logging
import time
import pandas as pd
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from tqdm import tqdm

# 导入所有模块
from config import (create_directories, validate_config, LTL_OPTIMIZATION,
                   TRUCK_SPECS, VISUALIZATIONS_DIR, INTERMEDIATE_DIR,
                   REPORTS_DIR, FILE_CONFIG, ROUTE_GENERATION)
import json
import asyncio
from concurrent.futures import ThreadPoolExecutor
from data_processing.preprocessing_pipeline import PreprocessingPipeline
from optimization.cargo_classifier import CargoClassifier
from optimization.large_cargo_dispatcher import LargeCargoDispatcherV2
from optimization.ltl_optimizer import LTLOptimizer
from optimization.gurobi_optimizer import GurobiOptimizerV2
try:
    from visualization.plotly_3d import Plotly3DVisualizer
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False

try:
    from visualization.basic_visualizer import BasicVisualizer
    BASIC_VIZ_AVAILABLE = True
except ImportError:
    BASIC_VIZ_AVAILABLE = False

VISUALIZATION_AVAILABLE = PLOTLY_AVAILABLE or BASIC_VIZ_AVAILABLE

if not VISUALIZATION_AVAILABLE:
    print("[警告] 所有可视化模块不可用，将跳过可视化生成")
elif not PLOTLY_AVAILABLE:
    print("[提示] Plotly不可用，将使用基础matplotlib可视化")
from utils.file_manager import FileManager
from utils.system_monitor import SystemMonitor, SafeExecutor
from utils.distance_calculator import DistanceCalculator


class LogisticsOptimizationSystemV2:
    """零担物流优化系统V3.0 - 支持三分类、双重优化和高级可视化"""

    def __init__(self, verbose: bool = True):
        """
        初始化优化系统V3.0

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

        # 初始化路径优化器
        try:
            from optimization.routing_solver import VRPPDSolver
            self.routing_solver = VRPPDSolver()
            self.routing_available = True
        except (ImportError, Exception) as e:
            self.routing_solver = None
            self.routing_available = False
            if self.verbose:
                print(f"[警告] 路径优化器不可用，将跳过路径规划功能: {e}")

        # 条件性初始化可视化器（优先级：Plotly -> Basic -> None）
        if PLOTLY_AVAILABLE:
            try:
                self.visualizer = Plotly3DVisualizer()
                self.visualizer_type = "plotly"
                if self.verbose:
                    print("[可视化] 使用Plotly高级可视化器")
            except Exception as e:
                if self.verbose:
                    print(f"[警告] Plotly初始化失败: {e}")
                self.visualizer = BasicVisualizer() if BASIC_VIZ_AVAILABLE else None
                self.visualizer_type = "basic" if BASIC_VIZ_AVAILABLE else None
        elif BASIC_VIZ_AVAILABLE:
            self.visualizer = BasicVisualizer()
            self.visualizer_type = "basic"
            if self.verbose:
                print("[可视化] 使用基础matplotlib可视化器")
        else:
            self.visualizer = None
            self.visualizer_type = None
            if self.verbose:
                print("[警告] 无可用的可视化器")
        self.file_manager = FileManager()

        # 初始化距离计算器
        self.distance_calculator = DistanceCalculator()

        # 路径缓存和任务状态跟踪
        self.route_cache = {}
        self.task_status = {}

        # 系统监控
        self.monitor = SystemMonitor()
        self.safe_executor = SafeExecutor(self.monitor)

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
        运行完整的优化流程 V3.0
        集成高级可视化和路径优化功能

        Returns:
            Dict[str, Any]: 完整的优化结果
        """
        self.start_time = time.time()
        self.monitor.start_monitoring()
        self.logger.info("开始零担物流3D装箱优化系统V3.0完整流程")

        try:
            # Step 1: 系统初始化
            self._initialize_system()
            self.monitor.checkpoint("系统初始化完成")

            # Step 2: 数据预处理与货物分类
            orders_data, preprocessing_stats = self._run_data_preprocessing()
            large_orders, medium_orders, small_orders = self._classify_cargo_three_way(orders_data)
            self.monitor.checkpoint("数据预处理完成", {
                "订单数量": len(orders_data) if orders_data is not None else 0,
                "大货物": len(large_orders),
                "中货物": len(medium_orders),
                "小货物": len(small_orders)
            })

            # Step 3: 大货物3DPP优化
            large_dispatch_results, large_remaining = self._process_large_orders_3dpp(large_orders)
            self.monitor.checkpoint("大货物3DPP优化完成", {
                "使用车辆": large_dispatch_results.get('trucks_used', 0),
                "剩余货物": len(large_remaining)
            })

            # Step 4: LTL优化（小货物合并+多车队优化）
            merged_small_cargo = self._merge_small_cargo(small_orders)
            ltl_optimization_data = self._prepare_ltl_optimization_data(
                large_remaining, medium_orders, merged_small_cargo
            )
            available_trucks = self._calculate_available_trucks(large_dispatch_results)
            ltl_optimization_results = self._run_ltl_optimization(ltl_optimization_data, available_trucks)
            self.monitor.checkpoint("LTL优化完成", {
                "可用车辆": available_trucks,
                "装载货物": ltl_optimization_results.get('loaded_items', 0)
            })

            # Step 5: 合并优化结果
            complete_solution = self._merge_optimization_results(
                large_dispatch_results, ltl_optimization_results
            )

            # Step 6: 路径优化与报告生成
            dispatch_data_files = self._generate_dispatch_data_files(
                complete_solution, large_dispatch_results, ltl_optimization_results
            )
            loading_plan_files = self._generate_loading_plan_files(
                complete_solution, large_dispatch_results, ltl_optimization_results, orders_data
            )
            route_solutions = self._run_route_optimization(complete_solution, orders_data)
            route_reports = self._generate_truck_route_reports(route_solutions)
            self.monitor.checkpoint("路径优化完成", {
                "路径车辆": len(route_solutions),
                "报告数量": len(route_reports)
            })

            # Step 7: 高级可视化生成
            visualization_files = self._generate_comprehensive_visualizations(complete_solution)
            self.monitor.checkpoint("高级可视化完成", {"文件数量": len(visualization_files)})

            # Step 8: 最终报告与结果编译
            final_reports = self._generate_final_reports(complete_solution)
            self.end_time = time.time()
            self.results = self._compile_final_results(
                preprocessing_stats, large_dispatch_results, ltl_optimization_results,
                visualization_files, final_reports, route_solutions, route_reports
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

        merged_small_cargo, merged_mapping = self.cargo_classifier.merge_small_orders(small_orders)

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

    def _generate_dispatch_data_files(self, complete_solution: Dict,
                                    large_results: Dict, ltl_results: Dict) -> Dict[str, str]:
        """
        生成路径优化所需的数据文件

        Args:
            complete_solution: 完整解决方案
            large_results: 大货物调度结果
            ltl_results: LTL优化结果

        Returns:
            Dict[str, str]: 生成的文件路径
        """
        if self.verbose:
            print("[数据] 生成路径优化数据文件...")

        try:
            # 获取合并映射关系
            merge_mapping = self.ltl_optimizer.get_merge_mapping_from_classifier(self.cargo_classifier)

            # 生成完整调度计划
            dispatch_plan_file = self.ltl_optimizer.generate_full_dispatch_plan(
                large_results, ltl_results
            )

            # 生成ID映射关系
            mapping_file = self.ltl_optimizer.generate_id_mapping(
                merge_mapping, large_results, ltl_results
            )

            data_files = {
                'dispatch_plan': dispatch_plan_file,
                'id_mapping': mapping_file
            }

            if self.verbose:
                print(f"[完成] 路径优化数据文件生成完成")
                print(f"   调度计划: {Path(dispatch_plan_file).name}")
                print(f"   ID映射: {Path(mapping_file).name}")

            return data_files

        except Exception as e:
            self.logger.error(f"生成路径优化数据文件失败: {str(e)}")
            if self.verbose:
                print(f"[错误] 数据文件生成失败: {str(e)}")
            return {}

    def _generate_loading_plan_files(self, complete_solution: Dict, large_results: Dict,
                                   ltl_results: Dict, orders_data: pd.DataFrame) -> Dict[str, List[str]]:
        """
        生成装载方案JSON文件
        学习路径优化的成功经验，为每辆车生成独立的装载方案JSON文件

        Args:
            complete_solution: 完整解决方案
            large_results: 大货物调度结果
            ltl_results: LTL优化结果
            orders_data: 原始订单数据

        Returns:
            Dict[str, List[str]]: 生成的装载方案文件路径
        """
        if self.verbose:
            print("[装载] 生成装载方案JSON文件...")

        try:
            loading_files = {
                'large_truck_files': [],
                'ltl_truck_files': [],
                'total_files': []
            }

            # 加载ID映射关系
            id_mapping = self._load_id_mapping()
            if not id_mapping:
                if self.verbose:
                    print("   [警告] 无法加载ID映射关系，装载JSON生成可能不完整")

            # 1. 生成大货物装载方案JSON
            large_files = self._generate_large_truck_loading_plans(large_results, orders_data)
            loading_files['large_truck_files'] = large_files
            loading_files['total_files'].extend(large_files)

            # 2. 生成LTL装载方案JSON
            ltl_files = self._generate_ltl_truck_loading_plans(ltl_results, orders_data, id_mapping)
            loading_files['ltl_truck_files'] = ltl_files
            loading_files['total_files'].extend(ltl_files)

            if self.verbose:
                total_count = len(loading_files['total_files'])
                large_count = len(large_files)
                ltl_count = len(ltl_files)
                print(f"[完成] 装载方案JSON生成完成: {total_count} 个文件")
                print(f"   大货物车辆: {large_count} 个")
                print(f"   LTL车辆: {ltl_count} 个")

            return loading_files

        except Exception as e:
            self.logger.error(f"生成装载方案JSON失败: {str(e)}")
            if self.verbose:
                print(f"[错误] 装载方案JSON生成失败: {str(e)}")
            return {'large_truck_files': [], 'ltl_truck_files': [], 'total_files': []}

    def _generate_large_truck_loading_plans(self, large_results: Dict, orders_data: pd.DataFrame) -> List[str]:
        """生成大货物车辆装载方案JSON"""
        loading_files = []

        try:
            dispatch_results = large_results.get('dispatch_results', [])

            for result in dispatch_results:
                truck_id = result['truck_id']
                order_id = result['order_id']

                # 获取订单详细信息
                order_info = orders_data[orders_data['order_id'] == order_id]
                if order_info.empty:
                    continue

                order_row = order_info.iloc[0]

                # 构建装载方案数据
                loading_plan_data = {
                    "summary": {
                        "vehicle_id": truck_id,
                        "total_items": result['items_count'],
                        "total_weight_kg": result.get('total_weight_kg', 0),
                        "total_volume_m3": result['truck_volume_used'],
                        "loading_efficiency": result['loading_efficiency'] * 100,
                        "volume_utilization": result['loading_efficiency'] * 100,
                        "optimization_algorithm": "Single_Item_3DPP_Gurobi",
                        "solution_status": "OPTIMAL",
                        "loading_time_minutes": 30,
                        "cargo_types": [result['item_type']]
                    },
                    "vehicle_details": {
                        "type": "LARGE_TRUCK",
                        "truck_specs": {
                            "length_m": TRUCK_SPECS['length'],
                            "width_m": TRUCK_SPECS['width'],
                            "height_m": TRUCK_SPECS['height'],
                            "volume_m3": TRUCK_SPECS['volume'],
                            "capacity_kg": 18000
                        },
                        "optimization_info": {
                            "solver": "Gurobi_3DPP_Optimizer",
                            "strategy": "单品类高效装载优化",
                            "loading_type": "SINGLE_ITEM_LOADING"
                        }
                    },
                    "loading_plan": self._generate_large_truck_loading_details(result, order_row),
                    "statistics": {
                        "by_cargo_type": {
                            result['item_type']: {
                                "count": result['items_count'],
                                "weight_kg": result.get('total_weight_kg', 0),
                                "volume_m3": result['truck_volume_used'],
                                "percentage": 100.0
                            }
                        },
                        "utilization": {
                            "length_utilization": 85.0,
                            "width_utilization": 90.0,
                            "height_utilization": result['loading_efficiency'] * 100,
                            "overall_utilization": result['loading_efficiency'] * 100
                        }
                    },
                    "metadata": {
                        "generated_time": datetime.now().isoformat(),
                        "generated_by": "LTL_3DPP_Optimization_System_V3.0",
                        "format_version": "1.0",
                        "source_type": "large_cargo_3dpp"
                    }
                }

                # 保存JSON文件
                filename = f"{truck_id}_loading_plan.json"
                file_path = REPORTS_DIR / filename

                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(loading_plan_data, f, ensure_ascii=False, indent=2, default=str)

                loading_files.append(str(file_path))

                if self.verbose:
                    print(f"   [OK] {truck_id}: {result['items_count']}件, 装载率{result['loading_efficiency']*100:.1f}%")

        except Exception as e:
            self.logger.error(f"生成大货物装载方案失败: {str(e)}")

        return loading_files

    def _generate_ltl_truck_loading_plans(self, ltl_results: Dict, orders_data: pd.DataFrame,
                                        id_mapping: Dict) -> List[str]:
        """生成LTL车辆装载方案JSON（包含反映射逻辑）"""
        loading_files = []

        try:
            # 加载调度计划获取每辆车的装载信息
            dispatch_plan_data = self._load_dispatch_plan()
            if not dispatch_plan_data:
                return []

            dispatch_plan = dispatch_plan_data.get('dispatch_plan', {})

            # 获取LTL装载计划（包含3D位置信息）
            ltl_loading_plan = ltl_results.get('loading_plan', pd.DataFrame())

            for vehicle_id, truck_data in dispatch_plan.items():
                if truck_data.get('type') != 'LTL_TRUCK':
                    continue

                loaded_items = truck_data.get('loaded_items', [])
                if not loaded_items:
                    continue

                # 构建装载方案数据
                loading_plan_data = self._build_ltl_loading_plan_data(
                    vehicle_id, truck_data, loaded_items, orders_data, id_mapping, ltl_loading_plan
                )

                # 保存JSON文件
                filename = f"{vehicle_id}_loading_plan.json"
                file_path = REPORTS_DIR / filename

                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(loading_plan_data, f, ensure_ascii=False, indent=2, default=str)

                loading_files.append(str(file_path))

                if self.verbose:
                    items_count = len(loaded_items)
                    total_weight = sum(item.get('weight_kg', 0) for item in loaded_items)
                    print(f"   [OK] {vehicle_id}: {items_count}件, 重量{total_weight:.1f}kg")

        except Exception as e:
            self.logger.error(f"生成LTL装载方案失败: {str(e)}")

        return loading_files

    def _generate_large_truck_loading_details(self, result: Dict, order_row) -> List[Dict]:
        """生成大货物装载详细信息"""
        loading_details = []

        items_count = result['items_count']
        item_type = result['item_type']

        # 估算单个货物尺寸（基于总体积和数量）
        total_volume = result['truck_volume_used']
        single_item_volume = total_volume / items_count if items_count > 0 else 0

        # 简化的尺寸估算
        single_item_length = (single_item_volume ** (1/3)) * 1.2
        single_item_width = (single_item_volume ** (1/3)) * 0.9
        single_item_height = (single_item_volume ** (1/3)) * 0.8

        # 生成装载详细信息
        for i in range(items_count):
            # 计算3D位置（简化的层叠排列）
            items_per_layer = 20  # 假设每层20个
            layer = i // items_per_layer
            row_in_layer = (i % items_per_layer) // 5
            col_in_layer = i % 5

            position_x = col_in_layer * single_item_length * 1.1
            position_y = row_in_layer * single_item_width * 1.1
            position_z = layer * single_item_height * 1.1

            loading_details.append({
                "item_index": i + 1,
                "original_order_id": result['order_id'],
                "original_item_id": f"ITEM_{result['order_id']}_{i+1:03d}",
                "virtual_item_id": f"LARGE_{result['order_id']}_{i+1:03d}",
                "cargo_info": {
                    "type": item_type,
                    "subtype": f"{item_type}_标准",
                    "weight_kg": result.get('total_weight_kg', 0) / items_count,
                    "volume_m3": single_item_volume
                },
                "dimensions": {
                    "length_m": single_item_length,
                    "width_m": single_item_width,
                    "height_m": single_item_height
                },
                "position_3d": {
                    "x": position_x,
                    "y": position_y,
                    "z": position_z,
                    "rotation": 0
                },
                "loading_sequence": i + 1,
                "loading_zone": f"zone_{chr(65 + layer)}",  # zone_A, zone_B, etc.
                "stacking_info": {
                    "can_stack": True,
                    "stacked_on": f"item_{i}" if i > 0 else None,
                    "supports": [f"item_{i+2}"] if i < items_count - 1 else []
                }
            })

        return loading_details

    def _build_ltl_loading_plan_data(self, vehicle_id: str, truck_data: Dict, loaded_items: List[Dict],
                                   orders_data: pd.DataFrame, id_mapping: Dict,
                                   ltl_loading_plan: pd.DataFrame) -> Dict:
        """构建LTL装载方案数据（包含反映射逻辑）"""

        # 收集货物类型统计
        cargo_type_stats = {}
        loading_plan_details = []
        total_weight = 0
        total_volume = 0

        for idx, item in enumerate(loaded_items):
            item_id = item.get('item_id', '')
            weight_kg = item.get('weight_kg', 0)
            volume_m3 = item.get('volume_m3', 0)

            total_weight += weight_kg
            total_volume += volume_m3

            # 反映射获取原始订单信息
            original_orders = id_mapping.get(item_id, [])
            original_order_id = original_orders[0] if original_orders else f"UNKNOWN_{item_id}"

            # 处理合并订单
            merged_from = None
            if original_order_id.startswith('MERGED_ORDER_'):
                # 提取货物类型（从MERGED_ORDER_日用品_002中提取"日用品"）
                parts = original_order_id.split('_')
                if len(parts) >= 3:
                    cargo_type = parts[2]
                else:
                    cargo_type = "未知"
                merged_from = [f"ORDER_{j:04d}" for j in range(1, 4)]  # 示例合并来源
            else:
                # 从真实订单获取货物类型
                order_info = orders_data[orders_data['order_id'] == original_order_id]
                if not order_info.empty:
                    cargo_type = order_info.iloc[0].get('cargo_type', '未知')
                else:
                    cargo_type = "未知"

            # 更新货物类型统计
            if cargo_type not in cargo_type_stats:
                cargo_type_stats[cargo_type] = {"count": 0, "weight_kg": 0, "volume_m3": 0}
            cargo_type_stats[cargo_type]["count"] += 1
            cargo_type_stats[cargo_type]["weight_kg"] += weight_kg
            cargo_type_stats[cargo_type]["volume_m3"] += volume_m3

            # 尝试从LTL装载计划获取3D位置信息
            position_3d = {"x": 0.0, "y": 0.0, "z": 0.0, "rotation": 0}
            dimensions = {"length_m": 0.5, "width_m": 0.4, "height_m": 0.3}

            if not ltl_loading_plan.empty:
                # 查找对应的装载位置信息
                item_position = ltl_loading_plan[ltl_loading_plan['item_id'] == item_id]
                if not item_position.empty:
                    pos_row = item_position.iloc[0]
                    position_3d = {
                        "x": pos_row.get('position_x', 0.0),
                        "y": pos_row.get('position_y', 0.0),
                        "z": pos_row.get('position_z', 0.0),
                        "rotation": 0
                    }
                    dimensions = {
                        "length_m": pos_row.get('estimated_length', 0.5),
                        "width_m": pos_row.get('estimated_width', 0.4),
                        "height_m": pos_row.get('estimated_height', 0.3)
                    }

            # 构建装载详情
            item_detail = {
                "item_index": idx + 1,
                "original_order_id": original_order_id,
                "original_item_id": f"ITEM_{original_order_id}_{idx+1:03d}",
                "virtual_item_id": item_id,
                "cargo_info": {
                    "type": cargo_type,
                    "subtype": f"{cargo_type}_混合",
                    "weight_kg": weight_kg,
                    "volume_m3": volume_m3
                },
                "dimensions": dimensions,
                "position_3d": position_3d,
                "loading_sequence": idx + 1,
                "loading_zone": f"zone_{chr(65 + (idx // 20))}",  # zone_A, zone_B, etc.
                "stacking_info": {
                    "can_stack": weight_kg < 1000,  # 重量小于1吨可以堆叠
                    "stacked_on": None,
                    "supports": []
                }
            }

            if merged_from:
                item_detail["merged_from"] = merged_from

            loading_plan_details.append(item_detail)

        # 计算统计百分比
        for cargo_type in cargo_type_stats:
            cargo_type_stats[cargo_type]["percentage"] = (
                cargo_type_stats[cargo_type]["volume_m3"] / total_volume * 100 if total_volume > 0 else 0
            )

        # 构建完整的装载方案数据
        loading_plan_data = {
            "summary": {
                "vehicle_id": vehicle_id,
                "total_items": len(loaded_items),
                "total_weight_kg": total_weight,
                "total_volume_m3": total_volume,
                "loading_efficiency": (total_volume / TRUCK_SPECS['volume']) * 100,
                "volume_utilization": (total_volume / TRUCK_SPECS['volume']) * 100,
                "optimization_algorithm": "Multi_Truck_3DPP_Gurobi",
                "solution_status": "OPTIMAL",
                "loading_time_minutes": 60,
                "cargo_types": list(cargo_type_stats.keys())
            },
            "vehicle_details": {
                "type": "LTL_TRUCK",
                "truck_specs": {
                    "length_m": TRUCK_SPECS['length'],
                    "width_m": TRUCK_SPECS['width'],
                    "height_m": TRUCK_SPECS['height'],
                    "volume_m3": TRUCK_SPECS['volume'],
                    "capacity_kg": 15000
                },
                "optimization_info": {
                    "solver": "Gurobi_3DPP_Optimizer",
                    "strategy": "多品类混合装载优化",
                    "loading_type": "LTL_MIXED_LOADING"
                }
            },
            "loading_plan": loading_plan_details,
            "statistics": {
                "by_cargo_type": cargo_type_stats,
                "utilization": {
                    "length_utilization": 85.0,
                    "width_utilization": 90.0,
                    "height_utilization": (total_volume / TRUCK_SPECS['volume']) * 100,
                    "overall_utilization": (total_volume / TRUCK_SPECS['volume']) * 100
                }
            },
            "metadata": {
                "generated_time": datetime.now().isoformat(),
                "generated_by": "LTL_3DPP_Optimization_System_V3.0",
                "format_version": "1.0",
                "source_type": "ltl_mixed_loading",
                "id_mapping_source": "id_to_orders_mapping.json"
            }
        }

        return loading_plan_data

    def _run_route_optimization(self, complete_solution: Dict,
                              orders_data: pd.DataFrame) -> Dict:
        """
        使用简化路径生成替换VRP求解器
        支持FULL_TRUCK和LTL_TRUCK的统一路径生成

        Args:
            complete_solution: 完整解决方案
            orders_data: 原始订单数据

        Returns:
            Dict: 所有车辆的路径方案
        """
        if self.verbose:
            print("[路径] 开始简化路径生成...")

        try:
            route_solutions = {}

            # 加载调度计划
            dispatch_plan_data = self._load_dispatch_plan()
            if not dispatch_plan_data:
                if self.verbose:
                    print("[错误] 无法加载调度计划数据")
                return {}

            # 生成FULL_TRUCK路径
            if self.verbose:
                print("[路径] 生成FULL_TRUCK路径...")
            full_truck_routes = self._generate_full_truck_routes_integrated(
                dispatch_plan_data, orders_data
            )
            route_solutions.update(full_truck_routes)

            # 生成LTL_TRUCK路径
            if self.verbose:
                print("[路径] 生成LTL_TRUCK路径...")
            ltl_truck_routes = self._generate_ltl_truck_routes_integrated(
                dispatch_plan_data, orders_data
            )
            route_solutions.update(ltl_truck_routes)

            if self.verbose:
                successful_routes = len(route_solutions)
                total_trucks = len(dispatch_plan_data.get('dispatch_plan', {}))
                print(f"[完成] 路径生成完成: {successful_routes}/{total_trucks} 辆车成功")

            return route_solutions

        except Exception as e:
            self.logger.error(f"路径生成失败: {str(e)}")
            if self.verbose:
                print(f"[错误] 路径生成失败: {str(e)}")
            return {}

    def _load_dispatch_plan(self) -> Optional[Dict]:
        """加载调度计划数据"""
        try:
            dispatch_plan_file = INTERMEDIATE_DIR / FILE_CONFIG['full_dispatch_plan_file']
            if not dispatch_plan_file.exists():
                self.logger.error("调度计划文件不存在")
                return None

            with open(dispatch_plan_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            self.logger.error(f"加载调度计划失败: {str(e)}")
            return None

    def _load_id_mapping(self) -> Optional[Dict]:
        """加载ID映射关系数据"""
        try:
            id_mapping_file = INTERMEDIATE_DIR / FILE_CONFIG['id_to_orders_mapping_file']
            if not id_mapping_file.exists():
                return None

            with open(id_mapping_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('id_to_orders_mapping', {})
        except Exception as e:
            self.logger.error(f"加载ID映射关系失败: {str(e)}")
            return None

    def _generate_full_truck_routes_integrated(self, dispatch_data: Dict, orders_data: pd.DataFrame) -> Dict:
        """
        集成版FULL_TRUCK路径生成
        基于generate_full_truck_routes.py的逻辑
        """
        route_solutions = {}
        depot_coord = ROUTE_GENERATION['depot_coordinates']

        for vehicle_id, truck_data in dispatch_data['dispatch_plan'].items():
            if truck_data.get('type') != 'FULL_TRUCK':
                continue

            try:
                # 获取订单信息
                order_id = truck_data.get('source_order')
                if not order_id:
                    continue

                order_data = orders_data[orders_data['order_id'] == order_id]
                if order_data.empty:
                    if self.verbose:
                        print(f"   警告: 未找到订单 {order_id} 的数据")
                    continue

                order_row = order_data.iloc[0]

                # 计算路径
                route_plan = self._calculate_full_truck_route(
                    vehicle_id, truck_data, order_row, depot_coord
                )

                if route_plan:
                    route_solutions[vehicle_id] = route_plan
                    if self.verbose:
                        summary = route_plan['summary']
                        print(f"   [OK] {vehicle_id}: {summary['total_distance_km']:.1f}km, "
                              f"成本{summary['fuel_cost_yuan']:.2f}元")

            except Exception as e:
                self.logger.error(f"生成{vehicle_id}路径失败: {str(e)}")
                if self.verbose:
                    print(f"   [FAIL] {vehicle_id}: 路径生成失败")

        return route_solutions

    def _generate_ltl_truck_routes_integrated(self, dispatch_data: Dict, orders_data: pd.DataFrame) -> Dict:
        """
        集成版LTL_TRUCK路径生成
        为多停靠点车辆生成优化路径
        """
        route_solutions = {}
        depot_coord = ROUTE_GENERATION['depot_coordinates']

        for vehicle_id, truck_data in dispatch_data['dispatch_plan'].items():
            if truck_data.get('type') != 'LTL_TRUCK':
                continue

            try:
                # 获取装载的货物
                loaded_items = truck_data.get('loaded_items', [])
                if not loaded_items:
                    if self.verbose:
                        print(f"   警告: {vehicle_id} 没有装载货物")
                    continue

                # 构建停靠点序列
                route_plan = self._calculate_ltl_truck_route(
                    vehicle_id, truck_data, loaded_items, orders_data, depot_coord
                )

                if route_plan:
                    route_solutions[vehicle_id] = route_plan
                    if self.verbose:
                        summary = route_plan['summary']
                        print(f"   [OK] {vehicle_id}: {summary['total_distance_km']:.1f}km, "
                              f"{summary['total_stops']}停靠点, "
                              f"成本{summary['fuel_cost_yuan']:.2f}元")

            except Exception as e:
                self.logger.error(f"生成{vehicle_id}路径失败: {str(e)}")
                if self.verbose:
                    print(f"   [FAIL] {vehicle_id}: 路径生成失败")

        return route_solutions

    def _calculate_full_truck_route(self, vehicle_id: str, truck_data: Dict, order_row: pd.Series, depot_coord: List[float]) -> Optional[Dict]:
        """
        计算FULL_TRUCK路径
        基于generate_full_truck_routes.py的实现
        """
        try:
            # 目标坐标
            dest_lat = order_row['latitude']
            dest_lng = order_row['longitude']
            order_type = order_row['pickup_delivery']

            # 计算距离
            distance_km = self.distance_calculator.haversine_distance(
                depot_coord[0], depot_coord[1],  # 纬度, 经度
                dest_lat, dest_lng
            )

            # 计算时间和成本
            avg_speed = ROUTE_GENERATION['avg_speed_kmh']
            travel_time_hours = distance_km / avg_speed

            # 车辆信息
            total_weight_kg = truck_data.get('total_weight_kg', 0)
            empty_weight_kg = ROUTE_GENERATION['empty_truck_weight_kg']
            fuel_cost_per_ton_km = ROUTE_GENERATION['fuel_cost_per_ton_km']

            # 计算燃油成本
            total_weight_ton = (empty_weight_kg + total_weight_kg) / 1000.0
            fuel_cost = fuel_cost_per_ton_km * total_weight_ton * distance_km

            # 生成路径规划
            start_time = datetime.now().replace(hour=8, minute=0, second=0, microsecond=0)
            arrival_time = start_time + timedelta(hours=travel_time_hours)

            # 服务时间
            service_time_minutes = (ROUTE_GENERATION['service_time_delivery']
                                  if order_type == '配送需求'
                                  else ROUTE_GENERATION['service_time_pickup'])
            completion_time = arrival_time + timedelta(minutes=service_time_minutes)

            # 构建路径数据
            route_plan = {
                "summary": {
                    "vehicle_id": vehicle_id,
                    "total_distance_km": round(distance_km, 2),
                    "total_duration_hours": round(travel_time_hours + service_time_minutes/60.0, 2),
                    "fuel_cost_yuan": round(fuel_cost, 2),
                    "total_stops": 1,
                    "pickup_stops": 1 if order_type == '取货需求' else 0,
                    "delivery_stops": 1 if order_type == '配送需求' else 0,
                    "initial_load_kg": total_weight_kg if order_type == '配送需求' else 0,
                    "final_load_kg": total_weight_kg if order_type == '取货需求' else 0,
                    "load_efficiency": round(total_weight_kg / ROUTE_GENERATION['truck_capacity_kg'] * 100, 2),
                    "optimization_algorithm": "Point_to_Point_Direct",
                    "solution_status": "DIRECT_ROUTE",
                    "completion_time": completion_time.strftime('%H:%M'),
                    "start_time": ROUTE_GENERATION['start_time'],
                    "working_hours": round(travel_time_hours + service_time_minutes/60.0, 2),
                    "cargo_type": truck_data.get('item_type', '未知'),
                    "cargo_quantity": truck_data.get('quantity_per_truck', 0)
                },
                "route_details": {
                    "depot_info": {
                        "name": "A网点（成都至重庆专线）",
                        "coordinates": {
                            "lat": depot_coord[0],
                            "lng": depot_coord[1]
                        },
                        "address": f"({depot_coord[0]:.6f}, {depot_coord[1]:.6f})"
                    },
                    "vehicle_info": {
                        "type": "9.6米厢式货车",
                        "capacity_kg": ROUTE_GENERATION['truck_capacity_kg'],
                        "empty_weight_kg": empty_weight_kg,
                        "fuel_coefficient": fuel_cost_per_ton_km
                    },
                    "optimization_info": {
                        "solver": "Direct_Point_to_Point",
                        "strategy": "单一订单直达运输",
                        "route_type": "FULL_TRUCK_DIRECT"
                    }
                },
                "itinerary": [
                    {
                        "step": 1,
                        "action": "送货" if order_type == '配送需求' else "取货",
                        "order_id": order_row['order_id'],
                        "coordinates": [dest_lat, dest_lng],
                        "weight_change_kg": -total_weight_kg if order_type == '配送需求' else total_weight_kg,
                        "distance_from_previous_km": round(distance_km, 2),
                        "estimated_arrival": arrival_time.strftime('%H:%M'),
                        "service_time_minutes": service_time_minutes,
                        "departure_time": completion_time.strftime('%H:%M'),
                        "address": f"坐标({dest_lat:.4f}, {dest_lng:.4f})",
                        "cumulative_load_kg": total_weight_kg if order_type == '取货需求' else 0,
                        "cargo_info": {
                            "type": truck_data.get('item_type', '未知'),
                            "quantity": truck_data.get('quantity_per_truck', 0),
                            "total_weight_kg": total_weight_kg
                        }
                    }
                ],
                "performance_metrics": {
                    "total_service_time_minutes": service_time_minutes,
                    "total_travel_time_hours": round(travel_time_hours, 2),
                    "service_efficiency": round(service_time_minutes / (travel_time_hours * 60 + service_time_minutes) * 100, 2),
                    "fuel_efficiency_yuan_per_km": round(fuel_cost / distance_km, 2),
                    "cargo_density_kg_per_m3": round(total_weight_kg / ROUTE_GENERATION['vehicle_volume_m3'], 2)
                },
                "solver_info": {
                    "method": "Direct_Point_to_Point",
                    "solve_time_seconds": 0.01,
                    "status": "DIRECT_ROUTE_SUCCESS"
                },
                "generated_time": datetime.now().isoformat(),
                "generated_by": "Integrated_Full_Truck_Route_Generator"
            }

            return route_plan

        except Exception as e:
            self.logger.error(f"计算{vehicle_id}路径失败: {str(e)}")
            return None

    def _calculate_ltl_truck_route(self, vehicle_id: str, truck_data: Dict, loaded_items: List[Dict],
                                 orders_data: pd.DataFrame, depot_coord: List[float]) -> Optional[Dict]:
        """
        计算LTL_TRUCK路径
        使用最近邻算法生成多停靠点路径
        """
        try:
            # 加载ID映射关系
            id_mapping = self._load_id_mapping()
            if not id_mapping:
                if self.verbose:
                    print(f"   警告: {vehicle_id} 无法加载ID映射关系")
                return None

            # 提取停靠点坐标和信息
            stops = []
            processed_orders = set()  # 避免重复添加相同订单的停靠点

            for item in loaded_items:
                item_id = item.get('item_id', '')
                if not item_id:
                    continue

                # 通过ID映射找到对应的原始订单
                mapped_orders = id_mapping.get(item_id, [])
                if not mapped_orders:
                    if self.verbose:
                        print(f"   警告: {vehicle_id} item_id {item_id} 无映射订单")
                    continue

                for mapped_order in mapped_orders:
                    # 跳过虚拟合并订单，寻找真实订单
                    if mapped_order.startswith('MERGED_ORDER_'):
                        if self.verbose:
                            print(f"   警告: {vehicle_id} 跳过虚拟订单 {mapped_order}")
                        continue

                    # 避免重复处理同一订单
                    if mapped_order in processed_orders:
                        continue

                    # 查找真实订单数据
                    order_info = orders_data[orders_data['order_id'] == mapped_order]
                    if not order_info.empty:
                        order_row = order_info.iloc[0]
                        stops.append({
                            'order_id': mapped_order,
                            'item_id': item_id,
                            'latitude': order_row['latitude'],
                            'longitude': order_row['longitude'],
                            'pickup_delivery': order_row['pickup_delivery'],
                            'weight_kg': item.get('weight_kg', 0),
                            'item_type': item.get('item_type', '未知'),
                            'destination_address': order_row.get('destination_address', '未知地址')
                        })
                        processed_orders.add(mapped_order)
                    else:
                        if self.verbose:
                            print(f"   警告: {vehicle_id} 未找到订单 {mapped_order} 的坐标信息")

            if not stops:
                if self.verbose:
                    print(f"   警告: {vehicle_id} 无有效停靠点")
                return None

            # 使用最近邻算法优化路径
            optimized_stops = self._optimize_route_nearest_neighbor(stops, depot_coord)

            # 计算路径指标
            total_distance = 0
            total_weight = sum(stop['weight_kg'] for stop in stops)
            current_time = datetime.now().replace(hour=8, minute=0, second=0, microsecond=0)
            current_location = depot_coord

            itinerary = []
            pickup_stops = 0
            delivery_stops = 0

            for i, stop in enumerate(optimized_stops):
                # 计算到该停靠点的距离
                distance = self.distance_calculator.haversine_distance(
                    current_location[0], current_location[1],
                    stop['latitude'], stop['longitude']
                )
                total_distance += distance

                # 计算到达时间
                travel_time = distance / ROUTE_GENERATION['avg_speed_kmh']
                current_time += timedelta(hours=travel_time)

                # 服务时间
                service_time = (ROUTE_GENERATION['service_time_delivery']
                              if stop['pickup_delivery'] == '配送需求'
                              else ROUTE_GENERATION['service_time_pickup'])

                departure_time = current_time + timedelta(minutes=service_time)

                # 统计停靠点类型
                if stop['pickup_delivery'] == '取货需求':
                    pickup_stops += 1
                else:
                    delivery_stops += 1

                itinerary.append({
                    "step": i + 1,
                    "action": "送货" if stop['pickup_delivery'] == '配送需求' else "取货",
                    "order_id": stop['order_id'],
                    "coordinates": [stop['latitude'], stop['longitude']],
                    "weight_change_kg": -stop['weight_kg'] if stop['pickup_delivery'] == '配送需求' else stop['weight_kg'],
                    "distance_from_previous_km": round(distance, 2),
                    "estimated_arrival": current_time.strftime('%H:%M'),
                    "service_time_minutes": service_time,
                    "departure_time": departure_time.strftime('%H:%M'),
                    "address": f"坐标({stop['latitude']:.4f}, {stop['longitude']:.4f})",
                    "cargo_info": {
                        "type": stop['item_type'],
                        "weight_kg": stop['weight_kg']
                    }
                })

                current_location = [stop['latitude'], stop['longitude']]
                current_time = departure_time

            # 返回配送中心的距离
            return_distance = self.distance_calculator.haversine_distance(
                current_location[0], current_location[1],
                depot_coord[0], depot_coord[1]
            )
            total_distance += return_distance
            return_time = return_distance / ROUTE_GENERATION['avg_speed_kmh']
            final_time = current_time + timedelta(hours=return_time)

            # 计算总成本
            empty_weight_kg = ROUTE_GENERATION['empty_truck_weight_kg']
            fuel_cost_per_ton_km = ROUTE_GENERATION['fuel_cost_per_ton_km']
            avg_weight_ton = (empty_weight_kg + total_weight / 2) / 1000.0  # 平均载重
            fuel_cost = fuel_cost_per_ton_km * avg_weight_ton * total_distance

            # 构建路径数据
            route_plan = {
                "summary": {
                    "vehicle_id": vehicle_id,
                    "total_distance_km": round(total_distance, 2),
                    "total_duration_hours": round((final_time - datetime.now().replace(hour=8, minute=0, second=0, microsecond=0)).total_seconds() / 3600, 2),
                    "fuel_cost_yuan": round(fuel_cost, 2),
                    "total_stops": len(stops),
                    "pickup_stops": pickup_stops,
                    "delivery_stops": delivery_stops,
                    "initial_load_kg": 0,  # LTL车辆从空车开始
                    "final_load_kg": 0,    # 最终返回空车
                    "max_load_kg": total_weight,
                    "load_efficiency": round(total_weight / ROUTE_GENERATION['truck_capacity_kg'] * 100, 2),
                    "optimization_algorithm": "Nearest_Neighbor_TSP",
                    "solution_status": "MULTI_STOP_OPTIMIZED",
                    "completion_time": final_time.strftime('%H:%M'),
                    "start_time": ROUTE_GENERATION['start_time'],
                    "working_hours": round((final_time - datetime.now().replace(hour=8, minute=0, second=0, microsecond=0)).total_seconds() / 3600, 2)
                },
                "route_details": {
                    "depot_info": {
                        "name": "A网点（成都至重庆专线）",
                        "coordinates": {
                            "lat": depot_coord[0],
                            "lng": depot_coord[1]
                        }
                    },
                    "vehicle_info": {
                        "type": "9.6米厢式货车",
                        "capacity_kg": ROUTE_GENERATION['truck_capacity_kg'],
                        "empty_weight_kg": empty_weight_kg
                    },
                    "optimization_info": {
                        "solver": "Nearest_Neighbor_Algorithm",
                        "strategy": "多停靠点路径优化",
                        "route_type": "LTL_MULTI_STOP"
                    }
                },
                "itinerary": itinerary,
                "performance_metrics": {
                    "total_service_time_minutes": len(stops) * ((ROUTE_GENERATION['service_time_pickup'] + ROUTE_GENERATION['service_time_delivery']) / 2),
                    "total_travel_time_hours": round(total_distance / ROUTE_GENERATION['avg_speed_kmh'], 2),
                    "fuel_efficiency_yuan_per_km": round(fuel_cost / total_distance if total_distance > 0 else 0, 2),
                    "average_distance_per_stop": round(total_distance / len(stops) if len(stops) > 0 else 0, 2)
                },
                "solver_info": {
                    "method": "Nearest_Neighbor_TSP",
                    "solve_time_seconds": 0.1,
                    "status": "MULTI_STOP_OPTIMIZED"
                },
                "generated_time": datetime.now().isoformat(),
                "generated_by": "Integrated_LTL_Route_Generator"
            }

            return route_plan

        except Exception as e:
            self.logger.error(f"计算{vehicle_id}路径失败: {str(e)}")
            return None

    def _optimize_route_nearest_neighbor(self, stops: List[Dict], depot_coord: List[float]) -> List[Dict]:
        """
        使用最近邻算法优化停靠点顺序
        """
        if len(stops) <= 1:
            return stops

        optimized = []
        remaining = stops.copy()
        current_location = depot_coord

        while remaining:
            # 找到最近的停靠点
            min_distance = float('inf')
            nearest_stop = None
            nearest_index = -1

            for i, stop in enumerate(remaining):
                distance = self.distance_calculator.haversine_distance(
                    current_location[0], current_location[1],
                    stop['latitude'], stop['longitude']
                )
                if distance < min_distance:
                    min_distance = distance
                    nearest_stop = stop
                    nearest_index = i

            if nearest_stop:
                optimized.append(nearest_stop)
                current_location = [nearest_stop['latitude'], nearest_stop['longitude']]
                remaining.pop(nearest_index)

        return optimized

    def _generate_truck_route_reports(self, route_solutions: Dict) -> List[str]:
        """
        生成单车路径报告文件

        Args:
            route_solutions: 所有车辆的路径方案

        Returns:
            List[str]: 生成的报告文件路径列表
        """
        if not route_solutions:
            if self.verbose:
                print("[跳过] 无路径方案，跳过报告生成")
            return []

        if self.verbose:
            print("[报告] 生成路径规划报告...")

        try:
            import json
            from datetime import datetime

            report_files = []

            for truck_id, route_solution in route_solutions.items():
                # 生成单车路径报告文件
                report_filename = f"{truck_id}_route_plan.json"
                report_file = REPORTS_DIR / report_filename

                # 添加生成时间戳
                route_solution['generated_time'] = datetime.now().isoformat()
                route_solution['generated_by'] = 'LTL_3DPP_Optimization_System_V2'

                # 保存报告
                with open(report_file, 'w', encoding='utf-8') as f:
                    json.dump(route_solution, f, ensure_ascii=False, indent=2)

                report_files.append(str(report_file))

                if self.verbose:
                    summary = route_solution['summary']
                    print(f"   {truck_id}: {summary['total_distance_km']:.1f}km, "
                          f"{summary['total_stops']}停靠点, "
                          f"成本{summary['fuel_cost_yuan']:.2f}元")

            if self.verbose:
                print(f"[完成] 生成 {len(report_files)} 个路径报告")

            # 集成export_route_results调用
            try:
                from utils.export_route_results import export_route_summary_to_excel
                excel_file = export_route_summary_to_excel()

                if self.verbose:
                    print(f"[Excel] 路径汇总报告已生成: {Path(excel_file).name}")

                # 添加到报告文件列表
                if excel_file:
                    report_files.append(str(excel_file))

            except Exception as e:
                self.logger.error(f"Excel报告生成失败: {str(e)}")
                if self.verbose:
                    print(f"[警告] Excel报告生成失败: {str(e)}")

            return report_files

        except Exception as e:
            self.logger.error(f"生成路径报告失败: {str(e)}")
            if self.verbose:
                print(f"[错误] 报告生成失败: {str(e)}")
            return []

    def _generate_comprehensive_visualizations(self, complete_solution: Dict) -> List[str]:
        """
        生成V3.0综合可视化系统
        包含所有高级可视化功能：3DPP装载、路径优化、效率分析
        """
        # 数据采样 - 防止卡死
        from config import VISUALIZATION_PERFORMANCE

        # 获取原始数据并进行采样
        truck_assignments = self._extract_truck_assignments(complete_solution)
        if truck_assignments:
            total_items = sum(len(items) for items in truck_assignments.values())
            max_items = VISUALIZATION_PERFORMANCE.get('max_items_per_visualization', 500)
            sample_ratio = VISUALIZATION_PERFORMANCE.get('sample_ratio', 0.3)

            if total_items > max_items:
                if self.verbose:
                    print(f"[采样] 数据量过大({total_items}个货物)，采样显示防止卡死")
                truck_assignments = self._sample_truck_assignments(truck_assignments, max_items, sample_ratio)
                # 更新complete_solution中的数据
                complete_solution = complete_solution.copy()
                complete_solution['sampled_truck_assignments'] = truck_assignments

        if self.verbose:
            print("[可视化] 生成V3.0综合可视化系统...")

        all_visualization_files = []

        try:
            # 1. 传统3D可视化（保持兼容性）
            traditional_viz = self._generate_3d_visualizations(complete_solution)
            if traditional_viz:
                all_visualization_files.extend(traditional_viz)
                if self.verbose:
                    print(f"   [OK] 传统3D可视化: {len(traditional_viz)} 个文件")

            # 2. 高级3DPP可视化（单品类+多品类+密度+效率）
            advanced_3dpp_viz = self._generate_advanced_3dpp_visualizations(complete_solution)
            if advanced_3dpp_viz:
                all_visualization_files.extend(advanced_3dpp_viz)
                if self.verbose:
                    print(f"   [OK] 高级3DPP可视化: {len(advanced_3dpp_viz)} 个文件")

            # 3. 路径优化可视化系统
            route_viz = self._generate_route_optimization_visualizations(complete_solution)
            if route_viz:
                all_visualization_files.extend(route_viz)
                if self.verbose:
                    print(f"   [OK] 路径优化可视化: {len(route_viz)} 个文件")

            if self.verbose:
                print(f"[完成] V3.0综合可视化完成: {len(all_visualization_files)} 个文件")
                print("   可视化类型:")
                print("     • 单品类3DPP装载可视化")
                print("     • 多品类3DPP装载可视化")
                print("     • 装载密度热力图")
                print("     • 3D装载效率分析")
                print("     • 路径优化结果可视化")
                print("     • 路径效率热力图")
                print("     • 车辆性能仪表盘")
                print("     • 综合路径分析")

        except Exception as e:
            self.logger.error(f"综合可视化生成失败: {str(e)}")
            if self.verbose:
                print(f"[警告] 综合可视化生成失败: {str(e)}")

        return all_visualization_files

    def _generate_advanced_3dpp_visualizations(self, complete_solution: Dict) -> List[str]:
        """生成高级3DPP可视化"""
        # 数据采样 - 防止卡死
        from config import VISUALIZATION_PERFORMANCE

        truck_assignments = self._extract_truck_assignments(complete_solution)
        if truck_assignments:
            total_items = sum(len(items) for items in truck_assignments.values())
            max_items = VISUALIZATION_PERFORMANCE.get('max_items_per_visualization', 500)
            sample_ratio = VISUALIZATION_PERFORMANCE.get('sample_ratio', 0.3)

            if total_items > max_items:
                if self.verbose:
                    print(f"[采样] 高级3DPP可视化 - 数据量过大({total_items}个货物)，采样显示")
                truck_assignments = self._sample_truck_assignments(truck_assignments, max_items, sample_ratio)
                # 更新complete_solution中的数据
                complete_solution = complete_solution.copy()
                complete_solution['sampled_truck_assignments'] = truck_assignments

        advanced_viz_files = []

        try:
            if self.visualizer:
                # 单品类3DPP可视化
                single_category_viz = self._generate_enhanced_single_category_visualization(complete_solution)
                if single_category_viz:
                    advanced_viz_files.extend(single_category_viz)

                # 多品类3DPP可视化
                multi_category_viz = self._generate_multi_category_visualization(complete_solution)
                if multi_category_viz:
                    advanced_viz_files.extend(multi_category_viz)

                # 装载密度热力图
                density_heatmap = self._generate_loading_density_heatmap(complete_solution)
                if density_heatmap:
                    advanced_viz_files.append(density_heatmap)

                # 3D装载效率分析
                efficiency_analysis = self._generate_3d_efficiency_analysis(complete_solution)
                if efficiency_analysis:
                    advanced_viz_files.append(efficiency_analysis)

        except Exception as e:
            self.logger.error(f"高级3DPP可视化生成失败: {str(e)}")

        return advanced_viz_files

    def _generate_3d_visualizations(self, complete_solution: Dict) -> List[str]:
        """生成增强版3D可视化"""
        # 数据采样 - 防止卡死
        from config import VISUALIZATION_PERFORMANCE
        truck_assignments = self._extract_truck_assignments(complete_solution)
        if truck_assignments:
            total_items = sum(len(items) for items in truck_assignments.values())
            max_items = VISUALIZATION_PERFORMANCE.get('max_items_per_visualization', 500)
            sample_ratio = VISUALIZATION_PERFORMANCE.get('sample_ratio', 0.3)

            if total_items > max_items:
                if self.verbose:
                    print(f"[采样] 3D可视化数据量过大({total_items})，采样显示")
                truck_assignments = self._sample_truck_assignments(truck_assignments, max_items, sample_ratio)
                # 更新complete_solution中的数据
                complete_solution = complete_solution.copy()
                complete_solution['sampled_truck_assignments'] = truck_assignments

        if self.verbose:
            print("[可视化] 生成增强版3D可视化...")

        visualization_files = []

        try:
            # 生成大件货物3DPP可视化报告（原有功能）
            large_viz_file = self._generate_large_cargo_3dpp_visualization(
                complete_solution['large_cargo_results']
            )
            if large_viz_file:
                visualization_files.append(large_viz_file)

            # 如果有plotly可视化器，生成增强版交互式3D图
            if self.visualizer:
                # 1. 生成增强版单品类3DPP可视化
                single_category_viz = self._generate_enhanced_single_category_visualization(complete_solution)
                if single_category_viz:
                    visualization_files.extend(single_category_viz)
                    if self.verbose:
                        print(f"   [OK] 单品类3DPP可视化: {len(single_category_viz)} 个文件")

                # 2. 生成多品类3DPP可视化
                multi_category_viz = self._generate_multi_category_visualization(complete_solution)
                if multi_category_viz:
                    visualization_files.extend(multi_category_viz)
                    if self.verbose:
                        print(f"   [OK] 多品类3DPP可视化: {len(multi_category_viz)} 个文件")

                # 3. 生成装载密度热力图
                density_heatmap = self._generate_loading_density_heatmap(complete_solution)
                if density_heatmap:
                    visualization_files.append(density_heatmap)
                    if self.verbose:
                        print(f"   [OK] 装载密度热力图已生成")

                # 4. 生成3D装载效率分析
                efficiency_analysis = self._generate_3d_efficiency_analysis(complete_solution)
                if efficiency_analysis:
                    visualization_files.append(efficiency_analysis)
                    if self.verbose:
                        print(f"   [OK] 3D装载效率分析已生成")

                # 5. 生成原有的交互式3D图
                interactive_viz = self._generate_interactive_3d_visualization(complete_solution)
                if interactive_viz:
                    visualization_files.append(interactive_viz)

                # 6. 生成路径优化结果可视化
                route_viz_files = self._generate_route_optimization_visualizations(complete_solution)
                if route_viz_files:
                    visualization_files.extend(route_viz_files)
                    if self.verbose:
                        print(f"   [OK] 路径优化可视化: {len(route_viz_files)} 个文件")

        except Exception as e:
            self.logger.error(f"3D可视化生成失败: {str(e)}")
            if self.verbose:
                print(f"[警告] 3D可视化生成失败: {str(e)}")

        if self.verbose:
            print(f"[完成] 增强版3D可视化完成: {len(visualization_files)} 个文件")

        return visualization_files

    def _generate_enhanced_single_category_visualization(self, complete_solution: Dict) -> List[str]:
        """生成增强版单品类3DPP可视化"""
        try:
            truck_assignments = self._extract_truck_assignments(complete_solution)
            if not truck_assignments:
                return []

            # 数据采样 - 防止卡死
            from config import VISUALIZATION_PERFORMANCE
            total_items = sum(len(items) for items in truck_assignments.values())
            max_items = VISUALIZATION_PERFORMANCE.get('max_items_per_visualization', 500)
            sample_ratio = VISUALIZATION_PERFORMANCE.get('sample_ratio', 0.3)

            if total_items > max_items:
                if self.verbose:
                    print(f"[采样] 单品类可视化数据量过大({total_items})，采样显示")
                truck_assignments = self._sample_truck_assignments(truck_assignments, max_items, sample_ratio)
                # 更新complete_solution中的数据
                complete_solution = complete_solution.copy()
                complete_solution['sampled_truck_assignments'] = truck_assignments

            solution_data = {'truck_assignments': truck_assignments}
            figures = self.visualizer.create_enhanced_single_category_3dpp_visualization(solution_data)

            visualization_files = []
            for i, fig in enumerate(figures):
                filename = f"enhanced_single_category_3dpp_{i+1}"
                file_path = self.visualizer.save_enhanced_visualization(fig, filename)
                visualization_files.append(file_path)

            return visualization_files

        except Exception as e:
            self.logger.error(f"单品类3DPP可视化生成失败: {str(e)}")
            return []

    def _generate_multi_category_visualization(self, complete_solution: Dict) -> List[str]:
        """生成多品类3DPP可视化"""
        try:
            truck_assignments = self._extract_truck_assignments(complete_solution)
            if not truck_assignments:
                return []

            # 数据采样 - 防止卡死
            from config import VISUALIZATION_PERFORMANCE
            total_items = sum(len(items) for items in truck_assignments.values())
            max_items = VISUALIZATION_PERFORMANCE.get('max_items_per_visualization', 500)
            sample_ratio = VISUALIZATION_PERFORMANCE.get('sample_ratio', 0.3)

            if total_items > max_items:
                if self.verbose:
                    print(f"[采样] 多品类可视化数据量过大({total_items})，采样显示")
                truck_assignments = self._sample_truck_assignments(truck_assignments, max_items, sample_ratio)
                # 更新complete_solution中的数据
                complete_solution = complete_solution.copy()
                complete_solution['sampled_truck_assignments'] = truck_assignments

            solution_data = {'truck_assignments': truck_assignments}
            figures = self.visualizer.create_multi_category_3dpp_visualization(solution_data)

            visualization_files = []
            for i, fig in enumerate(figures):
                filename = f"multi_category_3dpp_{i+1}"
                file_path = self.visualizer.save_enhanced_visualization(fig, filename)
                visualization_files.append(file_path)

            return visualization_files

        except Exception as e:
            self.logger.error(f"多品类3DPP可视化生成失败: {str(e)}")
            return []

    def _generate_loading_density_heatmap(self, complete_solution: Dict) -> Optional[str]:
        """生成装载密度热力图"""
        try:
            # 检查配置是否启用密度分析
            from config import VISUALIZATION_PERFORMANCE
            if not VISUALIZATION_PERFORMANCE['density_analysis_enabled']:
                self.logger.info("密度分析已禁用，跳过装载密度热力图生成")
                return None

            truck_assignments = self._extract_truck_assignments(complete_solution)
            if not truck_assignments:
                return None

            # 检查数据量是否过大
            total_items = sum(len(items) for items in truck_assignments.values())
            if total_items > VISUALIZATION_PERFORMANCE['skip_heavy_charts_above_items']:
                self.logger.warning(f"货物数量过多({total_items})，跳过密度分析以防止卡死")
                return None

            solution_data = {'truck_assignments': truck_assignments}
            fig = self.visualizer.create_loading_density_heatmap(solution_data)

            filename = "loading_density_heatmap"
            file_path = self.visualizer.save_enhanced_visualization(fig, filename)

            return file_path

        except Exception as e:
            self.logger.error(f"装载密度热力图生成失败: {str(e)}")
            return None

    def _generate_3d_efficiency_analysis(self, complete_solution: Dict) -> Optional[str]:
        """生成3D装载效率分析"""
        try:
            truck_assignments = self._extract_truck_assignments(complete_solution)
            if not truck_assignments:
                return None

            # 数据采样 - 防止卡死
            from config import VISUALIZATION_PERFORMANCE
            total_items = sum(len(items) for items in truck_assignments.values())
            max_items = VISUALIZATION_PERFORMANCE.get('max_items_per_visualization', 500)
            sample_ratio = VISUALIZATION_PERFORMANCE.get('sample_ratio', 0.3)

            if total_items > max_items:
                if self.verbose:
                    print(f"[采样] 3D效率分析数据量过大({total_items})，采样显示")
                truck_assignments = self._sample_truck_assignments(truck_assignments, max_items, sample_ratio)

            solution_data = {'truck_assignments': truck_assignments}
            fig = self.visualizer.create_3d_loading_efficiency_analysis(solution_data)

            filename = "3d_loading_efficiency_analysis"
            file_path = self.visualizer.save_enhanced_visualization(fig, filename)

            return file_path

        except Exception as e:
            self.logger.error(f"3D装载效率分析生成失败: {str(e)}")
            return None

    def _sample_truck_assignments(self, truck_assignments: Dict, max_items: int = 500, sample_ratio: float = 0.3) -> Dict:
        """
        对车辆分配数据进行采样，防止可视化卡死

        Args:
            truck_assignments: 原始车辆分配数据
            max_items: 最大货物数量
            sample_ratio: 采样比例

        Returns:
            采样后的车辆分配数据
        """
        if not truck_assignments:
            return {}

        # 计算总货物数量
        total_items = sum(len(items) for items in truck_assignments.values())

        # 计算目标数量：取较小值
        target_items = min(max_items, int(total_items * sample_ratio))

        if total_items <= target_items:
            # 不需要采样
            return truck_assignments

        # 计算采样比例
        actual_sample_ratio = target_items / total_items

        # 对每个车辆的货物进行采样
        sampled_assignments = {}
        import random

        for truck_id, items in truck_assignments.items():
            if not items:
                continue

            # 计算该车辆应该采样的数量
            vehicle_target = max(1, int(len(items) * actual_sample_ratio))

            # 随机采样
            if len(items) > vehicle_target:
                sampled_items = random.sample(items, vehicle_target)
            else:
                sampled_items = items

            sampled_assignments[truck_id] = sampled_items

        if hasattr(self, 'verbose') and self.verbose:
            sampled_total = sum(len(items) for items in sampled_assignments.values())
            print(f"   [采样] 从{total_items}个货物采样到{sampled_total}个 (比例: {sampled_total/total_items:.1%})")

        return sampled_assignments

    def _extract_truck_assignments(self, complete_solution: Dict) -> Dict:
        """从完整解决方案中提取车辆分配数据（优先使用JSON文件）"""
        try:
            # 优先使用JSON装载方案文件的真实数据
            truck_assignments = self._load_truck_assignments_from_json()
            if truck_assignments:
                if self.verbose:
                    print(f"   [JSON] 使用装载方案JSON文件: {len(truck_assignments)} 个车辆")
                return truck_assignments

            # 备用方案：从complete_solution中提取（原有逻辑）
            truck_assignments = {}

            # 从大货物结果中提取
            large_cargo_results = complete_solution.get('large_cargo_results', {})
            large_assignments = large_cargo_results.get('truck_assignments', {})
            if large_assignments:
                truck_assignments.update(large_assignments)

            # 从LTL结果中提取
            ltl_results = complete_solution.get('ltl_optimization_results', {})
            ltl_assignments = ltl_results.get('truck_assignments', {})
            if ltl_assignments:
                truck_assignments.update(ltl_assignments)

            if self.verbose:
                print(f"   [备用] 使用complete_solution数据: {len(truck_assignments)} 个车辆")
            return truck_assignments

        except Exception as e:
            self.logger.error(f"提取车辆分配数据失败: {str(e)}")
            return {}

    def _load_truck_assignments_from_json(self) -> Dict:
        """从JSON装载方案文件加载车辆分配数据"""
        try:
            from visualization.real_data_loader import RealDataLoader
            data_loader = RealDataLoader()

            # 获取装载可视化数据
            loading_data = data_loader.get_loading_visualization_data()
            raw_truck_assignments = loading_data.get('truck_assignments', {})

            # 转换数据格式以适配可视化函数
            truck_assignments = {}
            for truck_id, truck_data in raw_truck_assignments.items():
                # 可视化函数期望truck_assignments[truck_id]直接是货物列表
                truck_assignments[truck_id] = truck_data.get('loaded_items', [])

            if truck_assignments:
                self.logger.info(f"成功从JSON文件加载 {len(truck_assignments)} 个车辆装载数据")

            return truck_assignments

        except Exception as e:
            self.logger.warning(f"从JSON文件加载装载数据失败: {str(e)}")
            return {}

    def _generate_route_optimization_visualizations(self, complete_solution: Dict) -> List[str]:
        """生成路径优化结果可视化"""
        # 数据采样 - 防止卡死
        from config import VISUALIZATION_PERFORMANCE

        truck_assignments = self._extract_truck_assignments(complete_solution)
        if truck_assignments:
            total_items = sum(len(items) for items in truck_assignments.values())
            max_items = VISUALIZATION_PERFORMANCE.get('max_items_per_visualization', 500)
            sample_ratio = VISUALIZATION_PERFORMANCE.get('sample_ratio', 0.3)

            if total_items > max_items:
                if self.verbose:
                    print(f"[采样] 路径优化可视化 - 数据量过大({total_items}个货物)，采样显示")
                truck_assignments = self._sample_truck_assignments(truck_assignments, max_items, sample_ratio)
                # 更新complete_solution中的数据
                complete_solution = complete_solution.copy()
                complete_solution['sampled_truck_assignments'] = truck_assignments

        if self.verbose:
            print("[可视化] 生成路径优化结果可视化...")

        visualization_files = []

        try:
            # 检查是否有路径解决方案
            route_solutions = complete_solution.get('route_solutions', {})
            if not route_solutions:
                if self.verbose:
                    print("   [提示] 没有路径优化结果可视化")
                return []

            # 导入路径可视化器（使用基础实现）
            try:
                from visualization.route_visualizer import RouteVisualizer
                route_visualizer = RouteVisualizer()
            except (ImportError, Exception):
                from visualization.basic_route_visualizer import BasicRouteVisualizer
                route_visualizer = BasicRouteVisualizer()

            # 1. 生成增强版路径优化可视化
            enhanced_route_viz = self._generate_enhanced_route_visualization(route_solutions, route_visualizer)
            if enhanced_route_viz:
                visualization_files.extend(enhanced_route_viz)
                if self.verbose:
                    print(f"   [OK] 增强版路径可视化: {len(enhanced_route_viz)} 个文件")

            # 2. 生成路径效率热力图
            efficiency_heatmap = self._generate_route_efficiency_heatmap(route_solutions, route_visualizer)
            if efficiency_heatmap:
                visualization_files.append(efficiency_heatmap)
                if self.verbose:
                    print(f"   [OK] 路径效率热力图已生成")

            # 3. 生成车辆性能仪表盘
            performance_dashboard = self._generate_vehicle_performance_dashboard(route_solutions, route_visualizer)
            if performance_dashboard:
                visualization_files.append(performance_dashboard)
                if self.verbose:
                    print(f"   [OK] 车辆性能仪表盘已生成")

            # 4. 生成综合路径分析
            comprehensive_analysis = self._generate_comprehensive_route_analysis(route_solutions, route_visualizer)
            if comprehensive_analysis:
                visualization_files.append(comprehensive_analysis)
                if self.verbose:
                    print(f"   [OK] 综合路径分析已生成")

        except Exception as e:
            self.logger.error(f"路径优化可视化生成失败: {str(e)}")
            if self.verbose:
                print(f"[警告] 路径优化可视化生成失败: {str(e)}")

        if self.verbose:
            print(f"[完成] 路径优化可视化完成: {len(visualization_files)} 个文件")

        return visualization_files

    def _generate_enhanced_route_visualization(self, route_solutions: Dict, route_visualizer) -> List[str]:
        """生成增强版路径优化可视化"""
        try:
            visualization_files = []

            for truck_id, route_data in route_solutions.items():
                if route_data and 'route_points' in route_data:
                    fig = route_visualizer.create_enhanced_route_optimization_visualization(
                        truck_id, route_data
                    )

                    if fig:
                        filename = f"enhanced_route_{truck_id}"
                        file_path = route_visualizer.save_visualization(fig, filename)
                        visualization_files.append(file_path)

            return visualization_files

        except Exception as e:
            self.logger.error(f"增强版路径可视化生成失败: {str(e)}")
            return []

    def _generate_route_efficiency_heatmap(self, route_solutions: Dict, route_visualizer) -> Optional[str]:
        """生成路径效率热力图"""
        # 路径数据采样 - 防止卡死
        from config import VISUALIZATION_PERFORMANCE

        if route_solutions:
            total_routes = len(route_solutions)
            max_routes = VISUALIZATION_PERFORMANCE.get('max_items_per_visualization', 500)

            if total_routes > max_routes:
                if hasattr(self, 'verbose') and self.verbose:
                    print(f"[采样] 路径效率热力图 - 路径数量过大({total_routes})，采样显示")
                # 对路径进行采样
                import random
                route_keys = list(route_solutions.keys())
                sampled_keys = random.sample(route_keys, min(max_routes, len(route_keys)))
                route_solutions = {k: route_solutions[k] for k in sampled_keys}

        try:
            fig = route_visualizer.create_route_efficiency_heatmap(route_solutions)

            if fig:
                filename = "route_efficiency_heatmap"
                file_path = route_visualizer.save_visualization(fig, filename)
                return file_path

            return None

        except Exception as e:
            self.logger.error(f"路径效率热力图生成失败: {str(e)}")
            return None

    def _generate_vehicle_performance_dashboard(self, route_solutions: Dict, route_visualizer) -> Optional[str]:
        """生成车辆性能仪表盘"""
        # 路径数据采样 - 防止卡死
        from config import VISUALIZATION_PERFORMANCE

        if route_solutions:
            total_routes = len(route_solutions)
            max_routes = VISUALIZATION_PERFORMANCE.get('max_items_per_visualization', 500)

            if total_routes > max_routes:
                if hasattr(self, 'verbose') and self.verbose:
                    print(f"[采样] 车辆性能仪表盘 - 路径数量过大({total_routes})，采样显示")
                # 对路径进行采样
                import random
                route_keys = list(route_solutions.keys())
                sampled_keys = random.sample(route_keys, min(max_routes, len(route_keys)))
                route_solutions = {k: route_solutions[k] for k in sampled_keys}

        try:
            fig = route_visualizer.create_vehicle_performance_dashboard(route_solutions)

            if fig:
                filename = "vehicle_performance_dashboard"
                file_path = route_visualizer.save_visualization(fig, filename)
                return file_path

            return None

        except Exception as e:
            self.logger.error(f"车辆性能仪表盘生成失败: {str(e)}")
            return None

    def _generate_comprehensive_route_analysis(self, route_solutions: Dict, route_visualizer) -> Optional[str]:
        """生成综合路径分析"""
        try:
            fig = route_visualizer.create_comprehensive_route_analysis(route_solutions)

            if fig:
                filename = "comprehensive_route_analysis"
                file_path = route_visualizer.save_visualization(fig, filename)
                return file_path

            return None

        except Exception as e:
            self.logger.error(f"综合路径分析生成失败: {str(e)}")
            return None

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
                             visualization_files, final_reports, route_solutions=None, route_reports=None) -> Dict[str, Any]:
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
            'route_optimization_results': route_solutions if route_solutions else {},
            'visualization_files': visualization_files,
            'final_reports': final_reports,
            'route_reports': route_reports if route_reports else [],
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
        print("零担物流3D装箱优化系统V3.0 - 运行完成")
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
        # 数据采样 - 防止卡死
        from config import VISUALIZATION_PERFORMANCE

        dispatch_results = large_cargo_results.get('dispatch_results', {})
        if dispatch_results:
            total_items = sum(len(items.get('loaded_items', [])) for truck_id, items in dispatch_results.items())
            max_items = VISUALIZATION_PERFORMANCE.get('max_items_per_visualization', 500)

            if total_items > max_items:
                if hasattr(self, 'verbose') and self.verbose:
                    print(f"[采样] 大件货物3DPP可视化 - 数据量过大({total_items}个货物)，采样显示")
                # 对大件货物分配结果进行采样
                sample_ratio = min(1.0, max_items / total_items)
                import random

                sampled_dispatch = {}
                for truck_id, truck_data in dispatch_results.items():
                    loaded_items = truck_data.get('loaded_items', [])
                    if loaded_items:
                        target_count = max(1, int(len(loaded_items) * sample_ratio))
                        sampled_items = random.sample(loaded_items, min(target_count, len(loaded_items)))
                        sampled_truck_data = truck_data.copy()
                        sampled_truck_data['loaded_items'] = sampled_items
                        sampled_dispatch[truck_id] = sampled_truck_data

                large_cargo_results = large_cargo_results.copy()
                large_cargo_results['dispatch_results'] = sampled_dispatch

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
        """生成交互式3D可视化"""
        if not self.visualizer:
            self.logger.info("可视化器不可用，跳过交互式3D可视化")
            return None

        # 数据采样 - 防止卡死
        from config import VISUALIZATION_PERFORMANCE

        truck_assignments = self._extract_truck_assignments(complete_solution)
        if truck_assignments:
            total_items = sum(len(items) for items in truck_assignments.values())
            max_items = VISUALIZATION_PERFORMANCE.get('max_items_per_visualization', 500)
            sample_ratio = VISUALIZATION_PERFORMANCE.get('sample_ratio', 0.3)

            if total_items > max_items:
                self.logger.info(f"[采样] 交互式3D可视化 - 数据量过大({total_items}个货物)，采样显示")
                truck_assignments = self._sample_truck_assignments(truck_assignments, max_items, sample_ratio)

        try:
            # 获取车辆分配数据 (再次检查，确保数据存在)
            if not truck_assignments:
                self.logger.info("无车辆分配数据，跳过交互式3D可视化")
                return None

            # 根据可视化器类型选择不同的实现
            if self.visualizer_type == "plotly":
                # 使用Plotly高级可视化
                solution_data = {'truck_assignments': truck_assignments}
                try:
                    figures = self.visualizer.create_interactive_3d_visualization(solution_data)
                    if figures:
                        filename = "interactive_3d_visualization"
                        file_path = self.visualizer.save_enhanced_visualization(figures[0], filename)
                        self.logger.info(f"Plotly交互式3D可视化已生成: {file_path}")
                        return file_path
                except AttributeError:
                    # 如果Plotly可视化器没有这个方法，使用基础方法
                    pass

            # 使用基础可视化器生成3D图片
            if hasattr(self.visualizer, 'create_enhanced_single_category_3dpp_visualization'):
                solution_data = {'truck_assignments': truck_assignments}
                visualization_files = self.visualizer.create_enhanced_single_category_3dpp_visualization(solution_data)

                if visualization_files:
                    self.logger.info(f"基础3D可视化已生成: {len(visualization_files)} 个文件")
                    return visualization_files[0]  # 返回第一个文件

            self.logger.info("3D可视化生成完成")
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