from importlib import import_module
from inspect import getsource, iscoroutinefunction, isfunction
from typing import Dict, List, Tuple

import libcst as cst
from fastapi.routing import APIRoute
from libcst._nodes.expression import Call, Integer
from starlette.exceptions import HTTPException


def generate_args(status_code: str, detail: str) -> Tuple[int, str]:
    detail_f = detail[1:-1]
    status_code_f = int(status_code)

    return (status_code_f, detail_f)


class GetHTTPExceptions(cst.CSTVisitor):
    def __init__(self, endpoint):
        self.http_exceptions: List[HTTPException] = []
        self.current_module_functions = []
        self.module = import_module(endpoint.__module__)

    def visit_Call(self, node: Call):
        if node.func.value == "HTTPException":
            if isinstance(node.args[0].value, Integer):
                status_temp = node.args[0].value.value
            else:
                status_temp = node.args[0].value.attr.value[5:8]
            detail_temp = node.args[1].value.value

            status, detail = generate_args(status_temp, detail_temp)
            temp_HTTPException = HTTPException(status, detail)
            self.http_exceptions.append(temp_HTTPException)

        else:
            if isinstance(node.func.value, str):
                if node.func.value != "Depends":
                    current_function_name = node.func.value
                else:
                    current_function_name = node.args[0].value.value
                self.current_module_functions.append(
                    getattr(self.module, current_function_name)
                )


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
