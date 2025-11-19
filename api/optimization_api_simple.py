"""
简化版优化任务管理API
Simplified Optimization Task Management API

提供基础的优化任务管理功能，用于演示完整的前后端集成流程。
"""

import asyncio
import uuid
import json
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from pathlib import Path
from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect, BackgroundTasks
from fastapi.responses import FileResponse
from pydantic import BaseModel

# 导入简单演示优化器
from optimization.simple_demo_optimizer import SimpleDemoOptimizer

router = APIRouter()

# 全局任务存储（生产环境应使用数据库）
active_tasks: Dict[str, Dict] = {}
task_history: List[Dict] = []
websocket_connections: Dict[str, List[WebSocket]] = {}

# 初始化简单演示优化器
demo_optimizer = SimpleDemoOptimizer()


class OptimizationRequest(BaseModel):
    """优化请求模型"""
    optimization_mode: str = "demo"  # "fast", "enhanced", "demo"
    order_count: int = 50
    data_source: str = "demo"  # "demo", "upload", "database"
    config: Optional[Dict[str, Any]] = None


class TaskStatus(BaseModel):
    """任务状态模型"""
    task_id: str
    status: str  # "pending", "running", "completed", "error", "cancelled"
    progress: float = 0.0  # 0-100
    current_step: str = ""
    total_steps: int = 0
    message: str = ""
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    result_available: bool = False


@router.post("/start")
async def start_optimization(request: OptimizationRequest, background_tasks: BackgroundTasks):
    """
    启动优化任务
    """
    task_id = str(uuid.uuid4())

    # 创建任务记录
    task = TaskStatus(
        task_id=task_id,
        status="pending",
        progress=0.0,
        current_step="等待启动",
        total_steps=7,  # 默认7个步骤
        message=f"优化任务已创建，模式: {request.optimization_mode}",
        created_at=datetime.now(),
        result_available=False
    )

    # 保存任务
    active_tasks[task_id] = {
        "task_info": task.dict(),
        "request": request.dict(),
        "result": None
    }

    # 初始化WebSocket连接列表
    websocket_connections[task_id] = []

    # 异步启动优化任务
    background_tasks.add_task(run_optimization_task, task_id, request)

    return {
        "success": True,
        "task_id": task_id,
        "message": "优化任务已启动",
        "estimated_time": _estimate_optimization_time(request.optimization_mode, request.order_count)
    }


async def run_optimization_task(task_id: str, request: OptimizationRequest):
    """执行优化任务"""
    try:
        # 更新任务状态为运行中
        await update_task_status(task_id, "running", "开始优化流程...", 0)

        # 根据模式选择优化器
        progress_callback = lambda progress: websocket_progress_update(task_id, progress)
        result = await demo_optimizer.run_complete_optimization_demo(
            progress_callback=progress_callback,
            order_count=request.order_count,
            optimization_mode=request.optimization_mode
        )

        # 保存结果
        active_tasks[task_id]["result"] = result
        await update_task_status(task_id, "completed", "优化完成！", 100)

        # 生成可视化文件
        await generate_visualizations(task_id, result)

        # 移动到历史记录
        _move_to_history(task_id)

    except Exception as e:
        error_msg = f"优化任务执行失败: {str(e)}"
        print(f"[错误] 任务 {task_id} 失败: {error_msg}")
        await update_task_status(task_id, "error", error_msg, 0)
        _move_to_history(task_id)


@router.get("/status/{task_id}")
async def get_task_status(task_id: str):
    """获取任务状态"""
    # 检查活跃任务
    if task_id in active_tasks:
        return {
            "success": True,
            "task": active_tasks[task_id]["task_info"],
            "result_available": active_tasks[task_id]["result"] is not None
        }

    # 检查历史任务
    for task in task_history:
        if task["task_id"] == task_id:
            return {
                "success": True,
                "task": task,
                "result_available": task.get("result") is not None,
                "from_history": True
            }

    raise HTTPException(status_code=404, detail=f"任务 {task_id} 不存在")


@router.get("/result/{task_id}")
async def get_task_result(task_id: str):
    """获取任务结果"""
    # 检查活跃任务
    if task_id in active_tasks and active_tasks[task_id]["result"]:
        return {
            "success": True,
            "result": active_tasks[task_id]["result"],
            "task_info": active_tasks[task_id]["task_info"]
        }

    # 检查历史任务
    for task in task_history:
        if task["task_id"] == task_id and task.get("result"):
            return {
                "success": True,
                "result": task["result"],
                "task_info": task,
                "from_history": True
            }

    return {
        "success": False,
        "message": "任务结果不存在或任务尚未完成",
        "task_id": task_id
    }


@router.get("/history")
async def get_task_history(limit: int = 20):
    """获取任务历史"""
    # 返回最近的任务（按创建时间倒序）
    recent_tasks = sorted(task_history, key=lambda x: x["created_at"], reverse=True)[:limit]

    return {
        "success": True,
        "tasks": recent_tasks,
        "total_count": len(task_history),
        "active_tasks_count": len(active_tasks)
    }


@router.post("/cancel/{task_id}")
async def cancel_task(task_id: str):
    """取消任务"""
    if task_id in active_tasks:
        # 更新任务状态
        await update_task_status(task_id, "cancelled", "任务已取消", 0)

        # 移动到历史记录
        _move_to_history(task_id)

        return {
            "success": True,
            "message": f"任务 {task_id} 已取消"
        }

    raise HTTPException(status_code=404, detail=f"任务 {task_id} 不存在或已完成")


