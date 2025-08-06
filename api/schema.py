import graphene
from core.mutations.auth_mutations import (
    SignUpMutation,
    LoginMutation,
    ForgotPasswordMutation,
    ResetPasswordMutation,
    GoogleSignInMutation,
    ChangePasswordMutation,
    UpdateProfileMutation,
    UpdateProfessionalProfileMutation,
    UpdateClientProfileMutation
)
from core.queries.auth_queries import Query


class Mutation(graphene.ObjectType):
    signup = SignUpMutation.Field()
    login = LoginMutation.Field()
    forgot_password = ForgotPasswordMutation.Field()
    reset_password = ResetPasswordMutation.Field()
    google_signin = GoogleSignInMutation.Field()
    change_password = ChangePasswordMutation.Field()
    update_profile = UpdateProfileMutation.Field()
    update_professional_profile = UpdateProfessionalProfileMutation.Field()
    update_client_profile = UpdateClientProfileMutation.Field()


schema = graphene.Schema(query=Query, mutation=Mutation)
