from fastapi import APIRouter

billing_router = APIRouter(prefix="/billing", tags=["billing"])

# @auth_router.post("/register", status_code=201)
