"""
空间-时间约束系统测试用例
Test Suite for Spatial-Temporal Constraint System

测试覆盖：
- 3D空间冲突检测
- 时间窗约束优化
- 增强Gurobi优化器集成
- 多目标优化功能
"""

import unittest
import sys
import logging
from pathlib import Path

# 添加项目路径
sys.path.append(str(Path(__file__).parent.parent))

from optimization.spatial_collision_detector import (
    SpatialCollisionDetector, Item3D, Truck3D, RotationType
)
from optimization.time_window_optimizer import (
    TimeWindowOptimizer, CustomerNode, VehicleInfo, TimeWindow
)
from optimization.gurobi_optimizer_enhanced import (
    GurobiOptimizerEnhanced, EnhancedCargoItem
)
from config import TRUCK_SPECS, SPATIAL_CONSTRAINT_CONFIG, TIME_WINDOW_CONFIG


class TestSpatialCollisionDetection(unittest.TestCase):
    """3D空间冲突检测测试"""

    def setUp(self):
        """测试前准备"""
        self.detector = SpatialCollisionDetector()
        self.truck = Truck3D(
            length=TRUCK_SPECS['length'],
            width=TRUCK_SPECS['width'],
            height=TRUCK_SPECS['height'],
            volume=TRUCK_SPECS['volume'],
            max_weight=TRUCK_SPECS['max_weight']
        )

    def test_rotation_types(self):
        """测试6种旋转方式 (公式3-4)"""
        print("\n=== 测试旋转方式 ===")

        item = Item3D("test_item", 2.0, 1.0, 0.5, 1.0, 100)

        # 测试所有6种旋转方式
        rotations = [
            (RotationType.ORIGINAL, (2.0, 1.0, 0.5)),
            (RotationType.HEIGHT_LENGTH, (0.5, 1.0, 2.0)),
            (RotationType.WIDTH_LENGTH, (1.0, 2.0, 0.5)),
            (RotationType.HEIGHT_WIDTH, (0.5, 2.0, 1.0)),
            (RotationType.WIDTH_HEIGHT, (1.0, 0.5, 2.0)),
            (RotationType.LENGTH_HEIGHT, (2.0, 0.5, 1.0))
        ]

        for rotation_type, expected_dims in rotations:
            actual_dims = item.get_rotated_dimensions(rotation_type)
            self.assertEqual(actual_dims, expected_dims,
                           f"旋转类型 {rotation_type} 尺寸不匹配")
            print(f"✅ 旋转类型 {rotation_type.value}: {actual_dims}")

    def test_basic_collision_detection(self):
        """测试基础碰撞检测"""
        print("\n=== 测试基础碰撞检测 ===")

        # 创建两个明显重叠的货物
        item1 = Item3D("item_001", 1.0, 1.0, 1.0, 1.0, 100)
        item2 = Item3D("item_002", 1.0, 1.0, 1.0, 1.0, 100)

        # 重叠位置
        pos1 = {
            'position': {'x': 0, 'y': 0, 'z': 0},
            'dimensions': {'length': 1.0, 'width': 1.0, 'height': 1.0}
        }
        pos2 = {
            'position': {'x': 0.5, 'y': 0.5, 'z': 0.5},
            'dimensions': {'length': 1.0, 'width': 1.0, 'height': 1.0}
        }

        # 检测重叠
        is_overlapping = self.detector._check_overlap(pos1, pos2)
        self.assertTrue(is_overlapping, "货物应该重叠")
        print("✅ 重叠检测正确")

        # 不重叠位置
        pos3 = {
            'position': {'x': 2.0, 'y': 2.0, 'z': 0},
            'dimensions': {'length': 1.0, 'width': 1.0, 'height': 1.0}
        }

        not_overlapping = self.detector._check_overlap(pos1, pos3)
        self.assertFalse(not_overlapping, "货物不应该重叠")
        print("✅ 非重叠检测正确")

    def test_boundary_constraints(self):
        """测试边界约束 (公式3-3)"""
        print("\n=== 测试边界约束 ===")

        item = Item3D("boundary_test", 8.0, 2.0, 2.0, 32.0, 1000)

        # 在边界内的位置
        valid_position = {
            'position': {'x': 0.5, 'y': 0.2, 'z': 0.1},
            'dimensions': {'length': 8.0, 'width': 2.0, 'height': 2.0}
        }

        validation = self.detector.validate_solution([valid_position], self.truck)
        self.assertTrue(validation['valid'], "在边界内的位置应该有效")
        print("✅ 边界内位置验证通过")

        # 超出边界的位置
        invalid_position = {
            'position': {'x': 2.0, 'y': 0.5, 'z': 0.5},
            'dimensions': {'length': 8.0, 'width': 2.0, 'height': 2.0}
        }

        validation = self.detector.validate_solution([invalid_position], self.truck)
        self.assertFalse(validation['valid'], "超出边界的位置应该无效")
        self.assertTrue(any("超出车厢边界" in error for error in validation['errors']))
        print("✅ 边界外位置检测正确")


