import React, { useState } from 'react';
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
  ChevronDownIcon,
  ChevronRightIcon,
  BellIcon,
  EyeIcon,
  EyeSlashIcon,
  SunIcon,
  MoonIcon,
  PlusIcon,
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
  description?: string;
}

const Sidebar: React.FC<SidebarProps> = ({ isOpen, className }) => {
  const router = useRouter();
  const { user } = useAuth();
  const { sidebarOpen, setSidebarOpen, toggleSidebar, theme, toggleTheme } = useUIStore();
  const [expandedSections, setExpandedSections] = useState<Set<string>>(new Set(['Dashboard']));

  const navigation: NavigationItem[] = [
    {
      name: 'Dashboard',
      href: '/dashboard',
      icon: HomeIcon,
      description: 'Overview and key metrics'
    },
    {
      name: 'Campaigns',
      href: '/campaigns',
      icon: ChartBarIcon,
      description: 'Manage marketing campaigns',
      children: [
        { name: 'All Campaigns', href: '/campaigns', icon: DocumentTextIcon, description: 'View all campaigns' },
        { name: 'Create Campaign', href: '/campaigns/new', icon: DocumentDuplicateIcon, description: 'Start new campaign' },
        { name: 'Templates', href: '/campaigns/templates', icon: FolderIcon, description: 'Campaign templates' },
        { name: 'Analytics', href: '/campaigns/analytics', icon: ChartBarIcon, description: 'Campaign performance' },
      ],
    },
    {
      name: 'Reports',
      href: '/reports',
      icon: DocumentTextIcon,
      description: 'Data analysis and insights',
      children: [
        { name: 'All Reports', href: '/reports', icon: DocumentTextIcon, description: 'View all reports' },
        { name: 'Upload Report', href: '/upload', icon: DocumentDuplicateIcon, description: 'Upload new data' },
        { name: 'Export Data', href: '/reports/export', icon: DocumentDuplicateIcon, description: 'Export reports' },
      ],
    },
    {
      name: 'Scoring',
      href: '/scoring-results',
      icon: ChartPieIcon,
      description: 'AI-powered scoring system',
      children: [
        { name: 'Scoring Results', href: '/scoring-results', icon: ChartPieIcon, description: 'View scoring outcomes' },
        { name: 'Scoring Config', href: '/scoring-config', icon: CogIcon, description: 'Configure scoring rules' },
        { name: 'Model Training', href: '/scoring/training', icon: ChartBarIcon, description: 'Train scoring models' },
      ],
    },
    {
      name: 'Analytics',
      href: '/insights',
      icon: ChartBarIcon,
      description: 'Advanced analytics and insights',
      children: [
        { name: 'Performance Metrics', href: '/insights/performance', icon: ChartBarIcon, description: 'Key performance indicators' },
        { name: 'Trend Analysis', href: '/insights/trends', icon: ChartPieIcon, description: 'Trend identification' },
        { name: 'Predictive Models', href: '/insights/predictions', icon: ChartBarIcon, description: 'AI predictions' },
      ],
    },
    {
      name: 'Settings',
      href: '/settings',
      icon: CogIcon,
      description: 'System configuration',
      children: [
        { name: 'Profile', href: '/profile', icon: UserIcon, description: 'User profile settings' },
        { name: 'Account Settings', href: '/settings', icon: CogIcon, description: 'Account configuration' },
        { name: 'Team Management', href: '/settings/team', icon: UserIcon, description: 'Manage team members' },
        { name: 'API Keys', href: '/settings/api', icon: CogIcon, description: 'API configuration' },
      ],
    },
  ];

  const isActiveRoute = (href: string) => {
    return router.pathname === href || router.pathname.startsWith(href + '/');
  };

  const toggleSection = (sectionName: string) => {
    setExpandedSections(prev => {
      const newSet = new Set(prev);
      if (newSet.has(sectionName)) {
        newSet.delete(sectionName);
      } else {
        newSet.add(sectionName);
      }
      return newSet;
    });
  };

  const renderNavigationItem = (item: NavigationItem, level = 0) => {
    const isActive = isActiveRoute(item.href);
    const hasChildren = item.children && item.children.length > 0;
    const isExpanded = expandedSections.has(item.name);
    
    const baseClasses = cn(
      'group flex items-center px-3 py-2 text-sm font-medium rounded-md transition-all duration-200 cursor-pointer',
      level === 0 ? 'mx-2 mb-1' : 'ml-6 mr-2 mb-1',
      isActive
        ? 'bg-blue-100 text-blue-900 dark:bg-blue-900 dark:text-blue-100 shadow-sm'
        : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900 dark:text-gray-300 dark:hover:bg-gray-700 dark:hover:text-white'
    );

    const iconClasses = cn(
      'mr-3 h-5 w-5 flex-shrink-0 transition-colors duration-200',
      isActive
        ? 'text-blue-500 dark:text-blue-400'
        : 'text-gray-400 group-hover:text-gray-500 dark:group-hover:text-gray-300'
    );

    if (level === 0 && hasChildren) {
      return (
        <div key={item.href} className="space-y-1">
          <button
            onClick={() => toggleSection(item.name)}
            className={cn(
              baseClasses,
              'w-full justify-between group'
            )}
          >
            <div className="flex items-center">
              <item.icon className={iconClasses} />
              <span className="flex-1 text-left">{item.name}</span>
            </div>
            {isExpanded ? (
              <ChevronDownIcon className="h-4 w-4 text-gray-400 group-hover:text-gray-500 transition-transform duration-200" />
            ) : (
              <ChevronRightIcon className="h-4 w-4 text-gray-400 group-hover:text-gray-500 transition-transform duration-200" />
            )}
          </button>
          
          {item.description && (
            <p className="ml-11 text-xs text-gray-500 dark:text-gray-400 mb-2">
              {item.description}
            </p>
          )}
          
          {isExpanded && hasChildren && (
            <div className="mt-1 space-y-1">
              {item.children!.map((child) => renderNavigationItem(child, level + 1))}
            </div>
          )}
        </div>
      );
    }

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
          <div className="flex-1 text-left">
            <span>{item.name}</span>
            {item.description && level > 0 && (
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                {item.description}
              </p>
            )}
          </div>
          {item.badge && (
            <span className="ml-auto inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200">
              {item.badge}
            </span>
          )}
        </Link>
        
        {hasChildren && level > 0 && (
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
            className="lg:hidden p-2 rounded-md text-gray-400 hover:text-gray-500 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors duration-200"
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
              <div className="ml-3 flex-1">
                <p className="text-sm font-medium text-gray-900 dark:text-white">
                  {user.full_name || user.displayName || 'User'}
                </p>
                <p className="text-xs text-gray-500 dark:text-gray-400">
                  {user.role || 'Member'}
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Quick Actions */}
        <div className="px-4 py-3 border-b border-gray-200 dark:border-gray-700">
          <div className="space-y-2">
            <Link
              href="/campaigns/new"
              className="w-full flex items-center px-3 py-2 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 rounded-md transition-colors duration-200"
            >
              <PlusIcon className="w-4 h-4 mr-2" />
              New Campaign
            </Link>
            <Link
              href="/upload"
              className="w-full flex items-center px-3 py-2 text-sm font-medium text-gray-700 dark:text-gray-200 bg-gray-100 hover:bg-gray-200 dark:bg-gray-700 dark:hover:bg-gray-600 rounded-md transition-colors duration-200"
            >
              <DocumentDuplicateIcon className="w-4 h-4 mr-2" />
              Upload Data
            </Link>
          </div>
        </div>

        {/* Navigation */}
        <nav className="flex-1 px-2 py-4 space-y-1 overflow-y-auto">
          {navigation.map((item) => renderNavigationItem(item))}
        </nav>

        {/* Footer */}
        <div className="px-4 py-3 border-t border-gray-200 dark:border-gray-700 space-y-2">
          {/* Theme Toggle */}
          <button
            onClick={toggleTheme}
            className="w-full flex items-center px-3 py-2 text-sm font-medium text-gray-600 rounded-md hover:bg-gray-100 hover:text-gray-900 dark:text-gray-300 dark:hover:bg-gray-700 dark:hover:text-white transition-colors duration-200"
          >
            {theme === 'dark' ? (
              <SunIcon className="mr-3 h-5 w-5 text-yellow-500" />
            ) : (
              <MoonIcon className="mr-3 h-5 w-5 text-gray-400" />
            )}
            <span className="flex-1 text-left">
              {theme === 'dark' ? 'Light Mode' : 'Dark Mode'}
            </span>
          </button>
          
          {/* Sidebar Toggle */}
          <button
            onClick={() => setSidebarOpen(false)}
            className="w-full flex items-center px-3 py-2 text-sm font-medium text-gray-600 rounded-md hover:bg-gray-100 hover:text-gray-900 dark:text-gray-300 dark:hover:bg-gray-700 dark:hover:text-white transition-colors duration-200 lg:hidden"
          >
            <EyeSlashIcon className="mr-3 h-5 w-5 text-gray-400" />
            <span className="flex-1 text-left">Hide Sidebar</span>
          </button>
        </div>
      </div>

      {/* Mobile menu button */}
      <button
        onClick={toggleSidebar}
        className="lg:hidden fixed top-4 left-4 z-50 p-2 rounded-md bg-white dark:bg-gray-800 shadow-lg text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors duration-200"
      >
        <Bars3Icon className="h-6 w-6" />
      </button>
    </>
  );
};

export default Sidebar;



