import ast
from dataclasses import dataclass
from importlib import import_module
from inspect import getsource
from typing import Any, Callable, Type

import libcst as cst
from fastapi.routing import APIRoute
from starlette.exceptions import HTTPException


@dataclass
class ExceptionArgs:
    status_code: int
    detail: str | None
    exception_class: type[HTTPException] | Any


def get_args_with_parentheses(
    node_exp: cst.BaseExpression, module: str, base_exception: HTTPException
) -> ExceptionArgs | None:
    call_name = node_exp.func.value if isinstance(node_exp.func, cst.Name) else ""
    exception_class = getattr(module, call_name, None) if call_name else None
    is_exception = (
        exception_class
        and issubclass(exception_class, Exception)
        and issubclass(exception_class, base_exception)
    )
    status_code = None
    detail = None
    for arg in node_exp.args:
        if isinstance(arg.keyword, cst.Name) and arg.keyword.value == "status_code":
            status_code = arg.value.value

        elif isinstance(arg.keyword, cst.Name) and arg.keyword.value == "detail":
            detail = ast.literal_eval(arg.value.value)

    if is_exception and not status_code:
        status_code = exception_class().status_code

    if is_exception and not detail:
        detail = exception_class().detail

    if isinstance(status_code, int):
        return ExceptionArgs(status_code, detail, exception_class)
    return None


def get_args_without_parentheses(
    node_exp: cst.BaseExpression, module: str, base_exception: HTTPException
) -> ExceptionArgs | None:
    exception_class = getattr(module, node_exp.value, None)
    is_exception = (
        exception_class
        and issubclass(exception_class, Exception)
        and issubclass(exception_class, base_exception)
    )
    status_code = None
    detail = None
    if is_exception:
        status_code = exception_class().status_code
        detail = exception_class().detail

    if isinstance(status_code, int):
        return ExceptionArgs(status_code, detail, exception_class)
    return None


NODE_TO_PARSE: dict[Type[cst.BaseExpression], Callable[..., ExceptionArgs | None]] = {
    cst.Call: get_args_with_parentheses,
    cst.Name: get_args_without_parentheses,
}


class RouterExceptionVisitor(cst.CSTVisitor):
    def __init__(self, endpoint, base_exception):
        self.http_exceptions: list[HTTPException] = []
        self.module = import_module(endpoint.__module__)
        self.base_exception = base_exception
        self.constant_values = {}

    def visit_Raise(self, node: cst.Raise):
        # Check if the exception is being raised with parentheses
        assert node.exc is not None
        strategy = NODE_TO_PARSE.get(type(node.exc), None)
        assert strategy is not None
        result = strategy(node.exc, self.module, self.base_exception)
        if result:
            temp_HTTPException: HTTPException = result.exception_class(
                result.status_code, result.detail
            )
            self.http_exceptions.append(temp_HTTPException)


def extract_exceptions(
    endpoint: Callable[..., Any], base_exception=HTTPException
) -> list[HTTPException]:
    source = getsource(endpoint)
    abstract_syntax_tree = cst.parse_module(source)
    visitor = RouterExceptionVisitor(endpoint, base_exception)
    abstract_syntax_tree.visit(visitor)
    return visitor.http_exceptions


def add_exception_to_openapi_schema(
    openapi_schema: dict, route: APIRoute, exc: HTTPException
) -> None:
    path = getattr(route, "path")
    methods = [method.lower() for method in getattr(route, "methods")]
    for method in methods:
        status_code = str(exc.status_code)
        if status_code not in openapi_schema["paths"][path][method]["responses"]:
            response_schema = {
                "description": exc.__class__.__name__,
                "content": {
                    "application/json": {
                        "schema": {
                            "type": "object",
                            "properties": {
                                "detail": {"type": "string", "example": exc.detail}
                            },
                        }
                    }
                },
            }
            openapi_schema["paths"][path][method]["responses"][
                status_code
            ] = response_schema
