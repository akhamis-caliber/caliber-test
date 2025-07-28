import { useState, useEffect } from 'react';
import { useRouter } from 'next/router';
import { withAuth } from '../../utils/authGuard';
import Layout from '../../components/Shared/Layout';
import PageHeader from '../../components/Shared/PageHeader';
import { campaignAPI } from '../../services/api';
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/card.jsx';
import { Badge } from '../../components/ui/badge.jsx';
import { Button } from '../../components/ui/button.jsx';
import { ArrowLeftIcon, ChartBarIcon, DocumentTextIcon, ClockIcon, UserIcon } from '@heroicons/react/24/outline';
import Link from 'next/link';
import CampaignAnalytics from '../../components/CampaignAnalytics/CampaignAnalytics';

function CampaignResultsPage() {
  const router = useRouter();
  const { id } = router.query;
  const [campaign, setCampaign] = useState(null);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    if (id) {
      fetchCampaignData();
    }
  }, [id]);

  const fetchCampaignData = async () => {
    try {
      setLoading(true);
      setError('');
      
      // Fetch campaign details
      const campaignResponse = await campaignAPI.getCampaign(id);
      setCampaign(campaignResponse.data);
      
      // Fetch campaign statistics
      const statsResponse = await campaignAPI.getCampaignStats(id);
      setStats(statsResponse.data);
    } catch (err) {
      console.error('Failed to fetch campaign data:', err);
      setError(err.response?.data?.detail || 'Failed to load campaign data');
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status) => {
    switch (status?.toLowerCase()) {
      case 'active':
        return 'bg-green-100 text-green-800';
      case 'draft':
        return 'bg-gray-100 text-gray-800';
      case 'paused':
        return 'bg-yellow-100 text-yellow-800';
      case 'completed':
        return 'bg-blue-100 text-blue-800';
      case 'archived':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getScoreColor = (score) => {
    if (score >= 90) return 'text-green-600 bg-green-100';
    if (score >= 80) return 'text-blue-600 bg-blue-100';
    if (score >= 70) return 'text-yellow-600 bg-yellow-100';
    return 'text-red-600 bg-red-100';
  };

  if (loading) {
    return (
      <Layout title="Campaign Results - Caliber" description="Campaign results and analytics">
        <div className="flex items-center justify-center min-h-screen">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mx-auto mb-4"></div>
            <p className="text-gray-600">Loading campaign data...</p>
          </div>
        </div>
      </Layout>
    );
  }

  if (error) {
    return (
      <Layout title="Campaign Results - Caliber" description="Campaign results and analytics">
        <div className="flex items-center justify-center min-h-screen">
          <div className="text-center">
            <div className="text-red-600 mb-4">
              <svg className="w-16 h-16 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
              </svg>
            </div>
            <h3 className="text-lg font-medium text-gray-900 mb-2">Error Loading Campaign</h3>
            <p className="text-gray-600 mb-4">{error}</p>
            <Link href="/campaigns">
              <Button>
                <ArrowLeftIcon className="w-4 h-4 mr-2" />
                Back to Campaigns
              </Button>
            </Link>
          </div>
        </div>
      </Layout>
    );
  }

  if (!campaign) {
    return (
      <Layout title="Campaign Results - Caliber" description="Campaign results and analytics">
        <div className="flex items-center justify-center min-h-screen">
          <div className="text-center">
            <h3 className="text-lg font-medium text-gray-900 mb-2">Campaign Not Found</h3>
            <p className="text-gray-600 mb-4">The campaign you're looking for doesn't exist.</p>
            <Link href="/campaigns">
              <Button>
                <ArrowLeftIcon className="w-4 h-4 mr-2" />
                Back to Campaigns
              </Button>
            </Link>
          </div>
        </div>
      </Layout>
    );
  }

  return (
    <Layout title={`${campaign.name} - Campaign Results - Caliber`} description="Campaign results and analytics">
      <PageHeader 
        title={campaign.name}
        description="Campaign results and detailed analytics"
        breadcrumbs={[
          { label: 'Campaigns', href: '/campaigns' },
          { label: campaign.name }
        ]}
        actions={
          <Link href="/campaigns">
            <Button variant="outline">
              <ArrowLeftIcon className="w-4 h-4 mr-2" />
              Back to Campaigns
            </Button>
          </Link>
        }
      />

      <div className="space-y-6">
        {/* Campaign Overview */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Status</CardTitle>
              <DocumentTextIcon className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <Badge className={getStatusColor(campaign.status)}>
                {campaign.status}
              </Badge>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Total Submissions</CardTitle>
              <ChartBarIcon className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{campaign.total_submissions || 0}</div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Average Score</CardTitle>
              <ChartBarIcon className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {campaign.average_score ? `${campaign.average_score.toFixed(1)}/100` : 'N/A'}
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Created</CardTitle>
              <ClockIcon className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-sm">
                {new Date(campaign.created_at).toLocaleDateString()}
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Campaign Details */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2">
            <Card>
              <CardHeader>
                <CardTitle>Campaign Details</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <h4 className="font-medium text-gray-900">Description</h4>
                  <p className="text-gray-600 mt-1">
                    {campaign.description || 'No description provided'}
                  </p>
                </div>
                
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <h4 className="font-medium text-gray-900">Template Type</h4>
                    <p className="text-gray-600 mt-1">{campaign.template_type}</p>
                  </div>
                  <div>
                    <h4 className="font-medium text-gray-900">Max Score</h4>
                    <p className="text-gray-600 mt-1">{campaign.max_score}/100</p>
                  </div>
                  {campaign.target_score && (
                    <div>
                      <h4 className="font-medium text-gray-900">Target Score</h4>
                      <p className="text-gray-600 mt-1">{campaign.target_score}/100</p>
                    </div>
                  )}
                  <div>
                    <h4 className="font-medium text-gray-900">Min Score</h4>
                    <p className="text-gray-600 mt-1">{campaign.min_score}/100</p>
                  </div>
                </div>

                {campaign.scoring_criteria && (
                  <div>
                    <h4 className="font-medium text-gray-900">Scoring Criteria</h4>
                    <div className="mt-2 space-y-2">
                      {campaign.scoring_criteria.map((criteria, index) => (
                        <div key={index} className="flex justify-between items-center p-2 bg-gray-50 rounded">
                          <span className="text-sm">{criteria.criterion_name}</span>
                          <Badge variant="outline">{(criteria.weight * 100).toFixed(0)}%</Badge>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>

          <div>
            <Card>
              <CardHeader>
                <CardTitle>Quick Actions</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <Button className="w-full" variant="outline">
                  <ChartBarIcon className="w-4 h-4 mr-2" />
                  View Analytics
                </Button>
                <Button className="w-full" variant="outline">
                  <DocumentTextIcon className="w-4 h-4 mr-2" />
                  Export Results
                </Button>
                <Button className="w-full" variant="outline">
                  <UserIcon className="w-4 h-4 mr-2" />
                  Share Report
                </Button>
              </CardContent>
            </Card>

            {stats && (
              <Card className="mt-6">
                <CardHeader>
                  <CardTitle>Performance Stats</CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-600">Total Reports</span>
                    <span className="font-medium">{stats.total_reports}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-600">Completed</span>
                    <span className="font-medium">{stats.completed_reports}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-600">Pending</span>
                    <span className="font-medium">{stats.pending_reports}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-600">Average Score</span>
                    <span className={`font-medium ${getScoreColor(stats.average_score)}`}>
                      {stats.average_score?.toFixed(1) || 'N/A'}
                    </span>
                  </div>
                </CardContent>
              </Card>
            )}
          </div>
        </div>

        {/* Analytics Section */}
        <Card>
          <CardHeader>
            <CardTitle>Campaign Analytics</CardTitle>
          </CardHeader>
          <CardContent>
            <CampaignAnalytics campaignId={id} />
          </CardContent>
        </Card>

        {/* Reports Section */}
        <Card>
          <CardHeader>
            <CardTitle>Campaign Reports</CardTitle>
          </CardHeader>
          <CardContent>
            {campaign.reports && campaign.reports.length > 0 ? (
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Report Name
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Status
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Score
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Uploaded
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {campaign.reports.map((report) => (
                      <tr key={report.id} className="hover:bg-gray-50">
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="text-sm font-medium text-gray-900">
                            {report.filename}
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <Badge className={getStatusColor(report.status)}>
                            {report.status}
                          </Badge>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          {report.score ? (
                            <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getScoreColor(report.score)}`}>
                              {report.score.toFixed(1)}/100
                            </span>
                          ) : (
                            <span className="text-gray-500">N/A</span>
                          )}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {new Date(report.created_at).toLocaleDateString()}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="text-center py-8">
                <div className="text-gray-400 mb-4">
                  <DocumentTextIcon className="w-16 h-16 mx-auto" />
                </div>
                <h3 className="text-lg font-medium text-gray-900 mb-2">No Reports Yet</h3>
                <p className="text-gray-600 mb-4">Upload reports to see results and analytics.</p>
                <Link href="/upload">
                  <Button>
                    Upload Report
                  </Button>
                </Link>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </Layout>
  );
}

export default withAuth(CampaignResultsPage, {
  redirectTo: '/login',
  requireEmailVerification: false
}); 