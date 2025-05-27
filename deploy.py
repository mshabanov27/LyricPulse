import psycopg2
import pandas as pd
from services.FingerprintGenerator import FingerprintGenerator
from services.MelodicContourGenerator import MelodicContourGenerator
import os
from dotenv import load_dotenv
from pydub import AudioSegment
from io import BytesIO


def load_audio_from_path(file_path):
    try:
        audio = AudioSegment.from_file(file_path)
    except Exception as e:
        print(f"Error loading file: {str(e)}")
        return None

    wav = BytesIO()
    audio.export(wav, format='wav')
    wav.seek(0)
    return wav


if __name__ == '__main__':
    load_dotenv()

    fingerprint_generator = FingerprintGenerator()
    melodic_contour_generator = MelodicContourGenerator()

    conn = psycopg2.connect(database=os.getenv('DATABASE_NAME'),
                            host=os.getenv('DATABASE_HOST'),
                            user=os.getenv('DATABASE_USER'),
                            password=os.getenv('DATABASE_PASSWORD'),
                            port=os.getenv('DATABASE_PORT'))

    cursor = conn.cursor()

    cursor.execute(open("create_tables.sql", "r").read())
    conn.commit()

    songs = pd.read_csv(os.getenv("METADATA_PATH"))
    songs_query = "INSERT INTO songs(name, artist, album_cover, lyrics, youtube_id) VALUES (%s, %s, %s, %s, %s) RETURNING id"
    hashes_query = "INSERT INTO fingerprints(song_id, hash, time_anchor) VALUES (%s, %s, %s)"
    contour_query = "INSERT INTO melodic_contours(song_id, chunk_index, delta_pitches, dp_mean, dp_std) VALUES (%s, %s, %s, %s, %s)"
    audio_base_path = os.getenv('AUDIO_BASE_PATH')

    for index, row in songs.iterrows():
        wav_io = load_audio_from_path(os.path.join(audio_base_path, row['Path']))

        cursor.execute(songs_query, (row['Title'], row['Artist'], row['CoverImage'], row['Lyrics'], row['YouTubeID']))
        song_id = cursor.fetchone()[0]

        all_hashes = fingerprint_generator.extract_hashes_from_audio(wav_io)

        for h, t in all_hashes:
            cursor.execute(hashes_query, (song_id, h, int(t)))

        conn.commit()

        wav_io.seek(0)
        features = melodic_contour_generator.extract_features(wav_io)

        for feature in features:
            cursor.execute(contour_query, (song_id,
                                           feature['chunk_index'],
                                           feature['delta_pitches'],
                                           feature['dp_mean'],
                                           feature['dp_std']))

        conn.commit()
        print(f"Uploaded {row['Title']} by {row['Artist']}...")

    cursor.execute(open("post_deployment.sql", "r").read())
    conn.commit()

    cursor.close()
    conn.close()
