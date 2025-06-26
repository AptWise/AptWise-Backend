# LinkedIn OAuth Integration - Complete Setup

## 🎯 Summary

I've successfully set up LinkedIn OAuth verification for your AptWise backend. Users can now:

1. **Sign up/Login with LinkedIn** - Create new accounts using LinkedIn credentials
2. **Connect LinkedIn to existing accounts** - Link LinkedIn profiles to existing user accounts
3. **Fetch LinkedIn profile data** - Access user's LinkedIn information
4. **Manage LinkedIn connections** - Connect/disconnect LinkedIn accounts

## 📋 What's Been Implemented

### ✅ Database Changes
- **New migration**: Added LinkedIn OAuth fields to users table
- **New fields**: `linkedin_id`, `linkedin_access_token`, `profile_picture_url`, `is_linkedin_connected`
- **Unique constraints**: LinkedIn ID is unique when present

### ✅ API Endpoints
- `GET /auth/linkedin/authorize` - Get LinkedIn authorization URL
- `POST /auth/linkedin/callback` - Handle OAuth callback and login/signup
- `POST /auth/linkedin/connect` - Connect LinkedIn to existing account
- `POST /auth/linkedin/disconnect` - Disconnect LinkedIn from account
- `GET /auth/linkedin/profile` - Get fresh LinkedIn profile data

### ✅ Security Features
- **CSRF Protection**: State parameter prevents attacks
- **JWT Integration**: Seamless with existing authentication
- **Unique LinkedIn accounts**: One LinkedIn account per user
- **Secure token storage**: LinkedIn access tokens stored securely

### ✅ Error Handling
- **Graceful degradation**: Works without LinkedIn credentials
- **Comprehensive error messages**: Clear feedback for all scenarios
- **CORS support**: Ready for frontend integration

## 🔧 Configuration Required

### 1. LinkedIn App Setup
```
1. Go to https://www.linkedin.com/developers/
2. Create a new app
3. Add redirect URI: http://localhost:8000/auth/linkedin/callback
4. Note your Client ID and Client Secret
```

### 2. Environment Variables
Create `.env` file in project root:
```bash
LINKEDIN_CLIENT_ID=your_client_id_here
LINKEDIN_CLIENT_SECRET=your_client_secret_here
LINKEDIN_REDIRECT_URI=http://localhost:8000/auth/linkedin/callback
```

## 🚀 Usage Examples

### Frontend Integration (JavaScript)

#### Option 1: Sign Up/Login with LinkedIn
```javascript
// Step 1: Get authorization URL
const authResponse = await fetch('/auth/linkedin/authorize');
const { authorization_url, state } = await authResponse.json();

// Store state for security
sessionStorage.setItem('linkedin_state', state);

// Redirect user to LinkedIn
window.location.href = authorization_url;

// Step 2: Handle callback (on your callback page)
const urlParams = new URLSearchParams(window.location.search);
const code = urlParams.get('code');
const returnedState = urlParams.get('state');
const storedState = sessionStorage.getItem('linkedin_state');

if (returnedState === storedState) {
    const response = await fetch('/auth/linkedin/callback', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ code, state: returnedState })
    });
    
    const result = await response.json();
    // User is now logged in!
}
```

#### Option 2: Connect LinkedIn to Existing Account
```javascript
// User must be logged in first
const response = await fetch('/auth/linkedin/connect', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include', // Include JWT cookies
    body: JSON.stringify({ code, state })
});
```

### Backend API Testing
```bash
# Test authorization URL
curl -X GET "http://localhost:8000/auth/linkedin/authorize"

# Test callback
curl -X POST "http://localhost:8000/auth/linkedin/callback" \
  -H "Content-Type: application/json" \
  -d '{"code": "your_code", "state": "your_state"}'
```

## 📊 Database Schema

### Updated Users Table
```sql
CREATE TABLE users (
    email VARCHAR PRIMARY KEY,
    name VARCHAR,
    password VARCHAR,
    linkedin_url VARCHAR,
    github_url VARCHAR,
    linkedin_id VARCHAR UNIQUE,           -- NEW
    linkedin_access_token VARCHAR,        -- NEW
    profile_picture_url VARCHAR,          -- NEW
    is_linkedin_connected BOOLEAN DEFAULT FALSE -- NEW
);
```

## 🔍 API Documentation

### Response Examples

#### Authorization URL Response
```json
{
  "authorization_url": "https://www.linkedin.com/oauth/v2/authorization?...",
  "state": "security_token_here"
}
```

#### Successful Login Response
```json
{
  "status": "success",
  "message": "LinkedIn authentication successful",
  "user": {
    "name": "John Doe",
    "email": "john@example.com",
    "linkedin_id": "ABC123",
    "profile_picture_url": "https://media.licdn.com/...",
    "is_linkedin_connected": true
  }
}
```

#### User Profile Response
```json
{
  "name": "John Doe",
  "email": "john@example.com",
  "linkedin_url": null,
  "github_url": null,
  "linkedin_id": "ABC123",
  "profile_picture_url": "https://media.licdn.com/...",
  "is_linkedin_connected": true
}
```

## 🛡️ Security Considerations

1. **State Parameter**: Prevents CSRF attacks
2. **HTTPS in Production**: Required for LinkedIn OAuth
3. **Token Storage**: LinkedIn tokens stored securely in database
4. **Rate Limiting**: Consider implementing for OAuth endpoints
5. **CORS Configuration**: Properly configured for your frontend

## 🧪 Testing

### Run Test Server
```bash
cd AptWise-Backend
uvicorn src.aptwise.main:app --reload
```

### Test Endpoints
```bash
python test_linkedin_oauth.py
```

### View API Documentation
```
http://localhost:8000/docs
```

## 📝 Files Created/Modified

### New Files:
- `src/aptwise/config/linkedin_config.py` - LinkedIn OAuth configuration
- `src/aptwise/auth/linkedin_service.py` - LinkedIn OAuth service
- `migrations/versions/51ea273bcb45_add_linkedin_oauth_fields.py` - Database migration
- `LINKEDIN_OAUTH_SETUP.md` - Detailed setup documentation
- `test_linkedin_oauth.py` - Test script
- `.env.example` - Environment variables template

### Modified Files:
- `src/aptwise/auth/routes.py` - Added LinkedIn OAuth routes
- `src/aptwise/auth/models.py` - Added LinkedIn OAuth models
- `src/aptwise/database/db_auth_services.py` - Added LinkedIn database functions
- `src/aptwise/database/__init__.py` - Exported new functions
- `src/aptwise/main.py` - Added CORS middleware
- `pyproject.toml` - Added new dependencies

## 🎉 Next Steps

1. **Set up LinkedIn App**: Create LinkedIn developer app and get credentials
2. **Configure Environment**: Add credentials to `.env` file
3. **Test Integration**: Use the provided test script
4. **Frontend Integration**: Implement the JavaScript flow in your frontend
5. **Production Deployment**: Ensure HTTPS and proper CORS configuration

## 🔧 Troubleshooting

- **"LinkedIn OAuth not configured"**: Add credentials to `.env` file
- **"Invalid redirect_uri"**: Ensure redirect URI matches LinkedIn app settings
- **CORS errors**: Check CORS configuration in `main.py`
- **State mismatch**: Ensure frontend properly stores and verifies state

The LinkedIn OAuth integration is now complete and ready for use! 🚀
