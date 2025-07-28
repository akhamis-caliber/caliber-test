import { useEffect } from 'react';
import { useRouter } from 'next/router';
import { useAuth } from '../context/AuthContext';
import LoadingSpinner from '../components/Shared/LoadingSpinner';

/**
 * Higher-order component to protect routes that require authentication
 * @param {React.Component} WrappedComponent - The component to wrap
 * @param {Object} options - Configuration options
 * @param {string} options.redirectTo - Where to redirect unauthenticated users (default: '/login')
 * @param {boolean} options.requireEmailVerification - Whether email verification is required (default: false)
 * @param {string} options.verificationRedirectTo - Where to redirect unverified users (default: '/verify-email')
 * @returns {React.Component} The wrapped component
 */
export function withAuth(WrappedComponent, options = {}) {
  const {
    redirectTo = '/login',
    requireEmailVerification = false,
    verificationRedirectTo = '/verify-email'
  } = options;

  return function AuthenticatedComponent(props) {
    const { user, loading } = useAuth();
    const router = useRouter();

    useEffect(() => {
      if (!loading) {
        // If user is not authenticated, redirect to login
        if (!user) {
          router.replace(redirectTo);
          return;
        }

        // If email verification is required and user is not verified
        if (requireEmailVerification && !user.emailVerified) {
          router.replace(verificationRedirectTo);
          return;
        }
      }
    }, [user, loading, router, redirectTo, requireEmailVerification, verificationRedirectTo]);

    // Show loading state while checking authentication
    if (loading) {
      return <LoadingSpinner size="lg" className="min-h-screen" text="Checking authentication..." />;
    }

    // If user is not authenticated, don't render the component
    if (!user) {
      return null;
    }

    // If email verification is required and user is not verified, don't render the component
    if (requireEmailVerification && !user.emailVerified) {
      return null;
    }

    // User is authenticated and verified (if required), render the component
    return <WrappedComponent {...props} />;
  };
}

/**
 * Hook to check if user has required permissions
 * @param {Array} requiredPermissions - Array of required permissions
 * @returns {Object} Object containing hasPermission boolean and missingPermissions array
 */
export function usePermissions(requiredPermissions = []) {
  const { user } = useAuth();

  if (!user || !requiredPermissions.length) {
    return { hasPermission: true, missingPermissions: [] };
  }

  // This is a placeholder - you would implement your own permission logic
  // based on your user model and permission system
  const userPermissions = user.permissions || [];
  
  const missingPermissions = requiredPermissions.filter(
    permission => !userPermissions.includes(permission)
  );

  return {
    hasPermission: missingPermissions.length === 0,
    missingPermissions
  };
}

/**
 * Component to conditionally render content based on permissions
 * @param {Object} props - Component props
 * @param {Array} props.permissions - Required permissions
 * @param {React.ReactNode} props.children - Content to render if user has permissions
 * @param {React.ReactNode} props.fallback - Content to render if user doesn't have permissions
 * @returns {React.ReactNode} Rendered content
 */
export function RequirePermissions({ permissions = [], children, fallback = null }) {
  const { hasPermission } = usePermissions(permissions);

  if (!hasPermission) {
    return fallback;
  }

  return children;
}

/**
 * Hook to get authentication status and user info
 * @returns {Object} Authentication status and user info
 */
export function useAuthStatus() {
  const { user, loading, backendToken } = useAuth();

  return {
    isAuthenticated: !!user,
    isEmailVerified: user?.emailVerified || false,
    isBackendAuthenticated: !!backendToken,
    user,
    loading
  };
}

/**
 * Utility function to check if a route requires authentication
 * @param {string} pathname - The route pathname
 * @param {Array} publicRoutes - Array of public route patterns
 * @returns {boolean} Whether the route requires authentication
 */
export function isProtectedRoute(pathname, publicRoutes = ['/login', '/register', '/forgot-password', '/reset-password']) {
  return !publicRoutes.some(route => {
    // Handle exact matches
    if (route === pathname) return true;
    
    // Handle wildcard patterns (e.g., '/auth/*')
    if (route.endsWith('/*')) {
      const baseRoute = route.slice(0, -2);
      return pathname.startsWith(baseRoute);
    }
    
    return false;
  });
}

/**
 * Utility function to get the appropriate redirect path based on authentication status
 * @param {Object} user - The current user object
 * @param {string} currentPath - The current pathname
 * @param {Object} options - Configuration options
 * @returns {string|null} The redirect path or null if no redirect is needed
 */
export function getAuthRedirectPath(user, currentPath, options = {}) {
  const {
    requireEmailVerification = false,
    verificationRedirectTo = '/verify-email',
    loginRedirectTo = '/login',
    dashboardRedirectTo = '/dashboard'
  } = options;

  // If user is not authenticated and trying to access protected route
  if (!user && isProtectedRoute(currentPath)) {
    return loginRedirectTo;
  }

  // If user is authenticated but email verification is required and not verified
  if (user && requireEmailVerification && !user.emailVerified && currentPath !== verificationRedirectTo) {
    return verificationRedirectTo;
  }

  // If user is authenticated and on auth pages, redirect to dashboard
  if (user && ['/login', '/register'].includes(currentPath)) {
    return dashboardRedirectTo;
  }

  return null;
} 