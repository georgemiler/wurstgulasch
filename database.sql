CREATE TABLE sftib_posts (
    id INTEGER PRIMARY KEY,
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
    id INTEGER PRIMARY KEY,
    tag TEXT
);

CREATE TABLE sftib_post_is_tagged (
    id INTEGER PRIMARY KEY,
    post_id INTEGER,
    tag_id INTEGER
);

CREATE TABLE sftib_connected_instances (
    id INTEGER PRIMARY KEY,
    screen_name TEXT,
    base_url TEXT,
);

INSERT INTO sftib_posts (id, post_id, origin, content_type, content_string, source, description, reference, signature) VALUES (NULL, "13374288", "http://dev.img.sft.mx/", "image", "http://www.looki.de/gfx/product/1/1960/screenshot/114029_800.jpg", "http://www.alpecin.de", "Dr. Adolf Klenk", NULL, NULL);
