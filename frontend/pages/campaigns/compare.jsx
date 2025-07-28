import { withAuth } from '../../utils/authGuard';
import Layout from '../../components/Shared/Layout';
import PageHeader from '../../components/Shared/PageHeader';
import CampaignComparison from '../../components/CampaignComparison/CampaignComparison';

function CampaignComparePage() {
  return (
    <Layout title="Campaign Comparison - Caliber" description="Compare campaign performance">
      <PageHeader 
        title="Campaign Comparison"
        description="Compare multiple campaigns side by side to analyze performance differences"
        breadcrumbs={[
          { label: 'Campaigns', href: '/campaigns' },
          { label: 'Comparison' }
        ]}
      />
      
      <CampaignComparison />
    </Layout>
  );
}

export default withAuth(CampaignComparePage, {
  redirectTo: '/login',
  requireEmailVerification: false
}); 