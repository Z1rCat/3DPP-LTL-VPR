"""
真实物流数据 API 路由
Real Logistics Data API Routes
"""

from fastapi import APIRouter, HTTPException
from pathlib import Path
import json
import pandas as pd
from typing import Dict, List, Any, Optional
from datetime import datetime
import glob
import os

router = APIRouter()

# 数据路径配置
OUTPUT_DIR = Path(__file__).parent.parent.parent / "output"
REPORTS_DIR = OUTPUT_DIR / "reports"
INTERMEDIATE_DIR = OUTPUT_DIR / "intermediate"
OPTIMIZATION_RESULTS_DIR = OUTPUT_DIR / "optimization_results"

@router.get("/optimization-summary")
async def get_optimization_summary() -> Dict[str, Any]:
    """获取优化结果汇总"""
    try:
        # 尝试读取最新的优化汇总文件
        summary_file = OUTPUT_DIR / "optimization_summary.json"

        if summary_file.exists():
            with open(summary_file, 'r', encoding='utf-8') as f:
                return json.load(f)

        # 如果没有汇总文件，从各个报告文件中汇总数据
        return generate_summary_from_reports()

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"无法获取优化汇总: {str(e)}")

@router.get("/loading-plans")
async def get_loading_plans() -> List[Dict[str, Any]]:
    """获取所有车辆的装载计划"""
    try:
        loading_plans = []

        # 搜索所有装载计划文件
        pattern = str(REPORTS_DIR / "*_loading_plan.json")
        loading_files = glob.glob(pattern)

        for file_path in loading_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    plan_data = json.load(f)
                    loading_plans.append(plan_data)
            except Exception as e:
                print(f"读取装载计划文件失败 {file_path}: {e}")
                continue

        # 按车辆ID排序
        loading_plans.sort(key=lambda x: x.get('summary', {}).get('vehicle_id', ''))

        return loading_plans

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"无法获取装载计划: {str(e)}")

@router.get("/loading-plans/{truck_id}")
async def get_loading_plan_by_truck(truck_id: str) -> Dict[str, Any]:
    """获取指定车辆的装载计划"""
    try:
        # 标准化truck_id格式
        standardized_id = standardize_truck_id(truck_id)
        pattern = str(REPORTS_DIR / f"{standardized_id}_loading_plan.json")

        matching_files = glob.glob(pattern)

        if not matching_files:
            raise HTTPException(status_code=404, detail=f"未找到车辆 {truck_id} 的装载计划")

        with open(matching_files[0], 'r', encoding='utf-8') as f:
            return json.load(f)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取装载计划失败: {str(e)}")

@router.get("/route-plans")
async def get_route_plans() -> List[Dict[str, Any]]:
    """获取所有车辆的路径计划"""
    try:
        route_plans = []

        # 搜索所有路径计划文件
        pattern = str(REPORTS_DIR / "*_route_plan.json")
        route_files = glob.glob(pattern)

        for file_path in route_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    plan_data = json.load(f)

                    # 提取路径坐标信息
                    route_data = extract_route_coordinates(plan_data)
                    if route_data:
                        route_plans.append(route_data)

            except Exception as e:
                print(f"读取路径计划文件失败 {file_path}: {e}")
                continue

        # 按车辆ID排序
        route_plans.sort(key=lambda x: x.get('truck_id', ''))

        return route_plans

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"无法获取路径计划: {str(e)}")

@router.get("/route-plans/{truck_id}")
async def get_route_plan_by_truck(truck_id: str) -> Dict[str, Any]:
    """获取指定车辆的路径计划"""
    try:
        # 标准化truck_id格式
        standardized_id = standardize_truck_id(truck_id)
        pattern = str(REPORTS_DIR / f"{standardized_id}_route_plan.json")

        matching_files = glob.glob(pattern)

        if not matching_files:
            raise HTTPException(status_code=404, detail=f"未找到车辆 {truck_id} 的路径计划")

        with open(matching_files[0], 'r', encoding='utf-8') as f:
            plan_data = json.load(f)

        # 提取路径坐标信息
        return extract_route_coordinates(plan_data)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取路径计划失败: {str(e)}")

@router.get("/optimization-results")
async def get_optimization_results() -> List[Dict[str, Any]]:
    """获取所有优化结果"""
    try:
        results = []

        # 搜索所有优化结果文件
        pattern = str(OPTIMIZATION_RESULTS_DIR / "*_summary.json")
        result_files = glob.glob(pattern)

        for file_path in result_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    result_data = json.load(f)
                    results.append(result_data)
            except Exception as e:
                print(f"读取优化结果文件失败 {file_path}: {e}")
                continue

        # 按生成时间排序（最新的在前）
        results.sort(key=lambda x: x.get('generated_time', ''), reverse=True)

        return results

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"无法获取优化结果: {str(e)}")

@router.get("/dispatch-plan")
async def get_dispatch_plan() -> Dict[str, Any]:
    """获取调度计划"""
    try:
        # 查找最新的调度计划文件
        dispatch_files = list(INTERMEDIATE_DIR.glob("full_dispatch_plan*.json"))

        if not dispatch_files:
            return {"dispatch_plan": {}, "metadata": {"message": "暂无调度计划"}}

        # 选择最新的文件
        latest_file = max(dispatch_files, key=os.path.getctime)

        with open(latest_file, 'r', encoding='utf-8') as f:
            return json.load(f)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"无法获取调度计划: {str(e)}")

