DROP TABLE IF EXISTS user;
DROP TABLE IF EXISTS post;
DROP TABLE IF EXISTS vote;
DROP TABLE IF EXISTS comment;
DROP TABLE IF EXISTS commentvote;

CREATE TABLE user (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  username TEXT UNIQUE NOT NULL,
  password TEXT NOT NULL,
  created TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  about TEXT,
  is_golden BOOLEAN NOT NULL DEFAULT 0
);

INSERT INTO user (username, password) VALUES ('Anonymous', '.');

CREATE TABLE post (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  author_id INTEGER NOT NULL,
  created TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  edited TIMESTAMP,
  title TEXT NOT NULL,
  body TEXT NOT NULL,
  rendered TEXT NOT NULL,
  anon BOOLEAN,
  show_in_feed BOOLEAN NOT NULL DEFAULT 1,
  FOREIGN KEY (author_id) REFERENCES user (id)
);
CREATE INDEX idx_post_created ON post(created);

ALTER TABLE user ADD COLUMN about_post_id INT REFERENCES post(id);

CREATE TABLE vote (
  user_id INTEGER NOT NULL,
  post_id INTEGER NOT NULL,
  vote INTEGER NOT NULL,
  weighted_vote INTEGER NOT NULL,
  karma_vote REAL NOT NULL,
  FOREIGN KEY (user_id) REFERENCES user (id),
  FOREIGN KEY (post_id) REFERENCES post (id),
  UNIQUE (user_id, post_id)
);

CREATE TABLE comment (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  author_id INTEGER NOT NULL,
  created TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  body TEXT NOT NULL,
  rendered TEXT NOT NULL,
  post_id INTEGER NOT NULL,
  parent_id INTEGER,
  anon BOOLEAN,
  FOREIGN KEY (author_id) REFERENCES user (id),
  FOREIGN KEY(post_id) REFERENCES post (id)
);
CREATE INDEX idx_comment_post ON comment(post_id);

CREATE TABLE commentvote (
  user_id INTEGER NOT NULL,
  post_id INTEGER NOT NULL,
  comment_id INTEGER NOT NULL,
  vote INTEGER NOT NULL,
  weighted_vote INTEGER NOT NULL,
  karma_vote REAL NOT NULL, 
  FOREIGN KEY (user_id) REFERENCES user (id),
  FOREIGN KEY (post_id) REFERENCES post (id),
  FOREIGN KEY (comment_id) REFERENCES comment (id),
  UNIQUE (user_id, post_id, comment_id)
);
CREATE INDEX idx_commentvote_post ON commentvote(post_id);
