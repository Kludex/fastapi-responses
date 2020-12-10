from fastapi import FastAPI


def inspect(app: FastAPI):
    for route in app.routes:
        print(route.handle.)
