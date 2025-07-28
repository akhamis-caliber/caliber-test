# Database Setup and Management

This directory contains the database models, migrations, and utilities for the Caliber application.

## 📁 Directory Structure

```
db/
├── models.py          # SQLAlchemy models and enums
├── utils.py           # Database utility functions
├── README.md          # This file
└── __init__.py        # Package initialization
```

## 🗄️ Database Models

### Core Models

1. **User** - User authentication and profile information

   - `id`, `email`, `full_name`, `firebase_uid`, `is_active`
   - Timestamps: `created_at`, `updated_at`

2. **Organization** - Multi-tenancy support

   - `id`, `name`, `description`, `is_active`
   - Timestamps: `created_at`, `updated_at`

3. **UserOrganization** - Many-to-many relationship with roles

   - `user_id`, `organization_id`, `role`, `is_active`
   - Timestamps: `created_at`, `updated_at`

4. **Campaign** - Scoring campaigns

   - `id`, `name`, `description`, `user_id`, `organization_id`
   - `template_type`, `status`, `scoring_criteria` (JSON)
   - `target_score`, `max_score`, `total_submissions`, `average_score`
   - Timestamps: `created_at`, `updated_at`

5. **Report** - File uploads and processing results

   - `id`, `campaign_id`, `user_id`, `title`, `description`
   - `filename`, `file_path`, `file_size`, `file_type`
   - `status`, `report_type`, `score_data` (JSON), `metadata` (JSON)
   - Timestamps: `created_at`, `updated_at`, `processed_at`

6. **ScoringResult** - Detailed scoring results for individual metrics
   - `id`, `report_id`, `metric_name`, `metric_value`, `score`
   - `weight`, `weighted_score`, `explanation`, `metadata` (JSON)
   - Timestamp: `created_at`

### Supporting Models

7. **AuditLog** - System audit trail

   - `id`, `user_id`, `organization_id`, `action`, `resource_type`
   - `resource_id`, `details` (JSON), `ip_address`, `user_agent`
   - Timestamp: `created_at`

8. **SystemConfig** - System configuration settings
   - `id`, `key`, `value`, `description`, `is_active`
   - Timestamps: `created_at`, `updated_at`

## 🔧 Setup Instructions

### 1. Database Initialization

```bash
# Navigate to backend directory
cd backend

# Initialize database (creates tables and initial data)
python init_db.py

# Initialize with sample data
python init_db.py --sample-data
```

### 2. Database Migrations

```bash
# Navigate to backend directory
cd backend

# Initialize Alembic (first time only)
alembic init migrations

# Create a new migration
alembic revision --autogenerate -m "Description of changes"

# Apply migrations
alembic upgrade head

# Check migration status
alembic current

# Rollback to previous version
alembic downgrade -1
```

### 3. Environment Configuration

Make sure your `.env` file contains the correct database URL:

```env
DATABASE_URL=postgresql://username:password@localhost:5432/caliber_db
```

## 📊 Database Relationships

```
User (1) ←→ (N) UserOrganization (N) ←→ (1) Organization
User (1) ←→ (N) Campaign (N) ←→ (1) Organization
Campaign (1) ←→ (N) Report (1) ←→ (N) ScoringResult
User (1) ←→ (N) Report
```

## 🔍 Key Features

### Multi-tenancy Support

- Organizations provide data isolation
- Users can belong to multiple organizations with different roles
- All data is scoped to organizations

### Audit Trail

- Complete audit logging for all important actions
- Tracks user actions, resource changes, and system events
- Supports compliance and debugging

### Flexible Scoring

- Campaigns can have custom scoring criteria stored as JSON
- Individual metric scores are tracked separately
- Supports weighted scoring and explanations

### File Management

- File uploads are tracked with metadata
- Processing status is maintained
- File paths and sizes are recorded

## 🛠️ Database Utilities

The `utils.py` file provides helper functions for common operations:

### User Operations

- `get_user_by_id()`, `get_user_by_email()`, `get_user_by_firebase_uid()`
- `create_user()`, `update_user()`, `deactivate_user()`

### Organization Operations

- `get_organization_by_id()`, `create_organization()`
- `get_user_organizations()`, `add_user_to_organization()`

### Campaign Operations

- `get_campaign_by_id()`, `get_user_campaigns()`
- `create_campaign()`, `update_campaign()`, `delete_campaign()`

### Report Operations

- `get_report_by_id()`, `get_campaign_reports()`
- `create_report()`, `update_report_status()`

### Scoring Operations

- `get_report_scoring_results()`, `create_scoring_result()`
- `bulk_create_scoring_results()`

### Audit Operations

- `create_audit_log()`, `get_audit_logs()`

### System Configuration

- `get_system_config()`, `set_system_config()`

### Analytics

- `get_campaign_statistics()`, `get_user_statistics()`

## 📈 Performance Considerations

### Indexes

- Primary keys are automatically indexed
- Foreign keys have indexes for join performance
- Common query fields (email, status, created_at) are indexed
- Composite indexes for frequently used combinations

### Connection Pooling

- Configured with appropriate pool size and overflow settings
- Connection timeouts and pre-ping enabled
- Settings can be adjusted in `config/settings.py`

### Query Optimization

- Use utility functions for common queries
- Implement pagination for large result sets
- Use bulk operations for multiple records

## 🔒 Security Features

### Data Isolation

- Multi-tenant architecture with organization-based isolation
- User permissions controlled through roles
- Soft deletes for data retention

### Audit Trail

- Complete logging of all data modifications
- User action tracking with IP addresses
- Resource-level audit logs

### Input Validation

- SQLAlchemy model validation
- Pydantic schema validation
- Type checking and constraints

## 🚀 Best Practices

1. **Always use transactions** for multi-step operations
2. **Use utility functions** instead of direct queries
3. **Create audit logs** for important actions
4. **Validate data** before database operations
5. **Use appropriate indexes** for query performance
6. **Implement soft deletes** for data retention
7. **Use connection pooling** for performance
8. **Test migrations** in development before production

## 🐛 Troubleshooting

### Common Issues

1. **Connection Errors**

   - Check DATABASE_URL in .env file
   - Verify database server is running
   - Check network connectivity

2. **Migration Errors**

   - Ensure all models are imported in env.py
   - Check for conflicting migrations
   - Verify database schema matches models

3. **Performance Issues**
   - Check query execution plans
   - Verify indexes are being used
   - Monitor connection pool usage

### Debug Commands

```bash
# Check database connection
python -c "from config.database import engine; print(engine.execute('SELECT 1').scalar())"

# List all tables
python -c "from db.models import Base; from config.database import engine; print(Base.metadata.tables.keys())"

# Check migration status
alembic current
alembic history
```
