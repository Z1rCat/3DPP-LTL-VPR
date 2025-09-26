"""
API响应格式化工具
API Response Formatting Utilities
"""

from typing import Any, Optional
from datetime import datetime
from ..models.schemas import APIResponse

def success_response(data: Any = None, message: str = "操作成功") -> APIResponse:
    """
    创建成功响应

    Args:
        data: 响应数据
        message: 响应消息

    Returns:
        APIResponse: 格式化的成功响应
    """
    return APIResponse(
        success=True,
        message=message,
        data=data,
        timestamp=datetime.now()
    )

def error_response(message: str, data: Any = None) -> APIResponse:
    """
    创建错误响应

    Args:
        message: 错误消息
        data: 错误详细数据

    Returns:
        APIResponse: 格式化的错误响应
    """
    return APIResponse(
        success=False,
        message=message,
        data=data,
        timestamp=datetime.now()
    )

def paginated_response(
    items: list,
    total: int,
    page: int = 1,
    page_size: int = 50,
    message: str = "数据获取成功"
) -> APIResponse:
    """
    创建分页响应

    Args:
        items: 当前页数据
        total: 总记录数
        page: 当前页号
        page_size: 每页大小
        message: 响应消息

    Returns:
        APIResponse: 格式化的分页响应
    """
    total_pages = (total + page_size - 1) // page_size

    data = {
        "items": items,
        "pagination": {
            "current_page": page,
            "page_size": page_size,
            "total_items": total,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1
        }
    }

    return success_response(data=data, message=message)