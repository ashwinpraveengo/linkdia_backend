"""
File handling utilities for binary file storage in database
"""
import base64
import mimetypes
from typing import Optional, Dict, Any, Tuple
from django.core.exceptions import ValidationError
from django.http import HttpResponse
import magic


class FileValidator:
    """Validate file types and sizes"""
    
    ALLOWED_EXTENSIONS = {
        'image': ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp'],
        'document': ['pdf', 'doc', 'docx', 'txt', 'rtf'],
        'all': ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp', 'pdf', 'doc', 'docx', 'txt', 'rtf']
    }
    
    MAX_FILE_SIZES = {
        'image': 5 * 1024 * 1024,  # 5MB
        'document': 10 * 1024 * 1024,  # 10MB
        'profile_picture': 2 * 1024 * 1024,  # 2MB
    }
    
    @classmethod
    def validate_file(cls, file, file_type: str = 'all', max_size_key: str = 'document') -> Dict[str, Any]:
        """
        Validate uploaded file and return file metadata
        
        Args:
            file: The uploaded file object
            file_type: Type of file ('image', 'document', 'all')
            max_size_key: Key for max file size lookup
            
        Returns:
            Dict with file metadata
            
        Raises:
            ValidationError: If file is invalid
        """
        if not file:
            raise ValidationError("No file provided")
        
        # Read file data
        file_data = file.read()
        file_size = len(file_data)
        file_name = getattr(file, 'name', 'unknown')
        
        # Reset file pointer
        if hasattr(file, 'seek'):
            file.seek(0)
        
        # Get content type
        content_type = getattr(file, 'content_type', None)
        if not content_type:
            content_type, _ = mimetypes.guess_type(file_name)
        
        # Use python-magic for more accurate content type detection
        if not content_type:
            try:
                content_type = magic.from_buffer(file_data, mime=True)
            except:
                content_type = 'application/octet-stream'
        
        # Validate file extension
        file_extension = file_name.split('.')[-1].lower() if '.' in file_name else ''
        allowed_extensions = cls.ALLOWED_EXTENSIONS.get(file_type, cls.ALLOWED_EXTENSIONS['all'])
        
        if file_extension not in allowed_extensions:
            raise ValidationError(f"File type '{file_extension}' not allowed. Allowed types: {', '.join(allowed_extensions)}")
        
        # Validate file size
        max_size = cls.MAX_FILE_SIZES.get(max_size_key, cls.MAX_FILE_SIZES['document'])
        if file_size > max_size:
            raise ValidationError(f"File size {file_size} bytes exceeds maximum allowed size {max_size} bytes")
        
        # Additional validation for images
        if file_type == 'image':
            cls._validate_image(file_data, content_type)
        
        return {
            'data': file_data,
            'name': file_name,
            'content_type': content_type,
            'size': file_size,
            'extension': file_extension
        }
    
    @classmethod
    def _validate_image(cls, file_data: bytes, content_type: str) -> None:
        """Additional validation for image files"""
        try:
            from PIL import Image
            import io
            
            # Try to open the image to verify it's a valid image
            image = Image.open(io.BytesIO(file_data))
            image.verify()
            
            # Check image dimensions (optional)
            image = Image.open(io.BytesIO(file_data))
            width, height = image.size
            
            # Set reasonable limits
            max_dimension = 4000
            if width > max_dimension or height > max_dimension:
                raise ValidationError(f"Image dimensions {width}x{height} exceed maximum allowed {max_dimension}x{max_dimension}")
                
        except ImportError:
            # PIL not available, skip image validation
            pass
        except Exception as e:
            raise ValidationError(f"Invalid image file: {str(e)}")


