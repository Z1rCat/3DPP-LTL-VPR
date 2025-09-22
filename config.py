"""
全局配置参数 - 零担物流3D装箱优化系统
Configuration Parameters for LTL 3D Bin Packing Optimization System
"""

import os
from pathlib import Path

# ===== 项目路径配置 =====
PROJECT_ROOT = Path(__file__).parent
DATA_FILE = PROJECT_ROOT / "表2-1 A网点某年某月某日需完成的取送货订单需求.xlsx"

# 输出目录
OUTPUT_DIR = PROJECT_ROOT / "output"
INTERMEDIATE_DIR = OUTPUT_DIR / "intermediate"
REPORTS_DIR = OUTPUT_DIR / "reports"
VISUALIZATIONS_DIR = OUTPUT_DIR / "visualizations"
LOGS_DIR = OUTPUT_DIR / "logs"

# ===== 车辆规格配置 =====
# 标准货车尺寸 (单位: 米)
TRUCK_SPECS = {
    'length': 9.6,     # 长度 9.6m
    'width': 2.4,      # 宽度 2.4m
    'height': 2.4,     # 高度 2.4m
    'volume': 55.296,  # 总体积 55m³
    'max_weight': 18000 # 最大载重 18000kg (如果需要)
}

# 车队配置
FLEET_CONFIG = {
    'total_trucks': 20,        # 可用货车总数
    'truck_cost': 1000,        # 每辆车使用成本 (如果考虑成本优化)
    'utilization_threshold': 0.9  # 装载率阈值
}

# ===== 货物分类配置 =====
CARGO_CLASSIFICATION = {
    'large_cargo_threshold': 50.0,   # 大货物阈值 (m³) - 订单总体积 > 50m³
    'medium_cargo_threshold': 10.0,  # 中货物下限 (m³) - 10m³ ≤ 订单总体积 ≤ 50m³
    'small_cargo_max': 10.0,         # 小货物上限 (m³) - 订单总体积 < 10m³
    'min_package_volume': 0.001,     # 最小包裹体积 (m³)
    'max_package_volume': 300.0      # 最大包裹体积 (m³)
}

# ===== 零担优化配置 =====
LTL_OPTIMIZATION = {
    'max_trucks_available': 20,          # 总车队数量
    'enable_small_cargo_merging': True,  # 启用小货物合并
    'merge_by_cargo_type': True,         # 按货物类型分组合并
    'objective': 'maximize_loading_rate' # 目标函数：最大化装载率
}

# ===== 单位转换配置 =====
UNIT_CONVERSION = {
    'dm3_to_m3': 0.001,        # 立方分米转立方米
    'cm3_to_m3': 0.000001,     # 立方厘米转立方米
    'kg_to_ton': 0.001         # 公斤转吨
}

# ===== 尺寸估算参数 =====
DIMENSION_ESTIMATION = {
    'length_width_ratio_range': (0.5, 3.0),    # 长宽比范围
    'height_ratio_range': (0.3, 2.0),          # 高度比例范围
    'shape_variation_factor': 0.1,             # 形状变化系数
    'cube_probability': 0.3,                   # 立方体概率
    'random_seed': 42                          # 随机种子（确保可重现）
}

# ===== Gurobi求解器配置 =====
GUROBI_CONFIG = {
    # 单货物3DPP优化配置 - 🔧 调整为30分钟确保生成有意义XYZ坐标
    'single_item_3dpp': {
        'time_limit': 1800,        # 求解时间限制 (秒) - 30分钟充分求解
        'mip_gap': 0.01,          # MIP gap (1%)
        'objective': 'maximize_loading_rate'
    },
    # 多车队LTL 3DPP优化配置 - 🔧 调整为30分钟确保生成有意义XYZ坐标
    'multi_truck_ltl': {
        'time_limit': 1800,       # 求解时间限制 (秒) - 30分钟充分求解
        'mip_gap': 0.02,          # MIP gap (2%)
        'objective': 'maximize_loading_rate'
    },
    # 通用配置
    'threads': 0,              # 使用所有可用线程 (0表示自动)
    'presolve': 1,             # 启用预处理
    'cuts': 1,                 # 启用切平面
    'heuristics': 0.05,        # 启发式算法时间占比
    'log_to_console': 1,       # 输出到控制台
    'log_file': None           # 日志文件 (暂时禁用)
}

