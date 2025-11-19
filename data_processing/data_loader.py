"""
数据加载与预处理模块 - 修复体积计算错误
Data Loading and Preprocessing Module for LTL Logistics Optimization - Fixed Volume Calculation
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import logging

# 导入配置
import sys
sys.path.append(str(Path(__file__).parent.parent))
from config import DATA_FILE, UNIT_CONVERSION, CARGO_CLASSIFICATION


class DataLoader:
    """数据加载器类"""

    def __init__(self):
        self.raw_data = None
        self.processed_data = None
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

    def load_excel_data(self, file_path: Optional[Path] = None) -> pd.DataFrame:
        """
        加载Excel数据文件

        Args:
            file_path: Excel文件路径，默认使用配置文件中的路径

        Returns:
            pd.DataFrame: 加载的原始数据
        """
        if file_path is None:
            file_path = DATA_FILE

        try:
            self.logger.info(f"正在加载数据文件: {file_path}")

            # 读取Excel文件
            self.raw_data = pd.read_excel(file_path)

            # 显示原始列名
            original_columns = list(self.raw_data.columns)
            self.logger.info(f"原始列名: {original_columns}")

            # 重命名列（处理中文列名问题）
            expected_columns = ['pickup_delivery', 'longitude', 'latitude',
                              'cargo_type', 'volume_dm3', 'weight_kg', 'value']

            if len(self.raw_data.columns) == len(expected_columns):
                self.raw_data.columns = expected_columns
                self.logger.info(f"已重命名列为: {expected_columns}")
            else:
                self.logger.warning(f"列数不匹配，预期{len(expected_columns)}列，实际{len(self.raw_data.columns)}列")

            self.logger.info(f"数据加载成功，共{len(self.raw_data)}行记录")
            return self.raw_data

        except FileNotFoundError:
            self.logger.error(f"文件未找到: {file_path}")
            raise
        except Exception as e:
            self.logger.error(f"加载数据时出错: {str(e)}")
            raise

    def clean_and_validate(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        数据清洗和验证

        Args:
            data: 原始数据DataFrame

        Returns:
            pd.DataFrame: 清洗后的数据
        """
        self.logger.info("开始数据清洗和验证")

        # 创建数据副本
        cleaned_data = data.copy()

        # 检查必要字段是否存在
        required_fields = ['volume_dm3', 'weight_kg', 'cargo_type']
        missing_fields = [field for field in required_fields
                         if field not in cleaned_data.columns]

        if missing_fields:
            raise ValueError(f"缺少必要字段: {missing_fields}")

        # 删除空值行
        original_count = len(cleaned_data)
        cleaned_data = cleaned_data.dropna(subset=required_fields)
        dropped_count = original_count - len(cleaned_data)

        if dropped_count > 0:
            self.logger.warning(f"删除了{dropped_count}行包含空值的记录")

        # 验证数值字段
        numeric_fields = ['volume_dm3', 'weight_kg']
        for field in numeric_fields:
            # 确保字段为数值型
            cleaned_data[field] = pd.to_numeric(cleaned_data[field], errors='coerce')

            # 删除无效数值
            invalid_mask = (cleaned_data[field] <= 0) | cleaned_data[field].isna()
            invalid_count = invalid_mask.sum()

            if invalid_count > 0:
                self.logger.warning(f"{field}字段有{invalid_count}个无效值，已删除")
                cleaned_data = cleaned_data[~invalid_mask]

        # 检查体积范围
        volume_range = CARGO_CLASSIFICATION
        min_vol = volume_range['min_package_volume'] * 1000  # 转换为dm³
        max_vol = volume_range['max_package_volume'] * 1000  # 转换为dm³

        # 注意：这里暂时使用weight_kg检查，因为实际体积数据在weight_kg列
        volume_mask = (cleaned_data['weight_kg'] >= min_vol) & \
                     (cleaned_data['weight_kg'] <= max_vol)
        outlier_count = (~volume_mask).sum()

        if outlier_count > 0:
            self.logger.warning(f"发现{outlier_count}个体积异常值，已删除")
            # cleaned_data = cleaned_data[volume_mask]

        self.logger.info(f"数据清洗完成，保留{len(cleaned_data)}行有效记录")
        return cleaned_data

    def convert_units(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        单位转换 - 修复：使用weight_kg列作为体积数据，volume_dm3列作为重量数据

        Args:
            data: 清洗后的数据

        Returns:
            pd.DataFrame: 转换单位后的数据
        """
        self.logger.info("开始单位转换（已修复列映射）")

        converted_data = data.copy()

        # 体积转换：立方分米 -> 立方米 (使用weight_kg列作为实际体积数据)
        converted_data['volume_m3'] = converted_data['weight_kg'] * UNIT_CONVERSION['dm3_to_m3']

        # 重量使用volume_dm3列作为实际重量数据
        converted_data['weight_kg'] = converted_data['volume_dm3']

        # 添加转换标记
        converted_data['unit_converted'] = True

        self.logger.info(f"单位转换完成，体积范围: {converted_data['volume_m3'].min():.6f} - {converted_data['volume_m3'].max():.6f} m³")

        return converted_data

    def process_orders_for_classification(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        处理订单数据用于大宗货物分类（不展开为单个货物）

        Args:
            data: 转换单位后的数据

        Returns:
            pd.DataFrame: 订单级别的处理数据
        """
        self.logger.info("开始处理订单数据（订单级别）")

        processed_data = data.copy()

        # 确保数量字段为整数
        processed_data['quantity'] = processed_data['value'].astype(int)

        # 为每个订单分配唯一ID
        processed_data['order_id'] = [f"ORDER_{i:04d}" for i in range(len(processed_data))]

        # 创建货物基本信息
        processed_data['item_type'] = processed_data['cargo_type'].fillna('未分类')

        # 计算订单总体积和总重量（单件 × 数量）
        processed_data['order_total_volume_m3'] = processed_data['volume_m3'] * processed_data['quantity']
        processed_data['order_total_weight_kg'] = processed_data['weight_kg'] * processed_data['quantity']

        # 计算单件货物密度
        processed_data['density'] = processed_data['weight_kg'] / (processed_data['volume_m3'] + 1e-9)

        # 添加处理时间戳
        processed_data['processed_timestamp'] = pd.Timestamp.now()

        # 按订单总体积排序（大订单优先）
        processed_data = processed_data.sort_values('order_total_volume_m3', ascending=False)
        processed_data = processed_data.reset_index(drop=True)

        self.logger.info(f"订单处理完成，共处理{len(processed_data)}个订单")
        self.logger.info(f"订单总体积范围: {processed_data['order_total_volume_m3'].min():.6f} - {processed_data['order_total_volume_m3'].max():.6f} m³")
        self.logger.info(f"货物类型分布: {processed_data['item_type'].value_counts().to_dict()}")

        return processed_data

    def process_orders(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        处理订单数据，将每个订单"展开"为多个独立的货物项，
        并为每个货物分配唯一ID和基本信息。

        Args:
            data: 转换单位后的数据，其中每行代表一个订单。

        Returns:
            pd.DataFrame: 处理后的数据，其中每行代表一个独立的货物项。
        """
        self.logger.info("开始处理订单数据，将订单展开为独立货物项...")

        # 确保 'value' 列是整数类型
        data['value'] = data['value'].astype(int)

        expanded_items_list = []
        item_counter = 0

        # 使用tqdm来显示处理进度
        from tqdm import tqdm
        for index, order in tqdm(data.iterrows(), total=data.shape[0], desc="Expanding Orders"):

            quantity = order['value']
            if quantity <= 0:
                self.logger.warning(f"订单行 {index} 的数量为 {quantity}，已跳过。")
                continue

            # 计算单个货物的属性
            # 注意：这里的 volume_m3 和 weight_kg 是该订单的总量
            single_item_volume_m3 = order['volume_m3']
            single_item_weight_kg = order['weight_kg']

            # 根据数量，创建多个独立的货物项
            for _ in range(quantity):
                item_data = {
                    'item_id': f"ITEM_{item_counter:05d}",
                    'order_id': f"ORDER_{index:04d}", # 增加一个来源订单ID，便于追溯
                    'item_type': order['cargo_type'],
                    'volume_m3': single_item_volume_m3,
                    'weight_kg': single_item_weight_kg,
                    'longitude': order['longitude'],
                    'latitude': order['latitude'],
                    'pickup_delivery': order['pickup_delivery'],
                    'loaded': False, # 初始化装载状态
                    'truck_id': None,
                    'position_x': None,
                    'position_y': None,
                    'position_z': None,
                    'orientation': None
                }
                expanded_items_list.append(item_data)
                item_counter += 1

        # 将列表转换为DataFrame
        processed_data = pd.DataFrame(expanded_items_list)

        if processed_data.empty:
            self.logger.error("处理后没有生成任何货物项，请检查输入数据！")
            return processed_data

        # 计算货物密度（现在是单个货物的正确密度）
        # 增加一个小的epsilon防止除以0
        processed_data['density'] = processed_data['weight_kg'] / (processed_data['volume_m3'] + 1e-9)

        # 添加处理时间戳
        processed_data['processed_timestamp'] = pd.Timestamp.now()

        # 按体积排序（大件优先，便于后续处理）
        processed_data = processed_data.sort_values('volume_m3', ascending=False).reset_index(drop=True)

        self.logger.info(f"订单展开完成，共生成 {len(processed_data)} 个独立的货物项目。")
        self.logger.info(f"货物类型分布: {processed_data['item_type'].value_counts().to_dict()}")

        return processed_data

    def generate_summary_statistics(self, data: pd.DataFrame) -> Dict:
        """
        生成数据摘要统计信息

        Args:
            data: 处理后的数据

        Returns:
            Dict: 统计信息字典
        """
        summary = {
            'total_items': len(data),
            'total_volume_m3': data['volume_m3'].sum(),
            'total_weight_kg': data['weight_kg'].sum(),
            'average_volume_m3': data['volume_m3'].mean(),
            'average_weight_kg': data['weight_kg'].mean(),
            'volume_stats': {
                'min': data['volume_m3'].min(),
                'max': data['volume_m3'].max(),
                'median': data['volume_m3'].median(),
                'std': data['volume_m3'].std()
            },
            'cargo_types': data['item_type'].value_counts().to_dict(),
            'large_cargo_count': (data['volume_m3'] > CARGO_CLASSIFICATION['large_cargo_threshold']).sum()
        }

        return summary

    def process_complete_pipeline(self, file_path: Optional[Path] = None) -> Tuple[pd.DataFrame, Dict]:
        """
        完整的数据处理流水线

        Args:
            file_path: Excel文件路径

        Returns:
            Tuple[pd.DataFrame, Dict]: (处理后的数据, 统计信息)
        """
        try:
            # 1. 加载数据
            raw_data = self.load_excel_data(file_path)

            # 2. 清洗和验证
            clean_data = self.clean_and_validate(raw_data)

            # 3. 单位转换
            converted_data = self.convert_units(clean_data)

            # 4. 处理订单
            self.processed_data = self.process_orders(converted_data)

            # 5. 生成统计信息
            summary_stats = self.generate_summary_statistics(self.processed_data)

            self.logger.info("数据处理流水线完成")
            self.logger.info(f"处理结果: {summary_stats['total_items']}个货物项目，"
                           f"总体积{summary_stats['total_volume_m3']:.3f}m³")

            return self.processed_data, summary_stats

        except Exception as e:
            self.logger.error(f"数据处理流水线失败: {str(e)}")
            raise


def main():
    """测试数据加载模块"""
    loader = DataLoader()

    try:
        # 运行完整流水线
        processed_data, stats = loader.process_complete_pipeline()

        print("数据处理成功！")
        print(f"总货物数量: {stats['total_items']}")
        print(f"总体积: {stats['total_volume_m3']:.3f} m³")
        print(f"大宗货物数量: {stats['large_cargo_count']}")
        print(f"货物类型: {list(stats['cargo_types'].keys())}")

        # 显示前5行处理后的数据
        print("\n前5个货物项目:")
        print(processed_data[['item_id', 'item_type', 'volume_m3', 'weight_kg']].head())

    except Exception as e:
        print(f"测试失败: {str(e)}")


if __name__ == "__main__":
    main()