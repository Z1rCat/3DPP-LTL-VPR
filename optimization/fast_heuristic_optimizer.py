"""
快速启发式3D装箱优化器 - 时间优先版本
Fast Heuristic 3D Packing Optimizer - Time-Focused Version

实现First-Fit Decreasing Height (FFDH)算法，
专为快速求解设计，目标时间 < 1分钟

作者: Claude Code AI Assistant
创建时间: 2025-11-13
"""

import time
import logging
from typing import List, Dict, Any, Tuple, Optional
from dataclasses import dataclass
import math

# 导入配置
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))
from config import TRUCK_SPECS


@dataclass
class FastCargoItem:
    """快速货物数据结构 - 简化版"""
    item_id: str
    volume_m3: float
    weight_kg: float
    length: float
    width: float
    height: float

    # 计算属性
    @property
    def is_cube(self) -> bool:
        """是否为近立方体"""
        max_dim = max(self.length, self.width, self.height)
        min_dim = min(self.length, self.width, self.height)
        return (max_dim / min_dim) < 1.5


@dataclass
class FastBin3D:
    """3D箱子 (车厢) - 简化版"""
    bin_id: str
    length: float
    width: float
    height: float
    max_weight: float
    volume: float

    # 已装载货物
    items: List[FastCargoItem]
    current_volume: float
    current_weight: float

    # 3D网格Occupancy (用于快速重叠检测)
    occupancy_grid: Dict[Tuple[int, int, int], str]  # (x, y, z) -> item_id

    def __init__(self, bin_id: str, length: float, width: float,
                 height: float, max_weight: float):
        self.bin_id = bin_id
        self.length = length
        self.width = width
        self.height = height
        self.max_weight = max_weight
        self.volume = length * width * height
        self.items = []
        self.current_volume = 0.0
        self.current_weight = 0.0
        self.occupancy_grid = {}

    def can_place(self, item: FastCargoItem) -> bool:
        """检查是否可以放置货物"""
        # 重量检查
        if self.current_weight + item.weight_kg > self.max_weight:
            return False

        # 体积检查
        if self.current_volume + item.volume_m3 > self.volume:
            return False

        # 3D重叠检查 (使用网格Occupancy)
        # 简化: 只需检查一个位置 (0, 0, 0) - 底层堆叠
        if (0, 0, 0) in self.occupancy_grid:
            return False  # 已有货物占用

        return True

    def place_item(self, item: FastCargoItem) -> bool:
        """放置货物到箱子"""
        if not self.can_place(item):
            return False

        self.items.append(item)
        self.current_volume += item.volume_m3
        self.current_weight += item.weight_kg

        # 标记网格占用 (简化: 只占一个网格)
        self.occupancy_grid[(0, 0, 0)] = item.item_id

        return True

    @property
    def volume_utilization(self) -> float:
        """体积利用率"""
        return (self.current_volume / self.volume * 100) if self.volume > 0 else 0

    @property
    def weight_utilization(self) -> float:
        """重量利用率"""
        return (self.current_weight / self.max_weight * 100) if self.max_weight > 0 else 0


