"""
JSON数据处理器 - 专门处理装载和路径JSON文件
JSON Data Processor for Loading and Route Plan Files
"""

import json
import random
from pathlib import Path
from typing import Dict, List, Optional, Any
import logging

class JsonDataProcessor:
    """JSON文件数据处理器"""

    def __init__(self, reports_dir: str = "A:\\MYpython\\物流\\output\\reports"):
        """初始化JSON数据处理器"""
        self.reports_dir = Path(reports_dir)
        self.logger = self._setup_logger()

    def _setup_logger(self):
        """设置日志记录器"""
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.INFO)
        return logger

    def scan_json_files(self) -> Dict[str, List[Path]]:
        """
        扫描并分类JSON文件，按后缀分类

        Returns:
            Dict: 包含loading_plans和route_plans的文件路径列表
        """
        try:
            loading_plans = list(self.reports_dir.glob("*_loading_plan.json"))
            route_plans = list(self.reports_dir.glob("*_route_plan.json"))

            self.logger.info(f"发现装载计划文件: {len(loading_plans)}个")
            self.logger.info(f"发现路径计划文件: {len(route_plans)}个")

            return {
                'loading_plans': loading_plans,
                'route_plans': route_plans
            }

        except Exception as e:
            self.logger.error(f"扫描JSON文件失败: {str(e)}")
            return {'loading_plans': [], 'route_plans': []}

    def load_loading_plan(self, json_path: Path) -> Optional[Dict]:
        """
        加载装载计划JSON文件，处理vehicle_id不一致问题

        Args:
            json_path: JSON文件路径

        Returns:
            Dict: 装载计划数据
        """
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # 修复vehicle_id不一致问题
            data = self._fix_vehicle_id_inconsistency(data, json_path)

            return data

        except Exception as e:
            self.logger.error(f"加载装载计划文件失败 {json_path}: {str(e)}")
            return None

    def load_route_plan(self, json_path: Path) -> Optional[Dict]:
        """
        加载路径计划JSON文件

        Args:
            json_path: JSON文件路径

        Returns:
            Dict: 路径计划数据
        """
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            return data

        except Exception as e:
            self.logger.error(f"加载路径计划文件失败 {json_path}: {str(e)}")
            return None

    def apply_sampling(self, loading_plan: List[Dict], max_items: int = 500) -> List[Dict]:
        """
        应用>500货物的随机抽样逻辑

        Args:
            loading_plan: 装载计划列表
            max_items: 最大项目数量

        Returns:
            List: 抽样后的装载计划列表
        """
        if len(loading_plan) > max_items:
            sampled_plan = random.sample(loading_plan, max_items)
            self.logger.info(f"货物数量 {len(loading_plan)} > {max_items}，随机抽样到 {len(sampled_plan)} 件")
            return sampled_plan
        else:
            return loading_plan

    def extract_vehicle_id_from_path(self, json_path: Path) -> str:
        """
        从文件路径提取标准化的vehicle_id

        Args:
            json_path: JSON文件路径

        Returns:
            str: 标准化的vehicle_id
        """
        filename = json_path.stem
        if '_loading_plan' in filename:
            return filename.replace('_loading_plan', '')
        elif '_route_plan' in filename:
            return filename.replace('_route_plan', '')
        else:
            return filename

    def _fix_vehicle_id_inconsistency(self, data: Dict, json_path: Path) -> Dict:
        """
        修复LARGE_TRUCK的vehicle_id不一致问题

        Args:
            data: JSON数据
            json_path: 文件路径

        Returns:
            Dict: 修复后的数据
        """
        if 'LARGE_TRUCK' in str(json_path):
            # 从文件名提取正确的vehicle_id
            correct_vehicle_id = self.extract_vehicle_id_from_path(json_path)
            if 'summary' in data:
                data['summary']['vehicle_id'] = correct_vehicle_id
                self.logger.debug(f"修复vehicle_id: {correct_vehicle_id}")

        return data

    def get_loading_efficiency_summary(self, json_files: List[Path]) -> List[Dict]:
        """
        获取所有装载文件的效率摘要信息

        Args:
            json_files: 装载计划JSON文件列表

        Returns:
            List: 效率摘要数据列表
        """
        efficiency_data = []

        for json_path in json_files:
            loading_data = self.load_loading_plan(json_path)
            if not loading_data:
                continue

            summary = loading_data.get('summary', {})
            vehicle_id = self.extract_vehicle_id_from_path(json_path)

            efficiency_data.append({
                'vehicle_id': vehicle_id,
                'loading_efficiency': summary.get('loading_efficiency', 0),
                'total_items': summary.get('total_items', 0),
                'total_volume_m3': summary.get('total_volume_m3', 0),
                'cargo_types': summary.get('cargo_types', []),
                'truck_type': 'LARGE_TRUCK' if 'LARGE_TRUCK' in vehicle_id else 'LTL_TRUCK'
            })

        return efficiency_data

    def get_3d_efficiency_analysis_data(self, json_files: List[Path]) -> List[Dict]:
        """
        获取3D装载效率分析所需的数据

        Args:
            json_files: 装载计划JSON文件列表

        Returns:
            List: 包含效率分析数据的列表
        """
        analysis_data = []

        for json_path in json_files:
            loading_data = self.load_loading_plan(json_path)
            if not loading_data:
                continue

            summary = loading_data.get('summary', {})
            vehicle_details = loading_data.get('vehicle_details', {})
            truck_specs = vehicle_details.get('truck_specs', {})

            vehicle_id = self.extract_vehicle_id_from_path(json_path)

            # 基础数据
            loading_efficiency = summary.get('loading_efficiency', 0)
            total_volume_used = summary.get('total_volume_m3', 0)
            total_items = summary.get('total_items', 0)

            # 车辆规格
            truck_volume_capacity = truck_specs.get('volume_m3', 55.296)  # 默认大型卡车容量
            truck_weight_capacity = truck_specs.get('capacity_kg', 18000)  # 默认载重

            # 计算指标
            volume_utilization = (total_volume_used / truck_volume_capacity) * 100 if truck_volume_capacity > 0 else 0

            # 由于重量数据缺失，使用体积密度估算
            # 假设平均密度为 200 kg/m³ (一个合理的货物密度)
            estimated_weight = total_volume_used * 200  # kg
            weight_ratio = (estimated_weight / truck_weight_capacity) * 100 if truck_weight_capacity > 0 else 0

            # 体积效率指标 (T·m³) = 重量(T) × 体积利用率(m³)
            volume_efficiency_tm3 = (estimated_weight / 1000) * volume_utilization / 100

            analysis_data.append({
                'vehicle_id': vehicle_id,
                'loading_efficiency': loading_efficiency,  # X轴: 装载效率(%)
                'weight_ratio': weight_ratio,  # Y轴: 重量比例(%)
                'volume_efficiency_tm3': volume_efficiency_tm3,  # Z轴: 体积效率(T·m³)
                'total_items': total_items,
                'total_volume_used': total_volume_used,
                'estimated_weight_kg': estimated_weight,
                'truck_type': 'LARGE_TRUCK' if 'LARGE_TRUCK' in vehicle_id else 'LTL_TRUCK'
            })

        return analysis_data

    def get_all_position_data(self, json_files: List[Path], max_items_per_truck: int = 500) -> List[Dict]:
        """
        获取所有装载文件的position_3d数据用于密度分析

        Args:
            json_files: 装载计划JSON文件列表
            max_items_per_truck: 每辆车最大项目数

        Returns:
            List: 位置数据列表
        """
        all_positions = []

        for json_path in json_files:
            loading_data = self.load_loading_plan(json_path)
            if not loading_data:
                continue

            vehicle_id = self.extract_vehicle_id_from_path(json_path)
            loading_plan = loading_data.get('loading_plan', [])

            # 应用抽样
            sampled_plan = self.apply_sampling(loading_plan, max_items_per_truck)

            for item in sampled_plan:
                pos = item.get('position_3d', {})
                dims = item.get('dimensions', {})
                cargo_info = item.get('cargo_info', {})

                all_positions.append({
                    'vehicle_id': vehicle_id,
                    'x': pos.get('x', 0),
                    'y': pos.get('y', 0),
                    'z': pos.get('z', 0),
                    'volume': cargo_info.get('volume_m3', 0),
                    'cargo_type': cargo_info.get('type', 'unknown'),
                    'length': dims.get('length_m', 0),
                    'width': dims.get('width_m', 0),
                    'height': dims.get('height_m', 0)
                })

        self.logger.info(f"收集位置数据: {len(all_positions)} 个货物位置")
        return all_positions