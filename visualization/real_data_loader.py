"""
真实数据加载器
Real Data Loader for Enhanced Visualizations
"""

import pickle
import json
import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional, Any
import logging

class RealDataLoader:
    """真实数据加载器 - 为可视化提供真实数据接口"""

    def __init__(self, base_path: Optional[str] = None):
        """
        初始化数据加载器

        Args:
            base_path: 数据基础路径，默认为当前项目的output目录
        """
        if base_path is None:
            self.base_path = Path(__file__).parent.parent / "output"
        else:
            self.base_path = Path(base_path)

        self.logger = self._setup_logger()

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

    def load_gurobi_solution(self) -> Optional[Dict]:
        """
        加载Gurobi 3D装箱解决方案

        Returns:
            Dict: Gurobi解决方案数据
        """
        gurobi_file = self.base_path / "intermediate" / "gurobi_solution.pkl"

        if not gurobi_file.exists():
            self.logger.warning(f"Gurobi解决方案文件不存在: {gurobi_file}")
            return None

        try:
            with open(gurobi_file, 'rb') as f:
                data = pickle.load(f)

            self.logger.info(f"成功加载Gurobi解决方案，包含 {len(data.get('loaded_items', []))} 个装载货物")
            return data
        except Exception as e:
            self.logger.error(f"加载Gurobi解决方案失败: {e}")
            return None

    def load_ltl_candidate_items(self) -> Optional[pd.DataFrame]:
        """
        加载LTL候选货物数据

        Returns:
            pd.DataFrame: LTL候选货物数据
        """
        ltl_file = self.base_path / "intermediate" / "ltl_candidate_items.pkl"

        if not ltl_file.exists():
            self.logger.warning(f"LTL候选货物文件不存在: {ltl_file}")
            return None

        try:
            with open(ltl_file, 'rb') as f:
                data = pickle.load(f)

            ltl_data = data.get('data')
            if isinstance(ltl_data, pd.DataFrame):
                self.logger.info(f"成功加载LTL候选货物，包含 {len(ltl_data)} 条记录")
                return ltl_data
            else:
                self.logger.error("LTL候选货物数据格式不正确")
                return None
        except Exception as e:
            self.logger.error(f"加载LTL候选货物失败: {e}")
            return None

    def load_dispatch_plan(self) -> Optional[Dict]:
        """
        加载调度计划数据

        Returns:
            Dict: 调度计划数据
        """
        dispatch_file = self.base_path / "intermediate" / "full_dispatch_plan.json"

        if not dispatch_file.exists():
            self.logger.warning(f"调度计划文件不存在: {dispatch_file}")
            return None

        try:
            with open(dispatch_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            dispatch_plan = data.get('dispatch_plan', {})
            self.logger.info(f"成功加载调度计划，包含 {len(dispatch_plan)} 个车辆")
            return data
        except Exception as e:
            self.logger.error(f"加载调度计划失败: {e}")
            return None

    def load_route_plans(self) -> Dict[str, Dict]:
        """
        加载所有路径计划数据

        Returns:
            Dict[str, Dict]: 所有车辆的路径计划
        """
        route_plans = {}
        reports_dir = self.base_path / "reports"

        if not reports_dir.exists():
            self.logger.warning(f"报告目录不存在: {reports_dir}")
            return route_plans

        try:
            # 查找所有路径计划文件
            route_files = list(reports_dir.glob("*_route_plan.json"))

            for route_file in route_files:
                vehicle_id = route_file.stem.replace("_route_plan", "")

                with open(route_file, 'r', encoding='utf-8') as f:
                    route_data = json.load(f)

                route_plans[vehicle_id] = route_data

            self.logger.info(f"成功加载 {len(route_plans)} 个路径计划")
            return route_plans
        except Exception as e:
            self.logger.error(f"加载路径计划失败: {e}")
            return {}

    def get_single_category_data(self, cargo_type: str) -> List[Dict]:
        """
        获取指定货物类型的单品类3DPP数据

        Args:
            cargo_type: 货物类型

        Returns:
            List[Dict]: 单品类货物的装载数据
        """
        gurobi_data = self.load_gurobi_solution()
        if not gurobi_data:
            return []

        loaded_items = gurobi_data.get('loaded_items', [])

        # 筛选指定类型的货物
        single_category_items = []
        for item in loaded_items:
            if item.get('item_type') == cargo_type:
                # 转换数据格式以适配可视化需求
                converted_item = {
                    'item_index': item.get('item_id', ''),
                    'position_x': item.get('position', (0, 0, 0))[0],
                    'position_y': item.get('position', (0, 0, 0))[1],
                    'position_z': item.get('position', (0, 0, 0))[2],
                    'estimated_length': item.get('dimensions', (0, 0, 0))[0],
                    'estimated_width': item.get('dimensions', (0, 0, 0))[1],
                    'estimated_height': item.get('dimensions', (0, 0, 0))[2],
                    'volume': item.get('volume', 0),
                    'weight': item.get('weight', 0),
                    'item_type': item.get('item_type', ''),
                    'truck_id': item.get('truck_id', ''),
                    'orientation': item.get('orientation', 0)
                }
                single_category_items.append(converted_item)

        self.logger.info(f"找到 {len(single_category_items)} 个 {cargo_type} 类型的货物")
        return single_category_items

    def get_multi_category_data(self) -> List[Dict]:
        """
        获取多品类3DPP数据（所有货物类型混合）

        Returns:
            List[Dict]: 多品类货物的装载数据
        """
        gurobi_data = self.load_gurobi_solution()
        if not gurobi_data:
            return []

        loaded_items = gurobi_data.get('loaded_items', [])

        # 转换所有货物数据
        multi_category_items = []
        for item in loaded_items:
            converted_item = {
                'item_id': item.get('item_id', ''),
                'position_x': item.get('position', (0, 0, 0))[0],
                'position_y': item.get('position', (0, 0, 0))[1],
                'position_z': item.get('position', (0, 0, 0))[2],
                'estimated_length': item.get('dimensions', (0, 0, 0))[0],
                'estimated_width': item.get('dimensions', (0, 0, 0))[1],
                'estimated_height': item.get('dimensions', (0, 0, 0))[2],
                'volume': item.get('volume', 0),
                'weight': item.get('weight', 0),
                'item_type': item.get('item_type', ''),
                'truck_id': item.get('truck_id', ''),
                'orientation': item.get('orientation', 0)
            }
            multi_category_items.append(converted_item)

        self.logger.info(f"加载 {len(multi_category_items)} 个多品类货物")
        return multi_category_items

    def get_route_optimization_data(self) -> Dict:
        """
        获取路径优化数据

        Returns:
            Dict: 路径优化数据
        """
        route_plans = self.load_route_plans()

        # 转换路径数据格式
        route_optimization_data = {
            'route_solutions': {},
            'depot_location': [30.800835, 104.139111]  # A网点坐标
        }

        for vehicle_id, route_data in route_plans.items():
            # 处理路径序列
            itinerary = route_data.get('itinerary', [])
            route_sequence = []

            for step in itinerary:
                route_sequence.append({
                    'order_id': step.get('order_id', ''),
                    'type': 'pickup' if step.get('action') == '取货' else 'delivery',
                    'latitude': step.get('coordinates', [0, 0])[0],
                    'longitude': step.get('coordinates', [0, 0])[1],
                    'weight_kg': abs(step.get('weight_change_kg', 0)),
                    'arrival_time': step.get('estimated_arrival', ''),
                    'travel_distance_km': step.get('distance_from_previous_km', 0),
                    'service_time_minutes': step.get('service_time_minutes', 30)
                })

            route_optimization_data['route_solutions'][vehicle_id] = {
                'vehicle_id': vehicle_id,
                'route_sequence': route_sequence,
                'summary': route_data.get('summary', {}),
                'vehicle_info': route_data.get('route_details', {}).get('vehicle_info', {})
            }

        self.logger.info(f"转换 {len(route_optimization_data['route_solutions'])} 个路径方案")
        return route_optimization_data

    def get_available_cargo_types(self) -> List[str]:
        """
        获取可用的货物类型列表

        Returns:
            List[str]: 货物类型列表
        """
        gurobi_data = self.load_gurobi_solution()
        if not gurobi_data:
            return []

        loaded_items = gurobi_data.get('loaded_items', [])
        cargo_types = set()

        for item in loaded_items:
            item_type = item.get('item_type')
            if item_type:
                cargo_types.add(item_type)

        return list(cargo_types)

    def load_loading_plans(self) -> Dict[str, Dict]:
        """
        加载所有装载方案JSON文件

        Returns:
            Dict[str, Dict]: 所有车辆的装载方案
        """
        loading_plans = {}
        reports_dir = self.base_path / "reports"

        if not reports_dir.exists():
            self.logger.warning(f"报告目录不存在: {reports_dir}")
            return loading_plans

        try:
            # 查找所有装载方案文件
            loading_files = list(reports_dir.glob("*_loading_plan.json"))

            for loading_file in loading_files:
                vehicle_id = loading_file.stem.replace("_loading_plan", "")

                with open(loading_file, 'r', encoding='utf-8') as f:
                    loading_data = json.load(f)

                loading_plans[vehicle_id] = loading_data

            self.logger.info(f"成功加载 {len(loading_plans)} 个装载方案")
            return loading_plans
        except Exception as e:
            self.logger.error(f"加载装载方案失败: {e}")
            return {}

    def get_loading_visualization_data(self) -> Dict:
        """
        获取装载可视化数据（基于JSON文件的真实数据）

        Returns:
            Dict: 装载可视化数据
        """
        loading_plans = self.load_loading_plans()

        # 转换装载数据格式以适配可视化需求
        visualization_data = {
            'truck_assignments': {},
            'summary': {
                'total_vehicles': len(loading_plans),
                'vehicle_types': set(),
                'cargo_types': set(),
                'total_items': 0,
                'total_volume': 0,
                'total_weight': 0
            }
        }

        for vehicle_id, loading_data in loading_plans.items():
            summary = loading_data.get('summary', {})
            loading_plan = loading_data.get('loading_plan', [])
            vehicle_details = loading_data.get('vehicle_details', {})

            # 处理装载的货物
            loaded_items = []
            for item in loading_plan:
                cargo_info = item.get('cargo_info', {})
                position_3d = item.get('position_3d', {})
                dimensions = item.get('dimensions', {})

                converted_item = {
                    'item_id': item.get('virtual_item_id', ''),
                    'original_order_id': item.get('original_order_id', ''),
                    # 兼容plotly_3d.py可视化器的格式要求
                    'position': (position_3d.get('x', 0), position_3d.get('y', 0), position_3d.get('z', 0)),
                    'dimensions': (dimensions.get('length_m', 0), dimensions.get('width_m', 0), dimensions.get('height_m', 0)),
                    # 保留原始字段以备兼容性
                    'position_x': position_3d.get('x', 0),
                    'position_y': position_3d.get('y', 0),
                    'position_z': position_3d.get('z', 0),
                    'estimated_length': dimensions.get('length_m', 0),
                    'estimated_width': dimensions.get('width_m', 0),
                    'estimated_height': dimensions.get('height_m', 0),
                    'volume': cargo_info.get('volume_m3', 0),
                    'weight': cargo_info.get('weight_kg', 0),
                    'item_type': cargo_info.get('type', ''),
                    'item_subtype': cargo_info.get('subtype', ''),
                    'orientation': position_3d.get('rotation', 0),
                    'loading_sequence': item.get('loading_sequence', 0),
                    'stacking_info': item.get('stacking_info', {}),
                    'merged_from': item.get('merged_from', [])
                }
                loaded_items.append(converted_item)

            # 添加到车辆分配数据
            visualization_data['truck_assignments'][vehicle_id] = {
                'truck_id': vehicle_id,
                'vehicle_type': vehicle_details.get('type', ''),
                'truck_specs': vehicle_details.get('truck_specs', {}),
                'loaded_items': loaded_items,
                'loading_efficiency': summary.get('loading_efficiency', 0),
                'volume_utilization': summary.get('volume_utilization', 0),
                'total_items': summary.get('total_items', 0),
                'total_weight': summary.get('total_weight_kg', 0),
                'total_volume': summary.get('total_volume_m3', 0),
                'cargo_types': summary.get('cargo_types', []),
                'optimization_algorithm': summary.get('optimization_algorithm', ''),
                'solution_status': summary.get('solution_status', '')
            }

            # 更新总体统计
            visualization_data['summary']['vehicle_types'].add(vehicle_details.get('type', ''))
            visualization_data['summary']['cargo_types'].update(summary.get('cargo_types', []))
            visualization_data['summary']['total_items'] += summary.get('total_items', 0)
            visualization_data['summary']['total_volume'] += summary.get('total_volume_m3', 0)
            visualization_data['summary']['total_weight'] += summary.get('total_weight_kg', 0)

        # 转换为列表
        visualization_data['summary']['vehicle_types'] = list(visualization_data['summary']['vehicle_types'])
        visualization_data['summary']['cargo_types'] = list(visualization_data['summary']['cargo_types'])

        self.logger.info(f"装载可视化数据准备完成: {len(loading_plans)} 个车辆, {visualization_data['summary']['total_items']} 个货物")
        return visualization_data

    def get_statistics(self) -> Dict:
        """
        获取数据统计信息

        Returns:
            Dict: 统计信息
        """
        gurobi_data = self.load_gurobi_solution()
        dispatch_data = self.load_dispatch_plan()
        route_plans = self.load_route_plans()
        loading_plans = self.load_loading_plans()

        stats = {
            'loaded_items_count': len(gurobi_data.get('loaded_items', [])) if gurobi_data else 0,
            'trucks_used': gurobi_data.get('trucks_used', 0) if gurobi_data else 0,
            'loading_efficiency': gurobi_data.get('loading_efficiency', 0) if gurobi_data else 0,
            'dispatch_vehicles': len(dispatch_data.get('dispatch_plan', {})) if dispatch_data else 0,
            'route_plans_count': len(route_plans),
            'loading_plans_count': len(loading_plans),
            'cargo_types': self.get_available_cargo_types()
        }

        return stats


def main():
    """测试数据加载器"""
    print("=== 真实数据加载器测试 ===")

    loader = RealDataLoader()

    # 测试统计信息
    stats = loader.get_statistics()
    print(f"数据统计: {stats}")

    # 测试货物类型
    cargo_types = loader.get_available_cargo_types()
    print(f"可用货物类型: {cargo_types}")

    # 测试单品类数据
    if cargo_types:
        single_data = loader.get_single_category_data(cargo_types[0])
        print(f"单品类数据样本数量: {len(single_data)}")

    # 测试多品类数据
    multi_data = loader.get_multi_category_data()
    print(f"多品类数据样本数量: {len(multi_data)}")

    # 测试路径数据
    route_data = loader.get_route_optimization_data()
    print(f"路径方案数量: {len(route_data.get('route_solutions', {}))}")


if __name__ == "__main__":
    main()