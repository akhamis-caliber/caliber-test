'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/router';
import { useAuth } from '@/context/AuthContext';
import { LoginForm } from '@/components/Auth/LoginForm';
import { RegisterForm } from '@/components/Auth/RegisterForm';
import { ForgotPasswordForm } from '@/components/Auth/ForgotPasswordForm';
import { Layout } from '@/components/Shared/Layout';

type AuthView = 'login' | 'register' | 'forgot-password';

export default function AuthPage() {
  const [currentView, setCurrentView] = useState<AuthView>('login');
  const { user, loading } = useAuth();
  const router = useRouter();

  // Redirect if already authenticated
  React.useEffect(() => {
    if (user && !loading) {
      router.push('/dashboard');
    }
  }, [user, loading, router]);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600 dark:text-gray-400">Loading...</p>
        </div>
      </div>
    );
  }

  if (user) {
    return null; // Will redirect
  }

  const renderAuthForm = () => {
    switch (currentView) {
      case 'login':
        return (
          <LoginForm
            onSwitchToRegister={() => setCurrentView('register')}
            onForgotPassword={() => setCurrentView('forgot-password')}
          />
        );
      case 'register':
        return (
          <RegisterForm
            onSwitchToLogin={() => setCurrentView('login')}
          />
        );
      case 'forgot-password':
        return (
          <ForgotPasswordForm
            onBackToLogin={() => setCurrentView('login')}
          />
        );
      default:
        return <LoginForm />;
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md mx-auto">
        {/* Logo/Brand */}
        <div className="text-center mb-8">
          <div className="mx-auto h-16 w-16 bg-blue-600 rounded-full flex items-center justify-center mb-4">
            <svg
              className="h-8 w-8 text-white"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
              />
            </svg>
          </div>
          <h1 className="text-4xl font-bold text-gray-900 dark:text-white">
            Caliber
          </h1>
          <p className="mt-2 text-lg text-gray-600 dark:text-gray-400">
            Campaign Optimization Platform
          </p>
        </div>

        {/* Auth Form */}
        <div className="transition-all duration-300 ease-in-out">
          {renderAuthForm()}
        </div>

        {/* Footer */}
        <div className="mt-8 text-center">
          <p className="text-sm text-gray-500 dark:text-gray-400">
            © 2024 Caliber. All rights reserved.
          </p>
          <div className="mt-2 flex justify-center space-x-4 text-xs text-gray-400 dark:text-gray-500">
            <a href="#" className="hover:text-gray-600 dark:hover:text-gray-300">
              Privacy Policy
            </a>
            <a href="#" className="hover:text-gray-600 dark:hover:text-gray-300">
              Terms of Service
            </a>
            <a href="#" className="hover:text-gray-600 dark:hover:text-gray-300">
              Support
            </a>
          </div>
        </div>
      </div>
    </div>
  );
}



