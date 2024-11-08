CREATE SCHEMA IF NOT EXISTS notifications;


CREATE SEQUENCE notifications.id
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


CREATE TABLE notifications.history (
    id integer DEFAULT nextval('notifications.id'::regclass),
    userid UUID NOT NULL,
    text character varying(1400),
    status character varying(40),
    created timestamp DEFAULT now(),
    update timestamp
);

