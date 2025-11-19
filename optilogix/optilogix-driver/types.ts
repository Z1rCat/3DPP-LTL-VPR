export interface Driver {
  id: string;
  name: string;
  phone: string;
  avatar: string;
  vehicleId: string;
  stats: {
    todayTasks: number;
    completedTasks: number;
    efficiency: number;
    totalDistance: number;
  };
}

export interface Vehicle {
  id: string;
  plateNumber: string;
  type: string;
  capacity: {
    weight: number; // tons
    volume: number; // m3
  };
  status: 'IDLE' | 'IN_TRANSIT' | 'LOADING' | 'ERROR';
}

export interface CargoItem {
  id: string;
  name: string;
  quantity: number;
  weight: number;
  type: 'Electronics' | 'Furniture' | 'FMCG' | 'Auto Parts' | 'Cold Chain';
  dimensions?: [number, number, number]; // l, w, h
}

export interface Task {
  id: string;
  title: string;
  time: string;
  location: string;
  status: 'pending' | 'active' | 'completed' | 'urgent';
  duration: number; // minutes
  notes?: string;
  cargo?: CargoItem[];
  type: 'PICKUP' | 'DELIVERY' | 'REST' | 'MAINTENANCE';
}

export interface RouteData {
  currentLocation: [number, number];
  destination: [number, number];
  waypoints: Array<{ coordinates: [number, number]; name: string }>;
  estimatedTime: number;
  distance: number;
}