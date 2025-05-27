from fastapi import APIRouter, Request, Depends, HTTPException
from typing import Annotated
from routers.models import User
from routers.login import get_current_user
from routers.recognition import request_song_info, add_song_to_history, make_empty_response
from template_conf import templates


router = APIRouter()


@router.get("/", tags=["Templates"])
def home(request: Request):
    response = {'request': request}
    return templates.TemplateResponse('landing.html', response)


@router.get("/signIn/", tags=["Templates"])
def get_signin(request: Request):
    response = {'request': request}
    return templates.TemplateResponse('sign-in.html', response)


@router.get("/signUp/", tags=["Templates"])
def get_signup(request: Request):
    response = {'request': request}
    return templates.TemplateResponse('sign-up.html', response)


@router.get("/detection/", tags=["Templates"])
def get_detection(request: Request):
    response = {'request': request}
    return templates.TemplateResponse('detection.html', response)


@router.get("/hummingDetection/", tags=["Templates"])
def get_detection(request: Request):
    response = {'request': request}
    return templates.TemplateResponse('humming-detection.html', response)


@router.get("/lyrics/{trackId}", tags=["Templates", "Recognition"])
async def get_lyrics(request: Request, trackId: str):
    if trackId != "NotFound":
        response = await request_song_info(trackId)

        if 'access_token' in request.cookies:
            token = request.cookies['access_token']
            try:
                user = await get_current_user(token)
                if user:
                    add_song_to_history(user.id, trackId)
            except HTTPException:
                pass
    else:
        response = make_empty_response()

    response['request'] = request

    return templates.TemplateResponse('lyrics.html', response)


@router.get("/profile/", tags=["Templates"])
def get_profile(request: Request, current_user: Annotated[User, Depends(get_current_user)]):
    response = {'username': current_user.username, 'request': request}
    return templates.TemplateResponse('profile.html', response)


@router.get("/password/", tags=["Templates"])
def get_password_change_page(request: Request, current_user: Annotated[User, Depends(get_current_user)]):
    response = {'username': current_user.username, 'request': request}
    return templates.TemplateResponse('password.html', response)
