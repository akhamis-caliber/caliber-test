import React, { useState, useEffect } from 'react';
import { scoringAPI } from '../../services/api';
import { toast } from 'react-toastify';

const ScoringDashboard = ({ campaignId }) => {
  const [loading, setLoading] = useState(false);
  const [scoringJobs, setScoringJobs] = useState([]);
  const [analytics, setAnalytics] = useState(null);
  const [performance, setPerformance] = useState(null);
  const [activeTab, setActiveTab] = useState('jobs');

  useEffect(() => {
    if (campaignId) {
      loadScoringData();
    }
  }, [campaignId]);

  const loadScoringData = async () => {
    setLoading(true);
    try {
      const [jobsRes, analyticsRes, performanceRes] = await Promise.all([
        scoringAPI.getScoringJobs({ campaign_id: campaignId }),
        scoringAPI.getCampaignScoringAnalytics(campaignId),
        scoringAPI.getCampaignScoringPerformance(campaignId)
      ]);

      setScoringJobs(jobsRes.data.jobs || []);
      setAnalytics(analyticsRes.data);
      setPerformance(performanceRes.data);
    } catch (error) {
      console.error('Error loading scoring data:', error);
      toast.error('Failed to load scoring data');
    } finally {
      setLoading(false);
    }
  };

  const handleScoreAllReports = async () => {
    try {
      setLoading(true);
      await scoringAPI.scoreAllCampaignReports(campaignId);
      toast.success('Scoring job started for all reports');
      loadScoringData(); // Refresh data
    } catch (error) {
      console.error('Error scoring reports:', error);
      toast.error('Failed to start scoring job');
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'completed': return 'text-green-600';
      case 'processing': return 'text-blue-600';
      case 'failed': return 'text-red-600';
      case 'queued': return 'text-yellow-600';
      default: return 'text-gray-600';
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'completed': return '✅';
      case 'processing': return '⏳';
      case 'failed': return '❌';
      case 'queued': return '⏰';
      default: return '❓';
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-bold text-gray-800">Scoring Dashboard</h2>
        <button
          onClick={handleScoreAllReports}
          disabled={loading}
          className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg disabled:opacity-50"
        >
          {loading ? 'Processing...' : 'Score All Reports'}
        </button>
      </div>

      {/* Tab Navigation */}
      <div className="border-b border-gray-200 mb-6">
        <nav className="-mb-px flex space-x-8">
          {[
            { id: 'jobs', label: 'Scoring Jobs', count: scoringJobs.length },
            { id: 'analytics', label: 'Analytics', count: analytics?.total_metrics || 0 },
            { id: 'performance', label: 'Performance', count: performance?.job_performance?.total_jobs || 0 }
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === tab.id
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              {tab.label}
              <span className="ml-2 bg-gray-100 text-gray-900 py-0.5 px-2.5 rounded-full text-xs">
                {tab.count}
              </span>
            </button>
          ))}
        </nav>
      </div>

      {/* Tab Content */}
      <div className="min-h-96">
        {activeTab === 'jobs' && (
          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-gray-800">Recent Scoring Jobs</h3>
            {scoringJobs.length === 0 ? (
              <p className="text-gray-500 text-center py-8">No scoring jobs found</p>
            ) : (
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Job ID
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Report
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Status
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Progress
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Created
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {scoringJobs.map((job) => (
                      <tr key={job.id} className="hover:bg-gray-50">
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                          #{job.id}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          Report #{job.report_id}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor(job.status)}`}>
                            {getStatusIcon(job.status)} {job.status}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="w-full bg-gray-200 rounded-full h-2">
                            <div
                              className="bg-blue-600 h-2 rounded-full"
                              style={{ width: `${job.progress}%` }}
                            ></div>
                          </div>
                          <span className="text-xs text-gray-500">{job.progress}%</span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {new Date(job.created_at).toLocaleDateString()}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}

        {activeTab === 'analytics' && analytics && (
          <div className="space-y-6">
            <h3 className="text-lg font-semibold text-gray-800">Scoring Analytics</h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
              <div className="bg-blue-50 p-4 rounded-lg">
                <h4 className="text-sm font-medium text-blue-800">Total Reports</h4>
                <p className="text-2xl font-bold text-blue-900">{analytics.total_reports}</p>
              </div>
              <div className="bg-green-50 p-4 rounded-lg">
                <h4 className="text-sm font-medium text-green-800">Total Metrics</h4>
                <p className="text-2xl font-bold text-green-900">{analytics.total_metrics}</p>
              </div>
              <div className="bg-purple-50 p-4 rounded-lg">
                <h4 className="text-sm font-medium text-purple-800">Average Score</h4>
                <p className="text-2xl font-bold text-purple-900">
                  {Object.values(analytics.analytics).length > 0
                    ? (Object.values(analytics.analytics).reduce((sum, metric) => sum + metric.average_score, 0) / Object.values(analytics.analytics).length).toFixed(1)
                    : '0.0'}
                </p>
              </div>
            </div>

            <div className="space-y-4">
              <h4 className="text-md font-semibold text-gray-800">Metric Performance</h4>
              {Object.entries(analytics.analytics).map(([metricName, data]) => (
                <div key={metricName} className="border border-gray-200 rounded-lg p-4">
                  <div className="flex justify-between items-center mb-2">
                    <h5 className="font-medium text-gray-800">{metricName}</h5>
                    <span className="text-sm text-gray-500">{data.total_reports} reports</span>
                  </div>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                    <div>
                      <span className="text-gray-500">Avg Score:</span>
                      <span className="ml-1 font-medium">{data.average_score.toFixed(1)}</span>
                    </div>
                    <div>
                      <span className="text-gray-500">Range:</span>
                      <span className="ml-1 font-medium">{data.min_score.toFixed(1)} - {data.max_score.toFixed(1)}</span>
                    </div>
                    <div>
                      <span className="text-gray-500">Avg Weight:</span>
                      <span className="ml-1 font-medium">{data.average_weight.toFixed(2)}</span>
                    </div>
                    <div>
                      <span className="text-gray-500">Distribution:</span>
                      <div className="flex space-x-1 mt-1">
                        <span className="text-xs bg-green-100 text-green-800 px-1 rounded">
                          {data.score_distribution.excellent}
                        </span>
                        <span className="text-xs bg-blue-100 text-blue-800 px-1 rounded">
                          {data.score_distribution.good}
                        </span>
                        <span className="text-xs bg-yellow-100 text-yellow-800 px-1 rounded">
                          {data.score_distribution.average}
                        </span>
                        <span className="text-xs bg-red-100 text-red-800 px-1 rounded">
                          {data.score_distribution.poor}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {activeTab === 'performance' && performance && (
          <div className="space-y-6">
            <h3 className="text-lg font-semibold text-gray-800">Performance Metrics</h3>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="bg-white border border-gray-200 rounded-lg p-6">
                <h4 className="text-lg font-medium text-gray-800 mb-4">Job Performance</h4>
                <div className="space-y-3">
                  <div className="flex justify-between">
                    <span className="text-gray-600">Total Jobs:</span>
                    <span className="font-medium">{performance.job_performance.total_jobs}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Completed:</span>
                    <span className="font-medium text-green-600">{performance.job_performance.completed_jobs}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Failed:</span>
                    <span className="font-medium text-red-600">{performance.job_performance.failed_jobs}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Success Rate:</span>
                    <span className="font-medium">{performance.job_performance.success_rate.toFixed(1)}%</span>
                  </div>
                </div>
              </div>

              <div className="bg-white border border-gray-200 rounded-lg p-6">
                <h4 className="text-lg font-medium text-gray-800 mb-4">Processing Performance</h4>
                <div className="space-y-3">
                  <div className="flex justify-between">
                    <span className="text-gray-600">Avg Processing Time:</span>
                    <span className="font-medium">{performance.processing_performance.average_processing_time.toFixed(2)}s</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Total Scoring Runs:</span>
                    <span className="font-medium">{performance.processing_performance.total_scoring_runs}</span>
                  </div>
                </div>
              </div>
            </div>

            <div className="bg-white border border-gray-200 rounded-lg p-6">
              <h4 className="text-lg font-medium text-gray-800 mb-4">Recent History</h4>
              {performance.recent_history.length === 0 ? (
                <p className="text-gray-500 text-center py-4">No recent scoring history</p>
              ) : (
                <div className="space-y-3">
                  {performance.recent_history.map((entry) => (
                    <div key={entry.id} className="flex justify-between items-center py-2 border-b border-gray-100 last:border-b-0">
                      <div>
                        <span className="font-medium">Report #{entry.report_id}</span>
                        <span className="text-sm text-gray-500 ml-2">v{entry.version}</span>
                      </div>
                      <div className="text-right">
                        <div className="text-sm text-gray-600">
                          {new Date(entry.created_at).toLocaleDateString()}
                        </div>
                        {entry.results_summary && (
                          <div className="text-xs text-gray-500">
                            Avg: {entry.results_summary.average_score?.toFixed(1) || 'N/A'}
                          </div>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default ScoringDashboard; 