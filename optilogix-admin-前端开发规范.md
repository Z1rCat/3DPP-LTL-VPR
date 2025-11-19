# OptiLogix Admin 前端开发规范

## 项目概述

OptiLogix Admin 是一个基于 React + TypeScript + Tailwind CSS 的现代化智能物流优化系统管理平台，采用 Vite 构建工具，支持 3D 可视化和实时数据分析。

## 技术栈

- **前端框架**: React 19.2+ (TypeScript)
- **构建工具**: Vite
- **样式框架**: Tailwind CSS
- **3D 渲染**: @react-three/fiber + @react-three/drei
- **图表库**: Recharts
- **图标库**: Lucide React
- **字体**: Inter + Noto Sans SC

## 配色方案

### 主色调 (Primary Colors)

```css
tech-blue: '#1890ff'    /* 主品牌蓝 - 用于按钮、链接、重要操作 */
tech-dark: '#001529'    /* 深色调 - 用于特定暗色强调 */
tech-light: '#f0f2f5'   /* 浅灰背景 */
tech-card: '#ffffff'    /* 卡片背景 */
```

### 语义化颜色

```css
tech-success: '#52c41a'  /* 成功状态 - 完成状态、成功提示 */
tech-warning: '#faad14'  /* 警告状态 - 注意信息、待处理 */
tech-text: '#1f2937'     /* 主文本颜色 */
tech-subtext: '#6b7280'  /* 次要文本颜色 */
```

### 专用颜色

```css
/* 专车优化类型 - 蓝色系 */
blue-50: '#eff6ff'
blue-100: '#dbeafe'
blue-600: '#2563eb'
blue-700: '#1d4ed8'

/* 混装优化类型 - 紫色系 */
purple-50: '#faf5ff'
purple-100: '#f3e8ff'
purple-600: '#9333ea'
purple-700: '#7c3aed'

/* 状态颜色 */
emerald-50: '#ecfdf5'    /* 成功背景 */
emerald-600: '#059669'   /* 成功状态 */
amber-50: '#fffbeb'      /* 警告背景 */
amber-600: '#d97706'     /* 警告状态 */
slate-50: '#f8fafc'      /* 页面背景 */
slate-100: '#f1f5f9'     /* 浅色背景 */
slate-200: '#e2e8f0'     /* 边框颜色 */
slate-300: '#cbd5e1'     /* 分割线颜色 */
slate-400: '#94a3b8'     /* 次要图标 */
slate-500: '#64748b'     /* 辅助文本 */
slate-600: '#475569'     /* 次要文本 */
slate-700: '#334155'     /* 主要文本 */
slate-800: '#1e293b'     /* 重要文本 */
slate-900: '#0f172a'     /* 标题文本 */
```

### 货物类型配色

```css
/* 3D 货物可视化标准色 */
Electronics: '#1890ff'  /* 电子产品 - 蓝色 */
Furniture: '#faad14'    /* 家具 - 黄色 */
FMCG: '#52c41a'         /* 快消品 - 绿色 */
Auto Parts: '#eb2f96'   /* 汽配 - 粉色 */
Cold Chain: '#13c2c2'   /* 冷链 - 青色 */
Merged Box: '#722ed1'   /* 聚合标准箱 - 紫色 */
```

## 字体规范

### 字体族

```css
font-family: 'Inter', 'Noto Sans SC', sans-serif
```

### 字号层级

```css
/* 主标题 */
text-xl: 1.25rem (20px)   /* 页面主标题 */
text-lg: 1.125rem (18px)  /* 区域标题 */

/* 副标题/内容标题 */
text-sm: 0.875rem (14px)  /* 卡片标题、按钮文字 */
text-xs: 0.75rem (12px)   /* 小标题、标签文字 */

/* 正文内容 */
text-base: 1rem (16px)    /* 正文内容 */

/* 辅助信息 */
text-[10px]: 0.625rem     /* 元数据、时间戳 */
text-[9px]: 0.5625rem     /* 状态标签 */
```

### 字重规范

```css
font-light: 300           /* 轻体 - 用于品牌名 */
font-normal: 400          /* 常规 - 正文内容 */
font-medium: 500          /* 中等 - 重要信息 */
font-semibold: 600        /* 半粗 - 次级标题 */
font-bold: 700            /* 粗体 - 主要标题 */
```

## 布局规范

### 整体布局

