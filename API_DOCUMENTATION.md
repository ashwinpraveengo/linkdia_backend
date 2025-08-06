# Linkdia Backend - GraphQL API Documentation

## Server Information
- **GraphQL Endpoint**: `http://localhost:8001/graphql/`
- **GraphiQL Interface**: `http://localhost:8001/graphql/` (for testing in browser)
- **Admin Panel**: `http://localhost:8001/admin/`

## Authentication Flow for Flutter Mobile App

### 1. User Registration (Sign Up)

```graphql
mutation SignUp {
  signup(
    email: "user@example.com"
    password: "securepassword123"
    userType: "CLIENT"  # or "PROFESSIONAL"
    firstName: "John"
    lastName: "Doe"
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
      fullName
      phoneNumber
      isEmailVerified
      dateJoined
    }
    accessToken
    refreshToken
  }
}
```

**User Types:**
- `CLIENT`: For users who want to hire professionals
- `PROFESSIONAL`: For service providers

### 2. User Login

```graphql
mutation Login {
  login(
    email: "user@example.com"
    password: "securepassword123"
  ) {
    success
    message
    user {
      id
      email
      firstName
      lastName
      fullName
      phoneNumber
      isEmailVerified
      profilePicture
      dateJoined
    }
    accessToken
    refreshToken
  }
}
```

### 3. Google Sign In/Sign Up

```graphql
mutation GoogleSignIn {
  googleSignin(
    accessToken: "google_access_token_here"
  ) {
    success
    message
    user {
      id
      email
      firstName
      lastName
      fullName
      profilePicture
      isEmailVerified
      dateJoined
    }
    accessToken
    refreshToken
  }
}
```

### 4. Forgot Password

```graphql
mutation ForgotPassword {
  forgotPassword(
    email: "user@example.com"
  ) {
    success
    message
  }
}
```

### 5. Reset Password

```graphql
mutation ResetPassword {
  resetPassword(
    token: "reset_token_from_email"
    newPassword: "newSecurePassword123"
  ) {
    success
    message
  }
}
```

### 6. Change Password (Authenticated Users)

```graphql
mutation ChangePassword {
  changePassword(
    oldPassword: "currentPassword"
    newPassword: "newSecurePassword123"
  ) {
    success
    message
  }
}
```

### 7. Update Profile (Authenticated Users)

```graphql
mutation UpdateProfile {
  updateProfile(
    firstName: "Jane"
    lastName: "Smith"
    phoneNumber: "+9876543210"
  ) {
    success
    message
    user {
      id
      email
      firstName
      lastName
      fullName
      phoneNumber
      profilePicture
    }
  }
}
```

## Profile Management

### 8. Update Professional Profile (Professionals Only)

```graphql
mutation UpdateProfessionalProfile {
  updateProfessionalProfile(
    bio: "I am an experienced software engineer with 5 years of experience."
    skills: "JavaScript, Python, React, Django"
    experience: "5 years in full-stack development"
    hourlyRate: 75.00
    location: "New York, NY"
    isAvailable: true
  ) {
    success
    message
    profile {
      id
      bio
      skills
      experience
      hourlyRate
      location
      isAvailable
      createdAt
      updatedAt
    }
  }
}
```

### 9. Update Client Profile (Clients Only)

```graphql
mutation UpdateClientProfile {
  updateClientProfile(
    companyName: "Tech Startup Inc."
    bio: "We are a fast-growing startup looking for talented professionals."
    location: "San Francisco, CA"
  ) {
    success
    message
    profile {
      id
      companyName
      bio
      location
      createdAt
      updatedAt
    }
  }
}
```

## Queries

### 1. Get Current User (Me)

```graphql
query Me {
  me {
    id
    email
    firstName
    lastName
    userType
    fullName
    phoneNumber
    profilePicture
    isEmailVerified
    dateJoined
  }
}
```

### 2. Get My Professional Profile

```graphql
query MyProfessionalProfile {
  myProfessionalProfile {
    id
    bio
    skills
    experience
    hourlyRate
    location
    isAvailable
    createdAt
    updatedAt
  }
}
```

### 3. Get My Client Profile

```graphql
query MyClientProfile {
  myClientProfile {
    id
    companyName
    bio
    location
    createdAt
    updatedAt
  }
}
```

### 4. Get All Professionals

```graphql
query GetProfessionals {
  professionals {
    id
    email
    firstName
    lastName
    userType
    fullName
    profilePicture
    dateJoined
  }
}
```

### 5. Get All Clients

```graphql
query GetClients {
  clients {
    id
    email
    firstName
    lastName
    userType
    fullName
    profilePicture
    dateJoined
  }
}
```

### 6. Get User by ID

```graphql
query GetUser {
  user(id: "user_id_here") {
    id
    email
    firstName
    lastName
    userType
    fullName
    phoneNumber
    profilePicture
    isEmailVerified
    dateJoined
  }
}
```

