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
    'encoding': 'utf-8'
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

if __name__ == "__main__":
    # 创建目录并验证配置
    create_directories()
    validate_config()
    print("系统配置初始化完成")