```
Header (64px)
├── Logo + 品牌信息
└── 用户信息 + 系统状态

Main Content (flex-1)
├── Sidebar (320px)
│   ├── 工单管理
│   ├── 计算引擎状态
│   └── 车辆资源池
│       ├── 专车资源池 (Dedicated)
│       ├── 混装资源池 (Mixed)
│       └── 待命车队 (Standby)
└── 可视化区域
    ├── Tab 导航
    ├── 动态信息栏
    └── 内容展示区
        ├── 3D 装载视图
        ├── 路径规划视图
        └── 分析报告
```

### 间距规范

```css
/* 页面级间距 */
p-4: 1rem (16px)        /* 页面内边距 */
p-6: 1.5rem (24px)      /* 区块内边距 */

/* 组件级间距 */
gap-2: 0.5rem (8px)     /* 元素间距 */
gap-3: 0.75rem (12px)   /* 卡片间距 */
gap-4: 1rem (16px)      /* 区块间距 */

/* 内容间距 */
space-y-2: 0.5rem (8px)  /* 垂直间距 */
space-y-3: 0.75rem (12px)
space-y-4: 1rem (16px)
space-y-6: 1.5rem (24px)
space-y-8: 2rem (32px)
```

### 组件尺寸

```css
/* 按钮尺寸 */
px-4 py-2: 16px 8px      /* 标准按钮 */
px-3 py-1.5: 12px 6px    /* 小按钮 */
px-8 py-3: 32px 12px     /* 主要操作按钮 */

/* 卡片圆角 */
rounded-lg: 8px          /* 标准卡片 */
rounded-xl: 12px         /* 大卡片 */
rounded-2xl: 16px        /* 特大卡片 */

/* 图标尺寸 */
w-4 h-4: 16px           /* 标准图标 */
w-5 h-5: 20px           /* 大图标 */
w-6 h-6: 24px           /* 特大图标 */
```

## 组件规范

### 按钮样式

#### 主要操作按钮

```css
/* 主要按钮 */
bg-blue-600 hover:bg-blue-700 text-white font-bold px-8 py-3
shadow-lg shadow-blue-200 hover:shadow-blue-300 active:scale-95

/* 次要按钮 */
bg-white border border-slate-300 text-slate-700 font-medium
hover:bg-slate-50 px-6 py-3
```

#### 状态按钮

```css
/* 成功状态 */
bg-emerald-600 text-white hover:bg-emerald-700
px-4 py-2 rounded-lg shadow-sm

/* 警告状态 */
bg-amber-600 text-white hover:bg-amber-700
px-4 py-2 rounded-lg shadow-sm

/* 禁用状态 */
opacity-50 cursor-not-allowed pointer-events-none
```

### 卡片样式

#### 基础卡片

```css
bg-white border border-slate-200 rounded-xl shadow-sm
hover:shadow-md transition-shadow
```

#### 信息卡片

```css
bg-white p-4 rounded-xl border border-slate-200 shadow-sm
relative overflow-hidden
```

#### 状态卡片

```css
/* 选中状态 */
bg-blue-50 border-blue-200 shadow-sm translate-x-1

/* 悬停状态 */
hover:border-blue-200 hover:shadow-sm
```

### 表单组件

#### 输入框

```css
w-full px-3 py-2 bg-white border border-slate-300 rounded-lg
focus:ring-2 focus:ring-blue-500 focus:border-blue-500
text-sm text-slate-700
```

#### 文件上传区域

```css
group cursor-pointer overflow-hidden rounded-xl
border-2 border-dashed border-slate-300 bg-slate-50
hover:bg-blue-50 hover:border-blue-400 transition-all
p-6
```

## 状态管理

### 状态枚举

```typescript
// 车辆状态
enum VehicleStatus {
  IDLE = 'IDLE',           // 空闲
  OPTIMIZED = 'OPTIMIZED', // 已优化
  IN_TRANSIT = 'IN_TRANSIT' // 运输中
}

// 优化类型
enum OptimizationType {
  DEDICATED = 'DEDICATED', // 专车
  MIXED = 'MIXED'          // 混装
}

// 模拟状态
type SimulationPhase = 'IDLE' | 'ANALYZING' | 'CONFIRM_ANALYSIS' |
                      'PACKING_3D' | 'ROUTING_VRP' | 'COMPLETE';
```

### 状态样式映射

