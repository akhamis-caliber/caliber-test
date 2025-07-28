import { useState, useEffect } from 'react';
import { useRouter } from 'next/router';
import { withAuth } from '../../../utils/authGuard';
import Layout from '../../../components/Shared/Layout';
import PageHeader from '../../../components/Shared/PageHeader';
import { campaignAPI } from '../../../services/api';
import { Card, CardContent, CardHeader, CardTitle } from '../../../components/ui/card.jsx';
import { Button } from '../../../components/ui/button.jsx';
import { Input } from '../../../components/ui/input.jsx';
import { Select } from '../../../components/ui/select.jsx';
import { Textarea } from '../../../components/ui/textarea.jsx';
import { ArrowLeftIcon, SaveIcon, XMarkIcon } from '@heroicons/react/24/outline';
import Link from 'next/link';

function EditCampaignPage() {
  const router = useRouter();
  const { id } = router.query;
  const [campaign, setCampaign] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    status: '',
    target_score: '',
    max_score: 100,
    min_score: 0
  });

  useEffect(() => {
    if (id) {
      fetchCampaign();
    }
  }, [id]);

  const fetchCampaign = async () => {
    try {
      setLoading(true);
      setError('');
      const response = await campaignAPI.getCampaign(id);
      const campaignData = response.data;
      setCampaign(campaignData);
      
      // Populate form data
      setFormData({
        name: campaignData.name || '',
        description: campaignData.description || '',
        status: campaignData.status || 'draft',
        target_score: campaignData.target_score || '',
        max_score: campaignData.max_score || 100,
        min_score: campaignData.min_score || 0
      });
    } catch (err) {
      console.error('Failed to fetch campaign:', err);
      setError(err.response?.data?.detail || 'Failed to load campaign');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    try {
      setSaving(true);
      setError('');
      
      const updateData = {
        ...formData,
        target_score: formData.target_score ? parseFloat(formData.target_score) : null,
        max_score: parseFloat(formData.max_score),
        min_score: parseFloat(formData.min_score)
      };
      
      await campaignAPI.updateCampaign(id, updateData);
      router.push(`/campaigns/${id}`);
    } catch (err) {
      console.error('Failed to update campaign:', err);
      setError(err.response?.data?.detail || 'Failed to update campaign');
    } finally {
      setSaving(false);
    }
  };

  const handleInputChange = (field, value) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  if (loading) {
    return (
      <Layout title="Edit Campaign - Caliber" description="Edit campaign details">
        <div className="flex items-center justify-center min-h-screen">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mx-auto mb-4"></div>
            <p className="text-gray-600">Loading campaign...</p>
          </div>
        </div>
      </Layout>
    );
  }

  if (error && !campaign) {
    return (
      <Layout title="Edit Campaign - Caliber" description="Edit campaign details">
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

  return (
    <Layout title={`Edit ${campaign?.name} - Caliber`} description="Edit campaign details">
      <PageHeader 
        title={`Edit Campaign: ${campaign?.name}`}
        description="Update campaign details and settings"
        breadcrumbs={[
          { label: 'Campaigns', href: '/campaigns' },
          { label: campaign?.name, href: `/campaigns/${id}` },
          { label: 'Edit' }
        ]}
        actions={
          <div className="flex space-x-3">
            <Link href={`/campaigns/${id}`}>
              <Button variant="outline">
                <XMarkIcon className="w-4 h-4 mr-2" />
                Cancel
              </Button>
            </Link>
          </div>
        }
      />

      <div className="max-w-4xl mx-auto">
        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Basic Information */}
          <Card>
            <CardHeader>
              <CardTitle>Basic Information</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <label htmlFor="name" className="block text-sm font-medium text-gray-700 mb-1">
                  Campaign Name *
                </label>
                <Input
                  id="name"
                  type="text"
                  value={formData.name}
                  onChange={(e) => handleInputChange('name', e.target.value)}
                  placeholder="Enter campaign name"
                  required
                />
              </div>

              <div>
                <label htmlFor="description" className="block text-sm font-medium text-gray-700 mb-1">
                  Description
                </label>
                <Textarea
                  id="description"
                  value={formData.description}
                  onChange={(e) => handleInputChange('description', e.target.value)}
                  placeholder="Enter campaign description"
                  rows={4}
                />
              </div>

              <div>
                <label htmlFor="status" className="block text-sm font-medium text-gray-700 mb-1">
                  Status
                </label>
                <Select
                  id="status"
                  value={formData.status}
                  onValueChange={(value) => handleInputChange('status', value)}
                >
                  <option value="draft">Draft</option>
                  <option value="active">Active</option>
                  <option value="paused">Paused</option>
                  <option value="completed">Completed</option>
                  <option value="archived">Archived</option>
                </Select>
              </div>
            </CardContent>
          </Card>

          {/* Scoring Configuration */}
          <Card>
            <CardHeader>
              <CardTitle>Scoring Configuration</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                  <label htmlFor="target_score" className="block text-sm font-medium text-gray-700 mb-1">
                    Target Score
                  </label>
                  <Input
                    id="target_score"
                    type="number"
                    min="0"
                    max="100"
                    step="0.1"
                    value={formData.target_score}
                    onChange={(e) => handleInputChange('target_score', e.target.value)}
                    placeholder="0-100"
                  />
                  <p className="text-xs text-gray-500 mt-1">Optional target score (0-100)</p>
                </div>

                <div>
                  <label htmlFor="max_score" className="block text-sm font-medium text-gray-700 mb-1">
                    Maximum Score *
                  </label>
                  <Input
                    id="max_score"
                    type="number"
                    min="0"
                    step="0.1"
                    value={formData.max_score}
                    onChange={(e) => handleInputChange('max_score', e.target.value)}
                    required
                  />
                </div>

                <div>
                  <label htmlFor="min_score" className="block text-sm font-medium text-gray-700 mb-1">
                    Minimum Score *
                  </label>
                  <Input
                    id="min_score"
                    type="number"
                    min="0"
                    step="0.1"
                    value={formData.min_score}
                    onChange={(e) => handleInputChange('min_score', e.target.value)}
                    required
                  />
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Campaign Details */}
          <Card>
            <CardHeader>
              <CardTitle>Campaign Details</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Template Type
                  </label>
                  <p className="text-sm text-gray-600 bg-gray-50 px-3 py-2 rounded">
                    {campaign?.template_type || 'Custom'}
                  </p>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Total Submissions
                  </label>
                  <p className="text-sm text-gray-600 bg-gray-50 px-3 py-2 rounded">
                    {campaign?.total_submissions || 0}
                  </p>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Average Score
                  </label>
                  <p className="text-sm text-gray-600 bg-gray-50 px-3 py-2 rounded">
                    {campaign?.average_score ? `${campaign.average_score.toFixed(1)}/100` : 'N/A'}
                  </p>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Created Date
                  </label>
                  <p className="text-sm text-gray-600 bg-gray-50 px-3 py-2 rounded">
                    {campaign?.created_at ? new Date(campaign.created_at).toLocaleDateString() : 'N/A'}
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Error Display */}
          {error && (
            <Card className="border-red-200 bg-red-50">
              <CardContent className="pt-6">
                <div className="flex items-center text-red-600">
                  <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
                  </svg>
                  {error}
                </div>
              </CardContent>
            </Card>
          )}

          {/* Form Actions */}
          <div className="flex justify-end space-x-3">
            <Link href={`/campaigns/${id}`}>
              <Button variant="outline" type="button">
                <XMarkIcon className="w-4 h-4 mr-2" />
                Cancel
              </Button>
            </Link>
            <Button type="submit" disabled={saving}>
              <SaveIcon className="w-4 h-4 mr-2" />
              {saving ? 'Saving...' : 'Save Changes'}
            </Button>
          </div>
        </form>
      </div>
    </Layout>
  );
}

export default withAuth(EditCampaignPage, {
  redirectTo: '/login',
  requireEmailVerification: false
}); 