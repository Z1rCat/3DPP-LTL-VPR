"""
尺寸估算模块
Dimension Estimation Module for Converting Volume to 3D Dimensions
"""

import numpy as np
import pandas as pd
from typing import Tuple, List, Dict, Optional
import logging
import random
from pathlib import Path

# 导入配置
import sys
sys.path.append(str(Path(__file__).parent.parent))
from config import DIMENSION_ESTIMATION


class DimensionEstimator:
    """三维尺寸估算器类"""

    def __init__(self, random_seed: Optional[int] = None):
        """
        初始化尺寸估算器

        Args:
            random_seed: 随机种子，确保结果可重现
        """
        self.config = DIMENSION_ESTIMATION
        self.random_seed = random_seed or self.config['random_seed']
        self.logger = self._setup_logger()

        # 设置随机种子
        np.random.seed(self.random_seed)
        random.seed(self.random_seed)

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

    def estimate_dimensions(self, volume: float, item_id: str = "") -> Tuple[float, float, float]:
        """
        基于体积估算三维尺寸

        Args:
            volume: 货物体积 (m³)
            item_id: 货物ID（用于调试）

        Returns:
            Tuple[float, float, float]: (长度, 宽度, 高度) in meters
        """
        if volume <= 0:
            raise ValueError(f"体积必须大于0，当前值: {volume}")

        # 检查是否生成立方体
        if np.random.random() < self.config['cube_probability']:
            return self._generate_cube_dimensions(volume)
        else:
            return self._generate_rectangular_dimensions(volume)

    def _generate_cube_dimensions(self, volume: float) -> Tuple[float, float, float]:
        """
        生成立方体尺寸

        Args:
            volume: 体积

        Returns:
            Tuple[float, float, float]: (长度, 宽度, 高度)
        """
        # 立方体边长 = 立方根(体积)
        side_length = np.cbrt(volume)

        # 添加小量随机扰动（保持接近立方体）
        variation = self.config['shape_variation_factor']
        length = side_length * np.random.uniform(1 - variation, 1 + variation)
        width = side_length * np.random.uniform(1 - variation, 1 + variation)

        # 根据长宽计算高度以保证体积守恒
        height = volume / (length * width)

        return self._validate_and_adjust_dimensions(length, width, height, volume)

    def _generate_rectangular_dimensions(self, volume: float) -> Tuple[float, float, float]:
        """
        生成长方体尺寸

        Args:
            volume: 体积

        Returns:
            Tuple[float, float, float]: (长度, 宽度, 高度)
        """
        # 生成长宽比
        length_width_ratio = np.random.uniform(
            *self.config['length_width_ratio_range']
        )

        # 生成高度比例系数
        height_ratio = np.random.uniform(
            *self.config['height_ratio_range']
        )

        # 基准尺寸：假设宽度为立方根的某个比例
        base_dimension = np.cbrt(volume)

        # 计算各维度
        width = base_dimension / np.cbrt(length_width_ratio * height_ratio)
        length = width * length_width_ratio
        height = width * height_ratio

        # 微调以保证精确的体积守恒
        calculated_volume = length * width * height
        scale_factor = np.cbrt(volume / calculated_volume)

        length *= scale_factor
        width *= scale_factor
        height *= scale_factor

        return self._validate_and_adjust_dimensions(length, width, height, volume)

    def _validate_and_adjust_dimensions(self, length: float, width: float,
                                      height: float, target_volume: float) -> Tuple[float, float, float]:
        """
        验证并调整尺寸以确保合理性和体积守恒

        Args:
            length, width, height: 初始尺寸
            target_volume: 目标体积

        Returns:
            Tuple[float, float, float]: 调整后的(长度, 宽度, 高度)
        """
        # 确保所有尺寸为正
        length = max(length, 0.01)  # 最小1cm
        width = max(width, 0.01)
        height = max(height, 0.01)

        # 检查尺寸比例的合理性
        dimensions = [length, width, height]
        dimensions.sort()  # 排序: 最小, 中等, 最大

        min_dim, mid_dim, max_dim = dimensions

        # 确保最大尺寸不会过于极端
        if max_dim / min_dim > 20:  # 长宽比不超过20:1
            # 重新分配尺寸
            target_ratio = 10  # 目标最大比例
            adjustment_factor = np.cbrt(target_ratio / (max_dim / min_dim))

            if length == max_dim:
                length = min_dim * target_ratio
                width = mid_dim * adjustment_factor
                height = target_volume / (length * width)
            elif width == max_dim:
                width = min_dim * target_ratio
                length = mid_dim * adjustment_factor
                height = target_volume / (length * width)
            else:  # height == max_dim
                height = min_dim * target_ratio
                length = mid_dim * adjustment_factor
                width = target_volume / (length * height)

        # 最终体积校正
        actual_volume = length * width * height
        volume_error = abs(actual_volume - target_volume) / target_volume

        if volume_error > 0.001:  # 0.1%误差阈值
            scale_factor = np.cbrt(target_volume / actual_volume)
            length *= scale_factor
            width *= scale_factor
            height *= scale_factor

        return round(length, 4), round(width, 4), round(height, 4)

    def generate_shape_variations(self, volume: float, count: int = 1) -> List[Tuple[float, float, float]]:
        """
        为同一体积生成多个形状变体

        Args:
            volume: 体积
            count: 变体数量

        Returns:
            List[Tuple[float, float, float]]: 尺寸变体列表
        """
        variations = []
        for i in range(count):
            # 为每个变体使用不同的随机种子
            temp_seed = self.random_seed + i
            np.random.seed(temp_seed)
            random.seed(temp_seed)

            dimensions = self.estimate_dimensions(volume, f"variant_{i}")
            variations.append(dimensions)

        # 恢复原始随机种子
        np.random.seed(self.random_seed)
        random.seed(self.random_seed)

        return variations

    def validate_dimensions(self, length: float, width: float, height: float) -> Dict:
        """
        验证尺寸的合理性

        Args:
            length, width, height: 三维尺寸

        Returns:
            Dict: 验证结果
        """
        volume = length * width * height
        dimensions = sorted([length, width, height])
        min_dim, mid_dim, max_dim = dimensions

        validation_result = {
            'volume': volume,
            'aspect_ratio': max_dim / min_dim if min_dim > 0 else float('inf'),
            'is_reasonable': True,
            'warnings': []
        }

        # 检查尺寸合理性
        if min_dim < 0.01:  # 小于1cm
            validation_result['warnings'].append(f"存在过小尺寸: {min_dim:.4f}m")
            validation_result['is_reasonable'] = False

        if max_dim > 5.0:  # 大于5m
            validation_result['warnings'].append(f"存在过大尺寸: {max_dim:.4f}m")
            validation_result['is_reasonable'] = False

        if validation_result['aspect_ratio'] > 20:
            validation_result['warnings'].append(f"长宽比过大: {validation_result['aspect_ratio']:.1f}:1")
            validation_result['is_reasonable'] = False

        if volume < 0.000001 or volume > 100:  # 1cm³ ~ 100m³
            validation_result['warnings'].append(f"体积异常: {volume:.6f}m³")
            validation_result['is_reasonable'] = False

        return validation_result

    def estimate_batch_dimensions(self, volumes: List[float],
                                item_ids: Optional[List[str]] = None) -> pd.DataFrame:
        """
        批量估算尺寸

        Args:
            volumes: 体积列表
            item_ids: 货物ID列表

        Returns:
            pd.DataFrame: 包含尺寸信息的DataFrame
        """
        if item_ids is None:
            item_ids = [f"ITEM_{i:04d}" for i in range(len(volumes))]

        if len(volumes) != len(item_ids):
            raise ValueError("体积数量与ID数量不匹配")

        self.logger.info(f"开始批量估算{len(volumes)}个货物的尺寸")

        results = []
        failed_count = 0

        for i, (volume, item_id) in enumerate(zip(volumes, item_ids)):
            try:
                # 估算尺寸
                length, width, height = self.estimate_dimensions(volume, item_id)

                # 验证结果
                validation = self.validate_dimensions(length, width, height)

                result = {
                    'item_id': item_id,
                    'original_volume': volume,
                    'estimated_length': length,
                    'estimated_width': width,
                    'estimated_height': height,
                    'calculated_volume': length * width * height,
                    'volume_error': abs(length * width * height - volume) / volume,
                    'aspect_ratio': validation['aspect_ratio'],
                    'is_reasonable': validation['is_reasonable'],
                    'warnings': '; '.join(validation['warnings']) if validation['warnings'] else None
                }

                results.append(result)

            except Exception as e:
                self.logger.error(f"估算货物{item_id}尺寸时失败: {str(e)}")
                failed_count += 1

        self.logger.info(f"批量尺寸估算完成，成功{len(results)}个，失败{failed_count}个")

        results_df = pd.DataFrame(results)

        # 统计信息
        if len(results_df) > 0:
            reasonable_count = results_df['is_reasonable'].sum()
            avg_volume_error = results_df['volume_error'].mean()
            max_aspect_ratio = results_df['aspect_ratio'].max()

            self.logger.info(f"合理尺寸比例: {reasonable_count}/{len(results_df)} "
                           f"({100*reasonable_count/len(results_df):.1f}%)")
            self.logger.info(f"平均体积误差: {avg_volume_error:.6f} ({100*avg_volume_error:.4f}%)")
            self.logger.info(f"最大长宽比: {max_aspect_ratio:.1f}:1")

        return results_df

    def add_dimensions_to_dataframe(self, df: pd.DataFrame,
                                  volume_column: str = 'volume_m3',
                                  id_column: str = 'item_id') -> pd.DataFrame:
        """
        为DataFrame添加尺寸信息

        Args:
            df: 包含体积信息的DataFrame
            volume_column: 体积列名
            id_column: ID列名

        Returns:
            pd.DataFrame: 添加了尺寸信息的DataFrame
        """
        if volume_column not in df.columns:
            raise ValueError(f"DataFrame中没有找到列: {volume_column}")

        if id_column not in df.columns:
            raise ValueError(f"DataFrame中没有找到列: {id_column}")

        # 提取体积和ID
        volumes = df[volume_column].tolist()
        item_ids = df[id_column].tolist()

        # 批量估算尺寸
        dimensions_df = self.estimate_batch_dimensions(volumes, item_ids)

        # 合并结果
        merged_df = df.merge(dimensions_df[['item_id', 'estimated_length',
                                          'estimated_width', 'estimated_height',
                                          'calculated_volume', 'volume_error',
                                          'aspect_ratio', 'is_reasonable']],
                           left_on=id_column, right_on='item_id', how='left')

        return merged_df


