"""
地理距离计算工具
Geographic Distance Calculator for Vehicle Routing
"""

import math
import numpy as np
from typing import List, Tuple, Union


class DistanceCalculator:
    """地理距离计算器"""

    EARTH_RADIUS_KM = 6371.0  # 地球半径（公里）

    @staticmethod
    def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        使用Haversine公式计算两点间的球面距离

        Args:
            lat1, lon1: 第一个点的纬度和经度
            lat2, lon2: 第二个点的纬度和经度

        Returns:
            float: 两点间距离（公里）
        """
        # 将度数转换为弧度
        lat1_rad = math.radians(lat1)
        lon1_rad = math.radians(lon1)
        lat2_rad = math.radians(lat2)
        lon2_rad = math.radians(lon2)

        # 计算纬度和经度差值
        dlat = lat2_rad - lat1_rad
        dlon = lon2_rad - lon1_rad

        # Haversine公式
        a = (math.sin(dlat / 2) ** 2 +
             math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2) ** 2)
        c = 2 * math.asin(math.sqrt(a))

        # 计算距离
        distance = DistanceCalculator.EARTH_RADIUS_KM * c

        return distance

    @classmethod
    def build_distance_matrix(cls, coordinates: List[Tuple[float, float]]) -> np.ndarray:
        """
        构建坐标点间的距离矩阵

        Args:
            coordinates: 坐标列表，每个元素为(latitude, longitude)

        Returns:
            np.ndarray: n×n的距离矩阵（公里）
        """
        n = len(coordinates)
        distance_matrix = np.zeros((n, n))

        for i in range(n):
            for j in range(n):
                if i != j:
                    lat1, lon1 = coordinates[i]
                    lat2, lon2 = coordinates[j]
                    distance_matrix[i][j] = cls.haversine_distance(lat1, lon1, lat2, lon2)
                else:
                    distance_matrix[i][j] = 0.0

        return distance_matrix

    @staticmethod
    def calculate_route_distance(coordinates: List[Tuple[float, float]],
                               route: List[int]) -> float:
        """
        计算指定路径的总距离

        Args:
            coordinates: 坐标列表
            route: 路径节点索引列表

        Returns:
            float: 总距离（公里）
        """
        total_distance = 0.0

        for i in range(len(route) - 1):
            current_idx = route[i]
            next_idx = route[i + 1]

            lat1, lon1 = coordinates[current_idx]
            lat2, lon2 = coordinates[next_idx]

            total_distance += DistanceCalculator.haversine_distance(lat1, lon1, lat2, lon2)

        return total_distance

    @staticmethod
    def validate_coordinates(lat: float, lon: float) -> bool:
        """
        验证坐标的有效性

        Args:
            lat: 纬度
            lon: 经度

        Returns:
            bool: 坐标是否有效
        """
        return (-90 <= lat <= 90) and (-180 <= lon <= 180)

    @classmethod
    def get_coordinates_bounds(cls, coordinates: List[Tuple[float, float]]) -> dict:
        """
        获取坐标列表的边界信息

        Args:
            coordinates: 坐标列表

        Returns:
            dict: 包含最小/最大纬度和经度的字典
        """
        if not coordinates:
            return {}

        lats = [coord[0] for coord in coordinates]
        lons = [coord[1] for coord in coordinates]

        return {
            'min_lat': min(lats),
            'max_lat': max(lats),
            'min_lon': min(lons),
            'max_lon': max(lons),
            'center_lat': sum(lats) / len(lats),
            'center_lon': sum(lons) / len(lons)
        }


def test_distance_calculator():
    """测试距离计算器功能"""
    print("=== 距离计算器测试 ===")

    # 测试单点距离计算
    # 成都天府广场到重庆解放碑的距离（约308公里）
    chengdu_coord = (30.667, 104.066)
    chongqing_coord = (29.556, 106.577)

    distance = DistanceCalculator.haversine_distance(
        chengdu_coord[0], chengdu_coord[1],
        chongqing_coord[0], chongqing_coord[1]
    )
    print(f"成都到重庆距离: {distance:.2f} 公里")

    # 测试距离矩阵
    test_coords = [
        (30.800835, 104.139111),  # A网点
        (30.650, 104.100),        # 客户点1
        (30.700, 104.200),        # 客户点2
        (30.750, 104.050)         # 客户点3
    ]

    matrix = DistanceCalculator.build_distance_matrix(test_coords)
    print(f"\n距离矩阵形状: {matrix.shape}")
    print("距离矩阵 (前4x4):")
    print(matrix[:4, :4])

    # 测试坐标验证
    print(f"\n坐标验证测试:")
    print(f"成都坐标有效性: {DistanceCalculator.validate_coordinates(30.667, 104.066)}")
    print(f"无效坐标测试: {DistanceCalculator.validate_coordinates(91.0, 200.0)}")

    # 测试边界计算
    bounds = DistanceCalculator.get_coordinates_bounds(test_coords)
    print(f"\n坐标边界: {bounds}")


if __name__ == "__main__":
    test_distance_calculator()