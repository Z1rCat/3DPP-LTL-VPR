"""
实验管理路由
Experiment Management Routes
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Dict, List, Any, Optional
from datetime import datetime

from experiment_manager.experiment_tracker import experiment_tracker
from database.db_manager import db_manager

router = APIRouter()

class ExperimentCreate(BaseModel):
    name: str
    description: Optional[str] = None
    algorithm: str = "integrated"
    parameters: Optional[Dict[str, Any]] = None
    created_by: str = "api_user"

class ExperimentUpdate(BaseModel):
    status: Optional[str] = None
    total_orders: Optional[int] = None
    total_vehicles: Optional[int] = None

class ExperimentFilter(BaseModel):
    created_by: Optional[str] = None
    algorithm: Optional[str] = None
    status: Optional[str] = None
    date_from: Optional[str] = None
    date_to: Optional[str] = None

@router.post("/", summary="创建新实验")
async def create_experiment(experiment: ExperimentCreate):
    """
    创建新的优化实验

    - **name**: 实验名称
    - **description**: 实验描述（可选）
    - **algorithm**: 使用的算法，默认 "integrated"
    - **parameters**: 算法参数（可选）
    - **created_by**: 创建者，默认 "api_user"
    """
    try:
        experiment_id = experiment_tracker.start_experiment(
            name=experiment.name,
            description=experiment.description,
            algorithm=experiment.algorithm,
            parameters=experiment.parameters,
            created_by=experiment.created_by
        )

        return {
            "success": True,
            "experiment_id": experiment_id,
            "message": f"实验 '{experiment.name}' 创建成功"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建实验失败: {str(e)}")

@router.get("/", summary="获取实验列表")
async def list_experiments(
    limit: int = Query(50, ge=1, le=1000, description="返回数量限制"),
    offset: int = Query(0, ge=0, description="偏移量"),
    created_by: Optional[str] = Query(None, description="按创建者筛选")
):
    """
    获取实验列表，支持分页和筛选

    - **limit**: 返回数量限制（1-1000）
    - **offset**: 偏移量
    - **created_by**: 按创建者筛选（可选）
    """
    try:
        experiments = experiment_tracker.list_experiments(
            limit=limit,
            offset=offset,
            created_by=created_by
        )

        return {
            "success": True,
            "data": experiments,
            "count": len(experiments),
            "pagination": {
                "limit": limit,
                "offset": offset,
                "has_more": len(experiments) == limit
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取实验列表失败: {str(e)}")

@router.get("/{experiment_id}", summary="获取实验详情")
async def get_experiment(experiment_id: str):
    """
    获取指定实验的详细信息

    - **experiment_id**: 实验ID
    """
    try:
        experiment = experiment_tracker.get_experiment_summary(experiment_id)

        if not experiment:
            raise HTTPException(status_code=404, detail=f"实验 {experiment_id} 不存在")

        return {
            "success": True,
            "data": experiment
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取实验详情失败: {str(e)}")

@router.put("/{experiment_id}", summary="更新实验信息")
async def update_experiment(experiment_id: str, update_data: ExperimentUpdate):
    """
    更新实验信息

    - **experiment_id**: 实验ID
    - **status**: 新状态
    - **total_orders**: 总订单数
    - **total_vehicles**: 总车辆数
    """
    try:
        # 检查实验是否存在
        experiment = experiment_tracker.get_experiment_summary(experiment_id)
        if not experiment:
            raise HTTPException(status_code=404, detail=f"实验 {experiment_id} 不存在")

        # 更新实验状态
        if update_data.status:
            db_manager.update_experiment_status(
                experiment_id=experiment_id,
                status=update_data.status,
                total_orders=update_data.total_orders,
                total_vehicles=update_data.total_vehicles
            )

        return {
            "success": True,
            "message": f"实验 {experiment_id} 更新成功"
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新实验失败: {str(e)}")

@router.post("/{experiment_id}/complete", summary="完成实验")
async def complete_experiment(experiment_id: str, results_data: Optional[Dict] = None):
    """
    标记实验为完成状态并保存结果

    - **experiment_id**: 实验ID
    - **results_data**: 结果数据（可选，为空则自动从output目录收集）
    """
    try:
        # 检查实验是否存在
        experiment = experiment_tracker.get_experiment_summary(experiment_id)
        if not experiment:
            raise HTTPException(status_code=404, detail=f"实验 {experiment_id} 不存在")

        # 完成实验
        experiment_tracker.complete_experiment(experiment_id, results_data)

        return {
            "success": True,
            "message": f"实验 {experiment_id} 已标记为完成"
        }

    except HTTPException:
        raise
    except Exception as e:
        # 如果完成失败，标记为失败状态
        experiment_tracker.fail_experiment(experiment_id, str(e))
        raise HTTPException(status_code=500, detail=f"完成实验失败: {str(e)}")

@router.post("/{experiment_id}/fail", summary="标记实验失败")
async def fail_experiment(experiment_id: str, error_info: Dict[str, str]):
    """
    标记实验为失败状态

    - **experiment_id**: 实验ID
    - **error_info**: 包含error_message的错误信息
    """
    try:
        error_message = error_info.get("error_message", "未知错误")
        experiment_tracker.fail_experiment(experiment_id, error_message)

        return {
            "success": True,
            "message": f"实验 {experiment_id} 已标记为失败"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"标记实验失败状态时出错: {str(e)}")

@router.delete("/{experiment_id}", summary="删除实验")
async def delete_experiment(
    experiment_id: str,
    remove_data: bool = Query(True, description="是否删除相关数据文件")
):
    """
    删除实验（谨慎操作）

    - **experiment_id**: 实验ID
    - **remove_data**: 是否删除相关的数据文件
    """
    try:
        # 检查实验是否存在
        experiment = experiment_tracker.get_experiment_summary(experiment_id)
        if not experiment:
            raise HTTPException(status_code=404, detail=f"实验 {experiment_id} 不存在")

        # 删除实验
        success = experiment_tracker.delete_experiment(experiment_id, remove_data)

        if success:
            return {
                "success": True,
                "message": f"实验 {experiment_id} 删除成功"
            }
        else:
            raise HTTPException(status_code=500, detail="删除实验失败")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除实验时出错: {str(e)}")

@router.get("/{experiment_id}/vehicles", summary="获取实验车辆数据")
async def get_experiment_vehicles(experiment_id: str):
    """
    获取指定实验的车辆数据

    - **experiment_id**: 实验ID
    """
    try:
        experiment = experiment_tracker.get_experiment_summary(experiment_id)
        if not experiment:
            raise HTTPException(status_code=404, detail=f"实验 {experiment_id} 不存在")

        vehicles = experiment.get('vehicles', [])

        return {
            "success": True,
            "data": vehicles,
            "count": len(vehicles)
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取车辆数据失败: {str(e)}")

@router.get("/{experiment_id}/metrics", summary="获取实验性能指标")
async def get_experiment_metrics(experiment_id: str):
    """
    获取指定实验的性能指标

    - **experiment_id**: 实验ID
    """
    try:
        experiment = experiment_tracker.get_experiment_summary(experiment_id)
        if not experiment:
            raise HTTPException(status_code=404, detail=f"实验 {experiment_id} 不存在")

        metrics = experiment.get('metrics', [])

        # 按类别组织指标
        metrics_by_category = {}
        for metric in metrics:
            category = metric.get('category', 'overall')
            if category not in metrics_by_category:
                metrics_by_category[category] = []
            metrics_by_category[category].append(metric)

        return {
            "success": True,
            "data": {
                "all_metrics": metrics,
                "by_category": metrics_by_category,
                "count": len(metrics)
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取性能指标失败: {str(e)}")

@router.post("/compare", summary="对比多个实验")
async def compare_experiments(experiment_ids: List[str]):
    """
    对比多个实验的性能

    - **experiment_ids**: 实验ID列表
    """
    try:
        if len(experiment_ids) < 2:
            raise HTTPException(status_code=400, detail="至少需要2个实验进行对比")

        if len(experiment_ids) > 10:
            raise HTTPException(status_code=400, detail="最多支持对比10个实验")

        # 检查所有实验是否存在
        for exp_id in experiment_ids:
            experiment = experiment_tracker.get_experiment_summary(exp_id)
            if not experiment:
                raise HTTPException(status_code=404, detail=f"实验 {exp_id} 不存在")

        # 执行对比
        comparison_data = db_manager.compare_experiments(experiment_ids)

        return {
            "success": True,
            "data": comparison_data,
            "experiments_compared": len(experiment_ids)
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"实验对比失败: {str(e)}")

@router.get("/statistics/overview", summary="获取实验统计概览")
async def get_experiments_overview():
    """
    获取实验系统的统计概览
    """
    try:
        stats = db_manager.get_statistics()

        return {
            "success": True,
            "data": stats
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取统计概览失败: {str(e)}")

@router.post("/batch/delete", summary="批量删除实验")
async def batch_delete_experiments(
    experiment_ids: List[str],
    remove_data: bool = Query(True, description="是否删除相关数据文件")
):
    """
    批量删除实验（谨慎操作）

    - **experiment_ids**: 实验ID列表
    - **remove_data**: 是否删除相关的数据文件
    """
    try:
        if len(experiment_ids) > 50:
            raise HTTPException(status_code=400, detail="单次批量删除最多支持50个实验")

        deleted_count = 0
        failed_experiments = []

        for exp_id in experiment_ids:
            try:
                success = experiment_tracker.delete_experiment(exp_id, remove_data)
                if success:
                    deleted_count += 1
                else:
                    failed_experiments.append(exp_id)
            except Exception:
                failed_experiments.append(exp_id)

        return {
            "success": True,
            "deleted_count": deleted_count,
            "failed_count": len(failed_experiments),
            "failed_experiments": failed_experiments,
            "message": f"成功删除 {deleted_count} 个实验"
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"批量删除失败: {str(e)}")