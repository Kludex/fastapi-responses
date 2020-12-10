import inspect
import re
from typing import Callable


class CustomException(Exception):
    status_code = 400


def func2(num: int):
    if num == 3:
        raise CustomException("meat")


def func(num: int):
    if num == 1:
        raise CustomException("potato")
    if num > 2:
        func2(num)
    return num


def print_exception_object(function: Callable):
    for line in function.split("\n"):
        if line.strip().startswith("raise"):
            for name in re.split(" |\(", line):
                try:
                    class_obj = globals()[name]
                    print(class_obj.status_code)
                except:
                    continue


lines = inspect.getsource(func).split("\n")
for line in lines:
    #    if 'raise' in line:
    #        print(line)
    for name in re.split(" |\(", line):
        try:
            functions = inspect.getsource(locals()[name]).split("\n")
            for function in functions:
                print_exception_object(function)
        except:
            ...
