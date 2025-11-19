import React from 'react';
import { MessageCircle, Building2, Zap } from 'lucide-react';

export const SocialLogin: React.FC = () => {
  return (
    <div className="space-y-6">
      <div className="relative">
        <div className="absolute inset-0 flex items-center">
          <div className="w-full border-t border-slate-200"></div>
        </div>
        <div className="relative flex justify-center text-sm">
          <span className="px-2 bg-white text-slate-500">或使用以下方式登录</span>
        </div>
      </div>

      <div className="grid grid-cols-3 gap-4">
        <button
          type="button"
          className="flex items-center justify-center w-full py-2.5 px-4 border border-slate-200 rounded-lg hover:bg-slate-50 hover:border-slate-300 transition-all duration-200 group"
          title="微信登录"
        >
          <MessageCircle className="w-5 h-5 text-green-600 group-hover:scale-110 transition-transform" />
        </button>

        <button
          type="button"
          className="flex items-center justify-center w-full py-2.5 px-4 border border-slate-200 rounded-lg hover:bg-slate-50 hover:border-slate-300 transition-all duration-200 group"
          title="钉钉登录"
        >
          <Zap className="w-5 h-5 text-blue-500 group-hover:scale-110 transition-transform" />
        </button>

        <button
          type="button"
          className="flex items-center justify-center w-full py-2.5 px-4 border border-slate-200 rounded-lg hover:bg-slate-50 hover:border-slate-300 transition-all duration-200 group"
          title="企业SSO"
        >
          <Building2 className="w-5 h-5 text-slate-700 group-hover:scale-110 transition-transform" />
        </button>
      </div>
    </div>
  );
};