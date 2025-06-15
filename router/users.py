# Here is your opportunity to keep learning!

# 1. Create a new route called Users.

# 2. Then create 2 new API Endpoints

# get_user: this endpoint should return all information about the user that is currently logged in.

# change_password: this endpoint should allow a user to change their current password.

from fastapi import Depends, APIRouter, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from typing import Annotated
from database import SessionLocal
from models import Users
from .auth import get_current_user, bcrypt_context, BaseModel
from .todos import Field

# This creates FastAPI into an instance which later being used for creating endpoints.
router = APIRouter(prefix="/users", tags=["Users"])


class ChangePassword(BaseModel):
    current_password: str = Field(min_length=1, description="Current password")
    new_password: str = Field(
        min_length=6, description="New password (minimum 6 characters)"
    )


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


db_dependency = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[dict, Depends(get_current_user)]


@router.get("/", status_code=status.HTTP_200_OK)
async def get_current_user_info(user: user_dependency, db: db_dependency):
    """Get information about the currently logged-in user."""
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required"
        )

    user_info = db.query(Users).filter(Users.id == user.get("id")).first()
    if not user_info:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    return user_info


@router.put("/password", status_code=status.HTTP_200_OK)
async def change_password(
    user: user_dependency, db: db_dependency, password_data: ChangePassword
):
    """Change the current user's password."""
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required"
        )

    # Get user from database
    user_model = db.query(Users).filter(Users.id == user.get("id")).first()
    if not user_model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    # Verify current password
    if not bcrypt_context.verify(
        password_data.current_password, user_model.hashed_password
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Current password is incorrect",
        )

    # Check if new password is different from current
    if bcrypt_context.verify(password_data.new_password, user_model.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password must be different from current password",
        )

    try:
        # Hash new password and update
        user_model.hashed_password = bcrypt_context.hash(password_data.new_password)

        db.add(user_model)
        db.commit()
        db.refresh(user_model)

        return {"message": "Password updated successfully"}

    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update password",
        )
