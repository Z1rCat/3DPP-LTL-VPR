import React, { Suspense, useState, useMemo, useRef, useEffect } from 'react';
import * as THREE from 'three';
import { Canvas, useFrame } from '@react-three/fiber';
import { 
  OrbitControls, 
  Environment, 
  ContactShadows, 
  Html, 
  Grid, 
  useCursor,
  Edges
} from '@react-three/drei';
import { Info, Box as BoxIcon, Play, Pause, Layers, Maximize2, RotateCcw, Truck } from 'lucide-react';

// --- 类型定义 ---
interface CargoData {
  id: string;
  position: [number, number, number];
  size: [number, number, number];
  color: string;
  type: string;
  label: string;
  category: 'LARGE' | 'STANDARD' | 'LONG';
}

// --- 全局 JSX 扩展 ---
// Fix: Explicitly declare Three.js elements for TypeScript to avoid "Property does not exist" errors
// We extend both the global JSX namespace and React's JSX namespace to ensure compatibility with different React/TS configurations.
declare global {
  namespace JSX {
    interface IntrinsicElements {
      group: any;
      mesh: any;
      boxGeometry: any;
      cylinderGeometry: any;
      planeGeometry: any;
      meshStandardMaterial: any;
      meshPhysicalMaterial: any;
      ambientLight: any;
      directionalLight: any;
      orthographicCamera: any;
      color: any;
      fog: any;
      [elemName: string]: any;
    }
  }
}

declare module 'react' {
  namespace JSX {
    interface IntrinsicElements {
      group: any;
      mesh: any;
      boxGeometry: any;
      cylinderGeometry: any;
      planeGeometry: any;
      meshStandardMaterial: any;
      meshPhysicalMaterial: any;
      ambientLight: any;
      directionalLight: any;
      orthographicCamera: any;
      color: any;
      fog: any;
      [elemName: string]: any;
    }
  }
}

// --- 组件：单个货物箱 ---
const CargoBox: React.FC<{ data: CargoData; isHovered: boolean; onHover: (id: string | null) => void }> = ({ data, isHovered, onHover }) => {
  const meshRef = useRef<THREE.Mesh>(null);
  useCursor(isHovered);

  const scale = isHovered ? 1.05 : 1;
  // 选中时发光，未选中时保持原色
  const color = isHovered ? '#ffffff' : data.color;
  const emissive = isHovered ? '#444444' : '#000000';

  return (
    <group position={data.position}>
      <mesh
        ref={meshRef}
        scale={scale}
        onPointerOver={(e) => { e.stopPropagation(); onHover(data.id); }}
        onPointerOut={(e) => { e.stopPropagation(); onHover(null); }}
      >
        <boxGeometry args={data.size} />
        <meshStandardMaterial 
          color={color} 
          roughness={0.6} 
          metalness={0.1}
          emissive={emissive}
        />
        {/* 边缘线，增强立体感 */}
        <Edges color="#000000" threshold={15} opacity={0.15} scale={1.001} />
      </mesh>
    </group>
  );
};

