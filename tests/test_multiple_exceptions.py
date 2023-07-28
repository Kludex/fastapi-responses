from fastapi import Depends, FastAPI, HTTPException
from fastapi.testclient import TestClient

from fastapi_responses import custom_openapi

app = FastAPI()


def raise_another():
    raise HTTPException(status_code=200, detail="Another function!")


async def get_another_user():
    raise HTTPException(status_code=304, detail="Yet another function!")


def get_user(opa: str = Depends(get_another_user)):
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
    "openapi": "3.1.0",
    "info": {"title": "FastAPI", "version": "0.1.0"},
    "paths": {
        "/": {
            "get": {
                "summary": "Home",
                "operationId": "home__get",
                "parameters": [
                    {
                        "required": True,
                        "schema": {"title": "Item", "type": "integer"},
                        "name": "item",
                        "in": "query",
                    }
                ],
                "responses": {
                    "200": {
                        "description": "Successful Response",
                        "content": {"application/json": {"schema": {}}},
                    },
                    "422": {
                        "description": "Validation Error",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/HTTPValidationError"
                                }
                            }
                        },
                    },
                    "404": {
                        "description": (
                            "I need a really long sentence so I can analyze..."
                        )
                    },
                    "201": {"description": "HAHA"},
                    "304": {"description": "Yet another function!"},
                },
            }
        }
    },
    "components": {
        "schemas": {
            "HTTPValidationError": {
                "title": "HTTPValidationError",
                "type": "object",
                "properties": {
                    "detail": {
                        "title": "Detail",
                        "type": "array",
                        "items": {"$ref": "#/components/schemas/ValidationError"},
                    }
                },
            },
            "ValidationError": {
                "title": "ValidationError",
                "required": ["loc", "msg", "type"],
                "type": "object",
                "properties": {
                    "loc": {
                        "title": "Location",
                        "type": "array",
                        "items": {"anyOf": [{"type": "string"}, {"type": "integer"}]},
                    },
                    "msg": {"title": "Message", "type": "string"},
                    "type": {"title": "Error Type", "type": "string"},
                },
            },
        }
    },
}


def test_multiple_exceptions():
    openapi = client.get("/openapi.json/")
    print(openapi.json())
    assert openapi.json() == openapi_schema
