# Authentication Service

This directory contains the complete authentication service for the Caliber application, supporting both traditional email/password authentication and Google OAuth via Firebase.

## 📁 Directory Structure

```
auth_service/
├── __init__.py              # Package initialization
├── models/
│   └── user.py              # User model operations
├── routes/
│   ├── __init__.py          # Routes package
│   └── auth.py              # Authentication endpoints
├── middleware.py            # Authentication middleware
├── jwt_manager.py           # JWT token management
├── firebase_verify.py       # Firebase token verification
└── README.md               # This file
```

## 🔐 Authentication Methods

### 1. Email/Password Authentication

- User registration with password hashing (bcrypt)
- Secure login with password verification
- Password update functionality

### 2. Google OAuth Authentication

- Firebase integration for Google OAuth
- Automatic user creation from Google data
- Secure token verification

### 3. JWT Token Management

- Access tokens (short-lived)
- Refresh tokens (long-lived)
- Token verification and validation
- Automatic token refresh

## 🛠️ Setup Instructions

### 1. Environment Configuration

Add the following to your `.env` file:

```env
# JWT Settings
JWT_SECRET_KEY=your-super-secret-jwt-key-here
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# Firebase Settings (for Google OAuth)
FIREBASE_PROJECT_ID=your-firebase-project-id
FIREBASE_PRIVATE_KEY_ID=your-private-key-id
FIREBASE_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"
FIREBASE_CLIENT_EMAIL=your-service-account@project.iam.gserviceaccount.com
FIREBASE_CLIENT_ID=your-client-id
FIREBASE_CLIENT_X509_CERT_URL=https://www.googleapis.com/robot/v1/metadata/x509/your-service-account%40project.iam.gserviceaccount.com
```

### 2. Firebase Setup

1. Create a Firebase project at [Firebase Console](https://console.firebase.google.com/)
2. Enable Google Authentication in Authentication > Sign-in method
3. Create a service account in Project Settings > Service Accounts
4. Download the service account JSON file
5. Use the values from the JSON file in your `.env` configuration

### 3. Database Setup

Ensure your database has the updated User model with the `password_hash` field:

```sql
ALTER TABLE users ADD COLUMN password_hash VARCHAR(255);
ALTER TABLE users ADD COLUMN organization VARCHAR(255);
ALTER TABLE users ADD COLUMN role VARCHAR(50) DEFAULT 'user';
```

## 🚀 API Endpoints

### Authentication Endpoints

| Method | Endpoint                 | Description               | Auth Required |
| ------ | ------------------------ | ------------------------- | ------------- |
| POST   | `/api/auth/register`     | Register new user         | No            |
| POST   | `/api/auth/login`        | Login with email/password | No            |
| POST   | `/api/auth/google-login` | Login with Google OAuth   | No            |
| GET    | `/api/auth/me`           | Get current user info     | Yes           |
| POST   | `/api/auth/logout`       | Logout user               | Yes           |
| POST   | `/api/auth/refresh`      | Refresh access token      | No            |
| PUT    | `/api/auth/profile`      | Update user profile       | Yes           |
| DELETE | `/api/auth/account`      | Delete user account       | Yes           |
| GET    | `/api/auth/verify`       | Verify token validity     | Yes           |

### Request/Response Examples

#### Register User

```bash
POST /api/auth/register
Content-Type: application/json

{
  "email": "user@example.com",
  "full_name": "John Doe",
  "password": "securepassword123",
  "organization": "Example Corp",
  "role": "user"
}
```

Response:

```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

#### Login

```bash
POST /api/auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "securepassword123"
}
```

#### Google OAuth Login

```bash
POST /api/auth/google-login
Content-Type: application/json

{
  "id_token": "google_id_token_here"
}
```

#### Get Current User

```bash
GET /api/auth/me
Authorization: Bearer your_access_token_here
```

Response:

```json
{
  "id": 1,
  "email": "user@example.com",
  "full_name": "John Doe",
  "organization": "Example Corp",
  "role": "user",
  "firebase_uid": null,
  "is_active": true,
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z"
}
```

## 🔒 Security Features

### Password Security

- **bcrypt hashing**: All passwords are hashed using bcrypt
- **Salt generation**: Automatic salt generation for each password
- **Secure comparison**: Constant-time password verification

### JWT Security

- **Short-lived access tokens**: 30 minutes by default
- **Long-lived refresh tokens**: 7 days by default
- **Token verification**: Secure token validation
- **Automatic expiration**: Tokens expire automatically

### Firebase Security

- **Token verification**: All Google tokens are verified with Firebase
- **User validation**: Firebase user data is validated
- **Secure integration**: Service account authentication

### Rate Limiting

- **Request limiting**: Built-in rate limiting middleware
- **IP-based tracking**: Rate limits per IP address
- **Configurable limits**: Adjustable requests per minute

## 🛡️ Middleware Usage

### Protecting Routes

```python
from auth_service.middleware import get_current_user, require_admin

