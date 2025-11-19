"""
API数据模型定义
API Data Models and Schemas
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Union
from datetime import datetime
from enum import Enum

# ===== 通用响应模型 =====
class APIResponse(BaseModel):
    """API通用响应格式"""
    success: bool = Field(description="是否成功")
    message: str = Field(description="响应消息")
    data: Optional[Any] = Field(None, description="响应数据")
    timestamp: datetime = Field(default_factory=datetime.now, description="响应时间")

# ===== 用户认证相关模型 =====
class UserRole(str, Enum):
    """用户角色枚举"""
    ADMIN = "admin"
    OPERATOR = "operator"
    VIEWER = "viewer"
    DRIVER = "driver"      # 司机
    MANAGER = "manager"    # 管理层
    CUSTOMER = "customer"  # 客户

class LoginRequest(BaseModel):
    """登录请求模型"""
    username: str = Field(description="用户名", min_length=3, max_length=20)
    password: str = Field(description="密码", min_length=1)
    rememberMe: bool = Field(False, description="记住我")

class RegisterRequest(BaseModel):
    """注册请求模型"""
    username: str = Field(description="用户名", min_length=3, max_length=20)
    email: str = Field(description="邮箱地址")
    password: str = Field(description="密码", min_length=8)
    passwordConfirm: str = Field(description="确认密码")
    role: UserRole = Field(description="用户角色")
    agreeTerms: bool = Field(description="同意服务条款")

class UserProfile(BaseModel):
    """用户资料模型"""
    username: str = Field(description="用户名")
    email: str = Field(description="邮箱地址")
    role: UserRole = Field(description="用户角色")
    created_at: datetime = Field(description="创建时间")
    last_login: Optional[datetime] = Field(None, description="最后登录时间")
    is_active: bool = Field(True, description="是否激活")

class UserInfo(BaseModel):
    """用户信息模型（包含token）"""
    username: str = Field(description="用户名")
    email: str = Field(description="邮箱地址")
    role: UserRole = Field(description="用户角色")
    created_at: datetime = Field(description="创建时间")
    last_login: Optional[datetime] = Field(None, description="最后登录时间")
    token: str = Field(description="访问令牌")
    token_type: str = Field("bearer", description="令牌类型")

class ChangePasswordRequest(BaseModel):
    """修改密码请求模型"""
    currentPassword: str = Field(description="当前密码")
    newPassword: str = Field(description="新密码", min_length=8)
    confirmPassword: str = Field(description="确认新密码")

class UpdateUserStatusRequest(BaseModel):
    """更新用户状态请求模型"""
    is_active: bool = Field(description="是否激活")

class TokenData(BaseModel):
    """Token数据模型"""
    username: Optional[str] = None
    role: Optional[str] = None

# ===== 可视化相关模型 =====
class VisualizationType(str, Enum):
    """可视化类型枚举"""
    SINGLE_3DPP = "3dpp"
    MULTI_3DPP = "multi_3dpp"
    HEATMAP = "heatmap"
    EFFICIENCY = "efficiency"
    ROUTE = "route"
    ANALYSIS_3D = "3d_analysis"

class VisualizationFile(BaseModel):
    """可视化文件信息"""
    filename: str = Field(description="文件名")
    filepath: str = Field(description="文件路径")
    type: str = Field(description="可视化类型")
    size: int = Field(description="文件大小（字节）")
    created_at: datetime = Field(description="创建时间")
    modified_at: datetime = Field(description="修改时间")

class VisualizationRequest(BaseModel):
    """可视化生成请求"""
    type: VisualizationType = Field(description="可视化类型")
    vehicle_ids: Optional[List[str]] = Field(None, description="指定车辆ID列表")
    parameters: Optional[Dict[str, Any]] = Field(None, description="可视化参数")

# ===== 数据相关模型 =====
class TruckType(str, Enum):
    """卡车类型枚举"""
    LARGE_TRUCK = "LARGE_TRUCK"
    LTL_TRUCK = "LTL_TRUCK"

class TruckData(BaseModel):
    """卡车数据模型"""
    vehicle_id: str = Field(description="车辆ID")
    type: TruckType = Field(description="卡车类型")
    total_items: int = Field(description="装载货物总数")
    total_weight_kg: float = Field(description="总重量(kg)")
    total_volume_m3: float = Field(description="总体积(m³)")
    loading_efficiency: float = Field(description="装载效率(%)")
    volume_utilization: float = Field(description="体积利用率(%)")
    cargo_types: List[str] = Field(description="货物类型列表")

class RouteData(BaseModel):
    """路径数据模型"""
    vehicle_id: str = Field(description="车辆ID")
    total_distance_km: float = Field(description="总距离(km)")
    total_stops: int = Field(description="总停靠点数")
    estimated_duration_hours: float = Field(description="预估时长(小时)")
    optimization_algorithm: str = Field(description="使用的优化算法")

class Location(BaseModel):
    """位置坐标模型"""
    latitude: float = Field(description="纬度")
    longitude: float = Field(description="经度")
    address: Optional[str] = Field(None, description="地址描述")

# ===== 优化相关模型 =====
class OptimizationAlgorithm(str, Enum):
    """优化算法枚举"""
    GUROBI_3DPP = "gurobi_3dpp"
    LTL_OPTIMIZER = "ltl_optimizer"
    VRP_BASIC = "vrp_basic"
    INTEGRATED = "integrated"

class OptimizationRequest(BaseModel):
    """优化请求模型"""
    algorithm: OptimizationAlgorithm = Field(description="使用的优化算法")
    data_source: str = Field(description="数据源文件名")
    parameters: Optional[Dict[str, Any]] = Field(None, description="优化参数")
    generate_visualizations: bool = Field(True, description="是否生成可视化")
    use_enhanced: bool = Field(True, description="⚡ 是否使用增强版优化器（main_enhanced）")

class OptimizationStatus(str, Enum):
    """优化任务状态枚举"""
    STARTED = "started"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class OptimizationResult(BaseModel):
    """优化结果模型"""
    task_id: str = Field(description="任务ID")
    algorithm_used: str = Field(description="使用的算法")
    total_trucks: int = Field(description="处理的卡车总数")
    total_items_processed: int = Field(description="处理的货物总数")
    average_loading_efficiency: float = Field(description="平均装载效率")
    total_distance_km: float = Field(description="总距离")
    optimization_time_seconds: float = Field(description="优化耗时(秒)")
    visualization_files: List[str] = Field(description="生成的可视化文件")
    data_files: List[str] = Field(description="生成的数据文件")

# ===== 统计相关模型 =====
class DataSummary(BaseModel):
    """数据摘要模型"""
    total_trucks: int = Field(description="卡车总数")
    total_routes: int = Field(description="路径总数")
    total_items: int = Field(description="货物总数")
    total_distance_km: float = Field(description="总距离")
    average_loading_efficiency: float = Field(description="平均装载效率")
    truck_types: Dict[str, int] = Field(description="各类型卡车数量")

class VisualizationStats(BaseModel):
    """可视化统计模型"""
    total_files: int = Field(description="文件总数")
    total_size_mb: float = Field(description="总文件大小(MB)")
    types: Dict[str, int] = Field(description="各类型文件数量")
    directory: str = Field(description="存储目录")

# ===== 系统状态模型 =====
class SystemHealth(BaseModel):
    """系统健康状态模型"""
    status: str = Field(description="系统状态")
    version: str = Field(description="系统版本")
    uptime_seconds: int = Field(description="运行时间(秒)")
    memory_usage_mb: float = Field(description="内存使用(MB)")
    disk_usage_percent: float = Field(description="磁盘使用率(%)")
    active_tasks: int = Field(description="活跃任务数")

# ===== 配置模型 =====
class OptimizationConfig(BaseModel):
    """优化配置模型"""
    max_vehicles: int = Field(50, description="最大车辆数")
    max_items_per_vehicle: int = Field(1000, description="每车最大货物数")
    visualization_sampling_threshold: int = Field(500, description="可视化采样阈值")
    timeout_seconds: int = Field(3600, description="优化超时时间(秒)")

class APIConfig(BaseModel):
    """API配置模型"""
    max_request_size_mb: int = Field(100, description="最大请求大小(MB)")
    rate_limit_per_minute: int = Field(60, description="每分钟请求限制")
    enable_cors: bool = Field(True, description="是否启用CORS")
    log_level: str = Field("INFO", description="日志级别")