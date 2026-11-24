import os

import requests
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from starlette.exceptions import HTTPException

STUDENT_N = int(os.getenv("STUDENT_N", 1))
# Звертаємося до іншого контейнера по імені сервісу з docker-compose
INVENTORY_URL = os.getenv("INVENTORY_URL", "http://inventory-service:8000")

app = FastAPI(title=f"Order Service N{STUDENT_N}")

ORDERS = []


class OrderRequest(BaseModel):
    product_id: int
    quantity: int


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


@app.post("/orders")
def create_order(order: OrderRequest):
    """Створює замовлення, попередньо перевіривши склад в Inventory Service"""
    if order.quantity <= 0:
        raise HTTPException(status_code=400, detail="Quantity must be > 0")

    # 1. Синхронний HTTP-запит до іншого мікросервісу
    try:
        resp = requests.get(
            f"{INVENTORY_URL}/stock/{order.product_id}", timeout=5)
    except requests.exceptions.RequestException:
        raise HTTPException(status_code=503,
                            detail="Inventory Service is unavailable")

    # 2. Чи існує товар
    if resp.status_code == 404:
        raise HTTPException(status_code=400, detail="Product does not exist")

    item = resp.json()["data"]

    # 3. Чи вистачає на складі
    if item["quantity"] < order.quantity:
        raise HTTPException(status_code=400, detail="Not enough stock")

    # 4. Створюємо замовлення
    new_order = {
        "student_id": STUDENT_N,
        "order_id": len(ORDERS) + 1,
        "product_id": order.product_id,
        "product_name": item["name"],
        "quantity": order.quantity,
        "total_price": item["price"] * order.quantity,
        "status": "Created",
    }
    ORDERS.append(new_order)
    return new_order


@app.get("/orders")
def get_orders():
    """Список усіх замовлень"""
    return {"student_id": STUDENT_N, "orders": ORDERS}
