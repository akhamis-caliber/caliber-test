import React from 'react';

interface LoadingSpinnerProps {
  size?: 'sm' | 'md' | 'lg' | 'xl';
  text?: string;
  className?: string;
  variant?: 'spinner' | 'dots' | 'pulse';
}

interface SkeletonProps {
  className?: string;
  lines?: number;
  height?: string;
  width?: string;
}

export default function LoadingSpinner({ 
  size = 'md', 
  text = 'Loading...', 
  className = '',
  variant = 'spinner'
}: LoadingSpinnerProps) {
  const sizeClasses = {
    sm: 'h-4 w-4',
    md: 'h-8 w-8',
    lg: 'h-12 w-12',
    xl: 'h-16 w-16'
  };

  const renderSpinner = () => {
    switch (variant) {
      case 'dots':
        return (
          <div className="flex space-x-1">
            <div className={`${sizeClasses[size]} bg-indigo-600 rounded-full animate-bounce`} style={{ animationDelay: '0ms' }}></div>
            <div className={`${sizeClasses[size]} bg-indigo-600 rounded-full animate-bounce`} style={{ animationDelay: '150ms' }}></div>
            <div className={`${sizeClasses[size]} bg-indigo-600 rounded-full animate-bounce`} style={{ animationDelay: '300ms' }}></div>
          </div>
        );
      case 'pulse':
        return (
          <div className={`${sizeClasses[size]} bg-indigo-600 rounded-full animate-pulse`}></div>
        );
      default:
        return (
          <div className={`animate-spin rounded-full border-b-2 border-indigo-600 ${sizeClasses[size]}`}></div>
        );
    }
  };

  return (
    <div className={`flex flex-col items-center justify-center ${className}`}>
      {renderSpinner()}
      {text && <p className="mt-2 text-sm text-gray-600 dark:text-gray-400">{text}</p>}
    </div>
  );
}

// Skeleton loader component
export function Skeleton({ className = '', lines = 1, height = 'h-4', width = 'w-full' }: SkeletonProps) {
  return (
    <div className={`animate-pulse ${className}`}>
      {Array.from({ length: lines }).map((_, index) => (
        <div
          key={index}
          className={`bg-gray-200 dark:bg-gray-700 rounded ${height} ${width} ${
            index < lines - 1 ? 'mb-2' : ''
          }`}
        />
      ))}
    </div>
  );
}

// Card skeleton loader
export function CardSkeleton({ className = '' }: { className?: string }) {
  return (
    <div className={`bg-white dark:bg-gray-800 rounded-lg shadow-sm p-6 ${className}`}>
      <div className="flex items-center space-x-4 mb-4">
        <Skeleton className="w-12 h-12 rounded-full" />
        <div className="flex-1">
          <Skeleton lines={2} />
        </div>
      </div>
      <Skeleton lines={3} />
    </div>
  );
}

// Table skeleton loader
export function TableSkeleton({ rows = 5, columns = 4, className = '' }: { rows?: number; columns?: number; className?: string }) {
  return (
    <div className={`bg-white dark:bg-gray-800 rounded-lg shadow-sm overflow-hidden ${className}`}>
      {/* Header */}
      <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
        <div className="flex space-x-4">
          {Array.from({ length: columns }).map((_, index) => (
            <Skeleton key={index} width="w-24" />
          ))}
        </div>
      </div>
      
      {/* Rows */}
      {Array.from({ length: rows }).map((_, rowIndex) => (
        <div key={rowIndex} className="px-6 py-4 border-b border-gray-200 dark:border-gray-700 last:border-b-0">
          <div className="flex space-x-4">
            {Array.from({ length: columns }).map((_, colIndex) => (
              <Skeleton key={colIndex} width="w-24" />
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}

// Form skeleton loader
export function FormSkeleton({ fields = 4, className = '' }: { fields?: number; className?: string }) {
  return (
    <div className={`bg-white dark:bg-gray-800 rounded-lg shadow-sm p-6 ${className}`}>
      <div className="space-y-6">
        {Array.from({ length: fields }).map((_, index) => (
          <div key={index}>
            <Skeleton width="w-32" className="mb-2" />
            <Skeleton height="h-10" />
          </div>
        ))}
        <div className="flex space-x-3 pt-4">
          <Skeleton width="w-24" height="h-10" />
          <Skeleton width="w-24" height="h-10" />
        </div>
      </div>
    </div>
  );
}

// Dashboard skeleton loader
export function DashboardSkeleton({ className = '' }: { className?: string }) {
  return (
    <div className={`space-y-6 ${className}`}>
      {/* Stats cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {Array.from({ length: 4 }).map((_, index) => (
          <CardSkeleton key={index} />
        ))}
      </div>
      
      {/* Chart area */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-6">
        <Skeleton width="w-48" className="mb-4" />
        <Skeleton height="h-64" />
      </div>
      
      {/* Table */}
      <TableSkeleton rows={5} columns={4} />
    </div>
  );
} 