CREATE SCHEMA IF NOT EXISTS payment;

CREATE TABLE payment.history (
    userid UUID NOT NULL,
    tr_guid UUID NOT NULL,
    sum integer,
    created timestamp DEFAULT now()
);

INSERT INTO  payment.history(userid, tr_guid, sum) VALUES ('6c6af38e-1e76-4b8a-9284-efd9a0842f0d', gen_random_uuid (), 1000);