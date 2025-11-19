import React, { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { User, Lock, AlertCircle, CheckCircle2, Loader2, Truck } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { FormInput } from './FormInput';
import { SocialLogin } from './SocialLogin';

// --- 1. 定义模拟用户数据 (对应不同端口) ---
const USERS = [
  { username: 'admin',  password: '123', role: 'admin',  port: 3001 },
  { username: 'driver', password: '123', role: 'driver', port: 3002 },
  { username: 'client', password: '123', role: 'client', port: 3003 },
];

// --- 2. 修改验证规则 (方便测试，把密码最短长度改为3) ---
const loginSchema = z.object({
  username: z.string().min(3, '用户名至少需要3个字符').max(20, '用户名不能超过20个字符'),
  password: z.string().min(3, '密码至少需要3个字符'), // 原来是8，改为3方便测试 "123"
  rememberMe: z.boolean().optional(),
});

type LoginFormInputs = z.infer<typeof loginSchema>;

export const LoginForm: React.FC = () => {
  const [isLoading, setIsLoading] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);
  const [loginSuccess, setLoginSuccess] = useState(false);

  const { register, handleSubmit, watch, formState: { errors } } = useForm<LoginFormInputs>({
    resolver: zodResolver(loginSchema),
    defaultValues: {
      username: '',
      password: '',
      rememberMe: false,
    }
  });

  const passwordValue = watch('password');

  // Password strength calculation (保持原来的UI逻辑)
  const getPasswordStrength = (pwd: string) => {
    if (!pwd) return 0;
    let score = 0;
    if (pwd.length >= 5) score += 1; // 稍微调整标准
    if (pwd.length >= 8) score += 1;
    if (/[A-Z]/.test(pwd) && /[0-9]/.test(pwd)) score += 1;
    return score; // 0-3
  };

  const strength = getPasswordStrength(passwordValue);
  
  const getStrengthColor = (s: number) => {
    if (s === 1) return 'bg-tech-error';
    if (s === 2) return 'bg-tech-warning';
    if (s === 3) return 'bg-tech-success';
    return 'bg-slate-200';
  };

  // --- 3. 核心逻辑修改区 ---
  const onSubmit = async (data: LoginFormInputs) => {
    setIsLoading(true);
    setFormError(null);

    try {
      // 模拟 API 延迟，让 Loading 动画转一会，体验更好
      await new Promise(resolve => setTimeout(resolve, 800));

      // 在模拟数据库中查找用户
      const user = USERS.find(u => u.username === data.username && u.password === data.password);

      if (user) {
        setLoginSuccess(true);
        
        // 延迟 1 秒跳转，让用户看到"登录成功"的绿色提示
        setTimeout(() => {
            console.log(`Redirecting to ${user.role} dashboard on port ${user.port}`);
            // 执行硬跳转
            window.location.href = `http://localhost:${user.port}`;
        }, 1000);

      } else {
        throw new Error('用户名或密码错误 (测试账号: admin / 123)');
      }
    } catch (err) {
      setFormError(err instanceof Error ? err.message : '登录失败，请稍后重试');
      setIsLoading(false); // 只有失败才停止 Loading，成功了就保持 Loading 状态直到跳转
    }
  };

  return (
    <div className="w-full max-w-[440px] mx-auto px-6">
      {/* Mobile Header Logo */}
      <div className="lg:hidden flex items-center gap-2 mb-8 justify-center text-tech-blue">
        <Truck className="w-8 h-8" />
        <span className="text-xl font-bold text-slate-900">OptiLogix</span>
      </div>

      <motion.div
        initial={{ opacity: 0, x: 20 }}
        animate={{ opacity: 1, x: 0 }}
        transition={{ duration: 0.5, delay: 0.2 }}
      >
        <div className="mb-8">
          <h2 className="text-3xl font-bold text-slate-900">欢迎回来</h2>
          <p className="text-slate-600 mt-2 flex items-center gap-2">
            请登录您的账户以继续使用
            <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700 text-[10px] font-medium border border-emerald-200">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></span>
              系统正常
            </span>
          </p>
        </div>

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
          <div className="space-y-4">
            <FormInput
              id="username"
              label="用户名"
              placeholder="请输入用户名 (如 admin)"
              registration={register('username')}
              error={errors.username?.message}
              icon={User}
            />
            
            <div>
                <FormInput
                id="password"
                label="密码"
                type="password"
                placeholder="请输入密码 (默认 123)"
                registration={register('password')}
                error={errors.password?.message}
                icon={Lock}
                />
                {/* Password Strength Indicator */}
                {passwordValue && (
                    <div className="mt-2 flex gap-1 h-1">
                        <div className={`flex-1 rounded-full transition-colors duration-300 ${strength >= 1 ? getStrengthColor(strength) : 'bg-slate-200'}`}></div>
                        <div className={`flex-1 rounded-full transition-colors duration-300 ${strength >= 2 ? getStrengthColor(strength) : 'bg-slate-200'}`}></div>
                        <div className={`flex-1 rounded-full transition-colors duration-300 ${strength >= 3 ? getStrengthColor(strength) : 'bg-slate-200'}`}></div>
                    </div>
                )}
            </div>
          </div>

          <div className="flex items-center justify-between">
            <label className="flex items-center space-x-2 cursor-pointer">
              <input
                type="checkbox"
                className="w-4 h-4 rounded border-slate-300 text-tech-blue focus:ring-tech-blue/20"
                {...register('rememberMe')}
              />
              <span className="text-sm text-slate-600">记住登录状态 (7天)</span>
            </label>
            <a href="#" className="text-sm font-medium text-tech-blue hover:text-blue-700 hover:underline">
              忘记密码？
            </a>
          </div>

          <AnimatePresence mode='wait'>
            {formError && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                exit={{ opacity: 0, height: 0 }}
                className="p-3 rounded-lg bg-red-50 border border-red-200 flex items-center gap-2 text-sm text-red-700"
              >
                <AlertCircle className="w-4 h-4 shrink-0" />
                {formError}
              </motion.div>
            )}
            {loginSuccess && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                exit={{ opacity: 0, height: 0 }}
                className="p-3 rounded-lg bg-green-50 border border-green-200 flex items-center gap-2 text-sm text-green-700"
              >
                <CheckCircle2 className="w-4 h-4 shrink-0" />
                登录成功，正在跳转系统...
              </motion.div>
            )}
          </AnimatePresence>

          <button
            type="submit"
            disabled={isLoading || loginSuccess}
            className={`
              w-full flex items-center justify-center py-3 px-4 rounded-lg text-white font-bold text-lg
              transition-all duration-200
              ${isLoading || loginSuccess 
                ? 'bg-slate-400 cursor-not-allowed' 
                : 'bg-tech-blue hover:bg-[#096dd9] shadow-lg shadow-blue-500/30 hover:shadow-blue-500/40 hover:-translate-y-0.5 active:translate-y-0'
              }
            `}
          >
            {isLoading ? (
              <>
                <Loader2 className="w-5 h-5 animate-spin mr-2" />
                验证中...
              </>
            ) : loginSuccess ? (
              '已登录'
            ) : (
              '登 录'
            )}
          </button>

          <SocialLogin />

          <p className="text-center text-sm text-slate-600">
            测试账号: admin / driver / client
            <span className="block text-xs text-slate-400 mt-1">密码统一为: 123</span>
          </p>
        </form>

        <div className="mt-12 pt-6 border-t border-slate-100 text-center">
             <p className="text-xs text-slate-400">
                遇到问题？联系技术支持 <span className="text-slate-600">support@optilogix.com</span>
             </p>
        </div>
      </motion.div>
    </div>
  );
};