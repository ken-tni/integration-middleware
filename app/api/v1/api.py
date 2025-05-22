from fastapi import APIRouter
from app.api.v1.endpoints import customers, products, quotations, invoices, auth, websocket

api_router = APIRouter()

# Include routers for different endpoints
api_router.include_router(auth.router, prefix="/v1/auth", tags=["authentication"])
api_router.include_router(customers.router, prefix="/v1/customers", tags=["customers"])
api_router.include_router(products.router, prefix="/v1/products", tags=["products"])
api_router.include_router(quotations.router, prefix="/v1/quotations", tags=["quotations"])
api_router.include_router(invoices.router, prefix="/v1/invoices", tags=["invoices"])
api_router.include_router(websocket.router, prefix="/v1/ws", tags=["websocket"]) 