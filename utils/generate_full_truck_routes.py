"""
为FULL_TRUCK车辆生成点对点路径规划
"""

import json
import pandas as pd
from pathlib import Path
import logging
from datetime import datetime, timedelta
import sys
sys.path.append('.')

from utils.distance_calculator import DistanceCalculator

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def generate_full_truck_routes():
    """为所有FULL_TRUCK车辆生成点对点路径规划"""
    
    # 加载调度计划
    try:
        with open('output/intermediate/full_dispatch_plan.json', 'r', encoding='utf-8') as f:
            dispatch_plan = json.load(f)
    except Exception as e:
        logger.error(f"无法加载调度计划: {e}")
        return
    
    # 加载订单数据
    try:
        orders_df = pd.read_csv('output/intermediate/processed_items.csv')
    except Exception as e:
        logger.error(f"无法加载订单数据: {e}")
        return
    
    # 初始化距离计算器
    distance_calc = DistanceCalculator()
    
    # A网点坐标
    depot_coord = [104.139111, 30.800835]  # [经度, 纬度]
    
    generated_routes = 0
    
    for vehicle_id, truck_data in dispatch_plan['dispatch_plan'].items():
        if truck_data['type'] == 'FULL_TRUCK':
            # 检查是否已有路径文件
            route_file = Path(f"output/reports/{vehicle_id}_route_plan.json")
            if route_file.exists():
                continue
                
            # 获取订单信息
            order_id = truck_data['source_order']
            order_data = orders_df[orders_df['order_id'] == order_id]
            
            if order_data.empty:
                logger.warning(f"未找到订单 {order_id} 的数据")
                continue
            
            # 获取第一条记录（订单数据）
            order_row = order_data.iloc[0]
            
            # 目标坐标
            dest_lat = order_row['latitude']
            dest_lng = order_row['longitude']
            order_type = order_row['pickup_delivery']
            
            # 计算距离
            distance_km = distance_calc.haversine_distance(
                depot_coord[1], depot_coord[0],  # 纬度, 经度
                dest_lat, dest_lng
            )
            
            # 计算时间和成本
            avg_speed = 40  # km/h
            travel_time_hours = distance_km / avg_speed
            
            # 车辆信息
            total_weight_kg = truck_data['total_weight_kg']
            empty_weight_kg = 8500  # 空车重量
            fuel_cost_per_ton_km = 0.16
            
            # 计算燃油成本
            total_weight_ton = (empty_weight_kg + total_weight_kg) / 1000.0
            fuel_cost = fuel_cost_per_ton_km * total_weight_ton * distance_km
            
            # 生成路径规划
            start_time = datetime.now().replace(hour=8, minute=0, second=0, microsecond=0)
            arrival_time = start_time + timedelta(hours=travel_time_hours)
            
            # 服务时间
            service_time_minutes = 30 if order_type == '配送需求' else 20
            completion_time = arrival_time + timedelta(minutes=service_time_minutes)
            
            # 构建路径数据
            route_plan = {
                "summary": {
                    "vehicle_id": vehicle_id,
                    "total_distance_km": round(distance_km, 2),
                    "total_duration_hours": round(travel_time_hours + service_time_minutes/60.0, 2),
                    "fuel_cost_yuan": round(fuel_cost, 2),
                    "total_stops": 1,
                    "pickup_stops": 1 if order_type == '取货需求' else 0,
                    "delivery_stops": 1 if order_type == '配送需求' else 0,
                    "initial_load_kg": total_weight_kg if order_type == '配送需求' else 0,
                    "final_load_kg": total_weight_kg if order_type == '取货需求' else 0,
                    "load_efficiency": round(total_weight_kg / 15000 * 100, 2),  # 15吨容量
                    "optimization_algorithm": "Point_to_Point_Direct",
                    "solution_status": "DIRECT_ROUTE",
                    "completion_time": completion_time.strftime('%H:%M'),
                    "start_time": "08:00",
                    "working_hours": round(travel_time_hours + service_time_minutes/60.0, 2),
                    "cargo_type": truck_data.get('item_type', '未知'),
                    "cargo_quantity": truck_data.get('quantity_per_truck', 0)
                },
                "route_details": {
                    "depot_info": {
                        "name": "A网点（成都至重庆专线）",
                        "coordinates": {
                            "lat": depot_coord[1],
                            "lng": depot_coord[0]
                        },
                        "address": f"({depot_coord[1]:.6f}, {depot_coord[0]:.6f})"
                    },
                    "vehicle_info": {
                        "type": "9.6米厢式货车",
                        "capacity_kg": 15000,
                        "empty_weight_kg": empty_weight_kg,
                        "fuel_coefficient": fuel_cost_per_ton_km
                    },
                    "optimization_info": {
                        "solver": "Direct_Point_to_Point",
                        "strategy": "单一订单直达运输",
                        "route_type": "FULL_TRUCK_DIRECT"
                    }
                },
                "itinerary": [
                    {
                        "step": 1,
                        "action": "送货" if order_type == '配送需求' else "取货",
                        "order_id": order_id,
                        "coordinates": [dest_lat, dest_lng],
                        "weight_change_kg": -total_weight_kg if order_type == '配送需求' else total_weight_kg,
                        "distance_from_previous_km": round(distance_km, 2),
                        "estimated_arrival": arrival_time.strftime('%H:%M'),
                        "service_time_minutes": service_time_minutes,
                        "departure_time": completion_time.strftime('%H:%M'),
                        "address": f"坐标({dest_lat:.4f}, {dest_lng:.4f})",
                        "cumulative_load_kg": total_weight_kg if order_type == '取货需求' else 0,
                        "cargo_info": {
                            "type": truck_data.get('item_type', '未知'),
                            "quantity": truck_data.get('quantity_per_truck', 0),
                            "total_weight_kg": total_weight_kg
                        }
                    }
                ],
                "performance_metrics": {
                    "total_service_time_minutes": service_time_minutes,
                    "total_travel_time_hours": round(travel_time_hours, 2),
                    "service_efficiency": round(service_time_minutes / (travel_time_hours * 60 + service_time_minutes) * 100, 2),
                    "fuel_efficiency_yuan_per_km": round(fuel_cost / distance_km, 2),
                    "cargo_density_kg_per_m3": round(total_weight_kg / 55.296, 2)  # 车厢体积55.296m³
                },
                "solver_info": {
                    "method": "Direct_Point_to_Point",
                    "solve_time_seconds": 0.01,
                    "status": "DIRECT_ROUTE_SUCCESS"
                },
                "generated_time": datetime.now().isoformat(),
                "generated_by": "Full_Truck_Route_Generator"
            }
            
            # 保存路径文件
            with open(route_file, 'w', encoding='utf-8') as f:
                json.dump(route_plan, f, ensure_ascii=False, indent=2)
            
            logger.info(f"已生成 {vehicle_id} 的路径规划: {distance_km:.1f}km, {order_type}")
            generated_routes += 1
    
    logger.info(f"共生成 {generated_routes} 个FULL_TRUCK路径规划")
    return generated_routes

if __name__ == "__main__":
    generated_count = generate_full_truck_routes()
    print(f"\n=== FULL_TRUCK路径生成完成 ===")
    print(f"成功生成: {generated_count} 个路径规划")
    
    if generated_count > 0:
        print("\n重新运行汇总脚本...")
        # 重新生成汇总报告
        import export_route_results
        export_route_results.export_route_summary_to_excel()
