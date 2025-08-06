import graphene
from graphene_django import DjangoObjectType
from django.contrib.auth import authenticate
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
import requests
import jwt
from datetime import datetime, timedelta

from core.models import CustomUser, PasswordResetToken, ProfessionalProfile, ClientProfile


class UserType(DjangoObjectType):
    full_name = graphene.String()
    
    class Meta:
        model = CustomUser
        fields = ('id', 'email', 'first_name', 'last_name', 'user_type', 'is_active', 
                 'date_joined', 'profile_picture', 'phone_number', 'is_email_verified')

    def resolve_full_name(self, info):
        return self.full_name


class AuthPayload(graphene.ObjectType):
    success = graphene.Boolean()
    message = graphene.String()
    user = graphene.Field(UserType)
    access_token = graphene.String()
    refresh_token = graphene.String()


class SignUpMutation(graphene.Mutation):
    class Arguments:
        email = graphene.String(required=True)
        password = graphene.String(required=True)
        user_type = graphene.String(required=True)  
        first_name = graphene.String()
        last_name = graphene.String()
        phone_number = graphene.String()

    Output = AuthPayload

    def mutate(self, info, email, password, user_type, first_name=None, last_name=None, phone_number=None):
        try:
            # Validate user_type
            if user_type not in ['PROFESSIONAL', 'CLIENT']:
                return AuthPayload(
                    success=False,
                    message="user_type must be either 'PROFESSIONAL' or 'CLIENT'"
                )

            # Check if user already exists
            if CustomUser.objects.filter(email=email).exists():
                return AuthPayload(
                    success=False,
                    message="User with this email already exists"
                )

            # Validate password
            try:
                validate_password(password)
            except ValidationError as e:
                return AuthPayload(
                    success=False,
                    message=str(e.messages[0])
                )

            # Create user
            user = CustomUser.objects.create_user(
                email=email,
                password=password,
                first_name=first_name or '',
                last_name=last_name or '',
                phone_number=phone_number,
                user_type=user_type
            )

            # Create corresponding profile based on user type
            if user_type == 'PROFESSIONAL':
                ProfessionalProfile.objects.create(user=user)
            elif user_type == 'CLIENT':
                ClientProfile.objects.create(user=user)

            # Generate JWT tokens
            from rest_framework_simplejwt.tokens import RefreshToken
            refresh = RefreshToken.for_user(user)
            access_token = str(refresh.access_token)
            refresh_token = str(refresh)

            return AuthPayload(
                success=True,
                message="User created successfully",
                user=user,
                access_token=access_token,
                refresh_token=refresh_token
            )

        except Exception as e:
            return AuthPayload(
                success=False,
                message=f"An error occurred: {str(e)}"
            )


class LoginMutation(graphene.Mutation):
    class Arguments:
        email = graphene.String(required=True)
        password = graphene.String(required=True)

    Output = AuthPayload

    def mutate(self, info, email, password):
        try:
            user = authenticate(email=email, password=password)
            
            if user is None:
                return AuthPayload(
                    success=False,
                    message="Invalid email or password"
                )

            if not user.is_active:
                return AuthPayload(
                    success=False,
                    message="Account is deactivated"
                )

            # Generate JWT tokens
            from rest_framework_simplejwt.tokens import RefreshToken
            refresh = RefreshToken.for_user(user)
            access_token = str(refresh.access_token)
            refresh_token = str(refresh)

            return AuthPayload(
                success=True,
                message="Login successful",
                user=user,
                access_token=access_token,
                refresh_token=refresh_token
            )

        except Exception as e:
            return AuthPayload(
                success=False,
                message=f"An error occurred: {str(e)}"
            )


class ForgotPasswordMutation(graphene.Mutation):
    class Arguments:
        email = graphene.String(required=True)

    success = graphene.Boolean()
    message = graphene.String()

    def mutate(self, info, email):
        try:
            user = CustomUser.objects.get(email=email)
            
            # Create password reset token
            reset_token = PasswordResetToken.objects.create(user=user)
            
            # Send reset email
            reset_link = f"http://localhost:3000/reset-password?token={reset_token.token}"
            
            send_mail(
                'Password Reset Request',
                f'Click the following link to reset your password: {reset_link}',
                settings.DEFAULT_FROM_EMAIL,
                [email],
                fail_silently=False,
            )

            return ForgotPasswordMutation(
                success=True,
                message="Password reset link has been sent to your email"
            )

        except CustomUser.DoesNotExist:
            return ForgotPasswordMutation(
                success=False,
                message="User with this email does not exist"
            )
        except Exception as e:
            return ForgotPasswordMutation(
                success=False,
                message=f"An error occurred: {str(e)}"
            )


