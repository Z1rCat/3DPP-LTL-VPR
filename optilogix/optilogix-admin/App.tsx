
import React, { useState, useEffect } from 'react';
import { 
  LayoutDashboard, 
  Truck, 
  Package, 
  Map as MapIcon, 
  UploadCloud, 
  Play, 
  CheckCircle2, 
  AlertCircle,
  BarChart3,
  Layers,
  FileCode,
  FileText,
  ArrowRight,
  Scale,
  Combine,
  Split,
  BoxSelect,
  MoreHorizontal,
  Barcode,
  Clock,
  User,
  Info,
  Download,
  Send,
  Database,
  Smartphone,
  ChevronDown,
  ChevronUp,
  Users,
  Wifi
} from 'lucide-react';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { MOCK_VEHICLES, MOCK_DELIVERY_POINTS, generateSmartCargo } from './constants';
import { Vehicle, SimulationState, VehicleStatus, BatchMetadata, OptimizationType, AnalysisReport } from './types';
import { ThreeDPacking } from './components/ThreeDPacking';
import { RouteMap } from './components/RouteMap';

const App = () => {
  // --- State ---
  const [activeTab, setActiveTab] = useState<'3D' | 'MAP' | 'ANALYTICS'>('3D');
  
  // Data States
  const [batchInfo, setBatchInfo] = useState<BatchMetadata | null>(null);
  const [analysisReport, setAnalysisReport] = useState<AnalysisReport | null>(null);
  
  const [vehicles, setVehicles] = useState<Vehicle[]>(
    MOCK_VEHICLES.map(v => ({ ...v, status: VehicleStatus.IDLE, efficiency: 0 }))
  );
  const [selectedVehicle, setSelectedVehicle] = useState<Vehicle>(vehicles[0]);
  const [cargoData, setCargoData] = useState([]); // Initially empty
  
  const [simulation, setSimulation] = useState<SimulationState>({
    phase: 'IDLE',
    progress: 0,
    logs: []
  });

  // New States for Features
  const [exportingPdf, setExportingPdf] = useState(false);
  const [dispatchState, setDispatchState] = useState<{show: boolean, step: number, completed: boolean}>({
      show: false, step: 0, completed: false
  });
  const [isStandbyExpanded, setIsStandbyExpanded] = useState(false);

  // Sync selected vehicle update when vehicle list changes
  useEffect(() => {
    const updated = vehicles.find(v => v.id === selectedVehicle.id);
    if (updated) setSelectedVehicle(updated);
  }, [vehicles, selectedVehicle.id]);

  // --- Handlers ---

  // 1. Upload & Analyze
  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    // Updated to Chengdu Region Code (CD)
    const mockBatchId = `CD-${new Date().getFullYear()}${(new Date().getMonth()+1).toString().padStart(2,'0')}${new Date().getDate()}-X92`;
    
    setBatchInfo({
      batchId: mockBatchId,
      fileName: file.name,
      uploadTime: new Date().toLocaleTimeString(),
      totalOrders: 2842,
      totalWeight: 124500,
      status: 'PENDING',
      priority: 'High',
      operator: 'OP_28 (李工/成都)',
      estimatedCompletion: '15s'
    });

    // Start Pre-analysis
    setSimulation({ phase: 'ANALYZING', progress: 0, logs: [`正在读取文件 "${file.name}"...`, `地域配置：中国·成都 (Chengdu)`] });
    
    setTimeout(() => {
        setAnalysisReport({
            totalVolume: 1250, // m3
            largeCargoVolume: 850, // m3 (For dedicated trucks)
            smallCargoCount: 2400, // items
            mergedBoxCount: 48, // 2400 items / 50 per box
            dedicatedTrucksNeeded: 3,
            mixedTrucksNeeded: 2
        });
        setSimulation(prev => ({ 
            phase: 'CONFIRM_ANALYSIS', 
            progress: 100, 
            logs: [`数据预处理完成。`, `识别到显著量纲差异，已生成分层优化建议。`, ...prev.logs] 
        }));
        setBatchInfo(prev => prev ? { ...prev, status: 'ANALYZED' } : null);
    }, 1500);
  };

  // 1.1 Export PDF Logic
  const handlePdfExport = () => {
      setExportingPdf(true);
      // Simulate generation delay
      setTimeout(() => {
          // Create a dummy file
          const content = `
          ================================================
          OPTILOGIX INTELLIGENT LOGISTICS REPORT (CHENGDU)
          ================================================
          Batch ID: ${batchInfo?.batchId}
          Region: Chengdu, Sichuan, CN
          Date: ${new Date().toLocaleString()}
          Operator: ${batchInfo?.operator}
          
          [ANALYSIS SUMMARY]
          Total Volume: ${analysisReport?.totalVolume} m3
          Small Items: ${analysisReport?.smallCargoCount} -> Merged to ${analysisReport?.mergedBoxCount} Boxes
          
          [OPTIMIZATION STRATEGY]
          - Dedicated Trucks: ${analysisReport?.dedicatedTrucksNeeded}
          - Mixed Trucks: ${analysisReport?.mixedTrucksNeeded}
          
          [STATUS]
          Optimization Strategy: Hierarchical Spatial-Temporal Constraint
          
          *** END OF REPORT ***
          `;
          const blob = new Blob([content], { type: 'text/plain' }); // using text/plain for simplicity to ensure download
          const url = URL.createObjectURL(blob);
          const link = document.createElement('a');
          link.href = url;
          link.download = `OptiLogix_CD_Report_${batchInfo?.batchId}.txt`; // Downloading as TXT for reliability in mockup
          document.body.appendChild(link);
          link.click();
          document.body.removeChild(link);
          URL.revokeObjectURL(url);
          
          setExportingPdf(false);
      }, 2000);
  };
  
  // 2. Execute Optimization
  const startOptimization = () => {
    if (!batchInfo) return;
    
    setSimulation({ phase: 'PACKING_3D', progress: 0, logs: ['初始化优化引擎 (Map: Chengdu_V2)...'] });
    setBatchInfo(prev => prev ? { ...prev, status: 'PROCESSING' } : null);
    setAnalysisReport(null); // Hide overlay

    // Simulate Realistic Logic Timeline
    const timeline = [
      { time: 500, progress: 10, phase: 'PACKING_3D', log: '执行分流策略：分离 >15m³ 大宗货物...' },
      { time: 1500, progress: 25, phase: 'PACKING_3D', log: '小件聚合：正在将 2400 件微型货物合并为标准箱...' },
      { time: 2500, progress: 40, phase: 'PACKING_3D', log: '专车优化：计算 [家具专线] 3DPP 装载率...' },
      { time: 4000, progress: 55, phase: 'PACKING_3D', log: '混装优化：[聚合箱 + 中型散货] 混合模拟退火算法...' },
      { time: 5500, progress: 70, phase: 'ROUTING_VRP', log: '路径规划：生成成都市区 VRPPD 拓扑网络...' },
      { time: 7000, progress: 85, phase: 'ROUTING_VRP', log: '约束检查：三环路限行规则与车辆限重...' },
      { time: 8500, progress: 95, phase: 'COMPLETE', log: '正在生成三维可视化数据...' },
      { time: 9500, progress: 100, phase: 'COMPLETE', log: '全流程优化完成。' }
    ];

    timeline.forEach((step) => {
      setTimeout(() => {
        setSimulation(prev => ({
          phase: step.phase as any,
          progress: step.progress,
          logs: [step.log, ...prev.logs.slice(0, 6)]
        }));

        if (step.progress === 100) {
          finishOptimization();
        }
      }, step.time);
    });
  };

  const finishOptimization = () => {
    setBatchInfo(prev => prev ? { ...prev, status: 'DONE' } : null);
    
    // Update Vehicles with "Real" results
    setVehicles(prev => prev.map((v) => ({
      ...v,
      status: VehicleStatus.OPTIMIZED,
      // Dedicated gets high efficiency, mixed varies
      efficiency: v.optType === OptimizationType.DEDICATED ? 98.5 : 89.2
    })));

    // Generate cargo for the currently selected vehicle immediately
    setCargoData(generateSmartCargo(selectedVehicle));
  };

  // 3. Dispatch Workflow
  const handleOpenDispatch = () => {
      setDispatchState({ show: true, step: 0, completed: false });
      
      // Simulate Dispatch Steps
      const steps = [
          { step: 1, delay: 1000 }, // Sync DB
          { step: 2, delay: 2500 }, // Generate Waybills
          { step: 3, delay: 4000 }, // Push to App
          { step: 4, delay: 5500 }  // Finish
      ];

      steps.forEach(s => {
          setTimeout(() => {
              setDispatchState(prev => ({ 
                  ...prev, 
                  step: s.step, 
                  completed: s.step === 4 
              }));
          }, s.delay);
      });
  };

  // Update cargo when selecting different vehicle AFTER optimization
  useEffect(() => {
      if (batchInfo?.status === 'DONE') {
          setCargoData(generateSmartCargo(selectedVehicle));
      }
  }, [selectedVehicle, batchInfo?.status]);


  // --- Render Helpers ---
  const getStatusColor = (status: VehicleStatus) => {
    switch(status) {
      case VehicleStatus.OPTIMIZED: return 'text-emerald-600 border-emerald-200 bg-emerald-50';
      case VehicleStatus.IN_TRANSIT: return 'text-amber-600 border-amber-200 bg-amber-50';
      default: return 'text-gray-400 border-gray-200 bg-gray-50';
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 font-sans flex flex-col overflow-hidden">
      
      {/* --- Header --- */}
      <header className="h-16 border-b border-slate-200 bg-white/80 backdrop-blur-md flex items-center justify-between px-6 z-40 shadow-sm">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 bg-gradient-to-br from-blue-600 to-blue-800 rounded-lg flex items-center justify-center shadow-lg shadow-blue-200">
            <Layers className="text-white w-5 h-5" />
          </div>
          <div className="flex flex-col justify-center">
            <h1 className="text-lg font-bold text-slate-800 tracking-tight leading-tight">OptiLogix <span className="text-tech-blue font-light">Chengdu</span></h1>
            <p className="text-[10px] text-slate-400 uppercase tracking-widest font-medium">西南大区智能调度中台</p>
          </div>
        </div>
        
        <div className="flex items-center gap-6 text-sm">
           {batchInfo?.status === 'DONE' && (
                <button 
                    onClick={handleOpenDispatch}
                    className="hidden md:flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg shadow-md hover:bg-blue-700 transition-all active:scale-95 font-bold text-xs"
                >
                    <Send size={14} /> 提交成都调度中心
                </button>
           )}
           
           <div className="flex items-center gap-2 px-3 py-1.5 bg-slate-100 rounded-full border border-slate-200 text-xs text-slate-600">
              <span className="w-2 h-2 bg-emerald-500 rounded-full animate-pulse"></span>
              成都节点在线
           </div>
          <div className="flex items-center gap-3 pl-4 border-l border-slate-200">
             <div className="w-8 h-8 rounded-full bg-slate-100 flex items-center justify-center border border-slate-200 text-slate-600 font-medium shadow-inner">
               L
             </div>
             <div className="text-right hidden sm:block">
               <div className="text-slate-800 font-bold text-xs">Li.Operator</div>
               <div className="text-[10px] text-slate-400 font-mono">CD-028</div>
             </div>
          </div>
        </div>
      </header>

      {/* --- Main Content --- */}
      <div className="flex-1 flex overflow-hidden relative">
        
        {/* --- Sidebar --- */}
        <aside className="w-80 bg-white border-r border-slate-200 flex flex-col py-6 overflow-y-auto z-30 shadow-[4px_0_24px_-12px_rgba(0,0,0,0.08)]">
           <div className="px-5 space-y-8 flex-1">
              
              {/* 1. Import / Batch Ticket Section */}
              <div>
                 <div className="flex items-center justify-between mb-3 px-1">
                    <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider">工单管理</h3>
                    {batchInfo && (
                         <span className={`text-[10px] px-1.5 py-0.5 rounded font-bold ${batchInfo.status === 'DONE' ? 'bg-emerald-100 text-emerald-700' : 'bg-blue-100 text-blue-700'}`}>
                            {batchInfo.status === 'DONE' ? 'FINISHED' : 'ACTIVE'}
                         </span>
                    )}
                 </div>
                 
                 {!batchInfo ? (
                    <div className="group cursor-pointer relative overflow-hidden rounded-xl border-2 border-dashed border-slate-300 bg-slate-50 hover:bg-blue-50 hover:border-blue-400 transition-all duration-300 p-6">
                        <input type="file" className="absolute inset-0 opacity-0 cursor-pointer z-10" onChange={handleFileUpload} disabled={simulation.phase !== 'IDLE' && simulation.phase !== 'COMPLETE'} />
                        <div className="flex flex-col items-center gap-3 text-center">
                            <div className="p-3 bg-white rounded-full shadow-sm group-hover:scale-110 transition-transform duration-300">
                                <UploadCloud className="text-slate-400 group-hover:text-blue-500 transition-colors" size={24} />
                            </div>
                            <div>
                                <span className="text-sm text-slate-700 font-bold block group-hover:text-blue-600">
                                   导入订单数据
                                </span>
                                <span className="text-[10px] text-slate-400 block mt-1">
                                    支持 JSON / CSV 格式
                                </span>
                            </div>
                        </div>
                    </div>
                 ) : (
                    // DIGITAL TICKET STYLE
                    <div className="bg-white border border-slate-200 rounded-xl shadow-sm relative overflow-hidden group">
                        {/* Ticket Header */}
                        <div className="bg-slate-50 border-b border-slate-200 p-3 flex justify-between items-center">
                           <div className="flex items-center gap-2">
                              <FileText size={14} className="text-blue-600"/>
                              <span className="text-xs font-bold text-slate-700 font-mono tracking-tight">{batchInfo.batchId}</span>
                           </div>
                           <MoreHorizontal size={14} className="text-slate-400 cursor-pointer hover:text-slate-600"/>
                        </div>

                        {/* Ticket Body */}
                        <div className="p-4 space-y-3">
                            <div>
                                <div className="text-[10px] text-slate-400 uppercase tracking-wide mb-1">文件来源</div>
                                <div className="text-xs font-bold text-slate-800 truncate" title={batchInfo.fileName}>{batchInfo.fileName}</div>
                            </div>
                            
                            <div className="grid grid-cols-2 gap-3">
                                <div>
                                    <div className="text-[10px] text-slate-400 uppercase tracking-wide mb-1 flex items-center gap-1"><User size={10}/> 操作员</div>
                                    <div className="text-xs font-medium text-slate-700">{batchInfo.operator}</div>
                                </div>
                                <div>
                                    <div className="text-[10px] text-slate-400 uppercase tracking-wide mb-1 flex items-center gap-1"><Clock size={10}/> 预期耗时</div>
                                    <div className="text-xs font-medium text-slate-700">{batchInfo.estimatedCompletion}</div>
                                </div>
                            </div>

                            <div className="pt-3 border-t border-dashed border-slate-200 grid grid-cols-2 gap-2">
                                <div className="bg-slate-50 p-2 rounded border border-slate-100 text-center">
                                   <div className="text-[10px] text-slate-400">优先级</div>
                                   <div className="text-xs font-bold text-orange-500">{batchInfo.priority}</div>
                                </div>
                                <div className="bg-slate-50 p-2 rounded border border-slate-100 text-center">
                                   <div className="text-[10px] text-slate-400">订单量</div>
                                   <div className="text-xs font-bold text-blue-600">{batchInfo.totalOrders}</div>
                                </div>
                            </div>
                        </div>

                        {/* Barcode Decoration */}
                        <div className="bg-slate-50 p-2 border-t border-slate-200 flex justify-center opacity-60">
                           <Barcode className="w-full h-6 text-slate-400" />
                        </div>
                    </div>
                 )}
              </div>

              {/* 2. Engine Status */}
              <div className="space-y-3">
                 <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider px-1">计算引擎</h3>
                 
                 <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm relative overflow-hidden">
                    <div className="flex justify-between items-center mb-2">
                       <span className="text-xs font-medium text-slate-600 flex items-center gap-1">
                           <span className={`w-1.5 h-1.5 rounded-full ${simulation.phase === 'IDLE' ? 'bg-slate-300' : 'bg-blue-500 animate-pulse'}`}></span>
                           {simulation.phase === 'IDLE' ? '等待任务' : '计算中...'}
                       </span>
                       <span className="text-[10px] text-blue-600 font-mono font-bold">{simulation.progress}%</span>
                    </div>
                    <div className="h-1.5 bg-slate-100 rounded-full overflow-hidden mb-3">
                       <div 
                         className="h-full bg-gradient-to-r from-blue-500 to-indigo-500 transition-all duration-300 ease-out"
                         style={{ width: `${simulation.progress}%` }}
                       />
                    </div>
                    
                    <div className="h-28 overflow-hidden relative bg-slate-50 rounded-lg p-3 border border-slate-100 inner-shadow">
                       <div className="space-y-1.5 font-mono text-[10px]">
                          {simulation.logs.length === 0 && <span className="text-slate-400 italic opacity-50">System Ready...</span>}
                          {simulation.logs.map((log, i) => (
                             <div key={i} className={`truncate flex gap-2 ${i===0 ? 'text-blue-700 font-bold' : 'text-slate-400'}`}>
                               <span className="opacity-50 text-[8px]">{new Date().toLocaleTimeString().split(' ')[0]}</span>
                               <span>{log}</span>
                             </div>
                          ))}
                       </div>
                    </div>
                 </div>
              </div>

              {/* 3. Vehicle List (Grouped) */}
              <div className="space-y-6 flex-1">
                 {/* Dedicated Fleet */}
                 <div>
                    <h3 className="text-xs font-bold text-blue-600 uppercase tracking-wider px-1 mb-3 flex items-center gap-2">
                       <span className="p-1 bg-blue-100 rounded text-blue-600"><BoxSelect size={12}/></span>
                       专车资源池 (Dedicated)
                    </h3>
                    <div className="space-y-2.5 pl-2 border-l-2 border-blue-100">
                      {vehicles.filter(v => v.optType === OptimizationType.DEDICATED).map(v => (
                         <div 
                           key={v.id}
                           onClick={() => setSelectedVehicle(v)}
                           className={`p-3 rounded-lg border cursor-pointer transition-all duration-200 group relative
                             ${selectedVehicle.id === v.id 
                               ? 'bg-blue-50/50 border-blue-200 shadow-sm translate-x-1' 
                               : 'bg-white border-slate-100 hover:border-blue-200 hover:shadow-sm'}`}
                         >
                            <div className="flex justify-between items-start">
                               <div>
                                  <div className={`text-xs font-bold transition-colors ${selectedVehicle.id === v.id ? 'text-blue-700' : 'text-slate-700'}`}>{v.name}</div>
                                  <div className="text-[10px] text-slate-500 mt-0.5 font-medium">{v.cargoTypeDescription}</div>
                               </div>
                               <div className={`text-[9px] px-1.5 py-0.5 rounded font-mono font-bold ${getStatusColor(v.status)}`}>
                                 {v.efficiency > 0 ? `${v.efficiency}%` : '-'}
                               </div>
                            </div>
                         </div>
                      ))}
                    </div>
                 </div>

                 {/* Mixed Fleet */}
                 <div>
                    <h3 className="text-xs font-bold text-purple-600 uppercase tracking-wider px-1 mb-3 flex items-center gap-2">
                       <span className="p-1 bg-purple-100 rounded text-purple-600"><Combine size={12}/></span>
                       混装资源池 (Mixed)
                    </h3>
                    <div className="space-y-2.5 pl-2 border-l-2 border-purple-100">
                      {vehicles.filter(v => v.optType === OptimizationType.MIXED).map(v => (
                         <div 
                           key={v.id}
                           onClick={() => setSelectedVehicle(v)}
                           className={`p-3 rounded-lg border cursor-pointer transition-all duration-200 group relative
                             ${selectedVehicle.id === v.id 
                               ? 'bg-purple-50/50 border-purple-200 shadow-sm translate-x-1' 
                               : 'bg-white border-slate-100 hover:border-purple-200 hover:shadow-sm'}`}
                         >
                            <div className="flex justify-between items-start">
                               <div>
                                  <div className={`text-xs font-bold transition-colors ${selectedVehicle.id === v.id ? 'text-purple-700' : 'text-slate-700'}`}>{v.name}</div>
                                  <div className="text-[10px] text-slate-500 mt-0.5 font-medium">{v.cargoTypeDescription}</div>
                               </div>
                               <div className={`text-[9px] px-1.5 py-0.5 rounded font-mono font-bold ${getStatusColor(v.status)}`}>
                                 {v.efficiency > 0 ? `${v.efficiency}%` : '-'}
                               </div>
                            </div>
                         </div>
                      ))}
                    </div>
                 </div>

                 {/* Standby Fleet (Expandable) */}
                 <div className="pt-2 border-t border-slate-100">
                    <button 
                        onClick={() => setIsStandbyExpanded(!isStandbyExpanded)}
                        className="w-full flex items-center justify-between p-2 text-slate-500 hover:text-slate-700 hover:bg-slate-50 rounded-lg transition-colors"
                    >
                        <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider">
                           <Users size={14} />
                           待命车队 (Standby)
                        </div>
                        {isStandbyExpanded ? <ChevronUp size={14}/> : <ChevronDown size={14}/>}
                    </button>
                    
                    {isStandbyExpanded && (
                        <div className="mt-2 space-y-2 pl-2 border-l-2 border-slate-200 animate-in slide-in-from-top-2 duration-300">
                            {Array.from({length: 12}).map((_, i) => (
                                <div key={i} className="p-2 rounded bg-slate-50 border border-slate-100 flex justify-between items-center opacity-70">
                                    <div>
                                        <div className="text-[10px] font-bold text-slate-600">川A·{8000+i} (检修)</div>
                                        <div className="text-[9px] text-slate-400">定期维护中</div>
                                    </div>
                                    <div className="w-2 h-2 rounded-full bg-slate-300"></div>
                                </div>
                            ))}
                        </div>
                    )}
                 </div>

              </div>
           </div>
        </aside>

        {/* --- Main Visualization Area --- */}
        <main className="flex-1 flex flex-col bg-[#f8fafc] relative p-4 lg:p-6 overflow-hidden">
           
           {/* Tab Navigation */}
           <div className="flex items-center justify-between mb-4">
              <div className="flex gap-1 bg-white p-1 rounded-xl shadow-sm border border-slate-200 z-10">
                 <button 
                   onClick={() => setActiveTab('3D')}
                   className={`px-4 py-2 rounded-lg text-xs font-bold flex items-center gap-2 transition-all ${activeTab === '3D' ? 'bg-slate-800 text-white shadow-md' : 'text-slate-500 hover:text-slate-800 hover:bg-slate-50'}`}
                 >
                   <Package size={14} /> 
                   {selectedVehicle.optType === OptimizationType.DEDICATED ? '3D 装载视图' : '3D 混装视图'}
                 </button>
                 <button 
                   onClick={() => setActiveTab('MAP')}
                   className={`px-4 py-2 rounded-lg text-xs font-bold flex items-center gap-2 transition-all ${activeTab === 'MAP' ? 'bg-slate-800 text-white shadow-md' : 'text-slate-500 hover:text-slate-800 hover:bg-slate-50'}`}
                 >
                   <MapIcon size={14} /> 路径规划视图
                 </button>
              </div>
              
              {/* Dynamic Header Info */}
              {batchInfo?.status === 'DONE' && (
                <div className="flex items-center gap-4 animate-in fade-in slide-in-from-right duration-500">
                   <div className="text-xs font-medium px-4 py-2 bg-white border border-slate-200 rounded-lg shadow-sm text-slate-500 flex items-center gap-3">
                      <span className="flex flex-col text-right leading-tight">
                          <span className="text-[10px] uppercase tracking-wider">当前车辆</span>
                          <span className="text-slate-800 font-bold">{selectedVehicle.name}</span>
                      </span>
                      <div className="h-6 w-px bg-slate-200"></div>
                      <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wide ${selectedVehicle.optType === OptimizationType.DEDICATED ? 'bg-blue-50 text-blue-600' : 'bg-purple-50 text-purple-600'}`}>
                        {selectedVehicle.optType === OptimizationType.DEDICATED ? '专用线路' : '混合线路'}
                      </span>
                   </div>
                </div>
              )}
           </div>

           {/* Visualization Canvas */}
           <div className="flex-1 bg-white rounded-2xl shadow-[0_2px_16px_-4px_rgba(0,0,0,0.05)] border border-slate-200 overflow-hidden relative ring-1 ring-slate-100">
              
              {/* --- ANALYSIS REPORT MODAL (The "Classify First" Logic) --- */}
              {simulation.phase === 'CONFIRM_ANALYSIS' && analysisReport && (
                  <div className="absolute inset-0 z-[60] bg-slate-900/40 backdrop-blur-sm flex items-center justify-center p-8 animate-in zoom-in-95 duration-300">
                      <div className="bg-white rounded-2xl shadow-2xl shadow-black/20 border border-white/20 max-w-4xl w-full overflow-hidden flex flex-col max-h-[90vh]">
                          
                          {/* Modal Header */}
                          <div className="bg-slate-900 p-6 text-white flex justify-between items-center relative overflow-hidden">
                              <div className="absolute inset-0 bg-gradient-to-br from-blue-600/20 to-purple-600/20"></div>
                              <div className="relative z-10">
                                <h2 className="text-xl font-bold flex items-center gap-3">
                                    <div className="p-2 bg-white/10 rounded-lg"><Scale size={20} className="text-blue-300"/></div>
                                    智能分层优化建议报告
                                </h2>
                                <p className="text-slate-400 text-xs mt-1 ml-12">基于空间-时间约束算法 (S-T Constraint Algorithm) 的预处理结果</p>
                              </div>
                              <div className="text-right relative z-10">
                                  <div className="text-3xl font-bold text-blue-400 font-mono tracking-tight">{batchInfo?.totalOrders}</div>
                                  <div className="text-[10px] text-slate-400 uppercase">Total Orders</div>
                              </div>
                          </div>

                          <div className="p-8 overflow-y-auto bg-slate-50/50">
                              <div className="grid grid-cols-3 gap-6 mb-8">
                                  {/* Strategy 1: Dedicated */}
                                  <div className="bg-white rounded-xl p-6 border border-slate-200 shadow-sm relative overflow-hidden hover:shadow-md transition-shadow">
                                      <div className="absolute -right-4 -top-4 p-4 rounded-full bg-blue-50"><BoxSelect size={48} className="text-blue-100" /></div>
                                      <h3 className="text-slate-800 font-bold text-sm mb-1 flex items-center gap-2"><span className="w-2 h-2 bg-blue-500 rounded-full"></span> 大宗专车策略</h3>
                                      <p className="text-slate-500 text-xs mb-6">针对体积 '&gt;' 15m³ 的单一品类</p>
                                      
                                      <div className="space-y-2">
                                          <div className="flex justify-between text-xs">
                                              <span className="text-slate-400">大宗体积</span>
                                              <span className="font-mono font-bold text-slate-700">{analysisReport.largeCargoVolume} m³</span>
                                          </div>
                                          <div className="flex justify-between text-xs">
                                              <span className="text-slate-400">所需车辆</span>
                                              <span className="font-mono font-bold text-blue-600">{analysisReport.dedicatedTrucksNeeded} 辆 (大型)</span>
                                          </div>
                                      </div>
                                  </div>

                                  {/* Strategy 2: Merging */}
                                  <div className="bg-white rounded-xl p-6 border border-purple-200 shadow-sm relative overflow-hidden ring-1 ring-purple-50 hover:shadow-md transition-shadow">
                                      <div className="absolute -right-4 -top-4 p-4 rounded-full bg-purple-50"><Combine size={48} className="text-purple-100" /></div>
                                      <h3 className="text-slate-800 font-bold text-sm mb-1 flex items-center gap-2"><span className="w-2 h-2 bg-purple-500 rounded-full"></span> 智能聚合策略</h3>
                                      <p className="text-slate-500 text-xs mb-6">针对体积 &lt; 0.01m³ 微小件</p>
                                      
                                      <div className="flex items-center justify-center gap-4 mb-4">
                                          <div className="text-center">
                                              <div className="text-lg font-bold text-slate-700 font-mono">{analysisReport.smallCargoCount}</div>
                                              <div className="text-[9px] text-slate-400 uppercase">散件</div>
                                          </div>
                                          <ArrowRight size={16} className="text-purple-300"/>
                                          <div className="text-center">
                                              <div className="text-2xl font-bold text-purple-600 font-mono">{analysisReport.mergedBoxCount}</div>
                                              <div className="text-[9px] text-purple-400 uppercase font-bold">标准箱</div>
                                          </div>
                                      </div>
                                      <div className="text-[10px] text-center text-purple-600/80 bg-purple-50 py-1 rounded">已应用动态装箱算法</div>
                                  </div>

                                  {/* Strategy 3: Mixed */}
                                  <div className="bg-white rounded-xl p-6 border border-slate-200 shadow-sm relative overflow-hidden hover:shadow-md transition-shadow">
                                      <div className="absolute -right-4 -top-4 p-4 rounded-full bg-emerald-50"><Truck size={48} className="text-emerald-100" /></div>
                                      <h3 className="text-slate-800 font-bold text-sm mb-1 flex items-center gap-2"><span className="w-2 h-2 bg-emerald-500 rounded-full"></span> 混合拼装策略</h3>
                                      <p className="text-slate-500 text-xs mb-6">余货 + 标准箱拼车</p>
                                      
                                      <div className="space-y-2">
                                          <div className="flex justify-between text-xs">
                                              <span className="text-slate-400">混合体积</span>
                                              <span className="font-mono font-bold text-slate-700">{(analysisReport.totalVolume - analysisReport.largeCargoVolume).toFixed(0)} m³</span>
                                          </div>
                                          <div className="flex justify-between text-xs">
                                              <span className="text-slate-400">所需车辆</span>
                                              <span className="font-mono font-bold text-emerald-600">{analysisReport.mixedTrucksNeeded} 辆 (中型)</span>
                                          </div>
                                      </div>
                                  </div>
                              </div>

                              <div className="bg-blue-50/50 rounded-lg p-5 border border-blue-100 text-sm text-slate-600 leading-relaxed flex gap-4 items-start">
                                  <Info className="text-blue-500 shrink-0 mt-0.5" size={18} />
                                  <div>
                                    <p className="mb-1"><span className="font-bold text-slate-800">系统决策摘要：</span></p>
                                    <p>
                                        检测到 <span className="font-mono font-bold">{analysisReport.smallCargoCount}</span> 个微小订单造成空间离散。
                                        系统已自动启用<span className="text-purple-600 font-bold">「动态聚合算法 (Dynamic Merging)」</span>，
                                        将微小件合并为 <span className="font-mono font-bold">{analysisReport.mergedBoxCount}</span> 个标准周转箱。
                                        剩余大件与周转箱将通过<span className="text-emerald-600 font-bold">「多品类混合装载 (Multi-Category VRP)」</span>进行最终优化。
                                    </p>
                                    <div className="mt-3 flex items-center gap-2 text-xs font-medium text-blue-700">
                                        <CheckCircle2 size={12}/> 预计提升满载率：+24.5%
                                    </div>
                                  </div>
                              </div>
                          </div>

                          <div className="p-6 bg-white border-t border-slate-200 flex justify-end gap-3">
                              <button 
                                onClick={handlePdfExport}
                                disabled={exportingPdf}
                                className="px-6 py-3 bg-white border border-slate-300 rounded-lg text-sm font-medium text-slate-700 hover:bg-slate-50 hover:text-slate-900 transition-colors shadow-sm flex items-center gap-2"
                              >
                                  {exportingPdf ? (
                                      <>
                                        <span className="w-3 h-3 border-2 border-slate-400 border-t-transparent rounded-full animate-spin"></span>
                                        生成中...
                                      </>
                                  ) : (
                                      <>
                                        <Download size={16} /> 导出详细报表 (PDF)
                                      </>
                                  )}
                              </button>
                              <button 
                                onClick={startOptimization}
                                className="px-8 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-sm font-bold shadow-lg shadow-blue-200 hover:shadow-blue-300 transition-all flex items-center gap-2 active:scale-95"
                              >
                                  <Play size={16} fill="currentColor" /> 执行分层优化策略
                              </button>
                          </div>
                      </div>
                  </div>
              )}
              
              {/* --- DISPATCH CENTER MODAL --- */}
              {dispatchState.show && (
                 <div className="absolute inset-0 z-[70] bg-slate-900/90 backdrop-blur-md flex items-center justify-center p-8 animate-in fade-in duration-300">
                     <div className="bg-white rounded-2xl shadow-2xl max-w-2xl w-full p-8 text-center relative overflow-hidden">
                         {!dispatchState.completed ? (
                             <div className="space-y-8">
                                <h2 className="text-2xl font-bold text-slate-800">正在提交成都调度中心</h2>
                                <p className="text-slate-500">Syncing optimization results to Chengdu Central Dispatch...</p>
                                
                                <div className="flex justify-center items-center gap-8 my-8">
                                    {/* Step 1: DB */}
                                    <div className={`flex flex-col items-center gap-3 transition-all duration-500 ${dispatchState.step >= 1 ? 'opacity-100 scale-110' : 'opacity-30'}`}>
                                        <div className={`w-16 h-16 rounded-full flex items-center justify-center ${dispatchState.step >= 1 ? 'bg-blue-100 text-blue-600' : 'bg-slate-100 text-slate-400'}`}>
                                            <Database size={32} />
                                        </div>
                                        <span className="text-xs font-bold text-slate-700">云端写入 (SW-Region)</span>
                                    </div>
                                    <div className="w-16 h-1 bg-slate-100 rounded overflow-hidden">
                                        <div className={`h-full bg-blue-500 transition-all duration-1000 ${dispatchState.step >= 2 ? 'w-full' : 'w-0'}`}></div>
                                    </div>
                                    
                                    {/* Step 2: Waybill */}
                                    <div className={`flex flex-col items-center gap-3 transition-all duration-500 ${dispatchState.step >= 2 ? 'opacity-100 scale-110' : 'opacity-30'}`}>
                                        <div className={`w-16 h-16 rounded-full flex items-center justify-center ${dispatchState.step >= 2 ? 'bg-purple-100 text-purple-600' : 'bg-slate-100 text-slate-400'}`}>
                                            <FileText size={32} />
                                        </div>
                                        <span className="text-xs font-bold text-slate-700">电子路单</span>
                                    </div>
                                    <div className="w-16 h-1 bg-slate-100 rounded overflow-hidden">
                                        <div className={`h-full bg-blue-500 transition-all duration-1000 ${dispatchState.step >= 3 ? 'w-full' : 'w-0'}`}></div>
                                    </div>

                                    {/* Step 3: Driver */}
                                    <div className={`flex flex-col items-center gap-3 transition-all duration-500 ${dispatchState.step >= 3 ? 'opacity-100 scale-110' : 'opacity-30'}`}>
                                        <div className={`w-16 h-16 rounded-full flex items-center justify-center ${dispatchState.step >= 3 ? 'bg-emerald-100 text-emerald-600' : 'bg-slate-100 text-slate-400'}`}>
                                            <Smartphone size={32} className={dispatchState.step >= 3 ? 'animate-bounce' : ''} />
                                        </div>
                                        <span className="text-xs font-bold text-slate-700">司机推送</span>
                                    </div>
                                </div>

                                <div className="text-xs text-slate-400 animate-pulse">Processing... Step {dispatchState.step}/3</div>
                             </div>
                         ) : (
                             <div className="space-y-6 animate-in zoom-in duration-500">
                                 <div className="w-24 h-24 bg-emerald-100 rounded-full flex items-center justify-center mx-auto mb-6 text-emerald-600">
                                     <CheckCircle2 size={48} />
                                 </div>
                                 <h2 className="text-2xl font-bold text-slate-800">调度下发成功</h2>
                                 <p className="text-slate-500 text-sm max-w-md mx-auto">
                                     已成功生成 6 份电子路单并推送到司机移动端。车辆监控系统已激活，即时位置数据每 30 秒同步一次。
                                 </p>
                                 <button 
                                     onClick={() => setDispatchState({show: false, step: 0, completed: false})}
                                     className="mt-6 px-8 py-3 bg-slate-900 text-white rounded-lg hover:bg-slate-800 transition-colors font-bold text-sm"
                                 >
                                     返回监控大屏
                                 </button>
                             </div>
                         )}
                     </div>
                 </div>
              )}

              {/* 3D View */}
              <div className={`absolute inset-0 transition-all duration-500 ${activeTab === '3D' ? 'opacity-100 z-10' : 'opacity-0 z-0 pointer-events-none'}`}>
                 {/* Only render if optimization started or done */}
                 {(simulation.phase === 'PACKING_3D' || simulation.phase === 'ROUTING_VRP' || simulation.phase === 'COMPLETE' || batchInfo?.status === 'DONE') && (
                    <ThreeDPacking vehicle={selectedVehicle} cargo={cargoData} />
                 )}
                 
                 {/* Placeholder for Initial State */}
                 {simulation.phase === 'IDLE' && !batchInfo && (
                     <div className="absolute inset-0 flex flex-col items-center justify-center text-slate-300 select-none bg-slate-50/50">
                         <div className="p-6 bg-white rounded-full shadow-sm mb-4 border border-slate-100">
                            <Package size={48} className="text-slate-200" />
                         </div>
                         <p className="text-sm font-medium text-slate-400">等待数据导入以初始化 3D 引擎</p>
                     </div>
                 )}
              </div>

              {/* Map View */}
              <div className={`absolute inset-0 transition-all duration-500 ${activeTab === 'MAP' ? 'opacity-100 z-10 translate-x-0' : 'opacity-0 z-0 -translate-x-4 pointer-events-none'}`}>
                 <RouteMap points={MOCK_DELIVERY_POINTS} highlightRoute={batchInfo?.status === 'DONE'} />
              </div>

           </div>
        </main>
      </div>
    </div>
  );
};

export default App;
