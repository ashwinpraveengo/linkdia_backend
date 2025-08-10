import graphene
from graphene_django import DjangoObjectType
from graphene_file_upload.scalars import Upload
from core.models import (
    CustomUser, 
    ProfessionalProfile, 
    ClientProfile, 
    PasswordResetToken
)
from core.types.file_types import FileInfoType


class UserType(DjangoObjectType):
    """GraphQL type for CustomUser model"""
    full_name = graphene.String()
    fullName = graphene.String()  # Add camelCase alias
    firstName = graphene.String()  # Add camelCase alias for first_name
    lastName = graphene.String()   # Add camelCase alias for last_name
    is_professional = graphene.Boolean()
    is_client = graphene.Boolean()
    profile_picture = graphene.Field(FileInfoType)
    profilePictureData = graphene.String()    # Use only camelCase version
    
    class Meta:
        model = CustomUser
        fields = (
            'id', 'email', 'first_name', 'last_name', 'user_type', 
            'is_active', 'date_joined', 'phone_number', 
            'is_email_verified', 'google_id', 'is_google_user',
            # Don't include profile_picture_data in fields - handle via resolver only
            'profile_picture_name', 'profile_picture_content_type', 'profile_picture_size'
        )

    def resolve_full_name(self, info):
        return self.full_name
    
    def resolve_fullName(self, info):
        return self.full_name
    
    def resolve_firstName(self, info):
        return self.first_name
    
    def resolve_lastName(self, info):
        return self.last_name
    
    def resolve_is_professional(self, info):
        return self.is_professional
    
    def resolve_is_client(self, info):
        return self.is_client
    
    def resolve_profile_picture(self, info):
        return FileInfoType.from_instance(self, 'profile_picture')
    
    def resolve_profilePictureData(self, info):
        # Return base64 encoded image data if exists
        if hasattr(self, 'profile_picture_data') and self.profile_picture_data:
            import base64
            return base64.b64encode(self.profile_picture_data).decode('utf-8')
        return None


class ClientProfileType(DjangoObjectType):
    """GraphQL type for ClientProfile model"""
    user_full_name = graphene.String()
    
    class Meta:
        model = ClientProfile
        fields = (
            'id', 'user', 'company_name', 'bio', 'location',
            'created_at', 'updated_at'
        )
    
    def resolve_user_full_name(self, info):
        return self.user.full_name


class PasswordResetTokenType(DjangoObjectType):
    """GraphQL type for PasswordResetToken model"""
    is_expired = graphene.Boolean()
    
    class Meta:
        model = PasswordResetToken
        fields = ('id', 'user', 'token', 'created_at', 'is_used')
    
    def resolve_is_expired(self, info):
        return self.is_expired()


# Input Types for mutations
class UserInputType(graphene.InputObjectType):
    """Input type for user creation/updates"""
    email = graphene.String()
    first_name = graphene.String()
    last_name = graphene.String()
    user_type = graphene.String()
    phone_number = graphene.String()
    profile_picture = Upload()


class ClientProfileInputType(graphene.InputObjectType):
    """Input type for client profile updates"""
    company_name = graphene.String()
    bio = graphene.String()
    location = graphene.String()


class ProfessionalProfileInputType(graphene.InputObjectType):
    """Input type for professional profile updates"""
    area_of_expertise = graphene.String()
    years_of_experience = graphene.Int()
    bio_introduction = graphene.String()
    location = graphene.String()