import { withAuth } from '../utils/authGuard';
import Layout from '../components/Shared/Layout';
import PageHeader from '../components/Shared/PageHeader';

function SettingsPage() {
  return (
    <Layout title="Settings - Caliber" description="Manage your account settings">
      <PageHeader 
        title="Settings"
        description="Manage your account and application settings"
        breadcrumbs={[{ label: 'Settings' }]}
      />
      
      <div className="bg-white rounded-lg shadow p-6">
        <div className="text-center py-12">
          <h3 className="text-lg font-medium text-gray-900 mb-2">Account Settings</h3>
          <p className="text-gray-500">This page is under development. Settings management features will be available soon.</p>
        </div>
      </div>
    </Layout>
  );
}

export default withAuth(SettingsPage, {
  redirectTo: '/login',
  requireEmailVerification: false
}); 