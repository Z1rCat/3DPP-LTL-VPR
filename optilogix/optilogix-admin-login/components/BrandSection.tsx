import React from 'react';
import { Truck, Package, Map, BarChart3, TrendingUp } from 'lucide-react';
import { motion } from 'framer-motion';

const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.15,
      delayChildren: 0.3
    }
  }
};

const itemVariants = {
  hidden: { opacity: 0, x: -20 },
  visible: { opacity: 1, x: 0, transition: { duration: 0.5, ease: "easeOut" } }
};

export const BrandSection: React.FC = () => {
  return (
    <div className="relative hidden lg:flex flex-col justify-between w-full lg:w-1/2 bg-[#1890ff] overflow-hidden p-12 text-white">
      {/* Background Gradient Overlay */}
      <div 
        className="absolute inset-0 z-0" 
        style={{ 
          background: 'linear-gradient(135deg, #1890ff 0%, #096dd9 100%)' 
        }} 
      />
      
      {/* Decorative geometric circles */}
      <div className="absolute top-[-10%] right-[-10%] w-96 h-96 rounded-full bg-white/5 blur-3xl" />
      <div className="absolute bottom-[-10%] left-[-20%] w-[500px] h-[500px] rounded-full bg-white/5 blur-3xl" />

      {/* Header */}
      <motion.div 
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
        className="relative z-10 flex items-center gap-3"
      >
        <div className="p-2 bg-white/10 rounded-lg backdrop-blur-sm">
          <Truck className="w-8 h-8 text-white" />
        </div>
        <div>
          <h1 className="text-2xl font-bold tracking-tight">OptiLogix</h1>
          <p className="text-blue-100 text-xs opacity-90">v4.0.0 Intelligent Logistics</p>
        </div>
      </motion.div>

      {/* Features List */}
      <motion.div 
        variants={containerVariants}
        initial="hidden"
        animate="visible"
        className="relative z-10 flex flex-col gap-8 my-auto"
      >
        <div className="space-y-2">
          <h2 className="text-4xl font-bold leading-tight">
            下一代智能<br/>物流优化系统
          </h2>
          <p className="text-blue-100 text-lg max-w-md">
            全链路数字化决策支持，让物流更智慧、更高效。
          </p>
        </div>

        <div className="grid gap-6 mt-8">
          <motion.div variants={itemVariants} className="flex items-start gap-4 p-4 rounded-xl bg-white/10 backdrop-blur-sm border border-white/10 hover:bg-white/15 transition-colors">
            <div className="p-2 bg-white/20 rounded-lg">
              <Package className="w-6 h-6" />
            </div>
            <div>
              <h3 className="font-semibold text-lg">3D 智能装载</h3>
              <p className="text-blue-100 text-sm mt-1">先进的3D装箱算法，最大化空间利用率，降低运输成本。</p>
            </div>
          </motion.div>

          <motion.div variants={itemVariants} className="flex items-start gap-4 p-4 rounded-xl bg-white/10 backdrop-blur-sm border border-white/10 hover:bg-white/15 transition-colors">
            <div className="p-2 bg-white/20 rounded-lg">
              <Map className="w-6 h-6" />
            </div>
            <div>
              <h3 className="font-semibold text-lg">智能路径规划</h3>
              <p className="text-blue-100 text-sm mt-1">AI驱动的车辆路径优化(VRP)，实时规避拥堵，准时送达。</p>
            </div>
          </motion.div>
          
           <div className="flex gap-4">
               <motion.div variants={itemVariants} className="flex-1 flex items-center gap-3 p-3 rounded-xl bg-white/5 border border-white/5">
                 <BarChart3 className="w-5 h-5 text-blue-200" />
                 <span className="text-sm font-medium">实时监控</span>
               </motion.div>
               <motion.div variants={itemVariants} className="flex-1 flex items-center gap-3 p-3 rounded-xl bg-white/5 border border-white/5">
                 <TrendingUp className="w-5 h-5 text-blue-200" />
                 <span className="text-sm font-medium">数据分析</span>
               </motion.div>
           </div>
        </div>
      </motion.div>

      {/* Footer */}
      <motion.div 
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 1, duration: 0.6 }}
        className="relative z-10 text-blue-200 text-sm"
      >
        © 2025 OptiLogix Systems. All rights reserved.
      </motion.div>
    </div>
  );
};