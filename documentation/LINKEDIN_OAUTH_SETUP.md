# LinkedIn OAuth Integration Setup

## Overview
This setup allows users to authenticate with LinkedIn OAuth and connect their LinkedIn accounts to your application. Users can sign up/login with LinkedIn or connect LinkedIn to existing accounts.

## Configuration

### 1. LinkedIn Developer App Setup
1. Go to [LinkedIn Developer Portal](https://www.linkedin.com/developers/)
2. Create a new app or use an existing one
3. Add the following redirect URI to your app:
   - For development: `http://localhost:8000/auth/linkedin/callback`
   - For production: `https://yourdomain.com/auth/linkedin/callback`
4. Note down your `Client ID` and `Client Secret`

### 2. Environment Variables
Create a `.env` file in your project root with the following variables:

```bash
# LinkedIn OAuth Configuration
LINKEDIN_CLIENT_ID=your_linkedin_client_id_here
LINKEDIN_CLIENT_SECRET=your_linkedin_client_secret_here
LINKEDIN_REDIRECT_URI=http://localhost:8000/auth/linkedin/callback

# Your existing database and JWT configuration
DATABASE_URL=postgresql://username:password@localhost:5432/database_name
SECRET_KEY=your_jwt_secret_key_here
```

## API Endpoints

### 1. Get Authorization URL
**GET** `/auth/linkedin/authorize`

Returns the LinkedIn authorization URL that frontend should redirect users to.

**Response:**
```json
{
  "authorization_url": "https://www.linkedin.com/oauth/v2/authorization?...",
  "state": "security_state_token"
}
```

### 2. Handle OAuth Callback
**POST** `/auth/linkedin/callback`

Handles the OAuth callback and creates/logins user.

**Request Body:**
```json
{
  "code": "authorization_code_from_linkedin",
  "state": "state_token_from_step_1"
}
```

**Response:**
```json
{
  "status": "success",
  "message": "LinkedIn authentication successful",
  "user": {
    "name": "John Doe",
    "email": "john@example.com",
    "linkedin_id": "linkedin_user_id",
    "profile_picture_url": "https://media.licdn.com/...",
    "is_linkedin_connected": true
  }
}
```

### 3. Connect LinkedIn to Existing Account
**POST** `/auth/linkedin/connect`

Connects LinkedIn account to an already authenticated user.

**Headers:** Requires JWT authentication
**Request Body:**
```json
{
  "code": "authorization_code_from_linkedin",
  "state": "state_token"
}
```

### 4. Disconnect LinkedIn Account
**POST** `/auth/linkedin/disconnect`

Disconnects LinkedIn from the current user's account.

**Headers:** Requires JWT authentication

### 5. Get LinkedIn Profile
**GET** `/auth/linkedin/profile`

Fetches fresh LinkedIn profile data for the current user.

**Headers:** Requires JWT authentication

## Frontend Integration Flow

### Option 1: Sign Up/Login with LinkedIn

1. **Get Authorization URL**
   ```javascript
   const response = await fetch('/auth/linkedin/authorize');
   const { authorization_url, state } = await response.json();
   
   // Store state for verification
   sessionStorage.setItem('linkedin_state', state);
   
   // Redirect user to LinkedIn
   window.location.href = authorization_url;
   ```

2. **Handle Callback**
   ```javascript
   // On your callback page (after LinkedIn redirects back)
   const urlParams = new URLSearchParams(window.location.search);
   const code = urlParams.get('code');
   const state = urlParams.get('state');
   const storedState = sessionStorage.getItem('linkedin_state');
   
   if (state !== storedState) {
     throw new Error('State mismatch - possible CSRF attack');
   }
   
   const response = await fetch('/auth/linkedin/callback', {
     method: 'POST',
     headers: { 'Content-Type': 'application/json' },
     body: JSON.stringify({ code, state })
   });
   
   const result = await response.json();
   // User is now logged in with JWT cookies set
   ```

### Option 2: Connect LinkedIn to Existing Account

1. **User must be logged in first**
2. **Get Authorization URL** (same as above)
3. **Handle Connection**
   ```javascript
   const response = await fetch('/auth/linkedin/connect', {
     method: 'POST',
     headers: { 'Content-Type': 'application/json' },
     credentials: 'include', // Include JWT cookies
     body: JSON.stringify({ code, state })
   });
   ```

## Database Schema Changes

The following fields were added to the `users` table:

- `linkedin_id` (String, nullable, unique when not null)
- `linkedin_access_token` (String, nullable) - for API calls
- `profile_picture_url` (String, nullable)
- `is_linkedin_connected` (Boolean, default: false)

## Security Features

1. **State Parameter**: Prevents CSRF attacks during OAuth flow
2. **Unique LinkedIn ID**: Prevents one LinkedIn account from being connected to multiple users
3. **JWT Integration**: Seamless integration with existing authentication system
4. **Token Storage**: LinkedIn access tokens are securely stored for API calls

## Testing

1. Start your development server:
   ```bash
   uvicorn src.aptwise.main:app --reload
   ```

2. Test the authorization URL endpoint:
   ```bash
   curl http://localhost:8000/auth/linkedin/authorize
   ```

3. Open the returned authorization URL in a browser to test the full flow

## Production Considerations

1. **HTTPS Required**: LinkedIn OAuth requires HTTPS in production
2. **Environment Variables**: Ensure all secrets are properly configured
3. **CORS Settings**: Configure CORS for your frontend domain
4. **Token Refresh**: Consider implementing LinkedIn token refresh logic
5. **Rate Limiting**: Implement rate limiting for OAuth endpoints
6. **Error Handling**: Add comprehensive error logging and monitoring

## Troubleshooting

### Common Issues:

1. **"Invalid redirect_uri"**: Ensure the redirect URI in your LinkedIn app matches exactly
2. **"Invalid client_id"**: Check your environment variables
3. **State mismatch**: Ensure frontend properly stores and verifies state parameter
4. **CORS errors**: Configure FastAPI CORS middleware for your frontend domain

### Debug Mode:
Add logging to see detailed OAuth flow:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```
