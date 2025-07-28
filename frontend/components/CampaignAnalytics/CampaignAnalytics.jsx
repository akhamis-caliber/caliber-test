import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card.jsx';
import { Badge } from '../ui/badge.jsx';
import { Button } from '../ui/button.jsx';
import { 
  ChartBarIcon, 
  TrendingUpIcon, 
  TrendingDownIcon,
  DocumentTextIcon,
  ClockIcon,
  UserIcon,
  ArrowUpIcon,
  ArrowDownIcon
} from '@heroicons/react/24/outline';

export default function CampaignAnalytics({ campaignId }) {
  const [analytics, setAnalytics] = useState(null);
  const [performance, setPerformance] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    if (campaignId) {
      fetchAnalytics();
    }
  }, [campaignId]);

  const fetchAnalytics = async () => {
    try {
      setLoading(true);
      setError('');
      
      // Fetch both analytics and performance data
      const [analyticsResponse, performanceResponse] = await Promise.all([
        fetch(`/api/campaigns/${campaignId}/scoring-analytics`),
        fetch(`/api/campaigns/${campaignId}/scoring-performance`)
      ]);
      
      if (analyticsResponse.ok) {
        const analyticsData = await analyticsResponse.json();
        setAnalytics(analyticsData);
      }
      
      if (performanceResponse.ok) {
        const performanceData = await performanceResponse.json();
        setPerformance(performanceData);
      }
    } catch (err) {
      console.error('Failed to fetch analytics:', err);
      setError('Failed to load analytics data');
    } finally {
      setLoading(false);
    }
  };

  const getMetricColor = (value, threshold = 70) => {
    if (value >= threshold) return 'text-green-600';
    if (value >= threshold * 0.8) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getTrendIcon = (current, previous) => {
    if (!previous || previous === 0) return null;
    const change = ((current - previous) / previous) * 100;
    if (change > 5) return <TrendingUpIcon className="h-4 w-4 text-green-600" />;
    if (change < -5) return <TrendingDownIcon className="h-4 w-4 text-red-600" />;
    return null;
  };

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="animate-pulse">
          <div className="h-32 bg-gray-200 rounded-lg mb-4"></div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="h-24 bg-gray-200 rounded"></div>
            <div className="h-24 bg-gray-200 rounded"></div>
            <div className="h-24 bg-gray-200 rounded"></div>
          </div>
        </div>
      </div>
    );
  }

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
            <h3 className="text-lg font-medium text-gray-900 mb-2">Error Loading Analytics</h3>
            <p className="text-gray-600 mb-4">{error}</p>
            <Button onClick={fetchAnalytics}>
              Try Again
            </Button>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      {/* Overview Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Reports</CardTitle>
            <DocumentTextIcon className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {analytics?.total_reports || 0}
            </div>
            <p className="text-xs text-muted-foreground">
              Processed reports
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Metrics</CardTitle>
            <ChartBarIcon className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {analytics?.total_metrics || 0}
            </div>
            <p className="text-xs text-muted-foreground">
              Scoring metrics
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Success Rate</CardTitle>
            <TrendingUpIcon className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {performance?.job_performance?.success_rate?.toFixed(1) || 0}%
            </div>
            <p className="text-xs text-muted-foreground">
              Processing success
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Avg Processing Time</CardTitle>
            <ClockIcon className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {performance?.processing_performance?.average_processing_time?.toFixed(1) || 0}s
            </div>
            <p className="text-xs text-muted-foreground">
              Per report
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Detailed Analytics */}
      {analytics?.analytics && Object.keys(analytics.analytics).length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Metric Performance</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {Object.entries(analytics.analytics).map(([metricName, data]) => (
                <div key={metricName} className="border rounded-lg p-4">
                  <div className="flex items-center justify-between mb-3">
                    <h4 className="font-medium text-gray-900">{metricName}</h4>
                    <Badge variant="outline">
                      {data.total_reports} reports
                    </Badge>
                  </div>
                  
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                    <div>
                      <span className="text-gray-500">Average Score:</span>
                      <span className={`ml-1 font-medium ${getMetricColor(data.average_score)}`}>
                        {data.average_score.toFixed(1)}
                      </span>
                    </div>
                    <div>
                      <span className="text-gray-500">Min Score:</span>
                      <span className="ml-1 font-medium">{data.min_score.toFixed(1)}</span>
                    </div>
                    <div>
                      <span className="text-gray-500">Max Score:</span>
                      <span className="ml-1 font-medium">{data.max_score.toFixed(1)}</span>
                    </div>
                    <div>
                      <span className="text-gray-500">Avg Weight:</span>
                      <span className="ml-1 font-medium">{(data.average_weight * 100).toFixed(1)}%</span>
                    </div>
                  </div>
                  
                  {/* Score Distribution */}
                  <div className="mt-3">
                    <h5 className="text-sm font-medium text-gray-700 mb-2">Score Distribution</h5>
                    <div className="grid grid-cols-4 gap-2 text-xs">
                      <div className="text-center">
                        <div className="text-green-600 font-medium">{data.score_distribution.excellent}</div>
                        <div className="text-gray-500">Excellent</div>
                      </div>
                      <div className="text-center">
                        <div className="text-blue-600 font-medium">{data.score_distribution.good}</div>
                        <div className="text-gray-500">Good</div>
                      </div>
                      <div className="text-center">
                        <div className="text-yellow-600 font-medium">{data.score_distribution.average}</div>
                        <div className="text-gray-500">Average</div>
                      </div>
                      <div className="text-center">
                        <div className="text-red-600 font-medium">{data.score_distribution.poor}</div>
                        <div className="text-gray-500">Poor</div>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Performance History */}
      {performance?.recent_history && performance.recent_history.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Recent Scoring History</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {performance.recent_history.slice(0, 5).map((item, index) => (
                <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <div className="flex items-center space-x-3">
                    <div className="p-2 bg-indigo-100 rounded-lg">
                      <DocumentTextIcon className="h-4 w-4 text-indigo-600" />
                    </div>
                    <div>
                      <p className="text-sm font-medium text-gray-900">
                        Report #{item.report_id}
                      </p>
                      <p className="text-xs text-gray-500">
                        Version {item.version} • {new Date(item.created_at).toLocaleDateString()}
                      </p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="text-sm font-medium text-gray-900">
                      {item.results_summary?.total_score?.toFixed(1) || 'N/A'}
                    </p>
                    <p className="text-xs text-gray-500">Total Score</p>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Job Performance */}
      {performance?.job_performance && (
        <Card>
          <CardHeader>
            <CardTitle>Processing Performance</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="text-center">
                <div className="text-2xl font-bold text-blue-600">
                  {performance.job_performance.completed_jobs}
                </div>
                <p className="text-sm text-gray-600">Completed</p>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-red-600">
                  {performance.job_performance.failed_jobs}
                </div>
                <p className="text-sm text-gray-600">Failed</p>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-green-600">
                  {performance.job_performance.success_rate.toFixed(1)}%
                </div>
                <p className="text-sm text-gray-600">Success Rate</p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
} 