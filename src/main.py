# -*- coding: utf-8 -*-
import sys
from pathlib import Path
from typing import Optional

import uvicorn
from fastapi import FastAPI, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_DIR))


from src.fund import get_fund_returns

app = FastAPI(title="Alpha Select")
app.mount("/static", StaticFiles(directory="src/static"), name="static")
templates = Jinja2Templates(directory="src/templates")


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/api/fund/{fund_code}")
async def fund_returns_api(fund_code: str, investment_amount: Optional[int] = Query(100000)):
    return get_fund_returns(fund_code, investment_amount)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
