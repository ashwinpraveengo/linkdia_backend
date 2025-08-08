"""
GraphQL types and scalars for file handling
"""
import graphene
from graphene import ObjectType, String, Int, Boolean
from graphene.types.generic import GenericScalar
from core.utils.file_handlers import FileStorageHandler


class FileInfoType(ObjectType):
    """GraphQL type for file information"""
    name = String(description="Original filename")
    content_type = String(description="MIME content type")
    size = Int(description="File size in bytes")
    base64_url = String(description="Base64 encoded data URL")
    
    @staticmethod
    def from_instance(instance, field_prefix: str):
        """Create FileInfoType from model instance"""
        file_info = FileStorageHandler.get_file_info(instance, field_prefix)
        if not file_info:
            return None
        
        return FileInfoType(
            name=file_info['name'],
            content_type=file_info['content_type'],
            size=file_info['size'],
            base64_url=file_info['base64_url']
        )


class FileDownloadType(ObjectType):
    """GraphQL type for file download information"""
    download_url = String(description="URL to download the file")
    filename = String(description="Original filename")
    content_type = String(description="MIME content type")
    size = Int(description="File size in bytes")


class FileUploadResponse(ObjectType):
    """Response type for file upload mutations"""
    success = Boolean(description="Whether the upload was successful")
    message = String(description="Success or error message")
    file_info = graphene.Field(FileInfoType, description="Information about the uploaded file")
    errors = graphene.List(String, description="List of validation errors")


# Custom scalar types
class Base64FileInput(graphene.InputObjectType):
    """Input type for base64 encoded file data"""
    filename = String(required=True, description="Original filename")
    content_type = String(required=True, description="MIME content type")
    data = String(required=True, description="Base64 encoded file data")


class FileMetadata(graphene.ObjectType):
    """Metadata about a file without the actual data"""
    name = String()
    content_type = String()
    size = Int()
    uploaded_at = graphene.DateTime()
    
    def __init__(self, name=None, content_type=None, size=None, uploaded_at=None):
        self.name = name
        self.content_type = content_type
        self.size = size
        self.uploaded_at = uploaded_at
