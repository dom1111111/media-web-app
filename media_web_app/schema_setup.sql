-- the main table to hold all media entries
CREATE TABLE IF NOT EXISTS media (
    title TEXT NOT NULL,
    type TEXT
        CHECK (type IN ('movie', 'show', 'video')),
    thumbnail TEXT,    
    description TEXT,
    genre TEXT,
    released INT
        CHECK (released BETWEEN 1800 and 9999),
    length INT
        CHECK (length < 100000),
    path TEXT
);