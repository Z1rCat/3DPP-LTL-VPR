"""
货物分类器模块
Cargo Classifier Module for Three-way Classification and Small Cargo Merging
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
from config import (CARGO_CLASSIFICATION, LTL_OPTIMIZATION, DIMENSION_ESTIMATION,
                   REPORTS_DIR, FILE_CONFIG)


class CargoClassifier:
    """货物分类器 - 实现三分类：大、中、小货物"""

    def __init__(self):
        """初始化货物分类器"""
        self.logger = self._setup_logger()
        self.large_threshold = CARGO_CLASSIFICATION['large_cargo_threshold']
        self.medium_threshold = CARGO_CLASSIFICATION['medium_cargo_threshold']
        self.small_max = CARGO_CLASSIFICATION['small_cargo_max']
        self.enable_merging = LTL_OPTIMIZATION['enable_small_cargo_merging']
        self.merge_by_type = LTL_OPTIMIZATION['merge_by_cargo_type']

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

    def classify_all_orders(self, orders_data: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """
        三分类所有订单：大货物、中货物、小货物

        Args:
            orders_data: 包含所有订单信息的DataFrame（订单级别）

        Returns:
            Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]: (大货物订单, 中货物订单, 小货物订单)
        """
        self.logger.info("开始三分类订单：大货物、中货物、小货物")

        # 检查必要字段
        required_fields = ['order_id', 'order_total_volume_m3', 'volume_m3', 'quantity', 'item_type']
        missing_fields = [field for field in required_fields if field not in orders_data.columns]

        if missing_fields:
            raise ValueError(f"缺少必要字段: {missing_fields}")

        # 三分类逻辑
        large_mask = orders_data['order_total_volume_m3'] > self.large_threshold
        medium_mask = (orders_data['order_total_volume_m3'] >= self.medium_threshold) & \
                     (orders_data['order_total_volume_m3'] <= self.large_threshold)
        small_mask = orders_data['order_total_volume_m3'] < self.small_max

        large_orders = orders_data[large_mask].copy()
        medium_orders = orders_data[medium_mask].copy()
        small_orders = orders_data[small_mask].copy()

        # 分类统计
        self.logger.info(f"三分类完成:")
        self.logger.info(f"  大货物订单: {len(large_orders)} 个，总体积 {large_orders['order_total_volume_m3'].sum():.6f} m³")
        self.logger.info(f"  中货物订单: {len(medium_orders)} 个，总体积 {medium_orders['order_total_volume_m3'].sum():.6f} m³")
        self.logger.info(f"  小货物订单: {len(small_orders)} 个，总体积 {small_orders['order_total_volume_m3'].sum():.6f} m³")

        # 详细统计
        if len(large_orders) > 0:
            self.logger.info(f"  大货物详情:")
            for _, order in large_orders.head(10).iterrows():  # 只显示前10个
                self.logger.info(f"    {order['order_id']}: {order['item_type']} x{order['quantity']}, "
                               f"总体积 {order['order_total_volume_m3']:.6f} m³")

        # 导出分类结果
        self._export_classification_results(large_orders, medium_orders, small_orders)

        return large_orders, medium_orders, small_orders

    def merge_small_orders(self, small_orders: pd.DataFrame) -> pd.DataFrame:
        """
        合并小货物订单

        Args:
            small_orders: 小货物订单DataFrame

        Returns:
            pd.DataFrame: 合并后的虚拟货物DataFrame
        """
        if len(small_orders) == 0:
            self.logger.info("没有小货物订单需要合并")
            return pd.DataFrame()

        self.logger.info(f"开始合并{len(small_orders)}个小货物订单")

        merged_items = []
        item_counter = 0

        if self.merge_by_type:
            # 按货物类型分组合并
            cargo_types = small_orders['item_type'].unique()

            for cargo_type in cargo_types:
                type_orders = small_orders[small_orders['item_type'] == cargo_type].copy()

                if len(type_orders) == 0:
                    continue

                # 计算该类型货物的总体积和总重量
                total_volume_m3 = type_orders['order_total_volume_m3'].sum()
                total_weight_kg = type_orders['order_total_weight_kg'].sum() if 'order_total_weight_kg' in type_orders.columns else 0
                total_quantity = type_orders['quantity'].sum()

                # 计算平均单件尺寸（用于估算合并后尺寸）
                avg_single_volume = type_orders['volume_m3'].mean()

                # 估算合并后的尺寸
                merged_dimensions = self._estimate_merged_dimensions(
                    total_volume_m3,
                    total_quantity,
                    avg_single_volume
                )

                # 创建虚拟合并货物
                merged_item = {
                    'item_id': f"MERGED_{cargo_type}_{item_counter:03d}",
                    'order_id': f"MERGED_ORDER_{cargo_type}_{item_counter:03d}",
                    'item_type': cargo_type,
                    'volume_m3': total_volume_m3,
                    'weight_kg': total_weight_kg,
                    'estimated_length': merged_dimensions[0],
                    'estimated_width': merged_dimensions[1],
                    'estimated_height': merged_dimensions[2],
                    'quantity': 1,  # 合并后视为1件
                    'is_merged': True,
                    'original_orders_count': len(type_orders),
                    'original_items_count': total_quantity,
                    'original_order_ids': type_orders['order_id'].tolist(),
                    'density': total_weight_kg / total_volume_m3 if total_volume_m3 > 0 else 0,
                    'cargo_source': 'small_merged',
                    'processed_timestamp': pd.Timestamp.now()
                }

                merged_items.append(merged_item)
                item_counter += 1

                self.logger.info(f"  合并{cargo_type}: {len(type_orders)}个订单 → 1个虚拟货物，"
                               f"总体积 {total_volume_m3:.6f} m³")

        else:
            # 不分类型，全部合并为一个虚拟货物
            total_volume_m3 = small_orders['order_total_volume_m3'].sum()
            total_weight_kg = small_orders['order_total_weight_kg'].sum() if 'order_total_weight_kg' in small_orders.columns else 0
            total_quantity = small_orders['quantity'].sum()

            avg_single_volume = small_orders['volume_m3'].mean()
            merged_dimensions = self._estimate_merged_dimensions(
                total_volume_m3,
                total_quantity,
                avg_single_volume
            )

            merged_item = {
                'item_id': f"MERGED_ALL_{item_counter:03d}",
                'order_id': f"MERGED_ORDER_ALL_{item_counter:03d}",
                'item_type': 'mixed_small_cargo',
                'volume_m3': total_volume_m3,
                'weight_kg': total_weight_kg,
                'estimated_length': merged_dimensions[0],
                'estimated_width': merged_dimensions[1],
                'estimated_height': merged_dimensions[2],
                'quantity': 1,
                'is_merged': True,
                'original_orders_count': len(small_orders),
                'original_items_count': total_quantity,
                'original_order_ids': small_orders['order_id'].tolist(),
                'density': total_weight_kg / total_volume_m3 if total_volume_m3 > 0 else 0,
                'cargo_source': 'small_merged',
                'processed_timestamp': pd.Timestamp.now()
            }

            merged_items.append(merged_item)

        # 转换为DataFrame
        merged_df = pd.DataFrame(merged_items)

        self.logger.info(f"小货物合并完成：{len(small_orders)}个订单 → {len(merged_df)}个虚拟货物")

        # 导出合并结果
        self._export_merged_results(merged_df, small_orders)

        return merged_df

    def _estimate_merged_dimensions(self, total_volume: float, total_quantity: int,
                                  avg_single_volume: float) -> Tuple[float, float, float]:
        """
        估算合并货物的尺寸

        Args:
            total_volume: 总体积 (m³)
            total_quantity: 总件数
            avg_single_volume: 平均单件体积 (m³)

        Returns:
            Tuple[float, float, float]: (长, 宽, 高) in meters
        """
        # 基于立方体假设的基础尺寸
        cube_side = total_volume ** (1/3)

        # 应用形状变化系数，模拟更真实的货物形状
        variation_factor = DIMENSION_ESTIMATION['shape_variation_factor']
        length_width_ratio_range = DIMENSION_ESTIMATION['length_width_ratio_range']
        height_ratio_range = DIMENSION_ESTIMATION['height_ratio_range']

        # 使用随机种子确保可重现性
        np.random.seed(hash(str(total_volume)) % (2**32))

        # 随机生成长宽比和高度比
        length_width_ratio = np.random.uniform(*length_width_ratio_range)
        height_ratio = np.random.uniform(*height_ratio_range)

        # 计算尺寸
        # 设 width = w, length = w * ratio, height = h
        # volume = w * w * ratio * h = w² * ratio * h
        # h = height_ratio * w (或其他合理关系)

        # 简化计算：基于立方体调整
        width = cube_side
        length = cube_side * length_width_ratio
        height = cube_side * height_ratio

        # 确保体积匹配
        calculated_volume = length * width * height
        if calculated_volume > 0:
            scale_factor = (total_volume / calculated_volume) ** (1/3)
            length *= scale_factor
            width *= scale_factor
            height *= scale_factor

        return round(length, 3), round(width, 3), round(height, 3)

    def _export_classification_results(self, large_orders: pd.DataFrame,
                                     medium_orders: pd.DataFrame,
                                     small_orders: pd.DataFrame) -> str:
        """
        导出分类结果到Excel文件

        Args:
            large_orders: 大货物订单
            medium_orders: 中货物订单
            small_orders: 小货物订单

        Returns:
            str: 输出文件路径
        """
        output_file = REPORTS_DIR / FILE_CONFIG['cargo_classification_file']

        try:
            with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
                # 分类汇总
                summary_data = {
                    '分类': ['大货物', '中货物', '小货物', '总计'],
                    '订单数量': [len(large_orders), len(medium_orders), len(small_orders),
                              len(large_orders) + len(medium_orders) + len(small_orders)],
                    '总体积(m³)': [
                        large_orders['order_total_volume_m3'].sum() if len(large_orders) > 0 else 0,
                        medium_orders['order_total_volume_m3'].sum() if len(medium_orders) > 0 else 0,
                        small_orders['order_total_volume_m3'].sum() if len(small_orders) > 0 else 0,
                        (large_orders['order_total_volume_m3'].sum() if len(large_orders) > 0 else 0) +
                        (medium_orders['order_total_volume_m3'].sum() if len(medium_orders) > 0 else 0) +
                        (small_orders['order_total_volume_m3'].sum() if len(small_orders) > 0 else 0)
                    ],
                    '体积占比': ['', '', '', '']
                }

                total_volume = summary_data['总体积(m³)'][3]
                if total_volume > 0:
                    for i in range(3):
                        ratio = summary_data['总体积(m³)'][i] / total_volume * 100
                        summary_data['体积占比'][i] = f"{ratio:.1f}%"
                    summary_data['体积占比'][3] = "100.0%"

                summary_df = pd.DataFrame(summary_data)
                summary_df.to_excel(writer, sheet_name='分类汇总', index=False)

                # 详细订单列表
                if len(large_orders) > 0:
                    large_orders.to_excel(writer, sheet_name='大货物订单', index=False)

                if len(medium_orders) > 0:
                    medium_orders.to_excel(writer, sheet_name='中货物订单', index=False)

                if len(small_orders) > 0:
                    small_orders.to_excel(writer, sheet_name='小货物订单', index=False)

            self.logger.info(f"货物分类结果已导出: {output_file}")
            return str(output_file)

        except Exception as e:
            self.logger.error(f"导出分类结果失败: {str(e)}")
            raise

    def _export_merged_results(self, merged_df: pd.DataFrame,
                             original_small_orders: pd.DataFrame) -> str:
        """
        导出小货物合并结果到Excel文件

        Args:
            merged_df: 合并后的虚拟货物
            original_small_orders: 原始小货物订单

        Returns:
            str: 输出文件路径
        """
        output_file = REPORTS_DIR / FILE_CONFIG['small_cargo_merged_file']

        try:
            with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
                # 合并汇总
                summary_data = {
                    '指标': ['原始小货物订单数', '合并后虚拟货物数', '合并比率', '总体积(m³)', '平均单个虚拟货物体积(m³)'],
                    '数值': [
                        len(original_small_orders),
                        len(merged_df),
                        f"{len(merged_df)/len(original_small_orders)*100:.1f}%" if len(original_small_orders) > 0 else "0%",
                        f"{merged_df['volume_m3'].sum():.6f}" if len(merged_df) > 0 else "0.000000",
                        f"{merged_df['volume_m3'].mean():.6f}" if len(merged_df) > 0 else "0.000000"
                    ]
                }
                summary_df = pd.DataFrame(summary_data)
                summary_df.to_excel(writer, sheet_name='合并汇总', index=False)

                # 合并后的虚拟货物
                if len(merged_df) > 0:
                    merged_df.to_excel(writer, sheet_name='合并后虚拟货物', index=False)

                # 原始小货物订单
                if len(original_small_orders) > 0:
                    original_small_orders.to_excel(writer, sheet_name='原始小货物订单', index=False)

            self.logger.info(f"小货物合并结果已导出: {output_file}")
            return str(output_file)

        except Exception as e:
            self.logger.error(f"导出合并结果失败: {str(e)}")
            raise

    def get_classification_summary(self, large_orders: pd.DataFrame,
                                 medium_orders: pd.DataFrame,
                                 small_orders: pd.DataFrame) -> Dict:
        """
        获取分类汇总统计信息

        Args:
            large_orders: 大货物订单
            medium_orders: 中货物订单
            small_orders: 小货物订单

        Returns:
            Dict: 分类统计信息
        """
        total_orders = len(large_orders) + len(medium_orders) + len(small_orders)
        total_volume = (
            (large_orders['order_total_volume_m3'].sum() if len(large_orders) > 0 else 0) +
            (medium_orders['order_total_volume_m3'].sum() if len(medium_orders) > 0 else 0) +
            (small_orders['order_total_volume_m3'].sum() if len(small_orders) > 0 else 0)
        )

        summary = {
            'classification_criteria': {
                'large_threshold': self.large_threshold,
                'medium_threshold': self.medium_threshold,
                'small_max': self.small_max
            },
            'large_cargo': {
                'order_count': len(large_orders),
                'total_volume_m3': large_orders['order_total_volume_m3'].sum() if len(large_orders) > 0 else 0,
                'volume_percentage': (large_orders['order_total_volume_m3'].sum() / total_volume * 100) if total_volume > 0 and len(large_orders) > 0 else 0
            },
            'medium_cargo': {
                'order_count': len(medium_orders),
                'total_volume_m3': medium_orders['order_total_volume_m3'].sum() if len(medium_orders) > 0 else 0,
                'volume_percentage': (medium_orders['order_total_volume_m3'].sum() / total_volume * 100) if total_volume > 0 and len(medium_orders) > 0 else 0
            },
            'small_cargo': {
                'order_count': len(small_orders),
                'total_volume_m3': small_orders['order_total_volume_m3'].sum() if len(small_orders) > 0 else 0,
                'volume_percentage': (small_orders['order_total_volume_m3'].sum() / total_volume * 100) if total_volume > 0 and len(small_orders) > 0 else 0
            },
            'totals': {
                'total_orders': total_orders,
                'total_volume_m3': total_volume
            }
        }

        return summary


def main():
    """测试货物分类器模块"""
    # 模拟测试数据
    test_orders = pd.DataFrame({
        'order_id': [f"ORDER_{i:04d}" for i in range(20)],
        'order_total_volume_m3': [60, 45, 30, 8, 5, 80, 25, 15, 3, 70,
                                 12, 6, 40, 2, 90, 20, 7, 35, 4, 55],
        'volume_m3': [0.5, 0.3, 0.2, 0.1, 0.05, 0.6, 0.25, 0.15, 0.03, 0.7,
                     0.12, 0.06, 0.4, 0.02, 0.9, 0.2, 0.07, 0.35, 0.04, 0.55],
        'quantity': [120, 150, 150, 80, 100, 133, 100, 100, 100, 100,
                    100, 100, 100, 100, 100, 100, 100, 100, 100, 100],
        'item_type': ['食品', '饮水', '农产品', '日用品', '食品', '饮水', '农产品', '日用品',
                     '食品', '饮水', '农产品', '日用品', '食品', '饮水', '农产品', '日用品',
                     '食品', '饮水', '农产品', '日用品'],
        'order_total_weight_kg': [i*10 for i in range(20)]
    })

    # 创建分类器并测试
    classifier = CargoClassifier()

    try:
        # 三分类
        large_orders, medium_orders, small_orders = classifier.classify_all_orders(test_orders)

        print(f"分类测试完成:")
        print(f"  大货物: {len(large_orders)} 个")
        print(f"  中货物: {len(medium_orders)} 个")
        print(f"  小货物: {len(small_orders)} 个")

        # 合并小货物
        if len(small_orders) > 0:
            merged_small = classifier.merge_small_orders(small_orders)
            print(f"  合并后虚拟货物: {len(merged_small)} 个")

        # 获取统计信息
        summary = classifier.get_classification_summary(large_orders, medium_orders, small_orders)
        print(f"总体积: {summary['totals']['total_volume_m3']:.3f} m³")

    except Exception as e:
        print(f"测试失败: {str(e)}")


if __name__ == "__main__":
    main()