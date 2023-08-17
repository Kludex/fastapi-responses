import ast
from dataclasses import dataclass
from importlib import import_module
from inspect import getsource, isclass, isfunction, signature
from typing import Any, Callable, List, Type, Union

import libcst as cst
from fastapi.params import Depends
from fastapi.routing import APIRoute
from starlette.exceptions import HTTPException


@dataclass
class ExceptionArgs:
    status_code: int
    detail: Union[str, None]
    exception_class: Union[type[HTTPException], Any]


def get_args_with_parentheses(
    node_exp: cst.BaseExpression, module: str, base_exception: HTTPException
) -> Union[ExceptionArgs, None]:
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

    if isinstance(status_code, str):
        return ExceptionArgs(int(status_code), detail, exception_class)
    return None


def get_args_without_parentheses(
    node_exp: cst.BaseExpression, module: str, base_exception: HTTPException
) -> Union[ExceptionArgs, None]:
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


NODE_TO_PARSE: dict[
    Type[cst.BaseExpression], Callable[..., Union[ExceptionArgs, None]]
] = {
    cst.Call: get_args_with_parentheses,
    cst.Name: get_args_without_parentheses,
}


class RouterExceptionVisitor(cst.CSTVisitor):
    def __init__(self, endpoint, base_exception):
        self.http_exceptions: List[HTTPException] = []
        self.module = import_module(endpoint.__module__)
        self.base_exception = base_exception
        self.functions_to_visit = [endpoint]

    def visit_Call(self, node: cst.Call) -> None:
        func_name = None
        if isinstance(node.func, cst.Attribute):
            func_name = node.func.attr.value
        elif isinstance(node.func, cst.Name):
            func_name = node.func.value

        if func_name:
            module = import_module(self.module.__name__)
            func_or_class = getattr(module, func_name, None)
            if func_or_class:
                if isfunction(func_or_class):
                    self.functions_to_visit.append(func_or_class)
                elif isclass(func_or_class):
                    init_method = getattr(func_or_class, "__init__", None)
                    if init_method and isfunction(init_method):
                        self.functions_to_visit.append(init_method)
                    else:
                        self.functions_to_visit.append(func_or_class)

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
) -> List[HTTPException]:
    stack: list[Callable] = [endpoint]
    http_exceptions = []
    visited = set()

    while len(stack) > 0:
        func_or_class = stack.pop()
        sig = signature(func_or_class)
        for value in sig.parameters.values():
            if "Depends" in str(value) and hasattr(value.default, "dependency"):
                dependency: Depends = value.default
                stack.append(dependency.dependency)  # type: ignore

        if func_or_class in visited:  # Skip if already visited
            continue
        visited.add(func_or_class)  # Mark as visited
        try:
            source = getsource(func_or_class)
            print(f"getting {func_or_class}")
            abstract_syntax_tree = cst.parse_module(source)
            visitor = RouterExceptionVisitor(func_or_class, base_exception)
            abstract_syntax_tree.visit(visitor)

            http_exceptions.extend(visitor.http_exceptions)
            stack.extend(
                f for f in visitor.functions_to_visit if f not in visited
            )  # Only add unvisited functions
        except Exception as error:
            ...

        print(f"NOW -> {len(http_exceptions)}")
    print(f"VISITED {len(visited)}")
    return http_exceptions


# def extract_exceptions(
#     endpoint: Callable[..., Any], base_exception=HTTPException
# ) -> List[HTTPException]:
#     visitor = RouterExceptionVisitor(endpoint, base_exception)
#     while visitor.functions_to_visit:
#         function = visitor.functions_to_visit.pop()
#         source = getsource(function)
#         abstract_syntax_tree = cst.parse_module(source)
#         abstract_syntax_tree.visit(visitor)
#     return visitor.http_exceptions


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
