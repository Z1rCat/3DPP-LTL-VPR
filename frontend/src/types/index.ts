// 车辆相关类型
export interface Vehicle {
  id: string
  name: string
  type: 'LARGE_TRUCK' | 'MEDIUM_TRUCK' | 'SMALL_TRUCK' | 'LTL_TRUCK'
  status: 'pending' | 'optimizing' | 'completed' | 'error'
  efficiency?: number
  capacity: {
    weight: number // 载重(kg)
    volume: number // 容积(m³)
    dimensions: {
      length: number // 长(m)
      width: number  // 宽(m)
      height: number // 高(m)
    }
  }
  currentLoad?: {
    weight: number
    volume: number
    itemCount: number
  }
  route?: Route
  loadingPlan?: LoadingPlan
  createdAt: string
  updatedAt: string
}

// 路径相关类型
export interface Route {
  id: string
  vehicleId: string
  waypoints: Waypoint[]
  totalDistance: number // 总距离(km)
  totalDuration: number // 总时间(分钟)
  totalCost: number // 总成本
  efficiency: number // 效率评分
  status: 'planning' | 'active' | 'completed'
  createdAt: string
}

export interface Waypoint {
  id: string
  type: 'depot' | 'delivery' | 'pickup'
  location: {
    lat: number
    lng: number
    address: string
  }
  orders: Order[]
  arrivalTime?: string
  departureTime?: string
  serviceDuration: number // 服务时间(分钟)
  sequence: number
}

// 订单相关类型
export interface Order {
  id: string
  customerId: string
  items: OrderItem[]
  pickupLocation: Location
  deliveryLocation: Location
  priority: 'low' | 'medium' | 'high' | 'urgent'
  timeWindows: {
    pickup: {
      start: string
      end: string
    }
    delivery: {
      start: string
      end: string
    }
  }
  status: 'pending' | 'assigned' | 'in_transit' | 'delivered' | 'cancelled'
  createdAt: string
  updatedAt: string
}

export interface OrderItem {
  id: string
  productId: string
  quantity: number
  weight: number
  volume: number
  dimensions: {
    length: number
    width: number
    height: number
  }
  category: string
  fragile: boolean
  stacking_limit?: number
}

// 位置信息类型
export interface Location {
  lat: number
  lng: number
  address: string
  city?: string
  district?: string
  postalCode?: string
}

// 装载计划类型
export interface LoadingPlan {
  id: string
  vehicleId: string
  items: LoadedItem[]
  totalWeight: number
  totalVolume: number
  spaceUtilization: number // 空间利用率(%)
  weightUtilization: number // 重量利用率(%)
  loadingSequence: LoadingStep[]
  visualizationUrl?: string
  createdAt: string
}

export interface LoadedItem {
  orderItemId: string
  position: {
    x: number
    y: number
    z: number
  }
  rotation: {
    x: number
    y: number
    z: number
  }
  loadingOrder: number
}

export interface LoadingStep {
  step: number
  itemId: string
  action: 'load' | 'unload'
  position: {
    x: number
    y: number
    z: number
  }
  estimatedTime: number // 秒
}

// 优化任务类型
export interface OptimizationTask {
  id: string
  name: string
  type: '3dpp' | 'vrppd' | 'hybrid'
  status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled'
  progress: {
    current: number // 当前进度(0-100)
    stage: OptimizationStage
    estimatedTimeRemaining?: number // 预估剩余时间(秒)
  }
  parameters: OptimizationParameters
  results?: OptimizationResult
  error?: string
  createdAt: string
  startedAt?: string
  completedAt?: string
}

export interface OptimizationStage {
  name: string
  progress: number
  status: 'pending' | 'running' | 'completed' | 'failed'
  startTime?: string
  endTime?: string
}

export interface OptimizationParameters {
  vehicles: string[] // 车辆ID列表
  orders: string[] // 订单ID列表
  objectives: OptimizationObjective[]
  constraints: OptimizationConstraint[]
  timeLimit: number // 时间限制(秒)
  maxIterations?: number
}

