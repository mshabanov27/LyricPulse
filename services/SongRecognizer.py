import numpy as np
from routers.database import conn, cursor
import pandas as pd
from collections import defaultdict
from pgvector.psycopg2 import register_vector
from pydub import AudioSegment
from io import BytesIO


class SongRecognizer:
    def __init__(self, fingerprint_generator, melodic_contour_generator, top_n=500):
        self.__fingerprint_generator = fingerprint_generator
        register_vector(conn)
        self.__melodic_contour_generator = melodic_contour_generator
        self.top_n = top_n

    def find_by_song_piece(self, memory_file):
        wav_io = self.__load_audio_from_memory(memory_file)
        if wav_io == 'NotFound':
            return wav_io

        query_hashes = self.__fingerprint_generator.extract_hashes_from_audio(wav_io)
        if len(query_hashes) == 0:
            return 'NotFound'

        hash_to_times = defaultdict(list)
        for h, t in query_hashes:
            hash_to_times[h].append(t)
        unique_hashes = list(hash_to_times.keys())

        df_db = self.match_db_fingerprints(unique_hashes)

        top_matches = self.get_best_fingerprinting_results(df_db, hash_to_times)

        if len(top_matches) >= 2:
            top_count = top_matches.iloc[0]['count']
            second_count = top_matches.iloc[1]['count']

            if top_count - second_count < 5 and top_count < 25:
                return 'NotFound'
            return top_matches.iloc[0]['song_id']

        return 'NotFound'

    def find_by_humming(self, memory_file):
        wav_io = self.__load_audio_from_memory(memory_file)
        if wav_io == 'NotFound':
            return wav_io

        user_chunk = self.__melodic_contour_generator.extract_features(wav_io)[0]

        if abs(user_chunk['dp_mean']) < 0.1 and abs(user_chunk['dp_std']) < 0.5:
            return 'NotFound'

        user_dp = np.array(user_chunk['delta_pitches'])

        delta_candidates = self.query_candidates(user_dp, user_chunk['dp_std'])

        user_dp_denormalized = user_dp * (user_chunk['dp_std'] + 1e-6) + user_chunk['dp_mean']

        song_scores = self.__get_scores(user_dp_denormalized, delta_candidates)

        return song_scores[:3]

    @staticmethod
    def __load_audio_from_memory(memory_file: BytesIO):
        memory_file.seek(0)
        try:
            audio = AudioSegment.from_file(memory_file)
        except:
            return 'NotFound'
        wav_io = BytesIO()
        audio.export(wav_io, format='wav')
        wav_io.seek(0)
        return wav_io

    def get_best_fingerprinting_results(self, df_db, hash_to_times):
        df_query = pd.DataFrame({
            'hash': [h for h, times in hash_to_times.items() for _ in times],
            'time_query': [t_query for times in hash_to_times.values() for t_query in times]
        })

        merged = df_db.merge(df_query, on='hash')
        merged['delta'] = merged['time_anchor'] - merged['time_query']

        grouped = merged.groupby(['song_id', 'delta']).size().reset_index(name='count')

        top_deltas = grouped.sort_values(by='count', ascending=False)
        top_per_song = top_deltas.groupby('song_id').head(3)

        song_scores = top_per_song.groupby('song_id')['count'].sum().reset_index()
        return song_scores.sort_values(by='count', ascending=False).head(5)

    def __get_scores(self, user_dp_denormalized, delta_candidates):
        results = []
        for candidate in delta_candidates:
            song_dp_denormalized = candidate[2] * (candidate[4] + 1e-6) + candidate[3]

            dist = self.__melodic_contour_generator.compare(song_dp_denormalized, user_dp_denormalized)
            results.append((candidate[0], candidate[1], dist))

        aggregated = defaultdict(list)
        for song_id, chunk_idx, dist in results:
            aggregated[song_id].append((dist, chunk_idx))

        song_scores = [
            (song_id, min(dists_chunks))
            for song_id, dists_chunks in aggregated.items()
        ]

        song_scores.sort(key=lambda x: x[1][0])

        return song_scores

    def match_db_fingerprints(self, unique_hashes):
        cursor.execute(
            "SELECT song_id, hash, time_anchor FROM fingerprints WHERE hash = ANY(%s)",
            (unique_hashes,)
        )
        rows = cursor.fetchall()

        return pd.DataFrame(rows, columns=['song_id', 'hash', 'time_anchor'])

    def query_candidates(self, delta_query_vec, user_std):
        delta_query_vec = np.pad(delta_query_vec, (0, 300 - len(delta_query_vec)), mode="reflect").tolist()

        with conn.cursor() as cur:
            cur.execute("""
                SELECT song_id, chunk_index, delta_pitches, dp_mean, dp_std
                FROM melodic_contours
                ORDER BY delta_pitches <#> %s::vector
                LIMIT %s
            """, (delta_query_vec, self.top_n))

            delta_candidates = cur.fetchall()

        return delta_candidates
