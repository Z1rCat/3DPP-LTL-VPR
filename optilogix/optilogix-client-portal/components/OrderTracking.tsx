import React from 'react';
import { Package, Truck, Home, CheckCircle2, Map } from 'lucide-react';
import { Order } from '../types';

const timeline = [
  { time: '09:00', title: '订单已创建', status: 'done', desc: '订单已成功提交，等待系统确认' },
  { time: '09:15', title: '订单已确认', status: 'done', desc: '系统已接单，正在分配最近的司机' },
  { time: '09:45', title: '司机已取货', status: 'done', desc: '司机 王师傅 (138****1234) 已揽件' },
  { time: '10:30', title: '运输中', status: 'current', desc: '车辆正在前往目的地，距您约 15km' },
  { time: '11:45', title: '预计送达', status: 'pending', desc: '预计今日中午送达' },
];

const OrderTracking: React.FC = () => {
  return (
    <div className="max-w-5xl mx-auto grid grid-cols-1 lg:grid-cols-3 gap-6 animate-in fade-in">
      {/* Left Column: Status & Map */}
      <div className="lg:col-span-2 space-y-6">
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
          <div className="p-6 border-b border-slate-100 flex justify-between items-center">
            <div>
              <h2 className="text-xl font-bold text-slate-800">订单 #ORD-2024-8392</h2>
              <p className="text-slate-500 text-sm">预计送达: 今日 11:45</p>
            </div>
            <span className="bg-blue-50 text-tech-blue px-3 py-1 rounded-full text-sm font-bold">
              运输中
            </span>
          </div>
          
          {/* Mock Map */}
          <div className="h-64 bg-slate-100 relative flex items-center justify-center">
             <div className="absolute inset-0 bg-[url('https://api.placeholder.com/maps')] opacity-50"></div>
             <div className="text-slate-400 flex flex-col items-center gap-2 relative z-10">
               <Map className="w-8 h-8" />
               <span>实时地图加载中...</span>
             </div>
             {/* Simulated Route Line */}
             <div className="absolute left-1/4 top-1/2 w-1/2 h-1 bg-tech-blue/20 rounded-full"></div>
             <div className="absolute left-1/2 top-1/2 w-4 h-4 bg-tech-blue rounded-full border-4 border-white shadow-lg transform -translate-x-1/2 -translate-y-1/2 animate-pulse"></div>
          </div>

          <div className="p-6">
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 rounded-full bg-slate-100 overflow-hidden">
                <img src="https://picsum.photos/200" alt="Driver" className="w-full h-full object-cover" />
              </div>
              <div>
                <div className="font-bold text-slate-800">王师傅</div>
                <div className="text-sm text-slate-500">金牌司机 • 4.9分 • 川A·88***</div>
              </div>
              <button className="ml-auto border border-slate-200 hover:bg-slate-50 px-4 py-2 rounded-lg text-sm font-medium transition-colors">
                联系司机
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Right Column: Timeline */}
      <div className="lg:col-span-1">
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6 h-full">
          <h3 className="font-bold text-slate-800 mb-6">物流详情</h3>
          
          <div className="relative space-y-8">
            <div className="absolute left-3 top-2 bottom-2 w-0.5 bg-slate-100"></div>
            
            {timeline.map((item, index) => (
              <div key={index} className="relative pl-10 group">
                <div className={`absolute left-0 top-1 w-6 h-6 rounded-full border-2 flex items-center justify-center bg-white z-10
                  ${item.status === 'done' ? 'border-tech-emerald text-tech-emerald' : 
                    item.status === 'current' ? 'border-tech-blue text-tech-blue animate-pulse' : 
                    'border-slate-300 text-slate-300'}`}>
                  {item.status === 'done' ? <CheckCircle2 className="w-3 h-3" /> : 
                   item.status === 'current' ? <Truck className="w-3 h-3" /> :
                   <div className="w-2 h-2 rounded-full bg-slate-300" />}
                </div>
                
                <div>
                  <div className="text-xs text-slate-400 mb-0.5 font-mono">{item.time}</div>
                  <div className={`font-bold text-sm mb-1 ${item.status === 'current' ? 'text-tech-blue' : 'text-slate-800'}`}>
                    {item.title}
                  </div>
                  <div className="text-xs text-slate-500 leading-relaxed">
                    {item.desc}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default OrderTracking;