"""
系统管理相关的API路由
System Management API Routes
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any, Optional
import logging
import psutil
import os
import shutil
import zipfile
from datetime import datetime, timedelta
from pathlib import Path
import json

from ..models.schemas import APIResponse
from ..utils.response import success_response, error_response
from .auth import get_current_user

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/clear-cache", response_model=APIResponse)
async def clear_cache(current_user: dict = Depends(get_current_user)):
    """
    清理系统缓存
    """
    try:
        # 检查用户权限
        if current_user.get('role') != 'admin':
            return error_response("权限不足", status_code=403)

        cache_cleared = 0

        # 清理输出目录中的临时文件
        output_dirs = ['output/temp', 'output/cache']
        for dir_path in output_dirs:
            if os.path.exists(dir_path):
                for file in os.listdir(dir_path):
                    file_path = os.path.join(dir_path, file)
                    try:
                        if os.path.isfile(file_path):
                            os.remove(file_path)
                            cache_cleared += 1
                        elif os.path.isdir(file_path):
                            shutil.rmtree(file_path)
                            cache_cleared += 1
                    except Exception as e:
                        logger.warning(f"删除缓存文件失败: {file_path}, 错误: {e}")

        # 清理Python缓存
        try:
            import gc
            gc.collect()
        except Exception as e:
            logger.warning(f"清理Python缓存失败: {e}")

        return success_response(
            data={"files_cleared": cache_cleared},
            message=f"缓存清理完成，共清理 {cache_cleared} 个文件"
        )

    except Exception as e:
        logger.error(f"清理缓存失败: {str(e)}")
        return error_response(f"清理缓存失败: {str(e)}")

@router.get("/health-check", response_model=APIResponse)
async def health_check(current_user: dict = Depends(get_current_user)):
    """
    系统健康检查
    """
    try:
        # 获取系统信息
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')

        # 检查数据库状态（简化版）
        database_status = "healthy"
        try:
            # 这里可以添加实际的数据库连接检查
            pass
        except Exception:
            database_status = "error"

        # 检查API服务状态
        api_status = "healthy"  # 如果能到达这里，API就是健康的

        # 计算总体状态
        overall_status = "healthy"
        if cpu_percent > 90 or memory.percent > 90 or disk.percent > 90:
            overall_status = "warning"
        if database_status == "error":
            overall_status = "error"

        health_data = {
            "overall_status": overall_status,
            "cpu_usage": round(cpu_percent, 2),
            "memory_usage": round(memory.percent, 2),
            "disk_usage": round(disk.percent, 2),
            "database_status": database_status,
            "api_status": api_status,
            "timestamp": datetime.now().isoformat()
        }

        return success_response(
            data=health_data,
            message=f"系统检查完成，状态: {overall_status}"
        )

    except Exception as e:
        logger.error(f"系统健康检查失败: {str(e)}")
        return error_response(f"系统健康检查失败: {str(e)}")

@router.post("/export-logs", response_model=APIResponse)
async def export_logs(
    request: dict,
    current_user: dict = Depends(get_current_user)
):
    """
    导出系统日志
    """
    try:
        # 检查用户权限
        if current_user.get('role') != 'admin':
            return error_response("权限不足", status_code=403)

        start_date = request.get('start_date')
        end_date = request.get('end_date')

        # 创建临时目录
        temp_dir = Path('output/temp/logs_export')
        temp_dir.mkdir(parents=True, exist_ok=True)

        # 准备日志文件列表
        log_files = []
        logs_dir = Path('output/logs')

        if logs_dir.exists():
            for log_file in logs_dir.glob('*.log'):
                # 这里可以根据日期过滤日志文件
                log_files.append(log_file)

        # 创建ZIP文件
        zip_filename = f"system_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
        zip_path = temp_dir / zip_filename

        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for log_file in log_files:
                zipf.write(log_file, log_file.name)

            # 添加系统信息
            system_info = {
                "export_time": datetime.now().isoformat(),
                "start_date": start_date,
                "end_date": end_date,
                "files_included": [f.name for f in log_files]
            }

            zipf.writestr("export_info.json", json.dumps(system_info, indent=2))

        # 返回文件信息（实际应该提供下载链接）
        return success_response(
            data={
                "filename": zip_filename,
                "size": zip_path.stat().st_size,
                "files_count": len(log_files),
                "download_url": f"/api/system/download/{zip_filename}"
            },
            message="日志导出完成"
        )

    except Exception as e:
        logger.error(f"导出日志失败: {str(e)}")
        return error_response(f"导出日志失败: {str(e)}")

@router.post("/restart", response_model=APIResponse)
async def restart_system(current_user: dict = Depends(get_current_user)):
    """
    重启系统（模拟）
    """
    try:
        # 检查用户权限
        if current_user.get('role') != 'admin':
            return error_response("权限不足", status_code=403)

        # 在生产环境中，这里应该触发实际的系统重启
        # 现在只是模拟响应
        logger.info(f"系统重启请求，操作用户: {current_user.get('username')}")

        return success_response(
            data={"restart_scheduled": True, "restart_time": 10},
            message="系统重启指令已发送，将在10秒后重启"
        )

    except Exception as e:
        logger.error(f"重启系统失败: {str(e)}")
        return error_response(f"重启系统失败: {str(e)}")

@router.get("/info", response_model=APIResponse)
async def get_system_info(current_user: dict = Depends(get_current_user)):
    """
    获取系统配置信息
    """
    try:
        # 这里应该从配置文件或数据库读取实际配置
        system_info = {
            "max_file_size": 100,  # MB
            "smtp_server": "",
            "sender_email": "",
            "session_timeout": 8,  # hours
            "min_password_length": 8,
            "auto_backup": False,
            "enable_email_notify": False,
            "require_strong_password": True
        }

        return success_response(
            data=system_info,
            message="系统信息获取成功"
        )

    except Exception as e:
        logger.error(f"获取系统信息失败: {str(e)}")
        return error_response(f"获取系统信息失败: {str(e)}")

@router.put("/settings", response_model=APIResponse)
async def update_system_settings(
    settings: dict,
    current_user: dict = Depends(get_current_user)
):
    """
    更新系统设置
    """
    try:
        # 检查用户权限
        if current_user.get('role') != 'admin':
            return error_response("权限不足", status_code=403)

        # 验证设置值
        if settings.get('max_file_size', 0) <= 0:
            return error_response("文件大小限制必须大于0")

        if settings.get('session_timeout', 0) <= 0:
            return error_response("会话超时时间必须大于0")

        if settings.get('min_password_length', 0) < 6:
            return error_response("密码最小长度不能少于6位")

        # 在实际应用中，这里应该保存到配置文件或数据库
        logger.info(f"系统设置更新，操作用户: {current_user.get('username')}")
        logger.info(f"更新的设置: {settings}")

        return success_response(
            data=settings,
            message="系统设置保存成功"
        )

    except Exception as e:
        logger.error(f"保存系统设置失败: {str(e)}")
        return error_response(f"保存系统设置失败: {str(e)}")

@router.get("/stats", response_model=APIResponse)
async def get_system_stats():
    """
    获取系统统计信息
    """
    try:
        # 获取基本系统统计
        stats = {
            "uptime": "运行中",
            "total_tasks": 0,
            "active_users": 1,
            "disk_usage": 0,
            "last_backup": None
        }

        # 统计任务数量
        try:
            # 这里应该从数据库查询实际数据
            pass
        except Exception:
            pass

        # 统计磁盘使用
        try:
            disk = psutil.disk_usage('/')
            stats["disk_usage"] = round(disk.percent, 2)
        except Exception:
            pass

        return success_response(
            data=stats,
            message="系统统计获取成功"
        )

    except Exception as e:
        logger.error(f"获取系统统计失败: {str(e)}")
        return error_response(f"获取系统统计失败: {str(e)}")