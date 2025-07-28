import React from 'react';

export const Progress = ({ value = 0, max = 100, className = '', ...props }) => {
  const percentage = Math.min(Math.max((value / max) * 100, 0), 100);
  
  const baseClasses = 'relative h-4 w-full overflow-hidden rounded-full bg-secondary';
  const indicatorClasses = 'h-full w-full flex-1 bg-primary transition-all';
  
  return (
    <div className={`${baseClasses} ${className}`} {...props}>
      <div 
        className={indicatorClasses}
        style={{ width: `${percentage}%` }}
      />
    </div>
  );
}; 