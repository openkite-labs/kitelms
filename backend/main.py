from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from scalar_fastapi import get_scalar_api_reference

from backend.core.settings import settings
from backend.modules.auth.auth_routes import auth_router
from backend.modules.courses.course_routes import course_router
from backend.modules.lessons.lesson_routes import lesson_router
from backend.modules.sections.section_routes import section_router
from backend.modules.users.user_routes import user_router

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=settings.APP_DESCRIPTION,
    openapi_url=settings.APP_OPENAPI_URL,
    docs_url=settings.APP_DOCS_URL,
    redoc_url=settings.APP_REDOC_URL,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=settings.CORS_ALLOW_METHODS,
    allow_headers=settings.CORS_ALLOW_HEADERS,
)


app.include_router(auth_router)
app.include_router(course_router)
app.include_router(section_router)
app.include_router(lesson_router)
app.include_router(user_router)


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/scalar", include_in_schema=False)
async def scalar_api_reference():
    return get_scalar_api_reference(
        openapi_url=settings.APP_OPENAPI_URL,
        title=settings.APP_NAME,
    )
