from fastapi import APIRouter
from .endpoints import lenders, api_configs, api_templates, generated_apis, api_tests, users, deployments, samples, analytics, health, external, auth, validation, utils, steps, integrations, field_management

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(
    lenders.router,
    prefix="/lenders",
    tags=["lenders"]
)

api_router.include_router(
    field_management.router,
    prefix="/field-management",
    tags=["field-management"]
)

api_router.include_router(
    steps.router,
    prefix="/steps",
    tags=["steps"]
)

api_router.include_router(
    integrations.router,
    prefix="/integrations",
    tags=["integrations"]
)

api_router.include_router(
    api_configs.router,
    prefix="/api-configs",
    tags=["api-configs"]
)

api_router.include_router(
    api_templates.router,
    prefix="/api-templates",
    tags=["api-templates"]
)

api_router.include_router(
    generated_apis.router,
    prefix="/generated-apis",
    tags=["generated-apis"]
)

api_router.include_router(
    api_tests.router,
    prefix="/api-tests",
    tags=["api-tests"]
)

api_router.include_router(
    users.router,
    prefix="/users",
    tags=["users"]
)

api_router.include_router(
    deployments.router,
    prefix="/deployments",
    tags=["deployments"]
)

api_router.include_router(
    samples.router,
    prefix="/samples",
    tags=["samples"]
)

api_router.include_router(
    analytics.router,
    prefix="/analytics",
    tags=["analytics"]
)

# Health under versioned API as well
api_router.include_router(
    health.router,
    prefix="/health",
    tags=["health"]
)

# Public-facing external routes that trigger configured sequences
api_router.include_router(
    external.router,
    prefix="/external",
    tags=["external"]
)

# Auth and validation
api_router.include_router(
    auth.router,
    prefix="/auth",
    tags=["auth"]
)

api_router.include_router(
    validation.router,
    prefix="",
    tags=["validation"]
)

api_router.include_router(
    utils.router,
    prefix="/utils",
    tags=["utils"]
)
