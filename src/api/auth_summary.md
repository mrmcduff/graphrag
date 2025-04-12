# GraphRAG Authentication System Summary

This document provides a comprehensive overview of the Google OAuth authentication system implemented in the GraphRAG application. Use this as a reference when configuring authentication in other projects with Windsurf.

## Google OAuth Configuration

### Client ID
- Google OAuth client ID: `911441509904-gigqvoc05jc5vilbtp5ba1td3ktc5h17.apps.googleusercontent.com`
- This client ID is used for both local development and Heroku deployment

### Authorized Origins
- Heroku app: `https://graphrag-api-a77f8919e96d.herokuapp.com`
- Local development: `http://localhost:5000`, `http://127.0.0.1:5000`, `http://localhost:52155`, `http://127.0.0.1:52155`, `http://localhost:3000`
- Additional origins can be added via the `ALLOWED_ORIGINS` environment variable

### Redirect URIs
- Heroku callback: `https://graphrag-api-a77f8919e96d.herokuapp.com/api/auth/callback`
- Local callback: `http://localhost:5000/api/auth/callback`

## Authentication Flow

1. **Client-Side Authentication**:
   - The web client loads the Google Identity Services library (`<script src="https://accounts.google.com/gsi/client" async defer></script>`)
   - User clicks the Google Sign-In button
   - Google returns a credential token to the client
   - Client extracts user information from the token

2. **Server-Side Verification**:
   - Client sends the token to `/api/users/authorize` endpoint
   - Server verifies the token and checks if the user's email is authorized
   - If authorized, user gains access to the application

3. **API Authentication**:
   - All subsequent API requests include the Google token in the Authorization header:
     `Authorization: Bearer [GOOGLE_TOKEN]`
   - Server validates the token for each request

## Implementation Details for Windsurf Integration

### Client-Side Code
```javascript
// Google OAuth Button Configuration
<div id="g_id_onload"
     data-client_id="911441509904-gigqvoc05jc5vilbtp5ba1td3ktc5h17.apps.googleusercontent.com"
     data-context="signin"
     data-ux_mode="popup"
     data-callback="handleCredentialResponse"
     data-auto_prompt="false">
</div>

<div class="g_id_signin"
     data-type="standard"
     data-shape="rectangular"
     data-theme="outline"
     data-text="signin_with"
     data-size="large"
     data-logo_alignment="left">
</div>

// Google OAuth Callback
function handleCredentialResponse(response) {
    userToken = response.credential;
    const userInfo = parseJwt(userToken);
    userEmail = userInfo.email;
    
    // Check if user is authorized
    checkUserAuthorization(userEmail);
}

// Parse JWT token
function parseJwt(token) {
    const base64Url = token.split('.')[1];
    const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
    const jsonPayload = decodeURIComponent(atob(base64).split('').map(function(c) {
        return '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2);
    }).join(''));
    return JSON.parse(jsonPayload);
}

// Check if user is authorized to access the application
function checkUserAuthorization(email) {
    fetch(`${API_URL}/users/authorize`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${userToken}`
        },
        body: JSON.stringify({ email: email })
    })
    .then(response => response.json())
    .then(data => {
        isAuthorized = data.authorized;
        if (isAuthorized) {
            // Enable application access
        }
    });
}
```

## Cross-Origin Integration for Windsurf

To access the GraphRAG API from your Windsurf application:

1. **Option 1: Pass the Google OAuth Token**
   ```javascript
   // In your Windsurf application
   const graphragApiUrl = 'https://graphrag-api-a77f8919e96d.herokuapp.com/api';
   const googleToken = 'your-google-oauth-token';

   // Make API calls with the token
   fetch(`${graphragApiUrl}/game/new`, {
     method: 'POST',
     headers: {
       'Content-Type': 'application/json',
       'Authorization': `Bearer ${googleToken}`
     }
   })
   .then(response => response.json())
   .then(data => {
     console.log('New game created:', data);
   });
   ```

2. **Option 2: Create a Proxy in Your Windsurf Application**
   - Get the Google token from your Windsurf application
   - Make requests to the GraphRAG API
   - Return the responses to your frontend

## CORS Configuration

The GraphRAG API is configured to allow CORS requests from specific origins. If you're developing a Windsurf application that needs to access the GraphRAG API:

1. Make sure your application's origin is in the allowed list
2. If not, add it to the `ALLOWED_ORIGINS` environment variable on Heroku:
   ```
   heroku config:set ALLOWED_ORIGINS="http://localhost:3000,https://your-windsurf-app.com" --app graphrag-api-a77f8919e96d
   ```

## Environment Variables for Windsurf Integration

- `ALLOWED_ORIGINS`: Comma-separated list of additional allowed origins for CORS
- `GOOGLE_CLIENT_ID`: Google OAuth client ID (same as above)

## Troubleshooting CORS Issues

If you encounter CORS issues when integrating with Windsurf:

1. Check the browser console for specific CORS error messages
2. Verify that your Windsurf application's origin is in the allowed list
3. Check the Heroku logs for any CORS-related errors:
   ```
   heroku logs --tail --app graphrag-api-a77f8919e96d | grep -i cors
   ```
4. Ensure you're sending the correct headers with your requests

## Security Best Practices for Windsurf Integration

1. Always use HTTPS for production environments
2. Never expose any secrets in client-side code
3. Validate tokens on the server for every authenticated request
4. Implement proper error handling for authentication failures