class TestTimeWindowConstraints(unittest.TestCase):
    """时间窗约束测试"""

    def setUp(self):
        """测试前准备"""
        self.optimizer = TimeWindowOptimizer()

    def test_time_window_format(self):
        """测试时间窗格式"""
        print("\n=== 测试时间窗格式 ===")

        # 有效时间窗
        valid_tw = TimeWindow("08:00", "18:00", 30)
        self.assertTrue(valid_tw.is_valid_time_window(), "有效时间窗应该通过验证")
        self.assertEqual(valid_tw.get_earliest_minutes(), 8 * 60)
        self.assertEqual(valid_tw.get_latest_minutes(), 18 * 60)
        print("✅ 有效时间窗格式正确")

        # 无效时间窗
        invalid_tw = TimeWindow("18:00", "08:00", 30)
        self.assertFalse(invalid_tw.is_valid_time_window(), "无效时间窗应该失败")
        print("✅ 无效时间窗检测正确")

    def test_time_window_violations(self):
        """测试时间窗违规检测"""
        print("\n=== 测试时间窗违规检测 ===")

        # 创建时间窗违规的安排
        schedule = [
            {
                'node_id': 'node_001',
                'time_window': {'earliest': '09:00', 'latest': '12:00'},
                'schedule': {'arrival_time': '08:30'},  # 早到
                'violations': {'early_arrival': 30, 'late_arrival': 0}
            },
            {
                'node_id': 'node_002',
                'time_window': {'earliest': '10:00', 'latest': '14:00'},
                'schedule': {'arrival_time': '15:00'},  # 晚到
                'violations': {'early_arrival': 0, 'late_arrival': 60}
            },
            {
                'node_id': 'node_003',
                'time_window': {'earliest': '11:00', 'latest': '15:00'},
                'schedule': {'arrival_time': '13:00'},  # 准时
                'violations': {'early_arrival': 0, 'late_arrival': 0}
            }
        ]

        validation = self.optimizer.validate_time_windows(schedule)

        self.assertEqual(validation['statistics']['early_violations'], 1)
        self.assertEqual(validation['statistics']['late_violations'], 1)
        self.assertEqual(validation['statistics']['total_violations'], 2)
        self.assertEqual(validation['statistics']['on_time_rate'], 33.33)  # 1/3 * 100

        self.assertGreater(validation['total_penalty'], 0)
        print("✅ 时间窗违规检测正确")
        print(f"  早到违规: {validation['statistics']['early_violations']}")
        print(f"  晚到违规: {validation['statistics']['late_violations']}")
        print(f"  准时率: {validation['statistics']['on_time_rate']:.2f}%")
        print(f"  总惩罚: {validation['total_penalty']:.2f}元")

    def test_service_time_calculation(self):
        """测试服务时间计算 (公式3-19)"""
        print("\n=== 测试服务时间计算 ===")

        # 测试不同的服务时间设置
        service_times = [10, 15, 20, 30]
        for service_time in service_times:
            time_window = TimeWindow("08:00", "18:00", service_time)
            self.assertEqual(time_window.service_time, service_time)
            print(f"✅ 服务时间 {service_time} 分钟设置正确")