class ResetPasswordMutation(graphene.Mutation):
    class Arguments:
        token = graphene.String(required=True)
        new_password = graphene.String(required=True)

    success = graphene.Boolean()
    message = graphene.String()

    def mutate(self, info, token, new_password):
        try:
            # Validate password
            try:
                validate_password(new_password)
            except ValidationError as e:
                return ResetPasswordMutation(
                    success=False,
                    message=str(e.messages[0])
                )

            # Find reset token
            reset_token = PasswordResetToken.objects.get(token=token, is_used=False)
            
            if reset_token.is_expired():
                return ResetPasswordMutation(
                    success=False,
                    message="Reset token has expired"
                )

            # Update password
            user = reset_token.user
            user.set_password(new_password)
            user.save()

            # Mark token as used
            reset_token.is_used = True
            reset_token.save()

            return ResetPasswordMutation(
                success=True,
                message="Password has been reset successfully"
            )

        except PasswordResetToken.DoesNotExist:
            return ResetPasswordMutation(
                success=False,
                message="Invalid or expired reset token"
            )
        except Exception as e:
            return ResetPasswordMutation(
                success=False,
                message=f"An error occurred: {str(e)}"
            )


class GoogleSignInMutation(graphene.Mutation):
    class Arguments:
        access_token = graphene.String(required=True)

    Output = AuthPayload

    def mutate(self, info, access_token):
        try:
            # Verify Google token
            google_response = requests.get(
                f'https://www.googleapis.com/oauth2/v1/userinfo?access_token={access_token}'
            )
            
            if google_response.status_code != 200:
                return AuthPayload(
                    success=False,
                    message="Invalid Google access token"
                )

            google_data = google_response.json()
            
            # Extract user data
            email = google_data.get('email')
            google_id = google_data.get('id')
            first_name = google_data.get('given_name', '')
            last_name = google_data.get('family_name', '')
            profile_picture = google_data.get('picture', '')

            if not email:
                return AuthPayload(
                    success=False,
                    message="Email not provided by Google"
                )

            # Check if user exists
            user = None
            try:
                user = CustomUser.objects.get(email=email)
                # Update Google data if user exists
                if not user.google_id:
                    user.google_id = google_id
                    user.is_google_user = True
                    user.profile_picture = profile_picture
                    user.is_email_verified = True
                    user.save()
            except CustomUser.DoesNotExist:
                # Create new user
                user = CustomUser.objects.create_user(
                    email=email,
                    first_name=first_name,
                    last_name=last_name,
                    google_id=google_id,
                    is_google_user=True,
                    profile_picture=profile_picture,
                    is_email_verified=True
                )

            # Generate JWT tokens
            from rest_framework_simplejwt.tokens import RefreshToken
            refresh = RefreshToken.for_user(user)
            access_token_jwt = str(refresh.access_token)
            refresh_token = str(refresh)

            return AuthPayload(
                success=True,
                message="Google sign-in successful",
                user=user,
                access_token=access_token_jwt,
                refresh_token=refresh_token
            )

        except Exception as e:
            return AuthPayload(
                success=False,
                message=f"An error occurred: {str(e)}"
            )


class ChangePasswordMutation(graphene.Mutation):
    class Arguments:
        old_password = graphene.String(required=True)
        new_password = graphene.String(required=True)

    success = graphene.Boolean()
    message = graphene.String()

    def mutate(self, info, old_password, new_password):
        user = info.context.user
        
        if not user.is_authenticated:
            return ChangePasswordMutation(
                success=False,
                message="Authentication required"
            )

        try:
            # Validate old password
            if not user.check_password(old_password):
                return ChangePasswordMutation(
                    success=False,
                    message="Current password is incorrect"
                )

            # Validate new password
            try:
                validate_password(new_password, user)
            except ValidationError as e:
                return ChangePasswordMutation(
                    success=False,
                    message=str(e.messages[0])
                )

            # Update password
            user.set_password(new_password)
            user.save()

            return ChangePasswordMutation(
                success=True,
                message="Password changed successfully"
            )

        except Exception as e:
            return ChangePasswordMutation(
                success=False,
                message=f"An error occurred: {str(e)}"
            )


