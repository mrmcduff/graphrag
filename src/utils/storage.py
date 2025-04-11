"""
Storage utilities for GraphRAG.

This module provides a unified interface for file storage operations,
supporting both local filesystem and cloud storage (S3).
"""

import os
import logging
import boto3
from botocore.exceptions import ClientError
from urllib.parse import urlparse
import io

logger = logging.getLogger(__name__)

class StorageManager:
    """Storage manager for GraphRAG files."""

    def __init__(self):
        """Initialize the storage manager."""
        # Check for Bucketeer (Heroku add-on) first
        if os.environ.get("BUCKETEER_BUCKET_NAME"):
            self.s3_enabled = True
            self.s3_bucket = os.environ.get("BUCKETEER_BUCKET_NAME")
            self.s3_prefix = os.environ.get("BUCKETEER_PREFIX", "graphrag")
            
            try:
                self.s3_client = boto3.client(
                    's3',
                    aws_access_key_id=os.environ.get("BUCKETEER_AWS_ACCESS_KEY_ID"),
                    aws_secret_access_key=os.environ.get("BUCKETEER_AWS_SECRET_ACCESS_KEY"),
                    region_name=os.environ.get("BUCKETEER_AWS_REGION", "us-east-1")
                )
                logger.info(f"Bucketeer storage initialized with bucket: {self.s3_bucket}")
            except Exception as e:
                logger.error(f"Failed to initialize Bucketeer client: {e}")
                self.s3_enabled = False
        
        # Fall back to regular AWS S3 if Bucketeer is not available
        elif os.environ.get("AWS_S3_BUCKET"):
            self.s3_enabled = True
            self.s3_bucket = os.environ.get("AWS_S3_BUCKET")
            self.s3_prefix = os.environ.get("AWS_S3_PREFIX", "graphrag")
            
            try:
                self.s3_client = boto3.client(
                    's3',
                    aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID"),
                    aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY"),
                    region_name=os.environ.get("AWS_REGION", "us-east-1")
                )
                logger.info(f"S3 storage initialized with bucket: {self.s3_bucket}")
            except Exception as e:
                logger.error(f"Failed to initialize S3 client: {e}")
                self.s3_enabled = False
        else:
            self.s3_enabled = False
            self.s3_bucket = ""
            self.s3_prefix = "graphrag"
    
    def get_storage_path(self, path):
        """
        Get the appropriate storage path.
        
        Args:
            path: The relative path within the storage system
            
        Returns:
            Full path for storage operations
        """
        if self.s3_enabled:
            # For S3, combine the prefix with the path
            return f"{self.s3_prefix}/{path.lstrip('/')}"
        else:
            # For local storage, use the base directory
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            return os.path.join(base_dir, path)
    
    def save_file(self, file_path, content, binary=False):
        """
        Save a file to storage.
        
        Args:
            file_path: Relative path to save the file to
            content: File content (string or bytes)
            binary: Whether the content is binary
            
        Returns:
            Full path or URL to the saved file
        """
        if self.s3_enabled:
            s3_key = self.get_storage_path(file_path)
            try:
                if binary:
                    self.s3_client.put_object(
                        Bucket=self.s3_bucket,
                        Key=s3_key,
                        Body=content
                    )
                else:
                    self.s3_client.put_object(
                        Bucket=self.s3_bucket,
                        Key=s3_key,
                        Body=content.encode('utf-8') if isinstance(content, str) else content
                    )
                return f"s3://{self.s3_bucket}/{s3_key}"
            except ClientError as e:
                logger.error(f"Error saving file to S3: {e}")
                raise
        else:
            # Local file storage
            full_path = self.get_storage_path(file_path)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            
            mode = 'wb' if binary else 'w'
            with open(full_path, mode) as f:
                f.write(content)
            return full_path
    
    def read_file(self, file_path, binary=False):
        """
        Read a file from storage.
        
        Args:
            file_path: Path to the file to read
            binary: Whether to read as binary
            
        Returns:
            File content
        """
        # Check if it's an S3 URL
        if file_path.startswith('s3://'):
            if not self.s3_enabled:
                raise ValueError("S3 storage is not configured but an S3 URL was provided")
            
            parsed = urlparse(file_path)
            bucket = parsed.netloc
            key = parsed.path.lstrip('/')
            
            try:
                response = self.s3_client.get_object(Bucket=bucket, Key=key)
                if binary:
                    return response['Body'].read()
                else:
                    return response['Body'].read().decode('utf-8')
            except ClientError as e:
                logger.error(f"Error reading file from S3: {e}")
                raise
        
        elif self.s3_enabled and not os.path.isabs(file_path):
            # Relative path with S3 enabled
            s3_key = self.get_storage_path(file_path)
            try:
                response = self.s3_client.get_object(Bucket=self.s3_bucket, Key=s3_key)
                if binary:
                    return response['Body'].read()
                else:
                    return response['Body'].read().decode('utf-8')
            except ClientError as e:
                logger.error(f"Error reading file from S3: {e}")
                raise
        else:
            # Local file
            if not os.path.isabs(file_path):
                file_path = self.get_storage_path(file_path)
            
            mode = 'rb' if binary else 'r'
            with open(file_path, mode) as f:
                return f.read()
    
    def file_exists(self, file_path):
        """
        Check if a file exists in storage.
        
        Args:
            file_path: Path to the file to check
            
        Returns:
            True if the file exists, False otherwise
        """
        # Check if it's an S3 URL
        if file_path.startswith('s3://'):
            if not self.s3_enabled:
                return False
            
            parsed = urlparse(file_path)
            bucket = parsed.netloc
            key = parsed.path.lstrip('/')
            
            try:
                self.s3_client.head_object(Bucket=bucket, Key=key)
                return True
            except ClientError:
                return False
        
        elif self.s3_enabled and not os.path.isabs(file_path):
            # Relative path with S3 enabled
            s3_key = self.get_storage_path(file_path)
            try:
                self.s3_client.head_object(Bucket=self.s3_bucket, Key=s3_key)
                return True
            except ClientError:
                return False
        else:
            # Local file
            if not os.path.isabs(file_path):
                file_path = self.get_storage_path(file_path)
            return os.path.exists(file_path)
    
    def list_files(self, directory_path):
        """
        List files in a directory.
        
        Args:
            directory_path: Path to the directory to list
            
        Returns:
            List of file paths
        """
        if self.s3_enabled:
            s3_prefix = self.get_storage_path(directory_path)
            if not s3_prefix.endswith('/'):
                s3_prefix += '/'
                
            try:
                response = self.s3_client.list_objects_v2(
                    Bucket=self.s3_bucket,
                    Prefix=s3_prefix
                )
                
                if 'Contents' in response:
                    return [obj['Key'][len(s3_prefix):] for obj in response['Contents']]
                return []
            except ClientError as e:
                logger.error(f"Error listing files from S3: {e}")
                raise
        else:
            # Local directory
            full_path = self.get_storage_path(directory_path)
            if os.path.exists(full_path) and os.path.isdir(full_path):
                return os.listdir(full_path)
            return []
    
    def delete_file(self, file_path):
        """
        Delete a file from storage.
        
        Args:
            file_path: Path to the file to delete
            
        Returns:
            True if successful, False otherwise
        """
        if file_path.startswith('s3://'):
            if not self.s3_enabled:
                return False
            
            parsed = urlparse(file_path)
            bucket = parsed.netloc
            key = parsed.path.lstrip('/')
            
            try:
                self.s3_client.delete_object(Bucket=bucket, Key=key)
                return True
            except ClientError as e:
                logger.error(f"Error deleting file from S3: {e}")
                return False
        
        elif self.s3_enabled and not os.path.isabs(file_path):
            # Relative path with S3 enabled
            s3_key = self.get_storage_path(file_path)
            try:
                self.s3_client.delete_object(Bucket=self.s3_bucket, Key=s3_key)
                return True
            except ClientError as e:
                logger.error(f"Error deleting file from S3: {e}")
                return False
        else:
            # Local file
            if not os.path.isabs(file_path):
                file_path = self.get_storage_path(file_path)
            
            if os.path.exists(file_path):
                os.remove(file_path)
                return True
            return False

# Create a singleton instance
storage = StorageManager()
