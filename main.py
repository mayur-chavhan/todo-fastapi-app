from fastapi import Depends, FastAPI, HTTPException, Path
from sqlalchemy.orm import Session
from typing import Annotated
from database import SessionLocal, engine
import models

app = FastAPI()

models.Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


db_depedency = Annotated[Session, Depends(get_db)]


@app.get("/")
async def read_all_todos(db: db_depedency):
    return db.query(models.Todos).all()


@app.get("/todos/{todo_id}")
async def get_todo_id(db: db_depedency, todo_id: int = Path(gt=0)):
    total_todos = db.query(models.Todos).filter(models.Todos.id == todo_id).first()

    if total_todos is not None:
        return total_todos
    raise HTTPException(status_code=404, detail="To Dos not found")
