import React from 'react';
import { Clock, MapPin, Package, ChevronRight } from 'lucide-react';
import { Task } from '../types';

interface Props {
  tasks: Task[];
}

const TaskTimeline: React.FC<Props> = ({ tasks }) => {
  const getStatusColor = (status: Task['status']) => {
    switch (status) {
      case 'completed': return 'border-l-tech-emerald bg-gradient-to-r from-emerald-50 to-white';
      case 'active': return 'border-l-tech-blue bg-gradient-to-r from-blue-50 to-white';
      case 'urgent': return 'border-l-tech-red bg-gradient-to-r from-red-50 to-white';
      default: return 'border-l-tech-amber bg-gradient-to-r from-amber-50 to-white';
    }
  };

  const getIconColor = (status: Task['status']) => {
    switch (status) {
      case 'completed': return 'text-tech-emerald bg-emerald-100';
      case 'active': return 'text-tech-blue bg-blue-100';
      case 'urgent': return 'text-tech-red bg-red-100';
      default: return 'text-tech-amber bg-amber-100';
    }
  };

  return (
    <div className="space-y-4 pl-2">
      {tasks.map((task, index) => (
        <div key={task.id} className="relative flex gap-4 animate-in slide-in-from-bottom-4 fade-in duration-500" style={{ animationDelay: `${index * 100}ms` }}>
          
          {/* Time Column */}
          <div className="flex flex-col items-end min-w-[50px] pt-1">
            <span className={`text-sm font-bold ${task.status === 'active' ? 'text-tech-blue' : 'text-slate-900'}`}>
              {task.time}
            </span>
            <span className="text-[10px] text-slate-400">
              {task.type === 'REST' ? '休息' : '工作'}
            </span>
          </div>

          {/* Timeline Line & Node */}
          <div className="relative flex flex-col items-center">
            <div className={`w-3 h-3 rounded-full z-10 ring-2 ring-white ${
              task.status === 'completed' ? 'bg-tech-emerald' : 
              task.status === 'active' ? 'bg-tech-blue animate-pulse' : 'bg-slate-300'
            }`} />
            {index !== tasks.length - 1 && (
              <div className="absolute top-3 w-0.5 h-[calc(100%+1rem)] bg-slate-200 -z-0" />
            )}
          </div>

          {/* Task Card */}
          <div className={`flex-1 rounded-lg p-4 border-l-4 shadow-sm mb-2 active:scale-[0.98] transition-transform touch-manipulation ${getStatusColor(task.status)}`}>
            <div className="flex justify-between items-start mb-2">
              <h3 className="text-base font-bold text-slate-800">{task.title}</h3>
              {task.status === 'active' && (
                 <span className="px-2 py-0.5 bg-blue-500 text-white text-[10px] rounded-full font-medium">
                   进行中
                 </span>
              )}
            </div>
            
            <div className="space-y-2">
              <div className="flex items-center gap-2 text-slate-600 text-sm">
                <MapPin className="w-4 h-4 shrink-0 text-slate-400" />
                <span className="truncate">{task.location}</span>
              </div>
              
              {task.cargo && (
                <div className="flex items-center gap-2 text-slate-500 text-xs bg-white/50 p-2 rounded">
                  <Package className="w-3 h-3 shrink-0" />
                  <span>{task.cargo.length} 件货物 • {task.cargo.reduce((acc, c) => acc + c.weight, 0)}kg</span>
                </div>
              )}
            </div>

            {task.status === 'active' && (
              <div className="mt-3 pt-3 border-t border-blue-100/50 flex gap-2">
                 <button className="flex-1 bg-tech-blue text-white text-xs font-medium py-2 rounded-lg shadow-sm active:bg-blue-700">
                   签到打卡
                 </button>
                 <button className="flex items-center justify-center w-8 h-8 rounded-lg bg-white text-tech-blue border border-blue-100">
                   <ChevronRight className="w-4 h-4" />
                 </button>
              </div>
            )}
          </div>
        </div>
      ))}
    </div>
  );
};

export default TaskTimeline;