import React, { useEffect, useRef, useState } from 'react';
import { RotateCcw, Menu, Mic, X, Navigation, MapPin, ArrowRight } from 'lucide-react';
import * as L from 'leaflet';
import { useNavigate } from 'react-router-dom';
import { MOCK_ROUTE } from '../constants';

// 定义成都的真实坐标路径点 (模拟从市中心到高新区的路径)
const CHENGDU_PATH: [number, number][] = [
  [30.6760, 104.0648], // 起点：附近天府广场
  [30.6600, 104.0650], // 沿人民南路南下
  [30.6400, 104.0660], // 继续南下
  [30.6200, 104.0700], // 接近二环
  [30.6000, 104.0710], // 上天府大道
  [30.5800, 104.0680], // 天府大道中段
  [30.5700, 104.0650], // 终点：高新区/软件园附近
];

// 模拟导航指令数据
const NAV_STEPS = [
  { id: 1, instruction: '从 天府广场 出发，向南行驶', distance: '500m', icon: Navigation },
  { id: 2, instruction: '进入 人民南路四段', distance: '2.5km', icon: ArrowRight },
  { id: 3, instruction: '靠左行驶进入 天府大道北段', distance: '5.8km', icon: ArrowRight },
  { id: 4, instruction: '前方路口直行', distance: '1.2km', icon: ArrowRight },
  { id: 5, instruction: '右转进入 世纪城路', distance: '800m', icon: RotateCcw },
  { id: 6, instruction: '到达目的地 天府软件园', distance: '0m', icon: MapPin },
];

