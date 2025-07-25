from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from domain.user.value_objects import UserRole
from typing import Annotated
from config import get_settings

settings = get_settings()

SECRET_KEY = settings.SECRET_KEY
ALGORITHM = settings.ALGORITHM

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")

def get_current_user_role(token: str = Depends(oauth2_scheme)) -> UserRole:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        role = payload.get("role")
        if not role:
            raise ValueError("Missing role in token")
        return UserRole(role)
    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
        )

def only_admins(role: Annotated[UserRole, Depends(get_current_user_role)]) -> None:
    if role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="You don't have permission to access this resource.")

def admins_or_owners(role: Annotated[UserRole, Depends(get_current_user_role)]) -> None:
    if role not in [UserRole.ADMIN, UserRole.OWNER]:
        raise HTTPException(status_code=403, detail="You don't have permission to access this resource.")