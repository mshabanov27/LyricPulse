WITH a AS (
  SELECT hash, count(*)
  FROM fingerprints
  GROUP BY hash
  HAVING COUNT(*) > 1000
)
DELETE FROM fingerprints
USING a
WHERE fingerprints.hash = a.hash;

CREATE INDEX idx_hash_song_time ON fingerprints(hash, song_id, time_anchor);

CREATE INDEX ON melodic_contours USING hnsw (delta_pitches vector_cosine_ops)
WITH (m = 32, ef_construction = 200);
SET hnsw.ef_search = 100;
SET enable_seqscan = OFF;
