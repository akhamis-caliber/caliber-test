// MongoDB initialization script for Caliber
// This script runs when MongoDB container starts for the first time

// Switch to Caliber database
db = db.getSiblingDB('caliber');

// Create collections with some initial data if needed
db.createCollection('users');
db.createCollection('campaigns');
db.createCollection('reports');

// Create indexes for better performance
db.users.createIndex({ "email": 1 }, { unique: true });
db.campaigns.createIndex({ "name": 1 });
db.campaigns.createIndex({ "created_at": -1 });
db.reports.createIndex({ "campaign_id": 1 });

// Insert some sample data for development
db.users.insertOne({
  "_id": "dev-user-123",
  "name": "Development User",
  "email": "dev@caliber.com",
  "created_at": new Date(),
  "organizations": [{
    "id": "default-org",
    "name": "Development User's Organization",
    "role": "Admin"
  }]
});

print("MongoDB initialized for Caliber with collections and indexes");