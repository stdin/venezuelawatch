# Phase 2 Discovery: Authentication & User Management

## Research Summary

Investigated django-allauth integration with django-ninja for React SPA authentication, JWT vs session patterns, and user model design for future team features.

## Key Findings

### 1. django-allauth Headless for SPAs

**Selected Approach:** Use `django-allauth` with `allauth.headless` module for React SPA integration.

**Rationale:**
- Purpose-built for headless/SPA authentication
- Native JWT support via `allauth.headless.contrib.ninja.security.jwt_token_auth`
- Integrated with django-ninja (our existing API framework)
- Handles registration, login, password reset, email verification
- Battle-tested library with high reputation (1077+ code snippets)

**Configuration:**
```python
# settings.py
INSTALLED_APPS = [
    'allauth',
    'allauth.account',
    'allauth.headless',
]

HEADLESS_FRONTEND_URLS = {
    "ACCOUNT_ACTIVATION_URL": "http://localhost:5173/auth/verify/",
    "PASSWORD_RESET_URL": "http://localhost:5173/auth/reset/",
}

ACCOUNT_EMAIL_VERIFICATION_BY_CODE_ENABLED = True  # Better for headless
```

**API Endpoints:**
- Registration: `POST /_allauth/auth/registration/`
- Login: `POST /_allauth/auth/login/`
- Logout: `POST /_allauth/auth/logout/`
- User details: `GET /_allauth/auth/user/`

**Alternative Considered:** dj-rest-auth
- More verbose configuration
- Extra dependency layer
- django-allauth headless more direct for our use case

### 2. JWT Authentication for React SPA

**Selected Approach:** JWT tokens in httpOnly cookies

**Rationale:**
- Stateless authentication (scalable for future growth)
- React frontend on different origin (localhost:5173 in dev)
- httpOnly cookies prevent XSS attacks on tokens
- Automatic CSRF protection with django-allauth headless
- Refresh token pattern for session management

**Implementation with django-ninja:**
```python
from allauth.headless.contrib.ninja.security import jwt_token_auth
from ninja import Router

router = Router()

@router.get("/protected", auth=jwt_token_auth)
def protected_endpoint(request):
    return {"user": request.auth.email}
```

**Token Storage:**
- Access token: httpOnly cookie, 15-minute expiry
- Refresh token: httpOnly cookie, 7-day expiry
- CSRF token: Standard Django CSRF for state-changing operations

**Alternative Considered:** Session-based auth
- Requires sticky sessions (limits horizontal scaling)
- More complex CORS configuration
- Less suitable for future mobile apps
- JWT more flexible for multi-client scenarios

### 3. User Model Design for Future Teams

**Selected Approach:** Custom User model extending AbstractUser with team-ready fields

**Rationale:**
- Start with individual users (Phase 2 requirement)
- Add fields that enable future team features without migration pain
- Avoid costly schema changes when teams are added later

**User Model Structure:**
```python
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    # Core fields (inherited from AbstractUser)
    # - username, email, password, first_name, last_name, is_active, is_staff, date_joined

    # Team-ready fields (for future Phase expansion)
    organization_name = models.CharField(max_length=200, blank=True)
    role = models.CharField(max_length=50, default='individual')  # individual, team_member, team_admin, org_admin

    # Subscription/billing (for future SaaS features)
    subscription_tier = models.CharField(max_length=50, default='free')

    # Metadata
    timezone = models.CharField(max_length=50, default='UTC')

    class Meta:
        db_table = 'users'
```

**Future Team Integration Path:**
- Phase 2: Individual users with role='individual'
- Future phase: Add Team model with ForeignKey to User (team_id nullable)
- Future phase: Add organization-level permissions and workspaces
- No User model migration needed - just add Team relationship

**Alternative Considered:** Minimal User model, add fields later
- Requires migration when teams added
- Risk of downtime during team feature rollout
- Harder to test team scenarios without fields

## Technology Stack

### Backend Dependencies
```
django-allauth>=0.63.0  # Headless support introduced in 0.63
djangorestframework-simplejwt>=5.3  # JWT token backend
```

### Frontend Dependencies (React)
```
axios  # HTTP client (already in use from Phase 1)
react-router-dom  # For protected routes
```

## API Design Decisions

### 1. Authentication Endpoints

**Use django-allauth headless endpoints at `/_allauth/`:**
- Consistent with library conventions
- Auto-generated, well-tested endpoints
- Reduces custom code maintenance

