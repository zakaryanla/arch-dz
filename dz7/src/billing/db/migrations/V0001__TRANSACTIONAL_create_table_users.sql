CREATE SCHEMA IF NOT EXISTS billing;

CREATE TABLE billing.users (
    id UUID NOT NULL,
    bill integer DEFAULT 0
);

ALTER TABLE ONLY billing.users
    ADD CONSTRAINT users_id_key UNIQUE (id);

CREATE TABLE billing.history (
    userid UUID NOT NULL,
    operation character varying(40),
    sum integer,
    created timestamp DEFAULT now()
);