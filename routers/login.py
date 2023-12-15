from fastapi import APIRouter, status, HTTPException, Response, Depends
from fastapi.security import OAuth2PasswordRequestForm
from typing import Annotated
from jose import JWTError, jwt
from routers.security import oauth2_scheme, SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_DAYS, create_access_token, check_password, encrypt_value
from datetime import timedelta
from routers.models import User, TokenData
from routers.database import cursor
from routers.validation import validate_username, validate_password


router = APIRouter()


async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    if token.startswith("Bearer "):
        token = token[7:]

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=ALGORITHM)
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
        token_data = TokenData(id=user_id)
    except JWTError:
        raise credentials_exception

    query = "SELECT id, username, is_admin from users WHERE id = %s"
    cursor.execute(query, (token_data.id, ))
    user = cursor.fetchone()

    if user is None:
        raise credentials_exception

    user_obj = User(id=user[0], username=user[1], is_admin=user[2])
    return user_obj


def authenticate_user(username: str, password: str):
    query = "SELECT id, username, is_admin from users WHERE username = %s"
    cursor.execute(query, (username,))
    user = cursor.fetchone()
    if not user or not check_password(username, password):
        return False

    user_obj = User(id=user[0], username=user[1], is_admin=user[2])
    return user_obj


@router.post("/token/", tags=["Account"])
def login(response: Response, form_data: Annotated[OAuth2PasswordRequestForm, Depends()]):
    if not (validate_username(form_data.username) and validate_password(form_data.password)):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Failed username or password validation")

    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS)
    access_token = create_access_token(
        data={"sub": user.id}, expires_delta=access_token_expires
    )

    response.set_cookie(key="access_token", value=f"Bearer {access_token}",
                        httponly=True)

    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/logout/", tags=["Account"])
def logout(response: Response):
    response.delete_cookie(key="access_token")
    return {"message": "Logged out successfully"}
