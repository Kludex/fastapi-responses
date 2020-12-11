import importlib
import inspect
import tokenize
import typing
from inspect import iscoroutinefunction, isfunction
from io import BytesIO
from queue import LifoQueue
from tokenize import TokenInfo
from types import FunctionType
from typing import Generator

from fastapi import FastAPI
from fastapi.params import Depends
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


def analyze(app: FastAPI):
    for route in app.routes:
        if getattr(route, "include_in_schema", None):
            stack = LifoQueue()
            stack.put(getattr(route, "endpoint"))
            while not stack.empty():
                endpoint = stack.get()
                for dependency in get_dependencies(endpoint):
                    stack.put(dependency)
                source = inspect.getsource(endpoint)
                module = importlib.import_module(endpoint.__module__)
                tokens = tokenize.tokenize(BytesIO(source.encode("utf-8")).readline)
                try:
                    while True:
                        token = next(tokens)
                        try:
                            obj = getattr(module, token.string)
                            if inspect.isclass(obj):
                                statement = build_statement(token, tokens)
                                http_exc = eval(statement)
                                if isinstance(http_exc, HTTPException):
                                    print(repr(http_exc))
                            if is_function_or_coroutine(obj) and obj is not endpoint:
                                stack.put(obj)
                        except Exception:
                            continue
                except StopIteration:
                    ...
    print()
