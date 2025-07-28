import React, { useState, useRef, useEffect } from 'react';

export const DropdownMenu = ({ children, ...props }) => {
  return <div {...props}>{children}</div>;
};

export const DropdownMenuTrigger = ({ children, asChild = false, ...props }) => {
  return <button {...props}>{children}</button>;
};

export const DropdownMenuContent = ({ children, className = '', ...props }) => {
  const baseClasses = 'z-50 min-w-[8rem] overflow-hidden rounded-md border bg-popover p-1 text-popover-foreground shadow-md data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0 data-[state=closed]:zoom-out-95 data-[state=open]:zoom-in-95 data-[side=bottom]:slide-in-from-top-2 data-[side=left]:slide-in-from-right-2 data-[side=right]:slide-in-from-left-2 data-[side=top]:slide-in-from-bottom-2';
  
  return (
    <div className={`${baseClasses} ${className}`} {...props}>
      {children}
    </div>
  );
};

export const DropdownMenuItem = ({ children, className = '', ...props }) => {
  const baseClasses = 'relative flex cursor-default select-none items-center rounded-sm px-2 py-1.5 text-sm outline-none transition-colors focus:bg-accent focus:text-accent-foreground data-[disabled]:pointer-events-none data-[disabled]:opacity-50';
  
  return (
    <div className={`${baseClasses} ${className}`} {...props}>
      {children}
    </div>
  );
};

export const DropdownMenuCheckboxItem = ({ children, checked, onCheckedChange, className = '', ...props }) => {
  const baseClasses = 'relative flex cursor-default select-none items-center rounded-sm px-2 py-1.5 text-sm outline-none transition-colors focus:bg-accent focus:text-accent-foreground data-[disabled]:pointer-events-none data-[disabled]:opacity-50';
  
  return (
    <div 
      className={`${baseClasses} ${className}`} 
      onClick={() => onCheckedChange?.(!checked)}
      {...props}
    >
      <span className="mr-2">
        {checked && (
          <svg className="h-4 w-4" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
          </svg>
        )}
      </span>
      {children}
    </div>
  );
};

export const DropdownMenuLabel = ({ children, className = '', ...props }) => {
  const baseClasses = 'px-2 py-1.5 text-sm font-semibold';
  
  return (
    <div className={`${baseClasses} ${className}`} {...props}>
      {children}
    </div>
  );
};

export const DropdownMenuSeparator = ({ className = '', ...props }) => {
  const baseClasses = '-mx-1 my-1 h-px bg-muted';
  
  return <div className={`${baseClasses} ${className}`} {...props} />;
}; 