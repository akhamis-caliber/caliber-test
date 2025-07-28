import { Html, Head, Main, NextScript } from 'next/document'

export default function Document() {
  return (
    <Html lang="en">
      <Head>
        <meta charSet="utf-8" />
        <meta name="description" content="Caliber Scoring System - AI-powered campaign management and scoring platform" />
        <meta name="keywords" content="scoring, AI, campaign management, analytics" />
        <meta name="author" content="Caliber Team" />
        
        {/* Favicon */}
        <link rel="icon" href="/favicon.ico" />
        <link rel="apple-touch-icon" sizes="180x180" href="/apple-touch-icon.png" />
        <link rel="icon" type="image/png" sizes="32x32" href="/favicon-32x32.png" />
        <link rel="icon" type="image/png" sizes="16x16" href="/favicon-16x16.png" />
        
        {/* Preconnect to external domains */}
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        
        {/* Open Graph */}
        <meta property="og:title" content="Caliber Scoring System" />
        <meta property="og:description" content="AI-powered campaign management and scoring platform" />
        <meta property="og:type" content="website" />
        <meta property="og:url" content="https://caliber-app.com" />
        <meta property="og:image" content="/og-image.png" />
        
        {/* Twitter Card */}
        <meta name="twitter:card" content="summary_large_image" />
        <meta name="twitter:title" content="Caliber Scoring System" />
        <meta name="twitter:description" content="AI-powered campaign management and scoring platform" />
        <meta name="twitter:image" content="/og-image.png" />
      </Head>
      <body className="antialiased">
        <Main />
        <NextScript />
      </body>
    </Html>
  )
} 