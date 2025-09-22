# 零担物流3D装箱优化系统 - 集成版本

## 🚀 系统概述

本系统是一个集成了VRP路径优化和前端API接口的零担物流3D装箱优化解决方案。支持多种运行模式，包括命令行模式、Web API服务器模式和交互式模式。

## ✨ 主要特性

### 🔧 VRP优化替换
- ✅ **解决VRP求解器失效问题**：用简化路径生成替换复杂VRP求解器
- ✅ **统一路径生成**：FULL_TRUCK和LTL_TRUCK使用一致的路径算法
- ✅ **自动Excel导出**：集成export_route_results，自动生成汇总报告
- ✅ **100%成功率**：所有车辆都能生成有效路径规划

### 🌐 前端API接口
- ✅ **RESTful API**：完整的Web API接口支持
- ✅ **异步任务管理**：支持长时间运行的优化任务
- ✅ **实时进度跟踪**：13步骤详细进度反馈
- ✅ **文件上传下载**：支持Excel文件上传和结果下载
- ✅ **CORS支持**：跨域访问支持

### 🎯 多运行模式
- ✅ **命令行模式**：传统的CLI执行方式
- ✅ **API服务器模式**：Web服务模式，支持前端调用
- ✅ **交互式模式**：带进度显示的交互式执行
- ✅ **测试模式**：系统功能测试
- ✅ **状态模式**：查看系统状态信息

## 📦 安装依赖

```bash
# 基础依赖（已有）
pip install pandas numpy matplotlib plotly

# 新增API依赖
pip install flask flask-cors

# 可选：更好的WSGI服务器
pip install gunicorn
```

## 🎯 使用方法

### 1. 命令行模式（默认）
```bash
python startup.py
# 或
python startup.py --mode cli --verbose
```

### 2. Web API服务器模式
```bash
# 使用默认配置
python startup.py --mode api

# 自定义配置
python startup.py --mode api --host 0.0.0.0 --port 8080 --debug
```

### 3. 交互式模式
```bash
python startup.py --mode interactive
```

### 4. 系统测试
```bash
python startup.py --mode test
```

### 5. 查看状态
```bash
python startup.py --mode status
```

## 🔌 API接口文档

### 基础接口

#### 健康检查
```http
GET /api/health
```

#### 提交优化任务
```http
POST /api/optimize
Content-Type: application/json

{
  "config": {
    "custom_settings": "value"
  }
}
```

#### 查询任务状态
```http
GET /api/status/{task_id}
```

#### 获取优化结果
```http
GET /api/result/{task_id}
```

#### 下载结果文件
```http
GET /api/download/{task_id}/excel
GET /api/download/{task_id}/routes
GET /api/download/{task_id}/visualizations
```

#### 列出所有任务
```http
GET /api/tasks
```

### API响应示例

#### 任务状态响应
```json
{
  "task_id": "123e4567-e89b-12d3-a456-426614174000",
  "status": "running",
  "progress": 65,
  "current_step": "LTL优化中...",
  "steps_completed": 8,
  "total_steps": 13,
  "estimated_remaining": "5分钟"
}
```

#### 优化结果响应
```json
{
  "task_id": "123e4567-e89b-12d3-a456-426614174000",
  "status": "completed",
  "summary": {
    "total_trucks_used": 12,
    "total_items_loaded": 1580,
    "loading_efficiency": 85.6,
    "large_cargo_trucks": 8,
    "ltl_trucks": 4,
    "optimization_time": "18分35秒"
  },
  "files": {
    "route_reports_count": 12,
    "visualization_files_count": 5,
    "excel_download": "/api/download/{task_id}/excel"
  }
}
```

## 📁 项目结构

```
物流/
├── startup.py                 # 统一启动脚本
├── main.py                   # 主优化系统（已增强VRP功能）
├── config.py                 # 配置文件（已扩展API配置）
├── api.py                    # Flask Web API接口
├── frontend_interface.py     # 前端集成接口层
├── generate_full_truck_routes.py  # FULL_TRUCK路径生成
├── export_route_results.py   # 路径结果导出
├── uploads/                  # 文件上传目录
├── cache/                    # 结果缓存目录
└── output/
    ├── reports/              # 报告输出
    ├── visualizations/       # 可视化文件
    └── logs/                # 日志文件
```

## 🔧 配置说明

### API配置（config.py）
```python
API_CONFIG = {
    'host': '0.0.0.0',              # 服务器地址
    'port': 5000,                   # 端口号
    'debug': True,                  # 调试模式
    'max_concurrent_tasks': 3,      # 最大并发任务数
    'task_timeout_seconds': 3600,   # 任务超时时间
    'result_cache_hours': 24,       # 结果缓存时间
    'enable_cors': True,            # 启用跨域支持
}
```

### 路径生成配置
```python
ROUTE_GENERATION = {
    'depot_coordinates': [30.800835, 104.139111],  # A网点坐标
    'avg_speed_kmh': 40,                           # 平均车速
    'service_time_pickup': 20,                     # 取货服务时间(分钟)
    'service_time_delivery': 30,                   # 送货服务时间(分钟)
    'fuel_cost_per_ton_km': 0.16,                 # 燃油成本系数
    'route_optimization_method': 'nearest_neighbor' # 路径优化方法
}
```

## 🎯 主要改进

### VRP优化替换
1. **问题解决**：原VRP求解器导致所有货物的truck_id、position等字段为NaN
2. **解决方案**：集成generate_full_truck_routes逻辑，使用简化的点对点和多点路径生成
3. **效果**：路径生成成功率从0%提升到100%

### 前端接口支持
1. **API设计**：完整的RESTful API接口
2. **任务管理**：异步任务队列和状态跟踪
3. **进度反馈**：实时进度更新和预估时间
4. **文件处理**：上传Excel文件和下载结果

### 系统集成
1. **统一启动**：单一启动脚本支持多种模式
2. **向后兼容**：保持原有命令行功能
3. **错误处理**：完善的异常处理和日志记录
4. **配置驱动**：灵活的配置管理

## 🔍 故障排除

### 常见问题

#### 1. API服务器无法启动
```bash
# 检查端口是否被占用
netstat -ano | findstr :5000

# 使用其他端口
python startup.py --mode api --port 8080
```

#### 2. VRP路径生成失败
- **原因**：数据文件格式问题或距离计算失败
- **解决**：检查数据文件完整性，确保坐标字段有效

#### 3. Excel报告不生成
- **原因**：缺少路径数据或文件权限问题
- **解决**：确保output/reports目录可写，检查路径生成是否成功

#### 4. 任务长时间运行
- **原因**：数据量大或系统资源不足
- **解决**：调整并发任务数量，增加系统资源

### 日志查看
```bash
# 查看系统日志
tail -f output/logs/system.log

# 查看详细输出
python startup.py --mode cli --verbose
```

## 🚀 部署建议

### 开发环境
```bash
python startup.py --mode api --debug
```

### 生产环境
```bash
# 使用Gunicorn部署
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 api:app
```

## 📞 技术支持

如有问题，请检查：
1. Python版本 >= 3.8
2. 所有依赖已正确安装
3. 数据文件存在且格式正确
4. 输出目录具有写入权限

---

**零担物流3D装箱优化系统 v2.0** - 集成VRP优化和前端API接口的完整解决方案