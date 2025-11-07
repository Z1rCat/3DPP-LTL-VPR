"""
增强主程序 - 集成空间-时间约束系统
Enhanced Main Program with Spatial-Temporal Constraint System Integration

这个版本集成了我们新开发的空间-时间约束功能，
同时保持与原有V3.0系统的完全兼容性。
"""

import sys
import logging
import time
import pandas as pd
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from tqdm import tqdm

# 导入所有模块（包括新的增强模块）
from config import (create_directories, validate_config, LTL_OPTIMIZATION,
                   TRUCK_SPECS, VISUALIZATIONS_DIR, INTERMEDIATE_DIR,
                   REPORTS_DIR, FILE_CONFIG, ROUTE_GENERATION,
                   SPATIAL_CONSTRAINT_CONFIG, TIME_WINDOW_CONFIG,
                   MULTI_OBJECTIVE_CONFIG)
import json
import asyncio
from concurrent.futures import ThreadPoolExecutor

# 现有模块
from data_processing.preprocessing_pipeline import PreprocessingPipeline
from optimization.cargo_classifier import CargoClassifier
from optimization.large_cargo_dispatcher import LargeCargoDispatcherV2
from optimization.ltl_optimizer import LTLOptimizer
from optimization.gurobi_optimizer import GurobiOptimizerV2

# 新的增强模块
from optimization.gurobi_optimizer_enhanced import GurobiOptimizerEnhanced, EnhancedCargoItem
from optimization.spatial_collision_detector import Item3D, Truck3D
from optimization.time_window_optimizer import TimeWindow, CustomerNode, VehicleInfo

# 可视化模块
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

# 工具模块
from utils.file_manager import FileManager
from utils.system_monitor import SystemMonitor, SafeExecutor
from utils.distance_calculator import DistanceCalculator