class FileStorageHandler:
    """Handle file storage operations for binary fields"""
    
    @staticmethod
    def store_file(file, file_type: str = 'all', max_size_key: str = 'document') -> Dict[str, Any]:
        """
        Store file as binary data
        
        Args:
            file: The uploaded file object
            file_type: Type of file validation to perform
            max_size_key: Maximum size validation key
            
        Returns:
            Dict with fields to save to model
        """
        file_metadata = FileValidator.validate_file(file, file_type, max_size_key)
        
        return {
            'data': file_metadata['data'],
            'name': file_metadata['name'],
            'content_type': file_metadata['content_type'],
            'size': file_metadata['size']
        }
    
    @staticmethod
    def get_file_response(file_data: bytes, file_name: str, content_type: str) -> HttpResponse:
        """
        Create HTTP response for file download
        
        Args:
            file_data: Binary file data
            file_name: Name of the file
            content_type: MIME content type
            
        Returns:
            HttpResponse with file data
        """
        response = HttpResponse(file_data, content_type=content_type)
        response['Content-Disposition'] = f'attachment; filename="{file_name}"'
        response['Content-Length'] = len(file_data)
        return response
    
    @staticmethod
    def get_base64_data_url(file_data: bytes, content_type: str) -> str:
        """
        Convert file data to base64 data URL
        
        Args:
            file_data: Binary file data
            content_type: MIME content type
            
        Returns:
            Base64 data URL string
        """
        if not file_data:
            return ""
        
        base64_data = base64.b64encode(file_data).decode('utf-8')
        return f"data:{content_type};base64,{base64_data}"
    
    @staticmethod
    def get_file_info(instance, field_prefix: str) -> Optional[Dict[str, Any]]:
        """
        Get file information from model instance
        
        Args:
            instance: Model instance
            field_prefix: Prefix for file fields (e.g., 'profile_picture', 'document')
            
        Returns:
            Dict with file info or None if no file
        """
        data_field = f"{field_prefix}_data"
        name_field = f"{field_prefix}_name"
        content_type_field = f"{field_prefix}_content_type"
        size_field = f"{field_prefix}_size"
        
        file_data = getattr(instance, data_field, None)
        if not file_data:
            return None
        
        return {
            'data': file_data,
            'name': getattr(instance, name_field, ''),
            'content_type': getattr(instance, content_type_field, ''),
            'size': getattr(instance, size_field, 0),
            'base64_url': FileStorageHandler.get_base64_data_url(
                file_data, 
                getattr(instance, content_type_field, '')
            )
        }


def process_uploaded_file(uploaded_file, file_type='all', max_size_key='document'):
    """
    Process uploaded file and return file data
    
    Args:
        uploaded_file: The uploaded file object
        file_type: Type of file validation
        max_size_key: Maximum size validation key
        
    Returns:
        Dict with file data: {'data': bytes, 'name': str, 'content_type': str, 'size': int}
    """
    if not uploaded_file:
        raise ValidationError("No file provided")
    
    # Read file data
    file_data = uploaded_file.read()
    file_size = len(file_data)
    file_name = getattr(uploaded_file, 'name', 'unknown')
    
    # Get content type
    content_type, _ = mimetypes.guess_type(file_name)
    if not content_type:
        try:
            content_type = magic.from_buffer(file_data, mime=True)
        except:
            content_type = 'application/octet-stream'
    
    # Basic validation
    max_size = FileValidator.MAX_FILE_SIZES.get(max_size_key, 10 * 1024 * 1024)  # 10MB default
    if file_size > max_size:
        raise ValidationError(f"File size {file_size} exceeds maximum allowed size {max_size}")
    
    return {
        'data': file_data,
        'name': file_name,
        'content_type': content_type,
        'size': file_size
    }


def process_uploaded_file(uploaded_file, file_type='all', max_size_key='document'):
    """
    Process uploaded file and return file data for storage
    
    Args:
        uploaded_file: The uploaded file object
        file_type: Type of file ('image', 'document', 'all')
        max_size_key: Key for max file size lookup
    
    Returns:
        Dict with file data for database storage
    """
    return FileStorageHandler.store_file(uploaded_file, file_type, max_size_key)


class FileUploadMixin:
    """Mixin for GraphQL mutations to handle file uploads"""
    
    def handle_file_upload(self, file, field_prefix: str, instance, file_type: str = 'all', max_size_key: str = 'document'):
        """
        Handle file upload and update model instance
        
        Args:
            file: Uploaded file object
            field_prefix: Prefix for model fields
            instance: Model instance to update
            file_type: Type of file validation
            max_size_key: Maximum size validation key
        """
        if file is None:
            return
        
        file_data = FileStorageHandler.store_file(file, file_type, max_size_key)
        
        # Update instance fields
        setattr(instance, f"{field_prefix}_data", file_data['data'])
        setattr(instance, f"{field_prefix}_name", file_data['name'])
        setattr(instance, f"{field_prefix}_content_type", file_data['content_type'])
        setattr(instance, f"{field_prefix}_size", file_data['size'])
    
    def clear_file_fields(self, instance, field_prefix: str):
        """Clear file fields from model instance"""
        setattr(instance, f"{field_prefix}_data", None)
        setattr(instance, f"{field_prefix}_name", None)
        setattr(instance, f"{field_prefix}_content_type", None)
        setattr(instance, f"{field_prefix}_size", None)


def process_uploaded_file(file, file_type='all', max_size_key='document'):
    """
    Process uploaded file and return file data dictionary
    
    Args:
        file: Uploaded file object
        file_type: Type of file validation
        max_size_key: Maximum size validation key
        
    Returns:
        Dict with file data: {data, name, content_type, size}
        
    Raises:
        ValidationError: If file is invalid
    """
    if not file:
        raise ValidationError("No file provided")
    
    # Validate file
    file_info = FileValidator.validate_file(file, file_type, max_size_key)
    
    # Store file
    return FileStorageHandler.store_file(file, file_type, max_size_key)
