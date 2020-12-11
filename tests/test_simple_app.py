from fastapi import Depends, FastAPI, HTTPException
from fastapi.testclient import TestClient
from fastapi_responses import custom_openapi

app = FastAPI()


def raise_another():
    raise HTTPException(status_code=200, detail="Another function!")


def get_user():
    raise HTTPException(status_code=201, detail="HAHA")


@app.get("/")
def home(item: int, user: str = Depends(get_user)):
    if item == 1:
        raise HTTPException(
            status_code=404, detail="I need a really long sentence so I can analyze..."
        )
    raise_another()


app.openapi = custom_openapi(app)

client = TestClient(app)

openapi_schema = {
    "openapi": "3.0.2",
    "info": {"title": "FastAPI", "version": "0.1.0"},
    "paths": {
        "/": {
            "get": {
                "summary": "Home",
                "operationId": "home__get",
                "responses": {
                    "200": {
                        "description": "Successful Response",
                        "content": {"application/json": {"schema": {}}},
                    }
                },
            }
        }
    },
}


def test_simple_app():
    openapi = client.get("/openapi.json/")
    print(openapi.json())
    assert openapi.json() == openapi_schema
    assert False
