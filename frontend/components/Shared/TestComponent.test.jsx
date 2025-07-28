import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import { AuthProvider } from '../../context/AuthContext';
import TestComponent from './TestComponent';

// Mock Next.js router
jest.mock('next/router', () => ({
  useRouter() {
    return {
      route: '/',
      pathname: '/',
      query: {},
      asPath: '/',
      push: jest.fn(),
      pop: jest.fn(),
      reload: jest.fn(),
      back: jest.fn(),
      prefetch: jest.fn().mockResolvedValue(undefined),
      beforePopState: jest.fn(),
      events: {
        on: jest.fn(),
        off: jest.fn(),
        emit: jest.fn(),
      },
      isFallback: false,
    };
  },
}));

// Mock API calls
jest.mock('../../services/api', () => ({
  authAPI: {
    login: jest.fn(),
    register: jest.fn(),
    logout: jest.fn(),
  },
  campaignAPI: {
    getCampaigns: jest.fn(),
    createCampaign: jest.fn(),
    updateCampaign: jest.fn(),
    deleteCampaign: jest.fn(),
  },
  reportAPI: {
    uploadFile: jest.fn(),
    getReports: jest.fn(),
    getReportStatus: jest.fn(),
  },
  userAPI: {
    getProfile: jest.fn(),
    updateProfile: jest.fn(),
    getSettings: jest.fn(),
    updateSettings: jest.fn(),
    changePassword: jest.fn(),
  },
}));

// Mock toast notifications
jest.mock('react-hot-toast', () => ({
  success: jest.fn(),
  error: jest.fn(),
  loading: jest.fn(),
}));

// Test wrapper component
const TestWrapper = ({ children }) => (
  <AuthProvider>
    {children}
  </AuthProvider>
);

