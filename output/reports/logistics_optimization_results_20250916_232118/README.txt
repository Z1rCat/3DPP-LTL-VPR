
零担物流3D装箱优化系统 - 结果归档
========================================

生成时间: 2025-09-16 23:21:18
系统版本: 1.0.0

目录结构说明:
├── reports/          # Excel报告文件
│   └── Final_Loading_Plan.xlsx    # 完整装载方案报告
├── visualizations/   # 3D可视化HTML文件
│   ├── TRUCK_XXX_visualization.html  # 各货车装载可视化
│   ├── fleet_summary.html           # 车队摘要仪表板
│   └── cargo_type_analysis.html     # 货物类型分析
└── intermediate/     # 中间处理文件
    ├── processed_items.pkl          # 预处理货物数据
    ├── gurobi_solution.pkl          # Gurobi求解结果
    └── preprocessing_statistics.txt  # 数据预处理统计

使用说明:
1. 查看 Final_Loading_Plan.xlsx 了解详细的装载方案
2. 在浏览器中打开 visualizations/ 目录下的HTML文件查看3D可视化
3. intermediate/ 目录包含系统运行的中间数据，可用于进一步分析

技术参数:
- 标准货车规格: 7.5m × 2.3m × 2.5m
- 货车容量: 43.125m³
- 优化引擎: Gurobi MILP求解器
- 可视化引擎: Plotly 3D

注意事项:
- HTML可视化文件需要在现代浏览器中打开
- 建议使用Chrome、Firefox或Edge浏览器获得最佳体验
- 大型装载方案的3D可视化可能需要较长加载时间

技术支持:
本系统基于Gurobi数学优化和Plotly可视化技术构建
如有技术问题，请检查系统日志或联系技术支持