# ===== 模型参数配置 =====
MODEL_PARAMS = {
    'big_m': 1000,             # 大M方法的M值
    'support_constraint': True, # 是否启用支撑约束
    'orientation_options': 6,   # 旋转选项数 (6种标准方向)
    'position_precision': 0.001 # 坐标精度 (mm)
}

# ===== 可视化配置 =====
VISUALIZATION_CONFIG = {
    'colors_palette': [
        '#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7',
        '#DDA0DD', '#98D8C8', '#F7DC6F', '#BB8FCE', '#85C1E9'
    ],
    'truck_color': '#E8E8E8',          # 货车颜色
    'truck_opacity': 0.1,              # 货车透明度
    'package_opacity': 0.8,            # 包裹透明度
    'max_packages_full_render': 2000,   # 完整渲染的最大包裹数
    'hover_template': '<b>货物ID:</b> %{customdata[0]}<br>' +
                     '<b>类型:</b> %{customdata[1]}<br>' +
                     '<b>尺寸:</b> %{customdata[2]}×%{customdata[3]}×%{customdata[4]}<br>' +
                     '<b>体积:</b> %{customdata[5]:.3f}m³<extra></extra>'
}

# 可视化性能控制配置
VISUALIZATION_PERFORMANCE = {
    'enable_heavy_visualizations': False,      # 是否启用重型可视化（密度分析等）
    'sample_ratio': 0.3,                      # 采样比例（30%）
    'max_items_per_visualization': 500,        # 每个可视化最大项目数
    'visualization_timeout': 30,               # 可视化超时时间（秒）
    'density_analysis_enabled': True,         # 密度分析开关 - 已启用
    'max_trucks_for_density': 20,             # 密度分析最大车辆数
    'max_vehicles_for_heatmap': 50,           # 热力图支持的最大车辆数
    'skip_heavy_charts_above_items': 5000,    # 超过此货物数量跳过重型图表
}

# 热力图专用配置
HEATMAP_CONFIG = {
    'enable_density_heatmap': True,            # 强制启用装载密度热力图
    'max_vehicles_for_heatmap': 50,            # 支持最大车辆数（可调整至50辆）
    'min_vehicles_for_heatmap': 1,             # 最小车辆数
    'heatmap_sample_vehicles': True,           # 当车辆过多时是否采样
    'heatmap_color_scheme': 'Viridis',         # 热力图颜色方案
    'show_vehicle_labels': True,               # 显示车辆标签
    'calculate_loading_efficiency': True,      # 计算装载效率（简单加法除法）
}

# 用户体验控制配置
USER_EXPERIENCE = {
    'verbose_logging': False,                  # 控制详细日志输出
    'show_progress_bars': True,                # 显示进度条
    'auto_open_results': False,                # 自动打开结果文件
    'max_console_output_lines': 50,            # 最大控制台输出行数
    'simplified_output': True,                 # 简化输出模式
}

# ===== 报告配置 =====
REPORT_CONFIG = {
    'excel_file_name': 'Final_Loading_Plan.xlsx',
    'summary_sheet': '装载方案摘要',
    'trucks_sheet': '车辆分配详情',
    'packages_sheet': '货物装载详情',
    'unloaded_sheet': '未装载货物',
    'date_format': '%Y-%m-%d %H:%M:%S'
}

# ===== 性能监控配置 =====
PERFORMANCE_CONFIG = {
    'progress_bar_format': '{desc}: {percentage:3.0f}%|{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}]',
    'memory_limit_gb': 8,              # 内存限制 (GB)
    'batch_size': 1000,                # 批处理大小
    'log_level': 'INFO'                # 日志级别
}

