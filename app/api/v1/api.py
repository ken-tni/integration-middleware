from fastapi import APIRouter
from app.api.v1.endpoints import customers, products, quotations, invoices

api_router = APIRouter()

# Include routers for different endpoints
api_router.include_router(customers.router, prefix="/v1/customers", tags=["customers"])
api_router.include_router(products.router, prefix="/v1/products", tags=["products"])
api_router.include_router(quotations.router, prefix="/v1/quotations", tags=["quotations"])
api_router.include_router(invoices.router, prefix="/v1/invoices", tags=["invoices"]) 