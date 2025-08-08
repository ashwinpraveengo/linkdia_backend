# Complete GraphQL Mutations for Testing - Professional Onboarding

This document contains all GraphQL mutations needed for testing the complete professional onboarding flow, from user signup to completion.

## Authentication Mutations

### 1. Sign Up as Professional
```graphql
mutation SignUp {
  signup(
    email: "lawyer@example.com"
    password: "SecurePassword123"
    firstName: "John"
    lastName: "Doe"
    userType: "PROFESSIONAL"
    phoneNumber: "+1234567890"
  ) {
    success
    message
    user {
      id
      email
      firstName
      lastName
      userType
      isEmailVerified
    }
    accessToken
    refreshToken
  }
}
```

### 2. Login
```graphql
mutation Login {
  login(
    email: "lawyer@example.com"
    password: "SecurePassword123"
  ) {
    success
    message
    user {
      id
      email
      firstName
      lastName
      userType
    }
    accessToken
    refreshToken
  }
}
```

### 3. Google Sign In (Alternative)
```graphql
mutation GoogleSignIn {
  googleSignin(
    accessToken: "your_google_access_token_here"
  ) {
    success
    message
    user {
      id
      email
      firstName
      lastName
      userType
      isGoogleUser
    }
    accessToken
    refreshToken
  }
}
```

## Professional Onboarding Mutations (6-Step Process)

### Step 1: Profile Setup
```graphql
mutation UpdateProfessionalProfile {
  updateProfessionalProfile(
    profileData: {
      areaOfExpertise: "CORPORATE_LAWYER"
      yearsOfExperience: 5
      bioIntroduction: "Experienced corporate lawyer specializing in mergers and acquisitions with over 5 years of practice."
      location: "New York, NY"
    }
    # profilePicture: Use multipart form data for actual file upload
  ) {
    success
    message
    professionalProfile {
      id
      areaOfExpertise
      yearsOfExperience
      bioIntroduction
      location
      onboardingStep
      onboardingCompleted
      user {
        firstName
        lastName
        email
      }
    }
  }
}
```

### Step 2a: Upload Professional Document (Upload minimum 2 documents)
```graphql
# First document - Use multipart form data for file upload
mutation UploadDocument1 {
  uploadProfessionalDocument(
    documentType: "GOVERNMENT_ID"
    # documentFile: Use multipart form data for actual file upload
  ) {
    success
    message
    document {
      id
      documentType
      verificationStatus
      uploadedAt
    }
  }
}

# Second document - Use multipart form data for file upload  
mutation UploadDocument2 {
  uploadProfessionalDocument(
    documentType: "PROFESSIONAL_LICENSE"
    # documentFile: Use multipart form data for actual file upload
  ) {
    success
    message
    document {
      id
      documentType
      verificationStatus
      uploadedAt
    }
  }
}
```

### Step 2b: Verify Documents (Admin Only)
```graphql
# Admin verifies first document
mutation VerifyDocument1 {
  verifyProfessionalDocument(
    documentId: "document_uuid_1"
    verificationStatus: "VERIFIED"
  ) {
    success
    message
    document {
      id
      documentType
      verificationStatus
      verifiedAt
    }
  }
}

# Admin verifies second document
mutation VerifyDocument2 {
  verifyProfessionalDocument(
    documentId: "document_uuid_2"
    verificationStatus: "VERIFIED"
  ) {
    success
    message
    document {
      id
      documentType
      verificationStatus
      verifiedAt
    }
  }
}
```

### Step 3a: Complete Video KYC
```graphql
mutation CompleteVideoKYC {
  completeVideoKyc {
    success
    message
    videoKyc {
      id
      status
      completedAt
      professional {
        onboardingStep
      }
    }
  }
}
```

### Step 3b: Verify Video KYC (Admin Only)
```graphql
mutation VerifyVideoKYC {
  verifyVideoKyc(
    kycId: "video_kyc_uuid"
    status: "VERIFIED"
  ) {
    success
    message
    videoKyc {
      id
      status
      verifiedAt
      professional {
        onboardingStep
      }
    }
  }
}
```

### Step 4: Create Portfolio
```graphql
mutation CreatePortfolio {
  createPortfolio(
    name: "Corporate Merger Case - ABC Corp"
    # documentFile: Use multipart form data for actual file upload
  ) {
    success
    message
    portfolio {
      id
      name
      createdAt
      professional {
        onboardingStep
      }
    }
  }
}
```

