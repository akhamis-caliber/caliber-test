import React, { useState, useEffect, useCallback } from 'react';
import zxcvbn from 'zxcvbn';
import './CaliberDemo.css';

// Simple logger for frontend
const logger = {
  info: (message) => console.log(`[INFO] ${message}`),
  warn: (message) => console.warn(`[WARN] ${message}`),
  error: (message) => console.error(`[ERROR] ${message}`),
  debug: (message) => console.debug(`[DEBUG] ${message}`)
};

const CaliberDemo = () => {
  const [currentPage, setCurrentPage] = useState('login'); // login, register, dashboard, wizard, results
  const [isDarkMode, setIsDarkMode] = useState(false);
  const [user, setUser] = useState(null);
  const [currentStep, setCurrentStep] = useState(1);
  const [uploadedFile, setUploadedFile] = useState(null);
  const [scoringProgress, setScoringProgress] = useState(0);
  
  // WebSocket progress tracking
  const [websocket, setWebsocket] = useState(null);
  const [realTimeProgress, setRealTimeProgress] = useState(null);
  const [progressDetails, setProgressDetails] = useState({
    currentStep: '',
    currentOperation: '',
    processedRows: 0,
    totalRows: 0,
    estimatedCompletion: null,
    errors: [],
    warnings: []
  });
  
  // Registration form state
  const [registrationForm, setRegistrationForm] = useState({
    fullName: '',
    email: '',
    password: '',
    confirmPassword: '',
    acceptTerms: false
  });
  const [registrationErrors, setRegistrationErrors] = useState({});
  const [passwordStrength, setPasswordStrength] = useState(null);
  const [error, setError] = useState(null);
  const [isLoading, setIsLoading] = useState(false);

  // Campaign Wizard Data
  const [campaignData, setCampaignData] = useState({
    name: '',
    campaign_type: '',
    goal: '',
    channel: '',
    ctr_sensitivity: false,
    analysis_level: '',
    save_as_template: false
  });

  // State for campaigns and results data
  const [campaigns, setCampaigns] = useState([]);
  const [campaignResults, setCampaignResults] = useState([]);
  const [selectedCampaignId, setSelectedCampaignId] = useState(null);
  const [loadingCampaigns, setLoadingCampaigns] = useState(false);
  const [loadingResults, setLoadingResults] = useState(false);

  // Dark Mode Effect
  useEffect(() => {
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme === 'dark') {
      setIsDarkMode(true);
      document.documentElement.setAttribute('data-theme', 'dark');
    }
  }, []);

  // WebSocket progress tracking functions
  const connectWebSocket = (campaignId) => {
    try {
      const wsUrl = `${process.env.REACT_APP_BACKEND_URL || 'http://localhost:8000'}`.replace('http', 'ws');
      const ws = new WebSocket(`${wsUrl}/ws/progress/${campaignId}`);
      
      ws.onopen = () => {
        logger.info(`WebSocket connected for campaign ${campaignId}`);
        setWebsocket(ws);
      };
      
      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (data.type === 'progress_update') {
            handleProgressUpdate(data.data);
          }
        } catch (error) {
          logger.error('Failed to parse WebSocket message:', error);
        }
      };
      
      ws.onerror = (error) => {
        logger.error('WebSocket error:', error);
        setRealTimeProgress(null);
      };
      
      ws.onclose = () => {
        logger.info('WebSocket connection closed');
        setWebsocket(null);
        setRealTimeProgress(null);
      };
      
      return ws;
    } catch (error) {
      logger.error('Failed to create WebSocket connection:', error);
      return null;
    }
  };
  
  const disconnectWebSocket = () => {
    if (websocket) {
      websocket.close();
      setWebsocket(null);
      setRealTimeProgress(null);
    }
  };
  
  const handleProgressUpdate = (progressData) => {
    setRealTimeProgress(progressData);
    setProgressDetails({
      currentStep: progressData.current_step || '',
      currentOperation: progressData.current_operation || '',
      processedRows: progressData.processed_rows || 0,
      totalRows: progressData.total_rows || 0,
      estimatedCompletion: progressData.estimated_completion || null,
      errors: progressData.errors || [],
      warnings: progressData.warnings || []
    });
    
    // Update scoring progress
    if (progressData.progress_percentage !== undefined) {
      setScoringProgress(progressData.progress_percentage);
    }
    
    // Handle completion
    if (progressData.status === 'completed') {
      logger.info('Scoring completed successfully via WebSocket');
      setTimeout(() => {
        setCurrentPage('results');
      }, 1000);
    } else if (progressData.status === 'failed') {
      logger.error('Scoring failed via WebSocket:', progressData.errors);
      setError(`Scoring failed: ${progressData.errors.join(', ')}`);
      setCurrentPage('dashboard');
    } else if (progressData.status === 'timeout') {
      logger.error('Scoring timed out via WebSocket');
      setError('Scoring timed out - results not available after 60 seconds. Please check your file size and try again.');
      setCurrentPage('dashboard');
    }
  };
  
  // Cleanup WebSocket on component unmount
  useEffect(() => {
    return () => {
      disconnectWebSocket();
    };
  }, []);

  const toggleDarkMode = () => {
    const newMode = !isDarkMode;
    setIsDarkMode(newMode);
    if (newMode) {
      document.documentElement.setAttribute('data-theme', 'dark');
      localStorage.setItem('theme', 'dark');
    } else {
      document.documentElement.setAttribute('data-theme', 'light');
      localStorage.setItem('theme', 'light');
    }
  };

  // Authentication Functions
  const handleLogin = async (email, password) => {
    try {
      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL || 'http://localhost:8000'}/api/auth/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email, password }),
      });

      if (response.ok) {
        const data = await response.json();
        localStorage.setItem('token', data.token);
        setUser({ name: data.user.name, email: data.user.email });
        setCurrentPage('dashboard');
      } else {
        const errorData = await response.json();
        // Handle different error formats properly
        let errorMessage = 'Login failed';
        if (errorData.detail) {
          if (Array.isArray(errorData.detail)) {
            // Handle validation errors array
            errorMessage = errorData.detail.map(err => `${err.loc?.join('.') || 'Field'}: ${err.msg}`).join('\n');
          } else {
            errorMessage = errorData.detail;
          }
        } else if (errorData.message) {
          errorMessage = errorData.message;
        }
        setError(errorMessage);
      }
    } catch (error) {
      console.error('Login error:', error);
      setError('Login failed. Please try again.');
    }
  };

  // Validation helper functions
  const validateFullName = (name) => {
    const trimmedName = name.trim();
    if (!trimmedName) return 'Full name is required';
    if (trimmedName.length < 2) return 'Full name must be at least 2 characters';
    if (trimmedName.length > 60) return 'Full name must be no more than 60 characters';
    
    // Allow letters, spaces, punctuation (but not numbers or special symbols)
    const nameRegex = /^[a-zA-Z\u00C0-\u00FF\u0100-\u017F\u0180-\u024F\u1E00-\u1EFF\s'\-.,]+$/;
    if (!nameRegex.test(trimmedName)) {
      return 'Full name can only contain letters, spaces, and common punctuation';
    }
    return null;
  };

  const validateEmail = (email) => {
    if (!email.trim()) return 'Email is required';
    
    // RFC 5322 compliant email regex (simplified but robust)
    const emailRegex = /^[a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+@[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$/;
    
    if (!emailRegex.test(email)) return 'Please enter a valid email address';
    if (email.length > 254) return 'Email address is too long';
    return null;
  };

  const validatePassword = (password) => {
    if (!password) return 'Password is required';
    if (password.length < 12) return 'Password must be at least 12 characters';
    
    // Check for 3 out of 4 character types
    const hasUppercase = /[A-Z]/.test(password);
    const hasLowercase = /[a-z]/.test(password);
    const hasDigit = /[0-9]/.test(password);
    const hasSymbol = /[^A-Za-z0-9]/.test(password);
    
    const characterTypesCount = [hasUppercase, hasLowercase, hasDigit, hasSymbol].filter(Boolean).length;
    
    if (characterTypesCount < 3) {
      return 'Password must include at least 3 of: uppercase letters, lowercase letters, numbers, symbols';
    }
    
    // Check password strength using zxcvbn
    const strength = zxcvbn(password);
    if (strength.score < 3) {
      return `Password is too weak: ${strength.feedback.warning || 'Please choose a stronger password'}`;
    }
    
    return null;
  };

  const handleRegister = async () => {
    // Validate all fields with new schema
    const errors = {};
    
    // Validate full name (2-60 chars, letters + punctuation)
    const fullNameError = validateFullName(registrationForm.fullName);
    if (fullNameError) errors.fullName = fullNameError;
    
    // Validate email (RFC-compliant)
    const emailError = validateEmail(registrationForm.email);
    if (emailError) errors.email = emailError;
    
    // Validate password (≥12 chars, 3 of 4 types, zxcvbn score ≥3)
    const passwordError = validatePassword(registrationForm.password);
    if (passwordError) errors.password = passwordError;
    
    // Validate confirm password (must match)
    if (!registrationForm.confirmPassword) {
      errors.confirmPassword = 'Please confirm your password';
    } else if (registrationForm.password !== registrationForm.confirmPassword) {
      errors.confirmPassword = 'Passwords do not match';
    }
    
    // Validate accept terms (required)
    if (!registrationForm.acceptTerms) {
      errors.acceptTerms = 'You must accept the Terms of Service and Privacy Policy';
    }
    
    if (Object.keys(errors).length > 0) {
      setRegistrationErrors(errors);
      return;
    }
    
    // Clear errors and make API call
    setRegistrationErrors({});
    
    try {
      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL || 'http://localhost:8000'}/api/auth/register`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          full_name: registrationForm.fullName,
          email: registrationForm.email,
          password: registrationForm.password,
        }),
      });

      if (response.ok) {
        const data = await response.json();
        localStorage.setItem('token', data.token);
        setUser({ name: data.user.name, email: data.user.email });
        setCurrentPage('dashboard');
        
        // Reset form
        setRegistrationForm({
          fullName: '',
          email: '',
          password: '',
          confirmPassword: '',
          acceptTerms: false
        });
      } else {
        const errorData = await response.json();
        // Handle different error formats properly
        let errorMessage = 'Registration failed';
        if (errorData.detail) {
          if (Array.isArray(errorData.detail)) {
            // Handle validation errors array
            errorMessage = errorData.detail.map(err => `${err.loc?.join('.') || 'Field'}: ${err.msg}`).join('\n');
          } else {
            errorMessage = errorData.detail;
          }
        } else if (errorData.message) {
          errorMessage = errorData.message;
        }
        setError(errorMessage);
      }
    } catch (error) {
      console.error('Registration error:', error);
      setError('Registration failed. Please try again.');
    }
  };

  // Handle password change with strength indicator
  const handlePasswordChange = (password) => {
    setRegistrationForm(prev => ({ ...prev, password }));
    
    if (password.length > 0) {
      const strength = zxcvbn(password);
      setPasswordStrength(strength);
    } else {
      setPasswordStrength(null);
    }
  };

  const handleGoogleAuth = () => {
    // TODO: Implement actual Google OAuth integration
    setError('Google OAuth integration not yet implemented. Please use email/password login.');
  };

  const handleLogout = () => {
    setUser(null);
    setCurrentPage('login');
  };

  // Campaign Wizard Functions
  const updateCampaignData = (updates) => {
    setCampaignData(prev => ({ ...prev, ...updates }));
  };

  const nextStep = () => {
    if (currentStep < 7 && isStepValid()) {
      setCurrentStep(currentStep + 1);
    }
  };

  const prevStep = () => {
    if (currentStep > 1) setCurrentStep(currentStep - 1);
  };

  const isStepValid = () => {
    switch (currentStep) {
      case 1: return campaignData.campaign_type !== '';
      case 2: return campaignData.goal !== '';
      case 3: return campaignData.channel !== '';
      case 4: return true;
      case 5: return campaignData.analysis_level !== '';
      case 6: return campaignData.name !== '';
      case 7: return uploadedFile !== null;
      default: return false;
    }
  };

  const fetchCampaignResults = useCallback(async (campaignId) => {
    if (!campaignId) return;
    
    setLoadingResults(true);
    try {
      const token = localStorage.getItem('token');
      // First get the campaign to find its reports
      const campaignResponse = await fetch(`${process.env.REACT_APP_BACKEND_URL || 'http://localhost:8000'}/api/campaigns/${campaignId}`, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (campaignResponse.ok) {
        // Get reports for this campaign
        const reportsResponse = await fetch(`${process.env.REACT_APP_BACKEND_URL || 'http://localhost:8000'}/api/reports`, {
          method: 'GET',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
        });

        if (reportsResponse.ok) {
          const reports = await reportsResponse.json();
          const campaignReports = reports.filter(report => report.campaign_id === campaignId);
          
          if (campaignReports.length > 0) {
            // Get scores for the first report
            const reportId = campaignReports[0].id;
            const scoresResponse = await fetch(`${process.env.REACT_APP_BACKEND_URL || 'http://localhost:8000'}/api/reports/${reportId}/scores`, {
              method: 'GET',
              headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json',
              },
            });

            if (scoresResponse.ok) {
              const scoresData = await scoresResponse.json();
              // Handle both formats: direct array or {data: array, pagination: object}
              const scores = scoresData.data || scoresData;
              if (Array.isArray(scores)) {
                setCampaignResults(scores);
                setSelectedCampaignId(campaignId);
              } else {
                console.error('Invalid scores format:', scoresData);
                setCampaignResults([]);
              }
            } else {
              console.error('Failed to fetch campaign scores');
              setCampaignResults([]);
            }
          } else {
            console.log('No reports found for this campaign');
            setCampaignResults([]);
            setSelectedCampaignId(null);
          }
        }
      } else {
        console.error('Failed to fetch campaign details');
        setCampaignResults([]);
        setSelectedCampaignId(null);
      }
    } catch (error) {
      console.error('Error fetching campaign results:', error);
      setCampaignResults([]);
      setSelectedCampaignId(null);
    } finally {
      setLoadingResults(false);
    }
  }, []);

  // Navigation and Page Functions
  const handleCampaignClick = useCallback(async (campaignId) => {
    await fetchCampaignResults(campaignId);
    setCurrentPage('results');
  }, [fetchCampaignResults]);

  const handleInsightsClick = () => {
    setCurrentPage('insights');
  };

  const handleAccountClick = () => {
    setCurrentPage('account');
  };

  const handleFileUpload = (event) => {
    const file = event.target.files[0];
    if (file && (file.name.endsWith('.csv') || file.name.endsWith('.xlsx') || file.name.endsWith('.xls'))) {
      setUploadedFile(file);
    } else {
      setError('Please upload a CSV or Excel file');
    }
  };

  const handleFileDrop = (event) => {
    event.preventDefault();
    const file = event.dataTransfer.files[0];
    
    if (file && (file.name.endsWith('.csv') || file.name.endsWith('.xlsx') || file.name.endsWith('.xls'))) {
      setUploadedFile(file);
    } else {
      setError('Please upload a CSV or Excel file');
    }
  };

  const handleDragOver = (event) => {
    event.preventDefault();
  };

  // Export and Download Functions
  const exportToCSV = () => {
    const headers = ['Domain', 'Publisher', 'CPM', 'CTR', 'Conversion Rate', 'Impressions', 'Total Spend', 'Conversions', 'Score', 'Status'];
    const csvContent = [
      headers.join(','),
      ...campaignResults.map(row => [
        row.domain,
        row.publisher,
        row.cpm,
        row.ctr,
        row.convRate,
        row.impressions || 1250,
        row.totalSpend || (row.cpm * (row.impressions || 1250) / 1000).toFixed(2),
        row.conversions || Math.round((row.impressions || 1250) * (row.convRate || 1.2) / 100),
        row.score,
        row.status
      ].join(','))
    ].join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `campaign_results_${campaignData.name?.replace(/[^a-z0-9]/gi, '_').toLowerCase() || 'export'}.csv`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(url);
  };

  const downloadWhitelist = () => {
    // Top 25% performers (sorted by score descending)
    const sortedResults = [...campaignResults].sort((a, b) => b.score - a.score);
    const topPerformers = sortedResults.slice(0, Math.ceil(sortedResults.length * 0.25));
    
    const headers = ['Domain', 'Publisher', 'CPM', 'CTR', 'Conversion Rate', 'Score', 'Status', 'Recommendation'];
    const csvContent = [
      headers.join(','),
      ...topPerformers.map(row => [
        row.domain,
        row.publisher,
        row.cpm,
        row.ctr,
        row.convRate,
        row.score,
        row.status,
        'RECOMMENDED - Top Performer'
      ].join(','))
    ].join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `whitelist_top_performers_${campaignData.name?.replace(/[^a-z0-9]/gi, '_').toLowerCase() || 'export'}.csv`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(url);
  };

  const downloadBlacklist = () => {
    // Bottom 25% performers (sorted by score ascending)
    const sortedResults = [...campaignResults].sort((a, b) => a.score - b.score);
    const bottomPerformers = sortedResults.slice(0, Math.ceil(sortedResults.length * 0.25));
    
    const headers = ['Domain', 'Publisher', 'CPM', 'CTR', 'Conversion Rate', 'Score', 'Status', 'Recommendation'];
    const csvContent = [
      headers.join(','),
      ...bottomPerformers.map(row => [
        row.domain,
        row.publisher,
        row.cpm,
        row.ctr,
        row.convRate,
        row.score,
        row.status,
        'BLACKLISTED - Poor Performer'
      ].join(','))
    ].join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `blacklist_poor_performers_${campaignData.name?.replace(/[^a-z0-9]/gi, '_').toLowerCase() || 'export'}.csv`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(url);
  };

  const exportToPDF = () => {
    // Create a simple HTML report for PDF generation
    const avgScore = campaignResults.length > 0 ? (campaignResults.reduce((sum, r) => sum + r.score, 0) / campaignResults.length).toFixed(1) : '0';
    const goodCount = campaignResults.filter(r => r.status === 'Good').length;
    const poorCount = campaignResults.filter(r => r.status === 'Poor').length;
    
    const reportHTML = `
      <html>
        <head>
          <title>Campaign Results Report - ${campaignData.name || 'Campaign'}</title>
          <style>
            body { font-family: Arial, sans-serif; margin: 40px; color: #002f3b; }
            .header { text-align: center; margin-bottom: 30px; border-bottom: 3px solid #009ba7; padding-bottom: 20px; }
            .header h1 { color: #002f3b; font-size: 28px; margin: 0; }
            .header p { color: #a6a6a6; margin: 5px 0; }
            .summary { display: flex; justify-content: space-around; margin: 30px 0; }
            .summary-card { text-align: center; padding: 20px; background: #f8fafb; border-radius: 8px; border-left: 4px solid #009ba7; }
            .summary-card h3 { color: #009ba7; margin: 0 0 10px 0; font-size: 24px; }
            .summary-card p { color: #a6a6a6; margin: 0; font-size: 12px; text-transform: uppercase; }
            .insights { margin: 30px 0; }
            .insights h2 { color: #002f3b; border-bottom: 2px solid #a1e1e6; padding-bottom: 10px; }
            .insight { margin: 15px 0; padding: 15px; background: #a1e1e6; border-radius: 6px; }
            .table { width: 100%; border-collapse: collapse; margin: 30px 0; }
            .table th { background: #002f3b; color: white; padding: 12px; text-align: left; }
            .table td { padding: 12px; border-bottom: 1px solid #d9d9d9; }
            .status-good { background: #009ba7; color: white; padding: 4px 8px; border-radius: 4px; font-size: 11px; }
            .status-moderate { background: #f1c232; color: #002f3b; padding: 4px 8px; border-radius: 4px; font-size: 11px; }
            .status-poor { background: #a6a6a6; color: white; padding: 4px 8px; border-radius: 4px; font-size: 11px; }
            .footer { text-align: center; margin-top: 40px; padding-top: 20px; border-top: 1px solid #d9d9d9; color: #a6a6a6; font-size: 12px; }
          </style>
        </head>
        <body>
          <div class="header">
            <h1>Campaign Results Report</h1>
            <p><strong>${campaignData.name || 'Campaign Name'}</strong></p>
            <p>Generated on ${new Date().toLocaleDateString()}</p>
          </div>
          
          <div class="summary">
            <div class="summary-card">
              <h3>${campaignResults.length}</h3>
              <p>Total Domains</p>
            </div>
            <div class="summary-card">
              <h3>${avgScore}</h3>
              <p>Average Score</p>
            </div>
            <div class="summary-card">
              <h3>${goodCount}</h3>
              <p>Good Performers</p>
            </div>
          </div>
          
          <div class="insights">
            <h2>AI Insights & Recommendations</h2>
            <div class="insight">🎯 Your top-performing domain is demo-site.net with 2.5x higher conversions</div>
            <div class="insight">📊 ${campaignResults.length > 0 ? Math.round((goodCount/campaignResults.length)*100) : 0}% of domains achieve 'Good' performance scores</div>
            <div class="insight">💡 Consider blacklisting bottom ${poorCount} domains to improve ROI</div>
            <div class="insight">⚡ Focus budget on top ${goodCount} performing domains for better results</div>
          </div>
          
          <table class="table">
            <thead>
              <tr>
                <th>Domain</th>
                <th>Publisher</th>
                <th>CPM</th>
                <th>CTR</th>
                <th>Conv Rate</th>
                <th>Score</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              ${campaignResults.map(row => `
                <tr>
                  <td>${row.domain}</td>
                  <td>${row.publisher}</td>
                  <td>$${row.cpm}</td>
                  <td>${row.ctr}%</td>
                  <td>${row.convRate}%</td>
                  <td><strong>${row.score}</strong></td>
                  <td><span class="status-${row.status.toLowerCase()}">${row.status}</span></td>
                </tr>
              `).join('')}
            </tbody>
          </table>
          
          <div class="footer">
            <p>Generated by Caliber - AI-Powered Inventory Scoring</p>
            <p>Campaign Type: ${campaignData.campaign_type} | Goal: ${campaignData.goal} | Channel: ${campaignData.channel}</p>
          </div>
        </body>
      </html>
    `;

    // Create a new window for PDF generation
    const printWindow = window.open('', '_blank');
    printWindow.document.write(reportHTML);
    printWindow.document.close();
    
    // Trigger print dialog after content loads
    setTimeout(() => {
      printWindow.print();
    }, 250);
  };

  const handleCampaignSubmit = async () => {
    // Create FormData for backend submission
    const formData = new FormData();
    formData.append('name', campaignData.name);
    formData.append('campaign_type', campaignData.campaign_type);
    formData.append('goal', campaignData.goal);
    formData.append('channel', campaignData.channel);
    formData.append('ctr_sensitivity', campaignData.ctr_sensitivity.toString());
    formData.append('analysis_level', campaignData.analysis_level);
    if (uploadedFile) {
      formData.append('file', uploadedFile);
    }

    try {
      setIsLoading(true);
      const token = localStorage.getItem('token');
      
      // Show scoring progress page
      setCurrentPage('scoring');
      setScoringProgress(10);
      
      logger.info('🚀 Starting campaign creation...');
      logger.info(`📤 Campaign data: ${JSON.stringify(campaignData)}`);
      logger.info(`📁 File: ${uploadedFile ? uploadedFile.name : 'None'}`);
      
      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL || 'http://localhost:8000'}/api/campaigns`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        },
        body: formData
      });

      logger.info(`📥 Response received: ${response.status} ${response.statusText}`);
      logger.info(`📋 Response headers: ${JSON.stringify(Object.fromEntries(response.headers.entries()))}`);

      if (response.ok) {
        logger.info('✅ HTTP response is OK (200-299)');
        
        // Try to parse response
        let campaignResponse;
        try {
          const responseText = await response.text();
          logger.info(`📄 Raw response text: ${repr(responseText)}`);
          
          if (responseText.trim()) {
            campaignResponse = JSON.parse(responseText);
            logger.info(`🔍 Parsed JSON response: ${JSON.stringify(campaignResponse, null, 2)}`);
          } else {
            logger.warn('⚠️ Response is empty (null/empty string)');
            campaignResponse = null;
          }
        } catch (parseError) {
          logger.error(`❌ JSON parsing failed: ${parseError}`);
          campaignResponse = null;
        }
        
        setScoringProgress(50);
        
        // Check if there's an error in the campaign response
        if (campaignResponse && campaignResponse.error) {
          logger.error(`🚨 Campaign created but scoring failed: ${campaignResponse.error}`);
          setError(`Campaign created but scoring failed: ${campaignResponse.error}`);
          setCurrentPage('dashboard');
          return;
        }
        
        if (!campaignResponse) {
          logger.warn('⚠️ No campaign response data, but HTTP was OK');
          // Continue with fallback behavior
        } else {
          logger.info('✅ Campaign response processed successfully');
        }
        
        // Refresh campaigns list
        await fetchCampaigns();
        setScoringProgress(70);
        
        // Connect to WebSocket for real-time progress updates
        const ws = connectWebSocket(campaignResponse?.id);
        if (ws) {
          logger.info('WebSocket connected for real-time progress updates');
          
          // Wait for WebSocket to connect before proceeding
          ws.onopen = () => {
            logger.info('WebSocket ready for progress updates');
            setScoringProgress(75);
          };
        } else {
          logger.warning('WebSocket connection failed, falling back to polling');
          // Fallback to polling if WebSocket fails
          if (campaignResponse?.id) {
            await fallbackPolling(campaignResponse.id);
          } else {
            logger.error('❌ No campaign ID available for polling');
            setError('Campaign created but no ID received for progress tracking');
            setCurrentPage('dashboard');
          }
        }
        
      } else {
        logger.error(`❌ HTTP response not OK: ${response.status} ${response.statusText}`);
        
        let errorData;
        try {
          const errorText = await response.text();
          logger.info(`📄 Error response text: ${repr(errorText)}`);
          
          if (errorText.trim()) {
            errorData = JSON.parse(errorText);
            logger.info(`🔍 Parsed error JSON: ${JSON.stringify(errorData, null, 2)}`);
          } else {
            logger.warn('⚠️ Error response is empty');
            errorData = {};
          }
        } catch (parseError) {
          logger.error(`❌ Error response JSON parsing failed: ${parseError}`);
          errorData = {};
        }
        
        // Handle different error formats properly
        let errorMessage = 'Campaign creation failed';
        if (errorData.detail) {
          if (Array.isArray(errorData.detail)) {
            // Handle validation errors array
            errorMessage = errorData.detail.map(err => `${err.loc?.join('.') || 'Field'}: ${err.msg}`).join('\n');
          } else {
            errorMessage = errorData.detail;
          }
        } else if (errorData.message) {
          errorMessage = errorData.message;
        }
        
        logger.error(`🚨 Setting error: ${errorMessage}`);
        setError(errorMessage);
        setCurrentPage('dashboard');
      }
    } catch (error) {
      logger.error(`💥 Campaign creation exception: ${error}`);
      logger.error(`💥 Error stack: ${error.stack}`);
      setError(`Campaign creation failed: ${error.message}`);
      setCurrentPage('dashboard');
    } finally {
      setIsLoading(false);
    }
  };

  // Helper function to safely represent strings
  const repr = (str) => {
    if (str === null) return 'null';
    if (str === undefined) return 'undefined';
    if (str === '') return '""';
    return `"${str}"`;
  };

  // Fallback polling function if WebSocket fails
  const fallbackPolling = async (campaignId) => {
    logger.info('Using fallback polling for progress updates');
    
    let attempts = 0;
    const maxAttempts = 60; // Reduced to 1 minute since backend has 60s timeout
    
    const pollForResults = async () => {
      try {
        // Get reports for this campaign
        const token = localStorage.getItem('token');
        const reportsResponse = await fetch(`${process.env.REACT_APP_BACKEND_URL || 'http://localhost:8000'}/api/reports`, {
          headers: {
            'Authorization': `Bearer ${token}`,
          },
        });
        
        if (reportsResponse.ok) {
          const reports = await reportsResponse.json();
          const campaignReports = reports.filter(report => report.campaign_id === campaignId);
          
          if (campaignReports.length > 0) {
            const report = campaignReports[0];
            console.log(`Polling report ${report.id}: status = ${report.status}`);
            
            // Check if report is completed
            if (report.status === 'COMPLETED') {
              setScoringProgress(90);
              
              // Get the scores
              const scoresResponse = await fetch(`${process.env.REACT_APP_BACKEND_URL || 'http://localhost:8000'}/api/reports/${report.id}/scores`, {
                headers: {
                  'Authorization': `Bearer ${token}`,
                },
              });
              
              if (scoresResponse.ok) {
                const scoresData = await scoresResponse.json();
                // Handle both formats: direct array or {data: array, pagination: object}
                const scores = scoresData.data || scoresData;
                
                if (Array.isArray(scores) && scores.length > 0) {
                  setCampaignResults(scores);
                  setSelectedCampaignId(campaignId);
                  setScoringProgress(100);
                  
                  // Show success message
                  setTimeout(() => {
                    setCurrentPage('results');
                  }, 1000);
                  return;
                } else {
                  // No scores found
                  throw new Error('Scoring completed but no results were generated. Please check your file and try again.');
                }
              }
            } else if (report.status === 'FAILED') {
              const errorMsg = report.error_message || 'Unknown error';
              throw new Error(`Scoring failed: ${errorMsg}`);
            } else if (report.status === 'PENDING' || report.status === 'PROCESSING') {
              // Report is still being processed, continue polling
              console.log(`Report status: ${report.status}, continuing to poll...`);
            } else {
              // Unknown status
              console.warn(`Unknown report status: ${report.status}`);
            }
          }
        }
        
        attempts++;
        if (attempts < maxAttempts) {
          // More gradual progress for longer processing times
          const progressIncrement = 20 / maxAttempts;
          setScoringProgress(70 + (attempts * progressIncrement));
          
          // Adaptive polling: faster at first, slower later
          const pollInterval = attempts < 20 ? 1000 : 2000;
          setTimeout(pollForResults, pollInterval);
        } else {
          throw new Error(`Scoring timeout - results not available after 1 minute. The backend has a 60-second timeout limit. Please check your file size and try again.`);
        }
      } catch (error) {
        console.error('Error polling for results:', error);
        setError(`Scoring failed: ${error.message}`);
        setCurrentPage('dashboard');
      }
    };
    
    // Start polling for results after a shorter initial delay
    setTimeout(pollForResults, 1000);
  };

  // API Functions
  const fetchCampaigns = useCallback(async () => {
    if (!user) return;
    
    setLoadingCampaigns(true);
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL || 'http://localhost:8000'}/api/campaigns`, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (response.ok) {
        const data = await response.json();
        setCampaigns(data);
      } else {
        console.error('Failed to fetch campaigns');
        setCampaigns([]); // Set empty array on error
      }
    } catch (error) {
      console.error('Error fetching campaigns:', error);
      setCampaigns([]); // Set empty array on error
    } finally {
      setLoadingCampaigns(false);
    }
  }, [user]);

  const handleDeleteCampaign = useCallback(async (campaignId, campaignName) => {
    if (!user) return;
    
    // Show confirmation dialog
    if (!window.confirm(`Are you sure you want to delete the campaign "${campaignName}"? This action cannot be undone and will also delete all related reports and scores.`)) {
      return;
    }
    
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL || 'http://localhost:8000'}/api/campaigns/${campaignId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        console.log('Campaign deleted successfully:', data);
        
        // Remove the deleted campaign from the local state
        setCampaigns(prevCampaigns => prevCampaigns.filter(campaign => campaign.id !== campaignId));
        
        // If the deleted campaign was selected, clear the selection
        if (selectedCampaignId === campaignId) {
          setSelectedCampaignId(null);
          setCampaignResults([]);
        }
        
        // Show success message
        alert(`Campaign "${campaignName}" deleted successfully!`);
      } else {
        const errorData = await response.json();
        console.error('Failed to delete campaign:', response.status, errorData);
        alert(`Failed to delete campaign: ${errorData.detail || 'Unknown error'}`);
      }
    } catch (error) {
      console.error('Error deleting campaign:', error);
      alert('Error deleting campaign. Please try again.');
    }
  }, [user, selectedCampaignId]);

  // Load campaigns when user logs in
  useEffect(() => {
    if (user) {
      fetchCampaigns();
    }
  }, [user, fetchCampaigns]);

  // Add error handling state
  // const [error, setError] = useState(null);
  // const [isLoading, setIsLoading] = useState(false);

  // Enhanced error handling for API calls
  const handleApiError = (error, message = 'An error occurred') => {
    console.error('API Error:', error);
    setError(message);
    setTimeout(() => setError(null), 5000); // Clear error after 5 seconds
  };

  // Enhanced message display function
  const showMessage = (message, type = 'error') => {
    setError({ message, type });
    setTimeout(() => setError(null), 5000); // Clear message after 5 seconds
  };

  // AI Question Handler
  const handleAIQuestion = useCallback(async (question) => {
    if (!question.trim()) return;
    
    try {
      setIsLoading(true);
      const token = localStorage.getItem('token');
      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL || 'http://localhost:8000'}/api/ai/insights`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          campaign_id: selectedCampaignId || 'general',
          query: question
        }),
      });

      if (response.ok) {
        const data = await response.json();
        // Display AI response (you can enhance this with a chat interface)
        showMessage(`AI Response: ${data.insights.join(', ')}`, 'success');
      } else {
        handleApiError(new Error('Failed to get AI insights'), 'Failed to get AI response');
      }
    } catch (error) {
      handleApiError(error, 'Failed to get AI response');
    } finally {
      setIsLoading(false);
    }
  }, [selectedCampaignId]);

  // Login Page
  const renderLogin = () => (
    <div className="auth-container">
      <div className="auth-card">
        <div className="auth-header">
          <div className="caliber-logo">
            <img src="https://customer-assets.emergentagent.com/job_caliber-scoring/artifacts/zxi0qkvb_Caliber%20Icon%20-%20Color%20%281%29.png" alt="Caliber Logo" />
          </div>
          <h1 className="caliber-title">Caliber</h1>
          <p className="caliber-subtitle">AI-Powered Inventory Scoring</p>
        </div>
        
        <div className="auth-form">
          <h2>Sign in to your account</h2>
          <p>Enter your email and password to access your dashboard</p>
          
          <form onSubmit={(e) => { 
            e.preventDefault(); 
            const email = e.target.email.value;
            const password = e.target.password.value;
            handleLogin(email, password);
          }}>
            <div className="form-group">
              <label>Email address</label>
              <input type="email" name="email" placeholder="Enter your email" required />
            </div>
            <div className="form-group">
              <label>Password</label>
              <input type="password" name="password" placeholder="Enter your password" required />
            </div>
            <button type="submit" className="btn-primary">Sign in</button>
          </form>
          
          <div className="auth-divider">
            <span>Or continue with</span>
          </div>
          
          <button onClick={handleGoogleAuth} className="btn-google">
            <span>🔍</span> Google
          </button>
          
          <p className="auth-link">
            Don't have an account? <button onClick={() => setCurrentPage('register')}>Sign up</button>
          </p>
        </div>
      </div>
    </div>
  );

  // Register Page
  const renderRegister = () => (
    <div className="auth-container">
      <div className="auth-card">
        <div className="auth-header">
          <div className="caliber-logo">
            <img src="https://customer-assets.emergentagent.com/job_caliber-scoring/artifacts/zxi0qkvb_Caliber%20Icon%20-%20Color%20%281%29.png" alt="Caliber Logo" />
          </div>
          <h1 className="caliber-title">Caliber</h1>
          <p className="caliber-subtitle">AI-Powered Inventory Scoring</p>
        </div>
        
        <div className="auth-form">
          <h2>Create your account</h2>
          <p>Get started with Caliber's advanced campaign analytics</p>
          
          <form onSubmit={(e) => { 
            e.preventDefault(); 
            handleRegister();
          }}>
            <div className="form-group">
              <label>Full name *</label>
              <input 
                type="text" 
                placeholder="Enter your full name (2-60 characters)" 
                value={registrationForm.fullName}
                onChange={(e) => setRegistrationForm(prev => ({ ...prev, fullName: e.target.value }))}
                className={registrationErrors.fullName ? 'error' : ''}
                maxLength={60}
              />
              {registrationErrors.fullName && (
                <span className="error-message">{registrationErrors.fullName}</span>
              )}
            </div>
            
            <div className="form-group">
              <label>Email address *</label>
              <input 
                type="email" 
                placeholder="Enter your email address" 
                value={registrationForm.email}
                onChange={(e) => setRegistrationForm(prev => ({ ...prev, email: e.target.value }))}
                className={registrationErrors.email ? 'error' : ''}
              />
              {registrationErrors.email && (
                <span className="error-message">{registrationErrors.email}</span>
              )}
            </div>
            
            <div className="form-group">
              <label>Password *</label>
              <input 
                type="password" 
                placeholder="Create a strong password (minimum 12 characters)" 
                value={registrationForm.password}
                onChange={(e) => handlePasswordChange(e.target.value)}
                className={registrationErrors.password ? 'error' : ''}
              />
              {passwordStrength && (
                <div className={`password-strength strength-${passwordStrength.score}`}>
                  <div className="strength-bar">
                    <div className="strength-fill" style={{width: `${(passwordStrength.score + 1) * 20}%`}}></div>
                  </div>
                  <span className="strength-text">
                    {['Very Weak', 'Weak', 'Fair', 'Good', 'Strong'][passwordStrength.score]}
                  </span>
                </div>
              )}
              <div className="password-requirements">
                <small>Password must be at least 12 characters and include 3 of: uppercase, lowercase, numbers, symbols</small>
              </div>
              {registrationErrors.password && (
                <span className="error-message">{registrationErrors.password}</span>
              )}
            </div>
            
            <div className="form-group">
              <label>Confirm Password *</label>
              <input 
                type="password" 
                placeholder="Confirm your password" 
                value={registrationForm.confirmPassword}
                onChange={(e) => setRegistrationForm(prev => ({ ...prev, confirmPassword: e.target.value }))}
                className={registrationErrors.confirmPassword ? 'error' : ''}
              />
              {registrationErrors.confirmPassword && (
                <span className="error-message">{registrationErrors.confirmPassword}</span>
              )}
            </div>
            
            <div className="form-group checkbox-group">
              <label className="checkbox-label">
                <input 
                  type="checkbox" 
                  checked={registrationForm.acceptTerms}
                  onChange={(e) => setRegistrationForm(prev => ({ ...prev, acceptTerms: e.target.checked }))}
                  className={registrationErrors.acceptTerms ? 'error' : ''}
                />
                <span className="checkmark"></span>
                I accept the <a href="#terms" target="_blank" rel="noopener noreferrer">Terms of Service</a> and <a href="#privacy" target="_blank" rel="noopener noreferrer">Privacy Policy</a> *
              </label>
              {registrationErrors.acceptTerms && (
                <span className="error-message">{registrationErrors.acceptTerms}</span>
              )}
            </div>
            
            <button type="submit" className="btn-primary">Create account</button>
          </form>
          
          <div className="auth-divider">
            <span>Or continue with</span>
          </div>
          
          <button onClick={handleGoogleAuth} className="btn-google">
            <span>🔍</span> Google
          </button>
          
          <p className="auth-link">
            Already have an account? <button onClick={() => setCurrentPage('login')}>Sign in</button>
          </p>
        </div>
      </div>
    </div>
  );

  // Dashboard
  const renderDashboard = () => (
    <div className="caliber-app">
      <div className="sidebar">
        <div className="sidebar-header">
          <div className="caliber-logo">
            <img src="https://customer-assets.emergentagent.com/job_caliber-scoring/artifacts/zxi0qkvb_Caliber%20Icon%20-%20Color%20%281%29.png" alt="Caliber Logo" />
          </div>
          <span>Caliber</span>
        </div>
        <nav className="sidebar-nav">
          <div className="nav-item active" onClick={() => setCurrentPage('dashboard')}>
            <span>📊</span> Dashboard
          </div>
          <div className="nav-item" onClick={() => setCurrentPage('wizard')}>
            <span>📈</span> Campaigns
          </div>
          <div className="nav-item" onClick={() => setCurrentPage('wizard')}>
            <span>📁</span> Upload
          </div>
          <div className="nav-item" onClick={handleInsightsClick}>
            <span>🧠</span> Insights
          </div>
          <div className="nav-item" onClick={handleAccountClick}>
            <span>👤</span> Account
          </div>
        </nav>
        <div className="sidebar-footer">
          <button onClick={handleLogout} className="btn-logout">Logout</button>
        </div>
      </div>
      
      <div className="main-content">
        <div className="dashboard-header">
          <h1>Welcome back, {user?.name}</h1>
          <p>Manage your campaigns and analyze performance</p>
        </div>
        
        <div className="quick-start">
          <div className="card">
            <h3>Start New Campaign</h3>
            <p>Create a new campaign with our 7-step wizard</p>
            <button onClick={() => setCurrentPage('wizard')} className="btn-primary">
              Create Campaign
            </button>
          </div>
        </div>
        
        <div className="campaigns-section">
          <h2>Recent Campaigns</h2>
          {loadingCampaigns ? (
            <div className="loading-message">Loading campaigns...</div>
          ) : (
            <div className="campaigns-table">
              <div className="table-header">
                <span>Campaign Name</span>
                <span>Goal</span>
                <span>Channel</span>
                <span>Score</span>
                <span>Date</span>
                <span>Actions</span>
              </div>
              {campaigns.length === 0 ? (
                <div className="empty-message">
                  <p>No campaigns found. Create your first campaign to get started!</p>
                </div>
              ) : (
                campaigns.map(campaign => (
                  <div key={campaign.id} className="table-row">
                    <span 
                      className="campaign-name-link" 
                      onClick={() => handleCampaignClick(campaign.id)}
                      style={{ cursor: 'pointer', color: 'var(--teal)', fontWeight: '600' }}
                    >
                      {campaign.name}
                    </span>
                    <span>{campaign.goal}</span>
                    <span>{campaign.channel}</span>
                    <span className={`score ${campaign.score > 80 ? 'good' : campaign.score > 60 ? 'moderate' : 'poor'}`}>
                      {campaign.score || 'N/A'}
                    </span>
                    <span>{campaign.created_at ? new Date(campaign.created_at).toLocaleDateString() : 'Recent'}</span>
                    <span className="actions-cell">
                      <button
                        className="delete-btn"
                        onClick={(e) => {
                          e.stopPropagation();
                          handleDeleteCampaign(campaign.id, campaign.name);
                        }}
                        title="Delete Campaign"
                      >
                        🗑️
                      </button>
                    </span>
                  </div>
                ))
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );

  // Campaign Wizard Steps
  const renderWizardStep = () => {
    switch (currentStep) {
      case 1:
        return (
          <div className="wizard-step">
            <h3>Select Campaign Type</h3>
            <p>Choose your advertising platform</p>
            <div className="option-grid">
              <div 
                className={`option-card ${campaignData.campaign_type === 'TradeDesk' ? 'selected' : ''}`}
                onClick={() => updateCampaignData({ campaign_type: 'TradeDesk' })}
              >
                <div className="option-icon">TD</div>
                <h4>The Trade Desk</h4>
                <p>Programmatic advertising platform</p>
              </div>
              <div 
                className={`option-card ${campaignData.campaign_type === 'PulsePoint' ? 'selected' : ''}`}
                onClick={() => updateCampaignData({ campaign_type: 'PulsePoint' })}
              >
                <div className="option-icon">PP</div>
                <h4>PulsePoint</h4>
                <p>Healthcare advertising platform</p>
              </div>
            </div>
          </div>
        );
      
      case 2:
        return (
          <div className="wizard-step">
            <h3>Select Campaign Goal</h3>
            <p>Choose your primary objective</p>
            <div className="option-grid">
              <div 
                className={`option-card ${campaignData.goal === 'Awareness' ? 'selected' : ''}`}
                onClick={() => updateCampaignData({ goal: 'Awareness' })}
              >
                <div className="option-icon">🎯</div>
                <h4>Awareness</h4>
                <p>Focus on reach and visibility</p>
              </div>
              <div 
                className={`option-card ${campaignData.goal === 'Action' ? 'selected' : ''}`}
                onClick={() => updateCampaignData({ goal: 'Action' })}
              >
                <div className="option-icon">⚡</div>
                <h4>Action</h4>
                <p>Focus on conversions</p>
              </div>
            </div>
          </div>
        );

      case 3:
        return (
          <div className="wizard-step">
            <h3>Select Channel</h3>
            <p>Choose your advertising channel</p>
            <div className="option-grid channel-grid">
              {['CTV', 'Display', 'Video', 'Audio'].map(channel => (
                <div 
                  key={channel}
                  className={`option-card ${campaignData.channel === channel ? 'selected' : ''}`}
                  onClick={() => updateCampaignData({ channel })}
                >
                  <div className="option-icon">📺</div>
                  <h4>{channel}</h4>
                </div>
              ))}
            </div>
          </div>
        );

      case 4:
        return (
          <div className="wizard-step">
            <h3>CTR Sensitivity Important?</h3>
            <p>Adjust click-through rate importance</p>
            <div className="option-grid">
              <div 
                className={`option-card ${campaignData.ctr_sensitivity === true ? 'selected' : ''}`}
                onClick={() => updateCampaignData({ ctr_sensitivity: true })}
              >
                <div className="option-icon">✅</div>
                <h4>Yes</h4>
                <p>Increase CTR weighting by 10%</p>
              </div>
              <div 
                className={`option-card ${campaignData.ctr_sensitivity === false ? 'selected' : ''}`}
                onClick={() => updateCampaignData({ ctr_sensitivity: false })}
              >
                <div className="option-icon">❌</div>
                <h4>No</h4>
                <p>Use standard CTR weighting</p>
              </div>
            </div>
          </div>
        );

      case 5:
        return (
          <div className="wizard-step">
            <h3>Select Level of Analysis</h3>
            <p>Choose analysis granularity</p>
            <div className="option-grid">
              <div 
                className={`option-card ${campaignData.analysis_level === 'DOMAIN' ? 'selected' : ''}`}
                onClick={() => updateCampaignData({ analysis_level: 'DOMAIN' })}
              >
                <div className="option-icon">🌐</div>
                <h4>Domain-Level</h4>
                <p>Analyze by individual domains</p>
              </div>
              <div 
                className={`option-card ${campaignData.analysis_level === 'VENDOR' ? 'selected' : ''}`}
                onClick={() => updateCampaignData({ analysis_level: 'VENDOR' })}
              >
                <div className="option-icon">🏢</div>
                <h4>Supply Vendor-Level</h4>
                <p>Analyze by supply platforms</p>
              </div>
            </div>
          </div>
        );

      case 6:
        return (
          <div className="wizard-step">
            <h3>Campaign Details</h3>
            <p>Name your campaign and save as template</p>
            <div className="form-group">
              <label>Campaign Name *</label>
              <input 
                type="text" 
                value={campaignData.name}
                onChange={(e) => updateCampaignData({ name: e.target.value })}
                placeholder="Enter campaign name"
              />
            </div>
            <div className="checkbox-group">
              <label>
                <input 
                  type="checkbox" 
                  checked={campaignData.save_as_template}
                  onChange={(e) => updateCampaignData({ save_as_template: e.target.checked })}
                />
                Save as reusable template
              </label>
            </div>
          </div>
        );

      case 7:
        return (
          <div className="wizard-step">
            <h3>Upload Your Data</h3>
            <p>Upload CSV or Excel file with inventory data</p>
            <div 
              className="file-upload-area"
              onDrop={handleFileDrop}
              onDragOver={handleDragOver}
            >
              <div className="upload-content">
                <div className="upload-icon">📁</div>
                <h4>Drop your file here</h4>
                <p>or click to browse and select a file</p>
                <input 
                  type="file" 
                  accept=".csv,.xlsx,.xls"
                  onChange={handleFileUpload}
                  className="file-input"
                  id="file-upload-input"
                />
                <label htmlFor="file-upload-input" className="btn-upload">
                  Choose File
                </label>
              </div>
            </div>
                         {uploadedFile && (
               <div className="uploaded-file">
                 <span>📄 {uploadedFile.name}</span>
                 <span>{(uploadedFile.size / 1024 / 1024).toFixed(2)} MB</span>
                 {uploadedFile.size > 1024 * 1024 && (
                   <span style={{color: 'var(--warning)', fontSize: '12px', marginLeft: '10px'}}>
                     ⚠️ Large file - processing may take 1-2 minutes
                   </span>
                 )}
                 <button 
                   onClick={() => setUploadedFile(null)}
                   style={{ marginLeft: '10px', background: 'none', border: 'none', color: 'var(--neutral-gray)', cursor: 'pointer' }}
                 >
                   ❌
                 </button>
               </div>
             )}
            <div className="required-columns">
              <h4>Required Columns:</h4>
              <div className="columns-grid">
                <div>
                  <strong>Essential:</strong>
                  <ul>
                    <li>Domain</li>
                    <li>Impressions</li>
                    <li>CTR</li>
                  </ul>
                </div>
                <div>
                  <strong>Optional:</strong>
                  <ul>
                    <li>Conversions</li>
                    <li>Total Spend</li>
                    <li>CPM</li>
                  </ul>
                </div>
              </div>
            </div>
          </div>
        );

      default:
        return null;
    }
  };

  // Campaign Wizard
  const renderWizard = () => (
    <div className="caliber-app">
      <div className="sidebar">
        <div className="sidebar-header">
          <div className="caliber-logo">
            <img src="https://customer-assets.emergentagent.com/job_caliber-scoring/artifacts/zxi0qkvb_Caliber%20Icon%20-%20Color%20%281%29.png" alt="Caliber Logo" />
          </div>
          <span>Caliber</span>
        </div>
        <nav className="sidebar-nav">
          <div className="nav-item" onClick={() => setCurrentPage('dashboard')}>
            <span>📊</span> Dashboard
          </div>
          <div className="nav-item active">
            <span>📈</span> Campaigns
          </div>
        </nav>
      </div>
      
      <div className="main-content">
        <div className="wizard-container">
          <div className="wizard-header">
            <h1>Create New Campaign</h1>
            <div className="progress-indicator">
              {[1, 2, 3, 4, 5, 6, 7].map(step => (
                <div 
                  key={step} 
                  className={`progress-step ${step <= currentStep ? 'active' : ''}`}
                >
                  {step}
                </div>
              ))}
            </div>
            <p>Step {currentStep} of 7</p>
          </div>
          
          <div className="wizard-content">
            {renderWizardStep()}
          </div>
          
          <div className="wizard-actions">
            <button 
              onClick={prevStep} 
              disabled={currentStep === 1}
              className="btn-secondary"
            >
              Back
            </button>
            
                         {currentStep === 7 ? (
               <button 
                 onClick={handleCampaignSubmit}
                 disabled={!isStepValid() || isLoading}
                 className="btn-gold"
               >
                 {isLoading ? '🔄 Processing...' : 'Create Campaign & Start Scoring'}
               </button>
             ) : (
              <button 
                onClick={nextStep}
                disabled={!isStepValid()}
                className="btn-primary"
              >
                Continue
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );

  // Scoring Progress
  const renderScoring = () => (
    <div className="scoring-page">
      <div className="scoring-header">
        <h1>🔄 Campaign Scoring in Progress</h1>
        <p>Processing your campaign data with AI-powered scoring...</p>
      </div>
      
      <div className="scoring-content">
        {/* Progress Bar */}
        <div className="progress-section">
          <div className="progress-bar">
            <div 
              className="progress-fill" 
              style={{ width: `${scoringProgress}%` }}
            ></div>
          </div>
          <div className="progress-text">{scoringProgress}% Complete</div>
        </div>
        
        {/* Real-time Progress Details */}
        {realTimeProgress && (
          <div className="progress-details">
            <h3>📊 Real-time Progress</h3>
            
            <div className="progress-grid">
              <div className="progress-item">
                <span className="label">Current Step:</span>
                <span className="value">{progressDetails.currentStep}</span>
              </div>
              
              <div className="progress-item">
                <span className="label">Operation:</span>
                <span className="value">{progressDetails.currentOperation}</span>
              </div>
              
              <div className="progress-item">
                <span className="label">Processed:</span>
                <span className="value">{progressDetails.processedRows} / {progressDetails.totalRows} rows</span>
              </div>
              
              {progressDetails.estimatedCompletion && (
                <div className="progress-item">
                  <span className="label">Estimated Completion:</span>
                  <span className="value">{progressDetails.estimatedCompletion}</span>
                </div>
              )}
            </div>
            
            {/* Errors and Warnings */}
            {progressDetails.errors.length > 0 && (
              <div className="progress-errors">
                <h4>⚠️ Errors</h4>
                <ul>
                  {progressDetails.errors.map((error, index) => (
                    <li key={index}>{error}</li>
                  ))}
                </ul>
              </div>
            )}
            
            {progressDetails.warnings.length > 0 && (
              <div className="progress-warnings">
                <h4>⚠️ Warnings</h4>
                <ul>
                  {progressDetails.warnings.map((warning, index) => (
                    <li key={index}>{warning}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}
        
        {/* Fallback Progress (when WebSocket not available) */}
        {!realTimeProgress && (
          <div className="fallback-progress">
            <h3>📈 Processing Status</h3>
            <p>Campaign creation and scoring is in progress...</p>
            <div className="status-indicators">
              <div className="status-item">
                <span className="status-icon">✅</span>
                <span>Campaign Created</span>
              </div>
              <div className="status-item">
                <span className="status-icon">🔄</span>
                <span>File Processing</span>
              </div>
              <div className="status-item">
                <span className="status-icon">⏳</span>
                <span>AI Scoring</span>
              </div>
              <div className="status-item">
                <span className="status-icon">📊</span>
                <span>Results Generation</span>
              </div>
            </div>
          </div>
        )}
        
        {/* Performance Tips */}
        <div className="performance-tips">
          <h3>💡 Performance Tips</h3>
          <ul>
            <li>Larger files may take longer to process</li>
            <li>Cache hits will significantly speed up repeated files</li>
            <li>Progress updates are real-time via WebSocket</li>
            <li>Fallback to polling if WebSocket unavailable</li>
          </ul>
        </div>
      </div>
    </div>
  );

  // Results Page
  const renderResults = () => (
    <div className="caliber-app">
      <div className="sidebar">
        <div className="sidebar-header">
          <div className="caliber-logo">
            <img src="https://customer-assets.emergentagent.com/job_caliber-scoring/artifacts/zxi0qkvb_Caliber%20Icon%20-%20Color%20%281%29.png" alt="Caliber Logo" />
          </div>
          <span>Caliber</span>
        </div>
        <nav className="sidebar-nav">
          <div className="nav-item" onClick={() => setCurrentPage('dashboard')}>
            <span>📊</span> Dashboard
          </div>
          <div className="nav-item active">
            <span>📈</span> Results
          </div>
        </nav>
      </div>
      
      <div className="main-content results-layout">
        <div className="results-header">
          <h1>Campaign Results: {campaignData.name}</h1>
          <div className="results-actions">
            <button className="btn-secondary" onClick={exportToCSV}>Export CSV</button>
            <button className="btn-secondary" onClick={exportToPDF}>Export PDF</button>
            <button className="btn-primary" onClick={downloadWhitelist}>Download Whitelist</button>
            <button className="btn-gold" onClick={downloadBlacklist}>Download Blacklist</button>
          </div>
        </div>
        
        <div className="results-summary">
          <div className="summary-card">
            <h3>Total Domains</h3>
            <span className="summary-number">{campaignResults.length}</span>
          </div>
          <div className="summary-card">
            <h3>Avg Score</h3>
            <span className="summary-number">{campaignResults.length > 0 ? (campaignResults.reduce((sum, r) => sum + r.score, 0) / campaignResults.length).toFixed(1) : '76.2'}</span>
          </div>
          <div className="summary-card">
            <h3>Good Performers</h3>
            <span className="summary-number">{campaignResults.filter(r => r.status === 'Good').length}</span>
          </div>
        </div>
        
        <div className="results-content-grid">
          <div className="results-table-container">
            {loadingResults ? (
              <div className="loading-message">Loading campaign results...</div>
            ) : (
              <div className="results-table">
                <div className="table-header">
                  <span>Domain</span>
                  <span>Publisher</span>
                  <span>CPM</span>
                  <span>CTR</span>
                  <span>Conv Rate</span>
                  <span>Score</span>
                  <span>Status</span>
                </div>
                {campaignResults.length === 0 ? (
                  <div className="empty-message">
                    <p>No results available yet. Results will appear after campaign processing is complete.</p>
                  </div>
                ) : (
                  campaignResults.map((result, index) => (
                    <div key={index} className="table-row">
                      <span>{result.domain}</span>
                      <span>{result.publisher}</span>
                      <span>${result.cpm}</span>
                      <span>{result.ctr}%</span>
                      <span>{result.conversion_rate || result.convRate}%</span>
                      <span className={`score ${result.status.toLowerCase()}`}>{result.score}</span>
                      <span className={`status ${result.status.toLowerCase()}`}>{result.status}</span>
                    </div>
                  ))
                )}
              </div>
            )}
          </div>
          
          <div className="ai-insights-panel">
            <h3>AI Insights</h3>
            <div className="insights">
              <div className="insight">
                <span>🎯</span>
                <p>Your top-performing domain is {campaignResults.length > 0 ? campaignResults[0]?.domain || 'demo-site.net' : 'demo-site.net'} with 2.5x higher conversions</p>
              </div>
              <div className="insight">
                <span>📊</span>
                <p>{campaignResults.length > 0 ? Math.round((campaignResults.filter(r => r.status === 'Good').length / campaignResults.length) * 100) : 40}% of domains achieve 'Good' performance scores</p>
              </div>
              <div className="insight">
                <span>💡</span>
                <p>Consider blacklisting bottom {Math.ceil(campaignResults.length * 0.2) || 20}% of domains to improve ROI</p>
              </div>
              <div className="insight">
                <span>⚡</span>
                <p>CTV channel shows 23% higher conversion rates than Display</p>
              </div>
              <div className="insight">
                <span>🚨</span>
                <p>{Math.min(campaignResults.length, 3)} domains have declining performance - review recommended</p>
              </div>
            </div>
            <div className="ai-chat">
              <h4>Ask Caliber</h4>
              <input 
                type="text" 
                placeholder="Ask a question about your campaign..." 
                onKeyPress={(e) => e.key === 'Enter' && handleAIQuestion(e.target.value)}
                disabled={isLoading}
              />
              <button className="btn-primary" onClick={() => handleAIQuestion(document.querySelector('.ai-chat input').value)} disabled={isLoading}>
                {isLoading ? 'Sending...' : 'Send'}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );

  // Dark Mode Toggle (always visible)
  const DarkModeToggle = () => (
    <button className="dark-mode-toggle" onClick={toggleDarkMode}>
      {isDarkMode ? '☀️' : '🌙'}
    </button>
  );

  // Insights Page
  const renderInsights = () => (
    <div className="caliber-app">
      <div className="sidebar">
        <div className="sidebar-header">
          <div className="caliber-logo">
            <img src="https://customer-assets.emergentagent.com/job_caliber-scoring/artifacts/zxi0qkvb_Caliber%20Icon%20-%20Color%20%281%29.png" alt="Caliber Logo" />
          </div>
          <span>Caliber</span>
        </div>
        <nav className="sidebar-nav">
          <div className="nav-item" onClick={() => setCurrentPage('dashboard')}>
            <span>📊</span> Dashboard
          </div>
          <div className="nav-item" onClick={() => setCurrentPage('wizard')}>
            <span>📈</span> Campaigns
          </div>
          <div className="nav-item" onClick={() => setCurrentPage('wizard')}>
            <span>📁</span> Upload
          </div>
          <div className="nav-item active">
            <span>🧠</span> Insights
          </div>
          <div className="nav-item" onClick={handleAccountClick}>
            <span>👤</span> Account
          </div>
        </nav>
        <div className="sidebar-footer">
          <button onClick={handleLogout} className="btn-logout">Logout</button>
        </div>
      </div>
      
      <div className="main-content">
        <div className="dashboard-header">
          <h1>AI Insights & Analytics</h1>
          <p>Deep insights into your campaign performance</p>
        </div>
        
        <div className="insights-grid">
          <div className="card">
            <h3>Performance Overview</h3>
            <div className="insight-stats">
              <div className="stat">
                <span className="stat-number">{campaignResults.length > 0 ? (campaignResults.reduce((sum, r) => sum + r.score, 0) / campaignResults.length).toFixed(1) : '87.3'}%</span>
                <span className="stat-label">Avg Performance Score</span>
              </div>
              <div className="stat">
                <span className="stat-number">{campaignResults.length || 156}</span>
                <span className="stat-label">Domains Analyzed</span>
              </div>
              <div className="stat">
                <span className="stat-number">${campaignResults.length > 0 ? (campaignResults.reduce((sum, r) => sum + (r.totalSpend || 0), 0) / 1000000).toFixed(1) : '2.4'}M</span>
                <span className="stat-label">Total Ad Spend</span>
              </div>
            </div>
          </div>
          
          <div className="card">
            <h3>Top Performing Domains</h3>
            <div className="top-domains">
              {campaignResults.length > 0 ? (
                campaignResults
                  .sort((a, b) => b.score - a.score)
                  .slice(0, 3)
                  .map((domain, index) => (
                    <div key={index} className="domain-item">
                      <span>{domain.domain}</span>
                      <span className={`score ${domain.status.toLowerCase()}`}>{domain.score}</span>
                    </div>
                  ))
              ) : (
                <>
                  <div className="domain-item">
                    <span>demo-site.net</span>
                    <span className="score good">91.2</span>
                  </div>
                  <div className="domain-item">
                    <span>example.com</span>
                    <span className="score good">87.5</span>
                  </div>
                  <div className="domain-item">
                    <span>testsite.org</span>
                    <span className="score moderate">72.3</span>
                  </div>
                </>
              )}
            </div>
          </div>
          
          <div className="card">
            <h3>AI Recommendations</h3>
            <div className="recommendations">
              <div className="recommendation">
                <span>🎯</span>
                <p>Focus 60% of budget on top {Math.min(campaignResults.length, 3)} performing domains for 23% better ROI</p>
              </div>
              <div className="recommendation">
                <span>🚨</span>
                <p>Blacklist {Math.ceil(campaignResults.length * 0.2) || 8} underperforming domains to save ${campaignResults.length > 0 ? Math.round(campaignResults.reduce((sum, r) => sum + (r.totalSpend || 0), 0) * 0.15 / 1000) : 45}K monthly</p>
              </div>
              <div className="recommendation">
                <span>📈</span>
                <p>Increase CTV allocation by 15% based on conversion trends</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );

  // Account Page
  const renderAccount = () => (
    <div className="caliber-app">
      <div className="sidebar">
        <div className="sidebar-header">
          <div className="caliber-logo">
            <img src="https://customer-assets.emergentagent.com/job_caliber-scoring/artifacts/zxi0qkvb_Caliber%20Icon%20-%20Color%20%281%29.png" alt="Caliber Logo" />
          </div>
          <span>Caliber</span>
        </div>
        <nav className="sidebar-nav">
          <div className="nav-item" onClick={() => setCurrentPage('dashboard')}>
            <span>📊</span> Dashboard
          </div>
          <div className="nav-item" onClick={() => setCurrentPage('wizard')}>
            <span>📈</span> Campaigns
          </div>
          <div className="nav-item" onClick={() => setCurrentPage('wizard')}>
            <span>📁</span> Upload
          </div>
          <div className="nav-item" onClick={handleInsightsClick}>
            <span>🧠</span> Insights
          </div>
          <div className="nav-item active">
            <span>👤</span> Account
          </div>
        </nav>
        <div className="sidebar-footer">
          <button onClick={handleLogout} className="btn-logout">Logout</button>
        </div>
      </div>
      
      <div className="main-content">
        <div className="dashboard-header">
          <h1>Account Settings</h1>
          <p>Manage your profile and preferences</p>
        </div>
        
        <div className="account-sections">
          <div className="card">
            <h3>Profile Information</h3>
            <div className="form-group">
              <label>Full Name</label>
              <input type="text" value={user?.name || ''} readOnly className="form-input" />
            </div>
            <div className="form-group">
              <label>Email Address</label>
              <input type="email" value={user?.email || ''} readOnly className="form-input" />
            </div>
            <button className="btn-secondary">Edit Profile</button>
          </div>
          
          <div className="card">
            <h3>Preferences</h3>
            <div className="preference-item">
              <label>
                <input type="checkbox" checked={isDarkMode} onChange={toggleDarkMode} />
                Dark Mode
              </label>
            </div>
            <div className="preference-item">
              <label>
                <input type="checkbox" defaultChecked />
                Email Notifications
              </label>
            </div>
            <div className="preference-item">
              <label>
                <input type="checkbox" defaultChecked />
                Weekly Reports
              </label>
            </div>
          </div>
          
          <div className="card">
            <h3>Usage Statistics</h3>
            <div className="usage-stats">
              <div className="usage-item">
                <span>Campaigns Created</span>
                <span>{campaigns.length}</span>
              </div>
              <div className="usage-item">
                <span>Files Processed</span>
                <span>{campaigns.length * 2}</span>
              </div>
              <div className="usage-item">
                <span>Domains Analyzed</span>
                <span>{campaignResults.length || 0}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );

  // Main render logic
  return (
    <div className="caliber-container">
      <DarkModeToggle />
      {error && (
        <div className={`message-banner ${typeof error === 'object' ? error.type : 'error'}`}>
          <span>{typeof error === 'object' ? error.message : error}</span>
          <button onClick={() => setError(null)}>❌</button>
        </div>
      )}
      {currentPage === 'login' && renderLogin()}
      {currentPage === 'register' && renderRegister()}
      {currentPage === 'dashboard' && renderDashboard()}
      {currentPage === 'wizard' && renderWizard()}
      {currentPage === 'scoring' && renderScoring()}
      {currentPage === 'results' && renderResults()}
      {currentPage === 'insights' && renderInsights()}
      {currentPage === 'account' && renderAccount()}
    </div>
  );
};

export default CaliberDemo;
