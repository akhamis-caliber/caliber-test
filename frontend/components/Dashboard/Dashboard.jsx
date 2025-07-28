import { useState, useEffect } from 'react';
import { useRouter } from 'next/router';
import Link from 'next/link';
import { 
  PlusIcon, 
  DocumentArrowUpIcon, 
  ChartBarIcon, 
  DocumentTextIcon,
  ClockIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon,
  ArrowTrendingUpIcon,
  ArrowTrendingDownIcon
} from '@heroicons/react/24/outline';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar } from 'recharts';
import { campaignAPI, reportAPI } from '../../services/api';
import LoadingSpinner from '../Shared/LoadingSpinner';

const mockScoringData = [
  { month: 'Jan', score: 75, reports: 12 },
  { month: 'Feb', score: 82, reports: 15 },
  { month: 'Mar', score: 78, reports: 18 },
  { month: 'Apr', score: 85, reports: 22 },
  { month: 'May', score: 88, reports: 25 },
  { month: 'Jun', score: 92, reports: 28 },
];

const mockRecentActivity = [
  {
    id: 1,
    type: 'report_uploaded',
    title: 'Q2 Marketing Report uploaded',
    description: 'New report uploaded and processing started',
    time: '2 hours ago',
    status: 'processing'
  },
  {
    id: 2,
    type: 'campaign_created',
    title: 'Summer Campaign created',
    description: 'New campaign "Summer 2024" has been created',
    time: '1 day ago',
    status: 'completed'
  },
  {
    id: 3,
    type: 'report_completed',
    title: 'Q1 Sales Report completed',
    description: 'Scoring analysis completed with 85% accuracy',
    time: '2 days ago',
    status: 'completed'
  },
  {
    id: 4,
    type: 'campaign_updated',
    title: 'Spring Campaign updated',
    description: 'Campaign parameters have been modified',
    time: '3 days ago',
    status: 'completed'
  }
];

