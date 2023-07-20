from importlib import import_module
from inspect import getsource, iscoroutinefunction, isfunction
import re
from typing import Callable, Dict, List, Tuple

from fastapi.routing import APIRoute
import libcst as cst
from starlette.exceptions import HTTPException


http_codes = [200, 201, 204, 304, 400, 403, 404, 409, 500]


def is_function_or_coroutine(obj):
    return isfunction(obj) or iscoroutinefunction(obj)


def generate_args(status_code: str, detail: str) -> Tuple[int, str]:
    detail_temp = []
    detail_temp.append(re.findall("'([^']*)'", detail))
    detail_temp.append(re.findall('"([^"]*)"', detail))

    for i in detail_temp:
        if i:
            detail_f = i[0]

    if len(status_code) == 3:
        status_code_f = int(status_code)
    else:
        for code in http_codes:
            if str(code) in status_code:
                status_code_f = code
    return (status_code_f, detail_f)


def exceptions_functions(
    endpoint: Callable,
    tree: cst._nodes.module.Module
) -> Tuple[List[HTTPException], List[Callable]]:
    stack = []
    module = import_module(endpoint.__module__)
    exceptions, functions = [], []
    stack.append(tree.body)

    while stack:
        current = stack.pop()

        if isinstance(current, tuple):
            for node in current:
                stack.append(node)
        else:
            if isinstance(current, cst._nodes.statement.Raise):
                if current.exc.func.value == 'HTTPException':
                    if getattr(current.exc.args[0].value, "attr", None):
                        _code = current.exc.args[0].value
                        code = _code.value.value + "." + _code.attr.value
                    else:
                        code = current.exc.args[0].value.value 
                    detail = current.exc.args[1].value.value
                    temp = generate_args(code, detail)
                    exceptions.append(HTTPException(temp[0], temp[1]))
            else:
                if isinstance(current, cst._nodes.statement.Expr):
                    functions.append(getattr(module, current.value.func.value))
                    continue
                if isinstance(current, cst._nodes.statement.FunctionDef):
                    params = current.params.params
                    for param in params:
                        if isinstance(param.default, cst._nodes.expression.Call):
                            for arg in param.default.args:
                                obj = getattr(module, arg.value.value)
                                if is_function_or_coroutine(obj):
                                    functions.append(obj)
                condition_1 = isinstance(current, cst._nodes.base.CSTNode)
                condition_2 = isinstance(
                    current, cst._nodes.statement.BaseSmallStatement
                    )
                if condition_1 and not condition_2:
                    stack.append(current.body)
    
    return exceptions, functions


def extract_exceptions(route: APIRoute) -> List[HTTPException]:
    exceptions = []
    functions = []
    functions.append(getattr(route, "endpoint"))
    while len(functions) > 0:
        endpoint = functions.pop()
        source = getsource(endpoint)
        tree = cst.parse_module(source)
        _exceptions, _functions = exceptions_functions(endpoint, tree)
        exceptions.extend(_exceptions)
        functions.extend(_functions)
    return exceptions


def write_response(api_schema: Dict, route: APIRoute, exc: HTTPException) -> None:
    path = getattr(route, "path")
    methods = [method.lower() for method in getattr(route, "methods")]
    for method in methods:
        status_code = str(exc.status_code)
        if status_code not in api_schema["paths"][path][method]["responses"]:
            api_schema["paths"][path][method]["responses"][status_code] = {
                "description": exc.detail
            }
