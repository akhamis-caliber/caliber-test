import React, { useEffect, useRef } from 'react';

export default function AccessibilityWrapper({ 
  children, 
  role = 'region', 
  'aria-label': ariaLabel,
  'aria-describedby': ariaDescribedby,
  tabIndex = 0,
  onKeyDown,
  className = '',
  ...props 
}) {
  const ref = useRef(null);

  useEffect(() => {
    const element = ref.current;
    if (!element) return;

    // Focus management for modals and overlays
    if (role === 'dialog' || role === 'alertdialog') {
      element.focus();
      
      // Trap focus within the dialog
      const focusableElements = element.querySelectorAll(
        'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
      );
      
      const firstElement = focusableElements[0];
      const lastElement = focusableElements[focusableElements.length - 1];

      const handleKeyDown = (e) => {
        if (e.key === 'Tab') {
          if (e.shiftKey) {
            if (document.activeElement === firstElement) {
              e.preventDefault();
              lastElement.focus();
            }
          } else {
            if (document.activeElement === lastElement) {
              e.preventDefault();
              firstElement.focus();
            }
          }
        }
        
        if (e.key === 'Escape') {
          // Close modal on escape
          const closeEvent = new CustomEvent('closeModal');
          element.dispatchEvent(closeEvent);
        }
      };

      element.addEventListener('keydown', handleKeyDown);
      return () => element.removeEventListener('keydown', handleKeyDown);
    }
  }, [role]);

  return (
    <div
      ref={ref}
      role={role}
      aria-label={ariaLabel}
      aria-describedby={ariaDescribedby}
      tabIndex={tabIndex}
      onKeyDown={onKeyDown}
      className={className}
      {...props}
    >
      {children}
    </div>
  );
}

// Accessibility hook for managing focus
export function useFocusManagement() {
  const focusableRefs = useRef([]);

  const addFocusableRef = (ref) => {
    if (ref && !focusableRefs.current.includes(ref)) {
      focusableRefs.current.push(ref);
    }
  };

  const focusFirst = () => {
    if (focusableRefs.current.length > 0) {
      focusableRefs.current[0].focus();
    }
  };

  const focusLast = () => {
    if (focusableRefs.current.length > 0) {
      focusableRefs.current[focusableRefs.current.length - 1].focus();
    }
  };

  const focusNext = (currentRef) => {
    const currentIndex = focusableRefs.current.indexOf(currentRef);
    if (currentIndex < focusableRefs.current.length - 1) {
      focusableRefs.current[currentIndex + 1].focus();
    }
  };

  const focusPrevious = (currentRef) => {
    const currentIndex = focusableRefs.current.indexOf(currentRef);
    if (currentIndex > 0) {
      focusableRefs.current[currentIndex - 1].focus();
    }
  };

  return {
    addFocusableRef,
    focusFirst,
    focusLast,
    focusNext,
    focusPrevious
  };
}

// Skip link component for keyboard users
export function SkipLink({ href, children = 'Skip to main content' }) {
  return (
    <a
      href={href}
      className="sr-only focus:not-sr-only focus:absolute focus:top-4 focus:left-4 bg-indigo-600 text-white px-4 py-2 rounded-md z-50"
    >
      {children}
    </a>
  );
}

// Live region for announcements
export function LiveRegion({ 
  'aria-live': ariaLive = 'polite',
  'aria-atomic': ariaAtomic = true,
  children,
  className = 'sr-only'
}) {
  return (
    <div
      aria-live={ariaLive}
      aria-atomic={ariaAtomic}
      className={className}
    >
      {children}
    </div>
  );
} 