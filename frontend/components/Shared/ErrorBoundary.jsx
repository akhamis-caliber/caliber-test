import { Component } from 'react';
import { ExclamationTriangleIcon, ArrowPathIcon, HomeIcon, InformationCircleIcon } from '@heroicons/react/24/outline';

interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
  errorInfo: any;
  errorId: string;
  retryCount: number;
}

interface ErrorBoundaryProps {
  children: React.ReactNode;
  fallback?: React.ComponentType<{ error: Error; errorInfo: any; retry: () => void }>;
  onError?: (error: Error, errorInfo: any) => void;
  maxRetries?: number;
}

class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = { 
      hasError: false, 
      error: null, 
      errorInfo: null,
      errorId: '',
      retryCount: 0
    };
  }

  static getDerivedStateFromError(error: Error): Partial<ErrorBoundaryState> {
    return { hasError: true };
  }

  componentDidCatch(error: Error, errorInfo: any) {
    const errorId = `error_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    
    this.setState({
      error: error,
      errorInfo: errorInfo,
      errorId: errorId
    });
    
    // Log error to console in development
    if (process.env.NODE_ENV === 'development') {
      console.error('Error caught by boundary:', error, errorInfo);
    }

    // Call custom error handler if provided
    if (this.props.onError) {
      this.props.onError(error, errorInfo);
    }

    // In production, you might want to send this to an error reporting service
    if (process.env.NODE_ENV === 'production') {
      // Example: sendErrorToService(error, errorInfo, errorId);
    }
  }

  handleRetry = () => {
    const { maxRetries = 3 } = this.props;
    const { retryCount } = this.state;

    if (retryCount < maxRetries) {
      this.setState(prevState => ({
        hasError: false,
        error: null,
        errorInfo: null,
        errorId: '',
        retryCount: prevState.retryCount + 1
      }));
    } else {
      // Reset retry count and show permanent error
      this.setState({
        retryCount: 0
      });
    }
  };

  handleGoHome = () => {
    window.location.href = '/dashboard';
  };

  render() {
    if (this.state.hasError) {
      // Use custom fallback if provided
      if (this.props.fallback) {
        const FallbackComponent = this.props.fallback;
        return (
          <FallbackComponent 
            error={this.state.error!} 
            errorInfo={this.state.errorInfo} 
            retry={this.handleRetry}
          />
        );
      }

      // Default error UI
      return (
        <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900 py-12 px-4 sm:px-6 lg:px-8">
          <div className="max-w-md w-full space-y-8">
            <div className="text-center">
              <div className="mx-auto h-24 w-24 bg-red-100 dark:bg-red-900/20 rounded-full flex items-center justify-center">
                <ExclamationTriangleIcon className="h-12 w-12 text-red-600 dark:text-red-400" />
              </div>
              
              <h2 className="mt-6 text-3xl font-extrabold text-gray-900 dark:text-white">
                Something went wrong
              </h2>
              
              <p className="mt-2 text-sm text-gray-600 dark:text-gray-400">
                We're sorry, but something unexpected happened. Our team has been notified.
              </p>

              {this.state.errorId && (
                <div className="mt-4 p-3 bg-gray-100 dark:bg-gray-800 rounded-md">
                  <div className="flex items-center text-sm text-gray-600 dark:text-gray-400">
                    <InformationCircleIcon className="h-4 w-4 mr-2" />
                    Error ID: {this.state.errorId}
                  </div>
                </div>
              )}

              <div className="mt-6 space-y-3">
                <button
                  onClick={this.handleRetry}
                  className="w-full inline-flex items-center justify-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 transition-colors duration-200"
                >
                  <ArrowPathIcon className="w-4 h-4 mr-2" />
                  {this.state.retryCount === 0 ? 'Try Again' : `Retry (${this.state.retryCount}/${this.props.maxRetries || 3})`}
                </button>
                
                <button
                  onClick={this.handleGoHome}
                  className="w-full inline-flex items-center justify-center px-4 py-2 border border-gray-300 dark:border-gray-600 text-sm font-medium rounded-md text-gray-700 dark:text-gray-200 bg-white dark:bg-gray-800 hover:bg-gray-50 dark:hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 transition-colors duration-200"
                >
                  <HomeIcon className="w-4 h-4 mr-2" />
                  Go to Dashboard
                </button>
              </div>

              {this.state.retryCount >= (this.props.maxRetries || 3) && (
                <div className="mt-4 p-3 bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-md">
                  <p className="text-sm text-yellow-800 dark:text-yellow-200">
                    Multiple retry attempts failed. Please contact support if the problem persists.
                  </p>
                </div>
              )}

              {process.env.NODE_ENV === 'development' && this.state.error && (
                <details className="mt-6 text-left">
                  <summary className="cursor-pointer text-sm text-gray-600 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200">
                    Error Details (Development)
                  </summary>
                  <div className="mt-2 text-xs bg-red-50 dark:bg-red-900/20 p-3 rounded border border-red-200 dark:border-red-800 overflow-auto max-h-64">
                    <div className="font-mono text-red-600 dark:text-red-400">
                      <div className="font-semibold mb-2">Error:</div>
                      <div className="mb-2">{this.state.error.toString()}</div>
                      
                      {this.state.errorInfo && this.state.errorInfo.componentStack && (
                        <>
                          <div className="font-semibold mb-2">Component Stack:</div>
                          <div className="whitespace-pre-wrap">{this.state.errorInfo.componentStack}</div>
                        </>
                      )}
                    </div>
                  </div>
                </details>
              )}
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary; 