def main():
    """测试尺寸估算模块"""
    estimator = DimensionEstimator()

    print("测试尺寸估算模块")

    # 测试单个体积
    test_volumes = [0.001, 0.01, 0.1, 1.0, 10.0]

    for volume in test_volumes:
        try:
            length, width, height = estimator.estimate_dimensions(volume)
            calculated_vol = length * width * height
            error = abs(calculated_vol - volume) / volume

            print(f"\n体积: {volume:.3f} m³")
            print(f"尺寸: {length:.3f} × {width:.3f} × {height:.3f} m")
            print(f"计算体积: {calculated_vol:.6f} m³")
            print(f"误差: {error:.6f} ({100*error:.4f}%)")

            # 验证尺寸
            validation = estimator.validate_dimensions(length, width, height)
            print(f"合理性: {validation['is_reasonable']}")
            if validation['warnings']:
                print(f"警告: {validation['warnings']}")

        except Exception as e:
            print(f"测试体积 {volume} 时出错: {str(e)}")

    # 测试批量处理
    print("\n\n测试批量处理:")
    test_volumes_batch = [0.005, 0.015, 0.025, 0.035, 0.045]
    test_ids = [f"TEST_{i}" for i in range(len(test_volumes_batch))]

    results_df = estimator.estimate_batch_dimensions(test_volumes_batch, test_ids)
    print(results_df[['item_id', 'original_volume', 'estimated_length',
                     'estimated_width', 'estimated_height', 'volume_error']])


if __name__ == "__main__":
    main()