class UpdateProfileMutation(graphene.Mutation):
    class Arguments:
        first_name = graphene.String()
        last_name = graphene.String()
        phone_number = graphene.String()

    success = graphene.Boolean()
    message = graphene.String()
    user = graphene.Field(UserType)

    def mutate(self, info, first_name=None, last_name=None, phone_number=None):
        user = info.context.user
        
        if not user.is_authenticated:
            return UpdateProfileMutation(
                success=False,
                message="Authentication required"
            )

        try:
            if first_name is not None:
                user.first_name = first_name
            if last_name is not None:
                user.last_name = last_name
            if phone_number is not None:
                user.phone_number = phone_number

            user.save()

            return UpdateProfileMutation(
                success=True,
                message="Profile updated successfully",
                user=user
            )

        except Exception as e:
            return UpdateProfileMutation(
                success=False,
                message=f"An error occurred: {str(e)}"
            )


class ProfessionalProfileType(DjangoObjectType):
    class Meta:
        model = ProfessionalProfile
        fields = '__all__'


class ClientProfileType(DjangoObjectType):
    class Meta:
        model = ClientProfile
        fields = '__all__'


class UpdateProfessionalProfileMutation(graphene.Mutation):
    class Arguments:
        bio = graphene.String()
        skills = graphene.String()
        experience = graphene.String()
        hourly_rate = graphene.Decimal()
        location = graphene.String()
        is_available = graphene.Boolean()

    success = graphene.Boolean()
    message = graphene.String()
    profile = graphene.Field(ProfessionalProfileType)

    def mutate(self, info, bio=None, skills=None, experience=None, hourly_rate=None, location=None, is_available=None):
        user = info.context.user
        
        if not user.is_authenticated:
            return UpdateProfessionalProfileMutation(
                success=False,
                message="Authentication required"
            )

        if not user.is_professional:
            return UpdateProfessionalProfileMutation(
                success=False,
                message="Only professionals can update professional profile"
            )

        try:
            profile, created = ProfessionalProfile.objects.get_or_create(user=user)
            
            if bio is not None:
                profile.bio = bio
            if skills is not None:
                profile.skills = skills
            if experience is not None:
                profile.experience = experience
            if hourly_rate is not None:
                profile.hourly_rate = hourly_rate
            if location is not None:
                profile.location = location
            if is_available is not None:
                profile.is_available = is_available

            profile.save()

            return UpdateProfessionalProfileMutation(
                success=True,
                message="Professional profile updated successfully",
                profile=profile
            )

        except Exception as e:
            return UpdateProfessionalProfileMutation(
                success=False,
                message=f"An error occurred: {str(e)}"
            )


class UpdateClientProfileMutation(graphene.Mutation):
    class Arguments:
        company_name = graphene.String()
        bio = graphene.String()
        location = graphene.String()

    success = graphene.Boolean()
    message = graphene.String()
    profile = graphene.Field(ClientProfileType)

    def mutate(self, info, company_name=None, bio=None, location=None):
        user = info.context.user
        
        if not user.is_authenticated:
            return UpdateClientProfileMutation(
                success=False,
                message="Authentication required"
            )

        if not user.is_client:
            return UpdateClientProfileMutation(
                success=False,
                message="Only clients can update client profile"
            )

        try:
            profile, created = ClientProfile.objects.get_or_create(user=user)
            
            if company_name is not None:
                profile.company_name = company_name
            if bio is not None:
                profile.bio = bio
            if location is not None:
                profile.location = location

            profile.save()

            return UpdateClientProfileMutation(
                success=True,
                message="Client profile updated successfully",
                profile=profile
            )

        except Exception as e:
            return UpdateClientProfileMutation(
                success=False,
                message=f"An error occurred: {str(e)}"
            )
