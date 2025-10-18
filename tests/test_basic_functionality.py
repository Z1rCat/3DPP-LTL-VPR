"""
基础功能测试 - 简化版本
Basic Functionality Tests - Simplified Version
"""

import unittest
import sys
from pathlib import Path

# 添加项目路径
sys.path.append(str(Path(__file__).parent.parent))

from optimization.spatial_collision_detector import Item3D, Truck3D, RotationType
from optimization.time_window_optimizer import TimeWindow
from config import TRUCK_SPECS, SPATIAL_CONSTRAINT_CONFIG, TIME_WINDOW_CONFIG


class TestBasicFunctionality(unittest.TestCase):
    """基础功能测试"""

    def test_truck_creation(self):
        """测试货车创建"""
        truck = Truck3D(
            length=TRUCK_SPECS['length'],
            width=TRUCK_SPECS['width'],
            height=TRUCK_SPECS['height'],
            volume=TRUCK_SPECS['volume'],
            max_weight=TRUCK_SPECS['max_weight']
        )
        self.assertEqual(truck.length, 9.6)
        self.assertEqual(truck.width, 2.4)
        self.assertEqual(truck.height, 2.4)
        print("货车创建测试通过")

    def test_item_rotation(self):
        """测试货物旋转"""
        item = Item3D("test_item", 2.0, 1.0, 0.5, 1.0, 100)

        # 测试原始方向
        dims = item.get_rotated_dimensions(RotationType.ORIGINAL)
        self.assertEqual(dims, (2.0, 1.0, 0.5))

        # 测试高度变为长度
        dims = item.get_rotated_dimensions(RotationType.HEIGHT_LENGTH)
        self.assertEqual(dims, (0.5, 1.0, 2.0))

        print("货物旋转测试通过")

    def test_time_window_creation(self):
        """测试时间窗创建"""
        tw = TimeWindow("08:00", "18:00", 30)
        self.assertTrue(tw.is_valid_time_window())
        self.assertEqual(tw.get_earliest_minutes(), 8 * 60)
        self.assertEqual(tw.get_latest_minutes(), 18 * 60)
        print("时间窗创建测试通过")

    def test_spatial_config(self):
        """测试空间配置"""
        config = SPATIAL_CONSTRAINT_CONFIG
        self.assertIn('enable_rotation_optimization', config)
        self.assertIn('enable_3d_collision_detection', config)
        self.assertGreater(config['big_m_for_spatial_constraints'], 0)
        print("空间配置测试通过")

    def test_time_config(self):
        """测试时间配置"""
        config = TIME_WINDOW_CONFIG
        self.assertIn('start_time_hour', config)
        self.assertIn('early_delivery_penalty', config)
        self.assertIn('late_delivery_penalty', config)
        self.assertGreaterEqual(config['start_time_hour'], 0)
        self.assertLess(config['start_time_hour'], 24)
        print("时间配置测试通过")

    def test_basic_math(self):
        """测试基础数学计算"""
        # 测试体积计算
        length, width, height = 2.0, 1.0, 0.5
        volume = length * width * height
        self.assertEqual(volume, 1.0)

        # 测试装载率计算
        item_volume = 1.0
        truck_volume = TRUCK_SPECS['volume']
        loading_rate = item_volume / truck_volume
        self.assertGreater(loading_rate, 0)
        self.assertLess(loading_rate, 1)

        print("基础数学计算测试通过")


def run_basic_tests():
    """运行基础测试"""
    print("开始基础功能测试")
    print("=" * 40)

    test_suite = unittest.TestSuite()
    tests = unittest.TestLoader().loadTestsFromTestCase(TestBasicFunctionality)
    test_suite.addTests(tests)

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)

    print("\n" + "=" * 40)
    print("测试总结:")
    print(f"运行测试数: {result.testsRun}")
    print(f"成功数: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"失败数: {len(result.failures)}")
    print(f"错误数: {len(result.errors)}")

    if result.failures:
        print("\n失败的测试:")
        for test, traceback in result.failures:
            print(f"  - {test}")

    if result.errors:
        print("\n错误的测试:")
        for test, traceback in result.errors:
            print(f"  - {test}")

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
    run_basic_tests()