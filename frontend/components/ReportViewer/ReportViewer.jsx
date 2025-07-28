import React, { useState, useEffect } from 'react';
import axios from 'axios';
import ScoreCard from './ScoreCard';
import ChartView from './ChartView';
import HistoryTable from './HistoryTable';
import ExportButton from './ExportButton';

function ReportViewer({ campaignId, userId }) {
  const [reports, setReports] = useState([]);
  const [selectedReport, setSelectedReport] = useState(null);
  const [reportData, setReportData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [activeTab, setActiveTab] = useState('overview');

  useEffect(() => {
    fetchReports();
  }, [campaignId]);

  useEffect(() => {
    if (selectedReport) {
      fetchReportData(selectedReport.id);
    }
  }, [selectedReport]);

  const fetchReports = async () => {
    try {
      const response = await axios.get('/api/reports');
      setReports(response.data);
      setLoading(false);
    } catch (err) {
      setError('Failed to fetch reports');
      setLoading(false);
    }
  };

  const fetchReportData = async (reportId) => {
    try {
      setLoading(true);
      const response = await axios.get(`/api/reports/${reportId}/data`);
      setReportData(response.data);
    } catch (err) {
      setError('Failed to fetch report data');
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'queued': return 'text-yellow-600 bg-yellow-100';
      case 'processing': return 'text-blue-600 bg-blue-100';
      case 'completed': return 'text-green-600 bg-green-100';
      case 'failed': return 'text-red-600 bg-red-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  const formatFileSize = (bytes) => {
    if (!bytes) return 'Unknown';
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(1024));
    return Math.round(bytes / Math.pow(1024, i) * 100) / 100 + ' ' + sizes[i];
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString();
  };

  // Mock data for charts and scores
  const getMockChartData = () => {
    if (!reportData) return [];
    
    return [
      { name: 'CTR', value: reportData.ctr || 2.5 },
      { name: 'CPM', value: reportData.cpm || 15.2 },
      { name: 'CPC', value: reportData.cpc || 0.85 },
      { name: 'Conversion Rate', value: reportData.conversionRate || 1.2 },
      { name: 'ROAS', value: reportData.roas || 3.8 }
    ];
  };

  const getMockTrendData = () => {
    return [
      { date: '2024-01-01', score: 75, impressions: 10000, clicks: 250 },
      { date: '2024-01-02', score: 78, impressions: 12000, clicks: 300 },
      { date: '2024-01-03', score: 82, impressions: 11000, clicks: 280 },
      { date: '2024-01-04', score: 85, impressions: 13000, clicks: 350 },
      { date: '2024-01-05', score: 87, impressions: 14000, clicks: 380 },
      { date: '2024-01-06', score: 89, impressions: 15000, clicks: 420 },
      { date: '2024-01-07', score: 92, impressions: 16000, clicks: 450 }
    ];
  };

  const getMockHistoryData = () => {
    return reports.map(report => ({
      id: report.id,
      name: report.filename,
      date: report.created_at,
      score: Math.floor(Math.random() * 30) + 70, // Mock score between 70-100
      status: report.status,
      impressions: Math.floor(Math.random() * 50000) + 10000,
      clicks: Math.floor(Math.random() * 1000) + 100,
      ctr: (Math.random() * 5 + 1).toFixed(2),
      cpm: (Math.random() * 20 + 10).toFixed(2)
    }));
  };

  const tableColumns = [
    { key: 'name', label: 'Report Name', sortable: true },
    { key: 'date', label: 'Date', type: 'date', sortable: true },
    { key: 'score', label: 'Score', type: 'score', sortable: true },
    { key: 'status', label: 'Status', type: 'status', sortable: true },
    { key: 'impressions', label: 'Impressions', type: 'number', sortable: true },
    { key: 'clicks', label: 'Clicks', type: 'number', sortable: true },
    { key: 'ctr', label: 'CTR (%)', sortable: true },
    { key: 'cpm', label: 'CPM ($)', sortable: true }
  ];

  if (loading && !selectedReport) {
    return <div className="p-8">Loading reports...</div>;
  }

  if (error && !selectedReport) {
    return <div className="p-8 text-red-600">{error}</div>;
  }

  return (
    <div className="space-y-6">
      {/* Reports List */}
      <div className="bg-white rounded-lg shadow-sm border">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-xl font-semibold text-gray-900">Reports</h2>
        </div>
        <div className="p-6">
          {reports.length === 0 ? (
            <p className="text-gray-500">No reports found.</p>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {reports.map((report) => (
                <div
                  key={report.id}
                  className={`border rounded-lg p-4 cursor-pointer transition-colors ${
                    selectedReport?.id === report.id
                      ? 'border-blue-500 bg-blue-50'
                      : 'border-gray-200 hover:border-gray-300'
                  }`}
                  onClick={() => setSelectedReport(report)}
                >
                  <div className="flex justify-between items-start mb-3">
                    <h3 className="font-medium text-gray-900 truncate">{report.filename}</h3>
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(report.status)}`}>
                      {report.status}
                    </span>
                  </div>
                  <div className="space-y-1 text-sm text-gray-500">
                    <p>Uploaded: {formatDate(report.created_at)}</p>
                    {report.file_size && <p>Size: {formatFileSize(report.file_size)}</p>}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Selected Report Details */}
      {selectedReport && (
        <div className="space-y-6">
          {/* Report Header */}
          <div className="bg-white rounded-lg shadow-sm border p-6">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h1 className="text-2xl font-bold text-gray-900">{selectedReport.filename}</h1>
                <p className="text-gray-600 mt-1">
                  Generated on {formatDate(selectedReport.created_at)}
                </p>
              </div>
              <ExportButton
                data={getMockHistoryData()}
                reportId={selectedReport.id}
                reportTitle={selectedReport.filename}
                onExportStart={(type) => console.log(`Starting ${type} export`)}
                onExportComplete={(type) => console.log(`${type} export completed`)}
                onExportError={(error, type) => console.error(`${type} export failed:`, error)}
              />
            </div>
          </div>

          {/* Tabs */}
          <div className="bg-white rounded-lg shadow-sm border">
            <div className="border-b border-gray-200">
              <nav className="-mb-px flex space-x-8 px-6">
                {[
                  { id: 'overview', label: 'Overview' },
                  { id: 'charts', label: 'Charts' },
                  { id: 'history', label: 'History' },
                  { id: 'details', label: 'Details' }
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
                      score={87}
                      title="Overall Score"
                      description="Campaign performance score"
                      trend={5}
                      size="medium"
                    />
                    <ScoreCard
                      score={92}
                      title="CTR Score"
                      description="Click-through rate performance"
                      trend={8}
                      size="medium"
                    />
                    <ScoreCard
                      score={78}
                      title="CPM Score"
                      description="Cost per thousand impressions"
                      trend={-2}
                      size="medium"
                    />
                    <ScoreCard
                      score={85}
                      title="ROAS Score"
                      description="Return on ad spend"
                      trend={12}
                      size="medium"
                    />
                  </div>

                  {/* Key Metrics Chart */}
                  <ChartView
                    data={getMockChartData()}
                    type="bar"
                    title="Key Performance Metrics"
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
                      data={getMockTrendData()}
                      type="line"
                      title="Score Trend Over Time"
                      xAxisKey="date"
                      yAxisKey="score"
                      height={300}
                    />
                    <ChartView
                      data={getMockTrendData()}
                      type="area"
                      title="Impressions & Clicks"
                      xAxisKey="date"
                      multipleSeries={true}
                      seriesKeys={['impressions', 'clicks']}
                      height={300}
                    />
                  </div>
                  <ChartView
                    data={getMockChartData()}
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

              {activeTab === 'details' && (
                <div className="space-y-4">
                  <div className="bg-gray-50 rounded-lg p-4">
                    <h3 className="font-medium text-gray-900 mb-2">Report Information</h3>
                    <div className="grid grid-cols-2 gap-4 text-sm">
                      <div>
                        <span className="text-gray-600">File Name:</span>
                        <span className="ml-2 font-medium">{selectedReport.filename}</span>
                      </div>
                      <div>
                        <span className="text-gray-600">File Size:</span>
                        <span className="ml-2 font-medium">{formatFileSize(selectedReport.file_size)}</span>
                      </div>
                      <div>
                        <span className="text-gray-600">Status:</span>
                        <span className={`ml-2 px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(selectedReport.status)}`}>
                          {selectedReport.status}
                        </span>
                      </div>
                      <div>
                        <span className="text-gray-600">Created:</span>
                        <span className="ml-2 font-medium">{formatDate(selectedReport.created_at)}</span>
                      </div>
                    </div>
                  </div>
                  
                  {reportData && (
                    <div className="bg-gray-50 rounded-lg p-4">
                      <h3 className="font-medium text-gray-900 mb-2">Processing Results</h3>
                      <pre className="text-sm text-gray-700 bg-white p-3 rounded border overflow-auto">
                        {JSON.stringify(reportData, null, 2)}
                      </pre>
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default ReportViewer; 