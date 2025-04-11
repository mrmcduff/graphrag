# Using S3 Storage with GraphRAG on Heroku

This guide explains how to configure and use Amazon S3 for file storage with your GraphRAG application on Heroku.

## Why S3 Storage?

Heroku has an ephemeral filesystem, meaning any files written to the filesystem will be lost when the dyno restarts. For GraphRAG, you need persistent storage for:

1. Document files (.docx)
2. Generated knowledge graphs
3. Game state saves
4. Local LLM models

## Setting Up S3

### 1. Create an AWS Account

If you don't already have one, create an account at [aws.amazon.com](https://aws.amazon.com/).

### 2. Create an S3 Bucket

1. Go to the S3 service in the AWS Console
2. Click "Create bucket"
3. Choose a globally unique name (e.g., "graphrag-files")
4. Select your preferred region
5. Configure other settings as needed (default settings are fine for starting)
6. Create the bucket

### 3. Create IAM Credentials

1. Go to the IAM service in the AWS Console
2. Create a new policy with the following permissions:
   ```json
   {
     "Version": "2012-10-17",
     "Statement": [
       {
         "Effect": "Allow",
         "Action": [
           "s3:PutObject",
           "s3:GetObject",
           "s3:DeleteObject",
           "s3:ListBucket"
         ],
         "Resource": [
           "arn:aws:s3:::YOUR-BUCKET-NAME",
           "arn:aws:s3:::YOUR-BUCKET-NAME/*"
         ]
       }
     ]
   }
   ```
3. Create a new IAM user with programmatic access
4. Attach the policy you created to this user
5. Save the Access Key ID and Secret Access Key

### 4. Configure Heroku Environment Variables

```bash
heroku config:set AWS_ACCESS_KEY_ID=your_access_key_id
heroku config:set AWS_SECRET_ACCESS_KEY=your_secret_access_key
heroku config:set AWS_REGION=your_bucket_region
heroku config:set AWS_S3_BUCKET=your_bucket_name
heroku config:set AWS_S3_PREFIX=graphrag
```

## Using the Storage Manager

The `StorageManager` class has been added to your project to provide a unified interface for file operations, automatically using S3 when configured or falling back to local storage.

### Example Usage

```python
from src.utils.storage import storage

# Save a file
content = "This is a test file"
path = storage.save_file("data/documents/test.txt", content)

# Read a file
content = storage.read_file("data/documents/test.txt")

# Check if a file exists
exists = storage.file_exists("data/documents/test.txt")

# List files in a directory
files = storage.list_files("data/documents")

# Delete a file
storage.delete_file("data/documents/test.txt")
```

## Local Development

For local development, the storage manager will use your local filesystem if AWS environment variables are not set.

To test S3 storage locally:

1. Create a `.env` file in your project root with your AWS credentials
2. The storage manager will automatically use S3 if the AWS_S3_BUCKET variable is set

## LLM Models on Heroku

For local LLM support on Heroku:

1. Upload your models to S3 using the AWS console or CLI
2. Set the environment variable to point to the S3 location:
   ```bash
   heroku config:set LLM_MODELS_PATH=s3://your-bucket-name/graphrag/models/llm
   ```

## Limitations and Considerations

1. **Heroku Slug Size**: Heroku has a 500MB slug size limit. Large LLM models should be stored in S3 and downloaded at runtime if needed.

2. **Cost Management**: S3 charges for storage and data transfer. Monitor your usage to avoid unexpected costs.

3. **Performance**: Accessing files in S3 will be slower than local filesystem access. Consider caching frequently accessed files.

4. **Security**: Ensure your S3 bucket has appropriate security settings and that your IAM user has only the necessary permissions.
