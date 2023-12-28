from fastapi import APIRouter, File, UploadFile
from fastapi.responses import RedirectResponse
from shazamio import Shazam
import shazamio.client
import shazamio.user_agent
import json
from io import BytesIO
import requests
from random import choice
import starlette.status as status
from routers.database import cursor, conn
from routers.history import in_history


router = APIRouter()


@router.post("/recognition/", tags=["Templates", "Recognition"])
async def recognize_track(file: UploadFile = File(...)):
    data = await file.read()
    memory_file = BytesIO()
    memory_file.write(data)

    shazam = Shazam()
    recognized = await shazam.recognize_song(memory_file.getvalue())
    if len(recognized['matches']) != 0:
        track_id = recognized['matches'][0]['id']
    else:
        track_id = 'NotFound'

    return RedirectResponse(url=f"/lyrics/{track_id}", status_code=status.HTTP_301_MOVED_PERMANENTLY)


async def request_song_info(track_id):
    return await shazamio.client.HTTPClient.request(
        'GET',
        f'https://www.shazam.com/discovery/v5/en-US/GB/web/-/track/{track_id}?shazamapiversion=v3&video=v3',
        headers={
            'X-Shazam-Platform': 'IPHONE',
            'X-Shazam-AppVersion': '14.1.0',
            'Accept': '*/*',
            'Accept-Language': 'en-US',
            'Accept-Encoding': 'gzip, deflate',
            'User-Agent': choice(shazamio.user_agent.USER_AGENTS),
        },
    )


def filer_response(resp):
    result = dict()
    result['name'] = resp['title']
    result['artist'] = resp['subtitle']
    result['album_cover'] = resp['images']['coverarthq']

    if 'text' in resp['sections'][1]:
        result['lyrics'] = ' <br> '.join(resp['sections'][1]['text'])
        youtube_resp = requests.get(resp['sections'][2]['youtubeurl']).text
    else:
        result['lyrics'] = 'This song has no lyrics.'
        youtube_resp = requests.get(resp['sections'][1]['youtubeurl']).text

    youtube_link = json.loads(youtube_resp)['actions'][0]['uri']
    result['youtube_id'] = youtube_link[17:youtube_link.find('?')]

    return result


def add_song_to_history(user_id, song_id, name, artist, album_cover):
    if not in_history(song_id):
        query = "INSERT INTO songs(id, name, artist, album_cover) \
                         VALUES (%s, %s, %s, %s)"
        cursor.execute(query, (song_id, name, artist, album_cover, ))
        conn.commit()

    query = "INSERT INTO history(user_id, song_id) VALUES (%s, %s)"

    cursor.execute(query, (user_id, song_id, ))
    conn.commit()


def make_empty_response():
    return {'name': 'Not Found',
            'artist': 'Not Found',
            'album_cover': 'https://demofree.sirv.com/nope-not-here.jpg',
            'lyrics': 'Not Found',
            'youtube_id': 'Not Found'}