export default function Dashboard() {
  const [stats, setStats] = useState({
    totalCampaigns: 0,
    totalReports: 0,
    averageScore: 0,
    recentReports: 0
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const router = useRouter();

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      // Fetch campaigns and reports data
      const [campaignsResponse, reportsResponse] = await Promise.all([
        campaignAPI.getCampaigns(),
        reportAPI.getReports()
      ]);

      const campaigns = campaignsResponse.data || [];
      const reports = reportsResponse.data || [];

      // Calculate stats
      const totalCampaigns = campaigns.length;
      const totalReports = reports.length;
      const averageScore = reports.length > 0 
        ? reports.reduce((sum, report) => sum + (report.score || 0), 0) / reports.length 
        : 0;
      const recentReports = reports.filter(report => {
        const reportDate = new Date(report.created_at || report.uploaded_at);
        const weekAgo = new Date();
        weekAgo.setDate(weekAgo.getDate() - 7);
        return reportDate > weekAgo;
      }).length;

      setStats({
        totalCampaigns,
        totalReports,
        averageScore: Math.round(averageScore),
        recentReports
      });
    } catch (err) {
      console.error('Error fetching dashboard data:', err);
      setError('Failed to load dashboard data');
    } finally {
      setLoading(false);
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'completed':
        return <CheckCircleIcon className="w-5 h-5 text-green-500" />;
      case 'processing':
        return <ClockIcon className="w-5 h-5 text-yellow-500" />;
      case 'error':
        return <ExclamationTriangleIcon className="w-5 h-5 text-red-500" />;
      default:
        return <ClockIcon className="w-5 h-5 text-gray-400" />;
    }
  };

  const getActivityIcon = (type) => {
    switch (type) {
      case 'report_uploaded':
        return <DocumentArrowUpIcon className="w-5 h-5 text-blue-500" />;
      case 'campaign_created':
        return <PlusIcon className="w-5 h-5 text-green-500" />;
      case 'report_completed':
        return <CheckCircleIcon className="w-5 h-5 text-green-500" />;
      case 'campaign_updated':
        return <ChartBarIcon className="w-5 h-5 text-purple-500" />;
      default:
        return <DocumentTextIcon className="w-5 h-5 text-gray-500" />;
    }
  };

  if (loading) {
    return <LoadingSpinner size="lg" className="h-64" />;
  }

  if (error) {
    return (
      <div className="text-center py-12">
        <ExclamationTriangleIcon className="mx-auto h-12 w-12 text-red-500" />
        <h3 className="mt-2 text-sm font-medium text-gray-900">Error</h3>
        <p className="mt-1 text-sm text-gray-500">{error}</p>
        <button
          onClick={fetchDashboardData}
          className="mt-4 inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700"
        >
          Try Again
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Welcome Section */}
      <div className="bg-gradient-to-r from-indigo-600 to-purple-600 rounded-lg shadow-lg p-6 text-white">
        <h1 className="text-2xl font-bold">Welcome back!</h1>
        <p className="text-indigo-100 mt-1">Here's what's happening with your campaigns and reports.</p>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <div className="p-2 bg-blue-100 rounded-lg">
              <ChartBarIcon className="w-6 h-6 text-blue-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Total Campaigns</p>
              <p className="text-2xl font-bold text-gray-900">{stats.totalCampaigns}</p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <div className="p-2 bg-green-100 rounded-lg">
              <DocumentTextIcon className="w-6 h-6 text-green-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Total Reports</p>
              <p className="text-2xl font-bold text-gray-900">{stats.totalReports}</p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <div className="p-2 bg-yellow-100 rounded-lg">
              <ArrowTrendingUpIcon className="w-6 h-6 text-yellow-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Average Score</p>
              <p className="text-2xl font-bold text-gray-900">{stats.averageScore}%</p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <div className="p-2 bg-purple-100 rounded-lg">
              <ClockIcon className="w-6 h-6 text-purple-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Recent Reports</p>
              <p className="text-2xl font-bold text-gray-900">{stats.recentReports}</p>
            </div>
          </div>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="bg-white rounded-lg shadow">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-lg font-medium text-gray-900">Quick Actions</h2>
        </div>
        <div className="p-6">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            <Link
              href="/campaigns/create-with-upload"
              className="flex items-center p-4 border border-gray-200 rounded-lg hover:border-indigo-300 hover:bg-indigo-50 transition-colors"
            >
              <div className="p-2 bg-indigo-100 rounded-lg">
                <PlusIcon className="w-6 h-6 text-indigo-600" />
              </div>
              <div className="ml-4">
                <h3 className="text-sm font-medium text-gray-900">Create Campaign & Upload Data</h3>
                <p className="text-sm text-gray-500">Create campaign and upload dataset in one flow</p>
              </div>
            </Link>

            <Link
              href="/campaigns/new"
              className="flex items-center p-4 border border-gray-200 rounded-lg hover:border-indigo-300 hover:bg-indigo-50 transition-colors"
            >
              <div className="p-2 bg-purple-100 rounded-lg">
                <PlusIcon className="w-6 h-6 text-purple-600" />
              </div>
              <div className="ml-4">
                <h3 className="text-sm font-medium text-gray-900">Create Campaign Only</h3>
                <p className="text-sm text-gray-500">Create campaign without uploading data</p>
              </div>
            </Link>

            <Link
              href="/reports/upload"
              className="flex items-center p-4 border border-gray-200 rounded-lg hover:border-indigo-300 hover:bg-indigo-50 transition-colors"
            >
              <div className="p-2 bg-green-100 rounded-lg">
                <DocumentArrowUpIcon className="w-6 h-6 text-green-600" />
              </div>
              <div className="ml-4">
                <h3 className="text-sm font-medium text-gray-900">Upload Report</h3>
                <p className="text-sm text-gray-500">Upload and analyze a new report</p>
              </div>
            </Link>
          </div>
        </div>
      </div>

      {/* Charts and Activity */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Scoring Trends Chart */}
        <div className="bg-white rounded-lg shadow">
          <div className="px-6 py-4 border-b border-gray-200">
            <h2 className="text-lg font-medium text-gray-900">Scoring Trends</h2>
          </div>
          <div className="p-6">
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={mockScoringData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="month" />
                <YAxis />
                <Tooltip />
                <Line 
                  type="monotone" 
                  dataKey="score" 
                  stroke="#4f46e5" 
                  strokeWidth={2}
                  name="Average Score"
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Recent Activity */}
        <div className="bg-white rounded-lg shadow">
          <div className="px-6 py-4 border-b border-gray-200">
            <h2 className="text-lg font-medium text-gray-900">Recent Activity</h2>
          </div>
          <div className="p-6">
            <div className="space-y-4">
              {mockRecentActivity.map((activity) => (
                <div key={activity.id} className="flex items-start space-x-3">
                  <div className="flex-shrink-0 mt-1">
                    {getActivityIcon(activity.type)}
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-gray-900">{activity.title}</p>
                    <p className="text-sm text-gray-500">{activity.description}</p>
                    <div className="flex items-center mt-1">
                      <span className="text-xs text-gray-400">{activity.time}</span>
                      <div className="ml-2 flex items-center">
                        {getStatusIcon(activity.status)}
                        <span className="ml-1 text-xs text-gray-500 capitalize">{activity.status}</span>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
            <div className="mt-6">
              <Link
                href="/activity"
                className="text-sm text-indigo-600 hover:text-indigo-500 font-medium"
              >
                View all activity →
              </Link>
            </div>
          </div>
        </div>
      </div>

      {/* Reports Overview Chart */}
      <div className="bg-white rounded-lg shadow">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-lg font-medium text-gray-900">Reports Overview</h2>
        </div>
        <div className="p-6">
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={mockScoringData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="month" />
              <YAxis />
              <Tooltip />
              <Bar dataKey="reports" fill="#10b981" name="Number of Reports" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
} 