import React from 'react';
import { NavLink } from 'react-router-dom';
import { Home, Calendar, Package, Map as MapIcon, User } from 'lucide-react';

const BottomNavigation: React.FC = () => {
  const navItems = [
    { path: '/', icon: Home, label: '首页' },
    { path: '/tasks', icon: Calendar, label: '任务' },
    { path: '/loading', icon: Package, label: '装载' },
    { path: '/route', icon: MapIcon, label: '导航' },
    { path: '/profile', icon: User, label: '我的' },
  ];

  return (
    <nav className="fixed bottom-0 left-0 right-0 z-50 bg-white border-t border-slate-200 pb-safe-bottom shadow-nav h-[64px] box-content">
      <div className="flex items-center justify-around h-full w-full max-w-md mx-auto">
        {navItems.map((item) => (
          <NavLink
            key={item.path}
            to={item.path}
            className={({ isActive }) => `
              flex flex-col items-center justify-center w-full h-full gap-1
              transition-all duration-200 active:scale-90
              ${isActive ? 'text-tech-blue' : 'text-tech-slate'}
            `}
          >
            {({ isActive }) => (
              <>
                <item.icon 
                  className={`w-6 h-6 ${isActive ? 'stroke-[2.5px]' : 'stroke-2'}`} 
                />
                <span className={`text-[10px] font-medium ${isActive ? 'text-tech-blue' : 'text-slate-500'}`}>
                  {item.label}
                </span>
              </>
            )}
          </NavLink>
        ))}
      </div>
    </nav>
  );
};

export default BottomNavigation;