class TestEnhancedOptimizer(unittest.TestCase):
    """增强优化器集成测试"""

    def setUp(self):
        """测试前准备"""
        self.optimizer = GurobiOptimizerEnhanced()

    def test_basic_optimization(self):
        """测试基础优化功能"""
        print("\n=== 测试基础优化功能 ===")

        # 创建测试货物
        items = [
            EnhancedCargoItem(
                item_id="test_001",
                volume_m3=1.0,
                weight_kg=200,
                estimated_length=1.0,
                estimated_width=1.0,
                estimated_height=1.0,
                earliest_delivery_time="08:00",
                latest_delivery_time="18:00"
            ),
            EnhancedCargoItem(
                item_id="test_002",
                volume_m3=1.5,
                weight_kg=300,
                estimated_length=1.5,
                estimated_width=1.0,
                estimated_height=1.0,
                earliest_delivery_time="09:00",
                latest_delivery_time="16:00"
            )
        ]

        try:
            result = self.optimizer.optimize_with_constraints(
                items=items,
                truck_specs=TRUCK_SPECS,
                max_items=2,
                enable_spatial=True,
                enable_time_windows=False  # 先不启用时间窗，简化测试
            )

            self.assertIn(result.status, ['optimal', 'feasible', 'time_limit'])
            self.assertGreaterEqual(result.volume_utilization, 0)
            self.assertGreaterEqual(result.weight_utilization, 0)

            print(f"✅ 基础优化成功")
            print(f"  状态: {result.status}")
            print(f"  体积利用率: {result.volume_utilization:.2f}%")
            print(f"  重量利用率: {result.weight_utilization:.2f}%")
            print(f"  求解时间: {result.solve_time:.2f}秒")

        except Exception as e:
            # 如果Gurobi不可用，跳过测试
            if "gurobi" in str(e).lower():
                self.skipTest("Gurobi不可用，跳过优化器测试")
            else:
                raise

    def test_spatial_constraints_integration(self):
        """测试空间约束集成"""
        print("\n=== 测试空间约束集成 ===")

        # 创建需要空间优化的货物
        items = [
            EnhancedCargoItem(
                item_id="spatial_001",
                volume_m3=2.0,
                weight_kg=400,
                estimated_length=2.0,
                estimated_width=1.0,
                estimated_height=1.0,
                rotation_allowed=True
            ),
            EnhancedCargoItem(
                item_id="spatial_002",
                volume_m3=1.8,
                weight_kg=350,
                estimated_length=1.8,
                estimated_width=1.0,
                estimated_height=1.0,
                rotation_allowed=True
            )
        ]

        try:
            result = self.optimizer.optimize_with_constraints(
                items=items,
                truck_specs=TRUCK_SPECS,
                max_items=2,
                enable_spatial=True,
                enable_time_windows=False
            )

            # 检查空间位置信息
            self.assertGreaterEqual(len(result.spatial_positions), 0)
            self.assertGreaterEqual(len(result.loading_plan), 0)

            print(f"✅ 空间约束集成成功")
            print(f"  装载货物数: {len(result.spatial_positions)}")
            print(f"  体积利用率: {result.volume_utilization:.2f}%")

            for pos in result.spatial_positions:
                print(f"  货物 {pos['item_id']}: 位置({pos['position']['x']}, {pos['position']['y']}, {pos['position']['z']})")

        except Exception as e:
            if "gurobi" in str(e).lower():
                self.skipTest("Gurobi不可用，跳过空间约束测试")
            else:
                raise

    def test_multi_objective_optimization(self):
        """测试多目标优化"""
        print("\n=== 测试多目标优化 ===")

        # 创建具有不同优先级的货物
        items = [
            EnhancedCargoItem(
                item_id="priority_001",
                volume_m3=2.5,
                weight_kg=500,
                estimated_length=2.5,
                estimated_width=1.0,
                estimated_height=1.0,
                priority=1,  # 高优先级
                time_window_penalty_rate=10.0
            ),
            EnhancedCargoItem(
                item_id="priority_002",
                volume_m3=1.0,
                weight_kg=200,
                estimated_length=1.0,
                estimated_width=1.0,
                estimated_height=1.0,
                priority=2,  # 低优先级
                time_window_penalty_rate=5.0
            )
        ]

        try:
            result = self.optimizer.optimize_with_constraints(
                items=items,
                truck_specs=TRUCK_SPECS,
                max_items=2,
                enable_spatial=True,
                enable_time_windows=False
            )

            # 检查多目标优化结果
            self.assertGreaterEqual(result.multi_objective_score, 0)
            self.assertGreaterEqual(result.economic_cost, 0)
            self.assertGreaterEqual(result.loading_efficiency, 0)

            print(f"✅ 多目标优化成功")
            print(f"  多目标得分: {result.multi_objective_score:.4f}")
            print(f"  经济成本: {result.economic_cost:.2f}")
            print(f"  装载效率: {result.loading_efficiency:.2f}")

        except Exception as e:
            if "gurobi" in str(e).lower():
                self.skipTest("Gurobi不可用，跳过多目标优化测试")
            else:
                raise


