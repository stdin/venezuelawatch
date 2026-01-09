from ninja import NinjaAPI
from core.api import router as health_router, user_router
from data_pipeline.api import router as tasks_router

api = NinjaAPI(
    title="VenezuelaWatch API",
    version="1.0.0",
    description="Real-time intelligence platform for Venezuela events"
)

# Add health check router
api.add_router("/health", health_router, tags=["Health"])

# Add user profile router
api.add_router("/user", user_router, tags=["User Profile"])

# Add data pipeline task trigger router (for Cloud Scheduler)
api.add_router("/tasks", tasks_router, tags=["Data Pipeline"])

# Will add more routers here in future phases
