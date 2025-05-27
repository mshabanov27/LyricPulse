from fastapi import APIRouter, File, UploadFile, Request
from fastapi.responses import RedirectResponse
from io import BytesIO
import starlette.status as status
from routers.database import cursor, conn
from services.recognizer_creation import get_recognizer
from template_conf import templates

router = APIRouter()
song_recognizer = get_recognizer()


@router.post("/recognition/", tags=["Templates", "Recognition"])
async def recognize_track(file: UploadFile = File(...)):
    data = await file.read()
    memory_file = BytesIO(data)

    track_id = song_recognizer.find_by_song_piece(memory_file)

    return RedirectResponse(url=f"/lyrics/{track_id}", status_code=status.HTTP_301_MOVED_PERMANENTLY)


@router.post("/hummingResults/", tags=["Templates", "Recognition"])
async def recognize_track_by_humming(request: Request, file: UploadFile = File(...)):
    data = await file.read()
    memory_file = BytesIO(data)

    best_matches_id = song_recognizer.find_by_humming(memory_file)

    if best_matches_id == 'NotFound':
        response = make_empty_response()
        response['request'] = request
        return templates.TemplateResponse('lyrics.html', response)

    best_matches_with_metadata = []

    for match_result in best_matches_id:
        song_info = await request_song_info(match_result[0])
        song_info['match_percent'] = 1 / (1 + match_result[1][0]) * 100
        best_matches_with_metadata.append(song_info)

    humming_results_tags = make_humming_results_response(best_matches_with_metadata)

    response = {'humming_results_tags': humming_results_tags, 'request': request}

    return templates.TemplateResponse('humming-results.html', response)


async def request_song_info(track_id):
    cursor.execute(
        "SELECT * FROM songs WHERE id=%s",
        (track_id,)
    )
    result = cursor.fetchone()
    columns = [desc[0] for desc in cursor.description]

    response = dict(zip(columns, result))
    if response['lyrics'] == 'NaN':
        response['lyrics'] = 'No lyrics for this song.'

    return response


def add_song_to_history(user_id, song_id):
    query = "INSERT INTO history(user_id, song_id) VALUES (%s, %s)"

    cursor.execute(query, (user_id, song_id, ))
    conn.commit()


def make_empty_response():
    return {'name': 'Not Found',
            'artist': 'Not Found',
            'album_cover': 'notfound.png',
            'lyrics': 'Not Found',
            'youtube_id': 'Not Found'}


def make_humming_results_response(songs):
    humming_results_tags = ''

    if songs:
        for song in songs:
            humming_results_tags += \
                f'<a class="result" href="/lyrics/{song["id"]}" target="_blank rel="noopener noreferrer"">\
                        <img src="/frontend/static/media/album_covers/{song["album_cover"]}"\
                                     alt="Album cover"\
                                     class="album-cover">\
                        <div>\
                            <div  class="song-metadata">\
                                <div class="name">{song["name"]}</div>\
                                <div class="artist">{song["artist"]}</div>\
                                <div class="artist">{song["match_percent"]:.0f}% match</div>\
                            </div>\
                        </div>\
                    </a>'
    else:
        humming_results_tags = '<div style="font-size: 40px; align-self: center;">No results!</div>'


    return humming_results_tags