# ===== 文件格式配置 =====
FILE_CONFIG = {
    'processed_items_file': 'processed_items.pkl',
    'large_cargo_dispatch_file': 'large_cargo_dispatch_list.xlsx',
    'remaining_vehicles_file': 'remaining_vehicles.json',
    'ltl_candidate_items_file': 'ltl_candidate_items.pkl',
    'gurobi_solution_file': 'gurobi_solution.pkl',
    'cargo_classification_file': 'cargo_classification_results.xlsx',
    'small_cargo_merged_file': 'small_cargo_merged.xlsx',
    'ltl_optimization_input_file': 'ltl_optimization_input.xlsx',
    'single_item_3dpp_results_file': 'single_item_3dpp_results.xlsx',
    'full_dispatch_plan_file': 'full_dispatch_plan.json',
    'id_to_orders_mapping_file': 'id_to_orders_mapping.json',
    'encoding': 'utf-8'
}

# ===== 路径优化配置 =====
ROUTING_CONFIG = {
    'fuel_cost_per_ton_km': 0.16,     # 燃油成本系数（元/吨·公里）
    'empty_vehicle_weight': 8.5,      # 空车重量（吨）
    'depot_coordinates': [104.139111, 30.800835],  # A网点坐标（经度，纬度）
    'max_route_time_hours': 12,       # 最大路径时间（小时）
    'average_speed_kmh': 40,          # 平均行驶速度（公里/小时）
    'max_payload_capacity': 15.0,     # 最大载货量（吨）
    'service_time_delivery': 15,      # 配送服务时间（分钟）
    'service_time_pickup': 10,        # 取货服务时间（分钟）
    'start_time': '08:00',           # 作业开始时间
    'max_working_hours': 10          # 最大工作时间（小时）
}

# ===== OR-Tools求解器配置 =====
ORTOOLS_CONFIG = {
    'first_solution_strategy': 'PATH_CHEAPEST_ARC',
    'local_search_metaheuristic': 'GUIDED_LOCAL_SEARCH',
    'time_limit_seconds': 300,        # 5分钟求解时限
    'log_search': True,               # 显示求解日志
    'solution_limit': 100,            # 解的数量限制
    'use_depth_first_search': False,  # 是否使用深度优先搜索
    'use_cp': False                   # 是否使用约束编程
}

def create_directories():
    """创建所有必要的输出目录"""
    directories = [
        OUTPUT_DIR, INTERMEDIATE_DIR, REPORTS_DIR,
        VISUALIZATIONS_DIR, LOGS_DIR
    ]

    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)

    print("已创建输出目录结构")

def validate_config():
    """验证配置参数的有效性"""
    assert TRUCK_SPECS['volume'] == (TRUCK_SPECS['length'] *
                                   TRUCK_SPECS['width'] *
                                   TRUCK_SPECS['height']), "货车体积计算错误"

    assert CARGO_CLASSIFICATION['large_cargo_threshold'] > 0, "大宗货物阈值必须大于0"
    assert CARGO_CLASSIFICATION['medium_cargo_threshold'] > 0, "中货物阈值必须大于0"
    assert CARGO_CLASSIFICATION['small_cargo_max'] > 0, "小货物阈值必须大于0"

    assert GUROBI_CONFIG['single_item_3dpp']['time_limit'] > 0, "求解时间限制必须大于0"
    assert GUROBI_CONFIG['multi_truck_ltl']['time_limit'] > 0, "求解时间限制必须大于0"

    assert DATA_FILE.exists(), f"数据文件不存在: {DATA_FILE}"

    print("配置参数验证通过")