**Custom endpoints needed:**
- None for Phase 2 - django-allauth provides complete auth flow

### 2. Protected Route Pattern

**Apply authentication at router level:**
```python
# Protected routers inherit auth
protected_router = Router(auth=jwt_token_auth)

# Public routers have no auth
public_router = Router()
```

**Benefits:**
- Clear separation of public vs protected endpoints
- Easy to identify security boundaries
- Consistent with django-ninja patterns from Phase 1

### 3. CORS Configuration

**Update existing CORS for auth endpoints:**
```python
CORS_ALLOWED_ORIGINS = ["http://localhost:5173"]
CORS_ALLOW_CREDENTIALS = True  # Required for httpOnly cookies
```

## Security Considerations

### 1. CSRF Protection
- django-allauth headless handles CSRF automatically
- Frontend must send CSRF token from cookie in X-CSRFToken header
- Enforced on state-changing operations (POST, PUT, DELETE)

### 2. Token Security
- Access tokens: 15-minute expiry (limit damage if compromised)
- Refresh tokens: 7-day expiry (balance security and UX)
- httpOnly cookies prevent JavaScript access (XSS protection)
- Secure flag in production (HTTPS only)

### 3. Password Requirements
- Django's default password validators (min length, common passwords, numeric, similarity)
- Consider adding custom validator for complexity in future

### 4. Rate Limiting
- Not implemented in Phase 2
- Add in future phase for production (django-ratelimit or nginx-level)

## Common Pitfalls to Avoid

### 1. Don't Store JWT in localStorage
**Why:** Vulnerable to XSS attacks. Always use httpOnly cookies.

### 2. Don't Skip CORS_ALLOW_CREDENTIALS
**Why:** Cookies won't be sent cross-origin without this flag.

### 3. Don't Use Long-Lived Access Tokens
**Why:** Increases attack surface. Use short expiry + refresh pattern.

### 4. Don't Custom-Build What django-allauth Provides
**Why:** Email verification, password reset, account management are complex. Use battle-tested library.

### 5. Don't Extend User Model Later
**Why:** Migrations on User model in production are risky. Add team-ready fields now.

## Integration Points

### Phase 1 Dependencies
- Django 5.2 backend (✓ from 01-01)
- django-ninja API framework (✓ from 01-01)
- CORS middleware (✓ from 01-01)
- React 18 frontend (✓ from 01-02)
- Vite proxy configuration (✓ from 01-02)
- PostgreSQL database (✓ from 01-03)

### Phase 3 Impact (Data Pipeline)
- Events will have `created_by` user foreign key
- User context for API rate limiting
- User-specific event filtering and saved searches

### Phase 5 Impact (Dashboard)
- User profile settings in dashboard
- Personalized event feeds
- User preferences storage

## Implementation Notes

### Django Migrations
- Custom User model must be set BEFORE first migration
- Use `AUTH_USER_MODEL = 'core.User'` in settings.py
- Cannot be changed after initial migration without major surgery

### Email Configuration
- Phase 2: Console email backend (development)
- Future phase: SendGrid/SES for production emails
- Email verification optional for Phase 2 (can be disabled)

### Frontend State Management
- Auth context using React Context API
- Token refresh handled automatically via axios interceptors
- Protected route wrapper component

## Next Steps

Phase 2 will be broken into 4 plans (standard depth):

1. **02-01: django-allauth Setup & User Model**
   - Install django-allauth with headless
   - Create custom User model
   - Configure JWT authentication
   - Run migrations

2. **02-02: Authentication Endpoints**
   - Configure allauth headless URLs
   - Set up CORS for credentials
   - Test registration and login endpoints
   - Verify JWT token generation

3. **02-03: Protected API Routes**
   - Apply jwt_token_auth to existing endpoints
   - Create user profile endpoint
   - Test authenticated requests
   - Update API documentation

4. **02-04: React Authentication UI**
   - Create auth context and provider
   - Build login and registration forms
   - Implement protected route wrapper
   - Add token refresh interceptor
   - Test full authentication flow

## References

- django-allauth docs: https://docs.allauth.org/
- django-allauth headless: https://docs.allauth.org/en/latest/headless/
- django-ninja auth guide: https://django-ninja.dev/guides/authentication/
- React SPA example: https://github.com/pennersr/django-allauth/tree/main/examples/react-spa

---
*Discovery completed: 2026-01-08*
