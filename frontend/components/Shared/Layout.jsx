import { useAuth } from '../../context/AuthContext';
import Navbar from './Navbar';
import Head from 'next/head';
import ErrorBoundary from './ErrorBoundary';
import ToastContainer from './ToastContainer';

export default function Layout({ children, title = 'Caliber', description = 'Caliber Scoring System' }) {
  const { user, loading } = useAuth();

  return (
    <>
      <Head>
        <title>{title}</title>
        <meta name="description" content={description} />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <link rel="icon" href="/favicon.ico" />
      </Head>
      
      <div className="min-h-screen bg-gray-50">
        {!loading && user && <Navbar />}
        
        <main className={!loading && user ? 'max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8' : ''}>
          <ErrorBoundary>
            {children}
          </ErrorBoundary>
        </main>
      </div>
      
      <ToastContainer />
    </>
  );
} 