import React from 'react';
import { Phone, Signal, Truck } from 'lucide-react';

const MobileHeader: React.FC = () => {
  return (
    <header className="fixed top-0 left-0 right-0 z-50 bg-gradient-to-r from-tech-blue to-blue-600 text-white shadow-md pt-safe-top">
      <div className="h-[60px] px-4 flex items-center justify-between">
        {/* Left: Vehicle Status */}
        <div className="flex items-center gap-3">
          <div className="bg-white/20 p-2 rounded-full backdrop-blur-sm">
            <Truck className="w-5 h-5" />
          </div>
          <div>
            <div className="font-bold text-base">川A·88888</div>
            <div className="flex items-center gap-1 text-xs text-blue-100">
              <span className="inline-block w-2 h-2 rounded-full bg-tech-emerald animate-pulse"></span>
              运输中
            </div>
          </div>
        </div>

        {/* Center: Online Status (Visual only for mobile) */}
        <div className="hidden sm:flex flex-col items-center">
           <span className="text-xs font-medium opacity-90">系统在线</span>
           <Signal className="w-4 h-4" />
        </div>

        {/* Right: Emergency Contact */}
        <button 
          className="flex items-center gap-2 bg-red-500/20 hover:bg-red-500/30 active:scale-95 transition-all border border-red-200/30 px-3 py-1.5 rounded-full backdrop-blur-md"
          onClick={() => alert("拨打调度中心紧急电话?")}
        >
          <Phone className="w-4 h-4" />
          <span className="text-xs font-bold">一键求助</span>
        </button>
      </div>
    </header>
  );
};

export default MobileHeader;