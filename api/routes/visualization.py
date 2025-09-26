"""
可视化相关的API路由
Visualization API Routes
"""

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse, JSONResponse
from typing import List, Optional, Dict, Any
from pathlib import Path
import json
import logging
from datetime import datetime

from ..models.schemas import VisualizationFile, VisualizationRequest, APIResponse
from ..utils.response import success_response, error_response

router = APIRouter()
logger = logging.getLogger(__name__)

# 可视化文件目录
VISUALIZATION_DIR = Path(__file__).parent.parent.parent / "output" / "visualizations"
REPORTS_DIR = Path(__file__).parent.parent.parent / "output" / "reports"

@router.get("/list", response_model=APIResponse)
async def list_visualizations(
    type_filter: Optional[str] = Query(None, description="过滤类型: 3dpp, heatmap, route, efficiency"),
    limit: Optional[int] = Query(50, description="返回数量限制")
):
    """
    获取可视化文件列表
    """
    try:
        if not VISUALIZATION_DIR.exists():
            return success_response(
                data=[],
                message="可视化目录不存在，请先运行优化生成可视化文件"
            )

        files = []
        for file_path in VISUALIZATION_DIR.glob("*.html"):
            file_stat = file_path.stat()
            file_info = VisualizationFile(
                filename=file_path.name,
                filepath=str(file_path),
                type=_detect_visualization_type(file_path.name),
                size=file_stat.st_size,
                created_at=datetime.fromtimestamp(file_stat.st_ctime),
                modified_at=datetime.fromtimestamp(file_stat.st_mtime)
            )

            # 应用类型过滤
            if type_filter and file_info.type != type_filter:
                continue

            files.append(file_info.dict())

        # 按修改时间排序（最新的在前）
        files.sort(key=lambda x: x['modified_at'], reverse=True)

        # 应用数量限制
        if limit:
            files = files[:limit]

        return success_response(
            data=files,
            message=f"找到 {len(files)} 个可视化文件"
        )

    except Exception as e:
        logger.error(f"获取可视化文件列表失败: {str(e)}")
        return error_response(f"获取可视化文件列表失败: {str(e)}")

@router.get("/file/{filename}")
async def get_visualization_file(filename: str):
    """
    获取特定的可视化文件
    """
    try:
        file_path = VISUALIZATION_DIR / filename

        if not file_path.exists():
            raise HTTPException(status_code=404, detail=f"文件 {filename} 不存在")

        if not file_path.suffix.lower() in ['.html', '.json']:
            raise HTTPException(status_code=400, detail="不支持的文件类型")

        return FileResponse(
            path=str(file_path),
            filename=filename,
            media_type='text/html' if file_path.suffix.lower() == '.html' else 'application/json'
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取可视化文件失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取可视化文件失败: {str(e)}")

@router.get("/types", response_model=APIResponse)
async def get_visualization_types():
    """
    获取可用的可视化类型
    """
    types = [
        {
            "type": "3dpp",
            "name": "3D装载可视化",
            "description": "显示单个卡车的3D装载布局"
        },
        {
            "type": "multi_3dpp",
            "name": "多品类3D可视化",
            "description": "显示多品类混合装载的3D布局"
        },
        {
            "type": "heatmap",
            "name": "装载密度热力图",
            "description": "显示装载空间的密度分布"
        },
        {
            "type": "efficiency",
            "name": "装载效率分析",
            "description": "显示装载效率和性能指标"
        },
        {
            "type": "route",
            "name": "路径优化地图",
            "description": "显示车辆路径优化结果"
        },
        {
            "type": "3d_analysis",
            "name": "3D效率分析",
            "description": "显示3D装载效率分析图表"
        }
    ]

    return success_response(
        data=types,
        message=f"可用的可视化类型: {len(types)} 种"
    )

@router.post("/generate", response_model=APIResponse)
async def generate_visualization(request: VisualizationRequest):
    """
    生成新的可视化
    """
    try:
        # 这里需要集成实际的可视化生成逻辑
        # 暂时返回模拟响应
        return success_response(
            data={
                "task_id": f"viz_task_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "status": "queued",
                "message": "可视化生成任务已加入队列"
            },
            message="可视化生成请求已接受"
        )

    except Exception as e:
        logger.error(f"生成可视化失败: {str(e)}")
        return error_response(f"生成可视化失败: {str(e)}")

@router.get("/stats", response_model=APIResponse)
async def get_visualization_stats():
    """
    获取可视化统计信息
    """
    try:
        if not VISUALIZATION_DIR.exists():
            return success_response(
                data={
                    "total_files": 0,
                    "total_size_mb": 0,
                    "types": {}
                },
                message="可视化目录不存在"
            )

        total_files = 0
        total_size = 0
        type_counts = {}

        for file_path in VISUALIZATION_DIR.glob("*.html"):
            total_files += 1
            total_size += file_path.stat().st_size

            viz_type = _detect_visualization_type(file_path.name)
            type_counts[viz_type] = type_counts.get(viz_type, 0) + 1

        stats = {
            "total_files": total_files,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "types": type_counts,
            "directory": str(VISUALIZATION_DIR)
        }

        return success_response(
            data=stats,
            message="可视化统计信息获取成功"
        )

    except Exception as e:
        logger.error(f"获取可视化统计失败: {str(e)}")
        return error_response(f"获取可视化统计失败: {str(e)}")

def _detect_visualization_type(filename: str) -> str:
    """
    根据文件名检测可视化类型
    """
    filename_lower = filename.lower()

    if "single_category_3dpp" in filename_lower:
        return "3dpp"
    elif "multi_category_3dpp" in filename_lower:
        return "multi_3dpp"
    elif "loading_density_heatmap" in filename_lower:
        return "heatmap"
    elif "loading_efficiency_dashboard" in filename_lower:
        return "efficiency"
    elif "3d_efficiency_analysis" in filename_lower:
        return "3d_analysis"
    elif "route_map" in filename_lower:
        return "route"
    else:
        return "unknown"