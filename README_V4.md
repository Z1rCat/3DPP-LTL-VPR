# 🚛 智能物流3D装箱优化系统 V4.0

[![版本](https://img.shields.io/badge/版本-V4.0-blue.svg)](https://github.com/Z1rCat/3DPP-LTL-VPR)
[![Python](https://img.shields.io/badge/python-3.8+-green.svg)](https://www.python.org/)
[![许可证](https://img.shields.io/badge/许可证-MIT-red.svg)](LICENSE)

## 🎯 系统概述

智能物流3D装箱优化系统V4.0是一个高性能的零担物流优化解决方案，集成了3D装箱算法、路径规划和智能可视化功能。本版本经过全面重构，解决了性能问题，提供了更好的用户体验。

### ✨ V4.0 主要改进

- 🚀 **性能优化**: 解决了可视化卡死问题，实现30%采样显示
- 📁 **模块化重构**: 清晰的文件结构，便于维护和扩展
- 🎛️ **可配置性**: 丰富的配置选项，支持性能调优
- 🌐 **API就绪**: 完整的API接口文档，支持前端集成
- 💡 **用户友好**: 简化的输出界面，更好的错误处理

## 📁 项目结构

```
logistics_system/
├── 📄 main.py                    # 主程序入口
├── 📄 config.py                  # 系统配置文件
├── 📄 api_interface.py           # API接口文档
├── 📄 requirements.txt           # 依赖包清单
│
├── 📁 data_processing/           # 数据处理模块
│   ├── data_loader.py           # 数据加载器
│   ├── dimension_estimator.py   # 尺寸估算器
│   └── preprocessing_pipeline.py # 预处理管道
│
├── 📁 optimization/              # 优化算法模块
│   ├── cargo_classifier.py      # 货物分类器
│   ├── large_cargo_dispatcher.py # 大货物调度器
│   ├── ltl_optimizer.py          # LTL优化器
│   └── gurobi_optimizer*.py      # Gurobi求解器
│
├── 📁 visualization/             # 可视化模块
│   ├── plotly_3d.py             # 3D可视化器
│   ├── route_visualizer.py      # 路径可视化器
│   └── real_data_loader.py      # 实际数据加载器
│
├── 📁 utils/                     # 工具模块
│   ├── system_monitor.py        # 系统监控
│   ├── file_manager.py          # 文件管理
│   └── distance_calculator.py   # 距离计算
│
└── 📁 output/                    # 输出目录
    ├── reports/                 # 报告文件
    ├── visualizations/          # 可视化文件
    └── logs/                    # 日志文件
```

## 🚀 快速开始

### 环境要求

- Python 3.8+
- Gurobi 9.5+ (需要许可证)
- 8GB+ 内存推荐

### 安装步骤

1. **克隆项目**
   ```bash
   git clone https://github.com/Z1rCat/3DPP-LTL-VPR.git
   cd 3DPP-LTL-VPR
   ```

2. **安装依赖**
   ```bash
   pip install -r requirements.txt
   ```

3. **配置Gurobi许可证**
   ```bash
   # 设置Gurobi许可证文件路径
   export GUROBI_LICENSE_PATH=/path/to/your/gurobi.lic
   ```

4. **运行系统**
   ```bash
   python main.py
   ```

## ⚙️ 配置说明

### 性能配置 (config.py)

```python
# 可视化性能控制
VISUALIZATION_PERFORMANCE = {
    'enable_heavy_visualizations': False,    # 是否启用重型可视化
    'sample_ratio': 0.3,                    # 采样比例（30%）
    'max_items_per_visualization': 500,      # 每个可视化最大项目数
    'density_analysis_enabled': False,      # 密度分析开关
}

# 用户体验控制
USER_EXPERIENCE = {
    'verbose_logging': False,               # 详细日志输出
    'show_progress_bars': True,             # 显示进度条
    'simplified_output': True,              # 简化输出模式
}
```

### 关键配置项

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| `sample_ratio` | 0.3 | 可视化采样比例，防止卡死 |
| `max_items_per_visualization` | 500 | 单个图表最大显示项目数 |
| `density_analysis_enabled` | False | 是否启用密度分析（高内存消耗） |
| `verbose_logging` | False | 是否显示详细日志 |

## 📊 使用说明

### 基本使用

1. **准备数据文件**
   - Excel格式，包含取送货信息
   - 必需列：取送货类型、经度、纬度、货物类型、体积、重量、价值

2. **运行优化**
   ```bash
   python main.py
   ```

3. **查看结果**
   - 报告文件：`output/reports/`
   - 可视化：`output/visualizations/`
   - 日志文件：`output/logs/`

### 高级配置

#### 启用高性能模式
```python
# 在config.py中修改
VISUALIZATION_PERFORMANCE['enable_heavy_visualizations'] = True
VISUALIZATION_PERFORMANCE['density_analysis_enabled'] = True
```

#### 调整采样比例
```python
# 提高可视化质量（更多数据显示）
VISUALIZATION_PERFORMANCE['sample_ratio'] = 0.5  # 50%采样
VISUALIZATION_PERFORMANCE['max_items_per_visualization'] = 1000
```

## 🔌 API集成

### Flask Web API

启动API服务：
```bash
python api_interface.py
```

### 主要端点

- `GET /api/v1/status` - 系统状态
- `POST /api/v1/optimize` - 创建优化任务
- `GET /api/v1/tasks/{task_id}` - 查询任务状态
- `GET /api/v1/results/{task_id}` - 下载结果

详细API文档请参考 `api_interface.py`

## 📈 性能特性

### V4.0性能优化

| 功能 | V3.0 | V4.0 | 改进 |
|------|------|------|------|
| 可视化性能 | 经常卡死 | 稳定运行 | ✅ 采样显示 |
| 内存使用 | 不可控 | 可控制 | ✅ 智能限制 |
| 错误处理 | 基础 | 完善 | ✅ 优雅降级 |
| 用户体验 | 复杂 | 简化 | ✅ 清晰输出 |

### 性能指标

- **处理能力**: 44个订单 → 11,000+货物
- **优化时间**: ~30秒（中等规模数据）
- **内存使用**: <500MB（正常模式）
- **可视化**: 30%采样，无卡死

## 🛠️ 故障排除

### 常见问题

1. **系统卡死**
   ```python
   # 降低可视化复杂度
   VISUALIZATION_PERFORMANCE['sample_ratio'] = 0.1  # 10%采样
   VISUALIZATION_PERFORMANCE['enable_heavy_visualizations'] = False
   ```

2. **内存不足**
   ```python
   # 启用内存保护
   VISUALIZATION_PERFORMANCE['max_items_per_visualization'] = 200
   ```

3. **Gurobi许可证错误**
   ```bash
   # 检查许可证
   gurobi_cl --license
   ```

### 日志分析

系统日志位于 `output/logs/system.log`，包含：
- 性能监控信息
- 错误详情
- 优化进度

## 🤝 开发贡献

### 分支管理

- `master` - 稳定版本
- `refactor-v4` - V4.0开发分支
- `backup-v3-before-refactor` - V3.0备份

### 代码规范

- 遵循PEP 8
- 函数注释完整
- 模块化设计

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

## 🔗 相关链接

- [项目主页](https://github.com/Z1rCat/3DPP-LTL-VPR)
- [问题反馈](https://github.com/Z1rCat/3DPP-LTL-VPR/issues)
- [Gurobi官网](https://www.gurobi.com/)

---

**智能物流3D装箱优化系统V4.0 - 让物流更智能，让效率更高效！** 🚀