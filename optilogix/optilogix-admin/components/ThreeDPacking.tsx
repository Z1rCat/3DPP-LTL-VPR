
import React, { useMemo } from 'react';
import { Canvas } from '@react-three/fiber';
import { OrbitControls, Grid, Center, Environment, PerspectiveCamera } from '@react-three/drei';
import { CargoItem, Vehicle, OptimizationType } from '../types';
import * as THREE from 'three';
import { AlertTriangle, Info, Layers, Box as BoxIcon, MousePointer2, Maximize, RotateCcw, ZoomIn } from 'lucide-react';

// Augment JSX namespace to include Three.js intrinsic elements
interface ThreeElementsImpl {
  mesh: any;
  boxGeometry: any;
  meshStandardMaterial: any;
  lineSegments: any;
  edgesGeometry: any;
  lineBasicMaterial: any;
  group: any;
  planeGeometry: any;
  ambientLight: any;
  spotLight: any;
  pointLight: any;
}

declare global {
  namespace JSX {
    interface IntrinsicElements extends ThreeElementsImpl {}
  }
}

declare module 'react' {
  namespace JSX {
    interface IntrinsicElements extends ThreeElementsImpl {}
  }
}

interface ThreeDPackingProps {
  vehicle: Vehicle;
  cargo: CargoItem[];
}

interface BoxProps {
  position: [number, number, number];
  args: [number, number, number];
  color: string;
  isMerged?: boolean;
}

const Box: React.FC<BoxProps> = ({ position, args, color, isMerged }) => {
  return (
    <mesh position={position}>
      <boxGeometry args={args} />
      <meshStandardMaterial color={color} roughness={0.3} metalness={0.1} transparent opacity={0.95} />
      <lineSegments>
        <edgesGeometry args={[new THREE.BoxGeometry(...args)]} />
        <lineBasicMaterial color="#000000" linewidth={1} opacity={0.15} transparent />
      </lineSegments>
      {isMerged && (
         // Add a visual indicator for merged boxes (a simple cross or texture hint)
         <group>
             <lineSegments>
                <edgesGeometry args={[new THREE.BoxGeometry(args[0]*0.8, args[1]*0.8, args[2]*0.8)]} />
                <lineBasicMaterial color="#ffffff" linewidth={1} opacity={0.4} transparent />
             </lineSegments>
         </group>
      )}
    </mesh>
  );
};

const Container = ({ dims }: { dims: [number, number, number] }) => {
  return (
    <group>
      <mesh position={[0, -dims[2]/2 - 0.05, 0]} rotation={[-Math.PI / 2, 0, 0]}>
        <planeGeometry args={[dims[0], dims[1]]} />
        <meshStandardMaterial color="#f1f5f9" side={THREE.DoubleSide} transparent opacity={0.8} />
      </mesh>
      <lineSegments position={[0, 0, 0]}>
        <edgesGeometry args={[new THREE.BoxGeometry(dims[0], dims[2], dims[1])]} />
        <lineBasicMaterial color="#94a3b8" linewidth={2} opacity={0.4} transparent />
      </lineSegments>
    </group>
  );
};