```css
/* 优化类型颜色 */
DEDICATED: 蓝色系 (blue-600, blue-100)
MIXED: 紫色系 (purple-600, purple-100)

/* 状态颜色 */
OPTIMIZED: 绿色系 (emerald-600, emerald-50)
IN_TRANSIT: 琥珀色系 (amber-600, amber-50)
IDLE: 灰色系 (slate-400, slate-50)
```

## 动画规范

### 过渡动画

```css
/* 标准过渡 */
transition-all duration-200
transition-colors duration-300
transition-transform duration-300

/* 页面级动画 */
animate-in fade-in slide-in-from-right duration-500
animate-in zoom-in-95 duration-300
animate-in slide-in-from-top-2 duration-300
```

### 交互反馈

```css
/* 按钮点击 */
active:scale-95

/* 悬停效果 */
hover:scale-105
hover:shadow-md
hover:bg-slate-50

/* 加载动画 */
animate-pulse          /* 脉冲动画 */
animate-bounce         /* 弹跳动画 */
animate-spin           /* 旋转动画 */
```

## 响应式设计

### 断点设置

```css
/* Tailwind 默认断点 */
sm: 640px    /* 小屏幕 */
md: 768px    /* 中屏幕 */
lg: 1024px   /* 大屏幕 */
xl: 1280px   /* 超大屏幕 */
```

### 响应式规则

```css
/* 隐藏/显示 */
hidden md:flex          /* 移动端隐藏，桌面端显示 */
block sm:hidden          /* 移动端显示，桌面端隐藏 */

/* 间距调整 */
p-4 lg:p-6             /* 移动端小间距，桌面端大间距 */

/* 字号调整 */
text-sm lg:text-base    /* 移动端小字，桌面端正常字 */
```

## 3D 可视化规范

### 性能优化

```typescript
// 渲染性能保护模式
- 采样显示：仅显示 40% 数据以保持流畅
- 自适应质量：根据设备性能调整渲染质量
- 视图控制：提供重置、缩放、全屏功能
```

### 3D 场景配置

```typescript
// 摄像机设置
PerspectiveCamera position={[12, 12, 12]} fov={45}

// 光照设置
ambientLight intensity={0.7}
spotLight position={[20, 30, 10]} intensity={1.5}
pointLight position={[-10, 5, -10]} intensity={0.5}

// 材质设置
roughness: 0.3          /* 粗糙度 */
metalness: 0.1          /* 金属度 */
opacity: 0.95           /* 透明度 */
```

### 控制面板

```css
/* 位置固定 */
absolute top-4 right-4 z-10

/* 样式统一 */
bg-white/90 backdrop-blur px-4 py-3
rounded-lg border border-slate-200 shadow-lg

/* 信息层级 */
text-xs font-bold text-slate-800 mb-1  /* 主信息 */
text-[10px] text-slate-500             /* 辅助信息 */
```

## 图标使用规范

### Lucide React 图标

```typescript
// 主要功能图标
LayoutDashboard: 仪表盘
Truck: 车辆/运输
Package: 包装/3D视图
Map: 地图/路径
UploadCloud: 文件上传
Play: 开始/执行
CheckCircle2: 完成/成功
AlertCircle: 警告/注意
BarChart3: 数据分析
Layers: 应用/系统
FileText: 文件/报告
Download: 下载/导出
Send: 发送/提交
```

### 图标尺寸

```css
/* 按钮图标 */
w-4 h-4: 16px  /* 标准按钮 */
w-5 h-5: 20px  /* 大按钮 */

/* 信息图标 */
w-6 h-6: 24px  /* 标题图标 */
w-8 h-8: 32px  /* 状态图标 */

/* 装饰图标 */
w-12 h-12: 48px /* 空状态图标 */
w-16 h-16: 64px /* 特殊场景 */
```

## 代码组织规范

### 文件命名

```typescript
// 组件文件
PascalCase.tsx     // React 组件
kebab-case.css     // 样式文件

// 类型文件
types.ts           // 类型定义
constants.ts       // 常量定义
```

### 目录结构

```
optilogix-admin/
├── components/          # 可复用组件
│   ├── RouteMap.tsx    # 路径地图组件
│   └── ThreeDPacking.tsx # 3D装载组件
├── App.tsx             # 主应用组件
├── types.ts            # 类型定义
├── constants.ts        # 常量定义
├── index.html          # HTML 模板
└── index.tsx           # 入口文件
```

### TypeScript 规范