const RouteMap: React.FC = () => {
  const navigate = useNavigate();
  const mapContainerRef = useRef<HTMLDivElement>(null);
  const mapInstanceRef = useRef<L.Map | null>(null);
  const truckMarkerRef = useRef<L.Marker | null>(null);
  
  // 交互状态
  const [showDetails, setShowDetails] = useState(false);
  const [isVoiceActive, setIsVoiceActive] = useState(false);

  useEffect(() => {
    if (!mapContainerRef.current) return;
    if (mapInstanceRef.current) return; // 防止重复初始化

    // 1. 初始化地图
    const map = L.map(mapContainerRef.current, {
      center: [30.62, 104.07],
      zoom: 13,
      zoomControl: false,
      attributionControl: true
    });

    mapInstanceRef.current = map;

    // 2. 添加瓦片图层
    L.tileLayer('https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png', {
      attribution: '&copy; OSM & Carto',
      subdomains: 'abcd',
      maxZoom: 20
    }).addTo(map);

    // 3. 绘制路径
    const routePolyline = L.polyline(CHENGDU_PATH, {
      color: '#1890ff',
      weight: 6,
      opacity: 0.8,
      lineJoin: 'round'
    }).addTo(map);

    map.fitBounds(routePolyline.getBounds(), { padding: [50, 50] });

    // 4. 自定义图标
    const truckIcon = L.divIcon({
      className: 'custom-truck-icon',
      html: `
        <div style="width: 40px; height: 40px; background: #1890ff; border: 2px solid white; border-radius: 50%; box-shadow: 0 4px 10px rgba(24,144,255,0.4); display: flex; align-items: center; justify-content: center; position: relative;">
          <div style="width: 60px; height: 60px; background: rgba(24,144,255,0.2); border-radius: 50%; position: absolute; animation: ping 1.5s cubic-bezier(0, 0, 0.2, 1) infinite;"></div>
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><polygon points="3 11 22 2 13 21 11 13 3 11"></polygon></svg>
          <style>@keyframes ping { 75%, 100% { transform: scale(2); opacity: 0; } }</style>
        </div>
      `,
      iconSize: [40, 40],
      iconAnchor: [20, 20]
    });

    const destIcon = L.divIcon({
      className: 'custom-dest-icon',
      html: `<div style="width: 24px; height: 24px; background: #ff4d4f; border: 2px solid white; border-radius: 50%; box-shadow: 0 2px 5px rgba(0,0,0,0.2);"></div>`,
      iconSize: [24, 24],
      iconAnchor: [12, 12]
    });

    // 5. 添加标记
    const currentPos = CHENGDU_PATH[3]; 
    truckMarkerRef.current = L.marker(currentPos, { icon: truckIcon, zIndexOffset: 1000 }).addTo(map);
    L.marker(CHENGDU_PATH[CHENGDU_PATH.length - 1], { icon: destIcon }).addTo(map);

    // 6. 模拟移动
    let step = 0;
    const interval = setInterval(() => {
      if (!mapInstanceRef.current || !truckMarkerRef.current) return;
      const p1 = CHENGDU_PATH[3];
      const p2 = CHENGDU_PATH[4];
      const factor = (Math.sin(Date.now() / 1000) + 1) / 2 * 0.1;
      const lat = p1[0] + (p2[0] - p1[0]) * factor;
      const lng = p1[1] + (p2[1] - p1[1]) * factor;
      truckMarkerRef.current.setLatLng([lat, lng]);
    }, 100);

    return () => {
      clearInterval(interval);
      map.remove();
      mapInstanceRef.current = null;
    };
  }, []);

  const handleVoiceToggle = () => {
    setIsVoiceActive(!isVoiceActive);
    // 模拟语音提示
    if (!isVoiceActive) {
      const msg = new SpeechSynthesisUtterance("前方200米左转进入天府大道辅路");
      msg.lang = 'zh-CN';
      window.speechSynthesis.speak(msg);
    } else {
      window.speechSynthesis.cancel();
    }
  };

  return (
    <div className="h-screen w-screen relative overflow-hidden bg-slate-100 flex flex-col">
      
      {/* Top Overlay */}
      <div className="absolute top-4 left-4 right-4 z-[1000]">
        <div className="bg-slate-900 text-white p-4 rounded-xl shadow-lg flex items-start gap-4 animate-in slide-in-from-top duration-500">
          <div className="bg-white/10 p-2 rounded-lg">
             <RotateCcw className="w-8 h-8 text-white" />
          </div>
          <div className="flex-1">
             <h2 className="text-2xl font-bold leading-none">200 米</h2>
             <p className="text-slate-300 text-sm mt-1">后左转进入 天府大道辅路</p>
          </div>
        </div>
      </div>

      {/* Map */}
      <div className="flex-1 relative z-0">
        <div ref={mapContainerRef} className="w-full h-full" id="leaflet-map"></div>
        
        {/* Zoom Controls */}
        <div className="absolute right-4 top-1/3 flex flex-col gap-3 z-[900]">
           <button onClick={() => mapInstanceRef.current?.zoomIn()} className="w-10 h-10 bg-white rounded-lg shadow-md flex items-center justify-center active:bg-slate-50 text-slate-700 border border-slate-200 font-bold text-xl">+</button>
           <button onClick={() => mapInstanceRef.current?.zoomOut()} className="w-10 h-10 bg-white rounded-lg shadow-md flex items-center justify-center active:bg-slate-50 text-slate-700 border border-slate-200 font-bold text-xl">-</button>
        </div>
      </div>

      {/* Bottom Main Card */}
      <div className="bg-white rounded-t-3xl shadow-[0_-5px_20px_rgba(0,0,0,0.1)] p-6 pb-safe-bottom z-[1000] animate-in slide-in-from-bottom duration-500 relative">
         <div className="w-12 h-1 bg-slate-200 rounded-full mx-auto mb-6"></div>
         
         <div className="flex justify-between items-center mb-6">
            <div>
               <h3 className="text-lg font-bold text-slate-800">距离目的地</h3>
               <div className="flex items-baseline gap-1">
                 <span className="text-2xl font-bold text-tech-blue">12.5</span>
                 <span className="text-sm text-slate-500">km</span>
                 <span className="mx-2 text-slate-300">|</span>
                 <span className="text-2xl font-bold text-slate-800">25</span>
                 <span className="text-sm text-slate-500">分钟</span>
               </div>
               <div className="text-xs text-slate-400 mt-1">目的地: {MOCK_ROUTE.waypoints[0].name}</div>
            </div>
            <button 
              onClick={() => navigate('/')}
              className="w-12 h-12 bg-red-500 rounded-full flex items-center justify-center shadow-lg shadow-red-200 active:scale-95 transition-transform"
            >
               <span className="text-white font-bold text-xs">退出</span>
            </button>
         </div>

         <div className="grid grid-cols-2 gap-3">
            <button 
              onClick={() => setShowDetails(true)}
              className="bg-slate-100 hover:bg-slate-200 text-slate-700 py-3 rounded-xl font-medium flex items-center justify-center gap-2 transition-colors"
            >
               <Menu className="w-4 h-4" /> 路线详情
            </button>
            <button 
              onClick={handleVoiceToggle}
              className={`${isVoiceActive ? 'bg-blue-600' : 'bg-tech-blue'} hover:bg-blue-700 text-white py-3 rounded-xl font-medium flex items-center justify-center gap-2 shadow-lg shadow-blue-200 transition-colors`}
            >
               <Mic className={`w-4 h-4 ${isVoiceActive ? 'animate-pulse' : ''}`} /> 
               {isVoiceActive ? '播报中...' : '语音播报'}
            </button>
         </div>
      </div>

      {/* Route Details Bottom Sheet Modal */}
      {showDetails && (
        <div className="absolute inset-0 z-[2000] flex flex-col justify-end">
          {/* Backdrop */}
          <div 
            className="absolute inset-0 bg-black/50 backdrop-blur-sm animate-in fade-in duration-300"
            onClick={() => setShowDetails(false)}
          ></div>
          
          {/* Sheet Content */}
          <div className="bg-white rounded-t-3xl p-6 pb-safe-bottom relative z-10 h-[60vh] flex flex-col animate-in slide-in-from-bottom duration-300">
            <div className="flex justify-between items-center mb-6">
              <h3 className="text-xl font-bold text-slate-900">全程导航 (12.5km)</h3>
              <button 
                onClick={() => setShowDetails(false)}
                className="p-2 bg-slate-100 rounded-full hover:bg-slate-200"
              >
                <X className="w-5 h-5 text-slate-600" />
              </button>
            </div>
            
            <div className="flex-1 overflow-y-auto no-scrollbar pr-2">
              <div className="relative border-l-2 border-slate-100 ml-3 space-y-6 pb-8">
                {NAV_STEPS.map((step, index) => (
                  <div key={step.id} className="relative pl-6">
                    <div className={`absolute -left-[9px] top-0 w-4 h-4 rounded-full border-2 border-white ${index === 0 ? 'bg-tech-blue' : index === NAV_STEPS.length - 1 ? 'bg-tech-red' : 'bg-slate-300'}`}></div>
                    <div className="flex items-start gap-3">
                      <div className="mt-0.5 text-slate-400">
                        <step.icon className="w-5 h-5" />
                      </div>
                      <div>
                        <div className="font-bold text-slate-800 text-sm">{step.instruction}</div>
                        {step.distance !== '0m' && (
                          <div className="text-xs text-slate-500 mt-1">行驶 {step.distance}</div>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div className="mt-4 pt-4 border-t border-slate-100">
              <button 
                onClick={() => setShowDetails(false)}
                className="w-full bg-tech-blue text-white py-3.5 rounded-xl font-bold shadow-lg shadow-blue-100 active:scale-[0.98] transition-transform"
              >
                继续导航
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default RouteMap;