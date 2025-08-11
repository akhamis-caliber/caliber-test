'use client';

import React from 'react';
import { ProtectedRoute } from '@/components/Auth/ProtectedRoute';
import { Layout } from '@/components/Shared/Layout';
import { useAuth } from '@/context/AuthContext';
import { Button } from '@/components/ui/Button';
import { useUIStore } from '@/store';

export default function DashboardPage() {
  const { user, logout } = useAuth();
  const { showToast } = useUIStore();

  const handleLogout = async () => {
    try {
      await logout();
      showToast({
        type: 'success',
        message: 'Successfully logged out!',
        duration: 3000
      });
    } catch (error) {
      showToast({
        type: 'error',
        message: 'Logout failed. Please try again.',
        duration: 5000
      });
    }
  };

  return (
    <ProtectedRoute>
      <Layout>
        <div className="p-6">
          <div className="max-w-7xl mx-auto">
            {/* Header */}
            <div className="mb-8">
              <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
                Dashboard
              </h1>
              <p className="mt-2 text-gray-600 dark:text-gray-400">
                Welcome back, {user?.full_name || user?.email}!
              </p>
            </div>

            {/* User Info Card */}
            <div className="bg-white dark:bg-gray-800 shadow rounded-lg p-6 mb-6">
              <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
                User Information
              </h2>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                    Full Name
                  </label>
                  <p className="mt-1 text-sm text-gray-900 dark:text-white">
                    {user?.full_name || 'Not provided'}
                  </p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                    Email
                  </label>
                  <p className="mt-1 text-sm text-gray-900 dark:text-white">
                    {user?.email}
                  </p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                    Role
                  </label>
                  <p className="mt-1 text-sm text-gray-900 dark:text-white capitalize">
                    {user?.role}
                  </p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                    Organization
                  </label>
                  <p className="mt-1 text-sm text-gray-900 dark:text-white">
                    {user?.organization?.name || 'Not assigned'}
                  </p>
                </div>
              </div>
            </div>

            {/* Quick Actions */}
            <div className="bg-white dark:bg-gray-800 shadow rounded-lg p-6 mb-6">
              <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
                Quick Actions
              </h2>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <Button
                  onClick={() => showToast({
                    type: 'info',
                    message: 'Campaign creation coming soon!',
                    duration: 3000
                  })}
                  variant="outline"
                  className="h-20 flex flex-col items-center justify-center"
                >
                  <svg className="w-8 h-8 mb-2 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                  </svg>
                  Create Campaign
                </Button>
                
                <Button
                  onClick={() => showToast({
                    type: 'info',
                    message: 'Report generation coming soon!',
                    duration: 3000
                  })}
                  variant="outline"
                  className="h-20 flex flex-col items-center justify-center"
                >
                  <svg className="w-8 h-8 mb-2 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                  Generate Report
                </Button>
                
                <Button
                  onClick={() => showToast({
                    type: 'info',
                    message: 'Analytics dashboard coming soon!',
                    duration: 3000
                  })}
                  variant="outline"
                  className="h-20 flex flex-col items-center justify-center"
                >
                  <svg className="w-8 h-8 mb-2 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                  </svg>
                  View Analytics
                </Button>
              </div>
            </div>

            {/* Logout Section */}
            <div className="bg-white dark:bg-gray-800 shadow rounded-lg p-6">
              <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
                Account
              </h2>
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600 dark:text-gray-400">
                    Ready to sign out?
                  </p>
                </div>
                <Button
                  onClick={handleLogout}
                  variant="outline"
                  className="text-red-600 border-red-300 hover:bg-red-50 dark:text-red-400 dark:border-red-600 dark:hover:bg-red-900/20"
                >
                  Sign Out
                </Button>
              </div>
            </div>
          </div>
        </div>
      </Layout>
    </ProtectedRoute>
  );
}



