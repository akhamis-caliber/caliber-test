import React from 'react';
import { useEffect } from 'react';

export default function TestComponent() {
  useEffect(() => {
    console.log('TestComponent mounted successfully');
  }, []);

  return (
    <div className="p-4 bg-green-100 border border-green-300 rounded-lg">
      <h3 className="text-green-800 font-medium">✅ Component Test</h3>
      <p className="text-green-700 text-sm">This component is rendering correctly!</p>
    </div>
  );
} 