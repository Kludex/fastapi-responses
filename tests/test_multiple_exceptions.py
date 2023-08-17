import pytest
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.testclient import TestClient

from fastapi_responses import custom_openapi

app = FastAPI()


def raise_another():
    raise HTTPException(status_code=401, detail="Another function!")


async def get_another_user():
    raise HTTPException(status_code=402, detail="Yet another function!")


def get_user(opa: str = Depends(get_another_user)):
    raise HTTPException(status_code=403, detail="HAHA")


class NoNeedParanthesis(HTTPException):
    def __init__(self, status_code=407, detail="WOW!"):
        super().__init__(status_code=status_code, detail=detail)


@app.get("/")
def home(item: int, user: str = Depends(get_user)):
    if item == 1:
        raise HTTPException(
            status_code=404, detail="I need a really long sentence so I can analyze..."
        )
    if item == 2:
        exception = HTTPException(
            status_code=405, detail="I hate this parsing thing :((((("
        )
        raise exception

    if item == 3:
        raise HTTPException(
            status_code=status.HTTP_406_NOT_ACCEPTABLE, detail="Hillow hillow"
        )

    if item == 4:
        raise NoNeedParanthesis

    if item == 5:
        raise NoNeedParanthesis(status_code=408)

    raise_another()


app.openapi = custom_openapi(app)

client = TestClient(app)


@pytest.fixture
def prepare_test():
    openapi: dict = client.get("/openapi.json/").json()["paths"]["/"]["get"][
        "responses"
    ]
    assert type(openapi) is dict
    print(openapi)
    yield openapi


def test_function_callable_inside_router(prepare_test: dict):
    assert prepare_test.get("401")


def test_depends_of_router(prepare_test: dict):
    assert prepare_test.get("402")
    assert prepare_test.get("403")


def test_exception_with_paranthesis_inside_router(prepare_test: dict):
    assert prepare_test.get("404")


def test_exception_without_paranthesis_inside_router(prepare_test: dict):
    assert prepare_test.get("405")


def test_exception_with_fastapi_status(prepare_test: dict):
    assert prepare_test.get("406")


def test_custom_exception_without_paranthesis(prepare_test: dict):
    assert prepare_test.get("407")


def test_custom_exception_with_paranthesis(prepare_test: dict):
    assert prepare_test.get("408")


# def test_exception_outside_router(prepare_test: dict):
#     assert prepare_test.get("408")
