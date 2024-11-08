CREATE SEQUENCE delivery.userid
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE TABLE delivery.runners (
    id integer DEFAULT nextval('delivery.userid'::regclass),
    fio character varying(1400),
    created timestamp DEFAULT now()
);

CREATE TABLE delivery.delivery (
    tr_guid UUID NOT NULL,
    userid integer,
    slot date,
    state character varying(200),
    created timestamp DEFAULT now(),
    UNIQUE (tr_guid, userid)
);

INSERT INTO delivery.runners(fio) values ('Ivanov');
INSERT INTO delivery.runners(fio) values ('Petrov');
INSERT INTO delivery.delivery(tr_guid, userid, slot, state) values (gen_random_uuid(), 1, '2025-01-01','confirmed');
INSERT INTO delivery.delivery(tr_guid, userid, slot, state) values (gen_random_uuid(), 1, '2025-01-02','confirmed');
INSERT INTO delivery.delivery(tr_guid, userid, slot, state) values (gen_random_uuid(), 2, '2025-01-03','confirmed');
INSERT INTO delivery.delivery(tr_guid, userid, slot, state) values (gen_random_uuid(), 2, '2025-01-01','confirmed');