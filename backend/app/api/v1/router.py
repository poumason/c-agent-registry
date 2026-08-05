from fastapi import APIRouter

from app.api.v1.endpoints import (
    agent_versions,
    agents,
    auth,
    dependencies,
    mcps,
    reviews,
    skills,
    users,
)

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(agents.router)
api_router.include_router(agent_versions.router)
api_router.include_router(dependencies.router)
api_router.include_router(reviews.router)
api_router.include_router(skills.router)
api_router.include_router(mcps.router)
