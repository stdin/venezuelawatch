from ninja import NinjaAPI
from core.api import router as health_router

api = NinjaAPI(
    title="VenezuelaWatch API",
    version="1.0.0",
    description="Real-time intelligence platform for Venezuela events"
)

# Add health check router
api.add_router("/health", health_router)

# Will add more routers here in future phases
