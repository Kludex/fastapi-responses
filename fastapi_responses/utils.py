import importlib
import inspect
import tokenize
from inspect import iscoroutinefunction, isfunction
from io import BytesIO
from tokenize import TokenInfo
from typing import Callable, Generator, List, Tuple

from fastapi.routing import APIRoute
from starlette.exceptions import HTTPException


def build_statement(exc: TokenInfo, tokens: Generator[TokenInfo, None, None]) -> str:
    statement = exc.string
    while True:
        token = next(tokens)
        statement += token.string.replace("\n", "")
        if token.type == tokenize.NEWLINE:
            return statement


def is_function_or_coroutine(obj):
    return isfunction(obj) or iscoroutinefunction(obj)


def exceptions_functions(
    endpoint: Callable, tokens: Generator[TokenInfo, None, None]
) -> Tuple[List[Exception], List[Callable]]:
    exceptions, functions = [], []
    module = importlib.import_module(endpoint.__module__)
    try:
        while True:
            token = next(tokens)
            try:
                obj = getattr(module, token.string)
                if inspect.isclass(obj):
                    statement = build_statement(token, tokens)
                    http_exc = eval(statement)
                    if isinstance(http_exc, HTTPException):
                        exceptions.append(http_exc)
                if is_function_or_coroutine(obj) and obj is not endpoint:
                    functions.append(obj)
            except Exception:
                ...
    except StopIteration:
        ...
    return exceptions, functions


def extract_exceptions(route: APIRoute) -> List[HTTPException]:
    exceptions = []
    functions = []
    functions.append(getattr(route, "endpoint"))
    while len(functions) > 0:
        endpoint = functions.pop()
        source = inspect.getsource(endpoint)
        tokens = tokenize.tokenize(BytesIO(source.encode("utf-8")).readline)
        _exceptions, _functions = exceptions_functions(endpoint, tokens)
        exceptions.extend(_exceptions)
        functions.extend(_functions)
    return exceptions


def write_response(api_schema: dict, route: APIRoute, exc: HTTPException) -> None:
    path = getattr(route, "path")
    methods = [method.lower() for method in getattr(route, "methods")]
    for method in methods:
        status_code = str(exc.status_code)
        if status_code not in api_schema["paths"][path][method]["responses"]:
            api_schema["paths"][path][method]["responses"][status_code] = {
                "description": exc.detail
            }
