import Link from 'next/link';
import { ChevronRightIcon, HomeIcon, ChevronDoubleLeftIcon } from '@heroicons/react/24/outline';

interface BreadcrumbItem {
  label: string;
  href?: string;
  icon?: React.ComponentType<{ className?: string }>;
}

interface BreadcrumbsProps {
  items?: BreadcrumbItem[];
  showBackButton?: boolean;
  onBack?: () => void;
  className?: string;
}

export default function Breadcrumbs({ 
  items = [], 
  showBackButton = false, 
  onBack,
  className = '' 
}: BreadcrumbsProps) {
  const handleBack = () => {
    if (onBack) {
      onBack();
    } else {
      window.history.back();
    }
  };

  return (
    <nav className={`flex items-center justify-between ${className}`} aria-label="Breadcrumb">
      {/* Breadcrumb trail */}
      <div className="flex items-center space-x-2">
        {/* Back button */}
        {showBackButton && (
          <button
            onClick={handleBack}
            className="flex items-center px-2 py-1 text-sm text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200 transition-colors duration-200 rounded-md hover:bg-gray-100 dark:hover:bg-gray-700"
            aria-label="Go back"
          >
            <ChevronDoubleLeftIcon className="w-4 h-4 mr-1" />
            Back
          </button>
        )}
        
        {/* Home icon */}
        <Link
          href="/dashboard"
          className="flex items-center p-1 text-gray-400 hover:text-gray-500 dark:text-gray-500 dark:hover:text-gray-400 transition-colors duration-200 rounded-md hover:bg-gray-100 dark:hover:bg-gray-700"
          aria-label="Go to dashboard"
        >
          <HomeIcon className="w-4 h-4" />
          <span className="sr-only">Dashboard</span>
        </Link>
        
        {/* Breadcrumb items */}
        {items.map((item, index) => (
          <div key={index} className="flex items-center">
            <ChevronRightIcon className="w-4 h-4 text-gray-400 dark:text-gray-500 mx-1" />
            {index === items.length - 1 ? (
              <div className="flex items-center px-2 py-1 text-sm font-medium text-gray-900 dark:text-white bg-gray-100 dark:bg-gray-700 rounded-md">
                {item.icon && <item.icon className="w-4 h-4 mr-1" />}
                <span>{item.label}</span>
              </div>
            ) : (
              <Link
                href={item.href || '#'}
                className="flex items-center px-2 py-1 text-sm text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200 transition-colors duration-200 rounded-md hover:bg-gray-100 dark:hover:bg-gray-700"
              >
                {item.icon && <item.icon className="w-4 h-4 mr-1" />}
                <span>{item.label}</span>
              </Link>
            )}
          </div>
        ))}
      </div>

      {/* Optional right side content */}
      <div className="flex items-center space-x-2">
        {/* Add any additional actions or info here */}
      </div>
    </nav>
  );
} 