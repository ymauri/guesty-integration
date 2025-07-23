from fastapi import APIRouter, Depends, HTTPException, status
from shared.dependencies import get_current_user_role
from domain.user.value_objects import UserRole
from application.auth_service import AuthService
from infrastructure.repositories.user_repository import SQLAlchemyUserRepository
from api.v1.schemas.auth_schema import RegisterRequest

router = APIRouter()
auth_service = AuthService(user_repository=SQLAlchemyUserRepository())

@router.get("/admin-only")
def admin_view(role: UserRole = Depends(get_current_user_role)):
    if role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Admins only")
    return {"message": "Welcome, admin!"}

@router.post("/register", status_code=status.HTTP_201_CREATED)
def register_user(request: RegisterRequest):
    try:
        auth_service.register_user(
            email=request.email,
            password=request.password,
            role=request.role
        )
        return {"message": "User registered successfully"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
