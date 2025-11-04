"""
Supabase Storage Integration for Django

This module provides utilities for uploading and fetching files from Supabase Storage.
Supports product images, rider documents, and other media files.
"""

import mimetypes
from typing import Optional, Dict, Any
from supabase import create_client, Client
from core.config import Config


class SupabaseStorage:
    """
    Wrapper for Supabase Storage operations.

    Features:
    - Upload files to Supabase Storage buckets
    - Generate public/signed URLs for files
    - Delete files from storage
    - List files in a bucket
    """

    _client: Optional[Client] = None

    @classmethod
    def get_client(cls) -> Client:
        """Get or create Supabase client instance (singleton pattern)."""
        if cls._client is None:
            if not Config.SUPABASE_URL or not Config.SUPABASE_SERVICE_KEY:
                raise ValueError(
                    "SUPABASE_URL and SUPABASE_SERVICE_KEY must be configured in .env"
                )
            cls._client = create_client(
                Config.SUPABASE_URL, Config.SUPABASE_SERVICE_KEY
            )
        return cls._client

    @classmethod
    def upload_file(
        cls,
        bucket_name: str,
        file_path: str,
        file_data: bytes,
        content_type: Optional[str] = None,
        upsert: bool = False,
    ) -> Dict[str, Any]:
        """
        Upload a file to Supabase Storage.

        Args:
            bucket_name: Name of the storage bucket (e.g., 'product-images', 'rider-docs')
            file_path: Path within the bucket (e.g., 'warehouse1/item123.jpg')
            file_data: Binary file data
            content_type: MIME type (auto-detected if None)
            upsert: Whether to overwrite existing file

        Returns:
            Dict with 'path', 'url', and other metadata

        Example:
            >>> with open('image.jpg', 'rb') as f:
            >>>     result = SupabaseStorage.upload_file(
            >>>         'product-images',
            >>>         'warehouse1/item123.jpg',
            >>>         f.read()
            >>>     )
            >>> print(result['url'])
        """
        client = cls.get_client()

        # Auto-detect content type if not provided
        if content_type is None:
            content_type, _ = mimetypes.guess_type(file_path)
            if content_type is None:
                content_type = "application/octet-stream"

        try:
            # Upload file to bucket
            response = client.storage.from_(bucket_name).upload(
                path=file_path,
                file=file_data,
                file_options={
                    "content-type": content_type,
                    "upsert": str(upsert).lower(),
                },
            )

            # Get public URL for the uploaded file
            public_url = cls.get_public_url(bucket_name, file_path)

            return {
                "success": True,
                "path": file_path,
                "url": public_url,
                "bucket": bucket_name,
                "content_type": content_type,
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "path": file_path,
                "bucket": bucket_name,
            }

    @classmethod
    def upload_django_file(
        cls, bucket_name: str, file_path: str, django_file, upsert: bool = False
    ) -> Dict[str, Any]:
        """
        Upload a Django UploadedFile to Supabase Storage.

        Args:
            bucket_name: Name of the storage bucket
            file_path: Path within the bucket
            django_file: Django UploadedFile object from request.FILES
            upsert: Whether to overwrite existing file

        Returns:
            Dict with upload result

        Example:
            >>> # In a DRF view
            >>> file = request.FILES.get('image')
            >>> result = SupabaseStorage.upload_django_file(
            >>>     'product-images',
            >>>     f'products/{file.name}',
            >>>     file
            >>> )
        """
        file_data = django_file.read()
        content_type = django_file.content_type

        return cls.upload_file(bucket_name, file_path, file_data, content_type, upsert)

    @classmethod
    def get_public_url(cls, bucket_name: str, file_path: str) -> str:
        """
        Get public URL for a file in a public bucket.

        Args:
            bucket_name: Name of the storage bucket
            file_path: Path to the file within the bucket

        Returns:
            Public URL string
        """
        client = cls.get_client()
        return client.storage.from_(bucket_name).get_public_url(file_path)

    @classmethod
    def create_signed_url(
        cls, bucket_name: str, file_path: str, expires_in: int = 36000
    ) -> Dict[str, Any]:
        """
        Create a signed URL for private files (expires after specified time).

        Args:
            bucket_name: Name of the storage bucket
            file_path: Path to the file within the bucket
            expires_in: URL expiration time in seconds (default: 1 hour)

        Returns:
            Dict with 'signedURL' and other metadata
        """
        client = cls.get_client()

        try:
            response = client.storage.from_(bucket_name).create_signed_url(
                file_path, expires_in
            )
            return {
                "success": True,
                "signedURL": response.get("signedURL"),
                "path": file_path,
                "expires_in": expires_in,
            }
        except Exception as e:
            return {"success": False, "error": str(e), "path": file_path}

    @classmethod
    def delete_file(cls, bucket_name: str, file_path: str) -> Dict[str, Any]:
        """
        Delete a file from Supabase Storage.

        Args:
            bucket_name: Name of the storage bucket
            file_path: Path to the file within the bucket

        Returns:
            Dict with deletion result
        """
        client = cls.get_client()

        try:
            response = client.storage.from_(bucket_name).remove([file_path])
            return {"success": True, "path": file_path, "bucket": bucket_name}
        except Exception as e:
            return {"success": False, "error": str(e), "path": file_path}

    @classmethod
    def list_files(cls, bucket_name: str, path: str = "") -> Dict[str, Any]:
        """
        List files in a bucket or folder.

        Args:
            bucket_name: Name of the storage bucket
            path: Folder path within the bucket (empty string for root)

        Returns:
            Dict with list of files
        """
        client = cls.get_client()

        try:
            response = client.storage.from_(bucket_name).list(path)
            return {
                "success": True,
                "files": response,
                "bucket": bucket_name,
                "path": path,
            }
        except Exception as e:
            return {"success": False, "error": str(e), "bucket": bucket_name}

    @classmethod
    def create_bucket(cls, bucket_name: str, public: bool = True) -> Dict[str, Any]:
        """
        Create a new storage bucket.

        Args:
            bucket_name: Name for the new bucket
            public: Whether the bucket should be publicly accessible

        Returns:
            Dict with creation result
        """
        client = cls.get_client()

        try:
            response = client.storage.create_bucket(
                bucket_name, options={"public": public}
            )
            return {"success": True, "bucket": bucket_name, "public": public}
        except Exception as e:
            return {"success": False, "error": str(e), "bucket": bucket_name}


# Convenience functions for common use cases


def upload_product_image(
    product_id: int, image_file, warehouse_id: int = None
) -> Dict[str, Any]:
    """Upload a product image to the 'product-images' bucket."""
    filename = (
        f"warehouse_{warehouse_id}/product_{product_id}/{image_file.name}"
        if warehouse_id
        else f"product_{product_id}/{image_file.name}"
    )
    return SupabaseStorage.upload_django_file(
        "product-images", filename, image_file, upsert=True
    )


def upload_rider_document(
    rider_id: int, doc_file, doc_type: str = "license"
) -> Dict[str, Any]:
    """Upload a rider document to the 'rider-documents' bucket."""
    filename = f"rider_{rider_id}/{doc_type}_{doc_file.name}"
    return SupabaseStorage.upload_django_file(
        "rider-documents", filename, doc_file, upsert=True
    )


def upload_warehouse_image(warehouse_id: int, image_file) -> Dict[str, Any]:
    """Upload a warehouse image to the 'warehouse-images' bucket."""
    filename = f"warehouse_{warehouse_id}/{image_file.name}"
    return SupabaseStorage.upload_django_file(
        "warehouse-images", filename, image_file, upsert=True
    )
