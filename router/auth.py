from datetime import timedelta, datetime, timezone
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from models import Users
from passlib.context import CryptContext
from database import SessionLocal
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from jose import JWTError, jwt

router = APIRouter(prefix="/auth", tags=["Auth"])

# generate secret key using : openssl rand -hex 32
SECRET_KEY = "a16f07be0304ad98d1fb0fc661e2efc394a94e0a2c3a49f2c69ebdc55076e566"
ALGORITHM = "HS256"

bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_bearer = OAuth2PasswordBearer(tokenUrl="/auth/token")


class CreateUserAuth(BaseModel):
    username: str
    email: str
    first_name: str
    last_name: str
    password: str
    is_active: bool
    role: str


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


db_depedency = Annotated[Session, Depends(get_db)]


def authenticate_users(username: str, password: str, db):
    user = db.query(Users).filter(Users.username == username).first()

    if not user:
        return False

    if not bcrypt_context.verify(password, user.hashed_password):
        return False
    return user


def create_access_token(
    username: str, user_id: int, role: str, expires_delta: timedelta
):
    encode = {"sub": username, "id": user_id, "role": role}

    expires = datetime.now(timezone.utc) + expires_delta
    # expires = datetime.now(timezone.UTC) + expires_delta
    encode.update({"exp": expires})

    return jwt.encode(encode, SECRET_KEY, algorithm=ALGORITHM)


credentials_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not verify credentials",
    headers={"WWW-Authenticate": "Bearer"},
)


async def get_current_user(token: Annotated[str, Depends(oauth2_bearer)]):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        user_id: int = payload.get("id")
        role: str = payload.get("role")

        if username is None or user_id is None:
            raise credentials_exception
        return {"username": username, "id": user_id, "role": role}
    except JWTError:
        raise credentials_exception


@router.get("/all_db_users", status_code=status.HTTP_200_OK)
async def all_db_users(db: db_depedency):
    return db.query(Users).all()


@router.post("/", status_code=status.HTTP_200_OK)
async def create_user_auth(db: db_depedency, create_user: CreateUserAuth):
    create_user_model = Users(
        username=create_user.username,
        email=create_user.email,
        first_name=create_user.first_name,
        last_name=create_user.last_name,
        hashed_password=bcrypt_context.hash(create_user.password),
        is_active=True,
        role=create_user.role,
    )

    db.add(create_user_model)
    db.commit()


@router.post("/token")
async def login_for_token_access(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()], db: db_depedency
):
    user = authenticate_users(form_data.username, form_data.password, db)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Failed Authentication"
        )

    token = create_access_token(
        user.username, user.id, user.role, timedelta(minutes=20)
    )

    return {"access_token": token, "token_type": "bearer"}
