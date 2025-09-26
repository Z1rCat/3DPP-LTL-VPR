"""
数据相关的API路由
Data API Routes
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional, Dict, Any
from pathlib import Path
import json
import logging

from ..models.schemas import TruckData, RouteData, APIResponse
from ..utils.response import success_response, error_response

router = APIRouter()
logger = logging.getLogger(__name__)

# 数据文件目录
REPORTS_DIR = Path(__file__).parent.parent.parent / "output" / "reports"

@router.get("/trucks", response_model=APIResponse)
async def get_trucks_data(
    truck_type: Optional[str] = Query(None, description="卡车类型: LARGE_TRUCK, LTL_TRUCK"),
    limit: Optional[int] = Query(50, description="返回数量限制")
):
    """
    获取卡车装载数据
    """
    try:
        if not REPORTS_DIR.exists():
            return error_response("报告目录不存在，请先运行优化程序")

        trucks = []
        loading_files = list(REPORTS_DIR.glob("*_loading_plan.json"))

        for file_path in loading_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                truck_info = _extract_truck_info(data, file_path.name)

                # 应用类型过滤
                if truck_type and truck_info.get('type') != truck_type:
                    continue

                trucks.append(truck_info)

            except Exception as e:
                logger.warning(f"读取文件 {file_path.name} 失败: {str(e)}")
                continue

        # 按装载效率排序
        trucks.sort(key=lambda x: x.get('loading_efficiency', 0), reverse=True)

        # 应用数量限制
        if limit:
            trucks = trucks[:limit]

        return success_response(
            data=trucks,
            message=f"找到 {len(trucks)} 辆卡车数据"
        )

    except Exception as e:
        logger.error(f"获取卡车数据失败: {str(e)}")
        return error_response(f"获取卡车数据失败: {str(e)}")

@router.get("/routes", response_model=APIResponse)
async def get_routes_data(
    truck_type: Optional[str] = Query(None, description="卡车类型: LARGE_TRUCK, LTL_TRUCK"),
    limit: Optional[int] = Query(50, description="返回数量限制")
):
    """
    获取路径优化数据
    """
    try:
        if not REPORTS_DIR.exists():
            return error_response("报告目录不存在，请先运行优化程序")

        routes = []
        route_files = list(REPORTS_DIR.glob("*_route_plan.json"))

        for file_path in route_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                route_info = _extract_route_info(data, file_path.name)

                # 应用类型过滤
                if truck_type and truck_type not in route_info.get('vehicle_id', ''):
                    continue

                routes.append(route_info)

            except Exception as e:
                logger.warning(f"读取文件 {file_path.name} 失败: {str(e)}")
                continue

        # 按总距离排序
        routes.sort(key=lambda x: x.get('total_distance_km', 0))

        # 应用数量限制
        if limit:
            routes = routes[:limit]

        return success_response(
            data=routes,
            message=f"找到 {len(routes)} 条路径数据"
        )

    except Exception as e:
        logger.error(f"获取路径数据失败: {str(e)}")
        return error_response(f"获取路径数据失败: {str(e)}")

@router.get("/trucks/{vehicle_id}", response_model=APIResponse)
async def get_truck_detail(vehicle_id: str):
    """
    获取特定卡车的详细数据
    """
    try:
        loading_file = REPORTS_DIR / f"{vehicle_id}_loading_plan.json"
        route_file = REPORTS_DIR / f"{vehicle_id}_route_plan.json"

        truck_detail = {"vehicle_id": vehicle_id}

        # 加载装载数据
        if loading_file.exists():
            with open(loading_file, 'r', encoding='utf-8') as f:
                loading_data = json.load(f)
            truck_detail["loading_plan"] = loading_data
        else:
            truck_detail["loading_plan"] = None

        # 加载路径数据
        if route_file.exists():
            with open(route_file, 'r', encoding='utf-8') as f:
                route_data = json.load(f)
            truck_detail["route_plan"] = route_data
        else:
            truck_detail["route_plan"] = None

        if not truck_detail["loading_plan"] and not truck_detail["route_plan"]:
            return error_response(f"未找到车辆 {vehicle_id} 的数据")

        return success_response(
            data=truck_detail,
            message=f"车辆 {vehicle_id} 详细数据获取成功"
        )

    except Exception as e:
        logger.error(f"获取车辆详细数据失败: {str(e)}")
        return error_response(f"获取车辆详细数据失败: {str(e)}")

@router.get("/summary", response_model=APIResponse)
async def get_data_summary():
    """
    获取数据摘要统计
    """
    try:
        if not REPORTS_DIR.exists():
            return error_response("报告目录不存在")

        loading_files = list(REPORTS_DIR.glob("*_loading_plan.json"))
        route_files = list(REPORTS_DIR.glob("*_route_plan.json"))

        total_loading_efficiency = 0
        total_distance = 0
        total_items = 0
        truck_types = {}

        # 统计装载数据
        for file_path in loading_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                summary = data.get('summary', {})
                total_loading_efficiency += summary.get('loading_efficiency', 0)
                total_items += summary.get('total_items', 0)

                # 统计卡车类型
                vehicle_details = data.get('vehicle_details', {})
                truck_type = vehicle_details.get('type', 'UNKNOWN')
                truck_types[truck_type] = truck_types.get(truck_type, 0) + 1

            except Exception as e:
                logger.warning(f"读取装载文件 {file_path.name} 失败: {str(e)}")

        # 统计路径数据
        for file_path in route_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                summary = data.get('summary', {})
                total_distance += summary.get('total_distance_km', 0)

            except Exception as e:
                logger.warning(f"读取路径文件 {file_path.name} 失败: {str(e)}")

        avg_loading_efficiency = (total_loading_efficiency / len(loading_files)) if loading_files else 0

        summary_data = {
            "total_trucks": len(loading_files),
            "total_routes": len(route_files),
            "total_items": total_items,
            "total_distance_km": round(total_distance, 2),
            "average_loading_efficiency": round(avg_loading_efficiency, 2),
            "truck_types": truck_types
        }

        return success_response(
            data=summary_data,
            message="数据摘要统计获取成功"
        )

    except Exception as e:
        logger.error(f"获取数据摘要失败: {str(e)}")
        return error_response(f"获取数据摘要失败: {str(e)}")

def _extract_truck_info(data: Dict, filename: str) -> Dict:
    """
    从装载计划JSON中提取卡车信息
    """
    summary = data.get('summary', {})
    vehicle_details = data.get('vehicle_details', {})

    return {
        "vehicle_id": summary.get('vehicle_id', filename.replace('_loading_plan.json', '')),
        "type": vehicle_details.get('type', 'UNKNOWN'),
        "total_items": summary.get('total_items', 0),
        "total_weight_kg": summary.get('total_weight_kg', 0),
        "total_volume_m3": summary.get('total_volume_m3', 0),
        "loading_efficiency": summary.get('loading_efficiency', 0),
        "volume_utilization": summary.get('volume_utilization', 0),
        "cargo_types": summary.get('cargo_types', []),
        "optimization_algorithm": summary.get('optimization_algorithm', ''),
        "solution_status": summary.get('solution_status', ''),
        "loading_time_minutes": summary.get('loading_time_minutes', 0)
    }

def _extract_route_info(data: Dict, filename: str) -> Dict:
    """
    从路径计划JSON中提取路径信息
    """
    summary = data.get('summary', {})

    return {
        "vehicle_id": summary.get('vehicle_id', filename.replace('_route_plan.json', '')),
        "total_distance_km": summary.get('total_distance_km', 0),
        "total_stops": summary.get('total_stops', 0),
        "optimization_algorithm": summary.get('optimization_algorithm', ''),
        "route_type": summary.get('route_type', ''),
        "start_location": summary.get('start_location', {}),
        "estimated_duration_hours": summary.get('estimated_duration_hours', 0)
    }