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
  is_golden BOOLEAN
);

CREATE TABLE post (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  author_id INTEGER NOT NULL,
  created TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  edited TIMESTAMP,
  title TEXT NOT NULL,
  body TEXT NOT NULL,
  rendered TEXT NOT NULL,
  FOREIGN KEY (author_id) REFERENCES user (id)
);

ALTER TABLE user ADD COLUMN about_post_id INT REFERENCES post(id);

CREATE TABLE vote (
  user_id INTEGER NOT NULL,
  post_id INTEGER NOT NULL,
  vote INTEGER NOT NULL,
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
  FOREIGN KEY (author_id) REFERENCES user (id),
  FOREIGN KEY(post_id) REFERENCES post (id)
);

CREATE TABLE commentvote (
  user_id INTEGER NOT NULL,
  post_id INTEGER NOT NULL,
  comment_id INTEGER NOT NULL,
  vote INTEGER NOT NULL,
  FOREIGN KEY (user_id) REFERENCES user (id),
  FOREIGN KEY (post_id) REFERENCES post (id),
  FOREIGN KEY (comment_id) REFERENCES comment (id),
  UNIQUE (user_id, post_id, comment_id)
);