// --- 组件：高保真卡车模型 ---
const DetailedTruck = () => {
  // 尺寸定义
  const truckWidth = 2.5;
  const chassisHeight = 0.8;
  const chassisLength = 9.2;
  const chassisZ = -0.4; // 底盘中心

  const cabinLength = 2.2;
  const cabinHeight = 3.0;
  const cabinZ = 3.2;

  const containerWidth = 2.55;
  const containerHeight = 2.9;
  const containerLength = 7.4;
  const containerZ = -1.6;

  // 车轮组件
  const Wheel = ({ position, isFront = false }: { position: [number, number, number], isFront?: boolean }) => {
    const wheelRadius = 0.52;
    const wheelWidth = 0.35;
    const rimRadius = 0.3;

    return (
      <group position={position}>
        {/* 轮胎主体 - 黑色橡胶 */}
        <mesh rotation={[0, 0, Math.PI / 2]}>
          <cylinderGeometry args={[wheelRadius, wheelRadius, wheelWidth, 32]} />
          <meshStandardMaterial color="#1a1a1a" roughness={0.9} />
        </mesh>
        
        {/* 轮毂 - 银色金属 */}
        <mesh rotation={[0, 0, Math.PI / 2]}>
          <cylinderGeometry args={[rimRadius, rimRadius, wheelWidth + 0.02, 24]} />
          <meshStandardMaterial color="#e2e8f0" metalness={0.8} roughness={0.2} />
        </mesh>
        
        {/* 轮轴细节 */}
        <mesh rotation={[0, 0, Math.PI / 2]}>
          <cylinderGeometry args={[0.1, 0.1, wheelWidth + 0.05, 8]} />
          <meshStandardMaterial color="#475569" metalness={0.5} />
        </mesh>
      </group>
    );
  };

  const wheelX = 1.05; // 轮距一半

  return (
    <group>
      {/* 1. 底盘大梁 (Chassis Frame) */}
      {/* 主梁 Left */}
      <mesh position={[-0.4, chassisHeight/2, chassisZ]}>
        <boxGeometry args={[0.15, 0.25, chassisLength]} />
        <meshStandardMaterial color="#1e293b" metalness={0.5} roughness={0.5} />
      </mesh>
      {/* 主梁 Right */}
      <mesh position={[0.4, chassisHeight/2, chassisZ]}>
        <boxGeometry args={[0.15, 0.25, chassisLength]} />
        <meshStandardMaterial color="#1e293b" metalness={0.5} roughness={0.5} />
      </mesh>
      {/* 多个横梁 */}
      {[-4, -2, 0, 2, 4].map((z, i) => (
        <mesh key={i} position={[0, chassisHeight/2, chassisZ + z]}>
          <boxGeometry args={[0.8, 0.1, 0.1]} />
          <meshStandardMaterial color="#1e293b" />
        </mesh>
      ))}

      {/* 2. 车轮组 */}
      {/* 前轴 */}
      <Wheel position={[-wheelX, 0.52, cabinZ]} isFront />
      <Wheel position={[wheelX, 0.52, cabinZ]} isFront />
      {/* 后轴 1 */}
      <Wheel position={[-wheelX, 0.52, containerZ - 2.0]} />
      <Wheel position={[wheelX, 0.52, containerZ - 2.0]} />
      {/* 后轴 2 */}
      <Wheel position={[-wheelX, 0.52, containerZ - 3.3]} />
      <Wheel position={[wheelX, 0.52, containerZ - 3.3]} />

      {/* 3. 驾驶室 (Cabin) */}
      <group position={[0, chassisHeight/2 + cabinHeight/2 + 0.1, cabinZ]}>
        {/* 驾驶室主体 */}
        <mesh castShadow>
          <boxGeometry args={[truckWidth, cabinHeight, cabinLength]} />
          <meshPhysicalMaterial 
            color="#ffffff" 
            metalness={0.1} 
            roughness={0.2} 
            clearcoat={1.0} 
            clearcoatRoughness={0.1}
          />
        </mesh>
        
        {/* 前挡风玻璃 */}
        <mesh position={[0, 0.2, cabinLength/2 + 0.01]}>
          <planeGeometry args={[truckWidth - 0.3, 1.4]} />
          <meshStandardMaterial color="#111827" metalness={0.8} roughness={0.1} />
        </mesh>

        {/* 前格栅 */}
        <mesh position={[0, -0.9, cabinLength/2 + 0.01]}>
          <planeGeometry args={[truckWidth - 0.4, 0.8]} />
          <meshStandardMaterial color="#0f172a" metalness={0.4} roughness={0.8} />
        </mesh>

        {/* 顶部导流罩 */}
        <mesh position={[0, cabinHeight/2 + 0.3, -0.2]} rotation={[-Math.PI/12, 0, 0]}>
          <boxGeometry args={[truckWidth, 0.6, cabinLength - 0.5]} />
          <meshStandardMaterial color="#ffffff" />
        </mesh>
      </group>

      {/* 4. 货箱 (Container) - 半透明科技感 */}
      <group position={[0, chassisHeight + containerHeight/2, containerZ]}>
        {/* 货箱轮廓线 */}
        <Edges color="#94a3b8" threshold={15} opacity={0.5} />
        
        {/* 货箱主体 - 半透明 */}
        <mesh>
          <boxGeometry args={[containerWidth, containerHeight, containerLength]} />
          <meshPhysicalMaterial 
            color="#f1f5f9"
            transparent
            opacity={0.15}
            transmission={0.2}
            roughness={0.1}
            metalness={0.1}
            depthWrite={false} // 关键：防止遮挡内部货物渲染
            side={THREE.DoubleSide}
          />
        </mesh>

        {/* 货箱实心地板 */}
        <mesh position={[0, -containerHeight/2 + 0.05, 0]}>
          <boxGeometry args={[containerWidth, 0.1, containerLength]} />
          <meshStandardMaterial color="#334155" roughness={0.8} />
        </mesh>
      </group>
    </group>
  );
};

