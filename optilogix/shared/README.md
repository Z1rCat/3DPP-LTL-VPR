# 共享组件库 (Shared Components)

<div align="center">

![共享组件库](https://via.placeholder.com/150x60/8b5cf6/ffffff?text=Shared+Library)

**OptiLogix 物流管理系统 - 通用组件和工具**

[![React](https://img.shields.io/badge/React-19.2.0-blue.svg)](https://reactjs.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.8.2-blue.svg)](https://www.typescriptlang.org/)
[![Storybook](https://img.shields.io/badge/Storybook-Ready-ff4785.svg)](https://storybook.js.org/)

[组件概览](#组件概览) • [使用指南](#使用指南) • [开发指南](#开发指南) • [API文档](#api文档)

</div>

## 📋 模块概述

共享组件库是OptiLogix物流系统的核心资源共享中心，包含所有前端应用共用的UI组件、工具函数、类型定义和业务逻辑。通过统一的组件库，确保系统的一致性、可维护性和开发效率。

### 🎯 核心价值
- **代码复用**: 避免重复开发，提高开发效率
- **一致性**: 统一的UI风格和交互体验
- **可维护性**: 集中管理，统一更新和维护
- **类型安全**: 完整的TypeScript类型定义
- **测试覆盖**: 全面测试确保组件质量

## ✨ 组件概览

### 🎨 UI组件库
**基础UI组件**

- **布局组件**: Grid、Container、Stack、Spacer
- **表单组件**: Form、Input、Select、DatePicker、Upload
- **数据展示**: Table、Card、List、Badge、Avatar
- **反馈组件**: Modal、Drawer、Toast、Loading、Empty
- **导航组件**: Menu、Breadcrumb、Pagination、Tabs
- **业务组件**: MapContainer、StatusIndicator、QRCode

```typescript
// 基础组件示例
import { Button, Input, Modal } from '@optilogix/shared/ui';

const MyComponent = () => {
  return (
    <div>
      <Input placeholder="请输入内容" />
      <Button variant="primary">提交</Button>
      <Modal title="确认对话框">
        <p>确定要执行此操作吗？</p>
      </Modal>
    </div>
  );
};
```

### 🗺️ 地图组件
**物流专用地图组件**

- **基础地图**: MapContainer、MapControls
- **标记组件**: Marker、ClusterMarker
- **路线组件**: RouteLine、NavigationPath
- **区域组件**: DeliveryZone、ServiceArea
- **交互组件**: Geocoder、DrawingTools

```typescript
import {
  MapContainer,
  Marker,
  RouteLine,
  DeliveryZone
} from '@optilogix/shared/maps';

const DeliveryMap = ({ routes, zones }) => {
  return (
    <MapContainer>
      {routes.map(route => (
        <RouteLine key={route.id} path={route.path} />
      ))}
      {zones.map(zone => (
        <DeliveryZone key={zone.id} area={zone.area} />
      ))}
    </MapContainer>
  );
};
```

### 📊 图表组件
**数据可视化组件**

- **基础图表**: LineChart、BarChart、PieChart
- **业务图表**: DeliveryChart、PerformanceChart
- **统计组件**: MetricCard、TrendIndicator
- **仪表盘**: DashboardGrid、WidgetContainer

```typescript
import {
  LineChart,
  MetricCard,
  DeliveryChart
} from '@optilogix/shared/charts';

const AnalyticsDashboard = ({ data }) => {
  return (
    <DashboardGrid>
      <MetricCard title="今日订单" value={data.todayOrders} />
      <LineChart data={data.trendData} />
      <DeliveryChart data={data.deliveryStats} />
    </DashboardGrid>
  );
};
```

### 🔧 工具函数库
**通用工具函数**

- **日期处理**: formatDate、dateDiff、timezoneConvert
- **数据验证**: validateEmail、validatePhone、validateAddress
- **数据转换**: formatCurrency、formatFileSize、formatPercentage
- **地理计算**: calculateDistance、getBounds、isPointInPolygon
- **字符串处理**: truncate、capitalize、slugify

```typescript
import {
  formatDate,
  validateEmail,
  calculateDistance,
  formatCurrency
} from '@optilogix/shared/utils';

// 使用示例
const formattedDate = formatDate(new Date(), 'YYYY-MM-DD');
const isValidEmail = validateEmail('user@example.com');
const distance = calculateDistance(point1, point2);
const price = formatCurrency(1234.56, 'CNY');
```

### 📝 类型定义
**TypeScript类型定义**

- **业务类型**: Order、User、Vehicle、Delivery
- **API类型**: ApiResponse、Pagination、FilterOptions
- **表单类型**: FormField、ValidationRule、FormData
- **事件类型**: ClickEvent、ChangeEvent、CustomEvent

```typescript
import type {
  Order,
  User,
  ApiResponse,
  PaginationOptions
} from '@optilogix/shared/types';

const processOrder = (order: Order): void => {
  // 类型安全的订单处理
};

const fetchUsers = async (
  options: PaginationOptions
): Promise<ApiResponse<User[]>> => {
  // 类型安全的API调用
};
```

## 🏗️ 技术架构

### 技术栈
```json
{
  "framework": "React 19.2.0",
  "language": "TypeScript 5.8.2",
  "ui": "@mui/material 5.15.0",
  "maps": "mapbox-gl 2.15.0",
  "charts": "recharts 2.8.0",
  "testing": "@testing-library/react 14.0.0",
  "storybook": "@storybook/react 7.0.0",
  "build": "vite 6.2.0",
  "linting": "eslint 8.0.0"
}
```

### 目录结构
```
shared/
├── components/              # UI组件
│   ├── ui/                 # 基础UI组件
│   │   ├── Button/
│   │   │   ├── Button.tsx
│   │   │   ├── Button.test.tsx
│   │   │   ├── Button.stories.tsx
│   │   │   └── index.ts
│   │   ├── Input/
│   │   ├── Modal/
│   │   └── ...
│   ├── business/           # 业务组件
│   │   ├── MapContainer/
│   │   ├── OrderCard/
│   │   └── ...
│   └── forms/              # 表单组件
│       ├── FormField/
│       ├── FormValidation/
│       └── ...
├── maps/                   # 地图相关组件
│   ├── MapContainer/
│   ├── Marker/
│   ├── RouteLine/
│   └── index.ts
├── charts/                 # 图表组件
│   ├── LineChart/
│   ├── MetricCard/
│   └── index.ts
├── utils/                  # 工具函数
│   ├── date.ts
│   ├── validation.ts
│   ├── geography.ts
│   ├── format.ts
│   └── index.ts
├── types/                  # TypeScript类型
│   ├── business.ts
│   ├── api.ts
│   ├── form.ts
│   └── index.ts
├── constants/              # 常量定义
│   ├── api.ts
│   ├── status.ts
│   ├── config.ts
│   └── index.ts
├── hooks/                  # 自定义Hooks
│   ├── useDebounce.ts
│   ├── useLocalStorage.ts
│   ├── useGeolocation.ts
│   └── index.ts
├── styles/                 # 样式文件
│   ├── theme.ts
│   ├── variables.ts
│   └── mixins.ts
├── stories/                # Storybook故事
├── tests/                  # 测试工具
│   ├── setup.ts
│   ├── mocks/
│   └── utils.ts
├── package.json
├── vite.config.ts
├── tsconfig.json
└── .storybook/
    └── main.ts
```

## 🚀 快速开始

### 安装依赖
```bash
cd shared
npm install
```

### 开发环境
```bash
# 启动Storybook
npm run storybook

# 访问 http://localhost:6006
```

### 构建组件库
```bash
# 构建生产版本
npm run build

# 类型检查
npm run type-check

# 生成类型声明文件
npm run generate-types
```

## 📖 使用指南

### 在其他项目中使用
```bash
# 在其他应用目录中安装
npm install ../shared

# 或使用yarn link
cd shared
yarn link

cd ../admin-dashboard
yarn link @optilogix/shared
```

### 导入组件
```typescript
// 导入UI组件
import { Button, Input, Modal } from '@optilogix/shared/ui';

// 导入地图组件
import { MapContainer, Marker } from '@optilogix/shared/maps';

// 导入工具函数
import { formatDate, validateEmail } from '@optilogix/shared/utils';

// 导入类型定义
import type { Order, User } from '@optilogix/shared/types';
```

### 主题配置
```typescript
import { createOptilogixTheme } from '@optilogix/shared/styles';

const theme = createOptilogixTheme({
  palette: {
    primary: {
      main: '#1e40af',
    }
  },
  components: {
    Button: {
      styleOverrides: {
        root: {
          borderRadius: 8,
        }
      }
    }
  }
});
```

## 🧪 测试

### 单元测试
```bash
# 运行测试
npm run test

# 测试覆盖率
npm run test:coverage

# 监听模式
npm run test:watch
```

### 组件测试
```typescript
import { render, screen } from '@testing-library/react';
import { Button } from '../Button';

describe('Button Component', () => {
  it('renders correctly', () => {
    render(<Button>Click me</Button>);
    expect(screen.getByText('Click me')).toBeInTheDocument();
  });

  it('handles click events', () => {
    const handleClick = jest.fn();
    render(<Button onClick={handleClick}>Click me</Button>);

    screen.getByText('Click me').click();
    expect(handleClick).toHaveBeenCalledTimes(1);
  });
});
```

## 🔧 开发指南

### 创建新组件
```bash
# 使用组件模板生成器
npm run generate-component MyComponent

# 手动创建组件目录
mkdir components/ui/MyComponent
touch components/ui/MyComponent/MyComponent.tsx
touch components/ui/MyComponent/MyComponent.test.tsx
touch components/ui/MyComponent/MyComponent.stories.tsx
touch components/ui/MyComponent/index.ts
```

### 组件开发规范
```typescript
// components/ui/MyComponent/MyComponent.tsx
import React from 'react';
import { Box, Typography } from '@mui/material';
import { MyComponentProps } from './types';

export const MyComponent: React.FC<MyComponentProps> = ({
  title,
  children,
  variant = 'default',
  ...props
}) => {
  return (
    <Box {...props}>
      <Typography variant="h6">{title}</Typography>
      {children}
    </Box>
  );
};

MyComponent.displayName = 'MyComponent';
```

### Storybook故事编写
```typescript
// components/ui/MyComponent/MyComponent.stories.tsx
import type { Meta, StoryObj } from '@storybook/react';
import { MyComponent } from './MyComponent';

const meta: Meta<typeof MyComponent> = {
  title: 'UI/MyComponent',
  component: MyComponent,
  tags: ['autodocs'],
};

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
  args: {
    title: '示例标题',
    children: '组件内容',
  },
};

export const WithVariant: Story = {
  args: {
    title: '变体示例',
    variant: 'primary',
    children: '这是主要变体',
  },
};
```

### 工具函数开发
```typescript
// utils/validation.ts
export const validateEmail = (email: string): boolean => {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return emailRegex.test(email);
};

export const validatePhone = (phone: string): boolean => {
  const phoneRegex = /^1[3-9]\d{9}$/;
  return phoneRegex.test(phone);
};

// 单元测试
import { validateEmail, validatePhone } from '../validation';

describe('Validation Utils', () => {
  it('should validate email correctly', () => {
    expect(validateEmail('test@example.com')).toBe(true);
    expect(validateEmail('invalid-email')).toBe(false);
  });

  it('should validate phone correctly', () => {
    expect(validatePhone('13800138000')).toBe(true);
    expect(validatePhone('12345678901')).toBe(false);
  });
});
```

## 📚 API文档

### 组件API
```typescript
interface ButtonProps {
  variant?: 'primary' | 'secondary' | 'danger';
  size?: 'small' | 'medium' | 'large';
  disabled?: boolean;
  loading?: boolean;
  icon?: React.ReactNode;
  onClick?: () => void;
  children: React.ReactNode;
}
```

### 工具函数API
```typescript
// 日期工具
export const formatDate = (
  date: Date | string | number,
  format: string = 'YYYY-MM-DD'
): string;

export const dateDiff = (
  date1: Date,
  date2: Date,
  unit: 'days' | 'hours' | 'minutes'
): number;

// 验证工具
export const validateEmail = (email: string): boolean;
export const validatePhone = (phone: string): boolean;
export const validateAddress = (address: Address): ValidationResult;

// 地理工具
export const calculateDistance = (
  point1: GeoLocation,
  point2: GeoLocation,
  unit: 'km' | 'miles' = 'km'
): number;
```

## 🎨 设计系统

### 颜色规范
```typescript
export const colors = {
  primary: {
    50: '#eff6ff',
    500: '#3b82f6',
    900: '#1e3a8a',
  },
  secondary: {
    50: '#f0f9ff',
    500: '#06b6d4',
    900: '#164e63',
  },
  success: '#10b981',
  warning: '#f59e0b',
  error: '#ef4444',
};
```

### 间距规范
```typescript
export const spacing = {
  xs: 4,
  sm: 8,
  md: 16,
  lg: 24,
  xl: 32,
  xxl: 48,
};
```

### 字体规范
```typescript
export const typography = {
  fontFamily: {
    primary: '"Inter", sans-serif',
    monospace: '"JetBrains Mono", monospace',
  },
  fontSize: {
    xs: '0.75rem',
    sm: '0.875rem',
    base: '1rem',
    lg: '1.125rem',
    xl: '1.25rem',
  },
};
```

## 🐛 故障排除

### 常见问题

**Q: 组件样式不生效**
A: 检查主题配置和样式导入顺序

**Q: TypeScript类型错误**
A: 确保正确导入类型定义

**Q: Storybook构建失败**
A: 检查组件依赖和配置文件

**Q: 测试覆盖率不足**
A: 补充缺失的测试用例

### 调试技巧
```typescript
// 开发模式调试
if (process.env.NODE_ENV === 'development') {
  console.log('Component props:', props);
}

// 组件边界错误
import { ErrorBoundary } from 'react-error-boundary';

<ErrorBoundary
  fallback={<div>组件渲染失败</div>}
  onError={(error) => console.error('Component Error:', error)}
>
  <MyComponent />
</ErrorBoundary>
```

## 📚 相关文档

- [组件设计规范](../../docs/component-design.md)
- [Storybook使用指南](../../docs/storybook-guide.md)
- [性能优化建议](../../docs/performance-optimization.md)

## 🤝 贡献

欢迎贡献新的组件和改进建议！

### 组件提交清单
- [ ] 组件功能完整
- [ ] TypeScript类型定义
- [ ] 单元测试覆盖
- [ ] Storybook故事
- [ ] API文档更新
- [ ] 无障碍访问支持

### 提交规范
```bash
# 新组件
git commit -m "feat(shared): 添加MapComponent地图组件"

# 组件修复
git commit -m "fix(shared): 修复Button组件样式问题"

# 文档更新
git commit -m "docs(shared): 更新组件API文档"
```

---

**[⬆ 返回顶部](#共享组件库-shared-components)**

维护者: [姓名](mailto:email@example.com) | 最后更新: 2024-01-XX