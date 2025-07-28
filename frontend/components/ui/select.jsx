import React from 'react';

export const Select = ({ children, value, onValueChange, className = '', ...props }) => {
  return (
    <select
      value={value}
      onChange={(e) => onValueChange?.(e.target.value)}
      className={`px-3 py-2 text-sm border border-gray-300 rounded-md bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-indigo-500 ${className}`}
      {...props}
    >
      {children}
    </select>
  );
};

export const SelectTrigger = ({ children, className = '', ...props }) => (
  <button
    className={`flex items-center justify-between w-full px-3 py-2 text-sm border border-gray-300 rounded-md bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-indigo-500 ${className}`}
    {...props}
  >
    {children}
    <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
    </svg>
  </button>
);

export const SelectValue = ({ value, placeholder = "Select an option" }) => (
  <span className="text-gray-900">
    {value || placeholder}
  </span>
);

export const SelectContent = ({ children, className = '', ...props }) => (
  <div
    className={`absolute z-50 w-full mt-1 bg-white border border-gray-300 rounded-md shadow-lg max-h-60 overflow-auto ${className}`}
    {...props}
  >
    {children}
  </div>
);

export const SelectItem = ({ children, value, onSelect, className = '', ...props }) => (
  <div
    className={`px-3 py-2 text-sm text-gray-900 hover:bg-gray-100 cursor-pointer ${className}`}
    onClick={onSelect}
    {...props}
  >
    {children}
  </div>
); 