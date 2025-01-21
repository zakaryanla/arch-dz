CREATE SCHEMA IF NOT EXISTS nf;

CREATE SEQUENCE nf.id
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE SEQUENCE nf.subid
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
    
CREATE TABLE nf.history (
    id integer DEFAULT nextval('nf.id'::regclass),
    userid UUID NOT NULL,
    text character varying(1400),
    status character varying(40),
    created timestamp DEFAULT now(),
    update timestamp
);

CREATE TABLE nf.sub (
    id integer DEFAULT nextval('nf.subid'::regclass),
    userid UUID NOT NULL,
    bookid UUID NOT NULL,
    created timestamp DEFAULT now()
);
