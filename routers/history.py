from fastapi import APIRouter, Depends, status, Request
from fastapi.responses import RedirectResponse
from typing import Annotated
from routers.models import User
from routers.login import get_current_user
from routers.database import cursor, conn
from template_conf import templates

router = APIRouter()


@router.get("/history/", tags=["Templates", "History"])
def get_history(current_user: Annotated[User, Depends(get_current_user)], request: Request):
    query = "SELECT h.song_id, s.* FROM history h LEFT JOIN LATERAL \
            (SELECT name, artist, album_cover FROM songs s WHERE h.song_id = s.id OFFSET 0) s ON TRUE \
             WHERE user_id = %s;"
    cursor.execute(query, (current_user.id,))
    history = cursor.fetchall()
    history.reverse()
    history_tags = ''

    if history:
        for song in history:
            history_tags += \
                f'<div class="song-info"> \
                    <img src="{song[3]}"\
                         alt="{song[1]}" \
                         class="album-cover"> \
                    <div> \
                        <div style=\
                            "display: flex; flex-direction: column; gap: 15px; align-self: center; max-width: 600px"> \
                            <div class="name">{song[1]}</div> \
                            <div class="artist">{song[2]}</div> \
                        </div> \
                    </div> \
                </div>'
    else:
        history_tags = '<div style="font-size: 40px; align-self: center;">Your history is empty</div>'

    response = {'history_tags': history_tags, 'request': request}

    return templates.TemplateResponse('history.html', response)


@router.delete("/history/", tags=["History"])
def delete_history(current_user: Annotated[User, Depends(get_current_user)]):
    query = "DELETE FROM history VALUES WHERE user_id = (SELECT id FROM users WHERE username = %s)"
    cursor.execute(query, (current_user.username,))
    conn.commit()
    return RedirectResponse(url="/profile/", status_code=status.HTTP_303_SEE_OTHER)


def in_history(song_id):
    query = "SELECT * FROM songs WHERE id = %s"
    cursor.execute(query, (song_id,))
    if cursor.fetchall():
        return True

    return False
