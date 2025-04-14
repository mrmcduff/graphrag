# Managing CORS Origins for GraphRAG API

This document explains how to add and manage allowed origins for Cross-Origin Resource Sharing (CORS) in the GraphRAG API.

## Current CORS Configuration

The GraphRAG API uses Flask-CORS to handle Cross-Origin Resource Sharing. The current configuration explicitly allows requests from specific origins:

1. The Heroku app itself: `https://graphrag-api-a77f8919e96d.herokuapp.com`
2. Local development servers: `http://localhost:5000` and `http://127.0.0.1:5000`
3. Common frontend development servers: `http://localhost:3000` (React/Next.js)
4. Any additional origins specified via the `ALLOWED_ORIGINS` environment variable

## Adding New Origins

### Method 1: Using Heroku Environment Variables (Recommended)

This is the easiest way to add new origins without redeploying:

```bash
# Add a single origin
heroku config:set ALLOWED_ORIGINS="https://new-app.com" --app graphrag-api

# Add multiple origins (comma-separated)
heroku config:set ALLOWED_ORIGINS="https://app1.com,https://app2.com" --app graphrag-api

# Append to existing origins
heroku config:set ALLOWED_ORIGINS="https://your-new-web-app.com,http://localhost:8080,https://another-app.com" --app graphrag-api
```

### Method 2: Modifying the Code

If you prefer to hardcode the origins:

1. Edit `src/api/server.py`
2. Add your new origins to the `cors_origins` list
3. Commit and push to Heroku

```python
cors_origins = [
    # Existing origins
    'https://graphrag-api-a77f8919e96d.herokuapp.com',
    'http://localhost:5000',
    'http://127.0.0.1:5000',
    'http://localhost:3000',
    'http://localhost:5173',
    'http://localhost:5174',
    'https://localhost:5173',
    'https://localhost:5174',
    # Add your new origins here
    'https://your-new-web-app.com',
    'http://localhost:8080',
]
```

## Testing CORS Configuration

To verify your CORS configuration is working correctly:

1. From your web application, make a request to the GraphRAG API
2. Check the browser console for CORS errors
3. If you see CORS errors, ensure your origin is in the allowed list

```javascript
// Example test in browser console
fetch('https://graphrag-api-a77f8919e96d.herokuapp.com/api/health', {
  method: 'GET',
  headers: {
    'Content-Type': 'application/json'
  }
})
.then(response => response.json())
.then(data => console.log('Success:', data))
.catch(error => console.error('Error:', error));
```

## Security Considerations

1. **Be Selective**: Only add origins that genuinely need access to your API
2. **Use HTTPS**: For production applications, always use HTTPS origins
3. **Review Regularly**: Periodically review your allowed origins and remove any that are no longer needed

## Troubleshooting

If you're still experiencing CORS issues after adding your origin:

1. Verify the exact origin URL (including protocol, domain, and port)
2. Check for typos in the origin URL
3. Restart the Heroku dyno after updating environment variables: `heroku restart --app graphrag-api`
4. Check the Heroku logs for any CORS-related errors: `heroku logs --tail --app graphrag-api`
