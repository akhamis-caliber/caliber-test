#!/usr/bin/env node

/**
 * Setup script for authentication testing
 * This script helps configure and test the authentication system
 */

const fs = require('fs');
const path = require('path');

console.log('🔧 Caliber Authentication Setup');
console.log('================================');

// Check if .env.local exists
const envPath = path.join(__dirname, '.env.local');
const envTemplatePath = path.join(__dirname, 'env.template');

if (!fs.existsSync(envPath)) {
  console.log('📝 Creating .env.local file...');
  
  if (fs.existsSync(envTemplatePath)) {
    const template = fs.readFileSync(envTemplatePath, 'utf8');
    fs.writeFileSync(envPath, template);
    console.log('✅ .env.local created from template');
  } else {
    // Create basic .env.local
    const basicEnv = `# API Configuration
NEXT_PUBLIC_API_URL=http://localhost:8000

# Application Configuration
NEXT_PUBLIC_APP_NAME=Caliber Scoring System
NEXT_PUBLIC_APP_VERSION=1.0.0

# Feature Flags
NEXT_PUBLIC_ENABLE_ANALYTICS=true
NEXT_PUBLIC_ENABLE_NOTIFICATIONS=true
`;
    fs.writeFileSync(envPath, basicEnv);
    console.log('✅ .env.local created with basic configuration');
  }
} else {
  console.log('✅ .env.local already exists');
}

console.log('\n📋 Setup Instructions:');
console.log('1. Make sure your backend server is running on http://localhost:8000');
console.log('2. Open your browser and go to http://localhost:3000/test-auth');
console.log('3. Click "Auto Login" to authenticate with test credentials');
console.log('4. Click "Test Campaigns API" to verify the connection');
console.log('\n🔑 Test Credentials:');
console.log('   Email: test@example.com');
console.log('   Password: testpassword123');
console.log('\n🚀 If everything works, you can now access the main dashboard at http://localhost:3000/dashboard');

console.log('\n📝 Troubleshooting:');
console.log('- If you get CORS errors, make sure the backend is running');
console.log('- If authentication fails, check that the backend auth endpoints are working');
console.log('- If campaigns don\'t load, verify the user has proper permissions');

console.log('\n✨ Setup complete! Happy testing!'); 