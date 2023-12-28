from fastapi import HTTPException, Depends, APIRouter, status, Form
from fastapi.responses import RedirectResponse
from typing import Annotated
from routers.database import cursor, conn
from routers.models import User
import routers.security as security
from routers.login import get_current_user
from routers.validation import validate_username, validate_password

router = APIRouter()


@router.get("/users/me", tags=["User", "Account"])
async def read_users_me(current_user: Annotated[User, Depends(get_current_user)]):
    return current_user


@router.post("/user/", status_code=status.HTTP_201_CREATED, tags=["User", "Account"])
def add_user(username: Annotated[str, Form()], password: Annotated[str, Form()]):
    if not (validate_username(username) and validate_password(password)):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Failed username or password validation")

    query = "SELECT username from users WHERE username = %s"
    cursor.execute(query, (username,))
    if cursor.fetchone():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Username already exists")

    encrypted_password = security.encrypt_value(password)
    query = "INSERT INTO users(username, password, is_admin) VALUES (%s, %s, false)"
    cursor.execute(query, (username, encrypted_password))
    conn.commit()


@router.put("/username/", tags=["User"])
def change_username(current_user: Annotated[User, Depends(get_current_user)], new_username: Annotated[str, Form()]):
    if not validate_username(new_username):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Failed new username validation")

    query = "UPDATE users SET username = %s WHERE id = %s"
    cursor.execute(query, (new_username, current_user.id,))
    conn.commit()

    return {"message": "Username changed successfully"}


@router.put("/password/", tags=["User"])
def change_password(current_user: Annotated[User, Depends(get_current_user)],
                    old_password: Annotated[str, Form()], new_password: Annotated[str, Form()]):
    if not validate_password(new_password):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Failed password validation")

    if not security.check_password(current_user.username, old_password):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Old password is incorrect")

    encrypted_password = security.encrypt_value(new_password)

    query = "UPDATE users SET password = %s WHERE id = %s"
    cursor.execute(query, (encrypted_password, current_user.id,))
    conn.commit()

    return {"message": "Password changed successfully"}


@router.delete("/user/", tags=["User"])
def delete_user(current_user: Annotated[User, Depends(get_current_user)]):
    query = "DELETE FROM users WHERE id = %s"
    cursor.execute(query, (current_user.id,))
    conn.commit()
    return RedirectResponse(url="/signUp/", status_code=status.HTTP_303_SEE_OTHER)