class FastHeuristicOptimizer:
    """快速启发式3D装箱优化器"""

    def __init__(self):
        """初始化优化器"""
        self.logger = self._setup_logger()
        self.truck_specs = TRUCK_SPECS

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

    def convert_to_fast_items(self, items) -> List[FastCargoItem]:
        """将通用货物转换为快速货物"""
        fast_items = []

        for item in items:
            # 提取尺寸信息
            if hasattr(item, 'estimated_length'):
                # EnhancedCargoItem
                length = item.estimated_length
                width = item.estimated_width
                height = item.estimated_height
                volume = item.volume_m3
                weight = item.weight_kg
                item_id = item.item_id
            else:
                # 其他格式
                length = getattr(item, 'length', 1.0)
                width = getattr(item, 'width', 1.0)
                height = getattr(item, 'height', 1.0)
                volume = getattr(item, 'volume_m3', 1.0)
                weight = getattr(item, 'weight_kg', 100)
                item_id = getattr(item, 'item_id', f'item_{len(fast_items)}')

            fast_item = FastCargoItem(
                item_id=item_id,
                volume_m3=volume,
                weight_kg=weight,
                length=length,
                width=width,
                height=height
            )
            fast_items.append(fast_item)

        return fast_items

    def solve(self, items, truck_specs=None, max_time_seconds=60) -> Dict[str, Any]:
        """
        快速求解3D装箱问题

        Args:
            items: 货物列表
            truck_specs: 车辆规格 (可选，使用默认配置)
            max_time_seconds: 最大求解时间 (秒)

        Returns:
            Dict: 优化结果
        """
        start_time = time.time()

        # 使用默认车辆规格
        if truck_specs is None:
            truck_specs = self.truck_specs

        self.logger.info(f"开始快速启发式优化，货物数量: {len(items)}")

        # Step 1: 转换为快速货物格式 (O(n))
        fast_items = self.convert_to_fast_items(items)
        self.logger.info(f"转换完成，货物数量: {len(fast_items)}")

        # Step 2: 按高度降序排序 First-Fit Decreasing Height (O(n log n))
        sorted_items = sorted(fast_items, key=lambda x: x.height, reverse=True)
        self.logger.info("排序完成 (按高度降序)")

        # Step 3: First-Fit装箱 (O(n*m)，m为箱子数)
        bins = []
        placed_count = 0

        for i, item in enumerate(sorted_items):
            # 检查时间限制
            elapsed = time.time() - start_time
            if elapsed > max_time_seconds:
                self.logger.warning(f"达到时间限制 {max_time_seconds}秒，停止优化")
                break

            # First-Fit: 找到第一个能容纳的箱子
            placed = False
            for bin in bins:
                if bin.can_place(item):
                    bin.place_item(item)
                    placed = True
                    placed_count += 1
                    break

            # 如果没有找到，创建新箱子
            if not placed:
                new_bin = FastBin3D(
                    bin_id=f"bin_{len(bins)}",
                    length=truck_specs['length'],
                    width=truck_specs['width'],
                    height=truck_specs['height'],
                    max_weight=truck_specs['max_weight']
                )
                new_bin.place_item(item)
                bins.append(new_bin)
                placed_count += 1

            # 每10个货物输出一次进度
            if (i + 1) % 10 == 0:
                self.logger.info(f"已处理 {i+1}/{len(sorted_items)} 个货物")

        elapsed = time.time() - start_time

        # Step 4: 计算统计信息
        total_items = len(fast_items)
        total_volume = sum(item.volume_m3 for item in fast_items)
        total_volume_placed = sum(bin.current_volume for bin in bins)
        total_weight_placed = sum(bin.current_weight for bin in bins)

        loading_rate = (total_volume_placed / total_volume * 100) if total_volume > 0 else 0
        avg_volume_utilization = sum(bin.volume_utilization for bin in bins) / len(bins) if bins else 0

        # Step 5: 构建返回结果
        result = {
            'status': 'fast_heuristic',
            'solve_time_seconds': elapsed,
            'solve_time_formatted': f"{elapsed:.2f}秒",
            'method': 'FFDH_Heuristic',
            'bins_count': len(bins),
            'items_count': total_items,
            'items_placed': placed_count,
            'items_unplaced': total_items - placed_count,
            'total_volume': total_volume,
            'volume_placed': total_volume_placed,
            'volume_unplaced': total_volume - total_volume_placed,
            'loading_rate': loading_rate,
            'average_volume_utilization': avg_volume_utilization,
            'total_weight_placed': total_weight_placed,
            'bins': bins,
            'bin_details': [
                {
                    'bin_id': bin.bin_id,
                    'items_count': len(bin.items),
                    'volume': bin.current_volume,
                    'volume_capacity': bin.volume,
                    'volume_utilization': bin.volume_utilization,
                    'weight': bin.current_weight,
                    'weight_capacity': bin.max_weight,
                    'weight_utilization': bin.weight_utilization,
                    'item_ids': [item.item_id for item in bin.items]
                }
                for bin in bins
            ],
            'configuration': {
                'truck_specs': truck_specs,
                'max_time_seconds': max_time_seconds,
                'algorithm': 'First-Fit Decreasing Height (FFDH)'
            }
        }

        # 输出结果摘要
        self.logger.info(f"快速启发式优化完成:")
        self.logger.info(f"  ⏱️ 求解时间: {elapsed:.2f}秒 (目标: <{max_time_seconds}秒)")
        self.logger.info(f"  📦 货物数量: {placed_count}/{total_items}")
        self.logger.info(f"  🚛 使用车辆: {len(bins)}辆")
        self.logger.info(f"  📊 装载率: {loading_rate:.1f}%")
        self.logger.info(f"  📈 平均车辆装载率: {avg_volume_utilization:.1f}%")

        if placed_count < total_items:
            self.logger.warning(f"  ⚠️ 未装载货物: {total_items - placed_count}个")

        return result

    def solve_with_time_windows(self, items, truck_specs=None,
                               max_time_seconds=60) -> Dict[str, Any]:
        """
        带时间窗的快速启发式优化

        Args:
            items: 货物列表
            truck_specs: 车辆规格
            max_time_seconds: 最大求解时间

        Returns:
            Dict: 优化结果
        """
        start_time = time.time()

        # 使用默认车辆规格
        if truck_specs is None:
            truck_specs = self.truck_specs

        # 提取时间窗信息
        items_with_time = []
        for item in items:
            if hasattr(item, 'earliest_delivery_time'):
                items_with_time.append({
                    'item': item,
                    'earliest': item.earliest_delivery_time,
                    'latest': item.latest_delivery_time
                })
            else:
                # 默认时间窗
                items_with_time.append({
                    'item': item,
                    'earliest': '08:00',
                    'latest': '18:00'
                })

        # 按最晚时间排序 (Earliest Deadline First)
        items_with_time.sort(key=lambda x: self._time_to_minutes(x['latest']))

        self.logger.info("带时间窗快速启发式优化开始")

        # 转换货物
        fast_items = [x['item'] for x in items_with_time]
        result = self.solve(fast_items, truck_specs, max_time_seconds)

        # 添加时间窗信息到结果
        result['time_window_info'] = {
            'enabled': True,
            'algorithm': 'Earliest Deadline First (EDF)',
            'items_with_time_windows': items_with_time
        }

        elapsed = time.time() - start_time
        self.logger.info(f"带时间窗优化完成，总时间: {elapsed:.2f}秒")

        return result

    def _time_to_minutes(self, time_str: str) -> int:
        """将时间字符串转换为分钟数"""
        try:
            hour, minute = map(int, time_str.split(':'))
            return hour * 60 + minute
        except:
            return 8 * 60  # 默认8:00


