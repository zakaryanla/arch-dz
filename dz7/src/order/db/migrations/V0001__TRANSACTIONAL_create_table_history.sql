CREATE SCHEMA IF NOT EXISTS orders;

CREATE TABLE orders.history (
    userid UUID NOT NULL,
    product character varying(40),
    sum integer,
    resault  character varying(40),
    created timestamp DEFAULT now()
);