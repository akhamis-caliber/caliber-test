import { useState, useEffect } from 'react';
import { withAuth } from '../utils/authGuard';
import Layout from '../components/Shared/Layout';
import PageHeader from '../components/Shared/PageHeader';
import CampaignWizard from '../components/CampaignWizard/CampaignWizard';
import { PlusIcon } from '@heroicons/react/24/outline';
import toast from 'react-hot-toast';
import { campaignAPI } from '../services/api';
import Link from 'next/link';

function CampaignPage() {
  const [showWizard, setShowWizard] = useState(false);
  const [campaigns, setCampaigns] = useState([]);
  const [loading, setLoading] = useState(false);
  const [editCampaign, setEditCampaign] = useState(null);

  // Fetch campaigns from backend on mount
  useEffect(() => {
    fetchCampaigns();
  }, []);

  const fetchCampaigns = async () => {
    setLoading(true);
    try {
      const response = await campaignAPI.getCampaigns();
      setCampaigns(response.data);
    } catch (error) {
      console.error('Failed to fetch campaigns', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateCampaign = async (campaignData) => {
    setShowWizard(false);
    setEditCampaign(null);
    try {
      if (editCampaign) {
        // Update existing campaign
        await campaignAPI.updateCampaign(editCampaign.id, campaignData);
        toast.success('Campaign updated successfully!');
      } else {
        // Create new campaign
        await campaignAPI.createCampaign(campaignData);
        toast.success('Campaign created successfully!');
      }
      fetchCampaigns();
    } catch (error) {
      toast.error('Failed to save campaign');
    }
  };

  const handleEdit = (campaign) => {
    setEditCampaign(campaign);
    setShowWizard(true);
  };

  const handleDelete = async (campaignId) => {
    if (!window.confirm('Are you sure you want to delete this campaign?')) return;
    try {
      await campaignAPI.deleteCampaign(campaignId);
      setCampaigns((prev) => prev.filter((c) => c.id !== campaignId));
      toast.success('Campaign deleted');
    } catch (error) {
      toast.error('Failed to delete campaign');
    }
  };

  const handleWizardClose = () => {
    setShowWizard(false);
    setEditCampaign(null);
  };

  return (
    <Layout title="Campaigns - Caliber" description="Manage your marketing campaigns">
      <PageHeader 
        title="Campaigns"
        description="Create and manage your marketing campaigns"
        breadcrumbs={[{ label: 'Campaigns' }]}
        actions={
          <button
            onClick={() => { setShowWizard(true); setEditCampaign(null); }}
            className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
          >
            <PlusIcon className="w-4 h-4 mr-2" />
            Create Campaign
          </button>
        }
      />

      {/* Campaign List */}
      <div className="bg-white shadow rounded-lg">
        {loading ? (
          <div className="text-center py-12 text-gray-500">Loading...</div>
        ) : campaigns.length === 0 ? (
          <div className="text-center py-12">
            <div className="mx-auto h-12 w-12 text-gray-400">
              <svg fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
            </div>
            <h3 className="mt-2 text-sm font-medium text-gray-900">No campaigns</h3>
            <p className="mt-1 text-sm text-gray-500">Get started by creating a new campaign.</p>
            <div className="mt-6">
              <button
                onClick={() => { setShowWizard(true); setEditCampaign(null); }}
                className="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
              >
                <PlusIcon className="w-4 h-4 mr-2" />
                Create Campaign
              </button>
            </div>
          </div>
        ) : (
          <div className="overflow-hidden">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Campaign
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Status
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Scoring Method
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Created
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {campaigns.map((campaign) => (
                  <tr key={campaign.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div>
                        <div className="text-sm font-medium text-gray-900">
                          <Link 
                            href={`/campaigns/${campaign.id}`}
                            className="text-indigo-600 hover:text-indigo-900 cursor-pointer"
                          >
                            {campaign.name}
                          </Link>
                        </div>
                        <div className="text-sm text-gray-500">{campaign.description}</div>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                        campaign.status === 'active' ? 'bg-green-100 text-green-800' :
                        campaign.status === 'draft' ? 'bg-gray-100 text-gray-800' :
                        campaign.status === 'paused' ? 'bg-yellow-100 text-yellow-800' :
                        'bg-red-100 text-red-800'
                      }`}>
                        {campaign.status}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {campaign.scoring_method?.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {new Date(campaign.created_at).toLocaleDateString()}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                      <button className="text-indigo-600 hover:text-indigo-900 mr-3" onClick={() => handleEdit(campaign)}>
                        Edit
                      </button>
                      <button className="text-red-600 hover:text-red-900" onClick={() => handleDelete(campaign.id)}>
                        Delete
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Campaign Wizard Modal */}
      {showWizard && (
        <CampaignWizard
          onClose={handleWizardClose}
          onComplete={handleCreateCampaign}
          initialData={editCampaign}
        />
      )}
    </Layout>
  );
}

export default withAuth(CampaignPage, {
  redirectTo: '/login',
  requireEmailVerification: false
}); 