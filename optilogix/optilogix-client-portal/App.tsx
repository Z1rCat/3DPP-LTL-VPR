import React, { useState } from 'react';
import { PackageSearch, Clock, HeadphonesIcon, LogOut, Menu, Bell } from 'lucide-react';
import Dashboard from './components/Dashboard';
import OrderWizard from './components/OrderWizard';
import OrderTracking from './components/OrderTracking';
import SupportChat from './components/SupportChat';
import { ViewState } from './types';
import { mockOrders } from './utils';

const App: React.FC = () => {
  const [currentView, setCurrentView] = useState<ViewState>('dashboard');
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  // Navigation Handler
  const navigateTo = (view: ViewState) => {
    setCurrentView(view);
    setIsMobileMenuOpen(false);
    window.scrollTo(0, 0);
  };

  const renderContent = () => {
    switch (currentView) {
      case 'order-wizard':
        return <OrderWizard onComplete={() => navigateTo('dashboard')} onCancel={() => navigateTo('dashboard')} />;
      case 'tracking':
        return <OrderTracking />;
      case 'history':
        return (
          <div className="animate-in fade-in">
            <h2 className="text-2xl font-bold text-slate-800 mb-6">历史订单</h2>
            <div className="bg-white p-8 rounded-xl border border-slate-200 text-center text-slate-500">
              暂无更多历史记录，功能演示中...
            </div>
          </div>
        );
      case 'dashboard':
      default:
        return <Dashboard onNavigate={navigateTo} orders={mockOrders} />;
    }
  };

  return (
    <div className="min-h-screen bg-[#f8fafc]">
      {/* Top Navbar */}
      <nav className="bg-white border-b border-slate-200 sticky top-0 z-40 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            {/* Left Logo & Brand */}
            <div className="flex items-center cursor-pointer" onClick={() => navigateTo('dashboard')}>
              <div className="w-8 h-8 bg-gradient-to-br from-tech-blue to-blue-600 rounded-lg flex items-center justify-center text-white font-bold mr-2">
                OL
              </div>
              <span className="text-xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-tech-blue to-blue-800">
                OptiLogix <span className="text-slate-400 font-normal text-sm">Client</span>
              </span>
            </div>

            {/* Desktop Nav */}
            <div className="hidden md:flex items-center space-x-8">
              <button 
                onClick={() => navigateTo('dashboard')}
                className={`text-sm font-medium transition-colors ${currentView === 'dashboard' ? 'text-tech-blue' : 'text-slate-600 hover:text-tech-blue'}`}
              >
                首页
              </button>
              <button 
                onClick={() => navigateTo('tracking')}
                className={`flex items-center gap-1 text-sm font-medium transition-colors ${currentView === 'tracking' ? 'text-tech-blue' : 'text-slate-600 hover:text-tech-blue'}`}
              >
                <PackageSearch className="w-4 h-4" /> 订单追踪
              </button>
              <button 
                onClick={() => navigateTo('history')}
                className={`flex items-center gap-1 text-sm font-medium transition-colors ${currentView === 'history' ? 'text-tech-blue' : 'text-slate-600 hover:text-tech-blue'}`}
              >
                <Clock className="w-4 h-4" /> 历史订单
              </button>
            </div>

            {/* Right User Actions */}
            <div className="flex items-center gap-4">
              <button className="relative p-2 text-slate-400 hover:text-slate-600 transition-colors">
                <Bell className="w-5 h-5" />
                <span className="absolute top-1.5 right-1.5 w-2 h-2 bg-red-500 rounded-full border border-white"></span>
              </button>
              
              <div className="hidden md:flex items-center gap-3 pl-4 border-l border-slate-200">
                <div className="text-right">
                  <div className="text-sm font-bold text-slate-700">王先生</div>
                  <div className="text-xs text-slate-400">VIP 客户</div>
                </div>
                <div className="w-8 h-8 rounded-full bg-gradient-to-r from-[#ff7a45] to-[#fa541c] flex items-center justify-center text-white font-bold text-xs shadow-sm">
                  W
                </div>
              </div>

              {/* Mobile Menu Button */}
              <button 
                className="md:hidden p-2 text-slate-600"
                onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
              >
                <Menu className="w-6 h-6" />
              </button>
            </div>
          </div>
        </div>

        {/* Mobile Menu Dropdown */}
        {isMobileMenuOpen && (
          <div className="md:hidden border-t border-slate-100 bg-white p-4 space-y-4 animate-in slide-in-from-top-2">
             <button onClick={() => navigateTo('dashboard')} className="block w-full text-left py-2 font-medium text-slate-600">首页</button>
             <button onClick={() => navigateTo('tracking')} className="block w-full text-left py-2 font-medium text-slate-600">订单追踪</button>
             <button onClick={() => navigateTo('history')} className="block w-full text-left py-2 font-medium text-slate-600">历史订单</button>
             <div className="border-t border-slate-100 pt-4 flex items-center gap-3">
                <div className="w-8 h-8 rounded-full bg-orange-100 flex items-center justify-center text-orange-600 font-bold">W</div>
                <span className="text-sm font-bold">王先生</span>
                <button className="ml-auto text-slate-400"><LogOut className="w-5 h-5" /></button>
             </div>
          </div>
        )}
      </nav>

      {/* Main Content Area */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {renderContent()}
      </main>

      {/* Global Support Widget */}
      <SupportChat />
    </div>
  );
};

export default App;
