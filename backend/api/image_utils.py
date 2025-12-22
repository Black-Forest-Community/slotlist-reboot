"""
Utility functions for downloading and storing images from external URLs.
"""
import requests
from typing import Optional
from urllib.parse import urlparse
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.conf import settings
import os


def download_and_store_image(url: str, path_prefix: str = '') -> Optional[str]:
    """
    Download an image from a URL and store it in the configured storage backend.
    
    Args:
        url: URL of the image to download
        path_prefix: Optional prefix for the storage path (e.g., 'missions/', 'communities/')
        
    Returns:
        Full URL to stored file or None if download fails
    """
    if not url:
        return None
    
    try:
        # Download image
        response = requests.get(url, timeout=30, stream=True)
        response.raise_for_status()
        
        # Get filename from URL
        parsed_url = urlparse(url)
        original_filename = os.path.basename(parsed_url.path)
        
        # Ensure we have a filename
        if not original_filename or '.' not in original_filename:
            # Try to get extension from content-type
            content_type = response.headers.get('content-type', '')
            ext = 'jpg'  # default
            if 'png' in content_type:
                ext = 'png'
            elif 'jpeg' in content_type or 'jpg' in content_type:
                ext = 'jpg'
            elif 'gif' in content_type:
                ext = 'gif'
            elif 'webp' in content_type:
                ext = 'webp'
            original_filename = f'image.{ext}'
        
        # Create storage path
        storage_path = os.path.join(path_prefix, original_filename)
        
        # Save to storage
        file_content = ContentFile(response.content)
        saved_path = default_storage.save(storage_path, file_content)
        
        # Return the full URL (with request context if available)
        file_url = default_storage.url(saved_path)
        
        # If URL is relative, make it absolute
        if file_url.startswith('/'):
            # In production, use settings for base URL
            base_url = getattr(settings, 'BACKEND_URL', 'http://localhost:8022')
            file_url = f'{base_url}{file_url}'
        
        return file_url
        
    except Exception as e:
        print(f"Failed to download image from {url}: {e}")
        return None
