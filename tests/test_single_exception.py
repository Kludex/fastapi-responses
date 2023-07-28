from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient

from fastapi_responses import custom_openapi

app = FastAPI()

app.openapi = custom_openapi(app)


@app.get("/{item_id}")
def get_item(item_id: int):
    if item_id == 0:
        raise HTTPException(status_code=404, detail="Item not found.")
    return "Item exists!"


client = TestClient(app)

openapi_schema = {
    "openapi": "3.1.0",
    "info": {"title": "FastAPI", "version": "0.1.0"},
    "paths": {
        "/{item_id}": {
            "get": {
                "summary": "Get Item",
                "operationId": "get_item__item_id__get",
                "parameters": [
                    {
                        "required": True,
                        "schema": {"title": "Item Id", "type": "integer"},
                        "name": "item_id",
                        "in": "path",
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
                    "404": {"description": "Item not found."},
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


def test_simple_app():
    res = client.get("/1")
    assert res.status_code == 200

    res = client.get("/0")
    assert res.status_code == 404

    res = client.get("/openapi.json/")
    assert res.json() == openapi_schema
