import os

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from starlette.exceptions import HTTPException

STUDENT_N = int(os.getenv("STUDENT_N", 1))

app = FastAPI(title=f"Inventory Service N{STUDENT_N}")

BASE_ID = 100 * STUDENT_N

# Імітація бази даних: ID починаються зі 100 * N
STOCK = {
    BASE_ID + 1: {"id": BASE_ID + 1, "name": "Laptop",
                  "quantity": 5, "price": 1000.0},
    BASE_ID + 2: {"id": BASE_ID + 2, "name": "Mouse",
                  "quantity": 50, "price": 25.0},
    BASE_ID + 3: {"id": BASE_ID + 3, "name": "Keyboard",
                  "quantity": 0, "price": 100.0},
}


class StockUpdate(BaseModel):
    product_id: int
    delta: int  # на скільки змінити залишок (+10 або -3)


@app.exception_handler(HTTPException)
async def http_error(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"student_id": STUDENT_N, "detail": exc.detail},
    )


@app.exception_handler(RequestValidationError)
async def validation_error(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={"student_id": STUDENT_N, "detail": "Invalid request"},
    )


@app.get("/stock/{product_id}")
def get_stock(product_id: int):
    """Перевірка кількості товару на складі"""
    if product_id not in STOCK:
        raise HTTPException(status_code=404, detail="Product not found")
    return {"student_id": STUDENT_N, "data": STOCK[product_id]}


@app.post("/stock/update")
def update_stock(upd: StockUpdate):
    """Зміна залишків (delta може бути від'ємною)"""
    if upd.product_id not in STOCK:
        raise HTTPException(status_code=404, detail="Product not found")
    item = STOCK[upd.product_id]
    new_qty = item["quantity"] + upd.delta
    if new_qty < 0:
        raise HTTPException(status_code=400, detail="Stock cannot be negative")
    item["quantity"] = new_qty
    return {"student_id": STUDENT_N, "data": item}
