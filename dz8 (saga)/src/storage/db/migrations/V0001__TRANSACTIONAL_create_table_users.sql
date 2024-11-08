CREATE SCHEMA IF NOT EXISTS storage;


CREATE SEQUENCE storage.id
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


CREATE TABLE storage.products (
    id integer DEFAULT nextval('storage.id'::regclass),
    tr_guid UUID NOT NULL,
    product character varying(1400),
    cnt integer,
    created timestamp DEFAULT now(),
    UNIQUE (tr_guid, cnt)
	);


INSERT INTO storage.products(tr_guid, product, cnt) values (gen_random_uuid (), 'pizza', 100);
INSERT INTO storage.products(tr_guid, product, cnt) values (gen_random_uuid (), 'sushi', 100);
INSERT INTO storage.products(tr_guid, product, cnt) values (gen_random_uuid (), 'cake', 100);
INSERT INTO storage.products(tr_guid, product, cnt) values (gen_random_uuid (), 'juice', 100);