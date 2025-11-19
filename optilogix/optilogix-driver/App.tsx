import React from 'react';
import { HashRouter, Routes, Route, useLocation } from 'react-router-dom';
import MobileHeader from './components/MobileHeader';
import BottomNavigation from './components/BottomNavigation';
import Dashboard from './pages/Dashboard';
import TaskList from './pages/TaskList';
import LoadingPlan3D from './pages/LoadingPlan3D';
import RouteMap from './pages/RouteMap';
import Profile from './pages/Profile';

const Layout: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const location = useLocation();
  // Hide header on Map view for full immersion
  const showHeader = location.pathname !== '/route';

  return (
    <div className="font-sans antialiased text-slate-900 bg-f0f2f5 min-h-screen selection:bg-blue-100">
      {showHeader && <MobileHeader />}
      <main>
        {children}
      </main>
      <BottomNavigation />
    </div>
  );
};

const App: React.FC = () => {
  return (
    <HashRouter>
      <Layout>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/tasks" element={<TaskList />} />
          <Route path="/loading" element={<LoadingPlan3D />} />
          <Route path="/route" element={<RouteMap />} />
          <Route path="/profile" element={<Profile />} />
        </Routes>
      </Layout>
    </HashRouter>
  );
};

export default App;