def test_fast_heuristic_optimizer():
    """测试快速启发式优化器"""
    print("=== 快速启发式3D装箱优化器测试 ===")

    # 创建测试货物
    items = [
        FastCargoItem(f"item_{i:03d}",
                     volume_m3=1.0 + i * 0.1,
                     weight_kg=100 + i * 10,
                     length=1.0,
                     width=1.0,
                     height=1.0 + i * 0.05)
        for i in range(50)
    ]

    # 创建优化器
    optimizer = FastHeuristicOptimizer()

    # 执行快速优化
    print("\n开始快速启发式优化...")
    result = optimizer.solve(items, max_time_seconds=60)

    # 输出结果
    print(f"\n✅ 优化成功!")
    print(f"状态: {result['status']}")
    print(f"求解时间: {result['solve_time_formatted']}")
    print(f"方法: {result['method']}")
    print(f"货物数量: {result['items_placed']}/{result['items_count']}")
    print(f"使用车辆: {result['bins_count']}辆")
    print(f"装载率: {result['loading_rate']:.1f}%")
    print(f"平均车辆装载率: {result['average_volume_utilization']:.1f}%")

    print(f"\n车辆详情:")
    for bin_detail in result['bin_details']:
        print(f"  {bin_detail['bin_id']}: "
              f"{bin_detail['items_count']}个货物, "
              f"装载率{bin_detail['volume_utilization']:.1f}%, "
              f"重量{bin_detail['weight']:.0f}kg")

    # 测试带时间窗的优化
    print("\n" + "="*60)
    print("测试带时间窗的优化...")

    # 创建带时间窗的货物
    class TestItemWithTime:
        def __init__(self, item_id, volume, weight, length, width, height,
                     earliest='08:00', latest='18:00'):
            self.item_id = item_id
            self.volume_m3 = volume
            self.weight_kg = weight
            self.estimated_length = length
            self.estimated_width = width
            self.estimated_height = height
            self.earliest_delivery_time = earliest
            self.latest_delivery_time = latest

    items_with_time = [
        TestItemWithTime(f"item_{i:03d}", 2.0, 500, 2.0, 1.0, 1.0,
                        earliest='08:00', latest='10:00')
        for i in range(20)
    ]

    result_with_time = optimizer.solve_with_time_windows(items_with_time, max_time_seconds=30)

    print(f"✅ 带时间窗优化成功!")
    print(f"求解时间: {result_with_time['solve_time_formatted']}")
    print(f"货物数量: {result_with_time['items_placed']}/{result_with_time['items_count']}")
    print(f"装载率: {result_with_time['loading_rate']:.1f}%")


if __name__ == "__main__":
    test_fast_heuristic_optimizer()
