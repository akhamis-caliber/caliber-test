# Authentication System

This directory contains the authentication components and utilities for the Caliber frontend application.

## Components

### Login.jsx

A comprehensive login component with:

- Email/password authentication
- Google OAuth integration
- Form validation using react-hook-form and Zod
- Error handling with user-friendly messages
- Password visibility toggle
- Loading states

### Register.jsx

A registration component with:

- User registration form
- Password strength validation with visual indicators
- Email verification setup
- Google OAuth registration
- Form validation and error handling
- Password confirmation

### ForgotPassword.jsx

A password reset component with:

- Email input for password reset
- Success state with instructions
- Error handling
- Resend functionality

### EmailVerification.jsx

An email verification component with:

- Verification status display
- Resend verification email functionality
- Countdown timer for resend cooldown
- Manual refresh option

## Context

### AuthContext.js

The main authentication context that provides:

- Firebase authentication integration
- User state management
- Login/logout functions
- Google OAuth setup
- Backend token management
- Email verification functions

## Services

### firebase.js

Firebase service configuration and methods:

- Firebase app initialization
- Authentication methods (email/password, Google)
- User management functions
- Email verification and password reset

## Utilities

### authGuard.js

Authentication utilities including:

- `withAuth` - Higher-order component for protected routes
- `usePermissions` - Hook for permission checking
- `RequirePermissions` - Component for conditional rendering based on permissions
- `useAuthStatus` - Hook for authentication status
- `isProtectedRoute` - Utility to check if a route requires authentication
- `getAuthRedirectPath` - Utility to determine redirect paths

## Usage Examples

### Protecting a Route

```jsx
import { withAuth } from "../utils/authGuard";

function Dashboard() {
  return <div>Protected Dashboard Content</div>;
}

export default withAuth(Dashboard);
```

### Using Authentication Context

```jsx
import { useAuth } from "../context/AuthContext";

function MyComponent() {
  const { user, login, logout } = useAuth();

  if (!user) {
    return <div>Please log in</div>;
  }

  return <div>Welcome, {user.displayName}!</div>;
}
```

### Permission-Based Rendering

```jsx
import { RequirePermissions } from "../utils/authGuard";

function AdminPanel() {
  return (
    <RequirePermissions permissions={["admin"]}>
      <div>Admin content</div>
    </RequirePermissions>
  );
}
```

## Environment Variables

Make sure to set up the following environment variables:

```env
NEXT_PUBLIC_FIREBASE_API_KEY=your_firebase_api_key
NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN=your_project.firebaseapp.com
NEXT_PUBLIC_FIREBASE_PROJECT_ID=your_project_id
NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET=your_project.appspot.com
NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID=your_sender_id
NEXT_PUBLIC_FIREBASE_APP_ID=your_app_id
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Features

- **Firebase Integration**: Complete Firebase Authentication setup
- **Google OAuth**: Seamless Google sign-in integration
- **Form Validation**: Robust validation using react-hook-form and Zod
- **Error Handling**: Comprehensive error handling with user-friendly messages
- **Loading States**: Proper loading indicators for better UX
- **Password Strength**: Visual password strength indicators
- **Email Verification**: Complete email verification flow
- **Password Reset**: Secure password reset functionality
- **Route Protection**: HOC for protecting routes
- **Permission System**: Flexible permission-based access control
- **Responsive Design**: Mobile-friendly UI components
- **Accessibility**: Proper ARIA labels and keyboard navigation

## Security Features

- Firebase ID token verification with backend
- Secure password requirements
- Email verification for new accounts
- Rate limiting for password reset requests
- Protected route access
- Token-based authentication
- Automatic logout on token expiration

## Dependencies

- `firebase` - Firebase SDK
- `react-hook-form` - Form handling
- `@hookform/resolvers` - Form validation resolvers
- `zod` - Schema validation
- `react-hot-toast` - Toast notifications
- `next/router` - Next.js routing
- `tailwindcss` - Styling
