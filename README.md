# 🚛 智能物流3D装箱优化系统 V4.0

[![版本](https://img.shields.io/badge/版本-V4.0-blue.svg)](https://github.com/logistics-optimization)
[![Python](https://img.shields.io/badge/python-3.8+-green.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.85+-00a393.svg)](https://fastapi.tiangolo.com/)
[![许可证](https://img.shields.io/badge/许可证-MIT-red.svg)](LICENSE)

## 🎯 系统概述

智能物流3D装箱优化系统V4.0是一个现代化的物流优化解决方案，集成了3D装箱算法、车辆路径规划、智能可视化和Web API接口。本系统采用模块化架构，支持高性能优化计算和实时可视化展示。

### ✨ V4.0 核心特性

- 🚀 **高性能优化**: 集成Gurobi求解器，支持大规模3D装箱和路径优化
- 🎨 **智能可视化**: 5种类型的交互式HTML可视化，包括2D热力图和3D效率分析
- 🌐 **RESTful API**: 基于FastAPI的现代Web API，完整的Swagger文档
- 🖥️ **Web界面**: 响应式前端界面，支持任务管理和实时监控
- 📊 **数据分析**: 装载效率分析、路径优化报告和性能统计
- 🧪 **实验管理**: 支持算法对比、性能追踪和实验结果分析
- 📈 **趋势分析**: 基于历史数据的性能趋势分析和预测
- 💾 **数据存储**: SQLite数据库支持，完整的数据管理系统
- 🔧 **模块化设计**: 清晰的代码结构，易于维护和扩展

## 📁 项目结构

```
logistics_system/
├── 📄 main.py                    # 主程序入口
├── 📄 config.py                  # 系统配置文件
├── 📄 requirements.txt           # 依赖包清单
├── 📄 README.md                  # 项目文档
├── 📄 .gitignore                 # Git忽略文件
│
├── 📁 api/                       # Web API模块
│   ├── 📄 app.py                 # FastAPI应用入口
│   ├── 📁 routes/                # API路由
│   │   ├── visualization.py      # 可视化API
│   │   ├── data.py               # 数据API
│   │   ├── optimization.py       # 优化API
│   │   ├── analytics.py          # 分析报告API
│   │   └── experiments.py        # 实验管理API
│   ├── 📁 models/                # 数据模型
│   │   └── schemas.py            # Pydantic模型
│   └── 📁 utils/                 # API工具
│       └── response.py           # 响应格式化
│
├── 📁 frontend/                  # Web前端
│   ├── 📁 templates/             # HTML模板
│   │   ├── login.html            # 登录页面
│   │   ├── admin.html            # 管理员控制台
│   │   ├── index.html            # 主页面（重定向）
│   │   └── analytics.html        # 分析仪表板页面
│   └── 📁 static/                # 静态资源
│       ├── 📁 css/               # 样式文件
│       │   ├── login.css         # 登录页面样式
│       │   ├── admin.css         # 管理员控制台样式
│       │   ├── style.css         # 主样式
│       │   └── analytics.css     # 分析页面样式
│       ├── 📁 js/                # JavaScript文件
│       │   ├── login.js          # 登录页面脚本
│       │   ├── admin.js          # 管理员控制台脚本
│       │   ├── analytics.js      # 分析页面脚本
│       │   ├── main.js           # 主要脚本
│       │   ├── api.js            # API接口脚本
│       │   └── visualization.js  # 可视化脚本
│       └── 📁 images/            # 图片资源
│           └── default-avatar.svg
│
├── 📁 data_processing/           # 数据处理模块
│   ├── data_loader.py            # 数据加载器
│   ├── dimension_estimator.py    # 尺寸估算器
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
├── 📁 analytics/                 # 数据分析模块
│   ├── trend_analyzer.py        # 趋势分析器
│   ├── performance_analyzer.py  # 性能分析器
│   └── report_generator.py      # 报告生成器
│
├── 📁 experiment_manager/        # 实验管理模块
│   ├── experiment_tracker.py    # 实验跟踪器
│   └── comparison_engine.py     # 对比引擎
│
├── 📁 database/                  # 数据库管理模块
│   ├── db_manager.py            # 数据库管理器
│   └── models.py                # 数据模型
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
- FastAPI 0.85+
- 8GB+ 内存推荐

### 安装步骤

1. **克隆项目**
   ```bash
   git clone https://github.com/logistics-optimization/system.git
   cd logistics-system
   ```

2. **安装依赖**
   ```bash
   # 推荐使用虚拟环境
   python -m venv venv

   # Windows
   venv\Scripts\activate
   pip install -r requirements.txt

   # Linux/Mac
   source venv/bin/activate
   pip install -r requirements.txt
   ```

3. **配置Gurobi许可证**
   ```bash
   # Windows
   set GUROBI_LICENSE_PATH=C:\path\to\your\gurobi.lic

   # 或者设置环境变量（推荐）
   # 在系统环境变量中添加：
   # 变量名：GUROBI_LICENSE_PATH
   # 变量值：C:\path\to\your\gurobi.lic

   # Linux/Mac
   export GUROBI_LICENSE_PATH=/path/to/your/gurobi.lic
   ```

4. **Windows特定配置**
   ```bash
   # 检查Python版本（需要3.8+）
   python --version

   # 检查Gurobi许可证
   gurobi_cl --license

   # 检查依赖
   pip list
   ```

### 🎯 使用方式

#### 方式一：命令行运行（传统方式）
```bash
python main.py
```

#### 方式二：Web API服务（推荐）
```bash
# 启动API服务器
python -m uvicorn api.app:app --host 0.0.0.0 --port 8000 --reload

# 或者直接运行
python api/app.py
```

访问 Web 界面：
- 🌐 **登录页面**: http://localhost:8000/login
- 👤 **管理员控制台**: http://localhost:8000/admin
- 📊 **系统概览**: http://localhost:8000/api
- 📋 **API文档**: http://localhost:8000/docs
- 📖 **ReDoc**: http://localhost:8000/redoc
- 🔍 **健康检查**: http://localhost:8000/health

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

### FastAPI Web API

启动API服务：
```bash
python -m uvicorn api.app:app --host 0.0.0.0 --port 8000
```

### 核心端点

#### 🎨 可视化 API
- `GET /api/visualizations/list` - 获取可视化文件列表
- `GET /api/visualizations/file/{filename}` - 获取特定可视化文件
- `GET /api/visualizations/types` - 获取可视化类型列表
- `GET /api/visualizations/stats` - 获取可视化统计信息

#### 📊 数据 API
- `GET /api/data/trucks` - 获取卡车数据列表
- `GET /api/data/routes` - 获取路径数据列表
- `GET /api/data/trucks/{vehicle_id}` - 获取特定卡车详细信息
- `GET /api/data/summary` - 获取数据摘要统计

#### ⚡ 优化 API
- `POST /api/optimization/run` - 启动优化任务
- `GET /api/optimization/status/{task_id}` - 查询任务状态
- `GET /api/optimization/result/{task_id}` - 获取优化结果
- `GET /api/optimization/history` - 获取任务历史

#### 🧪 实验管理 API
- `POST /api/experiments/create` - 创建新实验
- `GET /api/experiments/list` - 获取实验列表
- `GET /api/experiments/{experiment_id}` - 获取实验详情
- `PUT /api/experiments/{experiment_id}` - 更新实验状态
- `DELETE /api/experiments/{experiment_id}` - 删除实验
- `GET /api/experiments/compare` - 算法对比分析

#### 📈 分析报告 API
- `GET /api/analytics/trend` - 获取趋势分析报告
- `GET /api/analytics/performance` - 获取性能分析报告
- `GET /api/analytics/comparison` - 获取算法对比报告
- `GET /api/analytics/export/{format}` - 导出分析报告
- `GET /api/analytics/dashboard` - 获取仪表板数据

### API 特性
- 🔄 **异步处理**: 基于FastAPI的高性能异步API
- 📋 **自动文档**: Swagger UI和ReDoc自动生成
- 🛡️ **数据验证**: Pydantic模型确保数据完整性
- 🌐 **CORS支持**: 支持跨域请求

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

   # Windows环境变量检查
   echo %GUROBI_LICENSE_PATH%
   ```

4. **Windows特定问题**

   **a) 端口占用错误**
   ```bash
   # 查看端口占用
   netstat -ano | findstr :8000

   # 终止占用进程
   taskkill /PID <进程ID> /F
   ```

   **b) Python模块导入错误**
   ```bash
   # 重新安装依赖
   pip install -r requirements.txt --force-reinstall

   # 检查模块路径
   python -c "import sys; print(sys.path)"
   ```

   **c) 中文编码问题**
   ```python
   # 在代码开头添加
   # -*- coding: utf-8 -*-
   import sys
   sys.path.append('utf-8')
   ```

5. **前端无法加载静态资源**
   ```bash
   # 检查静态文件路径
   # 确保 frontend/static/ 目录存在且包含必要文件

   # 清除浏览器缓存
   Ctrl + Shift + Delete (Chrome)
   ```

### 开发调试模式

启用详细日志：
```python
# 在config.py中设置
USER_EXPERIENCE['verbose_logging'] = True
USER_EXPERIENCE['show_progress_bars'] = True
```

启动开发服务器：
```bash
# 开发模式（自动重载）
python -m uvicorn api.app:app --host 0.0.0.0 --port 8000 --reload --log-level debug
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

### 前端开发指南

1. **技术栈**
   - HTML5 + CSS3 + Vanilla JavaScript
   - Font Awesome 6.4.0 (图标)
   - Chart.js 3.9.1 (图表)
   - 响应式设计

2. **文件结构**
   ```
   frontend/
   ├── templates/          # HTML模板
   │   ├── login.html     # 登录页面
   │   ├── admin.html     # 管理员控制台
   │   └── analytics.html # 分析页面
   └── static/
       ├── css/           # 样式文件
       ├── js/            # JavaScript文件
       └── images/        # 图片资源
   ```

3. **开发规范**
   - 使用语义化HTML5标签
   - CSS采用BEM命名规范
   - JavaScript使用ES6+语法
   - 移动端优先的响应式设计

4. **调试技巧**
   ```bash
   # Chrome开发者工具
   F12 → Console/Network/Elements

   # 清除缓存
   Ctrl + Shift + R (强制刷新)

   # 移动端调试
   F12 → 设备模拟器
   ```

### 代码规范

- 遵循PEP 8
- 函数注释完整
- 模块化设计
- 前端代码遵循W3C标准
- 使用ESLint进行代码检查

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

## 🔗 相关链接

- [项目主页](https://github.com/Z1rCat/3DPP-LTL-VPR)
- [问题反馈](https://github.com/Z1rCat/3DPP-LTL-VPR/issues)
- [Gurobi官网](https://www.gurobi.com/)

---

**智能物流3D装箱优化系统V4.0 - 让物流更智能，让效率更高效！** 🚀