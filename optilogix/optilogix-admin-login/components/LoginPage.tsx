import React from 'react';
import { BrandSection } from './BrandSection';
import { LoginForm } from './LoginForm';

export const LoginPage: React.FC = () => {
  return (
    <div className="min-h-screen w-full flex bg-tech-light">
      {/* Left Side - Brand Section (50% width on Desktop, Hidden on Mobile) */}
      <BrandSection />

      {/* Right Side - Login Form (50% width on Desktop, Full on Mobile) */}
      <div className="flex-1 flex flex-col justify-center items-center bg-white lg:bg-white relative">
        {/* Corner Version Info */}
        <div className="absolute top-4 right-4 text-xs text-slate-400 hidden lg:block">
            Version 4.0.0 Build 20251119
        </div>
        
        <LoginForm />
      </div>
    </div>
  );
};