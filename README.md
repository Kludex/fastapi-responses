<h1 align="center">
    <strong>FastAPI Responses</strong>
</h1>
<p align="center">
    <a href="https://github.com/Kludex/fastapi-responses" target="_blank">
        <img src="https://img.shields.io/github/last-commit/Kludex/fastapi-responses" alt="Latest Commit">
    </a>
        <img src="https://img.shields.io/github/workflow/status/Kludex/fastapi-responses/Test">
        <img src="https://img.shields.io/codecov/c/github/Kludex/fastapi-responses">
    <br />
    <a href="https://pypi.org/project/fastapi-responses" target="_blank">
        <img src="https://img.shields.io/pypi/v/fastapi-responses" alt="Package version">
    </a>
    <img src="https://img.shields.io/pypi/pyversions/fastapi-responses">
    <img src="https://img.shields.io/github/license/Kludex/fastapi-responses">
</p>

<p align="center">
    <strong>This package is not stable. Do not use in production!</strong>
</p>

The goal of this package is to have your responses up-to-date according to your exceptions.

## Installation

```bash
pip install fastapi-responses
```

## Usage

```python
from fastapi import FastAPI, HTTPException
from fastapi_responses import custom_openapi

app = FastAPI()

app.openapi = custom_openapi(app)

@app.get("/{item_id}")
def get_item(item_id: int):
    if item_id == 0:
        raise HTTPException(status_code=404, detail="Item not found.")
    return "Item exists!"
```

## License

This project is licensed under the terms of the MIT license.
