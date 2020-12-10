from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from fastapi_responses import custom_openapi

app = FastAPI()


@app.get("/")
def home():
    raise HTTPException(status_code=404)


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
    openapi = client.get("/openapi.json")
    print(openapi.json())
    assert openapi.json() == openapi_schema
    assert False
