from fastapi import FastAPI

# from database import engine
# import models
from router import auth, todos, admin, users

# This creates FastAPI into an instance which later being used for creating endpoints.
app = FastAPI()

# models.Base.metadata.create_all(bind=engine)

app.include_router(admin.router)
app.include_router(auth.router)
app.include_router(todos.router)
app.include_router(users.router)
