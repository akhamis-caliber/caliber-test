import React, { useState } from 'react';
import Layout from '../components/Shared/Layout';
import Breadcrumbs from '../components/Shared/Breadcrumbs';
import LoadingSpinner, { 
  Skeleton, 
  CardSkeleton, 
  TableSkeleton, 
  FormSkeleton, 
  DashboardSkeleton 
} from '../components/Shared/LoadingSpinner';
import { 
  ChartBarIcon, 
  DocumentTextIcon, 
  CogIcon, 
  UserIcon,
  BellIcon,
  ExclamationTriangleIcon
} from '@heroicons/react/24/outline';

export default function LayoutDemo() {
  const [loading, setLoading] = useState(false);
  const [showError, setShowError] = useState(false);
  const [currentSection, setCurrentSection] = useState('overview');

  const breadcrumbs = [
    { label: 'Dashboard', href: '/dashboard', icon: ChartBarIcon },
    { label: 'Layout Demo', href: '/layout-demo' }
  ];

  const demoBreadcrumbs = [
    { label: 'Campaigns', href: '/campaigns', icon: DocumentTextIcon },
    { label: 'Create Campaign', href: '/campaigns/new' },
    { label: 'Step 2: Template', href: '/campaigns/new/template' }
  ];

  const simulateLoading = () => {
    setLoading(true);
    setTimeout(() => setLoading(false), 3000);
  };

  const simulateError = () => {
    setShowError(true);
    setTimeout(() => setShowError(false), 5000);
  };

  const sections = [
    { id: 'overview', name: 'Overview', icon: ChartBarIcon },
    { id: 'breadcrumbs', name: 'Breadcrumbs', icon: DocumentTextIcon },
    { id: 'loading', name: 'Loading States', icon: CogIcon },
    { id: 'skeletons', name: 'Skeleton Loaders', icon: UserIcon },
    { id: 'notifications', name: 'Notifications', icon: BellIcon },
    { id: 'errors', name: 'Error Handling', icon: ExclamationTriangleIcon }
  ];

  const renderSection = () => {
    switch (currentSection) {
      case 'breadcrumbs':
        return (
          <div className="space-y-6">
            <div>
              <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">
                Breadcrumb Navigation
              </h3>
              <div className="space-y-4">
                <div>
                  <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Basic Breadcrumbs
                  </h4>
                  <Breadcrumbs items={breadcrumbs} />
                </div>
                <div>
                  <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Breadcrumbs with Back Button
                  </h4>
                  <Breadcrumbs 
                    items={demoBreadcrumbs} 
                    showBackButton={true}
                    onBack={() => alert('Back button clicked!')}
                  />
                </div>
              </div>
            </div>
          </div>
        );

      case 'loading':
        return (
          <div className="space-y-6">
            <div>
              <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">
                Loading States
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                <div className="text-center">
                  <LoadingSpinner size="sm" text="Small" />
                </div>
                <div className="text-center">
                  <LoadingSpinner size="md" text="Medium" />
                </div>
                <div className="text-center">
                  <LoadingSpinner size="lg" text="Large" />
                </div>
                <div className="text-center">
                  <LoadingSpinner size="xl" text="Extra Large" />
                </div>
              </div>
              <div className="mt-6 grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="text-center">
                  <LoadingSpinner variant="dots" text="Dots" />
                </div>
                <div className="text-center">
                  <LoadingSpinner variant="pulse" text="Pulse" />
                </div>
                <div className="text-center">
                  <LoadingSpinner variant="spinner" text="Spinner" />
                </div>
              </div>
            </div>
          </div>
        );

      case 'skeletons':
        return (
          <div className="space-y-6">
            <div>
              <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">
                Skeleton Loaders
              </h3>
              <div className="space-y-6">
                <div>
                  <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Basic Skeleton
                  </h4>
                  <Skeleton lines={3} height="h-4" />
                </div>
                <div>
                  <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Card Skeleton
                  </h4>
                  <CardSkeleton />
                </div>
                <div>
                  <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Table Skeleton
                  </h4>
                  <TableSkeleton rows={3} columns={4} />
                </div>
                <div>
                  <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Form Skeleton
                  </h4>
                  <FormSkeleton fields={5} />
                </div>
                <div>
                  <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Dashboard Skeleton
                  </h4>
                  <DashboardSkeleton />
                </div>
              </div>
            </div>
          </div>
        );

      case 'notifications':
        return (
          <div className="space-y-6">
            <div>
              <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">
                Notification System
              </h3>
              <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-6">
                <p className="text-gray-600 dark:text-gray-400 mb-4">
                  The notification system is integrated into the navbar. Click the bell icon in the top-right corner to see notifications.
                </p>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="p-4 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg">
                    <div className="flex items-center">
                      <div className="flex-shrink-0">
                        <div className="w-8 h-8 bg-green-100 dark:bg-green-900/40 rounded-full flex items-center justify-center">
                          <span className="text-green-600 dark:text-green-400">✅</span>
                        </div>
                      </div>
                      <div className="ml-3">
                        <p className="text-sm font-medium text-green-800 dark:text-green-200">
                          Success Notification
                        </p>
                        <p className="text-sm text-green-700 dark:text-green-300">
                          This is an example success notification
                        </p>
                      </div>
                    </div>
                  </div>
                  <div className="p-4 bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg">
                    <div className="flex items-center">
                      <div className="flex-shrink-0">
                        <div className="w-8 h-8 bg-yellow-100 dark:bg-yellow-900/40 rounded-full flex items-center justify-center">
                          <span className="text-yellow-600 dark:text-yellow-400">⚠️</span>
                        </div>
                      </div>
                      <div className="ml-3">
                        <p className="text-sm font-medium text-yellow-800 dark:text-yellow-200">
                          Warning Notification
                        </p>
                        <p className="text-sm text-yellow-700 dark:text-yellow-300">
                          This is an example warning notification
                        </p>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        );

      case 'errors':
        return (
          <div className="space-y-6">
            <div>
              <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">
                Error Handling
              </h3>
              <div className="space-y-4">
                <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-6">
                  <p className="text-gray-600 dark:text-gray-400 mb-4">
                    The application includes comprehensive error boundaries and error handling. Try the buttons below to see different error scenarios.
                  </p>
                  <div className="flex space-x-3">
                    <button
                      onClick={simulateError}
                      className="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 transition-colors duration-200"
                    >
                      Simulate Error
                    </button>
                    <button
                      onClick={() => window.location.reload()}
                      className="px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700 transition-colors duration-200"
                    >
                      Reload Page
                    </button>
                  </div>
                  {showError && (
                    <div className="mt-4 p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
                      <div className="flex items-center">
                        <ExclamationTriangleIcon className="h-5 w-5 text-red-600 dark:text-red-400 mr-2" />
                        <p className="text-sm text-red-800 dark:text-red-200">
                          This is a simulated error message. In a real application, this would be handled by the error boundary.
                        </p>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        );

      default:
        return (
          <div className="space-y-6">
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-6">
              <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">
                Layout & Navigation Features
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    ✅ Responsive Navbar
                  </h4>
                  <ul className="text-sm text-gray-600 dark:text-gray-400 space-y-1">
                    <li>• User menu with profile options</li>
                    <li>• Notification system with badge</li>
                    <li>• Create menu with quick actions</li>
                    <li>• Mobile-responsive design</li>
                  </ul>
                </div>
                <div>
                  <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    ✅ Sidebar Navigation
                  </h4>
                  <ul className="text-sm text-gray-600 dark:text-gray-400 space-y-1">
                    <li>• Collapsible sections</li>
                    <li>• Hierarchical navigation</li>
                    <li>• Quick action buttons</li>
                    <li>• Theme toggle</li>
                  </ul>
                </div>
                <div>
                  <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    ✅ Breadcrumbs
                  </h4>
                  <ul className="text-sm text-gray-600 dark:text-gray-400 space-y-1">
                    <li>• Page navigation hierarchy</li>
                    <li>• Back button support</li>
                    <li>• Icon support</li>
                    <li>• Responsive design</li>
                  </ul>
                </div>
                <div>
                  <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    ✅ Loading States
                  </h4>
                  <ul className="text-sm text-gray-600 dark:text-gray-400 space-y-1">
                    <li>• Multiple spinner variants</li>
                    <li>• Skeleton loaders</li>
                    <li>• Card, table, form skeletons</li>
                    <li>• Dashboard skeleton</li>
                  </ul>
                </div>
              </div>
            </div>

            <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-6">
              <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                🚀 Interactive Demo
              </h4>
              <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
                Use the navigation tabs above to explore different features. Each section demonstrates specific functionality.
              </p>
              <div className="flex space-x-3">
                <button
                  onClick={simulateLoading}
                  className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors duration-200"
                >
                  {loading ? 'Loading...' : 'Simulate Loading'}
                </button>
                <button
                  onClick={() => setCurrentSection('breadcrumbs')}
                  className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 transition-colors duration-200"
                >
                  View Breadcrumbs
                </button>
              </div>
            </div>
          </div>
        );
    }
  };

  if (loading) {
    return (
      <Layout>
        <div className="space-y-6">
          <DashboardSkeleton />
        </div>
      </Layout>
    );
  }

  return (
    <Layout breadcrumbs={breadcrumbs}>
      <div className="space-y-6">
        {/* Section Navigation */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm">
          <div className="border-b border-gray-200 dark:border-gray-700">
            <nav className="flex space-x-8 px-6" aria-label="Tabs">
              {sections.map((section) => (
                <button
                  key={section.id}
                  onClick={() => setCurrentSection(section.id)}
                  className={`py-4 px-1 border-b-2 font-medium text-sm transition-colors duration-200 ${
                    currentSection === section.id
                      ? 'border-indigo-500 text-indigo-600 dark:text-indigo-400'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300 dark:text-gray-400 dark:hover:text-gray-300'
                  }`}
                >
                  <div className="flex items-center space-x-2">
                    <section.icon className="w-4 h-4" />
                    <span>{section.name}</span>
                  </div>
                </button>
              ))}
            </nav>
          </div>
        </div>

        {/* Content */}
        {renderSection()}
      </div>
    </Layout>
  );
}
