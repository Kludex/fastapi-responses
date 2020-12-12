from typing import Callable

from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi

from fastapi_responses.utils import extract_exceptions, write_response


def custom_openapi(app: FastAPI) -> Callable:
    def _custom_openapi() -> dict:
        if app.openapi_schema:  # pragma: no cover
            return app.openapi_schema
        openapi_schema = get_openapi(
            title=app.title,
            version=app.version,
            description=app.description,
            routes=app.routes,
        )
        for route in app.routes:
            if getattr(route, "include_in_schema", None):
                for exception in extract_exceptions(route):
                    write_response(openapi_schema, route, exception)
        app.openapi_schema = openapi_schema
        return app.openapi_schema

    return _custom_openapi
