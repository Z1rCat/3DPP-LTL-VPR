"""
优化相关的API路由
Optimization API Routes
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Dict, Any, Optional
import logging
from datetime import datetime
import asyncio
import os
from pathlib import Path

from ..models.schemas import OptimizationRequest, OptimizationResult, APIResponse
from ..utils.response import success_response, error_response

router = APIRouter()
logger = logging.getLogger(__name__)

# 优化任务状态存储（生产环境应使用数据库或Redis）
optimization_tasks = {}

@router.post("/run", response_model=APIResponse)
async def run_optimization(
    request: OptimizationRequest,
    background_tasks: BackgroundTasks
):
    """
    运行优化计算
    """
    try:
        task_id = f"opt_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{request.data_source.replace('.', '_')}"

        # 初始化任务状态
        optimization_tasks[task_id] = {
            "status": "started",
            "created_at": datetime.now(),
            "progress": 0,
            "message": "优化任务已开始",
            "request": request.dict(),
            "result": None,
            "error": None
        }

        # 在后台运行优化任务
        background_tasks.add_task(
            _run_optimization_task,
            task_id,
            request
        )

        return success_response(
            data={
                "task_id": task_id,
                "status": "started",
                "estimated_duration_minutes": _estimate_duration(request)
            },
            message="优化任务已开始，请使用task_id查询进度"
        )

    except Exception as e:
        logger.error(f"启动优化任务失败: {str(e)}")
        return error_response(f"启动优化任务失败: {str(e)}")

@router.get("/status/{task_id}", response_model=APIResponse)
async def get_optimization_status(task_id: str):
    """
    获取优化任务状态
    """
    try:
        if task_id not in optimization_tasks:
            return error_response(f"任务 {task_id} 不存在")

        task = optimization_tasks[task_id]

        return success_response(
            data={
                "task_id": task_id,
                "status": task["status"],
                "progress": task["progress"],
                "message": task["message"],
                "created_at": task["created_at"].isoformat(),
                "has_result": task["result"] is not None,
                "has_error": task["error"] is not None
            },
            message=f"任务状态: {task['status']}"
        )

    except Exception as e:
        logger.error(f"获取任务状态失败: {str(e)}")
        return error_response(f"获取任务状态失败: {str(e)}")

@router.get("/result/{task_id}", response_model=APIResponse)
async def get_optimization_result(task_id: str):
    """
    获取优化任务结果
    """
    try:
        if task_id not in optimization_tasks:
            return error_response(f"任务 {task_id} 不存在")

        task = optimization_tasks[task_id]

        if task["status"] != "completed":
            return error_response(f"任务尚未完成，当前状态: {task['status']}")

        if task["error"]:
            return error_response(f"任务执行失败: {task['error']}")

        return success_response(
            data=task["result"],
            message="优化结果获取成功"
        )

    except Exception as e:
        logger.error(f"获取优化结果失败: {str(e)}")
        return error_response(f"获取优化结果失败: {str(e)}")

@router.get("/history", response_model=APIResponse)
async def get_optimization_history(limit: int = 50):
    """
    获取优化任务历史
    """
    try:
        tasks = []
        for task_id, task_data in optimization_tasks.items():
            tasks.append({
                "task_id": task_id,
                "status": task_data["status"],
                "created_at": task_data["created_at"].isoformat(),
                "message": task_data["message"],
                "has_result": task_data["result"] is not None
            })

        # 按创建时间排序（最新的在前）
        tasks.sort(key=lambda x: x["created_at"], reverse=True)

        # 应用数量限制
        tasks = tasks[:limit]

        return success_response(
            data=tasks,
            message=f"找到 {len(tasks)} 个历史任务"
        )

    except Exception as e:
        logger.error(f"获取优化历史失败: {str(e)}")
        return error_response(f"获取优化历史失败: {str(e)}")

@router.delete("/task/{task_id}", response_model=APIResponse)
async def delete_optimization_task(task_id: str):
    """
    删除优化任务
    """
    try:
        if task_id not in optimization_tasks:
            return error_response(f"任务 {task_id} 不存在")

        del optimization_tasks[task_id]

        return success_response(
            data={"task_id": task_id},
            message="任务已删除"
        )

    except Exception as e:
        logger.error(f"删除任务失败: {str(e)}")
        return error_response(f"删除任务失败: {str(e)}")

@router.get("/algorithms", response_model=APIResponse)
async def get_available_algorithms():
    """
    获取可用的优化算法
    """
    algorithms = [
        {
            "id": "gurobi_3dpp",
            "name": "Gurobi 3D装载优化",
            "description": "使用Gurobi求解器进行3D装载优化",
            "category": "bin_packing",
            "supports": ["large_cargo", "single_item"]
        },
        {
            "id": "ltl_optimizer",
            "name": "LTL拼装优化",
            "description": "零担货物拼装优化算法",
            "category": "bin_packing",
            "supports": ["ltl_cargo", "multi_item"]
        },
        {
            "id": "vrp_basic",
            "name": "基本车辆路径优化",
            "description": "基础的车辆路径问题求解",
            "category": "routing",
            "supports": ["route_optimization"]
        },
        {
            "id": "integrated",
            "name": "集成优化",
            "description": "装载优化与路径优化的集成解决方案",
            "category": "integrated",
            "supports": ["full_optimization"]
        }
    ]

    return success_response(
        data=algorithms,
        message=f"可用算法: {len(algorithms)} 个"
    )

async def _run_optimization_task(task_id: str, request: OptimizationRequest):
    """
    运行优化任务的后台函数
    """
    try:
        # 更新任务状态
        optimization_tasks[task_id]["status"] = "running"
        optimization_tasks[task_id]["progress"] = 10
        optimization_tasks[task_id]["message"] = "正在初始化优化环境..."

        # 模拟优化过程
        # 在实际实现中，这里应该调用真实的优化算法
        await _simulate_optimization(task_id, request)

        # 标记任务完成
        optimization_tasks[task_id]["status"] = "completed"
        optimization_tasks[task_id]["progress"] = 100
        optimization_tasks[task_id]["message"] = "优化任务完成"

    except Exception as e:
        logger.error(f"优化任务 {task_id} 失败: {str(e)}")
        optimization_tasks[task_id]["status"] = "failed"
        optimization_tasks[task_id]["error"] = str(e)
        optimization_tasks[task_id]["message"] = f"优化任务失败: {str(e)}"

async def _simulate_optimization(task_id: str, request: OptimizationRequest):
    """
    模拟优化过程（实际实现中应该调用真实的优化系统）
    """
    stages = [
        (20, "正在加载数据..."),
        (40, "正在进行装载优化..."),
        (60, "正在计算路径优化..."),
        (80, "正在生成可视化..."),
        (95, "正在保存结果...")
    ]

    for progress, message in stages:
        await asyncio.sleep(2)  # 模拟处理时间
        optimization_tasks[task_id]["progress"] = progress
        optimization_tasks[task_id]["message"] = message

    # 设置模拟结果
    optimization_tasks[task_id]["result"] = {
        "algorithm_used": request.algorithm,
        "total_trucks": 12,
        "total_items_processed": 7500,
        "average_loading_efficiency": 88.5,
        "total_distance_km": 450.2,
        "optimization_time_seconds": 120.5,
        "visualization_files": [
            "single_category_3dpp_LARGE_TRUCK_000.html",
            "loading_density_heatmap.html",
            "3d_efficiency_analysis.html"
        ],
        "data_files": [
            "LARGE_TRUCK_000_loading_plan.json",
            "LARGE_TRUCK_000_route_plan.json"
        ]
    }

def _estimate_duration(request: OptimizationRequest) -> int:
    """
    估算优化任务持续时间（分钟）
    """
    # 简单的估算逻辑
    base_time = 5  # 基础时间5分钟

    if request.algorithm == "integrated":
        return base_time * 2
    elif request.algorithm == "gurobi_3dpp":
        return base_time + 3
    else:
        return base_time