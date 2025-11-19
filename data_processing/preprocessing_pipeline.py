"""
数据预处理流水线
Complete Data Preprocessing Pipeline for LTL Logistics Optimization
"""

import pandas as pd
import pickle
import logging
from pathlib import Path
from typing import Dict, Tuple
from tqdm import tqdm

# 导入模块
from data_processing.data_loader import DataLoader
from data_processing.dimension_estimator import DimensionEstimator
from config import INTERMEDIATE_DIR, FILE_CONFIG, create_directories


class PreprocessingPipeline:
    """数据预处理流水线类"""

    def __init__(self):
        """初始化预处理流水线"""
        self.data_loader = DataLoader()
        self.dimension_estimator = DimensionEstimator()
        self.logger = self._setup_logger()

        # 确保输出目录存在
        create_directories()

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

    def run_complete_preprocessing(self) -> Tuple[pd.DataFrame, Dict]:
        """
        运行完整的预处理流水线

        Returns:
            Tuple[pd.DataFrame, Dict]: (处理后的数据, 统计信息)
        """
        self.logger.info("开始运行完整数据预处理流水线")

        try:
            # 阶段1: 数据加载和预处理
            self.logger.info("阶段1: 数据加载和预处理")
            processed_data, basic_stats = self.data_loader.process_complete_pipeline()

            # 阶段2: 尺寸估算
            self.logger.info("阶段2: 为所有货物估算三维尺寸")

            # 使用tqdm显示进度条
            tqdm.pandas(desc="估算货物尺寸")

            # 添加尺寸信息
            enhanced_data = self.dimension_estimator.add_dimensions_to_dataframe(
                processed_data,
                volume_column='volume_m3',
                id_column='item_id'
            )

            # 阶段3: 数据验证和清理
            self.logger.info("阶段3: 数据验证和最终清理")
            final_data = self._final_data_cleanup(enhanced_data)

            # 阶段4: 生成完整统计信息
            complete_stats = self._generate_complete_statistics(final_data, basic_stats)

            # 阶段5: 保存处理结果
            self.logger.info("阶段5: 保存预处理结果")
            self._save_processed_data(final_data, complete_stats)

            self.logger.info("数据预处理流水线完成")
            return final_data, complete_stats

        except Exception as e:
            self.logger.error(f"数据预处理流水线失败: {str(e)}")
            raise

    def _final_data_cleanup(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        最终数据清理和验证

        Args:
            data: 包含尺寸信息的数据

        Returns:
            pd.DataFrame: 清理后的最终数据
        """
        self.logger.info("开始最终数据清理")

        cleaned_data = data.copy()
        original_count = len(cleaned_data)

        # 删除尺寸不合理的货物
        if 'is_reasonable' in cleaned_data.columns:
            unreasonable_mask = cleaned_data['is_reasonable'] == False
            unreasonable_count = unreasonable_mask.sum()

            if unreasonable_count > 0:
                self.logger.warning(f"删除{unreasonable_count}个尺寸不合理的货物")
                cleaned_data = cleaned_data[~unreasonable_mask]

        # 检查必要字段
        required_fields = [
            'item_id', 'volume_m3', 'weight_kg', 'item_type',
            'estimated_length', 'estimated_width', 'estimated_height'
        ]

        missing_fields = [field for field in required_fields
                         if field not in cleaned_data.columns]

        if missing_fields:
            raise ValueError(f"缺少必要字段: {missing_fields}")

        # 重新排序和重置索引
        cleaned_data = cleaned_data.sort_values(['volume_m3'], ascending=False)
        cleaned_data = cleaned_data.reset_index(drop=True)

        # 更新货物ID（确保连续性）
        cleaned_data['item_id'] = [f"ITEM_{i:04d}" for i in range(len(cleaned_data))]

        cleaned_count = len(cleaned_data)
        self.logger.info(f"最终数据清理完成: {original_count} -> {cleaned_count} 个货物")

        return cleaned_data

    def _generate_complete_statistics(self, data: pd.DataFrame, basic_stats: Dict) -> Dict:
        """
        生成完整的统计信息

        Args:
            data: 最终处理后的数据
            basic_stats: 基础统计信息

        Returns:
            Dict: 完整统计信息
        """
        complete_stats = basic_stats.copy()

        # 更新基本统计
        complete_stats.update({
            'final_item_count': len(data),
            'final_total_volume_m3': data['volume_m3'].sum(),
            'final_total_weight_kg': data['weight_kg'].sum(),
        })

        # 尺寸统计
        complete_stats['dimension_stats'] = {
            'average_length': data['estimated_length'].mean(),
            'average_width': data['estimated_width'].mean(),
            'average_height': data['estimated_height'].mean(),
            'length_range': (data['estimated_length'].min(), data['estimated_length'].max()),
            'width_range': (data['estimated_width'].min(), data['estimated_width'].max()),
            'height_range': (data['estimated_height'].min(), data['estimated_height'].max()),
            'volume_error_stats': {
                'mean': data['volume_error'].mean(),
                'max': data['volume_error'].max(),
                'std': data['volume_error'].std()
            }
        }

        # 形状分析
        if 'aspect_ratio' in data.columns:
            complete_stats['shape_analysis'] = {
                'average_aspect_ratio': data['aspect_ratio'].mean(),
                'max_aspect_ratio': data['aspect_ratio'].max(),
                'compact_items_count': (data['aspect_ratio'] <= 2.0).sum(),  # 近似立方体
                'elongated_items_count': (data['aspect_ratio'] > 5.0).sum()   # 细长物品
            }

        # 大宗货物分析
        from config import CARGO_CLASSIFICATION
        large_threshold = CARGO_CLASSIFICATION['large_cargo_threshold']
        large_cargo_mask = data['volume_m3'] > large_threshold

        complete_stats['large_cargo_analysis'] = {
            'large_cargo_count': large_cargo_mask.sum(),
            'large_cargo_total_volume': data[large_cargo_mask]['volume_m3'].sum(),
            'small_cargo_count': (~large_cargo_mask).sum(),
            'small_cargo_total_volume': data[~large_cargo_mask]['volume_m3'].sum()
        }

        return complete_stats

    def _save_processed_data(self, data: pd.DataFrame, stats: Dict):
        """
        保存处理后的数据

        Args:
            data: 处理后的数据
            stats: 统计信息
        """
        # 保存主数据文件
        processed_file_path = INTERMEDIATE_DIR / FILE_CONFIG['processed_items_file']

        with open(processed_file_path, 'wb') as f:
            pickle.dump({
                'data': data,
                'statistics': stats,
                'metadata': {
                    'processing_timestamp': pd.Timestamp.now(),
                    'total_items': len(data),
                    'columns': list(data.columns),
                    'data_types': data.dtypes.to_dict()
                }
            }, f)

        self.logger.info(f"已保存处理后的数据到: {processed_file_path}")

        # 同时保存CSV版本用于检查
        csv_path = INTERMEDIATE_DIR / "processed_items.csv"
        data.to_csv(csv_path, index=False, encoding='utf-8-sig')
        self.logger.info(f"已保存CSV版本到: {csv_path}")

        # 保存统计摘要
        stats_file = INTERMEDIATE_DIR / "preprocessing_statistics.txt"
        self._save_statistics_summary(stats, stats_file)

    def _save_statistics_summary(self, stats: Dict, file_path: Path):
        """
        保存统计摘要到文本文件

        Args:
            stats: 统计信息
            file_path: 保存路径
        """
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write("=" * 60 + "\n")
            f.write("数据预处理统计摘要\n")
            f.write("=" * 60 + "\n\n")

            f.write(f"最终货物数量: {stats['final_item_count']}\n")
            f.write(f"总体积: {stats['final_total_volume_m3']:.6f} m³\n")
            f.write(f"总重量: {stats['final_total_weight_kg']:.2f} kg\n\n")

            if 'dimension_stats' in stats:
                ds = stats['dimension_stats']
                f.write("尺寸统计:\n")
                f.write(f"  平均长度: {ds['average_length']:.3f} m\n")
                f.write(f"  平均宽度: {ds['average_width']:.3f} m\n")
                f.write(f"  平均高度: {ds['average_height']:.3f} m\n")
                f.write(f"  长度范围: {ds['length_range'][0]:.3f} - {ds['length_range'][1]:.3f} m\n")
                f.write(f"  宽度范围: {ds['width_range'][0]:.3f} - {ds['width_range'][1]:.3f} m\n")
                f.write(f"  高度范围: {ds['height_range'][0]:.3f} - {ds['height_range'][1]:.3f} m\n")
                f.write(f"  平均体积误差: {ds['volume_error_stats']['mean']:.6f}\n\n")

            if 'shape_analysis' in stats:
                sa = stats['shape_analysis']
                f.write("形状分析:\n")
                f.write(f"  平均长宽比: {sa['average_aspect_ratio']:.2f}:1\n")
                f.write(f"  最大长宽比: {sa['max_aspect_ratio']:.2f}:1\n")
                f.write(f"  紧凑型货物: {sa['compact_items_count']} 个\n")
                f.write(f"  细长型货物: {sa['elongated_items_count']} 个\n\n")

            if 'large_cargo_analysis' in stats:
                lca = stats['large_cargo_analysis']
                f.write("货物规模分析:\n")
                f.write(f"  大宗货物数量: {lca['large_cargo_count']} 个\n")
                f.write(f"  大宗货物总体积: {lca['large_cargo_total_volume']:.6f} m³\n")
                f.write(f"  零担货物数量: {lca['small_cargo_count']} 个\n")
                f.write(f"  零担货物总体积: {lca['small_cargo_total_volume']:.6f} m³\n")

        self.logger.info(f"已保存统计摘要到: {file_path}")

    def load_processed_data(self) -> Tuple[pd.DataFrame, Dict, Dict]:
        """
        加载已处理的数据

        Returns:
            Tuple[pd.DataFrame, Dict, Dict]: (数据, 统计信息, 元数据)
        """
        processed_file_path = INTERMEDIATE_DIR / FILE_CONFIG['processed_items_file']

        if not processed_file_path.exists():
            raise FileNotFoundError(f"处理后的数据文件不存在: {processed_file_path}")

        with open(processed_file_path, 'rb') as f:
            loaded_data = pickle.load(f)

        self.logger.info(f"已加载处理后的数据，共{len(loaded_data['data'])}个货物项目")

        return loaded_data['data'], loaded_data['statistics'], loaded_data['metadata']


def main():
    """运行预处理流水线"""
    pipeline = PreprocessingPipeline()

    try:
        print("开始数据预处理流水线...")
        processed_data, stats = pipeline.run_complete_preprocessing()

        print(f"\n预处理完成!")
        print(f"处理货物数量: {len(processed_data)}")
        print(f"总体积: {stats['final_total_volume_m3']:.6f} m³")
        print(f"平均体积误差: {stats['dimension_stats']['volume_error_stats']['mean']:.6f}")

        # 显示前5个货物
        print("\n前5个货物的信息:")
        display_columns = ['item_id', 'item_type', 'volume_m3',
                          'estimated_length', 'estimated_width', 'estimated_height']
        print(processed_data[display_columns].head())

        print(f"\n数据已保存到: {INTERMEDIATE_DIR / FILE_CONFIG['processed_items_file']}")

    except Exception as e:
        print(f"预处理失败: {str(e)}")


if __name__ == "__main__":
    main()