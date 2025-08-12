import React, { ReactNode, Suspense } from 'react';
import { useAuth } from '@/context/AuthContext';
import { useUIStore } from '@/store';
import Navbar from './Navbar';
import Sidebar from './Sidebar';
import ToastContainer from './ToastContainer';
import LoadingSpinner, { DashboardSkeleton } from './LoadingSpinner';
import ErrorBoundary from './ErrorBoundary';
import Breadcrumbs from './Breadcrumbs';

interface LayoutProps {
  children: ReactNode;
  showSidebar?: boolean;
  showNavbar?: boolean;
  breadcrumbs?: Array<{ label: string; href?: string; icon?: React.ComponentType<{ className?: string }> }>;
  showBackButton?: boolean;
  onBack?: () => void;
  loading?: boolean;
  error?: Error | null;
  onError?: (error: Error, errorInfo: any) => void;
}

const Layout: React.FC<LayoutProps> = ({ 
  children, 
  showSidebar = true, 
  showNavbar = true,
  breadcrumbs = [],
  showBackButton = false,
  onBack,
  loading = false,
  error = null,
  onError
}) => {
  const { loading: authLoading, user } = useAuth();
  const { sidebarOpen, theme } = useUIStore();

  // Apply theme to document
  React.useEffect(() => {
    document.documentElement.classList.toggle('dark', theme === 'dark');
  }, [theme]);

  // Show loading spinner while auth is loading
  if (authLoading) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center">
        <LoadingSpinner size="lg" text="Initializing..." />
      </div>
    );
  }

  // Show error if provided
  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center py-12 px-4">
        <div className="max-w-md w-full text-center">
          <div className="mx-auto h-24 w-24 bg-red-100 dark:bg-red-900/20 rounded-full flex items-center justify-center mb-6">
            <div className="h-12 w-12 bg-red-600 rounded-full"></div>
          </div>
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">
            Something went wrong
          </h2>
          <p className="text-gray-600 dark:text-gray-400 mb-6">
            {error.message || 'An unexpected error occurred'}
          </p>
          <button
            onClick={() => window.location.reload()}
            className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 transition-colors duration-200"
          >
            Refresh Page
          </button>
        </div>
      </div>
    );
  }

  return (
    <ErrorBoundary onError={onError}>
      <div className={`min-h-screen bg-gray-50 dark:bg-gray-900 transition-colors duration-200`}>
        {/* Toast Container */}
        <ToastContainer />
        
        {/* Navbar */}
        {showNavbar && <Navbar />}
        
        <div className="flex">
          {/* Sidebar */}
          {showSidebar && (
            <Sidebar 
              isOpen={sidebarOpen}
              className="transition-transform duration-300 ease-in-out"
            />
          )}
          
          {/* Main Content */}
          <main className={`flex-1 transition-all duration-300 ${
            showSidebar ? 'ml-0 lg:ml-64' : ''
          }`}>
            <div className="p-4 lg:p-6">
              {/* Breadcrumbs */}
              {breadcrumbs.length > 0 && (
                <div className="mb-6">
                  <Breadcrumbs 
                    items={breadcrumbs} 
                    showBackButton={showBackButton}
                    onBack={onBack}
                  />
                </div>
              )}
              
              {/* Content with Suspense and Loading States */}
              <Suspense fallback={<DashboardSkeleton />}>
                {loading ? (
                  <div className="space-y-6">
                    <DashboardSkeleton />
                  </div>
                ) : (
                  children
                )}
              </Suspense>
            </div>
          </main>
        </div>
      </div>
    </ErrorBoundary>
  );
};

export default Layout;