// --- 算法：生成高密度混装货物 ---
const generateDenseLoad = (): CargoData[] => {
  const cargo: CargoData[] = [];
  
  // 车厢内部有效空间
  // Z轴：从前(靠近驾驶室)向后(车尾)堆叠
  // 前端: -1.6(中心) + 3.7(半长) = 2.1
  // 后端: -1.6 - 3.7 = -5.3
  const startZ = 1.9; // 留一点空隙
  const endZ = -5.0;
  const floorY = 0.95; // 底盘+地板高度
  
  // 定义三个装载区域 (Lanes)
  // 左侧：大件家电 (Blue)
  // 中间：标准箱 (Amber)
  // 右侧：长条配件 (Emerald)
  
  const lanes = [
    { xCenter: -0.85, width: 0.8, color: '#2563eb', type: '大家电', category: 'LARGE' as const, baseHeight: 0.8 },
    { xCenter: 0, width: 0.7, color: '#d97706', type: '标准箱', category: 'STANDARD' as const, baseHeight: 0.5 },
    { xCenter: 0.85, width: 0.7, color: '#059669', type: '长配件', category: 'LONG' as const, baseHeight: 0.4 }
  ];

  let boxIdCounter = 1;

  lanes.forEach(lane => {
    let currentZ = startZ;
    
    // 沿 Z 轴向后堆叠
    while (currentZ > endZ) {
      // 随机生成这一排的长度 (Z轴长度)
      let rowLength = 0;
      if (lane.category === 'LARGE') rowLength = 0.7 + Math.random() * 0.3; // 0.7-1.0m
      if (lane.category === 'STANDARD') rowLength = 0.5 + Math.random() * 0.2; // 0.5-0.7m
      if (lane.category === 'LONG') rowLength = 1.0 + Math.random() * 0.5; // 1.0-1.5m

      // 如果剩余空间不足，停止
      if (currentZ - rowLength < endZ) break;

      // 沿 Y 轴向上堆叠
      let currentY = floorY;
      const maxH = 2.5; // 内部净高

      while (currentY < floorY + maxH) {
        // 随机生成这一层的高度
        let itemHeight = 0;
        if (lane.category === 'LARGE') itemHeight = 0.8 + Math.random() * 0.2;
        if (lane.category === 'STANDARD') itemHeight = 0.4 + Math.random() * 0.2;
        if (lane.category === 'LONG') itemHeight = 0.3 + Math.random() * 0.2;

        if (currentY + itemHeight > floorY + maxH) break;

        // 微小的位置抖动，模拟人工装载的不完美
        const jitterX = (Math.random() - 0.5) * 0.05;
        const jitterZ = (Math.random() - 0.5) * 0.05;

        // 98% 填充率，偶尔留空
        if (Math.random() > 0.02) {
          cargo.push({
            id: `box-${boxIdCounter++}`,
            position: [
              lane.xCenter + jitterX, 
              currentY + itemHeight/2, 
              currentZ - rowLength/2 + jitterZ
            ],
            size: [
              lane.width - 0.05, 
              itemHeight - 0.02, 
              rowLength - 0.05
            ],
            color: lane.color,
            type: lane.type,
            label: `A-${boxIdCounter}`,
            category: lane.category
          });
        }
        currentY += itemHeight;
      }
      currentZ -= rowLength;
    }
  });

  return cargo;
};