# ===== 路径生成配置 (增强版) =====
ROUTE_GENERATION = {
    'depot_coordinates': [30.800835, 104.139111],  # A网点坐标 [纬度, 经度]
    'avg_speed_kmh': 40,                           # 平均车速
    'service_time_pickup': 20,                     # 取货服务时间(分钟)
    'service_time_delivery': 30,                   # 送货服务时间(分钟)
    'fuel_cost_per_ton_km': 0.16,                 # 燃油成本系数
    'empty_truck_weight_kg': 8500,                # 空车重量
    'max_stops_per_truck': 20,                    # 单车最大停靠点数
    'route_optimization_method': 'nearest_neighbor', # 路径优化方法
    'max_working_hours': 10,                      # 最大工作时间(小时)
    'start_time': '08:00',                        # 开始工作时间
    'truck_capacity_kg': 15000,                   # 货车载重能力(kg)
    'vehicle_volume_m3': 55.296,                  # 货车容积(m3)
    'enable_return_to_depot': True                # 是否返回配送中心
}

# ===== API接口配置 =====
API_CONFIG = {
    'host': '0.0.0.0',
    'port': 5000,
    'debug': True,
    'max_concurrent_tasks': 3,
    'task_timeout_seconds': 3600,
    'result_cache_hours': 24,
    'enable_cors': True,
    'secret_key': 'logistics_optimization_system_secret_key_2024',
    'upload_timeout': 300,
    'max_request_size_mb': 100
}

# ===== 前端接口配置 =====
FRONTEND_CONFIG = {
    'static_folder': 'frontend/static',
    'template_folder': 'frontend/templates',
    'upload_folder': 'uploads',
    'cache_folder': 'cache',
    'allowed_extensions': {'xlsx', 'xls', 'csv'},
    'max_upload_size_mb': 50,
    'session_timeout_hours': 24,
    'auto_cleanup_days': 7,
    'enable_file_validation': True
}

# ===== 任务管理配置 =====
TASK_CONFIG = {
    'max_concurrent_optimization_tasks': 2,
    'task_progress_update_interval': 5,  # 秒
    'task_result_retention_hours': 48,
    'enable_task_queue': True,
    'queue_max_size': 10,
    'auto_retry_failed_tasks': True,
    'max_retry_attempts': 3
}

def create_all_directories():
    """创建所有必要的目录，包括API和前端相关目录"""
    directories = [
        OUTPUT_DIR, INTERMEDIATE_DIR, REPORTS_DIR,
        VISUALIZATIONS_DIR, LOGS_DIR,
        PROJECT_ROOT / FRONTEND_CONFIG['upload_folder'],
        PROJECT_ROOT / FRONTEND_CONFIG['cache_folder']
    ]

    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)

    print("已创建所有输出目录结构")

def validate_extended_config():
    """验证扩展配置参数的有效性"""
    # 验证原有配置
    validate_config()

    # 验证路径生成配置
    assert len(ROUTE_GENERATION['depot_coordinates']) == 2, "配送中心坐标格式错误"
    assert ROUTE_GENERATION['avg_speed_kmh'] > 0, "平均车速必须大于0"
    assert ROUTE_GENERATION['service_time_pickup'] > 0, "取货服务时间必须大于0"
    assert ROUTE_GENERATION['service_time_delivery'] > 0, "送货服务时间必须大于0"

    # 验证API配置
    assert 1000 <= API_CONFIG['port'] <= 65535, "API端口号范围错误"
    assert API_CONFIG['max_concurrent_tasks'] > 0, "最大并发任务数必须大于0"
    assert API_CONFIG['task_timeout_seconds'] > 0, "任务超时时间必须大于0"

    # 验证前端配置
    assert API_CONFIG['max_request_size_mb'] > 0, "最大请求大小必须大于0"
    assert len(FRONTEND_CONFIG['allowed_extensions']) > 0, "必须允许至少一种文件格式"

    print("扩展配置参数验证通过")

if __name__ == "__main__":
    # 创建目录并验证配置
    create_all_directories()
    validate_extended_config()
    print("系统完整配置初始化完成")