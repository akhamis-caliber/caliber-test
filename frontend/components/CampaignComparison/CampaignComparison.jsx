import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card.jsx';
import { Badge } from '../ui/badge.jsx';
import { Button } from '../ui/button.jsx';
import { Select } from '../ui/select.jsx';
import { 
  ChartBarIcon, 
  DocumentTextIcon,
  ClockIcon,
  TrendingUpIcon,
  TrendingDownIcon,
  ArrowRightIcon
} from '@heroicons/react/24/outline';
import { campaignAPI } from '../../services/api';

export default function CampaignComparison() {
  const [campaigns, setCampaigns] = useState([]);
  const [selectedCampaigns, setSelectedCampaigns] = useState([]);
  const [campaignData, setCampaignData] = useState({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    fetchCampaigns();
  }, []);

  useEffect(() => {
    if (selectedCampaigns.length > 0) {
      fetchCampaignData();
    }
  }, [selectedCampaigns]);

  const fetchCampaigns = async () => {
    try {
      const response = await campaignAPI.getCampaigns();
      setCampaigns(response.data || []);
    } catch (err) {
      console.error('Failed to fetch campaigns:', err);
      setError('Failed to load campaigns');
    }
  };

  const fetchCampaignData = async () => {
    try {
      setLoading(true);
      setError('');
      
      const dataPromises = selectedCampaigns.map(async (campaignId) => {
        const [campaignResponse, statsResponse] = await Promise.all([
          campaignAPI.getCampaign(campaignId),
          campaignAPI.getCampaignStats(campaignId)
        ]);
        
        return {
          id: campaignId,
          campaign: campaignResponse.data,
          stats: statsResponse.data
        };
      });
      
      const results = await Promise.all(dataPromises);
      const dataMap = {};
      results.forEach(result => {
        dataMap[result.id] = result;
      });
      
      setCampaignData(dataMap);
    } catch (err) {
      console.error('Failed to fetch campaign data:', err);
      setError('Failed to load campaign comparison data');
    } finally {
      setLoading(false);
    }
  };

  const handleCampaignSelect = (campaignId) => {
    if (selectedCampaigns.includes(campaignId)) {
      setSelectedCampaigns(prev => prev.filter(id => id !== campaignId));
    } else if (selectedCampaigns.length < 3) {
      setSelectedCampaigns(prev => [...prev, campaignId]);
    }
  };

  const getStatusColor = (status) => {
    switch (status?.toLowerCase()) {
      case 'active': return 'bg-green-100 text-green-800';
      case 'draft': return 'bg-gray-100 text-gray-800';
      case 'paused': return 'bg-yellow-100 text-yellow-800';
      case 'completed': return 'bg-blue-100 text-blue-800';
      case 'archived': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getScoreColor = (score) => {
    if (!score) return 'text-gray-500';
    if (score >= 90) return 'text-green-600';
    if (score >= 80) return 'text-blue-600';
    if (score >= 70) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getComparisonMetric = (metric, campaigns) => {
    const values = campaigns.map(c => c[metric]).filter(v => v !== null && v !== undefined);
    if (values.length === 0) return { best: null, worst: null, average: null };
    
    const best = Math.max(...values);
    const worst = Math.min(...values);
    const average = values.reduce((a, b) => a + b, 0) / values.length;
    
    return { best, worst, average };
  };

  if (error) {
    return (
      <Card>
        <CardContent className="pt-6">
          <div className="text-center py-8">
            <div className="text-red-600 mb-4">
              <svg className="w-16 h-16 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
              </svg>
            </div>
            <h3 className="text-lg font-medium text-gray-900 mb-2">Error Loading Comparison</h3>
            <p className="text-gray-600 mb-4">{error}</p>
            <Button onClick={fetchCampaigns}>
              Try Again
            </Button>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      {/* Campaign Selection */}
      <Card>
        <CardHeader>
          <CardTitle>Select Campaigns to Compare</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <p className="text-sm text-gray-600">
              Select up to 3 campaigns to compare their performance metrics side by side.
            </p>
            
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {campaigns.map((campaign) => (
                <div
                  key={campaign.id}
                  className={`p-4 border rounded-lg cursor-pointer transition-colors ${
                    selectedCampaigns.includes(campaign.id)
                      ? 'border-indigo-500 bg-indigo-50'
                      : 'border-gray-200 hover:border-gray-300'
                  }`}
                  onClick={() => handleCampaignSelect(campaign.id)}
                >
                  <div className="flex items-center justify-between mb-2">
                    <h4 className="font-medium text-gray-900">{campaign.name}</h4>
                    <input
                      type="checkbox"
                      checked={selectedCampaigns.includes(campaign.id)}
                      onChange={() => {}}
                      className="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded"
                    />
                  </div>
                  <p className="text-sm text-gray-600 mb-2">
                    {campaign.description?.substring(0, 100) || 'No description'}
                  </p>
                  <div className="flex items-center justify-between">
                    <Badge className={getStatusColor(campaign.status)}>
                      {campaign.status}
                    </Badge>
                    <span className="text-sm text-gray-500">
                      {campaign.total_submissions || 0} submissions
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Comparison Results */}
      {selectedCampaigns.length > 0 && (
        <div className="space-y-6">
          {loading ? (
            <Card>
              <CardContent className="pt-6">
                <div className="animate-pulse">
                  <div className="h-32 bg-gray-200 rounded-lg mb-4"></div>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div className="h-24 bg-gray-200 rounded"></div>
                    <div className="h-24 bg-gray-200 rounded"></div>
                    <div className="h-24 bg-gray-200 rounded"></div>
                  </div>
                </div>
              </CardContent>
            </Card>
          ) : (
            <>
              {/* Overview Comparison */}
              <Card>
                <CardHeader>
                  <CardTitle>Overview Comparison</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="overflow-x-auto">
                    <table className="min-w-full divide-y divide-gray-200">
                      <thead className="bg-gray-50">
                        <tr>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Metric
                          </th>
                          {selectedCampaigns.map(campaignId => (
                            <th key={campaignId} className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                              {campaignData[campaignId]?.campaign?.name || 'Campaign'}
                            </th>
                          ))}
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Best
                          </th>
                        </tr>
                      </thead>
                      <tbody className="bg-white divide-y divide-gray-200">
                        <tr>
                          <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                            Status
                          </td>
                          {selectedCampaigns.map(campaignId => (
                            <td key={campaignId} className="px-6 py-4 whitespace-nowrap">
                              <Badge className={getStatusColor(campaignData[campaignId]?.campaign?.status)}>
                                {campaignData[campaignId]?.campaign?.status}
                              </Badge>
                            </td>
                          ))}
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                            -
                          </td>
                        </tr>
                        <tr>
                          <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                            Total Submissions
                          </td>
                          {selectedCampaigns.map(campaignId => (
                            <td key={campaignId} className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                              {campaignData[campaignId]?.campaign?.total_submissions || 0}
                            </td>
                          ))}
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                            {(() => {
                              const values = selectedCampaigns.map(id => campaignData[id]?.campaign?.total_submissions || 0);
                              return Math.max(...values);
                            })()}
                          </td>
                        </tr>
                        <tr>
                          <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                            Average Score
                          </td>
                          {selectedCampaigns.map(campaignId => (
                            <td key={campaignId} className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                              <span className={getScoreColor(campaignData[campaignId]?.campaign?.average_score)}>
                                {campaignData[campaignId]?.campaign?.average_score?.toFixed(1) || 'N/A'}
                              </span>
                            </td>
                          ))}
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                            {(() => {
                              const values = selectedCampaigns
                                .map(id => campaignData[id]?.campaign?.average_score)
                                .filter(v => v !== null && v !== undefined);
                              return values.length > 0 ? Math.max(...values).toFixed(1) : 'N/A';
                            })()}
                          </td>
                        </tr>
                        <tr>
                          <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                            Created Date
                          </td>
                          {selectedCampaigns.map(campaignId => (
                            <td key={campaignId} className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                              {campaignData[campaignId]?.campaign?.created_at 
                                ? new Date(campaignData[campaignId].campaign.created_at).toLocaleDateString()
                                : 'N/A'
                              }
                            </td>
                          ))}
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                            -
                          </td>
                        </tr>
                      </tbody>
                    </table>
                  </div>
                </CardContent>
              </Card>

              {/* Performance Metrics */}
              <Card>
                <CardHeader>
                  <CardTitle>Performance Metrics</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    {selectedCampaigns.map(campaignId => {
                      const data = campaignData[campaignId];
                      if (!data) return null;
                      
                      return (
                        <div key={campaignId} className="space-y-4">
                          <h4 className="font-medium text-gray-900">{data.campaign.name}</h4>
                          
                          <div className="space-y-3">
                            <div className="flex justify-between">
                              <span className="text-sm text-gray-600">Total Reports:</span>
                              <span className="text-sm font-medium">{data.stats?.total_reports || 0}</span>
                            </div>
                            <div className="flex justify-between">
                              <span className="text-sm text-gray-600">Completed:</span>
                              <span className="text-sm font-medium">{data.stats?.completed_reports || 0}</span>
                            </div>
                            <div className="flex justify-between">
                              <span className="text-sm text-gray-600">Pending:</span>
                              <span className="text-sm font-medium">{data.stats?.pending_reports || 0}</span>
                            </div>
                            <div className="flex justify-between">
                              <span className="text-sm text-gray-600">Avg Score:</span>
                              <span className={`text-sm font-medium ${getScoreColor(data.stats?.average_score)}`}>
                                {data.stats?.average_score?.toFixed(1) || 'N/A'}
                              </span>
                            </div>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </CardContent>
              </Card>

              {/* Detailed Comparison */}
              <Card>
                <CardHeader>
                  <CardTitle>Detailed Comparison</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    {selectedCampaigns.map(campaignId => {
                      const data = campaignData[campaignId];
                      if (!data) return null;
                      
                      return (
                        <div key={campaignId} className="border rounded-lg p-4">
                          <h4 className="font-medium text-gray-900 mb-3">{data.campaign.name}</h4>
                          
                          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                            <div>
                              <span className="text-gray-500">Template:</span>
                              <span className="ml-1 font-medium">{data.campaign.template_type}</span>
                            </div>
                            <div>
                              <span className="text-gray-500">Max Score:</span>
                              <span className="ml-1 font-medium">{data.campaign.max_score}/100</span>
                            </div>
                            {data.campaign.target_score && (
                              <div>
                                <span className="text-gray-500">Target:</span>
                                <span className="ml-1 font-medium">{data.campaign.target_score}/100</span>
                              </div>
                            )}
                            <div>
                              <span className="text-gray-500">Min Score:</span>
                              <span className="ml-1 font-medium">{data.campaign.min_score}/100</span>
                            </div>
                          </div>
                          
                          {data.campaign.scoring_criteria && (
                            <div className="mt-3">
                              <h5 className="text-sm font-medium text-gray-700 mb-2">Scoring Criteria</h5>
                              <div className="space-y-1">
                                {data.campaign.scoring_criteria.map((criteria, index) => (
                                  <div key={index} className="flex justify-between text-xs">
                                    <span>{criteria.criterion_name}</span>
                                    <span>{(criteria.weight * 100).toFixed(0)}%</span>
                                  </div>
                                ))}
                              </div>
                            </div>
                          )}
                        </div>
                      );
                    })}
                  </div>
                </CardContent>
              </Card>
            </>
          )}
        </div>
      )}

      {selectedCampaigns.length === 0 && (
        <Card>
          <CardContent className="pt-6">
            <div className="text-center py-8">
              <div className="text-gray-400 mb-4">
                <ChartBarIcon className="w-16 h-16 mx-auto" />
              </div>
              <h3 className="text-lg font-medium text-gray-900 mb-2">No Campaigns Selected</h3>
              <p className="text-gray-600">
                Select campaigns from the list above to start comparing their performance.
              </p>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
} 