const LoadingPlan3D: React.FC = () => {
  const [autoRotate, setAutoRotate] = useState(true);
  const [hoveredBox, setHoveredBox] = useState<string | null>(null);
  
  // 使用 useMemo 缓存货物数据，避免重绘抖动
  const cargoData = useMemo(() => generateDenseLoad(), []);
  
  // 计算统计数据
  const stats = useMemo(() => {
    const total = cargoData.length;
    const volume = cargoData.reduce((acc, item) => acc + (item.size[0] * item.size[1] * item.size[2]), 0);
    const weight = volume * 150; // 假设平均密度
    return { total, volume, weight };
  }, [cargoData]);

  const hoveredItem = useMemo(() => 
    cargoData.find(c => c.id === hoveredBox), 
  [hoveredBox, cargoData]);

  return (
    <div className="fixed top-[60px] bottom-[64px] left-0 right-0 bg-slate-100 flex flex-col">
      
      {/* 1. 顶部 HUD (Head-Up Display) */}
      <div className="absolute top-4 left-4 right-4 z-10 flex justify-between items-start pointer-events-none">
        <div className="bg-white/90 backdrop-blur shadow-sm border border-slate-200 rounded-lg p-3 pointer-events-auto">
          <div className="flex items-center gap-2 mb-1">
            <Truck className="w-4 h-4 text-tech-blue" />
            <span className="font-bold text-sm text-slate-800">车辆满载率</span>
          </div>
          <div className="flex items-baseline gap-1">
            <span className="text-2xl font-bold text-tech-blue">92%</span>
            <span className="text-xs text-slate-500">容积利用</span>
          </div>
        </div>

        <div className="bg-white/90 backdrop-blur shadow-sm border border-slate-200 rounded-lg p-3 pointer-events-auto text-right">
           <div className="text-xs text-slate-500 mb-1">当前货物总量</div>
           <div className="font-bold text-slate-800">{stats.total} 件</div>
           <div className="text-xs text-slate-400 mt-0.5">{stats.volume.toFixed(1)} m³ / {(stats.weight/1000).toFixed(1)} 吨</div>
        </div>
      </div>

      {/* 2. 侧边控制栏 (避免底部遮挡) */}
      <div className="absolute right-4 top-1/2 -translate-y-1/2 z-10 flex flex-col gap-3 pointer-events-none">
        <button 
          onClick={() => setAutoRotate(!autoRotate)}
          className={`w-10 h-10 rounded-full shadow-lg flex items-center justify-center transition-all pointer-events-auto ${
            autoRotate ? 'bg-tech-blue text-white' : 'bg-white text-slate-600'
          }`}
        >
          {autoRotate ? <Pause className="w-5 h-5 fill-current" /> : <Play className="w-5 h-5 ml-0.5 fill-current" />}
        </button>
        
        <button className="w-10 h-10 bg-white text-slate-600 rounded-full shadow-lg flex items-center justify-center pointer-events-auto active:bg-slate-50">
          <RotateCcw className="w-5 h-5" />
        </button>
        
        <button className="w-10 h-10 bg-white text-slate-600 rounded-full shadow-lg flex items-center justify-center pointer-events-auto active:bg-slate-50">
          <Layers className="w-5 h-5" />
        </button>
      </div>

      {/* 3. 3D 场景 */}
      <div className="flex-1 w-full h-full">
        <Canvas shadows camera={{ position: [8, 6, 8], fov: 45 }} dpr={[1, 2]}>
          <Suspense fallback={null}>
            <color attach="background" args={['#f8fafc']} />
            <fog attach="fog" args={['#f8fafc', 10, 40]} />
            
            {/* 灯光系统 */}
            <ambientLight intensity={0.7} />
            <directionalLight 
              position={[10, 20, 5]} 
              intensity={1.2} 
              castShadow 
              shadow-mapSize={[2048, 2048]}
              shadow-bias={-0.0001}
            >
              <orthographicCamera attach="shadow-camera" args={[-15, 15, 15, -15]} />
            </directionalLight>
            <Environment preset="city" />

            {/* 场景内容 */}
            <group position={[0, -1, 0]}>
              <DetailedTruck />
              {cargoData.map((cargo) => (
                <CargoBox 
                  key={cargo.id} 
                  data={cargo} 
                  isHovered={hoveredBox === cargo.id}
                  onHover={setHoveredBox}
                />
              ))}
              
              <Grid 
                position={[0, 0.01, 0]} 
                args={[40, 40]} 
                cellSize={1} 
                cellThickness={1} 
                cellColor="#cbd5e1" 
                sectionSize={5} 
                sectionThickness={1.2} 
                sectionColor="#94a3b8" 
                fadeDistance={35} 
                infiniteGrid 
              />
              <ContactShadows opacity={0.5} scale={40} blur={2.5} far={4} resolution={512} color="#000000" />
            </group>

            <OrbitControls 
              makeDefault 
              autoRotate={autoRotate}
              autoRotateSpeed={0.8}
              minPolarAngle={0}
              maxPolarAngle={Math.PI / 2.1}
              enablePan={false}
              target={[0, 1, -1]} // 聚焦到货箱中心
            />
          </Suspense>
        </Canvas>
      </div>

      {/* 4. 底部信息面板 (交互时显示) */}
      {hoveredItem ? (
        <div className="absolute bottom-4 left-4 right-4 bg-slate-900/90 backdrop-blur text-white p-4 rounded-xl shadow-lg animate-in slide-in-from-bottom-2 border border-slate-700 z-20">
          <div className="flex justify-between items-start">
            <div>
              <div className="text-xs text-slate-400 mb-1">选中货物</div>
              <div className="text-lg font-bold flex items-center gap-2">
                {hoveredItem.type}
                <span className="text-xs font-mono bg-slate-700 px-1.5 py-0.5 rounded">{hoveredItem.label}</span>
              </div>
            </div>
            <div className="text-right">
              <div className="text-xs text-slate-400">尺寸 (L×W×H)</div>
              <div className="font-mono font-bold">
                {hoveredItem.size.map(n => n.toFixed(2)).join(' × ')} m
              </div>
            </div>
          </div>
        </div>
      ) : (
        <div className="absolute bottom-4 left-4 right-4 bg-white/90 backdrop-blur p-3 rounded-xl shadow-md border border-blue-100 flex gap-3 items-center z-20">
          <div className="bg-blue-50 p-2 rounded-full">
            <Info className="w-4 h-4 text-tech-blue" />
          </div>
          <p className="text-xs text-slate-600">
            点击货物查看详情，双指缩放查看细节。
            <span className="block text-[10px] text-slate-400 mt-0.5">智能混装方案 A-09 已验证安全</span>
          </p>
        </div>
      )}
    </div>
  );
};

export default LoadingPlan3D;