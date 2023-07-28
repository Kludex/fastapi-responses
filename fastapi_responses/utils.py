from importlib import import_module
from inspect import getsource, iscoroutinefunction, isfunction
from libcst._nodes.expression import Call
import re
from typing import Dict, List, Tuple

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


class GetHTTPExceptions(cst.CSTVisitor):
    def __init__(self, endpoint):
        self.http_exceptions: List[HTTPException] = []
        self.current_module_functions = []
        self.module = import_module(endpoint.__module__)


    def visit_Call(self, node: Call) -> bool | None:
        if node.func.value == 'HTTPException':
            temp = generate_args(node.args[0].value.value, node.args[1].value.value)
            temp_HTTPException = HTTPException(temp[0], temp[1])
            self.http_exceptions.append(temp_HTTPException)
        
        else:
            if isinstance(node.func.value, str):
                if node.func.value != 'Depends':
                    current_function_name = node.func.value
                else:
                    current_function_name = node.args[0].value.value
                self.current_module_functions.append(getattr(self.module, current_function_name))


def extract_exceptions(route: APIRoute) -> List[HTTPException]:
    functions = []
    exceptions = []
    functions.append(getattr(route, "endpoint"))
    while len(functions) > 0:
        endpoint = functions.pop()
        visitor = GetHTTPExceptions(endpoint)
        source = getsource(endpoint)
        tree = cst.parse_module(source)
        tree.visit(visitor)
        exceptions.extend(visitor.http_exceptions)
        functions.extend(visitor.current_module_functions)
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

