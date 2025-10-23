"""
Supabase diagnostic and utility views for testing integration.

These views help verify Supabase Auth and Storage integration.
"""

from typing import Any
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
from configs.config import Config
from configs.supabase_storage import (
    SupabaseStorage,
    upload_product_image,
    upload_rider_document,
)
from django.utils.timezone import now


@api_view(["GET"])
@permission_classes([AllowAny])
def supabase_health_check(request) -> Response:
    """
    Health check endpoint to verify Supabase integration status.

    GET /api/supabase/health/

    Returns status of:
    - Configuration
    - JWT verification capability
    - Storage connection
    - Database connection
    """
    health_status: dict[str, str | bool | dict[Any, Any]] = {
        "timestamp": now().isoformat(),
        "supabase_configured": False,
        "jwt_secret_configured": False,
        "storage_configured": False,
        "database_type": "local",
        "checks": {},
    }

    # Check configuration
    if (
        Config.SUPABASE_URL
        and Config.SUPABASE_URL != "https://your-project-id.supabase.co"
    ):
        health_status["supabase_configured"] = True
        health_status["checks"]["supabase_url"] = "OK"
    else:
        health_status["checks"]["supabase_url"] = "Not configured"

    if (
        Config.SUPABASE_JWT_SECRET
        and Config.SUPABASE_JWT_SECRET != "your-jwt-secret-here"
    ):
        health_status["jwt_secret_configured"] = True
        health_status["checks"]["jwt_secret"] = "OK"
    else:
        health_status["checks"]["jwt_secret"] = "Not configured"

    if (
        Config.SUPABASE_SERVICE_KEY
        and Config.SUPABASE_SERVICE_KEY != "your-service-role-key-here"
    ):
        health_status["storage_configured"] = True
        health_status["checks"]["storage_key"] = "OK"
    else:
        health_status["checks"]["storage_key"] = "Not configured"

    # Check database type
    if settings.USE_SUPABASE_DB:
        health_status["database_type"] = "supabase_managed"
        health_status["checks"]["database"] = f"Supabase ({Config.SUPABASE_DB_HOST})"
    else:
        health_status["database_type"] = "local"
        health_status["checks"]["database"] = f"Local ({Config.DB_HOST})"

    # Overall status
    health_status["status"] = (
        "healthy"
        if (
            health_status["supabase_configured"]
            and health_status["jwt_secret_configured"]
        )
        else "degraded"
    )

    return Response(health_status, status=status.HTTP_200_OK)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def verify_token(request) -> Response:
    """
    Verify the current user's Supabase JWT token.

    GET /api/supabase/verify-token/
    Authorization: Bearer <supabase_jwt>

    Returns:
    - User information
    - Token validity
    - Django user linkage
    """
    user = request.user

    return Response(
        {
            "authenticated": True,
            "user": {
                "id": user.id,
                "phone_number": user.phone_number,
                "email": user.email,
                "role": user.role,
                "supabase_uid": user.supabase_uid,
                "is_verified": user.is_verified,
            },
            "auth_method": "supabase_jwt" if user.supabase_uid else "django_token",
            "message": "Token is valid",
        },
        status=status.HTTP_200_OK,
    )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def upload_file(request) -> Response:
    """
    Example endpoint for uploading files to Supabase Storage.

    POST /api/supabase/upload/
    Authorization: Bearer <token>
    Content-Type: multipart/form-data

    Body:
    - file: The file to upload
    - bucket: Bucket name (optional, default: 'uploads')
    - folder: Folder path within bucket (optional)

    Returns:
    - Upload status
    - Public URL of uploaded file
    """
    if "file" not in request.FILES:
        return Response(
            {"error": "No file provided"}, status=status.HTTP_400_BAD_REQUEST
        )

    uploaded_file = request.FILES["file"]
    bucket_name = request.data.get("bucket", "uploads")
    folder = request.data.get("folder", "")

    # Construct file path
    user_id = request.user.id
    file_path = (
        f"{folder}/{user_id}/{uploaded_file.name}"
        if folder
        else f"{user_id}/{uploaded_file.name}"
    )

    try:
        # Upload to Supabase Storage
        result = SupabaseStorage.upload_django_file(
            bucket_name=bucket_name,
            file_path=file_path,
            django_file=uploaded_file,
            upsert=True,
        )

        if result["success"]:
            return Response(
                {
                    "success": True,
                    "message": "File uploaded successfully",
                    "file": {
                        "path": result["path"],
                        "url": result["url"],
                        "bucket": result["bucket"],
                        "size": uploaded_file.size,
                        "content_type": uploaded_file.content_type,
                    },
                },
                status=status.HTTP_201_CREATED,
            )
        else:
            return Response(
                {"success": False, "error": result.get("error", "Upload failed")},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    except Exception as e:
        return Response(
            {"success": False, "error": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def upload_product_image_view(request) -> Response:
    """
    Upload product image to Supabase Storage.

    POST /api/supabase/upload-product-image/
    Authorization: Bearer <token>

    Body:
    - image: Image file
    - product_id: Product/Item ID
    - warehouse_id: Warehouse ID (optional)
    """
    if "image" not in request.FILES:
        return Response(
            {"error": "No image provided"}, status=status.HTTP_400_BAD_REQUEST
        )

    product_id = request.data.get("product_id")
    warehouse_id = request.data.get("warehouse_id")

    if not product_id:
        return Response(
            {"error": "product_id is required"}, status=status.HTTP_400_BAD_REQUEST
        )

    try:
        result: dict[str, Any] = upload_product_image(
            product_id=int(product_id),
            image_file=request.FILES["image"],
            warehouse_id=int(warehouse_id) if warehouse_id else None,
        )

        if result["success"]:
            return Response(
                {
                    "success": True,
                    "message": "Product image uploaded",
                    "url": result["url"],
                    "path": result["path"],
                },
                status=status.HTTP_201_CREATED,
            )
        else:
            return Response(
                {"success": False, "error": result.get("error")},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def upload_rider_document_view(request) -> Response:
    """
    Upload rider document to Supabase Storage.

    POST /api/supabase/upload-rider-document/
    Authorization: Bearer <token>

    Body:
    - document: Document file (PDF, image, etc.)
    - doc_type: Document type (license, id_proof, etc.)
    """
    if "document" not in request.FILES:
        return Response(
            {"error": "No document provided"}, status=status.HTTP_400_BAD_REQUEST
        )

    doc_type = request.data.get("doc_type", "document")
    rider_id = request.user.id

    try:
        result = upload_rider_document(
            rider_id=rider_id, doc_file=request.FILES["document"], doc_type=doc_type
        )

        if result["success"]:
            return Response(
                {
                    "success": True,
                    "message": f"Rider {doc_type} uploaded",
                    "url": result["url"],
                    "path": result["path"],
                },
                status=status.HTTP_201_CREATED,
            )
        else:
            return Response(
                {"success": False, "error": result.get("error")},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
