from ninja import Router
from allauth.headless.contrib.ninja.security import jwt_token_auth

router = Router()


@router.get("/health")
def health_check(request):
    return {"status": "ok", "service": "venezuelawatch"}


# User endpoints (authenticated)
user_router = Router()


@user_router.get("/me", auth=jwt_token_auth)
def get_current_user(request):
    """Get current authenticated user profile."""
    user = request.auth  # jwt_token_auth sets request.auth to User instance
    return {
        "id": user.id,
        "email": user.email,
        "username": user.username,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "organization_name": user.organization_name,
        "role": user.role,
        "subscription_tier": user.subscription_tier,
        "timezone": user.timezone,
        "date_joined": user.date_joined.isoformat(),
    }
