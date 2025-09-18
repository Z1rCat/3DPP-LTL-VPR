# 零担物流3D装箱优化系统 V2.0

## 项目简介

零担物流3D装箱优化系统是一个基于Gurobi的智能物流优化解决方案，专门用于解决零担物流中的3D装箱问题。系统采用先进的混合整数线性规划(MILP)算法，通过三分类货物处理和双重优化策略，实现最优的车辆装载方案。

## 核心特性

- **智能三分类货物**：自动将货物分为大货物(>50m³)、中货物(10-50m³)、小货物(<10m³)
- **双重优化策略**：单货物3DPP优化 + 多车队LTL 3DPP优化
- **Gurobi MILP求解器**：使用业界最先进的优化算法，确保生成有意义的3D坐标
- **可视化支持**：3D装载方案可视化展示
- **完整数据处理流水线**：从订单数据加载到最终报告生成

## 系统架构

```
物流优化系统/
├── main.py                    # 主程序入口
├── config.py                  # 全局配置参数
├── preprocessing_pipeline.py  # 数据预处理流水线
├── data_processing/          # 数据处理模块
│   ├── data_loader.py        # 数据加载器
│   └── dimension_estimator.py # 尺寸估算器
├── optimization/             # 优化算法模块
│   ├── cargo_classifier.py   # 货物分类器
│   ├── large_cargo_dispatcher.py # 大货物调度器
│   ├── ltl_optimizer.py      # LTL优化器
│   └── gurobi_optimizer.py   # Gurobi优化器
├── visualization/            # 可视化模块
│   └── plotly_3d.py         # 3D可视化工具
├── utils/                   # 工具模块
│   └── file_manager.py      # 文件管理器
└── output/                  # 输出目录
    ├── intermediate/        # 中间文件
    ├── reports/            # 报告文件
    ├── visualizations/     # 可视化文件
    └── logs/              # 日志文件
```

## 优化流程

1. **数据预处理**：加载Excel订单数据，清洗和单位转换
2. **三分类货物**：按体积阈值分类为大、中、小货物
3. **大货物优化**：使用单货物3DPP算法进行优化分配
4. **小货物合并**：将小货物按类型合并为虚拟货物
5. **LTL优化**：对剩余货物执行多车队LTL 3DPP优化
6. **结果合并**：整合所有优化结果
7. **3D可视化**：生成装载方案的3D可视化
8. **报告生成**：输出最终优化报告

## 技术规格

### 车辆规格
- **长度**：9.6米
- **宽度**：2.4米
- **高度**：2.4米
- **容积**：55.296立方米
- **最大载重**：18,000公斤

### 优化参数
- **货物分类阈值**：
  - 大货物：>50m³
  - 中货物：10-50m³
  - 小货物：<10m³
- **求解时间限制**：30分钟（确保生成有意义坐标）
- **MIP Gap**：1-2%
- **车队规模**：20辆

## 安装要求

### 核心依赖
```bash
pip install pandas numpy gurobi plotly tqdm pathlib
```

### 软件要求
- **Python**：3.7+
- **Gurobi Optimizer**：9.0+（需要有效许可证）
- **Excel支持**：openpyxl或xlrd

### Gurobi许可证配置
1. 获取Gurobi学术/商业许可证
2. 安装gurobi包：`pip install gurobipy`
3. 激活许可证：`grbgetkey your-license-key`

## 使用方法

### 基本使用
```python
from main import LogisticsOptimizationSystemV2

# 创建优化系统实例
system = LogisticsOptimizationSystemV2(verbose=True)

# 运行完整优化
results = system.run_complete_optimization()
```

### 直接运行
```bash
python main.py
```

### 输入数据格式
系统读取Excel文件：`表2-1 A网点某年某月某日需完成的取送货订单需求.xlsx`

预期数据列：
- 订单ID
- 货物类型
- 数量
- 体积信息
- 其他物流相关字段

## 输出结果

### 报告文件
- **优化方案**：`Final_Loading_Plan.xlsx`
- **分类结果**：`cargo_classification_results.xlsx`
- **LTL输入数据**：`ltl_optimization_input.xlsx`

### 可视化文件
- **3D装载可视化**：`large_cargo_3dpp_visualization_*.txt`
- **交互式3D图**：`*.html`（如果Plotly可用）

### 性能指标
- 总装载率
- 车辆使用率
- 装载效率
- 优化算法性能

## 配置说明

主要配置在 `config.py` 中：

### 货物分类配置
```python
CARGO_CLASSIFICATION = {
    'large_cargo_threshold': 50.0,   # 大货物阈值
    'medium_cargo_threshold': 10.0,  # 中货物阈值
    'small_cargo_max': 10.0         # 小货物上限
}
```

### Gurobi求解器配置
```python
GUROBI_CONFIG = {
    'single_item_3dpp': {
        'time_limit': 1800,         # 30分钟求解时间
        'mip_gap': 0.01            # 1% MIP间隙
    }
}
```

## 算法详解

### 单货物3DPP优化
- **目标**：最大化大货物的装载率
- **约束**：体积限制、空间边界、位置分布
- **算法**：Gurobi MILP求解器

### 多车队LTL 3DPP优化
- **目标**：最大化多车队总装载率
- **处理对象**：中货物、剩余大货物、合并小货物
- **算法**：启发式 + Gurobi MILP优化

## 性能优化

- **并行处理**：支持多线程求解
- **内存管理**：批处理大数据集
- **求解参数调优**：预处理、切平面、启发式算法

## 故障排除

### 常见问题
1. **Gurobi许可证问题**：检查许可证激活和有效期
2. **内存不足**：减少batch_size或增加系统内存
3. **求解时间过长**：调整time_limit参数

### 日志查看
系统日志存储在 `output/logs/` 目录中，包含详细的运行信息和错误诊断。

## 贡献指南

1. Fork项目仓库
2. 创建特性分支：`git checkout -b feature/new-feature`
3. 提交更改：`git commit -am 'Add new feature'`
4. 推送到分支：`git push origin feature/new-feature`
5. 创建Pull Request

## 许可证

本项目采用MIT许可证 - 详见LICENSE文件

## 联系方式

如有问题或建议，请通过以下方式联系：
- 项目仓库：[GitHub链接]
- 邮箱：[联系邮箱]

---

**注意**：本系统需要有效的Gurobi许可证才能运行优化算法。学术用户可以申请免费的学术许可证。