
import { Vehicle, VehicleStatus, DeliveryPoint, CargoItem, OptimizationType } from './types';

export const MOCK_VEHICLES: Vehicle[] = [
  // 专车 (Dedicated)
  { 
    id: 'LARGE_TRUCK_001', 
    name: '川A·56789 (重型)', 
    type: 'LARGE', 
    optType: OptimizationType.DEDICATED,
    cargoTypeDescription: '家具专线 (双流/新都)',
    capacityWeight: 15000, 
    capacityVolume: 45, 
    status: VehicleStatus.OPTIMIZED, 
    efficiency: 98.2,
    dimensions: [12, 2.5, 3]
  },
  { 
    id: 'LARGE_TRUCK_002', 
    name: '川A·12345 (重型)', 
    type: 'LARGE', 
    optType: OptimizationType.DEDICATED,
    cargoTypeDescription: '家电专线 (高新南区)',
    capacityWeight: 15000, 
    capacityVolume: 45, 
    status: VehicleStatus.OPTIMIZED, 
    efficiency: 96.5,
    dimensions: [12, 2.5, 3]
  },
  { 
    id: 'LARGE_TRUCK_003', 
    name: '川A·99887 (重型)', 
    type: 'LARGE', 
    optType: OptimizationType.DEDICATED,
    cargoTypeDescription: '建材专线 (龙泉驿)',
    capacityWeight: 15000, 
    capacityVolume: 45, 
    status: VehicleStatus.OPTIMIZED, 
    efficiency: 95.8,
    dimensions: [12, 2.5, 3]
  },
  // 混装车 (Mixed)
  { 
    id: 'MEDIUM_TRUCK_101', 
    name: '川A·B1024 (中型)', 
    type: 'MEDIUM', 
    optType: OptimizationType.MIXED,
    cargoTypeDescription: '混合/聚合标准箱',
    capacityWeight: 5000, 
    capacityVolume: 18, 
    status: VehicleStatus.OPTIMIZED, 
    efficiency: 88.2,
    dimensions: [6, 2.2, 2.4]
  },
  { 
    id: 'MEDIUM_TRUCK_102', 
    name: '川A·C2048 (中型)', 
    type: 'MEDIUM', 
    optType: OptimizationType.MIXED,
    cargoTypeDescription: '混合/二环内配送',
    capacityWeight: 5000, 
    capacityVolume: 18, 
    status: VehicleStatus.IDLE, 
    efficiency: 0,
    dimensions: [6, 2.2, 2.4]
  },
  { 
    id: 'MEDIUM_TRUCK_103', 
    name: '川A·D4096 (中型)', 
    type: 'MEDIUM', 
    optType: OptimizationType.MIXED,
    cargoTypeDescription: '混合/天府新区加急',
    capacityWeight: 5000, 
    capacityVolume: 18, 
    status: VehicleStatus.IDLE, 
    efficiency: 0,
    dimensions: [6, 2.2, 2.4]
  },
];

// 成都真实地理坐标映射
// 仓库设在：成都传化公路港 (新都区)
export const MOCK_DELIVERY_POINTS: DeliveryPoint[] = [
  { id: 'DEPOT', name: '成都传化物流基地', lat: 30.822772, lng: 104.165738, demand: 0, sequence: 0 }, // 北部新都
  { id: 'DP_01', name: '锦江区春熙路IFS', lat: 30.655585, lng: 104.081529, demand: 1200, sequence: 1 }, // 市中心
  { id: 'DP_02', name: '高新区天府软件园', lat: 30.545333, lng: 104.069571, demand: 3000, sequence: 2 }, // 南部高新
  { id: 'DP_03', name: '青羊区宽窄巷子', lat: 30.663493, lng: 104.053142, demand: 500, sequence: 3 }, // 西部文创
  { id: 'DP_04', name: '成华区东郊记忆', lat: 30.674349, lng: 104.124836, demand: 2200, sequence: 4 }, // 东部
  { id: 'DP_05', name: '双流国际机场货运站', lat: 30.567862, lng: 103.957203, demand: 800, sequence: 5 }, // 西南
  { id: 'DP_06', name: '金牛区国际商贸城', lat: 30.773678, lng: 104.098515, demand: 1500, sequence: 6 }, // 北部商贸
  { id: 'DP_07', name: '龙泉驿汽车城', lat: 30.562242, lng: 104.243570, demand: 900, sequence: 7 }, // 东部工业
];

export const MOCK_CARGO_TYPES = [
  { type: 'Electronics', dim: [0.4, 0.3, 0.2], weight: 5, color: '#1890ff' }, // 电子产品
  { type: 'Furniture', dim: [1.2, 0.8, 0.6], weight: 40, color: '#faad14' }, // 家具
  { type: 'FMCG', dim: [0.5, 0.5, 0.5], weight: 15, color: '#52c41a' }, // 快消品
  { type: 'Auto Parts', dim: [0.8, 0.6, 0.4], weight: 25, color: '#eb2f96' }, // 汽配
  { type: 'Cold Chain', dim: [0.6, 0.4, 0.4], weight: 10, color: '#13c2c2' }, // 冷链
  { type: 'Merged Box', dim: [0.6, 0.4, 0.4], weight: 20, color: '#722ed1' }, // 聚合标准箱
];

// Generate cargo based on vehicle type
export const generateSmartCargo = (vehicle: Vehicle): CargoItem[] => {
  
  if (vehicle.optType === OptimizationType.DEDICATED) {
    // Uniform cargo, neatly packed
    const itemType = vehicle.cargoTypeDescription?.includes('家具') 
      ? MOCK_CARGO_TYPES[1] // Furniture
      : MOCK_CARGO_TYPES[0]; // Electronics
      
    return Array.from({ length: 60 }).map((_, i) => ({
      id: `UNI_${i}`,
      name: `${itemType.type} #${i}`,
      weight: itemType.weight,
      dimensions: itemType.dim as [number, number, number],
      color: itemType.color,
      isMergedItem: false
    }));
  } else {
    // Mixed cargo, including "Merged Boxes"
    return Array.from({ length: 45 }).map((_, i) => {
      // 30% chance of being a "Merged Box" (purple)
      const isMerged = Math.random() < 0.3;
      const type = isMerged ? MOCK_CARGO_TYPES[5] : MOCK_CARGO_TYPES[i % 5];
      
      return {
        id: `MIX_${i}`,
        name: isMerged ? `聚合微件包 #${i}` : `${type.type} #${i}`,
        weight: type.weight,
        dimensions: type.dim as [number, number, number],
        color: type.color,
        isMergedItem: isMerged
      };
    });
  }
};