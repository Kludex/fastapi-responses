from fastapi import FastAPI
from fastapi.testclient import TestClient

from fastapi_responses import custom_openapi

app = FastAPI()


@app.get("/")
def home():
    return "Hello World!"


app.openapi = custom_openapi(app)


client = TestClient(app)


def test_simple_app():
    res = client.get("/")
    assert res.status_code == 200
    openapi_json: dict = client.get("/openapi.json/").json()
    openapi_dict: dict = openapi_json["paths"]["/"]["get"]["responses"]
    assert openapi_dict.get("200")
