import React, { useState } from 'react';
import { UseFormRegisterReturn } from 'react-hook-form';
import { Eye, EyeOff, LucideIcon } from 'lucide-react';
import { motion } from 'framer-motion';

interface FormInputProps {
  id: string;
  label: string;
  type?: string;
  placeholder?: string;
  registration: UseFormRegisterReturn;
  error?: string;
  icon?: LucideIcon;
}

export const FormInput: React.FC<FormInputProps> = ({
  id,
  label,
  type = 'text',
  placeholder,
  registration,
  error,
  icon: Icon
}) => {
  const [showPassword, setShowPassword] = useState(false);
  const isPassword = type === 'password';

  return (
    <div className="space-y-1">
      <label htmlFor={id} className="block text-sm font-medium text-slate-700">
        {label}
      </label>
      <div className="relative group">
        {Icon && (
          <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
            <Icon className={`h-5 w-5 ${error ? 'text-tech-error' : 'text-slate-400 group-focus-within:text-tech-blue'}`} />
          </div>
        )}
        <input
          id={id}
          type={isPassword ? (showPassword ? 'text' : 'password') : type}
          placeholder={placeholder}
          className={`
            w-full py-3 pr-4 rounded-lg border bg-white text-slate-900 placeholder-slate-400
            transition-all duration-200 outline-none
            ${Icon ? 'pl-10' : 'pl-4'}
            ${error 
              ? 'border-tech-error focus:ring-2 focus:ring-tech-error/20' 
              : 'border-slate-300 focus:border-tech-blue focus:ring-2 focus:ring-tech-blue/20 hover:border-slate-400'
            }
          `}
          {...registration}
        />
        {isPassword && (
          <button
            type="button"
            onClick={() => setShowPassword(!showPassword)}
            className="absolute inset-y-0 right-0 pr-3 flex items-center text-slate-400 hover:text-slate-600 focus:outline-none"
          >
            {showPassword ? (
              <EyeOff className="h-5 w-5" />
            ) : (
              <Eye className="h-5 w-5" />
            )}
          </button>
        )}
      </div>
      {error && (
        <motion.p
          initial={{ opacity: 0, y: -5 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-sm text-tech-error flex items-center gap-1 mt-1"
        >
          {error}
        </motion.p>
      )}
    </div>
  );
};