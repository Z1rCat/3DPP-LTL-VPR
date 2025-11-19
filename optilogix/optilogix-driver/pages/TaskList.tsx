import React, { useState } from 'react';
import { Search, Filter, CheckCircle2, Clock, AlertCircle } from 'lucide-react';
import TaskTimeline from '../components/TaskTimeline';
import { MOCK_TASKS } from '../constants';

const TaskList: React.FC = () => {
  const [filter, setFilter] = useState<'ALL' | 'PENDING' | 'COMPLETED'>('ALL');

  const filteredTasks = MOCK_TASKS.filter(task => {
    if (filter === 'ALL') return true;
    if (filter === 'COMPLETED') return task.status === 'completed';
    return task.status !== 'completed';
  });

  return (
    <div className="min-h-screen bg-tech-light pt-20 pb-24 px-4">
      <h1 className="text-xl font-bold text-slate-900 mb-4">任务管理</h1>

      {/* Search & Filter */}
      <div className="flex gap-3 mb-6">
        <div className="flex-1 relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
          <input 
            type="text" 
            placeholder="搜索任务号、地址..." 
            className="w-full pl-9 pr-4 py-2.5 bg-white border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-tech-blue"
          />
        </div>
        <button className="bg-white px-3 rounded-xl border border-slate-200 text-slate-600">
          <Filter className="w-5 h-5" />
        </button>
      </div>

      {/* Tabs */}
      <div className="flex p-1 bg-slate-200/50 rounded-xl mb-6">
        {(['ALL', 'PENDING', 'COMPLETED'] as const).map((tab) => (
          <button
            key={tab}
            onClick={() => setFilter(tab)}
            className={`flex-1 py-2 text-xs font-bold rounded-lg transition-all ${
              filter === tab 
                ? 'bg-white text-tech-blue shadow-sm' 
                : 'text-slate-500 hover:text-slate-700'
            }`}
          >
            {tab === 'ALL' ? '全部' : tab === 'PENDING' ? '待执行' : '已完成'}
          </button>
        ))}
      </div>

      {/* Stats Summary */}
      <div className="grid grid-cols-3 gap-3 mb-6">
         <div className="bg-blue-50 p-3 rounded-xl border border-blue-100 flex flex-col items-center justify-center text-center">
            <div className="text-tech-blue font-bold text-lg">8</div>
            <div className="text-[10px] text-blue-600 font-medium">今日总量</div>
         </div>
         <div className="bg-emerald-50 p-3 rounded-xl border border-emerald-100 flex flex-col items-center justify-center text-center">
            <div className="text-tech-emerald font-bold text-lg">3</div>
            <div className="text-[10px] text-emerald-600 font-medium">已完成</div>
         </div>
         <div className="bg-amber-50 p-3 rounded-xl border border-amber-100 flex flex-col items-center justify-center text-center">
            <div className="text-tech-amber font-bold text-lg">1</div>
            <div className="text-[10px] text-amber-600 font-medium">进行中</div>
         </div>
      </div>

      {/* Task List */}
      <div className="bg-white rounded-2xl p-4 shadow-sm min-h-[300px]">
        <TaskTimeline tasks={filteredTasks} />
        
        {filteredTasks.length === 0 && (
           <div className="flex flex-col items-center justify-center py-10 text-slate-400">
             <CheckCircle2 className="w-12 h-12 mb-2 opacity-20" />
             <p className="text-sm">暂无相关任务</p>
           </div>
        )}
      </div>
    </div>
  );
};

export default TaskList;