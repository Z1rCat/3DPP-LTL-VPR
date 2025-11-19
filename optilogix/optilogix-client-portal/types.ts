import { LucideIcon } from 'lucide-react';

export type ViewState = 'dashboard' | 'order-wizard' | 'tracking' | 'history' | 'support';

export interface CargoType {
  id: string;
  name: string;
  icon: LucideIcon;
  color: string;
  description: string;
  quickOrder: {
    defaultWeight: number;
    defaultVolume: number;
    estimatedPrice: number;
    estimatedTime: string;
  };
}

export interface Order {
  id: string;
  createTime: string;
  status: 'pending' | 'confirmed' | 'processing' | 'shipping' | 'completed' | 'cancelled';
  cargoInfo: {
    name: string;
    type: string;
    quantity: number;
    weight: number;
  };
  route: {
    pickup: string;
    delivery: string;
  };
  pricing: {
    totalPrice: number;
    paymentMethod: string;
  };
}

export interface PricingBreakdown {
  basePrice: number;
  weightFee: number;
  specialFee: number;
  discount: number;
  totalPrice: number;
}

export interface ChatMessage {
  id: string;
  sender: 'user' | 'support' | 'ai';
  content: string;
  timestamp: Date;
}
