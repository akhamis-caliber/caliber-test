import { Inter } from 'next/font/google'
import { QueryClient, QueryClientProvider } from 'react-query'
import { AuthProvider } from '../context/AuthContext'
import Head from 'next/head'
import '../styles/globals.css'

const inter = Inter({ subsets: ['latin'] })

// Create a client
const queryClient = new QueryClient()

function MyApp({ Component, pageProps }) {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <Head>
          <meta name="viewport" content="width=device-width, initial-scale=1" />
        </Head>
        <div className={inter.className}>
          <Component {...pageProps} />
        </div>
      </AuthProvider>
    </QueryClientProvider>
  )
}

export default MyApp 