import graphene
from core.mutations.auth_mutations import (
    SignUpMutation,
    LoginMutation,
    ForgotPasswordMutation,
    ResetPasswordMutation,
    GoogleSignInMutation,
    ChangePasswordMutation,
    UpdateProfileMutation,
    UpdateClientProfileMutation
)
from core.mutations.professional_onboarding import ProfessionalOnboardingMutations
from core.mutations.file_mutations import FileMutations
from core.queries.auth_queries import Query as AuthQuery
from core.queries.professional_queries import ProfessionalQuery
from core.queries.file_queries import FileQuery


class Query(AuthQuery, ProfessionalQuery, FileQuery, graphene.ObjectType):
    pass


class Mutation(ProfessionalOnboardingMutations, FileMutations, graphene.ObjectType):
    # Auth mutations
    signup = SignUpMutation.Field()
    login = LoginMutation.Field()
    forgot_password = ForgotPasswordMutation.Field()
    reset_password = ResetPasswordMutation.Field()
    google_signin = GoogleSignInMutation.Field()
    change_password = ChangePasswordMutation.Field()
    update_profile = UpdateProfileMutation.Field()
    update_client_profile = UpdateClientProfileMutation.Field()
    
    # Professional Onboarding mutations (6-step process):
    # Step 1: update_professional_profile
    # Step 2: upload_professional_document, verify_professional_document (admin)
    # Step 3: complete_video_kyc, verify_video_kyc (admin)  
    # Step 4: create_portfolio
    # Step 5: set_consultation_availability
    # Step 6: add_payment_method
    # Utility: check_onboarding_status


schema = graphene.Schema(query=Query, mutation=Mutation)