@app.get("/protected")
async def protected_route(current_user: User = Depends(get_current_user)):
    return {"message": f"Hello {current_user.email}"}

@app.get("/admin-only")
async def admin_route(current_user: User = Depends(require_admin)):
    return {"message": "Admin access granted"}
```

### Role-Based Access

```python
from auth_service.middleware import require_role, require_user_or_admin

@app.get("/user-content")
async def user_content(current_user: User = Depends(require_user_or_admin)):
    return {"content": "User content here"}

@app.get("/viewer-content")
async def viewer_content(current_user: User = Depends(require_role("viewer"))):
    return {"content": "Viewer content here"}
```

### Permission-Based Access

```python
from auth_service.middleware import require_permission

@app.post("/campaigns")
async def create_campaign(
    current_user: User = Depends(require_permission("can_create_campaigns"))
):
    return {"message": "Campaign created"}
```

## 📊 Audit Logging

All authentication events are automatically logged:

- **User registration**: Tracks new user creation
- **User login**: Records login attempts and methods
- **User logout**: Logs logout events
- **Profile updates**: Tracks profile changes
- **Account deletion**: Records account deactivation
- **Token refresh**: Logs token refresh attempts

### Audit Log Example

```json
{
  "id": 1,
  "user_id": 1,
  "action": "USER_LOGIN",
  "resource_type": "USER",
  "resource_id": 1,
  "details": {
    "email": "user@example.com",
    "method": "email_password"
  },
  "ip_address": "192.168.1.1",
  "user_agent": "Mozilla/5.0...",
  "created_at": "2024-01-01T00:00:00Z"
}
```

## 🔧 Configuration Options

### JWT Configuration

```python
# In config/settings.py
JWT_SECRET_KEY: str = "your-secret-key"
JWT_ALGORITHM: str = "HS256"
JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7
```

### Firebase Configuration

```python
# In config/settings.py
FIREBASE_PROJECT_ID: str = "your-project-id"
FIREBASE_PRIVATE_KEY: str = "your-private-key"
FIREBASE_CLIENT_EMAIL: str = "your-service-account@project.iam.gserviceaccount.com"
```

### Rate Limiting Configuration

```python
# In config/settings.py
RATE_LIMIT_PER_MINUTE: int = 60
RATE_LIMIT_PER_HOUR: int = 1000
```

## 🚨 Error Handling

### Common Error Responses

#### 401 Unauthorized

```json
{
  "detail": "Could not validate credentials",
  "headers": { "WWW-Authenticate": "Bearer" }
}
```

#### 403 Forbidden

```json
{
  "detail": "Permission denied: can_create_campaigns"
}
```

#### 429 Too Many Requests

```json
{
  "detail": "Rate limit exceeded"
}
```

## 🧪 Testing

### Test Authentication Flow

1. **Register a new user**:

```bash
curl -X POST "http://localhost:8000/api/auth/register" \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"password123","full_name":"Test User"}'
```

2. **Login with the user**:

```bash
curl -X POST "http://localhost:8000/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"password123"}'
```

3. **Access protected endpoint**:

```bash
curl -X GET "http://localhost:8000/api/auth/me" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

## 🔍 Troubleshooting

### Common Issues

1. **Firebase Configuration Error**

   - Ensure all Firebase environment variables are set
   - Verify the service account JSON is properly formatted
   - Check Firebase project permissions

2. **JWT Token Issues**

   - Verify JWT_SECRET_KEY is set and secure
   - Check token expiration settings
   - Ensure proper token format in Authorization header

3. **Database Connection Issues**
   - Verify database connection string
   - Check if User table has required fields
   - Ensure database migrations are applied

### Debug Commands

```bash
# Check Firebase configuration
python -c "from auth_service.firebase_verify import FirebaseAuth; FirebaseAuth.initialize_firebase()"

# Test JWT token creation
python -c "from auth_service.jwt_manager import create_access_token; print(create_access_token({'sub': 'test@example.com', 'user_id': 1}))"

# Verify database connection
python -c "from config.database import get_db; db = next(get_db()); print('Database connected')"
```

## 📚 Best Practices

1. **Always use HTTPS** in production
2. **Rotate JWT secrets** regularly
3. **Monitor audit logs** for suspicious activity
4. **Implement proper error handling** in client applications
5. **Use refresh tokens** for better security
6. **Validate all inputs** on both client and server
7. **Keep dependencies updated** for security patches
8. **Implement proper logout** on client side
9. **Use strong passwords** and enforce password policies
10. **Monitor rate limiting** and adjust as needed
