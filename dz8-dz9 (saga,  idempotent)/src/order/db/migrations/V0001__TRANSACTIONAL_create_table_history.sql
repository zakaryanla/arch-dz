CREATE SCHEMA IF NOT EXISTS orderdb;

CREATE TABLE orderdb.history (
    userid UUID NOT NULL,
    tr_guid UUID NOT NULL,
    dt date,
    cnt integer,
    product character varying(40),
    sum integer,
    created timestamp DEFAULT now()
);

ALTER TABLE orderdb.history ADD COLUMN resault character varying(400);
ALTER TABLE orderdb.history ADD COLUMN status character varying(40) DEFAULT NULL;