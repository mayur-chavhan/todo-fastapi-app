from fastapi import Depends, APIRouter, HTTPException, Path, status
from sqlalchemy.orm import Session
from typing import Annotated
from database import SessionLocal
from models import Todos
from .auth import get_current_user

# This creates FastAPI into an instance which later being used for creating endpoints.
router = APIRouter(prefix="/admin", tags=["Admin"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


db_depedency = Annotated[Session, Depends(get_db)]
user_depedency = Annotated[dict, Depends(get_current_user)]


@router.get("/todo")
async def read_all(user: user_depedency, db: db_depedency):
    if user is None or user.get("role") != "admin":
        raise HTTPException(status_code=401, detail="Not an Admin user")
    return db.query(Todos).all()


@router.delete("/todo/{todo_id}")
async def delete_todo(
    user: user_depedency, db: db_depedency, todo_id: int = Path(gt=0)
):
    if user is None or user.get("role") != "admin":
        raise HTTPException(status_code=401, detail="Not an Admin user")

    todo_model = db.query(Todos).filter(Todos.id == todo_id).first()

    if todo_model is None:
        raise HTTPException(status_code=404, detail="To-DO ID Not FOUND!!")

    db.query(Todos).filter(Todos.id == todo_id).delete()
    db.commit()
