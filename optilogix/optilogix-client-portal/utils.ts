import { Order, PricingBreakdown } from './types';
import { format, subDays } from 'date-fns';

export const formatCurrency = (amount: number) => {
  return new Intl.NumberFormat('zh-CN', {
    style: 'currency',
    currency: 'CNY',
    minimumFractionDigits: 0,
  }).format(amount);
};

export const calculatePrice = (
  weight: number,
  volume: number,
  distance: number = 50, // Mock distance
  isFragile: boolean = false
): PricingBreakdown => {
  const baseRate = 12; // Base fee
  const distanceRate = 2.5; // Per km
  const weightRate = 1.8; // Per kg
  const volumeRate = 200; // Per m3
  
  const distanceFee = distance * distanceRate;
  const weightFee = Math.max(weight * weightRate, volume * volumeRate);
  const specialFee = isFragile ? 50 : 0;
  
  const subtotal = baseRate + distanceFee + weightFee + specialFee;
  const discount = subtotal > 500 ? subtotal * 0.05 : 0;

  return {
    basePrice: Math.round(baseRate + distanceFee),
    weightFee: Math.round(weightFee),
    specialFee,
    discount: Math.round(discount),
    totalPrice: Math.round(subtotal - discount)
  };
};

export const mockOrders: Order[] = [
  {
    id: 'ORD-2024-8392',
    createTime: format(new Date(), 'yyyy-MM-dd HH:mm'),
    status: 'shipping',
    cargoInfo: { name: '办公椅套装', type: 'furniture', quantity: 5, weight: 45 },
    route: { pickup: '成都市锦江区春熙路', delivery: '成都市双流区西航港' },
    pricing: { totalPrice: 340, paymentMethod: 'online' }
  },
  {
    id: 'ORD-2024-8391',
    createTime: format(subDays(new Date(), 1), 'yyyy-MM-dd HH:mm'),
    status: 'completed',
    cargoInfo: { name: '有机蔬菜配送', type: 'food', quantity: 10, weight: 12 },
    route: { pickup: '成都市龙泉驿区', delivery: '成都市高新区天府大道' },
    pricing: { totalPrice: 85, paymentMethod: 'monthly' }
  },
  {
    id: 'ORD-2024-8388',
    createTime: format(subDays(new Date(), 3), 'yyyy-MM-dd HH:mm'),
    status: 'pending',
    cargoInfo: { name: '电子配件', type: 'electronics', quantity: 200, weight: 5 },
    route: { pickup: '重庆市渝北区', delivery: '成都市武侯区' },
    pricing: { totalPrice: 120, paymentMethod: 'online' }
  }
];