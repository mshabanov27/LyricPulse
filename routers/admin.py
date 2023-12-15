from fastapi import APIRouter, Request, Depends, HTTPException, status, Path
from typing import Annotated
from routers.models import User
from routers.login import get_current_user
from routers.database import cursor, conn
from template_conf import templates


router = APIRouter()


@router.get("/adminPanel/", tags=["Admin Actions", "Templates"])
def get_admin_panel(request: Request, current_user: Annotated[User, Depends(get_current_user)]):
    if not current_user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail='Available only for administrators')

    user_tags = ''
    response = {'user_tags': user_tags, 'request': request}

    return templates.TemplateResponse('adminpanel.html', response)


@router.get("/users/{searchQuery}", tags=["Admin Actions", "Templates"])
def search_users(request: Request, current_user: Annotated[User, Depends(get_current_user)], searchQuery: str):
    if not current_user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail='Available only for administrators')

    query = "SELECT id, username from users WHERE is_admin = false AND username LIKE %s ORDER BY username;"
    cursor.execute(query, (f'{searchQuery}%',))
    users = cursor.fetchall()

    if users:
        user_tags = ''

        for user in users:
            user_tags += f'<div class="user-piece"> \
                                <div class="username">{user[1]}</div> \
                                <button class ="black-button" id="{user[0]}" onclick="blockUser(this.id)"> Block </button> \
                            </div>'
    else:
        user_tags = '<div style="font-size: 40px; align-self: center;">Not found</div>'

    response = {'user_tags': user_tags, 'request': request}

    return templates.TemplateResponse('adminpanel.html', response)


@router.get("/users/", tags=["Admin Actions"])
def handle_empty_users(request: Request, current_user: Annotated[User, Depends(get_current_user)]):
    if not current_user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail='Available only for administrators')

    user_tags = '<div style="font-size: 40px; align-self: center;">Your search query was empty</div>'
    response = {'user_tags': user_tags, 'request': request}

    return templates.TemplateResponse('adminpanel.html', response)


@router.delete("/users/{userId}", tags=["Admin Actions"])
def delete_other_user(request: Request, current_user: Annotated[User, Depends(get_current_user)], userId: str = Path()):
    if not current_user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail='Available only for administrators')

    query = "DELETE FROM users WHERE id = %s;"
    cursor.execute(query, (userId,))
    conn.commit()

    return {"message": "User blocked successfully"}