export interface OptimizationObjective {
  name: 'minimize_distance' | 'minimize_time' | 'minimize_cost' | 'maximize_utilization'
  weight: number // 权重
  priority: number
}

export interface OptimizationConstraint {
  type: 'time_window' | 'capacity' | 'driver_work hours' | 'vehicle_constraints'
  value: any
  strict: boolean // 是否严格约束
}

export interface OptimizationResult {
  totalDistance: number
  totalTime: number
  totalCost: number
  vehicleUtilization: {
    vehicleId: string
    utilizationRate: number
    routeDistance: number
    routeTime: number
    ordersCount: number
  }[]
  kpis: {
    costPerKm: number
    costPerOrder: number
    averageUtilization: number
    onTimeDeliveryRate: number
  }
  routes: Route[]
  loadingPlans: LoadingPlan[]
}

// 数据导入类型
export interface ImportTask {
  id: string
  fileName: string
  fileType: 'csv' | 'json' | 'excel'
  status: 'uploading' | 'validating' | 'processing' | 'completed' | 'failed'
  progress: number
  recordsProcessed: number
  totalRecords: number
  errors?: ImportError[]
  summary?: ImportSummary
  createdAt: string
  completedAt?: string
}

export interface ImportError {
  row: number
  field: string
  value: any
  message: string
  severity: 'error' | 'warning'
}

export interface ImportSummary {
  vehiclesCreated: number
  ordersCreated: number
  customersCreated: number
  recordsUpdated: number
  recordsSkipped: number
}

// 系统统计类型
export interface SystemStats {
  overview: {
    totalVehicles: number
    activeVehicles: number
    totalOrders: number
    pendingOrders: number
    completedOrders: number
    totalDistance: number
    averageEfficiency: number
  }
  performance: {
    onTimeDeliveryRate: number
    averageDeliveryTime: number
    vehicleUtilizationRate: number
    fuelEfficiency: number
    costPerKm: number
  }
  alerts: Alert[]
  recentActivities: Activity[]
}

export interface Alert {
  id: string
  type: 'info' | 'warning' | 'error' | 'success'
  title: string
  message: string
  timestamp: string
  read: boolean
  actionUrl?: string
}

export interface Activity {
  id: string
  type: 'order_created' | 'optimization_completed' | 'vehicle_dispatched' | 'delivery_completed'
  title: string
  description: string
  timestamp: string
  userId?: string
  metadata?: Record<string, any>
}

// API响应类型
export interface ApiResponse<T = any> {
  success: boolean
  data?: T
  message?: string
  error?: {
    code: string
    message: string
    details?: any
  }
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  pageSize: number
  totalPages: number
}

// 用户类型
export interface User {
  id: string
  username: string
  email: string
  role: 'admin' | 'manager' | 'dispatcher' | 'driver'
  profile: {
    firstName: string
    lastName: string
    avatar?: string
    phone?: string
  }
  permissions: string[]
  lastLoginAt?: string
  createdAt: string
}

// 文件上传类型
export interface FileUploadOptions {
  accept: string[]
  maxSize: number // bytes
  multiple?: boolean
  autoUpload?: boolean
}

export interface UploadedFile {
  id: string
  name: string
  size: number
  type: string
  url?: string
  status: 'uploading' | 'completed' | 'error'
  progress: number
  error?: string
}

// 图表数据类型
export interface ChartData {
  labels: string[]
  datasets: {
    label: string
    data: number[]
    backgroundColor?: string | string[]
    borderColor?: string | string[]
    borderWidth?: number
    fill?: boolean
  }[]
}

// 实时数据类型
export interface RealTimeData {
  vehicles: {
    id: string
    location: {
      lat: number
      lng: number
    }
    speed: number
    heading: number
    status: string
    fuelLevel: number
    lastUpdate: string
  }[]
  orders: {
    id: string
    status: string
    estimatedDelivery?: string
    driverLocation?: {
      lat: number
      lng: number
    }
  }[]
}