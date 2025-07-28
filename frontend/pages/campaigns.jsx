import { useState, useEffect } from 'react';
import { withAuth } from '../utils/authGuard';
import Layout from '../components/Shared/Layout';
import PageHeader from '../components/Shared/PageHeader';
import { campaignAPI } from '../services/api';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card.jsx';
import { Badge } from '../components/ui/badge.jsx';
import { Button } from '../components/ui/button.jsx';
import { Input } from '../components/ui/input.jsx';
import { Select } from '../components/ui/select.jsx';
import { 
  PlusIcon, 
  MagnifyingGlassIcon, 
  FunnelIcon,
  EllipsisVerticalIcon,
  ChartBarIcon,
  DocumentTextIcon,
  ClockIcon,
  UserIcon,
  TrashIcon,
  PencilIcon,
  EyeIcon,
  PlayIcon,
  PauseIcon,
  ArchiveBoxIcon,
  ChartBarSquareIcon
} from '@heroicons/react/24/outline';
import Link from 'next/link';
import { useRouter } from 'next/router';

function CampaignsPage() {
  const router = useRouter();
  const [campaigns, setCampaigns] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [showFilters, setShowFilters] = useState(false);
  const [selectedCampaign, setSelectedCampaign] = useState(null);
  const [showActionsMenu, setShowActionsMenu] = useState(null);

  useEffect(() => {
    fetchCampaigns();
  }, []);

  const fetchCampaigns = async () => {
    try {
      setLoading(true);
      setError('');
      const response = await campaignAPI.getCampaigns();
      setCampaigns(response.data || []);
    } catch (err) {
      console.error('Failed to fetch campaigns:', err);
      setError(err.response?.data?.detail || 'Failed to load campaigns');
    } finally {
      setLoading(false);
    }
  };

  const handleStatusUpdate = async (campaignId, newStatus) => {
    try {
      await campaignAPI.updateCampaign(campaignId, { status: newStatus });
      await fetchCampaigns(); // Refresh the list
      setShowActionsMenu(null);
    } catch (err) {
      console.error('Failed to update campaign status:', err);
      alert('Failed to update campaign status');
    }
  };

  const handleDeleteCampaign = async (campaignId) => {
    if (!confirm('Are you sure you want to delete this campaign? This action cannot be undone.')) {
      return;
    }

    try {
      await campaignAPI.deleteCampaign(campaignId);
      await fetchCampaigns(); // Refresh the list
      setShowActionsMenu(null);
    } catch (err) {
      console.error('Failed to delete campaign:', err);
      alert('Failed to delete campaign');
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
    if (!score) return 'text-gray-500';
    if (score >= 90) return 'text-green-600';
    if (score >= 80) return 'text-blue-600';
    if (score >= 70) return 'text-yellow-600';
    return 'text-red-600';
  };

  const filteredCampaigns = campaigns.filter(campaign => {
    const matchesSearch = campaign.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         campaign.description?.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesStatus = !statusFilter || campaign.status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  const getStatusOptions = () => {
    const statuses = [...new Set(campaigns.map(c => c.status))];
    return [
      { value: '', label: 'All Statuses' },
      ...statuses.map(status => ({ value: status, label: status.charAt(0).toUpperCase() + status.slice(1) }))
    ];
  };

  const renderCampaignCard = (campaign) => (
    <Card key={campaign.id} className="hover:shadow-md transition-shadow">
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <div className="flex items-center space-x-3">
          <div className="p-2 bg-indigo-100 rounded-lg">
            <ChartBarIcon className="h-5 w-5 text-indigo-600" />
          </div>
          <div>
            <CardTitle className="text-lg font-semibold text-gray-900">
              {campaign.name}
            </CardTitle>
            <p className="text-sm text-gray-500">
              Created {new Date(campaign.created_at).toLocaleDateString()}
            </p>
          </div>
        </div>
        <div className="relative">
          <button
            onClick={() => setShowActionsMenu(showActionsMenu === campaign.id ? null : campaign.id)}
            className="p-2 hover:bg-gray-100 rounded-full transition-colors"
          >
            <EllipsisVerticalIcon className="h-5 w-5 text-gray-400" />
          </button>
          
          {showActionsMenu === campaign.id && (
            <div className="absolute right-0 top-10 w-48 bg-white rounded-md shadow-lg border border-gray-200 z-10">
              <div className="py-1">
                <Link href={`/campaigns/${campaign.id}`}>
                  <button className="w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 flex items-center">
                    <EyeIcon className="h-4 w-4 mr-2" />
                    View Details
                  </button>
                </Link>
                <Link href={`/scoring-results?campaign_id=${campaign.id}`}>
                  <button className="w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 flex items-center">
                    <ChartBarSquareIcon className="h-4 w-4 mr-2" />
                    View Scoring Results
                  </button>
                </Link>
                <button 
                  onClick={() => router.push(`/campaigns/${campaign.id}/edit`)}
                  className="w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 flex items-center"
                >
                  <PencilIcon className="h-4 w-4 mr-2" />
                  Edit Campaign
                </button>
                {campaign.status === 'draft' && (
                  <button 
                    onClick={() => handleStatusUpdate(campaign.id, 'active')}
                    className="w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 flex items-center"
                  >
                    <PlayIcon className="h-4 w-4 mr-2" />
                    Activate
                  </button>
                )}
                {campaign.status === 'active' && (
                  <button 
                    onClick={() => handleStatusUpdate(campaign.id, 'paused')}
                    className="w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 flex items-center"
                  >
                    <PauseIcon className="h-4 w-4 mr-2" />
                    Pause
                  </button>
                )}
                {campaign.status === 'paused' && (
                  <button 
                    onClick={() => handleStatusUpdate(campaign.id, 'active')}
                    className="w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 flex items-center"
                  >
                    <PlayIcon className="h-4 w-4 mr-2" />
                    Resume
                  </button>
                )}
                {campaign.status !== 'archived' && (
                  <button 
                    onClick={() => handleStatusUpdate(campaign.id, 'archived')}
                    className="w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 flex items-center"
                  >
                    <ArchiveBoxIcon className="h-4 w-4 mr-2" />
                    Archive
                  </button>
                )}
                <button 
                  onClick={() => handleDeleteCampaign(campaign.id)}
                  className="w-full text-left px-4 py-2 text-sm text-red-600 hover:bg-red-50 flex items-center"
                >
                  <TrashIcon className="h-4 w-4 mr-2" />
                  Delete
                </button>
              </div>
            </div>
          )}
        </div>
      </CardHeader>
      
      <CardContent>
        <div className="space-y-4">
          <p className="text-gray-600 text-sm">
            {campaign.description || 'No description provided'}
          </p>
          
          <div className="flex items-center justify-between">
            <Badge className={getStatusColor(campaign.status)}>
              {campaign.status}
            </Badge>
            <div className="text-sm text-gray-500">
              {campaign.total_submissions || 0} submissions
            </div>
          </div>
          
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <span className="text-gray-500">Template:</span>
              <span className="ml-1 font-medium">{campaign.template_type}</span>
            </div>
            <div>
              <span className="text-gray-500">Avg Score:</span>
              <span className={`ml-1 font-medium ${getScoreColor(campaign.average_score)}`}>
                {campaign.average_score ? `${campaign.average_score.toFixed(1)}/100` : 'N/A'}
              </span>
            </div>
          </div>
          
          <div className="flex space-x-2">
            <Link href={`/campaigns/${campaign.id}`}>
              <Button variant="outline" size="sm" className="flex-1">
                <EyeIcon className="h-4 w-4 mr-1" />
                View Details
              </Button>
            </Link>
            <Link href={`/scoring-results?campaign_id=${campaign.id}`}>
              <Button variant="outline" size="sm" className="flex-1">
                <ChartBarSquareIcon className="h-4 w-4 mr-1" />
                Results
              </Button>
            </Link>
            <Link href={`/upload?campaign_id=${campaign.id}`}>
              <Button size="sm" className="flex-1">
                <DocumentTextIcon className="h-4 w-4 mr-1" />
                Upload Data
              </Button>
            </Link>
          </div>
        </div>
      </CardContent>
    </Card>
  );

  if (loading) {
    return (
      <Layout title="Campaigns - Caliber" description="Manage your marketing campaigns">
        <div className="flex items-center justify-center min-h-screen">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mx-auto mb-4"></div>
            <p className="text-gray-600">Loading campaigns...</p>
          </div>
        </div>
      </Layout>
    );
  }

  return (
    <Layout title="Campaigns - Caliber" description="Manage your marketing campaigns">
      <PageHeader 
        title="Campaigns"
        description="Create and manage your marketing campaigns"
        breadcrumbs={[{ label: 'Campaigns' }]}
        actions={
          <div className="flex space-x-3">
            <Link href="/campaigns/compare">
              <Button variant="outline">
                <ChartBarIcon className="h-4 w-4 mr-2" />
                Compare
              </Button>
            </Link>
            <Link href="/campaigns/new">
              <Button>
                <PlusIcon className="h-4 w-4 mr-2" />
                New Campaign
              </Button>
            </Link>
          </div>
        }
      />
      
      <div className="space-y-6">
        {/* Stats Overview */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Total Campaigns</CardTitle>
              <ChartBarIcon className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{campaigns.length}</div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Active Campaigns</CardTitle>
              <PlayIcon className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {campaigns.filter(c => c.status === 'active').length}
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Total Submissions</CardTitle>
              <DocumentTextIcon className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {campaigns.reduce((sum, c) => sum + (c.total_submissions || 0), 0)}
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Avg Score</CardTitle>
              <ChartBarIcon className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {(() => {
                  const scores = campaigns.map(c => c.average_score).filter(s => s !== null && s !== undefined);
                  return scores.length > 0 ? (scores.reduce((a, b) => a + b, 0) / scores.length).toFixed(1) : 'N/A';
                })()}
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Filters and Search */}
        <Card>
          <CardContent className="pt-6">
            <div className="flex flex-col sm:flex-row gap-4">
              <div className="relative flex-1">
                <MagnifyingGlassIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                <Input
                  type="text"
                  placeholder="Search campaigns..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-10"
                />
              </div>
              
              <div className="flex items-center space-x-2">
                <Select
                  value={statusFilter}
                  onValueChange={setStatusFilter}
                  className="w-40"
                >
                  <option value="">All Statuses</option>
                  <option value="draft">Draft</option>
                  <option value="active">Active</option>
                  <option value="paused">Paused</option>
                  <option value="completed">Completed</option>
                  <option value="archived">Archived</option>
                </Select>
                
                <Button
                  variant="outline"
                  onClick={() => setShowFilters(!showFilters)}
                  className="flex items-center"
                >
                  <FunnelIcon className="h-4 w-4 mr-2" />
                  Filters
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Campaigns List */}
        {error ? (
          <Card>
            <CardContent className="pt-6">
              <div className="text-center py-8">
                <div className="text-red-600 mb-4">
                  <svg className="w-16 h-16 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
                  </svg>
                </div>
                <h3 className="text-lg font-medium text-gray-900 mb-2">Error Loading Campaigns</h3>
                <p className="text-gray-600 mb-4">{error}</p>
                <Button onClick={fetchCampaigns}>
                  Try Again
                </Button>
              </div>
            </CardContent>
          </Card>
        ) : filteredCampaigns.length === 0 ? (
          <Card>
            <CardContent className="pt-6">
              <div className="text-center py-12">
                <div className="text-gray-400 mb-4">
                  <ChartBarIcon className="w-16 h-16 mx-auto" />
                </div>
                <h3 className="text-lg font-medium text-gray-900 mb-2">
                  {campaigns.length === 0 ? 'No Campaigns Yet' : 'No Campaigns Found'}
                </h3>
                <p className="text-gray-600 mb-6">
                  {campaigns.length === 0 
                    ? 'Get started by creating your first campaign to manage and analyze your marketing data.'
                    : 'Try adjusting your search or filter criteria.'
                  }
                </p>
                {campaigns.length === 0 && (
                  <Link href="/campaigns/new">
                    <Button>
                      <PlusIcon className="h-4 w-4 mr-2" />
                      Create Your First Campaign
                    </Button>
                  </Link>
                )}
              </div>
            </CardContent>
          </Card>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {filteredCampaigns.map(renderCampaignCard)}
          </div>
        )}
      </div>

      {/* Click outside to close actions menu */}
      {showActionsMenu && (
        <div 
          className="fixed inset-0 z-0" 
          onClick={() => setShowActionsMenu(null)}
        />
      )}
    </Layout>
  );
}

export default withAuth(CampaignsPage, {
  redirectTo: '/login',
  requireEmailVerification: false
}); 