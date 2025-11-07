"""
Secure Supabase Storage utilities with signed URLs and file validation
"""

from django.conf import settings
from supabase import create_client
from typing import Optional
import mimetypes
import logging

logger = logging.getLogger(__name__)


class SecureStorageService:
    """
    Service for secure file storage operations with Supabase
    """

    # Allowed file types and max sizes
    ALLOWED_IMAGE_TYPES = {
        "image/jpeg",
        "image/jpg",
        "image/png",
        "image/gif",
        "image/webp",
    }
    ALLOWED_DOCUMENT_TYPES = {
        "application/pdf",
        "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    }

    MAX_IMAGE_SIZE = 5 * 1024 * 1024  # 5 MB
    MAX_DOCUMENT_SIZE = 10 * 1024 * 1024  # 10 MB

    @classmethod
    def get_client(cls):
        """Get Supabase client"""
        return create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)

    @classmethod
    def validate_file(
        cls, file_obj, allowed_types: set, max_size: int
    ) -> tuple[bool, str]:
        """
        Validate file type and size

        Args:
            file_obj: File object to validate
            allowed_types: Set of allowed MIME types
            max_size: Maximum file size in bytes

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check file size
        if hasattr(file_obj, "size"):
            if file_obj.size > max_size:
                return (
                    False,
                    f"File size exceeds maximum of {max_size / (1024 * 1024):.1f} MB",
                )

        # Check file type
        if hasattr(file_obj, "content_type"):
            content_type = file_obj.content_type
        else:
            # Try to guess from filename
            content_type, _ = mimetypes.guess_type(file_obj.name)

        if content_type not in allowed_types:
            return False, f"File type '{content_type}' is not allowed"

        return True, ""

    @classmethod
    def validate_image(cls, image_file) -> tuple[bool, str]:
        """
        Validate image file

        Args:
            image_file: Image file object

        Returns:
            Tuple of (is_valid, error_message)
        """
        return cls.validate_file(
            image_file, cls.ALLOWED_IMAGE_TYPES, cls.MAX_IMAGE_SIZE
        )

    @classmethod
    def validate_document(cls, document_file) -> tuple[bool, str]:
        """
        Validate document file

        Args:
            document_file: Document file object

        Returns:
            Tuple of (is_valid, error_message)
        """
        return cls.validate_file(
            document_file, cls.ALLOWED_DOCUMENT_TYPES, cls.MAX_DOCUMENT_SIZE
        )

    @classmethod
    def generate_signed_url(
        cls, bucket: str, file_path: str, expires_in: int = 3600
    ) -> Optional[str]:
        """
        Generate short-lived signed URL for file access

        Args:
            bucket: Storage bucket name
            file_path: Path to file in bucket
            expires_in: URL expiry time in seconds (default 1 hour)

        Returns:
            Signed URL string or None if failed
        """
        try:
            client = cls.get_client()

            # Generate signed URL (expires in specified seconds)
            signed_url = client.storage.from_(bucket).create_signed_url(
                file_path, expires_in
            )

            if signed_url:
                return signed_url.get("signedURL")

            return None
        except Exception as e:
            logger.error(f"Failed to generate signed URL: {e}", exc_info=True)
            return None

    @classmethod
    def upload_file(
        cls, bucket: str, file_path: str, file_obj, validate_func=None
    ) -> tuple[bool, str]:
        """
        Upload file to Supabase storage with validation

        Args:
            bucket: Storage bucket name
            file_path: Destination path in bucket
            file_obj: File object to upload
            validate_func: Optional validation function

        Returns:
            Tuple of (success, message)
        """
        try:
            # Validate file if validation function provided
            if validate_func:
                is_valid, error_msg = validate_func(file_obj)
                if not is_valid:
                    return False, error_msg

            client = cls.get_client()

            # Read file content
            file_content = file_obj.read()

            # Upload file
            response = client.storage.from_(bucket).upload(file_path, file_content)

            return True, "File uploaded successfully"
        except Exception as e:
            logger.error(f"Failed to upload file: {e}", exc_info=True)
            return False, str(e)

    @classmethod
    def delete_file(cls, bucket: str, file_path: str) -> tuple[bool, str]:
        """
        Delete file from Supabase storage

        Args:
            bucket: Storage bucket name
            file_path: Path to file in bucket

        Returns:
            Tuple of (success, message)
        """
        try:
            client = cls.get_client()

            response = client.storage.from_(bucket).remove([file_path])

            return True, "File deleted successfully"
        except Exception as e:
            logger.error(f"Failed to delete file: {e}", exc_info=True)
            return False, str(e)
