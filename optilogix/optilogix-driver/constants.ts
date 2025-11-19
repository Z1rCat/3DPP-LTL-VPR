import { Driver, Task, Vehicle, RouteData } from './types';

export const MOCK_DRIVER: Driver = {
  id: 'driver001',
  name: '张师傅',
  phone: '13800138000',
  avatar: 'https://picsum.photos/200',
  vehicleId: 'vehicle001',
  stats: {
    todayTasks: 8,
    completedTasks: 3,
    efficiency: 89.5,
    totalDistance: 156.7
  }
};

export const MOCK_VEHICLE: Vehicle = {
  id: 'vehicle001',
  plateNumber: '川A·88888',
  type: '重型厢式货车',
  capacity: { weight: 15, volume: 45 },
  status: 'IN_TRANSIT'
};

export const MOCK_TASKS: Task[] = [
  {
    id: 't1',
    title: '仓库装货准备',
    time: '09:00',
    location: '龙泉驿区智能物流园 A3库',
    status: 'completed',
    duration: 60,
    type: 'PICKUP',
    notes: '检查货物清单，确认冷链设备状态'
  },
  {
    id: 't2',
    title: '高新区中心配送',
    time: '10:30',
    location: '高新区天府大道 SOHO',
    status: 'completed',
    duration: 45,
    type: 'DELIVERY',
    cargo: [
      { id: 'c1', name: '电子配件', quantity: 20, weight: 200, type: 'Electronics' },
      { id: 'c2', name: '办公家具', quantity: 5, weight: 150, type: 'Furniture' }
    ]
  },
  {
    id: 't3',
    title: '天府软件园配送',
    time: '13:00',
    location: '高新区天府软件园',
    status: 'active',
    duration: 90,
    type: 'DELIVERY',
    cargo: [
      { id: 'c3', name: '服务器机柜', quantity: 2, weight: 400, type: 'Electronics' }
    ]
  },
  {
    id: 't4',
    title: '午间休息',
    time: '14:30',
    location: '高新区休息区',
    status: 'pending',
    duration: 60,
    type: 'REST'
  },
  {
    id: 't5',
    title: '天府新区返程',
    time: '16:00',
    location: '天府新区经济开发区',
    status: 'pending',
    duration: 120,
    type: 'PICKUP'
  }
];

export const MOCK_ROUTE: RouteData = {
  currentLocation: [30.67, 104.07], // Chengdu City Center
  destination: [30.57, 104.06],     // High-tech Zone / Software Park area
  waypoints: [
    { coordinates: [30.62, 104.07], name: '高新区经停点' }
  ],
  estimatedTime: 45,
  distance: 28.5
};

export const COLORS = {
  blue: '#1890ff',
  emerald: '#52c41a',
  amber: '#faad14',
  red: '#ff4d4f',
  slate: '#64748b',
  dark: '#0f172a'
};