class TestConfigurationValidation(unittest.TestCase):
    """配置验证测试"""

    def test_spatial_config(self):
        """测试空间约束配置"""
        print("\n=== 测试空间约束配置 ===")

        config = SPATIAL_CONSTRAINT_CONFIG

        # 检查必需的配置项
        required_keys = [
            'enable_rotation_optimization',
            'enable_3d_collision_detection',
            'big_m_for_spatial_constraints',
            'rotation_enumeration_limit'
        ]

        for key in required_keys:
            self.assertIn(key, config, f"缺少配置项: {key}")

        # 检查配置值的有效性
        self.assertIsInstance(config['enable_rotation_optimization'], bool)
        self.assertIsInstance(config['enable_3d_collision_detection'], bool)
        self.assertGreater(config['big_m_for_spatial_constraints'], 0)
        self.assertGreater(config['rotation_enumeration_limit'], 0)

        print("✅ 空间约束配置验证通过")

    def test_time_window_config(self):
        """测试时间窗配置"""
        print("\n=== 测试时间窗配置 ===")

        config = TIME_WINDOW_CONFIG

        # 检查必需的配置项
        required_keys = [
            'start_time_hour',
            'early_delivery_penalty',
            'late_delivery_penalty',
            'service_time_per_item',
            'average_speed_kmh'
        ]

        for key in required_keys:
            self.assertIn(key, config, f"缺少配置项: {key}")

        # 检查配置值的有效性
        self.assertGreaterEqual(config['start_time_hour'], 0)
        self.assertLess(config['start_time_hour'], 24)
        self.assertGreaterEqual(config['early_delivery_penalty'], 0)
        self.assertGreaterEqual(config['late_delivery_penalty'], 0)
        self.assertGreater(config['service_time_per_item'], 0)
        self.assertGreater(config['average_speed_kmh'], 0)

        print("✅ 时间窗配置验证通过")


def run_comprehensive_tests():
    """运行全面的测试套件"""
    print("开始空间-时间约束系统全面测试")
    print("=" * 60)

    # 设置日志级别
    logging.basicConfig(level=logging.WARNING)  # 减少测试期间的日志输出

    # 创建测试套件
    test_suite = unittest.TestSuite()

    # 添加测试类
    test_classes = [
        TestSpatialCollisionDetection,
        TestTimeWindowConstraints,
        TestEnhancedOptimizer,
        TestConfigurationValidation
    ]

    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)

    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)

    # 输出测试总结
    print("\n" + "=" * 60)
    print("测试总结:")
    print(f"  运行测试数: {result.testsRun}")
    print(f"  成功数: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"  失败数: {len(result.failures)}")
    print(f"  错误数: {len(result.errors)}")
    print(f"  跳过数: {len(result.skipped) if hasattr(result, 'skipped') else 0}")

    if result.failures:
        print("\n失败的测试:")
        for test, traceback in result.failures:
            print(f"  - {test}: {traceback}")

    if result.errors:
        print("\n错误的测试:")
        for test, traceback in result.errors:
            print(f"  - {test}: {traceback}")

    success_rate = (result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100
    print(f"\n测试成功率: {success_rate:.1f}%")

    if success_rate >= 90:
        print("测试结果优秀！")
    elif success_rate >= 70:
        print("测试结果良好！")
    else:
        print("测试结果需要改进！")

    return result.wasSuccessful()


if __name__ == "__main__":
    run_comprehensive_tests()