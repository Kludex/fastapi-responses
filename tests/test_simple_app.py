from fastapi import FastAPI
from fastapi.testclient import TestClient

from fastapi_responses import custom_openapi

app = FastAPI()

app.openapi = custom_openapi(app)


@app.get("/")
def home():
    return "Hello World!"


client = TestClient(app)

openapi_schema = {
    "openapi": "3.1.0",
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
    res = client.get("/")
    assert res.status_code == 200

    res = client.get("/openapi.json/")
    assert res.json() == openapi_schema
