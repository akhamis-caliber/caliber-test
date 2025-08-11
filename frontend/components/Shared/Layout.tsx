import React, { ReactNode } from 'react';
import { useAuth } from '@/context/AuthContext';
import { useUIStore } from '@/store';
import Navbar from './Navbar';
import Sidebar from './Sidebar';
import ToastContainer from './ToastContainer';
import LoadingSpinner from './LoadingSpinner';

interface LayoutProps {
  children: ReactNode;
  showSidebar?: boolean;
  showNavbar?: boolean;
}

const Layout: React.FC<LayoutProps> = ({ 
  children, 
  showSidebar = true, 
  showNavbar = true 
}) => {
  const { loading: authLoading } = useAuth();
  const { sidebarOpen, theme } = useUIStore();

  // Apply theme to document
  React.useEffect(() => {
    document.documentElement.classList.toggle('dark', theme === 'dark');
  }, [theme]);

  if (authLoading) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  return (
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
            {children}
          </div>
        </main>
      </div>
    </div>
  );
};

export default Layout;



