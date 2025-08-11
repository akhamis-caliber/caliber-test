import React from 'react';
import Link from 'next/link';
import { useRouter } from 'next/router';
import { useAuth } from '@/context/AuthContext';
import { useUIStore } from '@/store';
import { cn } from '@/utils/cn';
import {
  HomeIcon,
  ChartBarIcon,
  DocumentTextIcon,
  CogIcon,
  UserIcon,
  FolderIcon,
  ChartPieIcon,
  DocumentDuplicateIcon,
  XMarkIcon,
  Bars3Icon,
} from '@heroicons/react/24/outline';

interface SidebarProps {
  isOpen: boolean;
  className?: string;
}

interface NavigationItem {
  name: string;
  href: string;
  icon: React.ComponentType<{ className?: string }>;
  badge?: string | number;
  children?: NavigationItem[];
}

const Sidebar: React.FC<SidebarProps> = ({ isOpen, className }) => {
  const router = useRouter();
  const { user } = useAuth();
  const { sidebarOpen, setSidebarOpen, toggleSidebar } = useUIStore();

  const navigation: NavigationItem[] = [
    {
      name: 'Dashboard',
      href: '/dashboard',
      icon: HomeIcon,
    },
    {
      name: 'Campaigns',
      href: '/campaigns',
      icon: ChartBarIcon,
      children: [
        { name: 'All Campaigns', href: '/campaigns', icon: DocumentTextIcon },
        { name: 'Create Campaign', href: '/campaigns/new', icon: DocumentDuplicateIcon },
        { name: 'Templates', href: '/campaigns/templates', icon: FolderIcon },
      ],
    },
    {
      name: 'Reports',
      href: '/reports',
      icon: DocumentTextIcon,
      children: [
        { name: 'All Reports', href: '/reports', icon: DocumentTextIcon },
        { name: 'Upload Report', href: '/upload', icon: DocumentDuplicateIcon },
      ],
    },
    {
      name: 'Scoring',
      href: '/scoring-results',
      icon: ChartPieIcon,
      children: [
        { name: 'Scoring Results', href: '/scoring-results', icon: ChartPieIcon },
        { name: 'Scoring Config', href: '/scoring-config', icon: CogIcon },
      ],
    },
    {
      name: 'Analytics',
      href: '/insights',
      icon: ChartBarIcon,
    },
    {
      name: 'Settings',
      href: '/settings',
      icon: CogIcon,
      children: [
        { name: 'Profile', href: '/profile', icon: UserIcon },
        { name: 'Account Settings', href: '/settings', icon: CogIcon },
      ],
    },
  ];

  const isActiveRoute = (href: string) => {
    return router.pathname === href || router.pathname.startsWith(href + '/');
  };

  const renderNavigationItem = (item: NavigationItem, level = 0) => {
    const isActive = isActiveRoute(item.href);
    const hasChildren = item.children && item.children.length > 0;
    
    const baseClasses = cn(
      'group flex items-center px-3 py-2 text-sm font-medium rounded-md transition-colors duration-200',
      level === 0 ? 'mx-2 mb-1' : 'ml-6 mr-2 mb-1',
      isActive
        ? 'bg-blue-100 text-blue-900 dark:bg-blue-900 dark:text-blue-100'
        : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900 dark:text-gray-300 dark:hover:bg-gray-700 dark:hover:text-white'
    );

    const iconClasses = cn(
      'mr-3 h-5 w-5 flex-shrink-0',
      isActive
        ? 'text-blue-500 dark:text-blue-400'
        : 'text-gray-400 group-hover:text-gray-500 dark:group-hover:text-gray-300'
    );

    return (
      <div key={item.href}>
        <Link
          href={item.href}
          className={baseClasses}
          onClick={() => {
            if (level === 0 && !hasChildren) {
              setSidebarOpen(false);
            }
          }}
        >
          <item.icon className={iconClasses} />
          <span className="flex-1">{item.name}</span>
          {item.badge && (
            <span className="ml-auto inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200">
              {item.badge}
            </span>
          )}
        </Link>
        
        {hasChildren && (
          <div className="mt-1">
            {item.children!.map((child) => renderNavigationItem(child, level + 1))}
          </div>
        )}
      </div>
    );
  };

  return (
    <>
      {/* Mobile backdrop */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 z-40 bg-gray-600 bg-opacity-75 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar */}
      <div
        className={cn(
          'fixed inset-y-0 left-0 z-50 w-64 bg-white dark:bg-gray-800 shadow-lg transform transition-transform duration-300 ease-in-out lg:translate-x-0 lg:static lg:inset-0',
          sidebarOpen ? 'translate-x-0' : '-translate-x-full',
          className
        )}
      >
        {/* Header */}
        <div className="flex items-center justify-between h-16 px-4 border-b border-gray-200 dark:border-gray-700">
          <div className="flex items-center">
            <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center">
              <span className="text-white font-bold text-lg">C</span>
            </div>
            <span className="ml-3 text-xl font-semibold text-gray-900 dark:text-white">
              Caliber
            </span>
          </div>
          
          {/* Close button for mobile */}
          <button
            onClick={() => setSidebarOpen(false)}
            className="lg:hidden p-2 rounded-md text-gray-400 hover:text-gray-500 hover:bg-gray-100 dark:hover:bg-gray-700"
          >
            <XMarkIcon className="h-6 w-6" />
          </button>
        </div>

        {/* User info */}
        {user && (
          <div className="px-4 py-3 border-b border-gray-200 dark:border-gray-700">
            <div className="flex items-center">
              <div className="w-8 h-8 bg-gray-300 dark:bg-gray-600 rounded-full flex items-center justify-center">
                <UserIcon className="h-5 w-5 text-gray-600 dark:text-gray-300" />
              </div>
              <div className="ml-3">
                <p className="text-sm font-medium text-gray-900 dark:text-white">
                  {user.full_name}
                </p>
                <p className="text-xs text-gray-500 dark:text-gray-400">
                  {user.role}
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Navigation */}
        <nav className="flex-1 px-2 py-4 space-y-1 overflow-y-auto">
          {navigation.map((item) => renderNavigationItem(item))}
        </nav>

        {/* Footer */}
        <div className="px-4 py-3 border-t border-gray-200 dark:border-gray-700">
          <button
            onClick={() => useUIStore.getState().toggleTheme()}
            className="w-full flex items-center px-3 py-2 text-sm font-medium text-gray-600 rounded-md hover:bg-gray-100 hover:text-gray-900 dark:text-gray-300 dark:hover:bg-gray-700 dark:hover:text-white transition-colors duration-200"
          >
            <CogIcon className="mr-3 h-5 w-5 text-gray-400" />
            <span className="flex-1">Toggle Theme</span>
          </button>
        </div>
      </div>

      {/* Mobile menu button */}
      <button
        onClick={toggleSidebar}
        className="lg:hidden fixed top-4 left-4 z-50 p-2 rounded-md bg-white dark:bg-gray-800 shadow-lg text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white hover:bg-gray-100 dark:hover:bg-gray-700"
      >
        <Bars3Icon className="h-6 w-6" />
      </button>
    </>
  );
};

export default Sidebar;



