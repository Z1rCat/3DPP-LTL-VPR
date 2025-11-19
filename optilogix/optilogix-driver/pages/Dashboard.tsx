import React from 'react';
import { PieChart, Clock, TrendingUp, Navigation } from 'lucide-react';
import TaskTimeline from '../components/TaskTimeline';
import { MOCK_TASKS, MOCK_DRIVER, MOCK_VEHICLE } from '../constants';

const Dashboard: React.FC = () => {
  return (
    <div className="min-h-screen bg-tech-light pb-24">
      
      {/* Summary Swiper Section */}
      <div className="pt-20 px-4 mb-6">
        <h2 className="text-lg font-bold text-slate-800 mb-3 flex items-center gap-2">
          今日概览 <span className="text-xs font-normal text-slate-500 bg-white px-2 py-0.5 rounded-full">Swipe</span>
        </h2>
        
        <div className="flex overflow-x-auto snap-x-mandatory no-scrollbar gap-4 pb-4 -mx-4 px-4">
          
          {/* Card 1: Task Stats */}
          <div className="snap-center shrink-0 w-[85vw] max-w-[350px] bg-white rounded-2xl p-5 shadow-card border border-slate-100 relative overflow-hidden">
            <div className="absolute right-0 top-0 p-4 opacity-5">
              <PieChart className="w-32 h-32" />
            </div>
            <div className="relative z-10">
               <div className="flex items-center gap-2 mb-4">
                 <div className="p-2 bg-blue-50 rounded-lg">
                   <PieChart className="w-5 h-5 text-tech-blue" />
                 </div>
                 <span className="font-semibold text-slate-700">任务统计</span>
               </div>
               <div className="flex justify-between items-end">
                 <div>
                   <div className="text-3xl font-bold text-slate-900">{MOCK_DRIVER.stats.completedTasks}<span className="text-lg text-slate-400">/{MOCK_DRIVER.stats.todayTasks}</span></div>
                   <div className="text-xs text-slate-500 mt-1">已完成 / 总任务</div>
                 </div>
                 <div className="text-right">
                   <div className="text-2xl font-bold text-tech-emerald">37.5%</div>
                   <div className="text-xs text-tech-emerald bg-emerald-50 px-2 py-0.5 rounded-full mt-1">进度良好</div>
                 </div>
               </div>
               {/* Mini Progress Bar */}
               <div className="w-full bg-slate-100 h-2 rounded-full mt-4 overflow-hidden">
                 <div className="bg-tech-blue h-full rounded-full" style={{ width: '37.5%' }}></div>
               </div>
            </div>
          </div>

          {/* Card 2: Efficiency */}
          <div className="snap-center shrink-0 w-[85vw] max-w-[350px] bg-white rounded-2xl p-5 shadow-card border border-slate-100 relative overflow-hidden">
             <div className="absolute right-0 top-0 p-4 opacity-5">
              <TrendingUp className="w-32 h-32" />
            </div>
            <div className="relative z-10">
               <div className="flex items-center gap-2 mb-4">
                 <div className="p-2 bg-amber-50 rounded-lg">
                   <Clock className="w-5 h-5 text-tech-amber" />
                 </div>
                 <span className="font-semibold text-slate-700">时效统计</span>
               </div>
               <div className="grid grid-cols-2 gap-4">
                 <div>
                   <div className="text-sm text-slate-500">计划工时</div>
                   <div className="text-xl font-bold text-slate-800">8h</div>
                 </div>
                 <div>
                   <div className="text-sm text-slate-500">已运行时长</div>
                   <div className="text-xl font-bold text-tech-blue">4.5h</div>
                 </div>
                 <div>
                   <div className="text-sm text-slate-500">预计完成</div>
                   <div className="text-xl font-bold text-slate-800">18:30</div>
                 </div>
                 <div>
                    <div className="text-sm text-slate-500">效率评分</div>
                    <div className="text-xl font-bold text-tech-emerald">98</div>
                 </div>
               </div>
            </div>
          </div>

           {/* Card 3: Vehicle */}
           <div className="snap-center shrink-0 w-[85vw] max-w-[350px] bg-white rounded-2xl p-5 shadow-card border border-slate-100">
            <div className="flex items-center gap-2 mb-4">
                 <div className="p-2 bg-emerald-50 rounded-lg">
                   <TrendingUp className="w-5 h-5 text-tech-emerald" />
                 </div>
                 <span className="font-semibold text-slate-700">车辆装载</span>
               </div>
               <div className="space-y-3">
                 <div>
                   <div className="flex justify-between text-sm mb-1">
                     <span className="text-slate-500">载重 (15吨)</span>
                     <span className="font-bold text-slate-700">80%</span>
                   </div>
                   <div className="w-full bg-slate-100 h-2 rounded-full overflow-hidden">
                     <div className="bg-tech-blue h-full rounded-full" style={{ width: '80%' }}></div>
                   </div>
                 </div>
                 <div>
                   <div className="flex justify-between text-sm mb-1">
                     <span className="text-slate-500">容积 (45m³)</span>
                     <span className="font-bold text-slate-700">65%</span>
                   </div>
                   <div className="w-full bg-slate-100 h-2 rounded-full overflow-hidden">
                     <div className="bg-purple-500 h-full rounded-full" style={{ width: '65%' }}></div>
                   </div>
                 </div>
               </div>
          </div>

        </div>
      </div>

      {/* Timeline Section */}
      <div className="px-4">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-bold text-slate-800">今日任务</h2>
          <span className="text-xs text-tech-blue font-medium bg-blue-50 px-2 py-1 rounded">
            共 {MOCK_TASKS.length} 项
          </span>
        </div>
        <div className="bg-white rounded-2xl p-4 shadow-sm border border-slate-100">
           <TaskTimeline tasks={MOCK_TASKS} />
        </div>
      </div>

      {/* Floating Quick Action - Only visible on Dashboard */}
      <button className="fixed bottom-24 right-4 w-12 h-12 bg-slate-900 text-white rounded-full shadow-lg flex items-center justify-center z-40 active:scale-90 transition-transform">
        <Navigation className="w-5 h-5" />
      </button>
    </div>
  );
};

export default Dashboard;