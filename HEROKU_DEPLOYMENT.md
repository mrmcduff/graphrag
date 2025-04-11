# Deploying GraphRAG to Heroku

This guide explains how to deploy your GraphRAG Text Adventure Game API to Heroku.

## Prerequisites

1. [Heroku CLI](https://devcenter.heroku.com/articles/heroku-cli) installed
2. Git repository initialized for your project
3. Heroku account created

## Deployment Steps

### 1. Login to Heroku

```bash
heroku login
```

### 2. Create a Heroku App

```bash
# Create a new Heroku app
heroku create graphrag-api

# Or if you want a specific name
heroku create your-preferred-name
```

### 3. Add PostgreSQL Database

```bash
heroku addons:create heroku-postgresql:hobby-dev
```

### 4. Set Environment Variables

Set any required environment variables for your application:

```bash
# JWT Secret Key
heroku config:set JWT_SECRET_KEY=your_secret_key

# Google OAuth (if using)
heroku config:set GOOGLE_CLIENT_ID=911441509904-gigqvoc05jc5vilbtp5ba1td3ktc5h17.apps.googleusercontent.com
heroku config:set GOOGLE_CLIENT_SECRET=your_client_secret

# Other environment variables as needed
```

### 5. Deploy Your Application

```bash
# From your project root directory
git add .
git commit -m "Prepare for Heroku deployment"
git push heroku main
```

### 6. Run Database Migrations (First Deployment)

When deploying for the first time, you need to initialize the database:

```bash
heroku run python -c "from src.api.server import create_app; from src.api.models import db; app = create_app(); app.app_context().push(); db.create_all()"
```

### 7. Create Admin User (Optional)

```bash
heroku run python -m src.api.server --create-admin
```

### 8. Open Your Application

```bash
heroku open
```

## File Storage with Bucketeer

Heroku has an ephemeral filesystem, meaning any files written to the filesystem will be lost when the dyno restarts. Fortunately, Heroku offers Bucketeer as an add-on for persistent file storage.

### Adding Bucketeer to Your App

```bash
# Add the Bucketeer add-on (various tiers available)
heroku addons:create bucketeer:hobbyist
```

This will automatically set up the following environment variables:
- `BUCKETEER_AWS_ACCESS_KEY_ID`
- `BUCKETEER_AWS_SECRET_ACCESS_KEY`
- `BUCKETEER_AWS_REGION`
- `BUCKETEER_BUCKET_NAME`

The GraphRAG `StorageManager` will automatically detect these variables and use Bucketeer for file storage.

### What to Store in Bucketeer

1. **Document Files**: All .docx files uploaded for world generation
2. **Generated Worlds**: Knowledge graphs and processed game data
3. **Game Saves**: Player progress and game state information
4. **LLM Models**: Local language models for offline use

## Scaling Your Application

Start with a basic Hobby dyno and scale up as needed:

```bash
# Upgrade to a Standard-1X dyno
heroku ps:scale web=1:standard-1x
```

## Monitoring

Monitor your application using Heroku's dashboard or add logging add-ons:

```bash
heroku addons:create papertrail:choklad
```

## Troubleshooting

View logs to diagnose issues:

```bash
heroku logs --tail
```