describe('Frontend Components', () => {
  beforeEach(() => {
    // Clear all mocks before each test
    jest.clearAllMocks();
  });

  describe('Authentication Components', () => {
    test('Login form renders correctly', () => {
      render(
        <TestWrapper>
          <TestComponent />
        </TestWrapper>
      );
      
      expect(screen.getByText('Test Component')).toBeInTheDocument();
    });

    test('Form validation works correctly', async () => {
      render(
        <TestWrapper>
          <TestComponent />
        </TestWrapper>
      );

      const emailInput = screen.getByLabelText(/email/i);
      const passwordInput = screen.getByLabelText(/password/i);
      const submitButton = screen.getByRole('button', { name: /submit/i });

      // Test empty form submission
      fireEvent.click(submitButton);
      
      await waitFor(() => {
        expect(screen.getByText(/email is required/i)).toBeInTheDocument();
        expect(screen.getByText(/password is required/i)).toBeInTheDocument();
      });

      // Test invalid email
      fireEvent.change(emailInput, { target: { value: 'invalid-email' } });
      fireEvent.click(submitButton);
      
      await waitFor(() => {
        expect(screen.getByText(/invalid email format/i)).toBeInTheDocument();
      });

      // Test valid form submission
      fireEvent.change(emailInput, { target: { value: 'test@example.com' } });
      fireEvent.change(passwordInput, { target: { value: 'password123' } });
      fireEvent.click(submitButton);
      
      await waitFor(() => {
        expect(screen.queryByText(/email is required/i)).not.toBeInTheDocument();
        expect(screen.queryByText(/password is required/i)).not.toBeInTheDocument();
      });
    });
  });

  describe('Campaign Wizard Components', () => {
    test('Step navigation works correctly', () => {
      render(
        <TestWrapper>
          <TestComponent />
        </TestWrapper>
      );

      const nextButton = screen.getByRole('button', { name: /next/i });
      const backButton = screen.getByRole('button', { name: /back/i });

      // Test next button
      fireEvent.click(nextButton);
      expect(screen.getByText(/step 2/i)).toBeInTheDocument();

      // Test back button
      fireEvent.click(backButton);
      expect(screen.getByText(/step 1/i)).toBeInTheDocument();
    });

    test('Form data persistence across steps', () => {
      render(
        <TestWrapper>
          <TestComponent />
        </TestWrapper>
      );

      const nameInput = screen.getByLabelText(/campaign name/i);
      fireEvent.change(nameInput, { target: { value: 'Test Campaign' } });

      const nextButton = screen.getByRole('button', { name: /next/i });
      fireEvent.click(nextButton);

      // Data should persist
      expect(screen.getByDisplayValue('Test Campaign')).toBeInTheDocument();
    });
  });

  describe('File Upload Component', () => {
    test('File validation works correctly', () => {
      render(
        <TestWrapper>
          <TestComponent />
        </TestWrapper>
      );

      const fileInput = screen.getByLabelText(/upload file/i);
      
      // Test invalid file type
      const invalidFile = new File(['test'], 'test.txt', { type: 'text/plain' });
      fireEvent.change(fileInput, { target: { files: [invalidFile] } });
      
      expect(screen.getByText(/please select a csv or excel file/i)).toBeInTheDocument();

      // Test valid file
      const validFile = new File(['test'], 'test.csv', { type: 'text/csv' });
      fireEvent.change(fileInput, { target: { files: [validFile] } });
      
      expect(screen.queryByText(/please select a csv or excel file/i)).not.toBeInTheDocument();
    });

    test('File size validation', () => {
      render(
        <TestWrapper>
          <TestComponent />
        </TestWrapper>
      );

      const fileInput = screen.getByLabelText(/upload file/i);
      
      // Create a large file (11MB)
      const largeFile = new File(['x'.repeat(11 * 1024 * 1024)], 'large.csv', { type: 'text/csv' });
      fireEvent.change(fileInput, { target: { files: [largeFile] } });
      
      expect(screen.getByText(/file size must be less than 10mb/i)).toBeInTheDocument();
    });
  });

  describe('Dashboard Components', () => {
    test('Loading states display correctly', () => {
      render(
        <TestWrapper>
          <TestComponent />
        </TestWrapper>
      );

      const loadingButton = screen.getByRole('button', { name: /loading/i });
      expect(loadingButton).toBeDisabled();
      expect(screen.getByText(/loading.../i)).toBeInTheDocument();
    });

    test('Error handling displays messages', async () => {
      render(
        <TestWrapper>
          <TestComponent />
        </TestWrapper>
      );

      const errorButton = screen.getByRole('button', { name: /trigger error/i });
      fireEvent.click(errorButton);

      await waitFor(() => {
        expect(screen.getByText(/an error occurred/i)).toBeInTheDocument();
      });
    });
  });

  describe('Responsive Design', () => {
    test('Mobile navigation works', () => {
      // Mock mobile viewport
      Object.defineProperty(window, 'innerWidth', {
        writable: true,
        configurable: true,
        value: 768,
      });

      render(
        <TestWrapper>
          <TestComponent />
        </TestWrapper>
      );

      const mobileMenuButton = screen.getByRole('button', { name: /menu/i });
      fireEvent.click(mobileMenuButton);

      expect(screen.getByText(/mobile menu/i)).toBeInTheDocument();
    });
  });

  describe('Accessibility', () => {
    test('All interactive elements have proper ARIA labels', () => {
      render(
        <TestWrapper>
          <TestComponent />
        </TestWrapper>
      );

      const buttons = screen.getAllByRole('button');
      buttons.forEach(button => {
        expect(button).toHaveAttribute('aria-label');
      });

      const inputs = screen.getAllByRole('textbox');
      inputs.forEach(input => {
        expect(input).toHaveAttribute('aria-label');
      });
    });

    test('Keyboard navigation works', () => {
      render(
        <TestWrapper>
          <TestComponent />
        </TestWrapper>
      );

      const firstButton = screen.getByRole('button', { name: /first/i });
      const secondButton = screen.getByRole('button', { name: /second/i });

      firstButton.focus();
      expect(firstButton).toHaveFocus();

      // Test tab navigation
      fireEvent.keyDown(document, { key: 'Tab' });
      expect(secondButton).toHaveFocus();
    });

    test('Screen reader announcements work', () => {
      render(
        <TestWrapper>
          <TestComponent />
        </TestWrapper>
      );

      const liveRegion = screen.getByRole('status');
      expect(liveRegion).toHaveAttribute('aria-live', 'polite');
    });
  });

  describe('API Integration', () => {
    test('Successful API calls show success messages', async () => {
      const { authAPI } = require('../../services/api');
      authAPI.login.mockResolvedValue({ data: { user: { id: 1, email: 'test@example.com' } } });

      render(
        <TestWrapper>
          <TestComponent />
        </TestWrapper>
      );

      const loginButton = screen.getByRole('button', { name: /login/i });
      fireEvent.click(loginButton);

      await waitFor(() => {
        expect(authAPI.login).toHaveBeenCalledWith({
          email: 'test@example.com',
          password: 'password123'
        });
      });
    });

    test('Failed API calls show error messages', async () => {
      const { authAPI } = require('../../services/api');
      authAPI.login.mockRejectedValue(new Error('Invalid credentials'));

      render(
        <TestWrapper>
          <TestComponent />
        </TestWrapper>
      );

      const loginButton = screen.getByRole('button', { name: /login/i });
      fireEvent.click(loginButton);

      await waitFor(() => {
        expect(screen.getByText(/invalid credentials/i)).toBeInTheDocument();
      });
    });
  });

  describe('State Management', () => {
    test('Form state updates correctly', () => {
      render(
        <TestWrapper>
          <TestComponent />
        </TestWrapper>
      );

      const input = screen.getByLabelText(/test input/i);
      fireEvent.change(input, { target: { value: 'new value' } });

      expect(input).toHaveValue('new value');
    });

    test('Component re-renders on state changes', () => {
      render(
        <TestWrapper>
          <TestComponent />
        </TestWrapper>
      );

      const toggleButton = screen.getByRole('button', { name: /toggle/i });
      
      expect(screen.getByText(/hidden content/i)).not.toBeVisible();
      
      fireEvent.click(toggleButton);
      
      expect(screen.getByText(/hidden content/i)).toBeVisible();
    });
  });
}); 