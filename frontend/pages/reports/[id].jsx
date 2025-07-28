import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/router';
import { useAuth } from '../../context/AuthContext';
import axios from 'axios';
import ScoreCard from '../../components/ReportViewer/ScoreCard';
import ChartView from '../../components/ReportViewer/ChartView';
import HistoryTable from '../../components/ReportViewer/HistoryTable';
import ExportButton from '../../components/ReportViewer/ExportButton';
import LoadingSpinner from '../../components/Shared/LoadingSpinner';

export default function ReportDetail() {
  const router = useRouter();
  const { id } = router.query;
  const { user } = useAuth();
  
  const [report, setReport] = useState(null);
  const [reportData, setReportData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [activeTab, setActiveTab] = useState('overview');
  const [realTimeData, setRealTimeData] = useState(null);

  useEffect(() => {
    if (id) {
      fetchReport();
      fetchReportData();
    }
  }, [id]);

  useEffect(() => {
    if (report && report.status === 'completed') {
      // Set up real-time updates for completed reports
      const interval = setInterval(() => {
        fetchRealTimeData();
      }, 30000); // Update every 30 seconds

      return () => clearInterval(interval);
    }
  }, [report]);

  const fetchReport = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`/api/reports/${id}`);
      setReport(response.data);
    } catch (err) {
      setError('Failed to fetch report');
      console.error('Error fetching report:', err);
    } finally {
      setLoading(false);
    }
  };

  const fetchReportData = async () => {
    try {
      const response = await axios.get(`/api/reports/${id}/data`);
      setReportData(response.data);
    } catch (err) {
      console.error('Error fetching report data:', err);
    }
  };

  const fetchRealTimeData = async () => {
    try {
      const response = await axios.get(`/api/reports/${id}/realtime`);
      setRealTimeData(response.data);
    } catch (err) {
      console.error('Error fetching real-time data:', err);
    }
  };

  const getScoreBreakdown = () => {
    if (!reportData) return [];
    
    return [
      { category: 'CTR Performance', score: reportData.ctr_score || 85 },
      { category: 'CPM Efficiency', score: reportData.cpm_score || 78 },
      { category: 'Conversion Rate', score: reportData.conversion_score || 92 },
      { category: 'ROAS Optimization', score: reportData.roas_score || 88 },
      { category: 'Audience Quality', score: reportData.audience_score || 82 }
    ];
  };

  const getPerformanceData = () => {
    if (!reportData) return [];
    
    return [
      { name: 'CTR', value: reportData.ctr || 2.5, target: 3.0 },
      { name: 'CPM', value: reportData.cpm || 15.2, target: 12.0 },
      { name: 'CPC', value: reportData.cpc || 0.85, target: 0.75 },
      { name: 'Conversion Rate', value: reportData.conversion_rate || 1.2, target: 1.5 },
      { name: 'ROAS', value: reportData.roas || 3.8, target: 4.0 }
    ];
  };

  const getTrendData = () => {
    // Mock trend data - in real implementation, this would come from the backend
    return [
      { date: '2024-01-01', score: 75, impressions: 10000, clicks: 250, conversions: 12 },
      { date: '2024-01-02', score: 78, impressions: 12000, clicks: 300, conversions: 15 },
      { date: '2024-01-03', score: 82, impressions: 11000, clicks: 280, conversions: 14 },
      { date: '2024-01-04', score: 85, impressions: 13000, clicks: 350, conversions: 18 },
      { date: '2024-01-05', score: 87, impressions: 14000, clicks: 380, conversions: 20 },
      { date: '2024-01-06', score: 89, impressions: 15000, clicks: 420, conversions: 22 },
      { date: '2024-01-07', score: 92, impressions: 16000, clicks: 450, conversions: 25 }
    ];
  };

  const getInsightsData = () => {
    if (!reportData) return [];
    
    return [
      { name: 'High Performing', value: reportData.high_performing || 35 },
      { name: 'Medium Performing', value: reportData.medium_performing || 45 },
      { name: 'Low Performing', value: reportData.low_performing || 20 }
    ];
  };

  const tableColumns = [
    { key: 'date', label: 'Date', type: 'date', sortable: true },
    { key: 'score', label: 'Score', type: 'score', sortable: true },
    { key: 'impressions', label: 'Impressions', type: 'number', sortable: true },
    { key: 'clicks', label: 'Clicks', type: 'number', sortable: true },
    { key: 'conversions', label: 'Conversions', type: 'number', sortable: true },
    { key: 'ctr', label: 'CTR (%)', sortable: true },
    { key: 'cpm', label: 'CPM ($)', sortable: true },
    { key: 'roas', label: 'ROAS', sortable: true }
  ];

  const getMockHistoryData = () => {
    return getTrendData().map((item, index) => ({
      id: index,
      date: item.date,
      score: item.score,
      impressions: item.impressions,
      clicks: item.clicks,
      conversions: item.conversions,
      ctr: ((item.clicks / item.impressions) * 100).toFixed(2),
      cpm: (Math.random() * 20 + 10).toFixed(2),
      roas: (Math.random() * 5 + 2).toFixed(2)
    }));
  };

  if (!user) {
    return <div className="p-8">Please log in to view this report.</div>;
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <LoadingSpinner />
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="text-red-600 text-xl mb-4">{error}</div>
          <button
            onClick={() => router.back()}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
          >
            Go Back
          </button>
        </div>
      </div>
    );
  }

  if (!report) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="text-gray-600 text-xl mb-4">Report not found</div>
          <button
            onClick={() => router.back()}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
          >
            Go Back
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center">
              <button
                onClick={() => router.back()}
                className="mr-4 p-2 text-gray-400 hover:text-gray-600"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                </svg>
              </button>
              <h1 className="text-xl font-semibold text-gray-900">Report Details</h1>
            </div>
            <ExportButton
              data={getMockHistoryData()}
              reportId={id}
              reportTitle={report.filename}
              onExportStart={(type) => console.log(`Starting ${type} export`)}
              onExportComplete={(type) => console.log(`${type} export completed`)}
              onExportError={(error, type) => console.error(`${type} export failed:`, error)}
            />
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Report Info */}
        <div className="bg-white rounded-lg shadow-sm border p-6 mb-6">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-2xl font-bold text-gray-900">{report.filename}</h2>
              <p className="text-gray-600 mt-1">
                Generated on {new Date(report.created_at).toLocaleDateString()}
              </p>
              <div className="flex items-center mt-2 space-x-4 text-sm text-gray-500">
                <span>Status: {report.status}</span>
                {report.file_size && <span>Size: {report.file_size} bytes</span>}
              </div>
            </div>
            {realTimeData && (
              <div className="text-right">
                <div className="text-sm text-gray-500">Last Updated</div>
                <div className="text-sm font-medium text-gray-900">
                  {new Date(realTimeData.timestamp).toLocaleTimeString()}
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Tabs */}
        <div className="bg-white rounded-lg shadow-sm border">
          <div className="border-b border-gray-200">
            <nav className="-mb-px flex space-x-8 px-6">
              {[
                { id: 'overview', label: 'Overview' },
                { id: 'charts', label: 'Charts & Analytics' },
                { id: 'history', label: 'Performance History' },
                { id: 'insights', label: 'AI Insights' }
              ].map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`py-4 px-1 border-b-2 font-medium text-sm ${
                    activeTab === tab.id
                      ? 'border-blue-500 text-blue-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }`}
                >
                  {tab.label}
                </button>
              ))}
            </nav>
          </div>

          <div className="p-6">
            {activeTab === 'overview' && (
              <div className="space-y-6">
                {/* Score Cards */}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                  <ScoreCard
                    score={reportData?.overall_score || 87}
                    title="Overall Score"
                    description="Campaign performance score"
                    trend={5}
                    breakdown={getScoreBreakdown()}
                    size="medium"
                  />
                  <ScoreCard
                    score={reportData?.ctr_score || 92}
                    title="CTR Score"
                    description="Click-through rate performance"
                    trend={8}
                    size="medium"
                  />
                  <ScoreCard
                    score={reportData?.cpm_score || 78}
                    title="CPM Score"
                    description="Cost per thousand impressions"
                    trend={-2}
                    size="medium"
                  />
                  <ScoreCard
                    score={reportData?.roas_score || 85}
                    title="ROAS Score"
                    description="Return on ad spend"
                    trend={12}
                    size="medium"
                  />
                </div>

                {/* Performance Metrics */}
                <ChartView
                  data={getPerformanceData()}
                  type="bar"
                  title="Performance vs Targets"
                  xAxisKey="name"
                  yAxisKey="value"
                  height={300}
                />
              </div>
            )}

            {activeTab === 'charts' && (
              <div className="space-y-6">
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                  <ChartView
                    data={getTrendData()}
                    type="line"
                    title="Score Trend Over Time"
                    xAxisKey="date"
                    yAxisKey="score"
                    height={300}
                  />
                  <ChartView
                    data={getTrendData()}
                    type="area"
                    title="Impressions & Clicks"
                    xAxisKey="date"
                    multipleSeries={true}
                    seriesKeys={['impressions', 'clicks']}
                    height={300}
                  />
                </div>
                <ChartView
                  data={getPerformanceData()}
                  type="radar"
                  title="Performance Radar Chart"
                  xAxisKey="name"
                  yAxisKey="value"
                  height={400}
                />
              </div>
            )}

            {activeTab === 'history' && (
              <HistoryTable
                data={getMockHistoryData()}
                columns={tableColumns}
                pageSize={10}
                sortable={true}
                filterable={true}
                onRowClick={(row) => console.log('Row clicked:', row)}
              />
            )}

            {activeTab === 'insights' && (
              <div className="space-y-6">
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                  <ChartView
                    data={getInsightsData()}
                    type="pie"
                    title="Performance Distribution"
                    yAxisKey="value"
                    height={300}
                  />
                  <div className="bg-gray-50 rounded-lg p-6">
                    <h3 className="text-lg font-semibold text-gray-900 mb-4">AI Insights</h3>
                    <div className="space-y-4">
                      <div className="bg-white p-4 rounded-lg border">
                        <h4 className="font-medium text-gray-900 mb-2">Performance Analysis</h4>
                        <p className="text-sm text-gray-600">
                          Your campaign shows strong CTR performance but has room for improvement in CPM efficiency. 
                          Consider optimizing your targeting to reduce costs while maintaining quality.
                        </p>
                      </div>
                      <div className="bg-white p-4 rounded-lg border">
                        <h4 className="font-medium text-gray-900 mb-2">Recommendations</h4>
                        <ul className="text-sm text-gray-600 space-y-1">
                          <li>• Optimize bid strategies for better CPM control</li>
                          <li>• Test new audience segments to improve conversion rates</li>
                          <li>• Consider creative refresh to boost engagement</li>
                        </ul>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
} 