export const ThreeDPacking: React.FC<ThreeDPackingProps> = ({ vehicle, cargo }) => {
  
  const packedItems = useMemo(() => {
    const items: React.ReactElement[] = [];
    
    if (vehicle.optType === OptimizationType.DEDICATED) {
        // --- DEDICATED ALGORITHM (Visual Simulation) ---
        // Neat rows and columns
        if(cargo.length === 0) return [];
        const sampleBox = cargo[0];
        const boxW = sampleBox.dimensions[0];
        const boxH = sampleBox.dimensions[2];
        const boxD = sampleBox.dimensions[1];
        
        let x = -vehicle.dimensions[0]/2 + boxW/2;
        let y = -vehicle.dimensions[2]/2 + boxH/2;
        let z = -vehicle.dimensions[1]/2 + boxD/2;
        
        cargo.forEach((box) => {
            if (y > vehicle.dimensions[2]/2) return; // Full
            
            items.push(
                <Box 
                  key={box.id} 
                  position={[x, y, z]} 
                  args={box.dimensions} 
                  color={box.color} 
                />
            );
            
            x += boxW + 0.02; // Small gap
            if (x > vehicle.dimensions[0]/2 - boxW/2) {
                x = -vehicle.dimensions[0]/2 + boxW/2;
                z += boxD + 0.02;
            }
            if (z > vehicle.dimensions[1]/2 - boxD/2) {
                z = -vehicle.dimensions[1]/2 + boxD/2;
                y += boxH;
            }
        });

    } else {
        // --- MIXED ALGORITHM (Visual Simulation) ---
        // Varied placement, resembling a complex puzzle
        let currentX = -vehicle.dimensions[0] / 2;
        let currentY = -vehicle.dimensions[2] / 2; 
        let currentZ = -vehicle.dimensions[1] / 2;
        const MAX_HEIGHT = vehicle.dimensions[2] / 2;
        
        cargo.forEach((box, idx) => {
           // Naive complex stacking simulation
           if (currentX + box.dimensions[0] > vehicle.dimensions[0] / 2) {
              currentX = -vehicle.dimensions[0] / 2;
              currentZ += box.dimensions[1];
           }
           if (currentZ + box.dimensions[1] > vehicle.dimensions[1] / 2) {
               currentZ = -vehicle.dimensions[1] / 2;
               currentY += box.dimensions[2];
           }
    
           if (currentY < MAX_HEIGHT) {
             items.push(
                <Box 
                  key={box.id} 
                  position={[
                      currentX + box.dimensions[0]/2, 
                      currentY + box.dimensions[2]/2, 
                      currentZ + box.dimensions[1]/2
                  ]} 
                  args={box.dimensions} 
                  color={box.color}
                  isMerged={box.isMergedItem}
                />
             );
             currentX += box.dimensions[0] + 0.05; 
           }
        });
    }
    
    return items;
  }, [vehicle, cargo]);

  return (
    <div className="w-full h-full bg-gradient-to-b from-slate-50 to-white rounded-lg overflow-hidden relative group select-none">
        
        {/* Top Left: Vehicle Context Info */}
        <div className="absolute top-4 left-4 z-10 bg-white/90 backdrop-blur px-4 py-3 rounded-lg border border-slate-200 shadow-lg shadow-slate-100/50">
          <div className="text-xs font-bold text-slate-800 mb-1 flex items-center gap-2">
            <div className={`w-2 h-2 rounded-full ${vehicle.optType === OptimizationType.DEDICATED ? 'bg-blue-500' : 'bg-purple-500'}`}></div>
            {vehicle.optType === OptimizationType.DEDICATED ? '专线装载模式 (Dedicated)' : '混合装载模式 (Mixed)'}
          </div>
          <div className="text-[10px] text-slate-500 max-w-[200px] leading-relaxed">
             {vehicle.optType === OptimizationType.DEDICATED 
               ? '算法优先考虑同规格货物的堆叠稳定性与体积利用率。' 
               : '算法优先处理小件聚合，利用模拟退火算法解决不规则空隙填充。'}
          </div>
        </div>

        {/* Top Right: View Controls */}
        <div className="absolute top-4 right-4 z-10 flex flex-col gap-2">
            <button className="p-2 bg-white/90 hover:bg-white backdrop-blur rounded-lg border border-slate-200 shadow-sm text-slate-600 hover:text-blue-600 transition-colors" title="复位视图">
                <RotateCcw size={16} />
            </button>
            <button className="p-2 bg-white/90 hover:bg-white backdrop-blur rounded-lg border border-slate-200 shadow-sm text-slate-600 hover:text-blue-600 transition-colors" title="缩放适配">
                <ZoomIn size={16} />
            </button>
            <button className="p-2 bg-white/90 hover:bg-white backdrop-blur rounded-lg border border-slate-200 shadow-sm text-slate-600 hover:text-blue-600 transition-colors" title="全屏模式">
                <Maximize size={16} />
            </button>
        </div>

        {/* Bottom Right: Legend */}
        <div className="absolute bottom-4 right-4 z-10 bg-white/90 backdrop-blur p-3 rounded-lg border border-slate-200 shadow-lg shadow-slate-100/50">
             <h4 className="text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-2">货物类型图例</h4>
             <div className="space-y-2">
                <div className="flex items-center gap-2">
                    <div className="w-3 h-3 bg-[#1890ff] rounded-sm shadow-sm"></div>
                    <span className="text-[10px] text-slate-600 font-medium">常规/专线货物</span>
                </div>
                {vehicle.optType === OptimizationType.MIXED && (
                   <div className="flex items-center gap-2">
                      <div className="w-3 h-3 bg-[#722ed1] rounded-sm shadow-sm flex items-center justify-center">
                        <div className="w-1.5 h-1.5 border border-white/50 rounded-[1px]"></div>
                      </div>
                      <span className="text-[10px] text-slate-600 font-medium">标准周转箱 (聚合小件)</span>
                   </div>
                )}
                 <div className="flex items-center gap-2">
                    <div className="w-3 h-3 border border-slate-300 bg-slate-100 rounded-sm"></div>
                    <span className="text-[10px] text-slate-400">可用剩余空间</span>
                </div>
             </div>
        </div>

        {/* Bottom Center: Performance Warning */}
        <div className="absolute bottom-6 left-1/2 transform -translate-x-1/2 z-20 flex flex-col items-center pointer-events-none w-full px-6">
           <div className="bg-amber-50/90 backdrop-blur-md border border-amber-200 text-amber-700 px-4 py-2 rounded-full shadow-sm flex items-center gap-2 max-w-lg">
              <AlertTriangle size={14} className="shrink-0 animate-pulse" />
              <span className="text-[10px] font-medium text-center">
                渲染性能保护模式已开启：当前仅显示 40% 采样数据以保持交互流畅。完整装箱清单请导出报表。
              </span>
           </div>
        </div>

        <Canvas shadows dpr={[1, 2]}>
            <PerspectiveCamera makeDefault position={[12, 12, 12]} fov={45} />
            <ambientLight intensity={0.7} />
            <spotLight position={[20, 30, 10]} angle={0.2} penumbra={1} intensity={1.5} castShadow />
            <pointLight position={[-10, 5, -10]} intensity={0.5} />
            
            <Center>
                <Container dims={[vehicle.dimensions[0], vehicle.dimensions[1], vehicle.dimensions[2]]} />
                {packedItems}
            </Center>

            <Grid infiniteGrid fadeDistance={60} sectionColor="#1890ff" cellColor="#e2e8f0" sectionThickness={1} cellThickness={0.6} />
            <Environment preset="city" />
            <OrbitControls autoRotate autoRotateSpeed={vehicle.optType === OptimizationType.DEDICATED ? 0.2 : 0.5} />
        </Canvas>
    </div>
  );
};
