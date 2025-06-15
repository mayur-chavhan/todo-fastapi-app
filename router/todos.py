from fastapi import Depends, APIRouter, HTTPException, Path, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from typing import Annotated
from database import SessionLocal, engine
import models
from models import Todos
from .auth import get_current_user

# This creates FastAPI into an instance which later being used for creating endpoints.
router = APIRouter()

# router.include_router(auth.router)
"""
Purpose: Creates all database tables defined in your SQLAlchemy models
How it works:
models.Base is the declarative base class from SQLAlchemy
.metadata contains information about all table schemas
.create_all() creates tables if they don't exist
bind=engine specifies which database engine to use
When it runs: Only once when the application starts

"""
models.Base.metadata.create_all(bind=engine)

"""
Purpose: Creates and manages database sessions for each request
Pattern: This is a Python generator function (uses yield)
How it works:
SessionLocal() creates a new database session
yield db provides the session to whoever calls this function
finally: db.close() ensures the session is always closed, even if an error occurs
Why this pattern: Ensures proper cleanup of database connections
"""


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


"""
Purpose: Creates a reusable type annotation for database dependency injection
Breaking it down:
Annotated is a typing feature that adds metadata to types
Session is the SQLAlchemy session type
Depends(get_db) tells FastAPI to call get_db() function to provide the dependency
Usage: This can be used in function parameters like db: db_depedency
"""
db_depedency = Annotated[Session, Depends(get_db)]
user_depedency = Annotated[dict, Depends(get_current_user)]


# This class is required for POST and PUT to take input from the Body and We can define the what data it should accept with validation
class TodoRequest(BaseModel):
    title: str = Field(min_length=0)
    description: str = Field(min_length=0, max_length=100)
    priority: int = Field(gt=0, lt=6)
    completed: bool


@router.get("/", status_code=status.HTTP_200_OK)
async def read_all_todos(user: user_depedency, db: db_depedency):
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="User is not authorized"
        )
    return db.query(Todos).filter(Todos.owner_id == user.get("id")).all()


@router.get("/todos/{todo_id}", status_code=status.HTTP_200_OK)
async def get_todo_id(
    user: user_depedency, db: db_depedency, todo_id: int = Path(gt=0)
):
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="User is not authorized"
        )
    total_todos = (
        db.query(Todos)
        .filter(Todos.id == todo_id)
        .filter(Todos.owner_id == user.get("id"))
        .first()
    )

    if total_todos is None:
        raise HTTPException(status_code=404, detail="To Dos not found")
    return total_todos


# Create a POST request to add To Do in Database


@router.post("/todo/", status_code=status.HTTP_201_CREATED)
async def add_todo(user: user_depedency, db: db_depedency, insert_todo: TodoRequest):
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="User is not authorized"
        )

    todo_model = models.Todos(**insert_todo.model_dump(), owner_id=user.get("id"))

    db.add(todo_model)
    db.commit()


# @router.put("/todo/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
# async def update_todo(
#     db: db_depedency, update_todo: TodoRequest, todo_id: int = Path(gt=0)
# ):
#     todo_model: Todos = (
#         db.query(Todos).filter(Todos.id == todo_id).first()
#     )

#     if todo_model is None:
#         raise HTTPException(status_code=404, detail="To Do not found")

#     todo_model.title = update_todo.title
#     todo_model.description = update_todo.description
#     todo_model.priority = update_todo.priority
#     todo_model.completed = update_todo.completed

#     db.add(todo_model)
#     db.commit()


@router.put("/todo/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def update_todo(
    user: user_depedency,
    db: db_depedency,
    update_todo: TodoRequest,
    todo_id: int = Path(gt=0),
):
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="User is not authorized"
        )
    # 1) ensure it exists
    exists = (
        db.query(Todos)
        .filter(Todos.id == todo_id)
        .filter(Todos.owner_id == user.get("id"))
        .first()
    )
    if not exists:
        raise HTTPException(status_code=404, detail="To Do not found")

    # 2) only update fields the client actually sent
    data = update_todo.model_dump(exclude_unset=True)

    # 3) single bulk-UPDATE
    db.query(Todos).filter(Todos.id == todo_id).update(data)
    db.commit()


@router.delete("/todo/{todo_id}", status_code=status.HTTP_200_OK)
async def delete_todo(
    user: user_depedency, db: db_depedency, todo_id: int = Path(gt=0)
):
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="User is not authorized"
        )
    todo_model = (
        db.query(Todos)
        .filter(Todos.id == todo_id)
        .filter(Todos.owner_id == user.get("id"))
        .first()
    )

    if todo_model is None:
        raise HTTPException(status_code=404, detail="To-DO ID not found")

    db.delete(todo_model)
    db.commit()
