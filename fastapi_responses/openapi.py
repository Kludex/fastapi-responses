from fastapi import FastAPI
from fastapi.routing import APIRoute
from starlette.exceptions import HTTPException

from fastapi_responses.utils import add_exception_to_openapi_schema, extract_exceptions


def custom_openapi(app: FastAPI, base_exception=HTTPException):
    def _custom_openapi():
        for route in app.routes:
            is_rest_api = isinstance(route, APIRoute)
            if is_rest_api:
                found_exceptions = extract_exceptions(
                    endpoint=route.endpoint,
                    base_exception=base_exception,
                )
                for exception in found_exceptions:
                    add_exception_to_openapi_schema(openapi_schema, route, exception)
        return app.openapi_schema

    openapi_schema = app.openapi()
    app.openapi = _custom_openapi  # type: ignore
    app.openapi_schema = _custom_openapi()
    return app.openapi
