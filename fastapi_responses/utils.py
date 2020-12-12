import importlib
import inspect
import tokenize
import typing
from collections import defaultdict
from inspect import iscoroutinefunction, isfunction
from io import BytesIO
from queue import LifoQueue
from tokenize import Token, TokenInfo
from types import FunctionType
from typing import Generator, Iterable, List, Tuple

from fastapi import FastAPI
from fastapi.params import Depends
from fastapi.routing import APIRoute
from starlette.exceptions import HTTPException


def build_statement(exc: TokenInfo, tokens: Generator[TokenInfo, None, None]) -> str:
    statement = exc.string
    while True:
        token = next(tokens)
        statement += token.string.replace("\n", "")
        if token.type == tokenize.NEWLINE:
            return statement


def get_dependencies(endpoint: callable) -> callable:
    dependencies = []
    signature = inspect.signature(endpoint)
    for param in signature.parameters.values():
        default = param.default
        if isinstance(default, Depends):
            dependencies.append(default.dependency)
    return dependencies


def is_function_or_coroutine(obj):
    return isfunction(obj) or iscoroutinefunction(obj)


def exceptions_functions(
    endpoint: callable, tokens: Iterable[TokenInfo]
) -> Tuple[List[Exception], List[callable]]:
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
        if str(exc.status_code) not in api_schema["paths"][path][method]["responses"]:
            api_schema["paths"][path][method]["responses"][exc.status_code] = {
                "description": exc.detail
            }
