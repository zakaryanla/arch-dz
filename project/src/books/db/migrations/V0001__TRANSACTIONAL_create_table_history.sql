CREATE SCHEMA IF NOT EXISTS books;

CREATE TABLE books.books (
    id UUID NOT NULL UNIQUE,
    price integer NOT NULL,
    lvl character varying(40),
    created timestamp DEFAULT now()
);


ALTER TABLE books.books ADD COLUMN summary character varying(400) NOT NULL;
ALTER TABLE books.books ADD COLUMN author character varying(400) NOT NULL;