# 巧满装载平台 - 企业级智能物流优化系统

## 项目概述

基于 **空间-时间约束系统集成** 的企业级智能物流优化系统管理员界面，重点展示3D装箱优化(3DPP)与车辆路径规划(VRPPD)的混合优化结果。

## 技术栈

### 前端技术
- **React 18** + **TypeScript** - 现代化前端框架
- **Vite** - 快速构建工具
- **Ant Design Pro** - 企业级UI组件库
- **Tailwind CSS** - 原子化CSS框架
- **React Query** - 数据状态管理
- **Zustand** - 轻量级状态管理
- **Framer Motion** - 动画库
- **React Beautiful DND** - 拖拽组件

### 可视化技术
- **ECharts** - 图表可视化
- **Three.js** - 3D可视化支持
- **iframe嵌入** - 本地HTML可视化文件集成

## 项目结构

```
frontend/
├── src/
│   ├── components/          # 通用组件
│   │   ├── Layout/         # 布局组件
│   │   ├── DataImport/     # 数据导入组件
│   │   ├── OptimizationPanel/ # 优化控制面板
│   │   ├── VehicleList/    # 车辆列表组件(待开发)
│   │   └── Visualization/  # 可视化组件(待开发)
│   ├── pages/              # 页面组件
│   │   ├── Dashboard/      # 主仪表板
│   │   ├── DataImport/     # 数据导入页面
│   │   ├── OptimizationPanel/ # 优化执行页面
│   │   ├── VehicleManagement/ # 车辆管理页面(待开发)
│   │   └── Visualization/  # 可视化页面(待开发)
│   ├── services/           # API服务
│   │   └── api.ts         # HTTP客户端配置
│   ├── types/              # TypeScript类型定义
│   │   └── index.ts       # 全局类型定义
│   ├── styles/             # 样式文件
│   │   └── index.css      # 全局样式
│   ├── App.tsx            # 主应用组件
│   └── main.tsx           # 应用入口
├── public/                # 静态资源
├── package.json          # 项目依赖
├── tsconfig.json         # TypeScript配置
├── tailwind.config.js    # Tailwind配置
├── vite.config.ts        # Vite构建配置
└── README.md            # 项目说明
```

## 功能模块

### ✅ 已完成功能

1. **基础架构**
   - React + TypeScript项目初始化
   - Vite构建工具配置
   - Ant Design Pro + Tailwind CSS样式系统
   - 路由配置和状态管理

2. **核心组件**
   - **数据导入组件**: 支持拖拽上传，文件验证，进度显示
   - **优化执行面板**: 分段进度条，实时状态显示，控制按钮
   - **响应式布局**: 企业级界面设计，侧边栏导航

3. **页面路由**
   - 仪表板页面 - 系统概览和快捷操作
   - 数据导入页面 - 文件上传和验证
   - 优化执行页面 - 智能优化控制台

### 🚧 开发中功能

4. **车辆选择列表面板**
   - 车辆状态卡片组件
   - 效率评分显示
   - 切换动效

5. **双视图展示系统**
   - 3D装箱可视化iframe集成
   - 路径优化地图iframe集成
   - 交互控制组件

6. **企业级视觉设计**
   - 设计系统实现
   - 动画效果
   - 响应式适配

## 安装和运行

### 环境要求
- Node.js >= 16.0.0
- npm >= 8.0.0
- 后端API服务运行在 http://localhost:8001

### 安装依赖
```bash
cd frontend
npm install
```

### 开发模式
```bash
npm run dev
```
应用将运行在 http://localhost:3000

### 生产构建
```bash
npm run build
```

### 预览构建结果
```bash
npm run preview
```

## 配置说明

### 环境变量
创建 `.env` 文件配置环境变量：

```bash
# API基础URL
VITE_API_BASE_URL=http://localhost:8001

# 其他配置
VITE_APP_TITLE=巧满装载平台
VITE_APP_VERSION=1.0.0
```

### 代理配置
开发环境下已配置API代理：
- `/api/*` -> `http://localhost:8001/api/*`
- `/visualizations/*` -> `http://localhost:8001/visualizations/*`

## API集成

### 支持的API端点
- `GET /api/vehicles` - 获取车辆列表
- `POST /api/optimization/start` - 启动优化任务
- `GET /api/optimization/status/{taskId}` - 获取任务状态
- `GET /visualizations/*` - 访问可视化文件

### 数据类型
项目包含完整的TypeScript类型定义，支持：
- 车辆管理 (Vehicle, Route)
- 订单管理 (Order, OrderItem)
- 优化任务 (OptimizationTask, OptimizationResult)
- 系统统计 (SystemStats, Alert)

## 可视化集成

### 3D装箱可视化
- 支持iframe嵌入本地HTML文件
- 文件路径: `/output/visualizations/single_category_3dpp_*.html`
- 备用方案: 高质量截图展示

### 路径地图可视化
- 支持iframe嵌入地图文件
- 文件路径: `/chengdu_route_map_fixed.html`
- 交互控制: 缩放、图层切换

## 开发指南

### 代码规范
- 使用ESLint进行代码检查
- 遵循TypeScript严格模式
- 组件使用函数式组件 + Hooks

### 样式规范
- 主色调: 科技蓝 (#1890ff) + 专业深灰 (#001529)
- 辅助色: 成功绿 (#52c41a)、警告橙 (#faad14)
- 响应式设计: 移动端适配

### 组件开发
- 使用Ant Design组件库
- 自定义样式使用Tailwind CSS
- 动画效果使用Framer Motion

## 部署说明

### 构建配置
- 代码分割: vendor、antd、charts、utils
- 资源优化: 图片压缩、CSS压缩
- 缓存策略: 静态资源长期缓存

### 生产部署
1. 构建项目: `npm run build`
2. 部署dist目录到静态文件服务器
3. 配置nginx或CDN
4. 确保后端API服务可访问

## 后续开发计划

### 第一阶段 (已完成)
- [x] 基础项目架构
- [x] 数据导入组件
- [x] 优化执行面板
- [x] 基础页面路由

### 第二阶段 (开发中)
- [ ] 车辆选择列表面板
- [ ] 3D装箱可视化集成
- [ ] 路径地图可视化集成
- [ ] 企业级视觉设计

### 第三阶段 (计划中)
- [ ] 进度条动画系统
- [ ] 模拟数据集创建
- [ ] API接口完整集成
- [ ] 性能优化

## 技术支持

如有问题请联系开发团队或查看：
- [Ant Design Pro文档](https://pro.ant.design/)
- [Tailwind CSS文档](https://tailwindcss.com/)
- [React Query文档](https://tanstack.com/query/latest)
- [Framer Motion文档](https://www.framer.com/motion/)

---

**开发团队**: 巧满装载平台开发组
**版本**: v1.0.0
**更新时间**: 2025-01-18