from core.settings import settings
from fastapi import FastAPI
from scalar_fastapi import get_scalar_api_reference

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=settings.APP_DESCRIPTION,
    openapi_url=settings.APP_OPENAPI_URL,
    docs_url=settings.APP_DOCS_URL,
    redoc_url=settings.APP_REDOC_URL,
)


@app.get("/scalar", include_in_schema=False)
async def scalar_api_reference():
    return get_scalar_api_reference(
        openapi_url=settings.APP_OPENAPI_URL,
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description=settings.APP_DESCRIPTION,
    )
