import React from 'react';
import { Utensils, ShoppingBag, Laptop, Sofa, Truck, Clock, TrendingUp, ArrowRight } from 'lucide-react';
import { CargoType, Order } from '../types';
import { formatCurrency } from '../utils';

interface DashboardProps {
  onNavigate: (view: any) => void;
  orders: Order[];
}

const cargoTypes: CargoType[] = [
  {
    id: 'food',
    name: '食品生鲜',
    icon: Utensils,
    color: 'bg-emerald-100 text-emerald-600',
    description: '冷链保鲜，极速送达',
    quickOrder: { defaultWeight: 50, defaultVolume: 0.5, estimatedPrice: 120, estimatedTime: '24h' }
  },
  {
    id: 'daily',
    name: '日用品',
    icon: ShoppingBag,
    color: 'bg-blue-100 text-blue-600',
    description: '商超配送，安全准时',
    quickOrder: { defaultWeight: 20, defaultVolume: 0.2, estimatedPrice: 45, estimatedTime: '2-3天' }
  },
  {
    id: 'electronics',
    name: '电子产品',
    icon: Laptop,
    color: 'bg-purple-100 text-purple-600',
    description: '防震包装，高价保险',
    quickOrder: { defaultWeight: 5, defaultVolume: 0.1, estimatedPrice: 80, estimatedTime: '48h' }
  },
  {
    id: 'furniture',
    name: '家具家装',
    icon: Sofa,
    color: 'bg-orange-100 text-orange-600',
    description: '大件搬运，上门安装',
    quickOrder: { defaultWeight: 150, defaultVolume: 2.5, estimatedPrice: 450, estimatedTime: '3-5天' }
  }
];

const Dashboard: React.FC<DashboardProps> = ({ onNavigate, orders }) => {
  return (
    <div className="space-y-8 animate-in fade-in duration-500">
      {/* Welcome Banner */}
      <div className="relative overflow-hidden rounded-2xl bg-gradient-to-r from-[#ff7a45] to-[#fa541c] p-8 text-white shadow-lg">
        <div className="relative z-10">
          <h1 className="text-3xl font-bold mb-2">👋 欢迎回来，王先生</h1>
          <p className="text-white/90 text-lg mb-6">今日物流运力充足，现在下单预计最快 2 小时内上门取件。</p>
          
          <div className="flex flex-wrap gap-4">
            <div className="bg-white/10 backdrop-blur-md rounded-lg p-4 min-w-[160px] border border-white/20">
              <div className="text-sm text-white/80 mb-1">待处理订单</div>
              <div className="text-3xl font-bold font-mono">2</div>
            </div>
            <div className="bg-white/10 backdrop-blur-md rounded-lg p-4 min-w-[160px] border border-white/20">
              <div className="text-sm text-white/80 mb-1">本月消费</div>
              <div className="text-3xl font-bold font-mono">¥4,580</div>
            </div>
            <div className="bg-white/10 backdrop-blur-md rounded-lg p-4 border border-white/20 flex flex-col justify-center">
              <div className="text-xs bg-white/20 px-2 py-1 rounded inline-block self-start mb-2">今日特惠</div>
              <div className="font-medium">同城专车 8.8 折优惠券</div>
            </div>
          </div>

          <button 
            onClick={() => onNavigate('order-wizard')}
            className="mt-8 bg-white text-[#fa541c] hover:bg-orange-50 px-8 py-3 rounded-lg font-bold shadow-sm transition-all active:scale-95 flex items-center gap-2"
          >
            <Truck className="w-5 h-5" />
            立即下单
          </button>
        </div>
        
        {/* Decorative background pattern */}
        <div className="absolute right-0 top-0 h-full w-1/3 bg-gradient-to-l from-white/10 to-transparent transform skew-x-12" />
        <div className="absolute -bottom-12 -right-12 w-64 h-64 bg-white/10 rounded-full blur-3xl" />
      </div>

      {/* Quick Order Grid */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-bold text-slate-800">快速下单</h2>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {cargoTypes.map((type) => (
            <div 
              key={type.id}
              onClick={() => onNavigate('order-wizard')}
              className="group bg-white p-6 rounded-xl border border-slate-200 shadow-sm hover:shadow-md hover:border-[#ff7a45]/30 transition-all cursor-pointer relative overflow-hidden"
            >
              <div className={`w-12 h-12 rounded-full flex items-center justify-center mb-4 ${type.color} transition-transform group-hover:scale-110`}>
                <type.icon className="w-6 h-6" />
              </div>
              <h3 className="text-lg font-bold text-slate-800 mb-1">{type.name}</h3>
              <p className="text-sm text-slate-500 mb-4">{type.description}</p>
              <div className="flex items-center text-xs text-slate-400 font-mono">
                预估 {formatCurrency(type.quickOrder.estimatedPrice)}起
              </div>
              <div className="absolute bottom-4 right-4 opacity-0 group-hover:opacity-100 transition-opacity transform translate-x-2 group-hover:translate-x-0">
                <div className="bg-[#ff7a45] text-white p-2 rounded-full shadow-lg">
                  <ArrowRight className="w-4 h-4" />
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Recent Orders */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-bold text-slate-800">最近订单</h2>
          <button onClick={() => onNavigate('history')} className="text-[#1890ff] text-sm font-medium hover:underline flex items-center gap-1">
            查看全部 <ArrowRight className="w-4 h-4" />
          </button>
        </div>
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
          {orders.slice(0, 3).map((order, idx) => (
            <div key={order.id} className={`p-4 flex items-center justify-between hover:bg-slate-50 transition-colors ${idx !== orders.length - 1 ? 'border-b border-slate-100' : ''}`}>
              <div className="flex items-center gap-4">
                <div className={`p-3 rounded-lg ${
                  order.status === 'completed' ? 'bg-tech-emerald/10 text-tech-emerald' :
                  order.status === 'shipping' ? 'bg-status-shipping/10 text-status-shipping' :
                  'bg-status-pending/10 text-status-pending'
                }`}>
                  {order.status === 'shipping' ? <Truck className="w-5 h-5" /> : 
                   order.status === 'completed' ? <TrendingUp className="w-5 h-5" /> : 
                   <Clock className="w-5 h-5" />}
                </div>
                <div>
                  <div className="font-medium text-slate-800">{order.cargoInfo.name}</div>
                  <div className="text-xs text-slate-500 font-mono">{order.id} • {order.createTime}</div>
                </div>
              </div>
              <div className="flex flex-col items-end gap-1">
                 <span className={`px-2 py-1 rounded text-[10px] font-medium uppercase
                  ${order.status === 'completed' ? 'bg-green-100 text-green-700' : 
                    order.status === 'shipping' ? 'bg-cyan-100 text-cyan-700' : 
                    'bg-amber-100 text-amber-700'}`}>
                  {order.status === 'shipping' ? '配送中' : order.status === 'completed' ? '已完成' : '处理中'}
                </span>
                <span className="font-mono text-sm font-bold">{formatCurrency(order.pricing.totalPrice)}</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
