import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { aiAPI } from '../services/api';

export default function Insights() {
  const [insights, setInsights] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const fetchInsights = async () => {
      try {
        setLoading(true);
        // Mock data for now - replace with actual API call
        const mockInsights = [
          {
            id: 1,
            title: 'Campaign Performance Analysis',
            description: 'Analysis of your recent campaign performance',
            type: 'performance',
            date: '2024-01-15'
          },
          {
            id: 2,
            title: 'Publisher Recommendations',
            description: 'AI-generated publisher recommendations',
            type: 'recommendations',
            date: '2024-01-14'
          }
        ];
        setInsights(mockInsights);
      } catch (err) {
        setError('Failed to load insights');
      } finally {
        setLoading(false);
      }
    };
    fetchInsights();
  }, []);

  if (loading) {
    return <div className="p-8">Loading insights...</div>;
  }

  if (error) {
    return <div className="p-8 text-red-600">{error}</div>;
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-6">
            <div className="flex items-center">
              <Link href="/dashboard" className="text-gray-400 hover:text-gray-600">
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                </svg>
              </Link>
              <h1 className="ml-4 text-2xl font-bold text-gray-900">AI Insights</h1>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto py-8 px-4 sm:px-6 lg:px-8">
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-medium text-gray-900 mb-4">AI-Generated Insights</h2>
          <p className="text-gray-600 mb-6">
            Discover AI-powered insights about your campaigns and performance.
          </p>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {insights.map((insight) => (
              <div key={insight.id} className="border border-gray-200 rounded-lg p-4">
                <h3 className="font-medium text-gray-900 mb-2">{insight.title}</h3>
                <p className="text-sm text-gray-600 mb-3">{insight.description}</p>
                <div className="flex justify-between items-center">
                  <span className="text-xs text-gray-500">{insight.date}</span>
                  <span className={`px-2 py-1 text-xs rounded-full ${
                    insight.type === 'performance' 
                      ? 'bg-blue-100 text-blue-800' 
                      : 'bg-green-100 text-green-800'
                  }`}>
                    {insight.type}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
} 