### 7. Get All Users (Admin only)

```graphql
query GetAllUsers {
  users {
    id
    email
    firstName
    lastName
    fullName
    phoneNumber
    isEmailVerified
    dateJoined
  }
}
```

## Authentication Headers for Flutter App

For authenticated requests, include the access token in the Authorization header:

```
Authorization: Bearer YOUR_ACCESS_TOKEN_HERE
```

## Flutter Integration Example

### HTTP Client Setup

```dart
import 'package:graphql_flutter/graphql_flutter.dart';

class GraphQLService {
  static String endpoint = 'http://localhost:8001/graphql/';
  static String? _accessToken;

  static GraphQLClient _client() {
    final HttpLink httpLink = HttpLink(endpoint);
    
    final AuthLink authLink = AuthLink(
      getToken: () async => _accessToken != null ? 'Bearer $_accessToken' : null,
    );

    final Link link = authLink.concat(httpLink);

    return GraphQLClient(
      link: link,
      cache: GraphQLCache(store: InMemoryStore()),
    );
  }

  static void setAccessToken(String token) {
    _accessToken = token;
  }

  static Future<QueryResult> query(String query, {Map<String, dynamic>? variables}) {
    return _client().query(QueryOptions(
      document: gql(query),
      variables: variables ?? {},
    ));
  }

  static Future<QueryResult> mutate(String mutation, {Map<String, dynamic>? variables}) {
    return _client().mutate(MutationOptions(
      document: gql(mutation),
      variables: variables ?? {},
    ));
  }
}
```

### Login Example

```dart
Future<bool> login(String email, String password) async {
  const String loginMutation = '''
    mutation Login(\$email: String!, \$password: String!) {
      login(email: \$email, password: \$password) {
        success
        message
        user {
          id
          email
          firstName
          lastName
        }
        accessToken
        refreshToken
      }
    }
  ''';

  try {
    final QueryResult result = await GraphQLService.mutate(
      loginMutation,
      variables: {
        'email': email,
        'password': password,
      },
    );

    if (result.hasException) {
      print('GraphQL Error: ${result.exception.toString()}');
      return false;
    }

    final loginData = result.data?['login'];
    if (loginData['success']) {
      // Store tokens securely
      final accessToken = loginData['accessToken'];
      final refreshToken = loginData['refreshToken'];
      
      // Set token for future requests
      GraphQLService.setAccessToken(accessToken);
      
      // Store tokens in secure storage
      await storeTokens(accessToken, refreshToken);
      
      return true;
    } else {
      print('Login failed: ${loginData['message']}');
      return false;
    }
  } catch (e) {
    print('Login error: $e');
    return false;
  }
}
```

## Testing with curl

### Sign Up
```bash
curl -X POST http://localhost:8001/graphql/ \
  -H "Content-Type: application/json" \
  -d '{
    "query": "mutation { signup(email: \"test@example.com\", password: \"testpass123\", firstName: \"Test\", lastName: \"User\") { success message user { id email firstName lastName } accessToken } }"
  }'
```

### Login
```bash
curl -X POST http://localhost:8001/graphql/ \
  -H "Content-Type: application/json" \
  -d '{
    "query": "mutation { login(email: \"test@example.com\", password: \"testpass123\") { success message user { id email firstName lastName } accessToken } }"
  }'
```

### Get Current User (with token)
```bash
curl -X POST http://localhost:8001/graphql/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "query": "query { me { id email firstName lastName } }"
  }'
```

## Production Setup

### PostgreSQL Configuration

1. Install PostgreSQL:
```bash
sudo apt update
sudo apt install postgresql postgresql-contrib
```

2. Create database and user:
```sql
sudo -u postgres psql
CREATE DATABASE linkdia_db;
CREATE USER linkdia_user WITH PASSWORD 'your_secure_password';
GRANT ALL PRIVILEGES ON DATABASE linkdia_db TO linkdia_user;
\q
```

3. Update .env file:
```env
DEBUG=False
DATABASE_URL=postgresql://linkdia_user:your_secure_password@localhost:5432/linkdia_db
ALLOWED_HOSTS=your-domain.com,www.your-domain.com
SECRET_KEY=your-production-secret-key
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
```

4. Run migrations:
```bash
python manage.py migrate
python manage.py collectstatic
```

### Google OAuth Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing
3. Enable Google+ API
4. Create OAuth 2.0 credentials
5. Add authorized domains
6. Update .env with client ID and secret

## Error Handling

The API returns consistent error responses:

```json
{
  "success": false,
  "message": "Error description here"
}
```

Common error codes:
- Invalid credentials
- User already exists
- Token expired
- Validation errors
- Server errors

## Rate Limiting

Consider implementing rate limiting in production to prevent abuse:
- Login attempts: 5 per minute
- Password reset: 3 per hour
- API calls: 1000 per hour per user