```typescript
// 接口定义
interface Vehicle {
  id: string;
  name: string;
  type: 'LARGE' | 'MEDIUM' | 'SMALL';
  optType: OptimizationType;
  // ...其他属性
}

// 枚举定义
enum VehicleStatus {
  IDLE = 'IDLE',
  OPTIMIZED = 'OPTIMIZED',
  IN_TRANSIT = 'IN_TRANSIT'
}

// 函数组件
interface ComponentProps {
  // 属性定义
}

const Component: React.FC<ComponentProps> = ({ prop }) => {
  // 组件实现
};
```

## 用户体验规范

### 加载状态

```css
/* 进度条 */
h-1.5 bg-slate-100 rounded-full overflow-hidden
bg-gradient-to-r from-blue-500 to-indigo-500 transition-all

/* 加载动画 */
w-3 h-3 border-2 border-slate-400 border-t-transparent rounded-full animate-spin
```

### 错误处理

```css
/* 错误提示 */
bg-red-50 border border-red-200 text-red-700
px-4 py-3 rounded-lg flex items-center gap-2

/* 警告提示 */
bg-amber-50 border border-amber-200 text-amber-700
px-4 py-3 rounded-lg flex items-center gap-2
```

### 成功反馈

```css
/* 成功状态 */
bg-emerald-50 border border-emerald-200 text-emerald-700
px-4 py-3 rounded-lg flex items-center gap-2
```

### 空状态

```css
/* 空状态样式 */
flex flex-col items-center justify-center
text-slate-300 select-none bg-slate-50/50

/* 空状态图标 */
p-6 bg-white rounded-full shadow-sm mb-4 border border-slate-100

/* 空状态文字 */
text-sm font-medium text-slate-400
```

## 可访问性规范

### 语义化标签

```jsx
// 正确的语义化结构
<header>    // 页面头部
<nav>       // 导航区域
<main>      // 主要内容
<aside>     // 侧边栏
<section>   // 内容区块
<footer>    // 页面底部
```

### ARIA 属性

```jsx
// 按钮状态
aria-label="关闭对话框"
aria-describedby="帮助文本"
aria-expanded={isOpen}
aria-disabled={isDisabled}
```

### 键盘导航

```css
/* 焦点样式 */
focus:ring-2 focus:ring-blue-500 focus:border-blue-500

/* 跳转链接 */
sr-only focus:not-sr-only focus:absolute focus:top-4 focus:left-4
```

## 性能优化规范

### 代码分割

```typescript
// 懒加载组件
const LazyComponent = React.lazy(() => import('./LazyComponent'));

// 条件渲染
{showComponent && <LazyComponent />}
```

### 状态优化

```typescript
// 使用 useMemo
const expensiveValue = useMemo(() => {
  return computeExpensiveValue(data);
}, [data]);

// 使用 useCallback
const handleClick = useCallback(() => {
  // 处理点击
}, [dependency]);
```

### 3D 性能优化

```typescript
// 采样渲染
const sampleData = cargo.slice(0, Math.floor(cargo.length * 0.4));

// 视图控制
OrbitControls
  autoRotate
  autoRotateSpeed={vehicle.optType === OptimizationType.DEDICATED ? 0.2 : 0.5}
```

## 开发工具配置

### Tailwind 配置

```javascript
// tailwind.config.js
module.exports = {
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', 'Noto Sans SC', 'sans-serif'],
      },
      colors: {
        tech: {
          blue: '#1890ff',
          dark: '#001529',
          light: '#f0f2f5',
          card: '#ffffff',
          success: '#52c41a',
          warning: '#faad14',
          text: '#1f2937',
          subtext: '#6b7280'
        }
      },
      animation: {
        'pulse-fast': 'pulse 1.5s cubic-bezier(0.4, 0, 0.6, 1) infinite',
      }
    },
  },
}
```

### 构建配置

```typescript
// vite.config.ts
export default defineConfig({
  plugins: [react()],
  optimizeDeps: {
    include: ['react', 'react-dom', 'three']
  }
})
```

## 部署规范

### 环境变量

```bash
# .env.local
VITE_API_URL=http://localhost:3000
VITE_APP_TITLE=OptiLogix Admin
```

### 构建输出

```bash
# 开发环境
npm run dev

# 生产构建
npm run build

# 预览构建结果
npm run preview
```

---

## 更新记录

- **v1.0** (2025-11-19): 基于现有代码库整理的初始版本前端规范

## 维护说明

本规范文档基于 OptiLogix Admin 项目的实际代码结构整理，随着项目迭代需要持续更新。开发新功能时请严格遵循本规范，确保界面风格的一致性和代码的可维护性。