@router.get("/demo-data")
async def get_demo_data(count: int = 50):
    """获取演示数据"""
    try:
        demo_data = demo_optimizer.generate_demo_data(count)
        return {
            "success": True,
            "data": demo_data,
            "count": len(demo_data)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取演示数据失败: {str(e)}")


@router.get("/statistics")
async def get_optimization_statistics():
    """获取优化统计信息"""
    try:
        demo_stats = demo_optimizer.get_optimization_statistics()

        # 添加实时统计
        real_time_stats = {
            "active_tasks": len(active_tasks),
            "total_completed_tasks": len([t for t in task_history if t["status"] == "completed"]),
            "total_failed_tasks": len([t for t in task_history if t["status"] == "error"]),
            "average_completion_time": _calculate_average_completion_time(),
            "most_used_mode": _get_most_used_mode()
        }

        return {
            "success": True,
            "demo_statistics": demo_stats,
            "real_time_statistics": real_time_stats
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取统计信息失败: {str(e)}")


@router.websocket("/progress/{task_id}")
async def websocket_progress(websocket: WebSocket, task_id: str):
    """WebSocket进度更新"""
    await websocket.accept()

    # 添加连接
    if task_id not in websocket_connections:
        websocket_connections[task_id] = []
    websocket_connections[task_id].append(websocket)

    try:
        # 持续发送进度更新
        while True:
            if task_id in active_tasks:
                task_info = active_tasks[task_id]["task_info"]

                await websocket.send_json({
                    "task_id": task_id,
                    "status": task_info["status"],
                    "progress": task_info["progress"],
                    "current_step": task_info["current_step"],
                    "message": task_info["message"],
                    "created_at": task_info["created_at"].isoformat(),
                    "started_at": task_info.get("started_at"),
                    "completed_at": task_info.get("completed_at")
                })

                # 如果任务完成或失败，关闭连接
                if task_info["status"] in ["completed", "error", "cancelled"]:
                    break

            await asyncio.sleep(1)

    except WebSocketDisconnect:
        pass
    finally:
        # 移除连接
        if task_id in websocket_connections:
            websocket_connections[task_id].remove(websocket)
            if not websocket_connections[task_id]:
                del websocket_connections[task_id]


# 辅助函数

async def update_task_status(task_id: str, status: str, message: str, progress: float = None, step: int = None):
    """更新任务状态"""
    if task_id not in active_tasks:
        return

    task_info = active_tasks[task_id]["task_info"]
    task_info["status"] = status
    task_info["message"] = message

    if progress is not None:
        task_info["progress"] = progress

    if step is not None:
        task_info["step"] = step

    if status == "running" and not task_info.get("started_at"):
        task_info["started_at"] = datetime.now().isoformat()
    elif status in ["completed", "error", "cancelled"]:
        task_info["completed_at"] = datetime.now().isoformat()
        task_info["result_available"] = True

    # 通过WebSocket广播更新
    await websocket_progress_update(task_id, task_info)


async def websocket_progress_update(task_id: str, progress_data: Dict):
    """WebSocket进度更新广播"""
    if task_id in websocket_connections:
        disconnected = []

        for websocket in websocket_connections[task_id]:
            try:
                await websocket.send_json({
                    "task_id": task_id,
                    **progress_data
                })
            except Exception:
                disconnected.append(websocket)

        # 移除断开的连接
        for ws in disconnected:
            websocket_connections[task_id].remove(ws)


def _move_to_history(task_id: str):
    """将任务移动到历史记录"""
    if task_id in active_tasks:
        task = active_tasks[task_id]

        # 限制历史记录数量
        if len(task_history) >= 100:
            task_history.pop(0)  # 移除最旧的记录

        task_history.append(task["task_info"])
        del active_tasks[task_id]

        # 清理WebSocket连接
        if task_id in websocket_connections:
            del websocket_connections[task_id]


def _estimate_optimization_time(mode: str, order_count: int) -> str:
    """估算优化时间"""
    if mode == "demo":
        return "约 10-20 秒"
    elif mode == "fast":
        return "约 1-3 分钟"
    elif mode == "enhanced":
        return "约 5-15 分钟"
    else:
        return "未知"


async def generate_visualizations(task_id: str, result: Dict):
    """生成可视化文件"""
    try:
        # 这里可以调用可视化模块生成图表
        # 例如：3D装箱图、性能指标图等
        print(f"[可视化] 为任务 {task_id} 生成可视化文件")

        # 生成结果摘要文件
        output_dir = Path("output/optimization_results")
        output_dir.mkdir(exist_ok=True)

        summary_file = output_dir / f"{task_id}_summary.json"
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2, default=str)

        print(f"[可视化] 结果摘要已保存: {summary_file}")

    except Exception as e:
        print(f"[错误] 生成可视化文件失败: {str(e)}")


def _calculate_average_completion_time() -> float:
    """计算平均完成时间"""
    completed_tasks = [
        task for task in task_history
        if task["status"] == "completed" and task.get("started_at") and task.get("completed_at")
    ]

    if not completed_tasks:
        return 0.0

    total_time = 0.0
    for task in completed_tasks:
        start = datetime.fromisoformat(task["started_at"])
        end = datetime.fromisoformat(task["completed_at"])
        total_time += (end - start).total_seconds()

    return round(total_time / len(completed_tasks), 2)


def _get_most_used_mode() -> str:
    """获取最常用的优化模式"""
    if not task_history:
        return "无数据"

    mode_count = {}
    for task in task_history:
        if "request" in task:
            mode = task["request"].get("optimization_mode", "unknown")
            mode_count[mode] = mode_count.get(mode, 0) + 1

    if not mode_count:
        return "无数据"

    return max(mode_count, key=mode_count.get)