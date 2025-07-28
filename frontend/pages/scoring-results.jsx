import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/router';
import Link from 'next/link';
import { scoringAPI } from '../services/api';
import toast from 'react-hot-toast';

const channels = ['All', 'Display', 'Video', 'CTV', 'Audio'];
const scoreRanges = ['All', '90-100', '80-89', '70-79', '60-69', '0-59'];

export default function ScoringResults() {
  const router = useRouter();
  const { campaign_id } = router.query;
  
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [summary, setSummary] = useState({});
  const [filters, setFilters] = useState({
    scoreRange: 'All',
    channel: 'All',
    publisher: ''
  });
  const [selectedExport, setSelectedExport] = useState('csv');
  const [generatingList, setGeneratingList] = useState(false);

  useEffect(() => {
    if (campaign_id) {
      fetchScoringResults();
    }
  }, [campaign_id, filters]);

  const fetchScoringResults = async () => {
    try {
      setLoading(true);
      setError('');
      
      const params = {
        score_range: filters.scoreRange !== 'All' ? filters.scoreRange : undefined,
        channel: filters.channel !== 'All' ? filters.channel : undefined,
        publisher: filters.publisher || undefined,
        limit: 1000
      };
      
      const response = await scoringAPI.getDetailedScoringResults(campaign_id, params);
      setResults(response.data.results || []);
      setSummary(response.data.summary || {});
    } catch (err) {
      console.error('Failed to fetch scoring results:', err);
      setError(err.response?.data?.detail || 'Failed to load scoring results. Please try again.');
      toast.error('Failed to load scoring results');
    } finally {
      setLoading(false);
    }
  };

  const getScoreColor = (score) => {
    if (score >= 90) return 'text-green-600 bg-green-100';
    if (score >= 80) return 'text-blue-600 bg-blue-100';
    if (score >= 70) return 'text-yellow-600 bg-yellow-100';
    return 'text-red-600 bg-red-100';
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'Good': return 'text-green-600 bg-green-100';
      case 'Moderate': return 'text-yellow-600 bg-yellow-100';
      case 'Poor': return 'text-red-600 bg-red-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  const generateWhitelist = async () => {
    try {
      setGeneratingList(true);
      const response = await scoringAPI.generateWhitelist(campaign_id, 25);
      const whitelist = response.data.results;
      
      // Export whitelist as CSV
      const csvContent = [
        'Domain,Publisher,CPM,CTR,Conversion Rate,Score,Status,Channel',
        ...whitelist.map(item => 
          `${item.domain},${item.publisher},${item.cpm},${(item.ctr * 100).toFixed(2)}%,${(item.conversion_rate * 100).toFixed(2)}%,${item.score},${item.score >= 80 ? 'Good' : item.score >= 60 ? 'Moderate' : 'Poor'},${item.channel}`
        )
      ].join('\n');
      
      const blob = new Blob([csvContent], { type: 'text/csv' });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `whitelist-top-25-campaign-${campaign_id}.csv`;
      a.click();
      
      toast.success(`Whitelist generated with ${whitelist.length} items`);
    } catch (err) {
      console.error('Failed to generate whitelist:', err);
      toast.error('Failed to generate whitelist');
    } finally {
      setGeneratingList(false);
    }
  };

  const generateBlacklist = async () => {
    try {
      setGeneratingList(true);
      const response = await scoringAPI.generateBlacklist(campaign_id, 25);
      const blacklist = response.data.results;
      
      // Export blacklist as CSV
      const csvContent = [
        'Domain,Publisher,CPM,CTR,Conversion Rate,Score,Status,Channel',
        ...blacklist.map(item => 
          `${item.domain},${item.publisher},${item.cpm},${(item.ctr * 100).toFixed(2)}%,${(item.conversion_rate * 100).toFixed(2)}%,${item.score},${item.score >= 80 ? 'Good' : item.score >= 60 ? 'Moderate' : 'Poor'},${item.channel}`
        )
      ].join('\n');
      
      const blob = new Blob([csvContent], { type: 'text/csv' });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `blacklist-bottom-25-campaign-${campaign_id}.csv`;
      a.click();
      
      toast.success(`Blacklist generated with ${blacklist.length} items`);
    } catch (err) {
      console.error('Failed to generate blacklist:', err);
      toast.error('Failed to generate blacklist');
    } finally {
      setGeneratingList(false);
    }
  };

  const exportData = () => {
    const data = results.map(result => ({
      Domain: result.domain,
      Publisher: result.publisher,
      CPM: result.cpm,
      CTR: `${(result.ctr * 100).toFixed(2)}%`,
      'Conversion Rate': `${(result.conversion_rate * 100).toFixed(2)}%`,
      Score: result.score,
      Status: result.status,
      Channel: result.channel
    }));

    if (selectedExport === 'csv') {
      const csvContent = [
        Object.keys(data[0]).join(','),
        ...data.map(row => Object.values(row).join(','))
      ].join('\n');
      
      const blob = new Blob([csvContent], { type: 'text/csv' });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `scoring-results-campaign-${campaign_id}.csv`;
      a.click();
      toast.success('CSV exported successfully');
    } else {
      // PDF export would be implemented here
      console.log('PDF export:', data);
      toast.info('PDF export coming soon');
    }
  };

  if (!campaign_id) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <h3 className="text-lg font-medium text-gray-900 mb-2">Campaign ID Required</h3>
          <p className="text-gray-600 mb-4">Please select a campaign to view scoring results.</p>
          <Link
            href="/campaigns"
            className="bg-indigo-600 text-white px-6 py-3 rounded-md font-medium hover:bg-indigo-700 transition-colors"
          >
            View Campaigns
          </Link>
        </div>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading scoring results...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center max-w-md mx-auto p-6">
          <div className="text-red-500 mb-4">
            <svg className="w-16 h-16 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
            </svg>
          </div>
          <h3 className="text-lg font-medium text-gray-900 mb-2">Failed to Load Results</h3>
          <p className="text-gray-600 mb-4">{error}</p>
          <button
            onClick={fetchScoringResults}
            className="bg-indigo-600 text-white px-4 py-2 rounded-md hover:bg-indigo-700 transition-colors"
          >
            Try Again
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-6">
            <div className="flex items-center">
              <Link href="/campaigns" className="text-gray-400 hover:text-gray-600">
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                </svg>
              </Link>
              <h1 className="ml-4 text-2xl font-bold text-gray-900">Scoring Results</h1>
              <span className="ml-2 text-sm text-gray-500">Campaign #{campaign_id}</span>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto py-8 px-4 sm:px-6 lg:px-8">
        {/* Summary Stats */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center">
              <div className="p-2 bg-blue-100 rounded-lg">
                <svg className="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                </svg>
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Total Records</p>
                <p className="text-2xl font-bold text-gray-900">{summary.total_records || 0}</p>
              </div>
            </div>
          </div>
          
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center">
              <div className="p-2 bg-green-100 rounded-lg">
                <svg className="w-5 h-5 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Average Score</p>
                <p className="text-2xl font-bold text-gray-900">
                  {summary.average_score ? summary.average_score.toFixed(1) : '0.0'}
                </p>
              </div>
            </div>
          </div>
          
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center">
              <div className="p-2 bg-green-100 rounded-lg">
                <svg className="w-5 h-5 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">High Performing</p>
                <p className="text-2xl font-bold text-gray-900">{summary.high_performing || 0}</p>
              </div>
            </div>
          </div>
          
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center">
              <div className="p-2 bg-red-100 rounded-lg">
                <svg className="w-5 h-5 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Low Performing</p>
                <p className="text-2xl font-bold text-gray-900">{summary.low_performing || 0}</p>
              </div>
            </div>
          </div>
        </div>

        {/* Filters and Actions */}
        <div className="bg-white rounded-lg shadow mb-6">
          <div className="px-6 py-4 border-b border-gray-200">
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between">
              <h2 className="text-lg font-medium text-gray-900 mb-4 sm:mb-0">
                Results ({results.length} items)
              </h2>
              
              {/* Export Options */}
              <div className="flex items-center space-x-4">
                <div className="flex items-center space-x-2">
                  <label className="text-sm font-medium text-gray-700">Export:</label>
                  <select
                    value={selectedExport}
                    onChange={(e) => setSelectedExport(e.target.value)}
                    className="border border-gray-300 rounded-md px-3 py-1 text-sm"
                  >
                    <option value="csv">CSV</option>
                    <option value="pdf">PDF</option>
                  </select>
                  <button
                    onClick={exportData}
                    className="px-3 py-1 bg-gray-600 text-white text-sm rounded-md hover:bg-gray-700"
                  >
                    Export
                  </button>
                </div>
                
                <div className="flex items-center space-x-2">
                  <button
                    onClick={generateWhitelist}
                    disabled={generatingList}
                    className="px-3 py-1 bg-green-600 text-white text-sm rounded-md hover:bg-green-700 disabled:opacity-50"
                  >
                    {generatingList ? 'Generating...' : 'Generate Whitelist'}
                  </button>
                  <button
                    onClick={generateBlacklist}
                    disabled={generatingList}
                    className="px-3 py-1 bg-red-600 text-white text-sm rounded-md hover:bg-red-700 disabled:opacity-50"
                  >
                    {generatingList ? 'Generating...' : 'Generate Blacklist'}
                  </button>
                </div>
              </div>
            </div>
          </div>

          {/* Filters */}
          <div className="px-6 py-4">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Score Range
                </label>
                <select
                  value={filters.scoreRange}
                  onChange={(e) => setFilters({...filters, scoreRange: e.target.value})}
                  className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
                >
                  {scoreRanges.map(range => (
                    <option key={range} value={range}>{range}</option>
                  ))}
                </select>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Channel
                </label>
                <select
                  value={filters.channel}
                  onChange={(e) => setFilters({...filters, channel: e.target.value})}
                  className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
                >
                  {channels.map(channel => (
                    <option key={channel} value={channel}>{channel}</option>
                  ))}
                </select>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Publisher Search
                </label>
                <input
                  type="text"
                  placeholder="Search publishers or domains..."
                  value={filters.publisher}
                  onChange={(e) => setFilters({...filters, publisher: e.target.value})}
                  className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
                />
              </div>
            </div>
          </div>
        </div>

        {/* Results Table */}
        <div className="bg-white rounded-lg shadow overflow-hidden">
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Domain / Publisher
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    CPM
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    CTR
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Conversion Rate
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Score
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Status
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Channel
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {results.map((result) => (
                  <tr key={result.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div>
                        <div className="text-sm font-medium text-gray-900">
                          {result.domain}
                        </div>
                        <div className="text-sm text-gray-500">
                          {result.publisher}
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      ${result.cpm.toFixed(2)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {(result.ctr * 100).toFixed(2)}%
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {(result.conversion_rate * 100).toFixed(2)}%
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getScoreColor(result.score)}`}>
                        {result.score}/100
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getStatusColor(result.status)}`}>
                        {result.status}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {result.channel}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          
          {results.length === 0 && (
            <div className="text-center py-12">
              <div className="text-gray-400 mb-4">
                <svg className="w-16 h-16 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
              </div>
              <h3 className="text-lg font-medium text-gray-900 mb-2">No results found</h3>
              <p className="text-gray-600 mb-4">Try adjusting your filters to see more results.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
} 