@router.get("/system-status")
async def get_system_status() -> Dict[str, Any]:
    """获取系统状态"""
    try:
        # 检查各个数据目录的状态
        reports_exist = REPORTS_DIR.exists()
        intermediate_exist = INTERMEDIATE_DIR.exists()
        optimization_results_exist = OPTIMIZATION_RESULTS_DIR.exists()

        # 统计文件数量
        loading_plan_files = len(glob.glob(str(REPORTS_DIR / "*_loading_plan.json")))
        route_plan_files = len(glob.glob(str(REPORTS_DIR / "*_route_plan.json")))
        optimization_result_files = len(glob.glob(str(OPTIMIZATION_RESULTS_DIR / "*_summary.json")))

        # 获取最新文件的时间戳
        latest_timestamp = get_latest_file_timestamp()

        return {
            "status": "healthy",
            "data_directories": {
                "reports": reports_exist,
                "intermediate": intermediate_exist,
                "optimization_results": optimization_results_exist
            },
            "file_counts": {
                "loading_plans": loading_plan_files,
                "route_plans": route_plan_files,
                "optimization_results": optimization_result_files
            },
            "latest_update": latest_timestamp,
            "api_version": "1.0.0"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"无法获取系统状态: {str(e)}")

def generate_summary_from_reports() -> Dict[str, Any]:
    """从报告文件生成汇总数据"""
    try:
        # 获取所有装载计划
        loading_plans = []
        loading_files = glob.glob(str(REPORTS_DIR / "*_loading_plan.json"))

        total_trucks = 0
        total_items = 0
        total_volume = 0
        loading_efficiencies = []

        for file_path in loading_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    plan_data = json.load(f)
                    summary = plan_data.get('summary', {})

                    total_trucks += 1
                    total_items += summary.get('total_items', 0)
                    total_volume += summary.get('total_volume_m3', 0)
                    loading_efficiencies.append(summary.get('loading_efficiency', 0))

            except Exception as e:
                print(f"处理装载计划文件失败 {file_path}: {e}")
                continue

        average_efficiency = sum(loading_efficiencies) / len(loading_efficiencies) if loading_efficiencies else 0

        return {
            "algorithm_used": "gurobi_3dpp",
            "data_source": "real_optimization_results",
            "execution_time": 0.0,
            "total_trucks": total_trucks,
            "total_items": total_items,
            "total_volume": total_volume,
            "average_loading_efficiency": average_efficiency / 100,  # 转换为小数
            "generated_time": datetime.now().isoformat()
        }

    except Exception as e:
        print(f"生成汇总数据失败: {e}")
        return {
            "algorithm_used": "unknown",
            "data_source": "error",
            "execution_time": 0,
            "total_trucks": 0,
            "total_items": 0,
            "total_volume": 0,
            "average_loading_efficiency": 0,
            "error": str(e)
        }

def standardize_truck_id(truck_id: str) -> str:
    """标准化车辆ID格式"""
    if 'TRUCK_' in truck_id:
        # 提取数字部分并格式化为3位
        number_part = truck_id.split('_')[-1]
        try:
            number = int(number_part)
            return f"TRUCK_{number:03d}"
        except ValueError:
            return truck_id
    return truck_id

def extract_route_coordinates(plan_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """从路径计划数据中提取坐标信息"""
    try:
        summary = plan_data.get('summary', {})
        itinerary = plan_data.get('itinerary', [])

        # 构建路径坐标点
        route_points = []

        # 添加起始点（仓库）
        route_points.append({
            "lat": 30.800835,  # 成都仓库坐标
            "lng": 104.139111
        })

        # 添加所有停靠点
        for stop in itinerary:
            coords = stop.get('coordinates', [])
            if len(coords) >= 2:
                route_points.append({
                    "lat": coords[0],
                    "lng": coords[1]
                })

        # 返回终点（仓库）
        route_points.append({
            "lat": 30.800835,
            "lng": 104.139111
        })

        return {
            "truck_id": summary.get('vehicle_id', 'unknown'),
            "route": route_points,
            "total_distance_km": summary.get('total_distance_km', 0),
            "stops": summary.get('total_stops', 0),
            "estimated_time_hours": summary.get('total_duration_hours', 0),
            "cargo_type": summary.get('cargo_type', 'unknown'),
            "cargo_quantity": summary.get('cargo_quantity', 0)
        }

    except Exception as e:
        print(f"提取路径坐标失败: {e}")
        return None

def get_latest_file_timestamp() -> str:
    """获取最新文件的时间戳"""
    try:
        all_files = []

        # 搜索所有相关文件
        all_files.extend(glob.glob(str(REPORTS_DIR / "*.json")))
        all_files.extend(glob.glob(str(INTERMEDIATE_DIR / "*.json")))
        all_files.extend(glob.glob(str(OPTIMIZATION_RESULTS_DIR / "*.json")))

        if not all_files:
            return datetime.now().isoformat()

        # 获取最新文件的修改时间
        latest_file = max(all_files, key=os.path.getctime)
        timestamp = datetime.fromtimestamp(os.path.getctime(latest_file))

        return timestamp.isoformat()

    except Exception:
        return datetime.now().isoformat()