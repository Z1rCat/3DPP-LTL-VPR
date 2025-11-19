import React, { useState, useEffect } from 'react';
import { Check, ChevronRight, MapPin, Package, Truck, CreditCard, AlertCircle, Calculator } from 'lucide-react';
import { calculatePrice, formatCurrency } from '../utils';
import { PricingBreakdown } from '../types';

interface OrderWizardProps {
  onComplete: () => void;
  onCancel: () => void;
}

type Step = 1 | 2 | 3;

const OrderWizard: React.FC<OrderWizardProps> = ({ onComplete, onCancel }) => {
  const [step, setStep] = useState<Step>(1);
  const [formData, setFormData] = useState({
    cargoName: '',
    cargoType: 'food',
    weight: 10,
    volume: 0.1,
    fragile: false,
    pickupAddress: '',
    deliveryAddress: '',
    contactName: '',
    contactPhone: ''
  });
  
  const [pricing, setPricing] = useState<PricingBreakdown | null>(null);

  // Simulate real-time price calculation
  useEffect(() => {
    const price = calculatePrice(formData.weight, formData.volume, 50, formData.fragile);
    setPricing(price);
  }, [formData.weight, formData.volume, formData.fragile]);

  const handleNext = () => {
    if (step < 3) setStep((prev) => (prev + 1) as Step);
  };

  const handleBack = () => {
    if (step > 1) setStep((prev) => (prev - 1) as Step);
  };

  const handleSubmit = () => {
    // Simulate API call
    setTimeout(() => {
      onComplete();
    }, 1500);
  };

  return (
    <div className="max-w-4xl mx-auto animate-in slide-in-from-right-4 duration-500">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-slate-800 mb-2">新建订单</h1>
        <p className="text-slate-500">请填写货物及配送信息，系统将为您匹配最优运力。</p>
      </div>

      {/* Progress Steps */}
      <div className="mb-8">
        <div className="relative flex justify-between items-center">
          <div className="absolute left-0 top-1/2 w-full h-1 bg-slate-200 -z-10 rounded-full"></div>
          <div className="absolute left-0 top-1/2 h-1 bg-tech-blue transition-all duration-500 -z-10 rounded-full" 
               style={{ width: step === 1 ? '0%' : step === 2 ? '50%' : '100%' }}></div>
          
          {[
            { num: 1, label: '货物信息', icon: Package },
            { num: 2, label: '配送地址', icon: MapPin },
            { num: 3, label: '确认支付', icon: CreditCard }
          ].map((s) => (
            <div key={s.num} className="flex flex-col items-center bg-[#f8fafc] px-2">
              <div className={`w-10 h-10 rounded-full flex items-center justify-center border-2 transition-colors duration-300 
                ${step >= s.num ? 'bg-tech-blue border-tech-blue text-white' : 'bg-white border-slate-300 text-slate-400'}`}>
                {step > s.num ? <Check className="w-5 h-5" /> : <s.icon className="w-5 h-5" />}
              </div>
              <span className={`text-xs mt-2 font-medium ${step >= s.num ? 'text-tech-blue' : 'text-slate-500'}`}>
                {s.label}
              </span>
            </div>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Main Form Area */}
        <div className="lg:col-span-2 bg-white rounded-xl border border-slate-200 shadow-sm p-6">
          {step === 1 && (
            <div className="space-y-6 animate-in fade-in">
              <h3 className="text-lg font-bold text-slate-800 flex items-center gap-2">
                <Package className="text-tech-blue" /> 货物详情
              </h3>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="col-span-2">
                  <label className="block text-sm font-medium text-slate-700 mb-1">货物名称</label>
                  <input 
                    type="text" 
                    value={formData.cargoName}
                    onChange={(e) => setFormData({...formData, cargoName: e.target.value})}
                    className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-tech-blue focus:border-tech-blue"
                    placeholder="例如：办公文件、家具、食品..."
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">货物类型</label>
                  <select 
                    value={formData.cargoType}
                    onChange={(e) => setFormData({...formData, cargoType: e.target.value})}
                    className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-tech-blue"
                  >
                    <option value="food">食品生鲜</option>
                    <option value="electronics">电子产品</option>
                    <option value="furniture">家具家装</option>
                    <option value="daily">日用品</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">特殊处理</label>
                  <div className="flex items-center gap-4 h-[42px]">
                    <label className="flex items-center gap-2 cursor-pointer">
                      <input 
                        type="checkbox" 
                        checked={formData.fragile}
                        onChange={(e) => setFormData({...formData, fragile: e.target.checked})}
                        className="w-4 h-4 text-tech-blue rounded focus:ring-tech-blue" 
                      />
                      <span className="text-sm text-slate-600">易碎品 (+¥50)</span>
                    </label>
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">重量 (kg)</label>
                  <input 
                    type="number" 
                    value={formData.weight}
                    onChange={(e) => setFormData({...formData, weight: Number(e.target.value)})}
                    className="w-full px-3 py-2 border border-slate-300 rounded-lg font-mono"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">体积 (m³)</label>
                  <input 
                    type="number" 
                    step="0.1"
                    value={formData.volume}
                    onChange={(e) => setFormData({...formData, volume: Number(e.target.value)})}
                    className="w-full px-3 py-2 border border-slate-300 rounded-lg font-mono"
                  />
                </div>
              </div>
              
              <div className="bg-blue-50 p-4 rounded-lg flex items-start gap-3">
                <AlertCircle className="w-5 h-5 text-tech-blue flex-shrink-0 mt-0.5" />
                <p className="text-sm text-blue-700">
                  AI 助手提示：对于 {formData.cargoType === 'food' ? '食品类' : '此类'} 货物，建议使用泡沫箱包装以确保安全。
                </p>
              </div>
            </div>
          )}

          {step === 2 && (
            <div className="space-y-6 animate-in fade-in">
               <h3 className="text-lg font-bold text-slate-800 flex items-center gap-2">
                <MapPin className="text-tech-blue" /> 配送信息
              </h3>

              <div className="space-y-4">
                <div className="bg-slate-50 p-4 rounded-lg border border-slate-200">
                  <label className="block text-xs font-bold text-slate-500 uppercase mb-2">取货地址 (From)</label>
                  <input 
                    type="text" 
                    value={formData.pickupAddress}
                    onChange={(e) => setFormData({...formData, pickupAddress: e.target.value})}
                    placeholder="例如：成都市高新区天府大道..."
                    className="w-full bg-white px-3 py-2 border border-slate-300 rounded-lg mb-3"
                  />
                  <div className="grid grid-cols-2 gap-3">
                    <input 
                      type="text" 
                      placeholder="联系人"
                      className="w-full bg-white px-3 py-2 border border-slate-300 rounded-lg text-sm"
                    />
                    <input 
                      type="text" 
                      placeholder="联系电话"
                      className="w-full bg-white px-3 py-2 border border-slate-300 rounded-lg text-sm"
                    />
                  </div>
                </div>

                <div className="flex justify-center">
                  <Truck className="text-slate-400 rotate-90 md:rotate-0" />
                </div>

                <div className="bg-slate-50 p-4 rounded-lg border border-slate-200">
                  <label className="block text-xs font-bold text-slate-500 uppercase mb-2">送货地址 (To)</label>
                  <input 
                    type="text" 
                    value={formData.deliveryAddress}
                    onChange={(e) => setFormData({...formData, deliveryAddress: e.target.value})}
                    placeholder="例如：成都市锦江区..."
                    className="w-full bg-white px-3 py-2 border border-slate-300 rounded-lg mb-3"
                  />
                  <div className="grid grid-cols-2 gap-3">
                     <input 
                      type="text" 
                      placeholder="收货人"
                      className="w-full bg-white px-3 py-2 border border-slate-300 rounded-lg text-sm"
                    />
                    <input 
                      type="text" 
                      placeholder="收货电话"
                      className="w-full bg-white px-3 py-2 border border-slate-300 rounded-lg text-sm"
                    />
                  </div>
                </div>
              </div>
            </div>
          )}

          {step === 3 && (
             <div className="space-y-6 animate-in fade-in">
               <h3 className="text-lg font-bold text-slate-800 flex items-center gap-2">
                <CreditCard className="text-tech-blue" /> 确认订单
              </h3>
              
              <div className="bg-slate-50 rounded-lg p-4 border border-slate-200 space-y-3 text-sm">
                <div className="flex justify-between">
                  <span className="text-slate-500">货物</span>
                  <span className="font-medium">{formData.cargoName || '未填写'} ({formData.weight}kg)</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500">取货</span>
                  <span className="font-medium">{formData.pickupAddress || '未填写'}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500">送货</span>
                  <span className="font-medium">{formData.deliveryAddress || '未填写'}</span>
                </div>
              </div>

              <div className="space-y-3">
                <label className="block text-sm font-medium text-slate-700">支付方式</label>
                <div className="grid grid-cols-2 gap-3">
                  <button className="flex items-center justify-center gap-2 border-2 border-tech-blue bg-blue-50 text-tech-blue py-3 rounded-lg font-bold">
                    <span>在线支付</span>
                  </button>
                  <button className="flex items-center justify-center gap-2 border border-slate-200 text-slate-600 py-3 rounded-lg hover:bg-slate-50">
                    <span>货到付款</span>
                  </button>
                </div>
              </div>
             </div>
          )}

          <div className="mt-8 flex justify-between pt-6 border-t border-slate-100">
            {step > 1 ? (
              <button 
                onClick={handleBack}
                className="px-6 py-2 text-slate-600 font-medium hover:bg-slate-100 rounded-lg transition-colors"
              >
                上一步
              </button>
            ) : (
              <button 
                onClick={onCancel}
                className="px-6 py-2 text-slate-600 font-medium hover:bg-slate-100 rounded-lg transition-colors"
              >
                取消
              </button>
            )}

            {step < 3 ? (
               <button 
                onClick={handleNext}
                className="bg-tech-blue text-white px-8 py-2 rounded-lg font-bold shadow-lg shadow-blue-200 hover:bg-blue-600 transition-all flex items-center gap-2"
              >
                下一步 <ChevronRight className="w-4 h-4" />
              </button>
            ) : (
              <button 
                onClick={handleSubmit}
                className="bg-tech-emerald text-white px-8 py-2 rounded-lg font-bold shadow-lg shadow-green-200 hover:bg-green-600 transition-all flex items-center gap-2"
              >
                确认支付 ¥{pricing?.totalPrice}
              </button>
            )}
          </div>
        </div>

        {/* Sidebar Summary */}
        <div className="lg:col-span-1">
          <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6 sticky top-24">
            <div className="flex items-center gap-2 mb-4 text-slate-800 font-bold">
              <Calculator className="w-5 h-5 text-tech-orange" />
              费用明细 (预估)
            </div>
            
            {pricing && (
              <div className="space-y-3 text-sm">
                <div className="flex justify-between text-slate-500">
                  <span>基础运费</span>
                  <span>{formatCurrency(pricing.basePrice)}</span>
                </div>
                <div className="flex justify-between text-slate-500">
                  <span>重量/体积费</span>
                  <span>{formatCurrency(pricing.weightFee)}</span>
                </div>
                {pricing.specialFee > 0 && (
                  <div className="flex justify-between text-tech-amber">
                    <span>特殊处理费</span>
                    <span>+{formatCurrency(pricing.specialFee)}</span>
                  </div>
                )}
                {pricing.discount > 0 && (
                   <div className="flex justify-between text-tech-emerald">
                    <span>优惠折扣</span>
                    <span>-{formatCurrency(pricing.discount)}</span>
                  </div>
                )}
                
                <div className="h-px bg-slate-100 my-4" />
                
                <div className="flex justify-between items-baseline">
                  <span className="font-bold text-slate-800">总计</span>
                  <span className="text-2xl font-bold font-mono text-tech-blue">{formatCurrency(pricing.totalPrice)}</span>
                </div>

                <div className="mt-4 bg-slate-50 p-3 rounded text-xs text-slate-500 leading-relaxed">
                  * 最终价格可能因实际路况和测量结果略有差异。下单即代表同意 OptiLogix 服务条款。
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default OrderWizard;