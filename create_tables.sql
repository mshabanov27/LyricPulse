CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE users(
    id SERIAL UNIQUE PRIMARY KEY,
    username VARCHAR(30) UNIQUE,
    password VARCHAR(255),
    is_admin BOOLEAN
);

CREATE TABLE songs(
    id SERIAL UNIQUE PRIMARY KEY,
    name VARCHAR(255),
    artist VARCHAR(255),
    album_cover VARCHAR(255),
    lyrics TEXT,
    youtube_id VARCHAR(255)
);

CREATE TABLE history(
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE ON UPDATE CASCADE,
    song_id INTEGER REFERENCES songs(id) ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE TABLE fingerprints (
    id SERIAL PRIMARY KEY,
    song_id INTEGER REFERENCES songs(id) ON DELETE CASCADE ON UPDATE CASCADE,
    hash VARCHAR(20),
    time_anchor INTEGER
);

CREATE TABLE melodic_contours (
    song_id INTEGER REFERENCES songs(id) ON DELETE CASCADE ON UPDATE CASCADE,
    chunk_index INTEGER,
    delta_pitches vector(300),
    dp_mean FLOAT,
    dp_std FLOAT,
    PRIMARY KEY (song_id, chunk_index)
);
