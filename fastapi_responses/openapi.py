from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi

from fastapi_responses.utils import analyze


def custom_openapi(app: FastAPI) -> callable:
    def _custom_openapi() -> dict:
        if app.openapi_schema:
            return app.openapi_schema
        openapi_schema = get_openapi(
            title=app.title,
            version=app.version,
            description=app.description,
            routes=app.routes,
        )
        app.openapi_schema = openapi_schema
        analyze(app)
        return app.openapi_schema

    return _custom_openapi
