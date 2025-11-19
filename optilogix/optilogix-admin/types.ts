
export enum VehicleStatus {
  IDLE = 'IDLE',
  OPTIMIZED = 'OPTIMIZED',
  IN_TRANSIT = 'IN_TRANSIT'
}

export enum OptimizationType {
  DEDICATED = 'DEDICATED', // 单品类专车
  MIXED = 'MIXED'          // 多品类混装
}

export interface Vehicle {
  id: string;
  name: string;
  type: 'LARGE' | 'MEDIUM' | 'SMALL';
  optType: OptimizationType; // New field
  capacityWeight: number; // kg
  capacityVolume: number; // m3
  status: VehicleStatus;
  efficiency: number; // percentage
  dimensions: [number, number, number]; // [L, W, H] in meters
  cargoTypeDescription?: string; // e.g., "家具专线" or "混合百货"
}

export interface CargoItem {
  id: string;
  name: string;
  weight: number;
  dimensions: [number, number, number]; // [L, W, H]
  color: string;
  isMergedItem?: boolean; // Flag for small items merged into standard box
}

export interface DeliveryPoint {
  id: string;
  name: string;
  lat: number; // Latitude
  lng: number; // Longitude
  demand: number;
  sequence?: number; // optimization order
}

export interface SimulationState {
  phase: 'IDLE' | 'ANALYZING' | 'CONFIRM_ANALYSIS' | 'PACKING_3D' | 'ROUTING_VRP' | 'COMPLETE';
  progress: number;
  logs: string[];
}

export interface BatchMetadata {
  batchId: string;
  fileName: string;
  uploadTime: string;
  totalOrders: number;
  totalWeight: number;
  status: 'PENDING' | 'ANALYZED' | 'PROCESSING' | 'DONE';
  priority: 'High' | 'Normal' | 'Low'; // New
  operator: string; // New
  estimatedCompletion: string; // New
}

export interface AnalysisReport {
  totalVolume: number;
  largeCargoVolume: number;
  smallCargoCount: number;
  mergedBoxCount: number; // After merging small items
  dedicatedTrucksNeeded: number;
  mixedTrucksNeeded: number;
}