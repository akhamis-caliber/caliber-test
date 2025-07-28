# Caliber Frontend

A modern React/Next.js frontend for the Caliber Scoring System.

## 🚀 Current Status

### ✅ Completed Features

- **Authentication System**: Firebase integration with fallback support
- **Dashboard**: Comprehensive dashboard with charts, stats, and activity feed
- **Navigation**: Responsive navbar with mobile menu
- **Layout System**: Consistent layout with error boundaries and loading states
- **API Integration**: Axios-based API service with token management
- **Component Library**: Reusable components (LoadingSpinner, ErrorBoundary, etc.)
- **Routing**: Protected routes with authentication guards

### 📁 Component Structure

```
components/
├── Auth/           # Authentication components
├── Dashboard/      # Dashboard-specific components
├── Shared/         # Reusable components
│   ├── Layout.jsx
│   ├── Navbar.jsx
│   ├── LoadingSpinner.jsx
│   ├── ErrorBoundary.jsx
│   ├── ToastContainer.jsx
│   ├── Breadcrumbs.jsx
│   └── PageHeader.jsx
└── CampaignWizard/ # Campaign creation (placeholder)
```

## 🛠️ Setup Instructions

### Prerequisites

- Node.js 18+
- npm or yarn

### Installation

```bash
# Install dependencies
npm install

# Copy environment template
cp env.template .env.local

# Edit .env.local with your Firebase configuration
```

### Environment Variables

Create a `.env.local` file with the following variables:

```env
# API Configuration
NEXT_PUBLIC_API_URL=http://localhost:8000

# Firebase Configuration (optional for development)
NEXT_PUBLIC_FIREBASE_API_KEY=your_firebase_api_key
NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN=your_project.firebaseapp.com
NEXT_PUBLIC_FIREBASE_PROJECT_ID=your_project_id
NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET=your_project.appspot.com
NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID=123456789
NEXT_PUBLIC_FIREBASE_APP_ID=your_app_id

# Application Configuration
NEXT_PUBLIC_APP_NAME=Caliber Scoring System
NEXT_PUBLIC_APP_VERSION=1.0.0
```

### Development

```bash
# Start development server
npm run dev

# Build for production
npm run build

# Start production server
npm start
```

## 🎨 Features

### Dashboard

- **Overview Cards**: Total campaigns, reports, average score, recent activity
- **Interactive Charts**: Scoring trends and reports overview using Recharts
- **Quick Actions**: Create campaigns and upload reports
- **Recent Activity Feed**: Real-time activity tracking with status indicators

### Navigation

- **Responsive Design**: Works on desktop, tablet, and mobile
- **User Menu**: Profile, settings, and logout functionality
- **Active State Indicators**: Visual feedback for current page
- **Mobile Hamburger Menu**: Collapsible navigation for mobile devices

### Authentication

- **Firebase Integration**: Email/password and Google authentication
- **Protected Routes**: Automatic redirection for unauthenticated users
- **Loading States**: Smooth loading experiences during auth checks
- **Error Handling**: Graceful fallbacks when Firebase is not configured

### API Integration

- **Token Management**: Automatic token handling and refresh
- **Error Interceptors**: Global error handling for API calls
- **Request/Response Interceptors**: Centralized API configuration

## 🔧 Technical Stack

- **Framework**: Next.js 14
- **Styling**: Tailwind CSS
- **Icons**: Heroicons
- **Charts**: Recharts
- **Authentication**: Firebase Auth
- **HTTP Client**: Axios
- **Notifications**: React Hot Toast
- **UI Components**: Headless UI

## 📱 Responsive Design

The application is fully responsive and optimized for:

- Desktop (1024px+)
- Tablet (768px - 1023px)
- Mobile (320px - 767px)

## 🚨 Error Handling

- **Error Boundaries**: Catches and displays React errors gracefully
- **Loading States**: Consistent loading indicators across the app
- **Toast Notifications**: User-friendly error and success messages
- **Fallback UI**: Graceful degradation when services are unavailable

## 🔒 Security

- **Protected Routes**: Authentication guards on all sensitive pages
- **Token Management**: Secure token storage and automatic refresh
- **Input Validation**: Form validation and sanitization
- **CORS Handling**: Proper cross-origin request handling

## 📈 Performance

- **Code Splitting**: Automatic code splitting by Next.js
- **Optimized Builds**: Production-optimized builds
- **Lazy Loading**: Components loaded on demand
- **Caching**: Efficient caching strategies

## 🧪 Testing

The application includes:

- **Component Testing**: Individual component testing
- **Integration Testing**: API integration testing
- **Error Testing**: Error boundary and fallback testing

## 📝 Development Notes

- Firebase configuration is optional for development
- Mock authentication is used when Firebase is not configured
- All components are designed to be reusable and maintainable
- Consistent error handling and loading states throughout the app

## 🚀 Deployment

The application can be deployed to:

- Vercel (recommended for Next.js)
- Netlify
- AWS Amplify
- Any static hosting service

## 📞 Support

For issues or questions:

1. Check the console for error messages
2. Verify environment variables are set correctly
3. Ensure all dependencies are installed
4. Check Firebase configuration if using authentication
