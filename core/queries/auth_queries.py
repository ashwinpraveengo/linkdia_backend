import graphene
from graphene_django import DjangoObjectType
from core.models import CustomUser, ProfessionalProfile, ClientProfile
from core.types import UserType, ProfessionalProfileType, ClientProfileType


class Query(graphene.ObjectType):
    me = graphene.Field(UserType)
    my_professional_profile = graphene.Field(ProfessionalProfileType)
    my_client_profile = graphene.Field(ClientProfileType)
    user = graphene.Field(UserType, id=graphene.ID())
    users = graphene.List(UserType)
    professionals = graphene.List(UserType)
    clients = graphene.List(UserType)

    def resolve_me(self, info):
        user = info.context.user
        if user.is_authenticated:
            return user
        return None

    def resolve_my_professional_profile(self, info):
        user = info.context.user
        if user.is_authenticated and user.is_professional:
            try:
                return user.professional_profile
            except ProfessionalProfile.DoesNotExist:
                return None
        return None

    def resolve_my_client_profile(self, info):
        user = info.context.user
        if user.is_authenticated and user.is_client:
            try:
                return user.client_profile
            except ClientProfile.DoesNotExist:
                return None
        return None

    def resolve_user(self, info, id):
        try:
            return CustomUser.objects.get(pk=id)
        except CustomUser.DoesNotExist:
            return None

    def resolve_users(self, info):
        return CustomUser.objects.all()

    def resolve_professionals(self, info):
        return CustomUser.objects.filter(user_type='PROFESSIONAL')

    def resolve_clients(self, info):
        return CustomUser.objects.filter(user_type='CLIENT')
