<h1 align="center">
    <strong>FastAPI Responses</strong>
</h1>
<p align="center">
    <a href="https://github.com/Kludex/fastapi-responses" target="_blank">
        <img src="https://img.shields.io/github/last-commit/Kludex/fastapi-responses?style=for-the-badge" alt="Latest Commit">
    </a>
        <!-- <img src="https://img.shields.io/github/workflow/status/ycd/manage-fastapi/Test?style=for-the-badge"> -->
        <img src="https://img.shields.io/codecov/c/github/Kludex/fastapi-responses?style=for-the-badge">
    <br />
    <!-- <a href="https://pypi.org/project/manage-fastapi" target="_blank">
        <img src="https://img.shields.io/pypi/v/manage-fastapi?style=for-the-badge" alt="Package version">
    </a> -->
    <!-- <img src="https://img.shields.io/pypi/pyversions/manage-fastapi?style=for-the-badge"> -->
    <img src="https://img.shields.io/github/license/Kludex/fastapi-responses?style=for-the-badge">
</p>

<p align="center">
    This package is not stable. Do not use in production!
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

app.openapi = custom_openapi

@app.get("/{item_id}")
def get_item(item_id: int):
    if item_id == 0:
        raise HTTPException(status_code=404, detail="Item not found.")
    return "Item exists!"
```

## license

This project is licensed under the terms of the MIT license.
