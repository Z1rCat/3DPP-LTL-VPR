import React from 'react';
import { User, Shield, Settings, LogOut, ChevronRight, Phone, Award, FileText } from 'lucide-react';
import { MOCK_DRIVER } from '../constants';

const Profile: React.FC = () => {
  return (
    <div className="min-h-screen bg-slate-50 pt-safe-top pb-24">
      
      {/* Header Background */}
      <div className="bg-tech-blue h-40 relative">
        <div className="absolute bottom-0 left-0 right-0 h-6 bg-slate-50 rounded-t-3xl"></div>
      </div>

      {/* Profile Card */}
      <div className="px-4 -mt-16 relative z-10">
        <div className="bg-white rounded-2xl shadow-card p-6 flex flex-col items-center">
           <div className="w-20 h-20 rounded-full bg-slate-200 border-4 border-white shadow-md -mt-12 mb-3 overflow-hidden">
             <img src={MOCK_DRIVER.avatar} alt="Avatar" className="w-full h-full object-cover" />
           </div>
           <h2 className="text-xl font-bold text-slate-900">{MOCK_DRIVER.name}</h2>
           <p className="text-sm text-slate-500 mb-4">工号: {MOCK_DRIVER.id} | 驾龄 5年</p>
           
           <div className="grid grid-cols-3 w-full border-t border-slate-100 pt-4 gap-4">
              <div className="text-center">
                <div className="text-lg font-bold text-slate-800">{MOCK_DRIVER.stats.efficiency}</div>
                <div className="text-xs text-slate-500">效率分</div>
              </div>
              <div className="text-center border-l border-r border-slate-100">
                <div className="text-lg font-bold text-slate-800">100%</div>
                <div className="text-xs text-slate-500">准点率</div>
              </div>
              <div className="text-center">
                <div className="text-lg font-bold text-slate-800">0</div>
                <div className="text-xs text-slate-500">事故</div>
              </div>
           </div>
        </div>
      </div>

      {/* Menu Groups */}
      <div className="px-4 mt-6 space-y-4">
        
        <div className="bg-white rounded-xl shadow-sm overflow-hidden">
           <MenuItem icon={Phone} label="联系调度中心" />
           <div className="h-[1px] bg-slate-50 mx-4"></div>
           <MenuItem icon={FileText} label="工作记录" />
           <div className="h-[1px] bg-slate-50 mx-4"></div>
           <MenuItem icon={Award} label="绩效考核" value="A+" />
        </div>

        <div className="bg-white rounded-xl shadow-sm overflow-hidden">
           <MenuItem icon={Shield} label="隐私与安全" />
           <div className="h-[1px] bg-slate-50 mx-4"></div>
           <MenuItem icon={Settings} label="系统设置" />
        </div>

        <button className="w-full bg-white text-tech-red font-medium py-4 rounded-xl shadow-sm flex items-center justify-center gap-2 active:bg-red-50">
           <LogOut className="w-5 h-5" />
           退出登录
        </button>
        
        <p className="text-center text-xs text-slate-400 pt-4">OptiLogix Driver v1.0.2</p>

      </div>
    </div>
  );
};

const MenuItem = ({ icon: Icon, label, value }: any) => (
  <button className="w-full flex items-center justify-between p-4 active:bg-slate-50 transition-colors">
    <div className="flex items-center gap-3">
      <div className="p-2 bg-slate-100 rounded-lg text-slate-600">
        <Icon className="w-5 h-5" />
      </div>
      <span className="text-sm font-medium text-slate-700">{label}</span>
    </div>
    <div className="flex items-center gap-2">
      {value && <span className="text-sm font-bold text-tech-blue">{value}</span>}
      <ChevronRight className="w-4 h-4 text-slate-300" />
    </div>
  </button>
);

export default Profile;