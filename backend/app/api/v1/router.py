from fastapi import APIRouter

from app.api.v1.endpoints import (
    admin,
    agent_fabs,
    agent_versions,
    agents,
    ai_models,
    auth,
    dependencies,
    fabs,
    mcps,
    registry,
    reviews,
    skills,
    users,
)

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(agents.router)
api_router.include_router(agent_versions.router)
api_router.include_router(agent_fabs.router)
api_router.include_router(dependencies.router)
api_router.include_router(reviews.router)
api_router.include_router(skills.router)
api_router.include_router(mcps.router)
api_router.include_router(admin.router)
api_router.include_router(registry.router)
api_router.include_router(ai_models.router)
api_router.include_router(fabs.router)
