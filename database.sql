CREATE TABLE sftib_posts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    post_id TEXT,
    timestamp INTEGER,
    origin TEXT,
    content_type TEXT,
    content_string TEXT,
    source TEXT,
    description TEXT,
    reference TEXT,
    signature TEXT
);

CREATE TABLE sftib_tags (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tag TEXT UNIQUE ON CONFLICT IGNORE
);

CREATE TABLE sftib_post_is_tagged (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    post_id INTEGER,
    tag_id INTEGER
);

CREATE TABLE sftib_connected_instances (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    screen_name TEXT,
    base_url TEXT
);