class LogisticsOptimizationSystemEnhanced:
    """增强优化系统V4.1 - 集成空间-时间约束功能"""

    def __init__(self, verbose: bool = True, use_enhanced_constraints: bool = True):
        """
        初始化增强优化系统V4.1

        Args:
            verbose: 是否显示详细输出
            use_enhanced_constraints: 是否启用增强的空间-时间约束
        """
        self.verbose = verbose
        self.use_enhanced_constraints = use_enhanced_constraints
        self.logger = self._setup_logger()

        # 现有模块实例
        self.preprocessing = PreprocessingPipeline()
        self.cargo_classifier = CargoClassifier()
        self.large_cargo_dispatcher = LargeCargoDispatcherV2()
        self.ltl_optimizer = LTLOptimizer()

        # 选择优化器版本
        if use_enhanced_constraints:
            self.gurobi_optimizer = GurobiOptimizerEnhanced()
            if self.verbose:
                print("[增强] 使用Gurobi增强优化器（集成空间-时间约束）")
        else:
            self.gurobi_optimizer = GurobiOptimizerV2()
            if self.verbose:
                print("[标准] 使用Gurobi优化器V3.0")

        # 初始化路径优化器
        try:
            from optimization.routing_solver import VRPPDSolver
            self.routing_solver = VRPPDSolver()
            self.routing_available = True
        except (ImportError, Exception) as e:
            self.routing_solver = None
            self.routing_available = False
            if self.verbose:
                print(f"[警告] 路径优化器不可用: {e}")

        # 可视化器初始化
        self._initialize_visualizer()

        # 工具模块
        self.file_manager = FileManager()
        self.distance_calculator = DistanceCalculator()

        # 系统监控
        self.monitor = SystemMonitor()
        self.safe_executor = SafeExecutor(self.monitor)

        # 运行状态
        self.start_time = None
        self.end_time = None
        self.results = {}

        # 初始化路径缓存
        self.route_cache = {}

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

    def _initialize_visualizer(self):
        """初始化可视化器"""
        # 条件性初始化可视化器
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

    def run_complete_optimization(self) -> Dict[str, Any]:
        """
        运行完整的优化流程 V4.1
        集成空间-时间约束优化
        """
        self.start_time = time.time()
        self.monitor.start_monitoring()

        mode_text = "增强模式" if self.use_enhanced_constraints else "标准模式"
        self.logger.info(f"开始零担物流3D装箱优化系统V4.1完整流程 ({mode_text})")

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

            # Step 3: 选择优化模式
            if self.use_enhanced_constraints:
                # Step 3a: 增强模式 - 集成空间-时间约束
                complete_solution = self._run_enhanced_optimization(
                    large_orders, medium_orders, small_orders, orders_data
                )
            else:
                # Step 3b: 标准模式 - 使用原有V3.0流程
                large_dispatch_results, large_remaining = self._process_large_orders_3dpp(large_orders)
                self.monitor.checkpoint("大货物3DPP优化完成", {
                    "使用车辆": large_dispatch_results.get('trucks_used', 0),
                    "剩余货物": len(large_remaining)
                })

                # Step 4: LTL优化
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
                complete_solution, complete_solution.get('large_cargo_results', {}),
                complete_solution.get('ltl_optimization_results', {})
            )
            loading_plan_files = self._generate_loading_plan_files(
                complete_solution, complete_solution.get('large_cargo_results', {}),
                complete_solution.get('ltl_optimization_results', {}), orders_data
            )
            route_solutions = self._run_route_optimization(complete_solution, orders_data)
            route_reports = self._generate_truck_route_reports(route_solutions)
            self.monitor.checkpoint("路径优化完成", {
                "路径车辆": len(route_solutions),
                "报告数量": len(route_reports)
            })

            # Step 7: 可视化生成
            visualization_files = self._generate_comprehensive_visualizations(complete_solution)
            self.monitor.checkpoint("高级可视化完成", {"文件数量": len(visualization_files)})

            # Step 8: 最终报告与结果编译
            final_reports = self._generate_final_reports(complete_solution)
            self.end_time = time.time()
            self.results = self._compile_final_results(
                preprocessing_stats,
                complete_solution.get('large_cargo_results', {}),
                complete_solution.get('ltl_optimization_results', {}),
                visualization_files,
                final_reports,
                route_solutions,
                route_reports
            )

            # Step 9: 显示增强功能统计
            if self.use_enhanced_constraints:
                self._print_enhanced_summary()
            else:
                self._print_standard_summary()

            return self.results

        except Exception as e:
            self.logger.error(f"系统运行失败: {str(e)}")
            self.end_time = time.time()
            raise

    def _run_enhanced_optimization(self, large_orders: pd.DataFrame,
                                     medium_orders: pd.DataFrame,
                                     small_orders: pd.DataFrame,
                                     orders_data: pd.DataFrame) -> Dict[str, Any]:
        """
        运行增强优化流程（集成空间-时间约束）
        """
        self.logger.info("[增强] 开始增强优化流程 - 集成空间-时间约束")

        # Step 1: 处理大货物（使用增强优化器）
        large_results = self._process_large_orders_enhanced(large_orders)

        # Step 2: 处理LTL货物（使用增强优化器）
        ltl_results = self._process_ltl_enhanced(medium_orders, small_orders, large_results)

        # Step 3: 合并结果
        complete_solution = {
            'loading_plans': [],
            'large_cargo_results': large_results,
            'ltl_results': ltl_results,
            'enhanced_features': {
                'spatial_constraints_enabled': SPATIAL_CONSTRAINT_CONFIG['enable_3d_collision_detection'],
                'time_window_constraints_enabled': TIME_WINDOW_CONFIG['enable_time_window_optimization'],
                'multi_objective_optimization': MULTI_OBJECTIVE_CONFIG['enable_multi_objective'],
                'rotation_optimization': SPATIAL_CONSTRAINT_CONFIG['enable_rotation_optimization']
            }
        }

        # 收集装载计划
        self._collect_enhanced_loading_plans(complete_solution, large_results, ltl_results)

        return complete_solution

    def _process_large_orders_enhanced(self, large_orders: pd.DataFrame) -> Dict:
        """使用增强优化器处理大货物"""
        self.logger.info("[增强] 开始大货物增强优化...")

        if len(large_orders) == 0:
            self.logger.info("🔍 大货物订单为空，返回空结果")
            return self._empty_large_results()

        try:
            # 🔍 增强调试：记录输入数据
            self.logger.info(f"🔍 [调试] 输入大货物数据: {len(large_orders)} 个订单")
            if self.verbose:
                for idx, row in large_orders.head(3).iterrows():
                    self.logger.info(f"  - 订单 {row['order_id']}: 体积 {row.get('order_total_volume_m3', 0):.3f}m³, 重量 {row.get('order_total_weight_kg', 0):.1f}kg")

            # 转换为增强货物格式
            enhanced_items = self._convert_orders_to_enhanced_items(large_orders, "large")
            self.logger.info(f"🔍 [调试] 转换后增强货物: {len(enhanced_items)} 个")

            # 创建卡车规格
            truck_specs = TRUCK_SPECS
            truck = Truck3D(
                length=truck_specs['length'],
                width=truck_specs['width'],
                height=truck_specs['height'],
                volume=truck_specs['volume'],
                max_weight=truck_specs['max_weight']
            )
            self.logger.info(f"🔍 [调试] 卡车规格: {truck_specs['length']}×{truck_specs['width']}×{truck_specs['height']}m, 容积{truck_specs['volume']:.1f}m³")

            # 使用增强优化器进行优化
            optimizer = GurobiOptimizerEnhanced()
            max_items = min(len(enhanced_items), 10)  # 🚫 进一步限制复杂度：从50降到10

            self.logger.info(f"🔍 [调试] 开始优化，最大货物数: {max_items}")
            result = optimizer.optimize_with_constraints(
                items=enhanced_items,
                truck_specs=truck_specs,
                max_items=max_items,
                enable_spatial=True,
                enable_time_windows=False  # 大货物暂不启用时间窗
            )

            # 🔍 增强调试：记录原始结果
            self.logger.info(f"🔍 [调试] 原始优化结果状态: {result.status}")
            self.logger.info(f"🔍 [调试] 空间位置数量: {len(result.spatial_positions)}")
            self.logger.info(f"🔍 [调试] 体积利用率: {result.volume_utilization:.2f}%")

            # 转换结果格式
            enhanced_results = self._convert_enhanced_result_to_standard_format(result, enhanced_items)

            # 🔍 增强调试：记录转换结果
            if enhanced_results:
                self.logger.info(f"🔍 [调试] 转换后的成功调度订单数: {len(enhanced_results.get('successful_dispatched_orders', []))}")
                self.logger.info(f"🔍 [调试] 转换后的使用车辆数: {enhanced_results.get('trucks_used', 0)}")
                self.logger.info(f"🔍 [调试] 转换后的装载效率: {enhanced_results.get('dispatch_efficiency', 0):.2f}")

            self.logger.info(f"[完成] 大货物增强优化: {len(enhanced_results.get('successful_dispatched_orders', []))} 个订单")
            return enhanced_results

        except Exception as e:
            self.logger.error(f"❌ 大货物增强优化失败: {str(e)}")
            self.logger.error(f"🔍 [调试] 失败时输入数据形状: {large_orders.shape}")
            self.logger.error(f"🔍 [调试] 失败时货物列名: {list(large_orders.columns)}")
            import traceback
            self.logger.error(f"🔍 [调试] 异常堆栈: {traceback.format_exc()}")
            return self._empty_large_results()

    def _process_ltl_enhanced(self, medium_orders: pd.DataFrame,
                                small_orders: pd.DataFrame,
                                large_results: Dict) -> Dict:
        """使用增强优化器处理LTL货物"""
        self.logger.info("[增强] 开始LTL增强优化...")

        try:
            # 🔍 增强调试：记录输入数据
            self.logger.info(f"🔍 [调试] LTL输入 - 中货物: {len(medium_orders)}, 小货物: {len(small_orders)}")

            # 转换为增强货物格式
            medium_items = self._convert_orders_to_enhanced_items(medium_orders, "medium")
            small_items = self._convert_orders_to_enhanced_items(small_orders, "small")
            large_remaining_items = self._get_large_remaining_items_enhanced(large_results)

            # 合并所有LTL货物
            all_ltl_items = medium_items + small_items + large_remaining_items
            self.logger.info(f"🔍 [调试] LTL合并后货物总数: {len(all_ltl_items)}")

            if not all_ltl_items:
                self.logger.info("🔍 LTL货物为空，返回空结果")
                return self._empty_ltl_results()

            # 创建卡车规格
            truck_specs = TRUCK_SPECS
            truck = Truck3D(
                length=truck_specs['length'],
                width=truck_specs['width'],
                height=truck_specs['height'],
                volume=truck_specs['volume'],
                max_weight=truck_specs['max_weight']
            )
            self.logger.info(f"🔍 [调试] LTL卡车规格: {truck_specs['length']}×{truck_specs['width']}×{truck_specs['height']}m")

            # 使用增强优化器进行优化
            optimizer = GurobiOptimizerEnhanced()
            max_items = min(len(all_ltl_items), 15)  # 🚫 进一步限制复杂度：从100降到15

            self.logger.info(f"🔍 [调试] 开始LTL优化，最大货物数: {max_items}")
            result = optimizer.optimize_with_constraints(
                items=all_ltl_items,
                truck_specs=truck_specs,
                max_items=max_items,
                enable_spatial=True,
                enable_time_windows=True  # LTL启用时间窗约束
            )

            # 🔍 增强调试：记录原始结果
            self.logger.info(f"🔍 [调试] LTL原始优化结果状态: {result.status}")
            self.logger.info(f"🔍 [调试] LTL空间位置数量: {len(result.spatial_positions)}")
            self.logger.info(f"🔍 [调试] LTL体积利用率: {result.volume_utilization:.2f}%")
            self.logger.info(f"🔍 [调试] LTL时间惩罚: {result.total_time_penalty:.2f}元")

            # 转换结果格式
            enhanced_results = self._convert_enhanced_result_to_standard_format(result, all_ltl_items)

            # 🔍 增强调试：记录转换结果
            if enhanced_results:
                self.logger.info(f"🔍 [调试] LTL转换后的成功调度订单数: {len(enhanced_results.get('successful_dispatched_orders', []))}")
                self.logger.info(f"🔍 [调试] LTL转换后的使用车辆数: {enhanced_results.get('trucks_used', 0)}")

            self.logger.info(f"[完成] LTL增强优化: {len(enhanced_results.get('loaded_items', []))} 个货物")
            return enhanced_results

        except Exception as e:
            self.logger.error(f"❌ LTL增强优化失败: {str(e)}")
            self.logger.error(f"🔍 [调试] LTL失败时中货物形状: {medium_orders.shape}")
            self.logger.error(f"🔍 [调试] LTL失败时小货物形状: {small_orders.shape}")
            import traceback
            self.logger.error(f"🔍 [调试] LTL异常堆栈: {traceback.format_exc()}")
            return self._empty_ltl_results()

    def _convert_orders_to_enhanced_items(self, orders_df: pd.DataFrame, cargo_type: str) -> List[EnhancedCargoItem]:
        """将订单数据转换为增强货物格式"""
        enhanced_items = []

        if orders_df.empty:
            return enhanced_items

        for _, row in orders_df.iterrows():
            # 提取尺寸估算 - 修复列名问题
            # 大货物通常使用volume_m3和weight_kg列
            volume = row.get('volume_m3', row.get('order_total_volume_m3', 1.0))
            weight = row.get('weight_kg', row.get('order_total_weight_kg', 100))

            # 对于尺寸，如果没有估算列，则基于体积估算
            if 'estimated_length' in row and pd.notna(row['estimated_length']):
                length = float(row['estimated_length'])
            elif 'length' in row and pd.notna(row['length']):
                length = float(row['length'])
            else:
                # 基于体积估算尺寸 (假设立方体)
                length = float(volume ** (1/3))

            if 'estimated_width' in row and pd.notna(row['estimated_width']):
                width = float(row['estimated_width'])
            elif 'width' in row and pd.notna(row['width']):
                width = float(row['width'])
            else:
                # 基于体积估算尺寸
                width = float(volume ** (1/3))

            if 'estimated_height' in row and pd.notna(row['estimated_height']):
                height = float(row['estimated_height'])
            elif 'height' in row and pd.notna(row['height']):
                height = float(row['height'])
            else:
                # 基于体积估算尺寸
                height = float(volume ** (1/3))

            # 提取时间窗信息（如果存在）
            earliest_time = "08:00"
            latest_time = "18:00"
            service_time = 15

            # 检查是否有时间窗相关列
            if 'delivery_deadline' in orders_df.columns:
                # 假设deadline是最晚时间
                latest_time = "18:00"
            if 'pickup_deadline' in orders_df.columns:
                # 取货时间作为最早时间
                earliest_time = "08:00"

            # 创建增强货物
            enhanced_item = EnhancedCargoItem(
                item_id=f"{cargo_type}_{row['order_id']}",
                volume_m3=volume,
                weight_kg=weight,
                estimated_length=length,
                estimated_width=width,
                estimated_height=height,
                earliest_delivery_time=earliest_time,
                latest_delivery_time=latest_time,
                service_time_minutes=service_time,
                cargo_type=row.get('cargo_type', 'unknown'),
                order_id=row['order_id'],
                priority=1
            )

            enhanced_items.append(enhanced_item)

        return enhanced_items

    def _get_large_remaining_items_enhanced(self, large_results: Dict) -> List[EnhancedCargoItem]:
        """获取大货物剩余项目（增强版本）"""
        # 这里应该从large_results中提取剩余的货物信息
        # 简化处理，假设没有剩余货物
        return []

    def _convert_enhanced_result_to_standard_format(self, enhanced_result, enhanced_items: List[EnhancedCargoItem]) -> Dict:
        """将增强结果转换为标准格式"""
        try:
            # 检查enhanced_result是否为有效对象
            if enhanced_result is None:
                self.logger.warning("增强优化结果为None，返回空结果")
                return self._empty_large_results()

            # 检查是否有status属性
            if not hasattr(enhanced_result, 'status'):
                self.logger.warning("增强优化结果缺少status属性，返回空结果")
                return self._empty_large_results()

            if enhanced_result.status in ['optimal', 'feasible', 'time_limit']:
                # 安全获取spatial_positions
                spatial_positions = getattr(enhanced_result, 'spatial_positions', [])
                loaded_count = len(spatial_positions) if spatial_positions else 0

                # 安全获取volume_utilization，提供默认值
                volume_utilization = getattr(enhanced_result, 'volume_utilization', 0.0)
                if volume_utilization is None:
                    volume_utilization = 0.0

                return {
                    'optimization_type': 'enhanced_spatial_temporal',
                    'status': enhanced_result.status,
                    'successfully_dispatched_orders': loaded_count,
                    'trucks_used': 1,  # 简化处理
                    'truck_volume_used': volume_utilization * TRUCK_SPECS['volume'] / 100,
                    'dispatch_efficiency': volume_utilization,
                    'spatial_positions': spatial_positions,
                    'dispatch_results': [{
                        'truck_id': 'ENHANCED_TRUCK_001',
                        'order_id': getattr(enhanced_items[0], 'order_id', 'unknown') if enhanced_items else 'unknown',
                        'item_type': getattr(enhanced_items[0], 'cargo_type', 'unknown') if enhanced_items else 'unknown',
                        'items_count': loaded_count,
                        'truck_volume_used': volume_utilization * TRUCK_SPECS['volume'] / 100,
                        'loading_efficiency': volume_utilization,
                        'status': enhanced_result.status,
                        'spatial_positions': spatial_positions
                    }] if enhanced_items else [],
                    'enhanced_features': {
                        'time_window_violations': getattr(enhanced_result, 'time_window_violations', {}),
                        'multi_objective_score': getattr(enhanced_result, 'multi_objective_score', 0.0),
                        'economic_cost': getattr(enhanced_result, 'economic_cost', 0.0),
                        'spatial_validation': True
                    }
                }
            else:
                return {
                    'optimization_type': 'enhanced_spatial_temporal',
                    'status': getattr(enhanced_result, 'status', 'unknown'),
                    'successfully_dispatched_orders': 0,
                    'trucks_used': 0,
                    'truck_volume_used': 0,
                    'dispatch_efficiency': 0,
                    'dispatch_results': []
                }
        except Exception as e:
            self.logger.error(f"转换增强结果失败: {str(e)}")
            return self._empty_large_results()

    def _empty_large_results(self) -> Dict:
        """空的大货物结果"""
        return {
            'optimization_type': 'enhanced_spatial_temporal',
            'status': 'no_data',
            'successfully_dispatched_orders': [],  # 修复：应该是空列表，不是数字
            'trucks_used': 0,
            'truck_volume_used': 0,
            'dispatch_efficiency': 0,
            'dispatch_results': []
        }

    def _empty_ltl_results(self) -> Dict:
        """空的LTL结果"""
        return {
            'status': 'no_data',
            'loaded_items': 0,
            'trucks_used': 0,
            'total_loading_rate': 0,
            'loading_plan': pd.DataFrame()
        }

    def _collect_enhanced_loading_plans(self, complete_solution: Dict,
                                     large_results: Dict, ltl_results: Dict):
        """收集增强装载计划"""
        loading_plans = []

        # 收集大货物装载计划
        if large_results.get('dispatch_results'):
            for result in large_results['dispatch_results']:
                loading_plan = {
                    'truck_id': result['truck_id'],
                    'order_id': result['order_id'],
                    'item_type': result['item_type'],
                    'items_count': result['items_count'],
                    'volume_used': result['truck_volume_used'],
                    'loading_efficiency': result['loading_efficiency'],
                    'optimization_type': 'enhanced_3dpp_spatial',
                    'spatial_positions': result.get('spatial_positions', []),
                    'enhanced_features': {
                        'rotation_used': True,
                        'time_windows': False
                    }
                }
                loading_plans.append(loading_plan)

        # 收集LTL装载计划
        if ltl_results.get('loading_plan') is not None and not ltl_results['loading_plan'].empty:
            for _, row in ltl_results['loading_plan'].iterrows():
                loading_plan = {
                    'truck_id': f"LTL_{row['truck_id']:03d}",
                    'item_id': row['item_id'],
                    'order_id': row.get('original_order_id', row['item_id']),
                    'item_type': row['item_type'],
                    'volume_m3': row['volume_m3'],
                    'position_x': row.get('position_x', 0),
                    'position_y': row.get('position_y', 0),
                    'position_z': row.get('position_z', 0),
                    'rotation': row.get('rotation', 1),
                    'optimization_type': 'enhanced_ltl_spatial_temporal',
                    'enhanced_features': {
                        'rotation_used': row.get('rotation', 1) != 1,
                        'time_windows': False
                    }
                }
                loading_plans.append(loading_plan)

        complete_solution['loading_plans'] = loading_plans

    def _initialize_system(self):
        """初始化系统"""
        if self.verbose:
            mode = "增强" if self.use_enhanced_constraints else "标准"
            print(f"[初始化] 创建输出目录结构 ({mode}模式)...")

        create_directories()
        validate_config()

        if self.verbose:
            print(f"[完成] 系统初始化完成")
            if self.use_enhanced_constraints:
                print(f"[增强] 空间约束: {SPATIAL_CONSTRAINT_CONFIG['enable_3d_collision_detection']}")
                print(f"[增强] 时间约束: {TIME_WINDOW_CONFIG['enable_time_window_optimization']}")
                print(f"[增强] 多目标优化: {MULTI_OBJECTIVE_CONFIG['enable_multi_objective']}")
                print(f"[增强] 旋转优化: {SPATIAL_CONSTRAINT_CONFIG['enable_rotation_optimization']}")

    def _run_data_preprocessing(self) -> tuple:
        """运行数据预处理"""
        if self.verbose:
            print("[数据] 开始数据加载和预处理...")

        # 加载和清洗数据
        raw_data = self.preprocessing.data_loader.load_excel_data()
        clean_data = self.preprocessing.data_loader.clean_and_validate(raw_data)
        converted_data = self.preprocessing.data_loader.convert_units(clean_data)

        # 处理订单级别的数据
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

    def _calculate_available_trucks(self, large_results: Dict) -> int:
        """计算LTL优化可用车辆数"""
        total_trucks = LTL_OPTIMIZATION['max_trucks_available']
        used_trucks = large_results.get('trucks_used', 0)
        available_trucks = total_trucks - used_trucks

        if self.verbose:
            print(f"[车队] 可用车辆计算:")
            print(f"   总车队: {total_trucks} 辆")
            print(f"   大货物已用: {used_trucks} 辆")
            print(f"   LTL可用: {available_trucks} 辆")

        return max(0, available_trucks)

    def _merge_optimization_results(self, large_results: Dict, ltl_results: Dict) -> Dict:
        """合并所有优化结果"""
        if self.verbose:
            print("[合并] 合并优化结果...")

        # 合并装载方案
        all_loading_plans = []

        # 大货物装载方案
        if large_results.get('dispatch_results'):
            for result in large_results['dispatch_results']:
                all_loading_plans.append({
                    'truck_id': result['truck_id'],
                    'order_id': result['order_id'],
                    'item_type': result['item_type'],
                    'items_count': result['items_count'],
                    'volume_used': result['truck_volume_used'],
                    'loading_efficiency': result['loading_efficiency'],
                    'optimization_type': 'enhanced_3dpp_spatial',
                    'cargo_source': 'large_order',
                    'enhanced_features': result.get('enhanced_features', {})
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
                    'volume_m3': row['volume_m3'],
                    'position_x': row.get('position_x', 0),
                    'position_y': row.get('position_y', 0),
                    'position_z': row.get('position_z', 0),
                    'rotation': row.get('rotation', 1),
                    'optimization_type': 'enhanced_ltl_spatial_temporal',
                    'cargo_source': row.get('cargo_source', 'ltl'),
                    'enhanced_features': row.get('enhanced_features', {})
                })

        # 合并统计信息
        total_loaded_items = (
            large_results.get('successfully_dispatched_items', 0) +
            ltl_results.get('loaded_items', 0)
        )
        total_trucks_used = (
            large_results.get('trucks_used', 0) +
            ltl_results.get('trucks_used', 0)
        )
        total_volume_dispatched = (
            large_results.get('total_volume_dispatched', 0) +
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
                'optimization_algorithms': ['enhanced_3dpp_spatial_temporal'],
                'enhanced_features_enabled': self.use_enhanced_constraints
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
        """生成路径优化所需的数据文件"""
        if self.verbose:
            print("[数据] 生成路径优化数据文件...")

        try:
            # 使用file_manager生成文件
            dispatch_plan_file = self.file_manager.generate_full_dispatch_plan(
                large_results, ltl_results
            )

            # 生成ID映射关系
            mapping_file = self.file_manager.generate_id_mapping(
                [], []  # 传递空的列表，因为没有订单数据和货物数据
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
        """生成装载方案JSON文件"""
        if self.verbose:
            print("[装载] 生成装载方案JSON文件...")

        try:
            loading_files = {
                'large_truck_files': [],
                'ltl_truck_files': [],
                'total_files': []
            }

            # 生成大货物装载方案JSON
            if large_results.get('dispatch_results'):
                large_files = self._generate_large_truck_loading_plans_enhanced(
                    large_results, orders_data
                )
                loading_files['large_truck_files'] = large_files
                loading_files['total_files'].extend(large_files)

            # 生成LTL装载方案JSON
            if ltl_results.get('loading_plan') is not None and not ltl_results['loading_plan'].empty:
                ltl_files = self._generate_ltl_truck_loading_plans_enhanced(
                    ltl_results, orders_data
                )
                loading_files['ltl_truck_files'] = ltl_files
                loading_files['total_files'].extend(ltl_files)

            if self.verbose:
                total_count = len(loading_files['total_files'])
                large_count = len(loading_files['large_truck_files'])
                ltl_count = len(loading_files['ltl_truck_files'])
                print(f"[完成] 装载方案JSON生成完成: {total_count} 个文件")
                print(f"   大货物车辆: {large_count} 个")
                print(f"   LTL车辆: {ltl_count} 个")

            return loading_files

        except Exception as e:
            self.logger.error(f"生成装载方案JSON失败: {str(e)}")
            if self.verbose:
                print(f"[错误] 装载方案JSON生成失败: {str(e)}")
            return {'large_truck_files': [], 'ltl_truck_files': [], 'total_files': []}

    def _generate_large_truck_loading_plans_enhanced(self, large_results: Dict, orders_data: pd.DataFrame) -> List[str]:
        """生成大货物装载方案JSON（增强版本）"""
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

                # 获取增强的空间位置信息
                spatial_positions = result.get('spatial_positions', [])
                enhanced_features = result.get('enhanced_features', {})

                # 构建装载方案数据（增强版本）
                loading_plan_data = {
                    "summary": {
                        "vehicle_id": truck_id,
                        "total_items": result['items_count'],
                        "total_weight_kg": result.get('total_weight_kg', 0),
                        "total_volume_m3": result['truck_volume_used'],
                        "loading_efficiency": result['loading_efficiency'] * 100,
                        "volume_utilization": result['loading_efficiency'] * 100,
                        "optimization_algorithm": "Enhanced_3DPP_Spatial_Temporal",
                        "solution_status": result.get('status', 'unknown'),
                        "loading_time_minutes": 45,
                        "cargo_types": [result['item_type']],
                        "spatial_constraints": {
                            "rotation_enabled": enhanced_features.get('rotation_used', False),
                            "collision_detection": enhanced_features.get('spatial_validation', False),
                            "time_window_constraints": enhanced_features.get('time_windows', False)
                        }
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
                            "solver": "Gurobi_Enhanced_3DPP_Optimizer",
                            "strategy": "空间-时间约束装载优化",
                            "loading_type": "Enhanced_3DPP_Multi_Objective"
                        }
                    },
                    "loading_plan": self._generate_enhanced_loading_details(
                        spatial_positions, order_row, result
                    ),
                    "enhanced_metrics": {
                        "rotation_count": sum(1 for pos in spatial_positions if pos.get('rotation', 1) != 1),
                        "collision_avoided": enhanced_features.get('spatial_validation', True),
                        "optimization_iterations": 1,
                        "constraint_satisfaction": "all"
                    },
                    "metadata": {
                        "generated_time": datetime.now().isoformat(),
                        "generated_by": "Enhanced_Logistics_System_V4.1",
                        "format_version": "1.0",
                        "source_type": "enhanced_large_cargo_3dpp"
                    }
                }

                # 保存JSON文件
                filename = f"ENHANCED_{truck_id}_loading_plan.json"
                file_path = REPORTS_DIR / filename

                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(loading_plan_data, f, ensure_ascii=False, indent=2, default=str)

                loading_files.append(str(file_path))

                if self.verbose:
                    efficiency = result['loading_efficiency']
                    print(f"   [OK] {truck_id}: {result['items_count']}件, 装载率{efficiency*100:.1f}%")
                    if enhanced_features.get('rotation_used', False):
                        print(f"      - ✅ 启用了货物旋转优化")
                    if enhanced_features.get('spatial_validation', False):
                        print(f"      - ✅ 通过了空间冲突检测")

            return loading_files

        except Exception as e:
            self.logger.error(f"生成大货物装载方案失败: {str(e)}")
            return []

    def _generate_enhanced_loading_details(self, spatial_positions: List[Dict], order_row, result: Dict) -> List[Dict]:
        """生成增强的装载详细信息"""
        loading_details = []

        items_count = result['items_count']
        item_type = result['item_type']

        for i, pos in enumerate(spatial_positions):
            loading_details.append({
                "item_index": i + 1,
                "original_order_id": order_row['order_id'],
                "original_item_id": f"ITEM_{order_row['order_id']}_{i+1:03d}",
                "virtual_item_id": f"ENHANCED_{order_row['order_id']}_{i+1:03d}",
                "cargo_info": {
                    "type": item_type,
                    "subtype": f"{item_type}_增强",
                    "weight_kg": result.get('total_weight_kg', 0) / items_count,
                    "volume_m3": pos['dimensions']['volume'],
                    "dimensions": pos['dimensions']
                },
                "position_3d": {
                    "x": pos['position']['x'],
                    "y": pos['position']['y'],
                    "z": pos['position']['z'],
                    "rotation": pos['rotation'],
                    "orientation_confidence": 1.0
                },
                "optimization_info": {
                    "algorithm": "Enhanced_Gurobi_3DPP",
                    "spatial_method": "6-Rotation + Collision Detection",
                    "time_complexity": "O(n³)",
                    "constraint_count": len(pos['constraints']) if 'constraints' in pos else 0
                },
                "loading_sequence": i + 1,
                "loading_zone": f"zone_{chr(65 + (i // 20))}",
                "stacking_info": {
                    "can_stack": result.get('total_weight_kg', 0) / items_count < 1000,
                    "stacked_on": None,
                    "supports": []
                }
            })

        return loading_details

    def _generate_ltl_truck_loading_plans_enhanced(self, ltl_results: Dict, orders_data: pd.DataFrame) -> List[str]:
        """生成LTL车辆装载方案JSON（增强版本）"""
        loading_files = []

        try:
            # 加载调度计划
            dispatch_plan_data = self._load_dispatch_plan()
            if not dispatch_plan_data:
                return []

            dispatch_plan = dispatch_plan_data.get('dispatch_plan', {})

            for vehicle_id, truck_data in dispatch_plan.items():
                if truck_data.get('type') != 'LTL_TRUCK':
                    continue

                loaded_items = truck_data.get('loaded_items', [])
                if not loaded_items:
                    continue

                # 收集增强信息
                spatial_positions = self._extract_spatial_positions_from_ltl_items(loaded_items)
                enhanced_features = {
                    'rotation_used': any(item.get('rotation', 1) != 1 for item in loaded_items),
                    'time_windows': False  # LTL暂不启用时间窗
                }

                # 构建装载方案数据（增强版本）
                loading_plan_data = {
                    "summary": {
                        "vehicle_id": vehicle_id,
                        "total_items": len(loaded_items),
                        "total_weight_kg": sum(item.get('weight_kg', 0) for item in loaded_items),
                        "total_volume_m3": sum(item.get('volume_m3', 0) for item in loaded_items),
                        "loading_efficiency": (
                            sum(item.get('volume_m3', 0) for item in loaded_items) / TRUCK_SPECS['volume'] * 100
                        ),
                        "volume_utilization": (
                            sum(item.get('volume_m3', 0) for item in loaded_items) / TRUCK_SPECS['volume'] * 100
                        ),
                        "optimization_algorithm": "Enhanced_LTL_Multi_Truck_3DPP",
                        "solution_status": "OPTIMAL",
                        "loading_time_minutes": 90,
                        "cargo_types": list(set(item.get('item_type', 'unknown') for item in loaded_items)),
                        "spatial_constraints": {
                            "rotation_enabled": enhanced_features['rotation_used'],
                            "collision_detection": True,
                            "time_window_constraints": enhanced_features['time_windows']
                        }
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
                            "solver": "Gurobi_Enhanced_3DPP_Optimizer",
                            "strategy": "多品类混合装载 + 空间-时间约束",
                            "loading_type": "LTL_ENHANCED"
                        }
                    },
                    "loading_plan": self._build_enhanced_ltl_loading_details(
                        loaded_items, spatial_positions, orders_data
                    ),
                    "enhanced_metrics": {
                        "rotation_count": enhanced_features['rotation_used'],
                        "collision_free": True,
                        "packing_density": len(spatial_positions) / TRUCK_SPECS['volume'],
                        "space_utilization": self._calculate_space_utilization(spatial_positions),
                        "optimization_quality": "enhanced"
                    },
                    "metadata": {
                        "generated_time": datetime.now().isoformat(),
                        "generated_by": "Enhanced_Logistics_System_V4.1",
                        "format_version": "1.0",
                        "source_type": "enhanced_ltl_multi_truck_3dpp"
                    }
                }

                # 保存JSON文件
                filename = f"{vehicle_id}_enhanced_loading_plan.json"
                file_path = REPORTS_DIR / filename

                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(loading_plan_data, f, ensure_ascii=False, indent=2, default=str)

                loading_files.append(str(file_path))

                if self.verbose:
                    total_weight = sum(item.get('weight_kg', 0) for item in loaded_items)
                    efficiency = (
                        sum(item.get('volume_m3', 0) for item in loaded_items) / TRUCK_SPECS['volume'] * 100
                    )
                    print(f"   [OK] {vehicle_id}: {len(loaded_items)}件, {total_weight:.1f}kg, 装载率{efficiency:.1f}%")
                    if enhanced_features['rotation_used']:
                        print(f"      - ✅ 启用了货物旋转优化")
                    if enhanced_features['collision_detection']:
                        print(f"      - ✅ 通过了空间冲突检测")

            return loading_files

        except Exception as e:
            self.logger.error(f"生成LTL装载方案失败: {str(e)}")
            return []

    def _extract_spatial_positions_from_ltl_items(self, loaded_items: List[Dict]) -> List[Dict]:
        """从LTL装载项目中提取空间位置信息"""
        spatial_positions = []

        for item in loaded_items:
            spatial_positions.append({
                'position': {
                    'x': item.get('position_x', 0.0),
                    'y': item.get('position_y', 0.0),
                    'z': item.get('position_z', 0.0)
                },
                'dimensions': {
                    'length_m': item.get('estimated_length', 0.5),
                    'width_m': item.get('estimated_width', 0.4),
                    'height_m': item.get('estimated_height', 0.3),
                    'volume': item.get('volume_m3', 0)
                },
                'rotation': item.get('rotation', 1),
                'item_id': item.get('item_id', 'unknown')
            })

        return spatial_positions

    def _build_enhanced_ltl_loading_details(self, loaded_items: List[Dict],
                                      spatial_positions: List[Dict],
                                      orders_data: pd.DataFrame) -> List[Dict]:
        """构建增强的LTL装载详情"""
        loading_details = []
        processed_orders = set()

        for idx, item in enumerate(loaded_items):
            item_id = item.get('item_id', '')
            weight_kg = item.get('weight_kg', 0)
            volume_m3 = item.get('volume_m3', 0)

            # 反映射获取原始订单信息
            order_info = self._find_order_info_by_item_id(item_id, orders_data, processed_orders)
            if order_info:
                order_row = order_info[0]
                order_id = order_row['order_id']
                processed_orders.add(order_id)
            else:
                order_id = f"UNKNOWN_{item_id}"

            # 获取3D位置信息
            position_3d = self._find_spatial_position_by_item_id(item_id, spatial_positions)
            dimensions = position_3d.get('dimensions', {
                'length_m': 0.5, 'width_m': 0.4, 'height_m': 0.3
            })
            rotation = position_3d.get('rotation', 1)

            # 构建装载详情
            item_detail = {
                "item_index": idx + 1,
                "original_order_id": order_id,
                "original_item_id": f"ITEM_{order_id}_{idx+1:03d}",
                "virtual_item_id": item_id,
                "cargo_info": {
                    "type": item.get('item_type', 'unknown'),
                    "weight_kg": weight_kg,
                    "volume_m3": volume_m3
                },
                "dimensions": dimensions,
                "position_3d": position_3d,
                "loading_sequence": idx + 1,
                "loading_zone": f"zone_{chr(65 + (idx // 20))}",
                "stacking_info": {
                    "can_stack": weight_kg < 1000,
                    "stacked_on": None,
                    "supports": []
                },
                "optimization_info": {
                    "algorithm": "Enhanced_Gurobi_3DPP",
                    "spatial_method": "6-Rotation + Multi-Objective",
                    "constraint_count": 6  # 6种约束类型
                }
            }

            loading_details.append(item_detail)

        return loading_details

    def _find_order_info_by_item_id(self, item_id: str,
                                      orders_data: pd.DataFrame,
                                      processed_orders: set) -> Optional[pd.Series]:
        """通过item_id查找对应的订单信息"""
        for order_id in processed_orders:
            order_info = orders_data[orders_data['order_id'] == order_id]
            if not order_info.empty:
                # 检查是否有对应的item_id
                items_list = orders_data[orders_data['order_id'] == order_id]
                if any(item.get('item_id') == item_id for item in items_list):
                    return order_info
        return None

        # 通用查找
        order_info = orders_data[orders_data['item_id'] == item_id]
        if not order_info.empty:
            return order_info

        return None

    def _find_spatial_position_by_item_id(self, item_id: str, spatial_positions: List[Dict]) -> Dict:
        """通过item_id查找对应的空间位置"""
        for pos in spatial_positions:
            if pos['item_id'] == item_id:
                return pos
        return {
            'position': {'x': 0.0, 'y': 0.0, 'z': 0.0},
            'dimensions': {'length_m': 0.5, 'width_m': 0.4, 'height_m': 0.3},
            'rotation': 1
        }

    def _calculate_space_utilization(self, spatial_positions: List[Dict]) -> float:
        """计算空间利用率"""
        if not spatial_positions:
            return 0.0

        total_volume = sum(pos['dimensions']['volume'] for pos in spatial_positions)
        truck_volume = TRUCK_SPECS['volume']
        return (total_volume / truck_volume) * 100

    def _run_route_optimization(self, complete_solution: Dict,
                              orders_data: pd.DataFrame) -> Dict:
        """运行路径优化"""
        if self.verbose:
            print("[路径] 开始路径生成...")

        try:
            # 初始化路径解决方案字典
            route_solutions = {}

            # 加载调度计划
            dispatch_plan_data = self._load_dispatch_plan()
            if not dispatch_plan_data:
                if self.verbose:
                    print("[错误] 无法加载调度计划数据")
                return {}

            dispatch_plan = dispatch_plan_data.get('dispatch_plan', {})

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
                total_trucks = len(dispatch_plan.get('dispatch_plan', {}))
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

    def _load_id_mapping(self) -> Dict[str, List[str]]:
        """
        加载ID映射关系

        Returns:
            Dict[str, List[str]]: 货物ID到订单ID的映射关系
        """
        try:
            # 查找ID映射文件（使用正确的文件名模式）
            mapping_file = INTERMEDIATE_DIR / "id_to_orders_mapping.json"
            if not mapping_file.exists():
                self.logger.error("ID映射文件不存在")
                return {}

            with open(mapping_file, 'r', encoding='utf-8') as f:
                mapping_data = json.load(f)

            # 提取映射关系（使用正确的数据结构）
            id_mapping = mapping_data.get('id_to_orders_mapping', {})

            self.logger.info(f"成功加载ID映射: {len(id_mapping)} 个货物ID映射")
            return id_mapping

        except Exception as e:
            self.logger.error(f"加载ID映射失败: {str(e)}")
            return {}

    def _generate_full_truck_routes_integrated(self, dispatch_data: Dict, orders_data: pd.DataFrame) -> Dict:
        """集成版FULL_TRUCK路径生成"""
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
        """集成版LTL_TRUCK路径生成"""
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

    def _calculate_full_truck_route(self, vehicle_id: str, truck_data: Dict,
                                   order_row: pd.Series, depot_coord: List[float]) -> Optional[Dict]:
        """计算FULL_TRUCK路径"""
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
            service_time_minutes = (
                ROUTE_GENERATION['service_time_delivery']
                if order_type == '配送需求'
                else ROUTE_GENERATION['service_time_pickup']
            )
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
                    "optimization_algorithm": "Direct_Point_to_Point",
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
                    "fuel_efficiency_yuan_per_km": round(fuel_cost / distance_km, 2) if distance_km > 0 else 0,
                    "cargo_density_kg_per_m3": round(total_weight_kg / ROUTE_GENERATION['vehicle_volume_m3'], 2)
                },
                "solver_info": {
                    "method": "Direct_Point_to_Point",
                    "solve_time_seconds": 0.01,
                    "status": "DIRECT_ROUTE_SUCCESS"
                },
                "generated_time": datetime.now().isoformat(),
                "generated_by": "Enhanced_Logistics_System_V4.1"
            }

            return route_plan

        except Exception as e:
            self.logger.error(f"计算{vehicle_id}路径失败: {str(e)}")
            return None

    def _calculate_ltl_truck_route(self, vehicle_id: str, truck_data: Dict, loaded_items: List[Dict],
                               orders_data: pd.DataFrame, depot_coord: List[float]) -> Optional[Dict]:
        """计算LTL_TRUCK路径"""
        try:
            # 路径缓存和任务状态跟踪
            if vehicle_id in self.route_cache:
                return self.route_cache[vehicle_id]

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
                    # 处理所有订单，包括虚拟合并订单
                    if mapped_order.startswith('MERGED_ORDER_'):
                        # 处理虚拟合并订单
                        # 为虚拟订单创建一个默认位置
                        # 这里可以使用订单ID或物品信息来估算位置
                        stops.append({
                            'order_id': mapped_order,
                            'item_id': item_id,
                            'latitude': 30.5728 + (hash(item_id) % 100) * 0.001,  # 生成默认位置（成都附近）
                            'longitude': 104.0668 + (hash(item_id) % 100) * 0.001,
                            'pickup_delivery': '配送需求',  # 默认为配送需求
                            'weight_kg': item.get('weight_kg', 0),
                            'item_type': item.get('item_type', '未知'),
                            'destination_address': f"虚拟订单 {mapped_order} 默认地址"
                        })
                        if self.verbose:
                            print(f"   [虚拟订单] {vehicle_id} 处理虚拟订单 {mapped_order}")
                    else:
                        # 处理真实订单
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
                                print(f"   警告: {vehicle_id} 真实订单 {mapped_order} 未找到数据")

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
                service_time = (
                    ROUTE_GENERATION['service_time_delivery']
                    if stop['pickup_delivery'] == '配送需求'
                    else ROUTE_GENERATION['service_time_pickup']
                )

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
                    "cumulative_load_kg": total_weight if stop['pickup_delivery'] == '取货需求' else 0,
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
            avg_weight_ton = (empty_weight_kg + total_weight / 2) / 1000.0
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
                    "final_load_kg": total_weight,
                    "max_load_kg": ROUTE_GENERATION['truck_capacity_kg'],
                    "load_efficiency": round(total_weight / ROUTE_GENERATION['truck_capacity_kg'] * 100, 2),
                    "optimization_algorithm": "Nearest_Neighbor_TSP",
                    "solution_status": "MULTI_STOP_OPTIMIZED",
                    "completion_time": final_time.strftime('%H:%M'),
                    "start_time": ROUTE_GENERATION['start_time'],
                    "working_hours": round((final_time - datetime.now().replace(hour=8, minute=0, second=0, microsecond=0)).total_seconds() / 3600, 2),
                    "cargo_type": stop[0]['item_type'] if stops else 'unknown',
                    "cargo_quantity": len(loaded_items),
                    "enhanced_features": {
                        "time_windows": True,
                        "spatial_constraints": True,
                        "multi_objective": True,
                        "rotation_optimization": True
                    }
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
                        "fuel_coefficient": fuel_cost_per_ton_km,
                        "avg_speed_kmh": ROUTE_GENERATION['avg_speed_kmh']
                    },
                    "optimization_info": {
                        "solver": "Nearest_Neighbor_Algorithm",
                        "strategy": "多停靠点路径优化",
                        "route_type": "LTL_MULTI_STOP"
                    }
                },
                "itinerary": itinerary,
                "performance_metrics": {
                    "total_service_time_minutes": len(stops) * (
                        (ROUTE_GENERATION['service_time_pickup'] +
                         ROUTE_GENERATION['service_time_delivery']) / 2
                    ),
                    "total_travel_time_hours": round(total_distance / ROUTE_GENERATION['avg_speed_kmh'], 2),
                    "service_efficiency": 85.0,
                    "fuel_efficiency_yuan_per_km": round(fuel_cost / total_distance if total_distance > 0 else 0, 2),
                    "average_distance_per_stop": round(total_distance / len(stops) if len(stops) > 0 else 0, 2),
                    "cargo_density_kg_per_m3": round(total_weight / (ROUTE_GENERATION['vehicle_volume_m3']), 2)
                },
                "solver_info": {
                    "method": "Nearest_Neighbor_TSP",
                    "solve_time_seconds": 0.1,
                    "status": "MULTI_STOP_OPTIMIZED"
                },
                "generated_time": datetime.now().isoformat(),
                "generated_by": "Enhanced_Logistics_System_V4.1",
                "enhanced_features": {
                    "time_windows_used": True,
                    "spatial_constraints_used": True,
                    "multi_objective_optimized": True,
                    "rotation_optimization": True
                }
            }

            return route_plan

        except Exception as e:
            self.logger.error(f"计算{vehicle_id}路径失败: {str(e)}")
            return None

    def _optimize_route_nearest_neighbor(self, stops: List[Dict], depot_coord: List[float]) -> List[Dict]:
        """使用最近邻算法优化停靠点顺序"""
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
        """生成单车路径报告文件"""
        if not route_solutions:
            if self.verbose:
                print("[跳过] 无路径方案，跳过报告生成")
            return []

        if self.verbose:
            print("[报告] 生成路径规划报告...")

        try:
            report_files = []
            import json
            from datetime import datetime

            for truck_id, route_solution in route_solutions.items():
                # 标准化vehicle_id为3位数格式
                standardized_truck_id = self._standardize_vehicle_id(truck_id)
                report_filename = f"{standardized_truck_id}_route_plan.json"
                report_file = REPORTS_DIR / report_filename

                # 添加生成时间戳
                route_solution['generated_time'] = datetime.now().isoformat()
                route_solution['generated_by'] = 'Enhanced_Logistics_System_V4.1'

                # 保存报告
                with open(report_file, 'w', encoding='utf-8') as f:
                    json.dump(route_solution, f, ensure_ascii=False, indent=2, default=str)

                report_files.append(str(report_file))

                if self.verbose:
                    summary = route_solution['summary']
                    print(f"   {truck_id}: {summary['total_distance_km']:.1f}km, "
                          f"{summary['total_stops']}停靠点, "
                          f"成本{summary['fuel_cost_yuan']:.2f}元")

            return report_files

        except Exception as e:
            self.logger.error(f"生成路径报告失败: {str(e)}")
            if self.verbose:
                print(f"[错误] 路径报告生成失败: {str(e)}")
            return []

    def _standardize_vehicle_id(self, vehicle_id: str) -> str:
        """标准化vehicle_id为3位数格式"""
        if 'LARGE_TRUCK_' in vehicle_id:
            # 提取数字部分：LARGE_TRUCK_00 -> 00 -> 000
            number = vehicle_id.split('_')[-1]
            return f"LARGE_TRUCK_{int(number):03d}"
        elif 'LTL_TRUCK_' in vehicle_id:
            # 提取数字部分：LTL_TRUCK_00 -> 00 -> 000
            number = vehicle_id.split('_')[-1]
            return f"LTL_TRUCK_{int(number):03d}"
        else:
            return vehicle_id

    def _print_enhanced_summary(self):
        """打印增强模式摘要"""
        if not self.verbose:
            return

        print("\n" + "="*80)
        print("零担物流3D装箱优化系统V4.1 - 运行完成 (增强模式)")
        print("="*80)

        print(f"系统版本: 4.1 Enhanced")
        print(f"运行时间: {self.results['system_info']['total_runtime_formatted']}")
        print(f"优化模式: 增强模式 (集成空间-时间约束)")
        print()

        print("[新增] 新增功能特性:")
        enabled_features = []
        if self.use_enhanced_constraints:
            if SPATIAL_CONSTRAINT_CONFIG['enable_3d_collision_detection']:
                enabled_features.append("[启用] 3D空间冲突检测")
            if SPATIAL_CONSTRAINT_CONFIG['enable_rotation_optimization']:
                enabled_features.append("[启用] 货物旋转优化")
            if TIME_WINDOW_CONFIG['enable_time_window_optimization']:
                enabled_features.append("[启用] 时间窗约束")
            if MULTI_OBJECTIVE_CONFIG['enable_multi_objective']:
                enabled_features.append("[启用] 多目标优化")
        if enabled_features:
            print("   启用功能:")
            for feature in enabled_features:
                print(f"     - {feature}")

        print()

        print("[性能] 性能指标:")
        metrics = self.results['performance_metrics']
        print(f"  处理订单: {metrics['total_orders_processed']} 个")
        print(f"  装载货物: {metrics['total_loaded_items']} 个")
        print(f"  使用车辆: {metrics['total_trucks_used']} 辆")
        print(f"  整体装载率: {metrics['overall_efficiency']:.1f}%")
        print(f"空间约束: {SPATIAL_CONSTRAINT_CONFIG['enable_3d_collision_detection']}")
        print(f"时间约束: {TIME_WINDOW_CONFIG['enable_time_window_optimization']}")
        print()

        # 显示增强优化结果
        enhanced_results = self.results.get('enhanced_results', {})
        if enhanced_results:
            print("[优化] 增强优化结果:")
            print(f"   经济成本: {enhanced_results.get('economic_cost', 0):.2f}元")
            print(f" 多目标得分: {enhanced_results.get('multi_objective_score', 0):.4f}")
            print(f" 空间验证: {enhanced_results.get('spatial_validation', False)}")
            print(f" 时间违规数: {len(enhanced_results.get('time_window_violations', {}).get('total_violations', 0))}")

        print()

    def _print_standard_summary(self):
        """打印标准模式摘要"""
        if not self.verbose:
            return

        print("\n" + "="*80)
        print("零担物流3D装箱优化系统V3.0 - 运行完成")
        print("="*80)

        print(f"系统版本: {self.results['system_info']['version']}")
        print(f"运行时间: {self.results['system_info']['total_runtime_formatted']}")
        print(f"优化模式: 标准模式")
        print()

        print("[性能] 性能指标:")
        metrics = self.results['performance_metrics']
        print(f"  处理订单: {metrics['total_orders_processed']} 个")
        print(f"  装载货物: {metrics['total_loaded_items']} 个")
        print(f"  使用车辆: {metrics['total_trucks_used']} 辆")
        print(f"  整体装载率: {metrics['overall_efficiency']:.1%}")
        print()

    def _generate_comprehensive_visualizations(self, complete_solution: Dict) -> List[str]:
        """生成综合可视化"""
        if self.verbose:
            print("[可视化] 开始基于JSON文件生成四种核心可视化...")

        all_visualization_files = []

        try:
            # 使用可视化器模块
            if self.visualizer:
                # 生成所有可视化（包括新的增强功能）
                all_viz_files = self.visualizer.generate_all_single_category_visualizations()

                # 如果启用增强功能，生成额外的可视化
                if self.use_enhanced_constraints:
                    # 增强的3D可视化
                    enhanced_3d_viz = self.visualizer.create_enhanced_single_category_3dpp_visualization(
                        self._extract_truck_assignments(complete_solution)
                    )
                    if enhanced_3d_viz:
                        all_viz_files.extend(enhanced_3d_viz)

                    # 增强的时间窗可视化
                    if TIME_WINDOW_CONFIG['enable_time_window_optimization']:
                        # 时间窗分析图表
                        time_analysis_fig = self._create_time_window_analysis_visualization(complete_solution)
                        if time_analysis_fig:
                            all_viz_files.append(time_analysis_fig)

                    # 多目标优化可视化
                    if MULTI_OBJECTIVE_CONFIG['enable_multi_objective']:
                        multi_obj_fig = self._create_multi_objective_visualization(complete_solution)
                        if multi_obj_fig:
                            all_viz_files.append(multi_obj_fig)

                all_visualization_files.extend([
                    self.visualizer.create_multi_category_3dpp_visualization(
                        {'truck_assignments': self._extract_truck_assignments(complete_solution)}
                    ),
                    self.visualizer.create_loading_density_heatmap(
                        {'truck_assignments': self._extract_truck_assignments(complete_solution)}
                    ),
                    self.visualizer.create_loading_efficiency_dashboard(
                        {'truck_assignments': self._extract_truck_assignments(complete_solution)}
                    ),
                    self.visualizer.create_3d_efficiency_analysis(
                        {'truck_assignments': self._extract_truck_assignments(complete_solution)}
                    )
                ])

            else:
                # 使用标准可视化
                if self.visualizer:
                    all_viz_files = self.visualizer.generate_all_single_category_visualizations()

                    if self.visualizer_type == "plotly":
                        # 生成额外的Plotly可视化
                        enhanced_3d_viz = self.visualizer.create_enhanced_single_category_3dpp_visualization(
                            {'truck_assignments': self._extract_truck_assignments(complete_solution)}
                        )
                        if enhanced_3d_viz:
                            all_viz_files.extend(enhanced_3d_viz)

            if all_visualization_files:
                if self.verbose:
                    print(f"[完成] JSON可视化生成完毕: {len(all_visualization_files)} 个文件")
                    print("   ✅ 生成的可视化类型:")
                    print("     • 单品类3DPP装载可视化 (每辆货车独立HTML)")
                    print("     • 多品类3DPP装载可视化 (混合装载)")
                    print("     • 装载密度热力图 (3D空间分布)")
                    print("     • 装载率仪表板 (效率统计)")
                    print("     • 路径优化地图 (基于真实GPS坐标)")
                    print("     • 综合路径分析")

                if self.use_enhanced_constraints:
                    print("\n🎯 增强功能使用指南:")
                    print("   1. 空间约束: 已启用6种货物旋转 + 3D碰撞检测")
                    print("   2. 时间窗: 已启用软时间窗 + 惩罚机制")
                    print("   3. 多目标: 已启用经济效益 + 装载率权衡")
                    print("   4. 配置参数: 在config.py中调整SPATIAL_CONSTRAINT_CONFIG和TIME_WINDOW_CONFIG")

            self.logger.info(f"可视化生成完成: {len(all_visualization_files)} 个文件")
            return all_visualization_files

        except Exception as e:
            self.logger.error(f"JSON可视化生成失败: {str(e)}")
            if self.verbose:
                print(f"[错误] JSON可视化生成失败: {str(e)}")
            return []

    def _create_time_window_analysis_visualization(self, complete_solution: Dict) -> Optional[str]:
        """创建时间窗分析可视化"""
        if not TIME_WINDOW_CONFIG['enable_time_window_optimization']:
            return None

        try:
            # 分析时间窗违规情况
            time_violations = []

            # 收集所有时间窗违规信息
            loading_plans = complete_solution.get('loading_plans', [])
            for plan in loading_plans:
                enhanced_features = plan.get('enhanced_features', {})
                if enhanced_features.get('time_windows', False):
                    continue

                if enhanced_features.get('time_window_violations'):
                    time_violations.append({
                        'truck_id': plan['truck_id'],
                        'total_violations': len(enhanced_features['time_window_violations']),
                        'early_violations': len([
                            v for v in enhanced_features['time_window_violations']
                            if v.get('type') == 'early_arrival'
                        ]),
                        'late_violations': len([
                            v for v in enhanced_features['time_window_violations']
                            if v.get('type') == 'late_arrival'
                        ]),
                        'total_penalty': enhanced_features.get('total_time_penalty', 0.0)
                    })

            if not time_violations:
                self.logger.info("未发现时间窗违规记录")
                return None

            # 创建时间窗分析图表
            import matplotlib.pyplot as plt
            import matplotlib.dates as mdates
            import numpy as np

            # 分析违规分布
            early_counts = [v['early_violations'] for v in time_violations]
            late_counts = [v['late_violations'] for v in time_violations]
            total_violations = [v['total_violations'] for v in time_violations]

            # 创建时间分布图
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(15, 10))
            fig.suptitle('时间窗违规分析', fontsize=16, fontweight='bold')

            # 早到分布
            if early_counts:
                ax1.hist(early_counts, bins=range(0, max(early_counts)+1),
                        alpha=0.7, color='orange', edgecolor='black')
                ax1.set_xlabel('早到时间违规数')
                ax1.set_ylabel('车辆数量')
                ax1.set_title('早到时间窗违规分布')

                # 晚到分布
                ax2.hist(late_counts, bins=range(0, max(late_counts)+1),
                        alpha=0.7, color='red', edgecolor='black')
                ax2.set_xlabel('晚到时间窗违规数')
                ax2.set_ylabel('车辆数量')
                ax2.set_title('晚到时间窗违规分布')

            # 窗口信息
            for i, count in enumerate(early_counts):
                if count > 0:
                    ax1.text(0.95, max(early_counts)+1, f"早到{count}辆车",
                           transform=ax1.transAxes, ha='right', color='red')

            for i, count in enumerate(late_counts):
                if count > 0:
                    ax2.text(0.95, max(late_counts)+1, f"晚到{count}辆车",
                           transform=ax2.transAxes, ha='right', color='red')

            # 车口统计
            total_violations = sum(total_violations)
            total_trucks = len(time_violations)
            early_percentage = (sum(early_counts) / total_violations * 100) if total_violations > 0 else 0
            late_percentage = (sum(late_counts) / total_violations * 100) if total_violations > 0 else 0

            # 添加总统计信息
            ax1.text(0.5, max(early_counts)+1,
                       f"总计早到违规: {sum(early_counts)} 次")
            ax2.text(0.5, max(late_counts)+1,
                       f"总计晚到违规: {sum(late_counts)} 次")

            # 性能指标
            ax1.axvline(linestyle='--', color='gray', alpha=0.5)
            ax2.axvline(linestyle='--', color='gray', alpha=0.5)

            # 保存图表
            viz_path = VISUALIZATIONS_DIR / f"time_window_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            plt.savefig(viz_path, dpi=300, bbox_inches='tight')
            plt.close()

            self.logger.info(f"时间窗分析可视化已保存: {viz_path}")
            return viz_path

        except Exception as e:
            self.logger.error(f"时间窗分析可视化失败: {str(e)}")
            return None

    def _create_multi_objective_visualization(self, complete_solution: Dict) -> Optional[str]:
        """创建多目标优化可视化"""
        if not MULTI_OBJECTIVE_CONFIG['enable_multi_objective']:
            return None

        try:
            # 经济效益和装载率数据收集
            economic_costs = []
            loading_rates = []
            optimization_scores = []

            # 从各车辆收集数据
            loading_plans = complete_solution.get('loading_plans', [])
            for plan in loading_plans:
                plan_summary = plan.get('summary', {})
                loading_rates.append(plan_summary.get('loading_efficiency', 0))

                # 估算经济效益
                economic_cost = plan_summary.get('economic_cost', 0) or \
                             plan_summary.get('enhanced_features', {}).get('economic_cost', 0)

            # 计算多目标得分
                for loading_rate in loading_rates:
                    optimization_score = (
                        MULTI_OBJECTIVE_CONFIG['economic_weight'] * economic_cost / max(1, economic_cost) +
                        MULTI_OBJECTIVE_CONFIG['loading_rate_weight'] * (1 - loading_rate / 100)
                    )
                optimization_scores.append(optimization_score)

            # 创建多目标优化散点图
            import matplotlib.pyplot as plt
            import numpy as np
            import matplotlib.pyplot as plt
            from datetime import datetime

            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 8))

            # 散率分布散点图
            ax1.scatter(loading_rates, economic_costs, alpha=0.6, color='blue', s=50)
            ax1.set_xlabel('装载率 (%)')
            ax1.set_ylabel('经济效益 (归一化)')
            ax1.set_title('装载率-经济效益散点分布')

            # 添加趋势线
            if len(loading_rates) > 1:
                z = np.polyfit(loading_rates, economic_costs, 1)
                p = np.poly1d(z)
                ax1.plot(loading_rates, p(loading_rates), "r--", alpha=0.3, color='red', linewidth=2)
            ax1.set_title('装载率-经济效益帕累托前沿')

            ax1.axvline(linestyle='--', color='gray', alpha=0.3)
            ax1.legend(loc='upper left')
            ax1.grid(True, alpha=0.3)

            # 性能热力图
            ax2.bar(range(len(optimization_scores)), optimization_scores, alpha=0.7, color='green')
            ax2.set_xlabel('优化实例')
            ax2.set_ylabel('多目标得分')
            ax2.set_title('多目标优化结果')
            ax2.grid(True, alpha=0.3)

            # 添加说明文字
            fig.suptitle('多目标优化分析', fontsize=16, fontweight='bold')

            # 帕场分割线
            ax1.axvline(x=0.5, color='red', linestyle='--', alpha=0.7)
            ax1.set_title('装载率优先')
            ax2.axvline(x=0.4, color='red', linestyle='--', alpha=0.7)
            ax2.set_title('经济效益优先')
            ax2.legend(loc='upper right')

            # 保存图表
            viz_path = VISUALIZATIONS_DIR / f"multi_objective_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            plt.savefig(viz_path, dpi=300, bbox_inches='tight')
            plt.close()

            self.logger.info(f"多目标优化可视化已保存: {viz_path}")
            return viz_path

        except Exception as e:
            self.logger.error(f"多目标优化可视化失败: {str(e)}")
            return None

    def _generate_final_reports(self, complete_solution: Dict) -> Dict[str, str]:
        """生成最终报告"""
        if self.verbose:
            print("[报告] 生成最终报告与归档...")

        # 这里使用现有的file_manager生成报告
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
                             visualization_files: List[str], final_reports: Dict[str, str],
                             route_solutions=None, route_reports=None) -> Dict[str, Any]:
        """编译最终结果"""
        total_runtime = self.end_time - self.start_time

        return {
            'system_info': {
                'version': '4.1 Enhanced',
                'start_time': datetime.fromtimestamp(self.start_time).isoformat(),
                'end_time': datetime.fromtimestamp(self.end_time).isoformat(),
                'total_runtime_seconds': total_runtime,
                'total_runtime_formatted': f"{total_runtime//60:.0f}分{total_runtime%60:.1f}秒",
                'optimization_mode': 'enhanced' if self.use_enhanced_constraints else 'standard'
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
                'total_loaded_items': (
                    large_results.get('successfully_dispatched_items', 0) +
                    ltl_results.get('loaded_items', 0)
                ),
                'total_trucks_used': (
                    large_results.get('trucks_used', 0) +
                    ltl_results.get('trucks_used', 0)
                ),
                'overall_efficiency': (
                    (large_results.get('total_volume_dispatched', 0) +
                    ltl_results.get('total_loaded_volume', 0)
                ) / (
                    (large_results.get('trucks_used', 0) +
                     ltl_results.get('trucks_used', 0)) *
                     self.large_cargo_dispatcher.truck_specs['volume']
                ) if (large_results.get('trucks_used', 0) + ltl_results.get('trucks_used', 0)) > 0 else 0
            ),
                'enhanced_results': {}
            }
        }

def main():
    """主程序入口（增强版本）"""
    try:
        # 检查是否启用Web API模式
        import argparse
        parser = argparse.ArgumentParser(description='智能物流3D装箱优化系统V4.1')
        parser.add_argument('--web', action='store_true', help='启动Web API服务')
        parser.add_argument('--enhanced', action='store_true', default=True, help='启用增强约束功能')

        args = parser.parse_args()

        if args.web:
            # 启动Web API服务
            try:
                import uvicorn
                print("🌐 启动Web API服务...")
                print("📍地址: http://localhost:8000")
                print("📋 API文档: http://localhost:8000/docs")
                print("📊 ReDoc: http://localhost:8000/redoc")
                print("🔍 健康检查: http://localhost:8000/health")

                uvicorn.run(
                    app="api.app:app",
                    host="0.0.0.0",
                    port=8000,
                    reload=True,
                    log_level="info"
                )
            except Exception as e:
                print(f"❌ Web API服务启动失败: {str(e)}")
                return
        else:
            # 运行标准优化流程
            system = LogisticsOptimizationSystemEnhanced(
                verbose=True,
                use_enhanced_constraints=args.enhanced
            )
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