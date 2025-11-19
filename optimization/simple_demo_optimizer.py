"""
简单演示优化器 - 用于管理员端展示
Simple Demo Optimizer for Admin Dashboard Display

提供基础的演示功能，避免复杂的依赖问题。
"""

import asyncio
import uuid
import json
import time
import random
from datetime import datetime
from typing import Dict, Any, List


class SimpleDemoOptimizer:
    """简单演示优化器"""

    def __init__(self):
        """初始化简单演示优化器"""
        self.demo_data = self._generate_simple_demo_data()
        print("[演示] 简单演示优化器已初始化")

    def _generate_simple_demo_data(self) -> List[Dict]:
        """生成简单演示数据"""
        customers = ["京东物流", "顺丰速运", "德邦物流", "安能物流", "百世快递"]
        destinations = ["成都高新区", "成都天府新区", "成都武侯区", "成都锦江区"]

        demo_orders = []
        for i in range(50):
            cargo_type = random.choice(['large', 'medium', 'small'])

            if cargo_type == 'large':
                length, width, height = random.uniform(2.0, 4.0), random.uniform(1.5, 2.5), random.uniform(1.5, 2.5)
                weight = random.uniform(500, 2000)
            elif cargo_type == 'medium':
                length, width, height = random.uniform(1.0, 2.0), random.uniform(0.8, 1.5), random.uniform(0.8, 1.5)
                weight = random.uniform(100, 500)
            else:  # small
                length, width, height = random.uniform(0.3, 1.0), random.uniform(0.3, 0.8), random.uniform(0.3, 0.8)
                weight = random.uniform(10, 100)

            demo_orders.append({
                "order_id": f"ORDER_{i+1:04d}",
                "customer_name": random.choice(customers),
                "cargo_type": cargo_type,
                "dimensions": {
                    "length": round(length, 2),
                    "width": round(width, 2),
                    "height": round(height, 2)
                },
                "weight": round(weight, 1),
                "volume": round(length * width * height, 2),
                "destination": random.choice(destinations)
            })

        return demo_orders

    def generate_demo_data(self, count: int = 50) -> List[Dict]:
        """生成演示订单数据"""
        return self.demo_data[:min(count, len(self.demo_data))]

    async def run_complete_optimization_demo(self,
                                            progress_callback=None,
                                            order_count: int = 50,
                                            optimization_mode: str = "fast") -> Dict[str, Any]:
        """运行演示版完整优化流程"""

        # 优化步骤定义
        steps = [
            "系统初始化",
            "数据预处理",
            "货物分类",
            "路径规划",
            "3D装箱优化",
            "方案验证",
            "结果生成"
        ]

        total_steps = len(steps)
        base_time_per_step = 0.5 if optimization_mode == "fast" else 1.5

        try:
            # 执行优化步骤
            for i, step in enumerate(steps):
                if progress_callback:
                    await progress_callback({
                        "step": i + 1,
                        "total_steps": total_steps,
                        "progress": round(((i + 1) / total_steps) * 100, 1),
                        "current_step": step,
                        "message": f"正在执行: {step}...",
                        "status": "running"
                    })

                # 模拟执行时间
                await asyncio.sleep(base_time_per_step * random.uniform(0.8, 1.2))

            # 生成优化结果
            result = self._generate_demo_result(order_count, optimization_mode)

            if progress_callback:
                await progress_callback({
                    "step": total_steps,
                    "total_steps": total_steps,
                    "progress": 100,
                    "current_step": "完成",
                    "message": "优化完成！",
                    "status": "completed"
                })

            return result

        except Exception as e:
            if progress_callback:
                await progress_callback({
                    "step": 0,
                    "total_steps": total_steps,
                    "progress": 0,
                    "current_step": "错误",
                    "message": f"优化失败: {str(e)}",
                    "status": "error"
                })

            return {
                "task_id": str(uuid.uuid4()),
                "status": "error",
                "error": str(e),
                "success": False,
                "message": f"优化失败: {str(e)}"
            }

    def _generate_demo_result(self, order_count: int, optimization_mode: str) -> Dict[str, Any]:
        """生成演示优化结果"""

        # 模拟性能指标
        total_loading_rate = round(random.uniform(75, 95), 1)
        used_trucks = max(3, order_count // 15)
        optimization_time = round(random.uniform(8, 25), 2)

        # 生成装载计划
        loading_plans = []
        for i in range(used_trucks):
            orders_per_truck = random.randint(3, 8)
            volume_utilization = round(random.uniform(70, 95), 1)
            weight_utilization = round(random.uniform(65, 90), 1)

            plan = {
                "truck_id": f"LTL_TRUCK_{i+1:03d}",
                "orders": [f"ORDER_{j+1:04d}" for j in range(i*orders_per_truck, (i+1)*orders_per_truck)],
                "total_volume": round(volume_utilization * 55.296 / 100, 2),
                "total_weight": round(weight_utilization * 18000 / 100, 1),
                "volume_utilization": volume_utilization,
                "weight_utilization": weight_utilization,
                "loading_positions": []
            }

            # 生成装载位置
            for j, order_id in enumerate(plan["orders"]):
                plan["loading_positions"].append({
                    "order_id": order_id,
                    "position": [
                        round(random.uniform(0, 8), 2),
                        round(random.uniform(0, 2), 2),
                        round(random.uniform(0, 2), 2)
                    ],
                    "dimensions": [random.uniform(0.5, 2), random.uniform(0.5, 1.5), random.uniform(0.3, 1)],
                    "weight": round(random.uniform(50, 500), 1)
                })

            loading_plans.append(plan)

        # 生成性能指标
        performance_metrics = {
            'orders_by_type': {
                'large': int(order_count * 0.2),
                'medium': int(order_count * 0.3),
                'small': int(order_count * 0.5)
            },
            'efficiency_scores': {
                'space_efficiency': total_loading_rate,
                'weight_efficiency': round(random.uniform(70, 90), 1),
                'route_efficiency': round(random.uniform(85, 95), 1),
                'time_efficiency': round(random.uniform(90, 98), 1)
            },
            'cost_analysis': {
                'total_distance': round(random.uniform(150, 500), 1),
                'fuel_cost': round(random.uniform(200, 800), 0),
                'driver_cost': round(random.uniform(500, 1500), 0),
                'total_cost': round(random.uniform(700, 2300), 0),
                'cost_per_order': round(random.uniform(15, 45), 1)
            },
            'improvement_metrics': {
                'loading_rate_improvement': round(random.uniform(5, 15), 1),
                'cost_reduction': round(random.uniform(8, 20), 1),
                'time_saving': round(random.uniform(10, 25), 1)
            }
        }

        return {
            "task_id": str(uuid.uuid4()),
            "optimization_mode": optimization_mode,
            "status": "completed",
            "total_orders": order_count,
            "used_trucks": used_trucks,
            "total_loading_rate": total_loading_rate,
            "total_weight_utilization": round(random.uniform(70, 90), 1),
            "optimization_time_seconds": optimization_time,
            "loading_plans": loading_plans,
            "performance_metrics": performance_metrics,
            "timestamp": datetime.now().isoformat(),
            "success": True,
            "message": "优化成功完成",
            "source": "simple_demo"
        }

    def get_optimization_statistics(self) -> Dict[str, Any]:
        """获取优化统计信息"""
        return {
            "demo_data_info": {
                "total_orders": len(self.demo_data),
                "destinations_count": 4,
                "cargo_distribution": {
                    'large': len([o for o in self.demo_data if o['cargo_type'] == 'large']),
                    'medium': len([o for o in self.demo_data if o['cargo_type'] == 'medium']),
                    'small': len([o for o in self.demo_data if o['cargo_type'] == 'small'])
                }
            },
            "system_info": {
                "optimizer_type": "Simple Demo Optimizer",
                "version": "1.0.0",
                "max_orders": len(self.demo_data)
            }
        }