### Step 5: Set Consultation Availability
```graphql
mutation SetConsultationAvailability {
  setConsultationAvailability(
    availabilityData: {
      monday: true
      tuesday: true
      wednesday: true
      thursday: true
      friday: true
      saturday: false
      sunday: false
      fromTime: "09:00:00"
      toTime: "17:00:00"
      consultationType: "BOTH"
      consultationDurationMinutes: 60
      googleCalendarSync: true
      outlookCalendarSync: false
    }
  ) {
    success
    message
    availability {
      id
      availableDays
      fromTime
      toTime
      consultationType
      consultationDurationMinutes
      professional {
        onboardingStep
      }
    }
  }
}
```

### Step 6a: Add Payment Method - Bank Account
```graphql
mutation AddBankPaymentMethod {
  addPaymentMethod(
    paymentData: {
      paymentType: "BANK_ACCOUNT"
      accountHolderName: "John Doe"
      bankName: "Chase Bank"
      accountNumber: "1234567890"
      ifscCode: "CHAS0001234"
    }
  ) {
    success
    message
    paymentMethod {
      id
      paymentType
      accountHolderName
      bankName
      professional {
        onboardingStep
        onboardingCompleted
      }
    }
  }
}
```

### Step 6b: Add Payment Method - Digital Wallet
```graphql
mutation AddWalletPaymentMethod {
  addPaymentMethod(
    paymentData: {
      paymentType: "DIGITAL_WALLET"
      walletProvider: "GOOGLE_PAY"
      walletPhoneNumber: "+1234567890"
    }
  ) {
    success
    message
    paymentMethod {
      id
      paymentType
      walletProvider
      walletPhoneNumber
      professional {
        onboardingStep
        onboardingCompleted
      }
    }
  }
}
```

## Utility Mutations

### Check Onboarding Status
```graphql
mutation CheckOnboardingStatus {
  checkOnboardingStatus {
    success
    message
    status {
      currentStep
      onboardingCompleted
      stepsCompleted
      nextStepMessage
    }
  }
}
```

### Update Profile (After Onboarding)
```graphql
mutation UpdateProfile {
  updateProfile(
    firstName: "John"
    lastName: "Smith"
    phoneNumber: "+1987654321"
  ) {
    success
    message
    user {
      id
      firstName
      lastName
      phoneNumber
    }
  }
}
```

### Change Password
```graphql
mutation ChangePassword {
  changePassword(
    oldPassword: "SecurePassword123"
    newPassword: "NewSecurePassword456"
  ) {
    success
    message
  }
}
```

## Query Examples for Testing

### Get My Professional Profile
```graphql
query GetMyProfile {
  myProfessionalProfile {
    id
    areaOfExpertise
    yearsOfExperience
    bioIntroduction
    location
    verificationStatus
    onboardingStep
    onboardingCompleted
    user {
      firstName
      lastName
      email
      profilePictureData
    }
  }
}
```

### Get My Documents
```graphql
query GetMyDocuments {
  myProfessionalDocuments {
    id
    documentType
    verificationStatus
    uploadedAt
    verifiedAt
  }
}
```

### Get My Video KYC
```graphql
query GetMyVideoKYC {
  myVideoKyc {
    id
    status
    completedAt
    verifiedAt
  }
}
```

### Get My Portfolios
```graphql
query GetMyPortfolios {
  myPortfolios {
    id
    name
    createdAt
  }
}
```

### Get My Consultation Availability
```graphql
query GetMyAvailability {
  myConsultationAvailability {
    id
    availableDays
    fromTime
    toTime
    consultationType
    consultationDurationMinutes
    googleCalendarSync
    outlookCalendarSync
  }
}
```

### Get My Payment Methods
```graphql
query GetMyPaymentMethods {
  myPaymentMethods {
    id
    paymentType
    accountHolderName
    bankName
    walletProvider
    walletPhoneNumber
    createdAt
  }
}
```

## Testing Flow

1. **Start**: Sign up as a professional user
2. **Step 1**: Update professional profile with all required fields + profile picture
3. **Step 2**: Upload at least 2 documents → Admin verifies them
4. **Step 3**: Complete video KYC → Admin verifies it
5. **Step 4**: Create portfolio with document
6. **Step 5**: Set consultation availability
7. **Step 6**: Add payment method
8. **Complete**: Check onboarding status to confirm completion

## Headers for Authentication

After login, include the JWT token in your headers:
```
{
  "Authorization": "Bearer <your_jwt_token_here>"
}
```

## File Upload Format

For mutations that require file uploads, use multipart form data format:
- Set `Content-Type: multipart/form-data`
- Include file in the form data
- Use tools like Postman, Insomnia, or GraphQL Playground with file upload support

## Error Scenarios to Test

1. Try to skip steps (should fail)
2. Upload invalid file types
3. Try admin mutations without admin privileges
4. Missing required fields
5. Invalid onboarding step transitions

This covers all mutations needed for complete professional onboarding testing!
