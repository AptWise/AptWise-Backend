# GitHub OAuth Setup Instructions

## Prerequisites
1. You need a GitHub account
2. Go to GitHub Settings > Developer settings > OAuth Apps
3. Click "New OAuth App" or go to: https://github.com/settings/applications/new

## GitHub OAuth App Configuration
Fill in the following details:
- **Application name**: AptWise (or your preferred name)
- **Homepage URL**: http://localhost:5174 (your frontend URL)
- **Authorization callback URL**: http://localhost:8000/auth/github/callback (your backend callback)
- **Application description**: (optional) AptWise - GitHub integration for user authentication

## Environment Variables
After creating your GitHub OAuth App, add these to your `.env` file:

```env
# GitHub OAuth Configuration
GITHUB_CLIENT_ID=your_github_client_id_here
GITHUB_CLIENT_SECRET=your_github_client_secret_here
GITHUB_REDIRECT_URI=http://localhost:8000/auth/github/callback
```

## GitHub OAuth Scopes
The following scopes are requested:
- `user:email` - Access to user's email address
- `read:user` - Access to user's profile information

## Testing
1. Run the test script: `python test_github_oauth.py`
2. Start your backend server
3. Visit: http://localhost:8000/auth/debug/github to check configuration
4. Test the OAuth flow by visiting: http://localhost:8000/auth/github/authorize

## API Endpoints
After setup, these endpoints will be available:

### OAuth Flow
- `GET /auth/github/authorize` - Get authorization URL
- `GET /auth/github/callback` - Handle OAuth redirect (for browser)
- `POST /auth/github/callback` - Handle OAuth callback (for frontend)

### Account Management
- `POST /auth/github/connect` - Connect GitHub to existing account
- `POST /auth/github/disconnect` - Disconnect GitHub from account
- `GET /auth/github/profile` - Get GitHub profile info

### Debug
- `GET /auth/debug/github` - Check configuration (remove in production)

## Frontend Integration
Your frontend should:
1. Call `/auth/github/authorize` to get the authorization URL
2. Redirect user to the authorization URL
3. Handle the callback at `/auth/github/callback` route in your frontend
4. Extract the `code` and `state` from callback URL
5. POST to `/auth/github/callback` with the code and state to complete login
