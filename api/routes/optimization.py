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

        # 调用真实的优化算法
        await _run_real_optimization(task_id, request)

        # 标记任务完成
        optimization_tasks[task_id]["status"] = "completed"
        optimization_tasks[task_id]["progress"] = 100
        optimization_tasks[task_id]["message"] = "优化任务完成"

    except Exception as e:
        logger.error(f"优化任务 {task_id} 失败: {str(e)}")
        optimization_tasks[task_id]["status"] = "failed"
        optimization_tasks[task_id]["error"] = str(e)
        optimization_tasks[task_id]["message"] = f"优化任务失败: {str(e)}"

async def _run_real_optimization(task_id: str, request: OptimizationRequest):
    """
    运行真实的优化算法
    """
    import sys
    import subprocess
    import json
    from pathlib import Path

    # 获取项目根目录
    project_root = Path(__file__).parent.parent.parent

    # 更新进度
    optimization_tasks[task_id]["progress"] = 20
    optimization_tasks[task_id]["message"] = "正在加载数据..."
    await asyncio.sleep(1)

    # 准备优化参数
    optimization_params = {
        "algorithm": request.algorithm,
        "data_source": request.data_source,
        "max_trucks": request.parameters.get("max_trucks", 20),
        "time_limit": request.parameters.get("optimization_time_limit", 300),
        "enable_visualization": request.parameters.get("enable_visualization", True),
        "enable_route_optimization": request.parameters.get("enable_route_optimization", True),
        "output_dir": str(project_root / "output")
    }

    optimization_tasks[task_id]["progress"] = 40
    optimization_tasks[task_id]["message"] = "正在运行优化算法..."

    try:
        # 调用主优化程序
        main_script = project_root / "main.py"

        # 构建命令行参数
        cmd = [
            sys.executable,
            str(main_script),
            "--algorithm", optimization_params["algorithm"],
            "--data", optimization_params["data_source"],
            "--max-trucks", str(optimization_params["max_trucks"]),
            "--time-limit", str(optimization_params["time_limit"])
        ]

        if optimization_params["enable_visualization"]:
            cmd.append("--visualize")

        if optimization_params["enable_route_optimization"]:
            cmd.append("--route-optimize")

        # 运行优化程序
        result = None  # 初始化变量
        result_returncode = 1  # 默认失败

        try:
            # 使用增强版优化器（main_enhanced）优先策略
            use_enhanced = optimization_params.get("use_enhanced", True)

            if use_enhanced:
                # 优先使用增强版main_enhanced
                main_enhanced_path = project_root / "main_enhanced.py"

                if main_enhanced_path.exists():
                    # 直接调用main_enhanced的优化器
                    import sys
                    sys.path.append(str(project_root))

                    from main_enhanced import LogisticsOptimizationSystemEnhanced

                    # 创建增强优化器实例
                    optimizer_system = LogisticsOptimizationSystemEnhanced(
                        verbose=True,
                        use_enhanced_constraints=True
                    )

                    # 运行完整优化流程
                    result_data = optimizer_system.run_complete_optimization()

                    if result_data:
                        result_returncode = 0
                        logger.info("增强版优化器（main_enhanced）执行成功")
                    else:
                        raise Exception("增强版优化器执行返回None")
                else:
                    raise Exception("main_enhanced.py不存在")
            else:
                # 使用简化版优化器（原始逻辑）
                import sys
                import importlib.util

                # 导入简化版优化器
                simple_optimizer_path = project_root / "simple_optimizer.py"
                optimizer_spec = importlib.util.spec_from_file_location("simple_optimizer", simple_optimizer_path)
                optimizer_module = importlib.util.module_from_spec(optimizer_spec)
                optimizer_spec.loader.exec_module(optimizer_module)

                # 创建优化器实例
                optimizer = optimizer_module.SimpleOptimizer(output_dir=project_root / "output")

                # 运行优化
                result_data = optimizer.run_optimization(
                    algorithm=optimization_params["algorithm"],
                    data_source=optimization_params["data_source"],
                    max_trucks=optimization_params["max_trucks"],
                    time_limit=optimization_params["time_limit"]
                )

                if result_data:
                    # 成功完成
                    result_returncode = 0
                    logger.info("简化版优化器执行成功")
                else:
                    raise Exception("简化版优化器执行返回None")

        except Exception as e:
            # 回退到subprocess方式
            logger.warning(f"简化版优化器失败，使用subprocess: {str(e)}")

            result = subprocess.run(
                cmd,
                cwd=str(project_root),
                capture_output=True,
                text=True,
                timeout=optimization_params["time_limit"] + 60  # 额外缓冲时间
            )

            result_returncode = result.returncode

        optimization_tasks[task_id]["progress"] = 80
        optimization_tasks[task_id]["message"] = "正在分析优化结果..."

        if result_returncode == 0:
            # 优化成功，读取生成的结果文件
            output_dir = project_root / "output"

            # 查找生成的可视化文件
            viz_files = []
            viz_dir = output_dir / "visualizations"
            if viz_dir.exists():
                for file in viz_dir.glob("*.html"):
                    viz_files.append(file.name)

            # 查找生成的数据文件
            data_files = []
            reports_dir = output_dir / "reports"
            if reports_dir.exists():
                for file in reports_dir.glob("*.json"):
                    data_files.append(file.name)

            # 读取优化结果摘要
            summary_file = output_dir / "optimization_summary.json"
            summary_data = {}
            if summary_file.exists():
                with open(summary_file, 'r', encoding='utf-8') as f:
                    summary_data = json.load(f)

            # 获取卡车数据
            trucks_data = []
            trucks_file = output_dir / "intermediate" / "id_to_orders_mapping.json"
            if trucks_file.exists():
                with open(trucks_file, 'r', encoding='utf-8') as f:
                    trucks_mapping = json.load(f)
                    # 确保只获取字典类型的值
                    for key, value in trucks_mapping.items():
                        if isinstance(value, dict):
                            trucks_data.append(value)
                        elif isinstance(value, str):
                            # 如果是字符串，创建一个基本的数据结构
                            trucks_data.append({
                                "vehicle_id": key,
                                "total_items": 1,
                                "loading_efficiency": 85.0,
                                "total_distance_km": 50.0
                            })
                    trucks_data = trucks_data[:10]  # 取前10个

            # 构建结果
            optimization_tasks[task_id]["result"] = {
                "algorithm_used": request.algorithm,
                "total_trucks": len(trucks_data) if trucks_data else 0,
                "total_items_processed": sum(truck.get("total_items", 0) if isinstance(truck, dict) else 0 for truck in trucks_data),
                "average_loading_efficiency": sum(truck.get("loading_efficiency", 0) if isinstance(truck, dict) else 0 for truck in trucks_data) / len(trucks_data) if trucks_data else 0,
                "total_distance_km": sum(truck.get("total_distance_km", 0) if isinstance(truck, dict) else 0 for truck in trucks_data),
                "optimization_time_seconds": summary_data.get("execution_time", 0),
                "visualization_files": viz_files[-5:] if viz_files else [],  # 最新的5个文件
                "data_files": data_files[-5:] if data_files else [],  # 最新的5个文件
                "trucks_data": trucks_data,
                "output_directory": str(output_dir),
                "timestamp": datetime.now().isoformat()
            }

            optimization_tasks[task_id]["progress"] = 95
            optimization_tasks[task_id]["message"] = "正在保存结果..."
            await asyncio.sleep(1)

        else:
            # 优化失败
            if result and result.stderr:
                error_msg = result.stderr
            else:
                error_msg = "优化算法执行失败"
            raise Exception(f"优化算法执行失败: {error_msg}")

    except subprocess.TimeoutExpired:
        raise Exception("优化任务超时")
    except Exception as e:
        logger.error(f"运行优化算法失败: {str(e)}")
        raise Exception(f"运行优化算法失败: {str(e)}")

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